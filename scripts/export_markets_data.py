#!/usr/bin/env python3
"""Data for /export-markets: who buys what Nepal exports, from CEPII BACI (HS 2022, 2022-2024).

Reads the BACI CSVs (not in the repo; about 750 MB) and writes data/export_markets.json:
  products  Nepal's top exported HS 6-digit products in the latest year (value at least USD 1 million)
  per product: Nepal's exports by destination per year, and the world's importers per year (top 25 by latest year)
Values are thousands of US dollars, as BACI publishes them. BACI: Etalab Open Licence 2.0, cite CEPII.

Run: python3 scripts/export_markets_data.py <folder with BACI_HS22_Y20xx_*.csv, country_codes_*.csv, product_codes_*.csv>
"""
import csv, json, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1])
YEARS = sorted(int(f.name.split('_Y')[1][:4]) for f in SRC.glob('BACI_HS22_Y*.csv'))
LAST = YEARS[-1]
NPL = '524'
MIN_K = 1000          # USD 1 million, in thousands
TOP_IMPORTERS = 25

iso = {}
with open(next(SRC.glob('country_codes_*.csv')), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        iso[r['country_code']] = r['country_iso3']
desc = {}
with open(next(SRC.glob('product_codes_HS22_*.csv')), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        desc[r['code']] = r['description']


def rows(year):
    with open(next(SRC.glob('BACI_HS22_Y%d_*.csv' % year)), encoding='utf-8') as f:
        rd = csv.reader(f); next(rd)
        for t, i, j, k, v, q in rd:
            yield i, j, k, float(v)


# 1. Nepal's exports by product and destination, every year
nx = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float)))   # k -> year -> dest -> v
for y in YEARS:
    for i, j, k, v in rows(y):
        if i == NPL:
            nx[k][y][iso.get(j, j)] += v
top = sorted((k for k in nx if sum(nx[k][LAST].values()) >= MIN_K), key=lambda k: -sum(nx[k][LAST].values()))
want = set(top)

# 2. The world's imports of those products, by importer and year
wm = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float)))   # k -> importer -> year -> v
for y in YEARS:
    for i, j, k, v in rows(y):
        if k in want:
            wm[k][iso.get(j, j)][y] += v

out = {'source': 'CEPII BACI, HS 2022 edition', 'licence': 'Etalab Open Licence 2.0', 'years': YEARS, 'unit': 'thousand USD', 'products': []}
for k in top:
    imp = wm[k]
    ranked = sorted(imp, key=lambda c: (-imp[c].get(LAST, 0), c))[:TOP_IMPORTERS]
    world = {y: round(sum(imp[c].get(y, 0) for c in imp)) for y in YEARS}
    out['products'].append({
        'hs6': k, 'desc': desc.get(k, ''),
        'nepal': {str(y): {c: round(v) for c, v in sorted(nx[k][y].items(), key=lambda x: -x[1]) if round(v)} for y in YEARS},
        'world': {str(y): world[y] for y in YEARS},
        'importers': [[c] + [round(imp[c].get(y, 0)) for y in YEARS] for c in ranked],
    })
(ROOT / 'data' / 'export_markets.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print('export_markets_data: %d products (Nepal exports >= USD 1m in %d), years %s' % (len(top), LAST, YEARS))
