#!/bin/bash

if ! [ -d "$ANALYSIS_PATH" ]; then
  echo "ANALYSIS_PATH is not set. Exiting."
  exit 1
fi
cd $ANALYSIS_PATH

CACHE_DIR=data/ds_cache

mkdir -p "$CACHE_DIR"
ERAS="Run2_2016 Run2_2016_HIPM Run2_2017 Run2_2018 Run3_2022 Run3_2022EE Run3_2023 Run3_2023BPix"

for era in $ERAS; do
  echo "Checking datasets existance for $era..."
  python RunKit/checkDatasetExistance.py --cache $CACHE_DIR/${era}.json NanoProd/crab/$era/*.yaml
done


