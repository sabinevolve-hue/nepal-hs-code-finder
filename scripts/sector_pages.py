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

# slug, name, icon, HS prefixes (digits), prefixes to leave out, one-line scope
SECTORS = [
    ('vehicles', 'Vehicles, motorcycles and EVs', '🚗', ['87'], [], 'cars, electric vehicles, motorcycles, buses, trucks, tractors and parts (HS chapter 87)'),
    ('fuel-energy', 'Fuel and energy', '⛽', ['27', '854142', '854143', '8507'], [], 'petrol, diesel, LPG, coal, electricity, solar panels and batteries'),
    ('electronics', 'Electronics and appliances', '📱', ['85', '8471', '8415', '8418', '8450'], ['854142', '854143', '8507'], 'mobile phones, computers, TVs, home appliances and electrical equipment'),
    ('construction-materials', 'Iron, steel and construction materials', '🏗️', ['72', '73', '2523', '69', '6802', '6810', '7003', '7004', '7005', '7007', '7008', '7610'], [], 'iron and steel, cement and clinker, tiles and ceramics, glass and structures'),
    ('pharma-medical', 'Pharmaceuticals and medical equipment', '💊', ['30', '9018', '9019', '9020', '9021', '9022'], [], 'medicines, vaccines and medical, surgical and diagnostic equipment'),
    ('food-edible-oils', 'Food and edible oils', '🌾', ['02', '03', '04', '07', '08', '10', '11', '12', '15', '16', '17', '18', '19', '20', '21'], ['1211'], 'cereals, edible oils, oilseeds, fruit, vegetables, dairy, sugar and prepared foods'),
    ('machinery', 'Machinery and industrial equipment', '⚙️', ['84'], ['8471', '8415', '8418', '8450'], 'industrial, agricultural and construction machinery, engines, pumps and parts'),
    ('textiles-garments', 'Textiles, garments and carpets', '🧵', [str(c) for c in range(50, 64)], [], 'yarn, fabric, readymade garments, carpets, felt and other textile products (HS chapters 50–63)'),
    ('gold-jewellery', 'Gold, silver and jewellery', '🥇', ['71'], [], 'gold, silver, precious stones and jewellery (HS chapter 71)'),
    ('tea-coffee-spices', 'Tea, coffee, spices and herbs', '🍵', ['09', '1211'], [], 'tea, coffee, cardamom, ginger and other spices, and medicinal herbs'),
    ('led-av-lighting', 'LED displays, audio-visual and lighting', '📺', ['8528', '8531', '8524', '8518', '8519', '8521', '8525', '853951', '853952', '9405'], [], 'monitors, projectors and TVs, LED display panels and modules, audio equipment, cameras, LED lamps and light fittings'),
]


def member(code, pre, exc):
    return any(code.startswith(p) for p in pre) and not any(code.startswith(x) for x in exc)


def fig(title, svg, legend=''):
    return ('<figure class="vzfig"><figcaption><b>%s</b>%s</figcaption><div class="vzwrap">%s</div>'
            '<p class="fineprint" style="margin:.4em 0 0">Source: Department of Customs, Nepal — Foreign Trade Statistics.</p></figure>'
            % (esc(title), legend, svg))


def duty_cell(code):
    d = DUTY.get(code)
    if not d or d[0] in ('', 'None'):
        return '—'
    g = 'Free' if d[0] in ('0', '0.0') else (d[0] + ('%' if re.fullmatch(r'[\d.]+', d[0]) else ''))
    s = d[1]
    if s and s not in ('None', d[0]) and re.fullmatch(r'[\d.]+', s):
        g += ' <span class="tk">SAFTA %s%%</span>' % s
    return g


def unit_price(row):
    unit, qty, val = row[1], row[2], row[3]
    if not qty or qty <= 0 or not unit or str(unit).lower() in ('', 'none'):
        return '—'
    p = val * 1000.0 / qty
    if p >= 1e5:
        return '%s per %s' % (money(p / 1000.0), str(unit).lower())
    return 'Rs %s per %s' % (('%.0f' % p) if p >= 100 else ('%.1f' % p), str(unit).lower())


built = []
for slug, name, icon, pre, exc, scope in SECTORS:
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
    sup = sorted(sup.items(), key=lambda x: -x[1])
    dst = {}
    for _, r in exps:
        for cn, v in r[4]:
            dst[cn] = dst.get(cn, 0.0) + v
    dst = sorted(dst.items(), key=lambda x: -x[1])
    built.append(dict(slug=slug, name=name, icon=icon, pre=pre, exc=exc, scope=scope, imps=imps, exps=exps, imp=imp, exp=exp,
                      rev=rev, hist=hist, sup=sup, dst=dst))

