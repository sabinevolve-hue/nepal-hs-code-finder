#!/usr/bin/env python3
"""Latest US product detail from the U.S. Census Bureau -> data/world/us_products.json (same shape as more_products.json).

The Census API needs a key. The key lives only in the Vercel project (CENSUS_API_KEY); this script reads the figures
through the site's own endpoint, /api/us-trade (world-src/api/us-trade.js), which adds the key server-side. No key is
needed, used or stored here.

Exports: total exports (domestic and foreign), FAS value. Imports: general imports, customs value (no freight or
insurance). Published in US dollars, so nothing is converted. The API's year-to-date field at month M is January..M, so
one call per period gives a year (M = 12) or the year so far.

Thousand US dollars:  xc, mc = [[HS chapter, prev year, full year, year to date, same months a year earlier]];
xk, mk = the same for the 15 largest six-digit products of the full year.
Usage:  python3 scripts/world_us_products.py     (network; the site must be deployed with the key set)
"""
import datetime, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'us_products.json')
API = 'https://world.customsnepal.com/api/us-trade'
TOP = 15
K = lambda v: int(round(v / 1000.0))


def get(flow, period, level):
    """{code: year-to-date dollars} for one flow, period and level, all partners together; None if not published yet."""
    url = f'{API}?flow={flow}&time={period}&level={level}'
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'world.customsnepal.com data build'}), timeout=120) as r:
                d = json.load(r)
            rows = d.get('rows') or []
            if not rows:
                return None
            head = rows[0]; ci = 0; vi = head.index('ALL_VAL_YR' if flow == 'exports' else 'GEN_VAL_YR')
            out = {}
            for row in rows[1:]:
                try:
                    out[row[ci]] = out.get(row[ci], 0) + int(row[vi])
                except (TypeError, ValueError):
                    continue
            return out
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')[:200]
            if e.code in (400, 503):
                raise SystemExit(f'{url} -> {e.code} {body}')
            time.sleep(5 + 5 * attempt)
        except Exception:
            time.sleep(5 + 5 * attempt)
    raise SystemExit('failed: ' + url)


def latest_month():
    d = datetime.date.today().replace(day=1)
    for _ in range(8):                                   # the Census Bureau publishes about five weeks after the month ends
        d = (d - datetime.timedelta(days=1)).replace(day=1)
        p = f'{d.year}-{d.month:02d}'
        if get('exports', p, 'HS2') and get('imports', p, 'HS2'):
            return p
    raise SystemExit('no recent month found')


last = latest_month(); ly, lm = int(last[:4]), int(last[5:])
full = ly if lm == 12 else ly - 1; cur = None if lm == 12 else ly
P = [f'{full - 1}-12', f'{full}-12'] + ([f'{cur}-{lm:02d}', f'{cur - 1}-{lm:02d}'] if cur else [])
rec = dict(src='U.S. Census Bureau, international trade in goods by HS code; exports FAS, general imports at customs value, in US dollars',
           short='the U.S. Census Bureau', last=last, full=full, cur=cur, upto=lm)
for flow, key in (('exports', 'x'), ('imports', 'm')):
    for level, suf, keep in (('HS2', 'c', None), ('HS6', 'k', TOP)):
        cols = [get(flow, p, level) or {} for p in P]
        codes = sorted(cols[1], key=lambda c: -cols[1][c])
        codes = [c for c in codes if c.isdigit() and len(c) == (2 if level == 'HS2' else 6)]
        if keep:
            codes = codes[:keep]
        rec[key + suf] = [[c] + [K(col.get(c, 0)) for col in cols] + ([0, 0] if not cur else []) for c in codes]
        sys.stderr.write(f'{flow} {level}: {len(cols[1]):,} codes, full year {sum(cols[1].values()) / 1e9:,.0f}B\n')
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(unit='thousand USD', fetched=datetime.date.today().isoformat(), countries={'USA': rec}), fh, ensure_ascii=False, separators=(',', ':'))
sys.stderr.write(f'us_products.json: latest month {last}, full year {full}, {os.path.getsize(OUT) / 1e3:.0f} KB\n')
