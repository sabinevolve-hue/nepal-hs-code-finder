"""Parse the official Dept. of Customs FTS workbook into a compact per-partner
dataset for the Nepal trade-partner pages.

OFFLINE / yearly refresh step (needs openpyxl, reads the committed .xlsx) — NOT
part of `npm run build`. Run it when a new FTS is dropped in, then commit the
JSON it writes; country_pages.py (stdlib only) reads that JSON at build time.

  Input : data/fts/<fy>/*.xlsx — official Department of Customs FTS workbooks (kept out of git; fetch with
          scripts/refresh.py or by hand from customs.gov.np). MAIN_FY is the latest COMPLETE year and
          drives every figure on the page; HIST_FYS add the per-partner trend; YTD_FY (optional) is the
          running year's latest cumulative workbook.
  Output: world/data/country.json

Yearly: bump MAIN_FY / HIST_FYS / YTD_*, then
  python3 scripts/world_country.py && node scripts/og_images.mjs <playwright>
"""
import pathlib, json, datetime, re
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
FTS = ROOT / 'data' / 'fts'
MAIN_FY = '2082-83'
HIST_FYS = ['2076-77', '2077-78', '2078-79', '2079-80', '2080-81', '2081-82', '2082-83']
YTD_FY, YTD_LABEL = '2083-84', 'Shrawan–Bhadra (first 2 months)'

def book(fy):
    fs = sorted((FTS / fy).glob('*.xlsx'))
    return fs[-1] if fs else None

XLSX = book(MAIN_FY)
OUT = ROOT / 'world' / 'data' / 'country.json'
FY = MAIN_FY.replace('-', '/')
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
    c.setdefault('aka', set()).add(clean(r[1]))
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
print('Customs revenue + supplier shares per product…')
code_tot = {}   # HS code -> {iso: import value}, across all partners
for r in wb['4_Imports_By_Commodity_Partner'].iter_rows(min_row=4, values_only=True):
    if not r[0] or not r[2]:
        continue
    iso, _ = resolve(r[2])
    v = float(r[5] or 0); rv = float(r[6] or 0)
    code = str(r[0]).strip()
    d = code_tot.setdefault(code, {})
    d[iso or '_'] = d.get(iso or '_', 0.0) + v
    if iso in countries:
        c = countries[iso]
        c['rev'] = c.get('rev', 0.0) + rv
        c.setdefault('revP', {})
        c['revP'][code] = c['revP'].get(code, 0.0) + rv
print('Aggregating exports by partner…')
accumulate('6_Exports_By_Commodity_Partner', 2, 5, 'expP', 'expC')

# ---- finalise: trim to top-N, drop detail for tiny partners ----
out_countries = {}
for iso, c in countries.items():
    total = c['imp'] + c['exp']
    rec = {'name': c['name'], 'iso': iso, 'flag': c['flag'],
           'imp': round(c['imp'], 1), 'exp': round(c['exp'], 1), 'rev': round(c.get('rev', 0.0), 1)}
    # never retire a published URL: a partner that already has a page keeps its detail even if it dips under the bar
    _slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', c['name'].lower())).strip('-')
    if total >= PROD_MIN_TH or (total > 0 and (ROOT / 'public' / 'trade-partner' / (_slug + '.html')).exists()):
        ip = sorted(([code, d[0], round(d[1], 1)] for code, d in c['impP'].items()), key=lambda x: -x[2])[:TOPN]
        ep = sorted(([code, d[0], round(d[1], 1)] for code, d in c['expP'].items()), key=lambda x: -x[2])[:TOPN]
        ic = sorted(([ch, round(v, 1)] for ch, v in c['impC'].items()), key=lambda x: -x[1])[:TOPCH]
        ec = sorted(([ch, round(v, 1)] for ch, v in c['expC'].items()), key=lambda x: -x[1])[:TOPCH]
        rec.update(impP=ip, expP=ep, impC=ic, expC=ec)
        rec['impR'] = {q[0]: round(c.get('revP', {}).get(q[0], 0.0), 1) for q in ip}
        comp = {}
        for q in ip:
            d = code_tot.get(q[0], {}); tot_c = sum(d.values()) or 1.0
            top3 = sorted(((k, v) for k, v in d.items() if k != '_'), key=lambda x: -x[1])[:3]
            comp[q[0]] = {'s': round(d.get(iso, 0.0) / tot_c * 100, 1), 't': [[k, round(v / tot_c * 100, 1)] for k, v in top3]}
        rec['comp'] = comp
    aka = sorted(a for a in c.get('aka', ()) if a.lower() != c['name'].lower())
    if aka:
        rec['aka'] = aka
    out_countries[iso] = rec

# ---- history: per-partner imports/exports for each complete year (sheet 3 only) ----
def partner_totals(path):
    w = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sn = next((n for n in w.sheetnames if n.lower().startswith('3_')), None)
    res = {}
    if not sn:
        return res
    for r in w[sn].iter_rows(min_row=4, values_only=True):
        if not r[1] or len(r) < 4:
            continue
        iso, _ = resolve(str(r[1]))
        if iso is None:
            continue
        try:
            i = float(r[2] or 0); e = float(r[3] or 0)
        except (TypeError, ValueError):
            continue
        a = res.setdefault(iso, [0.0, 0.0]); a[0] += i; a[1] += e
    return res

hist_years = []
for fy in HIST_FYS:
    b = book(fy)
    if not b:
        print('  (no workbook for', fy, '— skipped in trend)'); continue
    print('History', fy, b.name)
    pt = partner_totals(b)
    if fy == MAIN_FY:          # sanity: history must agree with the main parse
        for iso in ('IND', 'CHN'):
            assert abs(pt[iso][0] - countries[iso]['imp']) < 1, 'history/main mismatch ' + iso
    hist_years.append(fy.replace('-', '/'))
    for iso, rec in out_countries.items():
        v = pt.get(iso, [0.0, 0.0])
        rec.setdefault('hist', []).append([round(v[0], 1), round(v[1], 1)])
ytd = None
if YTD_FY and book(YTD_FY):
    print('Year to date', YTD_FY, book(YTD_FY).name)
    pt = partner_totals(book(YTD_FY))
    ytd = {'fy': YTD_FY.replace('-', '/'), 'label': YTD_LABEL}
    for iso, rec in out_countries.items():
        if iso in pt:
            rec['ytd'] = [round(pt[iso][0], 1), round(pt[iso][1], 1)]

ranked = sorted(out_countries.values(), key=lambda c: -(c['imp'] + c['exp']))
data = {
    'source': 'Department of Customs, Nepal — Foreign Trade Statistics',
    'fy': FY, 'unit': "Rs '000", 'updated': datetime.date.today().isoformat(),
    'totals': dict({k: round(v, 1) for k, v in tot.items()}, rev=round(sum(c.get('rev', 0.0) for c in countries.values()), 1)),
    'hist_years': hist_years, 'ytd': ytd,
    'order': [c['iso'] for c in ranked],
    'countries': out_countries,
}
OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
detail = sum(1 for c in out_countries.values() if 'impP' in c)
print('country.json: %d partners (%d with product detail), %.0f KB' % (len(out_countries), detail, OUT.stat().st_size / 1024))
print('Top 8:', ', '.join('%s %s' % (c['flag'], c['name']) for c in ranked[:8]))
