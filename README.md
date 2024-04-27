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

1. Check that task configurations for the given era are consistent and that all datasets are present and valid (replace path to `yaml`s accordingly):
   ```sh
   python RunKit/checkTasksConsistency.py NanoProd/crab/ERA/*.yaml
   python RunKit/checkDatasetExistance.py NanoProd/crab/ERA/*.yaml
   ```
1. Modify output and other site-specific settings in `NanoProd/crab/overseer_cfg.yaml`. In particular fileds value "TODO" must be set:
   - params/outputs/crabOutput
   - params/outputs/finalOutput
   - htmlReport

1. Test that the code works locally (take one of the miniAOD files as an input). E.g.
   ```sh
   mkdir -p tmp && cd tmp
   cmsEnv python3 $ANALYSIS_PATH/RunKit/nanoProdWrapper.py customise=NanoProd/NanoProd/customize.customize maxEvents=100 sampleType=mc era=Run3_2022 inputFiles=file:/eos/cms/store/group/phys_tau/kandroso/miniAOD/Run3_2022/TTtoLNu2Q.root writePSet=True keepIntermediateFiles=True 'output=nano.root;./output;../NanoProd/config/skim_htt.yaml;skim;skim_failed'
   cmsEnv $ANALYSIS_PATH/RunKit/crabJob.sh
   ```
   Check that output file `nano_0.root` is created correctly.
   You can, for example, create a documentation page based on the file you created:
   ```sh
   cmsEnv python3 $ANALYSIS_PATH/RunKit/inspectNanoFile.py output/nano_0.root -d content.html -s size.html
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
For each consecutive recovery number of files per job is reduced by a factor of 2.
For the last recovery with crab, one file for job will be used and the job will be submitted only to sites whitelisted in [NanoProd/crab/overseer_cfg.yaml](https://github.com/cms-tau-pog/NanoProd/blob/main/NanoProd/crab/overseer_cfg.yaml).
After the last recovery with crab, the final recovery attempt is done by submitting jobs on the local grid.

Note: if the file has no available Rucio replica on any of those sites, the job is bound to fail.

### Handling failures

If automatic recovery attemnts have failed, task will be declared as failed and requiring a manual intervention.

1. Run `check_update_failed` action to check availability of the input files for the failed jobs
   ```sh
   python RunKit/crabOverseer.py --action check_update_failed | tee missing_files.txt
   ```
   - If there is least one file available available, the task status will be reset to `SubmittedToLocal`. And production can be continued in a usual way by running `crabOverseer.py`.
   - If all listed files don't have replicas on DISK, or replicas are corrupted, please report it to O&C/Computing Tools.

1. If post-processing job fails, check the output log in `.crabOverseer/law/jobs/ProdTask/*.txt`. If the error is due to file access, it could be that the output file is corrupted in the storage element. In this case, you need to rerun the production job for these files before proceeding with the post-processing. To identify such cases run `check_update_processed` action:
   ```sh
   python RunKit/crabOverseer.py --action check_update_processed | tee output_file_status.txt
   ```
   - If at leaset one corrupted file is found, the task status will be reset to `SubmittedToLocal`. And production can be continued in a usual way by running `crabOverseer.py`.
