"""Shipping to Nepal — static, crawlable SEO pages on customsnepal.com (the authoritative
Nepal domain). Nepal is landlocked; this section maps how ocean cargo physically reaches it:
the Indian / Bangladeshi gateway ports, the Nepal dry ports (ICDs), the transit corridors,
indicative transit times, and an honest carrier-tracking directory (we link to each line's own
authoritative tracker — we do not store live tracking). Open-data / curated reference, built once.

Mirrors seo_pages.py / export_pages.py (same header/nav/canonical/GA/seo.css).

Emits into public/:
  /shipping              (shipping.html)          hub: landlocked logistics + corridors + transit + node grids
  /shipping/<slug>       (shipping/<slug>.html)   one page per gateway port / Nepal dry port
  /shipping/track        (shipping/track.html)    carrier & cargo tracking directory (deep-links out)
Appends shipping styles to /seo.css and the new URLs to /sitemap.xml.

Run after export_pages.py:  python3 scripts/shipping_pages.py
"""
import pathlib, json, datetime, html

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
(pub / 'shipping').mkdir(parents=True, exist_ok=True)

SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")
NAV = [('/', 'Search'), ('/ask-ai', 'Ask AI'), ('/imports', 'Imports'), ('/exports', 'Exports'),
       ('/export', 'Export guides'), ('/shipping', 'Shipping'), ('/trade-data', 'Trade'),
       ('/browse', 'Browse'), ('/tariff', 'Tariff'), ('/calculator', 'Calculator'), ('/faq', 'FAQ')]

def _cur(h, path):
    return (path == h) or (h == '/shipping' and path.startswith('/shipping')) or (h == '/export' and path.startswith('/export'))

def page_head(title, desc, path, breadcrumb, extra_ld=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = ''.join('<a href="%s"%s>%s</a>' % (h, ' class="cur"' if _cur(h, path) else '', esc(l)) for h, l in NAV)
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
        '<meta property="og:image" content="' + SITE + '/og.png">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="icon" href="' + FAVICON + '"><link rel="apple-touch-icon" href="/icon-180.png">'
        '<link rel="stylesheet" href="/seo.css">'
        + ldj + ANALYTICS +
        '</head><body>'
        '<header class="top"><div class="wrap topbar">'
        '<a class="logo" href="/" aria-label="Customs Nepal — home"><span class="mark">HS</span><span class="lt">Nepal HS Code Finder<small>Customs Tariff 2026/27</small></span></a>'
        '<nav class="topnav">' + nav + '</nav></div></header>'
        '<div class="wrap">'
    )

def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'

FOOT = ('<footer><div class="wrap">'
        '<p><b>Transit times &amp; distances are indicative planning ranges</b>, not quotes — actual times vary with '
        'sailing schedules, transshipment, port congestion, documentation and season. Confirm routing, rates and '
        'timings with your freight forwarder or shipping line. <b>Tracking links go to third-party carriers and '
        'authorities</b> (we do not store or provide live tracking data).</p>'
        '<p>Transit framework: Nepal&ndash;India Treaty of Transit and Nepal&ndash;Bangladesh transit arrangements. '
        'Dry ports are operated under the <a href="https://nitdb.gov.np" target="_blank" rel="noopener noreferrer nofollow">Nepal Intermodal Transport Development Board (NITDB)</a>; '
        'clearance is by the <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer nofollow">Department of Customs</a>.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/shipping">Shipping</a> · <a href="/shipping/track">Track a container</a> · '
        '<a href="/imports">Imports</a> · <a href="/export">Export guides</a> · <a href="/calculator">Landed-cost calculator</a> · © customsnepal.com</p></div></footer>'
        '</body></html>')

