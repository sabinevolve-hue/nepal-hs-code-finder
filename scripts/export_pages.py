"""Nepal Export Guides — static, crawlable SEO pages on customsnepal.com (the authoritative
Nepal domain), one per signature export product, plus an /export hub. Trade figures are baked
in at build time from the world data (BACI 2024); the interactive drill-down lives on the world
site and is linked. Mirrors seo_pages.py (same header/nav/canonical/GA/seo.css).

Emits into public/:
  /export            (export.html)            hub: Nepal export overview + guide grid + explorer CTA
  /export/<slug>     (export/<slug>.html)     one guide per product (data + how-to-export)
Appends export styles to /seo.css and the new URLs to /sitemap.xml.

Run after seo_pages.py:  python3 scripts/export_pages.py
"""
import pathlib, json, datetime, html

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'export').mkdir(parents=True, exist_ok=True)

NEP = json.loads((root / 'world/data/nepal.json').read_text(encoding='utf-8'))
PROD = json.loads((root / 'world/data/prod.json').read_text(encoding='utf-8'))
HS = json.loads((root / 'world/data/hs.json').read_text(encoding='utf-8'))
TRADE = json.loads((root / 'world/data/trade.json').read_text(encoding='utf-8'))
HSDESC = {s[0]: s[1] for s in HS['subs']}
ISO = {c['iso']: c['name'] for c in TRADE['countries']}

SITE = 'https://www.customsnepal.com'
WORLD = '/world/nepal/exports'           # interactive explorer (same domain, subdirectory)
TODAY = datetime.date.today().isoformat()

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def money(m):
    if m is None:
        return '—'
    m = float(m)
    if m >= 1000:
        return '$%.1fB' % (m / 1000)
    return '$%dM' % round(m)

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")
from nav import render_nav

def page_head(title, desc, path, breadcrumb, extra_ld=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = render_nav(path, esc)
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
        '<p><b>Trade figures:</b> BACI (CEPII), reconciled from UN Comtrade, 2024 — merchandise exports at HS-6, '
        'current US$. <b>Export procedure</b> is general guidance; incentive rates, GSP/preference eligibility and '
        'certification rules change — confirm current terms with the <a href="https://tepc.gov.np" target="_blank" rel="noopener noreferrer">Trade &amp; Export Promotion Centre (TEPC)</a>, '
        'the <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs</a> and the '
        '<a href="https://nepaltradeportal.gov.np" target="_blank" rel="noopener noreferrer">Nepal Trade Information Portal</a> before you ship.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/export">Export guides</a> · <a href="' + WORLD + '">Export Explorer</a> · '
        '<a href="/tariff">Tariff</a> · <a href="/faq">FAQ</a> · © customsnepal.com</p></div></footer>'
        '</body></html>')

