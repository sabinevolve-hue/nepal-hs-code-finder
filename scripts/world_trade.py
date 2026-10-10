#!/usr/bin/env python3
"""Build world/data/trade.json v2 from World Bank all-country totals + WITS deep detail.
Usage: world_trade.py <raw_dir> <out_dir>
Reads: wb_all_exp.json, wb_all_imp.json, countrylist.json, wits_{expP,impP,expProd,impProd}_<ISO>.xml
Network IO is done in the shell (world_fetch.sh); this parser is pure/local."""
import sys, os, json, re
import xml.etree.ElementTree as ET

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

DEEP = ["CHN","USA","DEU","NLD","JPN","ITA","FRA","KOR","MEX","BEL","HKG","ARE","CAN","GBR",
        "SGP","IND","RUS","ESP","CHE","POL","AUS","VNM","BRA","SAU","MYS","THA","IDN","TUR",
        "CZE","AUT","NPL"]
NAME_FIX = {"USA":"United States","KOR":"South Korea","RUS":"Russia","HKG":"Hong Kong",
            "VNM":"Vietnam","ARE":"United Arab Emirates","GBR":"United Kingdom","CZE":"Czechia",
            "IRN":"Iran","EGY":"Egypt","SVK":"Slovakia","VEN":"Venezuela","LAO":"Laos",
            "BRN":"Brunei","MDA":"Moldova","TWN":"Taiwan","BOL":"Bolivia","TZA":"Tanzania",
            "SYR":"Syria","COD":"DR Congo","COG":"Congo","KGZ":"Kyrgyzstan","MKD":"North Macedonia"}

def L(t): return t.split('}')[-1]
def flag(iso2):
    if not iso2 or len(iso2)!=2 or not iso2.isalpha(): return ''
    return ''.join(chr(0x1F1E6+ord(c)-ord('A')) for c in iso2.upper())

# ---- country metadata ----
cl = json.load(open(os.path.join(RAW,'countrylist.json')))[1]
meta, real, iso2of = {}, set(), {}
for c in cl:
    reg = c.get('region',{}).get('value','')
    nm = NAME_FIX.get(c['id'], c['name'])
    meta[c['id']] = {'name':nm, 'iso2':c.get('iso2Code',''), 'region':reg}
    iso2of[c['id']] = c.get('iso2Code','')
    if reg and reg!='Aggregates': real.add(c['id'])

def load_series(path):
    out={}
    for o in json.load(open(path))[1]:
        if o.get('value') is not None:
            out.setdefault(o['countryiso3code'],{})[int(o['date'])]=float(o['value'])
    return out
EXP = load_series(os.path.join(RAW,'wb_all_exp.json'))
IMP = load_series(os.path.join(RAW,'wb_all_imp.json'))

def latest(d):
    return (max(d), d[max(d)]) if d else (None,None)

# ---- WITS detail ----
PROD = {'01-05':'Animal & animal products','06-15':'Vegetable products','16-24':'Foodstuffs, beverages & tobacco',
        '25-26':'Minerals','27-27':'Mineral fuels & oils','28-38':'Chemicals & allied','39-40':'Plastics & rubber',
        '41-43':'Hides, skins & leather','44-49':'Wood & paper','50-63':'Textiles & clothing','64-67':'Footwear & headgear',
        '68-71':'Stone, glass & precious metals','72-83':'Base metals','84-85':'Machinery & electronics',
        '86-89':'Transport equipment','90-99':'Instruments, arms & misc.'}
def wits_partners(path):
    out=[]; yr=None
    try:
        for s in ET.parse(path).getroot().iter():
            if L(s.tag)!='Series': continue
            p=s.attrib.get('PARTNER')
            if not p or p=='WLD' or p not in real: continue
            for c in s:
                if L(c.tag)=='Obs' and c.attrib.get('OBS_VALUE'):
                    out.append((p,float(c.attrib['OBS_VALUE'])*1000.0)); yr=c.attrib.get('TIME_PERIOD',yr); break
    except Exception as e: sys.stderr.write(f'P {path}: {e}\n')
    out.sort(key=lambda x:-x[1])
    return [[p, NAME_FIX.get(p, meta.get(p,{}).get('name',p)), round(v)] for p,v in out[:10]], yr
