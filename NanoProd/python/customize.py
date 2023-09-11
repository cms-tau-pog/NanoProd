import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var
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
    mu_VLoose = WORKING_POINTS_v2p5["mu"]["VLoose"]
    jet_VVVLoose = WORKING_POINTS_v2p5["jet"]["VVVLoose"]
    for vs, wp, score in [ ("e", "VVVLoose", e_VVVLoose), ("mu", "VLoose", mu_VLoose), ("jet", "VVVLoose", jet_VVVLoose) ]:
      if deep_tau_ver == "2018v2p5":
        cuts.append(f"tauID('byDeepTau{deep_tau_ver}VS{vs}raw') > {score}")
      else:
        cuts.append(f"tauID('by{wp}DeepTau{deep_tau_ver}VS{vs}')")
    cut = "(" + " && ".join(cuts) + ")"
    deepTauCuts.append(cut)
  deepTauCut = "(tauID('decayModeFindingNewDMs') > 0.5 && (" + " || ".join(deepTauCuts) + "))"
  pnetCut = "( isTauIDAvailable('byPNetVSjetraw') && tauID('byPNetVSjetraw') > 0.05 )"

  process.finalTaus.cut = f"pt > 18 && ( {deepTauCut} || {pnetCut} )"
  return process

def customize(process):
  process.MessageLogger.cerr.FwkReport.reportEvery = 100
  process = customizeGenParticles(process)
  process = customizeTaus(process)
  return process

