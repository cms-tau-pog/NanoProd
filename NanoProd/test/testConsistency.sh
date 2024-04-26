#!/bin/bash

if ! [ -d "$ANALYSIS_PATH" ]; then
  echo "ANALYSIS_PATH is not set. Exiting."
  exit 1
fi
cd $ANALYSIS_PATH

echo "Checking Run2_2016 consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2016[FGH]-UL2016_MiniAODv2-v[1-9]/MINIAOD' NanoProd/crab/Run2_2016/*.yaml

echo "Checking Run2_2016_HIPM consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/RunIISummer20UL16MiniAODAPVv2-106X_mcRun2_asymptotic_preVFP_v11(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2016(B-ver2_|[C-F]-)HIPM_UL2016_MiniAODv2-v[1-9]/MINIAOD' NanoProd/crab/Run2_2016_HIPM/*.yaml

echo "Checking Run2_2017 consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2017[B-F]-UL2017_MiniAODv2-v[1-9]/MINIAOD' NanoProd/crab/Run2_2017/*.yaml

echo "Checking Run2_2018 consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2018[A-D]-UL2018_MiniAODv2_GT36-v[1-9]/MINIAOD' NanoProd/crab/Run2_2018/*.yaml

echo "Checking Run3_2022 consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2022[CD]-22Sep2023-v[1-9]/MINIAOD' NanoProd/crab/Run3_2022/*.yaml

echo "Checking Run3_2022EE consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/Run3Summer22EEMiniAODv4-(forPOG_|)130X_mcRun3_2022_realistic_postEE_v6(_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2022[EFG]-22Sep2023-v[1-9]/MINIAOD' NanoProd/crab/Run3_2022EE/*.yaml

echo "Checking Run3_2023 consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/Run3Summer23MiniAODv4-(tsg_|)130X_mcRun3_2023_realistic_v1[45](_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2023C-22Sep2023_v[1-9]-v[1-9]/MINIAOD' NanoProd/crab/Run3_2023/*.yaml

echo "Checking Run3_2023BPix consistency..."
python RunKit/checkTasksConsistency.py --dataset-name-mask-mc '^/.*/Run3Summer23BPixMiniAODv4-(tsg_|)130X_mcRun3_2023_realistic_postBPix_v[26](_ext[1-9]|)-v[1-9]/MINIAODSIM' --dataset-name-mask-data '^/.*/Run2023D-22Sep2023_v[1-9]-v[1-9]/MINIAOD' NanoProd/crab/Run3_2023BPix/*.yaml

echo "Checking cross-era consistency..."
python RunKit/checkTasksConsistency.py --exceptions NanoProd/crab/Sample_exceptions.yaml \
  --name-matching='-:_' \
  --name-matching='_13(p6|)TeV_:_TeV_' \
  --name-matching='DYJetsToLL_M_(.*)_madgraphMLM_:DYto2L_4Jets_MLL_\1_madgraphMLM_' \
  --name-matching='DYJetsToLL_([012])J_(.*)_amcatnloFXFX_:DYto2L_2Jets_MLL_50_\1J_\2_amcatnloFXFX_' \
  --name-matching='DYJetsToLL_M_(50|10to50)_(.*)_amcatnloFXFX_:DYto2L_2Jets_MLL_\1_\2_amcatnloFXFX_' \
  --name-matching='DY([1-4])JetsToLL_M_50_MatchEWPDG20_(.*)_madgraphMLM_:DYto2L_4Jets_MLL_50_\1J_\2_madgraphMLM_' \
  --name-matching='DYJetsToTauTauToMuTauh_:DYto2TautoMuTauh_' \
  --name-matching='ZJetsToNuNu:Zto2Nu_4Jets' \
  --name-matching='_HT_([0-9]+)ToInf_:_HT_\1_' \
  --name-matching='WToTauNu(.*)_tauola:WtoNuTau\1' \
  --name-matching='WJetsToLNu_(.*)_amcatnloFXFX_:WtoLNu_2Jets_\1_amcatnloFXFX_' \
  --name-matching='W([1-4])JetsToLNu_(.*)_madgraphMLM_:WtoLNu_4Jets_\1J_\2_madgraphMLM_' \
  --name-matching='WJetsToLNu_(.*)_madgraphMLM_:WtoLNu_4Jets_\1_madgraphMLM_' \
  --name-matching='TTToSemiLeptonic:TTtoLNu2Q' \
  --name-matching='TTToHadronic:TTto4Q' \
  --name-matching='WWW(.*)_madspin:WWW\1' \
  --name-matching='ST_t_channel_top_4f_InclusiveDecays_:TBbarQ_t_channel_4FS_' \
  --name-matching='ST_t_channel_antitop_4f_InclusiveDecays_:TbarBQ_t_channel_4FS_' \
  --name-matching='_PSWeights:' \
  --name-matching='_M_125:_M125' \
  --name-matching='UncorrelatedDecay_Filtered:UncorrelatedDecay' \
  --name-matching='UncorrelatedDecay_M125(.*)_minnlo:UncorrelatedDecay_M125\1' \
  --name-matching='TuneCP5:CP5' \
  --name-matching='ToTauTau:to2Tau' \
  --name-matching='_jhugen[0-9]+:' \
  --name-matching='_ext[1-9]$:' \
  --name-matching='_madspin_:_' \
  --name-matching='_amcatnloFXFX_:_amcatnlo_' \
  --name-matching='_cp5_narrow_:_narrow_cp5_' \
  --name-matching='_tev_cp5_:_cp5_tev_' \
  --name-matching='ZZTo2Nu2Q:ZZTo2Q2Nu' \
  --name-matching='([WZ])ZTo2Q2L_mllmin4p0_:\1Zto2L2Q_1Jets_' \
  --name-matching='WZTo3LNu_mllmin4p0_(.*)_powheg_:WZto3LNu_\1_powheg_' \
  --name-matching='WZTo3LNu_cp5_(.*)_amcatnlo_:WZto3LNu_1Jets_cp5_\1_amcatnlo_' \
  --name-matching='WZTo1L1Nu2Q_4f_:WZtoLNu2Q_1Jets_' \
  --name-matching='WWTo4Q_4f_:WWto4Q_1Jets_4fs_' \
  --name-matching='WWTo1L1Nu2Q_4f_:WWtoLNu2Q_1Jets_4fs_' \
  --name-matching='ZJetsToQQ_:Zto2Q_4Jets_' \
  --name-matching='([WZ])Z(.*)_[45]f(s|)_:\1Z\2_' \
  --name-matching='WZTo1L3Nu_:WZtoL3Nu_1Jets_' \
  --name-matching='TTZToQQ_:TTZ_ZtoQQ_1Jets_' \
  --name-matching='^QCD_HT:QCD_4Jets_HT_' \
  --name-matching='qcd_4jets_ht_2000toinf_:qcd_4jets_ht_2000_' \
  --name-matching='^ttHTo(non|)bb_:TTHto\g<1>2B_' \
  --name-matching='HToWW:Hto2W' \
  --name-matching='HTobb:Hto2b' \
  --name-matching='ZToQQ:Zto2Q' \
  --name-matching='ZToLL:Zto2L' \
  --cross-era NanoProd/crab/Run*_20*
