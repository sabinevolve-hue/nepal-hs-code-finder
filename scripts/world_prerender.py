#!/usr/bin/env python3
"""Prerender world.customsnepal.com — one static, indexable HTML document per public route.

Why: the world site is a client-side SPA. Before this, every URL (even made-up ones) returned the same 72 KB shell
with a canonical to the home page, and the real title/content only appeared after ~1.9 MB of JSON had loaded, so
Google indexed only a few hundred of ~6,000 URLs. This script renders each route server-side from world/data/*.json
with the same routing, labels and markup the SPA uses; the SPA then boots on top for interactivity.

Inputs  (source of truth)
  world-src/app.js     SPA source (META placeholder is filled in here)
  world-src/app.css    SPA styles
  world-src/meta.json  shared reference data: official sources, product groups, export guides
  world/data/*.json    hs.json, trade.json, prod.json, nepal.json, nepduty.json

Outputs (committed; the customsnepal-world Vercel project has no build step)
  world/index.html, world/<route>.html (served extension-less via cleanUrls), world/404.html
  world/assets/world.<hash>.css|js (immutable, shared by every page), world/favicon.svg
  world/sitemap.xml (sitemap index) + world/sitemap-*.xml (one per page type, honest <lastmod>)
  world/llms.txt, world/robots.txt are hand-maintained static files (not generated) — served as text/plain
  world/vercel.json    (static-first routing; redirects for codes the data links to but HS 2022 doesn't have)
  scripts/world_lastmod.json  per-URL content hash + date it last changed (drives <lastmod>/dateModified)

Run after editing world-src/* or refreshing world/data/*:   python3 scripts/world_prerender.py
"""
import datetime, hashlib, json, math, pathlib, re, shutil
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, SRC = ROOT / 'world', ROOT / 'world-src'
B = 'https://world.customsnepal.com'
MAIN = 'https://customsnepal.com'
LASTMOD_FILE = ROOT / 'scripts' / 'world_lastmod.json'
TODAY = datetime.date.today().isoformat()

D = W / 'data'
HS = json.load(open(D / 'hs.json', encoding='utf-8'))
TRADE = json.load(open(D / 'trade.json', encoding='utf-8'))
PROD = json.load(open(D / 'prod.json', encoding='utf-8'))
NEP = json.load(open(D / 'nepal.json', encoding='utf-8'))
DUTY = json.load(open(D / 'nepduty.json', encoding='utf-8'))
META = json.load(open(SRC / 'meta.json', encoding='utf-8'))
OFFICIAL, EUROSTAT, PGROUPS, EXGUIDES = META['OFFICIAL'], META['EUROSTAT'], META['PGROUPS'], META['EXGUIDES']

SUBS = HS['subs']
SUB = {s[0]: s for s in SUBS}
HEADINGS = HS['headings']
CH = {c[0]: c for c in HS['chapters']}
SEC = {s[0]: s for s in HS['sections']}
COUNTRIES = TRADE['countries']
CBYISO = {c['iso']: c for c in COUNTRIES}
WORLD = TRADE['world']
MISSING_CODES = set()   # /hs/code/X links to codes not in HS 2022 → redirected in vercel.json

# ---------------------------------------------------------------- helpers (mirror the SPA's JS helpers)
def esc(s):
    return '' if s is None else str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def jsround(x):
    return int(math.floor(x + 0.5))

def num(x):
    """JS Number→string for the duty rates we print (10.0 → '10', 12.5 → '12.5')."""
    return str(int(x)) if float(x) == int(x) else repr(float(x))

def to_fixed(x, f):
    """JavaScript Number.prototype.toFixed: exact binary value, ties rounded up (Python's % rounds half-even)."""
    if x < 0: return '-' + to_fixed(-x, f)
    return str(Decimal(x).quantize(Decimal(1).scaleb(-f), rounding=ROUND_HALF_UP))

