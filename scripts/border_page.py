"""/the-border — Nepal's customs gates drawn along the border, west to east, sized by the trade they handle.

Build-time, stdlib only. Trade figures: world/data/offices_trade.json (Department of Customs FTS).
Office directory: data/offices.json. The country outline is Natural Earth (world/data/worldmap.json).
Gate positions are SCHEMATIC: each gate is placed by its approximate longitude (LON below) on the
southern (India), northern (China) or inner (airport / dry port) line — the page says so.
"""
import json, re, math
import pagekit as k
from pagekit import esc, money, pub, root
import viz

T = json.loads((root / 'world/data/offices_trade.json').read_text(encoding='utf-8'))
DIR = json.loads((root / 'data/offices.json').read_text(encoding='utf-8'))['offices']
NPL = json.loads((root / 'world/data/worldmap.json').read_text(encoding='utf-8')).get('NPL', '')
FY = T['fy']
norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s or '').lower())
ALIAS = {'dryport': 'chobhar'}
# approximate longitude (°E) of each customs point — for left-to-right placement only
LON = {'kanchanpur': 80.2, 'kailali': 80.6, 'sati': 81.1, 'nepalgunj': 81.6, 'krishnanagar': 82.8, 'suthauli': 83.05, 'bhairahawa': 83.45,
       'gautambuddha': 83.42, 'maheshpur': 83.65, 'triveni': 83.95, 'birgunj': 84.87, 'gaur': 85.27, 'sarlahi': 85.56, 'jaleshwor': 85.8,
       'janakpur': 85.95, 'thadi': 86.15, 'siraha': 86.3, 'rajbiraj': 86.75, 'sunsari': 87.0, 'biratnagar': 87.28, 'bhadrapur': 88.05,
       'mechi': 88.13, 'pashupatinagar': 88.1, 'mustang': 83.9, 'rasuwa': 85.38, 'tatopani': 85.95, 'tia': 85.36, 'chobhar': 85.29, 'pokhara': 83.98}
SHORT = {'tia': 'Kathmandu airport', 'gautambuddha': 'Bhairahawa airport', 'chobhar': 'Chobhar dry port'}
timp, texp = T['totals']['imp'], T['totals']['exp']
gates = []
for o in DIR:
    key = ALIAS.get(norm(o.get('stat')), norm(o.get('stat')))
    if key in T['offices'] and o['id'] in LON:
        t = T['offices'][key]
        gates.append(dict(o=o, t=t, tot=t['imp'] + t['exp'], lon=LON[o['id']], nm=o['name'].replace(' Customs Office', ''),
                          short=SHORT.get(o['id'], o['name'].replace(' Customs Office', ''))))
gates.sort(key=lambda g: g['lon'])
by_val = sorted(gates, key=lambda g: -g['tot'])
rank = {g['o']['id']: i + 1 for i, g in enumerate(by_val)}

# ---- map geometry: scale the Natural Earth outline of Nepal into a 1000 x 380 frame ----
pts = [(float(x), float(y)) for x, y in re.findall(r'(-?[\d.]+),(-?[\d.]+)', NPL)]
W, H, PADX, PADT, PADB = 1000.0, 440.0, 56.0, 64.0, 96.0
x0 = min(p[0] for p in pts); x1 = max(p[0] for p in pts); y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
sx = (W - 2 * PADX) / (x1 - x0); sy = (H - PADT - PADB) / (y1 - y0)
P = [((x - x0) * sx + PADX, (y - y0) * sy + PADT) for x, y in pts]
LON0, LON1 = 80.06, 88.2
gx = lambda lon: PADX + (lon - LON0) / (LON1 - LON0) * (W - 2 * PADX)


