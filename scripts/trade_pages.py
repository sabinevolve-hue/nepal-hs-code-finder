"""Trade pages — static, crawlable per-country and per-category trade pages on customsnepal.com.

The interactive trade explorer (/trade-data, the SPA) has a Flows (sankey) view whose country
nodes (left) and category nodes (right) now link out to these pages. Each page is a real URL,
shareable and indexable, built from the Department of Customs foreign-trade statistics inlined
in data/stats.json (latest full fiscal year + a 7-year history).

Mirrors seo_pages.py / shipping_pages.py (same header / nav / canonical / GA / seo.css).

Emits into public/:
  /trade/countries            index of every trading-partner country
  /trade/categories           index of every HS category (chapter)
  /trade/country/<slug>       one page per partner country (Nepal–<country> trade)
  /trade/category/<nn>        one page per HS category (chapter) with trade + duty
Appends trade styles to /seo.css and the new URLs to /sitemap.xml.

Run after safta_page.py:  python3 scripts/trade_pages.py
"""
import pathlib, json, datetime, html, re, unicodedata

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'trade' / 'country').mkdir(parents=True, exist_ok=True)
(pub / 'trade' / 'category').mkdir(parents=True, exist_ok=True)

SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
S = json.load(open(root / 'data' / 'stats.json', encoding='utf-8'))
T = json.load(open(root / 'data' / 'tariff.json', encoding='utf-8'))
FY = S['fy']; UNIT = S['unit']

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def slug(n):
    n = unicodedata.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')

# short category names (kept in sync with CHSHORT in src.html)
CHSHORT = {1:"Live animals",2:"Meat",3:"Fish & seafood",4:"Dairy, eggs & honey",5:"Other animal products",6:"Live plants & flowers",7:"Vegetables",8:"Fruit & nuts",9:"Coffee, tea & spices",10:"Cereals",11:"Flour, malt & starch",12:"Oil seeds & medicinal plants",13:"Gums & resins",14:"Vegetable materials",15:"Edible oils & fats",16:"Meat & fish preparations",17:"Sugar & confectionery",18:"Cocoa & chocolate",19:"Cereal & bakery products",20:"Processed fruit & vegetables",21:"Misc. food preparations",22:"Beverages & spirits",23:"Animal feed & residues",24:"Tobacco",25:"Salt, stone, cement & lime",26:"Ores & ash",27:"Fuels, oils & gas",28:"Inorganic chemicals",29:"Organic chemicals",30:"Pharmaceuticals",31:"Fertilisers",32:"Dyes, paints & inks",33:"Cosmetics & perfumery",34:"Soap & cleaning products",35:"Glues & enzymes",36:"Explosives & matches",37:"Photographic goods",38:"Misc. chemicals",39:"Plastics",40:"Rubber",41:"Raw hides & leather",42:"Leather goods & bags",43:"Furskins",44:"Wood & timber",45:"Cork",46:"Straw & basketware",47:"Wood pulp",48:"Paper & paperboard",49:"Books & printed matter",50:"Silk",51:"Wool & animal hair",52:"Cotton",53:"Jute & other fibres",54:"Synthetic filaments",55:"Synthetic staple fibres",56:"Wadding, felt & rope",57:"Carpets",58:"Special fabrics & lace",59:"Coated & industrial textiles",60:"Knitted fabrics",61:"Knitted garments",62:"Woven garments",63:"Textile articles & rags",64:"Footwear",65:"Headgear",66:"Umbrellas & sticks",67:"Feathers & artificial flowers",68:"Stone & cement articles",69:"Ceramics",70:"Glass",71:"Gems, gold & jewellery",72:"Iron & steel",73:"Iron & steel articles",74:"Copper",75:"Nickel",76:"Aluminium",77:"Reserved",78:"Lead",79:"Zinc",80:"Tin",81:"Other base metals",82:"Tools & cutlery",83:"Misc. metal articles",84:"Machinery & mechanical",85:"Electrical & electronics",86:"Railway",87:"Vehicles & parts",88:"Aircraft & drones",89:"Ships & boats",90:"Optical, medical & precision",91:"Clocks & watches",92:"Musical instruments",93:"Arms & ammunition",94:"Furniture & lighting",95:"Toys, games & sports",96:"Misc. manufactured",97:"Art & antiques"}
SAARC = {'India','Pakistan','Bangladesh','Sri Lanka','Nepal','Bhutan','Maldives','Afghanistan'}
chapters_full = {int(k): v.get('t', '') for k, v in T['chapters'].items()}

