import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var, CandVars
from RecoTauTag.RecoTau.tauIdWPsDefs import WORKING_POINTS_v2p5
from PhysicsTools.NanoAOD.nano_eras_cff import *

# settings which can depend on (nanoAOD) era
era_dependent_settings = cms.PSet(
  cmsE = cms.double(13600.0), #center of mass energy in GeV (Run3 default)
)
(~run3_common).toModify(era_dependent_settings, cmsE = 13000.0)

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
  for vs, score in [ ("jet", 0.05) ]: # [ ("e", 0.05), ("mu", 0.05), ("jet", 0.05) ]:
    cuts.append(f"tauID('byUTagCHSVS{vs}raw') > {score}")
  utagCHSCut = "(" + " && ".join(cuts) + ")"

  cuts = []
  for vs, score in [ ("jet", 0.05) ]: # [ ("e", 0.05), ("mu", 0.05), ("jet", 0.05) ]:
    cuts.append(f"tauID('byUTagPUPPIVS{vs}raw') > {score}")
  utagPUPPICut = "(" + " && ".join(cuts) + ")"

  process.finalTaus.cut = f"pt > 18 && ( {deepTauCut} || {utagCHSCut} || {utagPUPPICut} )"

  process.tauTable.variables.dxyErr = Var("dxy_error", float, doc="dxy error", precision=10)
  process.tauTable.variables.ip3d = Var("ip3d", float, doc="3D impact parameter", precision=10)
  process.tauTable.variables.ip3dErr = Var("ip3d_error", float, doc="3D impact parameter error", precision=10)
  process.tauTable.variables.hasSV = Var("hasSecondaryVertex", bool, doc="has secondary vertex")
  process.tauTable.variables.flightLengthX = Var("flightLength().x()", float, doc="flight length x", precision=10)
  process.tauTable.variables.flightLengthY = Var("flightLength().y()", float, doc="flight length y", precision=10)
  process.tauTable.variables.flightLengthZ = Var("flightLength().z()", float, doc="flight length z", precision=10)
  process.tauTable.variables.flightLengthSig = Var("flightLengthSig()", float, doc="flight length significance", precision=10)

  process.tauTable.variables.dzErr = Var("?leadChargedHadrCand.isNonnull() && leadChargedHadrCand.hasTrackDetails()?leadChargedHadrCand.dzError(): 0/0.", float, doc="dz error", precision=10, lazyEval=True)
  process.tauTable.variables.leadTkNormChi2 = Var("leadingTrackNormChi2()", float, doc="normalized chi2 of the leading track", precision=10)
  process.tauTable.variables.leadChCandEtaAtEcalEntrance = Var("etaAtEcalEntranceLeadChargedCand", float, doc="eta of the leading charged candidate at the entrance of the ECAL", precision=10)

  return process

def customizePV(process):
  from PhysicsTools.NanoAOD.leptonTimeLifeInfo_common_cff import addExtendVertexInfo
  addExtendVertexInfo(process)

  #for backward compatibility (different table name, chi2 instead of normChi2)
  #process.refittedPV.useEleKfTracks = False
  #process.pvbsTable.variables.chi2 = Var("chi2()", float, doc = "chi2", precision = 8)

  process.pvbsTable.variables.ndof = Var("ndof()", float, doc = "number of degrees of freedom", precision = 8)
  process.pvbsTable.variables.valid = Var("isValid()", bool, doc = "PV fit is valid")

  return process

def addSpinnerWeights(process):
  process.tauSpinnerWeightTable = cms.EDProducer(
    "TauSpinnerTableProducer",
    branch   = cms.string("TauSpinner"),
    input    = cms.InputTag("prunedGenParticles"),
    theta    = cms.vdouble(0,0.25,0.5,-0.25,0.375),
    pdfSet   = cms.string("NNPDF31_nnlo_hessian_pdfas"),
    cmsE     = era_dependent_settings.cmsE #center of mass energy in GeV
  )
  process.globalTablesMCTask.add(process.tauSpinnerWeightTable)

  return process


def customize(process):
  #customize printout frequency
  maxEvts = process.maxEvents.input.value()
  if maxEvts > 10000 or maxEvts < 0:
    process.MessageLogger.cerr.FwkReport.reportEvery = 1000
  elif maxEvts > 10:
    process.MessageLogger.cerr.FwkReport.reportEvery = maxEvts//10
  #customize stored objects
  process = customizeGenParticles(process)
  process = customizeTaus(process)

  from PhysicsTools.NanoAOD.leptonTimeLifeInfo_common_cff import addTrackVarsToTimeLifeInfo
  process = addTrackVarsToTimeLifeInfo(process)

  process = customizePV(process)

  process = addSpinnerWeights(process)

  return process
