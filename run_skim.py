import subprocess
import sys
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

with open('skim.yaml', 'r') as f:
    skim_config = yaml.safe_load(f)
exclude_columns = ','.join(skim_config['exclude_columns'])
selection = skim_config['selection']

sh_call(['python3', 'skim_tree.py', '--input', input_file, '--output', output_file, '--input-tree', 'Events',
         '--other-trees', 'LuminosityBlocks,Runs', '--exclude-columns', exclude_columns, '--sel', selection,
         '--verbose', '1'], verbose=1)
