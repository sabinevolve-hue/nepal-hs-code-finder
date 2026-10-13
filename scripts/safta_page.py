"""SAFTA page — static, crawlable SEO page on customsnepal.com explaining the SAFTA / SAARC
preferential import duty for Nepal, with a DATA-BACKED "where SAFTA actually saves you money"
map computed at build time from data/tariff.json (the same general-vs-SAARC rates shown across
the site). Mirrors seo_pages.py / export_pages.py / shipping_pages.py.

Emits public/safta.html. Appends nothing new to seo.css (reuses existing classes + duty badges);
injects one URL into public/sitemap.xml.

Run after shipping_pages.py:  python3 scripts/safta_page.py
"""
import pathlib, json, datetime, html, statistics

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

# ---------------- data: compute SAFTA benefit from the tariff ----------------
rows = json.load(open(root / 'data/tariff.json', encoding='utf-8'))
if isinstance(rows, dict):
    rows = rows.get('rows') or rows.get('data') or list(rows.values())

def num(x):
    if x is None:
        return None
    s = str(x).strip().replace('%', '')
    if s.lower() in ('free', 'nil'):
        return 0.0
    try:
        return float(s)
    except Exception:
        return None  # specific / compound rate — skip

# auto-detect which column is general vs SAARC (general rate >= SAARC on average)
c4 = [num(r[4]) for r in rows if len(r) > 5]
c5 = [num(r[5]) for r in rows if len(r) > 5]
m4 = statistics.mean([v for v in c4 if v is not None])
m5 = statistics.mean([v for v in c5 if v is not None])
GEN, SAA = (5, 4) if m5 > m4 else (4, 5)

SEG = [("Instruments & medical", 90, 92), ("Furniture, lighting & toys", 94, 96),
       ("Base metals & steel", 72, 83),
       ("Footwear & headgear", 64, 67), ("Wood, paper & print", 44, 49),
       ("Stone, glass, gems & jewellery", 68, 71), ("Agriculture & food", 1, 24),
       ("Chemicals & pharmaceuticals", 28, 38), ("Minerals & fuels", 25, 27),
       ("Plastics & rubber", 39, 40), ("Vehicles & transport", 86, 89),
       ("Textiles & garments", 50, 63), ("Machinery & electronics", 84, 85),
       ("Leather & hides", 41, 43)]
def seg_of(ch):
    for name, a, b in SEG:
        if a <= ch <= b:
            return name
    return None

agg = {name: {'cmp': 0, 'g': 0.0, 's': 0.0, 'big': 0, 'free': 0, 'nob': 0} for name, _, _ in SEG}
prod = []  # (margin, code, desc, gen, saa)
for r in rows:
    if len(r) < 6:
        continue
    try:
        ch = int(str(r[0])[:2])
    except Exception:
        continue
    name = seg_of(ch)
    if not name:
        continue
    g = num(r[GEN]); s = num(r[SAA])
    if g is None or s is None:
        continue
    d = agg[name]; d['cmp'] += 1; d['g'] += g; d['s'] += s
    m = g - s
    if m >= 10:
        d['big'] += 1
        prod.append((m, str(r[0]), str(r[1]), g, s))
    if s == 0:
        d['free'] += 1
    if m <= 0:
        d['nob'] += 1

tot_cmp = sum(d['cmp'] for d in agg.values())
avg_gen = sum(d['g'] for d in agg.values()) / tot_cmp
avg_saa = sum(d['s'] for d in agg.values()) / tot_cmp
n_big = len(prod)
n_free = sum(d['free'] for d in agg.values())

seg_rows = []
for name, _, _ in SEG:
    d = agg[name]
    if d['cmp'] == 0:
        continue
    gav = d['g'] / d['cmp']; sav = d['s'] / d['cmp']; margin = gav - sav
    nob = 100 * d['nob'] / d['cmp']
    if margin >= 3.5 and nob < 60:
        tier = ('Strong', 'd-free')
    elif nob >= 70 or margin < 2:
        tier = ('Limited', 'd-hi')
    else:
        tier = ('Selective', 'd-mid')
    seg_rows.append((margin, name, gav, sav, d['big'], nob, tier))
