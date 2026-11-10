"""Shared top navigation for every static SEO generator
(seo_pages, export_pages, shipping_pages, trade_pages, safta_page).

Single source of truth so the menu bar is identical on every static page AND
matches the SPA header (``.nav-desk`` in src.html). If you change NAV here,
change that SPA header too — keep the two in lock-step.
"""

# world.customsnepal.com is its own site (the canonical copy of every world page); link it directly
# rather than via the customsnepal.com/world SPA mount.
WORLD_SITE = 'https://world.customsnepal.com'

# (href, label) in the SAME order the SPA desktop nav uses.
NAV = [
    ('/', 'Search'), ('/ask-ai', 'Ask AI'), ('/imports', 'Imports'), ('/exports', 'Exports'),
    ('/trade-data', 'Trade'), ('/trade-partners', 'Partners'), ('/browse', 'Browse'), ('/tariff', 'Tariff'), ('/calculator', 'Calculator'),
    ('/export', 'Export guides'), ('/shipping', 'Shipping'), ('/safta', 'SAFTA'), (WORLD_SITE + '/', 'World ↗'),
]

# A nav item is "current" on its own page and on any page beneath it.
_PREFIX = {
    '/tariff': '/tariff', '/export': '/export', '/shipping': '/shipping',
    '/trade-data': '/trade-data', '/trade-partners': '/trade-partner', '/safta': '/safta',
}


def cur(path, h):
    if path == h:
        return True
    p = _PREFIX.get(h)
    return bool(p and path.startswith(p))


def render_nav(path, esc):
    """Build the <a> run for <nav class="topnav">; esc is the caller's HTML escaper."""
    return ''.join(
        '<a href="%s"%s>%s</a>' % (h, ' class="cur"' if cur(path, h) else '', esc(l))
        for h, l in NAV
    )


# Footer "Our other sites" block — the sibling sites of the Nepal-data cluster (see the AI-search / site-network
# spec): plain followed links, anchor = the site's role + domain, max 3-4 links. Same text in the SPA footer
# (src.html) and on world.customsnepal.com (scripts/world_prerender.py FOOTER). No links to the LED/AV sites.
OTHER_SITES_LINKS = [
    (WORLD_SITE + '/', 'World HS codes &amp; global trade data by country and product — world.customsnepal.com'),
    ('https://nepalpublicdata.com/', 'Nepal public statistics: population, budget, trade &amp; places — nepalpublicdata.com'),
]
# The "Explore" lines (trade partners + duty-by-product-name) ride in the same constant so every main-site
# footer gets them without touching each generator. world_prerender.py has its own FOOTER (other host).
from links import explore_footer
OTHER_SITES = explore_footer() + ('<p class="other-sites"><b>Our other sites:</b> '
               + ' · '.join('<a href="%s">%s</a>' % (h, l) for h, l in OTHER_SITES_LINKS) + '</p>')
