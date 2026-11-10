"""Story-grade visuals for the trade-partner pages: the hero trade-flow ribbon,
Sankey flows, product treemap, the "Rs 100" waffle, an illustrated journey scene
and a downloadable social poster. All inline SVG generated at build time from the
same official figures as the tables (nothing estimated). Uses viz.py's palette
classes (c1..c5, cg) so everything stays theme-aware and exportable.
"""
import math
from viz import esc, cut, W, _svg

CLS = ['c1', 'c2', 'c3', 'c4', 'c5']
def _on(c):
    return 'onc' if c in ('c1', 'c2') else 'ond'

# ---------------------------------------------------------------- hero flow ribbon (always on the dark hero)
def flow(pflag, pname, imp, exp, imp_s, exp_s):
    mx = max(imp, exp, 1.0)
    wi = max(2.0, 54.0 * imp / mx); we = max(2.0, 54.0 * exp / mx)
    b = ['<defs><linearGradient id="fgi" x1="0" x2="1"><stop offset="0" stop-color="#5AA2FF"/><stop offset="1" stop-color="#7FE0FF"/></linearGradient>'
         '<linearGradient id="fge" x1="1" x2="0"><stop offset="0" stop-color="#FF9A5A"/><stop offset="1" stop-color="#FFC56B"/></linearGradient></defs>']
    pi = 'M118 118 C 230 %d, 370 %d, 482 118' % (44, 44)
    pe = 'M482 176 C 370 %d, 230 %d, 118 176' % (246, 246)
    b.append('<path d="%s" fill="none" stroke="url(#fgi)" stroke-width="%.1f" stroke-linecap="round" opacity=".92"><title>Imports %s</title></path>' % (pi, wi, esc(imp_s)))
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="%.1f" stroke-linecap="round" class="dash" opacity=".55"/>' % (pi, max(1.2, min(wi * .16, 3.5))))
    b.append('<path d="%s" fill="none" stroke="url(#fge)" stroke-width="%.1f" stroke-linecap="round" opacity=".95"><title>Exports %s</title></path>' % (pe, we, esc(exp_s)))
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="%.1f" stroke-linecap="round" class="dash" opacity=".55"/>' % (pe, max(1.0, min(we * .16, 3.5))))
    for cx, fl, nm in ((70, pflag, pname), (530, '\U0001F1F3\U0001F1F5', 'Nepal')):
        b.append('<circle cx="%d" cy="147" r="46" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.35)" stroke-width="1.5"/>' % cx)
        b.append('<text x="%d" y="162" font-size="44" text-anchor="middle">%s</text>' % (cx, fl))
        b.append('<text x="%d" y="216" font-size="14" font-weight="700" fill="#fff" text-anchor="middle">%s</text>' % (cx, esc(cut(nm, 16))))
    b.append('<text x="300" y="%.0f" font-size="16" font-weight="700" fill="#BFE3FF" text-anchor="middle">Imports %s →</text>' % (62 - wi / 2 - 12, esc(imp_s)))
    b.append('<text x="300" y="%.0f" font-size="16" font-weight="700" fill="#FFD2AE" text-anchor="middle">← Exports %s</text>' % (228 + we / 2 + 24, esc(exp_s)))
    return ('<svg class="flow" viewBox="0 0 %d 290" role="img" aria-label="Trade flow between %s and Nepal: imports %s, exports %s" '
            'xmlns="http://www.w3.org/2000/svg">%s</svg>' % (W, esc(pname), esc(imp_s), esc(exp_s), ''.join(b)))