def customizeEmbedding(process):
  # Add missing "BadPFMuonDz" and "hfNoisyHits" MET filter
  from RecoMET.METFilters.BadPFMuonDzFilter_cfi import BadPFMuonDzFilter
  process.BadPFMuonFilterUpdateDz=BadPFMuonDzFilter.clone(
    muons = cms.InputTag("slimmedMuons"),
    vtx   = cms.InputTag("offlineSlimmedPrimaryVertices"),
    PFCandidates = cms.InputTag("packedPFCandidates"),
    minDzBestTrack = cms.double(0.5),
    taggingMode    = cms.bool(True)
  )
  process.BadPFMuonFilterUpdateDz_step = cms.Path(process.BadPFMuonFilterUpdateDz)
  from RecoMET.METFilters.metFilters_cff import hfNoisyHitsFilter
  process.hfNoisyHitsFilter=hfNoisyHitsFilter.clone(
    hfrechits = cms.InputTag("slimmedHcalRecHits:reducedHcalRecHits")
  )
  process.hfNoisyHitsFilter_step = cms.Path(process.hfNoisyHitsFilter)
  process.schedule.insert(0,process.BadPFMuonFilterUpdateDz_step)
  process.schedule.insert(1,process.hfNoisyHitsFilter_step)
  process.extraFlagsTable = cms.EDProducer("GlobalVariablesTableProducer",
      extension = cms.bool(False),
      mightGet = cms.optional.untracked.vstring,
      name = cms.string(''),
      variables = cms.PSet(
          Flag_BadPFMuonDzFilter = cms.PSet(
              doc = cms.string('Bad PF muon Dz flag'),
              precision = cms.int32(-1),
              src = cms.InputTag("BadPFMuonFilterUpdateDz"),
              type = cms.string('bool')
          ),
          Flag_hfNoisyHitsFilter = cms.PSet(
              doc = cms.string('HF noisy hits flag'),
              precision = cms.int32(-1),
              src = cms.InputTag("hfNoisyHitsFilter"),
              type = cms.string('bool')
          )
      )
  )
  process.extraFlagsTableTask = cms.Task(process.extraFlagsTable) # This is already integrated in process.nanoSequenceCommon

  # Define sequence
  process.nanoAOD_step = cms.Path( cms.Sequence( process.nanoSequenceCommon + process.nanoSequenceOnlyData + process.nanoSequenceOnlyFullSim + cms.Sequence(cms.Task(process.genParticleTask, process.particleLevelTask, process.jetMCTaskak4, process.muonMCTask, process.electronMCTask, process.photonMCTask, process.tauMCTask, process.boostedTauMCTask, process.ttbarCatMCProducersTask, process.globalTablesMCTask, process.genWeightsTableTask, process.genVertexTablesTask, process.genParticleTablesTask, process.particleLevelTablesTask)) ) )

  process.linkedObjects.lowPtElectrons = cms.InputTag("finalElectrons")
  process.jetMCTaskak4.remove(process.genJetFlavourTable)
  process.nanoSequenceCommon.remove(process.lowPtElectronTablesTask)
  process.globalTablesMCTask.remove(process.genFilterTable)

  # Get embedded data
  process.unpackedPatTrigger.triggerResults = cms.InputTag("TriggerResults::SIMembeddingHLT")
  process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_SIMembeddingHLT")
  process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_MERGE")
  process.NANOAODSIMoutput.outputCommands.remove("keep edmTriggerResults_*_*_*")
  process.genParticles2HepMC.genEventInfo = cms.InputTag("generator", "", "SIMembeddingpreHLT")
  process.puppiMetTable.src = cms.InputTag("slimmedMETsPuppi", "", "RERUNPUPPI")
  process.rawPuppiMetTable.src = cms.InputTag("slimmedMETsPuppi", "", "RERUNPUPPI")
  process.updatedJetsPuppi.jetSource = cms.InputTag("slimmedJetsPuppi", "", "MERGE")
  process.jetPuppiCorrFactorsNano.src = cms.InputTag("slimmedJetsPuppi", "", "MERGE")

  # Add HF jet shape info (https://github.com/cms-sw/cmssw/blob/CMSSW_10_6_30/PhysicsTools/NanoAOD/python/jets_cff.py#L741-L759)
  from RecoJets.JetProducers.hfJetShowerShape_cfi import hfJetShowerShape
  process.hfJetShowerShapeforNanoAOD = hfJetShowerShape.clone(jets="updatedJets",vertices="offlineSlimmedPrimaryVertices")
  process.updatedJetsWithUserData.userFloats.hfsigmaEtaEta = cms.InputTag('hfJetShowerShapeforNanoAOD:sigmaEtaEta')
  process.updatedJetsWithUserData.userFloats.hfsigmaPhiPhi = cms.InputTag('hfJetShowerShapeforNanoAOD:sigmaPhiPhi')
  process.updatedJetsWithUserData.userInts.hfcentralEtaStripSize = cms.InputTag('hfJetShowerShapeforNanoAOD:centralEtaStripSize')
  process.updatedJetsWithUserData.userInts.hfadjacentEtaStripsSize = cms.InputTag('hfJetShowerShapeforNanoAOD:adjacentEtaStripsSize')
  process.jetTable.variables.hfsigmaEtaEta = Var("userFloat('hfsigmaEtaEta')",float,doc="sigmaEtaEta for HF jets (noise discriminating variable)",precision=10)
  process.jetTable.variables.hfsigmaPhiPhi = Var("userFloat('hfsigmaPhiPhi')",float,doc="sigmaPhiPhi for HF jets (noise discriminating variable)",precision=10)
  process.jetTable.variables.hfcentralEtaStripSize = Var("userInt('hfcentralEtaStripSize')", int, doc="eta size of the central tower strip in HF (noise discriminating variable) ")
  process.jetTable.variables.hfadjacentEtaStripsSize = Var("userInt('hfadjacentEtaStripsSize')", int, doc="eta size of the strips next to the central tower strip in HF (noise discriminating variable) ")
  _jetTask_rerunHFshowershape = process.jetTask.copy()
  _jetTask_rerunHFshowershape.add(process.hfJetShowerShapeforNanoAOD)
  process.jetTask = _jetTask_rerunHFshowershape

  process = customize(process)
  return process
