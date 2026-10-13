#!/usr/bin/env python3
"""Generate world/sitemap.xml for world.customsnepal.com from world/data/hs.json + trade.json.
Routes mirror the SPA router: hubs (/, /hs, /trade, /nepal) + 16 product groups + 97 chapters
+ 207 country profiles + 5,613 six-digit code pages. Run after the data is refreshed."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = 'https://world.customsnepal.com'
hs = json.load(open(ROOT / 'world/data/hs.json', encoding='utf-8'))
trade = json.load(open(ROOT / 'world/data/trade.json', encoding='utf-8'))
nepal = json.load(open(ROOT / 'world/data/nepal.json', encoding='utf-8'))

# Nepal export-destination markets (ISO3) — inverted from per-HS6 top partners, matches nepExports() in the SPA.
EX_DESTS = sorted({d[0].lower() for k, v in nepal.items()
                   if not k.startswith('_') and v.get('exs')
                   for d in v['exs'] if d[1] > 0})
EX_GUIDES = ['cardamom', 'carpets']  # must match EXGUIDES in world/index.html

# 16 product-group slugs — must match groupSlug() in world/index.html (stable).
GROUPS = ['animal-and-animal-products', 'vegetable-products', 'foodstuffs-beverages-and-tobacco',
          'minerals', 'mineral-fuels-and-oils', 'chemicals-and-allied', 'plastics-and-rubber',
          'hides-skins-and-leather', 'wood-and-paper', 'textiles-and-clothing', 'footwear-and-headgear',
          'stone-glass-and-precious-metals', 'base-metals', 'machinery-and-electronics',
          'transport-equipment', 'instruments-arms-and-misc']

urls = [('/', '1.0'), ('/hs', '0.9'), ('/trade', '0.9'), ('/nepal', '0.9'), ('/nepal/exports', '0.9')]
urls += [('/nepal/exports/guide/' + g, '0.8') for g in EX_GUIDES]
urls += [('/nepal/exports/' + iso, '0.6') for iso in EX_DESTS]
urls += [('/trade/product/' + g, '0.8') for g in GROUPS]
urls += [('/hs/chapter/' + c[0], '0.7') for c in hs['chapters']]
urls += [('/trade/' + c['iso'].lower(), '0.6') for c in trade['countries']]
urls += [('/hs/code/' + s[0], '0.5') for s in hs['subs']]

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, pr in urls:
    out.append(f'  <url><loc>{B}{path}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>')
out.append('</urlset>')
(ROOT / 'world/sitemap.xml').write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f'world sitemap: {len(urls):,} URLs '
      f'(hubs + {len(GROUPS)} groups + {len(hs["chapters"])} chapters + '
      f'{len(trade["countries"])} countries + {len(hs["subs"]):,} codes + '
      f'{len(EX_GUIDES)} export guides + {len(EX_DESTS)} Nepal export markets)')
