"""Home page "Nepal's trade today" block for the app shell.

assemble.py calls build() and injects the HTML between <!--HOMEINFO--> markers in src.html and the CSS
between /*HOMECSS*/ markers. Stdlib only; every figure is read from the same JSON the pages use
(world/data/country.json, data/stats.json). The block sits under the search results container and is
hidden by CSS while a search is active.
"""
import json, html, pathlib, re
root = pathlib.Path(__file__).resolve().parents[1]
esc = lambda s: html.escape(str(s), quote=True)


def money(th):
    r = abs(th) * 1000.0
    for d, u, f in ((1e11, 'kharba', '%.2f'), (1e9, 'arba', '%.2f'), (1e7, 'crore', '%.1f'), (1e5, 'lakh', '%.1f')):
        if r >= d:
            return ('−' if th < 0 else '') + 'Rs ' + f % (r / d) + ' ' + u
    return ('−' if th < 0 else '') + 'Rs %.0f' % r


def build():
    import links
    from nav import GROUPS
    from sectors_def import SECTORS, member
    CO = json.loads((root / 'world/data/country.json').read_text(encoding='utf-8'))
    S = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
    FY, T = CO['fy'], CO['totals']
    imp, exp, rev = T['imp'], T['exp'], T.get('rev', 0)
    o = ['<section class="hi" aria-label="Nepal’s trade at a glance">']
    # headline numbers
    o.append('<h2 class="hi-h">Nepal’s trade in FY %s</h2><div class="hi-nums">'
             '<a href="/trade-partners" class="hi-num i"><span>Imports</span><b>%s</b><small>%+.1f%% on last year</small></a>'
             '<a href="/sectors" class="hi-num e"><span>Exports</span><b>%s</b><small>%+.1f%% on last year</small></a>'
             '<a href="/compare" class="hi-num d"><span>Trade deficit</span><b>%s</b><small>Rs %.0f imported for every Rs 100 exported</small></a>'
             '<a href="/customs-offices" class="hi-num r"><span>Collected at customs</span><b>%s</b><small>Rs %.0f per Rs 100 of imports</small></a></div>'
             % (FY, money(imp), T.get('imp_yoy', 0), money(exp), T.get('exp_yoy', 0), money(imp - exp), (imp / exp * 100) if exp else 0,
                money(rev), rev / imp * 100 if imp else 0))
    # every Rs 100 of imports
    top = [CO['countries'][i] for i in sorted(CO['countries'], key=lambda i: -CO['countries'][i]['imp'])[:5]]
    segs = [(c['name'], c.get('flag', ''), c['imp'] / imp * 100, links.partner_href(c['name'])) for c in top]
    rest = 100 - sum(s[2] for s in segs)
    o.append('<h2 class="hi-h">Where every Rs 100 of imports comes from</h2><div class="hi-bar" role="img" aria-label="%s">%s<span class="hi-seg o" style="flex:%.2f"></span></div><ul class="hi-leg">%s<li><i class="o"></i>Everyone else <b>Rs %.0f</b></li></ul>'
             % (esc(', '.join('%s Rs %.0f' % (n, p) for n, _, p, _ in segs)),
                ''.join('<span class="hi-seg s%d" style="flex:%.2f"></span>' % (k, p) for k, (_, _, p, _) in enumerate(segs)), rest,
                ''.join('<li><i class="s%d"></i><a href="%s">%s %s</a> <b>Rs %.0f</b></li>' % (k, h or '/trade-partners', f, esc(n), p) for k, (n, f, p, h) in enumerate(segs)), rest))
    # sectors
    def tot(pre, exc, key):
        return sum(r[3] for c, r in S[key].items() if member(c, pre, exc))
    I = sorted(((s, tot(s[3], s[4], 'imports')) for s in SECTORS if s[-1] == 'import'), key=lambda x: -x[1])[:6]
    E = sorted(((s, tot(s[3], s[4], 'exports')) for s in SECTORS if s[-1] == 'export'), key=lambda x: -x[1])[:6]
    def col(rows, cls, head, more):
        mx = rows[0][1] or 1.0
        return ('<div><h3>%s</h3>' % head + ''.join(
            '<a class="hi-row" href="/sector/%s"><span class="hi-rn">%s %s</span><span class="hi-rt"><i class="%s" style="width:%.1f%%"></i></span><b>%s</b></a>'
            % (s[0], s[2], esc(s[1]), cls, max(2.0, v / mx * 100), money(v)) for s, v in rows) + '<a class="hi-more" href="/sectors">%s</a></div>' % more)
    o.append('<div class="hi-two">' + col(I, 'i', 'What Nepal buys', 'All import sectors') + col(E, 'e', 'What Nepal sells', 'All export industries') + '</div>')
    # teasers
    o.append('<div class="hi-tease">'
             '<a href="/the-border"><span aria-hidden="true">🛂</span><b>The Border</b><small>Every customs gate from west to east, sized by the trade it handles</small></a>'
             '<a href="/trade-partners"><span aria-hidden="true">🗺️</span><b>The world map</b><small>Tap any country to see what Nepal trades with it</small></a>'
             '<a href="/compare"><span aria-hidden="true">⚖️</span><b>Compare two countries</b><small>India against China, or any pair, side by side</small></a></div>')
    o.append('<p class="hi-src">Source: Department of Customs, Nepal — Foreign Trade Statistics, FY %s. 1 arba = 1 billion rupees; 1 kharba = 100 billion.</p></section>' % FY)
    return ''.join(o)


