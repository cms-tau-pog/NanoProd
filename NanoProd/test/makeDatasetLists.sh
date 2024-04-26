#!/bin/bash


if ! [ -d "$ANALYSIS_PATH" ]; then
  echo "ANALYSIS_PATH is not set. Exiting."
  exit 1
fi
cd $ANALYSIS_PATH

DS_LIST_DIR=data/ds_lists

mkdir -p $DS_LIST_DIR

declare -A ERAS
ERAS['Run2_2016']='RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17*'
ERAS['Run2_2016_HIPM']='RunIISummer20UL16MiniAODAPVv2-106X_mcRun2_asymptotic_preVFP_v11*'
ERAS['Run2_2017']='RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9*'
ERAS['Run2_2018']='RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1*'
ERAS['Run3_2022']='Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5*'
ERAS['Run3_2022EE']='Run3Summer22EEMiniAODv4-*130X_mcRun3_2022_realistic_postEE_v6*'
ERAS['Run3_2023']='Run3Summer23MiniAODv4-*130X_mcRun3_2023_realistic_v1*'
ERAS['Run3_2023BPix']='Run3Summer23BPixMiniAODv4-*130X_mcRun3_2023_realistic_postBPix_v*'

for era in "${!ERAS[@]}"; do
  if ! [ -f "$DS_LIST_DIR/$era.txt" ]; then
    echo "Making dataset lists for $era..."
    dasgoclient --query "dataset dataset=/*/${ERAS[$era]}/MINIAODSIM" | sort -h > "$DS_LIST_DIR/$era.txt"
  fi
done