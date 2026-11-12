"""One site footer for every main-site page (static pages and the app shell).

Two entry points:
  site_footer(page_sources_html)  -> '<footer class="sf">…</footer>'
  FOOTER_CSS                      -> styles (literal colours: the footer is always dark, so it works with
                                     both the app's and the static pages' token sets)
Used by:
  assemble.py         injects it into src.html between <!--SFOOT--> markers (app shell + its route copies)
  footer_pass.py      last build step: replaces the old <footer> on every static page, keeping that page's own
                      source note(s) as "About this page's data"
check_pages.py requires every footer to carry "Our other sites" and the world / nepalpublicdata links — kept here.
Relative links only (main site). Never import from world_prerender.py (other host).
"""
import json, pathlib, datetime, html

root = pathlib.Path(__file__).resolve().parents[1]
esc = lambda s: html.escape(str(s), quote=True)


def _facts():
    t = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
    c = json.loads((root / 'world/data/country.json').read_text(encoding='utf-8'))
    ytd = c.get('ytd') or {}
    return {'tv': t.get('v', ''), 'lines': len(t['rows']), 'fy': c['fy'], 'updated': c.get('updated', ''),
            'ytd': ('FY %s %s' % (ytd.get('fy', ''), ytd.get('label', '').split(' (')[0])) if ytd else '',
            'partners': sum(1 for x in c['countries'].values() if 'impP' in x)}


def site_footer(page_sources=''):
    from nav import GROUPS, WORLD_SITE
    import links
    f = _facts()
    try:
        upd = datetime.date.fromisoformat(f['updated']).strftime('%-d %B %Y')
    except Exception:
        upd = f['updated']
    o = ['<footer class="sf"><div class="sf-in">']
    # trust band
    o.append('<div class="sf-trust">'
             '<div><span aria-hidden="true">🏛️</span><b>Official figures only</b><small>Department of Customs and Ministry of Finance publications, quoted as published</small></div>'
             '<div><span aria-hidden="true">📘</span><b>Customs Tariff %s</b><small>%s tariff lines, HS 2022, with general and SAFTA rates</small></div>'
             '<div><span aria-hidden="true">📊</span><b>Trade data FY %s</b><small>Updated %s%s</small></div>'
             '<div><span aria-hidden="true">🔓</span><b>Free and independent</b><small>No sign-in needed. Not a government website.</small></div></div>'
             % (esc(f['tv']), format(f['lines'], ','), esc(f['fy']), esc(upd), (' · ' + esc(f['ytd']) + ' so far') if f['ytd'] else ''))
    # columns
    o.append('<div class="sf-grid"><div class="sf-brand"><a class="sf-logo" href="/"><span class="mark">HS</span>Customs Nepal</a>'
             '<p>Find the HS code, customs duty and landed cost for anything you import into Nepal — and see who Nepal trades with, in what, and how much.</p>'
             '<p><a href="mailto:info@customsnepal.com">info@customsnepal.com</a></p>'
             '<form class="sf-track" role="search" aria-label="Track a shipment" action="/shipping/track" method="get">'
             '<input name="n" type="search" autocomplete="off" spellcheck="false" placeholder="Track a container or air waybill" aria-label="Tracking number">'
             '<button type="submit">Track</button></form></div>')
    for gid, label, icon, hint, items in GROUPS:
        o.append('<nav class="sf-col" aria-label="%s"><h2>%s</h2><ul>%s</ul></nav>'
                 % (esc(label), esc(label), ''.join('<li><a href="%s">%s</a></li>' % (h, esc(l)) for h, l, _, _ in items)))
    o.append('</div>')
    # popular
    top = ''.join('<a href="%s">%s %s</a>' % (links.PARTNER_PAGE[i][0], links.PARTNER_PAGE[i][2], esc(links.PARTNER_PAGE[i][1])) for i in links.TOP_PARTNERS[:10])
    pop = [(s, l) for s, l in links._POPULAR if s in links._ALIAS_NAME]
    prods = ''.join('<a href="/import-duty/%s">%s</a>' % (s, esc(l)) for s, l in pop)
    o.append('<div class="sf-pop"><div><h2>Nepal&rsquo;s trade by country</h2><p>%s<a class="sf-more" href="/trade-partners">All %d countries</a></p></div>'
             '<div><h2>Import duty by product name</h2><p>%s<a class="sf-more" href="/import-duty#popular-names">All %d products</a></p></div></div>'
             % (top, len(links.PARTNER_PAGE), prods, len(links.ALIAS_RECS)))
    if page_sources:
        o.append('<div class="sf-src"><h2>About this page&rsquo;s data</h2>%s</div>' % page_sources)
    # legal + bottom bar
    o.append('<div class="sf-legal"><p><b>Not a government website.</b> Customs Nepal is an independent, privately operated reference tool. It is not '
             'affiliated with, endorsed by or representing the Government of Nepal, the Department of Customs or the Ministry of Finance. It is a search '
             'aid and estimate, not an official classification or customs assessment — confirm the final HS code and taxes with the customs office or '
             'your clearing agent. Official sources: <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">customs.gov.np</a> · '
             '<a href="https://www.mof.gov.np" target="_blank" rel="noopener noreferrer">mof.gov.np</a>.</p></div>')
    o.append('<div class="sf-bottom"><span>© %d customsnepal.com</span><span><a href="/about">About</a> · <a href="/privacy">Privacy</a> · '
             '<a href="/faq">FAQ</a> · <a href="mailto:info@customsnepal.com">Contact</a></span>'
             '<p class="other-sites"><b>Our other sites:</b> <a href="%s/">world.customsnepal.com — world HS codes &amp; trade</a> · '
             '<a href="https://nepalpublicdata.com/">nepalpublicdata.com — Nepal public statistics</a></p>'
             '<small>Google Analytics and Vercel Analytics count visits; nothing you type into the tools is sent to them.</small></div>'
             % (datetime.date.today().year, WORLD_SITE))
    o.append('</div></footer>')
    return ''.join(o)


