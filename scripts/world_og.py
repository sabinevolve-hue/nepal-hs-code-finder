#!/usr/bin/env python3
"""Share images for world.customsnepal.com: build/og/<name>.html (written by world_prerender.py) -> world/og/<name>.jpg.

One 1200x630 JPEG per country profile, plus world.jpg for every other page. Rendered with headless Chromium
(Playwright) using the site's own stylesheet and fonts, so no network is needed.

Run after world_prerender.py:   python3 scripts/world_og.py [name ...]
"""
import mimetypes, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, WORLD, OUT = ROOT / 'build' / 'og', ROOT / 'world', ROOT / 'world' / 'og'
HOST = 'http://og.local'


def serve(route):
    path = route.request.url[len(HOST):].split('?')[0]
    f = (SRC / path[len('/_og/'):]) if path.startswith('/_og/') else (WORLD / path.lstrip('/'))
    if f.is_file():
        route.fulfill(status=200, body=f.read_bytes(), content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    else:
        route.fulfill(status=404, body=b'')


def main():
    want = {a.lower() for a in sys.argv[1:]}
    pages = sorted(f for f in SRC.glob('*.html') if not want or f.stem in want)
    if not pages:
        sys.exit('no cards in build/og: run scripts/world_prerender.py first')
    OUT.mkdir(parents=True, exist_ok=True)
    if not want:
        for old in OUT.glob('*.jpg'):
            old.unlink()
    total = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(); ctx = browser.new_context(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
        ctx.route('**/*', lambda r: serve(r) if r.request.url.startswith(HOST) else r.abort())
        page = ctx.new_page()
        for f in pages:
            page.goto(f'{HOST}/_og/{f.name}', wait_until='load'); page.evaluate('document.fonts.ready')
            img = page.screenshot(type='jpeg', quality=80, clip={'x': 0, 'y': 0, 'width': 1200, 'height': 630})
            (OUT / f'{f.stem}.jpg').write_bytes(img); total += len(img)
        browser.close()
    print(f'world_og: {len(pages)} images, {total / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