def rsf(v):
    """Rs thousand -> Nepali-unit string (Arab/Crore/Lakh)."""
    try: r = float(v) * 1000.0
    except Exception: return '—'
    if r <= 0: return '—'
    if r >= 1e9: return 'Rs %s Arab' % ('%.2f' % (r / 1e9)).rstrip('0').rstrip('.')
    if r >= 1e7: return 'Rs %s Crore' % ('%.2f' % (r / 1e7)).rstrip('0').rstrip('.')
    if r >= 1e5: return 'Rs %s Lakh' % ('%.2f' % (r / 1e5)).rstrip('0').rstrip('.')
    return 'Rs %s' % ('{:,.0f}'.format(r))

def bn(v):
    try: return float(v) * 1000.0 / 1e9
    except Exception: return 0.0

def dotted(code):
    c = re.sub(r'\D', '', str(code))
    return c[:4] + '.' + c[4:6] + '.' + c[6:] if len(c) >= 8 else code

# ---------- totals / lookups ----------
TOT_IMP = sum((c[1] or 0) for c in S['countries'])
TOT_EXP = sum((c[2] or 0) for c in S['countries'])
CO_IMP = {c[0]: (c[1] or 0) for c in S['countries']}
CO_EXP = {c[0]: (c[2] or 0) for c in S['countries']}
CH_IMP = {c[0]: (c[2] or 0) for c in S['chapters']}
CH_EXP = {c[0]: (c[3] or 0) for c in S['chapters']}
imp_rank = {nm: i + 1 for i, nm in enumerate(sorted(CO_IMP, key=lambda n: -CO_IMP[n]))}
chimp_rank = {ch: i + 1 for i, ch in enumerate(sorted(CH_IMP, key=lambda c: -CH_IMP[c]))}
HY = S['history']['years']
HC = S['history']['countries']   # name -> [[imp,exp]*7]
HCH = S['history']['chapters']   # "n" -> [[imp,exp,x]*7]

# chapter -> source countries (import), from flow (top-30 source countries, full chapter split)
ch_sources = {}
for co, arr in S['flow'].items():
    for ch, v in arr:
        ch_sources.setdefault(int(ch), []).append((co, v))
# chapter -> export destinations, inverted from country_top[* ][1]
ch_dest = {}
for co, tt in S['country_top'].items():
    for ch, v in (tt[1] if len(tt) > 1 else []):
        ch_dest.setdefault(int(ch), []).append((co, v))

# chapter -> general-duty range from tariff.json
ch_duty = {}
for r in T['rows']:
    ch = int(r[0][:2]); g = str(r[5]).strip()
    m = re.match(r'^(\d+(?:\.\d+)?)$', g.replace('Free', '0') if g.lower() == 'free' else g)
    if m:
        ch_duty.setdefault(ch, []).append(float(m.group(1)))

def duty_label(ch):
    vals = ch_duty.get(ch)
    if not vals: return None
    lo, hi = min(vals), max(vals)
    f = lambda x: ('%g' % x)
    return (f(lo) + '%' if lo == hi else f(lo) + '–' + f(hi) + '%')

# ---------------- shared chrome (mirrors shipping_pages.py) ----------------
FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")
NAV = [('/', 'Search'), ('/ask-ai', 'Ask AI'), ('/imports', 'Imports'), ('/exports', 'Exports'),
       ('/export', 'Export guides'), ('/shipping', 'Shipping'), ('/safta', 'SAFTA'), ('/trade-data', 'Trade'),
       ('/browse', 'Browse'), ('/tariff', 'Tariff'), ('/calculator', 'Calculator'), ('/faq', 'FAQ')]

