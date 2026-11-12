"""/insights — data articles written from the Department of Customs figures the site already holds.

Every article is computed at build time from data/stats.json (Foreign Trade Statistics, 7-year history, monthly)
and data/tariff.json, so the numbers refresh when the data does. No figure is typed by hand and no cause is claimed
that the data cannot show: an article says WHAT moved and by how much, links to the pages that go deeper, and states
its source and method. Stdlib only.

Add an article: write a function returning art(...) and append it to ARTICLES. Runs after product_pages.py so
product links can be checked against the built files.
"""
import json, re, datetime, math
import pagekit as k
from pagekit import esc, money, pub, root
from statsfields import IMP_VALUE, IMP_REVENUE, IMP_PARTNERS, EXP_VALUE, EXP_PARTNERS, TARIFF_FY, slug, clean_name
import links, family
import ast
# chapter short names: read the literal from trade_pages.py without running that generator
_m = re.search(r'^CHSHORT = (\{.*?\})\s*$', (root / 'scripts/trade_pages.py').read_text(encoding='utf-8'), re.M)
CHSHORT = ast.literal_eval(_m.group(1))

S = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
T = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
FY, FYP = S['fy'], S['fy_prev']
H = S['history']; Y = H['years']
IMP, EXP = S['imports'], S['exports']
TODAY = datetime.date.today().isoformat()
TOT_I, TOT_E = S['overview']['imports'][1], S['overview']['exports'][1]
PRV_I, PRV_E = S['overview']['imports'][0], S['overview']['exports'][0]
TROW = {re.sub(r'\D', '', r[0]): r for r in T['rows']}
SRC = 'Department of Customs, Nepal, Foreign Trade Statistics'


# ---------- small helpers ----------
def pct(a, b, d=1):
    return ('%.' + str(d) + 'f%%') % (100.0 * a / b) if b else '—'


def chg(cur, prev):
    if not prev:
        return 'new'
    c = 100.0 * (cur - prev) / prev
    return ('+' if c >= 0 else '−') + ('%.0f%%' % abs(c) if abs(c) >= 10 else '%.1f%%' % abs(c))


def word(cur, prev):
    return ('up ' if cur >= prev else 'down ') + chg(cur, prev).lstrip('+−')


def updown(cur, prev):
    return 'rose' if cur > prev else 'fell'


def chname(ch):
    return CHSHORT.get(int(ch), 'Chapter %s' % ch)


def chlink(ch):
    return '<a href="/tariff/%02d">%s</a>' % (int(ch), esc(chname(ch)))


def pname(code):
    v = IMP.get(code) or EXP.get(code)
    return clean_name(v[0]) if v and v[0] else (TROW[code][1] if code in TROW else code)


def plink(code, name=None):
    nm = name or pname(code)
    f = pub / 'import-duty' / ('%s-%s.html' % (slug(nm), code))
    href = ('/import-duty/%s-%s' % (slug(nm), code)) if f.exists() else '/#hs-' + code
    return '<a href="%s">%s</a>' % (href, esc(nm))


def dotted(code):
    return '%s.%s.%s' % (code[:4], code[4:6], code[6:])


def duty(code):
    r = TROW.get(code)
    return family.rate(r[5]) if r else (None, '—')


def hist_code(code, i=0):
    """7-year series for a code: i=0 imports, 1 exports."""
    return [x[i] for x in H['codes'].get(code, [[0, 0]] * len(Y))]


# ---------- components ----------
def tiles(items):
    return '<div class="exstats">%s</div>' % ''.join('<div class="extile"><b>%s</b><span>%s</span></div>' % (a, esc(b)) for a, b in items)


def bars(rows, tone='a', note=''):
    """rows: [(label_html, value, right_text)]. A ranked horizontal bar list."""
    if not rows:
        return ''
    mx = max(abs(r[1]) for r in rows) or 1
    out = ['<ol class="ins-bars t-%s">' % tone]
    for lab, v, right in rows:
        out.append('<li><span class="l">%s</span><span class="b"><i style="width:%.1f%%"></i></span><span class="v">%s</span></li>'
                   % (lab, max(1.0, 100.0 * abs(v) / mx), right))
    out.append('</ol>')
    if note:
        out.append('<p class="fineprint">%s</p>' % note)
    return ''.join(out)


def cols(labels, series, names, fmt=money):
    """Grouped column chart, pure CSS. series: list of lists (same length as labels)."""
    mx = max(max(s) for s in series) or 1
    cells = []
    for i, lab in enumerate(labels):
        bs = ''.join('<i class="s%d" style="height:%.1f%%" title="%s: %s"></i>' % (j, max(1.0, 100.0 * s[i] / mx), esc(names[j]), esc(fmt(s[i])))
                     for j, s in enumerate(series))
        cells.append('<div class="c"><div class="bb">%s</div><span>%s</span></div>' % (bs, esc(lab)))
    key = ''.join('<span><i class="s%d"></i>%s</span>' % (j, esc(n)) for j, n in enumerate(names))
    desc = '; '.join('%s: %s' % (names[j], ', '.join('%s %s' % (labels[i], fmt(s[i])) for i in range(len(labels)))) for j, s in enumerate(series))
    return '<figure class="ins-cols" role="img" aria-label="%s"><div class="g">%s</div><figcaption>%s</figcaption></figure>' % (esc(desc), ''.join(cells), key)


def table(heads, rows, right=()):
    th = ''.join('<th%s>%s</th>' % (' class="r"' if i in right else '', esc(h)) for i, h in enumerate(heads))
    body = ''.join('<tr>%s</tr>' % ''.join('<td%s>%s</td>' % (' class="r"' if i in right else '', c) for i, c in enumerate(r)) for r in rows)
    return '<div class="tscroll"><table class="tbl ins-t"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)


def h2(t):
    return '<h2 class="sec">%s</h2>' % esc(t)


def p(t):
    return '<p>%s</p>' % t


def takeaways(items):
    return '<div class="ins-take"><h2>What this means if you trade</h2><ul>%s</ul></div>' % ''.join('<li>%s</li>' % x for x in items)


def art(slug_, tag, title, h1, dek, body, more=(), method=''):
    return dict(slug=slug_, tag=tag, title=title, h1=h1, dek=dek, body=body, more=list(more), method=method)


TAGS = {'big': 'The big picture', 'move': 'What changed', 'dep': 'Who Nepal depends on', 'tar': 'Duty and revenue', 'biz': 'Business openings'}

# ---------- ranked source lists used by several articles ----------
IMP_RANK = sorted(((c, v[IMP_VALUE]) for c, v in IMP.items()), key=lambda x: -x[1])
EXP_RANK = sorted(((c, v[EXP_VALUE]) for c, v in EXP.items()), key=lambda x: -x[1])
CO_I = sorted(S['countries'], key=lambda x: -x[1])
CO_E = sorted(S['countries'], key=lambda x: -x[2])
CH = {c[0]: c for c in S['chapters']}          # ch -> [ch, '', imports, exports, revenue]
REV_TOTAL = sum(c[4] for c in S['chapters'])
BAND = {b[0]: b for b in S['bands']}           # band -> [band, duty collected, import value]
BAND_VAL = sum(b[2] for b in S['bands']); BAND_DUTY = sum(b[1] for b in S['bands'])


def co_hist(name):
    return H['countries'].get(name, [[0, 0]] * len(Y))


# =====================================================================
# A. The big picture
# =====================================================================
def a_year():
    top_c = CO_I[0]; top_p = IMP_RANK[0]; top_e = EXP_RANK[0]
    gate = max(S['customs'], key=lambda x: x[1] + x[2])
    body = [
        tiles([(money(TOT_I), 'Imports, %s vs last year' % chg(TOT_I, PRV_I)), (money(TOT_E), 'Exports, %s' % chg(TOT_E, PRV_E)),
               (money(TOT_I - TOT_E), 'Trade deficit'), ('%.1f : 1' % (TOT_I / TOT_E), 'Imports for every rupee exported')]),
        h2('Seven years of imports and exports'),
        cols(Y, [[t[0] for t in H['totals']], [t[1] for t in H['totals']]], ['Imports', 'Exports']),
        h2('Ten numbers that sum up FY %s' % FY),
        '<ol class="ins-num">' + ''.join('<li>%s</li>' % x for x in [
            'Nepal imported goods worth <b>%s</b>, %s on FY %s.' % (money(TOT_I), chg(TOT_I, PRV_I), FYP),
            'It exported <b>%s</b>, %s.' % (money(TOT_E), chg(TOT_E, PRV_E)),
            'The gap between the two, the trade deficit, was <b>%s</b>.' % money(TOT_I - TOT_E),
            'Exports paid for <b>%s</b> of the import bill.' % pct(TOT_E, TOT_I),
            '<b>%s</b> supplied %s of all imports (%s).' % (links.partner_link(top_c[0], esc), pct(top_c[1], TOT_I), money(top_c[1])),
            '<b>%s</b> bought %s of all exports.' % (links.partner_link(CO_E[0][0], esc), pct(CO_E[0][2], TOT_E)),
            'The single largest import was %s at <b>%s</b>.' % (plink(top_p[0]), money(top_p[1])),
            'The single largest export was %s at <b>%s</b>.' % (esc(pname(top_e[0])), money(top_e[1])),
            'Customs collected <b>%s</b> on imports, equal to %s of their value.' % (money(REV_TOTAL), pct(REV_TOTAL, TOT_I)),
            '<b>%s</b> handled more trade than any other customs point: %s.' % (esc(gate[0]), money(gate[1] + gate[2])),
        ]) + '</ol>',
        takeaways(['Imports are about %.1f times exports, so most trade services in Nepal (freight, clearing, finance) are built around inbound goods.' % (TOT_I / TOT_E),
                   'One supplier country accounts for %s of imports. Check the <a href="/trade-partners">partner pages</a> before assuming a product has many sources.' % pct(top_c[1], TOT_I)]),
    ]
    return art('nepal-trade-year-in-numbers', 'big', 'Nepal trade in FY %s: the year in ten numbers' % FY,
               'Nepal’s trade in FY %s, in ten numbers' % FY,
               'Imports %s to %s and exports %s to %s. Here are the ten figures that describe the year.'
               % (updown(TOT_I, PRV_I), money(TOT_I), updown(TOT_E, PRV_E), money(TOT_E)), body,
               more=['nepal-trade-deficit-seven-years', 'top-imports-of-nepal', 'top-exports-of-nepal'])