# ---------------------------------------------------------------- sankey: source -> groups
def sankey(src_label, items, money, label, note):
    """items: [(name, icon, value, cls)]"""
    total = sum(v for _, _, v, _ in items) or 1.0
    H = 230.0; top = 30.0; gap = 8.0
    yl = top; yr = top; b = []
    b.append('<text x="0" y="16" class="t" font-size="12.5" font-weight="700">%s</text>' % src_label)
    b.append('<text x="296" y="16" class="m" font-size="11.5">%s</text>' % esc(note))
    for nm, ic, v, c in items:
        h = max(1.5, H * v / total)
        slot = max(h, 20.0)
        b.append('<path d="M14 %.1f C 155 %.1f, 155 %.1f, 296 %.1f L 296 %.1f C 155 %.1f, 155 %.1f, 14 %.1f Z" class="%s" opacity=".42">'
                 '<title>%s — %s (%.1f%%)</title></path>' % (yl, yl, yr, yr, yr + h, yr + h, yl + h, yl + h, c, esc(nm), esc(money(v)), v / total * 100))
        b.append('<rect x="0" y="%.1f" width="14" height="%.1f" rx="2" class="%s"/>' % (yl, h, c))
        b.append('<rect x="296" y="%.1f" width="14" height="%.1f" rx="2" class="%s"/>' % (yr, h, c))
        ty = yr + min(h, slot) / 2 + 4.5 if h >= 20 else yr + 13
        b.append('<text x="320" y="%.1f" class="t" font-size="12.5" font-weight="600">%s %s</text>' % (ty, ic, esc(cut(nm, 22))))
        b.append('<text x="600" y="%.1f" class="m" font-size="12" text-anchor="end">%.0f%% · %s</text>' % (ty, v / total * 100, esc(money(v))))
        yl += h; yr += slot + gap
    tsv = 'Product group\tShare %\tValue\n' + '\n'.join('%s\t%.1f\t%s' % (nm, v / total * 100, money(v)) for nm, _, v, _ in items)
    return _svg(int(yr) + 2, ''.join(b), label), tsv

# ---------------------------------------------------------------- treemap
def _squarify(vals, x, y, w, h):
    tot = sum(vals) or 1.0
    area = [v * w * h / tot for v in vals]
    rects = []; i = 0
    def worst(r, short):
        s = sum(r)
        return max(short * short * max(r) / (s * s), (s * s) / (short * short * min(r)))
    while i < len(area):
        short = max(min(w, h), 0.01)
        row = [area[i]]; i += 1
        while i < len(area) and worst(row + [area[i]], short) <= worst(row, short):
            row.append(area[i]); i += 1
        s = sum(row)
        if w >= h:
            rw = s / max(h, 0.01); yy = y
            for v in row:
                rh = v / max(rw, 0.01); rects.append((x, yy, rw, rh)); yy += rh
            x += rw; w -= rw
        else:
            rh = s / max(w, 0.01); xx = x
            for v in row:
                rw = v / max(rh, 0.01); rects.append((xx, y, rw, rh)); xx += rw
            y += rh; h -= rh
    return rects

def treemap(items, money, label):
    """items: [(name, icon, value, cls)] — sorted here; draws every item to scale."""
    items = sorted([it for it in items if it[2] > 0], key=lambda t: -t[2])
    total = sum(v for _, _, v, _ in items) or 1.0
    Ht = 330
    rects = _squarify([v for _, _, v, _ in items], 0, 0, W, Ht)
    b = []
    for (nm, ic, v, c), (x, y, w, h) in zip(items, rects):
        b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" class="%s"><title>%s — %s (%.1f%%)</title></rect>'
                 % (x + 1.5, y + 1.5, max(w - 3, 1), max(h - 3, 1), c, esc(nm), esc(money(v)), v / total * 100))
        on = _on(c)
        if w > 78 and h > 46:
            chars = int((w - 18) / 6.6)
            big = w > 150 and h > 80
            if big:
                b.append('<text x="%.1f" y="%.1f" font-size="22">%s</text>' % (x + 11, y + 32, ic))
                b.append('<text x="%.1f" y="%.1f" class="%s" font-size="13" font-weight="700">%s</text>' % (x + 11, y + 54, on, esc(cut(nm, chars))))
                b.append('<text x="%.1f" y="%.1f" class="%s" font-size="12" opacity=".9">%s · %.0f%%</text>' % (x + 11, y + 72, on, esc(money(v)), v / total * 100))
            else:
                b.append('<text x="%.1f" y="%.1f" class="%s" font-size="11.5" font-weight="700">%s %s</text>' % (x + 9, y + 20, on, ic, esc(cut(nm, max(chars - 3, 4)))))
                b.append('<text x="%.1f" y="%.1f" class="%s" font-size="11" opacity=".9">%s</text>' % (x + 9, y + 36, on, esc(money(v))))
        elif w > 34 and h > 26:
            b.append('<text x="%.1f" y="%.1f" font-size="15" text-anchor="middle">%s</text>' % (x + w / 2, y + h / 2 + 5, ic))
    tsv = 'Product\tValue\tShare %\n' + '\n'.join('%s\t%s\t%.1f' % (nm, money(v), v / total * 100) for nm, _, v, _ in items)
    return _svg(Ht, ''.join(b), label), tsv