def money(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    a = abs(v)
    if a >= 1e12: return '$' + to_fixed(v / 1e12, 2) + 'T'
    if a >= 1e9: return '$' + to_fixed(v / 1e9, 1 if a < 1e10 else 0) + 'B'
    if a >= 1e6: return '$' + to_fixed(v / 1e6, 0) + 'M'
    return '$' + format(jsround(v), ',')

def fmt_usd(n):
    return '$' + format(jsround(n), ',')

def fmt_code(c):
    return c[:4] + '.' + c[4:6]

def clip(s, n):
    s = str(s)
    if len(s) <= n: return s
    c = s[:n]; i = c.rfind(' ')
    return re.sub(r'[;,:\s]+$', '', c[:i] if i > n * 0.6 else c) + '…'

def stop(s):
    """End a clipped phrase as a sentence without doubling punctuation ('…' or '.')."""
    return s if s.endswith(('…', '.')) else s + '.'

def group_slug(label):
    s = label.lower().replace('&', 'and')
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', s))

def chapter_group(ch):
    ch = int(ch)
    return next((g for g in PGROUPS if g[1] <= ch <= g[2]), None)

def iso_meta(iso):
    c = CBYISO.get(iso)
    return (c['name'], c['flag']) if c else (iso, '')

def iso_name(iso):
    return iso_meta(iso)[0]

def hs_desc(code):
    s = SUB.get(code)
    return s[1] if s else HEADINGS.get(code[:4], code)

def pct(w):
    return '%.1f' % max(2, w)

def code_href(code):
    if code not in SUB: MISSING_CODES.add(code)
    return '/hs/code/' + code

ICON = {'search': '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>', 'right': '<path d="M9 6l6 6-6 6"/>',
        'left': '<path d="M15 6l-6 6 6 6"/>', 'info': '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
        'shield': '<path d="M12 2 4 5v6c0 5 3.4 8.3 8 11 4.6-2.7 8-6 8-11V5z"/><path d="m9 12 2 2 4-4"/>',
        'globe': '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20"/>',
        'box': '<path d="M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8"/>', 'chart': '<path d="M3 3v18h18"/><path d="M7 15v-4M12 15V7M17 15v-6"/>'}

def ic(k):
    return f'<svg class="i" viewBox="0 0 24 24">{ICON[k]}</svg>'

# ---------------------------------------------------------------- titles (mirror PT in world-src/app.js)
class T:
    home = staticmethod(lambda: 'World HS Codes & Global Trade Data — Customs Nepal')
    hs = staticmethod(lambda: f'World HS Code Finder — Search {len(SUBS):,} HS 2022 Codes')
    chapter = staticmethod(lambda ch, name: f'HS Chapter {ch}: {clip(name, 60)} — HS Codes List')
    trade = staticmethod(lambda: f'Global Trade Data — World Rankings & {len(COUNTRIES)} Country Profiles')
    group = staticmethod(lambda label: f'Global Trade in {label} — Top Exporters & Importers')
    nepal = staticmethod(lambda: 'Nepal in World Trade — Imports, Exports & Opportunities (2024)')
    nepEx = staticmethod(lambda: 'Nepal Export Explorer — What Nepal Exports & Where (2024)')
    nepMkt = staticmethod(lambda name: f"Nepal's Exports to {name} — Products & Values (2024)")
    guide = staticmethod(lambda g: f"{g['h1']} — Trade Data & Export Steps")

    @staticmethod
    def code(code, desc):
        b = f'HS Code {code} ({fmt_code(code)}) — {clip(desc, 48)}'
        has_trade = bool((PROD.get(code) or {}).get('x'))
        return b + (' — World Trade & Prices' if has_trade else ' — HS 2022 Code') if len(b) <= 58 else b

    @staticmethod
    def country(c):
        return (f"{c['name']} Trade Profile{' ' + str(c['expYear']) if c.get('expYear') else ''} — Exports, Imports"
                f"{', Partners & Products' if c.get('deep') else ' & Trade Balance'}")

# ---------------------------------------------------------------- shared view fragments (mirror the SPA markup)
def row_html(s, current=None):
    np_ = s[3] if len(s) > 3 else None
    return (f'<a class="row" href="{code_href(s[0])}" data-nav{" aria-current=\"page\"" if s[0] == current else ""}>'
            f'<span class="code">{fmt_code(s[0])}</span><span class="d">{esc(s[1])}</span>'
            f'<span class="end">{duty_chip(np_)} {ic("right")}</span></a>')

def duty_chip(np_):
    if not np_ or np_.get('g') is None: return ''
    g = np_['g']
    txt = f'{num(g[0])}–{num(g[1])}%' if isinstance(g, list) else ('Free' if g == 0 else num(g) + '%')
    return f'<span class="chip dutychip">NP {txt}</span>'

def leaderboard(lst, color):
    mx = max([x[3] for x in lst] + [1])
    return '<div class="bars">' + ''.join(
        f'<a class="lbrow" href="/trade/{x[0].lower()}" data-nav><span class="rk">{i + 1}</span>'
        f'<span class="lb">{x[2]} {esc(x[1])}</span><span class="tr"><span class="fi" style="width:{pct(x[3] / mx * 100)}%;background:{color}"></span></span>'
        f'<span class="vl">{money(x[3])}</span></a>' for i, x in enumerate(lst)) + '</div>'

def bars(items, mx, color='var(--accent)'):
    return '<div class="bars">' + ''.join(
        f'<div class="barrow"><span class="lb">{esc(it[-2])}</span><span class="tr"><span class="fi" style="width:{pct(it[-1] / mx * 100)}%;background:{color}"></span></span>'
        f'<span class="vl">{money(it[-1])}</span></div>' for it in items) + '</div>'

def trend_svg(trend):
    pts = [r for r in trend if r[1] is not None or r[2] is not None]
    if len(pts) < 2: return ''
    Wd, H, pad = 600, 150, 4
    minY, maxY = pts[0][0], pts[-1][0]
    vals = [v for r in pts for v in (r[1], r[2]) if v is not None]
    mx = max(vals) * 1.05
    X = lambda y: pad + (y - minY) / (maxY - minY) * (Wd - 2 * pad)
    Y = lambda v: H - pad - (v / mx) * (H - 2 * pad)
    def line(idx):
        p = [r for r in pts if r[idx] is not None]
        return ' '.join(('L' if i else 'M') + f'{X(r[0]):.1f} {Y(r[idx]):.1f}' for i, r in enumerate(p))
    def area(idx):
        p = [r for r in pts if r[idx] is not None]
        if not p: return ''
        return f'M{X(p[0][0]):.1f} {H} L' + ' L'.join(f'{X(r[0]):.1f} {Y(r[idx]):.1f}' for r in p) + f' L{X(p[-1][0]):.1f} {H} Z'
    return (f'<svg class="trend" viewBox="0 0 {Wd} {H}" preserveAspectRatio="none" role="img" aria-label="Exports and imports trend">'
            f'<path d="{area(1)}" fill="var(--exp)" opacity=".10"/><path d="{line(1)}" fill="none" stroke="var(--exp)" stroke-width="2.5"/>'
            f'<path d="{line(2)}" fill="none" stroke="var(--imp)" stroke-width="2.5" stroke-dasharray="1"/></svg>'
            f'<div class="lgnd"><span><i style="background:var(--exp)"></i>Exports</span><span><i style="background:var(--imp)"></i>Imports</span>'
            f'<span style="color:var(--muted)">{minY}–{maxY}</span></div>')

def src_box(label, body, year=''):
    yr = f'<span style="margin-left:auto;font-weight:600;color:var(--muted)">{year}</span>' if year else ''
    return f'<div class="src"><div class="src-h">{ic("shield")}<span>{label}</span>{yr}</div>{body}</div>'

def back(href, label):
    return f'<a class="back" href="{href}" data-nav>{ic("left")}{label}</a>'

def card(href, fl, inner):
    return f'<a class="nepalcard" href="{href}" data-nav><span class="fl">{fl}</span><span>{inner} {ic("right")}</span></a>'

def main(inner):
    return f'<main><div class="wrap">{inner}</div></main>'

# ---------------------------------------------------------------- views
def v_home():
    return (f'''<section class="hero"><div class="wrap"><h1>The world's HS codes and trade, in one place.</h1>
<p>Search the international Harmonized System — the classification behind every customs tariff on earth — and explore the import/export profiles of the largest economies.</p>
<div class="chips"><span>{len(SUBS):,} six-digit HS codes</span><span>{len(HS["chapters"])} chapters</span><span>{len(COUNTRIES)} economies</span><span>Official sources</span></div></div></section>'''
            + main(f'''<div class="grid2">
<a class="bigcard" href="/hs" data-nav><div class="ic">{ic("box")}</div><h3>World HS Code Finder</h3><p>Look up any product's 6-digit Harmonized System code and see how Nepal taxes it. The same code works in 200+ countries.</p><span class="go">Find a code {ic("right")}</span></a>
<a class="bigcard" href="/trade" data-nav><div class="ic">{ic("globe")}</div><h3>Global Trade Data</h3><p>World rankings and a trade profile for every one of {WORLD["count"]} economies — exports, imports, partners and product mix.</p><span class="go">Explore trade {ic("right")}</span></a>
</div><div class="statrow">
<div class="s"><b>{money(WORLD["totalExp"])}</b><span>World merchandise trade ({WORLD["year"]})</span></div>
<div class="s"><b>{WORLD["count"]}</b><span>Economies profiled</span></div>
<div class="s"><b>{len(SUBS):,}</b><span>HS codes linked to trade</span></div></div>'''))

def v_hs():
    secs = ''.join(
        f'<a class="sec" href="/hs/chapter/{s[2]:02d}" data-nav><span class="n">Section {s[0]}</span><span class="t">{esc(s[1])}</span>'
        f'<span class="c">Ch {s[2]}–{s[3]} · {sum(1 for x in SUBS if s[2] <= int(x[0][:2]) <= s[3])} codes</span></a>' for s in HS['sections'])
    chs = ''.join(f'<a class="row" href="/hs/chapter/{c[0]}" data-nav><span class="code">Ch {c[0]}</span><span class="d">{esc(c[1])}</span>'
                  f'<span class="end">{ic("right")}</span></a>' for c in HS['chapters'])
    return main(f'''<div class="ph"><h1 class="h2">World HS Code Finder</h1><p>Search {len(SUBS):,} international six-digit codes by product or number, or browse by section. {HS["edition"]} nomenclature.</p></div>
<form class="sbox" action="/hs" method="get" role="search">{ic("search")}<input id="q" name="q" type="search" placeholder="e.g. coffee, lithium battery, 8471, 0901…" autocomplete="off" aria-label="Search HS codes"></form>
<div id="res"></div><div id="browse"><h3 class="h">Browse by section</h3><div class="secs">{secs}</div>
<h3 class="h">All {len(HS["chapters"])} chapters</h3>{chs}</div>''')

def v_chapter(ch):
    cn = CH[ch]; sec = SEC.get(cn[2])
    rows = [s for s in SUBS if s[0].startswith(ch)]
    by = {}
    for s in rows: by.setdefault(s[2], []).append(s)
    body = ''.join(f'<h3 class="h">{h[:2]}.{h[2:]} — {esc(HEADINGS.get(h, ""))}</h3>' + ''.join(row_html(s) for s in by[h]) for h in sorted(by))
    return main(back('/hs', 'HS finder') + f'''<div class="ph"><p style="margin:0;color:var(--muted);font-size:.85rem">Section {cn[2]} · Chapter {ch}</p><h1 class="h2">{esc(cn[1])}</h1><p>{len(rows)} six-digit codes{" · " + esc(sec[1]) if sec else ""}.</p></div>{body}''')

def nepal_prod(code):
    z = NEP.get(code)
    if not z or not (z.get('im') or z.get('ex')): return ''
    p = PROD.get(code); parts = []
    if z.get('im'):
        src = ', '.join(esc(iso_name(x[0])) for x in (z.get('ims') or [])[:3])
        pr = ''
        if z.get('iu') and p and p.get('u'):
            d = jsround((z['iu'] / p['u'] - 1) * 100)
            rel = (f'<b style="color:var(--hi)">{d}% above</b>' if d > 8 else f'<b style="color:var(--free)">{abs(d)}% below</b>' if d < -8 else 'about')
            pr = f' at <b>${z["iu"]}/kg</b> — {rel} the world average (${p["u"]}/kg)'
        parts.append(f'imports <b>{money(z["im"] * 1e6)}</b>{f" (mainly from {src})" if src else ""}{pr}')
    if z.get('ex'):
        dst = ', '.join(esc(iso_name(x[0])) for x in (z.get('exs') or [])[:3])
        parts.append(f'exports <b>{money(z["ex"] * 1e6)}</b>{f" (to {dst})" if dst else ""}')
    return (f'<div class="outcome" style="margin-top:var(--s4)"><span style="font-size:1.3rem">🇳🇵</span><div><b>Nepal\'s trade in this product (2024):</b> '
            f'{"; ".join(parts)}. <a href="{MAIN}/?q={code}" target="_blank" rel="noopener">Nepal duty &amp; taxes ↗</a></div></div>')

def prod_block(code):
    p = PROD.get(code)
    if not p or not p.get('x'): return nepal_prod(code)
    mk = lambda a: [[iso, *iso_meta(iso), v * 1e6] for iso, v in a]
    ex, im = mk(p['x']), mk(p.get('m') or [])
    price = f' World average price: <b style="color:var(--fg)">${p["u"]}/kg</b>.' if p.get('u') else ''
    imp = f'<p class="fine" style="margin:14px 0 6px"><b style="color:var(--imp)">Top importers</b></p>{leaderboard(im, "var(--imp)")}' if im else ''
    return (f'<h3 class="h">Who trades this worldwide</h3><p class="fine" style="margin:0 0 10px">World trade in HS {fmt_code(code)} was '
            f'<b style="color:var(--fg)">{money(p["w"] * 1e6)}</b> in 2024.{price} Leading exporters and importers:</p>'
            f'<p class="fine" style="margin:0 0 6px"><b style="color:var(--exp)">Top exporters</b></p>{leaderboard(ex, "var(--exp)")}{imp}{nepal_prod(code)}'
            + src_box('Source', '<p><b>BACI</b> (CEPII) — bilateral trade at HS 6-digit, reconciled from <b>UN Comtrade</b> across ~200 countries; unit values = value ÷ quantity. Current US$.</p>', '2024'))

def landed_block(code):
    d = DUTY.get(code)
    if not d or d[0] is None: return ''
    gen = d[0]; saarc = gen if d[1] is None else d[1]
    CIF, V = 1000, 0.13
    landed = lambda r: CIF * (1 + r / 100) * (1 + V)
    lg, ls = landed(gen), landed(saarc)
    save, save_pct = jsround(lg - ls), jsround((lg - ls) / lg * 100)
    dl = lambda r: 'Free' if r == 0 else num(r) + '%'
    if saarc < gen:
        verdict = (f'<div class="outcome" style="margin-top:var(--s3)"><span style="font-size:1.3rem">🇳🇵</span><div>Sourcing from <b>India or another SAARC country</b> lands this '
                   f'<b style="color:var(--free)">{fmt_usd(save)} cheaper per $1,000</b> ({save_pct}% lower) than from China or the rest of the world — that gap is the SAFTA duty preference.</div></div>')
    elif gen == 0:
        verdict = f'<div class="outcome" style="margin-top:var(--s3)">{ic("info")}<div>This code is <b style="color:var(--free)">duty-free</b> into Nepal whatever the origin — you pay only the 13% VAT.</div></div>'
    else:
        verdict = f'<div class="outcome" style="margin-top:var(--s3)">{ic("info")}<div>Nepal charges the same <b>{dl(gen)}</b> customs duty on this code regardless of origin — there\'s no SAARC/SAFTA preference to capture here.</div></div>'
    return (f'''<h3 class="h">Import into Nepal — landed cost by origin</h3><p class="fine" style="margin:0 0 10px">On a <b style="color:var(--fg)">$1,000</b> shipment (CIF value), Nepal customs duty + 13% VAT comes to:</p>
<table class="bk"><tbody><tr><td>From India / a SAARC member <span class="fine">· {dl(saarc)} duty (SAFTA)</span></td><td>{fmt_usd(ls)}</td></tr>
<tr><td>From China / rest of world <span class="fine">· {dl(gen)} duty (general)</span></td><td>{fmt_usd(lg)}</td></tr></tbody></table>{verdict}
<p class="fine" style="margin-top:10px">Customs duty and 13% VAT only — excise duty, vehicle taxes and any product-specific levies are <b>not</b> included. <a href="{MAIN}/?q={code}" target="_blank" rel="noopener">Run the full Nepal calculator ↗</a> for the exact all-in figure.</p>''')

def v_code(code):
    s = SUB[code]; ch, head = code[:2], code[:4]
    cn = CH.get(ch, [ch, '', '']); sec = SEC.get(cn[2], ['', '', ''])
    np_ = s[3] if len(s) > 3 else None
    nepal = ''
    if np_ and np_.get('g') is not None:
        g = np_['g']; txt = f'{num(g[0])}–{num(g[1])}%' if isinstance(g, list) else ('Free' if g == 0 else num(g) + '%')
        nepal = (f'<div class="outcome">{ic("info")}<div>Nepal applies a general customs duty of <b>{txt}</b> on this code ({np_["n"]} national line{"s" if np_["n"] > 1 else ""}), '
                 f'plus excise/VAT where applicable. <a href="{MAIN}/?q={code}" target="_blank" rel="noopener">See full Nepal duty &amp; taxes ↗</a></div></div>')
    elif np_:
        nepal = f'<div class="outcome">{ic("info")}<div>Nepal lists this code ({np_["n"]} line{"s" if np_["n"] > 1 else ""}). <a href="{MAIN}/?q={code}" target="_blank" rel="noopener">See Nepal duty &amp; taxes ↗</a></div></div>'
    grp = chapter_group(ch)
    gcard = card(f'/trade/product/{group_slug(grp[0])}', ic('globe'), f'<b>Global trade in {esc(grp[0])}</b> — see the world\'s top exporters &amp; importers') if grp else ''
    sib = ''.join(row_html(x, current=code) for x in SUBS if x[0].startswith(head))
    return main(back(f'/hs/chapter/{ch}', f'Chapter {ch}') + f'''<h1 class="dcode">{fmt_code(code)}</h1><p class="dtitle">{esc(s[1])}</p>
<p class="crumb">Section {cn[2]} · <b>{esc(sec[1])}</b></p>{nepal}
<table class="bk"><tbody><tr><td>Six-digit HS code</td><td>{fmt_code(code)} <span class="fine">({code})</span></td></tr><tr><td>Heading</td><td>{head}</td></tr>
<tr><td>Chapter</td><td>{ch} — {esc(cn[1])}</td></tr><tr><td>Section</td><td>{cn[2]}</td></tr></tbody></table>
<p class="crumb" style="margin-top:14px"><b>Heading {head[:2]}.{head[2:]}:</b> {esc(HEADINGS.get(head, ""))}</p>
{prod_block(code)}{landed_block(code)}'''
        + src_box('International standard', f'<p>This is the global 6-digit Harmonized System code ({HS["edition"]}), identical across 200+ countries. Each country adds its own 8–10 digit extension and duty rates. <a href="https://www.wcoomd.org/en/topics/nomenclature/overview.aspx" target="_blank" rel="noopener">About the HS ↗</a></p>')
        + f'{gcard}<h3 class="h">Other codes in heading {head[:2]}.{head[2:]}</h3>{sib}')

def country_rows():
    return ''.join(f'<a class="row" href="/trade/{c["iso"].lower()}" data-nav><span class="code" style="color:var(--muted);min-width:30px;text-align:right">#{c.get("rankExp") or "–"}</span>'
                   f'<span class="d">{c["flag"]} {esc(c["name"])}</span><span class="end"><b class="ex">{money(c["exp"])}</b> {ic("right")}</span></a>'
                   for c in COUNTRIES if c.get('exp') is not None)

def pgroup_grid(current=None):
    return '<div class="secs">' + ''.join(
        f'<a class="sec" href="/trade/product/{group_slug(x[0])}" data-nav{" aria-current=\"page\"" if group_slug(x[0]) == current else ""}>'
        f'<span class="t">{esc(x[0])}</span><span class="c">HS {x[1]}–{x[2]}</span></a>' for x in PGROUPS) + '</div>'

def v_trade():
    np_ = CBYISO.get('NPL'); rmax = max([r[1] for r in WORLD['regions']] + [1])
    offs = sorted([(k, CBYISO[k]) for k in OFFICIAL if k != 'NPL' and k in CBYISO], key=lambda x: -(x[1].get('exp') or 0))[:12]
    osrc = ''.join(f'<a class="osrc-i" href="{OFFICIAL[k][1]}" target="_blank" rel="noopener">{c["flag"]} <span>{esc(OFFICIAL[k][0])}</span>{ic("right")}</a>' for k, c in offs)
    osrc += f'<a class="osrc-i" href="{EUROSTAT[1]}" target="_blank" rel="noopener">🇪🇺 <span>{esc(EUROSTAT[0])}</span>{ic("right")}</a>'
    ncard = card('/nepal', np_['flag'], '<b>Nepal in the world</b> — real imports, exports &amp; sourcing opportunities by product') if np_ else ''
    return main(f'''<div class="ph"><h1 class="h2">Global trade</h1><p>World merchandise trade reached <b>{money(WORLD["totalExp"])}</b> in {WORLD["year"]}, across {WORLD["count"]} economies. Explore the rankings below, or open any country.</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{money(WORLD["totalExp"])}</b><span>World exports ({WORLD["year"]})</span></div>
<div class="s"><b class="im">{money(WORLD["totalImp"])}</b><span>World imports ({WORLD["year"]})</span></div><div class="s"><b>{WORLD["count"]}</b><span>Economies</span></div></div>
<div class="card" style="margin-top:var(--s4)"><b style="font-size:.9rem">World trade over time</b>{trend_svg(WORLD["trend"])}</div>{ncard}
<div class="sub2" style="margin-top:var(--s5)"><button class="on" type="button">Top exporters</button><button type="button">Top importers</button></div>
{leaderboard(WORLD["topExp"], "var(--exp)")}<h3 class="h">By region</h3>{bars([[r[0], r[1]] for r in WORLD["regions"]], rmax, "var(--exp)")}
<h3 class="h">Trade by product</h3><p class="fine" style="margin:0 0 10px">Who leads world trade in each product family — and the HS codes behind it:</p>{pgroup_grid()}
<h3 class="h">All economies</h3><div class="sbox">{ic("search")}<input id="cq" type="search" placeholder="Find a country…" autocomplete="off" aria-label="Find a country"></div><div id="clist">{country_rows()}</div>
<h3 class="h">Freshest 2025 data — official national sources</h3><p class="fine" style="margin:0 0 10px">The figures above are the World Bank's comparable cross-country series (to 2023). For the latest <b>2025</b> import/export data, each economy's own customs or statistics office is the authoritative source:</p>
<div class="osrc">{osrc}</div>''' + src_box('Official sources', f'<p>World and country totals from the <b>World Bank</b> (merchandise trade, current US$); partners and product mix from <b>World Bank WITS</b>, sourced from <b>UN Comtrade</b>. Rankings cover {WORLD["count"]} reporting economies.</p>').replace('<div class="src">', '<div class="src" style="margin-top:var(--s4)">', 1))

def country_extras(c):
    """Year-by-year table + nearby economies in the same region (mirrors countryExtras() in world-src/app.js)."""
    yrs = [r for r in (c.get('trend') or []) if r[1] is not None or r[2] is not None][-6:][::-1]
    tbl = ('<h3 class="h">Trade by year</h3><table class="bk"><tbody><tr><td><b>Year</b></td><td>Exports · Imports</td></tr>'
           + ''.join(f'<tr><td>{r[0]}</td><td><span class="ex">{money(r[1])}</span> · <span class="im">{money(r[2])}</span></td></tr>' for r in yrs)
           + '</tbody></table>') if yrs else ''
    peers = sorted([x for x in COUNTRIES if x['iso'] != c['iso'] and x.get('region') == c.get('region') and x.get('exp') is not None],
                   key=lambda x: abs(x['exp'] - (c.get('exp') or 0)))[:8] if c.get('region') else []
    pl = (f'<h3 class="h">Other economies in {esc(c["region"])}</h3>' + ''.join(
        f'<a class="row" href="/trade/{x["iso"].lower()}" data-nav><span class="d">{x["flag"]} {esc(x["name"])}</span><span class="end"><b class="ex">{money(x["exp"])}</b> {ic("right")}</span></a>'
        for x in peers)) if peers else ''
    return tbl + pl

def v_country(c):
    deep = bool(c.get('deep')); bal = (c.get('exp') or 0) - (c.get('imp') or 0)
    if deep:
        parts, prods = c.get('expPartners') or [], c.get('expProducts') or []
        pmax = max([p[2] for p in parts] + [1]); rmax = max([p[1] for p in prods] + [1])
        detail = (f'<div class="sub2"><button class="on" type="button">Exports</button><button type="button">Imports</button></div>'
                  f'<h3 class="h">Top export destinations <small style="font-weight:600;color:var(--muted)">({c.get("pYear")})</small></h3>'
                  + (bars([[p[1], p[2]] for p in parts], pmax, 'var(--exp)') if parts else '<p class="fine">No partner data.</p>')
                  + '<h3 class="h">What it exports</h3>' + (bars([[p[0], p[1]] for p in prods], rmax, 'var(--exp)') if prods else '<p class="fine">No product data.</p>'))
    else:
        detail = f'<div class="outcome" style="margin-top:var(--s4)">{ic("info")}<div>Partner and product breakdowns are live for the ~30 largest traders and Nepal, and rolling out to more economies. The totals and trend above are from the World Bank.</div></div>'
    off = ''
    if c['iso'] in OFFICIAL:
        o = OFFICIAL[c['iso']]
        off = (f'<p style="margin-top:8px"><b style="color:var(--fg-2)">Freshest 2025 data →</b> <a href="{o[1]}" target="_blank" rel="noopener">{esc(o[0])} ↗</a>'
               + (f' · <a href="{EUROSTAT[1]}" target="_blank" rel="noopener">Eurostat ↗</a>' if c.get('region') == 'Europe & Central Asia' else '') + '</p>')
    elif c.get('region') == 'Europe & Central Asia':
        off = f'<p style="margin-top:8px"><b style="color:var(--fg-2)">Freshest 2025 data →</b> <a href="{EUROSTAT[1]}" target="_blank" rel="noopener">{esc(EUROSTAT[0])} ↗</a></p>'
    srcs = src_box('Official sources', f'<p>Trade totals from the <b>World Bank</b> (merchandise trade, current US$){"; partners and product mix from <b>World Bank WITS</b>, sourced from <b>UN Comtrade</b>" if deep else ""}. '
                   f'<a href="https://wits.worldbank.org/CountryProfile/en/{c["iso"]}" target="_blank" rel="noopener">World Bank profile ↗</a></p>{off}', c.get('pYear') if deep else '')
    sign = '+' if bal >= 0 else '−'
    return main(back('/trade', 'Global trade') + f'''<div class="ph"><h1 class="h2">{c["flag"]} {esc(c["name"])}</h1><p>{esc(c["region"]) + " · " if c.get("region") else ""}World rank <b>#{c.get("rankExp") or "–"}</b> exporter, <b>#{c.get("rankImp") or "–"}</b> importer, of {WORLD["count"]} economies.</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{money(c.get("exp"))}</b><span>Exports ({c.get("expYear")})</span></div>
<div class="s"><b class="im">{money(c.get("imp"))}</b><span>Imports ({c.get("impYear")})</span></div>
<div class="s"><b style="color:{"var(--free)" if bal >= 0 else "var(--hi)"}">{sign}{money(abs(bal))[1:]}</b><span>Trade balance</span></div></div>
<div class="card" style="margin-top:var(--s4)"><b style="font-size:.9rem">Exports vs imports</b>{trend_svg(c.get("trend") or [])}</div>{detail}{country_extras(c)}{srcs}'''
                + ('<p class="fine">Mirror-statistics note: a country&#39;s reported exports to a partner may differ from that partner&#39;s reported imports. Product groups follow HS chapter ranges.</p>' if deep else ''))

def product_traders(label, flow):
    key = 'expProducts' if flow == 'exp' else 'impProducts'; out = []
    for c in COUNTRIES:
        e = next((p for p in (c.get(key) or []) if p[0] == label), None)
        if e and e[1] > 0: out.append([c['iso'], c['name'], c['flag'], e[1]])
    return sorted(out, key=lambda x: -x[3])

def v_group(g):
    label, slug = g[0], group_slug(g[0])
    yr = next((c.get('pYear') for c in COUNTRIES if c.get('deep')), None)
    lb = product_traders(label, 'exp')[:15]
    n = sum(1 for s in SUBS if g[1] <= int(s[0][:2]) <= g[2])
    return main(back('/trade', 'Global trade') + f'''<div class="ph"><h1 class="h2">{esc(label)}</h1><p>Who trades this worldwide — HS chapters {g[1]}–{g[2]}. Leading exporters and importers among the major economies{f" ({yr})" if yr else ""}.</p></div>
<div class="sub2"><button class="on" type="button">Top exporters</button><button type="button">Top importers</button></div>
<h3 class="h">Leading exporters of {esc(label.lower())}</h3>{leaderboard(lb, "var(--exp)") if lb else '<p class="fine">No data for this group.</p>'}'''
                + card(f'/hs/chapter/{g[1]:02d}', ic('box'), f'<b>Find the exact HS codes</b> — browse the {n} six-digit codes in chapters {g[1]}–{g[2]}')
                + f'<h3 class="h">All product groups</h3>{pgroup_grid(slug)}'
                + src_box('Official sources', '<p>Rankings computed from <b>World Bank WITS</b> product data (sourced from <b>UN Comtrade</b>) across the major trading economies — each country\'s merchandise exports in this HS group. Smaller economies are not yet included, so treat it as "leading major-economy traders".</p>', yr or ''))

def nep_row(code, val, extra='', cls=''):
    return (f'<a class="row" href="{code_href(code)}" data-nav><span class="code">{fmt_code(code)}</span><span class="d">{esc(hs_desc(code))}'
            f'{f"<small style=\"display:block;color:var(--muted)\">{extra}</small>" if extra else ""}</span>'
            f'<span class="end"><b{f" class=\"{cls}\"" if cls else ""}>{money(val * 1e6)}</b> {ic("right")}</span></a>')

def ex_row(code, val, extra=''):
    return nep_row(code, val, extra, 'ex')

NEPSRC = 'Nepal\'s bilateral trade from <b>BACI</b> (CEPII, reconciled from UN Comtrade).'

def v_nepal():
    Tt = NEP.get('_t') or {'im': 0, 'ex': 0}; bal = Tt['ex'] - Tt['im']
    over = []
    for code, val in NEP.get('_im') or []:
        z, p = NEP.get(code), PROD.get(code)
        if z and z.get('iu') and p and p.get('u') and z['iu'] > p['u'] * 1.2 and val >= 1:
            over.append([code, val, jsround((z['iu'] / p['u'] - 1) * 100), z['iu'], p['u']])
    over.sort(key=lambda a: -(a[1] * a[2]))
    opn = []
    for code, val in NEP.get('_ex') or []:
        p = PROD.get(code)
        if p and p.get('w'):
            sh = val / p['w'] * 100
            if sh < 20: opn.append([code, val, p['w'], sh])
    opn.sort(key=lambda a: -a[2])
    share = lambda sh: '<1' if sh < 1 else str(jsround(sh))
    return main(back('/trade', 'Global trade') + f'''<div class="ph"><h1 class="h2">🇳🇵 Nepal in world trade</h1><p>Nepal's real merchandise trade by product (BACI 2024) — and where the data points to openings.</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="im">{money(Tt["im"] * 1e6)}</b><span>Imports (2024)</span></div>
<div class="s"><b class="ex">{money(Tt["ex"] * 1e6)}</b><span>Exports (2024)</span></div>
<div class="s"><b style="color:var(--hi)">−{money(abs(bal) * 1e6)[1:]}</b><span>Trade deficit</span></div></div>'''
                + card('/nepal/exports', '📦', '<b>Nepal Export Explorer</b> — what Nepal sells to each country, by product, with world-price benchmarks and export guides')
                + '<h3 class="h">Sourcing watch — imports Nepal may overpay for</h3><p class="fine" style="margin:0 0 8px">Products where Nepal\'s import price sits well above the world average — worth checking a cheaper origin.</p>'
                + (''.join(nep_row(c, v, f'Nepal ${iu}/kg vs ${u}/kg world · {d}% higher') for c, v, d, iu, u in over[:12]) or '<p class="fine">—</p>')
                + '<h3 class="h">Export openings — big world demand, small Nepal share</h3><p class="fine" style="margin:0 0 8px">Products Nepal already exports, where world import demand dwarfs Nepal\'s current sales.</p>'
                + (''.join(nep_row(c, v, f'World imports {money(w * 1e6)} · Nepal {share(sh)}%') for c, v, w, sh in opn[:12]) or '<p class="fine">—</p>')
                + '<h3 class="h">Nepal\'s top imports</h3>' + ''.join(nep_row(c, v) for c, v in (NEP.get('_im') or [])[:10])
                + '<h3 class="h">Nepal\'s top exports</h3>' + ''.join(nep_row(c, v) for c, v in (NEP.get('_ex') or [])[:10])
                + src_box('Source', f'<p>{NEPSRC} "Overpay" compares Nepal\'s import unit value to the world average — a signal to investigate, not proof (grade/quality and freight differ). For duty on any line, see <a href="{MAIN}/" target="_blank" rel="noopener">customsnepal.com ↗</a>.</p>', '2024'))

def js_key_order(d):
    """Iterate a JSON object in JavaScript's for-in order: canonical array-index keys ('580810') ascending first,
    then the remaining keys ('090240', '_t') in insertion order — so ties sort exactly as in the SPA."""
    idx = [k for k in d if k.isdigit() and (k == '0' or k[0] != '0') and int(k) < 2**32 - 1]
    ids = set(idx)
    return sorted(idx, key=int) + [k for k in d if k not in ids]

def nep_exports():
    cc, cp = {}, {}
    for k in js_key_order(NEP):
        z = NEP[k]
        if k.startswith('_') or not z.get('exs'): continue
        for iso, val in z['exs']:
            if not val > 0: continue
            cc[iso] = cc.get(iso, 0) + val; cp.setdefault(iso, []).append([k, val])
    for i in cp: cp[i].sort(key=lambda a: -a[1])
    order = sorted(cc, key=lambda i: -cc[i])
    return {'cc': cc, 'cp': cp, 'order': order, 'tot': sum(cc.values()),
            'nprod': sum(1 for k, z in NEP.items() if not k.startswith('_') and (z.get('ex') or 0) > 0)}
NEPEXP = nep_exports()

def exs_text(code):
    z = NEP.get(code)
    if not z or not z.get('exs'): return ''
    d = [esc(iso_name(x[0])) for x in z['exs'] if x[1] > 0][:3]
    return ('→ ' + ', '.join(d)) if d else ''

def ex_dest_rows(dests):
    X = NEPEXP; mx = max([X['cc'][i] for i in dests] + [1])
    return '<div class="bars">' + ''.join(
        f'<a class="lbrow" href="/nepal/exports/{i.lower()}" data-nav><span class="rk">{n + 1}</span><span class="lb">{iso_meta(i)[1]} {esc(iso_meta(i)[0])}</span>'
        f'<span class="tr"><span class="fi" style="width:{pct(X["cc"][i] / mx * 100)}%;background:var(--exp)"></span></span><span class="vl">{money(X["cc"][i] * 1e6)}</span></a>'
        for n, i in enumerate(dests)) + '</div>'

def v_nep_exports():
    X, Tt = NEPEXP, NEP.get('_t') or {'ex': 0}
    dests = [i for i in X['order'] if X['cc'][i] > 0]
    india = jsround((X['cc'].get('IND', 0)) / (Tt['ex'] or X['tot']) * 100)
    opn = []
    for code, val in NEP.get('_ex') or []:
        p = PROD.get(code)
        if p and p.get('w'):
            sh = val / p['w'] * 100
            if sh < 20: opn.append([code, val, p['w'], sh])
    opn.sort(key=lambda a: -a[2])
    guides = ''.join(f'<a class="sec" href="/nepal/exports/guide/{s}" data-nav><span class="t">{g["fl"]} {esc(g["name"])}</span><span class="c">Trade data + how to export</span></a>' for s, g in EXGUIDES.items())
    return main(back('/nepal', 'Nepal in world trade') + f'''<div class="ph"><h1 class="h2">🇳🇵 Nepal Export Explorer</h1><p>What Nepal sells to the world — by destination and by product, with world-price benchmarks (BACI 2024).</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{money(Tt["ex"] * 1e6)}</b><span>Total exports (2024)</span></div>
<div class="s"><b>{len(dests)}</b><span>Destination markets</span></div><div class="s"><b>{X["nprod"]}</b><span>Products exported</span></div></div>
<div class="outcome" style="margin-top:var(--s4)">{ic("info")}<div><b>{india}% of Nepal's exports go to India</b> — and a large part of that is refined soybean &amp; palm oil re-exported after processing (a duty-driven flow, not domestic production). Nepal's real manufactured and agri exports — carpets, cardamom, pashmina, tea, felt — are spread across the US, the EU and beyond.</div></div>
<h3 class="h">Explore by market</h3><p class="fine" style="margin:0 0 8px">Nepal's biggest export destinations — open one to see every product Nepal ships there.</p>{ex_dest_rows(dests[:15])}
<h3 class="h">Explore by product</h3><p class="fine" style="margin:0 0 8px">Nepal's top exports — open one for who buys it worldwide and the price Nepal gets.</p>
{"".join(ex_row(c, v, exs_text(c)) for c, v in [d for d in (NEP.get("_ex") or []) if d[1] > 0][:15])}
<h3 class="h">Export guides</h3><div class="secs">{guides}</div>
<h3 class="h">Export openings — big world demand, small Nepal share</h3><p class="fine" style="margin:0 0 8px">Products Nepal already exports, where world import demand dwarfs Nepal's current sales.</p>
{"".join(ex_row(o[0], o[1], f"World imports {money(o[2] * 1e6)} · Nepal {'<1' if o[3] < 1 else jsround(o[3])}%") for o in opn[:10]) or '<p class="fine">—</p>'}'''
                + src_box('Source', '<p>Nepal\'s exports by product and partner from <b>BACI</b> (CEPII, reconciled from UN Comtrade). Destination totals cover the major flows (top partners per product) — about 87% of the headline total; the rest is a long tail of small shipments. For the official, 8-digit, fiscal-year figures see the <b>Department of Customs</b> and <b>TEPC</b>.</p>', '2024')
                # the rest of the destinations (the SPA lists the top 15) — static links so every market page is discoverable
                + (f'<h3 class="h">All {len(dests)} destination markets</h3><div class="secs">' + ''.join(
                    f'<a class="sec" href="/nepal/exports/{i.lower()}" data-nav><span class="t">{iso_meta(i)[1]} {esc(iso_meta(i)[0])}</span><span class="c">{money(X["cc"][i] * 1e6)}</span></a>' for i in dests) + '</div>'))

def v_nep_market(iso):
    X = NEPEXP; name, flag = iso_meta(iso)
    prods = [x for x in X['cp'].get(iso, []) if x[1] > 0]
    tot = X['cc'].get(iso, 0); share = jsround(tot / ((NEP.get('_t') or {}).get('ex') or X['tot']) * 100)
    rows = ''.join(ex_row(c, v, f'world price ${PROD[c]["u"]}/kg' if PROD.get(c, {}).get('u') else '') for c, v in prods)
    return main(back('/nepal/exports', 'Export Explorer') + f'''<div class="ph"><h1 class="h2">{flag} Nepal → {esc(name)}</h1><p>Every product Nepal exports to {esc(name)} (BACI 2024), largest first.</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{money(tot * 1e6)}</b><span>Nepal's exports here</span></div>
<div class="s"><b>{len(prods)}</b><span>Products</span></div><div class="s"><b>{"<1" if share < 1 else share}%</b><span>of Nepal's exports</span></div></div>
<h3 class="h">Products Nepal exports to {esc(name)}</h3>{rows}'''
                + card(f'/trade/{iso.lower()}', flag, f'<b>{esc(name)}\'s full trade profile</b> — its total exports, imports &amp; top partners')
                + src_box('Source', f'<p>From <b>BACI</b> (CEPII, reconciled UN Comtrade). Values are Nepal→{esc(name)} merchandise exports at HS-6, current US$. For official 8-digit, fiscal-year figures, see Nepal\'s Department of Customs and TEPC; for Nepal duty and taxes see <a href="{MAIN}/" target="_blank" rel="noopener">customsnepal.com ↗</a>.</p>', '2024'))

def v_guide(slug):
    g = EXGUIDES[slug]; hs = g['hs']; z = NEP.get(hs) or {}; p = PROD.get(hs) or {}
    dests = [x for x in (z.get('exs') or []) if x[1] > 0][:5]
    dbars = ('<div class="bars">' + ''.join(
        f'<a class="lbrow" href="/nepal/exports/{x[0].lower()}" data-nav><span class="rk">{i + 1}</span><span class="lb">{iso_meta(x[0])[1]} {esc(iso_meta(x[0])[0])}</span>'
        f'<span class="tr"><span class="fi" style="width:{pct(x[1] / max(dests[0][1], 1) * 100)}%;background:var(--exp)"></span></span><span class="vl">{money(x[1] * 1e6)}</span></a>'
        for i, x in enumerate(dests)) + '</div>') if dests else '<p class="fine">—</p>'
    return main(back('/nepal/exports', 'Export Explorer') + f'''<div class="ph"><h1 class="h2">{g["fl"]} {esc(g["h1"])}</h1><p>{esc(g["sub"])}</p></div>
<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{money(z["ex"] * 1e6) if z.get("ex") else "—"}</b><span>Nepal exports (2024)</span></div>
<div class="s"><b>{money(p["w"] * 1e6) if p.get("w") else "—"}</b><span>World market</span></div><div class="s"><b>{"$" + str(p["u"]) + "/kg" if p.get("u") else "—"}</b><span>World price</span></div></div>
{g["body"]}<h3 class="h">Where Nepal sells it (2024)</h3>{dbars}<h3 class="h">The HS code</h3>
<a class="row" href="{code_href(hs)}" data-nav><span class="code">{fmt_code(hs)}</span><span class="d">{esc(hs_desc(hs))}</span><span class="end">{ic("right")}</span></a>'''
                + src_box('Sources', f'<p>Trade figures: <b>BACI</b> (CEPII / UN Comtrade), 2024. Export procedure: {g["sources"]} Incentive rates and GSP eligibility change yearly — confirm current terms with the official source before relying on them.</p>'))

# ---------------------------------------------------------------- per-route descriptions + breadcrumbs + JSON-LD
def top_names(lst, n=3):
    return ', '.join(iso_name(x[0]) for x in lst[:n])

def crumbs_for(p):
    cr = [('Home', '/')]; m = None
    if p == '/hs': cr.append(('HS Codes', '/hs'))
    elif (m := re.match(r'^/hs/chapter/(\d{2})$', p)):
        cr += [('HS Codes', '/hs'), (f'Chapter {m[1]} — {CH[m[1]][1]}', p)]
    elif (m := re.match(r'^/hs/code/(\d{6})$', p)):
        ch = m[1][:2]; cr += [('HS Codes', '/hs'), (f'Chapter {ch} — {CH[ch][1]}', f'/hs/chapter/{ch}'), (fmt_code(m[1]), p)]
    elif p == '/trade': cr.append(('Trade', '/trade'))
    elif p == '/nepal': cr += [('Trade', '/trade'), ('Nepal', '/nepal')]
    elif p == '/nepal/exports': cr += [('Trade', '/trade'), ('Nepal', '/nepal'), ('Exports', p)]
    elif (m := re.match(r'^/nepal/exports/guide/([a-z-]+)$', p)):
        cr += [('Trade', '/trade'), ('Nepal', '/nepal'), ('Exports', '/nepal/exports'), (EXGUIDES[m[1]]['name'], p)]
    elif (m := re.match(r'^/nepal/exports/([a-z]{3})$', p)):
        cr += [('Trade', '/trade'), ('Nepal', '/nepal'), ('Exports', '/nepal/exports'), (iso_name(m[1].upper()), p)]
    elif (m := re.match(r'^/trade/product/([a-z0-9-]+)$', p)):
        g = next(x for x in PGROUPS if group_slug(x[0]) == m[1]); cr += [('Trade', '/trade'), (g[0], p)]
    elif (m := re.match(r'^/trade/([a-z]{3})$', p)):
        cr += [('Trade', '/trade'), (iso_name(m[1].upper()), p)]
    return cr

def url(p):
    return B + ('/' if p == '/' else p)

ORG = {'@type': 'Organization', '@id': B + '/#org', 'name': 'Customs Nepal', 'url': 'https://www.customsnepal.com/',
       'logo': 'https://www.customsnepal.com/icon-512.png', 'sameAs': ['https://www.customsnepal.com/']}
WEBSITE = {'@type': 'WebSite', '@id': B + '/#website', 'url': B + '/', 'name': 'Customs Nepal — World HS & Trade',
           'description': 'International HS codes and global trade data.', 'inLanguage': 'en', 'publisher': {'@id': B + '/#org'},
           'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': B + '/hs?q={search_term_string}'},
                               'query-input': 'required name=search_term_string'}}

