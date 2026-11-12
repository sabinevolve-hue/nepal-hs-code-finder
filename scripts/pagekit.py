"""Shared page chrome for newer static generators (head, breadcrumb, money formatting).

Older generators each carry their own copy of page_head(); new ones should import from here instead
of adding another. Keep the <head> in step with country_pages.py.
"""
import json, html, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
SITE = 'https://www.customsnepal.com'
esc = lambda s: html.escape(str(s), quote=True)
sys.path.insert(0, str(root / 'scripts'))
from nav import render_nav, OTHER_SITES

def money(th):
    """Rs '000 -> Nepali-unit rupee string."""
    r = float(th or 0) * 1000.0
    neg = r < 0
    r = abs(r)
    if r >= 1e11:
        s = 'Rs %.2f kharba' % (r / 1e11)
    elif r >= 1e9:
        s = 'Rs %.2f arba' % (r / 1e9)
    elif r >= 1e7:
        s = 'Rs %.1f crore' % (r / 1e7)
    elif r >= 1e5:
        s = 'Rs %.0f lakh' % (r / 1e5)
    else:
        s = 'Rs %.0f' % r
    return ('−' + s) if neg else s

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")
def page_head(title, desc, path, breadcrumb, extra_ld=None, og=None):
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
        '<meta property="og:image" content="' + SITE + (og or '/og.png') + '">'
        + ('<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if og else '') +
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="icon" href="' + FAVICON + '"><link rel="apple-touch-icon" href="/icon-180.png">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&display=swap">'
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


def foot(source_line):
    return ('<footer><div class="wrap"><p>' + source_line + '</p>'
            '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
            '<p><a href="/">Home</a> · <a href="/trade-partners">Trade partners</a> · <a href="/customs-offices">Customs offices</a> · <a href="/sectors">Sectors</a> · '
            '<a href="/import-duty">Import duty</a> · <a href="/calculator">Calculator</a> · <a href="/tariff">Tariff</a> · © customsnepal.com</p>'
            + OTHER_SITES + '</div></footer><script src="/cn-tools.js" defer></script></body></html>')


def add_to_sitemap(paths):
    """Insert <url> entries for paths not already present (exact <loc> match). Returns how many were added."""
    import datetime
    sm = pub / 'sitemap.xml'
    x = sm.read_text(encoding='utf-8')
    today = datetime.date.today().isoformat()
    new = ''.join('<url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (SITE, p, today)
                  for p in paths if '<loc>%s%s</loc>' % (SITE, p) not in x)
    sm.write_text(x.replace('</urlset>', new + '</urlset>'), encoding='utf-8')
    return new.count('<url>')
