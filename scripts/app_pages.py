"""Real static HTML for the SPA's app routes (/calculator, /imports, /exports, /trade-data, /ask-ai,
/browse, /about, /privacy).

Before this, those paths were served the homepage HTML through the catch-all rewrite, with the homepage
<title>, description and canonical "/" — fixed only after JavaScript ran. Each route now gets its own file
(public/<route>.html, served by cleanUrls before any rewrite) that is the same app shell as index.html, but
with:
  * a unique <title>, meta description, Open Graph/Twitter tags and a self-referencing canonical;
  * a BreadcrumbList JSON-LD instead of the homepage's Organization/FAQ graph (no duplicated FAQPage);
  * the route's own section visible in the server HTML (search hero hidden), its heading promoted to <h1>
    and a short server-rendered intro with real numbers from the data.
The app's JS still boots exactly as on "/" — it reads location.pathname and opens the same tab.

Appends the routes to public/sitemap.xml. Run after assemble.py and seo_pages.py:
    python3 scripts/app_pages.py
"""
import pathlib, json, re, html, datetime, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from statsfields import IMP_DESC, IMP_VALUE, EXP_DESC, EXP_VALUE, TARIFF_FY, TARIFF_FY_AD, import_duty_path

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
BASE = (pub / 'index.html').read_text(encoding='utf-8')
S = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
T = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
PUBLISHED = set(json.loads((root / 'data/import_duty_published.json').read_text(encoding='utf-8'))['codes'])
FY = S['fy']
NLINES = format(len(T['rows']), ',')


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def rsf(v_thousand):
    v = float(v_thousand) * 1000.0
    if v >= 1e11:                                  # same style as the app's rs(): "Rs 2,096 Arab"
        return 'Rs {:,.0f} Arab'.format(v / 1e9)
    if v >= 1e9:
        return 'Rs %.2f Arab' % (v / 1e9)
    if v >= 1e7:
        return 'Rs %.2f Crore' % (v / 1e7)
    return 'Rs %.1f Lakh' % (v / 1e5)


def pct(a, b):
    return (a - b) / b * 100 if b else 0.0


ov = S['overview']
IMP, IMP0 = ov['imports'][1], ov['imports'][0]
EXP, EXP0 = ov['exports'][1], ov['exports'][0]
top_imp_co = sorted(S['countries'], key=lambda x: -x[1])[:5]
top_exp_co = sorted(S['countries'], key=lambda x: -x[2])[:5]
top_imp = sorted(S['imports'].items(), key=lambda kv: -kv[1][IMP_VALUE])[:6]
top_exp = sorted(S['exports'].items(), key=lambda kv: -kv[1][EXP_VALUE])[:6]


def prod_link(code, desc, value):
    name = esc(desc)
    if code in PUBLISHED or float(value) >= 1000:
        name = '<a href="%s">%s</a>' % (import_duty_path(code, desc), name)
    return '<li>%s (HS %s.%s.%s) — %s</li>' % (name, code[:4], code[4:6], code[6:], rsf(value))


def co_list(rows, idx, total):
    return ', '.join('%s (%.0f%%)' % (esc(r[0]), r[idx] / total * 100) for r in rows)


INTRO_IMPORTS = (
    '<p>Nepal imported <b>%s</b> of goods in FY %s, %s %.1f%% on FY %s, according to the Department of Customs '
    'foreign trade statistics. The largest suppliers were %s.</p>'
    '<p>Most-imported products by value:</p><ul>%s</ul>'
    '<p>For the duty on any of these, see <a href="/import-duty">import duty by product</a> or search the '
    '<a href="/tariff">Nepal Customs Tariff %s</a>.</p>'
    % (rsf(IMP), esc(FY), 'up' if IMP >= IMP0 else 'down', abs(pct(IMP, IMP0)), esc(S['fy_prev']),
       co_list(top_imp_co, 1, IMP), ''.join(prod_link(c, r[IMP_DESC], r[IMP_VALUE]) for c, r in top_imp), TARIFF_FY))

INTRO_EXPORTS = (
    '<p>Nepal exported <b>%s</b> of goods in FY %s, %s %.1f%% on FY %s (Department of Customs foreign trade '
    'statistics). The main destinations were %s.</p>'
    '<p>Top export products by value:</p><ul>%s</ul>'
    '<p>Exporting? Read the <a href="/export">export guides</a> for procedures, documents and certificates of origin.</p>'
    % (rsf(EXP), esc(FY), 'up' if EXP >= EXP0 else 'down', abs(pct(EXP, EXP0)), esc(S['fy_prev']),
       co_list(top_exp_co, 2, EXP),
       ''.join('<li>%s (HS %s.%s.%s) — %s</li>' % (esc(r[EXP_DESC]), c[:4], c[4:6], c[6:], rsf(r[EXP_VALUE])) for c, r in top_exp)))

