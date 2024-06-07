/**\class TauSpinnerTableProducer

 Description: Produces FlatTable with TauSpinner weights for H->tau,tau events

 Original Author: D.  Winterbottom (IC)
                  update, M. Bluj (NCBJ)
*/

#include <memory>
#include <vector>
#include <string>

#include "boost/functional/hash.hpp"
#include "boost/format.hpp"

#include "FWCore/Framework/interface/one/EDProducer.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Concurrency/interface/SharedResourceNames.h"
#include "DataFormats/Common/interface/View.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/NanoAOD/interface/FlatTable.h"

#include "Tauola/Tauola.h"
#include "TauSpinner/SimpleParticle.h"
#include "TauSpinner/tau_reweight_lib.h"

namespace {
  std::set<int> tauProdsIds{22, 111, 211, 321, 130, 310, 11, 12, 13, 14, 16};
}

class TauSpinnerTableProducer : public edm::one::EDProducer<edm::one::SharedResources> {
public:
  explicit TauSpinnerTableProducer(const edm::ParameterSet &);
  ~TauSpinnerTableProducer() override{};

  void produce(edm::Event &, const edm::EventSetup &) final;
  void beginJob() final { initialize(); }
  void endJob() final {}

private:
  void initialize();

  reco::GenParticle getBoson(const edm::View<reco::GenParticle> &parts, bool &foundBoson) const;
  reco::GenParticleRef getLastCopy(const reco::GenParticleRef &part) const;
  void getTaus(reco::GenParticleRefVector &taus, const reco::GenParticle &boson) const;
  void getTauDaughters(reco::GenParticleRefVector &tau_daughters, unsigned &type, const reco::GenParticle &tau) const;
  TauSpinner::SimpleParticle convertToSimplePart(const reco::GenParticle &input_part) const {
    return TauSpinner::SimpleParticle(
        input_part.px(), input_part.py(), input_part.pz(), input_part.energy(), input_part.pdgId());
  }

  std::vector<std::pair<std::string, double>> nameAndValue(const std::vector<double> &val_vec) const {
    std::vector<std::pair<std::string, double>> out;
    for (auto val : val_vec) {
      std::string name = std::to_string(val);
      name.erase(name.find_last_not_of('0') + 1, std::string::npos);
      name.erase(name.find_last_not_of('.') + 1, std::string::npos);
      size_t pos = name.find(".");
      if (pos != std::string::npos)
        name.replace(pos, 1, "p");
      pos = name.find("-");
      if (pos != std::string::npos)
        name.replace(pos, 1, "minus");
      out.push_back(std::make_pair(name, val));
    }
    return out;
  }

  void printModuleInfo(edm::ParameterSet const &config) const {
    std::string header = (boost::format("%-39s%39s") % config.getParameter<std::string>("@module_type") %
                          config.getParameter<std::string>("@module_label"))
                             .str();
    std::cout << std::string(78, '-') << "\n";
    std::cout << header << "\n";
    // std::cout << "Produces: " << flow << "\n";
    std::cout << boost::format("%-15s : %-60s\n") % "Input" % config.getParameter<edm::InputTag>("input").encode();
    std::cout << boost::format("%-15s : %-60s\n") % "Branch" % config.getParameter<std::string>("branch");
    std::string thetaStr;
    for (const auto &theta : theta_vec_)
      thetaStr += theta.first + ",";
    std::cout << boost::format("%-15s : %-60s\n") % "Theta" % thetaStr;
  }

  edm::EDGetTokenT<edm::View<reco::GenParticle>> genPartsToken_;
  std::string branch_;
  std::vector<std::pair<std::string, double>> theta_vec_;
  int bosonPdgId_;
  std::string tauSpinnerPDF_;
  bool ipp_;
  int ipol_;
  int nonSM2_;
  int nonSMN_;
  double cmsE_;
};

TauSpinnerTableProducer::TauSpinnerTableProducer(const edm::ParameterSet &config)
    : genPartsToken_(consumes(config.getParameter<edm::InputTag>("input"))),
      branch_(config.getParameter<std::string>("branch")),
      bosonPdgId_(25),                                             //Higgs, to be configurable?
      tauSpinnerPDF_(config.getParameter<std::string>("pdfSet")),  //"NNPDF30_nlo_as_0118"
      ipp_(true),                                                  //pp collisions
      ipol_(0),
      nonSM2_(0),
      nonSMN_(0),
      cmsE_(config.getParameter<double>("cmsE"))  //cms energy in GeV, 13000.0
{
  theta_vec_ = nameAndValue(config.getParameter<std::vector<double>>("theta"));

  printModuleInfo(config);

  //state that we use tauola/tauspinner resource
  usesResource(edm::SharedResourceNames::kTauola);

  produces<nanoaod::FlatTable>();
}

reco::GenParticle TauSpinnerTableProducer::getBoson(const edm::View<reco::GenParticle> &parts, bool &foundBoson) const {
  reco::GenParticle boson;
  foundBoson = false;
  for (auto part : parts) {
    if (std::abs(part.pdgId()) == bosonPdgId_ && part.isLastCopy()) {
      boson = part;
      foundBoson = true;
      break;
    }
  }
  return boson;
}

