"""Sector pages: /sectors (hub) and /sector/<slug> — one industry view across products, suppliers and duty.

Build-time, stdlib only. Everything comes from data/stats.json (Department of Customs Foreign Trade
Statistics, already parsed) and data/tariff.json (duty rates). A sector is a fixed list of HS prefixes
(SECTORS below), so pages refresh with every data update. Nothing is estimated.

These are the FREE summary pages: headline figures, top 10 products, main suppliers, duty. The long tail
(full product lists, supplier history, custom HS cuts) is deliberately left for the on-request report —
no table-download buttons here.
"""
import json, re, urllib.parse
import pagekit as k
from pagekit import esc, money, pub, root, SITE
import links, viz
import viz_story as story

S = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
TAR = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
FY, HY = S['fy'], S['history']['years']
TOT_IMP, TOT_EXP = S['history']['totals'][-1][0], S['history']['totals'][-1][1]
DUTY = {re.sub(r'\D', '', str(r[0])): (str(r[5]).strip(), str(r[4]).strip()) for r in TAR['rows']}
MONTHS = S.get('month_names', [])
MON = S.get('monthly', {}).get(FY, [])
EXCISE_CH = {'22', '24', '87'}
CONTACT = 'info@customsnepal.com'

from sectors_def import SECTORS, member


SRC = 'Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s · customsnepal.com' % FY
SHAPES = json.loads((root / 'world/data/worldmap.json').read_text(encoding='utf-8')) if (root / 'world/data/worldmap.json').exists() else {}
NAT_TAKE = (sum(r[4] for r in S['imports'].values()) / TOT_IMP * 100) if TOT_IMP else 0     # Rs collected per Rs 100, all imports
DESC = {re.sub(r'\D', '', str(r[0])): ' '.join(str(r[1]).split()) for r in TAR['rows']}


def fig(title, svg, legend=''):
    """Chart frame with 'Save image' only — these pages are summaries, so no data-copy button."""
    return ('<figure class="vzfig" data-title="%s" data-src="%s"><figcaption><b>%s</b>%s<span class="vzbtns">'
            '<button type="button" data-act="png">Save image</button></span></figcaption><div class="vzwrap">%s</div></figure>'
            % (esc(title), esc(SRC), esc(title), legend, svg))


def iso_of(cn):
    return links._PARTNER.get(str(cn).strip().lower())


def flag_of(cn):
    i = iso_of(cn)
    return links._C['countries'][i].get('flag', '') if i else '🏳️'


def country_flow(b, rows, total, note, title):
    """Sankey: the sector on the left, its top countries on the right."""
    items = [(cn, flag_of(cn), v, story.CLS[k]) for k, (cn, v) in enumerate(rows[:5])]
    other = total - sum(v for _, v in rows[:5])
    if other > total * 0.005:
        items.append(('Other countries', '🌍', other, 'cg'))
    sk, _ = story.sankey('%s %s' % (b['icon'], esc(viz.cut(b['name'], 24))), items, money, title, note)
    return fig(title, sk)


def country_map(rows, title):
    tot = {}
    for cn, v in rows:
        i = iso_of(cn)
        if i:
            tot[i] = tot.get(i, 0.0) + v
    if not SHAPES or not tot:
        return ''
    wm = story.worldmap(SHAPES, tot, {i: links.PARTNER_PAGE[i][0] for i in tot if i in links.PARTNER_PAGE},
                        {i: c['name'] for i, c in links._C['countries'].items()}, money)
    return fig(title, wm.replace('two-way trade with Nepal', 'in this sector'))


def product_map(rows, total, title, vi):
    """Treemap of the top 12 product lines, coloured by 4-digit HS heading."""
    heads = list(dict.fromkeys(c[:4] for c, _ in rows[:12]))[:5]
    cells = [(r[0], viz.chap_icon(c[:2]), r[vi], story.CLS[heads.index(c[:4])] if c[:4] in heads else 'cg') for c, r in rows[:12]]
    cov = sum(r[vi] for _, r in rows[:12]) / total * 100 if total else 0
    tf = '%s — top %d products, %.0f%% of the total' % (title, len(cells), cov)
    tm, _ = story.treemap(cells, money, tf, whole=total)
    return fig(tf, tm)


