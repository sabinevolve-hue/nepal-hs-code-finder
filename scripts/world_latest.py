#!/usr/bin/env python3
"""Fetch the latest monthly merchandise trade totals for world.customsnepal.com -> data/world/latest.json.

Source: World Trade Organization, monthly total merchandise exports (ITS_MTV_MX) and imports (ITS_MTV_MM), read through
the DBnomics API (a public mirror of the WTO series). Values are million US dollars, as each economy's customs
authority reported them. These are NOT the reconciled BACI figures used for partners and products: the two can differ
for the same economy and year, so pages always label which one a number comes from.

Months are only ever added: an existing latest.json is merged with the new download, so older months stay on file even
if the source later drops them. Run monthly:  python3 scripts/world_latest.py
"""
import csv, datetime, glob, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'latest.json')
API = 'https://api.db.nomics.world/v22/series/WTO/%s?limit=200&observations=1&offset=%d'
START = '2019-01'
# WTO reporter codes are UN M49 numbers; a few differ from the ISO list used on the site
M49 = json.load(open(os.path.join(ROOT, 'data', 'world', 'm49.json'), encoding='utf-8'))


def fetch(dataset):
    out = {}; offset = 0
    while True:
        with urllib.request.urlopen(API % (dataset, offset), timeout=120) as r:
            d = json.load(r)
        docs = d['series']['docs']
        for s in docs:
            dim = s.get('dimensions') or {}
            if dim.get('partner-economies') != '000' or dim.get('products-sector') != 'TO':
                continue
            iso = M49.get(dim.get('reporting-economies', ''))
            if not iso:
                continue
            out[iso] = {p: v for p, v in zip(s['period'], s['value']) if p >= START and isinstance(v, (int, float))}
        offset += len(docs)
        if offset >= d['series']['num_found'] or not docs:
            return out


x, m = fetch('ITS_MTV_MX'), fetch('ITS_MTV_MM')
old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'countries': {}}
countries = {}
for iso in sorted(set(x) | set(m) | set(old['countries'])):
    prev = old['countries'].get(iso, {'x': {}, 'm': {}})
    ex = dict(prev['x']); ex.update(x.get(iso, {})); im = dict(prev['m']); im.update(m.get(iso, {}))
    if ex or im:
        countries[iso] = {'x': dict(sorted(ex.items())), 'm': dict(sorted(im.items()))}
json.dump({'source': 'World Trade Organization, monthly merchandise trade values (via DBnomics)', 'unit': 'million USD',
           'fetched': datetime.date.today().isoformat(), 'countries': countries},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
last = max((max(c['x']) for c in countries.values() if c['x']), default='-')
sys.stderr.write('latest.json: %d economies, newest month %s\n' % (len(countries), last))