def edge(x, south):
    """y of the outline's southern / northern edge at horizontal position x (scan every outline segment)."""
    ys = []
    n = len(P)
    for i in range(n):
        (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
        if ax == bx:
            continue
        if min(ax, bx) <= x <= max(ax, bx):
            ys.append(ay + (by - ay) * (x - ax) / (bx - ax))
    if not ys:
        return (H - PADB) if south else PADT
    return max(ys) if south else min(ys)


mx = max(g['tot'] for g in gates) or 1.0
rad = lambda v: 5.0 + 34.0 * math.sqrt(v / mx)
b = ['<path d="M%s Z" class="bd-land"/>' % ' L'.join('%.1f,%.1f' % p for p in P)]
b.append('<text x="%.0f" y="30" class="m" font-size="14" text-anchor="middle" font-weight="700">CHINA (north)</text>' % (W / 2))
b.append('<text x="%.0f" y="%.0f" class="m" font-size="14" text-anchor="middle" font-weight="700">INDIA (south, east and west)</text>' % (W / 2, H - 14))
lab_n = set(g['o']['id'] for g in by_val[:9])
for g in sorted(gates, key=lambda g: -g['tot']):
    typ = g['o'].get('type'); x = gx(g['lon'])
    if typ == 'china':
        y = edge(x, False)
    elif typ == 'india':
        y = edge(x, True)
    else:
        y = (edge(x, True) + edge(x, False)) / 2
    g['x'], g['y'] = x, y
    r = rad(g['tot'])
    cls = {'china': 'bd-cn', 'india': 'bd-in'}.get(typ, 'bd-air')
    tip = '%s — imports %s, exports %s (%.1f%% of Nepal’s imports)' % (g['nm'], money(g['t']['imp']), money(g['t']['exp']), g['t']['imp'] / timp * 100)
    b.append('<a href="/customs-office/%s" aria-label="%s"><circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"><title>%s</title></circle></a>'
             % (g['o']['id'], esc(tip), x, y, r, cls, esc(tip)))
for g in gates:
    if g['o']['id'] in lab_n:
        r = rad(g['tot']); up = g['o'].get('type') != 'india'
        ly = g['y'] - r - 8 if up else g['y'] + r + 17
        anchor = 'end' if g['x'] > W - 70 else ('start' if g['x'] < 70 else 'middle')
        b.append('<text x="%.1f" y="%.1f" class="t bd-lab" font-size="14" font-weight="700" text-anchor="%s">%s</text>'
                 % (g['x'] + (r if anchor == 'end' else (-r if anchor == 'start' else 0)), ly, anchor, esc(g['short'])))
MAP = ('<svg class="vz bdmap" viewBox="0 0 %d %d" role="img" aria-label="Nepal’s customs gates placed along the border, sized by trade" '
       'xmlns="http://www.w3.org/2000/svg">%s</svg>' % (W, H, ''.join(b)))

# ---- page ----
SRC = 'Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s · customsnepal.com' % FY
title = 'The Border: every Nepal customs gate, west to east — FY %s' % FY
top = by_val[0]
india = sum(g['t']['imp'] for g in gates if g['o'].get('type') == 'india'); china = sum(g['t']['imp'] for g in gates if g['o'].get('type') == 'china')
air = sum(g['t']['imp'] for g in gates if g['o'].get('type') not in ('india', 'china'))
desc = ('A map of Nepal’s %d customs gates sized by the trade they clear. %s alone handles %.0f%% of imports; the two China gates together %.1f%%. '
        'Official customs figures, FY %s.' % (len(gates), top['nm'], top['t']['imp'] / timp * 100, china / timp * 100, FY))
qa = [('Which is the busiest customs point in Nepal?', '%s. It cleared imports worth %s in FY %s, %.0f%% of everything Nepal imported.'
       % (top['nm'], money(top['t']['imp']), FY, top['t']['imp'] / timp * 100)),
      ('How much of Nepal’s imports come across the India border?', 'About %.0f%% of imports by value were cleared at gates on the India border in FY %s, %.1f%% at the China border gates and %.0f%% at airports and the inland dry port.'
       % (india / timp * 100, FY, china / timp * 100, air / timp * 100)),
      ('How many customs offices handle trade in Nepal?', '%d customs offices reported trade in FY %s: %d on the India border, %d on the China border and %d airports or inland ports.'
       % (len(gates), FY, sum(1 for g in gates if g['o'].get('type') == 'india'), sum(1 for g in gates if g['o'].get('type') == 'china'),
          sum(1 for g in gates if g['o'].get('type') not in ('india', 'china'))))]
ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}]
bc = [('Home', '/'), ('Customs offices', '/customs-offices'), ('The Border', '')]
out = [k.page_head(title, desc, '/the-border', bc, extra_ld=ld), k.crumb_html(bc)]
out.append('</div><section class="cphero"><div class="wrap" style="display:block"><div class="cpkick">%d customs gates · FY %s</div>'
           '<h1>The Border</h1><p class="cplede">Nepal has no sea. Everything it buys and sells crosses a line on a map — and almost all of it crosses at a handful of gates. '
           'Walk the border from west to east and see what each one handles.</p>'
           '<div class="cpstats"><div class="cpstat i"><span>Through India-border gates</span><b>%.0f%%</b></div>'
           '<div class="cpstat e"><span>Through China-border gates</span><b>%.1f%%</b></div>'
           '<div class="cpstat pos"><span>By air and dry port</span><b>%.0f%%</b></div></div></div></section><div class="wrap">'
           % (len(gates), FY, india / timp * 100, china / timp * 100, air / timp * 100))
