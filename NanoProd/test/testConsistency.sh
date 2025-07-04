#!/bin/bash

if ! [ -d "$ANALYSIS_PATH" ]; then
  echo "ANALYSIS_PATH is not set. Exiting."
  exit 1
fi
cd $ANALYSIS_PATH

for era in Run2_2016 Run2_2016_HIPM Run2_2017 Run2_2018 Run3_2022 Run3_2022EE Run3_2023 Run3_2023BPix; do
  echo "Checking $era consistency..."
  python RunKit/checkTasksConsistency.py --era $era "$@" --dataset-naming-rules NanoProd/crab/dataset_naming_rules.yaml NanoProd/crab/$era/*.yaml
done


# --show-only-missing-with-candidates \
echo "Checking cross-era consistency..."
python RunKit/checkTasksConsistency.py --cross-era "$@" --dataset-naming-rules NanoProd/crab/dataset_naming_rules.yaml \
  --exceptions NanoProd/crab/dataset_exceptions.yaml \
  NanoProd/crab/Run*_20*
