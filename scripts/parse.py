"""Parse Nepal Customs Tariff 2026/27 (English text layer) into structured JSON.

Output: parsed.json with rows (tariff lines), headings, chapters (+notes), sections, export duties.
Design: line classifier + FIFO queue of rows still waiting for their unit/rate cells, because the PDF
text layer sometimes emits the rate cells after following description lines (column scrambling).
"""
import re, json, sys

lines = open(__import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'customs-tariff-2026-27.txt', encoding='utf-8').read().replace('g/m2kg ', 'g/m2 kg ').split('\n')
EXPORT_START = next(i for i, l in enumerate(lines) if l.strip() == 'Export Customs Tariff Rate' and i > 1000)
IMPORT_START = next(i for i, l in enumerate(lines) if l.strip() == 'Section 1')

UNIT_WORDS = ['nos/kg', 'kg/ltr.', 'kg/ltr', 'ltr/kg.', 'ltr/kg', 'ltr.', 'ltr', 'lt.', 'nos', 'Nos', 'kg', 'Kg', 'KG',
              'm2', 'm3', 'm', 'pair', 'pairs', 'stk', 'MT', 'KL', 'l', 'u', 'carat', 'g', 'gm', '1000 nos', 'nos/set',
              'set', 'sets', 'doz', 'sq.m', 'm²', 'm³', 'kWh', '1000kWh', 'ton', 'tola']
ATOM = r'(?:kg|Kg|KG|nos|Nos|NOS|m2|m3|m²|m³|ltr\.?|Ltr\.?|lt\.?|mtr\.?|pairs?|Pair|ft2|gro|[Cc]arat|cm2|pkt|MWH|[Ss]tk|Per cinema|MT|KL|sets?|doz|gm|g|l|m|u)'
UNIT_ALT = ATOM + r'(?:\s?/\s?' + ATOM + r')*\.?'
UNIT_RX = re.compile(r'(?:(?<=\s)|^)(' + UNIT_ALT + r')(?=\s|$|\d)')
NUM = r'(?:Free|free|FREE|\d+(?:\.\d+)?)'
TAIL = re.compile(r'^(.*?)\s*(?:(?<=\s)|^)(' + UNIT_ALT + r')\s*(' + NUM + r')\s+(' + NUM + r')\s*$')
RATE_ONLY = re.compile(r'^(?:(' + UNIT_ALT + r')\s+)?(' + NUM + r')\s+(' + NUM + r')$')
UNIT_ONLY = re.compile(r'^(' + UNIT_ALT + r')$')
CODE = re.compile(r'^(\d{4}\.\d{2}\.\d{2})\b\s*(.*)$')
HEAD = re.compile(r'^(\d{2}\.\d{2})\s+(?:(\d{4}\.\d{2}\.\d{2})\s*)?(.*)$')
CHAP = re.compile(r'^Chapter\s+(\d{1,2})\s*$')
SECT = re.compile(r'^Section\s+([0-9IVXL]+)\s*$')
JUNK = re.compile(r'^(Heading\s+Sub-heading.*|SAARC\s+GENERAL|1 2 3 4 5 6|Import Duty|Description of goods.*|Unit)$')
PAGE = re.compile(r'^(\d{1,3})$')

def clean(s):
    return re.sub(r'\s+', ' ', s).strip()

def code_key(c):
    return int(c.replace('.', ''))

rows, headings, chapters, sections = [], {}, {}, []
state = dict(sec=None, chap=None, head=None, page=1, last_code=0)
groups = {}           # dash level -> text
open_text = None      # row/heading/group currently collecting continuation text: ('row', row) | ('head', key) | ('group', lvl)
rate_queue = []       # rows lacking rates
notes = None
sec_notes = None

def dash_split(t):
    m = re.match(r'^(-{1,5})\s*(.*)$', t)
    return (len(m.group(1)), m.group(2)) if m else (0, t)

