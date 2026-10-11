#!/usr/bin/env python3
"""From BACI (CEPII, HS-6 bilateral, reconciled Comtrade) build two files in one pass:
  prod.json  — per HS6: top-6 exporters/importers, world total, world avg unit value ($/kg)
  nepal.json — Nepal's real imports/exports by HS6 + partner, Nepal's import $/kg, and a summary
Usage: world_products.py <BACI_year.csv> <country_codes.csv> <prod.json> <nepal.json>
BACI cols: t,i,j,k,v,q  (v=thousand USD, q=metric tons; unit value v/q = USD/kg). Run isolated (-I)."""
import sys, csv, json
from collections import defaultdict

TRADE, COUNTRIES, POUT, NOUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
NPL = 524

iso = {}
with open(COUNTRIES, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        try: iso[int(r['country_code'])] = r['country_iso3'] or r['country_code']
        except (ValueError, KeyError): pass

expv = defaultdict(lambda: defaultdict(float))
impv = defaultdict(lambda: defaultdict(float))
wv, wq = defaultdict(float), defaultdict(float)
nim = defaultdict(lambda: defaultdict(float)); nimv, nimq = defaultdict(float), defaultdict(float)
nex = defaultdict(lambda: defaultdict(float)); nexv = defaultdict(float)
n = 0
with open(TRADE, encoding='utf-8') as fh:
    rd = csv.reader(fh); next(rd, None)
    for row in rd:
        try:
            i, j, k, v = int(row[1]), int(row[2]), row[3].strip().zfill(6), float(row[4])
            q = float(row[5]) if row[5] not in ('', 'NA') else 0.0
        except (ValueError, IndexError):
            continue
        expv[k][i] += v; impv[k][j] += v; wv[k] += v; wq[k] += q
        if j == NPL: nim[k][i] += v; nimv[k] += v; nimq[k] += q
        if i == NPL: nex[k][j] += v; nexv[k] += v
        n += 1
        if n % 3_000_000 == 0: sys.stderr.write(f'...{n:,}\n')

def topv(d, m=6):
    return [[iso.get(c, str(c)), round(val / 1000)] for c, val in
            sorted(d.items(), key=lambda t: -t[1])[:m] if val > 0]

# prod.json
prod = {}
for k in wv:
    o = {'x': topv(expv[k]), 'm': topv(impv[k]), 'w': round(wv[k] / 1000)}
    if wq[k] > 0:
        uv = wv[k] / wq[k]                     # thousandUSD/ton = USD/kg
        if 0 < uv < 1e6: o['u'] = round(uv, 2)
    prod[k] = o
json.dump(prod, open(POUT, 'w'), separators=(',', ':'))

# nepal.json
nepal = {}
for k in set(nimv) | set(nexv):
    o = {}
    if nimv[k] > 0:
        o['im'] = round(nimv[k] / 1000); o['ims'] = topv(nim[k], 5)
        if nimq[k] > 0:
            iu = nimv[k] / nimq[k]
            if 0 < iu < 1e6: o['iu'] = round(iu, 2)
    if nexv[k] > 0:
        o['ex'] = round(nexv[k] / 1000); o['exs'] = topv(nex[k], 5)
    nepal[k] = o
nepal['_im'] = [[k, round(nimv[k] / 1000)] for k in sorted(nimv, key=lambda k: -nimv[k])[:50] if nimv[k] > 0]
nepal['_ex'] = [[k, round(nexv[k] / 1000)] for k in sorted(nexv, key=lambda k: -nexv[k])[:50] if nexv[k] > 0]
nepal['_t'] = {'im': round(sum(nimv.values()) / 1000), 'ex': round(sum(nexv.values()) / 1000)}
json.dump(nepal, open(NOUT, 'w'), separators=(',', ':'))

import os
print(f'rows {n:,} | prod {len(prod):,} ({os.path.getsize(POUT)/1024:.0f}KB) | '
      f'nepal products {len(nepal)-2:,} ({os.path.getsize(NOUT)/1024:.0f}KB)')
print('Nepal total imports $%.2fB, exports $%.2fB' % (sum(nimv.values())/1e6, sum(nexv.values())/1e6))
for code in ('090111', '151800', '090240'):   # coffee, veg oils, tea
    p = prod.get(code, {}); nz = nepal.get(code, {})
    print(code, 'world $/kg', p.get('u'), '| Nepal imports $%sM @ $%s/kg from' % (nz.get('im'), nz.get('iu')),
          [c for c, _ in nz.get('ims', [])[:3]])
