"""Inline data JSON into src.html and write public/index.html (single self-contained page),
plus public/robots.txt and public/sitemap.xml. This is the ONLY build step.

The <head> (title, meta description, canonical, Open Graph, Twitter, JSON-LD) is assembled
HERE so it lives inside <head> — src.html only carries the <body> content and inline data.
Nothing below changes the site's visual design, layout or fonts.
"""
import pathlib, re, json, datetime, os
root = pathlib.Path(__file__).resolve().parents[1]
src = (root / 'src.html').read_text(encoding='utf-8')
# keep the SPA footer's "Explore" links identical to the static pages' (single source: scripts/links.py)
import sys
sys.path.insert(0, str(root / 'scripts'))
import links as _links
import nav as _nav, html as _html
src = re.sub(r'<!--GNAV-->.*?<!--/GNAV-->', lambda m: '<!--GNAV-->' + _nav.render_nav('/', lambda s: _html.escape(str(s), quote=True), spa=True) + '<!--/GNAV-->', src, flags=re.S)
src = re.sub(r'/\*GNAVCSS\*/.*?/\*/GNAVCSS\*/', lambda m: '/*GNAVCSS*/' + _nav.NAV_CSS + '/*/GNAVCSS*/', src, flags=re.S)
import home_info as _home
src = re.sub(r'<!--HOMEINFO-->.*?<!--/HOMEINFO-->', lambda m: '<!--HOMEINFO-->' + _home.build() + '<!--/HOMEINFO-->', src, flags=re.S)
src = re.sub(r'/\*HOMECSS\*/.*?/\*/HOMECSS\*/', lambda m: '/*HOMECSS*/' + _home.CSS + '/*/HOMECSS*/', src, flags=re.S)
src = re.sub(r'<!--EXPLORE-->.*?<!--/EXPLORE-->', lambda m: '<!--EXPLORE-->' + _links.explore_footer() + '<!--/EXPLORE-->', src, flags=re.S)
# Data (tariff/stats/offices/integrated) is no longer inlined into the HTML. It is written to
# separate files below and fetched async by the app (__boot), so the HTML shell stays small and
# paints fast — important on Nepal mobile networks. Keeps the big 1.7 MB trade stats off the
# critical first paint and lets the service worker cache each file independently.
page = src
DATA_FILES = [('tariff.json', 't.json'), ('stats.json', 'st.json'),
              ('offices.json', 'of.json'), ('integrated.json', 'int.json')]

# ---------------------------------------------------------------------------
# SEO constants
# ---------------------------------------------------------------------------
SITE = 'https://www.customsnepal.com'
# Head terms from Search Console: "hs code nepal", "nepal customs tariff", "custom tariff nepal",
# "nepal bhansar rate". Tariff = Customs Tariff 2026/27 published by the Department of Customs = FY 2083/84 BS.
TITLE = 'HS Code Nepal & Nepal Customs Tariff 2083/84 | Customs Nepal'
DESC = ('Search any HS code in the official Nepal Customs Tariff 2083/84 (2026/27): import duty (bhansar rate), '
        'SAARC rate, 13% VAT and landed cost for all 6,340 tariff lines. Free calculator and AI HS classifier.')
OGIMG = SITE + '/og.png'
TODAY = datetime.date.today().isoformat()
# Google Search Console HTML-tag verification (optional fallback; GA4 verification needs none).
# Set env GSC_VERIFICATION="<token>" at build time to emit the meta tag.
GSC = os.environ.get('GSC_VERIFICATION', '').strip()

# FAQ — single source of truth (shared with seo_pages.py and the visible About FAQ)
FAQ = json.loads((root / 'data' / 'faq.json').read_text(encoding='utf-8'))['faqs']