def wits_products(path):
    out=[]
    try:
        for s in ET.parse(path).getroot().iter():
            if L(s.tag)!='Series': continue
            m=re.match(r'(\d\d-\d\d)_', s.attrib.get('PRODUCTCODE',''))
            if not m: continue
            for c in s:
                if L(c.tag)=='Obs' and c.attrib.get('OBS_VALUE'):
                    out.append([PROD.get(m.group(1),m.group(1)), round(float(c.attrib['OBS_VALUE'])*1000.0)]); break
    except Exception as e: sys.stderr.write(f'Prod {path}: {e}\n')
    out.sort(key=lambda x:-x[1])
    return out

# ---- build all countries ----
countries=[]
for iso in real:
    e,i = EXP.get(iso,{}), IMP.get(iso,{})
    if not e and not i: continue
    ey,ev = latest(e); iy,iv = latest(i)
    years = sorted(set(e)|set(i))
    trend = [[y, round(e[y]) if y in e else None, round(i[y]) if y in i else None] for y in years if y>=2012]
    countries.append({'iso':iso,'name':meta[iso]['name'],'flag':flag(meta[iso]['iso2']),
                      'region':meta[iso]['region'],'exp':round(ev) if ev else None,'expYear':ey,
                      'imp':round(iv) if iv else None,'impYear':iy,'trend':trend})
# ranks
for key,fld in (('exp','rankExp'),('imp','rankImp')):
    ranked=sorted([c for c in countries if c[key]],key=lambda c:-c[key])
    for n,c in enumerate(ranked,1): c[fld]=n
# deep detail
for c in countries:
    if c['iso'] not in DEEP: continue
    iso=c['iso']
    ep,ey = wits_partners(os.path.join(RAW,f'wits_expP_{iso}.xml'))
    ip,iy = wits_partners(os.path.join(RAW,f'wits_impP_{iso}.xml'))
    c['expPartners']=ep; c['impPartners']=ip
    c['expProducts']=wits_products(os.path.join(RAW,f'wits_expProd_{iso}.xml'))
    c['impProducts']=wits_products(os.path.join(RAW,f'wits_impProd_{iso}.xml'))
    c['pYear']=ey or iy; c['deep']=True
countries.sort(key=lambda c:-(c['exp'] or 0))

# ---- world aggregates (use WLD authentic totals) ----
wld_e, wld_i = EXP.get('WLD',{}), IMP.get('WLD',{})
wy = max(wld_e) if wld_e else None
wyears=sorted(set(wld_e)|set(wld_i))
wtrend=[[y, round(wld_e[y]) if y in wld_e else None, round(wld_i[y]) if y in wld_i else None] for y in wyears if y>=2012]
def toplist(fld):
    r=sorted([c for c in countries if c[fld]],key=lambda c:-c[fld])[:25]
    return [[c['iso'],c['name'],c['flag'],c[fld]] for c in r]
# regions (sum real countries by region, latest)
regagg={}
for c in countries:
    if not c['region']: continue
    a=regagg.setdefault(c['region'],[0,0])
    a[0]+=c['exp'] or 0; a[1]+=c['imp'] or 0
regions=sorted(([r,v[0],v[1]] for r,v in regagg.items()),key=lambda x:-x[1])

world={'year':wy,'totalExp':round(wld_e[wy]) if wy else None,'totalImp':round(wld_i[wy]) if wld_i else None,
       'trend':wtrend,'topExp':toplist('exp'),'topImp':toplist('imp'),'regions':regions,'count':len(countries)}

trade={'updated':'2026-10-10','totalsSource':'World Bank (merchandise trade, current US$)',
       'detailSource':'World Bank WITS, sourced from UN Comtrade','world':world,'countries':countries}
json.dump(trade,open(os.path.join(OUT,'trade.json'),'w'),ensure_ascii=False,separators=(',',':'))

# report
nd=sum(1 for c in countries if c.get('deep'))
print(f"countries: {len(countries)} (deep detail: {nd})  world exports {world['totalExp']/1e12:.1f}T ({wy})")
print("top5 exporters:", [(c['name'],round((c['exp'] or 0)/1e9)) for c in countries[:5]])
print("Nepal:", next(((c['name'],c['rankExp'],c.get('deep')) for c in countries if c['iso']=='NPL'),'MISSING'))
print(f"trade.json {os.path.getsize(os.path.join(OUT,'trade.json'))/1024:.1f} KB")
