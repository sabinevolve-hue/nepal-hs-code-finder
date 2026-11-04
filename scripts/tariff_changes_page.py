"""Tariff-changes page — static, crawlable explainer on customsnepal.com:
"Nepal Customs Tariff 2083/84 (2026/27): What Changed".

Accuracy rules (this page is about rates, so they matter):
  * Facts about the NEW tariff (line count, rate tiers, specific-rate lines, fuel rates) are computed at build time
    from data/tariff.json — the same transcription of the Department of Customs PDF used across the site.
  * Facts about what CHANGED vs 2082/83 come only from the cited sources in SOURCES below (budget speech, Finance
    Bill summaries, news). The repo holds no machine-readable 2082/83 tariff, so there is deliberately NO
    line-by-line diff here. If a 2082/83 tariff is ever added to data/, compute the diff instead of hand-writing it.
  * The build fails if the tariff data stops matching what the text says (e.g. the general column no longer has
    exactly seven ad-valorem rates), so the prose can never silently drift from the data.

Emits public/tariff/2083-84-changes.html (served at /tariff/2083-84-changes) and injects one URL into
public/sitemap.xml. Reuses seo.css classes (exstats/extile from export_pages.py, tbl, note, tools, fineprint).

Run after safta_page.py:  python3 scripts/tariff_changes_page.py
"""
import pathlib, json, datetime, html, sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nav import render_nav, OTHER_SITES

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'tariff').mkdir(parents=True, exist_ok=True)
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
PUBLISHED = '2026-11-04'
PATH = '/tariff/2083-84-changes'
YEAR = '2026/27'
FY_BS = '2083/84'
DOC_TARIFF_PAGE = 'https://customs.gov.np/content/50/customs-tarrif/'


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


# ---------------- data: the 2026/27 tariff as published ----------------
D = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
ROWS = D['rows']
GEN = 5   # row = [code, desc, path, unit, saarc, general, page, ldc] (see safta_page.py auto-detect)


def num(v):
    s = str(v if v is not None else '').strip()
    if s.lower() == 'free':
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def by_code(code):
    for r in ROWS:
        if r[0] == code:
            return r
    raise SystemExit('tariff_changes_page: HS %s missing from data/tariff.json' % code)


n_lines = len(ROWS)
n_chapters = len({r[0][:2] for r in ROWS})
adval = Counter()
n_specific = 0
for r in ROWS:
    g = str(r[GEN]).strip()
    v = num(g)
    if v is not None:
        adval[v] += 1
    elif g and 'corresponding new articles' not in g:
        n_specific += 1          # per-unit or "Rs X or Y% whichever is higher" rates
tiers = sorted(adval)
# The page text says the general column has seven ad-valorem rates. Fail the build if the data disagrees.
if len(tiers) != 7:
    raise SystemExit('tariff_changes_page: expected 7 ad-valorem general rates in data/tariff.json, found %d (%s) — '
                     'update the page text' % (len(tiers), tiers))

FUEL = [('2710.12.10', 'Motor spirit (petrol)'), ('2710.19.10', 'Kerosene (superior kerosene oil)'),
        ('2710.19.30', 'High-speed diesel')]
fuel_rows = [(code, name, by_code(code)[GEN]) for code, name in FUEL]


def fmt_rate(v):
    return 'Free' if v == 0 else ('%g%%' % v)


def fmt_fuel(s):
    # 'Per KL Rs. 25200' / 'Per KL Rs12000' -> 'Rs 25,200 per KL'
    digits = ''.join(ch for ch in str(s) if ch.isdigit())
    return 'Rs %s per KL' % format(int(digits), ',') if digits and 'KL' in str(s) else str(s)


