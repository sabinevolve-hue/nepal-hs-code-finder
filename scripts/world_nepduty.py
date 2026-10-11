#!/usr/bin/env python3
"""Nepal import duty per HS6 (general + SAARC) for the landed-cost tool.
Usage: world_nepduty.py <tariff.json> <out.json>
Output: {"<hs6>": [general_pct, saarc_pct], ...}  (numbers; Free=0; specific/na -> omitted)."""
import sys, json, re
from collections import Counter, defaultdict

TARIFF, OUT = sys.argv[1], sys.argv[2]
T = json.load(open(TARIFF, encoding='utf-8'))

def num(v):
    if v is None: return None
    s = str(v).strip()
    if re.fullmatch(r'free', s, re.I): return 0.0
    m = re.fullmatch(r'\d+(?:\.\d+)?', s)
    return float(s) if m else None            # specific/compound rates -> None

g_by = defaultdict(list); s_by = defaultdict(list)
for row in T['rows']:
    code = row[0].replace('.', '')
    if len(code) < 6: continue
    k = code[:6]
    g, s = num(row[5]), num(row[4])
    if g is not None: g_by[k].append(g)
    if s is not None: s_by[k].append(s)

out = {}
for k in set(g_by) | set(s_by):
    g = Counter(g_by[k]).most_common(1)[0][0] if g_by.get(k) else None   # modal (representative) rate
    s = Counter(s_by[k]).most_common(1)[0][0] if s_by.get(k) else None
    if g is None and s is None: continue
    out[k] = [g, s if s is not None else g]

json.dump(out, open(OUT, 'w'), separators=(',', ':'))
import os
print(f'nepduty: {len(out):,} HS6 codes, {os.path.getsize(OUT)/1024:.0f} KB')
for c in ('851713', '090111', '870321'):
    print(c, out.get(c))
