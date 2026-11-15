#!/usr/bin/env python3
"""Product detail for the earlier BACI years -> data/world/years.json, for the year pages on world.customsnepal.com.

deep.json holds the newest BACI year in full. This file holds, for every older year in the folder and every economy,
only what a year page shows about products: totals, exports and imports by HS chapter, and the largest products.

Source: BACI (CEPII), HS 2022. Values in thousand US dollars; every figure is a sum of BACI rows.

Usage (run isolated: the CSVs are downloaded files):
  python3 -I scripts/world_years.py <dir with BACI_HS22_Y<year>_V*.csv + country_codes_V*.csv>
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'years.json')
TOPK = 15

files = {int(re.search(r'_Y(\d{4})_', f).group(1)): f for f in glob.glob(os.path.join(SRC, 'BACI_HS22_Y*_V*.csv'))}
years = sorted(files)[:-1]          # the newest year is in deep.json
iso = {}
with open(glob.glob(os.path.join(SRC, 'country_codes_V*.csv'))[0], encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        try:
            iso[int(r['country_code'])] = (r.get('country_iso3') or '').strip() or r['country_code']
        except (ValueError, KeyError):
            continue
R = lambda v: int(round(v))
out = {}
for y in years:
    xk = defaultdict(lambda: defaultdict(float)); mk = defaultdict(lambda: defaultdict(float))
    with open(files[y], encoding='utf-8') as fh:
        rd = csv.reader(fh); next(rd, None)
        for row in rd:
            try:
                i, j, k, v = iso.get(int(row[1]), row[1]), iso.get(int(row[2]), row[2]), row[3].strip().zfill(6), float(row[4])
            except (ValueError, IndexError):
                continue
            xk[i][k] += v; mk[j][k] += v
    rec = {}
    for c in sorted(set(xk) | set(mk)):
        def side(d):
            ch = defaultdict(float)
            for k, v in d.items():
                ch[k[:2]] += v
            return (R(sum(d.values())), [[a, R(v)] for a, v in sorted(ch.items(), key=lambda kv: -kv[1]) if v >= 1],
                    [[k, R(v)] for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:TOPK]])
        x, xc, xks = side(xk.get(c, {})); m, mc, mks = side(mk.get(c, {}))
        if x + m > 0:
            rec[c] = dict(x=x, m=m, xc=xc, mc=mc, xk=xks, mk=mks, nx=len(xk.get(c, {})), nm=len(mk.get(c, {})))
    out[str(y)] = rec
    sys.stderr.write('%d: %d economies\n' % (y, len(rec)))
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(source='BACI (CEPII), HS 2022', unit='thousand USD', years=out), fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('years.json: %.1f MB\n' % (os.path.getsize(OUT) / 1e6))
