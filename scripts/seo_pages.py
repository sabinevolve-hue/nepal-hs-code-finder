"""Phase 3 SEO: generate real, crawlable static content pages from the tariff data.

Emits (into public/, served statically by Vercel with cleanUrls):
  /seo.css                      shared, on-brand stylesheet (cached across pages)
  /tariff        (tariff.html)  index of all sections -> chapters
  /tariff/<NN>   (tariff/NN.html) one page per chapter: every HS line + duty, chapter notes
and rewrites public/sitemap.xml to include the homepage + /tariff + every chapter.

These pages are lightweight (they do NOT load the 2.9 MB app bundle); each HS code links
into the app's detail view (/#hs-<code>) so users can go interactive. Design mirrors the
app (navy, system font stack, light/dark) but is self-contained. No change to the app itself.

Run after assemble.py:  python3 scripts/seo_pages.py
"""
import pathlib, json, re, datetime, html

root = pathlib.Path(__file__).resolve().parents[1]
D = json.loads((root / 'data' / 'tariff.json').read_text(encoding='utf-8'))
pub = root / 'public'
(pub / 'tariff').mkdir(parents=True, exist_ok=True)

SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()
YEAR = '2026/27'

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

# ---- rate formatting (mirrors the app's num()/pct()) ----
def num(v):
    if v is None or v == '':
        return None
    if str(v).strip().lower() == 'free':
        return 0.0
    try:
        return float(v)
    except ValueError:
        return None

def pct(v):
    n = num(v)
    if n is None:
        return esc(v) if v else 'Not stated'
    if n == 0:
        return 'Free'
    return (str(int(n)) if n == int(n) else str(n)) + '%'

def duty_cls(v):
    n = num(v)
    if n is None:
        return 'd-spec'
    return 'd-free' if n == 0 else 'd-low' if n <= 10 else 'd-mid' if n <= 20 else 'd-hi'

def label(desc, path):
    if not path or not re.match(r'^other\b', desc or '', re.I):
        return desc
    for p in reversed(path):
        if p and not re.match(r'^other$', p, re.I):
            return p + ' — ' + desc
    return desc

# ---- build chapter -> rows, grouped by heading ----
chapters = D['chapters']          # {'1': {t,s,n,pg}, ...}
heads = D['heads']                # {'01.01': [title, ch], ...}
sections = D['sections']          # [{n,t,f,notes}, ...]
strs = D['strs']

by_ch = {}
for r in D['rows']:
    code, desc, pids, unit, saarc, gen = r[0], r[1], r[2], r[3], r[4], r[5]
    ch = int(code[:2])
    h = code[:2] + '.' + code[2:4]
    path = [strs[p] for p in pids]
    by_ch.setdefault(ch, []).append({'code': code, 'desc': desc, 'path': path,
                                     'unit': unit, 's': saarc, 'g': gen, 'h': h})

def section_of(ch):
    s = None
    for x in sections:
        if x['f'] <= ch:
            s = x
    return s

CHAPTERS = sorted(by_ch.keys())

