# C++ Feature-Test Macros

This repo contains data for C++ feature-test macros, including

- list of feature-test macros and their values, extracted from https://github.com/BRevzin/sd6
- short description for each macro, extracted from https://en.cppreference.com/w/cpp/feature_test
- Clang/GCC/MSVC (and their standard library implementation) support for each macro, sourced from testing and the source code

This repo only attempts to track the latest master versions of [Clang](https://github.com/llvm/llvm-project/)/[GCC](https://gcc.gnu.org/git/?p=gcc.git;a=tree)/[MSVC STL](github.com/microsoft/STL/), not any particular release. For MSVC compiler, the latest release is tracked.

All data are located in the [`data.yaml`](./data.yaml) file.

## Tools

This repo also contains Python scripts for various purposes, located in the [`tools/`](./tools) directory. These include

- [`generate_testfiles.py`](./tools/generate_testfiles.py), for generating files that can be used to check feature-test macro support for each implementation. Macros are grouped by their kinds. This is mostly useful for manual testing.
  The generated test files can be identified as `test/{kind}/{impl}.cpp`, where `{kind}` is one of `attribute`/`language`/`library`, `{impl}` is one of `clang`/`gcc`/`msvc`. (`test/library/clang.cpp` and `test/library/gcc.cpp` test for libc++ and libstdc++ respectively, although these libraries can work with different compilers.) 
- [`do_test.py`](./tools/do_test.py), for automatically checking feature-test macro support.
- [`maketable_cppreference.py`](./tools/maketable_cppreference.py), which generates wikicode for language/library tables that can be used in https://en.cppreference.com/w/cpp/feature_test.

In addition, there's `utilities.py`, which contains utility variables/functions/classes for internal use.

These scripts must be invoked from the project root (the directory that contains `data.yaml`).
