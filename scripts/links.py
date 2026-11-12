"""Internal-link index shared by every main-site generator (stdlib only).

Two families of pages are only useful if the rest of the site points at them:

  /trade-partner/<slug>   one page per trading partner   (country_pages.py)
  /import-duty/<name>     consumer-name duty pages        (alias_pages.py)

This module answers "is there a page for this country / this HS code?" so any
generator can link to them without knowing how the slugs are made, and builds
the "Explore" footer block that nav.OTHER_SITES carries onto every page.

Relative links only — never import this from world_prerender.py (other host).
"""
import json, pathlib, re

_root = pathlib.Path(__file__).resolve().parents[1]


def _slug(name):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')


# ---------- trading partners ----------
_C = json.loads((_root / 'world/data/country.json').read_text(encoding='utf-8'))
_PARTNER = {}          # lower-cased country name (any known spelling) -> iso
PARTNER_PAGE = {}      # iso -> (href, display name, flag)
for _iso in _C['order']:
    _c = _C['countries'][_iso]
    if 'impP' not in _c:
        continue
    PARTNER_PAGE[_iso] = ('/trade-partner/' + _slug(_c['name']), _c['name'], _c.get('flag', ''))
    for _n in [_c['name']] + _c.get('aka', []):
        _PARTNER[_n.strip().lower()] = _iso
TOP_PARTNERS = [i for i in _C['order'] if i in PARTNER_PAGE]


def partner_href(name):
    """'/trade-partner/<slug>' for a country name in any spelling the customs data uses, else None."""
    iso = _PARTNER.get(str(name or '').strip().lower())
    return PARTNER_PAGE[iso][0] if iso else None


def partner_link(name, esc):
    h = partner_href(name)
    return '<a href="%s">%s</a>' % (h, esc(name)) if h else esc(name)


# 7-year history pages (/trade/country/<slug>, trade_pages.py, from stats.json) keyed by iso
import unicodedata as _ud
def _tslug(n):
    n = _ud.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
# /trade/country/<slug> (trade_pages.py) is the older, plainer country page. Where a partner profile exists it
# REPLACES that page: trade_pages.py skips it, vercel.json 301s the old URL, and country_href() points links
# at the profile. Countries without a profile keep their /trade/country page.
_S = json.loads((_root / 'data/stats.json').read_text(encoding='utf-8'))
OLD_COUNTRY = {}        # '/trade/country/<slug>' -> '/trade-partner/<slug>'
LONG_HIST = {}          # iso -> [[imp, exp] per year in LONG_YEARS], summed over every spelling of the country
LONG_YEARS = _S.get('history', {}).get('years', [])
for _n, _h in _S.get('history', {}).get('countries', {}).items():
    _i = _PARTNER.get(str(_n).strip().lower())
    if not _i:
        continue
    OLD_COUNTRY['/trade/country/' + _tslug(_n)] = PARTNER_PAGE[_i][0]
    _a = LONG_HIST.setdefault(_i, [[0.0, 0.0] for _ in LONG_YEARS])
    for _k, _v in enumerate(_h[:len(LONG_YEARS)]):
        _a[_k][0] += float(_v[0] or 0); _a[_k][1] += float(_v[1] or 0)
for _row in _S['countries']:
    _i = _PARTNER.get(str(_row[0]).strip().lower())
    if _i:
        OLD_COUNTRY['/trade/country/' + _tslug(_row[0])] = PARTNER_PAGE[_i][0]


def country_href(name):
    """Best page for a country name: its partner profile if there is one, else the plain /trade/country page."""
    return partner_href(name) or ('/trade/country/' + _tslug(name))