def movers(b, idx, word):
    """Products with the largest rise and fall against the previous year (from the 7-year code history)."""
    rows = []
    for c, h in S['history']['codes'].items():
        if member(c, b['pre'], b['exc']) and len(h) >= 2:
            d = h[-1][idx] - h[-2][idx]
            if abs(d) > 0:
                src = S['imports'] if idx == 0 else S['exports']
                rows.append((d, c, (src.get(c, [None])[0] or DESC.get(c, 'HS ' + c)), h[-2][idx], h[-1][idx]))
    up = sorted([r for r in rows if r[0] > 0], key=lambda r: -r[0])[:4]
    dn = sorted([r for r in rows if r[0] < 0], key=lambda r: r[0])[:4]
    if not up and not dn:
        return ''
    mx = max(abs(r[0]) for r in up + dn)
    def col(lst, cls, head):
        if not lst:
            return ''
        o = ['<div><h3 class="sub">%s</h3><ul class="mvl">' % head]
        for d, c, desc, a0, a1 in lst:
            pc = ('%+.0f%%' % ((a1 / a0 - 1) * 100)) if a0 > 0 else 'new'
            o.append('<li><div class="mvt">%s %s <span class="mono">%s.%s.%s</span></div>'
                     '<div class="mvb"><i class="%s" style="width:%.1f%%"></i></div>'
                     '<div class="mvn"><b>%s%s</b> <span>%s · %s → %s</span></div></li>'
                     % (viz.chap_icon(c[:2]), esc(viz.cut(desc, 46)), c[:4], c[4:6], c[6:8], cls, max(3.0, abs(d) / mx * 100),
                        '+' if d > 0 else '−', money(abs(d)), pc, money(a0), money(a1)))
        return ''.join(o) + '</ul></div>'
    return ('<h2 class="sec">What moved this year</h2><div class="catg">' + col(up, 'up', 'Biggest rises in %s' % word) + col(dn, 'dn', 'Biggest falls in %s' % word) +
            '</div><p class="fineprint">Change in the value of %s, FY %s against FY %s.</p>' % (word, HY[-1], HY[-2]))


def duty_cell(code):
    d = DUTY.get(code)
    if not d or d[0] in ('', 'None'):
        return '—'
    g = 'Free' if d[0] in ('0', '0.0') else (d[0] + ('%' if re.fullmatch(r'[\d.]+', d[0]) else ''))
    s = d[1]
    if s and s not in ('None', d[0]) and re.fullmatch(r'[\d.]+', s):
        g += ' <span class="tk">SAFTA %s%%</span>' % s
    return g


UNIT = {'pcs': 'piece', 'nos': 'piece', 'no': 'piece', 'kg': 'kg', 'ltr': 'litre', 'lt': 'litre', 'l': 'litre', 'mtr': 'metre', 'm': 'metre',
        'sqm': 'sq m', 'sq.m': 'sq m', 'cum': 'cu m', 'ton': 'tonne', 'mt': 'tonne', 'pair': 'pair', 'prs': 'pair', 'kwh': 'kWh', 'gm': 'gram', 'set': 'set', 'kl': 'kilolitre',
        'mtq': 'cu m', 'pr': 'pair', 'grm': 'gram', 'dzn': 'dozen', 'tne': 'tonne', 'gro': 'gross', 'car': 'carat', 'stk': 'stick', 'ftk': 'sq ft'}


def unit_price(row):
    unit, qty, val = row[1], row[2], row[3]
    if not qty or qty <= 0 or not unit or str(unit).lower() in ('', 'none'):
        return '—'
    p = val * 1000.0 / qty
    u = UNIT.get(str(unit).strip().lower(), str(unit).strip().lower())
    if p >= 1e5:
        return '%s per %s' % (money(p / 1000.0), u)
    return 'Rs %s per %s' % (('{:,.0f}'.format(p)) if p >= 100 else ('%.1f' % p), u)


built = []
for slug, name, icon, pre, exc, scope, guides_x, focus in SECTORS:
    imps = sorted(((c, r) for c, r in S['imports'].items() if member(c, pre, exc)), key=lambda x: -x[1][3])
    exps = sorted(((c, r) for c, r in S['exports'].items() if member(c, pre, exc)), key=lambda x: -x[1][3])
    imp = sum(r[3] for _, r in imps); exp = sum(r[3] for _, r in exps); rev = sum(r[4] for _, r in imps)
    if imp + exp <= 0:
        continue
    hist = [[0.0, 0.0] for _ in HY]
    for c, h in S['history']['codes'].items():
        if member(c, pre, exc):
            for i, v in enumerate(h[:len(HY)]):
                hist[i][0] += v[0]; hist[i][1] += v[1]
    if abs(hist[-1][0] - imp) > max(1.0, imp * 0.005):     # history must agree with this year's rows
        hist = []
    sup = {}
    for _, r in imps:
        for cn, v in r[5]:
            sup[cn] = sup.get(cn, 0.0) + v
    nice = lambda d: sorted((('Unspecified origin' if re.sub(r'[^a-z]', '', cn.lower()) in ('notspecified', 'others', 'unspecified') else cn, v) for cn, v in d.items()), key=lambda x: -x[1])
    sup = nice(sup)
    dst = {}
    for _, r in exps:
        for cn, v in r[4]:
            dst[cn] = dst.get(cn, 0.0) + v
    dst = nice(dst)
    built.append(dict(focus=focus, guides_x=guides_x, slug=slug, name=name, icon=icon, pre=pre, exc=exc, scope=scope, imps=imps, exps=exps, imp=imp, exp=exp,
                      rev=rev, hist=hist, sup=sup, dst=dst))