# ---- shared stylesheet ----
CSS = """
:root{--bg:#F8FAFC;--card:#fff;--fg:#0B1220;--fg2:#334155;--muted:#5B6878;--border:#E2E8F0;
--navy:#293C55;--accent:#5470C6;--accent-bg:#E8EDFA;--free:#15803D;--free-bg:#DCFCE7;--low:#0369A1;--low-bg:#E0F0FA;
--mid:#A15C07;--mid-bg:#FEF3C7;--hi:#B91C1C;--hi-bg:#FEE2E2;--spec:#475569;--spec-bg:#EEF2F6;
--f:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,system-ui,sans-serif;
--mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}
@media(prefers-color-scheme:dark){:root{--bg:#0B1120;--card:#131C2E;--fg:#F1F5F9;--fg2:#CBD5E1;--muted:#94A3B8;--border:#243047;
--navy:#E2E8F0;--accent:#7A93E6;--accent-bg:#1C2743;--free:#4ADE80;--free-bg:#0F2E1C;--low:#38BDF8;--low-bg:#0C2A40;
--mid:#FBBF24;--mid-bg:#33260A;--hi:#F87171;--hi-bg:#3A1414;--spec:#94A3B8;--spec-bg:#1A2436;color-scheme:dark}}
*{box-sizing:border-box}
html,body{overflow-x:hidden}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--f);line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:900px;margin:0 auto;padding:0 16px}
header.top{background:var(--navy);color:#fff}
@media(prefers-color-scheme:dark){header.top{background:#0B1428}}
header.top .wrap{display:flex;align-items:center;gap:10px;height:52px}
header.top .wrap.topbar{gap:14px}
.topnav{display:flex;gap:2px;margin-left:auto;overflow-x:auto;-webkit-overflow-scrolling:touch}
.topnav a{color:rgba(255,255,255,.82);font-size:.85rem;font-weight:600;padding:7px 11px;border-radius:8px;white-space:nowrap}
.topnav a:hover{background:rgba(255,255,255,.12);color:#fff;text-decoration:none}
.topnav a.cur{background:rgba(255,255,255,.16);color:#fff}
.logo{display:inline-flex;align-items:center;gap:8px;color:#fff;font-weight:700}
.logo b{background:#0F172A;color:#fff;font-family:var(--mono);font-size:12px;font-weight:700;padding:4px 6px;border-radius:6px}
@media(prefers-color-scheme:dark){header.top .logo{color:#F1F5F9}}
.crumb{font-size:.82rem;color:var(--muted);padding:12px 0 0}
.crumb a{color:var(--muted)}
h1{font-size:1.6rem;letter-spacing:-.02em;margin:.4em 0 .2em}
h2.sec{font-size:1.15rem;letter-spacing:-.01em;margin:1.6em 0 .4em;padding-bottom:.3em;border-bottom:1px solid var(--border)}
h3.head{font-size:.95rem;color:var(--fg2);margin:1.4em 0 .5em;font-family:var(--mono)}
.lede{color:var(--fg2);font-size:1.02rem;max-width:70ch}
.tools{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:9px 14px;border-radius:9px;font-weight:600;font-size:.9rem}
.btn.ghost{background:var(--accent-bg);color:var(--accent)}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.3em 0 1em}
.tbl{width:100%;border-collapse:collapse;font-size:.9rem;min-width:540px}
.tbl th,.tbl td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
.tbl th{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}
.tbl td.code{font-family:var(--mono);white-space:nowrap;font-size:.85rem}
.tbl td.unit{color:var(--muted);white-space:nowrap}
.duty{display:inline-block;font-weight:700;font-size:.8rem;padding:2px 7px;border-radius:6px;white-space:nowrap}
.d-free{background:var(--free-bg);color:var(--free)}.d-low{background:var(--low-bg);color:var(--low)}
.d-mid{background:var(--mid-bg);color:var(--mid)}.d-hi{background:var(--hi-bg);color:var(--hi)}.d-spec{background:var(--spec-bg);color:var(--spec)}
.note{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin:1em 0;font-size:.9rem;color:var(--fg2);white-space:pre-wrap}
.note summary{cursor:pointer;font-weight:600;color:var(--fg)}
.chgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin:.6em 0 1.4em}
.chcard{display:block;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;color:var(--fg)}
.chcard:hover{border-color:var(--accent);text-decoration:none}
.chcard .n{font-family:var(--mono);font-size:.75rem;color:var(--muted)}
.chcard .t{font-weight:600;display:block;margin-top:2px}
.chcard .c{font-size:.78rem;color:var(--muted)}
.pager{display:flex;justify-content:space-between;gap:10px;margin:1.6em 0;font-size:.9rem}
footer{border-top:1px solid var(--border);margin-top:2em;padding:20px 0 40px;color:var(--muted);font-size:.82rem}
footer a{color:var(--muted)}
"""

# ---- guarded analytics (same as assemble.py: live domain only) ----
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")

