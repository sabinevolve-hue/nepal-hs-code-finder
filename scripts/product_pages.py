"""Per-product import-duty landing pages — the SEO growth engine (Phase 1).

For each product Nepal actually imports at volume (HS 8-digit with real trade
value), a crawlable page: "Customs duty on <product> in Nepal" — general vs
India/SAARC (SAFTA) duty, VAT, a worked landed-cost example, Nepal's import
value + top source countries, a SAFTA saving note, and related products.
Baked at build time from data/tariff.json + data/stats.json.

Emits into public/:
  /import-duty                 (import-duty.html)          hub: top imported products
  /import-duty/<slug>-<code>   (import-duty/<..>.html)     one page per product

Appends URLs to /sitemap.xml. Mirrors seo_pages/export_pages (canonical ->
www.customsnepal.com, shared seo.css, GA4, shared nav).

Run after seo_pages.py (needs seo.css):  python3 scripts/product_pages.py
"""
import pathlib, json, datetime, html, re, unicodedata, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nav import OTHER_SITES
import textfit
import links
import family
from statsfields import IMP_VALUE, IMP_UNIT, IMP_DESC, IMP_PARTNERS, IMP_NPARTNERS, TARIFF_FY, TARIFF_FY_AD, validate_import_rows, slug, clean_name

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'import-duty').mkdir(parents=True, exist_ok=True)

TARIFF = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
STATS = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
ROWS = TARIFF['rows']
STRS = TARIFF.get('strs', [])
CH = TARIFF.get('chapters', {})
IMPORTS = STATS.get('imports', {})
FY = STATS.get('fy', '2082/83')          # trade-statistics year (Department of Customs FTS)
TY = TARIFF_FY                           # tariff year the duty rates come from (see statsfields.py)

SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
VAT = 0.13
THRESHOLD = 1000       # Rs thousand of import VALUE (Rs 10 lakh): products imported at real volume
EXBASE = 100000.0      # worked-example CIF value, Rs
FREE = {'free', 'nil', 'exempt'}


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def c8(code):
    return re.sub(r'\D', '', str(code))


def rate_info(x):
    """-> (numeric_pct_or_None, display, is_free). Handles 'Free' and specific/compound duties."""
    s = str(x).strip()
    if not s:
        return (None, '—', False)
    if s.lower() in FREE:
        return (0.0, 'Free', True)
    try:
        n = float(s)
        return (n, '%g%%' % n, False)
    except Exception:
        return (None, s, False)                 # specific / compound duty, shown verbatim


def rsf(v_thousand):
    if v_thousand is None:
        return '—'
    v = float(v_thousand) * 1000.0
    if v >= 1e9:
        return 'Rs %.2f Arab' % (v / 1e9)
    if v >= 1e7:
        return 'Rs %.2f Crore' % (v / 1e7)
    if v >= 1e5:
        return 'Rs %.1f Lakh' % (v / 1e5)
    return 'Rs %s' % format(int(round(v)), ',')


def rsplain(v):
    return 'Rs ' + format(int(round(v)), ',')


FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")


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
        '<p><b>Duty source:</b> Nepal Customs Tariff ' + TY + ' (' + TARIFF_FY_AD + ', HS 2022), Department of Customs. Figures are the '
        'statutory customs duty (general and India/SAARC under SAFTA); 13% VAT applies on (CIF value + duty). '
        'Some goods also carry excise duty, a road-development fee or other charges — use the '
        '<a href="/calculator">calculator</a> for the full figure.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool. Confirm the final HS code, '
        'customs valuation and taxes with the <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs</a> '
        'or your clearing agent before you import.</p>'
        '<p><a href="/">Home</a> · <a href="/import-duty">Import duty by product</a> · <a href="/tariff">Tariff</a> · '
        '<a href="/calculator">Calculator</a> · <a href="/safta">SAFTA</a> · © customsnepal.com</p>' + OTHER_SITES + '</div></footer>'
        '</body></html>')

from nav import render_nav

# ---------------- join + filter ----------------
TMAP = {c8(r[0]): r for r in ROWS}

# Codes whose page is already live: keep publishing them so indexed URLs never vanish.
PUBLISHED = set(json.loads((root / 'data/import_duty_published.json').read_text(encoding='utf-8'))['codes'])

