"""Shared top navigation for every static SEO generator
(seo_pages, export_pages, shipping_pages, trade_pages, safta_page).

Single source of truth so the menu bar is identical on every static page AND
matches the app shell: assemble.py injects the same menu into src.html. Change GROUPS here only.
"""

# world.customsnepal.com is its own site (the canonical copy of every world page); link it directly
# rather than via the customsnepal.com/world SPA mount.
WORLD_SITE = 'https://world.customsnepal.com'

# ---------------------------------------------------------------------------------------------------
# Four doors instead of thirteen tabs. ONE definition drives the header on every static page (render_nav)
# and the app shell (assemble.py injects render_nav(spa=True) between <!--GNAV--> markers in src.html).
# item: (href, label, one-line hint, SPA tab id or '')  — a tab id makes the link switch views inside the
# app without a page load (src.html binds every [data-tab]).
# ---------------------------------------------------------------------------------------------------
GROUPS = [
    ('find', 'Find', '🔎', 'HS codes and tariff', [
        ('/', 'Search', 'HS code and duty for any product', 'search'),
        ('/ask-ai', 'Ask AI', 'Describe it, get the code', 'ai'),
        ('/tariff', 'Tariff by chapter', 'All 97 chapters with rates', ''),
        ('/import-duty', 'Duty by product name', 'Mobile, car, laptop, gold…', ''),
        ('/browse', 'Browse', 'Chapters and customs offices', 'browse'),
    ]),
    ('cost', 'Cost', '🧮', 'Duty, VAT and landed cost', [
        ('/calculator', 'Landed-cost calculator', 'Duty, VAT and total in rupees', 'calc'),
        ('/invoice', 'Invoice maker', 'Proforma and commercial invoice', 'invoice'),
        ('/safta', 'SAFTA lower duty', 'Cheaper rates from South Asia', ''),
        ('/tariff/2083-84-changes', 'What changed in 2083/84', 'This year’s tariff changes', ''),
    ]),
    ('trade', 'Trade', '🌍', 'Who, what and how much', [
        ('/trade-partners', 'Countries', 'Nepal’s trade with each country', ''),
        ('/sectors', 'Sectors', 'Import markets and export industries', ''),
        ('/customs-offices', 'Customs offices', 'What each border point handles', ''),
        ('/compare', 'Compare two countries', 'Side by side', ''),
        ('/imports', 'Imports explorer', 'Every imported product', 'imports'),
        ('/exports', 'Exports explorer', 'Every exported product', 'exports'),
        ('/trade-data', 'Trade data by year', 'Seven years of totals', 'stats'),
        (WORLD_SITE + '/', 'World trade ↗', 'Global HS codes and flows', ''),
    ]),
    ('move', 'Move', '🚢', 'Shipping and exporting', [
        ('/shipping', 'Shipping routes', 'Ports, dry ports and transit', ''),
        ('/shipping/track', 'Track a shipment', 'Container, air waybill, courier', ''),
        ('/the-border', 'The Border', 'Every customs gate, west to east', ''),
        ('/export', 'Export guides', 'How to sell abroad, product by product', ''),
    ]),
]
# kept for anything that still wants the flat list
NAV = [(h, l) for _, _, _, _, items in GROUPS for h, l, _, _ in items]

# which door lights up for a path that is not itself a menu item
_GROUP_PREFIX = [('/tariff/2083-84-changes', 'cost'), ('/tariff', 'find'), ('/import-duty', 'find'), ('/faq', 'find'),
                 ('/safta', 'cost'), ('/trade-partner', 'trade'), ('/sector', 'trade'), ('/customs-office', 'trade'),
                 ('/compare', 'trade'), ('/trade', 'trade'), ('/shipping', 'move'), ('/export', 'move'), ('/the-border', 'move')]


def group_of(path):
    for gid, _, _, _, items in GROUPS:
        if any(h == path for h, _, _, _ in items):
            return gid
    for pre, gid in _GROUP_PREFIX:
        if path.startswith(pre):
            return gid
    return ''


# closes an open door on outside click, Escape, or after choosing a link (the app switches views without a reload)
_NAV_JS = ("<script>(function(){function shut(x){document.querySelectorAll('details.gnm[open]').forEach(function(d){if(d!==x)d.removeAttribute('open')})}"
           "document.addEventListener('click',function(e){var d=e.target.closest&&e.target.closest('details.gnm');"
           "if(!d||e.target.closest('.gnp a'))shut(e.target.closest&&e.target.closest('summary')?d:null);else shut(d)});"
           "document.addEventListener('keydown',function(e){if(e.key==='Escape')shut(null)})})();</script>")