def page_head(title, desc, path, breadcrumb):
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                               **({"item": SITE + b[1]} if b[1] else {})}
                              for i, b in enumerate(breadcrumb)]}
    ldj = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
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
        '<script type="application/ld+json">' + ldj + '</script>'
        + ANALYTICS +
        '</head><body>'
        '<header class="top"><div class="wrap topbar">'
        '<a class="logo" href="/"><b>HS</b> Customs Nepal</a>'
        '<nav class="topnav">'
        '<a href="/">Search</a>'
        '<a href="/#ai">Ask AI</a>'
        '<a href="/#stats">Trade data</a>'
        '<a href="/tariff" class="cur">Tariff</a>'
        '<a href="/#calc">Calculator</a>'
        '<a href="/#invoice">Invoice</a>'
        '</nav></div></header>'
        '<div class="wrap">'
    )

def crumb_html(breadcrumb):
    parts = []
    for name, p in breadcrumb:
        if p:
            parts.append('<a href="' + p + '">' + esc(name) + '</a>')
        else:
            parts.append(esc(name))
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'

FOOT = ('<footer><div class="wrap"><p><b>Source:</b> Government of Nepal, Department of Customs, '
        'Customs Tariff ' + YEAR + ' (HS 2022 nomenclature). Duty rates as printed. This is a search aid and '
        'estimate, not an official classification or customs assessment — confirm the final HS code and taxes '
        'with the customs office or your clearing agent.</p>'
        '<p><a href="/">Home</a> · <a href="/tariff">All chapters</a> · '
        '<a href="/#calc">Duty calculator</a> · <a href="/#ai">Ask AI</a> · © customsnepal.com</p></div></footer>'
        '</body></html>')

# ---- chapter pages ----
for idx, ch in enumerate(CHAPTERS):
    rows = by_ch[ch]
    meta = chapters.get(str(ch), {})
    ctitle = meta.get('t', 'Chapter %d' % ch)
    notes = meta.get('n', '')
    sec = section_of(ch)
    nn = '%02d' % ch
    path = '/tariff/' + nn
    title = 'Chapter %s: %s — HS Codes & Customs Duty | Nepal Tariff %s' % (nn, ctitle, YEAR)
    if len(title) > 68:
        title = 'Ch %s %s — HS Codes & Duty | Customs Nepal' % (nn, ctitle)
    desc = ('Nepal customs import duty and HS codes for %s (Chapter %s, Customs Tariff %s). %d tariff lines '
            'with general and SAARC duty rates and units.' % (ctitle, nn, YEAR, len(rows)))
    bc = [('Home', '/'), ('Tariff ' + YEAR, '/tariff')]
    if sec:
        bc.append(('Section ' + sec['n'], '/tariff'))
    bc.append(('Chapter ' + nn, ''))

    out = [page_head(title, desc, path, bc), crumb_html(bc)]
    out.append('<h1>Chapter %s — %s</h1>' % (nn, esc(ctitle)))
    out.append('<p class="lede">Nepal Customs Tariff %s import duty rates and %d HS code lines for '
               '<b>%s</b>%s. Each code shows the general and SAARC customs duty; tap a code to open the '
               'full breakdown and landed-cost estimate.</p>'
               % (YEAR, len(rows), esc(ctitle), (' (Section %s — %s)' % (sec['n'], esc(sec['t'])) if sec else '')))
    out.append('<div class="tools"><a class="btn" href="/">Search all HS codes</a>'
               '<a class="btn ghost" href="/#calc">Import duty calculator</a></div>')

    # group by heading
    seen = []
    groups = {}
    for r in rows:
        if r['h'] not in groups:
            groups[r['h']] = []
            seen.append(r['h'])
        groups[r['h']].append(r)
    for h in seen:
        htitle = heads.get(h, ['', 0])[0]
        out.append('<h3 class="head">%s — %s</h3>' % (esc(h), esc(htitle)))
        out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>HS code</th><th>Description</th><th>Unit</th>'
                   '<th>General duty</th><th>SAARC duty</th></tr></thead><tbody>')
        for r in groups[h]:
            lab = label(r['desc'], r['path'])
            out.append('<tr><td class="code"><a href="/#hs-%s">%s</a></td><td>%s</td><td class="unit">%s</td>'
                       '<td><span class="duty %s">%s</span></td><td><span class="duty %s">%s</span></td></tr>'
                       % (esc(r['code']), esc(r['code']), esc(lab), esc(r['unit'] or '—'),
                          duty_cls(r['g']), pct(r['g']), duty_cls(r['s']), pct(r['s'])))
        out.append('</tbody></table></div>')

    if notes:
        out.append('<details class="note"><summary>Chapter %s legal notes</summary>\n%s</details>' % (nn, esc(notes)))

    # pager
    prev_ch = CHAPTERS[idx - 1] if idx > 0 else None
    next_ch = CHAPTERS[idx + 1] if idx < len(CHAPTERS) - 1 else None
    pg = '<div class="pager">'
    pg += ('<a href="/tariff/%02d">← Chapter %02d: %s</a>' % (prev_ch, prev_ch, esc(chapters.get(str(prev_ch), {}).get('t', ''))) if prev_ch else '<span></span>')
    pg += ('<a href="/tariff/%02d">Chapter %02d: %s →</a>' % (next_ch, next_ch, esc(chapters.get(str(next_ch), {}).get('t', ''))) if next_ch else '<span></span>')
    pg += '</div>'
    out.append(pg)
    out.append('<p><a href="/tariff">← All chapters of the Nepal Customs Tariff %s</a></p>' % YEAR)
    out.append('</div>' + FOOT)
    (pub / 'tariff' / (nn + '.html')).write_text(''.join(out), encoding='utf-8')