items = []
for raw, imp in IMPORTS.items():
    code = c8(raw)
    # imp = [desc, unit, quantity, value, revenue, partners, n_partners]; VALUE is index 3 (Rs thousand).
    # (Index 2 is the QUANTITY — using it here was the bug that printed e.g. 154,991 laptops as "Rs 15.50 Crore".)
    try:
        valf = float(imp[IMP_VALUE])
    except Exception:
        valf = 0.0
    if valf <= 0 or (valf < THRESHOLD and code not in PUBLISHED):
        continue
    row = TMAP.get(code)
    if not row:
        continue
    items.append((code, row, imp, valf))
items.sort(key=lambda x: -x[3])

# Build-time data check: fail the build rather than publish a page whose numbers contradict each other.
_errs = validate_import_rows({c: imp for c, _, imp, _ in items}, STATS)
if _errs:
    sys.exit('product_pages: data check FAILED for %d product(s):\n  ' % len(_errs) + '\n  '.join(_errs[:50]))
_missing = PUBLISHED - {c for c, *_ in items}
if _missing:
    print('product_pages: WARNING %d previously published codes no longer in the data: %s' % (len(_missing), sorted(_missing)[:20]))

# product page path per 8-digit code, for the family ladder's links (lines without a page open in the app)
PAGE_OF = {c: '/import-duty/%s-%s' % (slug(clean_name(i[0] if i and i[0] else r[1])), c) for c, r, i, _ in items}
def fam_href(dotted):
    c = c8(dotted)
    return PAGE_OF.get(c, '/#hs-' + c)

by_head = {}
for it in items:
    by_head.setdefault(it[0][:6], []).append(it)


def chap_title(ch2):
    return CH.get(str(int(ch2)), {}).get('t', '')


def top_sources(imp):
    src = imp[IMP_PARTNERS] if len(imp) > IMP_PARTNERS and isinstance(imp[IMP_PARTNERS], list) else []
    out = []
    for s in src[:5]:
        if isinstance(s, list) and s:
            out.append((str(s[0]), float(s[1]) if len(s) > 1 else None))
    return out


def example_table(gen, gen_d, saarc, saarc_d):
    def calc(rate):
        duty = EXBASE * rate / 100.0
        vat = (EXBASE + duty) * VAT
        return duty, vat, EXBASE + duty + vat
    dg, vg, tg = calc(gen)
    body = ('<tr><td>General (any origin)</td><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td></tr>'
            % (gen_d, rsplain(dg), rsplain(vg), rsplain(tg)))
    if saarc is not None and saarc != gen:
        ds, vs, ts = calc(saarc)
        body += ('<tr><td>India &amp; SAARC (with SAFTA certificate of origin)</td><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td></tr>'
                 % (saarc_d, rsplain(ds), rsplain(vs), rsplain(ts)))
    return ('<div class="tscroll"><table class="tbl"><thead><tr><th>Origin</th><th>Customs duty</th>'
            '<th>Duty amount</th><th>VAT (13%)</th><th>Landed cost</th></tr></thead><tbody>'
            + body + '</tbody></table></div>')


def cost_stack(gen, gen_d, saarc, saarc_d):
    """The worked example as a picture: one bar per origin, split into goods, customs duty and VAT."""
    def row(label, rate):
        duty = EXBASE * rate / 100.0; vat = (EXBASE + duty) * VAT; tot = EXBASE + duty + vat
        seg = lambda cls, v, txt: '<i class="%s" style="flex:%.3f" title="%s">%s</i>' % (cls, max(v, 0.0001), txt, txt if v / tot > 0.09 else '')
        return ('<div><div class="cs-l">%s<span>Landed cost %s</span></div><div class="cs-bar" role="img" aria-label="Goods %s, customs duty %s, VAT %s, landed cost %s">%s%s%s</div></div>'
                % (label, rsplain(tot), rsplain(EXBASE), rsplain(duty), rsplain(vat), rsplain(tot),
                   seg('c', EXBASE, 'Goods ' + rsplain(EXBASE)), seg('d', duty, 'Duty ' + rsplain(duty)) if duty > 0 else '', seg('v', vat, 'VAT ' + rsplain(vat))))
    o = '<div class="cstack">' + row('General rate (%s)' % gen_d, gen)
    if saarc is not None and saarc != gen:
        o += row('India &amp; SAARC with SAFTA certificate (%s)' % saarc_d, saarc)
    return o + '</div><div class="cs-key"><span><i class="c"></i>Goods (CIF value)</span><span><i class="d"></i>Customs duty</span><span><i class="v"></i>VAT 13%</span></div>'