def a_deficit():
    tot = H['totals']; d = [t[0] - t[1] for t in tot]
    ratio = [t[0] / t[1] if t[1] else 0 for t in tot]
    rows = [(y, money(t[0]), money(t[1]), money(t[0] - t[1]), '%.1f : 1' % (t[0] / t[1])) for y, t in zip(Y, tot)]
    best = min(range(len(Y)), key=lambda i: ratio[i]); worst = max(range(len(Y)), key=lambda i: ratio[i])
    body = [
        tiles([(money(d[-1]), 'Deficit, FY %s' % FY), (chg(d[-1], d[0]), 'Change since FY %s' % Y[0]), ('%.1f : 1' % ratio[-1], 'Imports to exports now')]),
        h2('Imports, exports and the gap, FY %s to %s' % (Y[0], Y[-1])),
        cols(Y, [[t[0] for t in tot], [t[1] for t in tot], d], ['Imports', 'Exports', 'Deficit']),
        table(['Fiscal year', 'Imports', 'Exports', 'Deficit', 'Imports : exports'], rows, right=(1, 2, 3, 4)),
        p('The deficit %s from %s in FY %s to %s in FY %s. Over the same seven years exports grew %s and imports %s. '
          'The ratio of imports to exports was lowest in FY %s (%.1f to 1) and highest in FY %s (%.1f to 1).'
          % ('widened' if d[-1] > d[0] else 'narrowed', money(d[0]), Y[0], money(d[-1]), Y[-1], chg(tot[-1][1], tot[0][1]), chg(tot[-1][0], tot[0][0]),
             Y[best], ratio[best], Y[worst], ratio[worst])),
        takeaways(['A deficit is the difference between two totals. It can widen while exports grow, as long as imports grow by more rupees.',
                   'To see which goods drive the import side, read <a href="/insights/top-imports-of-nepal">the top imports</a>; for the export side, <a href="/insights/top-exports-of-nepal">the top exports</a>.']),
    ]
    return art('nepal-trade-deficit-seven-years', 'big', 'Nepal’s trade deficit: seven years of data, FY %s to %s' % (Y[0], Y[-1]),
               'Nepal’s trade deficit over seven years',
               'The gap between what Nepal buys and sells abroad was %s in FY %s. This is how it got there.' % (money(d[-1]), FY), body,
               more=['nepal-trade-year-in-numbers', 'how-much-nepal-depends-on-india', 'nepal-export-concentration'])


def _rank_rows(rank, n, total, idx, link=True):
    rows = []
    for c, v in rank[:n]:
        hs = hist_code(c, idx)
        rows.append(((plink(c) if link else esc(pname(c))) + ' <small>%s</small>' % dotted(c), v, '%s · %s' % (money(v), chg(v, hs[-2] if len(hs) > 1 else 0))))
    return rows


def a_top_imports():
    n = 20; top = IMP_RANK[:n]; share = sum(v for _, v in top)
    body = [tiles([(pct(share, TOT_I), 'of all imports come from these 20 lines'), (money(top[0][1]), 'Largest: ' + pname(top[0][0])[:34]), ('%d' % len(IMP), 'Lines imported at all')]),
            h2('The 20 largest import lines, FY %s' % FY),
            bars(_rank_rows(IMP_RANK, n, TOT_I, 0), note='Value and change on FY %s. Each name opens its duty page.' % FYP),
            p('The top five alone are worth %s, or %s of the import bill. %s.'
              % (money(sum(v for _, v in top[:5])), pct(sum(v for _, v in top[:5]), TOT_I),
                 'Of the 20, %d grew and %d shrank compared with FY %s' % (sum(1 for c, v in top if v >= hist_code(c)[-2]), sum(1 for c, v in top if v < hist_code(c)[-2]), FYP))),
            takeaways(['These are 8-digit tariff lines, the level at which duty is charged. A product people think of as one thing (a car, a phone) can be split across several lines.',
                       'For the same picture by industry, see the <a href="/sectors">sector pages</a>.'])]
    return art('top-imports-of-nepal', 'big', 'Top 20 imports of Nepal in FY %s, by value' % FY, 'What Nepal imports most: the top 20 lines',
               '%s was the largest single import line at %s. The 20 biggest lines make up %s of everything Nepal bought.'
               % (pname(top[0][0]), money(top[0][1]), pct(share, TOT_I)), body, more=['imports-that-grew-most', 'goods-that-pay-the-most-tax', 'top-suppliers-to-nepal'])


def a_top_exports():
    n = 20; top = EXP_RANK[:n]; share = sum(v for _, v in top)
    body = [tiles([(pct(share, TOT_E), 'of all exports come from these 20 lines'), (money(top[0][1]), 'Largest: ' + pname(top[0][0])[:34]), ('%d' % len(EXP), 'Lines exported at all')]),
            h2('The 20 largest export lines, FY %s' % FY),
            bars(_rank_rows(EXP_RANK, n, TOT_E, 1, link=False), tone='e', note='Value and change on FY %s.' % FYP),
            p('Nepal exported %d different tariff lines in the year, against %d imported. The top five export lines are worth %s, %s of all exports.'
              % (len(EXP), len(IMP), money(sum(v for _, v in top[:5])), pct(sum(v for _, v in top[:5]), TOT_E))),
            takeaways(['Export earnings sit in a small number of lines. A change in one buyer’s demand or one tariff abroad moves the national total.',
                       'The <a href="/sectors">export sector pages</a> show buyers and monthly movement for each group.'])]
    return art('top-exports-of-nepal', 'big', 'Top 20 exports of Nepal in FY %s, by value' % FY, 'What Nepal exports most: the top 20 lines',
               '%s led exports at %s. Twenty lines account for %s of what Nepal sold abroad.' % (pname(top[0][0]), money(top[0][1]), pct(share, TOT_E)), body,
               more=['nepal-export-concentration', 'exports-that-grew-most', 'top-export-markets-of-nepal'])


def a_suppliers():
    n = 15; top = CO_I[:n]
    rows = [(links.partner_link(c[0], esc), c[1], '%s · %s' % (money(c[1]), pct(c[1], TOT_I))) for c in top]
    t = [(links.partner_link(c[0], esc), money(c[1]), pct(c[1], TOT_I), chg(c[1], co_hist(c[0])[-2][0]), chg(c[1], co_hist(c[0])[0][0])) for c in top]
    body = [tiles([(pct(top[0][1], TOT_I), 'From %s' % top[0][0]), (pct(sum(c[1] for c in top[:3]), TOT_I), 'From the top three'), ('%d' % sum(1 for c in S['countries'] if c[1] > 0), 'Countries Nepal imported from')]),
            h2('The 15 largest suppliers, FY %s' % FY), bars(rows, note='Import value and share of all imports.'),
            h2('How each has moved'), table(['Country', 'Imports', 'Share', 'vs FY %s' % FYP, 'vs FY %s' % Y[0]], t, right=(1, 2, 3, 4)),
            takeaways(['The first three suppliers provide %s of imports. Past them, shares drop quickly.' % pct(sum(c[1] for c in top[:3]), TOT_I),
                       'Each country name opens its profile, with the products Nepal buys from it and the duty they pay. <a href="/compare">Compare any two side by side</a>.'])]
    return art('top-suppliers-to-nepal', 'big', 'Who Nepal imports from: top 15 countries, FY %s' % FY, 'Who Nepal buys from: the top 15 suppliers',
               '%s supplied %s of Nepal’s imports. The top three countries together supplied %s.' % (top[0][0], pct(top[0][1], TOT_I), pct(sum(c[1] for c in top[:3]), TOT_I)),
               body, more=['how-much-nepal-depends-on-india', 'what-nepal-buys-from-china', 'india-vs-china-by-product-group'])


def a_markets():
    n = 15; top = CO_E[:n]
    rows = [(links.partner_link(c[0], esc), c[2], '%s · %s' % (money(c[2]), pct(c[2], TOT_E))) for c in top]
    t = [(links.partner_link(c[0], esc), money(c[2]), pct(c[2], TOT_E), chg(c[2], co_hist(c[0])[-2][1]), money(c[2] - c[1])) for c in top]
    body = [tiles([(pct(top[0][2], TOT_E), 'To %s' % top[0][0]), (pct(sum(c[2] for c in top[:3]), TOT_E), 'To the top three'), ('%d' % sum(1 for c in S['countries'] if c[2] > 0), 'Countries Nepal exported to')]),
            h2('The 15 largest export markets, FY %s' % FY), bars(rows, tone='e', note='Export value and share of all exports.'),
            h2('Change and balance with each'), table(['Country', 'Exports', 'Share', 'vs FY %s' % FYP, 'Balance (exports − imports)'], t, right=(1, 2, 3, 4)),
            takeaways(['Nepal runs a surplus with only %d of these 15 markets.' % sum(1 for c in top if c[2] > c[1]),
                       'A market’s profile page lists exactly which lines it buys.'])]
    return art('top-export-markets-of-nepal', 'big', 'Where Nepal exports: top 15 markets, FY %s' % FY, 'Who buys from Nepal: the top 15 markets',
               '%s took %s of Nepal’s exports in FY %s.' % (top[0][0], pct(top[0][2], TOT_E), FY), body,
               more=['top-exports-of-nepal', 'nepal-export-concentration', 'top-suppliers-to-nepal'])