CSS = """
.hi{margin:var(--s5,24px) 0 var(--s4,16px)}
#toolbar:not([hidden])~#home-info{display:none}
.hi-h{font-size:1.05rem;margin:26px 0 10px;letter-spacing:-.01em}
.hi-doors{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.hi-door{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px}
.hi-dt span{font-size:1.5rem;line-height:1;display:block}.hi-dt b{display:block;font-size:1.05rem;margin-top:8px}.hi-dt small{display:block;color:var(--muted);font-size:.78rem}
.hi-dl{display:grid;gap:2px;margin-top:10px}.hi-dl a{font-size:.88rem;font-weight:600;color:var(--accent);padding:5px 0;text-decoration:none}.hi-dl a:hover{text-decoration:underline}
.hi-nums{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.hi-num{display:block;border-radius:16px;padding:14px 16px;color:#fff;text-decoration:none;background:linear-gradient(135deg,var(--hero1),var(--hero2))}
.hi-num span{display:block;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;opacity:.75}
.hi-num b{display:block;font-size:clamp(1.15rem,.9rem + 1vw,1.6rem);font-weight:800;letter-spacing:-.02em;margin:4px 0 2px;font-variant-numeric:tabular-nums}
.hi-num small{display:block;font-size:.76rem;opacity:.8}
.hi-num.i b{color:#8EC0FF}.hi-num.e b{color:#FFB08A}.hi-num.d b{color:#FF9B9B}.hi-num.r b{color:#7EE2A8}
.hi-bar{display:flex;height:34px;border-radius:12px;overflow:hidden;gap:2px}
.hi-seg{display:block;min-width:3px}.s0{background:#2a78d6}.s1{background:#eb6834}.s2{background:#1baf7a}.s3{background:#eda100}.s4{background:#e87ba4}.hi-seg.o,.hi-leg i.o{background:var(--border)}
.hi-leg{list-style:none;display:flex;flex-wrap:wrap;gap:6px 18px;margin:10px 0 0;padding:0;font-size:.88rem}
.hi-leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}.hi-leg a{color:var(--fg);font-weight:600;text-decoration:none}.hi-leg a:hover{color:var(--accent)}.hi-leg b{font-variant-numeric:tabular-nums}
.hi-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin-top:8px}
.hi-two h3{font-size:1.05rem;margin:18px 0 8px}
.hi-row{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);color:var(--fg);text-decoration:none;font-size:.9rem}
.hi-row:hover .hi-rn{color:var(--accent)}.hi-rn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
.hi-rt{height:10px;border-radius:5px;background:var(--muted-bg,var(--border));overflow:hidden}.hi-rt i{display:block;height:100%;border-radius:5px}.hi-rt i.i{background:#2a78d6}.hi-rt i.e{background:#eb6834}
.hi-row b{font-variant-numeric:tabular-nums;white-space:nowrap;font-size:.86rem}
.hi-more{display:inline-block;margin-top:10px;font-size:.86rem;font-weight:700;color:var(--accent);text-decoration:none}
.hi-tease{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:26px}
.hi-tease a{display:block;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px;color:var(--fg);text-decoration:none;transition:transform .15s,border-color .15s}
.hi-tease a:hover{transform:translateY(-2px);border-color:var(--accent)}
.hi-tease span{font-size:1.5rem;display:block}.hi-tease b{display:block;margin:6px 0 2px}.hi-tease small{color:var(--muted);font-size:.8rem;display:block}
.hi-src{font-size:.76rem;color:var(--muted);margin-top:16px}
@media(max-width:860px){.hi-doors,.hi-nums{grid-template-columns:repeat(2,minmax(0,1fr))}.hi-two,.hi-tease{grid-template-columns:minmax(0,1fr)}.hi-two{gap:0}}
@media(prefers-reduced-motion:reduce){.hi-tease a{transition:none}}
"""
