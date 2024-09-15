#!/usr/bin/env python3
import argparse, re, sys, yaml

parser = argparse.ArgumentParser()
parser.add_argument('input_filename', help='libstdc++ version.def file')
parser.add_argument('output_filename', help='output file name')

args = parser.parse_args()

s = open(args.input_filename, encoding='ascii').read()

s = re.sub(r'//.*?\n', '', s)
s = re.sub(r'/\*.*?\*/', '', s)
s = re.sub(r'AutoGen Definitions.*;', '', s)

s = s.strip()

tokens = []

while s:
    match = re.match(r'\w+|".*?"', s)
    if match:
        word = match.group()
        tokens.append(word)
        s = s[len(word):].lstrip()
    else:
        tok = s[0]
        tokens.append(tok)
        s = s[1:].lstrip()


def recursive_parse_definitions():
    result = dict()

    global tokens

    while tokens and re.fullmatch(r'\w+', tokens[0]):
        pos = tokens.index('=')
        itemname = ''.join(tokens[:pos])

        tokens = tokens[pos+1:]

        if tokens[0] == '{':
            result.setdefault(itemname, [])
            tokens = tokens[1:]
            parsed = recursive_parse_definitions()
            assert tokens[0] == '}'
            assert tokens[1] == ';'
            tokens = tokens[2:]
            result[itemname].append(parsed)
        else:
            pos = tokens.index(';')
            if pos != 1:
                assert tokens[0].startswith('"')

            assert itemname not in result
            result[itemname] = ''.join(tokens[:pos])
            tokens = tokens[pos+1:]

    return result


raw = recursive_parse_definitions()

with open('data.yaml', encoding='utf-8') as data:
    a = yaml.safe_load(data)

    for ftm in raw['ftms']:
        name = f"__cpp_lib_{ftm['name']}"

        mac = None
        for x in a['library']:
            if x['name'] == name:
                mac = x

        if not mac:
            print(f"warning: cannot find macro {name}", file=sys.stderr)

        if mac:
            support = []
            for value in ftm['values']:
                row = dict()

                if 'cxxmin' in value:
                    row['since'] = f"C++{value['cxxmin']}"

                depends = []
                if 'gthread' in value:
                    if value['gthread'] == 'yes':
                        depends.append('defined(_GLIBCXX_HAS_GTHREADS)')
                    else:
                        assert value['gthread'] == 'no'
                        depends.append('!defined(_GLIBCXX_HAS_GTHREADS)')

                if 'cxx11abi' in value:
                    if value['cxx11abi'] == 'yes':
                        depends.append('_GLIBCXX_USE_CXX11_ABI')
                    else:
                        assert value['cxx11abi'] == 'no'
                        depends.append('!_GLIBCXX_USE_CXX11_ABI')

                if 'extra_cond' in value:
                    extra_cond = value['extra_cond']
                    extra_cond = re.sub('"', '', extra_cond)
                    extra_cond = re.sub('__glibcxx_', '__cpp_lib_', extra_cond)
                    depends.append(extra_cond)

                if depends:
                    row['depends'] = ' && '.join(depends)

                row['value'] = int(value['v'])

                support.append(row)

            support.reverse()
            mac['support']['gcc'] = support

yaml.safe_dump(a, open(args.output_filename, 'w', encoding='utf-8'), sort_keys=False)
