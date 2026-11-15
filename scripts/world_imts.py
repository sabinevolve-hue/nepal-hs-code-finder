#!/usr/bin/env python3
"""Latest trade by partner for world.customsnepal.com -> data/world/imts.json.

Source: International Monetary Fund, International Trade in Goods by partner country (IMTS, formerly Direction of Trade).
The IMF collects each economy's own customs figures every month and publishes them in US dollars, converted at the
average exchange rate of the month the goods moved. That is the standard for trade (a flow through the month), and it
is why this script does no currency conversion of its own.

Where an economy has not reported yet, the IMF fills the gap with an estimate (from partner records or earlier data)
and flags the value. Flagged values are kept, and marked as estimates, so pages can say so.

Stored per economy, values in thousand US dollars:
  x, m     monthly totals with the world {'YYYY-MM': value}   (from 2019)
  xe, me   months whose total is flagged as an estimate
  p        {partner: [x_prev, x_full, x_ytd, x_ytd_prev, m_prev, m_full, m_ytd, m_ytd_prev, est]}
           full = latest complete calendar year, prev = the year before, ytd = current year to the newest month
  full, cur, upto   the years and newest month number those refer to
  pa       {year: {partner: [x, m, est]}} calendar-year totals by partner from 2019, for the year pages: every partner
           with at least $100,000 either way that year
  pn       {year: [number of export markets, number of suppliers]} (partners with at least $1,000 that year)
  ax, am   {year: total} calendar-year totals for the complete years before 2019, back to 2000 (the long history)
  axe      years before 2019 in which some of the total was estimated by the IMF
  ph       {year: {partner: [x, m]}} the fifteen largest markets and suppliers in 2000, 2005, 2010 and 2015.
           Fetched once and kept: these years do not change.
Months are only added on refresh; nothing already stored is dropped.

Usage:  python3 scripts/world_imts.py [ISO ...]      (no arguments = every economy on the site)
"""
import concurrent.futures as cf, csv, datetime, io, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'imts.json')
API = 'https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS/%s.XG_FOB_USD+MG_CIF_USD.%s.M?startPeriod=%s%s'
K = lambda v: int(round(v / 1000.0))


SNAP = (2000, 2005, 2010, 2015)


def get(iso, counterpart, start, dataonly, end=None):
    url = API % (iso, counterpart, start, ('&detail=dataonly' if dataonly else '') + ('&endPeriod=' + end if end else ''))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/vnd.sdmx.data+csv', 'User-Agent': 'world.customsnepal.com data build'})
            with urllib.request.urlopen(req, timeout=180) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode('utf-8'))))
        except Exception as e:          # the API answers 404 for an economy with no data
            if 'HTTP Error 404' in str(e):
                return []
            time.sleep(3 + 4 * attempt)
    return None


def month(tp):                          # '2025-M03' -> '2025-03'
    return tp[:4] + '-' + tp[6:8] if len(tp) >= 8 and tp[5] == 'M' else None