def _cur(h, path):
    return (path == h) or (h == '/trade-data' and path.startswith('/trade'))

def page_head(title, desc, path, breadcrumb, extra_ld=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = ''.join('<a href="%s"%s>%s</a>' % (h, ' class="cur"' if _cur(h, path) else '', esc(l)) for h, l in NAV)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0F172A">'
        '<title>' + esc(title) + '</title>'
        '<meta name="description" content="' + esc(desc) + '">'
        '<link rel="canonical" href="' + SITE + path + '">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Customs Nepal">'
        '<meta property="og:title" content="' + esc(title) + '">'
        '<meta property="og:description" content="' + esc(desc) + '">'
        '<meta property="og:url" content="' + SITE + path + '">'
        '<meta property="og:image" content="' + SITE + '/og.png">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="icon" href="' + FAVICON + '"><link rel="apple-touch-icon" href="/icon-180.png">'
        '<link rel="stylesheet" href="/seo.css">'
        + ldj + ANALYTICS +
        '</head><body>'
        '<header class="top"><div class="wrap topbar">'
        '<a class="logo" href="/" aria-label="Customs Nepal — home"><span class="mark">HS</span><span class="lt">Customs Nepal<small>HS codes, duty &amp; trade</small></span></a>'
        '<nav class="topnav">' + nav + '</nav></div></header>'
        '<div class="wrap">'
    )

def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'

FOOT = ('<footer><div class="wrap">'
        '<p><b>Figures are from the Department of Customs Foreign Trade Statistics</b> for %s (values in %s, '
        'customs/assessable value). Trade values are not the same as retail prices and exclude under/over-invoicing '
        'and informal trade. Use them as direction and scale, not exact accounting.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the '
        'Government of Nepal. Source: <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer nofollow">Department of Customs</a>.</p>'
        '<p><a href="/">Home</a> · <a href="/trade-data">Trade explorer</a> · <a href="/trade/countries">Countries</a> · '
        '<a href="/trade/categories">Categories</a> · <a href="/tariff">Tariff</a> · <a href="/calculator">Landed-cost calculator</a> · © customsnepal.com</p></div></footer>'
        '</body></html>') % (esc('FY ' + FY), esc(UNIT))

# ---------------- components ----------------
def tiles(items):
    return '<div class="tgrid">' + ''.join(
        '<div class="tile"><span class="tl">%s</span><b class="tv">%s</b>%s</div>' % (esc(l), esc(v), ('<span class="ts">%s</span>' % esc(s)) if s else '')
        for l, v, s in items) + '</div>'

def trend_svg(series_imp, series_exp, years):
    """compact grouped-bar SVG, imports vs exports over the fiscal years"""
    n = len(years); W = 680; H = 180; pad = 28
    mx = max([*(series_imp or [0]), *(series_exp or [0]), 1])
    bw = (W - pad * 2) / n
    bars = []
    for i in range(n):
        gx = pad + i * bw
        ih = (series_imp[i] / mx) * (H - 40); eh = (series_exp[i] / mx) * (H - 40)
        iw = bw * 0.30
        bars.append('<rect class="tb-imp" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>' % (gx + bw*0.18, H - 22 - ih, iw, ih))
        bars.append('<rect class="tb-exp" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>' % (gx + bw*0.52, H - 22 - eh, iw, eh))
        bars.append('<text class="tb-x" x="%.1f" y="%d" text-anchor="middle">%s</text>' % (gx + bw/2, H - 6, esc(years[i][2:])))
    return ('<div class="tchart"><svg viewBox="0 0 %d %d" role="img" aria-label="Imports and exports by fiscal year">%s</svg>'
            '<div class="tlegend"><span><i class="tb-imp"></i>Imports</span><span><i class="tb-exp"></i>Exports</span></div></div>'
            % (W, H, ''.join(bars)))

