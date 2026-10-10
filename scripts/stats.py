"""Build multi-year trade statistics from all Department of Customs FTS workbooks (FY 2076/77 -> latest).
Output data/stats.json (latest full year detail, like before, plus history) — compact enough to inline.
Layout: identical 10-sheet FTS workbooks. Values in Rs. thousand.
"""
import openpyxl, json, pathlib, re, glob, collections, sys
root = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'data' / 'fts'

# Nepali fiscal months in order (Shrawan first)
MONTHS = ['Shrawan', 'Bhadra', 'Asoj', 'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra', 'Baishakh', 'Jestha', 'Asar']
MKEY = {'shrawan': 0, 'sawan': 0, 'श्रावण': 0, 'साउन': 0, 'bhadra': 1, 'भाद्र': 1, 'asoj': 2, 'ashwin': 2, 'aswin': 2, 'असोज': 2, 'आश्विन': 2,
        'kartik': 3, 'कार्तिक': 3, 'कात्तिक': 3, 'mangsir': 4, 'मंसिर': 4, 'मार्ग': 4, 'poush': 5, 'push': 5, 'paush': 5, 'पुस': 5, 'पौष': 5,
        'magh': 6, 'माघ': 6, 'falgun': 7, 'fagun': 7, 'फागुन': 7, 'chaitra': 8, 'चैत्र': 8, 'baishakh': 9, 'baisakh': 9, 'baishak': 9, 'वैशाख': 9, 'बैशाख': 9,
        'jestha': 10, 'jeth': 10, 'जेठ': 10, 'जेष्ठ': 10, 'asar': 11, 'ashadh': 11, 'ashad': 11, 'असार': 11, 'annual': 11, 'final': 11}

def n(x):
    try: return float(x)
    except: return 0.0
I = lambda x: int(round(n(x)))
def code8(c):
    c = re.sub(r'\D', '', str(c or '')); return c if len(c) == 8 else None