# ---------------------------------------------------------------- waffle: "of every Rs 100"
def waffle(p_imp, p_exp, name):
    def grid(x0, p, c, l1, l2):
        n = int(round(p)); out = []
        for i in range(100):
            r, col = divmod(i, 10)
            out.append('<rect x="%d" y="%d" width="17" height="17" rx="4" class="%s"%s/>'
                       % (x0 + col * 21, 8 + r * 21, c if i < n else 'wf0', '' if i < n else ''))
        rs = ('%.2f' % p).rstrip('0').rstrip('.') if p >= 0.01 else '0.01'
        out.append('<text x="%d" y="244" class="t" font-size="15" font-weight="700">%sRs %s of every Rs 100</text>' % (x0, '' if p >= 0.01 else 'under ', rs))
        out.append('<text x="%d" y="263" class="m" font-size="12">%s</text>' % (x0, l1))
        out.append('<text x="%d" y="279" class="m" font-size="12">%s</text>' % (x0, esc(l2)))
        return ''.join(out)
    body = grid(0, p_imp, 'c1', 'Nepal spends on imports', 'goes to ' + name) + \
           grid(330, p_exp, 'c2', 'Nepal earns from exports', 'comes from ' + name)
    tsv = 'Measure\tRs per Rs 100\nNepal import spending going to %s\t%.2f\nNepal export earnings from %s\t%.2f' % (name, p_imp, name, p_exp)
    return _svg(288, body, 'Of every Rs 100: %s' % name), tsv

# ---------------------------------------------------------------- illustrated journey
def journey(kind, stops, label):
    """kind: himalaya | sea | land | corridor ; stops: [(label, sub)]"""
    pts = {'himalaya': [(50, 150), (172, 124), (300, 66), (428, 122), (552, 150)],
           'sea': [(42, 152), (140, 158), (248, 150), (356, 132), (458, 120), (556, 106)],
           'land': [(64, 142), (222, 138), (392, 128), (540, 112)],
           'corridor': [(50, 146), (172, 140), (300, 132), (424, 124), (552, 112)]}[kind][:len(stops)]
    gid = 'jg' + kind
    b = ['<defs><linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B1733"/><stop offset="1" stop-color="#1F3F78"/></linearGradient></defs>' % gid,
         '<rect x="0" y="0" width="600" height="212" rx="12" fill="url(#%s)"/>' % gid]
    for sx, sy, sr in ((60, 26, 1.2), (130, 44, .9), (220, 20, 1.1), (380, 30, 1), (470, 18, 1.3), (540, 46, .9), (310, 14, .8)):
        b.append('<circle cx="%d" cy="%d" r="%.1f" fill="#fff" opacity=".7"/>' % (sx, sy, sr))
    if kind == 'himalaya':
        b.append('<path d="M0 170 L70 110 L130 150 L210 70 L262 118 L300 44 L345 112 L400 78 L470 140 L530 104 L600 160 L600 212 L0 212 Z" fill="#2A4A85"/>')
        b.append('<path d="M300 44 L318 70 L304 66 L296 76 L286 64 Z M210 70 L224 90 L212 87 L204 94 L198 84 Z M400 78 L412 95 L402 92 L394 99 L390 90 Z" fill="#EAF2FF"/>')
        b.append('<path d="M0 190 L90 150 L180 176 L300 112 L420 172 L520 148 L600 182 L600 212 L0 212 Z" fill="#17305E"/>')
    elif kind == 'sea':
        b.append('<rect x="0" y="150" width="278" height="62" fill="#15508A"/>')
        for wy in (166, 180, 194):
            b.append('<path d="M0 %d q 14 -7 28 0 t 28 0 t 28 0 t 28 0 t 28 0 t 28 0 t 28 0 t 28 0 t 28 0 t 26 0" fill="none" stroke="#6FB7F2" stroke-width="1.4" opacity=".6"/>' % wy)
        b.append('<path d="M262 212 L262 152 L330 138 L420 124 L500 96 L560 70 L600 84 L600 212 Z" fill="#234A7C"/>')
        b.append('<path d="M470 110 L520 60 L548 84 L574 52 L600 78 L600 130 Z" fill="#2F5C99"/><path d="M574 52 L584 66 L576 64 L570 70 L566 62 Z" fill="#EAF2FF"/>')
    elif kind == 'corridor':
        b.append('<path d="M0 168 Q150 150 300 156 T600 130 L600 212 L0 212 Z" fill="#234A7C"/>')
        b.append('<path d="M286 120 L314 120 L330 212 L270 212 Z" fill="#15508A"/><path d="M262 128 L338 128" stroke="#EAF2FF" stroke-width="3"/>')
        b.append('<path d="M500 112 L548 62 L600 100 L600 140 Z" fill="#2F5C99"/>')
    else:
        b.append('<path d="M0 166 Q160 148 320 152 T600 128 L600 212 L0 212 Z" fill="#234A7C"/>')
        b.append('<path d="M470 122 L530 66 L562 92 L600 62 L600 140 Z" fill="#2F5C99"/><path d="M530 66 L542 82 L532 80 L526 86 L520 78 Z" fill="#EAF2FF"/>')
    d = 'M' + ' L'.join('%d %d' % p for p in pts)
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="2.2" stroke-dasharray="2 7" stroke-linecap="round" opacity=".9"/>' % d)
    for (x, y), (lab, sub) in zip(pts, stops):
        b.append('<circle cx="%d" cy="%d" r="6" fill="#FFD166" stroke="#0B1733" stroke-width="2"/>' % (x, y))
        b.append('<text x="%d" y="%d" font-size="10.5" font-weight="700" fill="#fff" text-anchor="middle">%s</text>' % (x, y + 21, esc(lab)))
        if sub:
            b.append('<text x="%d" y="%d" font-size="9.5" fill="#C9DBF5" text-anchor="middle">%s</text>' % (x, y + 33, esc(sub)))
    def mover(icon, seg, dur):
        return ('<text font-size="19" text-anchor="middle" dy="-9">%s<animateMotion dur="%ss" repeatCount="indefinite" path="%s"/></text>'
                % (icon, dur, 'M' + ' L'.join('%d %d' % p for p in seg)))
    if kind == 'sea':
        b.append(mover('\U0001F6A2', pts[:3], 7)); b.append(mover('\U0001F682', pts[2:], 8))
    else:
        b.append(mover('\U0001F69B', pts, 10))
    tsv = 'Step\tStage\tDetail\n' + '\n'.join('%d\t%s\t%s' % (i + 1, lab, sub) for i, (lab, sub) in enumerate(stops))
    return _svg(212, ''.join(b), label), tsv

