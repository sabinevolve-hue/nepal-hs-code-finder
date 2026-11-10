"""Consumer-term import-duty landing pages — the money-query layer.

People search "mobile customs duty nepal", "iphone bhansar", "led tv import tax",
not "HS 8517.13". tariff.json already ships a bilingual `aliases` map (consumer
terms incl. Devanagari -> HS prefixes); this turns each alias group into a
product-named landing page at /import-duty/<name> that shows the real duty for
the codes it covers, a worked landed-cost, and routes into the HS detail pages.

Accurate by construction: duty comes straight from tariff.json; no invented
figures. Bilingual (English + Nepali) because the aliases already carry both.

Mirrors seo_pages.py / product_pages.py (canonical->www, shared seo.css, nav, GA).
Run after product_pages.py:  python3 scripts/alias_pages.py
"""
import pathlib, json, datetime, html, re, sys

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'import-duty').mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root / 'scripts'))
from nav import render_nav, OTHER_SITES
import links

TAR = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
ROWS = TAR['rows']
from aliases import ALIASES as _ALIASES
# aliases.py ships ("comma, separated, terms", [codes]); normalise to (terms_list, codes)
ALIASES = [([t.strip() for t in s.split(',') if t.strip()], codes) for s, codes in _ALIASES]
TVER = TAR.get('v', '')
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
VAT = 0.13

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def is_np(t):
    return any('ऀ' <= ch <= 'ॿ' for ch in t)

def slugify(name):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')

def clean(s):
    return ' '.join(str(s or '').split()).strip(' .')

ACR = {'led', 'tv', 'pc', 'ac', 'cctv', 'dslr', 'usb', 'lpg', 'suv', 'gps', 'ups', 'hdd', 'ssd',
       'lcd', 'lan', 'ip', 'cpu', 'gpu', 'dvr', 'psu', 'ram', 'ups', 'evs', 'ev'}
def titleize(s):
    return ' '.join(w.upper() if w.lower() in ACR else (w if w[:1].isupper() else w.capitalize()) for w in s.split())

# chapters where excise duty is significant and NOT in tariff.json — never fabricate a landed cost here
EXCISE = {'22', '24', '87'}  # alcohol, tobacco, vehicles

def inr(n):
    n = int(round(n)); neg = n < 0; n = abs(n); s = str(n); l = s[-3:]; r = s[:-3]
    if r:
        l = ',' + l; r = re.sub(r'\B(?=(\d{2})+(?!\d))', ',', r)
    return ('-' if neg else '') + r + l

def rate_text(v):
    if v is None or str(v).strip() == '':
        return None
    s = str(v).strip()
    if s.lower() == 'free' or s == '0':
        return 'Free'
    if re.fullmatch(r'\d+(\.\d+)?', s):
        return (s.rstrip('0').rstrip('.') if '.' in s else s) + '%'
    return s

def rate_cls(txt):
    if txt is None:
        return ''
    if txt == 'Free':
        return 'free'
    m = re.match(r'(\d+(\.\d+)?)%', txt)
    if m:
        n = float(m.group(1))
        return 'low' if n <= 5 else 'mid' if n <= 15 else 'hi'
    return 'mid'

def rate_num(v):
    s = str(v).strip().lower()
    if s == 'free' or s == '':
        return 0.0
    m = re.fullmatch(r'(\d+(\.\d+)?)', s)
    return float(m.group(1)) if m else None

def matches(prefix):
    return [r for r in ROWS if str(r[0]).startswith(prefix)]

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
        '<p><b>Duty rates:</b> Nepal Customs Tariff ' + esc(TVER) + ' (general and India/SAARC rates). '
        '<b>VAT</b> is 13% on (customs value + duty). Actual duty depends on the exact HS sub-heading, the declared '
        'customs value and any excise; confirm with the <a href="https://www.customs.gov.np" target="_blank" '
        'rel="noopener noreferrer">Department of Customs</a> before you import.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/import-duty">Import duty by product</a> · <a href="/calculator">Calculator</a> · '
        '<a href="/tariff">Tariff</a> · © customsnepal.com</p>' + OTHER_SITES + '</div></footer>'
        '</body></html>')