# ---------------- nodes (curated reference) ----------------
# type: 'gateway' (sea port used for Nepal transit) | 'icd' (Nepal inland clearance depot / dry port)
NODES = {
 'kolkata': dict(type='gateway', name='Kolkata Port (Syama Prasad Mookerjee Port)', short='Kolkata',
   country='India', locode='INCCU', lat=22.55, lon=88.32, mode='Broad-gauge rail + road',
   tagline="Nepal's traditional sea gateway on the east coast.",
   to_birgunj='~720 km · ~3–6 days (after port release)',
   chain=['Ocean vessel', 'Kolkata Port', 'Broad-gauge rail', 'Raxaul (border)', 'Birgunj ICD', 'Nepal market'],
   about=("Kolkata Port (officially the Syama Prasad Mookerjee Port, Kolkata) is Nepal's traditional and still-"
          "heavily-used sea gateway under the Nepal–India Treaty of Transit. It is a riverine port on the Hooghly, "
          "so vessel draft is limited and larger ships often work the downstream docks at Haldia."),
   role=("Containers for Nepal move from Kolkata by broad-gauge rail to Raxaul, across the border from Birgunj, and "
         "on to the Birgunj ICD (Sirsiya) for Nepal Customs clearance. Congestion and dwell at Kolkata can be "
         "significant, which is a large part of why Visakhapatnam has grown as an alternative east-coast gateway."),
   feeds='birgunj'),
 'haldia': dict(type='gateway', name='Haldia Dock Complex', short='Haldia',
   country='India', locode='INHAL', lat=22.03, lon=88.09, mode='Broad-gauge rail + road',
   tagline="Deeper-draft dock complex downstream of Kolkata.",
   to_birgunj='~770 km · ~3–6 days (after port release)',
   chain=['Ocean vessel', 'Haldia Dock', 'Broad-gauge rail', 'Raxaul (border)', 'Birgunj ICD', 'Nepal market'],
   about=("Haldia, downstream of Kolkata on the Hooghly estuary, is part of the Kolkata port trust and handles "
          "deeper-draft vessels than the Kolkata docks themselves."),
   role=("For Nepal it plays the same role as Kolkata — an eastern gateway feeding the Birgunj rail corridor — and "
         "the two are usually quoted together as “Kolkata/Haldia.” Larger vessels from the Far East and Europe "
         "often discharge here rather than at the shallower Kolkata docks."),
   feeds='birgunj'),
 'visakhapatnam': dict(type='gateway', name='Visakhapatnam Port (Vizag)', short='Visakhapatnam',
   country='India', locode='INVTZ', lat=17.69, lon=83.28, mode='Container block trains (rail)',
   tagline="Deep-water east-coast port, Nepal's fast-growing alternative to Kolkata.",
   to_birgunj='~1,400 km · ~4–7 days (after port release)',
   chain=['Ocean vessel', 'Visakhapatnam Port', 'Container block train', 'Raxaul (border)', 'Birgunj ICD', 'Nepal market'],
   about=("Visakhapatnam (Vizag) is a deep-water port on India's east coast that was opened to Nepal's transit "
          "cargo (operational from 2018) specifically as an alternative to congested Kolkata. It takes bigger ships "
          "and offers direct container block-train service on the broad-gauge network toward the Nepal border."),
   role=("Though farther from Nepal than Kolkata, Vizag's deeper draft, larger-vessel calls and more reliable rail "
         "have made it a fast-growing choice for Nepal's containerized imports — particularly bulkier and "
         "Far-East-origin cargo that benefits from fewer transshipments and less port dwell."),
   feeds='birgunj'),
 'nhava-sheva': dict(type='gateway', name='Jawaharlal Nehru Port (Nhava Sheva / JNPT)', short='Nhava Sheva',
   country='India', locode='INNSA', lat=18.95, lon=72.95, mode='Rail (Concor) / road',
   tagline="India's largest container port — the west-coast gateway for Europe, Gulf & Americas cargo.",
   to_birgunj='~1,850 km · ~6–9 days (after port release)',
   chain=['Ocean vessel', 'Nhava Sheva (JNPT)', 'Rail (Concor) / road', 'Birgunj corridor', 'Birgunj ICD', 'Nepal market'],
   about=("Jawaharlal Nehru Port (Nhava Sheva, JNPT), near Mumbai, is India's largest container port and its main "
          "west-coast gateway, with calls from nearly every major shipping line."),
   role=("For Nepal it matters most for cargo originating in Europe, the Middle East and the Americas, which reaches "
         "India's west coast faster than the east. The inland haul to Nepal is long (~1,800+ km), handled by rail "
         "(Container Corporation of India) or road, usually routed to the Birgunj dry port."),
   feeds='birgunj'),
 'mundra': dict(type='gateway', name='Mundra Port', short='Mundra',
   country='India', locode='INMUN', lat=22.74, lon=69.70, mode='Rail (Concor) / road',
   tagline="India's largest private port (Gujarat) — a west-coast option with strong rail links.",
   to_birgunj='~2,000 km · ~6–9 days (after port release)',
   chain=['Ocean vessel', 'Mundra Port', 'Rail (Concor) / road', 'Birgunj corridor', 'Birgunj ICD', 'Nepal market'],
   about=("Mundra, in Gujarat, is India's largest private port (operated by the Adani group) and a growing west-"
          "coast gateway with its own dedicated rail corridors toward northern India."),
   role=("Like Nhava Sheva, Mundra serves Nepal cargo from Europe and the Gulf, offering an alternative west-coast "
         "entry with strong Concor rail connectivity toward the Nepal border and the Birgunj dry port."),
   feeds='birgunj'),
 'mongla': dict(type='gateway', name='Mongla Port', short='Mongla',
   country='Bangladesh', locode='BDMGL', lat=22.49, lon=89.59, mode='Road/rail via Banglabandha–Phulbari',
   tagline="Bangladesh's second seaport — an eastern-corridor alternative for Nepal.",
   to_birgunj='via Kakarbhitta (eastern Nepal)',
   chain=['Ocean vessel', 'Mongla Port', 'Banglabandha–Phulbari transit', 'Kakarbhitta (border)', 'Eastern Nepal'],
   about=("Mongla is Bangladesh's second seaport, made available to Nepal for transit trade — giving eastern Nepal "
          "an alternative to the Indian corridor."),
   role=("Cargo moves via the Banglabandha–Phulbari route (a short transit through India) toward the Kakarbhitta "
         "area in far-eastern Nepal. It is an emerging option, strongest for eastern Nepal and for trade with "
         "Bangladesh itself, though the multi-border routing adds complexity."),
   feeds='kakarbhitta'),
 'chittagong': dict(type='gateway', name='Chattogram Port (Chittagong)', short='Chattogram',
   country='Bangladesh', locode='BDCGP', lat=22.31, lon=91.80, mode='Road/rail via Banglabandha–Phulbari',
   tagline="Bangladesh's principal seaport — available to Nepal under transit arrangements.",
   to_birgunj='via Kakarbhitta (eastern Nepal)',
   chain=['Ocean vessel', 'Chattogram Port', 'Banglabandha–Phulbari transit', 'Kakarbhitta (border)', 'Eastern Nepal'],
   about=("Chattogram (Chittagong) is Bangladesh's principal and largest seaport, better-connected internationally "
          "than Mongla, and is also offered to Nepal under a transit arrangement."),
   role=("For Nepali traders it is mainly relevant for the eastern corridor and for growing Nepal–Bangladesh trade. "
         "It is farther from Nepal than the Indian east-coast ports, but its deeper international network can suit "
         "cargo bound for eastern Nepal."),
   feeds='kakarbhitta'),
 'birgunj': dict(type='icd', name='Birgunj ICD (Sirsiya Inland Container Depot)', short='Birgunj ICD',
   country='Nepal', operator='NITDB', lat=27.00, lon=84.87, mode='Rail-linked (broad gauge) + road', rail=True,
   tagline="Nepal's flagship rail-linked dry port — where most sea cargo is cleared.",
   border='Raxaul (India) — ~6 km broad-gauge rail link',
   chain=['Indian gateway (Kolkata / Vizag)', 'Broad-gauge rail', 'Raxaul (border)', 'Birgunj ICD', 'Nepal market'],
   about=("Birgunj ICD at Sirsiya is Nepal's flagship inland container depot and its only rail-linked dry port. A "
          "broad-gauge line runs about 6 km to Raxaul in India, connecting directly to Kolkata, Haldia and "
          "Visakhapatnam."),
   role=("Operated under the Nepal Intermodal Transport Development Board (NITDB), Birgunj is where the bulk of "
         "Nepal's containerized sea imports are cleared by Nepal Customs. For most ocean freight into Nepal, this is "
         "the destination node — the point where the sea-and-rail journey ends and goods enter the Nepali market."),
   fed_by=['kolkata', 'haldia', 'visakhapatnam', 'nhava-sheva', 'mundra']),
 'biratnagar': dict(type='icd', name='Biratnagar ICD', short='Biratnagar ICD',
   country='Nepal', operator='NITDB', lat=26.45, lon=87.28, mode='Road', rail=False,
   tagline="Road-based dry port serving eastern Nepal.",
   border='Jogbani (India)',
   chain=['Indian gateway', 'Rail / road to border', 'Jogbani (border)', 'Biratnagar ICD', 'Eastern Nepal'],
   about=("Biratnagar ICD, in eastern Nepal near the Jogbani (India) border, is a road-based inland clearance depot "
          "serving the eastern region and its industrial corridor."),
   role=("It handles cargo trucked from the Indian rail/road network and is part of Nepal's NITDB dry-port system, "
         "clearing goods destined for eastern Nepal without routing everything through Birgunj."),
   fed_by=['kolkata', 'haldia', 'visakhapatnam']),
 'bhairahawa': dict(type='icd', name='Bhairahawa ICD', short='Bhairahawa ICD',
   country='Nepal', operator='NITDB', lat=27.50, lon=83.45, mode='Road', rail=False,
   tagline="Road-based dry port serving western & central Nepal.",
   border='Belahiya / Sunauli (India)',
   chain=['Indian gateway', 'Rail / road to border', 'Belahiya–Sunauli (border)', 'Bhairahawa ICD', 'Western Nepal'],
   about=("Bhairahawa ICD, near the Belahiya/Sunauli border in Rupandehi, is a road-based dry port serving western "
          "and central Nepal, including the Lumbini region."),
   role=("Cargo is trucked in from the Indian side; it is a key clearance point for the western corridor, shortening "
         "the inland leg for goods bound for western Nepal compared with clearing at Birgunj."),
   fed_by=['nhava-sheva', 'mundra', 'kolkata']),
 'kakarbhitta': dict(type='icd', name='Kakarbhitta ICD', short='Kakarbhitta ICD',
   country='Nepal', operator='NITDB', lat=26.64, lon=88.16, mode='Road', rail=False,
   tagline="Far-eastern dry port — the node for the Bangladesh corridor.",
   border='Panitanki (India) / Banglabandha (Bangladesh)',
   chain=['Bangladesh port (Mongla / Chattogram)', 'Banglabandha–Phulbari transit', 'Kakarbhitta (border)', 'Kakarbhitta ICD', 'Eastern Nepal'],
   about=("Kakarbhitta ICD, in far-eastern Nepal near the Panitanki (India) crossing, sits at the junction of the "
          "eastern and Bangladesh corridors."),
   role=("The Banglabandha–Phulbari route from Mongla and Chattogram feeds cargo here, making Kakarbhitta the Nepal "
         "entry node for Bangladesh-routed sea freight as well as overland trade with far-eastern India."),
   fed_by=['mongla', 'chittagong']),
 'chobhar': dict(type='icd', name='Chobhar Dry Port (Kathmandu)', short='Chobhar Dry Port',
   country='Nepal', operator='NITDB', lat=27.65, lon=85.29, mode='Road', rail=False,
   tagline="Kathmandu Valley dry port — clearance near the capital's market.",
   border='fed overland from Birgunj / the southern border',
   chain=['Indian gateway', 'Birgunj corridor', 'Road to Kathmandu', 'Chobhar Dry Port', 'Kathmandu market'],
   about=("Chobhar Dry Port, in the Kathmandu Valley (operational from 2020), was built to decongest border "
          "clearance and move customs closer to the capital's consumption centre."),
   role=("Cargo is trucked up from the border and Birgunj corridor; Chobhar clears goods destined for the Kathmandu "
         "market, easing pressure on the southern dry ports for capital-bound freight."),
   fed_by=['birgunj']),
}
GATEWAYS = ['kolkata', 'haldia', 'visakhapatnam', 'nhava-sheva', 'mundra', 'mongla', 'chittagong']
ICDS = ['birgunj', 'biratnagar', 'bhairahawa', 'kakarbhitta', 'chobhar']

