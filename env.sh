#!/usr/bin/env bash

run_cmd() {
  "$@"
  RESULT=$?
  if (( $RESULT != 0 )); then
    echo "Error while running '$@'"
    kill -INT $$
  fi
}

get_os_prefix() {
  local os_version=$1
  local for_global_tag=$2
  if (( $os_version >= 8 )); then
    echo el
  elif (( $os_version < 6 )); then
    echo error
  else
    if [[ $for_global_tag == 1 || $os_version == 6 ]]; then
      echo slc
    else
      echo cc
    fi
  fi
}

do_install_cmssw() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  export SCRAM_ARCH=$1
  local CMSSW_VER=$2
  if ! [ -f "$this_dir/soft/$CMSSW_VER/.installed" ]; then
    run_cmd mkdir -p "$this_dir/soft"
    run_cmd cd "$this_dir/soft"
    run_cmd source /cvmfs/cms.cern.ch/cmsset_default.sh
    if [ -d $CMSSW_VER ]; then
      echo "Removing incomplete $CMSSW_VER installation..."
      run_cmd rm -rf $CMSSW_VER
    fi
    echo "Creating $CMSSW_VER area in $PWD ..."
    run_cmd scramv1 project CMSSW $CMSSW_VER
    run_cmd cd $CMSSW_VER/src
    run_cmd eval `scramv1 runtime -sh`

    #install CMSSW updates not in official releases
    local master_ver=`echo $CMSSW_VER | cut -d'_' -f 2`
    local sub_ver=`echo $CMSSW_VER | cut -d'_' -f 3`
    local subsub_ver=`echo $CMSSW_VER | cut -d'_' -f 4`
    if [[ $master_ver == "14"  && $sub_ver == "0" ]]; then
      run_cmd echo "=> Installing addons for CMSSW_"${master_ver}"_"$sub_ver
      run_cmd git cms-merge-topic -u cms-tau-pog:CMSSW_14_0_X_NanoProd_Addon_Powheg
      run_cmd git cms-merge-topic -u cms-tau-pog:CMSSW_14_0_X_tau-pog_BoostedDeepTau
      run_cmd wget https://github.com/cms-tau-pog/RecoTauTag-TrainingFiles/raw/refs/heads/BoostedDeepTau_v2/BoostedDeepTauId/boosteddeepTau_RunIIv2p0_{core,inner,outer}.pb -P RecoTauTag/TrainingFiles/data/BoostedDeepTauId/
      run_cmd git cms-merge-topic -u cms-tau-pog:CMSSW_14_0_X_tau-pog_DeepTauNoDA
      run_cmd wget https://github.com/cms-tau-pog/RecoTauTag-TrainingFiles/raw/refs/heads/deepTau_v2p5_noDomainAdaptation/DeepTauId/deepTau_2018v2p5_noDomainAdaptation_{core,inner,outer}.pb -P RecoTauTag/TrainingFiles/data/DeepTauId/
    fi

    run_cmd mkdir NanoProd
    run_cmd ln -s "$this_dir/NanoProd" NanoProd/NanoProd
    run_cmd scram b -j8
    run_cmd cd "$this_dir"
    run_cmd touch "$this_dir/soft/$CMSSW_VER/.installed"
  fi
}

install_cmssw() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
  local scram_arch=$1
  local cmssw_version=$2
  local node_os=$3
  local target_os=$4
  if [[ $node_os == $target_os ]]; then
    local env_cmd=""
    local env_cmd_args=""
  else
    local env_cmd="cmssw-$target_os"
    if ! command -v $env_cmd &> /dev/null; then
      echo "Unable to do a cross-platform installation for $cmssw_version SCRAM_ARCH=$scram_arch. $env_cmd is not available."
      return 1
    fi
    local env_cmd_args="--command-to-run"
  fi
  if ! [ -f "$this_dir/soft/$CMSSW_VER/.installed" ]; then
    run_cmd $env_cmd $env_cmd_args /usr/bin/env -i HOME=$HOME bash "$this_file" install_cmssw $scram_arch $cmssw_version
  fi
}

action() {
  # determine the directory of this file
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  export PYTHONPATH="$this_dir:$PYTHONPATH"
  export LAW_HOME="$this_dir/.law"
  export LAW_CONFIG_FILE="$this_dir/NanoProd/config/law.cfg"

  export ANALYSIS_PATH="$this_dir"
  export ANALYSIS_DATA_PATH="$ANALYSIS_PATH/data"
  export ANALYSIS_BIN_PATH="$ANALYSIS_PATH/soft/bin"
  export X509_USER_PROXY="$ANALYSIS_DATA_PATH/voms.proxy"

  run_cmd mkdir -p "$ANALYSIS_DATA_PATH"

  local os_version=$(cat /etc/os-release | grep VERSION_ID | sed -E 's/VERSION_ID="([0-9]+).*"/\1/')
  local os_prefix=$(get_os_prefix $os_version)
  local node_os=$os_prefix$os_version

  local default_cmssw_ver=CMSSW_14_0_18
  local target_os_version=8
  local target_os_prefix=$(get_os_prefix $target_os_version)
  local target_os_gt_prefix=$(get_os_prefix $target_os_version 1)
  local target_os=$target_os_prefix$target_os_version
  export DEFAULT_CMSSW_BASE="$ANALYSIS_PATH/soft/$default_cmssw_ver"

  run_cmd install_cmssw ${target_os_gt_prefix}${target_os_version}_amd64_gcc12 $default_cmssw_ver $node_os $target_os

  if [ ! -f "$ANALYSIS_BIN_PATH/.installed" ]; then
    run_cmd mkdir -p "$ANALYSIS_BIN_PATH"
    run_cmd ln -s /usr/bin/java "$ANALYSIS_BIN_PATH/java"
    run_cmd touch "$ANALYSIS_BIN_PATH/.installed"
  fi

  if [ ! -z $ZSH_VERSION ]; then
    autoload bashcompinit
    bashcompinit
  fi
  source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh LCG_105 x86_64-${os_prefix}${os_version}-gcc13-opt
  source /afs/cern.ch/user/m/mrieger/public/law_sw/setup.sh

  source "$( law completion )" ""

  local current_args=( "$@" )
  set --
  source /cvmfs/cms.cern.ch/rucio/setup-py3.sh &> /dev/null
  set -- "${current_args[@]}"

  export PATH="$ANALYSIS_BIN_PATH:$PATH"

  if [[ $node_os == $target_os ]]; then
    export CMSSW_SINGULARITY=""
    local env_cmd=""
  else
    export CMSSW_SINGULARITY="/cvmfs/cms.cern.ch/common/cmssw-$target_os"
    local env_cmd="$CMSSW_SINGULARITY --command-to-run"
  fi

  alias cmsEnv="$env_cmd env -i HOME=$HOME ANALYSIS_PATH=$ANALYSIS_PATH X509_USER_PROXY=$X509_USER_PROXY DEFAULT_CMSSW_BASE=$DEFAULT_CMSSW_BASE KRB5CCNAME=$KRB5CCNAME $ANALYSIS_PATH/RunKit/cmsEnv.sh"
}

if [ "X$1" = "Xinstall_cmssw" ]; then
  do_install_cmssw "${@:2}"
else
  action "$@"
fi