built.sort(key=lambda b: -(b['imp'] + b['exp']))
(pub / 'sector').mkdir(exist_ok=True)
FOOT = k.foot('<b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + '. Duty rates: Customs Tariff '
              + esc(TAR.get('v', '')) + '. Values in Nepali rupees (1 arba = 1 billion; 1 kharba = 100 billion). A sector here is a fixed list '
              'of HS codes chosen by Customs Nepal, not an official classification.')
low = lambda s: s[0].lower() + s[1:]

for b in built:
    slug, name = b['slug'], b['name']
    lname = low(name) if not name.startswith('LED') else name
    path = '/sector/' + slug
    imp, exp, rev = b['imp'], b['exp'], b['rev']
    export_led = exp > imp
    p_imp = imp / TOT_IMP * 100 if TOT_IMP else 0; p_exp = exp / TOT_EXP * 100 if TOT_EXP else 0
    yoy = ((b['hist'][-1][0] / b['hist'][-2][0] - 1) * 100) if b['hist'] and b['hist'][-2][0] > 0 else None
    yoye = ((b['hist'][-1][1] / b['hist'][-2][1] - 1) * 100) if b['hist'] and b['hist'][-2][1] > 0 else None
    title = 'Nepal %s market: imports %s, FY %s' % (lname, money(imp), FY) if not export_led else 'Nepal %s: exports %s, FY %s' % (lname, money(exp), FY)
    desc = ('Nepal’s %s trade in FY %s: imports %s, exports %s. Top products, main supplier countries, customs duty and %d-year trend, '
            'from official customs data.' % (lname, FY, money(imp), money(exp), len(HY)))
    bc = [('Home', '/'), ('Sectors', '/sectors'), (name, '')]
    top_sup = [(cn, v) for cn, v in b['sup'][:6]]
    qa = [('How big is Nepal’s %s import market?' % lname,
           'Nepal imported %s worth %s in FY %s, %.1f%% of the country’s total imports, according to the Department of Customs.' % (lname, money(imp), FY, p_imp))]
    if exp > 0:
        qa.append(('How much %s does Nepal export?' % lname, 'Nepal exported %s worth %s in FY %s, %.1f%% of total exports.' % (lname, money(exp), FY, p_exp)))
    if top_sup:
        qa.append(('Which countries supply Nepal’s %s?' % lname, 'The largest suppliers in FY %s were %s.'
                   % (FY, ', '.join('%s (%s)' % (cn, money(v)) for cn, v in top_sup[:4]))))
    if b['imps']:
        qa.append(('What are the biggest %s imports?' % lname, 'By value: %s.' % '; '.join('%s (%s)' % (viz.cut(r[0], 50), money(r[3])) for _, r in b['imps'][:4])))
    if rev > 0 and imp > 0:
        qa.append(('How much does the government collect on %s imports?' % lname,
                   'Customs collected %s on these imports in FY %s, about Rs %.1f for every Rs 100 of goods (customs duty plus other taxes charged at the border).'
                   % (money(rev), FY, rev / imp * 100)))
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}]
    out = [k.page_head(title, desc, path, bc, extra_ld=ld), k.crumb_html(bc)]
    out.append('<h1>%s %s in Nepal: the market in FY %s</h1>' % (b['icon'], esc(name), FY))
    out.append('<p class="lede">What Nepal buys and sells in %s, who supplies it and what it costs to bring in. Covers %s.</p>' % (esc(lname), esc(b['scope'])))
    chg = lambda v: ('%s%.0f%% on last year' % ('+' if v >= 0 else '−', abs(v))) if v is not None else ''
    out.append('<div class="cpfacts">'
               '<div class="cpfact"><div class="ic">📥</div><span>Imports</span><b>%s</b><small>%.1f%% of Nepal’s imports%s</small></div>'
               '<div class="cpfact"><div class="ic">📤</div><span>Exports</span><b>%s</b><small>%.1f%% of Nepal’s exports%s</small></div>'
               '<div class="cpfact"><div class="ic">🏛️</div><span>Collected at customs</span><b>%s</b><small>%s</small></div>'
               '<div class="cpfact"><div class="ic">🧾</div><span>Products traded</span><b>%d imported</b><small>%d exported (8-digit HS lines)</small></div></div>'
               % (money(imp), p_imp, (' · ' + chg(yoy)) if yoy is not None else '', money(exp), p_exp, (' · ' + chg(yoye)) if yoye is not None else '',
                  money(rev), ('Rs %.1f per Rs 100 of goods' % (rev / imp * 100)) if imp else '', len(b['imps']), len(b['exps'])))
    if b['hist']:
        out.append('<h2 class="sec">%d years of trade</h2>' % len(HY))
        tf, _ = story.trend(HY, b['hist'], money, name, heads=('Imports: %s', 'Exports: %s'))
        out.append(fig('%s — imports and exports, FY %s to %s' % (name, HY[0], HY[-1]), tf, viz.LEGEND_IE))
        h0 = next((h for h in b['hist'] if h[0] > 0), None)
        if h0 and h0 is not b['hist'][-1]:
            out.append('<p>Imports moved from %s in FY %s to %s in FY %s.</p>' % (money(h0[0]), HY[b['hist'].index(h0)], money(imp), FY))
    # products
    if b['imps']:
        out.append('<h2 class="sec">Top 10 imported products</h2><div class="tblwrap"><table class="ptbl"><thead><tr><th>Product</th><th>HS code</th>'
                   '<th class="r">Imports</th><th class="r">Share</th><th class="r">Average price</th><th class="r">Duty rate</th></tr></thead><tbody>')
        for c, r in b['imps'][:10]:
            al = links.alias_for(c)
            guide = ' <a class="dguide" href="%s">%s duty guide</a>' % (al[0], esc(al[1])) if al else ''
            pp = '/import-duty/'
            out.append('<tr><td>%s <a href="/#hs-%s.%s.%s">%s</a>%s</td><td class="mono">%s.%s.%s</td><td class="r">%s</td><td class="r">%.1f%%</td><td class="r">%s</td><td class="r">%s</td></tr>'
                       % (viz.chap_icon(c[:2]), c[:4], c[4:6], c[6:8], esc(viz.cut(r[0], 56)), guide, c[:4], c[4:6], c[6:8], money(r[3]), r[3] / imp * 100,
                          esc(unit_price(r)), duty_cell(c)))
        out.append('</tbody></table></div>')
        cov = sum(r[3] for _, r in b['imps'][:10]) / imp * 100
        out.append('<p class="fineprint">These ten make up %.0f%% of the sector’s imports; %d more product lines make up the rest. “Average price” is '
                   'import value divided by quantity as declared at customs, before duty and tax — a rough guide, since one HS line can mix very different goods.%s</p>'
                   % (cov, max(0, len(b['imps']) - 10),
                      ' Vehicles, alcohol and tobacco also pay excise duty, which is not in the duty-rate column.' if any(c[:2] in EXCISE_CH for c, _ in b['imps'][:10]) else ''))
    if b['exps'] and exp > 0:
        out.append('<h2 class="sec">Top exported products</h2><div class="tblwrap"><table class="ptbl"><thead><tr><th>Product</th><th>HS code</th>'
                   '<th class="r">Exports</th><th class="r">Share</th><th>Main buyers</th></tr></thead><tbody>')
        for c, r in b['exps'][:(10 if export_led else 5)]:
            out.append('<tr><td>%s %s</td><td class="mono">%s.%s.%s</td><td class="r">%s</td><td class="r">%.1f%%</td><td>%s</td></tr>'
                       % (viz.chap_icon(c[:2]), esc(viz.cut(r[0], 56)), c[:4], c[4:6], c[6:8], money(r[3]), r[3] / exp * 100,
                          ', '.join(links.partner_link(cn, esc) for cn, _ in r[4][:3])))
        out.append('</tbody></table></div>')
    # suppliers
    if top_sup:
        out.append('<h2 class="sec">Who supplies it</h2>')
        hb, _ = viz.hbars([('%s (%.0f%%)' % (cn, v / imp * 100), money(v), v) for cn, v in top_sup], 'c1', 'Main supplier countries for %s' % name)
        out.append(fig('Main supplier countries, FY %s' % FY, hb))
        lead = top_sup[0]
        out.append('<p>%s is the largest supplier with about %.0f%% of the sector’s imports%s. Open a country for everything Nepal trades with it: %s.</p>'
                   % (esc(lead[0]), lead[1] / imp * 100,
                      ('; the top three together supply about %.0f%%' % (sum(v for _, v in top_sup[:3]) / imp * 100)) if len(top_sup) >= 3 else '',
                      ' · '.join(links.partner_link(cn, esc) for cn, _ in top_sup)))
        out.append('<p class="fineprint">Country figures add up each product’s six largest sources, so small flows from other countries are not counted and the true shares can be slightly higher.</p>')
    if b['dst'] and exp > 0 and (export_led or exp > imp * 0.05):
        hb, _ = viz.hbars([('%s (%.0f%%)' % (cn, v / exp * 100), money(v), v) for cn, v in b['dst'][:6]], 'c2', 'Main export destinations for %s' % name)
        out.append('<h2 class="sec">Where Nepal sells it</h2>' + fig('Main export destinations, FY %s' % FY, hb))
    # seasonality (only when the sector is whole chapters and the year has all 12 months)
    chs = [p for p in b['pre'] if len(p) == 2]
    if len(chs) == len(b['pre']) and not b['exc'] and len(MON) == 12 and len(MONTHS) == 12:
        mv = [sum((m['ch'].get(str(int(c)), [0, 0])[0]) for c in chs) for m in MON]
        if abs(sum(mv) - imp) <= imp * 0.02 and max(mv) > 0:
            hb, _ = viz.hbars([(MONTHS[i], money(v), v) for i, v in enumerate(mv)], 'c1', 'Imports of %s by month' % name)
            out.append('<h2 class="sec">When it comes in</h2>' + fig('Imports by month, FY %s' % FY, hb))
            hi = max(range(12), key=lambda i: mv[i]); lo = min(range(12), key=lambda i: mv[i])
            out.append('<p>Imports peaked in %s (%s) and were lowest in %s (%s). Nepali months start mid-month: Shrawan is mid-July to mid-August.</p>'
                       % (MONTHS[hi], money(mv[hi]), MONTHS[lo], money(mv[lo])))
    # duty
    rates = sorted({float(DUTY[c][0]) for c, _ in b['imps'][:40] if c in DUTY and re.fullmatch(r'[\d.]+', DUTY[c][0])})
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
    subj = urllib.parse.quote('Full sector report: %s (FY %s)' % (name, FY))
    out.append('<div class="note"><b>Need the full picture?</b> This page shows the headline figures. A full report for this sector — every product line, '
               'supplier shifts over %d years, unit-price trends, and a cut for your own HS codes — is prepared on request for banks, consultancies, '
               'chambers and trading houses. <a href="mailto:%s?subject=%s"><b>Request the full %s report</b></a>.</div>' % (len(HY), CONTACT, subj, esc(lname)))
    out.append('<h2 class="sec">Other sectors</h2><p>' + ' · '.join('<a href="/sector/%s">%s %s</a>' % (x['slug'], x['icon'], esc(x['name'])) for x in built if x['slug'] != slug) + '</p>')
    out.append('</div>' + FOOT)
    (pub / 'sector' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')

# ---------------------------------------------------------------- hub
title = 'Nepal trade by sector, FY %s — vehicles, fuel, electronics, steel, pharma and more' % FY
desc = 'Market size, top products, supplier countries and customs duty for %d sectors of Nepal’s foreign trade in FY %s, from official customs data.' % (len(built), FY)
bc = [('Home', '/'), ('Sectors', '')]
out = [k.page_head(title, desc, '/sectors', bc), k.crumb_html(bc),
       '<h1>Nepal’s trade by sector</h1>',
       '<p class="lede">%d industries, each with its market size, biggest products, supplier countries and duty. Figures for FY %s from the Department of Customs.</p>' % (len(built), FY)]
gb, _ = viz.grouped([(viz.cut(b['name'], 30), b['imp'], b['exp']) for b in built], 'Sectors by imports and exports', money)
out.append(fig('Imports and exports by sector, FY %s' % FY, gb, viz.LEGEND_IE))
out.append('<div class="tblwrap"><table class="ptbl"><thead><tr><th>Sector</th><th class="r">Imports</th><th class="r">Share of imports</th><th class="r">Exports</th>'
           '<th>Largest supplier</th></tr></thead><tbody>' + ''.join(
    '<tr><td>%s <a href="/sector/%s">%s</a></td><td class="r">%s</td><td class="r">%.1f%%</td><td class="r">%s</td><td>%s</td></tr>'
    % (b['icon'], b['slug'], esc(b['name']), money(b['imp']), b['imp'] / TOT_IMP * 100, money(b['exp']),
       links.partner_link(b['sup'][0][0], esc) if b['sup'] else '—') for b in built) + '</tbody></table></div>')
out.append('<p class="fineprint">Sectors are fixed lists of HS codes chosen by Customs Nepal; a few products could sit in more than one, so the rows do not add up to Nepal’s total.</p>')
out.append('<p class="xlink"><b>See also:</b> <a href="/trade-partners">trade by country</a> · <a href="/customs-offices">by customs office</a> · '
           '<a href="/trade/categories">all 96 HS chapters</a> · <a href="/import-duty">import duty by product</a></p>')
out.append('</div>' + FOOT)
(pub / 'sectors.html').write_text(''.join(out), encoding='utf-8')
n = k.add_to_sitemap(['/sectors'] + ['/sector/' + b['slug'] for b in built])
print('sector_pages: %d sector pages + hub; +%d sitemap URLs' % (len(built), n))
for b in built:
    print('  %-24s imp %-18s exp %-16s hist %s' % (b['slug'], money(b['imp']), money(b['exp']), 'ok' if b['hist'] else 'MISMATCH'))
