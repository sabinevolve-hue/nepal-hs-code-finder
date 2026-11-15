#!/usr/bin/env python3
"""Turn the brief pages written by world_prerender.py (build/briefs/<iso>.html) into PDF trade briefs:
world/reports/<iso>-trade-brief.pdf. One A4 document per economy, rendered with headless Chromium (Playwright).

Run after world_prerender.py:   python3 scripts/world_pdf.py [iso ...]
The briefs load the site's own stylesheet and fonts from world/assets, so they match the site without a network.
"""
import mimetypes, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, WORLD, OUT = ROOT / 'build' / 'briefs', ROOT / 'world', ROOT / 'world' / 'reports'
HOST = 'http://brief.local'


def serve(route):
    path = route.request.url[len(HOST):].split('?')[0]
    f = (SRC / path[len('/_brief/'):]) if path.startswith('/_brief/') else (WORLD / path.lstrip('/'))
    if f.is_file():
        route.fulfill(status=200, body=f.read_bytes(), content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    else:
        route.fulfill(status=404, body=b'')


def main():
    want = {a.lower() for a in sys.argv[1:]}
    pages = sorted(f for f in SRC.glob('*.html') if not want or f.stem in want)
    if not pages:
        sys.exit('no briefs in build/briefs: run scripts/world_prerender.py first')
    OUT.mkdir(parents=True, exist_ok=True)
    if not want:
        for old in OUT.glob('*.pdf'):
            old.unlink()
    total = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(); ctx = browser.new_context()
        ctx.route('**/*', lambda r: serve(r) if r.request.url.startswith(HOST) else r.abort())
        page = ctx.new_page()
        for f in pages:
            page.goto(f'{HOST}/_brief/{f.name}', wait_until='load'); page.evaluate('document.fonts.ready')
            pdf = page.pdf(format='A4', print_background=True, prefer_css_page_size=True,
                           display_header_footer=True, header_template='<span></span>',
                           footer_template='<div style="font-size:7.5px;width:100%;text-align:center;color:#58686B">World Trade Data · world.customsnepal.com · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
            (OUT / f'{f.stem}-trade-brief.pdf').write_bytes(pdf); total += len(pdf)
        browser.close()
    print(f'world_pdf: {len(pages)} briefs, {total / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
