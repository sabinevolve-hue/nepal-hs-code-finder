"""Parse the official Dept. of Customs FTS workbook into a compact per-partner
dataset for the Nepal trade-partner pages.

OFFLINE / yearly refresh step (needs openpyxl, reads the committed .xlsx) — NOT
part of `npm run build`. Run it when a new FTS is dropped in, then commit the
JSON it writes; country_pages.py (stdlib only) reads that JSON at build time.

  Input : data/FTS_Annual_2081_82.xlsx  (Dept. of Customs, FY 2081/82 annual)
  Output: world/data/country.json

Run:  python3 scripts/world_country.py
"""
import pathlib, json, datetime
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
XLSX = ROOT / 'data' / 'FTS_Annual_2081_82.xlsx'
OUT = ROOT / 'world' / 'data' / 'country.json'
FY = '2081/82'
TOPN = 12          # top products kept per direction per partner
TOPCH = 8          # top chapters kept per direction per partner
PROD_MIN_TH = 100000.0   # keep product/chapter detail for partners whose total >= Rs 100M (value in Rs '000)

# ---- partner name -> ISO3 + flag, built from the world trade dataset + aliases ----
TRADE = json.loads((ROOT / 'world' / 'data' / 'trade.json').read_text(encoding='utf-8'))
NAME2ISO, ISO2FLAG = {}, {}
for c in TRADE['countries']:
    NAME2ISO[c['name'].lower()] = c['iso']
    ISO2FLAG[c['iso']] = c.get('flag', '')

ALIAS = {
    'united states': 'USA', 'u.s.a.': 'USA', 'usa': 'USA',
    'united arab emirates': 'ARE', 'uae': 'ARE',
    'korea, republic of': 'KOR', 'republic of korea': 'KOR', 'south korea': 'KOR',
    "korea, democratic people's republic of": 'PRK',
    'viet nam': 'VNM', 'vietnam': 'VNM',
    'russia': 'RUS', 'russian federation': 'RUS',
    'turkey': 'TUR', 'türkiye': 'TUR', 'turkiye': 'TUR',
    'hong kong': 'HKG', 'hong kong, china': 'HKG',
    'taiwan': 'TWN', 'taiwan, province of china': 'TWN', 'chinese taipei': 'TWN',
    'czech republic': 'CZE', 'czechia': 'CZE',
    'slovak republic': 'SVK', 'slovakia': 'SVK',
    "lao people's democratic republic": 'LAO', 'laos': 'LAO',
    'brunei darussalam': 'BRN',
    'syrian arab republic': 'SYR', 'syria': 'SYR',
    'iran, islamic republic of': 'IRN', 'iran': 'IRN',
    'tanzania, united republic of': 'TZA', 'tanzania': 'TZA',
    'venezuela, bolivarian republic of': 'VEN', 'venezuela': 'VEN',
    'moldova, republic of': 'MDA', 'moldova': 'MDA',
    'bolivia, plurinational state of': 'BOL', 'bolivia': 'BOL',
    'congo, the democratic republic of the': 'COD', 'congo': 'COG',
    'macedonia, the former yugoslav republic of': 'MKD', 'north macedonia': 'MKD',
    'libyan arab jamahiriya': 'LBY', 'libya': 'LBY',
    'cote d ivoire': 'CIV', "cote d'ivoire": 'CIV', 'ivory coast': 'CIV',
    'palestinian territory, occupied': 'PSE', 'palestine': 'PSE',
    'myanmar': 'MMR', 'burma': 'MMR',
    'macao': 'MAC', 'macau': 'MAC',
    'united kingdom': 'GBR', 'great britain': 'GBR',
    'cape verde': 'CPV',
}
# iso3 -> iso2 for a flag fallback when the trade set lacks one
ISO3_2 = {'KOR':'KR','PRK':'KP','VNM':'VN','RUS':'RU','TUR':'TR','HKG':'HK','TWN':'TW','CZE':'CZ',
          'SVK':'SK','LAO':'LA','BRN':'BN','SYR':'SY','IRN':'IR','TZA':'TZ','VEN':'VE','MDA':'MD',
          'BOL':'BO','COD':'CD','COG':'CG','MKD':'MK','LBY':'LY','CIV':'CI','PSE':'PS','MMR':'MM',
          'MAC':'MO','GBR':'GB','CPV':'CV','ARE':'AE','USA':'US'}

def flag_for(iso):
    if iso in ISO2FLAG and ISO2FLAG[iso]:
        return ISO2FLAG[iso]
    i2 = ISO3_2.get(iso)
    if i2:
        return ''.join(chr(0x1F1E6 + ord(ch) - ord('A')) for ch in i2)
    return '\U0001F3F3'  # white flag fallback

SKIP = {'total', 'not_specified', 'not specified', 'others', 'other countries', ''}

