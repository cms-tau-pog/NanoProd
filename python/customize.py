import FWCore.ParameterSet.Config as cms

def customize(process):
    process.MessageLogger.cerr.FwkReport.reportEvery = 100
    process.finalGenParticles.select = cms.vstring(
        "drop *",
        "keep++ abs(pdgId) == 15 & (pt > 15 ||  isPromptDecayed() )",#  keep full tau decay chain for some taus
        "keep+ abs(pdgId) == 15 ",  #  keep first gen decay product for all tau
        "+keep abs(pdgId) == 11 || abs(pdgId) == 13 || abs(pdgId) == 15", #keep leptons, with at most one mother back in the history
        "drop abs(pdgId)= 2212 && abs(pz) > 1000", #drop LHC protons accidentally added by previous keeps
        "keep abs(pdgId) == 23 || abs(pdgId) == 24 || abs(pdgId) == 25",   # keep VIP(articles)s
    )

    return process
