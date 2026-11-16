#!/usr/bin/env python3
"""Import tariffs from official national schedules that are free to republish -> data/world/tariffs/<iso>.json.

Only schedules whose licence allows republication are used. WTO tariff data is NOT used: its terms allow
non-commercial use only and require WTO permission to re-publish (checked 16 November 2026).

  United States   Harmonized Tariff Schedule (USITC), current revision. A U.S. Government work, public domain.
  United Kingdom  UK Global Tariff via the GOV.UK Trade Tariff API (HMRC). Open Government Licence v3.0.
  European Union  EU third-country duties (Common Customs Tariff) via the same service's EU tariff for Northern Ireland
                  (/xi/), which applies the EU tariff. EU content: CC BY 4.0 (Commission Decision 2011/833/EU).
  Australia       Customs Tariff Act 1995 Schedule 3 (general rates), Australian Border Force. Department of Home Affairs
                  website content: Creative Commons Attribution 3.0 Australia.
  Japan           Japan's Tariff Schedule (Japan Customs, English reference edition). Public Data License 1.0.
                  The rate shown is the one Japan Customs says applies to WTO members: the lower of the WTO rate and the
                  statutory rate (Temporary where set, otherwise General). Where they cannot be compared (per-unit or
                  mixed rates), the three are shown as printed.

Output per country:
  meta   source, edition, release date, licence, links
  lines  [[code, description path, general rate, special rate text, column 2 rate, notes], ...]  rate lines only
  n99    how many chapter 99 headings add a duty on top of "the duty provided in the applicable subheading"

Run: python3 scripts/world_tariffs.py   (needs network; ~13 MB download). Standard library only.
"""
import json, pathlib, re, subprocess, datetime, sys, time, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'world' / 'tariffs'


def get(url, timeout=240):
    """Plain curl, as used to check these files by hand (usitc.gov answers 403 to Python's default client)."""
    return subprocess.run(['curl', '-sSf', '-m', str(timeout), url], check=True, capture_output=True).stdout