INTRO_TRADE = (
    '<p>In FY %s Nepal imported <b>%s</b> and exported <b>%s</b> — a trade deficit of <b>%s</b>; exports covered '
    '%.1f%% of imports. This explorer covers every fiscal year from FY %s with chapters, products, partner '
    'countries, customs points and monthly series, from the Department of Customs foreign trade statistics.</p>'
    '<p>Static pages: <a href="/trade/countries">trade by country</a> · <a href="/trade/categories">trade by category</a>.</p>'
    % (esc(FY), rsf(IMP), rsf(EXP), rsf(IMP - EXP), EXP / IMP * 100, esc(S['history']['years'][0])))

INTRO_CALC = (
    '<p>Estimate what an import into Nepal really costs under the <b>Nepal Customs Tariff %s (%s)</b>. Enter the HS '
    'code (or product name) and the invoice value; the calculator works out:</p>'
    '<ol><li><b>CIF value</b> — cost + insurance + freight to the Nepal border, in rupees;</li>'
    '<li><b>customs duty</b> at the code&rsquo;s general rate, or the lower SAARC rate for goods from India and other '
    'SAARC countries with a SAFTA certificate of origin — including specific per-unit duties;</li>'
    '<li><b>excise duty</b> where the product carries it;</li>'
    '<li><b>13%% VAT</b> on CIF + customs duty + excise;</li>'
    '<li>the <b>landed cost</b> in total and per unit.</li></ol>'
    '<p>Per-product worked examples: <a href="/import-duty">import duty by product</a>. All rates: '
    '<a href="/tariff">full tariff by chapter</a>.</p>' % (TARIFF_FY, TARIFF_FY_AD))

INTRO_AI = (
    '<p>Not sure which Nepal HS code fits your product? Describe it in plain English or Nepali — what it is, what it '
    'is made of, what it does. The assistant searches all %s lines of the Nepal Customs Tariff %s, ranks the likely '
    '8-digit codes with reasons and a confidence level, and asks a follow-up question when the description is not '
    'enough. Always confirm the final classification with customs or your clearing agent.</p>' % (NLINES, TARIFF_FY))

INTRO_BROWSE = (
    '<p>Browse the Nepal Customs Tariff %s (%s) the way it is printed: 21 sections, 97 chapters, headings and %s '
    '8-digit lines, with the section and chapter legal notes, the General Rules of Interpretation and the export '
    'duty schedule. A crawlable version of every chapter is at <a href="/tariff">/tariff</a>.</p>'
    % (TARIFF_FY, TARIFF_FY_AD, NLINES))

# route -> (section id, title, description, h1 text or None to keep, intro html or '')
ROUTES = {
    '/calculator': ('v-calc', 'Nepal Import Duty & Landed Cost Calculator %s | Customs Nepal' % TARIFF_FY,
                    'Calculate Nepal customs duty, excise, 13%% VAT and total landed cost for any HS code under the '
                    'Customs Tariff %s (%s). SAARC/SAFTA rates and per-unit duties included. Free.' % (TARIFF_FY, TARIFF_FY_AD),
                    'Nepal import duty &amp; landed-cost calculator', INTRO_CALC, 'Calculator'),
    '/imports': ('v-imports', 'Nepal Imports FY %s — by Product & Country | Customs Nepal' % FY,
                 'Nepal imported %s of goods in FY %s. Top imported products, source countries and categories from '
                 'Department of Customs trade statistics, with duty for each product.' % (rsf(IMP), FY),
                 'Nepal imports — FY %s' % esc(FY), INTRO_IMPORTS, 'Imports'),
    '/exports': ('v-exports', 'Nepal Exports FY %s — by Product & Destination | Customs Nepal' % FY,
                 'Nepal exported %s of goods in FY %s. Top export products and destination countries from '
                 'Department of Customs trade statistics, with multi-year trends.' % (rsf(EXP), FY),
                 'Nepal exports — FY %s' % esc(FY), INTRO_EXPORTS, 'Exports'),
    '/trade-data': ('v-stats', 'Nepal Foreign Trade Statistics FY %s — Imports & Exports | Customs Nepal' % FY,
                    'Nepal foreign trade data from the Department of Customs: imports %s, exports %s in FY %s; '
                    'products, countries, customs points and trends since FY %s.' % (rsf(IMP), rsf(EXP), FY, S['history']['years'][0]),
                    None, INTRO_TRADE, 'Trade data'),
    '/ask-ai': ('v-ai', 'Ask AI — Find the Nepal HS Code for Any Product | Customs Nepal',
                'Describe your product in English or Nepali and get the likely Nepal HS codes from the Customs Tariff '
                '%s, ranked with reasons. Free AI HS-code classifier.' % TARIFF_FY,
                'Find the Nepal HS code with AI', INTRO_AI, 'Ask AI'),
    '/browse': ('v-browse', 'Browse the Nepal Customs Tariff %s by Section & Chapter | Customs Nepal' % TARIFF_FY,
                'Browse the Nepal Customs Tariff %s (%s): sections, chapters, headings and all %s HS code lines, with '
                'legal notes and the export duty schedule.' % (TARIFF_FY, TARIFF_FY_AD, NLINES),
                'Browse the Nepal Customs Tariff %s' % TARIFF_FY, INTRO_BROWSE, 'Browse'),
    '/about': ('v-about', 'About Customs Nepal — Nepal HS Code, Customs Tariff & Trade Portal',
               'Customs Nepal is a free, independent reference for Nepal HS codes, the Customs Tariff %s, import duty, '
               'landed cost and trade statistics. Data sources and how the site works.' % TARIFF_FY,
               None, '', 'About'),
    '/privacy': ('v-privacy', 'Privacy Policy | Customs Nepal',
                 'How Customs Nepal handles data: no server database, drafts stay in your browser, cookieless and GA4 '
                 'analytics, and what is sent to the AI provider.', None, '', 'Privacy'),
}