# ---------- consumer-name duty pages ----------
def _alias_records():
    import sys
    sys.path.insert(0, str(_root / 'scripts'))
    from aliases import ALIASES
    rows = json.loads((_root / 'data/tariff.json').read_text(encoding='utf-8'))['rows']
    codes_all = [str(r[0]) for r in rows]
    is_np = lambda t: any('ऀ' <= ch <= 'ॿ' for ch in t)
    clean = lambda s: ' '.join(str(s or '').split()).strip(' .')
    used, recs = {}, []
    for s, codes in ALIASES:                       # same order + rules as alias_pages.py
        terms = [t.strip() for t in s.split(',') if t.strip()]
        if not any(c.startswith(p) for p in codes for c in codes_all):
            continue
        en = [clean(t) for t in terms if not is_np(t)]
        canonical = (en[0] if en else terms[0]).strip()
        slug = _slug(canonical) or _slug(codes[0])
        if slug in used:
            used[slug] += 1; slug = '%s-%d' % (slug, used[slug])
        else:
            used[slug] = 1
        recs.append((slug, canonical, list(codes)))
    return recs


ALIAS_RECS = _alias_records()
ALIAS_SLUGS = [r[0] for r in ALIAS_RECS]
_ALIAS_NAME = {r[0]: r[1] for r in ALIAS_RECS}


def alias_for(code):
    """Best consumer-name page for an HS code: (href, name) or None. Longest matching prefix wins."""
    d = re.sub(r'\D', '', str(code))[:8]
    if len(d) < 4:
        return None
    dotted = d[:4] + ('.' + d[4:6] if len(d) >= 6 else '') + ('.' + d[6:8] if len(d) >= 8 else '')
    best = None
    for slug, name, codes in ALIAS_RECS:
        for p in codes:
            if dotted.startswith(p) and (best is None or len(p) > best[0]):
                best = (len(p), slug, name)
    return ('/import-duty/' + best[1], best[2]) if best else None


def aliases_in_chapter(ch, n=8):
    ch = str(ch).zfill(2)
    out = []
    for slug, name, codes in ALIAS_RECS:
        if any(str(p)[:2] == ch for p in codes):
            out.append(('/import-duty/' + slug, name))
    return out[:n]


# ---------- who supplies a product (FTS, top-3 origins by import value) ----------
_SUPPLY = {}
for _c in _C['countries'].values():
    for _code, _v in _c.get('comp', {}).items():
        _SUPPLY.setdefault(re.sub(r'\D', '', _code)[:8], _v['t'])


def suppliers_for(code):
    """[(country name, href or None, share %)] for an 8-digit HS code, or []."""
    out = []
    for iso, pct in _SUPPLY.get(re.sub(r'\D', '', str(code))[:8], []):
        c = _C['countries'].get(iso)
        if c:
            out.append((c['name'], PARTNER_PAGE.get(iso, (None,))[0], pct))
    return out


# ---------- footer "Explore" block (carried by nav.OTHER_SITES onto every page) ----------
_POPULAR = [('mobile', 'Mobile phone'), ('laptop', 'Laptop'), ('tv', 'TV'), ('car', 'Car'),
            ('motorcycle', 'Motorcycle'), ('electric-vehicle', 'Electric vehicle'), ('gold', 'Gold'),
            ('solar-panel', 'Solar panel'), ('refrigerator', 'Refrigerator'), ('air-conditioner', 'Air conditioner'),
            ('cement', 'Cement'), ('cosmetics', 'Cosmetics')]


def explore_footer():
    part = ' · '.join('<a href="%s">%s</a>' % (PARTNER_PAGE[i][0], PARTNER_PAGE[i][1]) for i in TOP_PARTNERS[:8])
    duty = ' · '.join('<a href="/import-duty/%s">%s</a>' % (s, l) for s, l in _POPULAR if s in _ALIAS_NAME)
    return ('<p class="explore"><b>Nepal&rsquo;s trade by country:</b> ' + part +
            ' · <a href="/trade-partners">all %d trading partners</a> · <a href="/customs-offices">by customs office</a> · <a href="/compare">compare two countries</a> · <a href="/data">download the data</a></p>'
            '<p class="explore"><b>Import duty by product name:</b> ' + duty +
            ' · <a href="/import-duty#popular-names">all %d products</a></p>') % (len(PARTNER_PAGE), len(ALIAS_RECS))
