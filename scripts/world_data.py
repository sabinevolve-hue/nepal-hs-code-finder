#!/usr/bin/env python3
"""Build world.customsnepal.com data from canonical HS tree + World Bank/WITS trade pulls.
Usage: world_data.py <hs.csv> <raw_dir> <tariff.json> <out_dir>
Writes <out_dir>/hs.json (Pillar 1) and <out_dir>/trade.json (Pillar 2).
Network IO is done in the shell (curl); this parser is pure/local."""
import sys, os, csv, json, re
import xml.etree.ElementTree as ET

HS_CSV, RAW, TARIFF, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(OUT, exist_ok=True)

# ---------------- HS section titles (21 sections, stable) ----------------
SECTIONS = [
 ("I","Live animals; animal products",1,5),
 ("II","Vegetable products",6,14),
 ("III","Animal, vegetable or microbial fats & oils",15,15),
 ("IV","Prepared foodstuffs; beverages, spirits & tobacco",16,24),
 ("V","Mineral products",25,27),
 ("VI","Products of the chemical or allied industries",28,38),
 ("VII","Plastics & rubber",39,40),
 ("VIII","Raw hides, skins, leather & furs",41,43),
 ("IX","Wood, cork & basketware",44,46),
 ("X","Pulp, paper & paperboard",47,49),
 ("XI","Textiles & textile articles",50,63),
 ("XII","Footwear, headgear & umbrellas",64,67),
 ("XIII","Articles of stone, plaster, cement, ceramics & glass",68,70),
 ("XIV","Natural & cultured pearls, precious stones & metals",71,71),
 ("XV","Base metals & articles thereof",72,83),
 ("XVI","Machinery & mechanical/electrical equipment",84,85),
 ("XVII","Vehicles, aircraft & vessels",86,89),
 ("XVIII","Optical, medical & precision instruments; clocks; musical",90,92),
 ("XIX","Arms & ammunition",93,93),
 ("XX","Miscellaneous manufactured articles",94,96),
 ("XXI","Works of art, collectors' pieces & antiques",97,97),
]
CH_SECTION = {}
for rn, t, a, b in SECTIONS:
    for c in range(a, b + 1):
        CH_SECTION[c] = rn