def dataset(name, desc, cover, temporal, based_on, keywords):
    return {'@type': 'Dataset', 'name': name, 'description': desc, 'creator': {'@id': B + '/#org'}, 'isAccessibleForFree': True,
            'spatialCoverage': cover, 'temporalCoverage': temporal, 'isBasedOn': based_on, 'keywords': keywords}

# ---------------------------------------------------------------- route table
def routes():
    """Yield (path, nav_key, title, description, body_html, page_type, extra_ld, sitemap_part)."""
    yield ('/', '', T.home(),
           f'Search {len(SUBS):,} international HS codes and explore the import/export trade of {len(COUNTRIES)} economies — world prices, top exporters and importers, and landed cost by origin.',
           v_home(), 'WebPage', [WEBSITE, ORG], 'hubs')
    yield ('/hs', 'hs', T.hs(),
           f'Search the full international Harmonized System — {len(SUBS):,} six-digit codes across {len(HS["chapters"])} chapters ({HS["edition"]}) — with world trade, top exporters and world prices for every code.',
           v_hs(), 'CollectionPage', [], 'hubs')
    yield ('/trade', 'trade', T.trade(),
           f'Global merchandise trade ({money(WORLD["totalExp"])} in {WORLD["year"]}): world rankings, exports and imports for {WORLD["count"]} economies, regional shares and trade by product group.',
           v_trade(), 'CollectionPage', [], 'hubs')
    Tt = NEP.get('_t') or {'im': 0, 'ex': 0}
    yield ('/nepal', 'trade', T.nepal(),
           f"Nepal in world trade: {money(Tt['im'] * 1e6)} imports, {money(Tt['ex'] * 1e6)} exports and a {money((Tt['im'] - Tt['ex']) * 1e6)} deficit (2024) — where Nepal overpays versus the world price, and its biggest export openings.",
           v_nepal(), 'WebPage', [dataset('Nepal merchandise trade by product (2024)', 'Nepal imports and exports by HS 6-digit product with partner countries and unit values compared with world averages, from BACI (CEPII) reconciled UN Comtrade data.',
                                         {'@type': 'Country', 'name': 'Nepal'}, '2024', 'https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37', ['Nepal trade', 'Nepal imports', 'Nepal exports'])], 'hubs')
    yield ('/nepal/exports', 'exports', T.nepEx(),
           f"What Nepal exports to the world — {len([i for i in NEPEXP['order'] if NEPEXP['cc'][i] > 0])} destination markets and {NEPEXP['nprod']} products, with world-price benchmarks. Total merchandise exports {money(Tt['ex'] * 1e6)} (2024).",
           v_nep_exports(), 'CollectionPage', [], 'hubs')
    for slug, g in EXGUIDES.items():
        yield (f'/nepal/exports/guide/{slug}', 'exports', T.guide(g), g['sub'], v_guide(slug), 'WebPage',
               [{'@type': 'Article', 'headline': g['h1'], 'description': g['sub'], 'author': {'@id': B + '/#org'}, 'publisher': {'@id': B + '/#org'},
                 'mainEntityOfPage': url(f'/nepal/exports/guide/{slug}'), 'about': {'@type': 'DefinedTerm', 'termCode': g['hs'], 'name': hs_desc(g['hs'])}}], 'hubs')
    for g in PGROUPS:
        slug = group_slug(g[0]); lx = product_traders(g[0], 'exp'); lm = product_traders(g[0], 'imp')
        yr = next((c.get('pYear') for c in COUNTRIES if c.get('deep')), '')
        d = (f'Who leads world trade in {g[0].lower()} (HS chapters {g[1]}–{g[2]}): top exporters {top_names(lx)}; top importers {top_names(lm)} ({yr}).')
        yield (f'/trade/product/{slug}', 'trade', T.group(g[0]), d, v_group(g), 'WebPage',
               [dataset(f'World trade in {g[0]} by country', d, {'@type': 'Place', 'name': 'World'}, str(yr), 'https://wits.worldbank.org/', [g[0], 'HS chapters %d-%d' % (g[1], g[2]), 'top exporters', 'top importers'])], 'product-groups')
    for c in HS['chapters']:
        ch = c[0]; n = sum(1 for s in SUBS if s[0].startswith(ch))
        heads = sorted({s[2] for s in SUBS if s[0].startswith(ch)})
        yield (f'/hs/chapter/{ch}', 'hs', T.chapter(ch, c[1]),
               f'All {n} six-digit HS codes in Chapter {ch} — {clip(c[1], 70)} ({HS["edition"]}), across {len(heads)} headings, each with world trade and top exporters.',
               v_chapter(ch), 'CollectionPage',
               [{'@type': 'DefinedTermSet', 'name': f'HS Chapter {ch} — {c[1]} ({HS["edition"]})', 'url': url(f'/hs/chapter/{ch}')}], 'hs-chapters')
    for c in COUNTRIES:
        iso = c['iso'].lower(); bal = (c.get('exp') or 0) - (c.get('imp') or 0)
        if c.get('exp') is not None:
            d = (f"{c['name']} trade profile: exports {money(c.get('exp'))} and imports {money(c.get('imp'))} in {c.get('expYear')}, "
                 f"trade balance {'+' if bal >= 0 else '−'}{money(abs(bal))[1:]}; world rank #{c.get('rankExp') or '–'} exporter, #{c.get('rankImp') or '–'} importer.")
            if c.get('deep') and c.get('expPartners'):
                d += ' Top export markets: ' + ', '.join(p[1] for p in c['expPartners'][:3]) + '.'
        else:
            d = f"{c['name']} trade profile: merchandise imports {money(c.get('imp'))} ({c.get('impYear')}), trend since {(c.get('trend') or [[None]])[0][0]} and official data sources."
        yrs = [r[0] for r in (c.get('trend') or [])]
        yield (f'/trade/{iso}', 'trade', T.country(c), d, v_country(c), 'WebPage',
               [dataset(f"{c['name']} merchandise trade — exports, imports{', partners and products' if c.get('deep') else ''}", d,
                        {'@type': 'Country', 'name': c['name']}, f'{yrs[0]}/{yrs[-1]}' if yrs else str(c.get('expYear') or ''),
                        'https://data.worldbank.org/', [f"{c['name']} exports", f"{c['name']} imports", f"{c['name']} trade balance"])], 'countries')
    for iso in NEPEXP['order']:
        if not NEPEXP['cc'][iso] > 0: continue
        name = iso_name(iso); prods = [x for x in NEPEXP['cp'][iso] if x[1] > 0]
        d = (f"Nepal exported {money(NEPEXP['cc'][iso] * 1e6)} to {name} in 2024 across {len(prods)} product{'s' if len(prods) != 1 else ''} — led by "
             f"{clip(hs_desc(prods[0][0]), 60)} (HS {fmt_code(prods[0][0])}). Values and world-price benchmarks.")
        yield (f'/nepal/exports/{iso.lower()}', 'exports', T.nepMkt(name), d, v_nep_market(iso), 'WebPage', [], 'nepal-exports')
    for s in SUBS:
        code = s[0]; p = PROD.get(code)
        if p and p.get('x'):
            d = (f'HS code {code} ({fmt_code(code)}): {stop(clip(s[1], 64))} World trade {money(p["w"] * 1e6)} (2024); top exporters {top_names(p["x"])}'
                 + (f'; world price ${p["u"]}/kg.' if p.get('u') else '.'))
        else:
            d = (f'HS code {code} ({fmt_code(code)}): {stop(clip(s[1], 90))} Six-digit {HS["edition"]} code in heading {code[:4]}, '
                 f'chapter {code[:2]} — {stop(clip(CH[code[:2]][1], 50))}')
        yield (f'/hs/code/{code}', 'hs', T.code(code, s[1]), d, v_code(code), 'WebPage',
               [{'@type': 'DefinedTerm', '@id': url(f'/hs/code/{code}') + '#term', 'termCode': code, 'name': s[1],
                 'inDefinedTermSet': {'@type': 'DefinedTermSet', 'name': 'Harmonized System (' + HS['edition'] + ')', 'url': 'https://www.wcoomd.org/en/topics/nomenclature/overview.aspx'}}], 'hs-codes')