# ---------------- carrier / cargo tracking directory ----------------
CARRIERS = [
 ('Maersk', 'https://www.maersk.com/tracking', 'World #1 line; strong India east- and west-coast coverage.'),
 ('MSC', 'https://www.msc.com/en/track-a-shipment', 'Largest container line; wide India service network.'),
 ('CMA CGM', 'https://www.cma-cgm.com/ebusiness/tracking/search', 'Major India calls and transshipment hubs.'),
 ('Hapag-Lloyd', 'https://www.hapag-lloyd.com/en/online-business/track/track-by-container.html', 'Strong Europe–India coverage.'),
 ('ONE (Ocean Network Express)', 'https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking', 'Asia–India services.'),
 ('COSCO Shipping', 'https://elines.coscoshipping.com/ebusiness/cargoTracking', 'China–India routes.'),
 ('Evergreen', 'https://www.shipmentlink.com/', 'Far-East network via ShipmentLink.'),
 ('HMM', 'https://www.hmm21.com/', 'Asia–India and Europe services.'),
]
INLAND = [
 ('CONCOR (India rail)', 'https://www.concorindia.co.in/', 'Container Corporation of India — tracks the rail leg to Raxaul / the Nepal border.'),
 ('Nepal Customs (ASYCUDA)', 'https://www.customs.gov.np/', 'Declaration and clearance status at the Nepal dry port.'),
 ('NITDB', 'https://nitdb.gov.np/', 'Nepal Intermodal Transport Development Board — the dry ports / ICDs.'),
]

