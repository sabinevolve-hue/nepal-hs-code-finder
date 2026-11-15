#!/usr/bin/env python3
"""customsnepal.com and world.customsnepal.com are two separate sites: a link from one to the other opens in a new tab.

Otherwise the visitor's Back button on one site walks them into the other. Used two ways:
  * world_prerender.py calls new_tab(html, MAIN_RX) on every world page (links to customsnepal.com);
  * run as the last build step before check_pages.py, it rewrites public/**/*.html (links to world.customsnepal.com).
Only <a> tags that have no target yet are touched, so running it twice changes nothing.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORLD_RX = re.compile(r'<a\b(?![^>]*\btarget=)([^>]*\bhref="https://world\.customsnepal\.com[^"]*"[^>]*)>')
MAIN_RX = re.compile(r'<a\b(?![^>]*\btarget=)([^>]*\bhref="https://(?:www\.)?customsnepal\.com[^"]*"[^>]*)>')


def new_tab(html, rx):
    return rx.sub(lambda m: f'<a{m[1]} target="_blank" rel="noopener">', html)


if __name__ == '__main__':
    n = files = 0
    for f in (ROOT / 'public').rglob('*.html'):
        t = f.read_text(encoding='utf-8'); u, k = WORLD_RX.subn(lambda m: f'<a{m[1]} target="_blank" rel="noopener">', t)
        if k:
            f.write_text(u, encoding='utf-8'); n += k; files += 1
    sys.stderr.write(f'cross_site: {n:,} links to the world site now open in a new tab ({files:,} files)\n')
