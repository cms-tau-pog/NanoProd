
run_prod() {
  local ds=$1
  local era=$2
  local sampleType=$3
  local maxEvents=$4
  echo "Producing dataset=$ds era=$era sampleType=$sampleType"
  if [ -f output/${ds}_0.root ]; then
    echo "File output/${ds}_0.root already exists. Skipping."
    continue
  fi
  echo
  cmsEnv python3 $ANALYSIS_PATH/RunKit/nanoProdWrapper.py customise=NanoProd/NanoProd/customize.customize maxEvents=$maxEvents sampleType=$sampleType era=$era inputFiles=file:/eos/cms/store/group/phys_tau/kandroso/miniAOD/$era/$ds.root writePSet=True keepIntermediateFiles=False "output=$ds.root;./output"
  cmsEnv $ANALYSIS_PATH/RunKit/crabJob.sh
  python $ANALYSIS_PATH/RunKit/inspectNanoFile.py --doc ${ds}_doc.html --size ${ds}_size.html output/${ds}_0.root && mv ${ds}_doc.html ${ds}_size.html /eos/home-k/kandroso/www/HLepRare/debug/skim_v2
}

action() {
  local DATASETS_MC=(TTtoLNu2Q TTto2L2Nu TTto4Q DYto2L_M-50_amcatnloFXFX WtoLNu_amcatnloFXFX)
  local DATASETS_DATA=(EGamma_Run2022D Muon_Run2022D Tau_Run2022D JetMET_Run2022D)
  local era=Run3_2022
  local maxEvents=-1

  for ds in ${DATASETS_MC[@]}; do
    run_prod $ds $era mc $maxEvents
  done

  for ds in ${DATASETS_DATA[@]}; do
    run_prod $ds $era data $maxEvents
  done
}

action