def a_revenue():
    ch = sorted(S['chapters'], key=lambda c: -c[4])[:15]
    rows = [(chlink(c[0]), c[4], '%s · %s' % (money(c[4]), pct(c[4], REV_TOTAL))) for c in ch]
    t = [(chlink(c[0]), money(c[2]), money(c[4]), pct(c[4], c[2]), pct(c[4], REV_TOTAL)) for c in ch]
    body = [tiles([(money(REV_TOTAL), 'Collected at customs on imports'), (pct(REV_TOTAL, TOT_I), 'of import value'), (pct(sum(c[4] for c in ch[:3]), REV_TOTAL), 'From the top three groups')]),
            h2('Which goods the revenue comes from'), bars(rows, tone='r', note='Revenue collected at customs on imports of each chapter (customs duty plus the other taxes charged at the border), FY %s.' % FY),
            h2('Revenue against import value'), table(['Product group', 'Imports', 'Revenue', 'Revenue as % of value', 'Share of all revenue'], t, right=(1, 2, 3, 4)),
            p('%s brought in the most: %s on imports of %s. Three groups provide %s of everything collected at the border.'
              % (esc(chname(ch[0][0])), money(ch[0][4]), money(ch[0][2]), pct(sum(c[4] for c in ch[:3]), REV_TOTAL))),
            takeaways(['Groups with a high revenue-to-value figure are where the landed cost sits furthest above the invoice price. Run those in the <a href="/calculator">calculator</a> before quoting a price.',
                       'See <a href="/insights/effective-tax-rate-by-product-group">the effective rate for every large group</a>.'])]
    return art('where-customs-revenue-comes-from', 'tar', 'Where Nepal’s customs revenue comes from, FY %s' % FY, 'Where customs revenue comes from',
               'Customs collected %s on imports in FY %s. %s alone provided %s of it.' % (money(REV_TOTAL), FY, chname(ch[0][0]), pct(ch[0][4], REV_TOTAL)), body,
               more=['goods-that-pay-the-most-tax', 'effective-tax-rate-by-product-group', 'imports-by-duty-rate'],
               method='“Revenue” is the figure the Department of Customs reports against imports: customs duty plus other taxes charged at the border.')


def a_gates():
    g = sorted(S['customs'], key=lambda x: -(x[1] + x[2])); tot = sum(x[1] + x[2] for x in g)
    nice = lambda n: 'Kathmandu airport (TIA)' if n == 'Ti_Airport' else n
    rows = [(esc(nice(x[0])), x[1] + x[2], '%s · %s' % (money(x[1] + x[2]), pct(x[1] + x[2], tot))) for x in g[:12]]
    t = [(esc(nice(x[0])), money(x[1]), money(x[2]), pct(x[1] + x[2], tot)) for x in g[:12]]
    body = [tiles([(pct(g[0][1] + g[0][2], tot), 'Through %s' % nice(g[0][0])), (pct(sum(x[1] + x[2] for x in g[:5]), tot), 'Through the top five'), ('%d' % len(g), 'Customs points reporting trade')]),
            h2('Trade handled by each customs point, FY %s' % FY), bars(rows, note='Imports plus exports cleared at each point.'),
            table(['Customs point', 'Imports', 'Exports', 'Share of trade'], t, right=(1, 2, 3)),
            takeaways(['The entry point is fixed when the shipment is booked. <a href="/the-border">The Border</a> maps every gate and <a href="/shipping">Shipping</a> shows the sea ports that feed them.',
                       'Each office has a page with contacts and what moves through it: <a href="/customs-offices">customs offices</a>.'])]
    return art('nepal-busiest-customs-points', 'big', 'Nepal’s busiest customs points by trade value, FY %s' % FY, 'Which border points carry Nepal’s trade',
               '%s cleared %s of Nepal’s trade in FY %s. Five customs points handled %s between them.'
               % (nice(g[0][0]), pct(g[0][1] + g[0][2], tot), FY, pct(sum(x[1] + x[2] for x in g[:5]), tot)), body,
               more=['nepal-trade-year-in-numbers', 'top-suppliers-to-nepal'])


# =====================================================================
# B. What changed
# =====================================================================
def _movers(idx, sign, floor=200000):
    out = []
    for c, hs in H['codes'].items():
        cur, prev = hs[-1][idx], hs[-2][idx]
        # a line that appears or vanishes outright is almost always a change of tariff code, not of trade: leave it out
        if max(cur, prev) < floor or min(cur, prev) <= 0 or c not in TROW:
            continue
        out.append((c, cur, prev, cur - prev))
    out.sort(key=lambda x: -x[3] * sign)
    return [x for x in out if x[3] * sign > 0]


def _mover_art(slug_, idx, sign, title, h1, word, tone, more):
    m = _movers(idx, sign)[:20]
    rows = [((plink(c) if idx == 0 else esc(pname(c))) + ' <small>%s</small>' % dotted(c), d, '%s%s · %s' % ('+' if sign > 0 else '−', money(abs(d)), chg(cur, prev))) for c, cur, prev, d in m]
    t = [(esc(pname(c)), money(prev), money(cur), ('+' if sign > 0 else '−') + money(abs(d))) for c, cur, prev, d in m]
    tot = sum(abs(x[3]) for x in m)
    net = (TOT_I - PRV_I) if idx == 0 else (TOT_E - PRV_E)
    body = [tiles([(money(abs(m[0][3])), 'Largest move: ' + pname(m[0][0])[:30]), (money(tot), 'Combined %s of these 20' % word), (('+' if net >= 0 else '−') + money(abs(net)), 'Net change in all %s' % ('imports' if idx == 0 else 'exports'))]),
            h2('The 20 lines that %s most in rupees' % ('gained' if sign > 0 else 'lost')),
            bars(rows, tone=tone, note='Change in %s value, FY %s against FY %s. Ranked by rupees, not percent, so small lines do not crowd out large ones. Lines that appear or disappear entirely are left out, because that usually reflects a change of tariff code.' % ('import' if idx == 0 else 'export', FY, FYP)),
            table(['Product', 'FY %s' % FYP, 'FY %s' % FY, 'Change'], t, right=(1, 2, 3)),
            takeaways(['The data shows that these lines moved, not why. Price, volume and reclassification between tariff lines can all produce a change this size.',
                       'Open a product to see its seven-year history and suppliers before reading a one-year move as a trend.'])]
    return art(slug_, 'move', title, h1, '%s moved the most: %s%s between FY %s and FY %s.' % (pname(m[0][0]), '+' if sign > 0 else '−', money(abs(m[0][3])), FYP, FY), body, more=more)


def a_imp_up():
    return _mover_art('imports-that-grew-most', 0, 1, 'Imports that grew the most in Nepal, FY %s' % FY, 'The imports that grew most this year', 'gain', 'a',
                      ['imports-that-fell-most', 'top-imports-of-nepal', 'this-fiscal-year-so-far'])


def a_imp_down():
    return _mover_art('imports-that-fell-most', 0, -1, 'Imports that fell the most in Nepal, FY %s' % FY, 'The imports that fell most this year', 'fall', 'd',
                      ['imports-that-grew-most', 'top-imports-of-nepal'])


def a_exp_up():
    return _mover_art('exports-that-grew-most', 1, 1, 'Nepal exports that grew the most, FY %s' % FY, 'The exports that grew most this year', 'gain', 'e',
                      ['top-exports-of-nepal', 'nepal-export-winners-five-years', 'nepal-export-concentration'])


def a_ytd():
    cur = S['current']; m = int(cur['months']); ov = cur['overview']; names = S['month_names'][:m]
    ci, pi = ov['imports'][1], ov['imports'][0]; ce, pe = ov['exports'][1], ov['exports'][0]
    prevm = S['monthly'].get(FY, [])[:m]
    pch = {}
    for mm in prevm:
        for c, v in mm.get('ch', {}).items():
            a = pch.setdefault(int(c), [0, 0]); a[0] += v[0]; a[1] += v[1]
    mv = sorted(((c[0], c[1], pch.get(c[0], [0, 0])[0]) for c in cur['chapters']), key=lambda x: -abs(x[1] - x[2]))[:12]
    rows = [(chlink(c), abs(a - b), '%s%s · %s' % ('+' if a >= b else '−', money(abs(a - b)), chg(a, b))) for c, a, b in mv]
    body = [tiles([(money(ci), 'Imports, first %d months (%s)' % (m, chg(ci, pi))), (money(ce), 'Exports (%s)' % chg(ce, pe)), (money(ci - ce), 'Deficit so far')]),
            h2('FY %s so far against the same months last year' % cur['fy']),
            cols(['Imports', 'Exports'], [[pi, pe], [ci, ce]], ['Same months, FY %s' % FY, 'FY %s' % cur['fy']]),
            h2('Product groups with the largest change in imports'), bars(rows, note='First %d months (%s) of FY %s against the same months of FY %s.' % (m, ' and '.join(names) if m <= 2 else names[0] + ' to ' + names[-1], cur['fy'], FY)),
            takeaways(['Early months are a small sample. A single large shipment can swing a group’s figure.',
                       'This page updates each month when the Department of Customs publishes new figures.'])]
    return art('this-fiscal-year-so-far', 'move', 'Nepal trade so far in FY %s: first %d months' % (cur['fy'], m), 'This fiscal year so far',
               'In the first %d months of FY %s, imports are %s and exports %s compared with the same months a year earlier.' % (m, cur['fy'], word(ci, pi), word(ce, pe)), body,
               more=['nepal-trade-year-in-numbers', 'imports-that-grew-most', 'when-nepal-imports-most'],
               method='Year-to-date figures are provisional and are revised by the Department of Customs.')