# ---------------------------------------------------------------- document template
NAV = [('/hs', 'hs', 'HS Codes'), ('/trade', 'trade', 'Trade'), ('/nepal/exports', 'exports', 'Nepal Exports')]

def header(k):
    links = ''.join(f'<a href="{h}" data-nav data-k="{kk}"{" class=\"on\"" if kk == k else ""}>{lbl}</a>' for h, kk, lbl in NAV)
    return (f'<header class="bar"><div class="wrap"><a class="logo" href="/" data-nav><span class="mk">HS</span><span>Customs Nepal<small>World HS &amp; Trade</small></span></a>'
            f'<nav class="nav">{links}<a class="ext" href="{MAIN}" target="_blank" rel="noopener">Nepal tools ↗</a></nav></div></header>')

# "Our other sites": the Nepal-data cluster siblings (AI-search / site-network spec) — plain followed links whose anchor is
# the site's role + domain. Same wording as OTHER_SITES in scripts/nav.py (main site). No links to unrelated sites.
OTHER_SITES = ('<p style="margin:0 0 6px"><b style="color:var(--fg-2)">Our other sites:</b> '
               '<a href="https://www.customsnepal.com/">Nepal HS codes, customs tariff 2083/84 &amp; import-duty calculator — customsnepal.com</a> · '
               '<a href="https://nepalpublicdata.com/">Nepal public statistics: population, budget, trade &amp; places — nepalpublicdata.com</a></p>')
