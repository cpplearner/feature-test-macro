#!/usr/bin/env python3
import yaml, pathlib
from utilities import kinds, implementations, standards, library_prologue, std_options, TestsuiteGenerator

a = yaml.safe_load(open('data.yaml'))
assert list(a.keys()) == kinds

testbasedir = pathlib.Path('test')
testbasedir.mkdir(exist_ok=True)

for kind in kinds:
    for impl in implementations:
        testdir = testbasedir / kind
        testdir.mkdir(exist_ok=True)

        testfile = open(testdir / f"{impl}.cpp", 'w+')

        generator = TestsuiteGenerator(kind, impl)

        opts = set()
        pedantic_options = None
        for macro in a[kind]:
            opts |= {tuple(x) for x in generator.make_options(macro)}
            if pedantic_options is None:
                pedantic_options = generator.pedantic_options(macro)

        if pedantic_options is not None:
            opts = {('-pedantic', *opt) for opt in opts} | {(opt,) for opt in pedantic_options}

        if opts != {()}:
            testfile.write("// Run with options:\n")
            for options in sorted(list(opts)):
                testfile.write(f"//    {' '.join(options)}\n")

        if kind == 'library':
            testfile.write(library_prologue)

        for macro in a[kind]:
            if 'removed' not in macro['rows'][-1]:
                generator.generate_test_item(macro)
        testfile.write(generator.output)

