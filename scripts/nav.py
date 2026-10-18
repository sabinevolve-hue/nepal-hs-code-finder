"""Shared top navigation for every static SEO generator
(seo_pages, export_pages, shipping_pages, trade_pages, safta_page).

Single source of truth so the menu bar is identical on every static page AND
matches the SPA header (``.nav-desk`` in src.html). If you change NAV here,
change that SPA header too — keep the two in lock-step.
"""

# (href, label) in the SAME order the SPA desktop nav uses.
NAV = [
    ('/', 'Search'), ('/ask-ai', 'Ask AI'), ('/imports', 'Imports'), ('/exports', 'Exports'),
    ('/trade-data', 'Trade'), ('/browse', 'Browse'), ('/tariff', 'Tariff'), ('/calculator', 'Calculator'),
    ('/export', 'Export guides'), ('/shipping', 'Shipping'), ('/safta', 'SAFTA'), ('/world', 'World ↗'),
]

# A nav item is "current" on its own page and on any page beneath it.
_PREFIX = {
    '/tariff': '/tariff', '/export': '/export', '/shipping': '/shipping',
    '/trade-data': '/trade', '/safta': '/safta', '/world': '/world',
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