seg_rows.sort(reverse=True)

# top individual saving products (dedup by code, biggest margin first)
prod.sort(reverse=True)
seen = set(); top = []
for m, code, desc, g, s in prod:
    if code in seen:
        continue
    seen.add(code); top.append((m, code, desc, g, s))
    if len(top) >= 40:
        break

def fmtpct(x):
    return ('Free' if x == 0 else (('%g' % x) + '%'))

# ---------------- page shell (mirrors the other generators) ----------------
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

def page_head(title, desc, path, breadcrumb, extra_ld=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = ''.join('<a href="%s"%s>%s</a>' % (h, ' class="cur"' if (path == h) else '', esc(l)) for h, l in NAV)
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
        '<a class="logo" href="/" aria-label="Customs Nepal — home"><span class="mark">HS</span><span class="lt">Nepal HS Code Finder<small>Customs Tariff 2026/27</small></span></a>'
        '<nav class="topnav">' + nav + '</nav></div></header>'
        '<div class="wrap">'
    )

def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'

FOOT = ('<footer><div class="wrap">'
        '<p><b>Preferential (SAARC/SAFTA) rates</b> are shown as printed in the Nepal Customs Tariff 2026/27 and apply '
        '<b>only</b> to goods from a SAARC country that carry a valid SAFTA Certificate of Origin, meet the Rules of '
        'Origin, and are not on Nepal’s Sensitive List. Rules of Origin, Sensitive Lists and LDC provisions change '
        '— confirm current terms with the <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer nofollow">Department of Customs</a> and the '
        '<a href="https://www.saarc-sec.org" target="_blank" rel="noopener noreferrer nofollow">SAARC Secretariat</a> before you import.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal or SAARC.</p>'
        '<p><a href="/">Home</a> · <a href="/safta">SAFTA</a> · <a href="/imports">Imports</a> · <a href="/calculator">Landed-cost calculator</a> · '
        '<a href="/tariff">Tariff</a> · <a href="/faq">FAQ</a> · © customsnepal.com</p></div></footer>'
        '</body></html>')

MEMBERS = "Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan and Sri Lanka"

# ---------------- build the page ----------------
title = 'SAFTA: lower import duty from South Asia — Nepal guide | Customs Nepal'
desc = ('How SAFTA (the SAARC free-trade area) cuts Nepal import duty — which products actually benefit, how much you '
        'save, and how to claim the rate with a SAFTA Certificate of Origin and Rules of Origin. Data from the Nepal '
        'Customs Tariff.')
bc = [('Home', '/'), ('SAFTA', '')]

faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": "Does SAFTA make all imports into Nepal cheaper?",
     "acceptedAnswer": {"@type": "Answer", "text": "No. SAFTA gives a lower (preferential) customs duty only on goods from a SAARC country that carry a valid SAFTA Certificate of Origin, meet the Rules of Origin, and are not on Nepal's Sensitive List. Across the tariff the average gap is about %.0f%% general vs %.0f%% SAFTA, and many products get no benefit at all." % (avg_gen, avg_saa)}},
    {"@type": "Question", "name": "How do I get the SAFTA preferential rate?",
     "acceptedAnswer": {"@type": "Answer", "text": "Your supplier obtains a SAFTA Certificate of Origin from the exporting country's designated authority, the goods must meet the SAFTA Rules of Origin (a change of 4-digit tariff heading plus local value addition — 40% generally, 30% for LDCs like Nepal), and the product must not be on Nepal's Sensitive List. You present the certificate at customs to claim the lower rate."}},
    {"@type": "Question", "name": "Does SAFTA reduce car import duty in Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": "Mostly no. Vehicles carry Nepal's highest general duty but about three-quarters of vehicle tariff lines get no SAFTA benefit — they are protected on the Sensitive List. SAFTA helps most on metals, household goods, footwear, wood and food, not vehicles."}},
    {"@type": "Question", "name": "Is SAFTA better than the Nepal-India trade treaty?",
     "acceptedAnswer": {"@type": "Answer", "text": "For imports from India, the bilateral Nepal-India Treaty of Trade is often more generous than SAFTA, so it is usually used instead. SAFTA matters most for imports from Bangladesh, Sri Lanka and Pakistan."}}]}