# ---------------------------------------------------------------- social poster (portrait, self-contained colours)
def poster(pflag, name, fy, imp_s, exp_s, bal_s, imp, exp, deficit, top_imp, top_exp, rank, nrank):
    mx = max(imp, exp, 1.0)
    wi = max(4.0, 480.0 * imp / mx); we = max(4.0, 480.0 * exp / mx)
    b = ['<defs><linearGradient id="pbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1530"/><stop offset=".6" stop-color="#13306B"/><stop offset="1" stop-color="#0D5A6B"/></linearGradient></defs>',
         '<rect width="540" height="675" fill="url(#pbg)"/>',
         '<circle cx="470" cy="70" r="150" fill="#5AA2FF" opacity=".10"/><circle cx="60" cy="640" r="170" fill="#FF9A5A" opacity=".08"/>',
         '<text x="30" y="42" font-size="12" font-weight="700" fill="#9FD8FF" letter-spacing="1.5">CUSTOMSNEPAL.COM</text>',
         '<text x="510" y="42" font-size="12" fill="#C9DBF5" text-anchor="end">FY %s</text>' % esc(fy),
         '<text x="270" y="124" font-size="58" text-anchor="middle" fill="#7FE0FF">\U0001F1F3\U0001F1F5 ⇄ %s</text>' % pflag,
         '<text x="270" y="172" font-size="30" font-weight="800" fill="#fff" text-anchor="middle">Nepal–%s trade</text>' % esc(cut(name, 20)),
         '<text x="270" y="196" font-size="12.5" fill="#C9DBF5" text-anchor="middle">Nepal’s #%d trade partner of %d</text>' % (rank, nrank)]
    for x, lab, val, col in ((30, 'IMPORTS', imp_s, '#8EC0FF'), (192, 'EXPORTS', exp_s, '#FFB08A'), (348, 'BALANCE', bal_s, '#FF9B9B' if deficit else '#7EE2A8')):
        b.append('<text x="%d" y="240" font-size="10.5" fill="#C9DBF5" letter-spacing="1.2">%s</text>' % (x, lab))
        b.append('<text x="%d" y="264" font-size="16.5" font-weight="800" fill="%s">%s</text>' % (x, col, esc(val)))
    b.append('<rect x="30" y="292" width="%.1f" height="26" rx="6" fill="#5AA2FF"/>' % wi)
    b.append('<rect x="30" y="326" width="%.1f" height="26" rx="6" fill="#FF9A5A"/>' % we)
    b.append('<line x1="30" y1="380" x2="510" y2="380" stroke="#fff" opacity=".18"/>')
    for x0, head, rows in ((30, 'TOP IMPORTS', top_imp), (285, 'TOP EXPORTS', top_exp)):
        b.append('<text x="%d" y="408" font-size="10.5" font-weight="700" fill="#9FD8FF" letter-spacing="1.2">%s</text>' % (x0, head))
        if not rows:
            b.append('<text x="%d" y="440" font-size="12.5" fill="#C9DBF5">Negligible</text>' % x0)
        for i, (ic, nm, vs) in enumerate(rows[:4]):
            y = 440 + i * 46
            b.append('<text x="%d" y="%d" font-size="13" font-weight="700" fill="#fff">%s %s</text>' % (x0, y, ic, esc(cut(nm, 24))))
            b.append('<text x="%d" y="%d" font-size="12" fill="#C9DBF5">%s</text>' % (x0, y + 17, esc(vs)))
    b.append('<text x="30" y="646" font-size="10.5" fill="#C9DBF5">Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s</text>' % esc(fy))
    return ('<svg class="vz poster" viewBox="0 0 540 675" role="img" aria-label="Nepal–%s trade poster" xmlns="http://www.w3.org/2000/svg">%s</svg>'
            % (esc(name), ''.join(b)))

