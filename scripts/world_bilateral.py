#!/usr/bin/env python3
"""Build data/world/deep.json — the bilateral layer behind the deep country profiles and country-pair pages on
world.customsnepal.com.

Source: BACI (CEPII), HS 2022, reconciled from UN Comtrade. Columns t,i,j,k,v,q: year, exporter, importer, HS6,
value (thousand USD), quantity (tonnes). One row per exporter-importer-product, so nothing here is estimated: every
figure is a sum of BACI rows.

For every economy:  total exports/imports for each year given; every partner (exports to, imports from);
                    top export and import products with the main partner for each; products where it ranks in the
                    world's top three exporters; import products that come mostly from one supplier.
For chosen pairs:   both directions' totals by year and the top products each way.

Usage (run isolated: the CSVs are downloaded files):
  python3 -I scripts/world_bilateral.py <dir with BACI_HS22_Y<year>_V*.csv + country_codes_V*.csv> [out.json]
The newest year present is the main year; older years give the short history.
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'data', 'world', 'deep.json')

SAARC = ['AFG', 'BGD', 'BTN', 'IND', 'MDV', 'NPL', 'PAK', 'LKA']
PAIR_EXTRA = ['CHN']          # always in the pair set, with SAARC
PAIR_TOP = 15                 # plus the world's largest exporters
PAIR_MIN = 10000              # thousand USD: a pair page needs at least $10M of trade in one direction
TOPK, TOPDEP, TOPLEAD, PAIRK = 40, 12, 15, 20

files = {}
for f in glob.glob(os.path.join(SRC, 'BACI_HS22_Y*_V*.csv')):
    files[int(re.search(r'_Y(\d{4})_', f).group(1))] = f
years = sorted(files)
if not years:
    sys.exit('no BACI_HS22_Y<year> csv in ' + SRC)
MAIN = years[-1]

iso, cname = {}, {}
with open(glob.glob(os.path.join(SRC, 'country_codes_V*.csv'))[0], encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        try:
            c = int(r['country_code'])
        except (ValueError, KeyError):
            continue
        iso[c] = (r.get('country_iso3') or '').strip() or str(c)
        cname[iso[c]] = (r.get('country_name') or '').strip()


def rows(path):
    with open(path, encoding='utf-8') as fh:
        rd = csv.reader(fh); next(rd, None)
        for row in rd:
            try:
                yield iso.get(int(row[1]), row[1]), iso.get(int(row[2]), row[2]), row[3].strip().zfill(6), float(row[4])
            except (ValueError, IndexError):
                continue


# ---- pass 1 (every year): totals per country and per ordered pair
tot_x = {y: defaultdict(float) for y in years}; tot_m = {y: defaultdict(float) for y in years}
pair = {y: defaultdict(float) for y in years}
for y in years:
    n = 0
    for i, j, k, v in rows(files[y]):
        tot_x[y][i] += v; tot_m[y][j] += v; pair[y][(i, j)] += v; n += 1
    sys.stderr.write('%d: %s rows\n' % (y, format(n, ',')))

top = [c for c, _ in sorted(tot_x[MAIN].items(), key=lambda kv: -kv[1])[:PAIR_TOP]]
PSET = set(SAARC + PAIR_EXTRA + top)

# ---- pass 2 (main year): products
xk = defaultdict(lambda: defaultdict(float)); mk = defaultdict(lambda: defaultdict(float))     # country -> hs6 -> value
bx, bm = {}, {}                                    # (country, hs6) -> [partner, value] largest partner
wk = defaultdict(float)                            # hs6 -> world
pk = defaultdict(lambda: defaultdict(float))       # (i, j) within PSET -> hs6 -> value
for i, j, k, v in rows(files[MAIN]):
    xk[i][k] += v; mk[j][k] += v; wk[k] += v
    b = bx.get((i, k))
    if b is None or v > b[1]:
        bx[(i, k)] = [j, v]
    b = bm.get((j, k))
    if b is None or v > b[1]:
        bm[(j, k)] = [i, v]
    if i in PSET and j in PSET:
        pk[(i, j)][k] += v

# world rank of each exporter per product
rank = {}
for k in wk:
    order = sorted(((c, xk[c].get(k, 0.0)) for c in xk if xk[c].get(k)), key=lambda kv: -kv[1])
    for n, (c, v) in enumerate(order[:3], 1):
        rank[(c, k)] = n

R = lambda v: int(round(v))
countries = {}
for c in sorted(set(tot_x[MAIN]) | set(tot_m[MAIN])):
    X, M = tot_x[MAIN].get(c, 0.0), tot_m[MAIN].get(c, 0.0)
    if X + M <= 0:
        continue
    xp = sorted(((j, v) for (i, j), v in pair[MAIN].items() if i == c), key=lambda kv: -kv[1])
    mp = sorted(((i, v) for (i, j), v in pair[MAIN].items() if j == c), key=lambda kv: -kv[1])
    xks = sorted(xk[c].items(), key=lambda kv: -kv[1])[:TOPK]
    mks = sorted(mk[c].items(), key=lambda kv: -kv[1])[:TOPK]
    lead = sorted(((k, v, rank[(c, k)], 100.0 * v / wk[k]) for k, v in xk[c].items() if (c, k) in rank and v >= 1000),
                  key=lambda r: -r[1])[:TOPLEAD]
    dep = sorted(((k, v, bm[(c, k)][0], 100.0 * bm[(c, k)][1] / v) for k, v in mk[c].items()
                  if v >= max(5000, M * 0.001) and bm[(c, k)][1] / v >= 0.75), key=lambda r: -r[1])[:TOPDEP]
    countries[c] = dict(
        n=cname.get(c, c), x=R(X), m=R(M),
        xp=[[p, R(v)] for p, v in xp if v >= 1], mp=[[p, R(v)] for p, v in mp if v >= 1],
        xk=[[k, R(v), bx[(c, k)][0], R(bx[(c, k)][1]), round(100.0 * v / wk[k], 1), rank.get((c, k), 0)] for k, v in xks],
        mk=[[k, R(v), bm[(c, k)][0], R(bm[(c, k)][1])] for k, v in mks],
        lead=[[k, R(v), r, round(s, 1)] for k, v, r, s in lead],
        dep=[[k, R(v), p, round(s)] for k, v, p, s in dep],
        nx=len(xk[c]), nm=len(mk[c]),
        hist={str(y): [R(tot_x[y].get(c, 0)), R(tot_m[y].get(c, 0))] for y in years})

pairs = {}
ps = sorted(PSET)
for a in ps:
    for b in ps:
        if a >= b:
            continue
        ab, ba = pair[MAIN].get((a, b), 0.0), pair[MAIN].get((b, a), 0.0)
        if max(ab, ba) < PAIR_MIN:
            continue
        pairs[a + '-' + b] = dict(
            ab=R(ab), ba=R(ba),
            abk=[[k, R(v)] for k, v in sorted(pk[(a, b)].items(), key=lambda kv: -kv[1])[:PAIRK]],
            bak=[[k, R(v)] for k, v in sorted(pk[(b, a)].items(), key=lambda kv: -kv[1])[:PAIRK]],
            nab=len(pk[(a, b)]), nba=len(pk[(b, a)]),
            hist={str(y): [R(pair[y].get((a, b), 0)), R(pair[y].get((b, a), 0))] for y in years})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
out = dict(source='BACI (CEPII), HS 2022, version in file name', unit='thousand USD', year=MAIN, years=years,
           world=R(sum(tot_x[MAIN].values())), pairset=ps, saarc=SAARC, countries=countries, pairs=pairs)
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('deep.json: %d economies, %d pairs, %.1f MB, main year %d\n'
                 % (len(countries), len(pairs), os.path.getsize(OUT) / 1e6, MAIN))
