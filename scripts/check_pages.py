"""Build-time QA for the generated site. Exits non-zero (fails `npm run build`) on any problem.

1. /import-duty product pages: re-reads the RENDERED HTML and checks that
   * the country rows never add up to more than the product's import total
     (allowing for the rounding of the displayed figures), and no single country exceeds it;
   * the "All countries" row equals the total in the text;
   * the total matches data/stats.json for that HS code;
   * the duty-source footer names the tariff year the data actually is.
2. Every sitemap URL is a real page (its own file, not the SPA fallback) whose canonical is itself.
3. Internal links on generated pages resolve to a real file, an SPA route, or a known rewrite —
   unknown paths return 404, so a broken link would be a real 404.
4. Links to https://world.customsnepal.com/... resolve to a prerendered page in world/, and every generated page
   with a footer carries the "Our other sites" block (world.customsnepal.com + nepalpublicdata.com).

Run last:  python3 scripts/check_pages.py
"""
import pathlib, re, json, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from statsfields import IMP_VALUE, TARIFF_FY

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
SITE = 'https://www.customsnepal.com'
S = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
errors = []

UNITS = {'Arab': 1e9, 'Crore': 1e7, 'Lakh': 1e5}


def money(s):
    """'Rs 8.78 Arab' -> (low, high) in rupees, given the display rounding."""
    s = re.sub(r'<[^>]+>', '', s).strip()
    m = re.match(r'Rs ([\d,]+(?:\.(\d+))?)(?: (Arab|Crore|Lakh))?$', s)
    if not m:
        return None
    x = float(m.group(1).replace(',', ''))
    dec = len(m.group(2) or '')
    mul = UNITS.get(m.group(3), 1.0)
    half = 0.5 * 10 ** (-dec) * mul
    return (x * mul - half, x * mul + half)


# ---------------- 1. import-duty pages ----------------
pages = sorted((pub / 'import-duty').glob('*.html'))
n_rows = 0
for f in pages:
    h = f.read_text(encoding='utf-8')
    code = re.search(r'-(\d{8})\.html$', f.name).group(1)
    m = re.search(r'Nepal imported about <b>(Rs [^<]+)</b>', h)
    if not m:
        errors.append('%s: no import total' % f.name); continue
    tot = money(m.group(1))
    exp = float(S['imports'][code][IMP_VALUE]) * 1000 if code in S['imports'] else None
    if exp is None or not (tot[0] - 1 <= exp <= tot[1] + 1):
        errors.append('%s: total %s does not match stats.json value %s' % (f.name, m.group(1), exp))
    tbl = re.search(r'<th>Source country</th>.*?<tbody>(.*?)</tbody>', h, re.S)
    if tbl:
        lo_sum = 0.0
        for name, val, cls in [(a, b, c) for c, a, b in re.findall(r'<tr(?: class="(\w+)")?><td>(.*?)</td><td>(.*?)</td></tr>', tbl.group(1))]:
            r = money(val)
            if r is None:
                errors.append('%s: unparsable value %r' % (f.name, val)); continue
            if cls == 'total':
                if not (r[0] <= tot[1] and tot[0] <= r[1]):
                    errors.append('%s: "All countries" %s != total %s' % (f.name, val, m.group(1)))
                continue
            n_rows += 1
            if r[0] > tot[1]:
                errors.append('%s: %s alone (%s) exceeds the total %s' % (f.name, re.sub('<[^>]+>', '', name), val, m.group(1)))
            lo_sum += r[0]
        if lo_sum > tot[1] * 1.001:
            errors.append('%s: country rows sum to >= Rs %.0f, more than the total %s' % (f.name, lo_sum, m.group(1)))
    if ('Nepal Customs Tariff %s' % TARIFF_FY) not in h:
        errors.append('%s: footer does not cite Nepal Customs Tariff %s' % (f.name, TARIFF_FY))

# ---------------- 2. sitemap -> real pages with self-canonical ----------------
sm = (pub / 'sitemap.xml').read_text(encoding='utf-8')
locs = re.findall(r'<loc>([^<]+)</loc>', sm)
if len(locs) != len(set(locs)):
    errors.append('sitemap: %d duplicate URLs' % (len(locs) - len(set(locs))))