FOOTER = ('<footer><div class="wrap"><p style="margin:0 0 6px"><b style="color:var(--fg-2)">world.customsnepal.com</b> — the international companion to Customs Nepal.</p>' + OTHER_SITES +
          '<p style="margin:0">HS nomenclature © World Customs Organization. Trade figures: World Bank &amp; World Bank WITS (sourced from UN Comtrade). This is an independent reference tool, not affiliated with any government or the WCO. Figures are indicative — verify against official sources before commercial decisions.</p></div></footer>')

GTAG = ('<script async src="https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV"></script>'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-T1FQWWL2VV',{send_page_view:false});</script>")

def document(seo_head, k, app_html, css_href, js_href, robots='index,follow,max-image-preview:large'):
    js = f'<script src="{js_href}" defer></script>' if js_href else ''
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<!--seo-->\n{seo_head}\n<!--/seo-->\n<meta name="robots" content="{robots}">\n<meta name="theme-color" content="#1B2A45">\n'
            f'<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="apple-touch-icon" href="https://www.customsnepal.com/icon-180.png">\n'
            f'<link rel="stylesheet" href="{css_href}">\n{GTAG}\n{js}\n</head>\n<body>\n{header(k)}\n<div id="app"><!--app-->{app_html}<!--/app--></div>\n{FOOTER}\n</body>\n</html>\n')