def resolve(name):
    k = name.strip().lower()
    if k in SKIP:
        return None, ''
    iso = ALIAS.get(k) or NAME2ISO.get(k)
    if not iso:
        # loose: strip punctuation/words
        kk = k.replace('.', '').replace(',', '').strip()
        iso = ALIAS.get(kk) or NAME2ISO.get(kk)
    if not iso:
        return None, '\U0001F3F3'
    return iso, flag_for(iso)

def clean(s):
    return ' '.join(str(s or '').split()).strip(' .')

print('Loading workbook…')
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)

# ---- Sheet 1: headline totals + YoY ----
tot = {}
for r in wb['1_Trade_Direction'].iter_rows(min_row=4, values_only=True):
    lab = (r[1] or '').lower() if r[1] else ''
    if 'import' in lab and tot.get('imp') is None:
        tot['imp'] = float(r[3] or 0); tot['imp_yoy'] = float(r[4] or 0)
    elif 'export' in lab and tot.get('exp') is None:
        tot['exp'] = float(r[3] or 0); tot['exp_yoy'] = float(r[4] or 0)

# ---- Sheet 3: per-partner totals ----
countries = {}
for r in wb['3_Trade_Balance_Country'].iter_rows(min_row=4, values_only=True):
    if not r[1]:
        continue
    iso, flag = resolve(r[1])
    if iso is None:
        continue
    imp = float(r[2] or 0); exp = float(r[3] or 0)
    c = countries.setdefault(iso, {'name': clean(r[1]), 'iso': iso, 'flag': flag,
                                   'imp': 0.0, 'exp': 0.0, 'impP': {}, 'expP': {}, 'impC': {}, 'expC': {}})
    c['imp'] += imp; c['exp'] += exp
    # prefer a clean well-known name from the trade set
    tn = next((x['name'] for x in TRADE['countries'] if x['iso'] == iso), None)
    if tn:
        c['name'] = tn

def accumulate(sheet, pcol, vcol, pkey, ckey):
    """Aggregate a commodity×partner sheet into per-partner product + chapter sums."""
    for r in wb[sheet].iter_rows(min_row=4, values_only=True):
        code = r[0]
        if not code or not r[pcol]:
            continue
        iso, _ = resolve(r[pcol])
        if iso is None or iso not in countries:
            continue
        v = float(r[vcol] or 0)
        if v <= 0:
            continue
        code = str(code).strip()
        desc = clean(r[1])
        c = countries[iso]
        p = c[pkey]
        if code in p:
            p[code][1] += v
        else:
            p[code] = [desc, v]
        ch = code[:2]
        c[ckey][ch] = c[ckey].get(ch, 0.0) + v

print('Aggregating imports by partner…')
accumulate('4_Imports_By_Commodity_Partner', 2, 5, 'impP', 'impC')
print('Aggregating exports by partner…')
accumulate('6_Exports_By_Commodity_Partner', 2, 5, 'expP', 'expC')

# ---- finalise: trim to top-N, drop detail for tiny partners ----
out_countries = {}
for iso, c in countries.items():
    total = c['imp'] + c['exp']
    rec = {'name': c['name'], 'iso': iso, 'flag': c['flag'],
           'imp': round(c['imp'], 1), 'exp': round(c['exp'], 1)}
    if total >= PROD_MIN_TH:
        ip = sorted(([code, d[0], round(d[1], 1)] for code, d in c['impP'].items()), key=lambda x: -x[2])[:TOPN]
        ep = sorted(([code, d[0], round(d[1], 1)] for code, d in c['expP'].items()), key=lambda x: -x[2])[:TOPN]
        ic = sorted(([ch, round(v, 1)] for ch, v in c['impC'].items()), key=lambda x: -x[1])[:TOPCH]
        ec = sorted(([ch, round(v, 1)] for ch, v in c['expC'].items()), key=lambda x: -x[1])[:TOPCH]
        rec.update(impP=ip, expP=ep, impC=ic, expC=ec)
    out_countries[iso] = rec

ranked = sorted(out_countries.values(), key=lambda c: -(c['imp'] + c['exp']))
data = {
    'source': 'Department of Customs, Nepal — Foreign Trade Statistics',
    'fy': FY, 'unit': "Rs '000", 'updated': datetime.date.today().isoformat(),
    'totals': {k: round(v, 1) for k, v in tot.items()},
    'order': [c['iso'] for c in ranked],
    'countries': out_countries,
}
OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
detail = sum(1 for c in out_countries.values() if 'impP' in c)
print('country.json: %d partners (%d with product detail), %.0f KB' % (len(out_countries), detail, OUT.stat().st_size / 1024))
print('Top 8:', ', '.join('%s %s' % (c['flag'], c['name']) for c in ranked[:8]))