# ---------------- guide content (prose; stats computed from data) ----------------
GUIDES = {
 'carpets': dict(hs='570110', name='Woollen carpets', emoji='\U0001F9F6',
   h1='Exporting hand-knotted woollen carpets from Nepal',
   lede="Nepal's flagship manufactured export — hand-knotted Tibetan-Nepali woollen carpets. Who buys them, and how to ship.",
   about="Hand-knotted woollen carpets are made around the Kathmandu Valley (Jawalakhel, Boudha, Sankhu) and are one of Nepal's larger formal-sector employers.",
   position="The United States is by far the largest market, followed by Germany, the UK and other EU countries. Western buyers increasingly require child-labour-free certification (GoodWeave), so that certification is effectively part of market access.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Certificate of origin","From a chamber of commerce or TEPC; a GSP Form A where the destination grants Nepal preferential access (confirm current eligibility)."),
          ("GoodWeave / quality certification","Child-labour-free certification, valued or required by most Western importers."),
          ("File the export declaration","Clear through customs — usually air or sea freight via Kolkata/Haldia.")],
   sources="Nepal Carpet Exporters' Association, TEPC, Department of Customs."),
 'cardamom': dict(hs='090831', name='Large cardamom', emoji='\U0001F33F',
   h1='Exporting large cardamom (alaichi) from Nepal',
   lede="Nepal is the world's largest producer of large (black) cardamom. The trade picture and how to ship it.",
   about="Large cardamom (Amomum subulatum), known locally as alaichi, is grown in the eastern hill districts — Taplejung, Panchthar, Ilam and Sankhuwasabha. Nepal is the world's top producer.",
   position="Almost all of Nepal's crop goes to India, which consumes it and re-exports onward. Because the market is so India-concentrated, prices swing with Indian demand and with how the India-Nepal trade treaty treats the product in a given year.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Phytosanitary certificate","From the National Plant Quarantine Program — required for agricultural produce."),
          ("Certificate of origin","From a chamber or TEPC (a SAARC/SAFTA certificate for shipments to India)."),
          ("Grading & quality","To the buyer's specification — moisture, size, cleanliness."),
          ("File the export declaration","Clear at the border / dry port.")],
   sources="TEPC, Department of Customs, National Plant Quarantine Program."),
 'tea': dict(hs='090240', name='Tea', emoji='\U0001F375',
   h1='Exporting tea from Nepal',
   lede="Himalayan orthodox tea from the eastern hills — bulk to India, premium leaf to Europe and Japan.",
   about="Nepali tea is grown mainly in Ilam and the eastern hills, bordering the Darjeeling belt. It splits into high-volume CTC tea and higher-value orthodox (whole-leaf) tea.",
   position="Most volume goes to India, often re-blended and re-exported. The real value opportunity is premium orthodox tea sold direct to specialty buyers in Germany, the EU, Japan and the US — where origin and quality command far higher prices.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Phytosanitary certificate","From the National Plant Quarantine Program."),
          ("Certificate of origin & quality","Chamber/TEPC certificate; orthodox grading and, increasingly, the Nepal Tea collective-trademark / origin story for premium buyers."),
          ("File the export declaration","Clear through customs.")],
   sources="National Tea & Coffee Development Board, TEPC, Department of Customs."),
 'pashmina': dict(hs='621420', name='Pashmina shawls', emoji='\U0001F9E3',
   h1='Exporting pashmina shawls & scarves from Nepal',
   lede="Nepali pashmina — fine Himalayan cashmere, a high-value fashion export. Markets and how to ship.",
   about="Pashmina is woven from the fine undercoat of the Himalayan mountain goat (Chyangra). Nepal protects authentic product under the Chyangra Pashmina trademark/GI. It is a high-value, low-volume export (one of the highest $/kg in Nepal's basket).",
   position="France, Germany, the US, China and Switzerland lead — fashion and luxury buyers. Authenticity matters: the Chyangra Pashmina mark separates genuine Nepali pashmina from cheaper blends and is a selling point in Western markets.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Chyangra Pashmina certification","Through the Nepal Pashmina Industries Association — authenticity / GI trademark valued by premium buyers."),
          ("Certificate of origin","Chamber/TEPC; GSP/preference where the destination grants it."),
          ("File the export declaration","Usually air freight for this high-value, low-weight product.")],
   sources="Nepal Pashmina Industries Association, TEPC, Department of Customs."),
 'dog-chew': dict(hs='230910', name='Himalayan dog chew', emoji='\U0001F436',
   h1='Exporting Himalayan dog chews (churpi) from Nepal',
   lede="The hardened yak-milk chew that became a booming Nepali export to Western pet markets.",
   about="Himalayan dog chews are made from churpi — hard cheese traditionally made from yak or cow milk. Marketed as a long-lasting, natural dog treat, they have grown fast as a premium pet product in the US.",
   position="The United States dominates, with Canada next. This is one of Nepal's most dynamic newer exports — a traditional Himalayan food turned into a Western pet-care niche.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Veterinary / health certificate","As an animal-origin product, a health certificate (Department of Livestock Services) is needed."),
          ("Importing-country pet-food compliance","US FDA / destination pet-food import rules, labelling and facility requirements."),
          ("Certificate of origin","Chamber/TEPC."),
          ("File the export declaration","Clear through customs.")],
   sources="Department of Livestock Services, TEPC, Department of Customs; destination pet-food regulator (e.g. US FDA)."),
 'herbs': dict(hs='121190', name='Herbs & medicinal plants', emoji='\U0001F33F',
   h1='Exporting medicinal & aromatic plants (herbs) from Nepal',
   lede="Nepal's Himalayan herbs and jadibuti — a large natural-products export with real compliance to watch.",
   about="Medicinal and aromatic plants (MAPs) — jadibuti — are gathered and cultivated across Nepal's hills and high mountains and used in herbal, cosmetic and pharmaceutical supply chains.",
   position="India is the dominant buyer, with onward demand across Asia. The critical compliance point: many high-value Himalayan species are CITES-listed, so protected-species permits are required — and some species are collection-restricted.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("CITES permit where applicable","For protected / endangered species, a CITES export permit (Department of Forests) is mandatory."),
          ("Phytosanitary certificate","From the National Plant Quarantine Program."),
          ("Certificate of origin","Chamber/TEPC."),
          ("File the export declaration","Clear through customs.")],
   sources="Department of Forests (CITES), National Plant Quarantine Program, TEPC, Department of Customs."),
 'noodles': dict(hs='190230', name='Instant noodles', emoji='\U0001F35C',
   h1='Exporting instant noodles from Nepal',
   lede="Packaged noodles are one of Nepal's manufactured-food success stories. Markets and food-safety steps.",
   about="Instant and packaged noodles are made by Nepal's larger food manufacturers and have built a real export presence, helped by diaspora demand and brand recognition.",
   position="India, Japan and Australia lead — a mix of regional trade and diaspora markets. For a processed food, destination food-safety and labelling compliance is the make-or-break step.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Food-safety certification","From the Department of Food Technology & Quality Control (DFTQC); destination food-import and labelling rules (and halal where relevant)."),
          ("Certificate of origin","Chamber/TEPC."),
          ("File the export declaration","Clear through customs.")],
   sources="Department of Food Technology & Quality Control (DFTQC), TEPC, Department of Customs."),
 'jute': dict(hs='630510', name='Jute sacks & bags', emoji='\U0001FAA2',
   h1='Exporting jute sacks & bags from Nepal',
   lede="Jute goods from the eastern Terai mills — a traditional industry, sold mainly to India.",
   about="Jute sacks and bags are produced by Nepal's jute mills, concentrated in the eastern Terai (Biratnagar). Jute is a long-standing industrial export using domestic and imported raw fibre.",
   position="India is overwhelmingly the main buyer. Demand tracks Indian packaging needs and the duty treatment under the India-Nepal trade regime.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Certificate of origin","Chamber/TEPC; a SAFTA certificate for India."),
          ("Quality to buyer spec","Weave, weight and sizing to the packaging buyer's standard."),
          ("File the export declaration","Clear at the border.")],
   sources="TEPC, Department of Customs, Nepal jute industry associations."),
 'knitwear': dict(hs='611012', name='Woollen knitwear', emoji='\U0001F9E5',
   h1='Exporting woollen & pashmina knitwear from Nepal',
   lede="Sweaters and cardigans in wool and fine animal hair — a high-value fashion export to Europe.",
   about="Knitted jerseys, pullovers and cardigans of wool or fine animal hair are a skilled, high-value garment export — often overlapping with the pashmina and felt craft sectors.",
   position="Germany, France, the UK, the US and Italy lead — fashion buyers paying a strong per-kg price for quality and origin.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Certificate of origin","Chamber/TEPC; GSP / EU EBA preference where the destination grants it (confirm current eligibility)."),
          ("Quality & labelling","Fibre-content and care labelling to destination rules."),
          ("File the export declaration","Clear through customs.")],
   sources="Garment Association Nepal, TEPC, Department of Customs."),
 'felt': dict(hs='560290', name='Wool felt products', emoji='\U0001F9F6',
   h1='Exporting wool felt products from Nepal',
   lede="Handmade Nepali felt — balls, slippers, home and pet decor — a growing craft export to the West.",
   about="Wool felt products are handmade from sheep wool: felt balls and rugs, slippers, soft toys, pet beds and home decor. It is a craft-and-design niche with a strong fair-trade story.",
   position="The US, the Netherlands, the UK and Germany lead — craft, home-decor and pet markets. Fair-trade and handmade positioning is central to the product's appeal.",
   steps=[("Register for an EXIM code","One-time exporter registration with the Department of Customs."),
          ("Certificate of origin","Chamber/TEPC; fair-trade certification where buyers ask for it."),
          ("Quality to buyer spec","Colour-fastness, sizing and finish for retail buyers."),
          ("File the export declaration","Clear through customs.")],
   sources="Fair Trade Group Nepal, TEPC, Department of Customs."),
}
ORDER = ['carpets', 'cardamom', 'tea', 'pashmina', 'dog-chew', 'herbs', 'noodles', 'jute', 'knitwear', 'felt']