def chain_html(segs):
    inner = ' <span class="ar">→</span> '.join('<span class="seg">%s</span>' % esc(s) for s in segs)
    return '<div class="chain">' + inner + '</div>'

def node_card(slug):
    n = NODES[slug]
    sub = ('%s · %s' % (n['country'], n.get('locode', n.get('operator', '')))) if n['type'] == 'gateway' \
          else ('%s · %s' % (n['country'], n.get('operator', '')))
    return ('<a class="chcard" href="/shipping/%s"><span class="t">%s</span>'
            '<span class="c">%s — %s</span></a>' % (slug, esc(n['short']), esc(sub), esc(n['tagline'])))

def node_tiles(n):
    t = 'Sea gateway' if n['type'] == 'gateway' else 'Nepal dry port'
    c2l, c2v = ('UN/LOCODE', n['locode']) if n['type'] == 'gateway' else ('Operator', n.get('operator', 'NITDB'))
    return ('<div class="exstats">'
            '<div class="extile"><b>%s</b><span>Type</span></div>'
            '<div class="extile"><b>%s</b><span>%s</span></div>'
            '<div class="extile"><b>%s</b><span>Mode to Nepal</span></div></div>'
            % (esc(t), esc(c2v), esc(c2l), esc(n['mode'])))

# ---------------- node pages ----------------
for slug, n in NODES.items():
    path = '/shipping/' + slug
    is_gw = n['type'] == 'gateway'
    kind = 'gateway port' if is_gw else 'Nepal dry port'
    title = '%s → Nepal: %s | Customs Nepal' % (n['short'], ('sea gateway' if is_gw else 'inland dry port'))
    if len(title) > 70:
        title = '%s — shipping to Nepal | Customs Nepal' % n['short']
    desc = '%s %s' % (n['tagline'], ('How cargo routes through %s to Nepal, the inland leg to the Birgunj dry port, and transit times.' % n['short']) if is_gw else ('How sea cargo reaches %s, the border crossing it uses, and which gateway ports feed it.' % n['short']))
    bc = [('Home', '/'), ('Shipping', '/shipping'), (n['short'], '')]
    place = {"@context": "https://schema.org", "@type": ("Seaport" if is_gw else "Place"),
             "name": n['name'], "address": {"@type": "PostalAddress", "addressCountry": n['country']},
             "geo": {"@type": "GeoCoordinates", "latitude": n['lat'], "longitude": n['lon']}}
    out = [page_head(title, desc, path, bc, extra_ld=[place]), crumb_html(bc)]
    out.append('<h1>%s</h1>' % esc(n['name']))
    out.append('<p class="lede">%s</p>' % esc(n['tagline']))
    out.append(node_tiles(n))
    out.append('<h2 class="sec">About</h2><p>%s</p>' % esc(n['about']))
    out.append('<h2 class="sec">%s</h2><p>%s</p>' % ('Role for Nepal cargo' if is_gw else 'What clears here', esc(n['role'])))
    out.append('<h2 class="sec">How cargo reaches Nepal</h2>')
    out.append(chain_html(n['chain']))
    if is_gw:
        out.append('<p><b>Inland leg to Birgunj ICD:</b> %s. <b>Mode:</b> %s.</p>' % (esc(n['to_birgunj']), esc(n['mode'])))
    else:
        out.append('<p><b>Border crossing:</b> %s. <b>Mode:</b> %s%s.</p>'
                   % (esc(n['border']), esc(n['mode']), ' — Nepal’s only rail-connected dry port' if n.get('rail') else ''))
    # related nodes
    if is_gw:
        feed = n.get('feeds')
        out.append('<p>Feeds the <a href="/shipping/%s">%s</a>.</p>' % (feed, esc(NODES[feed]['short'])) if feed else '')
        rel = [g for g in GATEWAYS if g != slug]
        rel_title = 'Other gateway ports'
    else:
        fb = n.get('fed_by', [])
        if fb:
            links = ', '.join('<a href="/shipping/%s">%s</a>' % (g, esc(NODES[g]['short'])) for g in fb)
            out.append('<p><b>Fed by:</b> %s.</p>' % links)
        rel = [i for i in ICDS if i != slug]
        rel_title = 'Other Nepal dry ports'
    out.append('<div class="tools"><a class="btn" href="/shipping/track">Track a container to Nepal</a>'
               '<a class="btn ghost" href="/calculator">Estimate landed cost</a>'
               '<a class="btn ghost" href="https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=11/%s/%s" target="_blank" rel="noopener noreferrer nofollow">View location ↗</a></div>'
               % (n['lat'], n['lon'], n['lat'], n['lon']))
    out.append('<h2 class="sec">%s</h2><div class="guidegrid">' % rel_title)
    for s in rel:
        out.append(node_card(s))
    out.append('</div>')
    out.append('<p class="fineprint">Transit times and distances are indicative planning ranges, not quotes — '
               'confirm with your freight forwarder. See the <a href="/shipping">shipping overview</a> for the full '
               'corridor and transit-time tables.</p>')
    out.append('</div>' + FOOT)
    (pub / 'shipping' / (slug + '.html')).write_text(''.join(out), encoding='utf-8')

