import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var, CandVars, ExtVar
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
  for deep_tau_ver in [ "2017v2p1", "2018v2p5", "2018v2p5noDA" ]:
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
    cuts.append(f"(?isTauIDAvailable('byUTagCHSVS{vs}raw')?tauID('byUTagCHSVS{vs}raw'):-1) > {score}")
  utagCHSCut = "(" + " && ".join(cuts) + ")"

  cuts = []
  for vs, score in [ ("jet", 0.05) ]: # [ ("e", 0.05), ("mu", 0.05), ("jet", 0.05) ]:
    cuts.append(f"(?isTauIDAvailable('byUTagPUPPIVS{vs}raw')?tauID('byUTagPUPPIVS{vs}raw'):-1) > {score}")
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

def customizeBoostedTaus(process):
  cuts = []
  for vs, score in [ ("jet", 0.72), ("e", 0.05), ("mu", 0.001) ]:
    cuts.append(f"tauID('byBoostedDeepTau20161718v2p0VS{vs}raw') > {score}")
  deepTauCut = "(" + " && ".join(cuts) + ")"

  process.finalBoostedTaus.cut = f"pt > 18 && tauID(\'decayModeFindingNewDMs\') && ( {deepTauCut} )"

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

def addIPCovToLeptons(process,lepton='all'):
  xyz = [ 'x', 'y', 'z' ]
  inputs = [ ('e', 'electron'), ('mu', 'muon'), ('tau', 'tau') ]
  for input_obj, input_col in inputs:
    if (lepton == input_obj or lepton == 'all') and hasattr(process, f'{input_col}TimeLifeInfoTable'):
      tag = cms.InputTag(f'{input_col}TimeLifeInfos')
      varPSet = getattr(process, f'{input_col}TimeLifeInfoTable').externalTypedVariables
      for i in range(len(xyz)):
        for j in range(i, len(xyz)):
            setattr(varPSet, f'IP_cov{j}{i}', cms.PSet(
              doc = cms.string(f'IP covariance element ({j}, {i})'),
              expr = cms.string(f'ipCovariance.c{xyz[j]}{xyz[i]}()'),
              lazyEval = cms.untracked.bool(False),
              precision = cms.int32(10),
              src = tag,
              type = cms.string('float')
            ))
  return process

