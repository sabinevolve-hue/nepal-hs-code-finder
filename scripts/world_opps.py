#!/usr/bin/env python3
"""Where import demand moved, for the largest product headings -> data/world/opps.json.

Source: BACI (CEPII), HS 2022. Values in thousand US dollars; every figure is a sum of BACI rows.
Compares the oldest and newest year in the folder (2022 and 2024 in the January 2026 release).
For each of the N largest headings by world trade in the newest year:
  g   importers whose imports rose most in dollars  [[ISO3, old, new, [[supplier, value] x3], number of suppliers]]
  f   importers that grew fastest in per cent (old >= FLOOR)  [[ISO3, old, new]]
  d   importers whose imports fell most in dollars  [[ISO3, old, new]]
  xg  exporters whose exports rose most in dollars  [[ISO3, old, new]]
For each exporting economy, its largest headings (exports >= FLOOR and >= 1% of world exports) with the markets
whose imports rose and where the economy's share of that market is below its share of world exports:
  c[ISO3] = [[heading, exports, world share %, [[market, old, new, exports to it] x4]]]
Usage (run isolated: the CSVs are downloaded files):
  python3 -I scripts/world_opps.py <dir with BACI_HS22_Y<year>_V*.csv + country_codes_V*.csv>
Re-run only when a new BACI release arrives.
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'opps.json')
N = 200; FLOOR = 50000          # FLOOR: $50 million, in thousand USD
HD = json.load(open(os.path.join(ROOT, 'data', 'world', 'headings.json'), encoding='utf-8'))
files = {int(re.search(r'_Y(\d{4})_', f).group(1)): f for f in glob.glob(os.path.join(SRC, 'BACI_HS22_Y*_V*.csv'))}
Y0, Y1 = min(files), max(files)
assert Y1 == HD['year'], 'headings.json and the BACI folder disagree on the newest year'
top = set(sorted(HD['headings'], key=lambda h: -HD['headings'][h]['w'].get(str(Y1), 0))[:N])
iso = {}
with open(glob.glob(os.path.join(SRC, 'country_codes_V*.csv'))[0], encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        s = (r.get('country_iso3') or '').strip()
        if re.fullmatch(r'[A-Z]{3}', s):
            iso[r['country_code'].strip()] = s
M = {y: defaultdict(lambda: defaultdict(float)) for y in (Y0, Y1)}      # imports  [year][heading][importer]
X = {y: defaultdict(lambda: defaultdict(float)) for y in (Y0, Y1)}      # exports  [year][heading][exporter]
B = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))        # newest year [heading][importer][exporter]
for y in (Y0, Y1):
    with open(files[y], encoding='utf-8') as fh:
        rd = csv.reader(fh); next(rd, None)
        for row in rd:
            h = row[3].strip().zfill(6)[:4]
            if h not in top:
                continue
            i, j = iso.get(row[1].strip()), iso.get(row[2].strip())
            if not i or not j:
                continue
            try:
                v = float(row[4])
            except ValueError:
                continue
            M[y][h][j] += v; X[y][h][i] += v
            if y == Y1:
                B[h][j][i] += v
R = lambda v: int(round(v))
heads = {}; byc = defaultdict(list)
for h in sorted(top):
    m0, m1, x0, x1 = M[Y0][h], M[Y1][h], X[Y0][h], X[Y1][h]
    W = sum(x1.values())
    imp = [j for j in m1 if m1[j] >= FLOOR]
    sup = lambda j: [[i, R(v)] for i, v in sorted(B[h][j].items(), key=lambda kv: -kv[1])[:3]]
    g = [[j, R(m0.get(j, 0)), R(m1[j]), sup(j), len(B[h][j])] for j in sorted(imp, key=lambda j: m0.get(j, 0) - m1[j])[:12] if m1[j] > m0.get(j, 0)]
    f = [[j, R(m0[j]), R(m1[j])] for j in sorted([j for j in imp if m0.get(j, 0) >= FLOOR], key=lambda j: -(m1[j] / m0[j]))[:10] if m1[j] > m0[j]]
    d = [[j, R(m0[j]), R(m1.get(j, 0))] for j in sorted([j for j in m0 if m0[j] >= FLOOR], key=lambda j: m1.get(j, 0) - m0[j])[:8] if m1.get(j, 0) < m0[j]]
    xg = [[i, R(x0.get(i, 0)), R(x1[i])] for i in sorted([i for i in x1 if x1[i] >= FLOOR], key=lambda i: x0.get(i, 0) - x1[i])[:10] if x1[i] > x0.get(i, 0)]
    heads[h] = dict(w=[R(sum(x0.values())), R(W)], g=g, f=f, d=d, xg=xg)
    for i, v in x1.items():
        if v < FLOOR or v < 0.01 * W:
            continue
        ws = v / W; mk = []
        for j in m1:
            gain = m1[j] - m0.get(j, 0)
            if j == i or gain < 20000 or m1[j] < FLOOR:
                continue
            if B[h][j].get(i, 0) / m1[j] < ws:
                mk.append((gain, j))
        mk = [[j, R(m0.get(j, 0)), R(m1[j]), R(B[h][j].get(i, 0))] for _, j in sorted(mk, reverse=True)[:4]]
        if mk:
            byc[i].append([h, R(v), round(100 * ws, 1), mk])
c = {i: sorted(v, key=lambda r: -r[1])[:8] for i, v in byc.items()}
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(source='BACI (CEPII), HS 2022', unit='thousand USD', y0=Y0, y1=Y1, floor=FLOOR, headings=heads, c=c), fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('opps.json: %d headings, %d economies, %.2f MB\n' % (len(heads), len(c), os.path.getsize(OUT) / 1e6))