out.append('<figure class="vzfig" data-title="Nepal’s customs gates by trade handled, FY %s" data-src="%s"><figcaption><b>Every gate, sized by the trade it clears</b>'
           '<span class="vzleg"><i class="bdk in"></i>India border<i class="bdk cn"></i>China border<i class="bdk air"></i>Airport / dry port</span>'
           '<span class="vzbtns"><button type="button" data-act="png">Save image</button></span></figcaption><div class="vzwrap">%s</div></figure>' % (FY, esc(SRC), MAP))
out.append('<p class="fineprint">Tap a circle to open that customs office. Circle area follows imports plus exports. Positions are schematic: each gate is placed by its '
           'approximate longitude along the border, not surveyed coordinates.</p>')
out.append('<h2 class="sec">Walk the border, west to east</h2><div class="bdwalk">')
for g in gates:
    o, t = g['o'], g['t']
    typ = {'india': 'India border', 'china': 'China border', 'airport': 'Airport', 'dryport': 'Inland dry port'}.get(o.get('type'), 'Customs office')
    out.append('<a class="bdgate %s" href="/customs-office/%s"><div class="bdg-h"><b>%s</b><span>%s · %s</span></div>'
               '<div class="bdg-b"><i style="width:%.1f%%"></i></div>'
               '<div class="bdg-n"><span>Imports <b>%s</b></span><span>Exports <b>%s</b></span><span>#%d of %d</span></div></a>'
               % ({'china': 'cn', 'india': 'in'}.get(o.get('type'), 'air'), o['id'], esc(g['nm']), esc(typ), esc(o.get('district') or ''),
                  max(1.5, g['tot'] / mx * 100), money(t['imp']), money(t['exp']), rank[o['id']], len(gates)))
out.append('</div>')
out.append('<h2 class="sec">Quick answers</h2><dl class="qa">' + ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(q), esc(a)) for q, a in qa) + '</dl>')
out.append('<p class="xlink"><b>Keep going:</b> <a href="/customs-offices">customs offices ranked</a> · <a href="/shipping">shipping routes and dry ports</a> · '
           '<a href="/trade-partners">trade by country</a> · <a href="/sectors">trade by sector</a></p>')
CSS = ('<style>.vz .bd-land{fill:var(--accent-bg);stroke:var(--border);stroke-width:2;stroke-linejoin:round}'
       '.vz .bd-in{fill:var(--v1);fill-opacity:.82;stroke:var(--card);stroke-width:1.5}.vz .bd-cn{fill:var(--v2);fill-opacity:.88;stroke:var(--card);stroke-width:1.5}'
       '.vz .bd-air{fill:var(--v3);fill-opacity:.88;stroke:var(--card);stroke-width:1.5}svg.bdmap a:hover circle,svg.bdmap a:focus circle{fill-opacity:1;stroke:var(--fg)}'
       '.vz .bd-lab{paint-order:stroke;stroke:var(--card);stroke-width:4px;stroke-linejoin:round}svg.vz.bdmap{min-width:720px}'
       '.bdk{display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 5px 0 12px}.bdk.in{background:var(--v1)}.bdk.cn{background:var(--v2)}.bdk.air{background:var(--v3)}'
       '.bdwalk{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}'
       '.bdgate{display:block;background:var(--card);border:1px solid var(--border);border-left:4px solid var(--v1);border-radius:12px;padding:12px 14px;color:var(--fg);text-decoration:none}'
       '.bdgate.cn{border-left-color:var(--v2)}.bdgate.air{border-left-color:var(--v3)}.bdgate:hover{border-color:var(--accent);text-decoration:none}'
       '.bdg-h b{display:block}.bdg-h span{font-size:.76rem;color:var(--muted)}'
       '.bdg-b{height:8px;border-radius:4px;background:var(--border);margin:9px 0 8px;overflow:hidden}.bdg-b i{display:block;height:100%;border-radius:4px;background:var(--v1)}'
       '.bdgate.cn .bdg-b i{background:var(--v2)}.bdgate.air .bdg-b i{background:var(--v3)}'
       '.bdg-n{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.8rem;color:var(--fg2)}.bdg-n b{font-variant-numeric:tabular-nums}</style>')
foot = k.foot('<b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + '. Country outline: Natural Earth. '
              'Gate positions are schematic.')
out.append(CSS + '</div>' + foot)
(pub / 'the-border.html').write_text(''.join(out), encoding='utf-8')
print('border_page: /the-border with %d gates; +%d sitemap URL' % (len(gates), k.add_to_sitemap(['/the-border'])))
