#!/usr/bin/env python3
import argparse, sys, textwrap, yaml
from utilities import kinds, standards

def find_std_value(name):
    for stdname, value in standards:
        if stdname == name:
            return value

parser = argparse.ArgumentParser()
parser.add_argument('kind', choices=kinds, help='Table to generate')
parser.add_argument('-o', dest='outfilename', help='Output file name (use stdout if omitted)')
args = parser.parse_args()

out = open(args.outfilename, 'w') if args.outfilename else sys.stdout

a = yaml.safe_load(open('data.yaml'))

if args.kind == 'attributes':
    print("sorry, unimplemented", file=sys.stderr)
    exit()
elif args.kind == 'language':
    out.write("""\
{| class="wikitable sortable" style="font-size:90%;"
|-
! style="width:0" | Macro name
! Feature
! Value
! <abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
! Paper(s)
""")
elif args.kind == 'library':
    out.write("""\
{| class="wikitable sortable" style="font-size:90%;"
|-
! style="width:0" | Macro name
! Feature
! Value
! Header
! <abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
! Paper(s)
""")

macros = [item for item in a[args.kind] if 'removed' not in item['rows'][-1]]
for item in macros:
    rows = []
    papers = []
    for row in item['rows']:
        if 'papers' in row:
            papers += row['papers'].split()

        if 'cppreference-description' in row:
            prev = rows[-1] if len(rows) > 0 else None
            if 'cppreference-treats-as-dr-against' in row:
                row['std'] = row['cppreference-treats-as-dr-against']
                stdvalue = find_std_value(row['std'])
                if row['value'] <= stdvalue:
                    print(f'warning: invalid DR for {item["name"]}', file=sys.stderr)
                    print(f'  standard: {row["std"]}', file=sys.stderr)
                    print(f'  printing: {row["value"]}', file=sys.stderr)
                elif prev and find_std_value(prev['std']) > stdvalue:
                    print(f'warning: invalid DR for {item["name"]}', file=sys.stderr)
                    print(f'  standard: {row["std"]}', file=sys.stderr)
                    print(f'  printing: {row["value"]}', file=sys.stderr)
                    print(f'  previous: {prev["std"]}, {prev["value"]}', file=sys.stderr)
            else:
                nextstd = [stdname for stdname, value in standards if value is None or row['value'] <= value][0]
                row['std'] = nextstd

                if prev and prev['std'] == row['std'] and row['std'] != standards[-1][0]:
                    print(f'warning: there is a newer value for {item["name"]}', file=sys.stderr)
                    print(f'  standard: {nextstd}', file=sys.stderr)
                    print(f'  printing: {row["value"]}', file=sys.stderr)
                    print(f'  previous value: {prev["value"]}', file=sys.stderr)
                    print(f'  support:', file=sys.stderr)
                    print(textwrap.indent(yaml.safe_dump(item['support']), '    '), file=sys.stderr)

            row['papers'] = papers
            rows.append(row)
            papers = []

    for index, row in enumerate(rows):
        out.write('|-\n')
        if index == 0:
            if len(rows) > 1:
                out.write(f'| rowspan="{len(rows)}" | ')
            else:
                out.write('| ')
            length_threshold = 30
            if len(item['name']) > length_threshold:
                break_point = item['name'].find('_', 15, 25) + 1
                assert break_point != 0
                out.write(f'{{{{tt|1={item["name"][:break_point]}{{{{br}}}}{item["name"][break_point:]}}}}} |')
            else:
                out.write(f'{{{{tt|{item["name"]}}}}} |')

        out.write(f'| {row["cppreference-description"]}')

        out.write(f' || {{{{c|{row["value"]}L}}}}')

        if args.kind == 'library':
            if 'cppreference-header_list' in row:
                header_list = row['cppreference-header_list'].split(' ')
            elif 'header_list' in item:
                header_list = item['header_list'].split(' ')
            else:
                header_list = ''
                assert item['name'] == '__cpp_lib_modules'

            if len(header_list) > 2 and len(rows) > 1 and not any('cppreference-header_list' in row for row in rows):
                if index == 0:
                    out.write(f' || rowspan="{len(rows)}" | ')
                    out.write(' '.join(f'{{{{header|{hdr}}}}}' for hdr in header_list))
            else:
                out.write(' || ')
                out.write(' '.join(f'{{{{header|{hdr}}}}}' for hdr in header_list))

        out.write(f' || {{{{mark {row["std"].lower()}}}}}')
        if 'cppreference-treats-as-dr-against' in row:
            out.write(f'<br>{{{{mark|DR}}}}')

        papers = '<br>'.join(f'{{{{stddoc|{paper}}}}}' for paper in row['papers'])
        out.write(f' || {papers}\n')

out.write('|-\n')
colspan = 6 if args.kind == 'library' else 5
viable_macros = [item for item in macros if any('cppreference-description' in row for row in item['rows'])]
out.write(f'! colspan="{colspan}" | Total number of macros: {len(viable_macros)} <!-- do not forget to update -->\n')

out.write('|}')

