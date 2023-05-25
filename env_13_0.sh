#!/usr/bin/env bash

function run_cmd {
  "$@"
  RESULT=$?
  if (( $RESULT != 0 )); then
    echo "Error while running '$@'"
    kill -INT $$
  fi
}

do_install_cmssw() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  export SCRAM_ARCH=$1
  local CMSSW_VER=$2
  local os_version=$3
  if ! [ -f "$this_dir/soft/CentOS$os_version/$CMSSW_VER/.installed" ]; then
    run_cmd mkdir -p "$this_dir/soft/CentOS$os_version"
    run_cmd cd "$this_dir/soft/CentOS$os_version"
    run_cmd source /cvmfs/cms.cern.ch/cmsset_default.sh
    if [ -d $CMSSW_VER ]; then
      echo "Removing incomplete $CMSSW_VER installation..."
      run_cmd rm -rf $CMSSW_VER
    fi
    echo "Creating $CMSSW_VER area for CentOS$os_version in $PWD ..."
    run_cmd scramv1 project CMSSW $CMSSW_VER
    run_cmd cd $CMSSW_VER/src
    run_cmd eval `scramv1 runtime -sh`
    run_cmd git-cms-init
    run_cmd git clone ssh://git@gitlab.cern.ch:7999/akhukhun/roccor.git RoccoR
    run_cmd git clone git@github.com:SVfit/ClassicSVfit.git TauAnalysis/ClassicSVfit -b fastMTT_19_02_2019
    run_cmd git clone git@github.com:SVfit/SVfitTF.git TauAnalysis/SVfitTF
    run_cmd ln -s "$this_dir" NanoProd
    run_cmd scram b -j8
    run_cmd cd "$this_dir"
    # run_cmd mkdir -p "$this_dir/soft/CentOS$os_version/bin"
    # run_cmd ln -s $(which python3) "$this_dir/soft/CentOS$os_version/bin/python"
    run_cmd touch "$this_dir/soft/CentOS$os_version/$CMSSW_VER/.installed"
  fi
}

install_cmssw() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
  local scram_arch=$1
  local cmssw_version=$2
  local os_version=$3
  if [[ $os_version < 8 ]] ; then
    local env_cmd=cmssw-cc$os_version
  else
    local env_cmd=cmssw-el$os_version
  fi
  if ! [ -f "$this_dir/soft/CentOS$os_version/$CMSSW_VER/.installed" ]; then
    run_cmd $env_cmd --command-to-run /usr/bin/env -i HOME=$HOME bash "$this_file" install_cmssw $scram_arch $cmssw_version $os_version
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
  export X509_USER_PROXY="$ANALYSIS_DATA_PATH/voms.proxy"

  run_cmd mkdir -p "$ANALYSIS_DATA_PATH"

  run_cmd install_cmssw slc7_amd64_gcc11 CMSSW_13_0_6 7 nano_prod
  run_cmd install_cmssw el8_amd64_gcc11 CMSSW_13_0_6 8 nano_prod

  local os_version=$(cat /etc/os-release | grep VERSION_ID | sed -E 's/VERSION_ID="([0-9]+).*"/\1/')
  local default_cmssw_ver=CMSSW_13_0_6
  export DEFAULT_CMSSW_BASE="$ANALYSIS_PATH/soft/CentOS$os_version/$default_cmssw_ver"

  if [ ! -z $ZSH_VERSION ]; then
    autoload bashcompinit
    bashcompinit
  fi
  source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh LCG_102 x86_64-centos${os_version}-gcc11-opt
  source /afs/cern.ch/user/m/mrieger/public/law_sw/setup.sh

  source "$( law completion )" ""
  alias cmsEnv="env -i HOME=$HOME ANALYSIS_PATH=$ANALYSIS_PATH X509_USER_PROXY=$X509_USER_PROXY DEFAULT_CMSSW_BASE=$DEFAULT_CMSSW_BASE $ANALYSIS_PATH/RunKit/cmsEnv.sh"
}

if [ "X$1" = "Xinstall_cmssw" ]; then
  do_install_cmssw "${@:2}"
else
  action "$@"
fi
