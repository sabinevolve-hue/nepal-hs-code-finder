#!/usr/bin/env python3
"""Latest product detail for the 27 EU members -> data/world/eu_products.json.

Source: Eurostat, EU trade since 1988 by HS2-4-6 and CN8 (dataset DS-045409), the EU's own customs and Intrastat
figures, monthly, in euros, by reporter and product, partner WORLD (trade inside and outside the EU together).

Currency: each month's euro value is converted to US dollars at that month's average ECB reference rate
(ECB series EXR/M.USD.EUR.SP00.A). Trade is a flow through the month, so the month's average rate is the right one;
a year-end rate would misstate months when the euro stood elsewhere. Yearly figures are sums of the converted months.

For each member, in thousand US dollars:
  xc, mc   [[HS chapter, prev year, full year, year to date, same months a year earlier]] exports, imports
  xk, mk   the same for the 15 largest six-digit products of the full year
Usage:  python3 scripts/world_eu_products.py
"""
import concurrent.futures as cf, csv, datetime, io, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'eu_products.json')
API = 'https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/%s?%s&format=SDMX-CSV'
ECB = 'https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?startPeriod=%s&format=csvdata'
EU = dict(AT='AUT', BE='BEL', BG='BGR', CY='CYP', CZ='CZE', DE='DEU', DK='DNK', EE='EST', ES='ESP', FI='FIN', FR='FRA', GR='GRC', HR='HRV',
          HU='HUN', IE='IRL', IT='ITA', LT='LTU', LU='LUX', LV='LVA', MT='MLT', NL='NLD', PL='POL', PT='PRT', RO='ROU', SE='SWE', SI='SVN', SK='SVK')
TOP = 15
K = lambda v: int(round(v / 1000.0))


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'world.customsnepal.com data build'}), timeout=240) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode('utf-8'))))
        except Exception as e:
            if 'HTTP Error 404' in str(e):
                return []
            time.sleep(4 + 5 * attempt)
    raise SystemExit('failed: ' + url)


this_year = datetime.date.today().year
fx = {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in get(ECB % ('%d-01' % (this_year - 3)))}       # US dollars per euro, monthly average
# the newest month every member has, and that has an exchange rate
probe = get(API % ('M.DE+FR+IT+NL+ES.WORLD.TOTAL.2.VALUE_IN_EUROS', 'startPeriod=%d-01' % (this_year - 1)))
by_rep = {}
for r in probe:
    if r['OBS_VALUE'] and float(r['OBS_VALUE']) > 0:
        by_rep.setdefault(r['reporter'], []).append(r['TIME_PERIOD'])
last = min(max(v) for v in by_rep.values()); last = max(m for m in fx if m <= last)
ly, lm = int(last[:4]), int(last[5:])
full = ly if lm == 12 else ly - 1; cur = None if lm == 12 else ly
start = '%d-01' % (full - 1)
CH = '+'.join('%02d' % i for i in range(1, 98) if i != 77)


def bucket(rows):
    """rows of one reporter -> {(flow, product): [prev, full, ytd, ytd_prev]} in US dollars"""
    out = {}
    for r in rows:
        p = r['TIME_PERIOD']
        if not r['OBS_VALUE'] or p not in fx or p > last:
            continue
        v = float(r['OBS_VALUE']) * fx[p]; y, mo = int(p[:4]), int(p[5:]); a = out.setdefault((r['flow'], r['product']), [0.0] * 4)
        if y == full - 1: a[0] += v
        if y == full: a[1] += v
        if cur and y == cur and mo <= lm: a[2] += v
        if cur and y == cur - 1 and mo <= lm: a[3] += v
    return out


def build(geo):
    ch = bucket(get(API % ('M.%s.WORLD.%s.1+2.VALUE_IN_EUROS' % (geo, CH), 'startPeriod=' + start)))
    ann = get(API % ('A.%s.WORLD..1+2.VALUE_IN_EUROS' % geo, 'startPeriod=%d&endPeriod=%d' % (full, full)))
    tops = {}
    for flow in ('1', '2'):
        six = sorted(((r['product'], float(r['OBS_VALUE'])) for r in ann if r['flow'] == flow and len(r['product']) == 6 and r['product'].isdigit() and r['OBS_VALUE']),
                     key=lambda kv: -kv[1])[:TOP]
        tops[flow] = [k for k, _ in six]
    codes = sorted(set(tops['1']) | set(tops['2']))
    pk = bucket(get(API % ('M.%s.WORLD.%s.1+2.VALUE_IN_EUROS' % (geo, '+'.join(codes)), 'startPeriod=' + start))) if codes else {}
    rec = {}
    for flow, key in (('2', 'x'), ('1', 'm')):            # Comext: flow 1 = imports, 2 = exports
        rec[key + 'c'] = sorted(([p] + [K(v) for v in a] for (f, p), a in ch.items() if f == flow and a[1] > 0), key=lambda r: -r[2])
        rec[key + 'k'] = sorted(([p] + [K(v) for v in pk[(flow, p)]] for p in tops[flow] if (flow, p) in pk), key=lambda r: -r[2])
    return EU[geo], rec


out = {}
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for iso, rec in ex.map(build, sorted(EU)):
        out[iso] = rec; sys.stderr.write(iso + ' ')
json.dump({'source': 'Eurostat, EU trade since 1988 by HS2-4-6 and CN8 (DS-045409); converted at ECB monthly average rates', 'unit': 'thousand USD',
           'fetched': datetime.date.today().isoformat(), 'last': last, 'full': full, 'cur': cur, 'upto': lm if cur else 12,
           'fx': {m: fx[m] for m in sorted(fx) if m >= start}, 'countries': dict(sorted(out.items()))},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
sys.stderr.write('\neu_products.json: %d members, newest month %s, %.2f MB\n' % (len(out), last, os.path.getsize(OUT) / 1e6))