def build(iso, old):
    tot = get(iso, 'G001', '2000-01', False)
    if not tot:
        return iso, None
    x = dict(old.get('x', {})); m = dict(old.get('m', {})); xe = set(old.get('xe', [])); me = set(old.get('me', []))
    hx, hm, he = {}, {}, set()          # months before 2019, only to build the yearly history
    for r in tot:
        p = month(r['TIME_PERIOD'])
        if not p or not r['OBS_VALUE']:
            continue
        if p < '2019-01':
            (hx if r['INDICATOR'] == 'XG_FOB_USD' else hm).setdefault(p[:4], {})[p] = float(r['OBS_VALUE'])
            if r.get('STATUS'):
                he.add(p[:4])
            continue
        d, e = (x, xe) if r['INDICATOR'] == 'XG_FOB_USD' else (m, me)
        d[p] = K(float(r['OBS_VALUE'])); (e.add if r.get('STATUS') else e.discard)(p)
    both = sorted(set(x) & set(m))
    if not both:
        return iso, None
    last = both[-1]; ly, lm = int(last[:4]), int(last[5:])
    full = ly if lm == 12 else ly - 1; cur = ly if lm < 12 else None
    rows = get(iso, '', '2019-01', False)
    if rows is None:
        return iso, None
    P = {}; A = {}
    for r in rows:
        c = r['COUNTERPART_COUNTRY']; p = month(r['TIME_PERIOD'])
        if len(c) != 3 or not p or not r['OBS_VALUE']:      # skip regional aggregates (G..., TX...)
            continue
        v = float(r['OBS_VALUE']); y, mo = int(p[:4]), int(p[5:]); o = 0 if r['INDICATOR'] == 'XG_FOB_USD' else 4
        if y <= full:
            b = A.setdefault(y, {}).setdefault(c, [0.0, 0.0, 0])
            b[0 if o == 0 else 1] += v
            if r.get('STATUS'): b[2] = 1
        if y < full - 1:
            continue
        a = P.setdefault(c, [0.0] * 8 + [0])
        if y == full - 1: a[o] += v
        if y == full: a[o + 1] += v
        if cur and y == cur and mo <= lm: a[o + 2] += v
        if cur and y == cur - 1 and mo <= lm: a[o + 3] += v
        if r.get('STATUS') and y >= full: a[8] = 1
    p_out = {c: [K(v) for v in a[:8]] + [a[8]] for c, a in P.items() if max(a[:8]) >= 1000}
    pa, pn = {}, {}
    for y, d in sorted(A.items()):
        pa[str(y)] = {c: [K(d[c][0]), K(d[c][1]), d[c][2]] for c in sorted(d) if max(d[c][:2]) >= 100000}
        pn[str(y)] = [sum(1 for v in d.values() if v[0] >= 1000), sum(1 for v in d.values() if v[1] >= 1000)]
    ax = {y: K(sum(d.values())) for y, d in sorted(hx.items()) if len(d) == 12 and len(hm.get(y, {})) == 12}
    am = {y: K(sum(hm[y].values())) for y in ax}
    ph = dict(old.get('ph', {}))
    for y in SNAP:
        if str(y) in ph or str(y) not in ax:
            continue
        rr = get(iso, '', '%d-01' % y, True, '%d-12' % y)
        if rr is None:
            continue
        d = {}
        for r in rr:
            c = r['COUNTERPART_COUNTRY']
            if len(c) == 3 and r['OBS_VALUE']:
                d.setdefault(c, [0.0, 0.0])[0 if r['INDICATOR'] == 'XG_FOB_USD' else 1] += float(r['OBS_VALUE'])
        keep = set(sorted(d, key=lambda c: -d[c][0])[:15]) | set(sorted(d, key=lambda c: -d[c][1])[:15])
        ph[str(y)] = {c: [K(d[c][0]), K(d[c][1])] for c in sorted(keep) if max(d[c]) >= 100000}
    return iso, dict(x=dict(sorted(x.items())), m=dict(sorted(m.items())), xe=sorted(xe), me=sorted(me), p=p_out, full=full, cur=cur, upto=lm if cur else 12, pa=pa, pn=pn,
                     ax=ax, am=am, axe=sorted(y for y in he if y in ax), ph=ph)


if __name__ == '__main__':
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'countries': {}}
    isos = sys.argv[1:] or sorted(c['iso'] for c in json.load(open(os.path.join(ROOT, 'world', 'data', 'trade.json'), encoding='utf-8'))['countries'])
    out = dict(old['countries']); done = 0
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for iso, rec in ex.map(lambda i: build(i, old['countries'].get(i, {})), isos):
            done += 1
            if rec:
                out[iso] = rec
            if done % 20 == 0:
                sys.stderr.write('%d/%d\n' % (done, len(isos)))
    json.dump({'source': 'International Monetary Fund, International Trade in Goods (by partner country), IMTS', 'unit': 'thousand USD',
               'fetched': datetime.date.today().isoformat(), 'countries': dict(sorted(out.items()))},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    sys.stderr.write('imts.json: %d economies, %.1f MB\n' % (len(out), os.path.getsize(OUT) / 1e6))
