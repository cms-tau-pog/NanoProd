import subprocess
import sys
import os
import yaml

def sh_call(cmd, shell=False, catch_stdout=False, decode=True, split=None, expected_return_codes = [ 0 ], verbose=0):
    cmd_str = []
    for s in cmd:
        if ' ' in s:
            s = f"'{s}'"
        cmd_str.append(s)
    cmd_str = ' '.join(cmd_str)
    if verbose > 0:
        print(f'>> {cmd_str}', file=sys.stderr)
    kwargs = {
        'shell': shell,
    }
    if catch_stdout:
        kwargs['stdout'] = subprocess.PIPE
    proc = subprocess.Popen(cmd, **kwargs)
    output, err = proc.communicate()
    if proc.returncode not in expected_return_codes:
        raise RuntimeError(f'Error while running "{cmd_str}". Error code: {proc.returncode}')
    if catch_stdout and decode:
        output_decoded = output.decode("utf-8")
        if split is None:
            output = output_decoded
        else:
            output = [ s for s in output_decoded.split(split) if len(s) > 0 ]
    return proc.returncode, output


input_file = sys.argv[1]
output_file = sys.argv[2]
store_failed = sys.argv[3] == 'True'

skim_cfg_path = os.path.join(os.environ['CMSSW_BASE'], 'src', 'NanoProd', 'NanoProd', 'data', 'skim.yaml')
with open(skim_cfg_path, 'r') as f:
    skim_config = yaml.safe_load(f)

selection = skim_config['selection']
skim_tree_path = os.path.join(os.environ['CMSSW_BASE'], 'python', 'NanoProd', 'NanoProd', 'skim_tree.py')
cmd_line = ['python3', skim_tree_path, '--input', input_file, '--output', output_file, '--input-tree', 'Events',
            '--other-trees', 'LuminosityBlocks,Runs', '--verbose', '1']

if 'selection' in skim_config:
    selection = skim_config['selection']
    cmd_line.extend(['--sel', selection])

if 'column_filters' in skim_config:
    columns = ','.join(skim_config['column_filters'])
    cmd_line.extend([f'--column-filters', columns])

sh_call(cmd_line, verbose=1)

if store_failed:
    if 'selection' not in skim_config:
        raise RuntimeError('store_failed=True, but selection is not specified.')
    cmd_line = ['python3', skim_tree_path, '--input', input_file, '--output', output_file, '--input-tree', 'Events',
                '--output-tree', 'EventsNotSelected', '--update-output', '--sel', selection, '--invert-sel',
                '--verbose', '1']

    if 'column_filters_for_failed' in skim_config:
        columns = ','.join(skim_config['column_filters_for_failed'])
        cmd_line.extend([f'--column-filters', columns])

    sh_call(cmd_line, verbose=1)
