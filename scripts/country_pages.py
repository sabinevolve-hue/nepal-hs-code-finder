"""Nepal trade-partner pages — static, crawlable SEO pages on customsnepal.com.

One page per partner country ("Nepal–China trade: imports, exports & duty"),
plus a /trade-partners hub. Each page is framed through Nepal (not a generic
global country profile): the real bilateral figures, what Nepal imports/exports
with that partner (official Dept. of Customs FTS), the duty/SAFTA treatment, the
route goods actually take, and an honest opportunity read.

Data: world/data/country.json  (built offline by world_country.py from the DoC
FTS FY 2081/82) + data/tariff.json (duty + SAFTA rate per HS code).

Mirrors seo_pages.py / export_pages.py (same header/nav/canonical/GA/seo.css).
Run after safta_page.py:  python3 scripts/country_pages.py
"""
import pathlib, json, datetime, html, re

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'trade-partner').mkdir(parents=True, exist_ok=True)

CO = json.loads((root / 'world/data/country.json').read_text(encoding='utf-8'))
TAR = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))

SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
FY = CO.get('fy', '2081/82')
NP_FY = FY.translate(str.maketrans('0123456789', '०१२३४५६७८९'))

# duty lookup: 8-digit (digits only) -> (general, saarc)
DUTY = {}
for r in TAR['rows']:
    code = re.sub(r'\D', '', str(r[0]))[:8]
    if code:
        DUTY[code] = (r[5], r[4])
CHAP = TAR.get('chapters', {})

SAARC = {'IND', 'PAK', 'BGD', 'LKA', 'BTN', 'MDV', 'AFG'}

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def slugify(name):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')

def money(th):
    """Rs '000 -> Nepali-unit rupee string."""
    r = float(th or 0) * 1000.0
    neg = r < 0
    r = abs(r)
    if r >= 1e11:
        s = 'Rs %.2f kharba' % (r / 1e11)
    elif r >= 1e9:
        s = 'Rs %.2f arba' % (r / 1e9)
    elif r >= 1e7:
        s = 'Rs %.1f crore' % (r / 1e7)
    elif r >= 1e5:
        s = 'Rs %.0f lakh' % (r / 1e5)
    else:
        s = 'Rs %.0f' % r
    return ('−' + s) if neg else s

def chap_name(ch2):
    try:
        return CHAP.get(str(int(ch2)), {}).get('t', 'Chapter ' + ch2)
    except Exception:
        return 'Chapter ' + ch2

def rate_text(v):
    if v is None or str(v).strip() == '':
        return None
    s = str(v).strip()
    if s.lower() == 'free' or s == '0':
        return 'Free'
    if re.fullmatch(r'\d+(\.\d+)?', s):
        return s.rstrip('0').rstrip('.') + '%' if '.' in s else s + '%'
    return s  # specific duty text

def rate_cls(txt):
    if txt is None:
        return ''
    if txt == 'Free':
        return 'free'
    m = re.match(r'(\d+(\.\d+)?)%', txt)
    if m:
        n = float(m.group(1))
        return 'low' if n <= 5 else 'mid' if n <= 15 else 'hi'
    return 'mid'

# corridor copy by partner
def corridor(iso):
    if iso == 'IND':
        return ('Overland, across the open Nepal–India border', 'land',
                "Goods move by road and rail directly across the border — Birgunj–Raxaul (the rail-linked main gate), "
                "Bhairahawa–Sunauli, Biratnagar–Jogbani and Kakarbhitta. No sea leg and no third-country transit.")
    if iso == 'CHN':
        return ('Overland, over the Himalaya — not by sea', 'himalaya',
                "China trade runs by road across the mountains: Rasuwagadhi–Kerung (Gyirong), Nepal's main China gate, "
                "and the historic Tatopani–Khasa (Zhangmu) crossing. A Kerung–Kathmandu rail link is proposed, not built.")
    if iso == 'BGD':
        return ('Via the Kakarbhitta–Banglabandha corridor', 'corridor',
                "Trade with Bangladesh moves through the Kakarbhitta–Banglabandha–Phulbari corridor, linking to the "
                "Mongla and Chattogram sea ports.")
    return ('By sea to an Indian gateway port, then overland', 'sea',
            "As a landlocked country Nepal has no sea port, so goods from %s arrive by ocean freight at an Indian "
            "gateway — Kolkata/Haldia or Visakhapatnam — then move by rail/road to the Birgunj (Sirsiya) ICD for "
            "customs clearance.")

# Nepali H1 for the biggest partners
NEPALI = {
    'CHN': 'नेपाल–चीन व्यापार',
    'IND': 'नेपाल–भारत व्यापार',
}

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")
import sys
sys.path.insert(0, str(root / 'scripts'))
from nav import render_nav, OTHER_SITES
import links
import viz
import viz_story as story