out = [page_head(title, desc, '/safta', bc, extra_ld=[faq]), crumb_html(bc)]
out.append('<h1>SAFTA: lower import duty from South Asia</h1>')
out.append('<p class="lede">SAFTA — the South Asian Free Trade Area — lets Nepal import many goods from its SAARC '
           'neighbours at a <b>lower, preferential customs duty</b> than the general rate. But it is a scalpel, not a '
           'blanket: it helps a lot on some products and nothing on others. Here is exactly where it saves you money, '
           'and what you need to claim it.</p>')
out.append('<div class="exstats">'
           '<div class="extile"><b>8</b><span>SAARC member countries</span></div>'
           '<div class="extile"><b>%.0f%% → %.0f%%</b><span>Avg duty: general → SAFTA</span></div>'
           '<div class="extile"><b>%d</b><span>Products saving 10%%+ with SAFTA</span></div></div>' % (avg_gen, avg_saa, n_big))

out.append('<h2 class="sec">What is SAFTA?</h2>')
out.append('<p>SAFTA is the free-trade agreement of the <b>SAARC</b> bloc — %s — in force since 2006. It phases down '
           'customs duties on trade between members. <b>Nepal is a Least Developed Country (LDC)</b> under SAFTA, which '
           'gives it more favourable terms: deeper tariff cuts from partners and an easier Rules-of-Origin threshold '
           '(30%% local value instead of 40%%). On customsnepal.com, the <b>“India &amp; SAARC”</b> duty shown '
           'on every HS code <i>is</i> this SAFTA preferential rate.</p>' % MEMBERS)

out.append('<h2 class="sec">Where SAFTA actually saves you money</h2>')
out.append('<p>Computed from the Nepal Customs Tariff 2026/27 — %d tariff lines compared. Average general duty '
           '<b>%.1f%%</b> vs SAFTA <b>%.1f%%</b>. The benefit is concentrated: some segments save double digits, '
           'others get almost nothing (they sit on the Sensitive List).</p>' % (tot_cmp, avg_gen, avg_saa))
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>Product segment</th><th>General</th><th>SAFTA</th>'
           '<th>Avg saving</th><th>Big savers</th><th>SAFTA benefit</th></tr></thead><tbody>')
for margin, name, gav, sav, big, nob, (label, cls) in seg_rows:
    out.append('<tr><td>%s</td><td>%.1f%%</td><td>%.1f%%</td><td><b>%.1f pts</b></td><td>%d</td>'
               '<td><span class="duty %s">%s</span></td></tr>'
               % (esc(name), gav, sav, margin, big, cls, label))
out.append('</tbody></table></div>')
out.append('<div class="note"><b>The three tiers.</b>\n'
           '<b>\U0001F7E2 Strong</b> — furniture &amp; household goods, metals &amp; steel, footwear, wood &amp; '
           'paper, and glass &amp; gems: real double-digit savings, and exactly what India, Bangladesh &amp; Sri Lanka export.\n'
           '<b>\U0001F7E1 Selective</b> — food &amp; agriculture (the broadest coverage), chemicals &amp; pharma, '
           'minerals and instruments: benefit is line-by-line, so check the specific HS code.\n'
           '<b>\U0001F534 Limited</b> — vehicles (highest duty but ~3/4 get no benefit), textiles &amp; garments '
           '(~80%% excluded) and machinery/electronics (duty already low): don’t expect SAFTA to help much.</div>')

out.append('<h2 class="sec">Top SAFTA-saving products</h2>')
out.append('<p>The tariff lines with the biggest gap between the general and SAFTA rate — where sourcing from a SAARC '
           'country with a valid certificate of origin saves the most. Tap a code for the full breakdown.</p>')
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>HS code</th><th>Product</th><th>General</th>'
           '<th>SAFTA</th><th>You save</th></tr></thead><tbody>')