def try_close(row):
    """Try to extract unit + rates from the row text buffer."""
    txt = clean(row['buf'])
    m = re.match(r'^(.*?)\s*(?:(?<=\s)|^)(' + UNIT_ALT + r')?\s*(\d+(?:\.\d+)?),\s*For Least Developed Countries\s*(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$', txt)
    if m:
        row['buf'] = m.group(1); row['u'] = row['u'] or (m.group(2) or '')
        row['s'], row['g'], row['ldc'] = m.group(3), m.group(5), m.group(4)
        return True
    m = TAIL.match(txt)
    if m:
        row['buf'], row['u'], row['s'], row['g'] = m.group(1), m.group(2), m.group(3), m.group(4)
        return True
    # special/specific duties: find unit, rest is rate text
    um = None
    for mm in UNIT_RX.finditer(txt):
        rest = txt[mm.end():].strip()
        if re.match(r'^(Per|per|Rs|Rates|\d)', rest):
            um = mm; break
    if um:
        rest = txt[um.end():].strip()
        half = split_dup(rest)
        if half:
            row['buf'], row['u'], row['s'], row['g'] = txt[:um.start()], um.group(1), half[0], half[1]
            return True
    return False

def split_dup(rest):
    rest = clean(rest)
    if not rest: return None
    toks = rest.split(' ')
    # identical halves (with whitespace/typo tolerance)
    for k in range(1, len(toks)):
        a, b = ' '.join(toks[:k]), ' '.join(toks[k:])
        na, nb = re.sub(r'[\s\.]', '', a).lower(), re.sub(r'[\s\.]', '', b).lower()
        if na == nb or (len(na) > 12 and na.replace('ng', '') == nb.replace('ng', '')):
            return a, b
    return None
    return None

def new_row(code, text):
    row = dict(code=code, buf=text, u='', s='', g='', h=state['head'], c=state['chap'], pg=state['page'],
               path=[groups[k] for k in sorted(groups)])
    rows.append(row)
    return row

def set_group(lvl, text):
    for k in list(groups):
        if k >= lvl: del groups[k]
    groups[lvl] = text

def finalize_group():
    global open_text
    if open_text and open_text[0] == 'group':
        lvl = open_text[1]
        t = clean(groups.get(lvl, ''))
        t = re.sub(r'\s+(nos|kg)$', '', t)
        groups[lvl] = t.rstrip(' :').strip()

