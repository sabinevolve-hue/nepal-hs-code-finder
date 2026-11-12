"""Keep vercel.json's 301s for replaced country pages in step with scripts/links.py.

/trade/country/<slug> was the older country page; where a /trade-partner/<slug> profile exists the old URL
must redirect to it (trade_pages.py no longer writes the old page). Runs in `npm run build`; vercel.json is
committed, so the redirect set that ships is the one this wrote. Only touches redirects whose source starts
with /trade/country/ — every other rule is left exactly as it is.
"""
import json, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
import links

p = root / 'vercel.json'
cfg = json.loads(p.read_text(encoding='utf-8'))
keep = [r for r in cfg.get('redirects', []) if not r['source'].startswith('/trade/country/')]
mine = [{"source": s, "destination": d, "permanent": True} for s, d in sorted(links.OLD_COUNTRY.items())]
cfg['redirects'] = mine + keep
lines = ['{']
keys = list(cfg)
for i, k in enumerate(keys):
    v = cfg[k]; end = ',' if i < len(keys) - 1 else ''
    if isinstance(v, list):
        lines.append('  %s: [' % json.dumps(k))
        lines += ['    ' + json.dumps(x, ensure_ascii=False) + (',' if j < len(v) - 1 else '') for j, x in enumerate(v)]
        lines.append('  ]' + end)
    else:
        lines.append('  %s: %s%s' % (json.dumps(k), json.dumps(v, ensure_ascii=False), end))
lines.append('}')
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
json.loads(p.read_text(encoding='utf-8'))
print('sync_redirects: %d country redirects, %d other rules kept' % (len(mine), len(keep)))