FOOTER_CSS = """
footer.sf{margin-top:56px;background:linear-gradient(180deg,#14233f,#0c1629);color:rgba(255,255,255,.78);font-size:.88rem;line-height:1.55;border-top:0;padding:0}
footer.sf .sf-in{max-width:1100px;margin:0 auto;padding:34px 20px 28px}
footer.sf a{color:#cfe0ff;text-decoration:none;font-weight:500}footer.sf a:hover{color:#fff;text-decoration:underline}
footer.sf h2{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin:0 0 10px;font-weight:700}
footer.sf p{margin:0 0 8px;max-width:none}
.sf-trust{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding-bottom:26px;border-bottom:1px solid rgba(255,255,255,.1)}
.sf-trust>div{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:12px 14px}
.sf-trust span{font-size:1.25rem;display:block;line-height:1}.sf-trust b{display:block;color:#fff;margin:8px 0 2px;font-size:.92rem}
.sf-trust small{display:block;color:rgba(255,255,255,.62);font-size:.78rem;line-height:1.45}
.sf-grid{display:grid;grid-template-columns:1.6fr repeat(4,minmax(0,1fr));gap:26px;padding:28px 0;border-bottom:1px solid rgba(255,255,255,.1)}
.sf-logo{display:inline-flex;align-items:center;gap:9px;color:#fff!important;font-weight:800;font-size:1.05rem;margin-bottom:10px}
.sf-logo .mark{width:30px;height:30px;border-radius:8px;background:#5470C6;color:#fff;display:grid;place-items:center;font-size:.68rem;font-weight:700}
.sf-brand p{color:rgba(255,255,255,.7)}
.sf-track{display:flex;gap:6px;margin-top:12px}
.sf-track input{flex:1;min-width:0;font:inherit;font-size:.85rem;padding:9px 11px;border-radius:10px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.07);color:#fff}
.sf-track input::placeholder{color:rgba(255,255,255,.5)}
.sf-track button{font:inherit;font-size:.85rem;font-weight:700;padding:0 14px;border-radius:10px;border:0;background:#5470C6;color:#fff;cursor:pointer}
.sf-track input:focus-visible,.sf-track button:focus-visible,footer.sf a:focus-visible{outline:2px solid #9FD8FF;outline-offset:2px}
.sf-col ul{list-style:none;margin:0;padding:0}.sf-col li{margin:0 0 7px}.sf-col a,.sf-bottom a,.sf-legal a,.sf-brand a{min-height:0;display:inline;padding:0}
.sf-pop{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;padding:24px 0;border-bottom:1px solid rgba(255,255,255,.1)}
.sf-pop p{display:flex;flex-wrap:wrap;gap:6px}
.sf-pop a{display:inline-flex;align-items:center;min-height:0;height:auto;width:auto;line-height:1.4;padding:4px 10px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);font-size:.8rem}
.sf-pop a:hover{background:rgba(255,255,255,.14);text-decoration:none}.sf-pop a.sf-more{background:none;border-color:rgba(159,216,255,.4);color:#9FD8FF}
.sf-src{padding:20px 0 6px;color:rgba(255,255,255,.66);font-size:.82rem}.sf-src p{margin:0 0 6px}
.sf-legal{padding:18px 0 6px;color:rgba(255,255,255,.6);font-size:.8rem}.sf-legal b{color:rgba(255,255,255,.85)}
.sf-bottom{display:flex;flex-wrap:wrap;gap:6px 22px;align-items:baseline;padding-top:14px;border-top:1px solid rgba(255,255,255,.1);font-size:.8rem;color:rgba(255,255,255,.6)}
.sf-bottom .other-sites{flex-basis:100%;margin:2px 0 0}.sf-bottom small{flex-basis:100%;font-size:.74rem;color:rgba(255,255,255,.45)}
@media(max-width:900px){.sf-trust{grid-template-columns:repeat(2,minmax(0,1fr))}.sf-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.sf-brand{grid-column:1/-1}.sf-pop{grid-template-columns:minmax(0,1fr)}}
@media(max-width:520px){.sf-trust{grid-template-columns:minmax(0,1fr)}footer.sf .sf-in{padding:26px 16px 22px}}
"""