def page_head(title, desc, path, breadcrumb, extra_ld=None, og=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = render_nav(path, esc)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0F172A">'
        '<title>' + esc(title) + '</title>'
        '<meta name="description" content="' + esc(desc) + '">'
        '<link rel="canonical" href="' + SITE + path + '">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Customs Nepal">'
        '<meta property="og:title" content="' + esc(title) + '">'
        '<meta property="og:description" content="' + esc(desc) + '">'
        '<meta property="og:url" content="' + SITE + path + '">'
        '<meta property="og:image" content="' + SITE + (og or '/og.png') + '">'
        + ('<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if og else '') +
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="icon" href="' + FAVICON + '"><link rel="apple-touch-icon" href="/icon-180.png">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&display=swap">'
        '<link rel="stylesheet" href="/seo.css">'
        + ldj + ANALYTICS +
        '</head><body>'
        '<header class="top"><div class="wrap topbar">'
        '<a class="logo" href="/" aria-label="Customs Nepal — home"><span class="mark">HS</span><span class="lt">Customs Nepal<small>HS codes, duty &amp; trade</small></span></a>'
        '<nav class="topnav">' + nav + '</nav></div></header>'
        '<div class="wrap">'
    )

def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'

FOOT = ('<footer><div class="wrap">'
        '<p><b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + ' (annual). '
        'Values in Nepali rupees (1 arba = 1 billion; 1 kharba = 100 billion). Duty rates from the Nepal Customs '
        'Tariff ' + esc(TAR.get('v', '')) + '. Figures are for guidance; confirm current rates and rules with the '
        '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs</a> '
        'before you trade.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/trade-partners">Trade partners</a> · <a href="/import-duty">Import duty</a> · '
        '<a href="/calculator">Calculator</a> · <a href="/tariff">Tariff</a> · © customsnepal.com</p>' + OTHER_SITES + '</div></footer>'
        '<script src="/cn-tools.js" defer></script></body></html>')

# ------------------------------------------------------------------ helpers
def scorecard(c, timp, texp):
    imp, exp = c['imp'], c['exp']
    bal = exp - imp
    simp = (imp / timp * 100) if timp else 0
    sexp = (exp / texp * 100) if texp else 0
    ratio = (imp / exp) if exp > 0 else None
    bd = ('Nepal imports <b>%.0f×</b> what it exports here' % ratio) if ratio and ratio >= 2 else \
         ('A rare near-balanced or surplus relationship' if exp >= imp else 'Nepal buys more than it sells here')
    return ('<div class="scards">'
            '<div class="scard imp"><span class="l">Nepal imports from %s</span><b>%s</b><span class="d">%.1f%% of all Nepal imports</span></div>'
            '<div class="scard exp"><span class="l">Nepal exports to %s</span><b>%s</b><span class="d">%.1f%% of all Nepal exports</span></div>'
            '<div class="scard bal"><span class="l">Trade balance</span><b>%s</b><span class="d">%s</span></div>'
            '</div>' % (esc(c['name']), money(imp), simp, esc(c['name']), money(exp), sexp, money(bal), bd))

def cbars(rows, total, cls):
    if not rows:
        return '<p class="fineprint">No chapter breakdown available.</p>'
    mx = max(v for _, v in rows) or 1
    out = ['<div class="cbars">']
    for ch, v in rows:
        share = (v / total * 100) if total else 0
        out.append('<div class="cbar"><span class="cn">%s</span>'
                   '<span class="ct"><i class="%s" style="width:%.1f%%"></i></span>'
                   '<span class="cv">%.0f%%</span></div>' % (esc(chap_name(ch)), cls, v / mx * 100, share))
    out.append('</div>')
    return ''.join(out)

def product_table(rows, iso, direction, rev=None):
    if not rows:
        return '<p class="fineprint">Negligible — no significant %s recorded this year.</p>' % direction
    saarc = iso in SAARC
    head = '<tr><th>Product</th><th>HS code</th><th class="r">Value (FY %s)</th>%s</tr>' % (
        FY, ('<th class="r">Duty rate</th>' + ('<th class="r">Collected at customs</th>' if rev else '')) if direction == 'imports' else '')
    body = []
    for code, desc, val in rows:
        c8 = re.sub(r'\D', '', str(code))[:8]
        hs_link = '/#hs-' + c8
        cell = ''
        if direction == 'imports':
            gen, sa = DUTY.get(c8, (None, None))
            gt = rate_text(gen)
            if gt is None:
                cell = '<td class="r">—</td>'
            else:
                badge = '<span class="badge %s">%s</span>' % (rate_cls(gt), esc(gt))
                if saarc:
                    st = rate_text(sa)
                    if st and st != gt:
                        badge += ' <span class="sfx">SAFTA %s</span>' % esc(st)
                cell = '<td class="r">%s</td>' % badge
            if rev:
                rv = rev.get(str(code), 0.0)
                cell += ('<td class="r">%s<span class="tk">%.1f%% of value</span></td>' % (money(rv), rv / val * 100)) if (rv > 0 and val > 0) else '<td class="r">—</td>'
        al = links.alias_for(c8) if direction == 'imports' else None
        guide = ' <a class="dguide" href="%s">%s duty guide</a>' % (al[0], esc(al[1])) if al else ''
        body.append('<tr><td>%s <a href="%s">%s</a>%s</td><td class="mono">%s.%s.%s</td><td class="r">%s</td>%s</tr>'
                    % (viz.chap_icon(c8[:2]), hs_link, esc(desc[:52]), guide, c8[:4], c8[4:6], c8[6:8], money(val), cell))
    return '<div class="tscroll"><table class="tbl ptbl">' + head + ''.join(body) + '</table></div>'

SRC = 'Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s · customsnepal.com' % FY

def seg_items(rows, total):
    top = rows[:5]
    items = [(viz.chap_short(ch, chap_name(ch)), viz.chap_icon(ch), v) for ch, v in top]
    other = total - sum(v for _, v in top)
    if other > total * 0.005:
        items.append(('Other', '\U0001F4E6', other))
    return items

def prod_items(rows, n=8):
    return [('%s %s' % (viz.chap_icon(str(code)[:2]), desc), money(val), val) for code, desc, val in rows[:n]]

def route_nodes(iso, name):
    if iso == 'IND':
        return [('\U0001F3ED', 'Indian supplier', ''), ('\U0001F69B', 'Road / rail', 'direct, no sea leg'),
                ('\U0001F6C3', 'Border customs', 'Birgunj · Bhairahawa'), ('\U0001F3D9', 'Nepal market', '')]
    if iso == 'CHN':
        return [('\U0001F3ED', 'China factory', 'Guangzhou · Yiwu'), ('\U0001F69B', 'Road via Tibet', ''),
                ('\U0001F3D4', 'Kerung–Rasuwagadhi', 'border crossing'), ('\U0001F6C3', 'Customs', 'duty + VAT'),
                ('\U0001F3D9', 'Kathmandu', '')]
    if iso == 'BGD':
        return [('\U0001F3ED', 'Supplier', 'Bangladesh'), ('\U0001F69B', 'Banglabandha', ''),
                ('\U0001F309', 'Phulbari', 'India transit'), ('\U0001F6C3', 'Kakarbhitta', 'customs'),
                ('\U0001F3D9', 'Nepal market', '')]
    return [('\U0001F3ED', 'Supplier', viz.cut(name, 16)), ('\U0001F6A2', 'Ocean freight', ''),
            ('\u2693', 'Kolkata / Vizag', 'gateway port'), ('\U0001F682', 'Rail / road', 'to Birgunj ICD'),
            ('\U0001F6C3', 'Customs', 'duty + VAT'), ('\U0001F3D9', 'Nepal market', '')]

# ------------------------------------------------------------------ per-country pages
countries = CO['countries']
order = CO['order']
timp = CO['totals'].get('imp', 0)
texp = CO['totals'].get('exp', 0)
trev = CO['totals'].get('rev', 0) or 1.0
have_page = {iso for iso in countries if 'impP' in countries[iso]}
slug_of = {iso: slugify(countries[iso]['name']) for iso in countries}

def other_partners(cur_iso, n=12):
    chips = []
    for iso in order:
        if iso == cur_iso or iso not in have_page:
            continue
        c = countries[iso]
        chips.append('<a href="/trade-partner/%s">%s %s</a>' % (slug_of[iso], c['flag'], esc(c['name'])))
        if len(chips) >= n:
            break
    return '<div class="pchips">' + ''.join(chips) + '</div>'

made = 0
for iso in order:
    if iso not in have_page:
        continue
    c = countries[iso]
    name = c['name']
    slug = slug_of[iso]
    path = '/trade-partner/' + slug
    saarc = iso in SAARC
    chd, _cls, cpara = corridor(iso)

    title = 'Nepal–%s trade: imports, exports & duty | Customs Nepal' % name
    if len(title) > 66:
        title = 'Nepal–%s trade, imports & duty | Customs Nepal' % name
    ratio = (c['imp'] / c['exp']) if c['exp'] > 0 else None
    # <= 160 characters (SEO pass 10 Nov 2026): the figures first, the rest only if it fits
    lead = ('Nepal–%s trade, FY %s (Dept. of Customs): imports %s, exports %s.'
            % (name, FY, money(c['imp']), money(c['exp'])))
    desc = next((d for d in (lead + ' Top products, import duty and how goods move.', lead + ' Top products and duty.', lead)
                 if len(d) <= 160), lead)
    bc = [('Home', '/'), ('Trade partners', '/trade-partners'), (name, '')]
    dataset_ld = {"@context": "https://schema.org", "@type": "Dataset",
                  "name": "Nepal–%s bilateral trade, FY %s" % (name, FY),
                  "description": desc,
                  "temporalCoverage": "Nepali FY %s" % FY,
                  "creator": {"@type": "GovernmentOrganization", "name": "Department of Customs, Nepal"},
                  "isAccessibleForFree": True}
    og = '/og/trade-%s.jpg' % slug
    out = [page_head(title, desc, path, bc, extra_ld=[dataset_ld], og=og if (pub / og.lstrip('/')).exists() else None), crumb_html(bc)]
    bal = c['exp'] - c['imp']
    rank = order.index(iso) + 1
    p_imp = (c['imp'] / timp * 100) if timp else 0
    p_exp = (c['exp'] / texp * 100) if texp else 0
    keytxt = ('Nepal–%s trade, FY %s (Department of Customs, Nepal): imports %s, exports %s, balance %s. '
              'Source: %s%s' % (name, FY, money(c['imp']), money(c['exp']), money(bal), SITE, path))
    np_line = ('<div class="cpnp">%s · आर्थिक वर्ष %s</div>' % (esc(NEPALI[iso]), NP_FY)) if iso in NEPALI else ''
    out.append('</div><section class="cphero"><div class="wrap"><div>'
               '<div class="cpkick">Trade partner #%d of %d · FY %s</div>'
               '<h1>Nepal <span class="arr">⇄</span> %s trade</h1>%s'
               '<p class="cplede">What actually crosses the border between Nepal and %s — the goods, the duty they carry '
               'and the route they take. Official Department of Customs figures.</p>'
               '<div class="cpstats">'
               '<div class="cpstat i"><span>Nepal imports</span><b data-count>%s</b></div>'
               '<div class="cpstat e"><span>Nepal exports</span><b data-count>%s</b></div>'
               '<div class="cpstat %s"><span>Trade balance</span><b data-count>%s</b></div></div>'
               '<button type="button" class="keycopy" data-act="text" data-text="%s">Copy key figures as text</button>'
               '</div><div>%s</div></div></section><div class="wrap">'
               % (rank, len(order), FY, esc(name), np_line, esc(name), money(c['imp']), money(c['exp']),
                  'neg' if bal < 0 else 'pos', money(bal), esc(keytxt),
                  story.flow(c['flag'], name, c['imp'], c['exp'], money(c['imp']), money(c['exp']))))

    # fact cards
    ti = c.get('impP') or []; te = c.get('expP') or []
    facts = ['<div class="cpfact"><div class="ic">\U0001F3C6</div><span>Rank</span><b>#%d of %d partners</b><small>by total trade with Nepal</small></div>' % (rank, len(order))]
    if ti:
        facts.append('<div class="cpfact"><div class="ic">%s</div><span>Top import</span><b>%s</b><small>%s</small></div>'
                     % (viz.chap_icon(str(ti[0][0])[:2]), esc(viz.cut(ti[0][1], 34)), money(ti[0][2])))
    if te:
        facts.append('<div class="cpfact"><div class="ic">%s</div><span>Top export</span><b>%s</b><small>%s</small></div>'
                     % (viz.chap_icon(str(te[0][0])[:2]), esc(viz.cut(te[0][1], 34)), money(te[0][2])))
    else:
        facts.append('<div class="cpfact"><div class="ic">\U0001F4E4</div><span>Top export</span><b>Negligible</b><small>no significant exports</small></div>')
    facts.append('<div class="cpfact"><div class="ic">%s</div><span>Duty treatment</span><b>%s</b><small>%s</small></div>'
                 % (('\U0001F91D', 'SAFTA rate may apply', 'SAARC member') if saarc else ('\U0001F9FE', 'Full general duty', 'no SAFTA preference')))
    out.append('<div class="cpfacts">' + ''.join(facts) + '</div>')

    wf, wf_tsv = story.waffle(p_imp, p_exp, name)
    out.append('<h2 class="sec">The Rs 100 test</h2>')
    out.append(viz.figure('Of every Rs 100 Nepal trades — the %s share' % name, wf, wf_tsv, SRC))

    def flows(chs, prods, total, src_label, note, t1, t2, fname, direction):
        chmap = {}
        items = []
        for k, (ch, v) in enumerate(chs[:5]):
            chmap[ch] = story.CLS[k]
            items.append((viz.chap_short(ch, chap_name(ch)), viz.chap_icon(ch), v, story.CLS[k]))
        other = total - sum(v for _, v in chs[:5])
        if other > total * 0.005:
            items.append(('Other groups', '\U0001F4E6', other, 'cg'))
        if items:
            sk, sk_tsv = story.sankey(src_label, items, money, t1, note)
            out.append(viz.figure(t1, sk, sk_tsv, SRC))
        if prods:
            cells = [(desc, viz.chap_icon(str(code)[:2]), val, chmap.get(str(code)[:2], 'cg')) for code, desc, val in prods]
            cov = sum(val for _, _, val in prods) / total * 100 if total else 0
            t2f = '%s — top %d products, %.0f%% of the total' % (t2, len(prods), cov)
            tm, tm_tsv = story.treemap(cells, money, t2f)
            out.append(viz.figure(t2f, tm, tm_tsv, SRC))

    # imports
    out.append('<h2 class="sec">What Nepal imports from %s</h2>' % esc(name))
    flows(c.get('impC', []), ti, c['imp'], '%s %s' % (c['flag'], esc(viz.cut(name, 18))), 'flows into Nepal as…',
          'From %s into Nepal — by product group' % name, 'What’s in the containers from %s' % name, slug, 'imports')
    if saarc:
        out.append('<div class="note"><b>SAFTA may apply.</b> %s is a SAARC member, so many goods qualify for the lower '
                   '<b>SAARC/SAFTA preferential duty</b> with a valid Certificate of Origin — see the <a href="/safta">SAFTA guide</a>. '
                   'The rates below are the general (MFN) rates; the SAFTA rate is shown where it is lower.</div>' % esc(name))
    else:
        out.append('<div class="note warn"><b>No SAFTA / preferential rate.</b> %s is not a SAARC member, so its goods pay '
                   'Nepal’s <b>full general (MFN) duty</b> — the rates shown below apply in full.</div>' % esc(name))
    out.append('<p>The largest products Nepal buys from %s, by value. Each links to its full HS classification, duty and a landed-cost calculator.</p>' % esc(name))
    if ti:
        out.append(viz.table_tools('nepal-imports-from-%s-fy-%s' % (slug, FY.replace('/', '-'))))
    out.append(product_table(ti, iso, 'imports', c.get('impR')))
    if c.get('impR'):
        out.append('<p class="fineprint">“Collected at customs” is the revenue the Department of Customs reports against each product '
                   'from %s — customs duty plus the other taxes charged at the border (such as VAT and excise) — so it can be '
                   'well above the duty rate alone, and is not zero just because the duty rate is.</p>' % esc(name))

    # what the border earns
    if c.get('rev', 0) > 0 and c['imp'] > 0 and timp:
        take = c['rev'] / c['imp'] * 100; avg = trev / timp * 100
        out.append('<h2 class="sec">What Nepal collects at the border</h2>')
        rvf, rv_tsv = story.revenue(take, avg, name, money(c['rev']))
        out.append(viz.figure('Customs revenue on goods from %s — %s in FY %s' % (name, money(c['rev']), FY), rvf, rv_tsv, SRC))
        out.append('<p>Nepal collected <b>%s</b> at customs on goods from %s — <b>%.1f%%</b> of everything customs collected on '
                   'imports that year. That is about Rs %.1f for every Rs 100 of goods, %s the Rs %.1f average across all '
                   'imports. The mix explains it: fuel, vehicles and consumer goods are taxed heavily; raw materials, '
                   'machinery and many electronics lightly.</p>'
                   % (money(c['rev']), esc(name), c['rev'] / trev * 100, take,
                      'above' if take > avg * 1.05 else ('below' if take < avg * 0.95 else 'close to'), avg))

    # who else sells it
    comp = c.get('comp') or {}
    rrows = []
    for code, pdesc, _v in ti[:6]:
        cc = comp.get(str(code))
        if not cc:
            continue
        segs = [(countries[k]['name'] if k in countries else k, pct, k == iso) for k, pct in cc['t']]
        if not any(m for _, _, m in segs) and cc['s'] > 0:
            segs.append((name, cc['s'], True))
        rrows.append(('%s %s' % (viz.chap_icon(str(code)[:2]), pdesc), str(code), segs))
    if rrows:
        out.append('<h2 class="sec">Who else sells it to Nepal</h2>')
        out.append('<p>For the biggest products Nepal buys from %s: how much of Nepal’s total import of that product comes '
                   'from %s (blue) and who the other main suppliers are (grey). A full blue bar means Nepal depends on one source.</p>'
                   % (esc(name), esc(name)))
        rf, rf_tsv = story.rivals(rrows, name)
        out.append(viz.figure('%s’s share of Nepal’s imports, product by product' % name, rf, rf_tsv, SRC))
        rl = []
        for k in dict.fromkeys(k for code, _, _ in ti[:6] for k, _ in (comp.get(str(code)) or {'t': []})['t']):
            if k != iso and k in have_page:
                rl.append('<a href="/trade-partner/%s">%s %s</a>' % (slug_of[k], countries[k]['flag'], esc(countries[k]['name'])))
        if rl:
            out.append('<p class="xlink"><b>Compare the competing suppliers:</b> ' + ' · '.join(rl[:6]) + '</p>')


    # exports
    out.append('<h2 class="sec">What Nepal exports to %s</h2>' % esc(name))
    if te:
        flows(c.get('expC', []), te, c['exp'], '\U0001F1F3\U0001F1F5 Nepal', 'flows to %s as…' % viz.cut(name, 18),
              'From Nepal to %s — by product group' % name, 'What Nepal ships to %s' % name, slug, 'exports')
        out.append(viz.table_tools('nepal-exports-to-%s-fy-%s' % (slug, FY.replace('/', '-'))))
        out.append(product_table(te, iso, 'exports'))
    else:
        out.append('<p class="fineprint">Nepal’s exports to %s are negligible this year.</p>' % esc(name))

    # how goods move
    out.append('<h2 class="sec">How goods move between Nepal and %s</h2>' % esc(name))
    kind = {'IND': 'land', 'CHN': 'himalaya', 'BGD': 'corridor'}.get(iso, 'sea')
    jr, jr_tsv = story.journey(kind, [(lab, sub) for _, lab, sub in route_nodes(iso, name)], 'Route between %s and Nepal' % name)
    out.append(viz.figure('The journey: %s → Nepal' % name, jr, jr_tsv, 'customsnepal.com/shipping'))
    out.append('<p><b>%s.</b> %s</p>' % (esc(chd), esc(cpara % name if '%s' in cpara else cpara)))
    out.append('<div class="tools"><a class="btn" href="/calculator">Estimate landed cost</a>'
               '<a class="btn ghost" href="/shipping">Shipping routes to Nepal</a></div>')

    # shareable poster
    pst = story.poster(c['flag'], name, FY, money(c['imp']), money(c['exp']), money(bal), c['imp'], c['exp'], bal < 0,
                       [(viz.chap_icon(str(a)[:2]), b_, money(v)) for a, b_, v in ti[:4]],
                       [(viz.chap_icon(str(a)[:2]), b_, money(v)) for a, b_, v in te[:4]], rank, len(order))
    out.append('<h2 class="sec">Share it</h2><div class="cpshare">'
               '<figure class="vzfig" data-title="Nepal %s trade poster" data-src="" data-bare="1" data-pad="0">'
               '<div class="vzwrap">%s</div></figure>'
               '<div><h3>One image, the whole story</h3><p>A ready-made portrait poster of Nepal–%s trade — sized for Instagram, '
               'Facebook, LinkedIn or a slide. Figures are the official FY %s numbers.</p>'
               '<span class="vzbtns" style="margin:0"><button type="button" data-act="pngsib">Download poster (PNG)</button>'
               '<button type="button" data-act="text" data-text="%s">Copy caption</button></span></div></div>'
               % (esc(name), pst, esc(name), FY, esc(keytxt)))

    # opportunity
    out.append('<h2 class="sec">The opportunity, honestly</h2>')
    if ratio and ratio >= 5:
        opp = ('This is a sourcing relationship, not an export one — Nepal buys far more than it sells. The practical '
               'moves: check whether a SAARC source carries a lower SAFTA rate, compare the route and landed cost before '
               'committing, and watch budget-year duty changes on electronics and vehicles. Import demand is not the same '
               'as profit — treat these figures as a starting point for research.')
    else:
        opp = ('Nepal has a real two-way relationship here. On the export side, look at where %s already buys heavily and '
               'where Nepal has genuine product (herbs, carpets, felt, pashmina, specialty agro). Import demand is not the '
               'same as profit — treat these figures as a starting point for research.' % esc(name))
    out.append('<p>%s</p>' % opp)

    hist = links.HISTORY.get(iso)
    out.append('<p class="xlink"><b>Keep going:</b> ' + ' · '.join(x for x in [
        '<a href="%s">%s: 7-year import and export trend</a>' % (hist, esc(name)) if hist else '',
        '<a href="/safta">how the SAFTA rate works</a>' if iso in SAARC else '',
        '<a href="/calculator">landed-cost calculator</a>',
        '<a href="/import-duty#popular-names">import duty by product name</a>',
        '<a href="/shipping">shipping &amp; container tracking</a>'] if x) + '</p>')

    # related
    out.append('<h2 class="sec">Other trade partners</h2>')
    out.append(other_partners(iso))
    out.append('<p class="fineprint">Bilateral figures: Department of Customs, Nepal — FTS FY %s. '
               'Global context on the <a href="/world/trade/%s">%s world trade profile</a>.</p>'
               % (FY, iso.lower(), esc(name)))
    out.append('</div>' + FOOT)
    (pub / 'trade-partner' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')
    made += 1

# ------------------------------------------------------------------ hub
title = 'Nepal’s trade partners — who Nepal trades with & how much | Customs Nepal'
desc = ('Nepal’s trade with every partner country (FY %s, Dept. of Customs): imports, exports and balance, with '
        'per-country guides to products, duty and shipping. India and China dominate.' % FY)
bc = [('Home', '/'), ('Trade partners', '')]
out = [page_head(title, desc, '/trade-partners', bc, og='/og/trade-partners.jpg' if (pub / 'og/trade-partners.jpg').exists() else None), crumb_html(bc)]
hub_key = ('Nepal foreign trade, FY %s (Department of Customs, Nepal): imports %s, exports %s, deficit %s. Source: %s/trade-partners'
           % (FY, money(timp), money(texp), money(texp - timp), SITE))
out.append('</div><section class="cphero"><div class="wrap"><div>'
           '<div class="cpkick">%d trade partners · FY %s</div>'
           '<h1>Who Nepal trades with</h1>'
           '<p class="cplede">Every country Nepal buys from and sells to — the money, the goods and the routes. '
           'India and China together are most of what Nepal buys. Official Department of Customs figures.</p>'
           '<div class="cpstats">'
           '<div class="cpstat i"><span>Total imports</span><b data-count>%s</b></div>'
           '<div class="cpstat e"><span>Total exports</span><b data-count>%s</b></div>'
           '<div class="cpstat neg"><span>Trade deficit</span><b data-count>%s</b></div></div>'
           '<button type="button" class="keycopy" data-act="text" data-text="%s">Copy key figures as text</button>'
           '</div><div>%s</div></div></section><div class="wrap">'
           % (len(order), FY, money(timp), money(texp), money(texp - timp), esc(hub_key),
              story.flow('\U0001F30D', 'The world', timp, texp, money(timp), money(texp))))
_wm = root / 'world/data/worldmap.json'
if _wm.exists():
    shapes = json.loads(_wm.read_text(encoding='utf-8'))
    wm = story.worldmap(shapes, {i: countries[i]['imp'] + countries[i]['exp'] for i in countries},
                        {i: '/trade-partner/' + slug_of[i] for i in have_page},
                        {i: countries[i]['name'] for i in countries}, money)
    wm_tsv = 'Country\tImports\tExports\tTwo-way trade\n' + '\n'.join(
        '%s\t%s\t%s\t%s' % (countries[i]['name'], money(countries[i]['imp']), money(countries[i]['exp']),
                             money(countries[i]['imp'] + countries[i]['exp'])) for i in order)
    out.append('<h2 class="sec">The map — tap a country</h2>')
    out.append(viz.figure('Nepal’s trade with the world, FY %s — darker means more trade' % FY, wm, wm_tsv, SRC))
out.append('<h2 class="sec">Top partners — open a country</h2><div class="cpcards">')
_mx = max(countries[i]['imp'] for i in order[:12])
for i in order[:12]:
    x = countries[i]
    out.append('<a class="cpcard" href="/trade-partner/%s"><div class="fl">%s</div><b>%s</b>'
               '<div class="mb"><i class="a" style="width:%.1f%%"></i></div><div class="mb"><i class="b" style="width:%.1f%%"></i></div>'
               '<small><span>In %s</span><span>Out %s</span></small></a>'
               % (slug_of[i], x['flag'], esc(x['name']), max(1.5, x['imp'] / _mx * 100), max(1.5, x['exp'] / _mx * 100), money(x['imp']), money(x['exp'])))
out.append('</div>')

top = [countries[i] for i in order[:10]]
gb, gb_tsv = viz.grouped([('%s %s' % (x['flag'], x['name']), x['imp'], x['exp']) for x in top], 'Top 10 partners', money)
out.append('<h2 class="sec">Nepal’s top 10 trade partners</h2>')
out.append(viz.figure('Nepal’s top 10 trade partners — imports vs exports, FY %s' % FY, gb, gb_tsv, SRC, legend=viz.LEGEND_IE))
conc = [(countries[i]['name'], countries[i]['flag'], countries[i]['imp']) for i in sorted(order, key=lambda k: -countries[k]['imp'])[:5]]
rest = timp - sum(v for _, _, v in conc)
if rest > 0:
    conc.append(('Other', '\U0001F30D', rest))
cs, cs_tsv = viz.segbar(conc, 'Where Nepal’s imports come from')
out.append(viz.figure('Where Nepal’s imports come from — share by country', cs, cs_tsv, SRC))
out.append('<h2 class="sec">Partners by total trade</h2>')
out.append(viz.table_tools('nepal-trade-partners-fy-%s' % FY.replace('/', '-')))
out.append('<div class="tscroll"><table class="tbl ptbl"><tr><th>Partner</th><th class="r">Imports</th><th class="r">Exports</th><th class="r">Balance</th></tr>')
for iso in order:
    c = countries[iso]
    if (c['imp'] + c['exp']) < 100000:  # skip the long tail on the hub
        continue
    nm = ('<a href="/trade-partner/%s">%s %s</a>' % (slug_of[iso], c['flag'], esc(c['name']))) if iso in have_page \
         else ('%s %s' % (c['flag'], esc(c['name'])))
    out.append('<tr><td>%s</td><td class="r">%s</td><td class="r">%s</td><td class="r">%s</td></tr>'
               % (nm, money(c['imp']), money(c['exp']), money(c['exp'] - c['imp'])))
out.append('</table></div>')
out.append('<p class="fineprint">Source: Department of Customs, Nepal — Foreign Trade Statistics, FY %s. '
           'Values in Nepali rupees (1 arba = 1 billion; 1 kharba = 100 billion).</p>' % FY)
out.append('</div>' + FOOT)
(pub / 'trade-partners.html').write_text(''.join(out), encoding='utf-8')

# ------------------------------------------------------------------ styles
CSS = """
.scards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:1.2em 0}
.scard{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:13px 15px;border-left:3px solid var(--muted)}
.scard.imp{border-left-color:#2a78d6}.scard.exp{border-left-color:#eb6834}.scard.bal{border-left-color:#c0392b}
.scard .l{font-size:.74rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.scard b{display:block;font-size:1.35rem;letter-spacing:-.01em;margin:4px 0 2px}
.scard .d{font-size:.78rem;color:var(--muted)}
.cbars{display:grid;gap:7px;margin:.6em 0 1.1em}
.cbar{display:grid;grid-template-columns:minmax(120px,1.3fr) minmax(0,2fr) auto;gap:10px;align-items:center}
.cbar .cn{font-size:.82rem;color:var(--ink);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cbar .ct{height:12px;background:var(--card);border:1px solid var(--border);border-radius:7px;overflow:hidden}
.cbar .ct i{display:block;height:100%;border-radius:7px}
.cbar .ct i.imp{background:#2a78d6}.cbar .ct i.exp{background:#eb6834}
.cbar .cv{font-size:.8rem;color:var(--muted);font-variant-numeric:tabular-nums;min-width:34px;text-align:right}
table.ptbl .badge{display:inline-block;font-size:.72rem;font-weight:700;padding:2px 7px;border-radius:5px}
table.ptbl .badge.free{background:#dcfce7;color:#047857}table.ptbl .badge.low{background:#e0f2fe;color:#0369a1}
table.ptbl .badge.mid{background:#fef3c7;color:#b45309}table.ptbl .badge.hi{background:#fee2e2;color:#b91c1c}
table.ptbl .sfx{font-size:.68rem;color:#047857;font-weight:600}
table.ptbl td.r,table.ptbl th.r{text-align:right;white-space:nowrap}
table.ptbl .mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;color:var(--muted)}
.h1np{font-size:.6em;color:var(--muted);font-weight:500}
.pchips{display:flex;flex-wrap:wrap;gap:8px;margin:.6em 0 1.2em}
.pchips a{font-size:.85rem;font-weight:600;color:var(--ink);background:var(--card);border:1px solid var(--border);border-radius:999px;padding:7px 13px;text-decoration:none}
.pchips a:hover{border-color:var(--accent);color:var(--accent)}
@media (max-width:560px){.scards{grid-template-columns:1fr}.cbar{grid-template-columns:1fr auto}.cbar .ct{display:none}}
"""
css_path = pub / 'seo.css'
cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
if '.scards{' not in cur:
    css_path.write_text(cur + '\n' + CSS.strip() + '\n', encoding='utf-8')

viz.write_assets(pub)
story.write_assets(pub)

# ------------------------------------------------------------------ sitemap
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows_xml = ['  <url><loc>%s/trade-partners</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>' % (SITE, TODAY)]
for iso in order:
    if iso in have_page:
        rows_xml.append('  <url><loc>%s/trade-partner/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, slug_of[iso], TODAY))
if '/trade-partners</loc>' not in sm:
    sm = sm.replace('</urlset>', '\n'.join(rows_xml) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('country_pages: %d partner pages + hub; styles + %d sitemap URLs' % (made, made + 1))