def render_nav(path, esc, spa=False):
    """The four-door menu. Static pages put it inside <nav class="topnav">; the app shell inside header.bar."""
    cur_g = group_of(path)
    o = ['<div class="gn">']
    for gid, label, icon, hint, items in GROUPS:
        o.append('<details class="gnm%s" name="gn"><summary><span class="gni" aria-hidden="true">%s</span>%s</summary><div class="gnp">'
                 '<div class="gnh">%s</div>' % (' cur' if gid == cur_g else '', icon, esc(label), esc(hint)))
        for h, l, d, tab in items:
            attrs = ''
            if spa and tab:
                attrs = ' data-tab="%s" aria-selected="%s"' % (tab, 'true' if tab == 'search' else 'false')
            elif h == path:
                attrs = ' class="cur" aria-current="page"'
            o.append('<a href="%s"%s><b>%s</b><small>%s</small></a>' % (h, attrs, esc(l), esc(d)))
        o.append('</div></details>')
    o.append('</div>' + _NAV_JS)
    return ''.join(o)


# One stylesheet for the menu, used by seo.css (static pages) and inlined into the app shell.
# Colours are literal on the dark header; the panel uses whichever token set the host page defines.
NAV_CSS = """
.gn{display:flex;gap:4px;align-items:center}
.gnm{position:relative}
.gnm>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:7px;height:40px;padding:0 13px;border-radius:10px;font-weight:700;font-size:.9rem;white-space:nowrap;color:rgba(255,255,255,.78);user-select:none}
.gnm>summary::-webkit-details-marker{display:none}
.gnm>summary:hover,.gnm[open]>summary{background:rgba(255,255,255,.12);color:#fff}
.gnm.cur>summary,.gnm:has([aria-selected="true"])>summary{background:rgba(255,255,255,.16);color:#fff;box-shadow:inset 0 -2px 0 #7FB2FF}
.gnm>summary:focus-visible{outline:2px solid #9FD8FF;outline-offset:2px}
.gni{font-size:1rem;line-height:1}
.gnp{position:absolute;right:0;top:calc(100% + 8px);z-index:60;width:300px;max-width:calc(100vw - 24px);background:var(--card,#fff);color:var(--fg,#0f172a);border:1px solid var(--border,#e2e8f0);border-radius:16px;padding:8px;box-shadow:0 18px 44px -18px rgba(10,20,50,.55)}
.gnm:first-child .gnp{right:auto;left:0}
.gnh{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted,#64748b);padding:6px 10px 4px}
.gnp a{display:block;padding:9px 10px;border-radius:10px;color:inherit;text-decoration:none;height:auto;white-space:normal;font-weight:400;background:none}
.gnp a:hover,.gnp a:focus-visible{background:var(--accent-bg,#e8edfa);text-decoration:none;color:inherit}
.gnp a b{display:block;font-size:.93rem;font-weight:700;color:var(--fg,#0f172a)}
.gnp a small{display:block;font-size:.78rem;color:var(--muted,#64748b);margin-top:1px}
.gnp a.cur b,.gnp a[aria-selected="true"] b{color:var(--accent,#5470c6)}
.topnav{overflow:visible!important}
@media(max-width:720px){
 .gn{position:fixed;left:0;right:0;bottom:0;z-index:50;gap:0;background:var(--card,#fff);border-top:1px solid var(--border,#e2e8f0);padding-bottom:env(safe-area-inset-bottom,0px)}
 .gnm{flex:1;position:static}
 .gnm>summary{flex-direction:column;justify-content:center;gap:2px;height:58px;padding:0;border-radius:0;font-size:.72rem;color:var(--muted,#64748b)}
 .gnm>summary:hover{background:none;color:var(--muted,#64748b)}
 .gnm[open]>summary,.gnm.cur>summary,.gnm:has([aria-selected="true"])>summary{background:none;color:var(--accent,#5470c6);box-shadow:inset 0 2px 0 var(--accent,#5470c6)}
 .gni{font-size:1.25rem}
 .gnp,.gnm:first-child .gnp{position:fixed;left:8px;right:8px;bottom:calc(66px + env(safe-area-inset-bottom,0px));top:auto;width:auto;max-width:none;max-height:70vh;overflow:auto}
 body{padding-bottom:calc(60px + env(safe-area-inset-bottom,0px))}
}
"""


def cur(path, h):
    return path == h


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