def product_page(code, row, imp, val):
    name = clean_name(imp[0] if imp and imp[0] else row[1])
    dotted = row[0]
    gen, gen_d, gen_free = rate_info(row[5])
    saarc, saarc_d, saarc_free = rate_info(row[4])
    numeric = gen is not None
    unit = row[3] or (imp[IMP_UNIT] if len(imp) > IMP_UNIT else '') or ''
    ch2 = code[:2]
    path = '/import-duty/' + slug(name) + '-' + code
    # title: product, code and rate up front — the three things people search for; <= 65 chars, whole words only
    rate_bit = ', duty-free' if str(gen_d).lower() == 'free' else ((', %s duty' % gen_d) if gen_d not in ('—', '') else '')
    tail = ' — HS %s%s' % (dotted, rate_bit)
    nm = ' '.join(name.split())
    if len(nm + ' in Nepal' + tail) <= 65:
        title = nm + ' in Nepal' + tail
    else:   # drop 'in Nepal' before cutting any of the product name
        title = textfit.clip_words(nm, max(18, 65 - len(tail))) + tail
    gtxt = gen_d if gen_d != '—' else 'the statutory rate'
    stxt = saarc_d if saarc_d != '—' else 'the SAARC rate'
    lead = 'Nepal customs duty on %s (HS %s): %s general, %s with SAFTA, plus 13%% VAT. Landed-cost example and import figures.'
    room = 158 - len(lead % ('', dotted, gtxt, stxt))
    desc = lead % (textfit.clip_words(name, max(24, room)), dotted, gtxt, stxt)
    desc = textfit.fit_desc(desc)

    bc = [('Home', '/'), ('Import duty', '/import-duty'), (name if len(name) < 40 else name[:38] + '…', '')]
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}
    if gen_d != '—':
        ans = "The customs duty on %s (HS %s) is %s (general)." % (name, dotted, ('free — 0%' if gen_free else gen_d))
        if saarc_d != '—' and saarc_d != gen_d:
            ans += " From India or another SAARC country under SAFTA, with a certificate of origin, it is %s." % ('free' if saarc_free else saarc_d)
        ans += " On top of customs duty, 13% VAT applies on the CIF value plus duty."
        faq["mainEntity"].append({"@type": "Question",
            "name": "What is the customs duty on %s in Nepal?" % name,
            "acceptedAnswer": {"@type": "Answer", "text": ans}})
    faq["mainEntity"].append({"@type": "Question",
        "name": "What is the HS code for %s in Nepal?" % name,
        "acceptedAnswer": {"@type": "Answer", "text": "The Nepal customs HS code for %s is %s (chapter %s — %s)."
                           % (name, dotted, ch2, chap_title(ch2))}})

    out = [page_head(title, desc, path, bc, extra_ld=[faq]), crumb_html(bc)]
    out.append('<h1>Customs duty on %s in Nepal</h1>' % esc(name))
    lede = '<b>%s</b> is classified under HS code <b>%s</b> (chapter %s, %s). ' % (esc(name), esc(dotted), esc(ch2), esc(chap_title(ch2)))
    if gen_free:
        lede += 'It is imported <b>duty-free</b> (0% customs duty), plus <b>13% VAT</b> on the CIF value.'
    elif gen_d != '—':
        lede += 'It attracts <b>%s customs duty</b> (general)' % esc(gen_d)
        if saarc_d != '—' and saarc_d != gen_d:
            lede += ', or <b>%s</b> from India &amp; SAARC under SAFTA' % esc(saarc_d)
        lede += ', plus <b>13% VAT</b> on the CIF value and duty.'
    else:
        lede += 'See its duty rate and a landed-cost note below.'
    out.append('<p class="lede">%s</p>' % lede)

    out.append('<div class="exstats">'
               '<div class="extile"><b>%s</b><span>General duty</span></div>'
               '<div class="extile"><b>%s</b><span>India &amp; SAARC (SAFTA)</span></div>'
               '<div class="extile"><b>13%%</b><span>VAT</span></div>'
               '<div class="extile"><b>%s</b><span>Customs unit</span></div></div>'
               % (esc(gen_d), esc(saarc_d), esc(unit or '—')))

    if numeric:
        out.append('<h2 class="sec">Landed cost — worked example</h2>')
        out.append('<p>For a shipment with a <b>CIF value of %s</b> (cost + insurance + freight to the Nepal border), '
                   'the customs duty and VAT work out as:</p>' % rsplain(EXBASE))
        out.append(cost_stack(gen, gen_d, saarc, saarc_d))
        out.append(example_table(gen, gen_d, saarc, saarc_d))
        if saarc is not None and 0 <= saarc < gen:
            saving = EXBASE * (gen - saarc) / 100.0
            saving += saving * VAT
            out.append('<div class="note">Importing from <b>India or SAARC</b> under SAFTA (with a certificate of origin) '
                       'cuts the duty from %s to %s — about <b>%s</b> less on this %s example, once the VAT on the saved '
                       'duty is counted. <a href="/safta">How SAFTA &amp; the certificate of origin work →</a></div>'
                       % (gen_d, saarc_d, rsplain(saving), rsplain(EXBASE)))
        out.append('<p class="trkhint">Excise duty, the road-development fee and other charges apply to specific goods '
                   '(vehicles, alcohol, tobacco, petroleum…) and are not in the figure above. '
                   '<a href="/calculator">Open the full calculator →</a></p>')
    elif gen_d != '—':
        out.append('<h2 class="sec">Duty on this product</h2>')
        out.append('<div class="note">This product carries a <b>specific duty</b> — <b>%s</b> — rather than a flat '
                   'percentage, so the amount depends on quantity. Enter your shipment in the '
                   '<a href="/calculator">calculator</a> for the exact figure; 13%% VAT still applies on the CIF value '
                   'plus duty.</div>' % esc(gen_d))

    out.append(family.render(dotted, fam_href))

    srcs = top_sources(imp)
    out.append('<h2 class="sec">Nepal&rsquo;s imports of %s</h2>' % esc(name))
    ctx = 'Nepal imported about <b>%s</b> of %s in FY&nbsp;%s' % (rsf(val), esc(name), esc(FY))
    ctx += (', mainly from ' + ', '.join('<b>%s</b>' % esc(s[0]) for s in srcs[:3]) + '.') if srcs else '.'
    out.append('<p>%s</p>' % ctx)
    _al = links.alias_for(code)
    if _al:
        out.append('<p class="xlink">Plain-language guide: <a href="%s">import duty on %s in Nepal</a> — every HS line '
                   'people mean by that name, with a worked example.</p>' % (_al[0], esc(_al[1])))
    if srcs:
        out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>Source country</th><th>Import value (FY %s)</th></tr></thead><tbody>' % esc(FY))
        for nm, v in srcs:
            out.append('<tr><td>%s</td><td>%s</td></tr>' % (links.partner_link(nm, esc), rsf(v) if v is not None else '—'))
        npart = int(imp[IMP_NPARTNERS]) if len(imp) > IMP_NPARTNERS and str(imp[IMP_NPARTNERS]).isdigit() else len(srcs)
        rest = val - sum(v or 0 for _, v in srcs)
        if npart > len(srcs) and rest >= 1:
            k = npart - len(srcs)
            out.append('<tr class="other"><td>Other countries (%d)</td><td>%s</td></tr>' % (k, rsf(rest)))
        out.append('<tr class="total"><td><b>All countries</b></td><td><b>%s</b></td></tr>' % rsf(val))
        out.append('</tbody></table></div>')

    rel = [x for x in by_head.get(code[:6], []) if x[0] != code]
    if len(rel) < 4:
        seen = {x[0] for x in rel} | {code}
        for x in items:
            if x[0][:2] == ch2 and x[0] not in seen:
                rel.append(x); seen.add(x[0])
            if len(rel) >= 8:
                break
    rel = rel[:8]
    if rel:
        out.append('<h2 class="sec">Related products</h2><div class="guidegrid">')
        for rc, rr, ri, rv in rel:
            rn = clean_name(ri[0] if ri and ri[0] else rr[1])
            out.append('<a class="chcard" href="/import-duty/%s-%s"><span class="t">%s</span>'
                       '<span class="c">HS %s · %s duty</span></a>'
                       % (slug(rn), rc, esc(rn), esc(rr[0]), esc(rate_info(rr[5])[1])))
        out.append('</div>')

    out.append('<div class="tools"><a class="btn" href="/calculator">Full landed-cost calculator</a>'
               '<a class="btn ghost" href="/#hs-%s">Open %s in the tariff</a>'
               '<a class="btn ghost" href="/tariff/%02d">Chapter %s</a></div>' % (code, esc(dotted), int(ch2), esc(ch2)))
    out.append(FOOT)
    (pub / 'import-duty' / (slug(name) + '-' + code + '.html')).write_text(''.join(out), encoding='utf-8')
    return path