# ---------------------------------------------------------------- customs take: revenue per Rs 100 of goods
def revenue(take, avg, name, rev_s):
    """take / avg: revenue collected at customs as % of import value (this partner / all imports)."""
    mx = max(take, avg, 1.0) * 1.18
    def bar(y, p, cls, l1):
        w = max(4.0, 600.0 * p / mx)
        inside = w > 190
        return ('<text x="0" y="%d" class="m" font-size="12">%s</text>'
                '<rect x="0" y="%d" width="600" height="30" rx="8" class="wf0"/>'
                '<rect x="0" y="%d" width="%.1f" height="30" rx="8" class="%s"/>'
                '<text x="%.1f" y="%d" class="%s" font-size="14" font-weight="700"%s>Rs %.1f per Rs 100</text>'
                % (y, esc(l1), y + 8, y + 8, w, cls,
                   (w - 10) if inside else (w + 10), y + 28, ('onc' if cls == 'c1' else 'ond') if inside else 't',
                   ' text-anchor="end"' if inside else '', p))
    body = bar(12, take, 'c1', 'Goods from %s — collected at customs' % name) + \
           bar(72, avg, 'cg', 'All of Nepal’s imports — average')
    tsv = ('Measure\tValue\nRevenue collected at customs on imports from %s\t%s\n'
           'Collected per Rs 100 of goods from %s\t%.1f\nCollected per Rs 100, all imports\t%.1f' % (name, rev_s, name, take, avg))
    return _svg(116, body, 'Revenue collected at customs on goods from %s' % name), tsv