def clean(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return re.sub(r'\s+', ' ', s).strip().rstrip(':').strip()


def usa():
    rel = json.loads(get('https://hts.usitc.gov/reststop/releaseList'))
    cur = next(r for r in rel if r.get('status') == 'current')
    m = re.match(r'(\d{4})HTSRev(\d+)$', cur['name']) or re.match(r'(\d{4})HTS(Basic)$', cur['name'])
    year, rev = m.group(1), m.group(2)
    fname = 'hts_%s_basic_edition_json.json' % year if rev == 'Basic' else 'hts_%s_revision_%s_json.json' % (year, rev)
    src = 'https://www.usitc.gov/sites/default/files/tata/hts/' + fname
    rows = json.loads(get(src))
    path, lines, n99 = {}, [], 0
    for x in rows:
        code = (x.get('htsno') or '').strip(); desc = clean(x.get('description'))
        ind = int(x.get('indent') or 0)
        digits = code.replace('.', '')
        if digits and len(digits) == 4:
            path = {0: desc}                       # a new heading resets the description path
        else:
            path[ind] = desc
            for k in [k for k in path if k > ind]:
                del path[k]
        gen = clean(x.get('general'))
        if digits[:2] == '99' and len(digits) == 8 and re.search(r'applicable subheading \+', gen):
            n99 += 1
        if not gen or not digits or len(digits) < 8 or digits[:2] in ('98', '99'):
            continue
        parts = [path[k] for k in sorted(path) if path.get(k)]
        notes = sorted({clean(f.get('value')) for f in (x.get('footnotes') or []) if clean(f.get('value'))})
        lines.append([digits, ' › '.join(parts), gen, clean(x.get('special')), clean(x.get('other')), notes])
    meta = {'iso': 'USA', 'name': 'United States', 'source': 'Harmonized Tariff Schedule of the United States',
            'publisher': 'U.S. International Trade Commission', 'edition': cur.get('title') or cur['name'],
            'release': cur.get('releaseStartDate') or cur.get('date'), 'file': src,
            'licence': 'U.S. Government work, public domain', 'licence_url': 'https://www.usa.gov/government-copyright',
            'search': 'https://hts.usitc.gov/', 'ch99': 'https://hts.usitc.gov/search?query=9903',
            'read': datetime.date.today().isoformat()}
    return {'meta': meta, 'lines': lines, 'n99': n99}


UKAPI = 'https://www.trade-tariff.service.gov.uk/uk/api/'


def ukget(path, base=None):
    for i in range(4):
        try:
            return json.loads(subprocess.run(['curl', '-sSf', '-m', '60', '-H', 'Accept: application/vnd.hmrc.2.0+json', (base or UKAPI) + path],
                                             check=True, capture_output=True).stdout)
        except subprocess.CalledProcessError as e:
            if b'404' in (e.stderr or b''):
                return None
            time.sleep(3 * (i + 1))
    raise RuntimeError('UK tariff API failed: ' + path)


def ukrate(t):
    """'12.00%' -> '12%', '0.00%' -> '0%'; other expressions kept as printed."""
    t = re.sub(r'\s+', ' ', t or '').strip().replace(' %', '%')
    return re.sub(r'(\d+)\.(\d*?)0+%', lambda m: m.group(1) + ('.' + m.group(2) if m.group(2) else '') + '%', t)


def uk(region='uk'):
    """Third-country (MFN) duty for every declarable commodity, read heading by heading (about 1,230 requests).
    region 'uk' = UK Global Tariff; 'xi' = the EU tariff as applied in Northern Ireland (EU third-country duties)."""
    base = 'https://www.trade-tariff.service.gov.uk/%s/api/' % region
    _get = ukget
    ukget_ = lambda path: _get(path, base)
    lines = []
    sec = ukget_('sections')
    chapters = []
    for s_ in sec['data']:
        d = ukget_('sections/%s' % s_['id'])
        chapters += [i['attributes']['goods_nomenclature_item_id'][:2] for i in d.get('included', []) if i['type'] == 'chapter']
    for ch in sorted(set(chapters)):
        cd = ukget_('chapters/%s' % ch)
        heads = [i['attributes']['goods_nomenclature_item_id'][:4] for i in cd.get('included', []) if i['type'] == 'heading']
        for hd in heads:
            d = ukget_('headings/%s' % hd)
            if not d:
                continue
            inc = {(i['type'], i['id']): i for i in d.get('included', [])}
            hdesc = clean(d['data']['attributes'].get('description_plain') or d['data']['attributes'].get('description'))
            coms = [i for i in d.get('included', []) if i['type'] == 'commodity']
            if not coms:                                   # a declarable heading has its measures on itself
                coms = [d['data']]
            sid = {c['attributes'].get('goods_nomenclature_sid'): c for c in coms}
            for c in coms:
                a = c['attributes']
                if coms[0] is not d['data'] and not (a.get('leaf') and a.get('declarable', True)):
                    continue
                duties = []
                for m in ((c.get('relationships') or {}).get('overview_measures') or {}).get('data') or []:
                    mm = inc.get(('measure', m['id']))
                    if not mm or mm['relationships']['measure_type']['data']['id'] != '103':
                        continue
                    if (mm['relationships'].get('additional_code') or {}).get('data'):
                        continue
                    de = inc.get(('duty_expression', mm['relationships']['duty_expression']['data']['id']))
                    if de:
                        duties.append(ukrate(clean(de['attributes'].get('base'))))
                if not duties:
                    continue
                path, p = [], c
                while p is not None and p is not d['data']:
                    path.append(clean(p['attributes'].get('description_plain') or p['attributes'].get('description')))
                    p = sid.get(p['attributes'].get('parent_sid'))
                parts = [hdesc] + [x for x in reversed(path) if x and x != hdesc]
                lines.append([(a.get('goods_nomenclature_item_id') or '')[:10], ' › '.join(parts), ' or '.join(dict.fromkeys(duties)), '', '', []])
            time.sleep(0.15)
        print('  %s chapter' % region, ch, len(lines), file=sys.stderr)
    lines.sort()
    if region == 'xi':
        return {'meta': {'iso': 'EUU', 'name': 'European Union', 'source': 'EU Common Customs Tariff (third-country duties)',
                         'publisher': 'European Commission, as published in the EU tariff of the GOV.UK Trade Tariff (Northern Ireland)',
                         'edition': 'as at ' + datetime.date.today().strftime('%-d %B %Y'), 'release': datetime.date.today().isoformat(),
                         'file': 'https://www.trade-tariff.service.gov.uk/xi/find_commodity',
                         'licence': '© European Union, reused under CC BY 4.0 (Commission Decision 2011/833/EU); service content under the Open Government Licence v3.0',
                         'licence_url': 'https://creativecommons.org/licenses/by/4.0/',
                         'search': 'https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp', 'read': datetime.date.today().isoformat()},
                'lines': lines}
    meta = {'iso': 'GBR', 'name': 'United Kingdom', 'source': 'UK Global Tariff', 'publisher': 'HM Revenue & Customs, GOV.UK Trade Tariff',
            'edition': 'as at ' + datetime.date.today().strftime('%-d %B %Y'), 'release': datetime.date.today().isoformat(),
            'file': 'https://www.trade-tariff.service.gov.uk/', 'licence': 'Contains public sector information licensed under the Open Government Licence v3.0',
            'licence_url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
            'search': 'https://www.trade-tariff.service.gov.uk/find_commodity', 'read': datetime.date.today().isoformat()}
    return {'meta': meta, 'lines': lines}


AUBASE = 'https://www.abf.gov.au'
AUS3 = '/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3'


def aus():
    """General rate for every 8-digit line in Schedule 3, chapter page by chapter page (about 100 requests)."""
    txt = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x))).replace('\u200b', '').strip()
    links = lambda page, part: sorted(set(re.findall(r'href="(%s/%s[^"#]*)"' % (re.escape(AUS3), part), page)))
    lines = []
    for sec in links(get(AUBASE + AUS3).decode('utf-8', 'replace'), 'section-[ivx]+'):
        if sec.count('/') != AUS3.count('/') + 1:
            continue
        for chp in links(get(AUBASE + sec).decode('utf-8', 'replace'), sec.rsplit('/', 1)[1] + '/chapter-\\d+'):
            page = get(AUBASE + chp).decode('utf-8', 'replace')
            head, levels = '', {}
            for row in re.findall(r'<tr[^>]*>(.*?)</tr>', page, re.S):
                th = [txt(x) for x in re.findall(r'<th[^>]*>(.*?)</th>', row, re.S)]
                td = [txt(x) for x in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
                if not th or len(td) < 4 or not re.match(r'^\d{4}', th[0]):
                    continue
                code = re.sub(r'\D', '', th[0]); goods, rate_ = td[2], td[3]
                if len(code) == 4:
                    head = goods.rstrip(':').strip(); head = head[:1] + head[1:].lower(); levels = {}
                    continue
                m = re.match(r'^(-+)\s*(.*)$', goods)
                lvl, desc = (len(m.group(1)), m.group(2)) if m else (1, goods)
                desc = desc.rstrip(':').strip()
                levels[lvl] = desc
                for k in [k for k in levels if k > lvl]:
                    del levels[k]
                if len(code) == 8 and rate_:
                    notes = []
                    if re.search(r'From\s*\d{1,2} \w+ \d{4}', rate_):     # a phased rate: keep the step now in force
                        steps = re.split(r'From\s*(\d{1,2} \w+ \d{4}):?\s*', rate_)
                        cur = steps[0].strip()
                        for k in range(1, len(steps) - 1, 2):
                            if datetime.datetime.strptime(steps[k], '%d %B %Y').date() <= datetime.date.today():
                                cur = steps[k + 1].strip()
                        notes = ['Phased rate in the schedule: ' + re.sub(r'\s*From\s*', '; From ', rate_).strip('; ')]
                        rate_ = cur
                    # the cell holds the general rate, then rates for listed origins ("5% DCS:4% CA:Free")
                    m2 = re.search(r'(?:[A-Z]{2,4}/)*[A-Z]{2,4}:', rate_)
                    gen, pref = (rate_[:m2.start()].strip(), rate_[m2.start():]) if m2 else (rate_, '')
                    pref = re.sub(r'\s*((?:[A-Z]{2,4}/)*[A-Z]{2,4}:)\s*', r' \1', pref).strip()
                    lines.append([code, ' › '.join([head] + [levels[k] for k in sorted(levels)]), gen or rate_, pref, '', notes])
            time.sleep(0.3)
        print('  AU', sec.rsplit('/', 1)[1], len(lines), file=sys.stderr)
    lines.sort()
    meta = {'iso': 'AUS', 'name': 'Australia', 'source': 'Customs Tariff Act 1995, Schedule 3', 'publisher': 'Australian Border Force',
            'edition': 'as at ' + datetime.date.today().strftime('%-d %B %Y'), 'release': datetime.date.today().isoformat(),
            'file': AUBASE + AUS3, 'licence': 'Content from the Department of Home Affairs website, licensed under Creative Commons Attribution 3.0 Australia',
            'licence_url': 'https://creativecommons.org/licenses/by/3.0/au/', 'search': AUBASE + AUS3, 'read': datetime.date.today().isoformat()}
    return {'meta': meta, 'lines': lines}


JPBASE = 'https://www.customs.go.jp/english/tariff/'


def _jp_num(t):
    t = (t or '').strip().strip('()').strip()
    if t.lower() == 'free':
        return 0.0
    m = re.fullmatch(r'(\d+(?:\.\d+)?)%', t)
    return float(m.group(1)) if m else None


def jpn():
    """Japan's tariff, chapter page by chapter page (97 requests), from the newest edition listed on the index."""
    idx = get(JPBASE + 'index.htm').decode('utf-8', 'replace')
    eds = sorted(set(re.findall(r'/english/tariff/(\d{4}_\d{2}_\d{2})/index\.htm', idx)))
    today = datetime.date.today().strftime('%Y_%m_%d')
    ed = [x for x in eds if x <= today][-1]
    txt = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x))).strip()
    lines = []
    for ch in range(1, 98):
        if ch == 77:
            continue
        try:
            raw = get(JPBASE + '%s/data/e_%02d.htm' % (ed, ch))
            cs_ = re.search(rb'charset=["\']?([\w-]+)', raw[:3000])
            page = raw.decode(cs_.group(1).decode() if cs_ else 'utf-8', 'replace').replace('\uff08', '(').replace('\uff09', ')')
        except subprocess.CalledProcessError:
            continue
        head, sub6, levels = '', '', {}
        for r in re.findall(r'<tr[^>]*>(.*?)</tr>', page, re.S):
            tds = [txt(x) for x in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
            cs = re.search(r'class="shell_var1_CSTNO"[^>]*>(.*?)</td>', r, re.S)
            it = re.search(r'class="shell_var1_ITEM_NAME"[^>]*padding-left:([\d.]+)em[^>]*>(.*?)</td>', r, re.S)
            if not cs:
                if tds and re.fullmatch(r'\d\d\.\d\d', tds[0]) and len(tds) > 2:
                    head = next((t for t in tds[1:4] if len(t) > 3), '').rstrip('.').strip(); levels = {}
                continue
            c6 = re.sub(r'\D', '', txt(cs.group(1)))
            if len(c6) == 6:
                sub6 = c6
            hs = re.search(r'class="shell_var1_HSCODE"[^>]*>(.*?)</td>', r, re.S)
            stat = re.sub(r'\D', '', txt(hs.group(1))) if hs else ''
            if it:
                lvl = float(it.group(1)); desc = re.sub(r'^\d+\s+', '', txt(it.group(2))).rstrip(':').strip()
                levels[lvl] = desc
                for k in [k for k in levels if k > lvl]:
                    del levels[k]
            if not sub6 or len(tds) < 6 or (len(stat) != 3 and len(c6) != 6):
                continue                          # a rate sits on a statistical line, or on a 6-digit line that has none
            gen, tmp, wto = tds[3], tds[4], tds[5]
            if not (gen or tmp or wto):
                continue
            stat_ = tmp or gen
            a, b = _jp_num(wto), _jp_num(stat_)
            if a is not None and b is not None:
                main = wto.strip('()') if a < b else stat_
            else:
                main = ''                         # not comparable: the page shows all three
            lines.append([sub6 + stat if len(stat) == 3 else sub6, ' › '.join([head] + [levels[k] for k in sorted(levels)]), main or 'Lower of the rates shown',
                          'General: %s · Temporary: %s · WTO: %s' % (gen or '–', tmp or '–', wto or '–'), '',
                          [] if main else ['WTO and statutory rates are not directly comparable here; the lower one applies (Japan Customs).']])
        time.sleep(0.3)
        if ch % 10 == 0:
            print('  JP chapter', ch, len(lines), file=sys.stderr)
    d = datetime.datetime.strptime(ed, '%Y_%m_%d').date()
    meta = {'iso': 'JPN', 'name': 'Japan', 'source': "Japan's Tariff Schedule", 'publisher': 'Japan Customs (Ministry of Finance)',
            'edition': 'as of ' + d.strftime('%-d %B %Y'), 'release': d.isoformat(), 'file': JPBASE + ed + '/index.htm',
            'licence': 'Public Data License 1.0 (Ministry of Finance, Japan Customs website); English edition published for reference only',
            'licence_url': 'https://www.digital.go.jp/en/resources/open_data/public_data_license_v1.0',
            'search': JPBASE + ed + '/index.htm', 'read': datetime.date.today().isoformat()}
    return {'meta': meta, 'lines': lines}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1:] or ['usa', 'gbr', 'euu', 'aus', 'jpn']
    for k, fn in (('usa', usa), ('gbr', uk), ('euu', lambda: uk('xi')), ('aus', aus), ('jpn', jpn)):
        if k not in which:
            continue
        d = fn()
        (OUT / (k + '.json')).write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print('world_tariffs: %s %s, %d rate lines' % (d['meta']['name'], d['meta']['edition'], len(d['lines'])))
