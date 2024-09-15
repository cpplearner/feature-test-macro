#!/usr/bin/env python3
import argparse, logging, sys, textwrap, yaml
from utilities import kinds, standards, infer_std

def find_std_value(name):
    for stdname, value in standards:
        if stdname == name:
            return value

parser = argparse.ArgumentParser()
parser.add_argument('kind', choices=kinds, help='Table to generate')
parser.add_argument('-o', dest='outfilename', help='Output file name (use stdout if omitted)')
parser.add_argument('--disable-warning', action='store_true')
args = parser.parse_args()

out = open(args.outfilename, 'w', encoding='utf-8') if args.outfilename else sys.stdout
if args.disable_warning:
    logging.disable(logging.WARNING)

a = yaml.safe_load(open('data.yaml', encoding='utf-8'))

if args.kind == 'attributes':
    logging.critical("unimplemented")
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
                    logging.warning(textwrap.dedent(f'''\
                        invalid DR for {item["name"]}
                          standard: {row["std"]}
                          printing: {row["value"]}'''))
                elif prev and find_std_value(prev['std']) > stdvalue:
                    logging.warning(textwrap.dedent(f'''\
                        invalid DR for {item["name"]}
                          standard: {row["std"]}
                          printing: {row["value"]}
                          previous: {prev["std"]}, {prev["value"]}'''))
            else:
                row['std'] = infer_std(row)

                if prev and prev['std'] == row['std'] and row['std'] != standards[-1][0]:
                    logging.warning(textwrap.dedent(f'''\
                        there is a newer value for {item["name"]}
                          standard: {row["std"]}
                          printing: {row["value"]}
                          previous value: {prev["value"]}
                          support:
                        ''') + textwrap.indent(yaml.safe_dump(item['support']), '    '))

            row['papers'] = papers
            rows.append(row)
            papers = []

    for index, row in enumerate(rows):
        if index == 0:
            out.write(f'|- id="{item["name"][2:]}"\n')
            if len(rows) > 1:
                out.write(f'| rowspan="{len(rows)}" | ')
            else:
                out.write('| ')
            length_threshold = 30
            if len(item['name']) > length_threshold:
                break_point = item['name'].find('_', 15, 25) + 1
                if break_point == 0:
                    break_point = item['name'].find('_', 10, 30) + 1
                if break_point == 0:
                    logging.error(f'cannot find a break point for {item["name"]}')
                out.write(f'{{{{tt|1={item["name"][:break_point]}{{{{br}}}}{item["name"][break_point:]}}}}} |')
            else:
                out.write(f'{{{{tt|{item["name"]}}}}} |')
        else:
            out.write('|-\n')

        out.write(f'| {row["cppreference-description"]}')

        out.write(f' || {{{{c|{row["value"]}L}}}}')

        if args.kind == 'library':
            if 'cppreference-header_list' in row:
                header_list = row['cppreference-header_list'].split(' ')
            elif 'header_list' in item:
                header_list = item['header_list'].split(' ')
            else:
                header_list = ''

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

if args.kind == 'library':
    out.write(f'! colspan="{colspan}" | Total number of macros: {len(viable_macros)} <!-- do not forget to update, see the talk page -->\n')
else:
    out.write(f'! colspan="{colspan}" | Total number of macros: {len(viable_macros)} <!-- update me, e.g., use the script on the talk page -->\n')

out.write('|}')