# ---------------------------------------------------------------- who else sells it: supplier share per product
def rivals(rows, me):
    """rows: [(label, code, [(supplier name, pct, is_me)])] — one 100% bar per product."""
    b = []; tsv = ['Product\tHS code\tSupplier\tShare of Nepal imports %']
    for i, (lab, code, segs) in enumerate(rows):
        y = i * 62
        b.append('<text x="0" y="%d" class="t" font-size="13" font-weight="600">%s</text>' % (y + 14, esc(cut(lab, 62))))
        b.append('<rect x="0" y="%d" width="600" height="22" rx="6" class="wf0"/>' % (y + 21))
        x = 0.0; k = 0
        for nm, pct, is_me in segs:
            w = 600.0 * min(pct, 100.0) / 100.0
            if w < 1.2:
                tsv.append('%s\t%s\t%s\t%.1f' % (lab, code, nm, pct)); continue
            cls = 'c1' if is_me else 'cg'
            op = '' if is_me else ' opacity="%.2f"' % (0.95, 0.68, 0.45)[min(k, 2)]
            if not is_me:
                k += 1
            b.append('<rect x="%.1f" y="%d" width="%.1f" height="22" rx="%d" class="%s"%s><title>%s — %.1f%%</title></rect>'
                     % (x, y + 21, max(w - 1.5, 1), 6 if w > 14 else 2, cls, op, esc(nm), pct))
            txt = '%s %.0f%%' % (cut(nm, 16), pct)
            if w > len(txt) * 7.2 + 12:
                b.append('<text x="%.1f" y="%d" class="%s" font-size="12" font-weight="600">%s</text>'
                         % (x + 8, y + 37, 'onc' if is_me else 'ond', esc(txt)))
            x += w
            tsv.append('%s\t%s\t%s\t%.1f' % (lab, code, nm, pct))
        rest = 100.0 - sum(p for _, p, _ in segs)
        if rest > 0.05:
            tsv.append('%s\t%s\tAll other countries\t%.1f' % (lab, code, rest))
            if 600 - x > 96:
                b.append('<text x="592" y="%d" class="m" font-size="11" text-anchor="end">others %.0f%%</text>' % (y + 37, rest))
    return _svg(len(rows) * 62 - 12, ''.join(b), 'Supplier shares for the top products Nepal buys from %s' % me), '\n'.join(tsv)

# ---------------------------------------------------------------- hub world map (choropleth, links to partner pages)
WM_BINS = [(1e8, 'Rs 1 kharba +'), (1e7, 'Rs 10 arba +'), (1e6, 'Rs 1 arba +'), (1e5, 'Rs 10 crore +'), (0, 'under Rs 10 crore')]

def worldmap(shapes, total, href, label, money):
    """shapes: iso -> svg path; total: iso -> two-way trade (Rs '000); href: iso -> partner page; label: iso -> name."""
    def cls(v):
        for i, (th, _) in enumerate(WM_BINS):
            if v >= th and v > 0:
                return 'wm%d' % (5 - i)
        return 'wm0'
    b = ['<rect x="0" y="0" width="960" height="500" rx="14" class="wmsea"/>']
    for iso, d in shapes.items():
        if iso == 'NPL':
            continue
        v = total.get(iso, 0.0)
        tip = '%s — %s two-way trade with Nepal' % (label.get(iso, iso), money(v)) if v else '%s — no recorded trade' % label.get(iso, iso)
        path = '<path d="%s" class="%s"><title>%s</title></path>' % (d, cls(v), esc(tip))
        b.append('<a href="%s" aria-label="%s">%s</a>' % (href[iso], esc(tip), path) if iso in href else path)
    if 'NPL' in shapes:
        b.append('<path d="%s" class="wmnp"><title>Nepal</title></path>' % shapes['NPL'])
    if 'NPL' in shapes:
        import re as _re
        pts = [(float(x), float(y)) for x, y in _re.findall(r'(-?[\d.]+),(-?[\d.]+)', shapes['NPL'])]
        cx = sum(x for x, _ in pts) / len(pts); cy = sum(y for _, y in pts) / len(pts)
        b.append('<circle cx="%.1f" cy="%.1f" r="15" class="wmring"/>'
                 '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="wmring"/>'
                 '<text x="%.1f" y="%.1f" class="t wmlab" font-size="14" font-weight="700" text-anchor="middle">Nepal</text>'
                 % (cx, cy, cx, cy - 15, cx, cy - 44, cx, cy - 50))
    x = 24
    for i, (_, lab) in enumerate(reversed(WM_BINS)):
        b.append('<rect x="%d" y="462" width="16" height="12" rx="3" class="wm%d"/><text x="%d" y="472" class="m" font-size="11">%s</text>'
                 % (x, i + 1, x + 21, esc(lab)))
        x += 30 + len(lab) * 6
    return ('<svg class="vz wmap" viewBox="0 0 960 500" role="img" aria-label="World map shaded by each country’s trade with Nepal" '
            'xmlns="http://www.w3.org/2000/svg">%s</svg>' % ''.join(b))


