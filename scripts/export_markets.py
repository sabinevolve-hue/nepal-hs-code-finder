#!/usr/bin/env python3
"""/export-markets: for each product Nepal exports (USD 1 million or more a year), who buys it, who else buys it,
and what duty the main markets charge.

Data:
  data/export_markets.json     CEPII BACI, HS 2022 edition, 2022-2024 (scripts/export_markets_data.py). Calendar years, US dollars.
  data/world/tariffs/*.json    official import tariffs of the US, UK, EU, Australia and Japan (scripts/world_tariffs.py)
These are a different source and period from the Department of Customs figures elsewhere on this site (fiscal years, rupees);
each table names its source and they are never mixed in one table.

Pages state recorded values only: no forecasts, no advice on where to sell.
Runs after export_pages.py and before footer_pass / check_pages. Stdlib only.
"""
import json, re, pathlib
import pagekit as k
from pagekit import esc, pub, root

D = json.loads((root / 'data' / 'export_markets.json').read_text(encoding='utf-8'))
YEARS = [str(y) for y in D['years']]; LAST, FIRST = YEARS[-1], YEARS[0]
TRADE = json.loads((root / 'world' / 'data' / 'trade.json').read_text(encoding='utf-8'))
NAME = {c['iso']: c['name'] for c in TRADE['countries']}
NAME.update({'S19': 'Other Asia, not elsewhere specified', 'TWN': 'Taiwan'})
PARTNER = {p.stem for p in (pub / 'trade-partner').glob('*.html')}
slugify = lambda s: re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')
GUIDE = {'570110': 'carpets', '090831': 'cardamom', '090240': 'tea', '621420': 'pashmina', '230910': 'dog-chew',
         '121190': 'herbs', '190230': 'noodles', '630510': 'jute', '611012': 'knitwear', '560290': 'felt'}
WORLD = 'https://world.customsnepal.com'
TARIFF = [('USA', 'United States', 'united-states', 'general rate'), ('EUU', 'European Union', 'european-union', 'third-country duty'),
          ('GBR', 'United Kingdom', 'united-kingdom', 'third-country duty'), ('JPN', 'Japan', 'japan', 'rate for WTO members'),
          ('AUS', 'Australia', 'australia', 'general rate')]
TF = {}
for iso, *_ in TARIFF:
    f = root / 'data' / 'world' / 'tariffs' / (iso.lower() + '.json')
    if f.exists():
        d = json.loads(f.read_text(encoding='utf-8'))
        by6 = {}
        for l in d['lines']:
            by6.setdefault(l[0][:6], []).append(l[2])
        TF[iso] = (d['meta'], by6)


def usd(th):
    v = float(th) * 1000
    if v >= 1e9:
        return '$%.2f bn' % (v / 1e9)
    if v >= 1e6:
        return '$%.1f m' % (v / 1e6)
    if v >= 1e3:
        return '$%.0f k' % (v / 1e3)
    return '$%.0f' % v


def change(a, b):
    if not a:
        return 'new' if b else '–'
    return '%+.0f%%' % (100.0 * (b - a) / a)


def country(iso):
    n = NAME.get(iso, iso); s = slugify(n)
    return f'<a href="/trade-partner/{s}">{esc(n)}</a>' if s in PARTNER else esc(n)


import textfit


def short(desc, n=60):
    """The product name the world site uses (textfit.hs_name), with the heading kept so 'Other' lines still say what they are."""
    s = textfit.hs_name(desc, n)
    s = re.sub(r'\s*\bn\.e\.c\.?(?= |$|,)', '', s).replace(' :', ':').strip(' ,;:')
    return s[:1].upper() + s[1:]


def fhs(c):
    return c[:4] + '.' + c[4:]


def rate_range(rates):
    pct = []
    for r in rates:
        t = r.strip()
        if t.lower() == 'free':
            pct.append(0.0)
        elif re.fullmatch(r'\d+(\.\d+)?%', t):
            pct.append(float(t[:-1]))
    other = len(rates) - len(pct)
    if not pct:
        return 'per unit or mixed' if rates else '–'
    lo, hi = min(pct), max(pct)
    f = lambda x: 'Free' if x == 0 else ('%g%%' % x)
    s = f(lo) if lo == hi else '%s to %s' % (f(lo), f(hi))
    return s + (' (some lines per unit)' if other else '')