def linklist(rows):
    return '<ul class="llist">' + ''.join(
        '<li><a href="%s"><span class="ln">%s</span><span class="lv">%s</span></a></li>' % (href, esc(name), esc(val))
        for href, name, val in rows) + '</ul>'

written = 0
sitemap_urls = []

# ================= COUNTRY PAGES =================
for name in sorted(CO_IMP, key=lambda n: -CO_IMP[n]):
    imp = CO_IMP[name]; exp = CO_EXP.get(name, 0)
    if not (imp or exp):
        continue
    sg = slug(name); path = '/trade/country/' + sg
    bal = exp - imp
    share = (imp / TOT_IMP * 100) if TOT_IMP else 0
    rank = imp_rank.get(name)
    is_saarc = name in SAARC
    tt = S['country_top'].get(name, [[], []])
    cp = S['country_prod'].get(name, [[], None, [], None])
    imp_codes = cp[0] if cp and len(cp) > 0 and isinstance(cp[0], list) else []
    hist = HC.get(name)

    title = 'Nepal–%s trade %s — imports, exports & top products | Customs Nepal' % (name, FY)
    desc = ('Nepal\'s trade with %s in FY %s: imports %s, exports %s. Top import categories, top products (HS codes), '
            '7-year trend%s. Department of Customs data.' % (name, FY, rsf(imp), rsf(exp), ', and SAFTA note' if is_saarc else ''))
    bc = [('Home', '/'), ('Trade data', '/trade-data'), ('Countries', '/trade/countries'), (name, '')]
    ld = [{"@context": "https://schema.org", "@type": "Dataset", "name": "Nepal–%s trade, FY %s" % (name, FY),
           "description": "Nepal's imports from and exports to %s by HS category and product, from the Department of Customs Foreign Trade Statistics." % name,
           "creator": {"@type": "Organization", "name": "Customs Nepal"}, "isAccessibleForFree": True,
           "temporalCoverage": FY, "spatialCoverage": "Nepal; %s" % name, "url": SITE + path}]
    o = [page_head(title, desc, path, bc, ld), crumb_html(bc)]
    o.append('<h1>Nepal–%s trade</h1>' % esc(name))
    o.append('<p class="lede">What Nepal bought from and sold to <b>%s</b> in FY %s, from the Department of Customs '
             'Foreign Trade Statistics. Values in %s.</p>' % (esc(name), esc(FY), esc(UNIT.lower())))
    o.append(tiles([
        ('Imports from ' + name, rsf(imp), ('%.1f%% of Nepal imports · #%s partner' % (share, rank)) if rank else ''),
        ('Exports to ' + name, rsf(exp), ''),
        ('Trade balance', ('+' if bal >= 0 else '−') + rsf(abs(bal)).replace('Rs ', 'Rs '), 'surplus for Nepal' if bal >= 0 else 'deficit for Nepal'),
        ('Two-way trade', rsf(imp + exp), ''),
    ]))
    if is_saarc:
        o.append('<div class="note"><b>%s is a SAARC member.</b> Qualifying goods can be imported at the lower '
                 '<b>SAFTA</b> customs-duty rate with a certificate of origin — often well below the general rate. '
                 'See <a href="/safta">how SAFTA duty works</a>.</div>' % esc(name))
    if hist and len(hist) == len(HY):
        o.append('<h2>7-year trend</h2>')
        o.append(trend_svg([h[0] for h in hist], [h[1] for h in hist], HY))
        rows = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(y), rsf(h[0]), rsf(h[1])) for y, h in zip(HY, hist))
        o.append('<table class="dtable"><thead><tr><th>Fiscal year</th><th>Imports</th><th>Exports</th></tr></thead><tbody>%s</tbody></table>' % rows)
    if tt[0]:
        o.append('<h2>Top import categories from %s</h2>' % esc(name))
        o.append(linklist([('/trade/category/%02d' % ch, '%s (Ch %d)' % (CHSHORT.get(ch, ''), ch), rsf(v)) for ch, v in tt[0][:12]]))
    if len(tt) > 1 and tt[1]:
        o.append('<h2>Top export categories to %s</h2>' % esc(name))
        o.append(linklist([('/trade/category/%02d' % ch, '%s (Ch %d)' % (CHSHORT.get(ch, ''), ch), rsf(v)) for ch, v in tt[1][:12]]))
    if imp_codes:
        o.append('<h2>Top products imported from %s</h2>' % esc(name))
        rr = ''.join('<tr><td class="mono"><a href="/#hs-%s">%s</a></td><td>%s</td><td>%s</td></tr>'
                     % (dotted(c[0]), dotted(c[0]), esc((S['imports'].get(re.sub(r'\D','',str(c[0])), ['', ])[0] or '')[:70]), rsf(c[1]))
                     for c in imp_codes[:20])
        o.append('<table class="dtable"><thead><tr><th>HS code</th><th>Product</th><th>Import value</th></tr></thead><tbody>%s</tbody></table>' % rr)
    o.append('<div class="cta"><a class="btn" href="/trade-data">Open the interactive trade explorer</a> '
             '<a class="btn ghost" href="/calculator">Estimate landed cost &amp; duty</a></div>')
    o.append('<p class="fine">Trade value ≠ retail price, and HS classification is decided by customs. '
             'Confirm the exact line before pricing a shipment.</p>')
    o.append(FOOT)
    (pub / 'trade' / 'country' / (sg + '.html')).write_text(''.join(o), encoding='utf-8')
    sitemap_urls.append((path, '0.6'))
    written += 1