# ---------------- sources (every changed-vs-last-year claim cites one of these) ----------------
SOURCES = {
    'doc': ('Department of Customs — Customs Tariff page (official 2026/27 tariff PDF)', DOC_TARIFF_PAGE),
    'speech': ('Budget speech FY 2083/84 by Finance Minister Dr Swarnim Wagle, full Nepali text (Arthik Awaj)',
               'https://arthikawaj.com/budget-2083-84/'),
    'ht': ('The Himalayan Times, 29 May 2026 — “Govt cuts customs tariff slabs, scraps excise duty on 360 items”',
           'https://thehimalayantimes.com/business/govt-cuts-customs-tariff-slabs-scraps-excise-duty-on-360-items'),
    'ekantipur': ('eKantipur, 28 June 2026 (14 Asar 2083) — Finance Bill 2083 passed by the House of Representatives',
                  'https://ekantipur.com/business/2026/06/28/economic-bill-2083-bs-passed-by-the-house-of-representatives-34-52.html'),
    'arthadabali': ('Artha Dabali, 17 July 2026 — FY 2083/84 begins; Finance Act 2083 in force from 1 Shrawan',
                    'https://www.arthadabali.com/2026/07/17/91026'),
    'infinity': ('Infinity Law, 16 June 2026 — Finance Bill 2083: key customs and excise duty changes',
                 'https://infinitynp.com/insights/finance-bill-2083-customs-excise-duty-nepal'),
    'saca': ('SAR Associates (SACA) — Finance Bill 2083: tax concessions and facilities',
             'https://www.saca.com.np/finance-bill-2083-tax-concessions-and-facilities/'),
    'ktmpost': ('The Kathmandu Post, 7 April 2026 — government halves customs duty and infrastructure tax on fuel',
                'https://kathmandupost.com/money/2026/04/07/halved-fuel-taxes-won-t-benefit-consumers-but-will-trim-noc-losses'),
}
ORDER = list(SOURCES)


def cite(*keys):
    return ''.join('<sup><a href="#src-%d">[%d]</a></sup>' % (ORDER.index(k) + 1, ORDER.index(k) + 1) for k in keys)


def ext(url, text):
    return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (esc(url), text)


# ---------------- page shell (mirrors safta_page.py / seo_pages.py) ----------------
FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")


def page_head(title, desc, path, breadcrumb, extra_ld):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0F172A">'
        '<title>' + esc(title) + '</title>'
        '<meta name="description" content="' + esc(desc) + '">'
        '<link rel="canonical" href="' + SITE + path + '">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<meta property="og:type" content="article"><meta property="og:site_name" content="Customs Nepal">'
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
        '<nav class="topnav">' + render_nav(path, esc) + '</nav></div></header>'
        '<div class="wrap">'
    )


def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'


FOOT = ('<footer><div class="wrap">'
        '<p><b>Official sources:</b> Government of Nepal, '
        '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs (customs.gov.np)</a> '
        '— Customs Tariff ' + YEAR + ' — and the '
        '<a href="https://www.mof.gov.np" target="_blank" rel="noopener noreferrer">Ministry of Finance (mof.gov.np)</a>. '
        'The Finance Act 2083 and the official tariff book prevail over this summary — confirm rates with the customs '
        'office or your clearing agent before a binding decision.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent, privately operated reference tool. '
        'It is not affiliated with, endorsed by, or representing the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/tariff">All chapters</a> · <a href="/import-duty">Import duty by product</a> · '
        '<a href="/calculator">Calculator</a> · <a href="/safta">SAFTA</a> · <a href="/faq">FAQ</a> · '
        '© customsnepal.com</p>' + OTHER_SITES + '</div></footer>'
        '</body></html>')

# ---------------- content ----------------
title = 'Nepal Customs Tariff 2083/84 (2026/27): What Changed | Customs Nepal'
desc = ('Nepal customs tariff 2083/84 (2026/27): official PDF download link, when it took effect, and what changed — '
        'duty tiers cut from 11 to 7, lower duty on 273 raw materials, green tax, fuel duty. With sources.')
h1 = 'Nepal Customs Tariff 2083/84 (2026/27): what changed'
bc = [('Home', '/'), ('Tariff ' + YEAR, '/tariff'), ('What changed in ' + FY_BS, '')]

tier_list = ', '.join(fmt_rate(t) for t in tiers[:-1]) + ' and ' + fmt_rate(tiers[-1])

