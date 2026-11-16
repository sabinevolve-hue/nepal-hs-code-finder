#!/usr/bin/env python3
"""Import tariffs from official national schedules that are free to republish -> data/world/tariffs/<iso>.json.

Only schedules whose licence allows republication are used. WTO tariff data is NOT used: its terms allow
non-commercial use only and require WTO permission to re-publish (checked 16 November 2026).

  United States   Harmonized Tariff Schedule (USITC), current revision. A U.S. Government work, public domain.
  United Kingdom  UK Global Tariff via the GOV.UK Trade Tariff API (HMRC). Open Government Licence v3.0.
  European Union  EU third-country duties (Common Customs Tariff) via the same service's EU tariff for Northern Ireland
                  (/xi/), which applies the EU tariff. EU content: CC BY 4.0 (Commission Decision 2011/833/EU).

Output per country:
  meta   source, edition, release date, licence, links
  lines  [[code, description path, general rate, special rate text, column 2 rate, notes], ...]  rate lines only
  n99    how many chapter 99 headings add a duty on top of "the duty provided in the applicable subheading"

Run: python3 scripts/world_tariffs.py   (needs network; ~13 MB download). Standard library only.
"""
import json, pathlib, re, subprocess, datetime, sys, time

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


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1:] or ['usa', 'gbr', 'euu']
    for k, fn in (('usa', usa), ('gbr', uk), ('euu', lambda: uk('xi'))):
        if k not in which:
            continue
        d = fn()
        (OUT / (k + '.json')).write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print('world_tariffs: %s %s, %d rate lines' % (d['meta']['name'], d['meta']['edition'], len(d['lines'])))
