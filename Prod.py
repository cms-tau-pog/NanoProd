# Crab wrapper.

import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing


options = VarParsing('analysis')
options.register('sampleType', '', VarParsing.multiplicity.singleton, VarParsing.varType.string,
                 "Indicates the sample type: data or mc")
options.register('era', '', VarParsing.multiplicity.singleton, VarParsing.varType.string,
                 "Indicates era: Run2_2016_HIPM, Run2_2016, Run2_2017, Run2_2018")

options.parseArguments()

cond_mc = {
    'Run2_2016_HIPM': 'auto:run2_mc_pre_vfp',
    'Run2_2016': 'auto:run2_mc',
    'Run2_2017': 'auto:phase1_2017_realistic',
    'Run2_2018': 'auto:phase1_2018_realistic',
}
cond_data = 'auto:run2_data'

if options.sampleType == 'data':
    cond = cond_data
elif options.sampleType == 'mc':
    cond = cond_mc[options.era]
else:
    raise RuntimeError(f"Unknown sample type {options.sampleType}")

process = cms.Process('NanoProd')

process.source = cms.Source("PoolSource", fileNames = cms.untracked.vstring(options.inputFiles))
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(-1))
process.options = cms.untracked.PSet(wantSummary = cms.untracked.bool(False))
process.exParams = cms.untracked.PSet(
    sampleType = cms.untracked.string(options.sampleType),
    era = cms.untracked.string(options.era),
    cond = cms.untracked.string(cond),
)

with open('PSet.py', 'w') as f:
    print(process.dumpPython(), file=f)
