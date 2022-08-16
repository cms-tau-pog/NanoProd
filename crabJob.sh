#/bin/bash

function run_cmd {
    echo "> $@"
    "$@"
    RESULT=$?
    if [ $RESULT -ne 0 ] ; then
        echo "Error while rinning '$@'"
        exit 1
    fi
}

PARAMS=$(python3 -c '
import PSet
p = PSet.process
input_files = ",".join(list(p.source.fileNames))
params = [
  f"--filein {input_files}",
  f"--{p.exParams.sampleType.value()}",
  f"--conditions {p.exParams.cond.value()}",
  f"--era {p.exParams.era.value()},run2_nanoAOD_106Xv2",
]
print(" ".join(params))
')

cmsDriver_out="nanoOrig.root"
final_out="nano.root"
n_threads=2
n_evt=100

run_cmd cmsDriver.py nano --fileout file:$cmsDriver_out --eventcontent NANOAODSIM --datatier NANOAODSIM \
  --step NANO --nThreads $n_threads -n $n_evt $PARAMS

run_cmd python3 run_skim.py $cmsDriver_out $final_out