# JSON-LD graph: Organization + WebSite + SoftwareApplication + FAQPage.
# The FAQ answers mirror the visible FAQ rendered in index.html (#v-about), so the
# structured data has matching on-page content. This is the data AI answer engines
# (ChatGPT, Claude, Perplexity, Gemini) and Google read to understand and cite the site.
LD = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "Organization", "@id": SITE + "/#org", "name": "Customs Nepal",
         "url": SITE + "/", "logo": OGIMG, "description": DESC,
         "areaServed": {"@type": "Country", "name": "Nepal"},
         "contactPoint": {"@type": "ContactPoint", "email": "info@customsnepal.com",
                          "contactType": "customer support", "areaServed": "NP",
                          "availableLanguage": ["English", "Nepali"]},
         "knowsAbout": ["Nepal HS codes", "Nepal customs tariff", "import duty", "VAT",
                        "landed cost", "SAARC preferential duty", "customs classification",
                        "Nepal foreign trade statistics"]},
        {"@type": "WebSite", "@id": SITE + "/#website", "name": "Customs Nepal",
         "alternateName": "Nepal HS Code Finder", "url": SITE + "/", "inLanguage": "en",
         "publisher": {"@id": SITE + "/#org"},
         "potentialAction": {"@type": "SearchAction",
                             "target": {"@type": "EntryPoint", "urlTemplate": SITE + "/?q={search_term_string}"},
                             "query-input": "required name=search_term_string"}},
        {"@type": "SoftwareApplication", "@id": SITE + "/#app", "name": "Customs Nepal",
         "alternateName": "Nepal HS Code Finder", "url": SITE + "/", "description": DESC,
         "applicationCategory": "BusinessApplication", "operatingSystem": "Web, Android",
         "inLanguage": ["en", "ne"], "isAccessibleForFree": True,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "NPR"},
         "featureList": ["HS code search", "Import duty and VAT calculator", "Landed-cost estimator",
                         "AI HS code classifier", "Proforma and commercial invoice generator",
                         "Nepal import and export trade data"],
         "publisher": {"@id": SITE + "/#org"}},
        {"@type": "FAQPage", "@id": SITE + "/#faq", "inLanguage": "en",
         "isPartOf": {"@id": SITE + "/#website"},
         "mainEntity": [{"@type": "Question", "name": f["q"],
                         "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in FAQ]},
    ],
}
LD_JSON = json.dumps(LD, ensure_ascii=False).replace('</', '<\\/')

# Analytics (Google Analytics 4 + Vercel Web Analytics). Guarded to the live domain only, so the
# standalone artifact/preview copy and local file:// never load trackers or send phantom data.
ANALYTICS = (
    "<script>(function(){var h=location.hostname;"
    "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
    "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
    "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
    "var v=document.createElement('script');v.defer=true;v.src='/_vercel/insights/script.js';document.head.appendChild(v);"
    "})();</script>"
)

# Service worker registration (installable PWA + offline). Registered only on the live domain,
# its vercel.app mirror, or localhost, so the standalone/preview copy never tries to register.
SW_REG = (
    "<script>(function(){if(!('serviceWorker' in navigator))return;"
    "var h=location.hostname;"
    "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0&&h!=='localhost'&&h!=='127.0.0.1')return;"
    "window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){})});"
    "})();</script>"
)

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")

def esc(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

# standalone page: build the <head> the artifact host normally supplies, now with full SEO metadata
head = (
    '<!doctype html><html lang="en"><head>'
    '<meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<meta name="theme-color" content="#0F172A">'
    '<title>' + esc(TITLE) + '</title>'
    '<meta name="description" content="' + esc(DESC) + '">'
    '<link rel="canonical" href="' + SITE + '/">'
    '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">'
    '<meta name="author" content="Customs Nepal">'
    + ('<meta name="google-site-verification" content="' + esc(GSC) + '">' if GSC else '') +
    # Open Graph
    '<meta property="og:type" content="website">'
    '<meta property="og:site_name" content="Customs Nepal">'
    '<meta property="og:title" content="' + esc(TITLE) + '">'
    '<meta property="og:description" content="' + esc(DESC) + '">'
    '<meta property="og:url" content="' + SITE + '/">'
    '<meta property="og:image" content="' + OGIMG + '">'
    '<meta property="og:image:width" content="1200">'
    '<meta property="og:image:height" content="630">'
    '<meta property="og:image:alt" content="Customs Nepal — Customs Tariff, Import Duty & Landed Cost">'
    '<meta property="og:locale" content="en_NP">'
    # Twitter
    '<meta name="twitter:card" content="summary_large_image">'
    '<meta name="twitter:title" content="' + esc(TITLE) + '">'
    '<meta name="twitter:description" content="' + esc(DESC) + '">'
    '<meta name="twitter:image" content="' + OGIMG + '">'
    # Icons
    '<link rel="icon" href="' + FAVICON + '">'
    '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">'
    '<link rel="apple-touch-icon" href="/icon-180.png">'
    # PWA (installable app) — manifest + platform hints
    '<link rel="manifest" href="/manifest.webmanifest">'
    '<meta name="application-name" content="Customs Nepal">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
    '<meta name="apple-mobile-web-app-title" content="Customs Nepal">'
    # Structured data
    '<script type="application/ld+json">' + LD_JSON + '</script>'
    + ANALYTICS + SW_REG +
    '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html,body{overflow-x:hidden}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
    '</head><body>')

# Inject the visible FAQ (same source as the FAQPage JSON-LD) into the About section,
# so the homepage structured data has matching on-page content and in-app users see it too.
FAQ_HTML = ('<h2>Frequently asked questions</h2>'
            + ''.join('<h3>' + esc(f['q']) + '</h3><p>' + esc(f['a']) + '</p>' for f in FAQ))
page = page.replace('<!--FAQ-->', FAQ_HTML)

(root / 'public').mkdir(exist_ok=True)

# ---- move the big inline blocks into content-hashed, long-cached files ----
# Every app route (/, /calculator, /imports, …) is a copy of this shell; inline, the 160 KB app script and 57 KB
# stylesheet were re-downloaded on each. As /assets/<name>.<hash>.<ext> they are fetched once and cached for a
# year (vercel.json). Scripts keep their order and become `defer`, so they still run after the DOM is parsed, in
# the same sequence: charts library -> app -> account. The links between them (window.CN) are used on click only.
import hashlib
ASSETS = root / 'public' / 'assets'
ASSETS.mkdir(exist_ok=True)
for _old in ASSETS.glob('*'):
    if re.match(r'^(app|account)\.[0-9a-f]{10}\.(js|css)$', _old.name):
        _old.unlink()
def _asset(name, ext, body):
    h = hashlib.sha256(body.encode('utf-8')).hexdigest()[:10]
    (ASSETS / ('%s.%s.%s' % (name, h, ext))).write_text(body, encoding='utf-8')
    return '/assets/%s.%s.%s' % (name, h, ext)
_m = re.search(r'<style>(\n/\* Layout: .*?)</style>', page, re.S)
assert _m, 'main stylesheet not found'
page = page[:_m.start()] + '<link rel="stylesheet" href="%s">' % _asset('app', 'css', _m.group(1)) + page[_m.end():]
_ec = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'
assert page.count(_ec) == 1, 'echarts tag changed'
page = page.replace(_ec, _ec.replace('<script ', '<script defer '))
_m = re.search(r'<script>(\n\(function\(\)\{\nasync function __boot\(\)\{.*?)</script>', page, re.S)
assert _m, 'app script not found'
page = page[:_m.start()] + '<script defer src="%s"></script>' % _asset('app', 'js', _m.group(1)) + page[_m.end():]
_m = re.search(r'<script>(\n\(function\(\)\{\n  var URL_=.*?)</script>', page, re.S)
assert _m, 'account script not found'
page = page[:_m.start()] + '<script defer src="%s"></script>' % _asset('account', 'js', _m.group(1)) + page[_m.end():]

(root / 'public' / 'index.html').write_text(head + page + '</body></html>', encoding='utf-8')
# write the data files the app fetches (see __boot in src.html)
for _src, _out in DATA_FILES:
    (root / 'public' / _out).write_text((root / 'data' / _src).read_text(encoding='utf-8'), encoding='utf-8')

# ---------------------------------------------------------------------------
# robots.txt + sitemap.xml (regenerated every build so they stay in sync)
# ---------------------------------------------------------------------------
# We actively WELCOME AI search / answer engines (GEO). "User-agent: *" already allows
# everyone; the named Allow blocks below make the intent explicit and future-proof the site
# against accidental AI blocking, so ChatGPT, Claude, Perplexity, Gemini, Copilot, Apple
# Intelligence, etc. may crawl, index and cite the tariff data.
AI_AGENTS = [
    "Googlebot",                                          # Google Search (AI Overviews / AI Mode)
    "GPTBot", "OAI-SearchBot", "ChatGPT-User",            # OpenAI (training, search, browsing)
    "ClaudeBot", "anthropic-ai", "Claude-Web", "Claude-User", "Claude-SearchBot",  # Anthropic
    "PerplexityBot", "Perplexity-User",                   # Perplexity
    "Google-Extended",                                    # Google Gemini / Vertex
    "Applebot-Extended",                                  # Apple Intelligence
    "Amazonbot", "Bingbot", "DuckAssistBot",              # Amazon, Microsoft Copilot, DuckDuckGo
    "meta-externalagent", "MistralAI-User", "cohere-ai", "CCBot",  # Meta, Mistral, Cohere, Common Crawl
    "Applebot", "DuckDuckBot", "Meta-ExternalFetcher", "Google-CloudVertexBot", "YouBot", "PetalBot",  # Siri/Spotlight, DDG, Meta AI fetch, Vertex, You.com, Petal
]
robots = ["# Customs Nepal (customsnepal.com) — crawling and indexing is welcome, including AI answer engines.",
          "", "User-agent: *", "Allow: /", ""]
for ua in AI_AGENTS:
    robots += ["User-agent: " + ua, "Allow: /", ""]
robots += ["Sitemap: " + SITE + "/sitemap.xml", ""]
(root / 'public' / 'robots.txt').write_text("\n".join(robots), encoding='utf-8')

# llms.txt — the emerging llmstxt.org standard: a concise, curated Markdown map of the site
# plus the key authoritative facts, so AI assistants can ground answers about Nepal customs
# on this source and link to the right page.
llms = """# Customs Nepal

> Customs Nepal (customsnepal.com) is a free tool to find the Nepal HS code, customs duty, VAT (13%) and total landed cost for any product, using the official Customs Tariff 2026/27 (FY 2083/84 BS, HS 2022 nomenclature). It also offers an AI HS-code classifier, a proforma/commercial invoice generator and Nepal import/export trade data.

Customs Nepal is an independent, privately operated reference tool. It is NOT a government website and is not affiliated with the Government of Nepal. Official sources: the Department of Customs (https://www.customs.gov.np) and the Ministry of Finance (https://www.mof.gov.np). Rates are shown as published and should be confirmed with the customs office or a clearing agent before any binding decision.

## Main pages
- [HS code search (home)](__SITE__/): Search the full Nepal Customs Tariff by product name, material or code, in English or Nepali.
- [Customs Tariff 2026/27 — all chapters](__SITE__/tariff): Browse every chapter of the tariff with general and SAARC import-duty rates.
- [Customs Tariff 2083/84 (2026/27): what changed](__SITE__/tariff/2083-84-changes): What changed in Nepal's customs tariff for FY 2083/84 — duty tiers cut from 11 to 7, lower duty on 273 industrial raw materials, customs-point levies merged into a green tax, the 50% fuel duty concession — with the official PDF link and cited sources.
- [Duty & landed-cost calculator](__SITE__/calculator): Estimate customs duty, VAT and total landed cost in rupees for any HS code.
- [Ask AI — HS code classifier](__SITE__/ask-ai): Describe a product in plain words and get ranked HS code suggestions with reasoning.
- [Nepal's trade partners](__SITE__/trade-partners): Nepal's imports, exports and balance with each trading partner country (Department of Customs), with a page per country at __SITE__/trade-partner/<country> (for example __SITE__/trade-partner/india, __SITE__/trade-partner/china): top products, customs revenue collected, competing suppliers and how goods move.
- [Import duty by product name](__SITE__/import-duty): Plain-name pages (air conditioner, laptop, solar panel, gold, car…) at __SITE__/import-duty/<name> that group every HS line for that product with its general and SAARC duty, 13% VAT and a worked landed-cost example; plus one page per 8-digit tariff line.
- [Imports](__SITE__/imports): Nepal import data and duty by product category and partner country.
- [Exports](__SITE__/exports): Nepal export data by product category and destination.
- [Export guides](__SITE__/export): Step-by-step guides to exporting from Nepal — procedures, documents, EXIM code, certificate of origin and product-specific notes.
- [SAFTA preferential duty](__SITE__/safta): How Nepal importers cut customs duty under the SAFTA agreement — eligible SAARC origins, rules of origin, certificate of origin, the sensitive list, and the product segments that benefit most.
- [Shipping to Nepal](__SITE__/shipping): Landlocked Nepal's sea–land freight routes — the Indian and Bangladeshi gateway ports (Kolkata/Haldia, Visakhapatnam, Nhava Sheva, Mundra, Mongla, Chittagong) and the inland customs points (Birgunj, Biratnagar, Bhairahawa, Kakarbhitta, Chobhar).
- [Track a shipment](__SITE__/shipping/track): Paste a container number or bill-of-lading number to identify the carrier (ISO 6346 check digit + owner-prefix / B/L-prefix match) and jump to the right carrier tracking page.
- [World HS codes & global trade](https://world.customsnepal.com/): International HS 2022 codes and the trade of 207 economies, with Nepal's trade seen against world flows (BACI benchmark data).
- [Trade data](__SITE__/trade-data): Multi-year Nepal foreign-trade statistics.
- [FAQ](__SITE__/faq): Common questions on HS codes, customs duty, VAT and landed cost in Nepal.
- [About](__SITE__/about): What Customs Nepal is, who it is for, and its data sources.

## Key facts about Nepal customs
- Nepal HS codes are 8 digits, written in dotted groups (for example 0101.21.00). The first 6 digits are the international HS subheading; Nepal adds the last 2 for national tariff lines.
- The standard VAT rate in Nepal is 13%. On imports, VAT is charged on the assessable value plus customs duty (plus excise where it applies).
- Customs duty is a percentage of the assessable (CIF) value of the goods. Each HS code has its own general rate.
- A lower SAARC (SAFTA) preferential duty rate may apply to qualifying goods from SAARC countries, subject to rules of origin and a certificate of origin.
- Depending on the product, imports may also attract excise duty and an agriculture reform fee.
- Landed cost = product price + freight + insurance + customs duty + VAT + any other import taxes and fees.

## Key facts about SAFTA (preferential duty)
- SAFTA is the South Asian Free Trade Area agreement among SAARC members (India, Pakistan, Bangladesh, Sri Lanka, Nepal, Bhutan, Maldives, Afghanistan). Qualifying goods pay the lower SAARC duty column instead of the general rate.
- To claim the SAARC rate, the importer needs a SAFTA Certificate of Origin issued in the exporting country. It is valid for 12 months from the date of issue.
- Rules of origin: the general rule is a change of tariff heading (CTH) at 4-digit HS level plus at least 40% domestic value addition; for least-developed members (which include Nepal) the value-addition threshold is 30%.
- Each country keeps a Sensitive List of products excluded from SAFTA concessions; goods on the importing country's sensitive list do not get the preferential rate.
- Nepal's graduation from least-developed-country (LDC) status was originally due in November 2026; on 29-30 October 2026 the UN General Assembly extended its preparatory period by three years, so Nepal now remains an LDC until 24 November 2029. Until then the LDC concessions (such as the 30% SAFTA value-addition threshold) continue to apply.

## Key facts about shipping to Nepal
- Nepal is landlocked, so almost all overseas cargo arrives by sea at an Indian or Bangladeshi port and then moves overland to an inland customs point in Nepal.
- Main gateway ports: Kolkata and Haldia, Visakhapatnam, Nhava Sheva (JNPT) and Mundra in India, and Mongla and Chittagong in Bangladesh.
- Main inland customs points / ICDs: Birgunj (Sirsiya ICD, the largest, rail-linked to Kolkata/Haldia), Biratnagar, Bhairahawa, Kakarbhitta and the Chobhar dry port near Kathmandu.
- A container number is four letters plus seven digits with an ISO 6346 check digit (for example ABCU1234567); the first three letters are the owner/carrier prefix. A bill-of-lading number usually starts with a carrier prefix (for example ONEY for Ocean Network Express, MEDU for MSC, MAEU for Maersk).

## Related sites
- [world.customsnepal.com](https://world.customsnepal.com/): World HS codes and global trade data by country and product — the international companion to this site (its own llms.txt: https://world.customsnepal.com/llms.txt).
- [nepalpublicdata.com](https://nepalpublicdata.com/): Nepal public statistics — population, budget, trade and places (budget explainer at https://nepalpublicdata.com/budget/).
""".replace('__SITE__', SITE)
(root / 'public' / 'llms.txt').write_text(llms, encoding='utf-8')

sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url><loc>' + SITE + '/</loc><lastmod>' + TODAY + '</lastmod>'
           '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
           '</urlset>\n')
(root / 'public' / 'sitemap.xml').write_text(sitemap, encoding='utf-8')

print('wrote public/index.html', len(page) // 1024, 'KB  + robots.txt + llms.txt + sitemap.xml  (%d FAQ)' % len(FAQ))
