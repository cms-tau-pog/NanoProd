#!/bin/bash

if ! [ -d "$ANALYSIS_PATH" ]; then
  echo "ANALYSIS_PATH is not set. Exiting."
  exit 1
fi
cd $ANALYSIS_PATH

# for era in Run2_2016 Run2_2016_HIPM Run2_2017 Run2_2018 Run3_2022 Run3_2022EE Run3_2023 Run3_2023BPix; do
#   echo "Checking $era consistency..."
#   python RunKit/checkTasksConsistency.py --era $era --dataset-name-masks NanoProd/crab/dataset_name_masks.yaml NanoProd/crab/$era/*.yaml
#   if [ $? -ne 0 ]; then
#     echo "Consistency check failed for $era."
#     exit 1
#   fi
# done


# --show-only-missing-with-candidates \
echo "Checking cross-era consistency..."
python RunKit/checkTasksConsistency.py --cross-era --dataset-name-masks NanoProd/crab/dataset_name_masks.yaml \
  --exceptions NanoProd/crab/Sample_exceptions.yaml \
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
  --name-matching='_withDipoleRecoil:' \
  --name-matching='_minlo:' \
  --name-matching='_M_125:_M125' \
  --name-matching='GluGluHToTauTauPlusTwoJetsUncorDecay:GluGluHJJto2TauUncorrelatedDecay' \
  --name-matching='UncorrelatedDecay_Filtered:UncorrelatedDecay' \
  --name-matching='UncorrelatedDecay_M125(.*)_minnlo:UncorrelatedDecay_M125\1' \
  --name-matching='_CP_odd_:_CPodd_' \
  --name-matching='_amcatnlopowheg_:_powheg_' \
  --name-matching='uncorrelateddecay_mm_:uncorrelateddecay_cp_mix_' \
  --name-matching='uncorrelateddecay_sm_:uncorrelateddecay_cp_even_' \
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
  NanoProd/crab/Run*_20*