# ================= CATEGORY PAGES =================
for ch in sorted(CH_IMP, key=lambda c: -CH_IMP[c]):
    imp = CH_IMP[ch]; exp = CH_EXP.get(ch, 0)
    if not (imp or exp):
        continue
    nn = '%02d' % ch; path = '/trade/category/' + nn
    short = CHSHORT.get(ch, ''); full = chapters_full.get(ch, short)
    share = (imp / TOT_IMP * 100) if TOT_IMP else 0
    rank = chimp_rank.get(ch)
    dl = duty_label(ch)
    hist = HCH.get(str(ch))
    srcs = sorted(ch_sources.get(ch, []), key=lambda x: -x[1])[:12]
    dests = sorted(ch_dest.get(ch, []), key=lambda x: -x[1])[:10]
    topcodes = sorted([(k, v) for k, v in S['imports'].items() if k[:2] == nn], key=lambda x: -(x[1][2] or 0))[:20]

    title = 'Nepal %s imports & exports %s (HS Chapter %d) | Customs Nepal' % (short, FY, ch)
    desc = ('Nepal %s trade in FY %s: imports %s, exports %s. Top source countries, top products (HS codes), import '
            'duty%s, 7-year trend. HS Chapter %d — Department of Customs data.'
            % (short, FY, rsf(imp), rsf(exp), (' ' + dl if dl else ''), ch))
    bc = [('Home', '/'), ('Trade data', '/trade-data'), ('Categories', '/trade/categories'), (short, '')]
    ld = [{"@context": "https://schema.org", "@type": "Dataset", "name": "Nepal %s trade (HS Chapter %d), FY %s" % (short, ch, FY),
           "description": "Nepal's imports and exports of %s (HS Chapter %d) by source country and product." % (full or short, ch),
           "creator": {"@type": "Organization", "name": "Customs Nepal"}, "isAccessibleForFree": True,
           "temporalCoverage": FY, "spatialCoverage": "Nepal", "url": SITE + path}]
    o = [page_head(title, desc, path, bc, ld), crumb_html(bc)]
    o.append('<h1>Nepal %s — imports &amp; exports</h1>' % esc(short))
    o.append('<p class="lede"><b>HS Chapter %d</b> · %s. What Nepal imported and exported in this category in FY %s, '
             'from the Department of Customs Foreign Trade Statistics.</p>' % (ch, esc(full or short), esc(FY)))
    o.append(tiles([
        ('Imports', rsf(imp), ('%.1f%% of Nepal imports · #%s category' % (share, rank)) if rank else ''),
        ('Exports', rsf(exp), ''),
        ('Import duty (general)', dl or '—', 'see full tariff'),
        ('Two-way trade', rsf(imp + exp), ''),
    ]))
    o.append('<div class="cta"><a class="btn" href="/tariff/%s">See duty for every HS code in Chapter %d</a> '
             '<a class="btn ghost" href="/calculator">Landed-cost calculator</a></div>' % (nn, ch))
    if hist and len(hist) == len(HY):
        o.append('<h2>7-year trend</h2>')
        o.append(trend_svg([h[0] for h in hist], [h[1] for h in hist], HY))
        rows = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(y), rsf(h[0]), rsf(h[1])) for y, h in zip(HY, hist))
        o.append('<table class="dtable"><thead><tr><th>Fiscal year</th><th>Imports</th><th>Exports</th></tr></thead><tbody>%s</tbody></table>' % rows)
    if srcs:
        o.append('<h2>Top source countries (imports)</h2>')
        o.append(linklist([('/trade/country/' + slug(co), co, rsf(v)) for co, v in srcs]))
    if dests:
        o.append('<h2>Top export destinations</h2>')
        o.append(linklist([('/trade/country/' + slug(co), co, rsf(v)) for co, v in dests]))
    if topcodes:
        o.append('<h2>Top imported products in this category</h2>')
        rr = ''.join('<tr><td class="mono"><a href="/#hs-%s">%s</a></td><td>%s</td><td>%s</td></tr>'
                     % (dotted(k), dotted(k), esc((v[0] or '')[:70]), rsf(v[2])) for k, v in topcodes)
        o.append('<table class="dtable"><thead><tr><th>HS code</th><th>Product</th><th>Import value</th></tr></thead><tbody>%s</tbody></table>' % rr)
    o.append('<p class="fine">Trade value ≠ retail price. The duty shown is the general customs-duty range; VAT (usually '
             '13%%) and any excise are extra. HS classification is decided by customs — confirm the exact line in the '
             '<a href="/tariff/%s">tariff</a> before pricing.</p>' % nn)
    o.append(FOOT)
    (pub / 'trade' / 'category' / (nn + '.html')).write_text(''.join(o), encoding='utf-8')
    sitemap_urls.append((path, '0.6'))
    written += 1

