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
! <abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
""")
elif args.kind == 'library':
    out.write("""\
{| class="wikitable sortable"
|-
! Macro name
! Feature
! Value
! Header
! <abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
""")

for item in a[args.kind]:
    if 'removed' in item['rows'][-1]:
        continue

    stdrevmap = {}

    rows = [row for row in item['rows'] if 'cppreference-description' in row]
    for index, row in enumerate(rows):
        out.write('|-\n')
        if index == 0:
            if len(rows) > 1:
                out.write(f'| rowspan="{len(rows)}" | ')
            else:
                out.write('| ')
            length_threshold = 31 if args.kind == 'language' else 30
            if len(item['name']) > length_threshold:
                break_opportunity = item['name'].find('_', 15) + 1
                if break_opportunity == 0 or break_opportunity > 25:
                    print(item['name'], file=sys.stderr)
                    break_opportunity = item['name'].rfind('_', 0, 15) + 1
                out.write(f'{{{{c|{item["name"][:break_opportunity]}}}}}')
                out.write(f'{{{{c|{item["name"][break_opportunity:]}}}}} |')
            else:
                out.write(f'{{{{c|{item["name"]}}}}} |')
        out.write(f'| {row["cppreference-description"]}')
        out.write(f' || {{{{c|{row["value"]}L}}}}')
        if args.kind == 'library':
            out.write(' || ')
            if 'header_list' in item:
                out.write(' '.join(f'{{{{header|{hdr}}}}}' for hdr in item['header_list'].split(' ')))
            else:
                assert item['name'] == '__cpp_lib_modules'

        if 'cppreference-treats-as-dr-against' in row:
            stdname = row['cppreference-treats-as-dr-against']
            out.write(f' || {{{{mark {stdname.lower()}}}}}{{{{mark|DR}}}}\n')
            stdvalue = [value for std, value in standards if std == stdname][0]

            stdrevmap[tuple(row)] = stdname, stdvalue

            if row['value'] <= stdvalue:
                print(f'warning: invalid DR for {item["name"]}', file=sys.stderr)
                print(f'  standard: {stdname}', file=sys.stderr)
                print(f'  printing: {row["value"]}', file=sys.stderr)
                print(f'  support: {item["support"]}', file=sys.stderr)
            elif index > 0:
                prevrow = rows[index - 1]
                prevstd = stdrevmap[tuple(prevrow)]
                if prevstd[1] > stdvalue:
                    print(f'warning: invalid DR for {item["name"]}', file=sys.stderr)
                    print(f'  standard: {stdname}', file=sys.stderr)
                    print(f'  printing: {row["value"]}', file=sys.stderr)
                    print(f'  previous: {prevstd[0]}, {prevrow["value"]}', file=sys.stderr)
                    print(f'  support: {item["support"]}', file=sys.stderr)
        else:
            def standard_around(value):
                previous = None
                for std in standards:
                    name, __cplusplus = std
                    if __cplusplus is None or value <= __cplusplus:
                        return {'previous': previous, 'next': std}
                    previous = std

            nextstd = standard_around(row['value'])['next']
            out.write(f' || {{{{mark {nextstd[0].lower()}}}}}\n')

            stdrevmap[tuple(row)] = nextstd

            if nextstd[1]:
                last_value = [r for r in item['rows'] if r['value'] <= nextstd[1]][-1]
            else:
                last_value = item['rows'][-1]
            if row is not last_value:
                print(f'warning: there is a newer value for {item["name"]}', file=sys.stderr)
                print(f'  standard: {nextstd[0]}', file=sys.stderr)
                print(f'  printing: {row["value"]}', file=sys.stderr)
                print(f'  new value: {last_value["value"]}', file=sys.stderr)
                print(f'  support: {item["support"]}', file=sys.stderr)

out.write('|}')

