#!/usr/bin/env python3
"""Who exports and imports each product heading (HS four digits) -> data/world/headings.json.

Source: BACI (CEPII), HS 2022. Values in thousand US dollars; every figure is a sum of BACI rows. For each heading:
  w     {year: world trade} for every year in the folder
  x, m  the 25 largest exporters and importers in the newest year [[ISO3, value]]
  nx, nm  how many economies export and import it
  k     its largest six-digit products in the newest year [[code, value]]
Usage (run isolated: the CSVs are downloaded files):
  python3 -I scripts/world_headings.py <dir with BACI_HS22_Y<year>_V*.csv + country_codes_V*.csv>
Re-run only when a new BACI release arrives.
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'headings.json')
files = {int(re.search(r'_Y(\d{4})_', f).group(1)): f for f in glob.glob(os.path.join(SRC, 'BACI_HS22_Y*_V*.csv'))}
years = sorted(files); MAIN = years[-1]
iso = {}
with open(glob.glob(os.path.join(SRC, 'country_codes_V*.csv'))[0], encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        try:
            iso[int(r['country_code'])] = (r.get('country_iso3') or '').strip() or r['country_code']
        except (ValueError, KeyError):
            continue
R = lambda v: int(round(v))
w = {y: defaultdict(float) for y in years}
x = defaultdict(lambda: defaultdict(float)); m = defaultdict(lambda: defaultdict(float)); k6 = defaultdict(lambda: defaultdict(float))
for y in years:
    with open(files[y], encoding='utf-8') as fh:
        rd = csv.reader(fh); next(rd, None)
        for row in rd:
            try:
                i, j, k, v = iso.get(int(row[1]), row[1]), iso.get(int(row[2]), row[2]), row[3].strip().zfill(6), float(row[4])
            except (ValueError, IndexError):
                continue
            h = k[:4]; w[y][h] += v
            if y == MAIN:
                x[h][i] += v; m[h][j] += v; k6[h][k] += v
out = {}
for h in sorted(w[MAIN]):
    top = lambda d: [[c, R(v)] for c, v in sorted(d.items(), key=lambda kv: -kv[1])[:25] if v >= 1]
    out[h] = dict(w={str(y): R(w[y].get(h, 0)) for y in years}, x=top(x[h]), m=top(m[h]), nx=len(x[h]), nm=len(m[h]),
                  k=[[c, R(v)] for c, v in sorted(k6[h].items(), key=lambda kv: -kv[1])[:6]])
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(source='BACI (CEPII), HS 2022', unit='thousand USD', year=MAIN, years=years, headings=out), fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('headings.json: %d headings, %.1f MB\n' % (len(out), os.path.getsize(OUT) / 1e6))
