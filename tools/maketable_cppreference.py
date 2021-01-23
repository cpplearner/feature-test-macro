#!/usr/bin/env python3
import argparse, sys, yaml
from utilities import kinds, standards

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
{| class="wikitable sortable"
|-
! Macro name
! Feature
! Value
! <abbr title="Standard in which the feature is introduced">Std</abbr>
""")
elif args.kind == 'library':
    out.write("""\
{| class="wikitable sortable"
|-
! Macro name
! Feature
! Value
! Header
! <abbr title="Standard in which the feature is introduced">Std</abbr>
""")

for item in a[args.kind]:
    if 'removed' in item['rows'][-1]:
        continue
    rows = [row for row in item['rows'] if 'cppreference-description' in row]
    for index, row in enumerate(rows):
        out.write('|-\n')
        if index == 0:
            if len(rows) > 1:
                out.write(f'| rowspan="{len(rows)}" | ')
            else:
                out.write('| ')
            length_threshold = 31 if args.kind == 'language' else 30
            if len(item["name"]) > length_threshold:
                break_opportunity = item["name"].find('_', 15) + 1
                if break_opportunity == 0 or break_opportunity > 25:
                    print(item["name"], file=sys.stderr)
                    break_opportunity = item["name"].rfind('_', 0, 15) + 1
                out.write(f'{{{{c|{item["name"][:break_opportunity]}}}}}')
                out.write(f'{{{{c|{item["name"][break_opportunity:]}}}}} |')
            else:
                out.write(f'{{{{c|{item["name"]}}}}} |')
        out.write(f'| {row["cppreference-description"]}')
        out.write(f' || {{{{c|{row["value"]}L}}}}')
        if args.kind == 'library':
            out.write(' || ')
            out.write(' '.join(f'{{{{header|{hdr}}}}}' for hdr in item['header_list'].split(' ')))
        for std, __cplusplus in standards:
            if std == standards[-1][0]:
                standard = std, 999999
            elif row["value"] <= __cplusplus:
                standard = std, __cplusplus
                break
        out.write(f' || {{{{mark {standard[0].lower()}}}}}\n')

        last_value = [r for r in item['rows'] if r['value'] <= standard[1]][-1]
        if row != last_value:
            print(f'warning: there is a newer value for {item["name"]}', file=sys.stderr)
            print(f'  standard: {standard[0]}', file=sys.stderr)
            print(f'  printing: {row["value"]}', file=sys.stderr)
            print(f'  new value: {last_value["value"]}', file=sys.stderr)
            print(f'  support: {item["support"]}', file=sys.stderr)

out.write('|}')