# =====================================================================
# C. Who Nepal depends on
# =====================================================================
def _share_series(name):
    return [100.0 * co_hist(name)[i][0] / H['totals'][i][0] for i in range(len(Y))]


def a_india():
    sh = _share_series('India'); ind = next(c for c in S['countries'] if c[0] == 'India')
    fl = dict(S['flow']['India'])
    dom = sorted(((ch, v, CH[ch][2]) for ch, v in fl.items() if ch in CH and CH[ch][2] > 5e6), key=lambda x: -x[1] / x[2])
    rows = [(chlink(ch), 100.0 * v / t, '%s of %s' % (pct(v, t), money(t))) for ch, v, t in dom[:15]]
    n90 = sum(1 for ch, v, t in dom if v / t >= 0.9)
    body = [tiles([(pct(ind[1], TOT_I), 'of imports come from India'), (pct(ind[2], TOT_E), 'of exports go to India'), (money(ind[1] - ind[2]), 'Deficit with India')]),
            h2('India’s share of Nepal’s imports, FY %s to %s' % (Y[0], Y[-1])),
            cols(Y, [sh], ['India’s share of imports'], fmt=lambda v: '%.1f%%' % v),
            p('India’s share was %.1f%% in FY %s and %.1f%% in FY %s. The highest in the seven years was %.1f%% (FY %s) and the lowest %.1f%% (FY %s).'
              % (sh[0], Y[0], sh[-1], Y[-1], max(sh), Y[sh.index(max(sh))], min(sh), Y[sh.index(min(sh))])),
            h2('Product groups where India supplies the most'),
            bars(rows, note='India’s share of Nepal’s imports in each group worth over Rs 5 arba, FY %s.' % FY),
            p('In %d of the %d large product groups, India supplies nine-tenths or more.' % (n90, len(dom))),
            takeaways(['Goods of Indian origin can qualify for the lower SAFTA rate with a certificate of origin. <a href="/safta">See which lines and how much</a>.',
                       'Where India’s share is near total, a second source usually means a different route and transit time. <a href="/shipping">Shipping routes</a> shows the options.'])]
    return art('how-much-nepal-depends-on-india', 'dep', 'How much does Nepal depend on India for imports? FY %s' % FY, 'How much Nepal depends on India',
               'India supplied %s of Nepal’s imports and bought %s of its exports in FY %s.' % (pct(ind[1], TOT_I), pct(ind[2], TOT_E), FY), body,
               more=['india-vs-china-by-product-group', 'what-nepal-buys-from-china', 'products-with-a-single-supplier'])


def a_china():
    sh = _share_series('China'); c = next(x for x in S['countries'] if x[0] == 'China')
    prods = S['country_prod']['China'][0][:15]
    rows = [(plink(code) + ' <small>%s</small>' % dotted(code), v, '%s · %s of this line' % (money(v), pct(v, IMP[code][IMP_VALUE]) if code in IMP else '—')) for code, v in prods]
    body = [tiles([(money(c[1]), 'Imports from China'), (pct(c[1], TOT_I), 'of all imports'), (chg(c[1], co_hist('China')[0][0]), 'Change since FY %s' % Y[0])]),
            h2('China’s share of Nepal’s imports'), cols(Y, [sh], ['China’s share of imports'], fmt=lambda v: '%.1f%%' % v),
            h2('The 15 largest lines Nepal buys from China, FY %s' % FY),
            bars(rows, note='Import value from China, and China’s share of Nepal’s total imports of that line.'),
            takeaways(['Chinese goods pay the general duty rate, not the SAFTA rate. Each product page shows both.',
                       'Goods from China reach Nepal by sea through Indian ports or overland through Rasuwa and Tatopani. <a href="/the-border">See the gates</a>.',
                       '<a href="/trade-partner/china">China’s full profile</a> lists every line.'])]
    return art('what-nepal-buys-from-china', 'dep', 'What Nepal imports from China: top products, FY %s' % FY, 'What Nepal buys from China',
               'China supplied %s of goods, %s of Nepal’s imports, in FY %s. The largest line was %s.' % (money(c[1]), pct(c[1], TOT_I), FY, pname(prods[0][0]).lower()), body,
               more=['india-vs-china-by-product-group', 'how-much-nepal-depends-on-india', 'top-suppliers-to-nepal'])


def a_single():
    L = []
    for code, v in IMP.items():
        val = v[IMP_VALUE]; ps = v[IMP_PARTNERS] or []
        if val >= 100000 and ps and ps[0][1] / val >= 0.9:
            L.append((code, val, ps[0][0], ps[0][1] / val))
    L.sort(key=lambda x: -x[1])
    big = [c for c, v in IMP_RANK if v >= 100000]
    by = {}
    for x in L:
        by[x[2]] = by.get(x[2], 0) + 1
    topc = sorted(by.items(), key=lambda kv: -kv[1])[:5]
    rows = [(plink(c) + ' <small>%s</small>' % dotted(c), val, '%s · %s from %s' % (money(val), '%.0f%%' % (100 * s), esc(n))) for c, val, n, s in L[:20]]
    body = [tiles([('%d' % len(L), 'Lines with one supplier at 90% or more'), (pct(len(L), len(big)), 'of all lines worth over Rs 10 crore'), (pct(sum(x[1] for x in L), TOT_I), 'of import value sits in them')]),
            h2('The largest single-supplier lines, FY %s' % FY), bars(rows, note='Lines worth over Rs 10 crore where one country supplied at least 90%.'),
            h2('Which country is the single supplier'),
            table(['Country', 'Lines where it supplies 90% or more'], [(links.partner_link(n, esc), '%d' % k_) for n, k_ in topc], right=(1,)),
            takeaways(['A single-supplier line is exposed to one country’s export rules, prices and transit route.',
                       'Each product page lists the other countries that supplied even small amounts, which is where a second source usually starts.'])]
    return art('products-with-a-single-supplier', 'dep', 'Nepal imports with a single supplier country, FY %s' % FY, 'Imports that depend on one country',
               '%d import lines worth over Rs 10 crore came at least 90%% from one country in FY %s.' % (len(L), FY), body,
               more=['how-much-nepal-depends-on-india', 'top-suppliers-to-nepal', 'india-vs-china-by-product-group'])


def _group_art(slug_, chs, label, title, h1, more, tone='a'):
    ser = [sum(H['chapters'][str(c)][i][0] for c in chs if str(c) in H['chapters']) for i in range(len(Y))]
    share = [100.0 * ser[i] / H['totals'][i][0] for i in range(len(Y))]
    codes = [(c, v) for c, v in IMP_RANK if int(c[:2]) in chs][:15]
    rows = [(plink(c) + ' <small>%s</small>' % dotted(c), v, '%s · %s' % (money(v), chg(v, hist_code(c)[-2]))) for c, v in codes]
    rev = sum(CH[c][4] for c in chs if c in CH)
    body = [tiles([(money(ser[-1]), '%s imported, FY %s' % (label, FY)), ('%.1f%%' % share[-1], 'of all imports'), (money(rev), 'Collected at customs on them')]),
            h2('%s: imports over seven years' % label), cols(Y, [ser], [label]),
            p('Imports of %s were %s in FY %s and %s in FY %s (%s). Their share of the total import bill moved from %.1f%% to %.1f%%.'
              % (label.lower(), money(ser[0]), Y[0], money(ser[-1]), Y[-1], chg(ser[-1], ser[0]), share[0], share[-1])),
            h2('The 15 largest lines'), bars(rows, tone=tone, note='Import value, FY %s, and change on FY %s.' % (FY, FYP))]
    if len(chs) > 1:
        g = sorted(((c, CH[c][2]) for c in chs if c in CH), key=lambda x: -x[1])[:8]
        body += [h2('By product group'), bars([(chlink(c), v, '%s · %s' % (money(v), pct(v, ser[-1]))) for c, v in g], tone=tone)]
    return art(slug_, 'dep', title, h1, 'Nepal imported %s of %s in FY %s, %.1f%% of all imports.' % (money(ser[-1]), label.lower(), FY, share[-1]), body, more=more)


def a_fuel():
    return _group_art('nepal-fuel-import-bill', [27], 'Fuel', 'Nepal’s fuel import bill: petrol, diesel and LPG, FY %s' % FY, 'Nepal’s fuel import bill',
                      ['nepal-food-import-bill', 'top-imports-of-nepal', 'where-customs-revenue-comes-from'], tone='d')


def a_food():
    a = _group_art('nepal-food-import-bill', list(range(1, 25)), 'Food and farm goods', 'Nepal’s food import bill: rice, oil, vegetables, FY %s' % FY, 'Nepal’s food import bill',
                   ['nepal-fuel-import-bill', 'top-imports-of-nepal', 'how-much-nepal-depends-on-india'], tone='e')
    a['method'] = '“Food and farm” here means HS chapters 1 to 24: live animals, food, drink, animal feed and tobacco. Edible oil imported for refining and re-export is included.'
    return a


# =====================================================================
# D. Duty and revenue
# =====================================================================
def _bandlabel(b):
    return 'Duty free' if b == '0' else (b if not b.isdigit() else '%d%%' % int(b))


