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
2. What three reporters that publish product detail openly buy from and sell to it, by HS chapter and year.
     prod     {'EU' | 'UK' | 'BR': {'x': {year: {chapter: thousand USD}}, 'm': {...}, 'upto': 'YYYY-MM'}}
              x = the economy's sales to that reporter (the reporter's imports), m = the reporter's sales to it
   EU: Eurostat, DS-045409, reporter EU27_2020, monthly, euros converted at each month's average ECB reference rate.
   UK: HM Revenue & Customs, Overseas Trade Statistics (api.uktradeinfo.com), monthly, pounds converted at the cross of the
       ECB's monthly average dollar and pound rates.
   BR: Ministry of Development, Industry, Trade and Services of Brazil, Comex Stat, published in US dollars (FOB).
3. Crude oil in barrels, as the economy itself reported it to the Joint Organisations Data Initiative (JODI-Oil World
   Database, primary products, monthly, thousand barrels a day). Many of these economies stopped reporting; the file keeps
   yearly averages only for years with at least nine reported months, and the last month reported.
     oil      {'prod': {year: [kb/d, months]}, 'exp': {year: [kb/d, months]}, 'last_prod': 'YYYY-MM', 'last_exp': 'YYYY-MM'}

Usage:  python3 scripts/world_sanctions.py [ISO ...]
"""
import csv, datetime, io, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'sanctions.json')
ECON = {'RUS': 'RU', 'IRN': 'IR', 'VEN': 'VE', 'BLR': 'BY', 'PRK': 'KP', 'CUB': 'CU', 'MMR': 'MM'}      # ISO3 -> Eurostat partner code
EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
START = 2010
IMF = 'https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS/.XG_FOB_USD+MG_CIF_USD.%s.M?startPeriod=%d-01'
EST = 'https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/M.EU27_2020.%s.%s.1+2.VALUE_IN_EUROS?startPeriod=%d-01&format=SDMX-CSV'
ECB = 'https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?startPeriod=%d-01&format=csvdata'
UK_ID = {'RUS': 75, 'IRN': 616, 'VEN': 484, 'BLR': 73, 'PRK': 724, 'CUB': 448, 'MMR': 676}                      # api.uktradeinfo.com CountryId
BR_ID = {'RUS': '676', 'IRN': '372', 'VEN': '850', 'BLR': '085', 'PRK': '187', 'CUB': '199', 'MMR': '093'}      # Comex Stat country id
JODI = 'https://www.jodidata.org/_resources/files/downloads/oil-data/annual-csv/primary/%s.csv'
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


def raw(url, body=None):
    for attempt in range(5):
        try:
            h = {'User-Agent': 'world.customsnepal.com data build'}
            if body:
                h['Content-Type'] = 'application/json'
            with urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=h), timeout=300) as r:
                return r.read().decode('utf-8-sig')
        except Exception as e:
            if 'HTTP Error 404' in str(e):
                return ''
            time.sleep(6 + 8 * attempt)
    raise SystemExit('failed: ' + url)


def tidy(out, last):
    return {'x': {y: {k: K(v) for k, v in sorted(d.items()) if v >= 1000} for y, d in sorted(out['x'].items())},
            'm': {y: {k: K(v) for k, v in sorted(d.items()) if v >= 1000} for y, d in sorted(out['m'].items())}, 'upto': last}


def uk_products(cid, fxg):
    """fxg: US dollars per pound, monthly average. UK imports (flows 1 and 3) are the economy's sales."""
    out = {'x': {}, 'm': {}}; last = ''
    apply = 'filter(CountryId eq %d and MonthId ge %d01)/groupby((Commodity/Hs2Code,MonthId,FlowTypeId),aggregate(Value with sum as V))' % (cid, START)
    url = 'https://api.uktradeinfo.com/OTS?$apply=' + urllib.parse.quote(apply, safe='()/,$=')
    while url:
        d = json.loads(raw(url)); url = d.get('@odata.nextLink')
        for r in d['value']:
            code = (r.get('Commodity') or {}).get('Hs2Code'); p = '%d-%02d' % (r['MonthId'] // 100, r['MonthId'] % 100)
            if not code or not code.isdigit() or p not in fxg or not r['V']:
                continue
            side = 'm' if r['FlowTypeId'] in (2, 4) else 'x'
            dd = out[side].setdefault(p[:4], {}); dd[code] = dd.get(code, 0.0) + r['V'] * fxg[p]; last = max(last, p)
        time.sleep(1.0)
    return tidy(out, last)


def br_products(cid):
    out = {'x': {}, 'm': {}}
    upd = json.loads(raw('https://api-comexstat.mdic.gov.br/general/dates/updated'))['data']; last = '%s-%02d' % (upd['year'], int(upd['monthNumber']))
    for side, flow in (('x', 'import'), ('m', 'export')):          # Brazil's imports are the economy's sales
        body = {'flow': flow, 'monthDetail': False, 'period': {'from': '%d-01' % START, 'to': last}, 'filters': [{'filter': 'country', 'values': [cid]}],
                'details': ['chapter'], 'metrics': ['metricFOB']}
        for r in json.loads(raw('https://api-comexstat.mdic.gov.br/general?language=en', body))['data']['list']:
            v = float(r.get('metricFOB') or 0)
            if v > 0 and r.get('chapterCode'):
                d = out[side].setdefault(str(r['year']), {}); d[r['chapterCode']] = d.get(r['chapterCode'], 0.0) + v
    return tidy(out, last)


def jodi_oil(codes):
    """{JODI area code: oil record}. Reads each yearly file once."""
    mon = {}
    this = datetime.date.today().year
    for y in range(START, this + 1):
        text = raw(JODI % (y if y < this else 'primaryyear%d' % y)) or (raw(JODI % y) if y == this else '')
        for r in csv.DictReader(io.StringIO(text)):
            if r['REF_AREA'] in codes and r['ENERGY_PRODUCT'] == 'CRUDEOIL' and r['UNIT_MEASURE'] == 'KBD' and r['FLOW_BREAKDOWN'] in ('INDPROD', 'TOTEXPSB'):
                try:
                    v = float(r['OBS_VALUE'])
                except ValueError:
                    continue
                if v > 0:
                    mon.setdefault(r['REF_AREA'], {}).setdefault('prod' if r['FLOW_BREAKDOWN'] == 'INDPROD' else 'exp', {})[r['TIME_PERIOD']] = v
    out = {}
    for a, d in mon.items():
        rec = {}
        for k in ('prod', 'exp'):
            ms = d.get(k) or {}
            by = {}
            for p, v in ms.items():
                by.setdefault(p[:4], []).append(v)
            rec[k] = {y: [round(sum(v) / len(v)), len(v)] for y, v in sorted(by.items()) if len(v) >= 9}
            rec['last_' + k] = max(ms) if ms else ''
        if any(v[0] >= 100 for v in rec['prod'].values()):          # economies that produce at least 100,000 barrels a day
            out[a] = rec
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
    return tidy(out, last)


if __name__ == '__main__':
    want = sys.argv[1:] or list(ECON)
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'countries': {}}
    fx = {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in get(ECB % START)}
    gbp = {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in get(ECB.replace('M.USD.EUR', 'M.GBP.EUR') % START)}
    fxg = {m: fx[m] / gbp[m] for m in fx if m in gbp}
    oil = jodi_oil(set(ECON.values()))
    out = dict(old.get('countries', {}))
    for iso in want:
        rec = mirror(iso)
        rec['prod'] = {'EU': eu_products(ECON[iso], fx), 'UK': uk_products(UK_ID[iso], fxg), 'BR': br_products(BR_ID[iso])}
        if ECON[iso] in oil:
            rec['oil'] = oil[ECON[iso]]
        out[iso] = rec
        sys.stderr.write('%s: full year %d, %d partners, products to %s; oil %s\n' % (iso, rec['full'], len(rec['yx'][str(rec['full'])]),
                         ' '.join(k + ' ' + v['upto'] for k, v in rec['prod'].items()), 'yes' if 'oil' in rec else 'no'))
    json.dump({'source': 'IMF IMTS (partners\' records); Eurostat DS-045409, HMRC OTS and Comex Stat (products); JODI-Oil (crude oil)', 'unit': 'thousand USD', 'fetched': datetime.date.today().isoformat(),
               'countries': dict(sorted(out.items()))}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    sys.stderr.write('sanctions.json: %d economies, %.1f MB\n' % (len(out), os.path.getsize(OUT) / 1e6))
