#!/usr/bin/env python3
"""Mount the world.customsnepal.com SPA under the main site at customsnepal.com/world.

world/ is now prerendered (scripts/world_prerender.py): one static page per route, served by the separate
`customsnepal-world` Vercel project. The /world mount on the main domain deliberately stays SPA-only — a single
self-contained shell (CSS + JS inlined, data in public/world/data/) that the main project's rewrite
`/world/(...)` → `/world` serves for every /world/* path. It carries NO static canonical: once the SPA routes, its
seoSync() sets <link rel=canonical> to the matching https://world.customsnepal.com/... URL, so the mount never
competes with the subdomain as duplicate content (the subdomain owns indexing; its pages are the canonical copies).

Source of truth stays world/ — this runs as part of `npm run build`, so every deploy re-syncs. Config files
(vercel.json, robots.txt, sitemaps) and the prerendered route files belong to the standalone project and are skipped."""
import pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = ROOT / 'world'
dst = ROOT / 'public' / 'world'

if not (src / 'index.html').exists():
    sys.exit('mount_world: world/index.html not found — nothing to mount')
page = (src / 'index.html').read_text(encoding='utf-8')

def asset(kind):
    m = re.search(r'/assets/(world\.[0-9a-f]+\.' + kind + ')', page)
    if not m: sys.exit(f'mount_world: no {kind} asset referenced by world/index.html — run scripts/world_prerender.py')
    return m.group(0), (src / 'assets' / m.group(1)).read_text(encoding='utf-8')

css_href, css = asset('css')
js_href, js = asset('js')

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%231B2A45%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
SEO = ('<title>World HS Codes &amp; Global Trade — Customs Nepal</title>\n'
       '<meta name="description" content="Search the international Harmonized System and explore the import/export trade of 207 economies — world prices, top exporters and importers.">\n'
       '<meta property="og:site_name" content="Customs Nepal"><meta property="og:type" content="website"><meta property="og:title" content="World HS Codes &amp; Global Trade — Customs Nepal">'
       '<meta property="og:image" content="https://www.customsnepal.com/og.png">')

shell = re.sub(r'<!--seo-->.*?<!--/seo-->', lambda m: SEO, page, count=1, flags=re.S)
shell = shell.replace(f'<link rel="stylesheet" href="{css_href}">', '<style>\n' + css + '\n</style>')
shell = shell.replace(f'<script src="{js_href}" defer></script>\n', '')
shell = shell.replace('<link rel="icon" href="/favicon.svg" type="image/svg+xml">', f'<link rel="icon" href="{FAVICON}">')
shell = re.sub(r'<!--app-->.*?<!--/app-->', '<div class="empty" style="padding-top:80px">Loading…</div>', shell, count=1, flags=re.S)
# header links point inside the mount (the SPA's click handler strips /world before routing)
shell = re.sub(r'<header class="bar">.*?</header>',
               lambda m: m.group(0).replace('href="/', 'href="/world/').replace('href="/world/"', 'href="/world"').replace(' class="on"', ''),
               shell, count=1, flags=re.S)
shell = shell.replace('</body>', '<script>\n' + js.replace('</script', '<\\/script') + '\n</script>\n</body>')
for tag in ('<!--seo-->', '<meta name="cn-route"', 'rel="canonical"', css_href, js_href):
    assert tag not in shell, f'mount_world: shell still contains {tag}'

shutil.rmtree(dst, ignore_errors=True)
(dst / 'data').mkdir(parents=True, exist_ok=True)
(dst / 'index.html').write_text(shell, encoding='utf-8')
n = 0
for f in sorted((src / 'data').glob('*.json')):
    shutil.copy2(f, dst / 'data' / f.name)
    n += 1

total = sum(x.stat().st_size for x in dst.rglob('*') if x.is_file())
print(f'mount_world: public/world/ <- SPA shell ({len(shell)/1024:.0f} KB, inlined CSS+JS) + {n} data files ({total/1024:.0f} KB)')
