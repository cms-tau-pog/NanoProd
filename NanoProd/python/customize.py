import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var, CandVars
from RecoTauTag.RecoTau.tauIdWPsDefs import WORKING_POINTS_v2p5

def customizeGenParticles(process):
  def pdgOR(pdgs):
    abs_pdgs = [ f'abs(pdgId) == {pdg}' for pdg in pdgs ]
    return '( ' + ' || '.join(abs_pdgs) + ' )'

  leptons = pdgOR([ 11, 12, 13, 14, 15, 16 ])
  important_particles = pdgOR([ 6, 23, 24, 25, 35, 39, 9990012, 9900012, 1000015 ])
  process.finalGenParticles.select = [
    'drop *',
    'keep++ statusFlags().isLastCopy() && ' + leptons,
    '+keep statusFlags().isFirstCopy() && ' + leptons,
    'keep+ statusFlags().isLastCopy() && ' + important_particles,
    '+keep statusFlags().isFirstCopy() && ' + important_particles,
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
  cuts = []
  for vs, score in [ ("e", 0.05), ("mu", 0.05), ("jet", 0.05) ]:
    cuts.append(f"isTauIDAvailable('byPNetVSjetraw')")
    cuts.append(f"tauID('byPNetVS{vs}raw') > {score}")
  pnetCut = "(" + " && ".join(cuts) + ")"

  process.finalTaus.cut = f"pt > 18 && ( {deepTauCut} || {pnetCut} )"

  process.tauTable.variables.dxyErr = Var("dxy_error", float, doc="dxy error", precision=10)
  process.tauTable.variables.ip3d = Var("ip3d", float, doc="3D impact parameter", precision=10)
  process.tauTable.variables.ip3dErr = Var("ip3d_error", float, doc="3D impact parameter error", precision=10)
  process.tauTable.variables.hasSV = Var("hasSecondaryVertex", bool, doc="has secondary vertex")
  process.tauTable.variables.flightLengthX = Var("flightLength().x()", float, doc="flight length x", precision=10)
  process.tauTable.variables.flightLengthY = Var("flightLength().y()", float, doc="flight length y", precision=10)
  process.tauTable.variables.flightLengthZ = Var("flightLength().z()", float, doc="flight length z", precision=10)
  process.tauTable.variables.flightLengthSig = Var("flightLengthSig()", float, doc="flight length significance", precision=10)

  process.tauTable.variables.dzErr = Var("?leadChargedHadrCand.isNonnull() && leadChargedHadrCand.hasTrackDetails()?leadChargedHadrCand.dzError(): 0/0.", float, doc="dz error", precision=10)
  process.tauTable.variables.leadTkNormChi2 = Var("leadingTrackNormChi2()", float, doc="normalized chi2 of the leading track", precision=10)
  process.tauTable.variables.leadChCandEtaAtEcalEntrance = Var("etaAtEcalEntranceLeadChargedCand", float, doc="eta of the leading charged candidate at the entrance of the ECAL", precision=10)

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
        CandVars,
        tauIdx = Var("status", "int16", doc="index of the mother tau"),
    )
  )

  process.tauSignalCandsTask = cms.Task(process.tauSignalCands, process.tauSignalCandsTable)
  process.tauTablesTask.add(process.tauSignalCandsTask)

  process.tauExTable = cms.EDProducer("TauExTableProducer",
    taus = process.tauTable.src,
    precision = cms.int32(10),
  )

  process.tauExTableTask = cms.Task(process.tauExTable)
  process.tauTablesTask.add(process.tauExTableTask)
  return process

def customizePV(process):
  process.vertexBSTable = cms.EDProducer("VertexBSTableProducer",
    pfCands = cms.InputTag("packedPFCandidates"),
    lostTracks = cms.InputTag("lostTracks"),
    beamSpot = cms.InputTag("offlineBeamSpot"),
    precision = cms.int32(10),
  )

  process.vertexBSTableTask = cms.Task(process.vertexBSTable)
  process.vertexTablesTask.add(process.vertexBSTableTask)
  return process

