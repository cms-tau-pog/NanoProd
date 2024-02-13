import law
import luigi
import os
import shutil
import tempfile

from RunKit.law_customizations import HTCondorWorkflow, copy_param
from RunKit.run_tools import ps_call
from RunKit.envToJson import get_cmsenv

class BenchmarkBase:
  bootstrap_path = copy_param(HTCondorWorkflow.bootstrap_path,
                              os.path.join(os.getenv('ANALYSIS_PATH'), 'bootstrap.sh'))
  sub_dir = copy_param(HTCondorWorkflow.sub_dir, os.getenv('ANALYSIS_DATA_PATH'))
  input = luigi.Parameter(description="directory with input files")
  version = luigi.Parameter()
  input_samples = luigi.Parameter(default='TTToSemiLeptonic:mc,DY_NLO:mc,W:mc,EGamma:data,SingleMuon:data,Tau:data')

  def local_path(self, *path):
    return os.path.join(self.sub_dir, self.__class__.__name__, self.version, *path)

  def create_branch_map(self):
    inputs = self.input_samples.split(',')
    branches = {}
    job_id = 0
    for job_id, input in enumerate(inputs):
      branches[job_id] = input.split(':')
    return branches

  def cmssw_env(self):
    if not hasattr(self, 'cmssw_env_'):
      self.cmssw_env_ = get_cmsenv(cmssw_path=os.getenv("DEFAULT_CMSSW_BASE"))
      for var in [ 'HOME', 'ANALYSIS_PATH', 'ANALYSIS_DATA_PATH', 'X509_USER_PROXY', 'DEFAULT_CMSSW_BASE' ]:
        if var in os.environ:
          self.cmssw_env_[var] = os.environ[var]
    return self.cmssw_env_

class ProdBenchmark(BenchmarkBase, HTCondorWorkflow, law.LocalWorkflow):
  max_runtime = copy_param(HTCondorWorkflow.max_runtime, 2.0)
  maxEvents = luigi.IntParameter(default=10000, description="maximal number of events to process")
  customise = luigi.Parameter(default='NanoProd/NanoProd/customize.customize')
  era = luigi.Parameter(default='Run2_2018')

  def workflow_requires(self):
    return {}

  def requires(self):
    return {}

  def law_job_home(self):
    if 'LAW_JOB_HOME' in os.environ:
      return os.environ['LAW_JOB_HOME'], False
    os.makedirs(self.local_path(), exist_ok=True)
    return tempfile.mkdtemp(dir=self.local_path()), True

  def output(self):
    input, input_type = self.branch_data
    done_flag = self.local_path(f'{input}.done')
    return law.LocalFileTarget(done_flag)

  def run(self):
    job_home, remove_job_home = self.law_job_home()
    input, input_type = self.branch_data
    print(f'Processing {input}')
    cmd = f'python3 $ANALYSIS_PATH/RunKit/nanoProdWrapper.py customise={self.customise} maxEvents={self.maxEvents} sampleType={input_type} era={self.era} inputFiles=file:{self.input}/{input}.root writePSet=True createTar=False'
    ps_call([cmd], shell=True, env=self.cmssw_env(), cwd=job_home, verbose=1)
    cmd = '$ANALYSIS_PATH/RunKit/crabJob.sh'
    ps_call([cmd], shell=True, env=self.cmssw_env(), cwd=job_home, verbose=1)
    cmssw_output = os.path.join(job_home, 'nano_0.root')
    root_output = self.local_path(f'{input}.root')
    os.makedirs(self.local_path(), exist_ok=True)
    shutil.move(cmssw_output, root_output)
    doc_html_path = self.local_path(f'{input}.doc.html')
    size_html_path = self.local_path(f'{input}.size.html')
    cmd = f'python $ANALYSIS_PATH/RunKit/inspectNanoFile.py --doc {doc_html_path} --size {size_html_path} {root_output}'
    ps_call([cmd], shell=True, verbose=1)
    htaccess_path = self.local_path('..', '.htaccess')
    if not os.path.exists(htaccess_path):
      with open(htaccess_path, 'w') as f:
        f.write('Options +Indexes\n')
    if remove_job_home:
      shutil.rmtree(job_home)
    self.output().touch()

class SkimBenchmark(BenchmarkBase, law.LocalWorkflow):
  skimCfg = luigi.Parameter()
  skimSetup = luigi.Parameter()
  skimSetupFailed = luigi.Parameter(default='')

  def output(self):
    input, input_type = self.branch_data
    done_flag = self.local_path(f'{input}.done')
    return law.LocalFileTarget(done_flag)

  def run(self):
    input, input_type = self.branch_data
    print(f'Processing {input}')
    os.makedirs(self.local_path(), exist_ok=True)
    input_root = os.path.join(self.input, f'{input}.root')
    root_output = self.local_path(f'{input}.root')
    skim_tree_path = os.path.join(os.getenv('ANALYSIS_PATH'), 'RunKit', 'skim_tree.py')
    cmd_line = [ 'python', skim_tree_path, '--input', input_root, '--output', root_output,
                 '--config', self.skimCfg, '--setup', self.skimSetup, '--verbose', '1' ]
    ps_call(cmd_line, verbose=1)

    if len(self.skimSetupFailed) and input_type == 'mc':
      cmd_line = [ 'python', skim_tree_path, '--input', input_root, '--output', root_output,
                   '--config', self.skimCfg, '--setup', self.skimSetupFailed,
                   '--update-output', '--verbose', '1' ]
      ps_call(cmd_line, verbose=1)

    doc_html_path = self.local_path(f'{input}.doc.html')
    size_html_path = self.local_path(f'{input}.size.html')
    cmd = f'python $ANALYSIS_PATH/RunKit/inspectNanoFile.py --doc {doc_html_path} --size {size_html_path} {root_output}'
    ps_call([cmd], shell=True, verbose=1)
    htaccess_path = self.local_path('..', '.htaccess')
    if not os.path.exists(htaccess_path):
      with open(htaccess_path, 'w') as f:
        f.write('Options +Indexes\n')
    os.remove(root_output)
    shutil.copyfile(self.skimCfg, self.local_path(f'{input}.yaml'))
    self.output().touch()