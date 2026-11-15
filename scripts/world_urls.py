#!/usr/bin/env python3
"""Addresses for country pages on world.customsnepal.com: the full country name instead of the ISO code.

  /trade/vnm             -> /trade/vietnam
  /trade/vnm/2023        -> /trade/vietnam/2023
  /trade/vnm/exports/851713 -> /trade/vietnam/exports/851713

Country pairs keep their codes (/trade/chn/usa). The generators still write ISO-coded paths; world_prerender.py passes
every finished page through nice_html() and files it under nice_path(), so there is one place where the mapping lives.
Old addresses redirect permanently (see write_vercel_json in world_prerender.py).
"""
import json, pathlib, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
OVERRIDE = {'MAC': 'macao', 'SOM': 'somalia', 'BHS': 'bahamas', 'PRK': 'north-korea', 'GMB': 'gambia', 'YEM': 'yemen',
            'SXM': 'sint-maarten', 'MAF': 'saint-martin', 'FSM': 'micronesia'}
RESERVED = {'pairs', 'region', 'product', 'sanctions'}


def _slug(name):
    n = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower().replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', n).strip('-')


def load():
    """{ISO3: slug} for every economy in world/data/trade.json."""
    cs = json.loads((ROOT / 'world' / 'data' / 'trade.json').read_text(encoding='utf-8'))['countries']
    out = {c['iso']: OVERRIDE.get(c['iso']) or _slug(c['name']) for c in cs}
    assert len(set(out.values())) == len(out), 'two economies share an address name'
    assert not any(len(v) <= 3 or v in RESERVED for v in out.values()), 'an address name clashes with a code or a section'
    return out


SLUG = load()
_RX = re.compile(r'((?:https://world\.customsnepal\.com)?/trade/)([a-z]{3})((?:/\d{4}|/exports/\d{6})?)(?=["\'<\s?#])')
_PX = re.compile(r'^/trade/([a-z]{3})((?:/\d{4}|/exports/\d{6})?)$')


def href(iso):
    return '/trade/' + SLUG.get(iso.upper(), iso.lower())


def nice_path(p):
    m = _PX.match(p)
    return '/trade/' + SLUG[m[1].upper()] + m[2] if m and m[1].upper() in SLUG else p


def nice_html(s):
    return _RX.sub(lambda m: m[1] + SLUG[m[2].upper()] + m[3] if m[2].upper() in SLUG else m[0], s)