def customize(process):
  process.MessageLogger.cerr.FwkReport.reportEvery = 100
  process = customizeGenParticles(process)
  process = customizeTaus(process)
  process = customizePV(process)
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

  # Embedding filter bits
  # e-leg:
  '''
  process.triggerObjectTable.selections[0].qualityBits = cms.string(
    "filter(’*CaloIdLTrackIdLIsoVL*TrackIso*Filter’) + " \
    "2*filter(’hltEle*WPTight*TrackIsoFilter*’) + " \
    "4*filter(’hltEle*WPLoose*TrackIsoFilter’) + " \
    "8*filter(’*OverlapFilter*IsoEle*PFTau*’) + " \
    "16*filter(’hltEle*Ele*CaloIdLTrackIdLIsoVL*Filter’) + " \
    "32*filter(’hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*’)+ " \
    "64*filter(’hltOverlapFilterIsoEle*PFTau*’) + " \
    "128*filter(’hltEle*Ele*Ele*CaloIdLTrackIdLDphiLeg*Filter’) + " \
    "256*max(filter(’hltL3fL1Mu*DoubleEG*Filtered*’),filter(’hltMu*DiEle*CaloIdLTrackIdLElectronleg* Filter’)) + " \
    "512*max(filter(’hltL3fL1DoubleMu*EG*Filter*’),filter(’hltDiMu*Ele*CaloIdLTrackIdLElectronleg* Filter’)) + " \
    "1024*min(filter(’hltEle32L1DoubleEGWPTightGsfTrackIsoFilter’),filter(’hltEGL1SingleEGOrFilter’) ) + " \
    "2048*filter(’hltEle*CaloIdVTGsfTrkIdTGsfDphiFilter’) + " \
    "4096*path(’HLT_Ele*PFJet*’) + " \
    "8192*max(filter(’hltEG175HEFilter’),filter(’hltEG200HEFilter’)) + " \
    "16384*filter(’hltEle27WPTightGsfTrackIsoFilter’) + " \
    "32768*filter(’hltEle32WPTightGsfTrackIsoFilter’) + " \
    "65536*filter(’hltEle32L1DoubleEGWPTightGsfTrackIsoFilter’) + " \
    "131072*filter(’hltEGL1SingleEGOrFilter’) + " \
    "262144*filter(’hltEle35noerWPTightGsfTrackIsoFilter’) + " \
    "524288*filter(’hltEle24erWPTightGsfTrackIsoFilterForTau’)"
  )
  '''
  # mu-leg:
  '''
  process.triggerObjectTable.selections[2].qualityBits = cms.string(
    "filter(’*RelTrkIsoVVLFiltered0p4’) + " \
    "2*filter(’hltL3crIso*Filtered0p07’) + " \
    "4*filter(’*OverlapFilterIsoMu*PFTau*’) + " \
    "8*max(filter(’hltL3crIsoL1*SingleMu*Filtered0p07’),filter(’hltL3crIsoL1sMu*Filtered0p07’)) + " \
    "16*filter(’hltDiMuon*Filtered*’) + " \
    "32*filter(’hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*’) + " \
    "64*filter(’hltOverlapFilterIsoMu*PFTau*’) + " \
    "128*filter(’hltL3fL1TripleMu*’) + " \
    "256*max(filter(’hltL3fL1DoubleMu*EG*Filtered*’),filter(’hltDiMu*Ele*CaloIdLTrackIdLElectronleg* Filter’)) + " \
    "512*max(filter(’hltL3fL1Mu*DoubleEG*Filtered*’),filter(’hltMu*DiEle*CaloIdLTrackIdLElectronleg* Filter’)) + " \
    "1024*max(filter(’hltL3fL1sMu*L3Filtered50*’),filter(’hltL3fL1sMu*TkFiltered50*’)) + " \
    "2048*max(filter(’hltL3fL1sMu*L3Filtered100*’),filter(’hltL3fL1sMu*TkFiltered100*’)) + " \
    "4096*filter(’hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p07’) + " \
    "8192*filter(’hltL3crIsoL1sMu22Or25L1f0L2f10QL3f27QL3trkIsoFiltered0p07’) + " \
    "16384*filter(’hltL3crIsoL1sMu18erTau24erIorMu20erTau24erL1f0L2f10QL3f20QL3trkIsoFiltered0p07’) + " \
    "32768*filter(’hltL3crIsoBigORMu18erTauXXer2p1L1f0L2f10QL3f20QL3trkIsoFiltered0p07’)"
  )
  '''
  # tau-leg:
  '''
  process.triggerObjectTable.selections[3].sel = cms.string(
    "( type(84) || type(-100) ) && (pt > 5) && coll(’*Tau*’) && " \
    "( filter(’*LooseChargedIso*’) || filter(’*MediumChargedIso*’) || " \
    "filter(’*TightChargedIso*’) || filter(’*TightOOSCPhotons*’) || " \
    "filter(’hltL2TauIsoFilter’) || filter(’*OverlapFilterIsoMu*’) || " \
    "filter(’*OverlapFilterIsoEle*’) || filter(’*L1HLTMatched*’) || " \
    "filter(’*Dz02*’) || filter(’*DoublePFTau*’) || " \
    "filter(’*SinglePFTau*’) || filter(’hlt*SelectedPFTau’) || " \
    "filter(’*DisplPFTau*’) || filter(’*Tau*’) )"
  )
  process.triggerObjectTable.selections[3].qualityBits = cms.string(
    "filter(’*LooseChargedIso*’) + " \
    "2*filter(’*MediumChargedIso*’) + " \
    "4*filter(’*TightChargedIso*’) + " \
    "8*filter(’*TightOOSCPhotons*’) + " \
    "16*filter(’*Hps*’) + " \
    "32*filter(’hltSelectedPFTau*MediumChargedIsolationL1HLTMatched*’) + " \
    "64*filter(’hltDoublePFTau*TrackPt1*ChargedIsolation*Dz02Reg’) + " \
    "128*filter(’hltOverlapFilterIsoEle*PFTau*’) + " \
    "256*filter(’hltOverlapFilterIsoMu*PFTau*’) + " \
    "512*filter(’hltDoublePFTau*TrackPt1*ChargedIsolation*’) + " \
    "1024*filter(’hltL1sBigORLooseIsoEGXXerIsoTauYYerdRMin0p3’) + " \
    "2048*filter(’hltL1sMu18erTau24erIorMu20erTau24er’) + " \
    "4096*filter(’hltL1sBigORMu18erTauXXer2p1’) + " \
    "8192*filter(’hltDoubleL2IsoTau26eta2p2’)"
  )
  '''

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