built.sort(key=lambda b: (b['focus'] != 'import', -(b['imp'] if b['focus'] == 'import' else b['exp'])))
(pub / 'sector').mkdir(exist_ok=True)
FOOT = k.foot('<b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + '. Duty rates: Customs Tariff '
              + esc(TAR.get('v', '')) + '. Values in Nepali rupees (1 arba = 1 billion; 1 kharba = 100 billion). A sector here is a fixed list '
              'of HS codes chosen by Customs Nepal, not an official classification.')
low = lambda s: s[0].lower() + s[1:]

def month_block(b, idx, word):
    chs = [p for p in b['pre'] if len(p) == 2]
    total = b['imp'] if idx == 0 else b['exp']
    if len(chs) != len(b['pre']) or b['exc'] or len(MON) != 12 or len(MONTHS) != 12 or total <= 0:
        return ''
    mv = [sum((m['ch'].get(str(int(c)), [0, 0])[idx]) for c in chs) for m in MON]
    if abs(sum(mv) - total) > total * 0.02 or max(mv) <= 0:
        return ''
    hb, _ = viz.hbars([(MONTHS[i], money(v), v) for i, v in enumerate(mv)], 'c1' if idx == 0 else 'c2', '%s of %s by month' % (word, b['name']))
    hi = max(range(12), key=lambda i: mv[i]); lo = min(range(12), key=lambda i: mv[i])
    return ('<h2 class="sec">%s</h2>' % ('When it comes in' if idx == 0 else 'When it ships') + fig('%s by month, FY %s' % (word, FY), hb) +
            '<p>%s peaked in %s (%s) and were lowest in %s (%s). Nepali months start mid-month: Shrawan is mid-July to mid-August.</p>'
            % (word, MONTHS[hi], money(mv[hi]), MONTHS[lo], money(mv[lo])))


def import_table(b, n):
    imp = b['imp']
    o = ['<div class="tblwrap"><table class="ptbl"><thead><tr><th>Product</th><th>HS code</th><th class="r">Imports</th><th class="r">Share</th>'
         '<th class="r">Average price</th><th class="r">Duty rate</th></tr></thead><tbody>']
    for c, r in b['imps'][:n]:
        al = links.alias_for(c)
        guide = ' <a class="dguide" href="%s">%s duty guide</a>' % (al[0], esc(al[1])) if al else ''
        o.append('<tr><td>%s <a href="/#hs-%s.%s.%s">%s</a>%s</td><td class="mono">%s.%s.%s</td><td class="r">%s</td><td class="r">%.1f%%</td><td class="r">%s</td><td class="r">%s</td></tr>'
                 % (viz.chap_icon(c[:2]), c[:4], c[4:6], c[6:8], esc(viz.cut(r[0], 56)), guide, c[:4], c[4:6], c[6:8], money(r[3]), r[3] / imp * 100,
                    esc(unit_price(r)), duty_cell(c) + (('<span class="tk">%.0f%% of value collected</span>' % (r[4] / r[3] * 100)) if r[3] > 0 and r[4] > 0 else '')))
    return ''.join(o) + '</tbody></table></div>'


def export_table(b, n, price):
    exp = b['exp']
    o = ['<div class="tblwrap"><table class="ptbl"><thead><tr><th>Product</th><th>HS code</th><th class="r">Exports</th><th class="r">Share</th>'
         + ('<th class="r">Average price</th>' if price else '') + '<th>Main buyers</th></tr></thead><tbody>']
    for c, r in b['exps'][:n]:
        o.append('<tr><td>%s %s</td><td class="mono">%s.%s.%s</td><td class="r">%s</td><td class="r">%.1f%%</td>%s<td>%s</td></tr>'
                 % (viz.chap_icon(c[:2]), esc(viz.cut(r[0], 56)), c[:4], c[4:6], c[6:8], money(r[3]), r[3] / exp * 100,
                    ('<td class="r">%s</td>' % esc(unit_price(r))) if price else '', ', '.join(links.partner_link(cn, esc) for cn, _ in r[4][:3])))
    return ''.join(o) + '</tbody></table></div>'


PRICE_NOTE = ('“% of value collected” is all revenue customs reports on that product (duty plus other border taxes). “Average price” is the declared value divided by the declared quantity at customs — a rough guide, since one HS line can mix very different goods.')