def a_bands():
    rows = [(_bandlabel(b[0]), b[2], '%s · %s' % (money(b[2]), pct(b[2], BAND_VAL))) for b in S['bands']]
    rows2 = [(_bandlabel(b[0]), b[1], '%s · %s' % (money(b[1]), pct(b[1], BAND_DUTY))) for b in S['bands']]
    cnt = {}
    for r in T['rows']:
        n, d = family.rate(r[5]); cnt[d if n is not None else 'Per unit'] = cnt.get(d if n is not None else 'Per unit', 0) + 1
    t = [(_bandlabel(b[0]), money(b[2]), pct(b[2], BAND_VAL), money(b[1]), pct(b[1], BAND_DUTY)) for b in S['bands']]
    top = max(S['bands'], key=lambda b: b[2]); topd = max(S['bands'], key=lambda b: b[1])
    body = [tiles([(pct(BAND['0'][2], BAND_VAL), 'of imports enter duty free'), (_bandlabel(top[0]), 'Band with the most imports'), (_bandlabel(topd[0]), 'Band that collects the most duty')]),
            h2('Import value in each duty band, FY %s' % FY), bars(rows, note='Value of imports that entered under each customs duty rate.'),
            h2('Customs duty collected in each band'), bars(rows2, tone='r', note='Customs duty only. VAT and excise are not in this figure.'),
            table(['Duty rate', 'Import value', 'Share', 'Duty collected', 'Share'], t, right=(1, 2, 3, 4)),
            p('The tariff itself has %s lines: %s.' % ('{:,}'.format(len(T['rows'])), ', '.join('%s at %s' % ('{:,}'.format(v), kx) for kx, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:7]))),
            takeaways(['Most import value sits in the low bands, while the high bands collect far more duty per rupee imported.',
                       'The <a href="/duty-free">duty-free page</a> lists the 0% and 5% lines. Each product page shows the other lines in its family and their rates.'])]
    return art('imports-by-duty-rate', 'tar', 'Nepal imports by customs duty rate: who pays what, FY %s' % FY, 'How much comes in at each duty rate',
               '%s of Nepal’s imports by value entered duty free in FY %s, and the %s band collected the most customs duty.' % (pct(BAND['0'][2], BAND_VAL), FY, _bandlabel(topd[0])), body,
               more=['where-customs-revenue-comes-from', 'highest-duty-goods-in-nepal', 'duty-free-share-over-time'],
               method='“Others” covers lines charged per unit (per litre, per stick, per tonne) and partial exemptions, as grouped by the Department of Customs.')


def a_highest():
    L = []
    for code, r in TROW.items():
        n, d = family.rate(r[5])
        if n is not None and n >= 40:
            L.append((code, n, d, IMP[code][IMP_VALUE] if code in IMP else 0))
    L.sort(key=lambda x: (-x[1], -x[3]))
    top = sorted(L, key=lambda x: -x[3])[:20]
    spec = sum(1 for r in T['rows'] if family.rate(r[5])[0] is None)
    mx = max(x[1] for x in L)
    rows = [(plink(c) + ' <small>%s · %s duty</small>' % (dotted(c), d), v, money(v)) for c, n, d, v in top if v > 0]
    by = {}
    for c, n, d, v in L:
        by[int(c[:2])] = by.get(int(c[:2]), 0) + 1
    body = [tiles([('%g%%' % mx, 'Highest percentage duty in the tariff'), ('%d' % len(L), 'Lines at 40% or more'), ('%d' % spec, 'Lines charged per unit instead')]),
            h2('The most-imported goods at 40%% duty or more, FY %s' % FY), bars(rows, tone='d', note='Import value of each line. All carry a general customs duty of 40% or more.'),
            h2('Which product groups hold the high-duty lines'),
            table(['Product group', 'Lines at 40% or more'], [(chlink(c), '%d' % n) for c, n in sorted(by.items(), key=lambda kv: -kv[1])[:8]], right=(1,)),
            p('A further %d lines carry a per-unit duty (so many rupees per litre, per thousand sticks, per tonne). These are mainly alcohol, tobacco and fuel, and their effective rate depends on the price of the goods.' % spec),
            takeaways(['Customs duty is only the first layer. Vehicles, alcohol and tobacco also pay excise, and VAT is charged on top of both. The <a href="/calculator">calculator</a> stacks them in order.',
                       'A high-duty line often has a lower-duty neighbour for a different build or size. Each product page shows the whole family.'])]
    return art('highest-duty-goods-in-nepal', 'tar', 'Highest customs duty in Nepal: goods taxed at 40%% to %g%%' % mx, 'The goods Nepal taxes hardest at the border',
               '%d tariff lines carry a customs duty of 40%% or more, up to %g%%.' % (len(L), mx), body,
               more=['imports-by-duty-rate', 'goods-that-pay-the-most-tax', 'high-duty-goods-nepal-still-imports'])


def a_payers():
    L = sorted(((c, v[IMP_REVENUE], v[IMP_VALUE]) for c, v in IMP.items() if v[IMP_VALUE] > 0), key=lambda x: -x[1])[:20]
    rows = [(plink(c) + ' <small>%s</small>' % dotted(c), r, '%s · %s of value' % (money(r), pct(r, v, 0))) for c, r, v in L]
    t = [(esc(pname(c)), money(v), money(r), pct(r, v, 0), esc(duty(c)[1])) for c, r, v in L]
    body = [tiles([(money(L[0][1]), 'Most revenue: ' + pname(L[0][0])[:30]), (pct(sum(x[1] for x in L), REV_TOTAL), 'of all customs revenue from these 20'), (pct(sum(x[2] for x in L), TOT_I), 'of import value')]),
            h2('The 20 import lines that paid the most at customs, FY %s' % FY), bars(rows, tone='r', note='Revenue collected at customs on each line, and that revenue as a share of the line’s import value.'),
            table(['Product', 'Imports', 'Revenue', 'Revenue as % of value', 'Customs duty rate'], t, right=(1, 2, 3, 4)),
            takeaways(['Where revenue as a share of value is well above the customs duty rate, the difference is excise, VAT and other border charges.',
                       'Where it is below the duty rate, part of the imports entered under an exemption, a SAFTA rate or a concession.'])]
    return art('goods-that-pay-the-most-tax', 'tar', 'Which imports pay the most tax in Nepal? Top 20, FY %s' % FY, 'The imports that pay the most at customs',
               '%s paid more at customs than any other line: %s in FY %s.' % (pname(L[0][0]), money(L[0][1]), FY), body,
               more=['where-customs-revenue-comes-from', 'effective-tax-rate-by-product-group', 'highest-duty-goods-in-nepal'],
               method='“Revenue” is the Department of Customs figure for all taxes collected at the border on that line, not customs duty alone.')


def a_effective():
    L = sorted(((c[0], c[2], c[4]) for c in S['chapters'] if c[2] >= 1e7), key=lambda x: -x[2] / x[1])
    hi, lo = L[:12], L[-12:][::-1]
    f = lambda xs, tone: bars([(chlink(c), 100.0 * r / v, '%s on %s' % (pct(r, v), money(v))) for c, v, r in xs], tone=tone)
    body = [tiles([(pct(REV_TOTAL, TOT_I), 'Average across all imports'), (pct(hi[0][2], hi[0][1]), 'Highest: ' + chname(hi[0][0])), (pct(lo[0][2], lo[0][1]), 'Lowest: ' + chname(lo[0][0]))]),
            h2('Product groups taxed most heavily'), f(hi, 'd'), h2('Product groups taxed most lightly'), f(lo, 'e'),
            p('The figure is revenue collected at customs divided by import value, for every product group with imports over Rs 10 arba in FY %s. It is what was actually paid, after exemptions and SAFTA rates, not the rate printed in the tariff.' % FY),
            takeaways(['Use this as a first estimate of how far landed cost sits above invoice value in a sector. The exact figure for a line is on its product page.',
                       'Light-taxed groups are mostly inputs: fertiliser, raw materials, machinery. Heavy-taxed groups are mostly finished consumer goods and fuel.'])]
    return art('effective-tax-rate-by-product-group', 'tar', 'Effective import tax rate by product group in Nepal, FY %s' % FY, 'What each product group really pays at the border',
               'Across all imports, customs collected %s of value in FY %s. By product group it ranged from %s to %s.' % (pct(REV_TOTAL, TOT_I), FY, pct(lo[0][2], lo[0][1]), pct(hi[0][2], hi[0][1])), body,
               more=['where-customs-revenue-comes-from', 'goods-that-pay-the-most-tax', 'imports-by-duty-rate'])


def a_safta():
    L = []
    for code, r in TROW.items():
        g, s = family.rate(r[5])[0], family.rate(r[4])[0]
        if g is None or s is None or s >= g:
            continue
        ind = 0
        if code in IMP:
            ind = sum(v for n, v in (IMP[code][IMP_PARTNERS] or []) if n == 'India')
        L.append((code, g, s, ind))
    gaps = {}
    for c, g, s, i in L:
        gaps[g - s] = gaps.get(g - s, 0) + 1
    top = sorted(L, key=lambda x: -x[3])[:20]
    rows = [(plink(c) + ' <small>%s · %g%% general, %g%% SAFTA</small>' % (dotted(c), g, s), i, money(i)) for c, g, s, i in top if i > 0]
    body = [tiles([('{:,}'.format(len(L)), 'Lines with a lower SAFTA rate'), (pct(len(L), len(TROW), 0), 'of the whole tariff'), ('%g points' % max(gaps), 'Largest gap between the two rates')]),
            h2('How big the SAFTA saving is'),
            table(['Gap between general and SAFTA duty', 'Number of lines'], [('%g percentage points' % g_, '{:,}'.format(n)) for g_, n in sorted(gaps.items(), key=lambda kv: -kv[1])[:8]], right=(1,)),
            h2('SAFTA-eligible lines Nepal imports most from India, FY %s' % FY),
            bars(rows, note='Import value from India of lines whose SAFTA rate is below the general rate.'),
            takeaways(['The lower rate applies only with a valid certificate of origin, and only to goods that meet the origin rules. <a href="/safta">How SAFTA works</a>.',
                       'The saving is larger than the duty gap, because VAT is charged on the value after duty.'])]
    return art('safta-duty-savings-by-product', 'tar', 'SAFTA duty savings in Nepal: %s lines with a lower rate' % '{:,}'.format(len(L)), 'Where the SAFTA rate beats the general rate',
               '%s of Nepal’s %s tariff lines carry a lower duty for goods from India and other SAARC countries.' % ('{:,}'.format(len(L)), '{:,}'.format(len(TROW))), body,
               more=['how-much-nepal-depends-on-india', 'imports-by-duty-rate', 'india-vs-china-by-product-group'],
               method='Rates are from the Nepal Customs Tariff %s. India import values are from the top-six partner list for each line, so small amounts may be missing.' % TARIFF_FY)


