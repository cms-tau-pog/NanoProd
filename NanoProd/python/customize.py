import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var, P3Vars
from RecoTauTag.RecoTau.tauIdWPsDefs import WORKING_POINTS_v2p5

def customizeGenParticles(process):
  def pdgOR(pdgs):
    abs_pdgs = [ f'abs(pdgId) == {pdg}' for pdg in pdgs ]
    return '( ' + ' || '.join(abs_pdgs) + ' )'

  leptons = pdgOR([ 11, 13, 15 ])
  important_particles = pdgOR([ 6, 23, 24, 25, 35, 39, 9990012, 9900012, 1000015 ])
  process.finalGenParticles.select = [
    'drop *',
    'keep++ statusFlags().isLastCopy() && ' + leptons,
    '+keep statusFlags().isFirstCopy() && ' + leptons,
    'keep+ statusFlags().isLastCopy() && ' + important_particles,
    '+keep statusFlags().isFirstCopy() && ' + important_particles,
    'keep abs(pdgId) == 12 || abs(pdgId) == 14 || abs(pdgId) == 16', # keep neutrinos
    '+keep pdgId == 22 && status == 1 && (pt > 10 || isPromptFinalState())', # keep photons
    'keep statusFlags().fromHardProcess() && statusFlags().isLastCopy()', # keep hard process particles
    "drop abs(pdgId) == 2212 && abs(pz) > 1000", #drop LHC protons accidentally added by previous keeps
  ]

  for coord in [ 'x', 'y', 'z']:
    setattr(process.genParticleTable.variables, 'v'+ coord,
            Var(f'vertex().{coord}', float, precision=10,
                doc=f'{coord} coordinate of the gen particle production vertex'))

  return process

def customizeTaus(process):
  deepTauCuts = []
  for deep_tau_ver in [ "2017v2p1", "2018v2p5" ]:
    cuts = []
    e_VVVLoose = WORKING_POINTS_v2p5["e"]["VVVLoose"]
    mu_VVLoose = 0.05
    jet_VVVLoose = WORKING_POINTS_v2p5["jet"]["VVVLoose"]
    for vs, wp, score in [ ("e", "VVVLoose", e_VVVLoose), ("mu", None, mu_VVLoose), ("jet", "VVVLoose", jet_VVVLoose) ]:
      if deep_tau_ver == "2018v2p5" or wp is None:
        cuts.append(f"tauID('byDeepTau{deep_tau_ver}VS{vs}raw') > {score}")
      else:
        cuts.append(f"tauID('by{wp}DeepTau{deep_tau_ver}VS{vs}')")
    cut = "(" + " && ".join(cuts) + ")"
    deepTauCuts.append(cut)
  deepTauCut = "(tauID('decayModeFindingNewDMs') > 0.5 && (" + " || ".join(deepTauCuts) + "))"
  pnetCut = "( isTauIDAvailable('byPNetVSjetraw') && tauID('byPNetVSjetraw') > 0.05 )"

  process.finalTaus.cut = f"pt > 18 && ( {deepTauCut} || {pnetCut} )"

  process.tauSignalCands = cms.EDProducer("PATTauSignalCandidatesProducer",
    src = process.tauTable.src,
    storeLostTracks = cms.bool(True)
  )

  from PhysicsTools.NanoAOD.simpleCandidateFlatTableProducer_cfi import simpleCandidateFlatTableProducer
  process.tauSignalCandsTable = simpleCandidateFlatTableProducer.clone(
    src = cms.InputTag("tauSignalCands"),
    cut = cms.string("pt > 0."),
    name = cms.string("TauProd"),
    doc = cms.string("tau signal candidates"),
    variables = cms.PSet(
        P3Vars,
        pdgId = Var("pdgId", int, doc="PDG code assigned by the event reconstruction (not by MC truth)"),
        tauIdx = Var("status", "int16", doc="index of the mother tau"),
        #trkPt = Var("?daughter(0).hasTrackDetails()?daughter(0).bestTrack().pt():0", float, precision=-1, doc="pt of associated track"), #MB: better to store ratio over cand pt?
    )
  )

  process.tauSignalCandsTask = cms.Task(process.tauSignalCands, process.tauSignalCandsTable)
  process.tauTablesTask.add(process.tauSignalCandsTask)
  return process

def customize(process):
  process.MessageLogger.cerr.FwkReport.reportEvery = 100
  process = customizeGenParticles(process)
  process = customizeTaus(process)
  return process