FAQS = [
    ('Where can I download the Nepal customs tariff 2083/84 PDF?',
     'The official Customs Tariff 2026/27 (FY 2083/84) PDF is published by the Department of Customs on its Customs '
     'Tariff page at customs.gov.np/content/50/customs-tarrif/ (link: “Customs Tarrif 2026-27”). Customs Nepal does '
     'not re-host the PDF; every rate on this site is transcribed from it, and you can search it by product or HS code.'),
    ('When did the 2083/84 customs tariff take effect?',
     'The budget was presented on 15 Jestha 2083 (29 May 2026) and the Finance Bill 2083 passed the House of '
     'Representatives on 14 Asar 2083 (28 June 2026). Fiscal year 2083/84 began on 1 Shrawan 2083 (17 July 2026) with '
     'the Finance Act 2083 in force. Some Finance Bill measures, such as the 50% fuel customs-duty concession, applied '
     'from budget day. The official tariff book itself does not print a start date.'),
    ('How many customs duty rates (tiers) are there in 2083/84?',
     'The FY 2083/84 budget cut the customs duty structure from 11 tiers to 7. In the published 2026/27 tariff the '
     'general (ad-valorem) duty column uses seven rates: %s. A further %d tariff lines carry specific per-unit or '
     '“whichever is higher” rates, mainly beverages and alcohol, fruit juices, tobacco and fuels.' % (tier_list, n_specific)),
    ('Which goods got lower customs duty in the 2083/84 budget?',
     'The budget speech says customs duty was cut on 273 types of industrial raw materials, with a rule that raw-material '
     'duty stays at least one tier below the duty on finished goods. The speech and news coverage do not publish a '
     'line-by-line list, so check the current rate for your specific HS code in the search or calculator.'),
    ('What is the bhansar (customs duty) rate on my product in 2026?',
     'Search the product or its 8-digit HS code on customsnepal.com: each code shows the 2026/27 general and SAARC '
     'customs duty from the official tariff. The landed-cost calculator then adds 13% VAT (charged on value plus duty) '
     'and gives a rupee estimate.'),
    ('Is the 2083/84 tariff the same as the 2026/27 tariff?',
     'Yes. 2083/84 is Nepal\'s fiscal year in Bikram Sambat (mid-July 2026 to mid-July 2027); the Department of Customs '
     'prints the same book as “Customs Tariff 2026/2027”. It follows the Harmonized System 2022 (seventh edition).'),
]

faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "url": SITE + PATH, "inLanguage": "en",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}
article_ld = {"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc,
              "inLanguage": "en", "datePublished": PUBLISHED, "dateModified": TODAY,
              "author": {"@type": "Organization", "@id": SITE + "/#org", "name": "Customs Nepal", "url": SITE + "/"},
              "publisher": {"@type": "Organization", "@id": SITE + "/#org", "name": "Customs Nepal", "url": SITE + "/"},
              "mainEntityOfPage": SITE + PATH, "image": SITE + "/og.png",
              "about": [{"@type": "Thing", "name": "Nepal Customs Tariff 2083/84"},
                        {"@type": "Thing", "name": "Nepal budget 2083/84 customs duty changes"}],
              "citation": [u for _, u in SOURCES.values()]}

out = [page_head(title, desc, PATH, bc, [article_ld, faq_ld]), crumb_html(bc)]
out.append('<h1>%s</h1>' % esc(h1))
out.append('<p class="lede">The <b>Nepal Customs Tariff 2083/84 (2026/27)</b> is the Department of Customs&rsquo; '
           'official schedule of import duty for every HS code, read with the Customs Tariff Act and the Finance Act 2083. It applies to fiscal year '
           '2083/84, which began on <b>1 Shrawan 2083 (17 July 2026)</b>%s. Download the official PDF from the '
           '%s.</p>' % (cite('arthadabali'), ext(DOC_TARIFF_PAGE, 'Department of Customs tariff page')))