for b in built:
    slug, name, X = b['slug'], b['name'], b['focus'] == 'export'
    lname = low(name) if not name.startswith('LED') else name
    path = '/sector/' + slug
    imp, exp, rev = b['imp'], b['exp'], b['rev']
    p_imp = imp / TOT_IMP * 100 if TOT_IMP else 0; p_exp = exp / TOT_EXP * 100 if TOT_EXP else 0
    yoy = ((b['hist'][-1][0] / b['hist'][-2][0] - 1) * 100) if b['hist'] and b['hist'][-2][0] > 0 else None
    yoye = ((b['hist'][-1][1] / b['hist'][-2][1] - 1) * 100) if b['hist'] and b['hist'][-2][1] > 0 else None
    chg = lambda v: ('%s%.0f%% on last year' % ('+' if v >= 0 else '−', abs(v))) if v is not None else ''
    top_sup = b['sup'][:6]; top_dst = b['dst'][:6]
    if X:
        title = 'Nepal %s exports: %s in FY %s — buyers, products, trend' % (lname, money(exp), FY)
        desc = ('Nepal exported %s worth %s in FY %s. Top products, buyer countries, average export price and %d-year trend, from official customs data.'
                % (lname, money(exp), FY, len(HY)))
        qa = [('How much %s does Nepal export?' % lname,
               'Nepal exported %s worth %s in FY %s, %.1f%% of the country’s total exports, according to the Department of Customs.' % (lname, money(exp), FY, p_exp))]
        if top_dst:
            qa.append(('Which countries buy Nepal’s %s?' % lname, 'The largest buyers in FY %s were %s.' % (FY, ', '.join('%s (%s)' % (cn, money(v)) for cn, v in top_dst[:4]))))
        if b['exps']:
            qa.append(('What are Nepal’s biggest %s exports?' % lname, 'By value: %s.' % '; '.join('%s (%s)' % (viz.cut(r[0], 50), money(r[3])) for _, r in b['exps'][:4])))
        if yoye is not None:
            qa.append(('Are Nepal’s %s exports growing?' % lname, 'Exports were %s in FY %s against %s the year before, a change of %+.0f%%.'
                       % (money(exp), FY, money(b['hist'][-2][1]), yoye)))
        if imp > 0:
            qa.append(('Does Nepal also import %s?' % lname, 'Yes. Nepal imported goods under the same HS codes worth %s in FY %s%s.'
                       % (money(imp), FY, (', mainly from ' + ', '.join(cn for cn, _ in top_sup[:3])) if top_sup else '')))
    else:
        title = 'Nepal %s market: imports %s, FY %s' % (lname, money(imp), FY)
        desc = ('Nepal’s %s trade in FY %s: imports %s, exports %s. Top products, main supplier countries, customs duty and %d-year trend, '
                'from official customs data.' % (lname, FY, money(imp), money(exp), len(HY)))
        qa = [('How big is Nepal’s %s import market?' % lname,
               'Nepal imported %s worth %s in FY %s, %.1f%% of the country’s total imports, according to the Department of Customs.' % (lname, money(imp), FY, p_imp))]
        if exp > 0:
            qa.append(('How much %s does Nepal export?' % lname, 'Nepal exported %s worth %s in FY %s, %.1f%% of total exports.' % (lname, money(exp), FY, p_exp)))
        if top_sup:
            qa.append(('Which countries supply Nepal’s %s?' % lname, 'The largest suppliers in FY %s were %s.' % (FY, ', '.join('%s (%s)' % (cn, money(v)) for cn, v in top_sup[:4]))))
        if b['imps']:
            qa.append(('What are the biggest %s imports?' % lname, 'By value: %s.' % '; '.join('%s (%s)' % (viz.cut(r[0], 50), money(r[3])) for _, r in b['imps'][:4])))
        if rev > 0 and imp > 0:
            qa.append(('How much does the government collect on %s imports?' % lname,
                       'Customs collected %s on these imports in FY %s, about Rs %.1f for every Rs 100 of goods (customs duty plus other taxes charged at the border).'
                       % (money(rev), FY, rev / imp * 100)))
    bc = [('Home', '/'), ('Sectors', '/sectors'), (name, '')]
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}]
    out = [k.page_head(title, desc, path, bc, extra_ld=ld), k.crumb_html(bc)]
    rank_list = [x for x in built if x['focus'] == b['focus']]
    growth = None
    gi = 1 if X else 0
    if b['hist']:
        h0 = next((h for h in b['hist'] if h[gi] > 0), None)
        if h0 and h0 is not b['hist'][-1]:
            growth = (HY[b['hist'].index(h0)], h0[gi], b['hist'][-1][gi])
    keytxt = ('Nepal %s, FY %s (Department of Customs): imports %s, exports %s. Source: customsnepal.com%s' % (lname, FY, money(imp), money(exp), path))
    out.append('</div><section class="cphero"><div class="wrap"><div>'
               '<div class="cpkick">%s #%d of %d · FY %s</div>'
               '<h1>%s %s</h1>'
               '<p class="cplede">%s Covers %s. Official Department of Customs figures.</p>'
               '<div class="cpstats">%s</div>'
               '<button type="button" class="keycopy" data-act="text" data-text="%s">Copy key figures as text</button>'
               '</div><div>%s</div></div></section><div class="wrap">'
               % ('Export industry' if X else 'Import sector', rank_list.index(b) + 1, len(rank_list), FY, b['icon'],
                  esc(name + (': what Nepal sells abroad' if X else ' in Nepal')),
                  ('Who buys Nepal’s %s, what sells and at what price.' % esc(lname)) if X else ('What Nepal buys in %s, who supplies it and what it costs to bring in.' % esc(lname)),
                  esc(b['scope']),
                  ('<div class="cpstat e"><span>Nepal exports</span><b data-count>%s</b></div><div class="cpstat i"><span>Imports, same goods</span><b data-count>%s</b></div>'
                   '<div class="cpstat %s"><span>On last year</span><b>%s</b></div>' % (money(exp), money(imp), 'pos' if (yoye or 0) >= 0 else 'neg', ('%+.0f%%' % yoye) if yoye is not None else '—'))
                  if X else
                  ('<div class="cpstat i"><span>Nepal imports</span><b data-count>%s</b></div><div class="cpstat e"><span>Nepal exports</span><b data-count>%s</b></div>'
                   '<div class="cpstat pos"><span>Collected at customs</span><b data-count>%s</b></div>' % (money(imp), money(exp), money(rev))),
                  esc(keytxt), story.flow('🌍', 'The world', imp, exp, money(imp), money(exp))))
    cards = []
    if X:
        if top_dst and exp:
            cards.append(('🎯', 'Biggest buyer', '%s %s' % (flag_of(top_dst[0][0]), top_dst[0][0]), '%.0f%% of these exports%s' % (top_dst[0][1] / exp * 100,
                          '; top three %.0f%%' % (sum(v for _, v in top_dst[:3]) / exp * 100) if len(top_dst) >= 3 else '')))
        if b['exps']:
            cards.append(('⭐', 'Star product', viz.cut(b['exps'][0][1][0], 30), '%.0f%% of the industry’s exports' % (b['exps'][0][1][3] / exp * 100)))
        if growth:
            cards.append(('📈', 'Since FY %s' % growth[0], ('%.1f×' % (growth[2] / growth[1])) if growth[2] >= growth[1] * 2 else ('%+.0f%%' % ((growth[2] / growth[1] - 1) * 100)),
                          '%s then, %s now' % (money(growth[1]), money(growth[2]))))
        if imp > 0:
            cards.append(('🔁', 'Imported under the same codes', 'Rs %.0f per Rs 100' % (imp / exp * 100) if exp else '—', 'imports for every Rs 100 exported — inputs and competing goods'))
    else:
        if top_sup and imp:
            cards.append(('🎯', 'Biggest supplier', '%s %s' % (flag_of(top_sup[0][0]), top_sup[0][0]), '%.0f%% of the sector%s' % (top_sup[0][1] / imp * 100,
                          '; top three %.0f%%' % (sum(v for _, v in top_sup[:3]) / imp * 100) if len(top_sup) >= 3 else '')))
        if b['imps']:
            cards.append(('⭐', 'Biggest product', viz.cut(b['imps'][0][1][0], 30), '%.0f%% of the sector’s imports' % (b['imps'][0][1][3] / imp * 100)))
        if growth:
            cards.append(('📈', 'Since FY %s' % growth[0], ('%.1f×' % (growth[2] / growth[1])) if growth[2] >= growth[1] * 2 else ('%+.0f%%' % ((growth[2] / growth[1] - 1) * 100)),
                          '%s then, %s now' % (money(growth[1]), money(growth[2]))))
        if imp and rev:
            tk = rev / imp * 100
            cards.append(('🏛️', 'Tax at the border', 'Rs %.0f per Rs 100' % tk, '%s the Rs %.0f average for all imports' % ('above' if tk > NAT_TAKE * 1.05 else ('below' if tk < NAT_TAKE * 0.95 else 'close to'), NAT_TAKE)))
    out.append('<div class="cpfacts">' + ''.join('<div class="cpfact"><div class="ic">%s</div><span>%s</span><b>%s</b><small>%s</small></div>'
                                                 % (ic, esc(l), esc(v), esc(s)) for ic, l, v, s in cards) + '</div>')
    if b['hist']:
        out.append('<h2 class="sec">%d years of trade</h2>' % len(HY))
        tf, _ = story.trend(HY, b['hist'], money, name, heads=('Imports: %s', 'Exports: %s'))
        out.append(fig('%s — imports and exports, FY %s to %s' % (name, HY[0], HY[-1]), tf, viz.LEGEND_IE))
        i = 1 if X else 0
        h0 = next((h for h in b['hist'] if h[i] > 0), None)
        if h0 and h0 is not b['hist'][-1]:
            j = b['hist'].index(h0); tot0 = S['history']['totals'][j][i]; tot1 = TOT_EXP if X else TOT_IMP
            out.append('<p>%s moved from %s in FY %s to %s in FY %s. As a share of all Nepal’s %s, that is %.1f%% then and %.1f%% now.</p>'
                       % ('Exports' if X else 'Imports', money(h0[i]), HY[j], money(exp if X else imp), FY, 'exports' if X else 'imports',
                          (h0[i] / tot0 * 100) if tot0 else 0, ((exp if X else imp) / tot1 * 100) if tot1 else 0))
    excise_note = ' Vehicles, alcohol and tobacco also pay excise duty, which is not in the duty-rate column.' if any(c[:2] in EXCISE_CH for c, _ in b['imps'][:10]) else ''
    sec_imp = sec_exp = sec_sup = sec_dst = ''
    if b['imps'] and imp > 0:
        n = 5 if X else 10
        cov = sum(r[3] for _, r in b['imps'][:n]) / imp * 100
        sec_imp = ('<h2 class="sec">%s</h2>' % ('What Nepal imports under the same codes' if X else 'What Nepal buys') +
                   ('' if X else product_map(b['imps'], imp, 'Imports of %s by product' % lname, 3)) + import_table(b, n) +
                   '<p class="fineprint">These %d make up %.0f%% of the imports; %d more product lines make up the rest. %s%s</p>'
                   % (min(n, len(b['imps'])), cov, max(0, len(b['imps']) - n), PRICE_NOTE, excise_note))
    if b['exps'] and exp > 0:
        n = 10 if X else 5
        sec_exp = ('<h2 class="sec">%s</h2>' % ('What Nepal sells' if X else 'Top exported products') +
                   (product_map(b['exps'], exp, 'Exports of %s by product' % lname, 3) if X else '') + export_table(b, n, X))
        if X:
            cov = sum(r[3] for _, r in b['exps'][:n]) / exp * 100
            sec_exp += '<p class="fineprint">These %d make up %.0f%% of the sector’s exports. %s</p>' % (min(n, len(b['exps'])), cov, PRICE_NOTE)
    if top_sup and imp > 0 and not X:
        sec_sup = ('<h2 class="sec">Who supplies it</h2>' + country_flow(b, b['sup'], imp, 'comes from…', 'Where Nepal’s %s come from' % lname) +
                   country_map(b['sup'], 'Supplier map — darker means more') +
                   '<p>%s is the largest supplier with about %.0f%% of the sector’s imports%s. Open a country for everything Nepal trades with it: %s.</p>'
                   % (esc(top_sup[0][0]), top_sup[0][1] / imp * 100,
                      ('; the top three together supply about %.0f%%' % (sum(v for _, v in top_sup[:3]) / imp * 100)) if len(top_sup) >= 3 else '',
                      ' · '.join(links.partner_link(cn, esc) for cn, _ in top_sup)) +
                   '<p class="fineprint">Country figures add up each product’s six largest sources, so small flows from other countries are not counted and the true shares can be slightly higher.</p>')
    if top_dst and exp > 0 and (X or exp > imp * 0.05):
        sec_dst = ('<h2 class="sec">%s</h2>' % ('Who buys it' if X else 'Where Nepal sells it') +
                   country_flow(b, b['dst'], exp, 'goes to…', 'Where Nepal’s %s go' % lname) + (country_map(b['dst'], 'Buyer map — darker means more') if X else ''))
        if X:
            sec_dst += ('<p>%s takes about %.0f%% of these exports%s. Open a country for everything Nepal trades with it: %s.</p>'
                        % (esc(top_dst[0][0]), top_dst[0][1] / exp * 100,
                           ' — a heavy dependence on one market' if top_dst[0][1] / exp > 0.7 else '',
                           ' · '.join(links.partner_link(cn, esc) for cn, _ in top_dst)) +
                        '<p class="fineprint">Country figures add up each product’s largest recorded buyers, so small flows to other countries are not counted.</p>')
    if X:
        out += [sec_dst, sec_exp, movers(b, 1, 'exports'), month_block(b, 1, 'Exports'), sec_imp]
        gl = [g for g in b['guides_x'] if (pub / 'export' / (g + '.html')).exists()]
        out.append('<h2 class="sec">Selling abroad</h2><p>Exports from Nepal need an EXIM code, a commercial invoice and packing list, a certificate of origin and, '
                   'for food and plant products, the relevant quality or plant-health certificate. Goods going to SAARC countries can claim the buyer’s lower '
                   '<a href="/safta">SAFTA rate</a> with a SAFTA certificate of origin.</p>')
        out.append('<p class="xlink"><b>Guides:</b> <a href="/export">how to export from Nepal</a>'
                   + ''.join(' · <a href="/export/%s">exporting %s</a>' % (g, esc(g.replace('-', ' '))) for g in gl)
                   + ' · <a href="/exports">export data explorer</a></p>')
    else:
        out += [sec_sup, sec_imp, movers(b, 0, 'imports'), month_block(b, 0, 'Imports'), sec_exp, sec_dst]
        rates = sorted({0.0 if DUTY[c][0].lower() == 'free' else float(DUTY[c][0]) for c, _ in b['imps'][:40] if c in DUTY and (DUTY[c][0].lower() == 'free' or re.fullmatch(r'[\d.]+', DUTY[c][0]))})
        guides = list(dict.fromkeys(a for a in (links.alias_for(c) for c, _ in b['imps'][:60]) if a))[:10]
        out.append('<h2 class="sec">Duty and landed cost</h2>')
        if rates:
            out.append('<p>General customs duty on the main products in this sector runs from %s to %g%%. VAT of 13%% applies on top unless the product is exempt, '
                       'and goods from SAARC countries can qualify for the lower <a href="/safta">SAFTA rate</a> with a certificate of origin.%s</p>'
                       % ('free' if rates[0] == 0 else '%g%%' % rates[0], rates[-1],
                          ' Excise duty also applies to vehicles, alcohol and tobacco and is often the largest part of the bill.' if any(p[:2] in EXCISE_CH for p in b['pre']) else ''))
        out.append('<p class="xlink"><b>Work out your own cost:</b> <a href="/calculator">landed-cost calculator</a>'
                   + (' · ' + ' · '.join('<a href="%s">%s duty</a>' % (h, esc(n)) for h, n in guides) if guides else '')
                   + ' · ' + ' · '.join('<a href="/tariff/%s">Chapter %d tariff</a>' % (c, int(c)) for c in list(dict.fromkeys(p[:2] for p in b['pre']))[:5]) + '</p>')
    if slug == 'led-av-lighting':
        out.append('<p class="fineprint"><b>Disclosure:</b> Customs Nepal is operated by Audio Visual Solutions Pvt. Ltd. (Evolve Tech), which imports and installs '
                   'LED displays and audio-visual systems in Nepal. The figures on this page are the Department of Customs’ and are presented the same way as every other sector.</p>')
    out.append('<h2 class="sec">Quick answers</h2><dl class="qa">' + ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(q), esc(a)) for q, a in qa) + '</dl>')
    subj = urllib.parse.quote('Full sector report: %s%s (FY %s)' % (name, ' exports' if X else '', FY))
    out.append('<div class="note"><b>Need the full picture?</b> This page shows the headline figures. A full report for this sector — every product line, '
               '%s over %d years, unit-price trends, and a cut for your own HS codes — is prepared on request for banks, consultancies, '
               'chambers and trading houses. <a href="mailto:%s?subject=%s"><b>Request the full %s report</b></a>.</div>'
               % ('buyer shifts' if X else 'supplier shifts', len(HY), CONTACT, subj, esc(lname)))
    same = [x for x in built if x['slug'] != slug and x['focus'] == b['focus']]; other = [x for x in built if x['focus'] != b['focus']]
    out.append('<h2 class="sec">Other %s sectors</h2><p>' % ('export' if X else 'import') + ' · '.join('<a href="/sector/%s">%s %s</a>' % (x['slug'], x['icon'], esc(x['name'])) for x in same) + '</p>')
    out.append('<p class="xlink"><b>%s:</b> ' % ('Import sectors' if X else 'Export sectors') + ' · '.join('<a href="/sector/%s">%s</a>' % (x['slug'], esc(x['name'])) for x in other) + '</p>')
    out.append('</div>' + FOOT)
    (pub / 'sector' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')

# ---------------------------------------------------------------- hub
title = 'Nepal imports and exports by sector, FY %s' % FY
desc = 'Market size, top products and trading countries for %d sectors of Nepal’s foreign trade in FY %s — import markets and export industries — from official customs data.' % (len(built), FY)
bc = [('Home', '/'), ('Sectors', '')]
nI = sum(1 for b in built if b['focus'] == 'import'); nE = len(built) - nI
out = [k.page_head(title, desc, '/sectors', bc), k.crumb_html(bc),
       '</div><section class="cphero"><div class="wrap"><div>'
       '<div class="cpkick">%d import sectors · %d export industries · FY %s</div>'
       '<h1>Nepal’s trade, industry by industry</h1>'
       '<p class="cplede">What Nepal buys and what it sells, grouped the way businesses think about it: each sector’s size, biggest products, '
       'trading countries, prices and trend. Official Department of Customs figures.</p>'
       '<div class="cpstats"><div class="cpstat i"><span>Total imports</span><b data-count>%s</b></div>'
       '<div class="cpstat e"><span>Total exports</span><b data-count>%s</b></div>'
       '<div class="cpstat neg"><span>Trade deficit</span><b data-count>%s</b></div></div>'
       '</div><div>%s</div></div></section><div class="wrap">'
       % (nI, nE, FY, money(TOT_IMP), money(TOT_EXP), money(TOT_IMP - TOT_EXP), story.flow('🌍', 'The world', TOT_IMP, TOT_EXP, money(TOT_IMP), money(TOT_EXP)))]
def cards(rows, key):
    return '<div class="cpcards">' + ''.join(
        '<a class="cpcard" href="/sector/%s"><div class="fl">%s</div><b>%s</b><small>%s · %s</small></a>'
        % (b['slug'], b['icon'], esc(b['name']), money(b[key]),
           ('from ' + b['sup'][0][0]) if key == 'imp' and b['sup'] else (('to ' + b['dst'][0][0]) if key == 'exp' and b['dst'] else '')) for b in rows) + '</div>'
I = [b for b in built if b['focus'] == 'import']; E = [b for b in built if b['focus'] == 'export']
out.append('<h2 class="sec">What Nepal buys: %d import sectors</h2>' % len(I))
out.append(cards(I, 'imp'))
hb, _ = viz.hbars([(viz.cut(b['name'], 36), money(b['imp']), b['imp']) for b in I], 'c1', 'Import sectors by value')
out.append(fig('Imports by sector, FY %s' % FY, hb))
out.append('<div class="tblwrap"><table class="ptbl"><thead><tr><th>Sector</th><th class="r">Imports</th><th class="r">Share of imports</th><th class="r">Exports</th>'
           '<th>Largest supplier</th></tr></thead><tbody>' + ''.join(
    '<tr><td>%s <a href="/sector/%s">%s</a></td><td class="r">%s</td><td class="r">%.1f%%</td><td class="r">%s</td><td>%s</td></tr>'
    % (b['icon'], b['slug'], esc(b['name']), money(b['imp']), b['imp'] / TOT_IMP * 100, money(b['exp']),
       links.partner_link(b['sup'][0][0], esc) if b['sup'] else '—') for b in I) + '</tbody></table></div>')
out.append('<h2 class="sec">What Nepal sells: %d export industries</h2>' % len(E))
out.append(cards(E, 'exp'))
hb, _ = viz.hbars([(viz.cut(b['name'], 36), money(b['exp']), b['exp']) for b in E], 'c2', 'Export industries by value')
out.append(fig('Exports by industry, FY %s' % FY, hb))
out.append('<div class="tblwrap"><table class="ptbl"><thead><tr><th>Industry</th><th class="r">Exports</th><th class="r">Share of exports</th>'
           '<th>Largest buyer</th></tr></thead><tbody>' + ''.join(
    '<tr><td>%s <a href="/sector/%s">%s</a></td><td class="r">%s</td><td class="r">%.1f%%</td><td>%s</td></tr>'
    % (b['icon'], b['slug'], esc(b['name']), money(b['exp']), b['exp'] / TOT_EXP * 100,
       links.partner_link(b['dst'][0][0], esc) if b['dst'] else '—') for b in E) + '</tbody></table></div>')
out.append('<p class="fineprint">Sectors are fixed lists of HS codes chosen by Customs Nepal; a few products could sit in more than one, so the rows do not add up to Nepal’s total.</p>')
out.append('<p class="xlink"><b>See also:</b> <a href="/trade-partners">trade by country</a> · <a href="/customs-offices">by customs office</a> · '
           '<a href="/trade/categories">all 96 HS chapters</a> · <a href="/import-duty">import duty by product</a></p>')
out.append('</div>' + FOOT)
(pub / 'sectors.html').write_text(''.join(out), encoding='utf-8')
n = k.add_to_sitemap(['/sectors'] + ['/sector/' + b['slug'] for b in built])
print('sector_pages: %d sector pages + hub; +%d sitemap URLs' % (len(built), n))
for b in built:
    print('  %-24s imp %-18s exp %-16s hist %s' % (b['slug'], money(b['imp']), money(b['exp']), 'ok' if b['hist'] else 'MISMATCH'))
