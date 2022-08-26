#!/usr/bin/env python

import argparse
import os
import re
from threading import active_count

parser = argparse.ArgumentParser(description='Skim tree.')
parser.add_argument('--input', required=True, type=str, help="input root file or txt file with a list of files")
parser.add_argument('--output', required=True, type=str, help="output root file")
parser.add_argument('--input-tree', required=True, type=str, help="input tree name")
parser.add_argument('--output-tree', required=False, type=str, default=None, help="output tree")
parser.add_argument('--other-trees', required=False, default=None, help="other trees to copy")
parser.add_argument('--sel', required=False, type=str, default=None, help="selection")
parser.add_argument('--invert-sel', action="store_true", help="Invert selection.")
parser.add_argument('--column-filters', required=False, default=None, type=str,
                    help="""Comma separated statements to keep and drop columns based on exact names or regex patterns.
                            By default, all columns will be included""")
parser.add_argument('--input-prefix', required=False, type=str, default='',
                    help="prefix to be added to input each input file")
parser.add_argument('--processing-module', required=False, type=str, default=None,
                    help="Python module used to process DataFrame. Should be in form file:method")
parser.add_argument('--comp-algo', required=False, type=str, default='LZMA', help="compression algorithm")
parser.add_argument('--comp-level', required=False, type=int, default=9, help="compression level")
parser.add_argument('--n-threads', required=False, type=int, default=None, help="number of threads")
parser.add_argument('--input-range', required=False, type=str, default=None,
                    help="read only entries in range begin:end (before any selection)")
parser.add_argument('--output-range', required=False, type=str, default=None,
                    help="write only entries in range begin:end (after all selections)")

parser.add_argument('--update-output', action="store_true", help="Update output file instead of overriding it.")
parser.add_argument('--verbose', required=False, type=int, default=3, help="number of threads")
args = parser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)

if args.n_threads is None:
    if args.input_range is not None or args.output_range is not None:
        args.n_threads = 1
    else:
        args.n_threads = 4

if args.n_threads > 1:
    ROOT.ROOT.EnableImplicitMT(args.n_threads)
column_filters = []
if args.column_filters is not None:
    column_filters = [ c.strip() for c in args.column_filters.split(',') if len(c.strip()) > 0 ]

inputs = ROOT.vector('string')()
if args.input.endswith('.root'):
    inputs.push_back(args.input_prefix + args.input)
    print("Adding input '{}'...".format(args.input))
elif args.input.endswith('.txt'):
    with open(args.input, 'r') as input_list:
        for name in input_list.readlines():
            name = name.strip()
            if len(name) > 0 and name[0] != '#':
                inputs.push_back(args.input_prefix + name)
                if args.verbose > 1:
                    print("Adding input '{}'...".format(name))
elif os.path.isdir(args.input):
    for f in os.listdir(args.input):
        if not f.endswith('.root'): continue
        file_name = os.path.join(args.input, f)
        inputs.push_back(file_name)
        if args.verbose > 1:
            print("Adding input '{}'...".format(file_name))
else:
    raise RuntimeError("Input format is not supported.")

df = ROOT.RDataFrame(args.input_tree, inputs)

if args.input_range is not None:
    begin, end = [ int(x) for x in args.input_range.split(':') ]
    df = df.Range(begin, end)

if args.processing_module is not None:
    module_desc = args.processing_module.split(':')
    import imp
    module = imp.load_source('processing', module_desc[0])
    fn = getattr(module, module_desc[1])
    df = fn(df)

def name_match(column, pattern):
    if pattern[0] == '^':
        return re.match(pattern, column) is not None
    return column == pattern

all_columns = [ str(c) for c in df.GetColumnNames() ]
selected_columns = { c for c in all_columns }
excluded_columns = set()
keep_prefix = "keep "
drop_prefix = "drop "
used_filters = set()
for c_filter in column_filters:
    if c_filter.startswith(keep_prefix):
        keep = True
        columns_from = excluded_columns
        columns_to = selected_columns
        prefix = keep_prefix
    elif c_filter.startswith(drop_prefix):
        keep = False
        columns_from = selected_columns
        columns_to = excluded_columns
        prefix = drop_prefix
    else:
        raise RuntimeError(f'Unsupported filter = "{c_filter}".')
    pattern = c_filter[len(prefix):]
    if len(pattern) == 0:
        raise RuntimeError(f'Filter with an empty pattern expression.')

    to_move = [ c for c in columns_from if name_match(c, pattern)]
    if len(to_move) > 0:
        used_filters.add(c_filter)
        for column in to_move:
            columns_from.remove(column)
            columns_to.add(column)

branches = ROOT.vector('string')()
for column in all_columns:
    if column in selected_columns:
        branches.push_back(column)
        if args.verbose > 2:
            print("Adding column '{}'...".format(column))

unused_filters = []
for c_filter in column_filters:
    if c_filter not in used_filters:
        unused_filters.append(c_filter)
if len(unused_filters) > 0:
    print("Unused column filters: " + " ".join(unused_filters))

if args.sel is not None:
    if args.invert_sel:
        df = df.Define('__passSkimSel', args.sel).Filter('!__passSkimSel')
    else:
        df = df.Filter(args.sel)

if args.output_range is not None:
    begin, end = [ int(x) for x in args.output_range.split(':') ]
    df = df.Range(begin, end)

if args.verbose > 0:
    print("Creating a snapshot...")
opt = ROOT.RDF.RSnapshotOptions()
opt.fCompressionAlgorithm = getattr(ROOT.ROOT, 'k' + args.comp_algo)
opt.fCompressionLevel = args.comp_level
if args.output_tree is None:
    args.output_tree = args.input_tree
if args.update_output:
    opt.fMode = 'UPDATE'
df.Snapshot(args.output_tree, args.output, branches, opt)

if args.other_trees is not None:
    other_trees = args.other_trees.split(',')
    for tree_name in other_trees:
        if args.verbose > 0:
            print("Copying {}...".format(tree_name))
        other_df = ROOT.RDataFrame(tree_name, inputs)
        branches = ROOT.vector('string')()
        for column in other_df.GetColumnNames():
            branches.push_back(column)
            if args.verbose > 2:
                print("\tAdding column '{}'...".format(column))
        opt.fMode = 'UPDATE'
        other_df.Snapshot(tree_name, args.output, branches, opt)

if args.verbose > 0:
    print("Skim successfully finished.")