def a_dutyfree_time():
    ser = []
    for i, bs in enumerate(H['bands']):
        d = {b[0]: b for b in bs}; tv = sum(b[2] for b in bs)
        ser.append((100.0 * d.get('0', [0, 0, 0])[2] / tv, 100.0 * sum(b[2] for b in bs if b[0] in ('0', '01', '05')) / tv, 100.0 * sum(b[2] for b in bs if b[0] in ('30', '40', '80')) / tv))
    t = [(y, '%.1f%%' % a, '%.1f%%' % b, '%.1f%%' % c) for y, (a, b, c) in zip(Y, ser)]
    body = [tiles([('%.1f%%' % ser[-1][0], 'Duty free, FY %s' % FY), ('%.1f%%' % ser[-1][1], 'At 5% or less'), ('%.1f%%' % ser[-1][2], 'At 30% or more')]),
            h2('Share of import value by duty level, FY %s to %s' % (Y[0], Y[-1])),
            cols(Y, [[s[1] for s in ser], [s[2] for s in ser]], ['At 5% or less (including duty free)', 'At 30% or more'], fmt=lambda v: '%.1f%%' % v),
            table(['Fiscal year', 'Duty free', '5% or less', '30% or more'], t, right=(1, 2, 3)),
            p('In FY %s, %.1f%% of imports by value entered at 5%% duty or less; in FY %s it was %.1f%%. The share entering at 30%% or more went from %.1f%% to %.1f%%.'
              % (Y[0], ser[0][1], Y[-1], ser[-1][1], ser[0][2], ser[-1][2])),
            takeaways(['The mix shifts when the tariff changes and when the goods people buy change. This chart shows the result, not which of the two caused it.',
                       'See <a href="/tariff/2083-84-changes">what changed in this year’s tariff</a>.'])]
    return art('duty-free-share-over-time', 'tar', 'How much of Nepal’s imports enter duty free? Seven years' , 'Is Nepal taxing imports more or less?',
               '%.1f%% of Nepal’s imports by value entered duty free in FY %s, against %.1f%% in FY %s.' % (ser[-1][0], Y[-1], ser[0][0], Y[0]), body,
               more=['imports-by-duty-rate', 'highest-duty-goods-in-nepal', 'where-customs-revenue-comes-from'])


# =====================================================================
# E. Business openings
# =====================================================================
def a_substitution():
    L = []
    for c, v in IMP_RANK:
        n, d = duty(c)
        if n is not None and n >= 20 and v >= 500000:
            L.append((c, v, d, n))
    rows = [(plink(c) + ' <small>%s · %s duty</small>' % (dotted(c), d), v, '%s · %s' % (money(v), chg(v, hist_code(c)[0]) + ' since ' + Y[0])) for c, v, d, n in L[:20]]
    by = {}
    for c, v, d, n in L:
        by[int(c[:2])] = by.get(int(c[:2]), 0) + v
    body = [tiles([('%d' % len(L), 'Lines at 20% duty or more with imports over Rs 50 crore'), (money(sum(x[1] for x in L)), 'Combined imports'), (pct(sum(x[1] for x in L), TOT_I), 'of all imports')]),
            h2('High duty, still heavily imported: the top 20, FY %s' % FY), bars(rows, tone='d', note='Lines with a general customs duty of 20% or more, ranked by import value.'),
            h2('Where they cluster'), bars([(chlink(c), v, money(v)) for c, v in sorted(by.items(), key=lambda kv: -kv[1])[:8]], tone='d'),
            takeaways(['A high duty with high imports means buyers pay the tax and still import. That is the pattern a local producer or assembler looks for, though the data cannot say whether local production is feasible.',
                       'Many of these headings rate unassembled kits and parts lower than finished goods. Open a product and read its family table.',
                       'Check who supplies each line and at what unit value on its product page before sizing a market.'])]
    return art('high-duty-goods-nepal-still-imports', 'biz', 'High-duty goods Nepal still imports heavily, FY %s' % FY, 'High duty, high imports: where local supply is thin',
               '%d lines carry 20%% duty or more and were still imported for over Rs 50 crore each in FY %s.' % (len(L), FY), body,
               more=['highest-duty-goods-in-nepal', 'top-imports-of-nepal', 'products-nepal-both-imports-and-exports'])


def a_winners():
    base = 1                      # FY Y[1] -> five fiscal years to Y[-1]
    L = []
    for c, hs in H['codes'].items():
        cur, old = hs[-1][1], hs[base][1]
        if cur >= 200000:
            L.append((c, cur, old, cur - old))
    L.sort(key=lambda x: -x[3]); L = [x for x in L if x[3] > 0][:20]
    rows = [(esc(pname(c)) + ' <small>%s</small>' % dotted(c), d, '+%s · now %s' % (money(d), money(cur))) for c, cur, old, d in L]
    t = [(esc(pname(c)), money(old), money(cur), 'new' if not old else '%.1f×' % (cur / old)) for c, cur, old, d in L]
    body = [tiles([(money(L[0][3]), 'Largest gain: ' + pname(L[0][0])[:30]), ('%d' % sum(1 for x in L if x[2] == 0), 'of the 20 were not exported at all in FY %s' % Y[base]), (chg(H['totals'][-1][1], H['totals'][base][1]), 'All exports, same period')]),
            h2('The 20 export lines that gained most, FY %s to %s' % (Y[base], Y[-1])), bars(rows, tone='e', note='Gain in export value over five fiscal years.'),
            table(['Product', 'FY %s' % Y[base], 'FY %s' % Y[-1], 'Multiple'], t, right=(1, 2, 3)),
            takeaways(['Some large gains are processing trade: an input is imported, processed and re-exported, and the export figure records the full value. Compare with <a href="/insights/products-nepal-both-imports-and-exports">goods Nepal both imports and exports</a>.',
                       'Sector pages show which countries bought each group and how it moved month by month.'])]
    return art('nepal-export-winners-five-years', 'biz', 'Nepal’s fastest-growing exports over five years' , 'Nepal’s export winners of the last five years',
               '%s added %s in export value between FY %s and FY %s, more than any other line.' % (pname(L[0][0]), money(L[0][3]), Y[base], Y[-1]), body,
               more=['top-exports-of-nepal', 'exports-that-grew-most', 'products-nepal-both-imports-and-exports'])


def a_twoway():
    L = []
    for c in set(IMP) & set(EXP):
        i, e = IMP[c][IMP_VALUE], EXP[c][EXP_VALUE]
        if min(i, e) >= 50000:
            L.append((c, i, e))
    L.sort(key=lambda x: -min(x[1], x[2]))
    t = [(plink(c) + ' <small>%s</small>' % dotted(c), money(i), money(e), money(e - i)) for c, i, e in L[:20]]
    rows = [(esc(pname(c)), min(i, e), 'in %s · out %s' % (money(i), money(e))) for c, i, e in L[:12]]
    h6 = {}
    for c, v in IMP.items():
        h6[c[:4]] = h6.get(c[:4], 0) + v[IMP_VALUE]
    body = [tiles([('%d' % len(L), 'Lines both imported and exported (over Rs 5 crore each way)'), (money(sum(x[2] for x in L)), 'Their exports'), (pct(sum(x[2] for x in L), TOT_E), 'of all exports')]),
            h2('The largest two-way lines, FY %s' % FY), bars(rows, note='Ranked by the smaller of the two flows.'),
            table(['Product', 'Imports', 'Exports', 'Balance'], t, right=(1, 2, 3)),
            takeaways(['Two-way trade in the same line can mean re-export, different grades of the same product, or border trade in both directions. The figures alone do not say which.',
                       'For an exporter, a line Nepal also imports is one where a foreign product already competes at home.'])]
    return art('products-nepal-both-imports-and-exports', 'biz', 'Goods Nepal both imports and exports, FY %s' % FY, 'The goods Nepal both buys and sells',
               '%d tariff lines moved in both directions for more than Rs 5 crore each way in FY %s.' % (len(L), FY), body,
               more=['nepal-export-winners-five-years', 'top-exports-of-nepal', 'high-duty-goods-nepal-still-imports'])


