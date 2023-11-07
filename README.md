# NanoProd

`NanoProd`: produce nanoAOD from miniAOD using CRAB and local grids.
`NanoProd` is based on the following tools:
- [law](https://github.com/riga/law) to submit and monitor jobs on a local grid
- [RunKit](https://github.com/kandrosov/RunKit) a toolkit to simplify root-tuple production and job submission within the CMS infrastructure
  - additional details on how to run and configure `RunKit/crabOverseer.py` can be found on [this page](https://kandrosov.github.io/RunKit/crabOverseer/)

## How to install
```sh
git clone --recursive https://github.com/cms-tau-pog/NanoProd.git
```

## Loading environment
Following command activates the framework environment:
```sh
source env.sh
```
## How to run miniAOD->nanoAOD skims production

Production should be run on the server that have the crab stageout area mounted to the file system.

1. Load environment
   ```sh
   source $PWD/env.sh
   voms-proxy-init -voms cms -rfc -valid 192:00
   ```

1. Check that all datasets are present and valid (replace path to `yaml`s accordingly):
   ```sh
   cat NanoProd/crab/ERA/*.yaml | grep -v -E '^( +| *#)' | grep -E ' /' | sed -E 's/.*: (.*)/\1/' | xargs python RunKit/checkDatasetExistance.py
   ```
   If all ok, there should be no output.
1. Modify output and other site-specific settings in `NanoProd/crab/overseer_cfg.yaml`. In particular:
   - params/outputs
   - renewKerberosTicket

1. Test that the code works locally (take one of the miniAOD files as an input). E.g.
   ```sh
   mkdir -p tmp && cd tmp
   cmsEnv python3 $ANALYSIS_PATH/RunKit/nanoProdWrapper.py customise=NanoProd/NanoProd/customize.customize maxEvents=100 sampleType=mc era=Run2_2018 inputFiles=file:/eos/cms/store/group/phys_tau/kandroso/miniAOD_UL18/TTToSemiLeptonic.root writePSet=True 'output=nano.root;./output;../NanoProd/config/skim_htt.yaml;skim;skim_failed'
   cmsEnv $ANALYSIS_PATH/RunKit/crabJob.sh
   ```
   Check that output file `nano_0.root` is created correctly.
   You can, for example, create a documentation page based on the file you created:
   ```sh
   cmsEnv python3 $ANALYSIS_PATH/RunKit/inspectNanoFile.py nano_0.root -d content.html -s size.html
   ```
   After that, you can remove `tmp` directory:
   ```sh
   cd $ANALYSIS_PATH
   rm -r tmp
   ```

1. Test a dryrun crab submission
   ```sh
   python RunKit/crabOverseer.py --work-area crab_test --cfg NanoProd/crab/overseer_cfg.yaml --no-loop NanoProd/crab/crab_test.yaml
   ```
   - If successful, the last line output to the terminal should be
     ```
     Tasks: 1 Total, 1 Submitted
     ```
   - NB. Crab estimates of processing time will not be accurate, ignore them.
   - After the test, remove `crab_test` directory:
     ```sh
     rm -r crab_test
     ```

1. Test that post-processing task is known to law:
   ```sh
   law index
   law run ProdTask --help
   ```

1. Submit tasks using `RunKit/crabOverseer.py` and monitor the process.
   It is recommended to run `crabOverseer` in `screen`.
   ```sh
   python RunKit/crabOverseer.py --cfg NanoProd/crab/overseer_cfg.yaml NanoProd/crab/Run2_2018/FILE1.yaml NanoProd/crab/Run2_2018/FILE2.yaml ...
   ```
   - Use `NanoProd/crab/Run2_2018/*.yaml` to submit all the tasks
   - For more information about available command line arguments run `python3 RunKit/crabOverseer.py --help`
   - For consecutive runs, if there are no modifications in the configs, it is enough to run `crabOverseer` without any arguments:
     ```sh
     python RunKit/crabOverseer.py
     ```

## Resubmission of failed tasks

The job handler will automatically create recovery tasks for jobs that failed multiple times.
As of recovery #1 the jobs created will run on a single miniAOD file each, while for the latest available iteration (default is recovery #2) the job will only run on specified sites which are whitelisted in the crab overseer config: [NanoProd/crab/overseer_cfg.yaml](https://github.com/cms-tau-pog/NanoProd/blob/main/NanoProd/crab/overseer_cfg.yaml).
Note: if the file has no available Rucio replica on any of those sites, the job is bound to fail.

### Handling failed jobs after last recovery task

General guidelines:

1. Check job output via Grafana [monit-grafana.cern.ch/d/cmsTMDetail/cms-task-monitoring-task-view](https://monit-grafana.cern.ch/d/15468761344/personal-tasks-monitoring-globalview?from=now-90d&to=now&orgId=11&var-user=All&var-site=All&var-current_url=%2Fd%2FcmsTMDetail%2Fcms_task_monitoring&var-task=All)
   During the resubmission step a link is also printed to screen with the direct link to the ongoing CRAB task.

1. Identify exit code, see [JobExitCodes](https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes)
   1. `>50000` most likely associated to I/O issue with the site or the dataset. Increase the number of max retries and resend the job.

   1. Special exit code defined in the tool: 666 - it is used to label errors which are neither related to CMSSW compilation, bash or crab job handling. Check the specific job output from the CRAB Monitor tool, copy the jobID from Grafana.
   It includes cases where the dataset is corrupted, unaccessible on any tier or with no existing replica.
   To check if the file has any available replica on the sites run
   ```sh
   dasgoclient --query 'site file=FILENAME'
   ```
   In case there is no available Rucio replica the file cannot be processed, please write an issue on CMS-talk (e.g. [Issue for Tau UL2018 file](https://cms-talk.web.cern.ch/t/cant-access-one-file-from-tau-run2018d-ul2018-miniaodv2-v1-miniaod/14522/2) and remove the file from the studied inputs, see below.

1. After identifying the problem and taking action to solve it either with CMSSW, requesting Rucio transfer or adding a specific storage center to the whitelist execute the following steps.
   1. Edit the `yaml` file corresponding to the dataset (e.g. [NanoProd/crab/Run2_2018/DY.yaml](https://github.com/cms-tau-pog/NanoProd/blob/main/NanoProd/crab/Run2_2018/DY.yaml):
      1. Increase the maximum number of retries by adding the entry `maxRecoveryCount` to `config` in the `yaml` file:
      	 ```python
		 config:
		 	maxRecoveryCount: 3
				params:
					sampleType: mc
					era: Run2_2018
      	 ```
      1. If the job fails due to a file which is corrupted or unavailable it needs to be skipped in the nanoAOD production, this can be done by editing the `yaml` file as follows:
      	 ```python
      	 DYJetsToLL_M-50-madgraphMLM_ext1: /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1_ext1-v1/MINIAODSIM
      	 ```
      	 ->
      	 ```python
      	 DYJetsToLL_M-50-madgraphMLM_ext1:
		 	inputDataset: /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1_ext1-v1/MINIAODSIM
				ignoreFiles:
				- /store/mc/RunIISummer20UL18MiniAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/MINIAODSIM/106X_upgrade2018_realistic_v16_L1v1_ext1-v1/40000/1D821371-03FD-B148-9E83-119185898E4F.root
      	 ```
   1. Change the status.json file so the job is marked as `WaitingForRecovery` instead of `Failed`
      ```sh
      python RunKit/crabOverseer.py --action 'run_cmd task.taskStatus.status = Status.WaitingForRecovery' --select 'task.name == TASK_NAME'
      ```
      where `TASK_NAME` is the dataset nickname provided in the `yaml` file, e.g. `DYJetsToLL_M-50-madgraphMLM_ext1`
   1. Run crabOverseer.py as in step 7 adding `--update-cfg` option.


## Running with ParticleNET

In order to produce NanoAOD along with output branches from ParticleNET (which will be found in the "Jet" and "FatJet" collections for AK4 and AK8 outputs, respectively), the following additions are made automatically when setting up the environment:
* Follow the installation recipe in the Readme [here](https://gitlab.cern.ch/rgerosa/particlenetstudiesrun2/-/tree/master/)
* Then copy the PNET models into place where they're needed, according to the first section in the ReadMe [here](https://gitlab.cern.ch/rgerosa/particlenetstudiesrun2/-/tree/master/TrainingNtupleMakerAK4) and [here](https://gitlab.cern.ch/rgerosa/particlenetstudiesrun2/-/tree/master/TrainingNtupleMakerAK8).
* Then it will only work locally however. To make it work for jobs submitted to crab, put the same files in `RecoBTag/Combined/data/` and `RecoTauTag/data/` inside the CMSSW_BASE/src/ directory.