# ---- build alias records ----
used = {}
records = []  # (slug, canonical, en_terms, np_terms, codes, covered_rows, primary_row)
for terms, codes in ALIASES:
    en = [clean(t) for t in terms if not is_np(t)]
    np = [clean(t) for t in terms if is_np(t)]
    canonical = (en[0] if en else terms[0]).strip()
    covered, seen = [], set()
    for p in codes:
        for r in matches(p):
            if r[0] not in seen:
                seen.add(r[0]); covered.append(r)
    if not covered:
        continue
    covered.sort(key=lambda r: r[0])
    primary = matches(codes[0])[0] if matches(codes[0]) else covered[0]
    slug = slugify(canonical) or slugify(codes[0])
    if slug in used:
        used[slug] += 1; slug = '%s-%d' % (slug, used[slug])
    else:
        used[slug] = 1
    records.append((slug, canonical, en, np, codes, covered, primary))

assert [r[0] for r in records] == links.ALIAS_SLUGS, 'links.py alias slugs drifted from alias_pages.py'
slug_by_idx = {i: rec[0] for i, rec in enumerate(records)}
CANON = {rec[0]: rec[1] for rec in records}

def related(cur_slug, cur_ch, n=8):
    same, other = [], []
    for rec in records:
        if rec[0] == cur_slug:
            continue
        ch = str(rec[5][0][0])[:2]
        (same if ch == cur_ch else other).append(rec)
    picks = (same + other)[:n]
    return '<div class="pchips">' + ''.join(
        '<a href="/import-duty/%s">%s</a>' % (r[0], esc(titleize(r[1]))) for r in picks) + '</div>'

def worked(primary):
    ch = str(primary[0])[:2]
    gen = rate_num(primary[5])
    cif = 100000
    gt0 = rate_text(primary[5]) or 'Free'
    if ch in EXCISE:
        return gt0, ('<div class="note warn"><b>Excise duty also applies — not shown here.</b> Vehicles, alcohol and '
                     'tobacco carry a large <b>excise duty</b> on top of customs duty and 13% VAT, which varies by type, '
                     'engine size or strength and changes with each budget. The rate below is the <b>customs duty only</b>; '
                     'for the full landed cost use the official tariff and excise schedule.</div>')
    if gen is None:
        return None, ('<div class="note">This item carries a <b>specific or compound duty</b> rather than a flat '
                      'percentage — open the HS code below or the <a href="/calculator">calculator</a> for the exact figure.</div>')
    duty = cif * gen / 100.0
    vat = (cif + duty) * VAT
    landed = cif + duty + vat
    gt = rate_text(primary[5]) or 'Free'
    tiles = ('<div class="exstats">'
             '<div class="extile"><b>%s</b><span>Customs duty</span></div>'
             '<div class="extile"><b>13%%</b><span>VAT (on value + duty)</span></div>'
             '<div class="extile"><b>Rs %s</b><span>Landed cost on Rs 1,00,000</span></div></div>'
             % (esc(gt), inr(landed)))
    line = ('<p>On a <b>Rs 1,00,000</b> import you would pay about <b>Rs %s</b> customs duty and <b>Rs %s</b> VAT — '
            'landing at <b>Rs %s</b>. <a href="/calculator">Try your own value →</a></p>'
            % (inr(duty), inr(vat), inr(landed)))
    return gt, tiles + line

