"""Customs-office pages: /customs-offices (hub) and /customs-office/<id> (one per office with trade data).

Build-time, stdlib only. Inputs:
  world/data/offices_trade.json   trade through each office by year (scripts/customs_offices.py, offline)
  data/offices.json               office directory captured from customs.gov.np (names, location, contacts)
Every figure is the Department of Customs' own; nothing is estimated. Runs after country_pages.py
(which writes the chart CSS/JS these pages use).
"""
import json, re
import pagekit as k
from pagekit import esc, money, pub, root
import links, viz
import viz_story as story

T = json.loads((root / 'world/data/offices_trade.json').read_text(encoding='utf-8'))
DIR = json.loads((root / 'data/offices.json').read_text(encoding='utf-8'))
FY, YEARS, YTD = T['fy'], T['hist_years'], T.get('ytd')
norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s or '').lower())
STAT_ALIAS = {'dryport': 'chobhar'}          # directory "stat" name -> workbook row
SRC = 'Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s · customsnepal.com' % FY
FOOT = k.foot('<b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + '. Office details from '
              '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">customs.gov.np</a>; phone numbers and '
              'postings change, so confirm with the office before you travel. Values in Nepali rupees (1 arba = 1 billion).')
TYPE = {'india': 'India border', 'china': 'China border', 'airport': 'Airport', 'dryport': 'Inland dry port', 'office': 'Office'}
timp, texp = T['totals']['imp'], T['totals']['exp']

recs = []
for o in DIR['offices']:
    key = norm(o.get('stat')); key = STAT_ALIAS.get(key, key)
    if key and key in T['offices']:
        recs.append((o, T['offices'][key]))
recs.sort(key=lambda r: -(r[1]['imp'] + r[1]['exp']))
rank = {o['id']: i + 1 for i, (o, _) in enumerate(recs)}
short = lambda o: o['name'].replace(' Customs Office', '')
(pub / 'customs-office').mkdir(exist_ok=True)
pct = lambda a, b: (a / b * 100) if b else 0.0

# ---------------------------------------------------------------- office pages
for o, t in recs:
    oid, nm = o['id'], short(o)
    path = '/customs-office/' + oid
    tot = t['imp'] + t['exp']
    title = '%s Customs: %s of trade in FY %s — imports, exports, contact' % (nm, money(tot), FY)
    desc = ('%s handled %s of imports (%.1f%% of Nepal’s total) and %s of exports in FY %s. Year-by-year trend, '
            'location and contact details. Source: Department of Customs.' % (o['name'], money(t['imp']), pct(t['imp'], timp), money(t['exp']), FY))
    bc = [('Home', '/'), ('Customs offices', '/customs-offices'), (nm, '')]
    ld = {"@context": "https://schema.org", "@type": "GovernmentOffice", "name": o['name'],
          "address": {"@type": "PostalAddress", "addressLocality": o.get('location', ''), "addressRegion": o.get('province', ''), "addressCountry": "NP"}}
    if o.get('phone'):
        ld['telephone'] = o['phone']
    out = [k.page_head(title, desc, path, bc, extra_ld=[ld]), k.crumb_html(bc)]
    out.append('<h1>%s Customs Office: trade in FY %s</h1>' % (esc(nm), FY))
    if o.get('np'):
        out.append('<p class="lede" lang="ne">%s</p>' % esc(o['np']))
    out.append('<div class="cpfacts">'
               '<div class="cpfact"><div class="ic">📥</div><span>Imports cleared</span><b>%s</b><small>%.1f%% of Nepal’s imports</small></div>'
               '<div class="cpfact"><div class="ic">📤</div><span>Exports cleared</span><b>%s</b><small>%.1f%% of Nepal’s exports</small></div>'
               '<div class="cpfact"><div class="ic">🏆</div><span>Rank</span><b>#%d of %d offices</b><small>by total trade handled</small></div>'
               '<div class="cpfact"><div class="ic">📍</div><span>Type</span><b>%s</b><small>%s</small></div></div>'
               % (money(t['imp']), pct(t['imp'], timp), money(t['exp']), pct(t['exp'], texp), rank[oid], len(recs),
                  esc(TYPE.get(o.get('type'), 'Customs office')), esc(', '.join(x for x in (o.get('district'), o.get('province')) if x))))
    hh = t.get('hist') or []
    if len(YEARS) >= 3 and len(hh) == len(YEARS) and any(a or b for a, b in hh):
        out.append('<h2 class="sec">%d years through %s</h2>' % (len(YEARS), esc(nm)))
        tf, tsv = story.trend(YEARS, hh, money, nm, heads=('Imports through %s', 'Exports through %s'))
        out.append(viz.figure('Trade cleared at %s, FY %s to %s' % (nm, YEARS[0], YEARS[-1]), tf, tsv, SRC, legend=viz.LEGEND_IE))
    if YTD and t.get('ytd') and (t['ytd'][0] or t['ytd'][1]):
        out.append('<p class="xlink"><b>FY %s so far</b> (%s): imports %s · exports %s. Provisional, from the latest monthly release.</p>'
                   % (YTD['fy'], esc(YTD['label']), money(t['ytd'][0]), money(t['ytd'][1])))
    out.append('<p>The Department of Customs publishes totals per office, not a product or country breakdown per office, so this page '
               'shows how much moves through %s, not what. For what Nepal trades and with whom, see the links below.</p>' % esc(nm))
    # directory
    rows = [(lab, o.get(f)) for lab, f in (('Office', 'name'), ('Location', 'location'), ('District', 'district'), ('Province', 'province'),
                                           ('Border / type', 'border'), ('Phone', 'phone'), ('Mobile', 'mobile'), ('Email', 'email'), ('Website', 'web'))]
    out.append('<h2 class="sec">Office details</h2><div class="tblwrap"><table class="ptbl"><tbody>' + ''.join(
        '<tr><th scope="row">%s</th><td>%s</td></tr>' % (lab, ('<a href="https://%s" target="_blank" rel="noopener noreferrer">%s</a>' % (esc(v), esc(v))) if lab == 'Website' else esc(v))
        for lab, v in rows if v) + '</tbody></table></div>')
    more = []
    if (pub / 'shipping' / (oid + '.html')).exists():
        more.append('<a href="/shipping/%s">%s dry port and shipping guide</a>' % (oid, esc(nm)))
    for cn in ({'india': ['India'], 'china': ['China']}.get(o.get('type'), [])):
        h = links.partner_href(cn)
        if h:
            more.append('<a href="%s">Nepal–%s trade profile</a>' % (h, cn))
    more += ['<a href="/customs-offices">all customs offices compared</a>', '<a href="/trade-partners">trade by country</a>',
             '<a href="/calculator">landed-cost calculator</a>']
    out.append('<p class="xlink"><b>Keep going:</b> ' + ' · '.join(more) + '</p>')
    near = [(x, y) for x, y in recs if x['id'] != oid][:8]
    out.append('<h2 class="sec">Other customs offices</h2><p>' + ' · '.join(
        '<a href="/customs-office/%s">%s</a> (%s)' % (x['id'], esc(short(x)), money(y['imp'] + y['exp'])) for x, y in near) + '</p>')
    out.append('</div>' + FOOT)
    (pub / 'customs-office' / (oid + '.html')).write_text(''.join(out), encoding='utf-8')

