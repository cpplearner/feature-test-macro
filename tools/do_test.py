#!/usr/bin/env python3
import argparse, subprocess, yaml, pathlib, sys
from utilities import kinds, implementations, standards, library_prologue, std_options, TestsuiteGenerator

def do_test(impl, kind, cc, extra_args, enabled_std, dry_run, verbose):
    test_std_opts = [std_opt for std, std_opt in std_options(impl) if std in enabled_std]
    compiler, diag_opt = cc, []
    if cc == None:
        if impl == 'clang':
            compiler, diag_opt = 'clang', ['-fno-caret-diagnostics']
        elif impl == 'gcc':
            compiler, diag_opt = 'gcc', ['-fno-diagnostics-show-caret', '-ftrack-macro-expansion=0']
        elif impl == 'msvc':
            compiler, diag_opt = 'cl.exe', ['-nologo', '-Zc:__cplusplus']

    if dry_run:
        print('Dry run...')

    a = yaml.safe_load(open('data.yaml', encoding='utf-8'))
    assert list(a.keys()) == kinds

    testbasedir = pathlib.Path('test/individuals')
    if dry_run:
        print('Would create directory', testbasedir)
    else:
        testbasedir.mkdir(parents=True, exist_ok=True)

    exitcode = 0

    for macro in a[kind]:
        if 'removed' in macro['rows'][-1]:
            continue

        generator = TestsuiteGenerator(kind, impl)
        output = library_prologue if kind == 'library' else ''

        s = f'"{macro["name"]}": '
        output += f'\n{s}{generator.test_expr(macro["name"])}\n'

        generator.generate_test_item(macro)
        output += generator.output

        testfile = str(testbasedir / f'{macro["name"]}.cpp')
        if dry_run:
            print('Would create', testfile)
        else:
            open(testfile, 'w', encoding='ascii').write(output)

        compiler_args = []
        for std_opt in test_std_opts:
            for opts in generator.make_options(macro):
                pedantic = generator.pedantic_options(macro) or [None]
                for ped_opt in pedantic:
                    compiler_args.append([std_opt] + ([ped_opt] if ped_opt else []) + opts)

        for args in compiler_args:
            run = [compiler, '-E', *diag_opt, *extra_args, *args, testfile]
            if dry_run or verbose:
                print('+', *run)
            if not dry_run:
                res = subprocess.run(run, capture_output=True, text=True)
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
                exitcode = exitcode or res.returncode
    return exitcode

standards = [std for std, __cplusplus in standards]

parser = argparse.ArgumentParser()
parser.add_argument('args', nargs='*', choices=[*implementations, *kinds], help='Implementation and kind of feature-test macros to test')
parser.add_argument('--cc', help='''Path that identifies the compiler executable.
                                    This defaults to the name of implementation to test, but the default is likely wrong,
                                    especially when testing library feature-test macros.''')
parser.add_argument('--extra-args', nargs=argparse.REMAINDER, help='Extra arguments to the compiler.')
parser.add_argument('--std', nargs='+', choices=standards, default=standards, help='Standards to test.')
parser.add_argument('-n', '--dry-run', action='store_true', help='Show how the compiler is invoked, without actually invoking')
parser.add_argument('--verbose', action='store_true', help='Show how the compiler is invoked before invoking')
args = parser.parse_args()
[impl] = [arg for arg in args.args if arg in implementations]
[kind] = [arg for arg in args.args if arg in kinds]

exitcode = do_test(impl, kind, args.cc, args.extra_args or [], args.std, args.dry_run, args.verbose)
sys.exit(exitcode)