def a_concentration():
    cum = 0; marks = {}; targets = [50, 80, 90]
    for i, (c, v) in enumerate(EXP_RANK, 1):
        cum += v
        for tg in targets:
            if tg not in marks and cum >= TOT_E * tg / 100.0:
                marks[tg] = i
    cumi = 0; mi = {}
    for i, (c, v) in enumerate(IMP_RANK, 1):
        cumi += v
        for tg in targets:
            if tg not in mi and cumi >= TOT_I * tg / 100.0:
                mi[tg] = i
    t = [('%d%%' % tg, '%d' % marks.get(tg, len(EXP_RANK)), '%d' % mi.get(tg, len(IMP_RANK))) for tg in targets]
    top5 = sum(v for _, v in EXP_RANK[:5])
    body = [tiles([('%d' % marks[50], 'Lines make half of all exports'), ('%d' % marks[80], 'Lines make 80%'), (pct(CO_E[0][2], TOT_E), 'of exports go to one country')]),
            h2('How few products carry the export total'),
            table(['Share of the total', 'Export lines needed', 'Import lines needed'], t, right=(1, 2)),
            p('Half of Nepal’s exports come from %d tariff lines; half of its imports take %d. The five largest export lines are worth %s, %s of the total.'
              % (marks[50], mi[50], money(top5), pct(top5, TOT_E))),
            h2('The five lines'), bars([(esc(pname(c)) + ' <small>%s</small>' % dotted(c), v, '%s · %s' % (money(v), pct(v, TOT_E))) for c, v in EXP_RANK[:5]], tone='e'),
            h2('And the buyers'), bars([(links.partner_link(c[0], esc), c[2], '%s · %s' % (money(c[2]), pct(c[2], TOT_E))) for c in CO_E[:5]], tone='e'),
            takeaways(['Concentration cuts both ways: a few lines doing well lifts the whole total, and a setback in one is visible nationally.',
                       'The long tail is where new exporters start. %d lines were exported in the year; most are small.' % len(EXP)])]
    return art('nepal-export-concentration', 'biz', 'How concentrated are Nepal’s exports? FY %s' % FY, 'How few products Nepal’s exports rest on',
               'Just %d tariff lines produce half of Nepal’s exports, and %s of exports go to one country.' % (marks[50], pct(CO_E[0][2], TOT_E)), body,
               more=['top-exports-of-nepal', 'top-export-markets-of-nepal', 'nepal-export-winners-five-years'])


def a_india_china():
    fi, fc = dict(S['flow']['India']), dict(S['flow']['China'])
    L = sorted(((ch, fi.get(ch, 0), fc.get(ch, 0), CH[ch][2]) for ch in CH if CH[ch][2] >= 1e7), key=lambda x: -x[3])[:20]
    lead = lambda i, c, tot: 'India' if (i >= c and i >= tot - i - c) else ('China' if (c > i and c >= tot - i - c) else 'Other countries')
    t = [(chlink(ch), money(tot), pct(i, tot, 0), pct(c, tot, 0), pct(tot - i - c, tot, 0), lead(i, c, tot)) for ch, i, c, tot in L]
    n_i = sum(1 for ch, i, c, tot in L if lead(i, c, tot) == 'India'); ch_c = [x for x in L if lead(x[1], x[2], x[3]) == 'China']
    ch_o = [x for x in L if lead(x[1], x[2], x[3]) == 'Other countries']
    rows = ''.join('<li><span class="l">%s</span><span class="sp"><i class="i" style="width:%.1f%%"></i><i class="c" style="width:%.1f%%"></i></span><span class="v">%s</span></li>'
                   % (chlink(ch), 100.0 * i / tot, 100.0 * c / tot, money(tot)) for ch, i, c, tot in L)
    body = [tiles([('%d of %d' % (n_i, len(L)), 'Large groups where India supplies the most'), ('%d' % len(ch_c), 'Where China does'), (pct(sum(x[1] + x[2] for x in L), sum(x[3] for x in L)), 'of these imports come from the two')]),
            h2('India and China in Nepal’s 20 largest import groups, FY %s' % FY),
            '<ol class="ins-split">%s</ol><p class="fineprint"><span class="k i"></span>India <span class="k c"></span>China. The unshaded part is every other country.</p>' % rows,
            table(['Product group', 'Imports', 'India', 'China', 'Others', 'Largest share'], t, right=(1, 2, 3, 4)),
            p('China supplies the most in %s.%s' % (', '.join(esc(chname(x[0])) for x in ch_c) if ch_c else 'none of the 20',
                                                  (' In %s, all other countries combined supply more than either.' % ', '.join(esc(chname(x[0])) for x in ch_o)) if ch_o else '')),
            takeaways(['Where India leads, check the SAFTA rate. Where China leads, the general rate applies and transit is longer.',
                       '<a href="/compare">Compare the two countries line by line</a>.'])]
    return art('india-vs-china-by-product-group', 'dep', 'India vs China in Nepal’s imports, by product group, FY %s' % FY, 'India or China: who supplies what',
               'Of Nepal’s 20 largest import groups, India supplies the most in %d and China in %d.' % (n_i, len(ch_c)), body,
               more=['how-much-nepal-depends-on-india', 'what-nepal-buys-from-china', 'top-suppliers-to-nepal'])


def a_season():
    yrs = [y for y in S['monthly'] if len(S['monthly'][y]) == 12 and all(m and m.get('val') for m in S['monthly'][y]) and y != S['current']['fy']]
    names = S['month_names']
    avg_i = [sum(100.0 * S['monthly'][y][m]['val'][0] / sum(x['val'][0] for x in S['monthly'][y]) for y in yrs) / len(yrs) for m in range(12)]
    avg_e = [sum(100.0 * S['monthly'][y][m]['val'][1] / sum(x['val'][1] for x in S['monthly'][y]) for y in yrs) / len(yrs) for m in range(12)]
    hi, lo = avg_i.index(max(avg_i)), avg_i.index(min(avg_i))
    t = [(names[m], '%.1f%%' % avg_i[m], '%.1f%%' % avg_e[m]) for m in range(12)]
    body = [tiles([(names[hi], 'Busiest month for imports'), (names[lo], 'Quietest month'), ('%.1f×' % (max(avg_i) / min(avg_i)), 'Busiest against quietest')]),
            h2('Each month’s share of the year, averaged over %d fiscal years' % len(yrs)),
            cols(names, [avg_i, avg_e], ['Imports', 'Exports'], fmt=lambda v: '%.1f%%' % v),
            table(['Month', 'Share of the year’s imports', 'Share of the year’s exports'], t, right=(1, 2)),
            p('An even year would put 8.3%% in every month. On average over FY %s, %s takes %.1f%% of imports and %s %.1f%%.' % (' , '.join(yrs).replace(' , ', ', '), names[hi], avg_i[hi], names[lo], avg_i[lo])),
            takeaways(['Busy months mean busier customs yards and tighter truck supply at the main gates. Book transport earlier in those months.',
                       'The pattern is an average of %d years. Any one year can differ.' % len(yrs)])]
    return art('when-nepal-imports-most', 'move', 'When does Nepal import the most? Month-by-month pattern', 'The months when Nepal imports most',
               '%s is on average the busiest month for imports and %s the quietest.' % (names[hi], names[lo]), body,
               more=['this-fiscal-year-so-far', 'nepal-busiest-customs-points', 'nepal-trade-year-in-numbers'],
               method='Monthly values are the Department of Customs’ month-by-month figures for FY %s. Nepali months run mid-month to mid-month (Shrawan starts in mid-July).' % ', '.join(yrs))


def a_ev():
    ev = [c for c in H['codes'] if c.startswith('870380')]
    oth = [c for c in H['codes'] if c.startswith('8703') and not c.startswith('870380')]
    se = [sum(H['codes'][c][i][0] for c in ev) for i in range(len(Y))]
    so = [sum(H['codes'][c][i][0] for c in oth) for i in range(len(Y))]
    share = [100.0 * a / (a + b) if a + b else 0 for a, b in zip(se, so)]
    cur = sorted(((c, IMP[c][IMP_VALUE]) for c in ev if c in IMP), key=lambda x: -x[1])[:10]
    rows = [(plink(c) + ' <small>%s · %s duty</small>' % (dotted(c), duty(c)[1]), v, money(v)) for c, v in cur]
    t = [(y, money(a), money(b), '%.0f%%' % s) for y, a, b, s in zip(Y, se, so, share)]
    src = {}
    for c in ev:
        if c in IMP:
            for n, v in IMP[c][IMP_PARTNERS] or []:
                src[n] = src.get(n, 0) + v
    tops = sorted(src.items(), key=lambda kv: -kv[1])[:5]
    body = [tiles([(money(se[-1]), 'Electric vehicle imports, FY %s' % FY), ('%.0f%%' % share[-1], 'of all passenger-vehicle imports by value'), (money(so[-1]), 'Petrol, diesel and hybrid')]),
            h2('Electric against other passenger vehicles, FY %s to %s' % (Y[0], Y[-1])), cols(Y, [se, so], ['Electric', 'Petrol, diesel and hybrid']),
            table(['Fiscal year', 'Electric', 'Other', 'Electric share'], t, right=(1, 2, 3)),
            h2('The electric lines, by import value'), bars(rows, tone='e', note='Lines under HS 8703.80 (vehicles with only an electric motor), FY %s. Duty steps up with motor power.' % FY),
            h2('Where they come from'), bars([(links.partner_link(n, esc), v, '%s · %s' % (money(v), pct(v, se[-1]))) for n, v in tops], tone='e'),
            takeaways(['Electric vehicle duty and excise are set by motor power (kW). The band a model falls in changes its landed cost sharply. Each line’s page shows its family.',
                       'Vehicles also pay excise and a road fee on top of customs duty. Use the <a href="/calculator">calculator</a> for the full stack.',
                       'The <a href="/sector/vehicles">vehicles sector page</a> has suppliers and monthly movement.'])]
    return art('electric-vs-petrol-vehicle-imports', 'biz', 'Electric vs petrol vehicle imports in Nepal, FY %s to %s' % (Y[0], Y[-1]), 'Electric vehicles against petrol: the import numbers',
               'Electric vehicles were %.0f%% of Nepal’s passenger-vehicle imports by value in FY %s, against %.0f%% in FY %s.' % (share[-1], Y[-1], share[0], Y[0]), body,
               more=['highest-duty-goods-in-nepal', 'goods-that-pay-the-most-tax', 'what-nepal-buys-from-china'],
               method='Passenger vehicles are HS heading 87.03. Electric means subheading 8703.80; hybrids are counted with petrol and diesel.')