# ---------------- tracking directory ----------------
path = '/shipping/track'
title = 'Track a container to Nepal: carrier & cargo tracking | Customs Nepal'
desc = ("Track your ocean freight to Nepal. Links to every major shipping line's own container tracker, plus the "
        "India-rail (CONCOR) and Nepal Customs clearance legs — and how the full journey is tracked end to end.")
bc = [('Home', '/'), ('Shipping', '/shipping'), ('Track a container', '')]
out = [page_head(title, desc, path, bc), crumb_html(bc)]
out.append('<h1>Track a container to Nepal</h1>')
out.append('<p class="lede">We don’t store live tracking data — these link straight to each carrier’s and '
           'authority’s own authoritative tracker. Enter your container or bill-of-lading number there.</p>')
out.append('<div class="note">Because Nepal is landlocked, the full journey is usually tracked in <b>two or three '
           'legs</b>, each by a different party:\n'
           '1. <b>The ocean line</b> (Maersk, MSC, …) — from the origin port to the Indian gateway (Kolkata / Vizag) '
           'or Bangladeshi port.\n'
           '2. <b>CONCOR / Indian Railways</b> — the rail leg from the gateway port to Raxaul / the Nepal border.\n'
           '3. <b>Nepal Customs (ASYCUDA)</b> — declaration and clearance at the Birgunj or other dry port.</div>')
