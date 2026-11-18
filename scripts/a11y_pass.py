#!/usr/bin/env python3
"""Landmarks on the static pages: one <main>, named navigation, and a logo link whose name matches its text.

Most generators open the page body with '</header><div class="wrap">' and close it with '</div><footer'. That leaves
no <main> landmark, so screen-reader users can't jump to the content, and axe reports 'landmark-one-main' and
'region' on every page. This pass turns that wrapper into <main class="wrap" id="main">, names the top menu and the
breadcrumb, and drops the logo's aria-label (its visible text already names it). Pages that don't follow the exact
pattern are left as they are. Running it twice changes nothing.
"""
import pathlib, sys

PUB = pathlib.Path(__file__).resolve().parent.parent / 'public'
OPEN, CLOSE = '</header><div class="wrap">', '</div><footer'
n = 0
for f in PUB.rglob('*.html'):
    s = f.read_text(encoding='utf-8'); t = s
    if s.count(OPEN) == 1 and '<main' not in s and CLOSE in s:
        i = s.rindex(CLOSE)
        t = s[:i] + '</main><footer' + s[i + len(CLOSE):]
        t = t.replace(OPEN, '</header><main class="wrap" id="main">', 1)
    t = t.replace('<nav class="topnav">', '<nav class="topnav" aria-label="Main menu">', 1)
    t = t.replace('<nav class="crumb">', '<nav class="crumb" aria-label="Breadcrumb">', 1)
    t = t.replace('<a class="logo" href="/" aria-label="Customs Nepal — home">', '<a class="logo" href="/">', 1)
    if t != s:
        f.write_text(t, encoding='utf-8'); n += 1
sys.stderr.write(f'a11y_pass: landmarks added on {n:,} pages\n')