def guide_stats(hs):
    z = NEP.get(hs, {}); p = PROD.get(hs, {})
    dests = [(d[0], d[1]) for d in z.get('exs', []) if d[1] > 0][:5]
    return z.get('ex'), p.get('w'), p.get('u'), dests

def tiles(nep, world, price):
    return ('<div class="exstats">'
            '<div class="extile"><b>%s</b><span>Nepal exports (2024)</span></div>'
            '<div class="extile"><b>%s</b><span>World market</span></div>'
            '<div class="extile"><b>%s</b><span>World price</span></div></div>'
            % (money(nep), money(world), ('$%s/kg' % price) if price else '—'))

def dest_list(dests):
    if not dests:
        return '<p>—</p>'
    rows = ''.join('<li><a href="%s/%s">%s</a> — %s</li>' % (WORLD, iso.lower(), esc(ISO.get(iso, iso)), money(v)) for iso, v in dests)
    return '<ul class="exdest">' + rows + '</ul>'

# ---------------- guide pages ----------------
for slug in ORDER:
    g = GUIDES[slug]
    hs = g['hs']
    nep, world, price, dests = guide_stats(hs)
    path = '/export/' + slug
    title = g['h1'] + ' — Customs Nepal'
    if len(title) > 66:
        title = 'Export ' + g['name'] + ' from Nepal — markets & how-to | Customs Nepal'
    desc = ('%s Nepal exported about %s in 2024 (world market %s). Top buyers, world price and a step-by-step '
            'export guide.' % (g['lede'], money(nep), money(world)))
    bc = [('Home', '/'), ('Export guides', '/export'), (g['name'], '')]
    howto = {"@context": "https://schema.org", "@type": "HowTo",
             "name": g['h1'], "description": g['lede'],
             "step": [{"@type": "HowToStep", "name": s[0], "text": s[1]} for s in g['steps']]}
    out = [page_head(title, desc, path, bc, extra_ld=[howto]), crumb_html(bc)]
    out.append('<h1>%s %s</h1>' % (g['emoji'], esc(g['h1'])))
    out.append('<p class="lede">%s</p>' % esc(g['lede']))
    out.append(tiles(nep, world, price))
    out.append('<h2 class="sec">About the product</h2><p>%s</p>' % esc(g['about']))
    out.append('<h2 class="sec">Nepal’s position</h2><p>%s</p>' % esc(g['position']))
    out.append('<h2 class="sec">How to export from Nepal</h2><ol class="exsteps">')
    for s in g['steps']:
        out.append('<li><b>%s</b> — %s</li>' % (esc(s[0]), esc(s[1])))
    out.append('</ol>')
    out.append('<h2 class="sec">Where Nepal sells it (2024)</h2>%s' % dest_list(dests))
    out.append('<div class="tools"><a class="btn" href="%s">Open the live Export Explorer</a>'
               '<a class="btn ghost" href="/#hs-%s">HS %s.%s — duty &amp; classification</a></div>'
               % (WORLD, hs, hs[:4], hs[4:]))
    # related guides
    rel = [s for s in ORDER if s != slug][:4]
    out.append('<h2 class="sec">More export guides</h2><div class="guidegrid">')
    for s in rel:
        out.append('<a class="chcard" href="/export/%s"><span class="t">%s %s</span>'
                   '<span class="c">Export guide + data</span></a>' % (s, GUIDES[s]['emoji'], esc(GUIDES[s]['h1'].replace('Exporting ', '').replace(' from Nepal', ''))))
    out.append('</div>')
    out.append('<p class="fineprint">Trade figures are indicative (BACI / UN Comtrade, 2024). For official 8-digit, '
               'fiscal-year figures see the Department of Customs and TEPC.</p>')
    out.append('</div>' + FOOT)
    (pub / 'export' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')

# ---------------- hub ----------------
tex = NEP.get('_t', {}).get('ex', 0)
X_cc = {}
for k, v in NEP.items():
    if k.startswith('_'):
        continue
    for d in v.get('exs', []):
        if d[1] > 0:
            X_cc[d[0]] = X_cc.get(d[0], 0) + d[1]
top_dests = sorted(X_cc.items(), key=lambda x: -x[1])[:10]
india = round((X_cc.get('IND', 0) / tex) * 100) if tex else 0

title = 'Nepal Export Guides — what Nepal exports & how to ship it | Customs Nepal'
desc = ('Nepal exported about %s of goods in 2024. Export guides for carpets, cardamom, tea, pashmina, dog chews, '
        'herbs, noodles, jute, knitwear and felt — markets, world prices and how to export.' % money(tex))
bc = [('Home', '/'), ('Export guides', '')]
out = [page_head(title, desc, '/export', bc), crumb_html(bc)]
out.append('<h1>Nepal export guides</h1>')
out.append('<p class="lede">Nepal exported about <b>%s</b> of merchandise in 2024. These guides cover its signature '
           'exports — who buys them around the world, the price they fetch, and how to export from Nepal — with a '
           'live, interactive <a href="%s">Export Explorer</a> for the full country-by-country, product-by-product data.</p>'
           % (money(tex), WORLD))
out.append('<div class="exstats">'
           '<div class="extile"><b>%s</b><span>Total exports (2024)</span></div>'
           '<div class="extile"><b>%d%%</b><span>Goes to India</span></div>'
           '<div class="extile"><b>%d</b><span>Guides</span></div></div>' % (money(tex), india, len(ORDER)))
out.append('<div class="note">%d%% of Nepal’s exports go to India — much of it refined soybean &amp; palm oil '
           're-exported after processing, a duty-driven flow rather than domestic production. The real manufactured '
           'and agri exports below are spread across the US, the EU and beyond.</div>' % india)
out.append('<h2 class="sec">Export guides by product</h2><div class="guidegrid">')
for slug in ORDER:
    g = GUIDES[slug]
    nep, world, price, dests = guide_stats(g['hs'])
    out.append('<a class="chcard" href="/export/%s"><span class="t">%s %s</span>'
               '<span class="c">Nepal exports %s · HS %s.%s</span></a>'
               % (slug, g['emoji'], esc(g['name']), money(nep), g['hs'][:4], g['hs'][4:]))
out.append('</div>')
out.append('<h2 class="sec">Explore by market</h2>'
           '<p>Nepal’s biggest export destinations — open any market for every product Nepal ships there:</p>'
           '<ul class="exdest">')
for iso, v in top_dests:
    out.append('<li><a href="%s/%s">%s</a> — %s</li>' % (WORLD, iso.lower(), esc(ISO.get(iso, iso)), money(v)))
out.append('</ul>')
out.append('<div class="tools"><a class="btn" href="%s">Open the full Export Explorer</a>'
           '<a class="btn ghost" href="/exports">Nepal export statistics</a></div>' % WORLD)
out.append('</div>' + FOOT)
(pub / 'export.html').write_text(''.join(out), encoding='utf-8')

# ---------------- append styles to seo.css ----------------
EXCSS = """
.exstats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:1.2em 0}
.extile{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.extile b{display:block;font-size:1.3rem;letter-spacing:-.01em;color:var(--accent)}
.extile span{font-size:.78rem;color:var(--muted)}
ol.exsteps{margin:.4em 0 1em;padding-left:22px;line-height:1.7}
ol.exsteps li{margin-bottom:7px}
ul.exdest{list-style:none;margin:.4em 0 1em;padding:0}
ul.exdest li{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)}
.guidegrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin:.6em 0 1.4em}
.fineprint{font-size:.8rem;color:var(--muted);margin:1.4em 0}
"""
css_path = pub / 'seo.css'
cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
if '.exstats{' not in cur:
    css_path.write_text(cur + '\n' + EXCSS.strip() + '\n', encoding='utf-8')

# ---------------- inject URLs into sitemap.xml ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows = ['  <url><loc>%s/export</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>' % (SITE, TODAY)]
for slug in ORDER:
    rows.append('  <url><loc>%s/export/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, slug, TODAY))
if '/export</loc>' not in sm:
    sm = sm.replace('</urlset>', '\n'.join(rows) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('export_pages: %d guides + hub; styles + %d sitemap URLs' % (len(ORDER), len(ORDER) + 1))
