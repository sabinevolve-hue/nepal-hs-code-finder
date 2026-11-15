#!/usr/bin/env python3
"""Latest product detail from two more national sources -> data/world/more_products.json (same shape as eu_products.json).

United Kingdom: HM Revenue & Customs, Overseas Trade Statistics (api.uktradeinfo.com), monthly, pounds sterling, EU and
  non-EU trade added together. Each month is converted to US dollars at that month's average rate, taken as the cross of
  the ECB's monthly average reference rates for the dollar and the pound against the euro.
Brazil: Ministry of Development, Industry, Trade and Services, Comex Stat (api-comexstat.mdic.gov.br), published in US
  dollars (FOB) by the ministry, so no conversion is done here.

Per economy, thousand US dollars:  xc, mc = [[HS chapter, prev year, full year, year to date, same months a year earlier]];
xk, mk = the same for the 15 largest six-digit products of the full year.
Usage:  python3 scripts/world_more_products.py
"""
import csv, datetime, io, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'more_products.json')
TOP = 15
K = lambda v: int(round(v / 1000.0))
UA = {'User-Agent': 'world.customsnepal.com data build'}


def http(url, body=None):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=dict(UA, **({'Content-Type': 'application/json'} if body else {})))
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode('utf-8')
        except Exception:
            time.sleep(4 + 5 * attempt)
    raise SystemExit('failed: ' + url)


def periods(last):
    ly, lm = int(last[:4]), int(last[5:])
    full = ly if lm == 12 else ly - 1
    return full, (None if lm == 12 else ly), lm


def add(a, y, mo, v, full, cur, lm):
    if y == full - 1: a[0] += v
    if y == full: a[1] += v
    if cur and y == cur and mo <= lm: a[2] += v
    if cur and y == cur - 1 and mo <= lm: a[3] += v


# ---------------------------------------------------------------- United Kingdom
def uk():
    yr = datetime.date.today().year
    ecb = lambda cur: {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in csv.DictReader(io.StringIO(http(
        'https://data-api.ecb.europa.eu/service/data/EXR/M.%s.EUR.SP00.A?startPeriod=%d-01&format=csvdata' % (cur, yr - 3))))}
    usd, gbp = ecb('USD'), ecb('GBP'); fx = {m: usd[m] / gbp[m] for m in usd if m in gbp}            # US dollars per pound, monthly average
    api = 'https://api.uktradeinfo.com/OTS?$apply='
    def q(apply):
        out = []; url = api + urllib.parse.quote(apply, safe='()/,$=')
        while url:
            d = json.loads(http(url)); out += d['value']; url = d.get('@odata.nextLink')
        return out
    months = sorted(r['MonthId'] for r in q('filter(MonthId ge %d01)/groupby((MonthId),aggregate(Value with sum as V))' % (yr - 1)) if r['V'] > 0)
    last = max(m for m in ('%d-%02d' % (x // 100, x % 100) for x in months) if m in fx)
    full, cur, lm = periods(last); start = (full - 1) * 100 + 1; end = int(last.replace('-', ''))
    flow = lambda f: 'x' if f in (2, 4) else 'm'
    def bucket(rows, key):
        out = {}
        for r in rows:
            code = (r.get('Commodity') or {}).get(key); p = '%d-%02d' % (r['MonthId'] // 100, r['MonthId'] % 100)
            if not code or p not in fx:
                continue
            add(out.setdefault((flow(r['FlowTypeId']), code), [0.0] * 4), r['MonthId'] // 100, r['MonthId'] % 100, r['V'] * fx[p], full, cur, lm)
        return out
    ch = bucket(q('filter(MonthId ge %d and MonthId le %d)/groupby((Commodity/Hs2Code,MonthId,FlowTypeId),aggregate(Value with sum as V))' % (start, end)), 'Hs2Code')
    ann = {}
    for r in q('filter(MonthId ge %d01 and MonthId le %d12)/groupby((Commodity/Hs6Code,FlowTypeId),aggregate(Value with sum as V))' % (full, full)):
        code = (r.get('Commodity') or {}).get('Hs6Code')
        if code and code.isdigit():
            ann[(flow(r['FlowTypeId']), code)] = ann.get((flow(r['FlowTypeId']), code), 0.0) + r['V']
    tops = {f: [k for (ff, k), _ in sorted(((kk, v) for kk, v in ann.items() if kk[0] == f), key=lambda kv: -kv[1])[:TOP]] for f in ('x', 'm')}
    codes = sorted(set(tops['x']) | set(tops['m']))
    cond = ' or '.join("Commodity/Hs6Code eq '%s'" % c for c in codes)
    pk = bucket(q('filter(MonthId ge %d and MonthId le %d and (%s))/groupby((Commodity/Hs6Code,MonthId,FlowTypeId),aggregate(Value with sum as V))' % (start, end, cond)), 'Hs6Code')
    rec = dict(src='HM Revenue & Customs, Overseas Trade Statistics; pounds converted to US dollars at monthly average ECB reference rates',
               short='HM Revenue & Customs', last=last, full=full, cur=cur, upto=lm if cur else 12)
    for f in ('x', 'm'):
        rec[f + 'c'] = sorted(([p] + [K(v) for v in a] for (ff, p), a in ch.items() if ff == f and a[1] > 0 and p.isdigit()), key=lambda r: -r[2])
        rec[f + 'k'] = sorted(([p] + [K(v) for v in pk[(f, p)]] for p in tops[f] if (f, p) in pk), key=lambda r: -r[2])
    return rec


# ---------------------------------------------------------------- Brazil
def brazil():
    api = 'https://api-comexstat.mdic.gov.br/general?language=en'
    upd = json.loads(http('https://api-comexstat.mdic.gov.br/general/dates/updated'))['data']
    last = '%s-%02d' % (upd['year'], int(upd['monthNumber'])); full, cur, lm = periods(last)
    spans = [('%d-01' % (full - 1), '%d-12' % (full - 1)), ('%d-01' % full, '%d-12' % full)] + ([('%d-01' % cur, last), ('%d-01' % (cur - 1), '%d-%02d' % (cur - 1, lm))] if cur else [])
    rec = dict(src='Ministry of Development, Industry, Trade and Services of Brazil, Comex Stat; published in US dollars (FOB)',
               short='Brazil&#39;s trade ministry (Comex Stat)', last=last, full=full, cur=cur, upto=lm if cur else 12)
    for f, flow in (('x', 'export'), ('m', 'import')):
        for detail, field, key in (('chapter', 'chapterCode', 'c'), ('subHeading', 'subHeadingCode', 'k')):
            vals = {}
            for i, (a, b) in enumerate(spans):
                body = {'flow': flow, 'monthDetail': False, 'period': {'from': a, 'to': b}, 'filters': [], 'details': [detail], 'metrics': ['metricFOB']}
                for r in json.loads(http(api, body))['data']['list']:
                    # a span that crosses no year boundary still comes back per year
                    vals.setdefault(r[field], [0.0] * 4)[i] += float(r['metricFOB'] or 0)
            rows = sorted(([p] + [K(v) for v in a] for p, a in vals.items() if a[1] > 0), key=lambda r: -r[2])
            rec[f + key] = rows if key == 'c' else rows[:TOP]
    return rec


out = {}
for iso, fn in (('GBR', uk), ('BRA', brazil)):
    out[iso] = fn(); sys.stderr.write('%s to %s\n' % (iso, out[iso]['last']))
json.dump({'unit': 'thousand USD', 'fetched': datetime.date.today().isoformat(), 'countries': out}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