# ================= INDEX PAGES =================
def index_page(path, title, desc, h1, lede, rows, crumb_last):
    bc = [('Home', '/'), ('Trade data', '/trade-data'), (crumb_last, '')]
    o = [page_head(title, desc, path, bc), crumb_html(bc), '<h1>%s</h1>' % esc(h1), '<p class="lede">%s</p>' % lede]
    o.append(linklist(rows))
    o.append(FOOT)
    (pub / (path.strip('/') + '.html')).write_text(''.join(o), encoding='utf-8')

co_rows = [('/trade/country/' + slug(n), n, rsf(CO_IMP[n] + CO_EXP.get(n, 0)))
           for n in sorted(CO_IMP, key=lambda n: -(CO_IMP[n] + CO_EXP.get(n, 0))) if CO_IMP[n] or CO_EXP.get(n, 0)]
index_page('/trade/countries', 'Nepal trade by country %s — every trading partner | Customs Nepal' % FY,
           'Nepal\'s imports and exports with every trading-partner country in FY %s. Open any country for its top products, categories and 7-year trend.' % FY,
           'Nepal trade by country', 'Every country Nepal traded with in FY %s, by two-way trade. Open any for its top imports, exports, products and trend.' % esc(FY),
           co_rows, 'Countries')

ch_rows = [('/trade/category/%02d' % ch, '%s (Ch %d)' % (CHSHORT.get(ch, ''), ch), rsf(CH_IMP[ch] + CH_EXP.get(ch, 0)))
           for ch in sorted(CH_IMP, key=lambda c: -(CH_IMP[c] + CH_EXP.get(c, 0))) if CH_IMP[ch] or CH_EXP.get(ch, 0)]