out.append('<div class="tools"><a class="btn" href="%s" target="_blank" rel="noopener noreferrer">Official tariff PDF (customs.gov.np)</a>'
           '<a class="btn ghost" href="/">Search any HS code</a><a class="btn ghost" href="/calculator">Duty calculator</a></div>'
           % esc(DOC_TARIFF_PAGE))
out.append('<div class="exstats">'
           '<div class="extile"><b>11 → 7</b><span>Customs duty tiers</span></div>'
           '<div class="extile"><b>273</b><span>Raw materials with lower duty</span></div>'
           '<div class="extile"><b>%s</b><span>Tariff lines in 2026/27</span></div></div>' % format(n_lines, ','))

# --- what changed
out.append('<h2 class="sec">What changed vs 2082/83</h2>')
out.append('<p>The changes below come from the FY 2083/84 budget, presented by Finance Minister Dr Swarnim Wagle on '
           '<b>15 Jestha 2083 (29 May 2026)</b>%s, and the Finance Bill 2083 that carries them into law.</p>' % cite('ht'))
out.append('<ol class="exsteps">'
           '<li><b>Customs duty tiers cut from 11 to 7.</b> The budget limited the existing eleven-tier customs rate '
           'structure to seven tiers.%s</li>'
           '<li><b>Lower duty on industrial raw materials.</b> Customs duty was reduced on <b>273 types of industrial raw '
           'materials</b>, under a rule that raw-material duty is at least one tier below the duty on the finished '
           'goods made from them.%s</li>'
           '<li><b>Customs-point levies merged into a green tax.</b> Scattered charges collected at customs — the '
           'infrastructure development tax and the road maintenance and improvement fee — were folded into a single '
           'green tax.%s</li>'
           '<li><b>Excise abolished on 360 goods.</b> Not a customs-duty change, but it lowers the landed cost of those '
           'imports.%s</li>'
           '<li><b>Fuel: 50%% customs-duty concession.</b> The Finance Bill 2083 gives a 50%% reduction in customs duty on '
           'petrol (2710.12.10), kerosene (2710.19.10) and high-speed diesel (2710.19.30) from 15 Jestha 2083, a cut the '
           'government first made on 7 April 2026.%s The government can change or withdraw it by notice in the Nepal '
           'Gazette.%s See the note below on how this shows in the tariff book.</li>'
           '<li><b>Relief for property damaged in the Gen Z movement.</b> Businesses importing goods to restore '
           'property damaged by arson or vandalism get a 50%% discount on customs and excise duty, backed by an insurance '
           'surveyor&rsquo;s report.%s</li>'
           '</ol>' % (cite('speech', 'ht'), cite('speech', 'ht'), cite('speech', 'ht'), cite('speech', 'ht'),
                      cite('infinity', 'saca', 'ktmpost'), cite('saca'), cite('infinity', 'saca')))

out.append('<div class="note"><b>Fuel rates: tariff book vs concession.</b>\n'
           'The 2026/27 tariff book prints the full schedule rates: %s. '
           'The Finance Bill 2083 concession halves these: Infinity Law&rsquo;s summary gives Rs 12,600 per KL for petrol and '
           'Rs 6,000 per KL for kerosene and high-speed diesel.%s Because the government can change the concession by '
           'gazette notice, confirm the rate in force on your import date with the customs office.</div>'
           % ('; '.join('%s (%s) %s' % (esc(name), code, esc(fmt_fuel(rate))) for code, name, rate in fuel_rows),
              cite('infinity')))

out.append('<h3 class="head">Why there is no line-by-line comparison here</h3>')
out.append('<p>A true line-by-line diff needs both years&rsquo; tariff schedules in machine-readable form. Customs Nepal '
           'holds the full 2026/27 schedule but not the 2082/83 one, and the budget documents do not list the 273 raw '
           'materials item by item. Rather than guess, this page states only changes we can cite. To see the rate in '
           'force for your product, look up its HS code (below) — the site always shows the current 2026/27 rate.</p>')

