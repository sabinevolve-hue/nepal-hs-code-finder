"""Customs-office trade totals from the official FTS workbooks (sheet 9_Customswise_Trade).

OFFLINE step (needs openpyxl; reads data/fts/<fy>/*.xlsx, which is kept out of git) — NOT part of
`npm run build`. Shares its year settings with world_country.py. Writes world/data/offices_trade.json,
which office_pages.py (stdlib) turns into /customs-offices and /customs-office/<id>.

Run:  python3 scripts/customs_offices.py
"""
import json, pathlib, re, datetime
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
FTS = ROOT / 'data' / 'fts'
MAIN_FY = '2082-83'
HIST_FYS = ['2076-77', '2077-78', '2078-79', '2079-80', '2080-81', '2081-82', '2082-83']
YTD_FY, YTD_LABEL = '2083-84', 'Shrawan–Bhadra (first 2 months)'
norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def book(fy):
    fs = sorted((FTS / fy).glob('*.xlsx'))
    return fs[-1] if fs else None


def read(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sn = next((n for n in wb.sheetnames if n.startswith('9_')), None)
    out, total = {}, None
    for r in (wb[sn].iter_rows(min_row=4, values_only=True) if sn else []):
        if not r[1]:
            continue
        try:
            row = [float(r[2] or 0), float(r[4] or 0)]
        except (TypeError, ValueError):
            continue
        if norm(r[1]) == 'total':
            total = row
        else:
            out[norm(r[1])] = (str(r[1]).strip(), row)
    return out, total


main, total = read(book(MAIN_FY))
years, hist = [], {}
for fy in HIST_FYS:
    b = book(fy)
    if not b:
        continue
    d, _ = read(b)
    years.append(fy.replace('-', '/'))
    for k in main:
        hist.setdefault(k, []).append([round(x, 1) for x in d.get(k, ('', [0.0, 0.0]))[1]])
ytd = {}
if YTD_FY and book(YTD_FY):
    d, _ = read(book(YTD_FY))
    ytd = {k: [round(x, 1) for x in v[1]] for k, v in d.items()}

offices = {}
for k, (label, (imp, exp)) in main.items():
    offices[k] = {'label': label, 'imp': round(imp, 1), 'exp': round(exp, 1), 'hist': hist.get(k, [])}
    if k in ytd:
        offices[k]['ytd'] = ytd[k]
assert abs(sum(o['imp'] for o in offices.values()) - total[0]) < 5, 'office imports do not add up to the published total'
out = {'source': 'Department of Customs, Nepal — Foreign Trade Statistics', 'fy': MAIN_FY.replace('-', '/'),
       'unit': "Rs '000", 'updated': datetime.date.today().isoformat(), 'hist_years': years,
       'ytd': {'fy': YTD_FY.replace('-', '/'), 'label': YTD_LABEL} if ytd else None,
       'totals': {'imp': round(total[0], 1), 'exp': round(total[1], 1)}, 'offices': offices}
(ROOT / 'world/data/offices_trade.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print('offices_trade.json: %d offices, years %s' % (len(offices), years))
print(sorted(offices))