# ---------------------------------------------------------------- trend: imports vs exports over the years
def trend(years, hist, money, name, heads=('Imports from %s', 'Exports to %s')):
    """years: ['2079/80', ...]; hist: [[imp, exp], ...] in Rs '000. Two lines, every point labelled."""
    n = len(years); mx = max(max(h) for h in hist) or 1.0
    X0, X1, Y0, Y1 = 60.0, 540.0, 34.0, 190.0
    xs = [X0 + (X1 - X0) * i / max(n - 1, 1) for i in range(n)]
    yy = lambda v: Y1 - (Y1 - Y0) * v / mx
    b = ['<line x1="0" y1="%.0f" x2="600" y2="%.0f" class="ax"/>' % (Y1, Y1)]
    for i, y in enumerate(years):
        b.append('<text x="%.1f" y="%.0f" class="m" font-size="12" text-anchor="middle">%s</text>' % (xs[i], Y1 + 20, esc(y)))
    for k, cls in ((0, 'c1'), (1, 'c2')):
        pts = [(xs[i], yy(hist[i][k])) for i in range(n)]
        b.append('<polyline points="%s" fill="none" class="s%s" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
                 % (' '.join('%.1f,%.1f' % p for p in pts), cls[1]))
        for i, (x, y) in enumerate(pts):
            other = yy(hist[i][1 - k])
            above = y <= other                       # the higher line labels above, the lower one below
            ly = y - 10 if above else y + 20
            if not above and ly > Y1 - 4:
                ly = y - 10 if abs(y - other) > 30 else Y1 - 6
            b.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="%s"/>' % (x, y, cls))
            b.append('<text x="%.1f" y="%.1f" class="t" font-size="11.5" font-weight="600" text-anchor="middle">%s</text>'
                     % (x, ly, esc(money(hist[i][k]).replace('Rs ', ''))))
    tsv = 'Fiscal year\t%s\t%s\n' % (heads[0] % name, heads[1] % name) + '\n'.join(
        '%s\t%s\t%s' % (years[i], money(hist[i][0]), money(hist[i][1])) for i in range(n))
    return _svg(216, ''.join(b), 'Nepal’s imports from and exports to %s by fiscal year' % name), tsv