# ---------------- Pillar 1: HS tree ----------------
chapters, headings, subs = {}, {}, []
with open(HS_CSV, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        code, desc, lvl = r['hscode'].strip(), r['description'].strip(), r.get('level', '')
        if lvl == '2' and len(code) == 2:
            chapters[code] = desc
        elif lvl == '4' and len(code) == 4:
            headings[code] = desc
        elif lvl == '6' and len(code) == 6:
            subs.append([code, desc, code[:4]])

# Nepal interlink: general duty per 6-digit (from Nepal 8-digit tariff)
nepal = {}
try:
    T = json.load(open(TARIFF, encoding='utf-8'))
    def gnum(v):
        if v is None: return None
        s = str(v)
        if re.fullmatch(r'free', s, re.I): return 0.0
        m = re.match(r'\d+(\.\d+)?$', s)
        return float(s) if m else None
    agg = {}
    for row in T['rows']:
        code = row[0].replace('.', '')      # 8-digit digits
        g = gnum(row[5])
        if len(code) >= 6:
            agg.setdefault(code[:6], []).append(g)
    for six, gs in agg.items():
        nums = sorted(set(x for x in gs if x is not None))
        if not nums:
            nepal[six] = {'n': len(gs)}
        elif len(nums) == 1:
            nepal[six] = {'n': len(gs), 'g': nums[0]}
        else:
            nepal[six] = {'n': len(gs), 'g': [nums[0], nums[-1]]}
except Exception as e:
    sys.stderr.write(f'nepal link skipped: {e}\n')

for s in subs:
    np = nepal.get(s[0])
    if np: s.append(np)        # [code, desc, heading, {n, g?}]

hs = {
    'edition': 'HS 2022',
    'note': 'International 6-digit Harmonized System nomenclature (WCO). National tariffs extend it to 8–10 digits.',
    'sections': [[rn, t, a, b] for rn, t, a, b in SECTIONS],
    'chapters': [[c, chapters[c], CH_SECTION.get(int(c), '')] for c in sorted(chapters)],
    'headings': headings,
    'subs': sorted(subs, key=lambda x: x[0]),
}
json.dump(hs, open(os.path.join(OUT, 'hs.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# ---------------- Pillar 2: country trade ----------------
def L(tag): return tag.split('}')[-1]

# real-country ISO3 set + iso3->(name, iso2) from WB country list
real, iso3meta = set(), {}
try:
    cl = json.load(open(os.path.join(RAW, 'countrylist.json'), encoding='utf-8'))[1]
    for c in cl:
        if c.get('region', {}).get('value') and c['region']['value'] != 'Aggregates':
            real.add(c['id'])
            iso3meta[c['id']] = (c['name'], c.get('iso2Code', ''))
except Exception as e:
    sys.stderr.write(f'country list: {e}\n')

def flag(iso2):
    if not iso2 or len(iso2) != 2 or not iso2.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(ch) - ord('A')) for ch in iso2.upper())

NAME_FIX = {'RUS': 'Russia', 'USA': 'United States', 'EUN': 'European Union',
            'KOR': 'South Korea', 'HKG': 'Hong Kong', 'ARE': 'United Arab Emirates',
            'GBR': 'United Kingdom', 'TWN': 'Taiwan', 'CZE': 'Czechia', 'VNM': 'Vietnam'}

def wb_series(path):
    """World Bank indicator JSON -> {year:int -> value}."""
    out = {}
    try:
        d = json.load(open(path, encoding='utf-8'))
        if isinstance(d, list) and len(d) > 1 and d[1]:
            for o in d[1]:
                if o.get('value') is not None:
                    out[int(o['date'])] = float(o['value'])
    except Exception as e:
        sys.stderr.write(f'wb {path}: {e}\n')
    return out

def wits_partners(path):
    """WITS SDMX -> list of (iso3, value_usd) for individual reporter->partner, excluding aggregates."""
    out = []
    try:
        root = ET.parse(path).getroot()
        for s in root.iter():
            if L(s.tag) != 'Series': continue
            p = s.attrib.get('PARTNER')
            if not p or p == 'WLD' or p not in real: continue
            for c in s:
                if L(c.tag) == 'Obs' and c.attrib.get('OBS_VALUE'):
                    out.append((p, float(c.attrib['OBS_VALUE']) * 1000.0))
                    break
    except Exception as e:
        sys.stderr.write(f'wits P {path}: {e}\n')
    out.sort(key=lambda x: -x[1])
    return out[:10]

PROD = {'01-05': 'Animal & animal products', '06-15': 'Vegetable products',
        '16-24': 'Foodstuffs, beverages & tobacco', '25-26': 'Minerals',
        '27-27': 'Mineral fuels & oils', '28-38': 'Chemicals & allied',
        '39-40': 'Plastics & rubber', '41-43': 'Hides, skins & leather',
        '44-49': 'Wood & paper', '50-63': 'Textiles & clothing',
        '64-67': 'Footwear & headgear', '68-71': 'Stone, glass & precious metals',
        '72-83': 'Base metals', '84-85': 'Machinery & electronics',
        '86-89': 'Transport equipment', '90-99': 'Instruments, arms & misc.'}

def wits_products(path):
    out = []
    try:
        root = ET.parse(path).getroot()
        for s in root.iter():
            if L(s.tag) != 'Series': continue
            pc = s.attrib.get('PRODUCTCODE', '')
            m = re.match(r'(\d\d-\d\d)_', pc)
            if not m: continue
            label = PROD.get(m.group(1), pc.split('_', 1)[-1])
            for c in s:
                if L(c.tag) == 'Obs' and c.attrib.get('OBS_VALUE'):
                    out.append([label, float(c.attrib['OBS_VALUE']) * 1000.0])
                    break
    except Exception as e:
        sys.stderr.write(f'wits Prod {path}: {e}\n')
    out.sort(key=lambda x: -x[1])
    return out

def pset(parts):
    return [[p, NAME_FIX.get(p, iso3meta.get(p, (p, ''))[0]), round(v)] for p, v in parts]

CFG = [  # name, flag, wbcode, witscode, partnerYear
    ("United States", "🇺🇸", "USA", "USA", 2022),
    ("China", "🇨🇳", "CHN", "CHN", 2022),
    ("European Union", "🇪🇺", "EUU", "EUN", 2022),
    ("India", "🇮🇳", "IND", "IND", 2022),
    ("Japan", "🇯🇵", "JPN", "JPN", 2022),
    ("Russia", "🇷🇺", "RUS", "RUS", 2021),
]

countries = []
for name, fl, wb, wt, py in CFG:
    exp, imp = wb_series(os.path.join(RAW, f'wb_exp_{wb}.json')), wb_series(os.path.join(RAW, f'wb_imp_{wb}.json'))
    years = sorted(set(exp) | set(imp))
    trend = [[y, round(exp.get(y)) if y in exp else None, round(imp.get(y)) if y in imp else None] for y in years if y >= 2012]
    expY = max(exp) if exp else None
    impY = max(imp) if imp else None
    countries.append({
        'iso': wb, 'name': name, 'flag': fl,
        'expYear': expY, 'exp': round(exp[expY]) if expY else None,
        'impYear': impY, 'imp': round(imp[impY]) if impY else None,
        'trend': trend,
        'pYear': py,
        'expPartners': pset(wits_partners(os.path.join(RAW, f'wits_expP_{wt}_{py}.xml'))),
        'impPartners': pset(wits_partners(os.path.join(RAW, f'wits_impP_{wt}_{py}.xml'))),
        'expProducts': [[l, round(v)] for l, v in wits_products(os.path.join(RAW, f'wits_expProd_{wt}.xml'))],
        'impProducts': [[l, round(v)] for l, v in wits_products(os.path.join(RAW, f'wits_impProd_{wt}.xml'))],
    })

countries.sort(key=lambda c: -(c['exp'] or 0))
trade = {
    'updated': '2026-10-10',
    'totalsSource': 'World Bank (merchandise trade, current US$)',
    'detailSource': 'World Bank WITS, sourced from UN Comtrade',
    'countries': countries,
}
json.dump(trade, open(os.path.join(OUT, 'trade.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# ---------------- report ----------------
print('HS: %d chapters, %d headings, %d subheadings; %d linked to Nepal duty' %
      (len(hs['chapters']), len(headings), len(subs), len(nepal)))
for c in countries:
    print('%-16s exp $%0.0fB (%s)  imp $%0.0fB  partners e%d/i%d  products e%d/i%d' % (
        c['name'], (c['exp'] or 0) / 1e9, c['expYear'], (c['imp'] or 0) / 1e9,
        len(c['expPartners']), len(c['impPartners']), len(c['expProducts']), len(c['impProducts'])))
print('hs.json %0.0f KB, trade.json %0.1f KB' % (
    os.path.getsize(os.path.join(OUT, 'hs.json')) / 1024, os.path.getsize(os.path.join(OUT, 'trade.json')) / 1024))
