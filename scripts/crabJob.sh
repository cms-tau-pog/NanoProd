#/bin/bash

function make_job_report {
  local exit_code=$1
  local exit_message="${@:2}"
  if [ $exit_code -ne 0 ]; then
    error_msg="
<FrameworkError ExitStatus=\"$exit_code\" Type=\"Fatal error\" >
<![CDATA[
$exit_message
]]>
</FrameworkError>"
  else
    error_msg=""
  fi
  cat << EOF > FrameworkJobReport.xml.tmp
<FrameworkJobReport>
<ReadBranches>
</ReadBranches>
<PerformanceReport>
  <PerformanceSummary Metric="StorageStatistics">
    <Metric Name="Parameter-untracked-bool-enabled" Value="true"/>
    <Metric Name="Parameter-untracked-bool-stats" Value="true"/>
    <Metric Name="Parameter-untracked-string-cacheHint" Value="application-only"/>
    <Metric Name="Parameter-untracked-string-readHint" Value="auto-detect"/>
    <Metric Name="ROOT-tfile-read-totalMegabytes" Value="0"/>
    <Metric Name="ROOT-tfile-write-totalMegabytes" Value="0"/>
  </PerformanceSummary>
</PerformanceReport>

<GeneratorInfo>
</GeneratorInfo>
$error_msg
</FrameworkJobReport>
EOF
  mv FrameworkJobReport.xml.tmp FrameworkJobReport.xml
}

function run_cmd {
    echo "> $@"
    "$@"
    local RESULT=$?
    if [ $RESULT -ne 0 ] ; then
        echo "Error while rinning '$@'"
        make_job_report $RESULT "Error while rinning '$@'"
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
  f"-n {p.maxEvents.input.value()}",
]
print(" ".join(params))
')

cmsDriver_out="nanoOrig.root"
final_out="nano.root"
n_threads=1

run_cmd cmsDriver.py nano --fileout file:$cmsDriver_out --eventcontent NANOAODSIM --datatier NANOAODSIM \
  --step NANO --nThreads $n_threads $PARAMS --customise "NanoProd/NanoProd/customize.customize"


run_cmd python3 $CMSSW_BASE/python/NanoProd/NanoProd/run_skim.py $cmsDriver_out $final_out

make_job_report 0 "All done"