def read(path, fy_hint=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    names = {re.sub(r'[^a-z]', '', s.lower()): s for s in wb.sheetnames}
    def sheet(key):
        for k, v in names.items():
            if key in k: return wb[v]
        return None
    def rows(ws, skip=3):
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i < skip or r is None or all(c in (None, '') for c in r): continue
            yield r
    out = {}
    ws = sheet('tradedirection')
    hdr = list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]
    top = ' '.join(str(c) for c in list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0] if c)
    fys_found = re.findall(r'(\d{4})\s*/\s*(\d{2,4})', str(hdr[2]) + ' ' + str(hdr[3]) + ' ' + top)
    fys_found = [a + '/' + b[-2:] for a, b in fys_found]
    if len(fys_found) >= 2: out['fy_prev'], out['fy'] = fys_found[0], fys_found[1]
    elif fys_found: out['fy'] = fys_found[-1]; out['fy_prev'] = str(int(fys_found[-1][:4]) - 1) + '/' + str(int(fys_found[-1][:4]) % 100).zfill(2)
    else: out['fy'] = fy_hint; out['fy_prev'] = str(int(fy_hint[:4]) - 1) + '/' + str(int(fy_hint[:4]) % 100).zfill(2)
    if fys_found and len(fys_found) < 2 and fy_hint: out['fy'] = fy_hint
    m = re.search(r'\((\d+)\s*Month', str(hdr[3])); out['months'] = int(m.group(1)) if m else 12
    ov = {}
    for r in rows(ws):
        key = str(r[1]).split(' (')[0].strip().lower().replace(' ', '_').replace('/', '_')
        ov[key] = [round(n(r[2]), 2), round(n(r[3]), 2)]
    out['overview'] = ov
    ch = []
    for r in rows(sheet('tradebalancechapter')):
        if str(r[0]).strip().isdigit(): ch.append([int(r[0]), I(r[2]), I(r[3]), I(r[5]) if len(r) > 5 else 0])
    out['chapters'] = ch
    co = []
    for r in rows(sheet('tradebalancecountry')):
        if r[1] and str(r[0]).strip().isdigit(): co.append([str(r[1]).strip(), I(r[2]), I(r[3])])
    out['countries'] = co
    cu = []
    for r in rows(sheet('customswise')):
        # the sheet ends with a 'Total' row that also carries a serial number: it is not an office
        if r[1] and str(r[0]).strip().isdigit() and str(r[1]).strip().lower() != 'total': cu.append([str(r[1]).strip().title(), I(r[2]), I(r[4])])
    out['customs'] = cu
    bd = []
    for r in rows(sheet('idvalue')):
        if r[0] is None or str(r[0]).lower().startswith(('total', 'id_rate')): continue
        bd.append([str(r[0]).strip(), I(r[1]), I(r[3])])
    out['bands'] = bd
    imp = {}
    for r in rows(sheet('importsbycommodity') if not sheet('importsbycommoditypartner') else wb[[v for k, v in names.items() if 'importsbycommodity' in k and 'partner' not in k][0]]):
        c = code8(r[0])
        if c: imp[c] = dict(d=str(r[1] or '').strip(), u=str(r[2] or '').strip(), q=round(n(r[3]), 1), v=I(r[4]), r=I(r[5]), p=[], np=0)
    part = collections.defaultdict(list)
    for r in rows(sheet('importsbycommoditypartner')):
        c = code8(r[0])
        if c: part[c].append((str(r[2] or '').strip(), I(r[5])))
    for c, lst in part.items():
        if c in imp: lst.sort(key=lambda x: -x[1]); imp[c]['p'] = [[a, b] for a, b in lst[:6]]; imp[c]['np'] = len(lst)
    exp = {}
    for r in rows(wb[[v for k, v in names.items() if 'exportsbycommodity' in k and 'partner' not in k][0]]):
        c = code8(r[0])
        if c: exp[c] = dict(d=str(r[1] or '').strip(), u=str(r[2] or '').strip(), q=round(n(r[3]), 1), v=I(r[4]), p=[], np=0)
    epart = collections.defaultdict(list)
    for r in rows(sheet('exportsbycommoditypartner')):
        c = code8(r[0])
        if c: epart[c].append((str(r[2] or '').strip(), I(r[5])))
    for c, lst in epart.items():
        if c in exp: lst.sort(key=lambda x: -x[1]); exp[c]['p'] = [[a, b] for a, b in lst[:6]]; exp[c]['np'] = len(lst)
    out['imports'], out['exports'] = imp, exp
    # country -> top chapters
    cc = collections.defaultdict(lambda: collections.defaultdict(int)); ce = collections.defaultdict(lambda: collections.defaultdict(int))
    for c, lst in part.items():
        for a, b in lst: cc[a][int(c[:2])] += b
    for c, lst in epart.items():
        for a, b in lst: ce[a][int(c[:2])] += b
    out['country_top'] = {nm: [sorted(cc[nm].items(), key=lambda x: -x[1])[:6], sorted(ce[nm].items(), key=lambda x: -x[1])[:6]] for nm, _, _ in co if cc[nm] or ce[nm]}
    # country x chapter full matrix for flows (top 30 countries x all chapters, imports)
    out['flow'] = {nm: [[k, v] for k, v in cc[nm].items() if v > 0] for nm in [x[0] for x in sorted(co, key=lambda x: -x[1])[:30]]}
    # country -> top-20 products (8-digit) by value, imports and exports (for the country drill-down)
    cpi = collections.defaultdict(lambda: collections.defaultdict(int)); cpe = collections.defaultdict(lambda: collections.defaultdict(int))
    for c, lst in part.items():
        for a, b in lst: cpi[a][c] += b
    for c, lst in epart.items():
        for a, b in lst: cpe[a][c] += b
    def _packtop(cm, N=20):
        s = sorted(cm.items(), key=lambda x: -x[1]); rest = s[N:]
        return [[[c, v] for c, v in s[:N]], ([sum(v for _, v in rest), len(rest)] if rest else 0)]
    out['country_prod'] = {nm: (_packtop(cpi[nm]) + _packtop(cpe[nm])) for nm in (set(cpi) | set(cpe))}
    return out

def month_of(name):
    s = name.lower()
    for k, v in MKEY.items():
        if k in s: return v
    return None

# ---- discover files: <fy>/<file>.xlsx under SRC, fy folder like 2081-82 ----
years = {}
for f in sorted(SRC.glob('*/*.xlsx')):
    fy = f.parent.name.replace('_', '-')
    mo = month_of(f.name)
    if mo is None: print('skip (month?)', f.name); continue
    years.setdefault(fy, {})[mo] = f
fys = sorted(years)
print('years', {fy: sorted(m) for fy, m in years.items()})