# adapted from https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/custom_btv_cff.py
def addPFCands(process, allPF = False, addAK4=False, addAK8=False):
    process.customizedPFCandsTask = cms.Task()
    process.schedule.associate(process.customizedPFCandsTask)

    process.finalJetsAK8Constituents = cms.EDProducer("PatJetConstituentPtrSelector",
                                            src = cms.InputTag("finalJetsAK8"),
                                            cut = cms.string("")
                                            )
    process.finalJetsAK4Constituents = cms.EDProducer("PatJetConstituentPtrSelector",
                                            src = cms.InputTag("finalJetsPuppi"),
                                            cut = cms.string("abs(eta) > 2.5")
                                            )
    if allPF:
        candInput = cms.InputTag("packedPFCandidates")
    elif not addAK8:
        candList = cms.VInputTag(cms.InputTag("finalJetsAK4Constituents", "constituents"))
        process.customizedPFCandsTask.add(process.finalJetsAK4Constituents)
        process.finalJetsConstituentsTable = cms.EDProducer("PackedCandidatePtrMerger", src = candList, skipNulls = cms.bool(True), warnOnSkip = cms.bool(True))
        candInput = cms.InputTag("finalJetsConstituentsTable")
    elif not addAK4:
        candList = cms.VInputTag(cms.InputTag("finalJetsAK8Constituents", "constituents"))
        process.customizedPFCandsTask.add(process.finalJetsAK8Constituents)
        process.finalJetsConstituentsTable = cms.EDProducer("PackedCandidatePtrMerger", src = candList, skipNulls = cms.bool(True), warnOnSkip = cms.bool(True))
        candInput = cms.InputTag("finalJetsConstituentsTable")
    else:
        candList = cms.VInputTag(cms.InputTag("finalJetsAK4Constituents", "constituents"), cms.InputTag("finalJetsAK8Constituents", "constituents"))
        process.customizedPFCandsTask.add(process.finalJetsAK4Constituents)
        process.customizedPFCandsTask.add(process.finalJetsAK8Constituents)
        process.finalJetsConstituentsTable = cms.EDProducer("PackedCandidatePtrMerger", src = candList, skipNulls = cms.bool(True), warnOnSkip = cms.bool(True))
        candInput = cms.InputTag("finalJetsConstituentsTable")

    process.customConstituentsExtTable = cms.EDProducer("SimplePATCandidateFlatTableProducer",
                                                        src = candInput,
                                                        cut = cms.string(""), #we should not filter after pruning
                                                        name = cms.string("PFCands"),
                                                        doc = cms.string("interesting particles from AK4 and AK8 jets"),
                                                        singleton = cms.bool(False), # the number of entries is variable
                                                        extension = cms.bool(False), # this is the extension table for the AK8 constituents
                                                        variables = cms.PSet(CandVars,
                                                            puppiWeight = Var("puppiWeight()", float, doc="Puppi weight",precision=10),
                                                            puppiWeightNoLep = Var("puppiWeightNoLep()", float, doc="Puppi weight removing leptons",precision=10),
                                                            vtxChi2 = Var("?hasTrackDetails()?vertexChi2():-1", float, doc="vertex chi2",precision=10),
                                                            trkChi2 = Var("?hasTrackDetails()?pseudoTrack().normalizedChi2():-1", float, doc="normalized trk chi2", precision=10),
                                                            dz = Var("?hasTrackDetails()?dz():-1", float, doc="pf dz", precision=10),
                                                            dzErr = Var("?hasTrackDetails()?dzError():-1", float, doc="pf dz err", precision=10),
                                                            d0 = Var("?hasTrackDetails()?dxy():-1", float, doc="pf d0", precision=10),
                                                            d0Err = Var("?hasTrackDetails()?dxyError():-1", float, doc="pf d0 err", precision=10),
                                                            pvAssocQuality = Var("pvAssociationQuality()", int, doc="primary vertex association quality. 0: NotReconstructedPrimary, 1: OtherDeltaZ, 4: CompatibilityBTag, 5: CompatibilityDz, 6: UsedInFitLoose, 7: UsedInFitTight"),
                                                            lostInnerHits = Var("lostInnerHits()", int, doc="lost inner hits. -1: validHitInFirstPixelBarrelLayer, 0: noLostInnerHits, 1: oneLostInnerHit, 2: moreLostInnerHits"),
                                                            lostOuterHits = Var("?hasTrackDetails()?pseudoTrack().hitPattern().numberOfLostHits('MISSING_OUTER_HITS'):0", int, doc="lost outer hits"),
                                                            numberOfHits = Var("numberOfHits()", int, doc="number of hits"),
                                                            numberOfPixelHits = Var("numberOfPixelHits()", int, doc="number of pixel hits"),
                                                            trkQuality = Var("?hasTrackDetails()?pseudoTrack().qualityMask():0", int, doc="track quality mask"),
                                                            trkHighPurity = Var("?hasTrackDetails()?pseudoTrack().quality('highPurity'):0", bool, doc="track is high purity"),
                                                            trkAlgo = Var("?hasTrackDetails()?pseudoTrack().algo():-1", int, doc="track algorithm"),
                                                            trkP = Var("?hasTrackDetails()?pseudoTrack().p():-1", float, doc="track momemtum", precision=-1),
                                                            trkPt = Var("?hasTrackDetails()?pseudoTrack().pt():-1", float, doc="track pt", precision=-1),
                                                            trkEta = Var("?hasTrackDetails()?pseudoTrack().eta():-1", float, doc="track pt", precision=12),
                                                            trkPhi = Var("?hasTrackDetails()?pseudoTrack().phi():-1", float, doc="track phi", precision=12),
                                                            rawCaloFraction = Var("rawCaloFraction", float, doc='rawCaloFraction', precision=10),
                                                            rawHcalFraction = Var("rawHcalFraction", float, doc='rawHcalFraction', precision=10),
                                                            caloFraction = Var("caloFraction", float, doc='caloFraction', precision=10),
                                                            hcalFraction = Var("hcalFraction", float, doc='hcalFraction', precision=10),
                                                         )
                                    )
    kwargs = { }
    import os
    sv_sort = os.getenv('CMSSW_NANOAOD_SV_SORT')
    if sv_sort is not None: kwargs['sv_sort'] = cms.untracked.string(sv_sort)
    pf_sort = os.getenv('CMSSW_NANOAOD_PF_SORT')
    if pf_sort is not None: kwargs['pf_sort'] = cms.untracked.string(pf_sort)
    process.customAK8ConstituentsTable = cms.EDProducer("PatJetConstituentTableProducer",
                                                        candidates = candInput,
                                                        jets = cms.InputTag("finalJetsAK8"),
                                                        jet_radius = cms.double(0.8),
                                                        name = cms.string("FatJetPFCands"),
                                                        idx_name = cms.string("pFCandsIdx"),
                                                        nameSV = cms.string("FatJetSVs"),
                                                        idx_nameSV = cms.string("sVIdx"),
                                                        **kwargs,
                                                        )
    process.customAK4ConstituentsTable = cms.EDProducer("PatJetConstituentTableProducer",
                                                        candidates = candInput,
                                                        jets = cms.InputTag("finalJetsPuppi"), # was finalJets before
                                                        jet_radius = cms.double(0.4),
                                                        name = cms.string("JetPFCands"),
                                                        idx_name = cms.string("pFCandsIdx"),
                                                        nameSV = cms.string("JetSVs"),
                                                        idx_nameSV = cms.string("sVIdx"),
                                                        **kwargs,
                                                        )
    process.customizedPFCandsTask.add(process.customConstituentsExtTable)

    if not allPF:
        process.customizedPFCandsTask.add(process.finalJetsConstituentsTable)
    # linkedObjects are WIP for Run3
    if addAK8:
        process.customizedPFCandsTask.add(process.customAK8ConstituentsTable)
    if addAK4:
        process.customizedPFCandsTask.add(process.customAK4ConstituentsTable)


    return process

