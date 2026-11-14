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
PAIR_PARTNERS = 10            # every economy also gets a pair page with each of its ten largest partners
PC_TOP, PC_MIN, PC_BUYERS = 10, 50000, 15     # product-by-country pages: top export products per economy, min $50M
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
                yield iso.get(int(row[1]), row[1]), iso.get(int(row[2]), row[2]), row[3].strip().zfill(6), float(row[4]), row[5]
            except (ValueError, IndexError):
                continue


# ---- pass 1 (every year): totals per country and per ordered pair
tot_x = {y: defaultdict(float) for y in years}; tot_m = {y: defaultdict(float) for y in years}
pair = {y: defaultdict(float) for y in years}
for y in years:
    n = 0
    for i, j, k, v, _q in rows(files[y]):
        tot_x[y][i] += v; tot_m[y][j] += v; pair[y][(i, j)] += v; n += 1
    sys.stderr.write('%d: %s rows\n' % (y, format(n, ',')))

top = [c for c, _ in sorted(tot_x[MAIN].items(), key=lambda kv: -kv[1])[:PAIR_TOP]]
PSET = set(SAARC + PAIR_EXTRA + top)
# pair keys: every pair inside PSET, plus each economy with its largest partners (by two-way trade)
PKEYS = set()
for a in PSET:
    for b in PSET:
        if a < b:
            PKEYS.add((a, b))
two = defaultdict(lambda: defaultdict(float))
for (i, j), v in pair[MAIN].items():
    two[i][j] += v; two[j][i] += v
for c, d in two.items():
    for p, _v in sorted(d.items(), key=lambda kv: -kv[1])[:PAIR_PARTNERS]:
        if p != c:
            PKEYS.add((min(c, p), max(c, p)))
PKEYS = {(a, b) for a, b in PKEYS if max(pair[MAIN].get((a, b), 0.0), pair[MAIN].get((b, a), 0.0)) >= PAIR_MIN}

# ---- pass 2 (main year): products
xk = defaultdict(lambda: defaultdict(float)); mk = defaultdict(lambda: defaultdict(float))     # country -> hs6 -> value
bx, bm = {}, {}                                    # (country, hs6) -> [partner, value] largest partner
wk = defaultdict(float)                            # hs6 -> world
pk = defaultdict(lambda: defaultdict(float))       # (i, j) within PSET -> hs6 -> value
xc = defaultdict(lambda: defaultdict(float)); mc = defaultdict(lambda: defaultdict(float))     # country -> HS chapter -> value
xq = defaultdict(float)                            # (country, hs6) -> tonnes exported (where reported)
for i, j, k, v, q in rows(files[MAIN]):
    xk[i][k] += v; mk[j][k] += v; wk[k] += v
    xc[i][k[:2]] += v; mc[j][k[:2]] += v
    try:
        xq[(i, k)] += float(q)
    except ValueError:
        pass
    b = bx.get((i, k))
    if b is None or v > b[1]:
        bx[(i, k)] = [j, v]
    b = bm.get((j, k))
    if b is None or v > b[1]:
        bm[(j, k)] = [i, v]
    if ((i, j) if i < j else (j, i)) in PKEYS:
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
        xc=[[ch, R(v)] for ch, v in sorted(xc[c].items(), key=lambda kv: -kv[1]) if v >= 1],
        mc=[[ch, R(v)] for ch, v in sorted(mc[c].items(), key=lambda kv: -kv[1]) if v >= 1],
        hist={str(y): [R(tot_x[y].get(c, 0)), R(tot_m[y].get(c, 0))] for y in years})

pairs = {}
ps = sorted(PSET)
if True:
    for a, b in sorted(PKEYS):
        ab, ba = pair[MAIN].get((a, b), 0.0), pair[MAIN].get((b, a), 0.0)
        pairs[a + '-' + b] = dict(
            ab=R(ab), ba=R(ba),
            abk=[[k, R(v)] for k, v in sorted(pk[(a, b)].items(), key=lambda kv: -kv[1])[:PAIRK]],
            bak=[[k, R(v)] for k, v in sorted(pk[(b, a)].items(), key=lambda kv: -kv[1])[:PAIRK]],
            nab=len(pk[(a, b)]), nba=len(pk[(b, a)]),
            hist={str(y): [R(pair[y].get((a, b), 0)), R(pair[y].get((b, a), 0))] for y in years})

# ---- product-by-country: each economy's largest export products, with who buys them
PCSET = set()
for c in countries:
    for k, v in sorted(xk[c].items(), key=lambda kv: -kv[1])[:PC_TOP]:
        if v >= PC_MIN:
            PCSET.add((c, k))
buy = defaultdict(lambda: defaultdict(float))
for i, j, k, v, _q in rows(files[MAIN]):
    if (i, k) in PCSET:
        buy[(i, k)][j] += v
pch = {y: defaultdict(float) for y in years if y != MAIN}
for y in pch:
    for i, j, k, v, _q in rows(files[y]):
        if (i, k) in PCSET:
            pch[y][(i, k)] += v
wtop = {}
for k in {k for _c, k in PCSET}:
    wtop[k] = [[c, R(xk[c][k])] for c in sorted((c for c in xk if xk[c].get(k)), key=lambda c: -xk[c][k])[:8]]
prodc = {}
for c, k in sorted(PCSET):
    v = xk[c][k]; b = sorted(buy[(c, k)].items(), key=lambda kv: -kv[1])
    order = sorted((cc for cc in xk if xk[cc].get(k)), key=lambda cc: -xk[cc][k])
    prodc[c + '-' + k] = dict(v=R(v), q=round(xq.get((c, k), 0.0), 1), w=R(wk[k]), s=round(100.0 * v / wk[k], 2), r=order.index(c) + 1,
                              ne=len(order), nb=len(b), b=[[j, R(x)] for j, x in b[:PC_BUYERS]],
                              hist={str(y): R(pch[y].get((c, k), 0.0)) for y in pch})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(os.path.join(os.path.dirname(OUT), 'prodc.json'), 'w', encoding='utf-8') as fh:
    json.dump(dict(year=MAIN, years=years, unit='thousand USD; q in tonnes', products=prodc, wtop=wtop), fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('prodc.json: %d product-by-country entries, %d products\n' % (len(prodc), len(wtop)))
out = dict(source='BACI (CEPII), HS 2022, version in file name', unit='thousand USD', year=MAIN, years=years,
           world=R(sum(tot_x[MAIN].values())), pairset=ps, saarc=SAARC, countries=countries, pairs=pairs)
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('deep.json: %d economies, %d pairs, %.1f MB, main year %d\n'
                 % (len(countries), len(pairs), os.path.getsize(OUT) / 1e6, MAIN))