parsed = {}
for fy in fys:
    for mo, f in sorted(years[fy].items()):
        print('reading', fy, MONTHS[mo], f.name, flush=True)
        parsed[(fy, mo)] = read(f, fy[:4] + '/' + fy[-2:])

# latest complete year = highest fy with month 11; current = highest fy overall
full = [fy for fy in fys if 11 in years[fy]]
latest_full = full[-1]
current = fys[-1]
cur_mo = max(years[current])
L = parsed[(latest_full, 11)]

# ---- history: per year totals, chapters, countries, customs; per code yearly import/export value ----
hist_years = full
history = dict(years=[parsed[(fy, 11)]['fy'] for fy in hist_years],
               totals=[[parsed[(fy, 11)]['overview']['imports'][1], parsed[(fy, 11)]['overview']['exports'][1]] for fy in hist_years],
               chapters={}, countries={}, customs={}, codes={}, bands=[], overview=[])
for i, fy in enumerate(hist_years):
    P = parsed[(fy, 11)]
    history['bands'].append(P['bands']); history['overview'].append(P['overview'])
    for c, iv, ev, rv in P['chapters']: history['chapters'].setdefault(c, [[0, 0, 0] for _ in hist_years])[i] = [iv, ev, rv]
    for nm, iv, ev in P['countries']: history['countries'].setdefault(nm, [[0, 0] for _ in hist_years])[i] = [iv, ev]
    for nm, iv, ev in P['customs']: history['customs'].setdefault(nm, [[0, 0] for _ in hist_years])[i] = [iv, ev]
    for c, v in P['imports'].items(): history['codes'].setdefault(c, [[0, 0] for _ in hist_years])[i][0] = v['v']
    for c, v in P['exports'].items(): history['codes'].setdefault(c, [[0, 0] for _ in hist_years])[i][1] = v['v']

# ---- monthly: difference cumulative files -> per-month totals and per-chapter (for years with >= 6 monthly files) ----
monthly = {}
for fy in fys:
    ms = sorted(years[fy])
    if len(ms) < 2: continue
    prev_t = [0, 0]; prev_ch = {}
    series = []
    for mo in range(12):
        if mo not in years[fy]:
            series.append(None); continue
        P = parsed[(fy, mo)]
        t = [P['overview']['imports'][1], P['overview']['exports'][1]]
        ch = {c: [iv, ev] for c, iv, ev, _ in P['chapters']}
        # cumulative -> monthly (if a month is missing, the diff spans the gap; mark by 'span')
        d = [round(t[0] - prev_t[0], 2), round(t[1] - prev_t[1], 2)]
        dch = {c: [ch[c][0] - prev_ch.get(c, [0, 0])[0], ch[c][1] - prev_ch.get(c, [0, 0])[1]] for c in ch}
        series.append(dict(m=mo, cum=t, val=d, ch=dch))
        prev_t, prev_ch = t, ch
    monthly[P['fy']] = series

out = dict(fy=L['fy'], fy_prev=L['fy_prev'], months=12, unit='Rs. thousand', period=f"FY {L['fy']} (annual)",
           overview=L['overview'], chapters=[[c, '', iv, ev, rv] for c, iv, ev, rv in L['chapters']], countries=L['countries'], customs=L['customs'], bands=L['bands'],
           imports={c: [v['d'], v['u'], v['q'], v['v'], v['r'], v['p'], v['np']] for c, v in L['imports'].items()},
           exports={c: [v['d'], v['u'], v['q'], v['v'], v['p'], v['np']] for c, v in L['exports'].items()},
           country_top=L['country_top'], flow=L['flow'], country_prod=L['country_prod'],
           history=history, monthly=monthly, month_names=MONTHS,
           current=dict(fy=parsed[(current, cur_mo)]['fy'], months=cur_mo + 1, overview=parsed[(current, cur_mo)]['overview'],
                        chapters=[[c, iv, ev, rv] for c, iv, ev, rv in parsed[(current, cur_mo)]['chapters']],
                        countries=sorted(parsed[(current, cur_mo)]['countries'], key=lambda x: -x[1])[:40]) if current != latest_full else None,
           source='Department of Customs, Nepal Foreign Trade Statistics, customs.gov.np')
js = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
(root / 'data' / 'stats.json').write_text(js, encoding='utf-8')
print('latest full', latest_full, 'current', current, MONTHS[cur_mo], '| KB', len(js.encode()) // 1024, '| codes hist', len(history['codes']))