def seo_head(p, title, desc, page_type, extra_ld, lastmod):
    u = url(p); cr = crumbs_for(p)
    bc = {'@type': 'BreadcrumbList', '@id': u + '#breadcrumb', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': url(h)} for i, (n, h) in enumerate(cr)]}
    page = {'@type': page_type, '@id': u + '#webpage', 'url': u, 'name': title, 'description': desc, 'inLanguage': 'en',
            'isPartOf': {'@id': B + '/#website'}, 'breadcrumb': {'@id': u + '#breadcrumb'}, 'dateModified': lastmod}
    ld = json.dumps({'@context': 'https://schema.org', '@graph': [page, bc] + extra_ld}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    t, d = esc(title), esc(desc)
    return (f'<title>{t}</title>\n<meta name="description" content="{d}">\n<link rel="canonical" href="{u}">\n<meta name="cn-route" content="{p}">\n'
            f'<meta property="og:site_name" content="Customs Nepal"><meta property="og:type" content="website"><meta property="og:url" content="{u}">'
            f'<meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:image" content="https://www.customsnepal.com/og.png">\n'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://www.customsnepal.com/og.png">\n'
            f'<script type="application/ld+json">{ld}</script>')

def out_path(p):
    return W / 'index.html' if p == '/' else W / (p.lstrip('/') + '.html')

# ---------------------------------------------------------------- 404
def page_404(css_href):
    hubs = [('/hs', 'World HS Code Finder', f'Search {len(SUBS):,} six-digit HS codes'), ('/trade', 'Global trade data', f'{len(COUNTRIES)} economies — rankings & profiles'),
            ('/nepal/exports', 'Nepal Export Explorer', 'What Nepal exports, and where')]
    cards = ''.join(f'<a class="row" href="{h}"><span class="d"><b>{t}</b><small style="display:block;color:var(--muted)">{s}</small></span><span class="end">{ic("right")}</span></a>' for h, t, s in hubs)
    body = main(f'''<div class="ph" style="padding-top:24px"><p style="margin:0;color:var(--muted);font-weight:700">404 — page not found</p><h1 class="h2">We couldn't find that page.</h1>
<p>The link may be old or mistyped. Search the HS codes, or jump to one of the sections below.</p></div>
<form class="sbox" action="/hs" method="get" role="search">{ic("search")}<input name="q" type="search" placeholder="Search a product or HS code, e.g. coffee, 8471" aria-label="Search HS codes" autofocus></form>
<p id="hint" class="fine" style="display:none"></p>{cards}
<p class="fine" style="margin-top:var(--s4)">Looking for Nepal's own tariff, duty and taxes? Use <a href="{MAIN}/">customsnepal.com</a>.</p>''')
    hint = ("<script>(function(){var m=location.pathname.match(/(\\d{6})/)||location.pathname.match(/(\\d{4})/);if(!m)return;var c=m[1],h=document.getElementById('hint');"
            "h.innerHTML=c.length===6?'Looking for HS '+c.slice(0,4)+'.'+c.slice(4)+'? <a href=\"/hs/code/'+c+'\">Open /hs/code/'+c+'</a> or <a href=\"/hs?q='+c+'\">search '+c+'</a>.':'<a href=\"/hs?q='+c+'\">Search HS codes starting '+c+'</a>.';h.style.display='';})();</script>")
    head = '<title>Page not found — World HS Codes & Trade</title>\n<meta name="description" content="This page does not exist on world.customsnepal.com.">'
    return document(head, '', body, css_href, None, robots='noindex,follow').replace('</body>', hint + '\n</body>')

# ---------------------------------------------------------------- build
def write_assets():
    (W / 'assets').mkdir(exist_ok=True)
    css = (SRC / 'app.css').read_text(encoding='utf-8')
    css += '\n/* prerender: semantic headings styled like the SPA\'s h2 */\nh1.h2{margin:0;font-size:1.5rem;letter-spacing:-.02em;font-weight:800}\nh1.dcode{margin:0}\na.row,a.sec,a.lbrow,a.nepalcard,a.back{text-decoration:none}\n'
    js = (SRC / 'app.js').read_text(encoding='utf-8')
    assert '/*@META@*/null' in js, 'META placeholder missing from world-src/app.js'
    js = js.replace('/*@META@*/null', json.dumps(META, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    names = {}
    for ext, body in (('css', css), ('js', js)):
        h = hashlib.sha1(body.encode('utf-8')).hexdigest()[:10]
        name = f'world.{h}.{ext}'
        (W / 'assets' / name).write_text(body, encoding='utf-8')
        names[ext] = '/assets/' + name
        for old in (W / 'assets').glob(f'world.*.{ext}'):
            if old.name != name: old.unlink()
    (W / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#1B2A45"/>'
                                   '<text x="16" y="21" font-family="monospace" font-size="13" font-weight="700" fill="white" text-anchor="middle">HS</text></svg>\n', encoding='utf-8')
    return names

def write_vercel_json():
    # GENERATED file (vercel.json allows no comment keys): every public route is a prerendered static file;
    # anything else falls through to Vercel's static 404 handling, which serves 404.html with a real 404 status.
    redirects = [{'source': f'/hs/code/{c}', 'destination': f'/hs/chapter/{c[:2]}', 'permanent': True} for c in sorted(MISSING_CODES) if c[:2] in CH]
    cfg = {
        'cleanUrls': True, 'trailingSlash': False,
        'redirects': redirects + [{'source': '/index', 'destination': '/', 'permanent': True}],
        'headers': [
            {'source': '/assets/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]},
            {'source': '/data/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=3600, must-revalidate'},
                                                 {'key': 'X-Robots-Tag', 'value': 'noindex'}]},
            {'source': '/(llms\\.txt|robots\\.txt)', 'headers': [{'key': 'Content-Type', 'value': 'text/plain; charset=utf-8'},
                                                                {'key': 'Cache-Control', 'value': 'public, max-age=3600, must-revalidate'}]},
            # IndexNow ownership key (<32 hex>.txt, hand-placed, see scripts/indexnow_submit.py) — plain text, short cache
            {'source': '/([0-9a-f]{32}\\.txt)', 'headers': [{'key': 'Content-Type', 'value': 'text/plain; charset=utf-8'},
                                                          {'key': 'Cache-Control', 'value': 'public, max-age=3600, must-revalidate'}]},
            {'source': '/(sitemap.*\\.xml)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=3600, must-revalidate'}]},
            {'source': '/(.*)', 'headers': [{'key': 'X-Content-Type-Options', 'value': 'nosniff'},
                                            {'key': 'Referrer-Policy', 'value': 'strict-origin-when-cross-origin'}]}]}
    (W / 'vercel.json').write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return len(redirects)

SITEMAP_PARTS = ['hubs', 'product-groups', 'hs-chapters', 'countries', 'nepal-exports', 'hs-codes']

def write_sitemaps(entries):
    for f in W.glob('sitemap*.xml'): f.unlink()
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    counts = {}
    for part in SITEMAP_PARTS:
        rows = [(p, lm) for p, lm, pt in entries if pt == part]
        counts[part] = len(rows)
        body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        body += [f'<url><loc>{url(p)}</loc><lastmod>{lm}</lastmod></url>' for p, lm in rows]
        body.append('</urlset>')
        (W / f'sitemap-{part}.xml').write_text('\n'.join(body) + '\n', encoding='utf-8')
        idx.append(f'<sitemap><loc>{B}/sitemap-{part}.xml</loc><lastmod>{max(lm for _, lm in rows)}</lastmod></sitemap>')
    idx.append('</sitemapindex>')
    (W / 'sitemap.xml').write_text('\n'.join(idx) + '\n', encoding='utf-8')
    return counts

def main_build():
    assets = write_assets()
    # generated route files are rebuilt from scratch each run (stale routes must disappear → 404)
    for d in ('hs', 'trade', 'nepal'):
        shutil.rmtree(W / d, ignore_errors=True)
        (W / (d + '.html')).unlink(missing_ok=True)
    try:
        lastmod = json.loads(LASTMOD_FILE.read_text(encoding='utf-8'))
    except FileNotFoundError:
        lastmod = {}
    new_lastmod, entries, seen = {}, [], set()
    total_bytes = n = 0
    for p, k, title, desc, body, ptype, extra_ld, part in routes():
        assert p not in seen, p; seen.add(p)
        # lastmod only moves when the page's own content changes (not when shared CSS/JS change)
        h = hashlib.sha1(json.dumps([title, desc, body, extra_ld], ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:16]
        prev = lastmod.get(p)
        lm = prev[1] if prev and prev[0] == h else TODAY
        new_lastmod[p] = [h, lm]
        doc = document(seo_head(p, title, desc, ptype, extra_ld, lm), k, body, assets['css'], assets['js'])
        f = out_path(p); f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(doc, encoding='utf-8')
        total_bytes += len(doc.encode('utf-8')); n += 1
        entries.append((p, lm, part))
    (W / '404.html').write_text(page_404(assets['css']), encoding='utf-8')
    LASTMOD_FILE.write_text(json.dumps(new_lastmod, separators=(',', ':'), sort_keys=True) + '\n', encoding='utf-8')
    counts = write_sitemaps(entries)
    nred = write_vercel_json()
    files = [x for x in W.rglob('*') if x.is_file()]
    out_bytes = sum(x.stat().st_size for x in files)
    print(f'world prerender: {n:,} pages ({total_bytes / 1e6:.1f} MB HTML, avg {total_bytes / n / 1024:.1f} KB) + 404.html; '
          f'assets {assets["css"]} {assets["js"]}; {nred} redirect(s)')
    print('  sitemaps: ' + ', '.join(f'{k} {v:,}' for k, v in counts.items()))
    print(f'  world/ total: {len(files):,} files, {out_bytes / 1e6:.1f} MB')

if __name__ == '__main__':
    main_build()
