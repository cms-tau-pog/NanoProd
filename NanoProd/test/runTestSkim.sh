
run_skim() {
  local ds=$1
  local input_dir=$2
  local output_dir=$3
  local skim_config=$4
  local skim_tag=$5
  local html_dir=$6
  echo "Skimming dataset=$ds"
  local input_file="$input_dir/${ds}_0.root"
  local output_file="$output_dir/$skim_tag/$ds.root"
  if ! [ -f $input_file ]; then
    echo "$input_file does not exist. Skipping."
    return
  fi
  if [ -f $output_file ]; then
    echo "$output_file already exists. Skipping."
    return
  fi
  mkdir -p $output_dir/$skim_tag
  python $ANALYSIS_PATH/RunKit/skim_tree.py --input "$input_file" --output "$output_file" --config "$skim_config" \
                                            --setup skim --skip-empty --verbose 1
  python $ANALYSIS_PATH/RunKit/skim_tree.py --input "$input_file" --output "$output_file" --config "$skim_config" \
                                            --setup skim_failed --skip-empty --update-output --verbose 1
  mkdir -p $html_dir/$skim_tag
  python $ANALYSIS_PATH/RunKit/inspectNanoFile.py --doc ${ds}_doc.html --size ${ds}_size.html "$output_file" && mv ${ds}_doc.html ${ds}_size.html $html_dir/$skim_tag
}

action() {
  local DATASETS_MC=(TTtoLNu2Q TTto2L2Nu TTto4Q DYto2L_M-50_amcatnloFXFX WtoLNu_amcatnloFXFX)
  local DATASETS_DATA=(EGamma_Run2022D Muon_Run2022D Tau_Run2022D JetMET_Run2022D)
  local INPUT_DIR=output
  local OUTPUT_DIR=skims
  local SKIM_TAG=skim_v$1
  local SKIM_CONFIG=$ANALYSIS_PATH/NanoProd/config/skim_htt.yaml
  local HTML_DIR="/eos/home-k/kandroso/www/HLepRare/debug/skim_v2"

  for ds in ${DATASETS_MC[@]}; do
    run_skim $ds $INPUT_DIR $OUTPUT_DIR $SKIM_CONFIG $SKIM_TAG $HTML_DIR
  done

  for ds in ${DATASETS_DATA[@]}; do
    run_skim $ds $INPUT_DIR $OUTPUT_DIR $SKIM_CONFIG $SKIM_TAG $HTML_DIR
  done
}

action "$@"