i = IMPORT_START
while i < EXPORT_START:
    l = clean(lines[i]); i += 1
    if not l: continue
    if PAGE.match(l):
        # page number sits alone at top of each page; ignore stray small ints inside notes
        n = int(l)
        if state['page'] is None or 0 < n - state['page'] <= 3:
            state['page'] = n
            continue
    if JUNK.match(l): continue
    m = SECT.match(l)
    if m:
        finalize_group(); open_text = None
        state['sec'] = m.group(1)
        t = []
        while i < EXPORT_START and not re.match(r'^(Notes?\.?|Chapter\s+\d)', lines[i].strip()):
            if lines[i].strip() and not PAGE.match(lines[i].strip()): t.append(lines[i].strip())
            i += 1
        sections.append(dict(n=state['sec'], t=clean(' '.join(t)), notes='', first=None))
        notes = sections[-1]; notes['_buf'] = []
        continue
    m = CHAP.match(l)
    if m:
        finalize_group(); open_text = None
        if notes is not None and '_buf' in notes:
            notes['notes'] = '\n'.join(notes.pop('_buf')).strip()
        state['chap'] = int(m.group(1)); state['head'] = None; groups.clear()
        if sections and sections[-1]['first'] is None: sections[-1]['first'] = state['chap']
        t = []
        while i < EXPORT_START and not re.match(r'^(Notes?\.?|Sub-?heading Notes?|Heading\s+Sub-heading|Additional Notes?|\d{2}\.\d{2}\s|Chapter\s+\d)', lines[i].strip()):
            s = lines[i].strip()
            if s and not PAGE.match(s): t.append(s)
            i += 1
            if len(t) > 6: break
        chapters[state['chap']] = dict(t=clean(' '.join(t)), s=state['sec'], notes='', pg=state['page'])
        notes = chapters[state['chap']]; notes['_buf'] = []
        continue
    # stacked bare codes: N codes on consecutive lines, then descs, then N units, then 2N rates (column-major)
    if re.match(r'^\d{4}\.\d{2}\.\d{2}$', l) and re.match(r'^\d{4}\.\d{2}\.\d{2}\s*$', lines[i].strip()):
        if notes is not None and '_buf' in notes:
            notes['notes'] = '\n'.join(notes.pop('_buf')).strip()
        finalize_group(); open_text = None
        codes = [l]
        while re.match(r'^\d{4}\.\d{2}\.\d{2}\s*$', lines[i].strip()):
            codes.append(lines[i].strip()); i += 1
        n = len(codes); items = []; units = []; rates = []
        while len(rates) < 2 * n and i < EXPORT_START:
            s2 = clean(lines[i]); i += 1
            if not s2 or JUNK.match(s2): continue
            if re.match(r'^' + UNIT_ALT + r'$', s2) and not items == []: units.append(s2); continue
            if re.match(r'^' + NUM + r'$', s2): rates.append(s2); continue
            if s2.startswith('-') or not items: items.append(s2)
            else: items[-1] += ' ' + s2
        descs, grps = items[-n:], items[:-n]
        for gtxt in grps:
            lv, t = dash_split(gtxt); set_group(lv, clean(t).rstrip(' :'))
        state['head'] = codes[0][:2] + '.' + codes[0][2:4]
        for k, c in enumerate(codes):
            state['last_code'] = code_key(c)
            row = new_row(c, descs[k] if k < len(descs) else '')
            row['u'] = units[k] if k < len(units) else ''
            row['s'] = rates[k] if k < len(rates) else ''
            row['g'] = rates[n + k] if n + k < len(rates) else ''
            row['stacked'] = True
        continue
    # structural matches (monotonic guards avoid cross-references like "heading 84.56 to")
    mc = CODE.match(l)
    if mc and code_key(mc.group(1)) > state['last_code'] and int(mc.group(1)[:2]) == state['chap']:
        if notes is not None and '_buf' in notes:
            notes['notes'] = '\n'.join(notes.pop('_buf')).strip()
        finalize_group()
        state['last_code'] = code_key(mc.group(1))
        state['head'] = mc.group(1)[:2] + '.' + mc.group(1)[2:4]
        row = new_row(mc.group(1), mc.group(2))
        if try_close(row): open_text = ('row', row, True)
        else:
            open_text = ('row', row, False); rate_queue.append(row)
        continue
    mh = HEAD.match(l)
    if mh and state['chap'] and int(mh.group(1)[:2]) == state['chap'] and \
            (state['head'] is None or mh.group(1) > state['head']) and \
            (mh.group(2) or re.match(r'^[A-Z"“\'(]', mh.group(3) or 'X')):
        if notes is not None and '_buf' in notes:
            notes['notes'] = '\n'.join(notes.pop('_buf')).strip()
        finalize_group(); groups.clear(); rate_queue.clear()
        state['head'] = mh.group(1)
        headings[state['head']] = dict(t=mh.group(3), c=state['chap'], pg=state['page'])
        if mh.group(2) and code_key(mh.group(2)) > state['last_code']:
            state['last_code'] = code_key(mh.group(2))
            row = new_row(mh.group(2), mh.group(3)); row['twin'] = True
            if try_close(row):
                headings[state['head']]['t'] = row['buf']; open_text = ('row', row, True)
            else:
                open_text = ('row', row, False); rate_queue.append(row)
        else:
            open_text = ('head', state['head'])
        continue
    if notes is not None and '_buf' in notes:
        notes['_buf'].append(l); continue
    if open_text and open_text[0] == 'row' and not open_text[2] and not l.startswith('-'):
        row = open_text[1]
        row['buf'] += ' ' + l
        if row.get('twin') and row['h'] in headings:
            headings[row['h']]['t'] += ' ' + l
        if try_close(row):
            if row in rate_queue: rate_queue.remove(row)
            if row.get('twin'): headings[row['h']]['t'] = row['buf']
            open_text = ('row', row, True)
        continue
    # rate-only line -> first row waiting for rates
    mr = RATE_ONLY.match(l)
    if mr and rate_queue:
        row = rate_queue.pop(0)
        if mr.group(1): row['u'] = mr.group(1)
        row['s'], row['g'] = mr.group(2), mr.group(3)
        continue
    mu = UNIT_ONLY.match(l)
    if mu and rate_queue:
        for r in rate_queue:
            if not r['u']:
                r['u'] = mu.group(1); break
        continue
    if l.startswith('-'):
        # a dash line: either a group label or a description for a stacked code with empty text
        finalize_group()
        lvl, t = dash_split(l)
        empty = [r for r in rate_queue if not clean(r['buf'])]
        if empty and lvl >= 2:
            r = empty[0]; r['buf'] = l; open_text = ('row', r, False)
            if try_close(r): rate_queue.remove(r)
            continue
        # if the open row is still collecting text and has no rates, a following dash line closes its text
        set_group(lvl, t); open_text = ('group', lvl)
        continue
    # continuation text
    if open_text:
        kind = open_text[0]
        if kind == 'row':
            row = open_text[1]
            if not open_text[2]:
                row['buf'] += ' ' + l
                if row.get('twin') and row['h'] in headings:
                    headings[row['h']]['t'] += ' ' + l
                if try_close(row):
                    if row in rate_queue: rate_queue.remove(row)
                    if row.get('twin'): headings[row['h']]['t'] = row['buf']
                    open_text = ('row', row, True)
                continue
            # row already complete: stray text; ignore
            continue
        if kind == 'head':
            headings[open_text[1]]['t'] += ' ' + l; continue
        if kind == 'group':
            groups[open_text[1]] = groups.get(open_text[1], '') + ' ' + l
            # "-Other: nos 80 80" style lines ending in rates belong to a waiting row
            continue