index_page('/trade/categories', 'Nepal trade by category %s — every HS chapter | Customs Nepal' % FY,
           'Nepal\'s imports and exports by HS category (chapter) in FY %s, with import duty. Open any category for its source countries, products and trend.' % FY,
           'Nepal trade by category', 'Every HS category Nepal traded in FY %s, by two-way trade. Open any for its source countries, top products, duty and trend.' % esc(FY),
           ch_rows, 'Categories')

# ---------------- append styles to seo.css ----------------
TRADECSS = """
.lede{font-size:1.05rem;color:var(--fg-2);line-height:1.5;margin:.2em 0 1.2em;max-width:62ch}
.tgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--border);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin:1em 0 1.4em}
.tile{background:var(--card);padding:14px 16px}
.tile .tl{display:block;font-size:.78rem;color:var(--muted);font-weight:600}
.tile .tv{display:block;font-size:1.28rem;font-weight:800;letter-spacing:-.02em;margin:.1em 0}
.tile .ts{display:block;font-size:.76rem;color:var(--fg-2)}
.tchart{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 10px 8px;margin:.4em 0 1em}
.tchart svg{width:100%;height:auto;display:block}
.tb-imp{fill:var(--accent)}
.tb-exp{fill:var(--free,#1a9e5f)}
.tb-x{fill:var(--muted);font-size:11px}
.tlegend{display:flex;gap:16px;justify-content:center;font-size:.8rem;color:var(--fg-2);margin-top:4px}
.tlegend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.tlegend .tb-imp{background:var(--accent)}
.tlegend .tb-exp{background:var(--free,#1a9e5f)}
.dtable{width:100%;border-collapse:collapse;font-size:.9rem;margin:.3em 0 1.3em}
.dtable th,.dtable td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--border)}
.dtable th{font-size:.76rem;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
.dtable td:last-child,.dtable th:last-child{text-align:right;white-space:nowrap}
.dtable td.mono{font-family:var(--mono);white-space:nowrap}
.dtable td.mono a{text-decoration:none;color:var(--accent)}
.llist{list-style:none;padding:0;margin:.2em 0 1.4em;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.llist a{display:flex;justify-content:space-between;gap:10px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 13px;text-decoration:none;color:var(--fg)}
.llist a:hover{border-color:var(--accent)}
.llist .ln{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.llist .lv{font-weight:700;white-space:nowrap;color:var(--fg-2)}
.note{background:var(--accent-bg);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:12px;padding:12px 15px;margin:1em 0 1.3em;font-size:.95rem}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:1em 0 1.4em}
.cta .btn{display:inline-block;background:var(--accent);color:#fff;font-weight:700;font-size:.92rem;padding:11px 18px;border-radius:12px;text-decoration:none}
.cta .btn.ghost{background:transparent;color:var(--accent);border:1.5px solid var(--border)}
"""
css_path = pub / 'seo.css'
cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
if '.tgrid{' not in cur:
    css_path.write_text(cur + '\n' + TRADECSS.strip() + '\n', encoding='utf-8')

# ---------------- inject URLs into sitemap.xml ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows = ['  <url><loc>%s/trade/countries</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, TODAY),
        '  <url><loc>%s/trade/categories</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, TODAY)]
for path, pr in sitemap_urls:
    rows.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>' % (SITE, path, TODAY, pr))
if '/trade/countries</loc>' not in sm:
    sm = sm.replace('</urlset>', '\n'.join(rows) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('trade_pages: %d pages (countries + categories) + 2 index pages; styles + %d sitemap URLs' % (written, len(sitemap_urls) + 2))
