#!/usr/bin/env python3
"""Import tariffs from official national schedules that are free to republish -> data/world/tariffs/<iso>.json.

Only schedules whose licence allows republication are used. WTO tariff data is NOT used: its terms allow
non-commercial use only and require WTO permission to re-publish (checked 16 November 2026).

  United States  Harmonized Tariff Schedule (USITC), current revision. A U.S. Government work, public domain.

Output per country:
  meta   source, edition, release date, licence, links
  lines  [[code, description path, general rate, special rate text, column 2 rate, notes], ...]  rate lines only
  n99    how many chapter 99 headings add a duty on top of "the duty provided in the applicable subheading"

Run: python3 scripts/world_tariffs.py   (needs network; ~13 MB download). Standard library only.
"""
import json, pathlib, re, subprocess, datetime

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


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    d = usa()
    (OUT / 'usa.json').write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('world_tariffs: USA %s, %d rate lines; %d chapter 99 headings add duty' % (d['meta']['edition'], len(d['lines']), d['n99']))