# --- the new tariff in numbers (repo data)
out.append('<h2 class="sec">The 2026/27 tariff in numbers</h2>')
out.append('<p>Computed from the official Customs Tariff 2026/27 (HS 2022, seventh edition) as transcribed on this site: '
           '<b>%s tariff lines</b> across <b>%d chapters</b>. The general duty column uses exactly <b>seven ad-valorem '
           'rates</b> — matching the seven-tier structure announced in the budget — plus <b>%d lines</b> with specific '
           'per-unit or &ldquo;whichever is higher&rdquo; rates (mainly beverages and alcohol, fruit juices, tobacco and fuels).</p>'
           % (format(n_lines, ','), n_chapters, n_specific))
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>General duty rate</th><th>Tariff lines</th>'
           '<th>Share of lines</th></tr></thead><tbody>')
for t in tiers:
    cls = 'd-free' if t == 0 else 'd-low' if t <= 10 else 'd-mid' if t <= 20 else 'd-hi'
    out.append('<tr><td><span class="duty %s">%s</span></td><td>%s</td><td>%.1f%%</td></tr>'
               % (cls, fmt_rate(t), format(adval[t], ','), 100.0 * adval[t] / n_lines))
out.append('<tr><td><span class="duty d-spec">Specific / compound</span></td><td>%s</td><td>%.1f%%</td></tr>'
           % (format(n_specific, ','), 100.0 * n_specific / n_lines))
out.append('</tbody></table></div>')
out.append('<p class="fineprint">The SAARC (SAFTA) preferential column has its own rates and is not part of the '
           'seven-tier count. See <a href="/safta">how SAFTA duty works</a>.</p>')

# --- how to look up
out.append('<h2 class="sec">How to find any HS code&rsquo;s 2083/84 rate</h2>')
out.append('<ol class="exsteps">'
           '<li><b>Search</b> the product name (English or Nepali) or the HS code on the <a href="/">home page</a>. '
           'Each result shows the 2026/27 general and SAARC customs duty.</li>'
           '<li><b>Browse by chapter</b> in the <a href="/tariff">full Customs Tariff %s</a> if you know roughly where '
           'the product sits.</li>'
           '<li><b>Estimate the landed cost</b> with the <a href="/calculator">duty &amp; VAT calculator</a>: customs duty, '
           '13%% VAT on value plus duty, and the total in rupees.</li>'
           '<li><b>Not sure of the code?</b> Describe the product to <a href="/ask-ai">Ask AI</a> for ranked HS code '
           'suggestions, then confirm with your clearing agent.</li></ol>' % YEAR)

# --- FAQ
out.append('<h2 class="sec">Frequently asked questions</h2>')
for q, a in FAQS:
    out.append('<h3 class="head">%s</h3><p>%s</p>' % (esc(q), esc(a)))

# --- sources
out.append('<h2 class="sec">Sources</h2><ol class="exsteps">')
for i, k in enumerate(ORDER):
    name, url = SOURCES[k]
    out.append('<li id="src-%d">%s</li>' % (i + 1, ext(url, esc(name))))
out.append('</ol>')
out.append('<p class="fineprint">Tariff figures on this page are computed from the Department of Customs&rsquo; Customs '
           'Tariff 2026/27 as transcribed by Customs Nepal; changes versus 2082/83 are reported from the sources above. '
           'Page last reviewed %s.</p>' % TODAY)
out.append('<div class="tools"><a class="btn" href="/tariff">Full tariff by chapter</a>'
           '<a class="btn ghost" href="/import-duty">Import duty by product</a>'
           '<a class="btn ghost" href="/faq">Customs FAQ</a></div>')
out.append('</div>' + FOOT)
(pub / 'tariff' / '2083-84-changes.html').write_text(''.join(out), encoding='utf-8')

# ---------------- inject URL into sitemap.xml ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rowx = ('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>'
        % (SITE, PATH, TODAY))
if PATH + '</loc>' not in sm:
    sm = sm.replace('</urlset>', rowx + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('tariff_changes_page: %s built — %d lines, %d ad-valorem tiers %s, %d specific-rate lines; +1 sitemap URL'
      % (PATH, n_lines, len(tiers), tiers, n_specific))
