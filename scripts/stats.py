"""Extract Nepal Foreign Trade Statistics (Department of Customs annual XLSX) into data/stats.json.
Values in the workbook are Rs. thousand; we keep Rs. thousand as integers."""
import openpyxl, json, pathlib, sys, collections, re
root = pathlib.Path(__file__).resolve().parents[1]
src = root / 'data' / (sys.argv[1] if len(sys.argv) > 1 else 'FTS_Annual_2081_82.xlsx')
wb = openpyxl.load_workbook(src, read_only=True, data_only=True)

def rows(name, skip=3):
    ws = wb[name]
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < skip: continue
        if r is None or all(c in (None, '') for c in r): continue
        yield r
def n(x):
    try: return float(x)
    except: return 0.0
I = lambda x: int(round(n(x)))
def code8(c):
    c = re.sub(r'\D', '', str(c or ''))
    return c if len(c) == 8 else None

period = [c for c in next(wb['1_Trade_Direction'].iter_rows(values_only=True)) if c and 'Based on' in str(c)]
hdr = list(wb['1_Trade_Direction'].iter_rows(min_row=3, max_row=3, values_only=True))[0]
fy_prev, fy_cur = str(hdr[2]).split(' (')[0].replace('FY ', ''), str(hdr[3]).split(' (')[0].replace('FY ', '')

overview = {}
for r in rows('1_Trade_Direction'):
    key = str(r[1]).split(' (')[0].strip().lower().replace(' ', '_').replace('/', '_')
    overview[key] = [round(n(r[2]), 2), round(n(r[3]), 2)]

chapters = []
for r in rows('2_Trade_Balance_Chapter'):
    if str(r[0]).strip().isdigit():
        chapters.append([int(r[0]), str(r[1]).strip(), I(r[2]), I(r[3]), I(r[5]) if len(r) > 5 else 0])

countries = []
for r in rows('3_Trade_Balance_Country'):
    if r[1] and str(r[0]).strip().isdigit():
        countries.append([str(r[1]).strip(), I(r[2]), I(r[3])])

customs = []
for r in rows('9_Customswise_Trade'):
    if r[1] and str(r[0]).strip().isdigit():
        customs.append([str(r[1]).strip().title(), I(r[2]), I(r[4])])

bands = []
for r in rows('8_ID_Value_Comaparison'):
    if r[0] is None or str(r[0]).lower().startswith(('total', 'id_rate')): continue
    bands.append([str(r[0]).strip(), I(r[1]), I(r[3])])

imp = {}
for r in rows('5_Imports_By_Commodity'):
    c = code8(r[0])
    if not c: continue
    imp[c] = dict(d=str(r[1] or '').strip(), u=str(r[2] or '').strip(), q=round(n(r[3]), 1), v=I(r[4]), r=I(r[5]), p=[])
part = collections.defaultdict(list)
for r in rows('4_Imports_By_Commodity_Partner'):
    c = code8(r[0])
    if c: part[c].append((str(r[2] or '').strip(), I(r[5])))
for c, lst in part.items():
    if c in imp:
        lst.sort(key=lambda x: -x[1]); imp[c]['p'] = [[a, b] for a, b in lst[:6]]; imp[c]['np'] = len(lst)

exp = {}
for r in rows('7_Exports_By_Commodity'):
    c = code8(r[0])
    if not c: continue
    exp[c] = dict(d=str(r[1] or '').strip(), u=str(r[2] or '').strip(), q=round(n(r[3]), 1), v=I(r[4]), p=[])
epart = collections.defaultdict(list)
for r in rows('6_Exports_By_Commodity_Partner'):
    c = code8(r[0])
    if c: epart[c].append((str(r[2] or '').strip(), I(r[5])))
for c, lst in epart.items():
    if c in exp:
        lst.sort(key=lambda x: -x[1]); exp[c]['p'] = [[a, b] for a, b in lst[:6]]; exp[c]['np'] = len(lst)

# compact arrays
imp_c = {c: [v['d'], v['u'], v['q'], v['v'], v['r'], v['p'], v.get('np', 0)] for c, v in imp.items()}
exp_c = {c: [v['d'], v['u'], v['q'], v['v'], v['p'], v.get('np', 0)] for c, v in exp.items()}

# country -> top chapters (for the countries view): aggregate partner table by chapter
cc = collections.defaultdict(lambda: collections.defaultdict(int))
for c, lst in part.items():
    for a, b in lst: cc[a][int(c[:2])] += b
ce = collections.defaultdict(lambda: collections.defaultdict(int))
for c, lst in epart.items():
    for a, b in lst: ce[a][int(c[:2])] += b
country_top = {}
for name, _, _ in countries:
    ti = sorted(cc[name].items(), key=lambda x: -x[1])[:5]
    te = sorted(ce[name].items(), key=lambda x: -x[1])[:5]
    if ti or te: country_top[name] = [ti, te]

out = dict(fy=fy_cur, fy_prev=fy_prev, period=period[0] if period else '', unit='Rs. thousand',
           overview=overview, chapters=chapters, countries=countries, customs=customs, bands=bands,
           imports=imp_c, exports=exp_c, country_top=country_top,
           source='Department of Customs, Nepal Foreign Trade Statistics (annual), customs.gov.np')
js = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
(root / 'data' / 'stats.json').write_text(js, encoding='utf-8')
print('fy', fy_cur, 'prev', fy_prev, '| chapters', len(chapters), 'countries', len(countries), 'customs', len(customs), 'bands', len(bands), 'imports', len(imp_c), 'exports', len(exp_c), '| KB', len(js.encode()) // 1024)
print('overview', overview)