def table(heads, rows, label, left=1):
    th = ''.join(f'<th{" class=r" if i >= left else ""}>{h}</th>' for i, h in enumerate(heads))
    tr = ''.join('<tr>' + ''.join(f'<td{" class=r" if i >= left else ""}>{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return (f'<div class="tscroll" tabindex="0" role="region" aria-label="{esc(label)}"><table class="tbl">'
            f'<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')


SRC = ('Trade figures: <a href="https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37" target="_blank" rel="noopener">CEPII BACI</a> '
       '(HS 2022 edition, calendar years %s to %s, US dollars; Etalab Open Licence 2.0). BACI reconciles what exporters and importers report, '
       'so its Nepal figures differ from the Department of Customs fiscal-year figures elsewhere on this site.' % (FIRST, LAST))

pages, cards = [], []
NAMES = json.loads((root / 'data' / 'export_market_names.json').read_text(encoding='utf-8'))   # plain names, written by hand
_seen = set()
for p in D['products']:
    hs6 = p['hs6']; nm = nm_t = NAMES.get(hs6) or short(p['desc'])
    slug = slugify(nm)
    if slug in _seen:
        slug += '-' + hs6
    _seen.add(slug)
    path = '/export-markets/' + slug
    nep = p['nepal']; tot = {y: sum(nep[y].values()) for y in YEARS}
    world = p['world']; share = 100.0 * tot[LAST] / world[LAST] if world[LAST] else 0
    dest = sorted(set().union(*[nep[y].keys() for y in YEARS]), key=lambda c: (-nep[LAST].get(c, 0), -sum(nep[y].get(c, 0) for y in YEARS), c))   # stable order
    top_dest = [c for c in dest if nep[LAST].get(c)][:3]
    cards.append((tot[LAST], hs6, nm, path, top_dest))

    # Nepal's buyers
    nrows = [(country(c), *[usd(nep[y][c]) if nep[y].get(c) else '–' for y in YEARS],
              '%.0f%%' % (100.0 * nep[LAST].get(c, 0) / tot[LAST]) if tot[LAST] else '–') for c in dest[:15]]
    # the world's buyers, with Nepal's sales in each
    imp = p['importers']
    wrows, gaps = [], []
    for row in imp[:20]:
        c, vals = row[0], dict(zip(YEARS, row[1:]))
        mine = nep[LAST].get(c, 0)
        if not mine:
            gaps.append(c)
        wrows.append((country(c), usd(vals[LAST]), change(vals[FIRST], vals[LAST]),
                      usd(mine) if mine else '–', ('%.1f%%' % (100.0 * mine / vals[LAST])) if mine and vals[LAST] else '–'))
    # duties in the five schedules
    trows = []
    for iso, name, tslug, label in TARIFF:
        if iso not in TF:
            continue
        meta, by6 = TF[iso]; rs = by6.get(hs6, [])
        if not rs:
            continue
        trows.append((f'<a href="{WORLD}/tariffs/{tslug}#hs={hs6}" target="_blank" rel="noopener">{esc(name)}</a>', esc(label),
                      esc(rate_range(rs)), str(len(rs))))

    title = f'{nm_t} from Nepal: Export Markets and Buyers (HS {fhs(hs6)})'
    if len(title) > 70:
        title = f'{nm_t} from Nepal: Export Markets (HS {fhs(hs6)})'
    desc = (f'Nepal exported {usd(tot[LAST])} of {nm_t[:1].lower() + nm_t[1:]} (HS {fhs(hs6)}) in {LAST}, '
            + (f'mostly to {NAME.get(top_dest[0], top_dest[0])}. ' if top_dest else '')
            + 'Its buyers, the world\'s largest importers and the duty they charge.')
    bc = [('Home', '/'), ('Export markets', '/export-markets'), (nm_t, '')]
    out = [k.page_head(title, desc[:300], path, bc), k.crumb_html(bc)]
    out.append(f'<h1>Who buys Nepal&#39;s {esc(nm[:1].lower() + nm[1:])}?</h1>')
    out.append(f'<p class="lede">HS {fhs(hs6)}: {esc(p["desc"])}.</p>')
    out.append('<style>.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:1em 0}.kpi{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px}.kpi b{display:block;font-size:1.25rem}.kpi span{font-size:.82rem;color:var(--muted)}</style><div class="kpis">'
               f'<div class="kpi"><b>{usd(tot[LAST])}</b><span>Nepal&#39;s exports, {LAST}</span></div>'
               f'<div class="kpi"><b>{change(tot[FIRST], tot[LAST])}</b><span>Change since {FIRST}</span></div>'
               f'<div class="kpi"><b>{usd(world[LAST])}</b><span>World imports, {LAST}</span></div>'
               f'<div class="kpi"><b>{share:.2f}%</b><span>Nepal&#39;s share of world imports</span></div></div>')
    if p['hs6'] in GUIDE:
        out.append(f'<p>How to export it, step by step: <a href="/export/{GUIDE[hs6]}">the export guide</a>.</p>')
    out.append('<h2 class="sec">Where Nepal sells it</h2>' + table(['Buyer'] + YEARS + [f'Share of {LAST}'], nrows, 'Nepal\'s buyers'))
    out.append(f'<h2 class="sec">The world&#39;s largest buyers, {LAST}</h2>'
               '<p>Every country that imports this product, largest first, with what Nepal sold there. A dash means no sales from Nepal were recorded.</p>'
               + table(['Importer', f'Imports {LAST}', f'Change since {FIRST}', 'From Nepal', 'Nepal&#39;s share'], wrows, 'World importers'))
    if gaps:
        out.append(f'<p class="note">Of these {len(wrows)} largest importers, {len(gaps)} recorded no imports from Nepal in {LAST}: '
                   + ', '.join(esc(NAME.get(c, c)) for c in gaps[:10]) + ('…' if len(gaps) > 10 else '') + '.</p>')
    if trows:
        out.append('<h2 class="sec">Import duty in five markets</h2>'
                   '<p>The normal duty each market&#39;s own tariff sets for this code, across its national tariff lines. '
                   'Goods from Nepal may pay less under preference schemes for least developed countries or trade agreements, '
                   'if they meet the rules of origin; check with the importing country&#39;s customs. The links open each full tariff on World Trade Data.</p>'
                   + table(['Market', 'Rate shown', 'Duty', 'Tariff lines'], trows, 'Import duty in five markets', 2))
    out.append(f'<div class="tools"><a class="btn" href="/#hs-{hs6[:4]}">Nepal&#39;s own tariff for heading {hs6[:4]}</a>'
               f'<a class="btn ghost" href="{WORLD}/hs/code/{hs6}" target="_blank" rel="noopener">World trade in this product</a>'
               '<a class="btn ghost" href="/export-markets">All export products</a></div>')
    out.append(k.foot(SRC + ' Duty: official tariffs of the US, UK, EU, Australia and Japan, as listed on World Trade Data.'))
    (pub / path.lstrip('/')).with_suffix('.html').parent.mkdir(parents=True, exist_ok=True)
    (pub / (path.lstrip('/') + '.html')).write_text(''.join(out), encoding='utf-8')
    pages.append(path)

# hub
cards.sort(key=lambda x: -x[0])
rows = [(f'<a href="{pth}">{esc(nm)}</a>', f'<span class="mono">{fhs(hs6)}</span>', usd(v), ', '.join(esc(NAME.get(c, c)) for c in td))
        for v, hs6, nm, pth, td in cards]
bc = [('Home', '/'), ('Export markets', '')]
title = 'Nepal Export Markets: Who Buys Nepali Products'
desc = (f'The {len(cards)} products Nepal exports most (USD 1 million or more in {LAST}): who buys each, '
        'the world\'s largest importers, and the import duty in the US, UK, EU, Australia and Japan.')
hub = [k.page_head(title, desc, '/export-markets', bc), k.crumb_html(bc),
       '<h1>Who buys what Nepal exports</h1>',
       f'<p class="lede">{len(cards)} products Nepal sold abroad worth USD 1 million or more in {LAST}. Each page shows where Nepal sells it, '
       'which countries import the most of it worldwide, and the duty five large markets charge.</p>',
       '<p>Looking for the export process itself? See the <a href="/export">export guides</a>.</p>',
       table(['Product', 'HS code', f'Nepal&#39;s exports {LAST}', 'Main buyers'], rows, 'Nepal\'s export products'),
       k.foot(SRC)]
(pub / 'export-markets.html').write_text(''.join(hub), encoding='utf-8')

# point the export guides and their hub at the market pages
SLUG_OF = {hs6: pth for _, hs6, _, pth, _ in cards}
for hs6, g in GUIDE.items():
    f = pub / 'export' / (g + '.html')
    if f.exists() and hs6 in SLUG_OF:
        t = f.read_text(encoding='utf-8'); mark = '<h2 class="sec">More export guides'
        if 'class="note emk"' not in t and mark in t:
            f.write_text(t.replace(mark, f'<p class="note emk">Every country that imports this product, Nepal&#39;s share in each, and the duty in five large markets: '
                                          f'<a href="{SLUG_OF[hs6]}">export markets for this product</a>.</p>' + mark, 1), encoding='utf-8')
f = pub / 'export.html'
t = f.read_text(encoding='utf-8'); mark = '<h2 class="sec">'
if 'class="note emk"' not in t and mark in t:
    f.write_text(t.replace(mark, f'<p class="note emk">Who buys each of the {len(cards)} products Nepal exports most, and the duty they face: '
                                 '<a href="/export-markets">export markets</a>.</p>' + mark, 1), encoding='utf-8')
print('export_markets: /export-markets + %d product pages; +%d sitemap URLs' % (len(pages), k.add_to_sitemap(['/export-markets'] + pages)))