finalize_group()
if notes is not None and '_buf' in notes:
    notes['notes'] = '\n'.join(notes.pop('_buf')).strip()

# ---- post-process rows ----
for r in rows:
    if not r['s']:
        txt = clean(r['buf'])
        for mm in UNIT_RX.finditer(txt):
            rest = txt[mm.end():].strip()
            if re.match(r'^(Per|per|Rs|Rates|\d)', rest):
                r['buf'], r['u'] = txt[:mm.start()], mm.group(1)
                r['s'] = r['g'] = rest; r['flag'] = 'check'
                break

out = []
for r in rows:
    lvl, d = dash_split(clean(r['buf']))
    d = d.strip().rstrip(':').strip()
    # recompute path from dash level captured at creation time
    path = [clean(p).rstrip(' :') for p in r['path']]
    # keep only groups shallower than this row's level
    if lvl:
        path = path[:max(0, lvl - 1)] if len(path) >= lvl - 1 else path
    o = dict(code=r['code'], d=d, lvl=lvl, u=r['u'], s=r['s'], g=r['g'], h=r['h'], c=r['c'], pg=r['pg'], p=path)
    if r.get('ldc'): o['ldc'] = r['ldc']
    if r.get('flag'): o['flag'] = r['flag']
    out.append(o)
for h in headings.values():
    h['t'] = clean(h['t']).rstrip(' .')

# ---- export tariff ----
export = {}
cur = None
for l in lines[EXPORT_START + 1:]:
    s = clean(l)
    if not s or PAGE.match(s) or s.startswith(('Heading Sub-heading', 'Export Customs', 'Duty Rate', 'specified', 'except otherwise', '1 2 3 4', '(Related')):
        continue
    if re.match(r'^\d\.\s', s) and cur is None: continue
    m = re.search(r'(\d{4}\.\d{2}\.\d{2})\s*(.*)$', s)
    if m:
        cur = m.group(1); export[cur] = m.group(2)
    elif cur and not re.match(r'^(\d{2}\.\d{2}\s|-)', s):
        export[cur] += ' ' + s
    else:
        cur = None
ex = {}
for k, v in export.items():
    v = clean(v)
    m = re.search(r'((?:Per\s+\w+\s*)?Rs\.?\s*[\d\.,]+(?:\s*per\s+[\w ]+)?|\d+(?:\.\d+)?\s*%?)\s*$', v, re.I)
    ex[k] = dict(d=(v[:m.start()] if m else v).strip(' -:'), r=(m.group(1).strip() if m else ''))

json.dump(dict(rows=out, headings=headings, chapters=chapters, sections=sections, export=ex),
          open(__import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'parsed.json', 'w'), ensure_ascii=False)
bad = [r for r in out if not r['s'] or not r['g']]
print('rows', len(out), 'headings', len(headings), 'chapters', len(chapters), 'sections', len(sections), 'export', len(ex))
print('rows missing rate', len(bad), '| missing unit', sum(1 for r in out if not r['u']), '| empty desc', sum(1 for r in out if not r['d']))
for r in bad[:80]: print(' ', r['code'], '|', r['d'][:90], '|', r['u'], r['s'], r['g'])