INTRO_CSS = ('<style>.route-intro{margin:0 0 var(--s4,24px);font-size:.95rem;line-height:1.55;max-width:72ch}'
             '.route-intro ul,.route-intro ol{padding-left:1.25em;margin:.4em 0}.route-intro p{margin:.5em 0}'
             '.route-intro a{color:var(--accent);text-decoration:none}.route-intro a:hover{text-decoration:underline}'
             '.hero .hero-h{margin:0 0 var(--s2);font-size:clamp(1.6rem,6vw,2.3rem);line-height:1.12;'
             'letter-spacing:-.03em;font-weight:800;text-wrap:balance;max-width:20ch}</style>')


def sub_one(s, pattern, repl, flags=0):
    new, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        sys.exit('app_pages: pattern not found: %s' % pattern)
    return new


def build(path, sec, title, desc, h1, intro, crumb):
    s = BASE
    url = SITE + path
    t, d = esc(title), esc(desc)
    s = sub_one(s, r'<title>[^<]*</title>', '<title>' + t + '</title>')
    s = sub_one(s, r'<meta name="description" content="[^"]*">', '<meta name="description" content="' + d + '">')
    s = sub_one(s, r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="' + url + '">')
    s = sub_one(s, r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="' + t + '">')
    s = sub_one(s, r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + d + '">')
    s = sub_one(s, r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="' + url + '">')
    s = sub_one(s, r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="' + t + '">')
    s = sub_one(s, r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="' + d + '">')
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": crumb, "item": url}]}
    s = sub_one(s, r'<script type="application/ld\+json">.*?</script>',
                lambda m: '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>', re.S)
    s = s.replace('</head>', INTRO_CSS + '</head>', 1)
    # server-side initial view: route section visible, search hero hidden, single <h1>
    s = sub_one(s, r'<section id="v-search">', '<section id="v-search" hidden>')
    s = sub_one(s, r'<h1>What are you importing into Nepal\?</h1>', '<h2 class="hero-h">What are you importing into Nepal?</h2>')
    s = sub_one(s, r'<section id="%s" hidden>' % sec, '<section id="%s">' % sec)
    i = s.index('<section id="%s">' % sec)
    head = s[i:]
    if sec == 'v-browse':
        # the browse section is rendered entirely by JS: give it a server-rendered heading + intro
        body = ('<div class="page-h"><h1>%s</h1></div><div class="route-intro">%s</div>' % (h1, intro))
        head = head.replace('<section id="v-browse"></section>', '<section id="v-browse">' + body + '</section>', 1)
    else:
        m = re.search(r'<div class="page-h">\s*<h2([^>]*)>(.*?)</h2>', head, re.S)
        if not m:
            sys.exit('app_pages: no page heading in %s' % sec)
        new_h = '<div class="page-h"><h1%s>%s</h1>' % (m.group(1), h1 if h1 else m.group(2))
        head = head[:m.start()] + new_h + head[m.end():]
        if intro:
            j = head.index('</div>', head.index('<div class="page-h">')) + len('</div>')
            head = head[:j] + '<div class="route-intro">' + intro + '</div>' + head[j:]
    s = s[:i] + head
    assert s.count('<h1') == BASE.count('<h1'), (path, s.count('<h1'))  # hero <h1> swapped for the route's
    (pub / (path.strip('/') + '.html')).write_text(s, encoding='utf-8')
    return path


paths = [build(p, *v) for p, v in ROUTES.items()]

# sitemap: these routes now have their own HTML, so they belong in it (seo_pages.py no longer lists them)
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
pri = {'/calculator': '0.9', '/imports': '0.8', '/exports': '0.8', '/trade-data': '0.7', '/ask-ai': '0.7',
       '/browse': '0.6', '/about': '0.5', '/privacy': '0.3'}
rows = ['  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>'
        % (SITE, p, TODAY, 'yearly' if p == '/privacy' else 'monthly', pri[p]) for p in paths if (SITE + p + '<') not in sm]
sm = sm.replace('</urlset>', '\n'.join(rows) + '\n</urlset>')
sm_path.write_text(sm, encoding='utf-8')
print('app_pages: %d static app-route pages (%s); +%d sitemap URLs' % (len(paths), ', '.join(paths), len(rows)))
