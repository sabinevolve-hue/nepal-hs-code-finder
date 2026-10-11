#!/usr/bin/env python3
"""Per-HS6 global top exporters/importers from BACI (CEPII, HS-6 bilateral, reconciled Comtrade).
Usage: world_products.py <BACI_year.csv> <country_codes.csv> <out.json>
Output: {"<hs6>": {"x":[[iso3, value_musd], ...top6], "m":[...top6], "w": world_total_musd}, ...}
Values in millions of current USD (BACI 'v' is thousand USD; /1000).  Run isolated (-I)."""
import sys, csv, json
from collections import defaultdict

TRADE, COUNTRIES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

iso = {}
with open(COUNTRIES, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        try: iso[int(r['country_code'])] = r['country_iso3'] or r['country_code']
        except (ValueError, KeyError): pass

exp = defaultdict(lambda: defaultdict(float))   # k -> exporter -> value
imp = defaultdict(lambda: defaultdict(float))   # k -> importer -> value
world = defaultdict(float)
n = 0
with open(TRADE, encoding='utf-8') as fh:
    rd = csv.reader(fh); next(rd, None)          # header t,i,j,k,v,q
    for row in rd:
        try:
            i, j, k, v = int(row[1]), int(row[2]), row[3].strip().zfill(6), float(row[4])
        except (ValueError, IndexError):
            continue
        exp[k][i] += v; imp[k][j] += v; world[k] += v
        n += 1
        if n % 2_000_000 == 0: sys.stderr.write(f'...{n:,} rows\n')

def top(d, n=6):
    return [[iso.get(c, str(c)), round(val / 1000)] for c, val in
            sorted(d.items(), key=lambda t: -t[1])[:n] if val > 0]

out = {}
for k in world:
    out[k] = {'x': top(exp[k]), 'm': top(imp[k]), 'w': round(world[k] / 1000)}

json.dump(out, open(OUT, 'w'), separators=(',', ':'))
import os
print(f'rows {n:,} | products {len(out):,} | {os.path.getsize(OUT)/1024:.0f} KB')
# sanity
for code in ('090111', '851713', '870321', '100630'):
    r = out.get(code)
    if r: print(code, 'exporters:', [(c, f'${v/1000:.1f}B') for c, v in r['x'][:4]])