ARTICLES = [a_year, a_deficit, a_top_imports, a_top_exports, a_suppliers, a_markets, a_gates,
            a_imp_up, a_imp_down, a_exp_up, a_ytd, a_season,
            a_india, a_china, a_india_china, a_single, a_fuel, a_food,
            a_revenue, a_bands, a_highest, a_payers, a_effective, a_safta, a_dutyfree_time,
            a_substitution, a_winners, a_twoway, a_concentration, a_ev]

CSS = ('<style>.ins-kick{font-size:.85rem;color:var(--muted);margin:0 0 .3em}.ins-kick a{color:inherit;text-decoration:underline}'
       '.ins-dek{font-size:1.12rem;line-height:1.5;color:var(--fg2);max-width:62ch;margin:.2em 0 1em}'
       '.ins-by{font-size:.82rem;color:var(--muted);margin:0 0 1.2em}'
       '.ins-bars{list-style:none;margin:.6em 0;padding:0;counter-reset:n}'
       '.ins-bars li{counter-increment:n;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr) auto;gap:4px 12px;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);font-size:.92rem}'
       '.ins-bars .l{min-width:0;overflow-wrap:anywhere}.ins-bars .l::before{content:counter(n) ". ";color:var(--muted);font-variant-numeric:tabular-nums}'
       '.ins-bars small{color:var(--muted);font-family:var(--mono);font-size:.74rem;white-space:nowrap}'
       '.ins-bars .b{height:12px;background:var(--spec-bg);border-radius:6px;overflow:hidden}.ins-bars .b i{display:block;height:100%;border-radius:6px;background:var(--accent)}'
       '.ins-bars.t-e .b i{background:var(--free)}.ins-bars.t-d .b i{background:var(--hi)}.ins-bars.t-r .b i{background:var(--mid)}'
       '.ins-bars .v{font-weight:650;font-variant-numeric:tabular-nums;white-space:nowrap;font-size:.86rem}'
       '.ins-cols{margin:.8em 0;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 14px 12px}'
       '.ins-cols .g{display:flex;align-items:flex-end;gap:6px;height:190px}'
       '.ins-cols .c{flex:1 1 0;min-width:0;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:6px}'
       '.ins-cols .bb{flex:1;width:100%;display:flex;align-items:flex-end;justify-content:center;gap:2px}'
       '.ins-cols .bb i{display:block;flex:1 1 0;max-width:26px;border-radius:5px 5px 0 0}'
       '.ins-cols .c span{font-size:.7rem;color:var(--muted);white-space:nowrap}'
       '.ins-cols i.s0{background:var(--accent)}.ins-cols i.s1{background:var(--free)}.ins-cols i.s2{background:var(--hi)}'
       '.ins-cols figcaption{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:10px;font-size:.8rem;color:var(--fg2)}'
       '.ins-cols figcaption i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}'
       '.ins-t .r{text-align:right;white-space:nowrap}.ins-t small{color:var(--muted);font-family:var(--mono);font-size:.74rem}'
       '.ins-num{padding-left:1.4em}.ins-num li{margin:.5em 0;line-height:1.5}'
       '.ins-take{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:12px;background:var(--card);padding:14px 18px;margin:1.6em 0}'
       '.ins-take h2{font-size:1.02rem;margin:0 0 .4em}.ins-take ul{margin:0;padding-left:1.1em}.ins-take li{margin:.4em 0}'
       '.ins-split{list-style:none;margin:.6em 0;padding:0}.ins-split li{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr) auto;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:.9rem}'
       '.ins-split .sp{display:flex;height:14px;background:var(--spec-bg);border-radius:7px;overflow:hidden}.ins-split .sp .i,.fineprint .k.i{background:var(--accent)}.ins-split .sp .c,.fineprint .k.c{background:var(--hi)}'
       '.ins-split .v{font-weight:650;white-space:nowrap;font-size:.86rem}.fineprint .k{display:inline-block;width:10px;height:10px;border-radius:3px;margin:0 5px 0 10px}'
       '.ins-more{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:.6em 0 1.4em}'
       '.ins-card{display:block;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;color:var(--fg);text-decoration:none}'
       '.ins-card:hover{border-color:var(--accent);text-decoration:none}.ins-card b{display:block;line-height:1.3}.ins-card span{display:block;font-size:.84rem;color:var(--fg2);margin-top:4px;line-height:1.4}'
       '.ins-card em{font-style:normal;font-size:.72rem;font-weight:650;color:var(--accent)}'
       '.ins-lead{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:1em 0 1.6em}.ins-lead .ins-card b{font-size:1.1rem}'
       '@media(max-width:600px){.ins-bars li{grid-template-columns:minmax(0,1fr) auto}.ins-bars .b{grid-column:1/-1;grid-row:2;height:8px}'
       '.ins-split li{grid-template-columns:minmax(0,1fr) auto}.ins-split .sp{grid-column:1/-1;grid-row:2}.ins-cols .g{height:150px;gap:3px}.ins-cols .c span{font-size:.58rem}}</style>')


def card(a, lead=False):
    return '<a class="ins-card" href="/insights/%s"><em>%s</em><b>%s</b><span>%s</span></a>' % (a['slug'], esc(TAGS[a['tag']]), esc(a['h1']), esc(a['dek']))


def build():
    arts = [f() for f in ARTICLES]
    by = {a['slug']: a for a in arts}
    assert len(by) == len(arts), 'duplicate insight slug'
    (pub / 'insights').mkdir(exist_ok=True)
    for old in (pub / 'insights').glob('*.html'):
        if old.stem not in by:
            old.unlink()
    for a in arts:
        path = '/insights/' + a['slug']
        bc = [('Home', '/'), ('Insights', '/insights'), (a['h1'], '')]
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": a['h1'], "description": a['dek'],
              "datePublished": "2026-11-12", "dateModified": TODAY, "mainEntityOfPage": k.SITE + path,
              "author": {"@type": "Organization", "name": "Customs Nepal", "url": k.SITE},
              "publisher": {"@type": "Organization", "name": "Customs Nepal", "url": k.SITE},
              "isBasedOn": "https://www.customs.gov.np"}
        out = [k.page_head(a['title'], a['dek'], path, bc, extra_ld=[ld]), k.crumb_html(bc), CSS,
               '<article><p class="ins-kick"><a href="/insights#%s">%s</a></p><h1>%s</h1><p class="ins-dek">%s</p>'
               '<p class="ins-by">Customs Nepal data desk · Figures for FY %s · Updated %s</p>' % (a['tag'], esc(TAGS[a['tag']]), esc(a['h1']), esc(a['dek']), FY, TODAY)]
        out += a['body']
        out.append('<h2 class="sec">How this was worked out</h2><p class="fineprint">Every figure is calculated from the %s, FY %s, and the Nepal Customs Tariff %s. '
                   'Values are in Nepali rupees (1 crore = 10 million, 1 arba = 1 billion, 1 kharba = 100 billion). %s '
                   'The article reports what the data shows and does not explain causes it cannot show.</p>' % (SRC, FY, TARIFF_FY, a['method']))
        more = [by[s] for s in a['more'] if s in by]
        if more:
            out.append('<h2 class="sec">Read next</h2><div class="ins-more">%s</div>' % ''.join(card(m) for m in more))
        out.append('</article>')
        out.append(k.foot('<b>Source:</b> %s, FY %s; Nepal Customs Tariff %s.' % (SRC, FY, TARIFF_FY)))
        (pub / 'insights' / (a['slug'] + '.html')).write_text(''.join(out), encoding='utf-8')
        for s in a['more']:
            assert s in by, 'insight %s links to missing %s' % (a['slug'], s)

    # hub
    title = 'Nepal trade insights: %d data articles on imports, exports and duty' % len(arts)
    desc = 'What Nepal buys and sells, who from, what it pays at the border and where the openings are. %d articles built from Department of Customs figures, FY %s.' % (len(arts), FY)
    bc = [('Home', '/'), ('Insights', '')]
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc,
          "hasPart": [{"@type": "Article", "headline": a['h1'], "url": k.SITE + '/insights/' + a['slug']} for a in arts]}
    out = [k.page_head(title, desc, '/insights', bc, extra_ld=[ld]), k.crumb_html(bc), CSS,
           '<h1>Insights: Nepal’s trade, read from the customs data</h1>'
           '<p class="ins-dek">%d articles, each worked out from the Department of Customs’ own figures for FY %s and refreshed when new data is published. '
           'They say what moved and by how much, and link to the pages that go deeper.</p>' % (len(arts), FY),
           '<div class="ins-lead">%s</div>' % ''.join(card(by[s]) for s in ('nepal-trade-year-in-numbers', 'this-fiscal-year-so-far', 'high-duty-goods-nepal-still-imports'))]
    for tag, name in TAGS.items():
        group = [a for a in arts if a['tag'] == tag]
        out.append('<h2 class="sec" id="%s">%s</h2><div class="ins-more">%s</div>' % (tag, esc(name), ''.join(card(a) for a in group)))
    out.append(k.foot('<b>Source:</b> %s, FY %s; Nepal Customs Tariff %s.' % (SRC, FY, TARIFF_FY)))
    (pub / 'insights.html').write_text(''.join(out), encoding='utf-8')
    n = k.add_to_sitemap(['/insights'] + ['/insights/' + a['slug'] for a in arts])
    print('insights_pages: hub + %d articles; +%d sitemap URLs' % (len(arts), n))


if __name__ == '__main__':
    build()