paths = [product_page(code, row, imp, val) for code, row, imp, val in items]

# ---------------- hub ----------------
hub_title = 'Nepal import duty by product — customs duty & tax lookup | Customs Nepal'
hub_desc = ('Customs duty on everything Nepal imports, product by product: general and India/SAARC (SAFTA) duty, '
            '13% VAT and a worked landed-cost example for each. The products Nepal actually imports, ranked by value.')
bc = [('Home', '/'), ('Import duty', '')]
out = [page_head(hub_title, hub_desc, '/import-duty', bc), crumb_html(bc)]
out.append('<h1>Nepal import duty by product</h1>')
out.append('<p class="lede">The customs duty and landed cost for the products Nepal imports — each with its general and '
           'India/SAARC (SAFTA) rate, 13%% VAT and a worked example. Covering <b>%d</b> traded products, ranked by import value. '
           'Looking for one specific item? <a href="/">Search the full tariff</a> or '
           '<a href="/calculator">use the calculator</a>.</p>' % len(items))
out.append('<div class="exstats"><div class="extile"><b>%d</b><span>Products covered</span></div>'
           '<div class="extile"><b>6,340</b><span>Tariff lines</span></div>'
           '<div class="extile"><b>FY %s</b><span>Import data</span></div></div>' % (len(items), esc(FY)))