for m, code, dsc, g, s in top:
    d = dsc if len(dsc) <= 60 else dsc[:58] + '…'
    out.append('<tr><td class="code"><a href="/#hs-%s">%s</a></td><td>%s</td><td>%s</td>'
               '<td><span class="duty d-free">%s</span></td><td><b>%g pts</b></td></tr>'
               % (esc(code), esc(code), esc(d), fmtpct(g), fmtpct(s), m))
out.append('</tbody></table></div>')
out.append('<p class="fineprint">%d tariff lines across the tariff save 10 percentage points or more under SAFTA; '
           '%d qualify for a fully duty-free (0%%) SAARC rate. Showing the top %d.</p>' % (n_big, n_free, len(top)))

out.append('<h2 class="sec">How to claim the SAFTA rate</h2>')
out.append('<p>The preferential rate is <b>not automatic</b>. Three conditions must all be met:</p>')
out.append('<ol class="exsteps">'
           '<li><b>SAFTA Certificate of Origin</b> — your supplier obtains the SAFTA combined declaration &amp; '
           'certificate from the exporting country’s designated issuing authority. It is valid 12 months and must '
           'be presented at Nepal customs to claim the rate.</li>'
           '<li><b>Rules of Origin</b> — the goods must be genuinely made in the exporting SAARC country: a change of '
           '4-digit HS heading <i>plus</i> local value addition of at least <b>40% (30% for LDCs like Nepal)</b>, or '
           'SAARC cumulation (≥50% aggregate regional content, ≥20% from the exporting country).</li>'
           '<li><b>Not on the Sensitive List</b> — each country keeps a Sensitive List of products excluded from '
           'concessions. For those, the SAARC rate equals the general rate (the “Limited” rows above are '
           'largely Nepal’s Sensitive List).</li></ol>')

out.append('<h2 class="sec">Which country — and the India nuance</h2>')
out.append('<p>For imports <b>from India</b>, the bilateral <b>Nepal–India Treaty of Trade</b> is often more '
           'generous than SAFTA, so it is usually used instead. SAFTA matters most for imports from <b>Bangladesh, '
           'Sri Lanka and Pakistan</b> (and Bhutan, Maldives, Afghanistan). Always compare the bilateral route with the '
           'SAFTA route for the specific product.</p>')

out.append('<h2 class="sec">Policy watch: Nepal’s LDC graduation</h2>')
out.append('<div class="note">Nepal is scheduled to <b>graduate from Least Developed Country (LDC) status in 2026</b>. '
           'Graduation mainly affects Nepal’s <b>exports</b> — it phases out LDC-specific preferences (EU EBA, GSP) '
           'and raises the SAFTA Rules-of-Origin value-addition threshold Nepali <b>exporters</b> must meet (from 30% '
           'toward 40%). The SAFTA duty Nepali <b>importers</b> pay on SAARC goods is set by Nepal’s own tariff '
           'schedule and is not changed by graduation itself, but the wider preferential-trade picture shifts — '
           'worth planning for.</div>')

out.append('<div class="tools"><a class="btn" href="/calculator">Landed-cost calculator (SAARC rate)</a>'
           '<a class="btn ghost" href="/imports">Import duty &amp; HS codes</a>'
           '<a class="btn ghost" href="/tariff">Full tariff</a></div>')
out.append('<p class="fineprint">Figures computed from the Nepal Customs Tariff 2026/27 (general vs SAARC rate per HS '
           'line; specific/compound-rate lines excluded). The SAARC rate applies only with a valid certificate of '
           'origin and Rules-of-Origin compliance.</p>')
out.append('</div>' + FOOT)
(pub / 'safta.html').write_text(''.join(out), encoding='utf-8')

# ---------------- inject URL into sitemap.xml ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rowx = '  <url><loc>%s/safta</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>' % (SITE, TODAY)
if '/safta</loc>' not in sm:
    sm = sm.replace('</urlset>', rowx + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('safta_page: /safta built — %d segments, top %d products; %d lines save >=10pts, %d SAFTA-free; +1 sitemap URL'
      % (len(seg_rows), len(top), n_big, n_free))
