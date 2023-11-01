import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var, P3Vars
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
        P3Vars,
        pdgId = Var("pdgId", int, doc="PDG code assigned by the event reconstruction (not by MC truth)"),
        tauIdx = Var("status", "int16", doc="index of the mother tau"),
        #trkPt = Var("?daughter(0).hasTrackDetails()?daughter(0).bestTrack().pt():0", float, precision=-1, doc="pt of associated track"), #MB: better to store ratio over cand pt?
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
