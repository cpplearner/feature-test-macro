#!/usr/bin/env python3
import argparse, subprocess, yaml, pathlib
from utilities import kinds, implementations, library_prologue, std_options, nonpedantic_option, TestsuiteGenerator

parser = argparse.ArgumentParser()
parser.add_argument('impl', choices=implementations, help='Implementation to test')
parser.add_argument('kind', choices=kinds, help='Kind of feature-test macros to test')
parser.add_argument('--cc', help='''Path that identifies the compiler executable.
                                    This defaults to the name of implementation to test, but the default is likely wrong,
                                    especially when testing library feature-test macros.''')
parser.add_argument('--extra-args', nargs=argparse.REMAINDER, help='Extra arguments to the compiler.')
parser.add_argument('-n', '--dry-run', action='store_true', help='Show how the compiler is invoked, without actually invoking')
parser.add_argument('--verbose', action='store_true', help='Show how the compiler is invoked before invoking')
args = parser.parse_args()

dry_run = args.dry_run
verbose = args.verbose
if dry_run:
    print('Dry run...')

impl = args.impl
kind = args.kind
cc = args.cc
extra_args = args.extra_args or []

a = yaml.safe_load(open('data.yaml'))
assert list(a.keys()) == kinds

def run_test(args, testfilename):
    compiler, diag_opt = cc, []
    if cc == None:
        if impl == 'clang':
            compiler, diag_opt = 'clang', ['-fno-caret-diagnostics']
        elif impl == 'gcc':
            compiler, diag_opt = 'gcc', ['-fno-diagnostics-show-caret']
        elif impl == 'msvc':
            compiler, diag_opt = 'cl', ['-nologo', '-Zc:__cplusplus']
    run = [compiler, '-E', *diag_opt, *extra_args, *args, str(testfilename)]
    if dry_run or verbose:
        print('+', *run)
    if not dry_run:
        res = subprocess.run(run, capture_output=True, encoding='utf-8')
        stderr = res.stderr
        if cc == None and impl == 'msvc':
            stderr = stderr[stderr.index('\n')+1:]
        if stderr.strip() != '':
            print(stderr.strip())
            print('compiler options: ', args)
            stdout = res.stdout
            if s in stdout:
                line = stdout.index(s)
                print(stdout[line:stdout.index('\n', line)])

testbasedir = pathlib.Path('test/individuals')
if dry_run:
    print('Would touch', testbasedir)
else:
    testbasedir.mkdir(parents=True, exist_ok=True)

for macro in a[kind]:
    if 'removed' in macro['rows'][-1]:
        continue
    output = library_prologue if kind == 'library' else ''
    s = f'"{macro["name"]}": '
    if kind == 'attributes':
        output += f'\n{s}__has_cpp_attribute({macro["name"]})\n'
    else:
        output += f'\n{s}{macro["name"]}\n'

    generator = TestsuiteGenerator(kind, impl)
    generator.generate_test_item(macro)
    output += generator.output

    outfilepath = testbasedir / f'{macro["name"]}.cpp'
    if dry_run:
        print('Would create', outfilepath)
    else:
        open(outfilepath, 'w').write(output)

    for std, std_opt in std_options(impl):
        for args in generator.make_options(macro):
            pedantic = generator.pedantic_options(macro) or [None]
            for ped_opt in pedantic:
                run_test(filter(bool, [std_opt, ped_opt, *args]), str(outfilepath))