# ---- per-alias pages ----
made = 0
for rec in records:
    slug, canonical, en, np, codes, covered, primary = rec
    cur_ch = str(primary[0])[:2]
    path = '/import-duty/' + slug
    disp = titleize(canonical)
    alt_en = ', '.join(dict.fromkeys(t.title() if t.islower() else t for t in en[1:]))[:60]
    np_main = np[0] if np else ''

    gt, workblock = worked(primary)
    rates = sorted({rate_text(r[5]) for r in covered if rate_text(r[5])}, key=lambda x: (x != 'Free', x))
    rate_phrase = gt if gt else 'a varying rate'

    title = '%s import duty in Nepal | Customs Nepal' % disp
    if len(title) > 62:
        title = '%s customs duty Nepal | Customs Nepal' % disp
    desc = ('Customs duty and VAT on importing %s into Nepal: general and India/SAARC (SAFTA) rate, 13%% VAT and a '
            'worked landed-cost example. HS code%s %s.'
            % (disp.lower(), 's' if len(covered) > 1 else '', ', '.join(dict.fromkeys(str(r[0]) for r in covered[:3]))))
    bc = [('Home', '/'), ('Import duty', '/import-duty'), (disp, '')]
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": "What is the customs duty on %s in Nepal?" % disp.lower(),
         "acceptedAnswer": {"@type": "Answer", "text": "Under the Nepal Customs Tariff %s, %s is classified under HS %s and carries a general import duty of %s, plus 13%% VAT on the customs value plus duty." % (TVER, disp.lower(), str(primary[0]), rate_phrase)}},
        {"@type": "Question", "name": "Is there VAT on importing %s into Nepal?" % disp.lower(),
         "acceptedAnswer": {"@type": "Answer", "text": "Yes. Nepal levies 13% VAT on almost all imports, calculated on the customs (CIF) value plus the customs duty."}}]}
    out = [page_head(title, desc, path, bc, extra_ld=[faq]), crumb_html(bc)]
    sub = (' <span class="h1np">%s भन्सार</span>' % esc(np_main)) if np_main else ''
    out.append('<h1>%s import duty in Nepal%s</h1>' % (esc(disp), sub))
    lede = ('How much customs duty and tax you pay to import <b>%s</b>%s into Nepal — the rate, the HS code it falls '
            'under, and a worked landed-cost example.' % (esc(disp.lower()), (' (' + esc(alt_en) + ')') if alt_en else ''))
    out.append('<p class="lede">%s</p>' % lede)
    # Nepali factual summary
    if np_main or True:
        subj = esc(np_main) if np_main else esc(disp.lower())
        if gt == 'Free':
            npl = '%s नेपालमा आयात गर्दा भन्सार महसुल लाग्दैन (निःशुल्क); केवल १३%% भ्याट लाग्छ।' % subj
        elif gt:
            npl = '%s नेपालमा आयात गर्दा साधारण भन्सार दर %s र त्यसमाथि १३%% भ्याट लाग्छ।' % (subj, esc(gt))
        else:
            npl = '%s को भन्सार दर एचएस उपशीर्षकअनुसार फरक पर्छ; तलको दर हेर्नुहोस्।' % subj
        out.append('<p class="nepsum">%s</p>' % npl)

    if workblock:
        out.append(workblock)

    out.append('<h2 class="sec">Which HS code%s %s falls under</h2>' % ('s' if len(covered) > 1 else '', esc(disp.lower())))
    saarc_lower = any(rate_num(r[4]) is not None and rate_num(r[5]) is not None and rate_num(r[4]) < rate_num(r[5]) for r in covered)
    out.append('<div class="tscroll"><table class="tbl ptbl"><tr><th>HS code</th><th>Description</th>'
               '<th class="r">General</th><th class="r">SAARC</th></tr>')
    for r in covered[:14]:
        c8 = re.sub(r'\D', '', str(r[0]))[:8]
        gt2 = rate_text(r[5]); st2 = rate_text(r[4])
        gb = '<span class="badge %s">%s</span>' % (rate_cls(gt2), esc(gt2)) if gt2 else '—'
        sb = '<span class="badge %s">%s</span>' % (rate_cls(st2), esc(st2)) if st2 else '—'
        out.append('<tr><td class="mono"><a href="/#hs-%s">%s</a></td><td>%s</td><td class="r">%s</td><td class="r">%s</td></tr>'
                   % (c8, esc(r[0]), esc(clean(r[1])[:60]), gb, sb))
    out.append('</table></div>')

    if saarc_lower:
        out.append('<div class="note"><b>Importing from India or another SAARC country?</b> The SAARC column may be '
                   'lower under <a href="/safta">SAFTA</a> with a valid Certificate of Origin. From China, the US or '
                   'elsewhere the general rate applies in full.</div>')

    out.append('<div class="tools"><a class="btn" href="/calculator">Landed-cost calculator</a>'
               '<a class="btn ghost" href="/import-duty">All products</a>'
               '<a class="btn ghost" href="/">Search the tariff</a></div>')

    sup_row = next((r for r in [primary] + covered if links.suppliers_for(r[0])), None)
    if sup_row:
        sups = links.suppliers_for(sup_row[0])
        out.append('<h2 class="sec">Who sells it to Nepal</h2>')
        out.append('<p>For HS %s (%s), Nepal&rsquo;s biggest suppliers by import value in FY %s were %s. '
                   'Open a country to see everything Nepal buys from it.</p>'
                   % (esc(sup_row[0]), esc(clean(sup_row[1])[:70]), esc(links._C['fy']),
                      ', '.join(('<a href="%s">%s</a>' % (h, esc(n)) if h else esc(n)) + ' (%s%%)' % ('%g' % p) for n, h, p in sups)))
    out.append('<p class="xlink"><b>See also:</b> <a href="/trade/category/%s">Nepal&rsquo;s imports and exports in this category</a> · '
               '<a href="/trade-partners">Nepal&rsquo;s trading partners</a> · <a href="/tariff/%s">Chapter %d tariff table</a></p>'
               % (cur_ch, cur_ch, int(cur_ch)))

    out.append('<h2 class="sec">Related products</h2>')
    out.append(related(slug, cur_ch))
    out.append('</div>' + FOOT)
    (pub / 'import-duty' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')
    made += 1

# ---- inject a "browse by product name" block into the import-duty hub ----
hub = pub / 'import-duty.html'
if hub.exists():
    htext = hub.read_text(encoding='utf-8')
    if 'popular-names' not in htext:
        chips = ''.join('<a href="/import-duty/%s">%s</a>' % (rec[0], esc(titleize(rec[1]))) for rec in records)
        block = ('<h2 class="sec" id="popular-names">Popular products by name</h2>'
                 '<p>Jump straight to the duty on a product by its common name (English or Nepali):</p>'
                 '<div class="pchips">' + chips + '</div>')
        anchor = '<div class="tools"><a class="btn" href="/">Search any product</a>'
        if anchor in htext:
            htext = htext.replace(anchor, block + anchor, 1)
            hub.write_text(htext, encoding='utf-8')

# ---- styles (small additions; most reused from product/country pages) ----
CSS = """
.nepsum{color:var(--ink);background:var(--card);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:10px;padding:10px 14px;margin:.4em 0 1em;font-size:.95rem}
"""
css_path = pub / 'seo.css'
cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
if '.nepsum{' not in cur:
    css_path.write_text(cur + '\n' + CSS.strip() + '\n', encoding='utf-8')

# ---- sitemap ----
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows_xml = ['  <url><loc>%s/import-duty/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>'
            % (SITE, rec[0], TODAY) for rec in records]
# only inject the ones not already present (avoid dupes with product_pages' own injections)
add = [x for x in rows_xml if ('<loc>%s</loc>' % x.split('<loc>')[1].split('</loc>')[0]) not in sm]
if add:
    sm = sm.replace('</urlset>', '\n'.join(add) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('alias_pages: %d consumer-term pages; +%d sitemap URLs' % (made, len(add)))