# adapted from https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/custom_jme_cff.py
def addPileUpJetIDVars(proc, jetName="", jetSrc="", jetTableName="", jetTaskName=""):
  """
  Setup modules to calculate pileup jet ID input variables for PF jet
  """

  PUIDVARS = cms.PSet(
    puId_dR2Mean    = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_dR2Mean'):-1",float,doc="pT^2-weighted average square distance of jet constituents from the jet axis (PileUp ID BDT input variable)", precision=14),
    puId_majW       = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_majW'):-1",float,doc="major axis of jet ellipsoid in eta-phi plane (PileUp ID BDT input variable)", precision=14),
    puId_minW       = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_minW'):-1",float,doc="minor axis of jet ellipsoid in eta-phi plane (PileUp ID BDT input variable)", precision=14),
    puId_frac01     = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_frac01'):-1",float,doc="fraction of constituents' pT contained within dR <0.1 (PileUp ID BDT input variable)", precision=14),
    puId_frac02     = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_frac02'):-1",float,doc="fraction of constituents' pT contained within 0.1< dR <0.2 (PileUp ID BDT input variable)", precision=14),
    puId_frac03     = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_frac03'):-1",float,doc="fraction of constituents' pT contained within 0.2< dR <0.3 (PileUp ID BDT input variable)", precision=14),
    puId_frac04     = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_frac04'):-1",float,doc="fraction of constituents' pT contained within 0.3< dR <0.4 (PileUp ID BDT input variable)", precision=14),
    puId_ptD        = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_ptD'):-1",float,doc="pT-weighted average pT of constituents (PileUp ID BDT input variable)", precision=14),
    puId_beta       = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_beta'):-1",float,doc="fraction of pT of charged constituents associated to PV (PileUp ID BDT input variable)", precision=14),
    puId_pull       = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_pull'):-1",float,doc="magnitude of pull vector (PileUp ID BDT input variable)", precision=14),
    puId_jetR       = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_jetR'):-1",float,doc="fraction of jet pT carried by the leading constituent (PileUp ID BDT input variable)", precision=14),
    puId_jetRchg    = Var("?(pt>=10 && abs(eta) > 2.5)?userFloat('puId_jetRchg'):-1",float,doc="fraction of jet pT carried by the leading charged constituent (PileUp ID BDT input variable)", precision=14),
    puId_nCharged   = Var("?(pt>=10 && abs(eta) > 2.5)?userInt('puId_nCharged'):-1","int16",doc="number of charged constituents (PileUp ID BDT input variable)"),
  )

  from RecoJets.JetProducers.PileupJetID_cfi import pileupJetIdCalculator, pileupJetId
  #
  # Calculate pileup jet ID variables
  #
  puJetIdVarsCalculator = "puJetIdCalculator{}".format(jetName)
  setattr(proc, puJetIdVarsCalculator, pileupJetIdCalculator.clone(
      jets = jetSrc,
      vertexes  = "offlineSlimmedPrimaryVertices",
      inputIsCorrected = True,
      applyJec  = False,
      srcConstituentWeights = "packedpuppi" if "PUPPI" in jetName.upper() else ""
    )
  )
  getattr(proc,jetTaskName).add(getattr(proc, puJetIdVarsCalculator))

  #
  # Get the variables
  #
  puJetIDVar = "puJetIDVar{}".format(jetName)
  setattr(proc, puJetIDVar, cms.EDProducer("PileupJetIDVarProducer",
      srcJet = cms.InputTag(jetSrc),
      srcPileupJetId = cms.InputTag(puJetIdVarsCalculator)
    )
  )
  getattr(proc,jetTaskName).add(getattr(proc, puJetIDVar))

  #
  # Save variables as userFloats and userInts for each jet
  #
  patJetWithUserData = "{}WithUserData".format(jetSrc)
  getattr(proc,patJetWithUserData).userFloats.puId_dR2Mean  = cms.InputTag("{}:dR2Mean".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_majW     = cms.InputTag("{}:majW".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_minW     = cms.InputTag("{}:minW".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_frac01   = cms.InputTag("{}:frac01".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_frac02   = cms.InputTag("{}:frac02".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_frac03   = cms.InputTag("{}:frac03".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_frac04   = cms.InputTag("{}:frac04".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_ptD      = cms.InputTag("{}:ptD".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_beta     = cms.InputTag("{}:beta".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_pull     = cms.InputTag("{}:pull".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_jetR     = cms.InputTag("{}:jetR".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userFloats.puId_jetRchg  = cms.InputTag("{}:jetRchg".format(puJetIDVar))
  getattr(proc,patJetWithUserData).userInts.puId_nCharged   = cms.InputTag("{}:nCharged".format(puJetIDVar))

  #
  # Specfiy variables in the jet table to save in NanoAOD
  #
  getattr(proc,jetTableName).variables.puId_dR2Mean  = PUIDVARS.puId_dR2Mean
  getattr(proc,jetTableName).variables.puId_majW     = PUIDVARS.puId_majW
  getattr(proc,jetTableName).variables.puId_minW     = PUIDVARS.puId_minW
  getattr(proc,jetTableName).variables.puId_frac01   = PUIDVARS.puId_frac01
  getattr(proc,jetTableName).variables.puId_frac02   = PUIDVARS.puId_frac02
  getattr(proc,jetTableName).variables.puId_frac03   = PUIDVARS.puId_frac03
  getattr(proc,jetTableName).variables.puId_frac04   = PUIDVARS.puId_frac04
  getattr(proc,jetTableName).variables.puId_ptD      = PUIDVARS.puId_ptD
  getattr(proc,jetTableName).variables.puId_beta     = PUIDVARS.puId_beta
  getattr(proc,jetTableName).variables.puId_pull     = PUIDVARS.puId_pull
  getattr(proc,jetTableName).variables.puId_jetR     = PUIDVARS.puId_jetR
  getattr(proc,jetTableName).variables.puId_jetRchg  = PUIDVARS.puId_jetRchg
  getattr(proc,jetTableName).variables.puId_nCharged = PUIDVARS.puId_nCharged

  return proc

def addPileUpJetID(proc):
  from RecoJets.JetProducers.PileupJetID_cfi import pileupJetId
  from RecoJets.JetProducers.PileupJetIDParams_cfi import trainingVariables_102X_Eta0To3, trainingVariables_102X_Eta3To5, full_106x_UL17_chs, cutbased
  full_133x_Winter24_puppiv18_wp = cms.PSet(
    # 4 Eta Categories  0-2.5 2.5-2.75 2.75-3.0 3.0-5.0
    # 5 Pt Categories   0-10, 10-20, 20-30, 30-40, 40-50

    #Tight Id
    Pt010_Tight  = cms.vdouble(-1.00, -1.00,  -1.00,  -1.00),
    Pt1020_Tight = cms.vdouble(0.038, 0.219, -0.220, -0.254),
    Pt2030_Tight = cms.vdouble(0.033, 0.060, -0.154, -0.154),
    Pt3040_Tight = cms.vdouble(0.056, 0.103, -0.159, -0.109),
    Pt4050_Tight = cms.vdouble(0.043, 0.127, -0.067, -0.059),

    #Medium Id
    Pt010_Medium  = cms.vdouble(-1.00,  - 1.00,  -1.00,  -1.00),
    Pt1020_Medium = cms.vdouble(-0.200, -0.068, -0.158, -0.384),
    Pt2030_Medium = cms.vdouble(-0.109, -0.179, -0.293, -0.322),
    Pt3040_Medium = cms.vdouble(-0.043, -0.124, -0.259, -0.286),
    Pt4050_Medium = cms.vdouble(-0.034, -0.071, -0.198, -0.235),

    #Loose Id
    Pt010_Loose  = cms.vdouble( -1.00,  -1.00,  -1.00,  -1.00),
    Pt1020_Loose = cms.vdouble(-0.723, -0.392, -0.277, -0.516),
    Pt2030_Loose = cms.vdouble(-0.548, -0.347, -0.313, -0.489),
    Pt3040_Loose = cms.vdouble(-0.413, -0.289, -0.322, -0.438),
    Pt4050_Loose = cms.vdouble(-0.279, -0.219, -0.279, -0.384),
  )
  full_133x_Winter24_puppi_v18_wp = full_106x_UL17_chs.clone(
    JetIdParams = full_133x_Winter24_puppiv18_wp,
    trainings = {0: dict(tmvaWeights   = "RecoJets/JetProducers/data/pileupJetId_133X_Winter24_Eta0p0To2p5_puppiV18_BDT.weights.xml.gz",
                         tmvaVariables = trainingVariables_102X_Eta0To3),
                 1: dict(tmvaWeights   = "RecoJets/JetProducers/data/pileupJetId_133X_Winter24_Eta2p5To2p75_puppiV18_BDT.weights.xml.gz",
                         tmvaVariables = trainingVariables_102X_Eta0To3),
                 2: dict(tmvaWeights   = "RecoJets/JetProducers/data/pileupJetId_133X_Winter24_Eta2p75To3p0_puppiV18_BDT.weights.xml.gz",
                         tmvaVariables = trainingVariables_102X_Eta0To3),
                 3: dict(tmvaWeights   = "RecoJets/JetProducers/data/pileupJetId_133X_Winter24_Eta3p0To5p0_puppiV18_BDT.weights.xml.gz",
                         tmvaVariables = trainingVariables_102X_Eta3To5)
    }
  )
  _puppiV18algos_133X_Winter24 = cms.VPSet(full_133x_Winter24_puppi_v18_wp,cutbased)
  proc.pileupJetIdPuppiWinter24 = pileupJetId.clone(
    jets = "updatedJetsPuppi",
    srcConstituentWeights = "packedpuppi",
    vertexes  = "offlineSlimmedPrimaryVertices",
    inputIsCorrected=True,
    applyJec=False,
    algos = cms.VPSet(_puppiV18algos_133X_Winter24),
  )
  proc.jetPuppiTask.add(proc.pileupJetIdPuppiWinter24)
  proc.updatedJetsPuppiWithUserData.userFloats.puIdDisc = cms.InputTag('pileupJetIdPuppiWinter24:fullDiscriminant')
  proc.jetPuppiTable.variables.puIdDisc = Var("userFloat('puIdDisc')", float, doc="Pileup ID BDT discriminant with 133X Winter24 PuppiV18 training",precision=10)
  return proc

def updateEcalBadCalibFilter(process):
  from PhysicsTools.NanoAOD.globalVariablesTableProducer_cfi import globalVariablesTableProducer

  process.load('RecoMET.METFilters.ecalBadCalibFilter_cfi')
  baddetEcallist = cms.vuint32([838871812])

  process.ecalBadCalibFilterUpdated = cms.EDFilter("EcalBadCalibFilter",
    EcalRecHitSource = cms.InputTag("reducedEgamma:reducedEBRecHits"),
    ecalMinEt        = cms.double(50.),
    baddetEcal    = baddetEcallist,
    taggingMode = cms.bool(True),
    debug = cms.bool(False)
  )

  process.extraFlagsTable = globalVariablesTableProducer.clone(
    variables = cms.PSet(
        Flag_ecalBadCalibFilterUpdated = ExtVar(cms.InputTag("ecalBadCalibFilterUpdated"), bool, doc = "Updated ECal BadCalibration Filter"),
    )
  )

  process.extraFlagsProducersTask.add(process.ecalBadCalibFilterUpdated)
  process.extraFlagsTableTask.add(process.extraFlagsTable)

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
  process = customizeBoostedTaus(process)

  from PhysicsTools.NanoAOD.leptonTimeLifeInfo_common_cff import addTrackVarsToTimeLifeInfo
  process = addTrackVarsToTimeLifeInfo(process)
  process = addIPCovToLeptons(process)

  process = customizePV(process)
  process = addSpinnerWeights(process)
  process = addPFCands(process, allPF=False, addAK4=True, addAK8=False)
  process = addPileUpJetIDVars(process, jetName="updatedJetsPuppi", jetSrc="updatedJetsPuppi", jetTableName="jetPuppiTable", jetTaskName="jetPuppiTask")
  process = addPileUpJetID(process)
  process = updateEcalBadCalibFilter(process)

  return process