# ---- tariff index ----
title = 'Nepal Customs Tariff %s — All Chapters & HS Codes | Customs Nepal' % YEAR
desc = ('Browse the full Nepal Customs Tariff %s by chapter: HS codes, general and SAARC import duty for all '
        '%d chapters and %d tariff lines. Free search, duty calculator and AI classifier.'
        % (YEAR, len(CHAPTERS), len(D['rows'])))
bc = [('Home', '/'), ('Tariff ' + YEAR, '')]
out = [page_head(title, desc, '/tariff', bc), crumb_html(bc)]
out.append('<h1>Nepal Customs Tariff %s — all chapters</h1>' % YEAR)
out.append('<p class="lede">Every chapter of the Nepal Customs Tariff %s (HS 2022), with %s HS code lines and '
           'their general and SAARC import duty. Pick a chapter, or search any product on the '
           '<a href="/">home page</a>.</p>' % (YEAR, format(len(D['rows']), ',')))
out.append('<div class="tools"><a class="btn" href="/">Search by product or code</a>'
           '<a class="btn ghost" href="/#calc">Duty & landed-cost calculator</a></div>')
for sec in sections:
    sec_chs = [c for c in CHAPTERS if section_of(c) is sec]
    if not sec_chs:
        continue
    out.append('<h2 class="sec">Section %s — %s</h2>' % (esc(sec['n']), esc(sec['t'])))
    out.append('<div class="chgrid">')
    for c in sec_chs:
        nn = '%02d' % c
        ct = chapters.get(str(c), {}).get('t', '')
        out.append('<a class="chcard" href="/tariff/%s"><span class="n">Chapter %s</span>'
                   '<span class="t">%s</span><span class="c">%d HS codes</span></a>'
                   % (nn, nn, esc(ct), len(by_ch[c])))
    out.append('</div>')
out.append('</div>' + FOOT)
(pub / 'tariff.html').write_text(''.join(out), encoding='utf-8')

# ---- shared stylesheet ----
(pub / 'seo.css').write_text(CSS.strip(), encoding='utf-8')

# ---- sitemap (homepage + tariff index + every chapter) ----
urls = [(SITE + '/', '1.0', 'weekly'), (SITE + '/tariff', '0.9', 'monthly')]
for ch in CHAPTERS:
    urls.append((SITE + '/tariff/%02d' % ch, '0.7', 'monthly'))
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, pr, cf in urls:
    sm.append('  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>'
              % (loc, TODAY, cf, pr))
sm.append('</urlset>')
(pub / 'sitemap.xml').write_text('\n'.join(sm) + '\n', encoding='utf-8')

print('seo_pages: %d chapter pages + tariff index + seo.css; sitemap has %d URLs' % (len(CHAPTERS), len(urls)))