out.append('<h2 class="sec">Ocean carriers</h2>')
out.append('<p>Track the sea leg to the Indian or Bangladeshi gateway port by container number:</p>')
out.append('<div class="guidegrid">')
for name, url, note in CARRIERS:
    out.append('<a class="chcard" href="%s" target="_blank" rel="noopener noreferrer nofollow">'
               '<span class="t">%s ↗</span><span class="c">%s</span></a>' % (url, esc(name), esc(note)))
out.append('</div>')
out.append('<h2 class="sec">Inland & clearance (the Nepal leg)</h2>')
out.append('<div class="guidegrid">')
for name, url, note in INLAND:
    out.append('<a class="chcard" href="%s" target="_blank" rel="noopener noreferrer nofollow">'
               '<span class="t">%s ↗</span><span class="c">%s</span></a>' % (url, esc(name), esc(note)))
out.append('</div>')
out.append('<div class="tools"><a class="btn" href="/shipping">Shipping overview &amp; transit times</a>'
           '<a class="btn ghost" href="/calculator">Estimate landed cost</a></div>')
out.append('<p class="fineprint">Carrier and authority links are provided for convenience and point to third-party '
           'websites; Customs Nepal is not affiliated with them and does not control their content or availability.</p>')
out.append('</div>' + FOOT)
(pub / 'shipping' / 'track.html').write_text(''.join(out), encoding='utf-8')

