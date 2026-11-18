#!/usr/bin/env python3
"""Point product links at the product's own page where one exists.

Many generated pages link a tariff line as href="/#hs-84502000" (or the dotted 8450.20.00). That opens the
product in the app, but to a search engine it is just a link to the home page. When the line has its own page,
/import-duty/<name>-<8 digits>, this pass rewrites the link to that page. Lines without a page keep the /#hs- link.
A product page's own "open in the tariff" link is left alone (it points to itself otherwise).
Runs after every page generator and before cross_site.py / check_pages.py. Running it twice changes nothing.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUB = ROOT / 'public'
PAGE = {}
for f in (PUB / 'import-duty').glob('*.html'):
    m = re.search(r'-(\d{8})\.html$', f.name)
    if m:
        PAGE[m.group(1)] = '/import-duty/' + f.stem

RX = re.compile(r'href="/#hs-(\d{4}\.?\d{2}\.?\d{2})"')

if __name__ == '__main__':
    n = files = 0
    for f in PUB.rglob('*.html'):
        t = f.read_text(encoding='utf-8')
        if '/#hs-' not in t:
            continue
        own = '/' + f.relative_to(PUB).with_suffix('').as_posix()

        def sub(m):
            p = PAGE.get(m.group(1).replace('.', ''))
            return f'href="{p}"' if p and p != own else m.group(0)
        u, k = RX.subn(sub, t)
        if u != t:
            f.write_text(u, encoding='utf-8'); files += 1
            n += sum(1 for _ in RX.finditer(t)) - sum(1 for _ in RX.finditer(u))
    left = sum(len(RX.findall(f.read_text(encoding='utf-8'))) for f in PUB.rglob('*.html'))
    sys.stderr.write(f'product_links: {n:,} links now go to the product page ({files:,} files); {left:,} links stay in the app (no page)\n')