# ---------------------------------------------------------------- hub
title = 'Nepal customs offices ranked by trade, FY %s — Birgunj, Bhairahawa, Biratnagar and more' % FY
top = recs[0]
desc = ('Which customs office handles the most trade in Nepal? %s cleared %.0f%% of all imports in FY %s. All %d offices '
        'with imports, exports, share and contact pages.' % (short(top[0]), pct(top[1]['imp'], timp), FY, len(recs)))
bc = [('Home', '/'), ('Customs offices', '')]
out = [k.page_head(title, desc, '/customs-offices', bc), k.crumb_html(bc)]
out.append('<h1>Nepal’s customs offices, ranked by the trade they handle</h1>')
top3 = sum(t['imp'] for _, t in recs[:3])
out.append('<p class="lede">%d customs offices reported trade in FY %s. Three of them — %s — cleared %.0f%% of everything Nepal imported.</p>'
           % (len(recs), FY, ', '.join(short(o) for o, _ in recs[:3]), pct(top3, timp)))
gb, gb_tsv = viz.grouped([(short(o), t['imp'], t['exp']) for o, t in recs[:10]], 'Top 10 customs offices', money)
out.append(viz.figure('Top 10 customs offices by trade, FY %s' % FY, gb, gb_tsv, SRC, legend=viz.LEGEND_IE))
out.append('<h2 class="sec">All offices</h2>' + viz.table_tools('nepal-customs-offices-fy-%s' % FY.replace('/', '-')))
out.append('<div class="tblwrap"><table class="ptbl"><thead><tr><th>Office</th><th>Type</th><th class="r">Imports</th>'
           '<th class="r">Share</th><th class="r">Exports</th><th class="r">Share</th></tr></thead><tbody>' + ''.join(
    '<tr><td><a href="/customs-office/%s">%s</a></td><td>%s</td><td class="r">%s</td><td class="r">%.1f%%</td><td class="r">%s</td><td class="r">%.1f%%</td></tr>'
    % (o['id'], esc(short(o)), esc(TYPE.get(o.get('type'), '')), money(t['imp']), pct(t['imp'], timp), money(t['exp']), pct(t['exp'], texp))
    for o, t in recs) + '</tbody></table></div>')
nodata = [short(o) for o in DIR['offices'] if o['id'] not in rank and o.get('type') != 'office']
if nodata:
    out.append('<p class="fineprint">Offices with no separate line in the FY %s statistics: %s.</p>' % (FY, esc(', '.join(nodata))))
out.append('<p class="xlink"><b>See also:</b> <a href="/trade-partners">trade by country</a> · <a href="/shipping">shipping routes and dry ports</a> · '
           '<a href="/browse">office directory in the app</a></p>')
out.append('</div>' + FOOT)
(pub / 'customs-offices.html').write_text(''.join(out), encoding='utf-8')
n = k.add_to_sitemap(['/customs-offices'] + ['/customs-office/' + o['id'] for o, _ in recs])
print('office_pages: %d office pages + hub; +%d sitemap URLs' % (len(recs), n))