CSS = """
.cphero{background:linear-gradient(135deg,#0A1530,#13306B 60%,#0D5A6B);color:#fff;margin-top:12px;padding:34px 0 28px;position:relative;overflow:hidden}
.cphero::before{content:"";position:absolute;right:-120px;top:-140px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(90,162,255,.28),transparent 65%)}
.cphero::after{content:"";position:absolute;left:-140px;bottom:-200px;width:440px;height:440px;border-radius:50%;background:radial-gradient(circle,rgba(255,154,90,.16),transparent 65%)}
.cphero .wrap{max-width:1120px;position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.02fr) minmax(0,.98fr);gap:26px;align-items:center}
.cpkick{font:600 .72rem var(--mono);letter-spacing:.14em;text-transform:uppercase;color:#9FD8FF}
.cphero h1{font-family:"Bricolage Grotesque",var(--f);font-size:clamp(2.1rem,1.1rem + 4.6vw,3.9rem);line-height:1;margin:.3em 0 .18em;color:#fff;letter-spacing:-.035em;font-weight:800}
.cphero h1 .arr{color:#7FE0FF;font-weight:600}
.cpnp{color:rgba(255,255,255,.7);font-size:1rem}
.cplede{color:rgba(255,255,255,.86);max-width:46ch;margin:.7em 0 0;font-size:1.02rem;line-height:1.5}
.cpstats{display:flex;flex-wrap:wrap;gap:14px 30px;margin-top:22px}
.cpstat span{display:block;font-size:.7rem;color:rgba(255,255,255,.66);text-transform:uppercase;letter-spacing:.1em}
.cpstat b{display:block;font:800 clamp(1.25rem,1rem + 1.1vw,1.75rem) "Bricolage Grotesque",var(--f);letter-spacing:-.02em;margin-top:2px;font-variant-numeric:tabular-nums}
.cpstat.i b{color:#8EC0FF}.cpstat.e b{color:#FFB08A}.cpstat.neg b{color:#FF9B9B}.cpstat.pos b{color:#7EE2A8}
.cphero .keycopy{margin-top:18px;background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.3);color:#fff}
.cphero .keycopy:hover{background:rgba(255,255,255,.18);border-color:#fff;color:#fff}
svg.flow{display:block;width:100%;height:auto;font-family:var(--f)}
svg.flow .dash{stroke-dasharray:3 15;animation:cpflow 1.1s linear infinite}
@keyframes cpflow{to{stroke-dashoffset:-18}}
.cpfacts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0 6px}
.cpfact{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:13px 14px;min-width:0}
.cpfact .ic{font-size:1.6rem;line-height:1}
.cpfact span{display:block;font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:8px}
.cpfact b{display:block;font-size:.98rem;line-height:1.25;margin-top:2px;overflow-wrap:anywhere}
.cpfact small{display:block;color:var(--muted);font-size:.78rem;margin-top:2px}
.vz .wf0{fill:var(--border)}
.cpshare{display:grid;grid-template-columns:minmax(0,380px) minmax(0,1fr);gap:22px;align-items:center;margin:1em 0}
.cpshare .vzfig{margin:0;padding:10px}
svg.vz.poster{min-width:0;border-radius:10px}
.cpshare h3{margin:0 0 .4em;font-size:1.15rem}.cpshare p{color:var(--fg2);margin:.3em 0 .8em}
.cpcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:.8em 0 1.4em}
.cpcard{display:block;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 14px;color:var(--fg);text-decoration:none;transition:transform .15s,border-color .15s,box-shadow .15s}
.cpcard:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 10px 24px -14px rgba(16,32,64,.5);text-decoration:none}
.cpcard .fl{font-size:1.7rem;line-height:1}.cpcard b{display:block;margin:6px 0 8px}
.cpcard .mb{height:7px;border-radius:5px;background:var(--border);overflow:hidden;margin-top:4px}.cpcard .mb i{display:block;height:100%;border-radius:5px}
.cpcard .mb .a{background:var(--v1)}.cpcard .mb .b{background:var(--v2)}
.cpcard small{display:flex;justify-content:space-between;color:var(--muted);font-size:.74rem;margin-top:6px}
.vz .s1{stroke:var(--v1)}.vz .s2{stroke:var(--v2)}.vz .ax{stroke:var(--border);stroke-width:1}
.vz .wmsea{fill:var(--bg)}
.vz .wm0{fill:var(--border)}.vz .wm1{fill:#cfe1f7}.vz .wm2{fill:#9cc2ee}.vz .wm3{fill:#6aa2e3}.vz .wm4{fill:#3a7fd2}.vz .wm5{fill:#184e9e}
.vz .wmnp{fill:var(--v2)}.vz .wmring{fill:none;stroke:var(--v2);stroke-width:2}
svg.wmap path{stroke:var(--card);stroke-width:.5;vector-effect:non-scaling-stroke}
svg.wmap a path{cursor:pointer;transition:opacity .12s}svg.wmap a:hover path,svg.wmap a:focus path{opacity:.72;stroke:var(--fg);stroke-width:1.2}
svg.vz.wmap{min-width:640px}
.vz .wmlab{paint-order:stroke;stroke:var(--card);stroke-width:4px;stroke-linejoin:round}
@media(prefers-color-scheme:dark){.vz .wm1{fill:#1c3558}.vz .wm2{fill:#234a80}.vz .wm3{fill:#2d64ad}.vz .wm4{fill:#4a8be0}.vz .wm5{fill:#9cc6f8}}
.xlink{margin:1em 0;background:var(--accent-bg);border:1px solid var(--border);border-radius:12px;padding:10px 14px;font-size:.93rem;line-height:1.55}
footer p.explore{line-height:1.7}
dl.qa{margin:.6em 0 1em}dl.qa dt{font-weight:700;margin-top:.9em}dl.qa dd{margin:.25em 0 0;color:var(--fg2);line-height:1.6}
table.ptbl a.dguide{display:inline-block;margin-left:6px;font-size:.7rem;font-weight:600;color:var(--accent);border:1px solid var(--border);border-radius:999px;padding:1px 8px;text-decoration:none;white-space:nowrap}
table.ptbl a.dguide:hover{border-color:var(--accent)}
table.ptbl .tk{display:block;font-size:.7rem;color:var(--muted);font-weight:400}
@media(max-width:860px){.cphero .wrap{grid-template-columns:1fr}.cpfacts{grid-template-columns:repeat(2,minmax(0,1fr))}.cpshare{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){svg.flow .dash{animation:none}}
"""

def write_assets(pub):
    css_path = pub / 'seo.css'
    cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
    if '.cphero{' not in cur:
        css_path.write_text(cur + '\n' + CSS.strip() + '\n', encoding='utf-8')