def file_for(path):
    if path == '/':
        return pub / 'index.html'
    p = path.strip('/')
    for cand in (pub / (p + '.html'), pub / p / 'index.html'):
        if cand.is_file():
            return cand
    return None


for loc in set(locs):
    if not loc.startswith(SITE):
        errors.append('sitemap: foreign URL %s' % loc); continue
    path = loc[len(SITE):] or '/'
    if path.startswith('/world'):
        continue                                  # world build is mounted & checked by its own scripts
    f = file_for(path)
    if not f:
        errors.append('sitemap: %s has no page of its own (would be a 404 / SPA fallback)' % path); continue
    m = re.search(r'<link rel="canonical" href="([^"]+)"', f.read_text(encoding='utf-8'))
    if not m or m.group(1) != loc:
        errors.append('sitemap: %s canonical is %s' % (path, m.group(1) if m else None))

# ---------------- 3. internal links ----------------
# SPA routes = the explicit app-route rewrite in vercel.json (everything else with no file is a 404)
VJ = json.loads((root / 'vercel.json').read_text(encoding='utf-8'))
SPA = {'/'}
for rw in VJ.get('rewrites', []):
    m = re.fullmatch(r'/\(([a-z|-]+)\)', rw['source'])
    if m and rw['destination'] == '/':
        SPA |= {'/' + x for x in m.group(1).split('|')}
src_paths = re.findall(r"PATHS = \{([^}]*)\}", (root / 'src.html').read_text(encoding='utf-8'))
for k in re.findall(r"'(/[a-z-]*)'", src_paths[0] if src_paths else ''):
    if k not in SPA and k != '/index.html' and not file_for(k):
        errors.append('vercel.json: SPA route %s (src.html PATHS) has no rewrite and no file' % k)
bad_links = {}
for f in [pub / 'index.html'] + sorted(p for p in pub.rglob('*.html') if 'world' not in p.parts):
    for href in set(re.findall(r'href="(/[^"#?]*)', f.read_text(encoding='utf-8'))):
        if href.startswith('//') or href in SPA or href.startswith(('/world', '/api/', '/_vercel/')):
            continue
        if file_for(href) or (pub / href.lstrip('/')).is_file():
            continue
        bad_links.setdefault(href, []).append(str(f.relative_to(pub)))
for href, where in sorted(bad_links.items()):
    errors.append('broken internal link %s (on %d pages, e.g. %s)' % (href, len(where), where[0]))

# ---------------- 4. links to world.customsnepal.com + "Our other sites" footer ----------------
# Links into the world subdomain must hit a prerendered page in world/ (unknown world URLs are real 404s).
WORLD_SITE = 'https://world.customsnepal.com'
wdir = root / 'world'
bad_world, no_block = {}, []
for f in [pub / 'index.html'] + sorted(p for p in pub.rglob('*.html') if 'world' not in p.parts):
    h = f.read_text(encoding='utf-8')
    for href in set(re.findall(r'href="' + re.escape(WORLD_SITE) + r'(/[^"#?]*)', h)):
        p = href.rstrip('/')
        if not (p == '' or (wdir / (p.lstrip('/') + '.html')).is_file() or (wdir / p.lstrip('/')).is_file()):
            bad_world.setdefault(href, []).append(str(f.relative_to(pub)))
    if '<footer' in h and not ('href="%s/"' % WORLD_SITE in h and 'href="https://nepalpublicdata.com/"' in h and 'Our other sites' in h):
        no_block.append(str(f.relative_to(pub)))
for href, where in sorted(bad_world.items()):
    errors.append('broken link %s%s (on %d pages, e.g. %s)' % (WORLD_SITE, href, len(where), where[0]))
if no_block:
    errors.append('%d page(s) with a footer but no "Our other sites" block, e.g. %s' % (len(no_block), no_block[0]))

print('check_pages: %d import-duty pages (%d country rows), %d sitemap URLs, links checked'
      % (len(pages), n_rows, len(set(locs))))
if errors:
    print('check_pages: FAILED — %d problem(s):' % len(errors))
    for e in errors[:80]:
        print('  ' + e)
    sys.exit(1)
print('check_pages: OK')
