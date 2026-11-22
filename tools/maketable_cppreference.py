#!/usr/bin/env python3
import argparse, sys, yaml
from utilities import kinds, standards, infer_std

def find_std_value(name):
    for stdname, value in standards:
        if stdname == name:
            return value

parser = argparse.ArgumentParser()
parser.add_argument('kind', choices=kinds, help='Table to generate')
parser.add_argument('-o', dest='outfilename', help='Output file name (use stdout if omitted)')
args = parser.parse_args()

out = open(args.outfilename, 'w', encoding='utf-8') if args.outfilename else sys.stdout

doc = yaml.safe_load(open('data.yaml', encoding='utf-8'))

if args.kind == 'attributes':
    exit()
elif args.kind == 'language':
    out.write("""\
{|class="wikitable sortable" style="font-size: 90%;"
|-{{#vardefine:counter|0}}
!style="width: 0"|Macro name
!Feature
!<abbr title="The year/month in which this feature was adopted. The hyperlink under each value opens a compiler support page with an entry for that feature.">Value</abbr>
!<abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
!Paper(s)

""")
elif args.kind == 'library':
    out.write("""\
{| class="wikitable sortable" style="font-size: 90%;"
|-{{#vardefine:counter|0}}
!style="width: 0"|Macro name
!Feature
!<abbr title="The year/month in which this feature was adopted. The hyperlink under each value opens a compiler support page with an entry for that feature.">Value</abbr>
!<abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr>
!Paper(s)

""")

macros = doc[args.kind]
for item in macros:
    rows = []
    papers = []
    for row in item['rows']:
        if 'papers' in row:
            papers += row['papers'].split()

        if 'cppreference-description' in row:
            row['std'] = infer_std(row)
            row['papers'] = papers
            rows.append(row)
            papers = []

    prev_std_span = 0
    for index, row in enumerate(rows):
        out.write('{{ftm_row\n')

        if index == 0:
            out.write(f'|{item["name"]}')
            if len(rows) > 1:
                out.write(f'|ftm_span="{len(rows)}"\n')
            else:
                out.write('\n')
        else:
            out.write('|\n')

        out.write(f'|{row["cppreference-description"]}\n')
        out.write(f'|{row["value"]}L\n')
        if prev_std_span > 0:
            prev_std_span -= 1
            out.write('|\n')
        else:
            out.write(f'|{row["std"][-2:]}')
            std_span = 1
            for j in range(index + 1, len(rows)):
                dr = row.get('cppreference-treats-as-dr-against', '')
                j_dr = rows[j].get('cppreference-treats-as-dr-against', '')
                if row['std'] != rows[j]['std'] or dr != j_dr:
                    break
                std_span += 1

            if std_span > 1:
                out.write(f'|std_span="{std_span}"')

            if 'cppreference-treats-as-dr-against' in row:
                out.write(f'|dr={row["cppreference-treats-as-dr-against"][-2:]}')

            out.write('\n')

            prev_std_span = std_span - 1

        out.write(f'|{' '.join(row["papers"])}\n')
        out.write('}}\n\n')

out.write("""\
|-
!colspan="5"|Total number of macros: {{#var:counter}}
|}

""")

