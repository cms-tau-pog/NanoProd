# NanoProd

## How to install

```sh
export SCRAM_ARCH=el8_amd64_gcc10
cmsrel CMSSW_12_4_8
cd CMSSW_12_4_8/src
cmsenv
git clone https://github.com/kandrosov/NanoProd.git NanoProd/NanoProd
scram b
```

## How to run locally

1. Creating PSet.py - this step will be done automatically be crab when submitting the job
   ```sh
   python3 NanoProd/NanoProd/python/Prod.py sampleType=TYPE inputFiles=FILE1,FILE2,... era=ERA maxEvents=N
   ```
   where `sampleType` = **data** or **mc**,
   `inputFiles` - comma separated list of input files,
   `era` = **Run2_2016_HIPM**, **Run2_2016**, **Run2_2017** or **Run2_2018**,
   `maxEvents` - number of events to process (default=-1, i.e. all events)

   Example:
   ```sh
   python3 NanoProd/NanoProd/python/Prod.py sampleType=mc inputFiles=file:/eos/cms/store/group/phys_tau/acardini/miniAODskim/TTToSemiLeptonic_UL18_006455CD-9CDB-B843-B50D-5721C39F30CE.root era=Run2_2018 maxEvents=100
   ```

1. Produce nanoAOD and run skim. The result will be stored in `nano.root` file.
   ```sh
   ./NanoProd/NanoProd/scripts/crabJob.sh
   ```

## Working with CRAB

1. Submitting tasks on crab
   ```sh
   python3 NanoProd/NanoProd/scripts/crab_submit.py --workArea WORK_AREA --cfg NanoProd/NanoProd/python/Prod.py --site SITE --output OUTPUT_PATH --splitting FileBased --unitsPerJob N --scriptExe NanoProd/NanoProd/scripts/crabJob.sh --outputFiles nano.root TASK_FILE1 TASK_FILE2 ...
   ```
   where `workArea` - local working area where tasks descriptions and monitoring logs will be stored,
   `site` and `output` - name of the site and the path where job results should be transferred,
   `splitting` and `unitsPerJob` - the job splitting algorithm and number of units per a single job (e.g. number of files for **FileBased** splitting),
   `TASK_FILE1` `TASK_FILE2` ... - list of .txt files with tasks definitions to submit.

   Example how to submit production for the Run2 2018:
   ```sh
   python3 NanoProd/NanoProd/scripts/crab_submit.py --workArea work_area --cfg NanoProd/NanoProd/python/Prod.py --site T2_CH_CERN --output /store/group/phys_tau/kandroso/DeepTau_v2p5_prod --splitting FileBased --unitsPerJob 10 --scriptExe NanoProd/NanoProd/scripts/crabJob.sh --outputFiles nano.root NanoProd/NanoProd/crab/Run2_2018/*.txt
   ```
2. Monitoring status of all tasks
   ```sh
   crab_cmd.py --workArea work_area --cmd status
   ```
3. Resubmitting failed jobs for a given task
   ```sh
   crab resubmit -d work_area/crab_MY_TASK
   ```