# ---------------- hub ----------------
OCEAN = [
 ('Shanghai / Ningbo (China)', 'Kolkata / Vizag', '~14–22 days*'),
 ('Singapore', 'Kolkata / Vizag', '~7–12 days'),
 ('Port Klang (Malaysia)', 'Kolkata', '~8–12 days'),
 ('Jebel Ali (UAE)', 'Nhava Sheva', '~5–8 days'),
 ('Rotterdam / Hamburg (Europe)', 'Nhava Sheva', '~20–28 days'),
 ('Rotterdam (Europe)', 'Kolkata', '~26–32 days'),
 ('US East Coast (New York)', 'Nhava Sheva', '~30–40 days'),
]
INLAND_T = [
 ('Kolkata / Haldia', '~720–770 km', 'Broad-gauge rail → Raxaul + road', '~3–6 days'),
 ('Visakhapatnam', '~1,400 km', 'Container block trains', '~4–7 days'),
 ('Nhava Sheva / Mundra', '~1,850–2,000 km', 'Rail (CONCOR) / road', '~6–9 days'),
]
faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": "Does Nepal have a seaport?",
     "acceptedAnswer": {"@type": "Answer", "text": "No. Nepal is landlocked. Ocean cargo reaches Nepal by sea to a gateway port in India (mainly Kolkata/Haldia or Visakhapatnam) or Bangladesh (Mongla/Chattogram), then by rail or road to a Nepal dry port, where it is cleared by Nepal Customs."}},
    {"@type": "Question", "name": "Which port is used for shipping to Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": "Most of Nepal's sea cargo is routed through Kolkata/Haldia or, increasingly, Visakhapatnam on India's east coast, then by broad-gauge rail to the Birgunj dry port (ICD Sirsiya). West-coast ports (Nhava Sheva, Mundra) are used for cargo from Europe, the Gulf and the Americas."}},
    {"@type": "Question", "name": "How long does ocean freight to Nepal take?",
     "acceptedAnswer": {"@type": "Answer", "text": "Indicatively 3–6 weeks door-to-dry-port: the sea leg to an Indian gateway (roughly 1–6 weeks depending on origin) plus the inland rail/road leg to Birgunj (about 3–9 days) and customs clearance. Congestion, transshipment and documentation can extend this."}}]}
title = 'Shipping to Nepal: ocean freight ports, routes & transit times | Customs Nepal'
desc = ("How ocean freight reaches landlocked Nepal — the Indian and Bangladeshi gateway ports (Kolkata, Haldia, "
        "Visakhapatnam, Nhava Sheva, Mundra, Mongla, Chattogram), the Nepal dry ports/ICDs, transit corridors, "
        "indicative transit times, and how to track your container.")
bc = [('Home', '/'), ('Shipping', '')]
out = [page_head(title, desc, '/shipping', bc, extra_ld=[faq]), crumb_html(bc)]
out.append('<h1>Shipping &amp; ocean freight to Nepal</h1>')
out.append('<p class="lede">Nepal is landlocked — it has no seaport. Every container of sea freight reaches Nepal the '
           'same way: by ocean to a gateway port in India or Bangladesh, then by rail or road to a Nepal dry port, '
           'where it is cleared by Nepal Customs. Here are the ports, the corridors, the transit times, and how to '
           'track it.</p>')
out.append('<div class="exstats">'
           '<div class="extile"><b>0</b><span>Nepal seaports (landlocked)</span></div>'
           '<div class="extile"><b>7</b><span>Gateway ports used</span></div>'
           '<div class="extile"><b>5</b><span>Nepal dry ports (ICD)</span></div></div>')
out.append('<div class="note">Nepal’s sea access runs on the <b>Nepal–India Treaty of Transit</b> (the main '
           'route, via Indian ports) and a <b>Nepal–Bangladesh</b> transit arrangement (an eastern alternative). '
           'Goods for China move overland instead — by road via Rasuwagadhi (Kerung) and Tatopani (Khasa) — not by '
           'sea.</div>')

