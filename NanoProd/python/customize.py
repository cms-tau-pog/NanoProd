import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import Var

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
    for vs, wp, score in [ ("e", "VVVLoose", "0.099"), ("mu", "VLoose","0.2949"), ("jet", "VVVLoose","0.4083") ]:
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