out.append('<h2 class="sec">Most-imported products</h2>')
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>Product</th><th>HS code</th>'
           '<th>General</th><th>SAARC</th><th>Nepal imports (FY %s)</th></tr></thead><tbody>' % esc(FY))
for code, row, imp, val in items[:200]:
    name = clean_name(imp[0] if imp and imp[0] else row[1])
    out.append('<tr><td><a href="/import-duty/%s-%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
               % (slug(name), code, esc(name), esc(row[0]),
                  esc(rate_info(row[5])[1]), esc(rate_info(row[4])[1]), rsf(val)))
out.append('</tbody></table></div>')
out.append('<p class="trkhint">Showing the top 200 by import value; all %d product pages are in the '
           '<a href="/sitemap.xml">sitemap</a> and linked from related products. Browse everything by chapter in the '
           '<a href="/tariff">full tariff</a>.</p>' % len(items))
out.append('<div class="tools"><a class="btn" href="/">Search any product</a>'
           '<a class="btn ghost" href="/calculator">Landed-cost calculator</a>'
           '<a class="btn ghost" href="/duty-free">Duty-free and 5% goods</a>'
           '<a class="btn ghost" href="/safta">SAFTA savings</a></div>')
out.append(FOOT)
(pub / 'import-duty.html').write_text(''.join(out), encoding='utf-8')

# ---------------- sitemap ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows_xml = ['  <url><loc>%s/import-duty</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, TODAY)]
for p in paths:
    rows_xml.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>yearly</changefreq><priority>0.6</priority></url>' % (SITE, p, TODAY))
if '</urlset>' in sm:
    sm = sm.replace('</urlset>', '\n'.join(rows_xml) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('product_pages: %d product pages + hub; +%d sitemap URLs' % (len(items), len(paths) + 1))