out.append('<h2 class="sec">The corridors</h2>')
out.append('<h3 class="head">Eastern India corridor — the primary route</h3>')
out.append(chain_html(['Ocean vessel', 'Kolkata / Haldia / Vizag', 'Broad-gauge rail', 'Raxaul (border)', 'Birgunj ICD', 'Nepal market']))
out.append('<h3 class="head">Western India corridor — for Europe, Gulf & the Americas</h3>')
out.append(chain_html(['Ocean vessel', 'Nhava Sheva / Mundra', 'Rail (CONCOR) / road', 'Birgunj corridor', 'Birgunj / Bhairahawa ICD', 'Nepal market']))
out.append('<h3 class="head">Bangladesh corridor — an eastern alternative</h3>')
out.append(chain_html(['Ocean vessel', 'Mongla / Chattogram', 'Banglabandha–Phulbari transit', 'Kakarbhitta (border)', 'Eastern Nepal']))

out.append('<h2 class="sec">Indicative transit times</h2>')
out.append('<p>Planning ranges only — not quotes. Totals run roughly <b>3–6 weeks door-to-dry-port</b> once you add '
           'port dwell and customs clearance.</p>')
out.append('<h3 class="head">Ocean leg · origin → Indian gateway</h3>')
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>From</th><th>To gateway</th><th>Typical sea transit</th></tr></thead><tbody>')
for a, b, c in OCEAN:
    out.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(a), esc(b), esc(c)))
out.append('</tbody></table></div>')
out.append('<h3 class="head">Inland leg · Indian gateway → Birgunj ICD</h3>')
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>Gateway</th><th>Distance</th><th>Mode</th><th>Typical transit</th></tr></thead><tbody>')
for a, b, c, d in INLAND_T:
    out.append('<tr><td>%s</td><td class="unit">%s</td><td>%s</td><td>%s</td></tr>' % (esc(a), esc(b), esc(c), esc(d)))
out.append('</tbody></table></div>')
out.append('<p class="fineprint">*Most East-Asia routings transship at Singapore, Port Klang or Colombo. Sea times '
           'exclude port dwell and the inland leg; add customs clearance at the dry port.</p>')

out.append('<h2 class="sec">Gateway ports</h2>')
out.append('<p>The sea ports Nepal’s cargo passes through — in India and Bangladesh:</p>')
out.append('<div class="guidegrid">')
for s in GATEWAYS:
    out.append(node_card(s))
out.append('</div>')

out.append('<h2 class="sec">Nepal dry ports (ICDs)</h2>')
out.append('<p>Where the sea-and-rail journey ends and Nepal Customs clears the goods:</p>')
out.append('<div class="guidegrid">')
for s in ICDS:
    out.append(node_card(s))
out.append('</div>')

out.append('<div class="tools"><a class="btn" href="/shipping/track">Track a container to Nepal</a>'
           '<a class="btn ghost" href="/calculator">Landed-cost calculator</a>'
           '<a class="btn ghost" href="/imports">Import duty &amp; HS codes</a></div>')
out.append('<p class="fineprint">A reference overview for Nepali importers and exporters. Routing, rates and transit '
           'times vary — always confirm with your freight forwarder, shipping line and the '
           '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer nofollow">Department of Customs</a>.</p>')
out.append('</div>' + FOOT)
(pub / 'shipping.html').write_text(''.join(out), encoding='utf-8')

# ---------------- append styles to seo.css ----------------
SHIPCSS = """
.chain{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:.5em 0 1.2em}
.chain .seg{background:var(--accent-bg);color:var(--accent);font-weight:600;font-size:.82rem;padding:5px 10px;border-radius:8px;white-space:nowrap}
.chain .ar{color:var(--muted);font-weight:700}
"""
css_path = pub / 'seo.css'
cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
if '.chain{' not in cur:
    css_path.write_text(cur + '\n' + SHIPCSS.strip() + '\n', encoding='utf-8')

# ---------------- inject URLs into sitemap.xml ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
rows = ['  <url><loc>%s/shipping</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>' % (SITE, TODAY),
        '  <url><loc>%s/shipping/track</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, TODAY)]
for slug in list(NODES.keys()):
    rows.append('  <url><loc>%s/shipping/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>' % (SITE, slug, TODAY))
if '/shipping</loc>' not in sm:
    sm = sm.replace('</urlset>', '\n'.join(rows) + '\n</urlset>')
    sm_path.write_text(sm, encoding='utf-8')

print('shipping_pages: hub + track + %d node pages (%d gateways, %d ICDs); styles + %d sitemap URLs'
      % (len(NODES), len(GATEWAYS), len(ICDS), len(NODES) + 2))
