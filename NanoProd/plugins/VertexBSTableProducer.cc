/* VertexBSTableProducer.cc

Add PV with the beam spot constraint to NanoAOD.
code is based on https://github.com/danielwinterbottom/TauRefit/blob/master/plugins/MiniAODRefitVertexProducer.cc

*/

#include "DataFormats/NanoAOD/interface/FlatTable.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "FWCore/Framework/interface/global/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "RecoVertex/AdaptiveVertexFit/interface/AdaptiveVertexFitter.h"
#include "RecoVertex/VertexPrimitives/interface/TransientVertex.h"
#include "RecoVertex/VertexPrimitives/interface/VertexException.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"

#include "CandidateTools.h"

class VertexBSTableProducer : public edm::global::EDProducer<> {
public:
  using Candidate = pat::PackedCandidate;
  using CandidateCollection = std::vector<Candidate>;
  using VertexCollection = reco::VertexCollection;
  using BeamSpot = reco::BeamSpot;

  static constexpr float default_value = std::numeric_limits<float>::quiet_NaN();

  VertexBSTableProducer(const edm::ParameterSet& cfg) :
      pfCandsToken_(consumes<CandidateCollection>(cfg.getParameter<edm::InputTag>("pfCands"))),
      lostTracksToken_(consumes<CandidateCollection>(cfg.getParameter<edm::InputTag>("lostTracks"))),
      bsToken_(consumes<BeamSpot>(cfg.getParameter<edm::InputTag>("beamSpot"))),
      transTrackBuilderToken_(esConsumes(edm::ESInputTag("", "TransientTrackBuilder"))),
      precision_(cfg.getParameter<int>("precision"))
  {
    produces<nanoaod::FlatTable>();
  }

private:
  void produce(edm::StreamID id, edm::Event& event, const edm::EventSetup& setup) const override
  {
    static const std::set<int> selectedQuality {
      pat::PackedCandidate::UsedInFitTight, pat::PackedCandidate::UsedInFitLoose,
    };

    const auto& pfCands = event.get(pfCandsToken_);
    const auto& lostTracks = event.get(lostTracksToken_);
    const auto& beamSpot = event.get(bsToken_);
    const auto& transTrackBuilder = setup.getData(transTrackBuilderToken_);

    std::vector<reco::TransientTrack> transTracks;
    for(auto candCollection : {&pfCands, &lostTracks}) {
      for(const auto& cand : *candCollection) {
        if(cand.charge()==0 || cand.vertexRef().isNull()
            || cand.vertexRef().key() != 0 || selectedQuality.count(cand.pvAssociationQuality()) == 0) continue;
        const reco::Track* track = cand_tools::getTrack(cand);
        if(track != nullptr)
          transTracks.push_back(transTrackBuilder.build(*track));
      }
    }

    bool pv_valid = false;
    float pv_x = default_value;
    float pv_y = default_value;
    float pv_z = default_value;
    float pv_chi2 = default_value;
    float pv_ndof = default_value;
    std::vector<float> pv_cov(6, default_value);

    TransientVertex transVtx;
    if(transTracks.size() >= 3) {
      AdaptiveVertexFitter avf;
	    avf.setWeightThreshold(0.1);
      try {
        transVtx = avf.vertex(transTracks, beamSpot);
        pv_valid = true;
      } catch(VertexException& e) {
        edm::LogWarning("VertexBSTableProducer") << "VertexException: " << e.what();
      }
    }

    if(pv_valid) {
      const reco::Vertex pv(transVtx);
      pv_x = pv.x();
      pv_y = pv.y();
      pv_z = pv.z();
      pv_chi2 = pv.chi2();
      pv_ndof = pv.ndof();
      const auto cov = pv.covariance();

      size_t cov_index = 0;
      for(size_t i = 0; i < 3; ++i) {
        for(size_t j = i; j < 3; ++j) {
          pv_cov.at(cov_index) = cov(i, j);
          ++cov_index;
        }
      }
    }

    auto pvTable = std::make_unique<nanoaod::FlatTable>(1, "RefitPV", true, false);
    pvTable->addColumnValue<bool>("valid", pv_valid, "refit PV with BS constraint is valid");
    pvTable->addColumnValue<float>("x", pv_x, "x of the refit PV", precision_);
    pvTable->addColumnValue<float>("y", pv_y, "y of the refit PV", precision_);
    pvTable->addColumnValue<float>("z", pv_z, "z of the refit PV", precision_);
    pvTable->addColumnValue<float>("chi2", pv_chi2, "chi2 of the refit PV", precision_);
    pvTable->addColumnValue<float>("ndof", pv_ndof, "ndof of the refit PV", precision_);

    size_t cov_index = 0;
    for(size_t i = 0; i < 3; ++i) {
      for(size_t j = i; j < 3; ++j) {
        std::ostringstream name, description;
        name << "cov" << i << j;
        description << "covariance (" << i << ", " << j << ") of the refit PV";
        pvTable->addColumnValue<float>(name.str(), pv_cov.at(cov_index), description.str(), precision_);
        ++cov_index;
      }
    }

    event.put(std::move(pvTable));
  }

private:
  const edm::EDGetTokenT<CandidateCollection> pfCandsToken_;
  const edm::EDGetTokenT<CandidateCollection> lostTracksToken_;
	const edm::EDGetTokenT<BeamSpot> bsToken_;
  const edm::ESGetToken<TransientTrackBuilder, TransientTrackRecord> transTrackBuilderToken_;
  const unsigned int precision_;
};

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(VertexBSTableProducer);