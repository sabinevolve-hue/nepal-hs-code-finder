"""Inline data JSON into src.html and write public/index.html (single self-contained page),
plus public/robots.txt and public/sitemap.xml. This is the ONLY build step.

The <head> (title, meta description, canonical, Open Graph, Twitter, JSON-LD) is assembled
HERE so it lives inside <head> — src.html only carries the <body> content and inline data.
Nothing below changes the site's visual design, layout or fonts.
"""
import pathlib, re, json, datetime
root = pathlib.Path(__file__).resolve().parents[1]
src = (root / 'src.html').read_text(encoding='utf-8')
data = (root / 'data' / 'tariff.json').read_text(encoding='utf-8').replace('</', '<\\/')
stats = (root / 'data' / 'stats.json').read_text(encoding='utf-8').replace('</', '<\\/')
offices = (root / 'data' / 'offices.json').read_text(encoding='utf-8').replace('</', '<\\/')
page = src.replace('/*DATA*/', data).replace('/*STATS*/', stats).replace('/*OFFICES*/', offices)

# ---------------------------------------------------------------------------
# SEO constants
# ---------------------------------------------------------------------------
SITE = 'https://www.customsnepal.com'
TITLE = 'Nepal HS Code Finder — Customs Tariff & Import Duty 2026/27'
DESC = ('Find the Nepal HS code, customs duty, VAT and landed cost for any product. '
        'Search the full Customs Tariff 2026/27, explore trade data and generate a '
        'proforma invoice — free.')
OGIMG = SITE + '/og.png'
TODAY = datetime.date.today().isoformat()

# JSON-LD: Organization + WebSite (with a sitelinks SearchAction that maps to /?q=)
LD = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "Organization", "@id": SITE + "/#org", "name": "Customs Nepal",
         "url": SITE + "/", "logo": OGIMG, "description": DESC},
        {"@type": "WebSite", "@id": SITE + "/#website", "name": "Nepal HS Code Finder",
         "alternateName": "Customs Nepal", "url": SITE + "/", "inLanguage": "en",
         "publisher": {"@id": SITE + "/#org"},
         "potentialAction": {"@type": "SearchAction",
                             "target": {"@type": "EntryPoint", "urlTemplate": SITE + "/?q={search_term_string}"},
                             "query-input": "required name=search_term_string"}},
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
    # Open Graph
    '<meta property="og:type" content="website">'
    '<meta property="og:site_name" content="Customs Nepal">'
    '<meta property="og:title" content="' + esc(TITLE) + '">'
    '<meta property="og:description" content="' + esc(DESC) + '">'
    '<meta property="og:url" content="' + SITE + '/">'
    '<meta property="og:image" content="' + OGIMG + '">'
    '<meta property="og:image:width" content="1200">'
    '<meta property="og:image:height" content="630">'
    '<meta property="og:image:alt" content="Nepal HS Code Finder — Customs Tariff, Import Duty & Landed Cost">'
    '<meta property="og:locale" content="en_NP">'
    # Twitter
    '<meta name="twitter:card" content="summary_large_image">'
    '<meta name="twitter:title" content="' + esc(TITLE) + '">'
    '<meta name="twitter:description" content="' + esc(DESC) + '">'
    '<meta name="twitter:image" content="' + OGIMG + '">'
    # Icons
    '<link rel="icon" href="' + FAVICON + '">'
    '<link rel="apple-touch-icon" href="/icon-180.png">'
    # Structured data
    '<script type="application/ld+json">' + LD_JSON + '</script>'
    + ANALYTICS +
    '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
    '</head><body>')

(root / 'public').mkdir(exist_ok=True)
(root / 'public' / 'index.html').write_text(head + page + '</body></html>', encoding='utf-8')

# ---------------------------------------------------------------------------
# robots.txt + sitemap.xml (regenerated every build so they stay in sync)
# ---------------------------------------------------------------------------
robots = ("User-agent: *\n"
          "Allow: /\n\n"
          "Sitemap: " + SITE + "/sitemap.xml\n")
(root / 'public' / 'robots.txt').write_text(robots, encoding='utf-8')

sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url><loc>' + SITE + '/</loc><lastmod>' + TODAY + '</lastmod>'
           '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
           '</urlset>\n')
(root / 'public' / 'sitemap.xml').write_text(sitemap, encoding='utf-8')

print('wrote public/index.html', len(page) // 1024, 'KB  + robots.txt + sitemap.xml')
