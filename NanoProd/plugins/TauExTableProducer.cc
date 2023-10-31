/* TauExTableProducer.cc

Add extended information to the tau table in NanoAOD.
SV refitting code is based on https://github.com/cms-sw/cmssw/blob/master/RecoTauTag/RecoTau/plugins/PFTauSecondaryVertexProducer.cc#L111-L141 and https://github.com/danielwinterbottom/ICHiggsTauTau/blob/master/plugins/ICTauProducer.hh#L348-L389

*/

#include "DataFormats/NanoAOD/interface/FlatTable.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "FWCore/Framework/interface/global/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "RecoVertex/KalmanVertexFit/interface/KalmanVertexFitter.h"
#include "RecoVertex/VertexPrimitives/interface/TransientVertex.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "CandidateTools.h"

class TauExTableProducer : public edm::global::EDProducer<> {
public:
  using TauCollection = edm::View<pat::Tau>;
  static constexpr float default_value = std::numeric_limits<float>::quiet_NaN();

  TauExTableProducer(const edm::ParameterSet& cfg) :
      tauToken_(consumes<TauCollection>(cfg.getParameter<edm::InputTag>("taus"))),
      transTrackBuilderToken_(esConsumes(edm::ESInputTag("", "TransientTrackBuilder"))),
      precision_(cfg.getParameter<int>("precision"))
  {
    produces<nanoaod::FlatTable>("Tau");
  }

private:
  void produce(edm::StreamID id, edm::Event& event, const edm::EventSetup& setup) const override
  {
    const auto& taus = event.get(tauToken_);
    const auto& transTrackBuilder = setup.getData(transTrackBuilderToken_);

    std::vector<bool> has_sv(taus.size(), false);
    std::vector<float> sv_x(taus.size(), default_value);
    std::vector<float> sv_y(taus.size(), default_value);
    std::vector<float> sv_z(taus.size(), default_value);
    std::vector<float> sv_chi2(taus.size(), default_value);
    std::vector<float> sv_ndof(taus.size(), default_value);
    std::vector<std::vector<float>> sv_cov(6, std::vector<float>(taus.size(), default_value));

    for(size_t tau_index = 0; tau_index < taus.size(); ++tau_index) {
      const auto& tau = taus[tau_index];
      if(tau.decayMode()>= 5) {
        // Get tracks form PFTau daugthers
        std::vector<reco::TransientTrack> transTrk;

        const auto cands = tau.signalChargedHadrCands();
        for (const auto& cand : cands) {
          if (cand.isNull())
            continue;
          const reco::Track* track = cand_tools::getTrack(*cand);
          if (track != nullptr)
            transTrk.push_back(transTrackBuilder.build(*track));
        }
        TransientVertex transVtx;
        if(transTrk.size() > 1 && fitVertex(transTrk, transVtx)) {
          const reco::Vertex sv(transVtx);
          has_sv[tau_index] = true;
          sv_x[tau_index] = sv.x();
          sv_y[tau_index] = sv.y();
          sv_z[tau_index] = sv.z();
          sv_chi2[tau_index] = sv.chi2();
          sv_ndof[tau_index] = sv.ndof();
          const auto cov = sv.covariance();

          size_t cov_index = 0;
          for(size_t i = 0; i < 3; ++i) {
            for(size_t j = i; j < 3; ++j) {
              sv_cov.at(cov_index)[tau_index] = cov(i, j);
              ++cov_index;
            }
          }
        }
      }
    }

    auto tauTable = std::make_unique<nanoaod::FlatTable>(taus.size(), "Tau", false, true);
    tauTable->addColumn<bool>("hasRefitSV", has_sv, "has SV refit using miniAOD quantities");
    tauTable->addColumn<float>("refitSVx", sv_x, "x of the refit SV", precision_);
    tauTable->addColumn<float>("refitSVy", sv_y, "y of the refit SV", precision_);
    tauTable->addColumn<float>("refitSVz", sv_z, "z of the refit SV", precision_);
    tauTable->addColumn<float>("refitSVchi2", sv_chi2, "chi2 of the refit SV", precision_);
    tauTable->addColumn<float>("refitSVndof", sv_ndof, "ndof of the refit SV", precision_);

    size_t cov_index = 0;
    for(size_t i = 0; i < 3; ++i) {
      for(size_t j = i; j < 3; ++j) {
        std::ostringstream name, description;
        name << "refitSVcov" << i << j;
        description << "covariance (" << i << ", " << j << ") of the refit SV";
        tauTable->addColumn<float>(name.str(), sv_cov.at(cov_index), description.str(), precision_);
        ++cov_index;
      }
    }

    event.put(std::move(tauTable), "Tau");
  }

private:
  static bool fitVertex(const std::vector<reco::TransientTrack>& transTrk, TransientVertex& transVtx)
  {
    KalmanVertexFitter kvf(true);
    if (transTrk.size() < 2)
      return false;
    transVtx = kvf.vertex(transTrk);
    return transVtx.hasRefittedTracks() && transVtx.refittedTracks().size() == transTrk.size();
  }

private:
  const edm::EDGetTokenT<TauCollection> tauToken_;
  const edm::ESGetToken<TransientTrackBuilder, TransientTrackRecord> transTrackBuilderToken_;
  const unsigned int precision_;
};

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(TauExTableProducer);