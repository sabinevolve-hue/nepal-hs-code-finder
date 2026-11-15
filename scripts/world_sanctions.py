#!/usr/bin/env python3
"""Data for the trade-under-sanctions pages on world.customsnepal.com -> data/world/sanctions.json.

These economies do not report complete trade figures, and some stopped part-way (Russia and Belarus reported until 2021).
To keep one basis across all years, this file holds MIRROR figures only: what every other economy records as its own
imports from, and exports to, the economy concerned.

1. Partners' records, monthly since 2010. Source: International Monetary Fund, International Trade in Goods by partner
   country (IMTS). One request per economy: every reporter's trade with it. US dollars, converted by the IMF at each
   month's average exchange rate. Values the IMF estimated for a reporter (STATUS r or e) are kept and counted, so pages
   can say what share of a year was reported directly.
     yx, ym   {year: {partner: thousand USD}}   the economy's exports (partners' imports from it) and imports
     ye       {year: [share of yx that is IMF-estimated, share of ym]}
     mx, mm   {series: {'YYYY-MM': thousand USD}} monthly, for TOTAL, EU27, the four largest partners of the latest year
              and the three largest over the whole period that are not already among them
2. What the European Union buys from and sells to it, by HS chapter and year. Source: Eurostat, DS-045409, reporter
   EU27_2020, monthly, euros converted at each month's average ECB reference rate.
     eu       {'x': {year: {chapter: thousand USD}}, 'm': {...}, 'upto': 'YYYY-MM'}   x = the economy's sales to the EU

Usage:  python3 scripts/world_sanctions.py [ISO ...]
"""
import csv, datetime, io, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'sanctions.json')
ECON = {'RUS': 'RU', 'IRN': 'IR', 'VEN': 'VE', 'BLR': 'BY', 'PRK': 'KP', 'CUB': 'CU', 'MMR': 'MM'}      # ISO3 -> Eurostat partner code
EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
START = 2010
IMF = 'https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS/.XG_FOB_USD+MG_CIF_USD.%s.M?startPeriod=%d-01'
EST = 'https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/M.EU27_2020.%s.%s.1+2.VALUE_IN_EUROS?startPeriod=%d-01&format=SDMX-CSV'
ECB = 'https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?startPeriod=%d-01&format=csvdata'
K = lambda v: int(round(v / 1000.0))


def get(url, accept=None):
    for attempt in range(4):
        try:
            h = {'User-Agent': 'world.customsnepal.com data build'}
            if accept:
                h['Accept'] = accept
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=300) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode('utf-8'))))
        except Exception as e:
            if 'HTTP Error 404' in str(e):
                return []
            time.sleep(4 + 5 * attempt)
    raise SystemExit('failed: ' + url)


def mirror(iso):
    rows = get(IMF % (iso, START), 'application/vnd.sdmx.data+csv')
    # partner's imports from it = its exports; partner's exports to it = its imports
    mon = {'x': {}, 'm': {}}; est = {'x': {}, 'm': {}}
    for r in rows:
        c = r['COUNTRY']; tp = r['TIME_PERIOD']
        if len(c) != 3 or not r['OBS_VALUE'] or len(tp) < 8 or tp[5] != 'M':
            continue
        side = 'x' if r['INDICATOR'] == 'MG_CIF_USD' else 'm'; p = tp[:4] + '-' + tp[6:8]; v = float(r['OBS_VALUE'])
        mon[side].setdefault(c, {})[p] = v
        if r.get('STATUS'):
            est[side][(c, p)] = v
    months = sorted({p for s in mon.values() for d in s.values() for p in d})
    # the latest complete year: the newest year whose December most of the large reporters have
    years = sorted({int(p[:4]) for p in months})
    def cover(y):
        big = sorted(mon['x'], key=lambda c: -sum(v for p, v in mon['x'][c].items() if p[:4] == str(y - 1)))[:20]
        return sum(1 for c in big if f'{y}-12' in mon['x'][c]) >= 16
    full = max(y for y in years if cover(y))
    out = dict(full=full, yx={}, ym={}, ye={}, mx={}, mm={})
    for side, key in (('x', 'yx'), ('m', 'ym')):
        for y in range(START, full + 1):
            d = {c: sum(v for p, v in s.items() if p[:4] == str(y)) for c, s in mon[side].items()}
            d = {c: v for c, v in d.items() if v >= 100000}
            out[key][str(y)] = {c: K(v) for c, v in sorted(d.items())}
            tot = sum(d.values()) or 1.0
            e = sum(v for (c, p), v in est[side].items() if p[:4] == str(y))
            out['ye'].setdefault(str(y), [0, 0])[0 if side == 'x' else 1] = round(100.0 * e / tot, 1)
        top = sorted(out[key][str(full)], key=lambda c: -out[key][str(full)][c])
        series = {'TOTAL': list(mon[side]), 'EU27': EU27}
        alltime = {}
        for y in out[key]:
            for c, v in out[key][y].items():
                alltime[c] = alltime.get(c, 0) + v
        picks = [c for c in top if c not in EU27][:4]
        picks += [c for c in sorted(alltime, key=lambda c: -alltime[c]) if c not in EU27 and c not in picks][:3]      # markets that mattered earlier
        for c in picks:
            series[c] = [c]
        mk = 'mx' if side == 'x' else 'mm'
        for name, members in series.items():
            out[mk][name] = {p: K(sum(mon[side].get(c, {}).get(p, 0.0) for c in members)) for p in months if p <= f'{full}-12'}
    return out


def eu_products(code, fx):
    ch = '+'.join('%02d' % i for i in range(1, 98) if i != 77)
    rows = get(EST % (code, ch, START))
    out = {'x': {}, 'm': {}}; last = ''
    for r in rows:
        p = r['TIME_PERIOD']
        if not r['OBS_VALUE'] or p not in fx:
            continue
        v = float(r['OBS_VALUE']) * fx[p]
        if v <= 0:
            continue
        side = 'x' if r['flow'] == '1' else 'm'          # flow 1 = EU imports = the economy's sales to the EU
        d = out[side].setdefault(p[:4], {}); d[r['product']] = d.get(r['product'], 0.0) + v; last = max(last, p)
    return {'x': {y: {k: K(v) for k, v in sorted(d.items()) if v >= 1000} for y, d in sorted(out['x'].items())},
            'm': {y: {k: K(v) for k, v in sorted(d.items()) if v >= 1000} for y, d in sorted(out['m'].items())}, 'upto': last}


if __name__ == '__main__':
    want = sys.argv[1:] or list(ECON)
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'countries': {}}
    fx = {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in get(ECB % START)}
    out = dict(old.get('countries', {}))
    for iso in want:
        rec = mirror(iso); rec['eu'] = eu_products(ECON[iso], fx)
        out[iso] = rec
        sys.stderr.write('%s: full year %d, %d partners, EU products to %s\n' % (iso, rec['full'], len(rec['yx'][str(rec['full'])]), rec['eu']['upto']))
    json.dump({'source': 'IMF IMTS (partners\' records) and Eurostat DS-045409', 'unit': 'thousand USD', 'fetched': datetime.date.today().isoformat(),
               'countries': dict(sorted(out.items()))}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    sys.stderr.write('sanctions.json: %d economies, %.1f MB\n' % (len(out), os.path.getsize(OUT) / 1e6))