reco::GenParticleRef TauSpinnerTableProducer::getLastCopy(const reco::GenParticleRef &part) const {
  reco::GenParticleRef last_copy(part);
  if (part->statusFlags().isLastCopy())
    return last_copy;
  for (const auto &daughter : part->daughterRefVector()) {
    if (daughter->pdgId() == part->pdgId()) {
      last_copy = getLastCopy(daughter);
    }
  }
  return last_copy;
}

void TauSpinnerTableProducer::getTaus(reco::GenParticleRefVector &taus, const reco::GenParticle &boson) const {
  for (auto daughterRef : boson.daughterRefVector()) {
    if (std::abs(daughterRef->pdgId()) != 15)
      continue;
    taus.push_back(getLastCopy(daughterRef));
  }
}

void TauSpinnerTableProducer::getTauDaughters(reco::GenParticleRefVector &tau_daughters,
                                              unsigned &type,
                                              const reco::GenParticle &tau) const {
  for (auto daughterRef : tau.daughterRefVector()) {
    int daughter_pdgid = std::abs(daughterRef->pdgId());
    if (tauProdsIds.find(daughter_pdgid) != tauProdsIds.end()) {
      if (daughter_pdgid == 11)
        type = 1;
      if (daughter_pdgid == 13)
        type = 2;
      tau_daughters.push_back(daughterRef);
    } else
      getTauDaughters(tau_daughters, type, *daughterRef);
  }
}

void TauSpinnerTableProducer::initialize() {
  // Initialize TauSpinner
  Tauolapp::Tauola::setNewCurrents(0);
  Tauolapp::Tauola::initialize();
  LHAPDF::initPDFSetByName(tauSpinnerPDF_);
  TauSpinner::initialize_spinner(ipp_, ipol_, nonSM2_, nonSMN_, cmsE_);
}

void TauSpinnerTableProducer::produce(edm::Event &event, const edm::EventSetup &setup) {
  // Input gen-particles collection
  auto const &genParts = event.get(genPartsToken_);

  // Output table
  auto wtTable = std::make_unique<nanoaod::FlatTable>(1, branch_, true);
  wtTable->setDoc("TauSpinner weights");

  // Search for boson
  bool foundBoson = false;
  reco::GenParticle boson = getBoson(genParts, foundBoson);
  if (!foundBoson) {  //boson not found, produce empty table (expected for non HTT sample)
    event.put(std::move(wtTable));
    return;
  }

  // Search dor taus from boson decay
  reco::GenParticleRefVector taus;
  getTaus(taus, boson);
  if (taus.size() != 2) {  //boson does not decay to tau pair, produce empty table (expected for non HTT sample)
    event.put(std::move(wtTable));
    return;
  }

  // Tau daughters from boson decay
  reco::GenParticleRefVector tau1_daughters;
  reco::GenParticleRefVector tau2_daughters;
  unsigned type1 = 0;
  unsigned type2 = 0;
  getTauDaughters(tau1_daughters, type1, *taus[0]);
  getTauDaughters(tau2_daughters, type2, *taus[1]);

  //convert particles to TauSpinner format
  TauSpinner::SimpleParticle simple_boson = convertToSimplePart(boson);
  TauSpinner::SimpleParticle simple_tau1 = convertToSimplePart(*taus[0]);
  TauSpinner::SimpleParticle simple_tau2 = convertToSimplePart(*taus[1]);
  std::vector<TauSpinner::SimpleParticle> simple_tau1_daughters;
  std::vector<TauSpinner::SimpleParticle> simple_tau2_daughters;
  for (auto daughterRef : tau1_daughters)
    simple_tau1_daughters.push_back(convertToSimplePart(*daughterRef));
  for (auto daughterRef : tau2_daughters)
    simple_tau2_daughters.push_back(convertToSimplePart(*daughterRef));

  // Compute TauSpinner weights and fill table
  double weight = 0;
  for (const auto &theta : theta_vec_) {
    // Can make this more general by having boson pdgid as input or have option for set boson type
    TauSpinner::setHiggsParametersTR(-cos(2 * M_PI * theta.second),
                                     cos(2 * M_PI * theta.second),
                                     -sin(2 * M_PI * theta.second),
                                     -sin(2 * M_PI * theta.second));
    Tauolapp::Tauola::setNewCurrents(0);
    weight = TauSpinner::calculateWeightFromParticlesH(
        simple_boson, simple_tau1, simple_tau2, simple_tau1_daughters, simple_tau2_daughters);
    wtTable->addColumnValue<double>(
        "weight_cp_" + theta.first, weight, "TauSpinner weight for theta_CP=" + theta.first);
    // also add weights for alternative hadronic currents (can be used for uncertainty estimates)
    Tauolapp::Tauola::setNewCurrents(1);
    weight = TauSpinner::calculateWeightFromParticlesH(
        simple_boson, simple_tau1, simple_tau2, simple_tau1_daughters, simple_tau2_daughters);
    wtTable->addColumnValue<double>(
        "weight_cp_" + theta.first + "_alt",
        weight,
        "TauSpinner weight for theta_CP=" + theta.first + " (alternative hadronic currents)");
  }

  event.put(std::move(wtTable));
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(TauSpinnerTableProducer);
