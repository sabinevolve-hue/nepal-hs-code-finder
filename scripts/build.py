import json, re
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from aliases import ALIASES
d = json.load(open(__import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'parsed.json'))

def norm_unit(u):
    u = re.sub(r'\s*/\s*', '/', u.strip()).rstrip('.')
    return u.replace('Kg', 'kg').replace('KG', 'kg').replace('Nos', 'nos').replace('Pair', 'pair').replace('ltr.', 'ltr')

def norm_rate(r):
    r = r.strip()
    if r.lower() == 'free': return 'Free'
    r = r.replace('Perent', 'Percent').replace('which ever is high', 'whichever is higher').replace('ltrRs', 'ltr Rs')
    r = r.replace('correspondi ng', 'corresponding').replace('Rs.', 'Rs. ').replace('Rs.  ', 'Rs. ')
    r = re.sub(r'\s+', ' ', r)
    r = re.sub(r'Rs\s(\d)', r'Rs. \1', r)
    return r

# string table for group paths
strs, sidx = [], {}
def S(t):
    if t not in sidx: sidx[t] = len(strs); strs.append(t)
    return sidx[t]

rows = []
for r in d['rows']:
    desc = r['d'].replace('cigaretters', 'cigarettes')
    rows.append([r['code'], desc, [S(p) for p in r['p'] if p], norm_unit(r['u']), norm_rate(r['s']), norm_rate(r['g']), r['pg'] or 0, r.get('ldc', '')])

codes = [r[0] for r in rows]
alias_out = []
for terms, prefixes in ALIASES:
    ok = [p for p in prefixes if any(c.replace('.', '').startswith(p.replace('.', '')) for c in codes)]
    bad = [p for p in prefixes if p not in ok]
    if bad: print('ALIAS PREFIX NOT FOUND', terms[:30], bad)
    if ok: alias_out.append([[t.strip() for t in terms.split(',')], ok])

sections = [dict(n=('I' if s['n']=='1' else s['n']), t=(lambda x:x[:1].upper()+x[1:].lower())(re.split(r' \d\.-',s['t'])[0].strip()), f=s['first']) for s in d['sections']]
roman = {'1': 'I'}
chapters = {int(k): dict(t=v['t'], s=v['s'], n=v['notes'], pg=v['pg']) for k, v in d['chapters'].items()}
heads = {k: [v['t'], v.get('pg') or 0] for k, v in d['headings'].items()}
export = {k: [v['d'], norm_rate(v['r'])] for k, v in d['export'].items()}

data = dict(v='2026/27', rows=rows, strs=strs, heads=heads, chapters=chapters, sections=sections, export=export, aliases=alias_out)
js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
js = re.sub(r'\\u00[01][0-9a-f]', '-', js)
open(__import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'tariff.json', 'w').write(js)
print('rows', len(rows), 'size KB', len(js.encode()) // 1024, 'aliases', len(alias_out))
print([ (s['n'], s['f'], s['t'][:40]) for s in sections])
