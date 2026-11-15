"""Deep country profiles, country-pair pages and the South Asia hub for world.customsnepal.com.

Rendered by scripts/world_prerender.py from data/world/deep.json (built by scripts/world_bilateral.py from BACI).
These pages are static: they ship without the SPA script, so what a crawler sees is exactly what a person sees.

Every number is a BACI figure or a ratio of two BACI figures. Sentences state what the data shows; none explains why.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODC_FILE = ROOT / 'data' / 'world' / 'prodc.json'
PRODW_FILE = ROOT / 'data' / 'world' / 'prodw.json'
IMTS_FILE = ROOT / 'data' / 'world' / 'imts.json'
DEEP_FILE = ROOT / 'data' / 'world' / 'deep.json'


class Views:
    def __init__(self, h):
        """h: helpers from world_prerender (esc, money, iso_meta, hs_desc, code_href, fmt_code, clip, ic, main, back,
        src_box, trend_svg, country_extras, CBYISO)."""
        self.h = h
        self.D = json.loads(DEEP_FILE.read_text(encoding='utf-8'))
        self.Y = self.D['year']; self.C = self.D['countries']; self.P = self.D['pairs']
        known = h['CBYISO']
        self.rank_x = {c: i + 1 for i, (c, _) in enumerate(sorted(((c, v['x']) for c, v in self.C.items() if c in known), key=lambda kv: -kv[1]))}
        self.rank_m = {c: i + 1 for i, (c, _) in enumerate(sorted(((c, v['m']) for c, v in self.C.items() if c in known), key=lambda kv: -kv[1]))}
        self.pairs_of = {}
        for key in self.P:
            a, b = key.split('-')
            if a in known and b in known:
                self.pairs_of.setdefault(a, []).append(b); self.pairs_of.setdefault(b, []).append(a)
        self._pair_keys = [k for k in sorted(self.P) if all(x in known for x in k.split('-'))]
        ptot = lambda x, q: self.P['-'.join(sorted([x, q]))]['ab'] + self.P['-'.join(sorted([x, q]))]['ba']
        for x in self.pairs_of:
            self.pairs_of[x].sort(key=lambda q: -ptot(x, q))
        pc = json.loads(PRODC_FILE.read_text(encoding='utf-8')) if PRODC_FILE.exists() else {'products': {}, 'wtop': {}}
        self.PC = {k: v for k, v in pc['products'].items() if k.split('-')[0] in known and h['has_code'](k.split('-')[1])}
        self.WTOP = pc['wtop']
        im = json.loads(IMTS_FILE.read_text(encoding='utf-8')) if IMTS_FILE.exists() else {'countries': {}, 'fetched': ''}
        self.IM = im['countries']; self.IM_DATE = im.get('fetched', '')
        yf = ROOT / 'data' / 'world' / 'years.json'
        yj = json.loads(yf.read_text(encoding='utf-8')) if yf.exists() else {}
        self.YR = yj.get('years', {}); self.YW = yj.get('world', {})
        self._years = {}; self._yrank = {}
        sf = ROOT / 'data' / 'world' / 'sanctions.json'
        sj = json.loads(sf.read_text(encoding='utf-8')) if sf.exists() else {}
        self.SD = sj.get('countries', {}); self.SD_DATE = sj.get('fetched', '')
        hf = ROOT / 'data' / 'world' / 'headings.json'
        self.HD = json.loads(hf.read_text(encoding='utf-8'))['headings'] if hf.exists() else {}
        of = ROOT / 'data' / 'world' / 'opps.json'
        self.OP = json.loads(of.read_text(encoding='utf-8')) if of.exists() else {}
        self.TPO = json.loads(f.read_text(encoding='utf-8')) if (f := ROOT / 'data' / 'world' / 'tpo.json').exists() else {}
        # product detail for the latest periods, from national sources (same record shape in every file)
        self.PL = {}
        f = ROOT / 'data' / 'world' / 'eu_products.json'
        if f.exists():
            eu = json.loads(f.read_text(encoding='utf-8'))
            for k, rec in eu['countries'].items():
                self.PL[k] = dict(rec, last=eu['last'], full=eu['full'], cur=eu['cur'], upto=eu['upto'], fetched=eu['fetched'], short='Eurostat, the EU&#39;s statistical office',
                                  src='Eurostat, EU trade by HS2-4-6 and CN8 (DS-045409), trade with all partners inside and outside the EU; euros converted to US dollars at each month&#39;s average ECB reference rate',
                                  note='Eurostat records goods by the member state where they are declared, so for transit hubs such as the Netherlands and Belgium its totals run higher than national figures.')
        f = ROOT / 'data' / 'world' / 'more_products.json'
        if f.exists():
            mp = json.loads(f.read_text(encoding='utf-8'))
            for k, rec in mp['countries'].items():
                self.PL[k] = dict(rec, fetched=mp['fetched'], note={'GBR': 'HMRC&#39;s product figures include non-monetary gold and follow its own coverage, so they do not add up to the IMF totals above.',
                                                                   'BRA': 'Imports are valued FOB here, without freight and insurance.'}.get(k, ''))
        f = ROOT / 'data' / 'world' / 'us_products.json'
        if f.exists():
            up = json.loads(f.read_text(encoding='utf-8'))
            for k, rec in up['countries'].items():
                self.PL[k] = dict(rec, fetched=up['fetched'], note='Exports are valued free alongside ship and imports at customs value, without freight and insurance, so they do not add up to the IMF totals above. '
                                                                   'This page uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.')
        self.PW = json.loads(PRODW_FILE.read_text(encoding='utf-8'))['products'] if PRODW_FILE.exists() else {}
        self._pc_keys = sorted(self.PC); self._pc_set = set(self.PC); self._pc_by_country = {}
        for k in sorted(self.PC, key=lambda k: -self.PC[k]['v']):
            self._pc_by_country.setdefault(k.split('-')[0], []).append(k.split('-')[1])

    # ---------- small helpers
    def usd(self, vk):
        return self.h['money'](vk * 1000.0)

    EXTRA_NAMES = {'TWN': 'Taiwan', 'KOS': 'Kosovo', 'WBG': 'West Bank and Gaza', 'VAT': 'Holy See'}      # partner codes in the IMF data with no profile on the site

    def name(self, iso):
        c = self.h['CBYISO'].get(iso)
        if c:
            return c['name']
        n = (self.C.get(iso) or {}).get('n') or self.EXTRA_NAMES.get(iso) or iso
        return 'Other Asia, n.e.s.' if iso == 'S19' else n

    def flag(self, iso):
        c = self.h['CBYISO'].get(iso)
        return c['flag'] if c else ''

    def clink(self, iso, text=None):
        t = self.h['esc'](text or self.name(iso))
        fl = self.flag(iso)
        lab = (fl + ' ' if fl else '') + t
        return f'<a href="/trade/{iso.lower()}">{lab}</a>' if iso in self.h['CBYISO'] else lab

    def pair_href(self, a, b):
        x, y = sorted([a, b])
        return f'/trade/{x.lower()}/{y.lower()}' if (x + '-' + y) in self.P and x in self.h['CBYISO'] and y in self.h['CBYISO'] else None

    def has(self, iso):
        return iso in self.C

    def share(self, part, whole, d=1):
        return ('%.' + str(d) + 'f%%') % (100.0 * part / whole) if whole else '—'

    def prod(self, code, n=62):
        e = self.h['esc']
        lab = e(self.h["clip"](self.h["hs_desc"](code), n))      # a few BACI codes (271000) have no page of their own: show the name without a link
        return (f'<a href="{self.h["code_href"](code)}">{lab}</a>' if self.h['has_code'](code) else lab) + f' <small class="hsc">{self.h["fmt_code"](code)}</small>'

    def barlist(self, rows, color):
        """rows: [(label_html, value_k, right_html)]"""
        if not rows:
            return '<p class="fine">No data.</p>'
        mx = max(r[1] for r in rows) or 1
        return '<div class="bars dp">' + ''.join(
            f'<div class="barrow"><span class="lb">{lab}</span><span class="tr"><span class="fi" style="width:{max(2.0, 100.0 * v / mx):.1f}%;background:{color}"></span></span>'
            f'<span class="vl">{right}</span></div>' for lab, v, right in rows) + '</div>'

    def table(self, heads, rows, cls=''):
        th = ''.join(f'<th{" class=r" if i else ""}>{x}</th>' for i, x in enumerate(heads))
        tr = ''.join('<tr>' + ''.join(f'<td{" class=r" if i else ""}>{x}</td>' for i, x in enumerate(r)) + '</tr>' for r in rows)
        return f'<div class="dscroll" tabindex="0" role="region" aria-label="Table, scrolls sideways on small screens"><table class="dt {cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'

    # ---------- graphics for the country profile (static HTML and SVG, no script)
    MAP_BINS = [(15.0, 5, '15% or more'), (5.0, 4, '5 to 15%'), (1.0, 3, '1 to 5%'), (0.1, 2, '0.1 to 1%')]

    def _map(self, iso, lst, total, verb):
        """World map shaded by each partner's share of the flow. Shapes come from one shared file (/assets/worldmap.svg)."""
        e = self.h['esc']; shapes = self.h['MAPIDS']; out = ['<use href="/assets/worldmap.svg#land" class="m0"/>']
        for p, v in lst:
            if p not in shapes or not total:
                continue
            s = 100.0 * v / total
            cls = next((c for th, c, _ in self.MAP_BINS if s >= th), None)
            if not cls:
                continue
            tip = f'{self.name(p)}: {self.usd(v)}, {s:.1f}% of {verb}'
            u = f'<use href="/assets/worldmap.svg#{p}" class="m{cls}"><title>{e(tip)}</title></use>'
            out.append(f'<a href="/trade/{p.lower()}">{u}</a>' if p in self.h['CBYISO'] else u)
        if iso and iso in shapes:
            out.append(f'<use href="/assets/worldmap.svg#{iso}" class="me"><title>{e(self.name(iso))}</title></use>')
        return f'<svg viewBox="0 60 960 400" role="group" aria-label="World map shaded by share of {e(self.name(iso)) + "&#39;s " if iso else ""}{verb}">{"".join(out)}</svg>'

    def map_block(self, iso, d):
        nm = self.h['esc'](self.name(iso)); k = iso.lower()
        legend = ('<div class="mlg"><span><i class="me"></i>' + nm + '</span>' + ''.join(f'<span><i class="m{c}"></i>{lab}</span>' for _, c, lab in self.MAP_BINS)
                  + '<span><i class="m0"></i>Under 0.1% or none</span></div>')
        return (f'<div class="gmap"><input type="radio" name="gm-{k}" id="gmx-{k}" checked><input type="radio" name="gm-{k}" id="gmm-{k}">'
                f'<div class="gtabs" role="group" aria-label="Map shows"><label for="gmx-{k}">Export markets</label><label for="gmm-{k}">Import suppliers</label></div>'
                f'<div class="gm gmx">{self._map(iso, d["xp"], d["x"], "exports")}</div><div class="gm gmm">{self._map(iso, d["mp"], d["m"], "imports")}</div>'
                f'{legend}<p class="fine">Shade shows each partner&#39;s share of {nm}&#39;s exports or imports. Hover or tap a country for the figure; every partner is in the table further down.</p></div>')

    def map_tabs(self, key, tabs, me_label, note):
        """tabs: [(label, svg)]. One map shows plainly; two get CSS-only tabs."""
        legend = ('<div class="mlg">' + (f'<span><i class="me"></i>{me_label}</span>' if me_label else '') + ''.join(f'<span><i class="m{c}"></i>{lab}</span>' for _, c, lab in self.MAP_BINS)
                  + '<span><i class="m0"></i>Under 0.1% or none</span></div>')
        if len(tabs) == 1:
            return f'<div class="gmap"><div class="gm" style="display:block">{tabs[0][1]}</div>{legend}<p class="fine">{note}</p></div>'
        return (f'<div class="gmap"><input type="radio" name="gm-{key}" id="gmx-{key}" checked><input type="radio" name="gm-{key}" id="gmm-{key}">'
                f'<div class="gtabs" role="group" aria-label="Map shows"><label for="gmx-{key}">{tabs[0][0]}</label><label for="gmm-{key}">{tabs[1][0]}</label></div>'
                f'<div class="gm gmx">{tabs[0][1]}</div><div class="gm gmm">{tabs[1][1]}</div>{legend}<p class="fine">{note}</p></div>')

    def year_cols(self, hist, la, lb):
        """Grouped columns, one group per year, both series on one scale. hist: {year: [a, b]}."""
        ys = sorted(hist.items())
        mx = max([max(v) for _, v in ys] + [1])
        if len(ys) < 2:
            return ''
        g = ''.join(f'<div class="yc"><div class="ycb"><i class="x" style="height:{max(1.5, 100.0 * v[0] / mx):.1f}%" title="{la}: {self.usd(v[0])}"><b>{self.usd(v[0])}</b></i>'
                    f'<i class="m" style="height:{max(1.5, 100.0 * v[1] / mx):.1f}%" title="{lb}: {self.usd(v[1])}"><b>{self.usd(v[1])}</b></i></div><span>{y if (len(ys) <= 16 or int(y) % 5 == 0) else ""}</span></div>' for y, v in ys)
        return (f'<div class="ycs{" many" if len(ys) > 4 else ""}{" lots" if len(ys) > 10 else ""}{" huge" if len(ys) > 16 else ""}">{g}</div><div class="dvk"><span><i class="pos"></i>{la}</span><span><i class="neg"></i>{lb}</span></div>')

    # ---------- every product: who exports and imports it (HS code pages)
    def has_product(self, code):
        return code in self.PW and bool(self.PW[code]['x'])

    def product_world(self, code):
        h = self.h; e = h['esc']; p = self.PW[code]; w = p['w']; Y = self.Y
        mx = self._map(None, p['x'], w, 'world exports'); mm = self._map(None, p['m'], w, 'world imports')
        def rows(lst, link):
            out = []
            for c, v in lst[:10]:
                href = self.pc_href(c, code) if link else None
                lab = self.clink(c) + (f' <a class="pl" href="{href}">buyers</a>' if href else '')
                out.append((lab, v, f'{self.usd(v)} <small>{self.share(v, w)}</small>'))
            return out
        top = p['x'][0] if p['x'] else None; topm = p['m'][0] if p['m'] else None
        lead = (f'<p class="ans">World trade in this product was <b>{self.usd(w)}</b> in {Y}, exported by {p["nx"]} economies and imported by {p["nm"]}.'
                + (f' The largest exporter was {self.clink(top[0])} ({self.share(top[1], w)})' if top else '')
                + (f' and the largest importer was {self.clink(topm[0])} ({self.share(topm[1], w)}).' if topm else '.') + '</p>')
        return (f'<section class="gsec"><h2>Who trades this product</h2>{lead}'
                + self.map_tabs('p' + code, [('Exporters', mx), ('Importers', mm)], '', 'Shade shows each economy&#39;s share of world exports or imports of this product. Hover or tap for the figure.')
                + f'<h3>Top {min(10, len(p["x"]))} exporters</h3>' + self.barlist(rows(p['x'], True), 'var(--exp)')
                + (f'<h3>Top {min(10, len(p["m"]))} importers</h3>' + self.barlist(rows(p['m'], False), 'var(--imp)') if p['m'] else '') + '</section>'
                + self.product_history(code))

    @staticmethod
    def _squarify(vals, x, y, w, h):
        tot = sum(vals) or 1.0
        area = [v * w * h / tot for v in vals]; rects = []; i = 0
        def worst(r, short):
            s = sum(r)
            return max(short * short * max(r) / (s * s), (s * s) / (short * short * min(r)))
        while i < len(area):
            short = max(min(w, h), 0.01); row = [area[i]]; i += 1
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

    def groups(self, chapters):
        """[[chapter, value]] -> [(group name, value, top chapter)] for the 16 product groups, largest first."""
        out = []
        for name, a, b in self.h['PGROUPS']:
            inside = [(ch, v) for ch, v in chapters if a <= int(ch) <= b]
            tot = sum(v for _, v in inside)
            if tot > 0:
                out.append((name, tot, max(inside, key=lambda kv: kv[1])[0]))
        return sorted(out, key=lambda r: -r[1])

    def treemap(self, chapters, total, tone, who, verb):
        e = self.h['esc']; gs = self.groups(chapters)
        if not gs or not total:
            return ''
        gs = [g for g in gs if g[1] / total >= 0.004] or gs[:1]
        rects = self._squarify([g[1] for g in gs], 0.0, 0.0, 100.0, 100.0)
        cells = []
        for (name, v, topch), (x, y, w, hh) in zip(gs, rects):
            s = 100.0 * v / total; size = 'lg' if (w >= 22 and hh >= 30) else ('md' if (w >= 12 and hh >= 16) else 'sm')
            tip = f'{name}: {self.usd(v)}, {s:.1f}% of {verb}'
            cells.append(f'<a class="tc {size}" href="/trade/product/{self.h["group_slug"](name)}" style="left:{x:.2f}%;top:{y:.2f}%;width:{w:.2f}%;height:{hh:.2f}%" title="{e(tip)}">'
                         f'<span><b>{e(name)}</b><i>{s:.0f}%</i><em>{self.usd(v)}</em></span></a>')
        lst = ''.join(f'<li><a href="/trade/product/{self.h["group_slug"](name)}">{e(name)}</a><span>{self.usd(v)}</span><i>{100.0 * v / total:.1f}%</i></li>' for name, v, _ in gs)
        return (f'<div class="tm {tone}" role="group" aria-label="{e(who)} {verb} by product group, area in proportion to value">{"".join(cells)}</div>'
                f'<details class="tml"><summary>The same figures as a list</summary><ol>{lst}</ol></details>')

    # ---------- latest months (IMF trade by partner: the last complete year and the current year to date)
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    EST = '<sup class="est" title="Derived by the IMF from the partner&#39;s records, not yet reported by this economy">†</sup>'

    def _chg(self, a, b):
        return '—' if not a or not b else f'{"+" if a >= b else "−"}{abs(100.0 * (a - b) / b):.1f}%'

    def _span(self, I):
        return (f'{self.MONTHS[0]}–{self.MONTHS[I["upto"] - 1]} {I["cur"]}' if I['upto'] > 1 else f'{self.MONTHS[0]} {I["cur"]}') if I.get('cur') else ''

    def latest(self, iso):
        I = self.IM.get(iso)
        if not I or not I['x'] or not I['m']:
            return ''
        e = self.h['esc']; nm = e(self.name(iso)); X, M = I['x'], I['m']; usd = self.usd
        months = sorted(set(X) & set(M)); last = months[-1]; ly, lm = int(last[:4]), int(last[5:])
        full, cur, upto = I['full'], I.get('cur'), I['upto']; span = self._span(I)
        def year_total(d, y):
            v = [d.get(f'{y}-{k:02d}') for k in range(1, 13)]
            return sum(v) if all(x is not None for x in v) else None
        def ytd(d, y):
            v = [d.get(f'{y}-{k:02d}') for k in range(1, upto + 1)]
            return sum(v) if all(x is not None for x in v) else None
        small = lambda a, b, tail: (f' <small>{self._chg(a, b)}</small> {tail}' if a and b else '')
        tiles = []
        for lab, d, cls in (('Exports', X, 'ex'), ('Imports', M, 'im')):
            a, b = year_total(d, full), year_total(d, full - 1)
            if a is not None:
                tiles.append(f'<div class="s"><b class="{cls}">{usd(a)}</b><span>{lab}, {full}{small(a, b, "on " + str(full - 1))}</span></div>')
        if cur:
            for lab, d, cls in (('Exports', X, 'ex'), ('Imports', M, 'im')):
                a, b = ytd(d, cur), ytd(d, cur - 1)
                if a is not None:
                    tiles.append(f'<div class="s"><b class="{cls}">{usd(a)}</b><span>{lab}, {span}{small(a, b, "on the same months of " + str(cur - 1))}</span></div>')
        # monthly chart from January three years back
        ms = [p for p in months if p >= f'{ly - 3}-01']
        mx = max(max(X[p], M[p]) for p in ms) or 1
        W, H = 1000.0, 300.0
        px = lambda i: W * i / max(len(ms) - 1, 1); py = lambda v: H - (H - 8.0) * v / mx
        path = lambda d: ' '.join(('M' if i == 0 else 'L') + f'{px(i):.1f},{py(d[p]):.1f}' for i, p in enumerate(ms))
        years = [(p[:4], 100.0 * px(i) / W) for i, p in enumerate(ms) if p.endswith('-01') or i == 0]
        grid = ''.join(f'<line x1="{W * x / 100:.1f}" y1="0" x2="{W * x / 100:.1f}" y2="{H}" class="lg"/>' for _, x in years[1:])
        tip = '; '.join(f'{self.MONTHS[int(p[5:]) - 1]} {p[:4]}: exports {usd(X[p])}, imports {usd(M[p])}' for p in ms[-6:])
        chart = (f'<div class="lch"><span class="lmx">{usd(mx)}</span><svg viewBox="0 0 {W:.0f} {H:.0f}" preserveAspectRatio="none" role="img" aria-label="Monthly exports and imports of {nm}. Last six months: {e(tip)}">'
                 f'{grid}<path d="{path(M)}" class="lm"/><path d="{path(X)}" class="lx"/></svg>'
                 '<div class="lyr">' + ''.join(f'<span style="left:{x:.1f}%">{y}</span>' for y, x in years) + '</div></div>'
                 f'<div class="dvk"><span><i class="pos"></i>Exports: {usd(X[last])} in {self.MONTHS[lm - 1]} {ly}</span><span><i class="neg"></i>Imports: {usd(M[last])}</span></div>')
        rows = []
        for y in range(ly, ly - 5, -1):
            if cur and y == cur:
                a, b = ytd(X, y), ytd(M, y); lab = f'{y} ({span.rsplit(" ", 1)[0]})'
            else:
                a, b = year_total(X, y), year_total(M, y); lab = str(y)
            if a is not None and b is not None:
                rows.append((lab, usd(a), usd(b), ('+' if a - b >= 0 else '−') + usd(abs(a - b))[1:]))
        # partners: the latest complete year and the current year to date
        def ptable(o, what):
            lst = sorted(((p, v) for p, v in I['p'].items() if v[o + 1] > 0), key=lambda kv: -kv[1][o + 1])[:10]
            if not lst:
                return '', False
            tot = sum(v[o + 1] for v in I['p'].values()) or 1
            any_est = any(v[8] for _, v in lst)
            heads = [what, str(full), f'Change on {full - 1}', 'Share'] + ([span, f'Change on {span.rsplit(" ", 1)[0]} {cur - 1}'] if cur else [])
            body = []
            for p, v in lst:
                ph = self.pair_href(iso, p)
                lab = self.clink(p) + (self.EST if v[8] else '') + (f' <a class="pl" href="{ph}">pair</a>' if ph else '')
                body.append([lab, usd(v[o + 1]), self._chg(v[o + 1], v[o]), self.share(v[o + 1], tot)] + ([usd(v[o + 2]) if v[o + 2] else '—', self._chg(v[o + 2], v[o + 3])] if cur else []))
            return self.table(heads, body), any_est
        tx, ex_est = ptable(0, 'Export market'); tm, im_est = ptable(4, 'Supplier')
        est_note = (f'<p class="fine">{self.EST} {nm} had not yet reported this flow, so the IMF derived it from the partner&#39;s own records. Treat these as provisional.</p>' if (ex_est or im_est) else '')
        return (f'<section class="gsec"><h2>{nm} in {full} and {cur or full + 1}: the latest figures</h2>'
                f'<p class="gk">Monthly customs figures in US dollars from the IMF&#39;s trade-by-partner database. The newest month is {self.MONTHS[lm - 1]} {ly}.</p>'
                f'<div class="statrow ltl" style="margin-top:0">{"".join(tiles)}</div>{chart}'
                + (self.table(['Period', 'Exports', 'Imports', 'Balance'], rows) if rows else '')
                + (f'<h3>Largest export markets in {full}{" and " + str(cur) + " so far" if cur else ""}</h3>' + tx if tx else '')
                + (f'<h3>Largest suppliers in {full}{" and " + str(cur) + " so far" if cur else ""}</h3>' + tm if tm else '') + est_note
                + f'<p class="fine">Source: International Monetary Fund, International Trade in Goods by partner country, retrieved {self.IM_DATE}. The IMF collects each economy&#39;s national customs figures '
                f'and converts them to US dollars at the average exchange rate of the month the goods moved. Imports include freight and insurance; exports do not. '
                f'The product and partner sections further down use BACI&#39;s reconciled figures for {self.Y}, which can differ noticeably for the same year, so compare like with like.</p></section>')

    def latest_products(self, iso):
        """Product detail for the last complete year and the current year to date, where a national source publishes it."""
        R = self.PL.get(iso)
        if not R or not R.get('xc'):
            return ''
        e = self.h['esc']; nm = e(self.name(iso)); full, cur, upto = R['full'], R.get('cur'), R['upto']
        span = (f'{self.MONTHS[0]}–{self.MONTHS[upto - 1]} {cur}' if upto > 1 else f'{self.MONTHS[0]} {cur}') if cur else ''
        def block(f, verb, tone, what):
            chap = [[r[0], r[2]] for r in R[f + 'c']]; tot = sum(v for _, v in chap)
            rows = []
            for r in R[f + 'k'][:10]:
                if not self.h['has_code'](r[0]):
                    continue
                rows.append([self.prod(r[0], 56), self.usd(r[2]), self._chg(r[2], r[1]), self.share(r[2], tot)] + ([self.usd(r[3]) if r[3] else '—', self._chg(r[3], r[4])] if cur else []))
            heads = ['Product', str(full), f'Change on {full - 1}', f'Share of {verb}'] + ([span, 'Change on a year earlier'] if cur else [])
            return (f'<h3>{what} by product group, {full}</h3>' + self.treemap(chap, tot, tone, self.name(iso), f'{verb} in {full}')
                    + (f'<h3>Ten largest {verb[:-1]} products, {full}{" and " + str(cur) + " so far" if cur else ""}</h3>' + self.table(heads, rows) if rows else ''))
        return (f'<section class="gsec"><h2>What {nm} traded in {full} and {cur or full + 1}, by product</h2>'
                f'<p class="gk">Product detail for the latest periods, from {R["short"]}. The newest month is {self.MONTHS[int(R["last"][5:]) - 1]} {R["last"][:4]}.</p>'
                + block('x', 'exports', 'exp', 'Exports') + block('m', 'imports', 'imp', 'Imports')
                + f'<p class="fine">Source: {R["src"]}; retrieved {R["fetched"]}. {R.get("note", "")} '
                f'These are the reporting office&#39;s own figures and are not the reconciled {self.Y} figures used in the sections below.</p></section>')

    def home_latest(self):
        """Home page: the largest exporters in the latest complete year and the current year to date (customs figures via the IMF)."""
        e = self.h['esc']; rows = []; full = cur = None; span = ''
        def yt(d, y, upto=12):
            v = [d.get(f'{y}-{k:02d}') for k in range(1, upto + 1)]
            return sum(v) if all(x is not None for x in v) else None
        cand = []
        for iso, I in self.IM.items():
            if iso not in self.h['CBYISO']:
                continue
            a = yt(I['x'], I['full'])
            if a:
                cand.append((a, iso, I))
        for a, iso, I in sorted(cand, key=lambda r: -r[0])[:10]:
            full, cur = I['full'], I.get('cur'); span = self._span(I)
            b = yt(I['x'], full - 1); c = yt(I['x'], cur, I['upto']) if cur else None; d = yt(I['x'], cur - 1, I['upto']) if cur else None
            rows.append([self.clink(iso), self.usd(a), self._chg(a, b)] + ([self.usd(c) if c else '—', self._chg(c, d)] if cur else []))
        if not rows:
            return ''
        heads = ['Exporter', str(full), f'Change on {full - 1}'] + ([span, 'Change on a year earlier'] if cur else [])
        return (f'<section class="wstrip"><h2>The latest: {full} and {cur or full + 1} so far</h2>'
                + self.table(heads, rows)
                + f'<p class="fine">Each economy&#39;s own customs figures in US dollars, from the International Monetary Fund&#39;s trade-by-partner database (retrieved {self.IM_DATE}). '
                f'Every country profile has its {full} and {cur or full + 1} figures by partner, and yearly totals back to 2000. <a href="/trade">Rankings for all economies</a> · <a href="/trade/latest">What changed this year</a> · <a href="/compare">Compare countries</a> · <a href="/opportunities">Market opportunities</a></p></section>')

    # ---------- PDF trade brief and the About page
    def brief_href(self, iso):
        return f'/reports/{iso.lower()}-trade-brief.pdf'

    def brief(self, c):
        """A short, self-contained report for one economy, laid out for A4. Built from the same parts as the profile."""
        h = self.h; e = h['esc']; iso = c['iso']; d = self.C[iso]; nm = e(c['name']); I = self.IM.get(iso) or {}
        ys = self.years_of(iso); v = self.year_view(iso, ys[-1]) if ys else d; yv = ys[-1] if ys else self.Y      # headline, cards and flow follow the latest year
        X, M = v['x'], v['m']; bal = X - M; xp, mp = v['xp'], v['mp']; BX, BM = d['x'], d['m']
        lead = (f'<p class="ans">{nm} exported <b>{self.usd(X)}</b> of goods and imported <b>{self.usd(M)}</b> in {yv}, a trade {"surplus" if bal >= 0 else "deficit"} of <b>{self.usd(abs(bal))}</b>.'
                + (f' Its largest export market was {e(self.name(xp[0][0]))} ({self.share(xp[0][1], X)} of exports)' if xp else '')
                + (f' and its largest supplier was {e(self.name(mp[0][0]))} ({self.share(mp[0][1], M)} of imports).' if mp else '.') + '</p>')
        def top(lst, total, what):
            rows = [(f'{self.flag(p)} {e(self.name(p))}', self.usd(v), self.share(v, total)) for p, v in lst[:10]]
            return self.table([what, str(yv), 'Share'], rows) if rows else ''
        prods = lambda lst, total, what: self.table([what, str(self.Y), 'Share'], [(e(h['clip'](h['hs_desc'](r[0]), 58)) + f' <small class="hsc">{h["fmt_code"](r[0])}</small>', self.usd(r[1]), self.share(r[1], total)) for r in lst[:8]]) if lst else ''
        tm_x = self.treemap(d.get('xc') or [], BX, 'exp', c['name'], 'exports'); tm_m = self.treemap(d.get('mc') or [], BM, 'imp', c['name'], 'imports')
        url = 'world.customsnepal.com' + self.h['chref'](iso)
        return (f'<header class="bh"><div><span class="bm">{h["MARK"]}</span><b>World Trade Data</b></div><span>Trade brief · {url}</span></header>'
                f'<h1>{c["flag"]} {nm}: trade brief</h1>'
                f'<p class="bsub">{"Customs figures for " + str(I["full"]) + (" and " + str(I["cur"]) + " to date" if I.get("cur") else "") + "; products" if ys else "Reconciled figures"} for {self.Y}; long-run totals. Prepared {self.h["TODAY"]}.</p>'
                + lead + self.highlights(iso, v)
                + self.latest(iso)
                + self.flow(iso, v)
                + ('' if ys else f'<section class="gsec"><h2>Partners in {self.Y}</h2><div class="b2"><div><h3>Export markets</h3>{top(xp, X, "Market")}</div><div><h3>Suppliers</h3>{top(mp, M, "Supplier")}</div></div></section>')
                + (f'<section class="gsec"><h2>What {nm} exports, {self.Y}</h2>{tm_x}<p class="gk">Reconciled figures (BACI): exports of {self.usd(BX)} on that basis. {self.Y} is the newest year with product detail for every economy.</p><h3>Largest export products</h3>{prods(d["xk"], BX, "Product")}</section>' if tm_x else '')
                + (f'<section class="gsec"><h2>What {nm} imports, {self.Y}</h2>{tm_m}<p class="gk">Reconciled figures (BACI): imports of {self.usd(BM)} on that basis.</p><h3>Largest import products</h3>{prods(d["mk"], BM, "Product")}</section>' if tm_m else '')
                + (f'<section class="gsec"><h2>{nm}&#39;s trade over the long run</h2><p class="gk">Merchandise exports and imports, World Bank series, current US dollars.</p>{h["trend_svg"](c.get("trend") or [])}</section>' if c.get('trend') else '')
                + f'<section class="gsec bsrc"><h2>Sources and method</h2><ul>'
                f'<li><b>{self.Y} products:</b> BACI (CEPII), which reconciles what exporters and importers each reported to UN Comtrade, six-digit HS, current US dollars.</li>'
                f'<li><b>Totals and partners, latest year and current year:</b> International Monetary Fund, International Trade in Goods by partner country: each economy&#39;s own monthly customs figures, converted to US dollars at the average exchange rate of each month. Values marked † were derived by the IMF from partners&#39; records because the economy had not yet reported.</li>'
                f'<li><b>Long-run totals:</b> World Bank, merchandise exports and imports, current US dollars.</li>'
                f'<li>The two sources use different methods and can give different totals for the same year. Compare like with like.</li>'
                f'<li>Product classification: Harmonized System, © World Customs Organization.</li></ul>'
                f'<p>World Trade Data is an independent reference published by Evolve Tech Pvt. Ltd. It is not affiliated with any government, the IMF, the WCO or the United Nations. '
                f'Free to share with attribution. The live page, with every partner and product, is at {url}.</p></section>')

    def about(self):
        h = self.h; e = h['esc']; n_c = len(h['CBYISO']); im = len(self.IM); pl = len(self.PL)
        src = [('BACI, by CEPII (Paris)', f'Partners and products for {self.Y}: every country pair and every six-digit product', 'Reconciles what the exporter and the importer each reported to UN Comtrade into one figure per flow. Updated each January.', 'Etalab Open Licence 2.0'),
               ('International Monetary Fund, International Trade in Goods by partner country', f'The latest complete year and the current year to date, month by month since 2019, for {im} economies', 'Each economy&#39;s own customs figures, collected monthly and published in US dollars.', 'IMF data terms: free to use with attribution'),
               ('World Bank, World Development Indicators', 'Long-run export and import totals for each economy', 'Yearly merchandise trade in current US dollars.', 'CC BY 4.0'),
               ('Eurostat (DS-045409)', 'Latest product detail for the 27 EU members', 'EU customs and Intrastat figures in euros, by product and month.', 'Eurostat reuse policy: free with attribution'),
               ('HM Revenue &amp; Customs, Overseas Trade Statistics', 'Latest product detail for the United Kingdom', 'UK customs figures in pounds, by product and month.', 'Open Government Licence'),
               ('Ministry of Development, Industry, Trade and Services of Brazil, Comex Stat', 'Latest product detail for Brazil', 'Brazil&#39;s customs figures, published in US dollars.', 'Open data'),
               ('World Customs Organization', 'The Harmonized System product classification (HS 2022)', 'The names and codes of products.', '© WCO'),
               ('European Central Bank', 'Monthly average exchange rates', 'Used only to convert euro and sterling figures to US dollars.', 'ECB reuse policy')]
        srcl = '<div class="absrc">' + ''.join(f'<div><b>{a}</b><p><span>Used for</span>{b}.</p><p><span>What it is</span>{c_}</p><p><span>Terms</span>{d_}</p></div>' for a, b, c_, d_ in src) + '</div>'
        return h['main'](h['back']('/', 'Home') + '<div class="ph"><h1 class="h2">About World Trade Data</h1>'
                         '<p>What this site is for, where every figure comes from, and how far to trust it.</p></div>'
                         '<section class="gsec"><h2>The goal</h2><p class="gk">Trade statistics are public, but they are scattered across agencies, published in different currencies and formats, and hard to read. '
                         f'World Trade Data puts them in one place and shows, for each of {n_c} economies, what it sells, what it buys and with whom, in plain words and charts. It is free, needs no sign-in and carries no advertising.</p>'
                         '<p class="gk">The site does not produce statistics of its own. Every number is taken from a published official source, named on the page where it appears, with the year it refers to.</p></section>'
                         '<section class="gsec"><h2>Where the figures come from</h2>' + srcl + '</section>'
                         '<section class="gsec"><h2>How to read the numbers</h2><ul class="abl">'
                         f'<li><b>Two kinds of figure.</b> The detailed {self.Y} pages use reconciled figures (BACI), where each export is matched to the partner&#39;s import record. The latest-year sections use customs figures as each economy reports them. The two can differ for the same country and year, sometimes by a lot, so each section says which it uses. Do not add or compare across them.</li>'
                         '<li><b>Currency.</b> Everything is in current US dollars. Where the source publishes in another currency, each month is converted at that month&#39;s average exchange rate and the months are added up. Figures are not adjusted for inflation.</li>'
                         '<li><b>Exports and imports are valued differently.</b> In customs figures, imports usually include freight and insurance and exports do not, so two countries&#39; figures for the same flow rarely match.</li>'
                         '<li><b>Derived values.</b> When an economy has not yet reported a recent flow, the IMF derives it from the partner&#39;s records. These are marked † and should be treated as provisional.</li>'
                         '<li><b>Goods only.</b> Services, such as tourism, transport and software, are not included.</li>'
                         '<li><b>Small flows and small economies.</b> Very small flows can be missing, and a few territories have no map shape or no profile.</li></ul></section>'
                         f'<section class="gsec"><h2>How often it is updated</h2><p class="gk">The latest-year figures are refreshed monthly. The detailed partner and product year moves forward once a year, when CEPII publishes a new BACI release, usually in January. '
                         f'Latest-year figures on this build were retrieved on {self.IM_DATE}. Earlier years are kept on the site as new ones are added.</p></section>'
                         '<section class="gsec"><h2>Using the figures</h2><p class="gk">You may quote and share anything here. Please name the original source shown on the page, for example '
                         '&ldquo;Source: BACI (CEPII), via World Trade Data&rdquo;. Each country profile has a PDF trade brief you can download and pass on.</p>'
                         '<p class="gk">Nothing here is advice. For a business or legal decision, check the figure with the source agency.</p></section>'
                         '<section class="gsec"><h2>Who publishes it</h2><p class="gk">World Trade Data is published by Evolve Tech Pvt. Ltd., a private company based in Kathmandu, Nepal, which also publishes '
                         '<a href="https://www.customsnepal.com/">customsnepal.com</a> and <a href="https://nepalpublicdata.com/">nepalpublicdata.com</a>. '
                         'It is an independent reference and is not affiliated with, or endorsed by, any government, CEPII, the IMF, Eurostat, the World Customs Organization or the United Nations.</p>'
                         '<p class="gk">Found a mistake, or a figure that does not match its source? Write to <a href="mailto:info@customsnepal.com">info@customsnepal.com</a> with the page address. Corrections are made at the next build.</p></section>')

    def pair_latest(self, a, b):
        """What each side reports selling the other in the latest complete year and the current year to date."""
        e = self.h['esc']; rows = []; est = False; span = ''; full = cur = None
        for x, y in ((a, b), (b, a)):
            I = self.IM.get(x); v = (I or {}).get('p', {}).get(y)
            if not I or not v or not v[1]:
                continue
            full, cur = I['full'], I.get('cur'); span = self._span(I); est = est or bool(v[8])
            rows.append([f'{e(self.name(x))} → {e(self.name(y))}' + (self.EST if v[8] else ''), self.usd(v[0]) if v[0] else '—', self.usd(v[1]), self._chg(v[1], v[0])]
                        + ([self.usd(v[2]) if v[2] else '—', self._chg(v[2], v[3])] if cur else []))
        if not rows:
            return ''
        heads = ['Exports', str(full - 1), str(full), 'Change'] + ([span, f'Change on a year earlier'] if cur else [])
        return (f'<section class="gsec"><h2>{full} and {cur or full + 1} so far</h2>'
                f'<p class="gk">Each row is the exporting country&#39;s own customs figure, in US dollars, from the IMF&#39;s trade-by-partner database.</p>'
                + self.table(heads, rows)
                + (f'<p class="fine">{self.EST} Not yet reported by the exporter; derived by the IMF from the partner&#39;s records. Treat as provisional.</p>' if est else '')
                + f'<p class="fine">Source: International Monetary Fund, retrieved {self.IM_DATE}; converted to US dollars at each month&#39;s average exchange rate. '
                f'The product sections of this page use BACI&#39;s reconciled figures for {self.Y}, which can differ for the same year.</p></section>')

    # ---------- highlights and flow (top of the country profile)
    def flow_side(self, items, total, tone, mirror, who, verb):
        """One side of the flow diagram: a bar for the country and ribbons to each partner, widths in proportion to value.
        items: [(iso or None, value)], largest first, last may be the 'all others' remainder. mirror=True draws partners on the left."""
        e = self.h['esc']; W, BAR, GAP, LAB = 400.0, 14.0, 10.0, 196.0
        n = len(items); S = 300.0; scale = S / total if total else 0
        hs = [max(3.0, v * scale) for _, v in items]
        slot = [max(hh, 38.0) for hh in hs]                      # room for a two-line label beside each node
        H = sum(slot) + GAP * (n - 1); src_h = sum(hs)
        y0 = (H - src_h) / 2.0                                   # the country's bar is centred
        xs, xn = (W - BAR, LAB) if mirror else (0.0, W - LAB - BAR)       # source bar x, node bar x
        col = 'var(--imp)' if tone == 'imp' else 'var(--exp)'
        out = [f'<rect x="{xs:.1f}" y="{y0:.1f}" width="{BAR}" height="{src_h:.1f}" rx="3" fill="{col}"/>']
        sy = y0; ny = 0.0
        for (p, v), hh, sl in zip(items, hs, slot):
            cy = ny + (sl - hh) / 2.0
            a, b = (xn + BAR, xs) if mirror else (xs + BAR, xn)   # ribbon from a to b
            mid = (a + b) / 2.0
            op = '.34' if p else '.16'
            out.append(f'<path d="M{a:.1f},{(cy if mirror else sy):.1f} C{mid:.1f},{(cy if mirror else sy):.1f} {mid:.1f},{(sy if mirror else cy):.1f} {b:.1f},{(sy if mirror else cy):.1f} '
                       f'L{b:.1f},{(sy if mirror else cy) + hh:.1f} C{mid:.1f},{(sy if mirror else cy) + hh:.1f} {mid:.1f},{(cy if mirror else sy) + hh:.1f} {a:.1f},{(cy if mirror else sy) + hh:.1f} Z" fill="{col}" opacity="{op}"/>')
            out.append(f'<rect x="{xn:.1f}" y="{cy:.1f}" width="{BAR}" height="{hh:.1f}" rx="3" fill="{col}"{"" if p else " opacity=\".45\""}/>')
            name = self.name(p) if p else 'All other partners'
            tx = (xn - 8) if mirror else (xn + BAR + 8); anc = 'end' if mirror else 'start'
            lab = (f'<text x="{tx:.1f}" y="{ny + sl / 2.0 - 3:.1f}" text-anchor="{anc}" class="fn">{e(self.h["clip"](name, 22))}</text>'
                   f'<text x="{tx:.1f}" y="{ny + sl / 2.0 + 14:.1f}" text-anchor="{anc}" class="fv">{self.usd(v)} · {self.share(v, total)}</text>')
            out.append(f'<a href="/trade/{p.lower()}">{lab}</a>' if p and p in self.h['CBYISO'] else lab)
            sy += hh; ny += sl + GAP
        return (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" role="group" aria-label="{e(who)} {verb}: ' + e('; '.join(f'{self.name(p) if p else "all others"} {self.share(v, total)}' for p, v in items)) + f'">{"".join(out)}</svg>')

    def flow(self, iso, d, n=5):
        nm = self.h['esc'](self.name(iso)); X, M = d['x'], d['m']
        def side(lst, total):
            top = [(p, v) for p, v in lst[:n]]; rest = total - sum(v for _, v in top)
            return top + ([(None, rest)] if rest > total * 0.005 else [])
        if not d['xp'] or not d['mp']:
            return ''
        return (f'<section class="gsec"><h2>Where {nm}&#39;s goods come from, and where they go</h2>'
                f'<p class="gk">The five largest suppliers and the five largest markets in {d.get("_y", self.Y)}. Ribbon width is in proportion to value within each side.</p>'
                f'<div class="flw"><div><b class="flh">Imports from</b>{self.flow_side(side(d["mp"], M), M, "imp", True, self.name(iso), "imports by supplier")}</div>'
                f'<div class="flc"><span>{self.flag(iso)}</span><b>{nm}</b><i>{self.usd(M)} in</i><i>{self.usd(X)} out</i></div>'
                f'<div><b class="flh">Exports to</b>{self.flow_side(side(d["xp"], X), X, "exp", False, self.name(iso), "exports by market")}</div></div></section>')

    def highlights(self, iso, d):
        """Six facts, each with a small graphic. Every figure is read straight from the data; nothing is inferred."""
        e = self.h['esc']; nm = e(self.name(iso)); X, M = d['x'], d['m']; cards = []
        rx, rm, n = d.get('_rk') or (self.rank_x.get(iso), self.rank_m.get(iso), len(self.rank_x))
        def bar(pct, tone='x'):
            return f'<div class="hb"><i class="{tone}" style="width:{max(1.5, min(100.0, pct)):.1f}%"></i></div>'
        def card(big, text, graphic, tone=''):
            cards.append(f'<div class="hc {tone}"><b>{big}</b><p>{text}</p>{graphic}</div>')
        if rx:
            pos = 100.0 * (rx - 1) / max(n - 1, 1)
            card(f'#{rx}', f'largest exporter of {n} economies, and #{rm or "–"} importer',
                 f'<div class="hr"><i style="left:{pos:.1f}%"></i></div><div class="hrl"><span>#1</span><span>#{n}</span></div>')
        xg = self.groups(d.get('xc') or [])
        if xg and X:
            s = 100.0 * xg[0][1] / X
            card(f'{s:.0f}%', f'of exports are <a href="/trade/product/{self.h["group_slug"](xg[0][0])}">{e(xg[0][0].lower())}</a>, the largest product group', bar(s))
        if d['xp'] and X:
            p, v = d['xp'][0]; s = 100.0 * v / X
            card(f'{s:.0f}%', f'of exports go to {self.clink(p)}, the largest market', bar(s))
        if len(d['xp']) >= 3 and X:
            t3 = [100.0 * v / X for _, v in d['xp'][:3]]
            seg = ''.join(f'<i class="x" style="width:{w:.1f}%"></i>' for w in t3)
            card(f'{sum(t3):.0f}%', f'of exports go to just three markets, out of {d.get("nxp") or len(d["xp"])}', f'<div class="hb seg">{seg}</div>')
        if X and M:
            bal = X - M; cov = 100.0 * X / M
            card(('+' if bal >= 0 else '−') + self.usd(abs(bal))[1:], f'trade {"surplus" if bal >= 0 else "deficit"}: exports pay for {cov:.0f}% of imports',
                 f'<div class="hb two"><i class="x" style="width:{100.0 * X / max(X, M):.1f}%"></i><i class="m" style="width:{100.0 * M / max(X, M):.1f}%"></i></div>', 'pos' if bal >= 0 else 'neg')
        if d.get('_prev') and d['_prev'][0]:
            a, b = X, d['_prev'][0]; mxv = max(a, b)
            card(self._chg(a, b), f'change in exports on {d["_y"] - 1}: {self.usd(b)} then, {self.usd(a)} in {d["_y"]}',
                 f'<div class="hb two"><i class="x" style="width:{100.0 * a / mxv:.1f}%"></i><i class="p" style="width:{100.0 * b / mxv:.1f}%"></i></div>')
        lead = [r for r in d.get('lead') or [] if r[2] == 1]
        if lead:
            k, v, r, s = lead[0]; href = self.pc_href(iso, k) or self.h['code_href'](k)
            card('#1', f'in the world for <a href="{href}">{e(self.pc_short(k, 46).lower())}</a>, with {s:.0f}% of world exports', bar(s))
        elif d['mp'] and M:
            p, v = d['mp'][0]; s = 100.0 * v / M
            card(f'{s:.0f}%', f'of imports come from {self.clink(p)}, the largest supplier', bar(s, 'm'))
        return f'<div class="hcs">{"".join(cards)}</div>' if cards else ''

    def glance(self, X, M):
        mx = max(X, M) or 1
        return (f'<div class="gl"><div class="glr"><span>Exports</span><div><i class="x" style="width:{max(1.0, 100.0 * X / mx):.1f}%"></i></div><b>{self.usd(X)}</b></div>'
                f'<div class="glr"><span>Imports</span><div><i class="m" style="width:{max(1.0, 100.0 * M / mx):.1f}%"></i></div><b>{self.usd(M)}</b></div></div>')

    def balance_chart(self, sur, dfc):
        """Diverging bars: surpluses grow right in the export colour, deficits grow left in the import colour, one shared scale."""
        rows = [(p, v) for p, v in sur] + [(p, v) for p, v in dfc]
        if not rows:
            return ''
        mx = max(abs(v) for _, v in rows) or 1
        out = []
        for p, v in rows:
            w = max(1.0, 50.0 * abs(v) / mx)
            bar = (f'<i class="pos" style="left:50%;width:{w:.1f}%"></i>' if v >= 0 else f'<i class="neg" style="right:50%;width:{w:.1f}%"></i>')
            out.append(f'<div class="dvr"><span>{self.clink(p)}</span><div>{bar}</div><b>{"+" if v >= 0 else "−"}{self.usd(abs(v))[1:]}</b></div>')
        return ('<div class="dv">' + ''.join(out) + '<div class="dvk"><span><i class="neg"></i>Deficit: imports more than it exports</span><span><i class="pos"></i>Surplus</span></div></div>')

    # ---------- year pages: one consistent series (IMF customs figures) for totals and partners, 2019 to the latest
    # complete year, with BACI product detail attached where that year has it. /trade/<iso> is the latest year.
    def years_of(self, iso):
        if iso in self._years:
            return self._years[iso]
        I = self.IM.get(iso) or {}; out = []
        for y in sorted(I.get('pa') or {}):
            if I['pa'][y] and all(f'{y}-{k:02d}' in I['x'] and f'{y}-{k:02d}' in I['m'] for k in range(1, 13)):
                out.append(int(y))
        if out and out[-1] != I.get('full'):
            out = []
        self._years[iso] = out
        return out

    def _year_tot(self, iso, y):
        I = self.IM[iso]
        return sum(I['x'][f'{y}-{k:02d}'] for k in range(1, 13)), sum(I['m'][f'{y}-{k:02d}'] for k in range(1, 13))

    def _year_rank(self, y):
        if y not in self._yrank:
            known = self.h['CBYISO']
            tot = {c: self._year_tot(c, y) for c in self.IM if c in known and y in self.years_of(c)}
            rx = {c: i + 1 for i, c in enumerate(sorted(tot, key=lambda c: -tot[c][0]))}
            rm = {c: i + 1 for i, c in enumerate(sorted(tot, key=lambda c: -tot[c][1]))}
            self._yrank[y] = (rx, rm, len(tot))
        return self._yrank[y]

    def year_view(self, iso, y):
        """The same shape as a deep.json record, built from the IMF figures of one calendar year."""
        I = self.IM[iso]; X, M = self._year_tot(iso, y); pa = I['pa'][str(y)]
        xp = sorted(([p, v[0]] for p, v in pa.items() if v[0] > 0), key=lambda r: -r[1])
        mp = sorted(([p, v[1]] for p, v in pa.items() if v[1] > 0), key=lambda r: -r[1])
        rx, rm, n = self._year_rank(y)
        est = any(m.startswith(str(y)) for m in I.get('xe', [])) or any(m.startswith(str(y)) for m in I.get('me', []))
        pn = (I.get('pn') or {}).get(str(y)) or [len(xp), len(mp)]
        d = dict(x=X, m=M, xp=xp, mp=mp, lead=[], dep=[], _y=y, _rk=(rx.get(iso), rm.get(iso), n), _est=est, _estp={p for p, v in pa.items() if v[2]},
                 nxp=max(pn[0], len(xp)), nmp=max(pn[1], len(mp)))
        if (y - 1) in self.years_of(iso):
            d['_prev'] = self._year_tot(iso, y - 1)
        return d

    def baci_year(self, iso, y):
        """Product detail for one year from BACI, or None. The newest year is deep.json; earlier ones are years.json."""
        if y == self.Y:
            return self.C.get(iso)
        return (self.YR.get(str(y)) or {}).get(iso)

    def year_href(self, iso, y):
        ys = self.years_of(iso)
        return f'/trade/{iso.lower()}' if (not ys or y == ys[-1]) else f'/trade/{iso.lower()}/{y}'

    def year_label(self, iso):
        """How the latest view is named: '2025–26' when the current year has months, else '2025'."""
        I = self.IM[iso]
        return f'{I["full"]}–{str(I["cur"])[2:]}' if I.get('cur') else str(I['full'])

    def yswitch(self, iso, y):
        ys = self.years_of(iso)[::-1]; nm = self.h['esc'](self.name(iso)); i = ys.index(y)
        chips = []
        for k, yy in enumerate(ys):
            lab = (self.year_label(iso) + ' <small>latest</small>') if k == 0 else str(yy)
            chips.append(f'<a href="{self.year_href(iso, yy)}"' + (' class="on" aria-current="page"' if yy == y else '') + f'>{lab}</a>')
        newer = (f'<a class="yar" href="{self.year_href(iso, ys[i - 1])}" rel="next" aria-label="Newer: {ys[i - 1]}">‹</a>' if i > 0 else '<span class="yar off" aria-hidden="true">‹</span>')
        older = (f'<a class="yar" href="{self.year_href(iso, ys[i + 1])}" rel="prev" aria-label="Older: {ys[i + 1]}">›</a>' if i + 1 < len(ys) else '<span class="yar off" aria-hidden="true">›</span>')
        return (f'<nav class="ysw" aria-label="{nm} trade by year"><span class="ysl">Year</span>{newer}<div class="ysc">{"".join(chips)}</div>{older}</nav>')

    def cy_title(self, c, y):
        ys = self.years_of(c['iso'])
        if y == ys[-1]:
            return f"{c['name']} Trade {self.year_label(c['iso'])}: Exports, Imports, Partners & Products"
        return f"{c['name']} Trade in {y}: Exports, Imports and Trading Partners"

    def cy_desc(self, c, y):
        d = self.year_view(c['iso'], y)
        s = f"{c['name']} exported {self.usd(d['x'])} and imported {self.usd(d['m'])} of goods in {y}."
        if d['xp']:
            s += f" Largest market: {self.name(d['xp'][0][0])} ({self.share(d['xp'][0][1], d['x'], 0)})."
        if d['mp']:
            s += f" Largest supplier: {self.name(d['mp'][0][0])} ({self.share(d['mp'][0][1], d['m'], 0)})."
        ys = self.years_of(c['iso'])
        return s + (f" Monthly figures to {self.MONTHS[self.IM[c['iso']]['upto'] - 1]} {self.IM[c['iso']]['cur']}, and every year back to {ys[0]}." if (y == ys[-1] and self.IM[c['iso']].get('cur')) else f" Partners{', products' if self.baci_year(c['iso'], y) else ''} and other years from {ys[0]} to {ys[-1]}.")

    def products_block(self, c, by, latest_note):
        """Products of one BACI year. The newest year carries main partner and world rank; earlier years the plain list."""
        h = self.h; e = h['esc']; iso = c['iso']; nm = e(c['name']); b = self.baci_year(iso, by)
        if not b or not (b.get('xk') or b.get('mk')):
            return ''
        X, M = b['x'], b['m']; rich = (by == self.Y)
        if rich:
            xrows = [(self.prod(k) + (f' <a class="pl" href="{self.pc_href(iso, k)}">buyers</a>' if self.pc_href(iso, k) else ''), self.usd(v), self.share(v, X), self.clink(tp) + f' <small>{self.share(tv, v, 0)}</small>', f'{ws}%' + (f' <span class="rk{r}">#{r}</span>' if r else ''))
                     for k, v, tp, tv, ws, r in b['xk'][:25]]
            mrows = [(self.prod(k), self.usd(v), self.share(v, M), self.clink(tp) + f' <small>{self.share(tv, v, 0)}</small>') for k, v, tp, tv in b['mk'][:25]]
            xt = self.table(['Product', 'Exports', 'Share of exports', 'Main buyer', 'World share'], xrows) if xrows else ''
            mt = self.table(['Product', 'Imports', 'Share of imports', 'Main supplier'], mrows) if mrows else ''
        else:
            xrows = [(self.prod(r[0]), self.usd(r[1]), self.share(r[1], X)) for r in b['xk'][:15]]
            mrows = [(self.prod(r[0]), self.usd(r[1]), self.share(r[1], M)) for r in b['mk'][:15]]
            xt = self.table(['Product', 'Exports', 'Share of exports'], xrows) if xrows else ''
            mt = self.table(['Product', 'Imports', 'Share of imports'], mrows) if mrows else ''
        tx = self.treemap(b.get('xc') or [], X, 'exp', c['name'], 'exports'); tm = self.treemap(b.get('mc') or [], M, 'imp', c['name'], 'imports')
        extra = ''
        if rich and b.get('lead'):
            extra += (f'<h3>Where {nm} is a top-three world exporter</h3>'
                      + self.table(['Product', 'Exports', 'World rank', 'World share'], [(self.prod(k), self.usd(v), f'<span class="rk{r}">#{r}</span>', f'{s}%') for k, v, r, s in b['lead']]))
        if rich and b.get('dep'):
            extra += (f'<h3>Imports that come mostly from one country</h3>'
                      + self.table(['Product', 'Imports', 'Main supplier', 'Its share'], [(self.prod(k), self.usd(v), self.clink(p), f'{s}%') for k, v, p, s in b['dep']])
                      + '<p class="fine">Products worth at least 0.1% of imports where a single supplier provides three-quarters or more.</p>')
        return (f'<section class="gsec" id="products"><h2>What {nm} trades: products in {by}</h2>'
                f'<p class="gk">{latest_note}Product figures are BACI&#39;s reconciled data, which matches each export to the partner&#39;s import record. On that basis {nm} exported {self.usd(X)} '
                f'and imported {self.usd(M)} in {by}, so these totals differ from the customs figures above. Shares below are of the BACI totals.</p>'
                + (f'<h3>Exports by product group, {by}</h3>' + tx if tx else '') + (f'<h3>Largest export products, {by}</h3>' + xt if xt else '')
                + (f'<p class="fine">{nm} exported {b["nx"]:,} different products in {by}.</p>' if b.get('nx') else '')
                + (f'<h3>Imports by product group, {by}</h3>' + tm if tm else '') + (f'<h3>Largest import products, {by}</h3>' + mt if mt else '') + extra + '</section>')

    def country_year(self, c, y=None):
        h = self.h; e = h['esc']; iso = c['iso']; nm = e(c['name']); ys = self.years_of(iso); I = self.IM[iso]
        latest = y is None or y == ys[-1]; y = ys[-1] if y is None else y
        d = self.year_view(iso, y); X, M = d['x'], d['m']; bal = X - M; xp, mp = d['xp'], d['mp']
        rx, rm, n = d['_rk']
        est = lambda p: (self.EST if p in d['_estp'] else '')
        lead = (f'<p class="ans">{nm} exported <b>{self.usd(X)}</b> of goods and imported <b>{self.usd(M)}</b> in {y}, '
                f'a trade {"surplus" if bal >= 0 else "deficit"} of <b>{self.usd(abs(bal))}</b>.'
                + (f' Its largest export market was {self.clink(xp[0][0])} ({self.share(xp[0][1], X)} of exports)' if xp else '')
                + (f' and its largest supplier was {self.clink(mp[0][0])} ({self.share(mp[0][1], M)} of imports).' if mp else '.')
                + (f' Against {y - 1}, exports changed by {self._chg(X, d["_prev"][0])} and imports by {self._chg(M, d["_prev"][1])}.' if d.get('_prev') else '') + '</p>')
        estn = (f'<p class="fine">{self.EST} {nm} had not reported some or all of {y} to the IMF when this was built, so those figures were derived by the IMF from its partners&#39; records. Treat them as provisional.</p>'
                if (d['_est'] or d['_estp']) else '')
        rk = (f'{e(c["region"])} · ' if c.get('region') else '') + f'World rank <b>#{rx or "–"}</b> exporter, <b>#{rm or "–"}</b> importer of {n} economies ({y}).'
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(X)}</b><span>Exports ({y})</span></div>'
                 f'<div class="s"><b class="im">{self.usd(M)}</b><span>Imports ({y})</span></div>'
                 f'<div class="s"><b style="color:{"var(--free)" if bal >= 0 else "var(--hi)"}">{"+" if bal >= 0 else "−"}{self.usd(abs(bal))[1:]}</b><span>Trade balance</span></div>'
                 f'<div class="s"><b>{d["nxp"]}</b><span>Export markets</span></div></div>')

        def partner_rows(lst, total, k=10):
            out = []
            for p, v in lst[:k]:
                ph = self.pair_href(iso, p)
                out.append((self.clink(p) + est(p) + (f' <a class="pl" href="{ph}">pair</a>' if ph else ''), v, f'{self.usd(v)} <small>{self.share(v, total)}</small>'))
            return out
        sec_p = ''
        if not latest:
            sec_p = (f'<section class="gsec gx"><h2>Where {nm} sold its goods in {y}</h2><p class="gk">{nm} exported {self.usd(X)} of goods to {d["nxp"]} markets in {y}.</p>'
                     + self.barlist(partner_rows(xp, X), 'var(--exp)') + '</section>'
                     f'<section class="gsec gm2"><h2>Where {nm} bought its goods in {y}</h2><p class="gk">{nm} imported {self.usd(M)} of goods from {d["nmp"]} suppliers in {y}.</p>'
                     + self.barlist(partner_rows(mp, M), 'var(--imp)') + '</section>')
        allp = {}
        for p, v in xp:
            allp.setdefault(p, [0, 0])[0] = v
        for p, v in mp:
            allp.setdefault(p, [0, 0])[1] = v
        bals = sorted(((p, a - b) for p, (a, b) in allp.items()), key=lambda kv: kv[1])
        sur = [x for x in bals[::-1] if x[1] > 0][:6]; dfc = [x for x in bals if x[1] < 0][:6]
        sec_bal = (f'<section class="gsec"><h2>Where {nm} ran a surplus, and where a deficit</h2>'
                   f'<p class="gk">Exports to each partner minus imports from it, {y}. The six largest on each side, on one scale.</p>'
                   + self.balance_chart(sur, dfc[::-1]) + '</section>') if (sur or dfc) else ''
        prow = sorted(allp.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:80]
        allrows = [(self.clink(p) + est(p), self.usd(a) if a else '—', self.usd(b) if b else '—', ('+' if a - b >= 0 else '−') + self.usd(abs(a - b))[1:]) for p, (a, b) in prow]
        sec_all = (f'<details class="dall"><summary>The {len(allrows)} largest trading partners of {nm} in {y}</summary>'
                   + self.table(['Partner', f'{nm} exports to', f'{nm} imports from', 'Balance'], allrows) + '</details>')
        sec_map = f'<section class="gsec"><h2>{nm}&#39;s partners on the map, {y}</h2>' + self.map_block(iso, d) + sec_all + '</section>'

        # products: the BACI year that matches, or on the latest view the newest BACI year, labelled as such
        by = y if self.baci_year(iso, y) else (self.Y if latest else None)
        note = (f'Product detail for every economy is published once a year, and {by} is the newest year available; {by + 1} is expected early in {by + 3}. ' if (latest and by and by != y) else '')
        prod = self.products_block(c, by, note) if by else ''
        if not prod and not latest:
            prod = f'<section class="gsec"><h2>Products</h2><p class="gk">Product detail on this site starts in {min(int(k) for k in self.YR) if self.YR else self.Y}. For {y} this page has totals and partners only.</p></section>'

        # every year, linked
        yrows = []
        if latest and I.get('cur'):
            sp = self._span(I); a = sum(I['x'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1)); b = sum(I['m'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1))
            yrows.append((f'{I["cur"]} ({sp.rsplit(" ", 1)[0]})', self.usd(a), self.usd(b), ('+' if a - b >= 0 else '−') + self.usd(abs(a - b))[1:]))
        for yy in ys[::-1]:
            a, b = self._year_tot(iso, yy)
            yrows.append((f'<b>{yy}</b>' if yy == y else f'<a href="{self.year_href(iso, yy)}">{yy}</a>', self.usd(a), self.usd(b), ('+' if a - b >= 0 else '−') + self.usd(abs(a - b))[1:]))
        LY = self.long_years(iso); hist = {str(yy): list(v) for yy, v in LY.items()}
        older = [(str(yy), self.usd(v[0]), self.usd(v[1]), ('+' if v[0] - v[1] >= 0 else '−') + self.usd(abs(v[0] - v[1]))[1:]) for yy, v in sorted(LY.items(), reverse=True) if yy < ys[0]]
        sec_time = (f'<section class="gsec" id="years"><h2>{nm}&#39;s trade year by year</h2><p class="gk">Customs figures in US dollars. Choose a year for its partners{" and products" if self.YR else ""}.</p>'
                    + self.year_cols(hist, 'Exports', 'Imports') + self.table(['Year', 'Exports', 'Imports', 'Balance'], yrows)
                    + (f'<details class="tml"><summary>Earlier years, {older[-1][0]} to {older[0][0]}</summary>' + self.table(['Year', 'Exports', 'Imports', 'Balance'], older) + '</details>' if older else '')
                    + (self.then_now(iso) if latest else '')
                    + (f'<h3>Longer trend, World Bank series</h3>{h["trend_svg"](c.get("trend") or [])}' if (latest and c.get('trend')) else '') + '</section>')
        src = h['src_box']('Sources', f'<p>Totals and partners for every year on this page: <b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}. '
                           f'These are each economy&#39;s own customs figures, converted to US dollars at the average exchange rate of each month; imports include freight and insurance, exports do not. '
                           + (f'Products for {by}: <b>BACI</b> (CEPII), reconciled from UN Comtrade at the 6-digit HS level. ' if by else '')
                           + ('The longer trend is the <b>World Bank</b> merchandise trade series. ' if (latest and c.get('trend')) else '')
                           + 'The sources use different methods, so compare like with like. <a href="/about">About the data</a></p>', str(y))
        head = (h['back']('/trade', 'Global trade') if latest else h['back'](f'/trade/{iso.lower()}', f'{c["name"]}: latest'))
        title = f'{c["flag"]} {nm}: trade in {y}' + (f' and {I["cur"]}' if (latest and I.get('cur')) else '')
        top = head + f'<div class="ph"><h1 class="h2">{title}</h1><p>{rk}</p></div>' + self.yswitch(iso, y) + lead + estn
        if latest:
            prs_all = self.pairs_of.get(iso, []); prs = prs_all[:30]
            sec_pairs = ''
            if prs:
                sec_pairs = (f'<section class="gsec"><h2>{nm} and its partners, pair by pair</h2><div class="pairgrid">'
                             + ''.join(f'<a href="{self.pair_href(iso, p)}">{self.flag(iso)} {nm} – {self.flag(p)} {e(self.name(p))}</a>' for p in prs) + '</div>'
                             + (f'<p class="fine">The 30 largest of {len(prs_all)} pair pages. <a href="/trade/pairs">All country pairs</a></p>' if len(prs_all) > 30 else '') + '</section>')
            sl = self.sanc_href(iso); cmp_ = self.compare_href(iso)
            return h['main'](top + self.highlights(iso, d)
                             + (f'<p class="fine" style="margin-top:12px">{nm} is named in sanctions programmes and its figures come from partner records. <a href="{sl}">{nm}: trade under sanctions, year by year</a></p>' if sl else '')
                             + (f'<p class="pdfl"><a href="{self.brief_href(iso)}" download>Download the {nm} trade brief (PDF)</a> <span>Key figures, partners, products and history on a few pages, free to share.</span></p>' if iso in self.C else '')
                             + (self.nepal_official() + '<p class="fine">More on Nepal: <a href="/nepal/exports">export explorer by market</a> and <a href="/nepal">world prices against what Nepal pays</a>.</p>' if iso == 'NPL' else '')
                             + (f'<p class="fine" style="margin-top:10px"><a href="{cmp_[0]}">Compare {nm} with {e(cmp_[1][0])} and {e(cmp_[1][1])}</a></p>' if cmp_ else '')
                             + (f'<p class="fine"><a href="{self.copp_href(iso)}">Export markets with rising demand for {nm}</a></p>' if self.copp_ok(iso) else '')
                             + self.tpo_line(iso)
                             + self.latest(iso) + self.flow(iso, d) + sec_bal + sec_map + self.latest_products(iso) + prod + sec_time + sec_pairs + (self.peers(c) if iso in self.C else '') + src)
        return h['main'](top + tiles + self.highlights(iso, d) + self.flow(iso, d) + sec_p + sec_bal + sec_map + prod + sec_time + src)

    # ---------- latest year across all economies (home page and the rankings page)
    def latest_year(self):
        """The newest complete year most economies have, and the totals for it: (year, {iso: (exports, imports)})."""
        known = self.h['CBYISO']; cnt = {}
        for c in self.IM:
            if c in known and self.years_of(c):
                cnt[self.years_of(c)[-1]] = cnt.get(self.years_of(c)[-1], 0) + 1
        if not cnt:
            return None, {}
        y = max(cnt, key=lambda k: cnt[k])
        return y, {c: self._year_tot(c, y) for c in self.IM if c in known and y in self.years_of(c)}

    def rankings(self):
        h = self.h; e = h['esc']; y, tot = self.latest_year()
        WX = sum(v[0] for v in tot.values()); WM = sum(v[1] for v in tot.values())
        prev = {c: self._year_tot(c, y - 1) for c in tot if (y - 1) in self.years_of(c)}
        PX = sum(prev[c][0] for c in prev); CX = sum(tot[c][0] for c in prev)
        any_cur = next((self.IM[c] for c in tot if self.IM[c].get('cur')), None); span = self._span(any_cur) if any_cur else ''
        rm = {c: i + 1 for i, c in enumerate(sorted(tot, key=lambda c: -tot[c][1]))}
        rows = []
        for i, c in enumerate(sorted(tot, key=lambda c: -tot[c][0]), 1):
            X, M = tot[c]; I = self.IM[c]; pv = prev.get(c)
            ytd = sum(I['x'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1)) if (I.get('cur') and self._span(I) == span) else None
            est = self.EST if any(m.startswith(str(y)) for m in I.get('xe', [])) else ''
            rows.append(f'<tr data-n="{e(self.name(c).lower())}"><td class="rkn">{i}</td><td>{self.clink(c)}{est}</td><td class=r>{self.usd(X)}</td><td class=r>{self._chg(X, pv[0]) if pv else "—"}</td>'
                        f'<td class=r>{self.usd(M)}</td><td class=r>#{rm[c]}</td><td class=r>{("+" if X - M >= 0 else "−") + self.usd(abs(X - M))[1:]}</td>' + (f'<td class=r>{self.usd(ytd) if ytd else "—"}</td>' if span else '') + '</tr>')
        top = sorted(tot, key=lambda c: -tot[c][0])[:10]; mx = tot[top[0]][0]
        bars = self.barlist([(self.clink(c), tot[c][0], f'{self.usd(tot[c][0])} <small>{self.share(tot[c][0], WX)}</small>') for c in top], 'var(--exp)')
        topm = sorted(tot, key=lambda c: -tot[c][1])[:10]
        barsm = self.barlist([(self.clink(c), tot[c][1], f'{self.usd(tot[c][1])} <small>{self.share(tot[c][1], WM)}</small>') for c in topm], 'var(--imp)')
        js = ('<script>(function(){var q=document.getElementById("rq"),r=document.querySelectorAll("#rkt tbody tr");if(!q)return;'
              'q.addEventListener("input",function(){var v=q.value.trim().toLowerCase();r.forEach(function(t){t.hidden=!!v&&t.getAttribute("data-n").indexOf(v)<0})})})();</script>')
        return h['main'](h['back']('/', 'Home') + f'<div class="ph"><h1 class="h2">World trade rankings, {y}</h1>'
                         f'<p>The {len(tot)} economies on this site exported <b>{self.usd(WX)}</b> of goods in {y}' + (f', {self._chg(CX, PX)} on {y - 1}' if PX else '') + '. Ranked by exports, with imports, balance'
                         + (f' and {span}' if span else '') + '.</p></div>'
                         f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(WX)}</b><span>Exports, all economies ({y})</span></div>'
                         f'<div class="s"><b class="im">{self.usd(WM)}</b><span>Imports, all economies ({y})</span></div><div class="s"><b>{len(tot)}</b><span>Economies</span></div></div>'
                         f'<section class="gsec gx"><h2>The ten largest exporters, {y}</h2>{bars}</section><section class="gsec gm2"><h2>The ten largest importers, {y}</h2>{barsm}</section>'
                         f'<section class="gsec"><h2>Every economy, {y}</h2><div class="sbox">{h["ic"]("search")}<input id="rq" type="search" placeholder="Find a country…" autocomplete="off" aria-label="Find a country"></div>'
                         f'<div class="dscroll"><table class="dt" id="rkt"><thead><tr><th>#</th><th>Economy</th><th class=r>Exports {y}</th><th class=r>Change on {y - 1}</th><th class=r>Imports {y}</th><th class=r>Import rank</th><th class=r>Balance</th>'
                         + (f'<th class=r>Exports {span}</th>' if span else '') + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
                         f'<p class="fine">{self.EST} Not yet reported by the economy for some or all of {y}; derived by the IMF from its partners&#39; records. Imports include freight and insurance and exports do not, so the two world totals differ.</p></section>'
                         f'<section class="gsec"><h2>More ways in</h2><div class="two"><a class="nepalcard" href="/trade/pairs"><span class="fl">🤝</span><span><b>Country pairs</b> {h["ic"]("right")}</span></a></div>'
                         + (f'<h3>Profiles without {y} customs figures</h3><div class="pairgrid">' + ''.join(self.clink(c) for c in sorted(h['CBYISO'], key=self.name) if c not in tot) + '</div>' if any(c not in tot for c in h['CBYISO']) else '')
                         + f'<h3>By region</h3>{self.region_nav()}<h3>By trade bloc or group</h3>{self.bloc_nav()}<h3>By theme</h3><div class="pairgrid"><a href="/trade/latest">What changed this year</a><a href="/compare">Compare countries</a><a href="/opportunities">Market opportunities</a><a href="/trade/sanctions">Trade under sanctions</a></div><h3>Trade by product group</h3>{h["pgroup_grid"]().replace(" data-nav", "")}</section>'
                         + h['src_box']('Source', f'<p><b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each economy&#39;s own customs figures in US dollars, '
                                        f'converted at the average exchange rate of each month. Each economy&#39;s page has every year back to 2019. <a href="/about">About the data</a></p>', str(y)) + js)

    # ---------- regions (World Bank grouping), latest customs year
    REGION_SLUGS = {'East Asia & Pacific': 'east-asia-pacific', 'Europe & Central Asia': 'europe-central-asia', 'Latin America & Caribbean': 'latin-america-caribbean',
                    'Middle East, North Africa, Afghanistan & Pakistan': 'middle-east-north-africa', 'North America': 'north-america', 'Sub-Saharan Africa': 'sub-saharan-africa'}

    def region_members(self, name):
        y, tot = self.latest_year()
        return [c for c in tot if (self.h['CBYISO'][c].get('region') or '').strip() == name]

    def region_href(self, name):
        name = (name or '').strip()
        return '/trade/region/south-asia' if name == 'South Asia' else (f'/trade/region/{self.REGION_SLUGS[name]}' if name in self.REGION_SLUGS else None)

    def regions_list(self):
        return [(n, s) for n, s in self.REGION_SLUGS.items() if self.region_members(n)]

    def region_nav(self, current=None):
        items = [(n, f'/trade/region/{s}') for n, s in self.regions_list()] + [('South Asia', '/trade/region/south-asia')]
        return '<div class="pairgrid">' + ''.join((f'<a href="{href}"' + (' aria-current="page" style="font-weight:700"' if n == current else '') + f'>{self.h["esc"](n)}</a>') for n, href in sorted(items)) + '</div>'

    def wregion_title(self, name):
        y, _ = self.latest_year()
        return f'{name} Trade {y}: Exports and Imports by Country'

    def wregion_desc(self, name):
        y, tot = self.latest_year(); S = self.region_members(name)
        top = sorted(S, key=lambda c: -tot[c][0])[:3]
        return (f'{name}: {len(S)} economies exported {self.usd(sum(tot[c][0] for c in S))} of goods in {y}. Largest exporters: {", ".join(self.name(c) for c in top)}. '
                f'Ranking, trade inside the region and its largest outside markets.')

    def wregion(self, name):
        h = self.h; e = h['esc']; y, tot = self.latest_year(); S = self.region_members(name); inS = set(S); N = e(name)
        RX = sum(tot[c][0] for c in S); RM = sum(tot[c][1] for c in S); WX = sum(v[0] for v in tot.values())
        intra = 0; out = {}
        for c in S:
            for p, v in self.IM[c]['pa'][str(y)].items():
                if p in inS:
                    intra += v[0]
                elif v[0]:
                    out[p] = out.get(p, 0) + v[0]
        prevS = [c for c in S if (y - 1) in self.years_of(c)]
        PX = sum(self._year_tot(c, y - 1)[0] for c in prevS); CX = sum(tot[c][0] for c in prevS)
        any_cur = next((self.IM[c] for c in S if self.IM[c].get('cur')), None); span = self._span(any_cur) if any_cur else ''
        lead = (f'<p class="ans">The {len(S)} economies of {N} exported <b>{self.usd(RX)}</b> of goods and imported <b>{self.usd(RM)}</b> in {y}'
                + (f', with exports {self._chg(CX, PX)} on {y - 1}' if PX else '') + f'. That is <b>{self.share(RX, WX)}</b> of the exports of all {len(tot)} economies on this site. '
                f'<b>{self.share(intra, RX)}</b> of the region&#39;s exports, {self.usd(intra)}, went to other economies inside it.</p>')
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(RX)}</b><span>Exports ({y})</span></div>'
                 f'<div class="s"><b class="im">{self.usd(RM)}</b><span>Imports ({y})</span></div>'
                 f'<div class="s"><b>{self.share(RX, WX)}</b><span>Share of all exports</span></div><div class="s"><b>{self.share(intra, RX)}</b><span>Exports staying in the region</span></div></div>')
        top = sorted(S, key=lambda c: -tot[c][0])
        bars = self.barlist([(self.clink(c), tot[c][0], f'{self.usd(tot[c][0])} <small>{self.share(tot[c][0], RX)}</small>') for c in top[:10]], 'var(--exp)')
        rows = []
        for i, c in enumerate(top, 1):
            X, M = tot[c]; I = self.IM[c]; pv = self._year_tot(c, y - 1) if (y - 1) in self.years_of(c) else None
            ytd = sum(I['x'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1)) if (I.get('cur') and self._span(I) == span) else None
            est = self.EST if any(m.startswith(str(y)) for m in I.get('xe', [])) else ''
            rows.append([f'<span class="rkn">{i}</span> ' + self.clink(c) + est, self.usd(X), self._chg(X, pv[0]) if pv else '—', self.usd(M), ('+' if X - M >= 0 else '−') + self.usd(abs(X - M))[1:]] + ([self.usd(ytd) if ytd else '—'] if span else []))
        tbl = self.table(['Economy', f'Exports {y}', f'Change on {y - 1}', f'Imports {y}', 'Balance'] + ([f'Exports {span}'] if span else []), rows)
        outs = sorted(out.items(), key=lambda kv: -kv[1])[:10]
        sec_out = (f'<section class="gsec gx"><h2>Where {N} sells outside the region</h2><p class="gk">Exports of the region&#39;s economies to partners outside it, {y}, added up.</p>'
                   + self.barlist([(self.clink(p), v, f'{self.usd(v)} <small>{self.share(v, RX)}</small>') for p, v in outs], 'var(--exp)') + '</section>') if outs else ''
        hist = {}
        for yy in range(y - 6, y + 1):
            ms = [c for c in S if yy in self.years_of(c)]
            if len(ms) == len(S):
                hist[str(yy)] = [sum(self._year_tot(c, yy)[0] for c in S), sum(self._year_tot(c, yy)[1] for c in S)]
        sec_hist = (f'<section class="gsec"><h2>{N} year by year</h2>' + self.year_cols(hist, 'Exports', 'Imports')
                    + self.table(['Year', 'Exports', 'Imports', 'Balance'], [(k, self.usd(v[0]), self.usd(v[1]), ('+' if v[0] - v[1] >= 0 else '−') + self.usd(abs(v[0] - v[1]))[1:]) for k, v in sorted(hist.items(), reverse=True)])
                    + '</section>') if len(hist) > 1 else ''
        return h['main'](h['back']('/trade', 'World rankings') + f'<div class="ph"><h1 class="h2">{N}: trade in {y}</h1><p>{len(S)} economies, ranked by exports. Grouping follows the World Bank&#39;s regions.</p></div>'
                         + lead + tiles + f'<section class="gsec gx"><h2>The largest exporters in {N}, {y}</h2>{bars}</section>'
                         + f'<section class="gsec"><h2>Every economy in {N}, {y}</h2>{tbl}'
                         f'<p class="fine">{self.EST} Not yet reported by the economy for some or all of {y}; derived by the IMF from its partners&#39; records.</p></section>'
                         + sec_out + sec_hist + '<section class="gsec"><h2>Other regions</h2>' + self.region_nav(name) + '<h3>Trade blocs and groups</h3>' + self.bloc_nav() + '</section>'
                         + h['src_box']('Source', f'<p><b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each economy&#39;s own customs figures in US dollars. '
                                        f'Regional totals are sums of the economies listed, so they count trade between members. <a href="/about">About the data</a></p>', str(y)))

    # ---------- trade blocs and groups (membership as stated in BLOC_DATE; one fixed member list applied to every year)
    BLOC_DATE = '15 November 2026'
    _EU = 'AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE'
    _ASEAN = 'BRN KHM IDN LAO MYS MMR PHL SGP THA TLS VNM'
    BLOCS = {      # slug: (name, kind, members, note)
        'european-union': ('European Union', 'Customs union and single market', _EU, 'The 27 member states. The United Kingdom left in 2020 and is not included in any year.'),
        'asean': ('ASEAN', 'Association of Southeast Asian Nations', _ASEAN, 'The 11 member states. Timor-Leste joined in October 2025 and is included in every year shown.'),
        'gcc': ('GCC', 'Gulf Cooperation Council', 'BHR KWT OMN QAT SAU ARE', 'The six member states.'),
        'mercosur': ('Mercosur', 'Southern Common Market', 'ARG BOL BRA PRY URY', 'The five active full members. Bolivia became a full member in 2024 and is included in every year. Venezuela has been suspended since 2016 and is not included.'),
        'usmca': ('USMCA', 'United States–Mexico–Canada Agreement', 'CAN MEX USA', 'The three parties to the agreement, which replaced NAFTA in 2020.'),
        'eaeu': ('Eurasian Economic Union', 'Customs union', 'ARM BLR KAZ KGZ RUS', 'The five member states.'),
        'rcep': ('RCEP', 'Regional Comprehensive Economic Partnership', 'AUS BRN KHM CHN IDN JPN KOR LAO MYS MMR NZL PHL SGP THA VNM', 'The 15 signatories.'),
        'cptpp': ('CPTPP', 'Comprehensive and Progressive Agreement for Trans-Pacific Partnership', 'AUS BRN CAN CHL JPN MYS MEX NZL PER SGP GBR VNM', 'The 12 parties. The United Kingdom joined in December 2024 and is included in every year shown.'),
        'brics': ('BRICS', 'Group of emerging economies', 'BRA RUS IND CHN ZAF EGY ETH IRN ARE IDN',
                  'Ten members: the original five, the four that joined in 2024 and Indonesia, which joined in 2025; all are included in every year shown. Saudi Arabia was invited in 2023 and some sources count it as a member; it is not included here.'),
        'g7': ('G7', 'Group of Seven', 'CAN FRA DEU ITA JPN GBR USA', 'The seven member countries. The European Union also takes part and is not added.'),
        'g20': ('G20', 'Group of Twenty', 'ARG AUS BRA CAN CHN FRA DEU IND IDN ITA JPN KOR MEX RUS SAU ZAF TUR GBR USA', 'The 19 member countries. The European Union and the African Union are also members and are not added, to avoid counting countries twice.'),
        'opec': ('OPEC', 'Organization of the Petroleum Exporting Countries', 'DZA COG GNQ GAB IRN IRQ KWT LBY NGA SAU ARE VEN',
                 'The 12 countries OPEC lists as members. The United Arab Emirates announced its withdrawal with effect from 1 May 2026; it is included because the yearly figures here end before that date. Figures are all goods, not only oil.'),
        'oecd': ('OECD', 'Organisation for Economic Co-operation and Development', 'AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA', 'The 38 member countries.'),
        'arab-league': ('Arab League', 'League of Arab States', 'DZA BHR COM DJI EGY IRQ JOR KWT LBN LBY MRT MAR OMN PSE QAT SAU SOM SDN SYR TUN ARE YEM', 'The 22 members.'),
        'african-union': ('African Union', 'Continental union', 'DZA AGO BEN BWA BFA BDI CPV CMR CAF TCD COM COG COD CIV DJI EGY GNQ ERI SWZ ETH GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA STP SEN SYC SLE SOM ZAF SSD SDN TZA TGO TUN UGA ZMB ZWE',
                          'The member states, including those whose participation is currently suspended. The Sahrawi Republic is a member with no trade figures.'),
        'middle-east': ('Middle East', 'Geographic area', 'BHR IRN IRQ ISR JOR KWT LBN OMN QAT SAU SYR ARE YEM PSE',
                        'There is no single agreed definition. This page uses 14 economies of Western Asia; Egypt is counted with Africa, and Turkey and Cyprus with Europe.'),
    }

    def bloc_members(self, slug):
        """(members with figures for the latest year, members without)."""
        y, tot = self.latest_year(); ms = self.BLOCS[slug][2].split()
        return [c for c in ms if c in tot], [c for c in ms if c not in tot]

    def bloc_list(self):
        if getattr(self, '_blocs', None) is None:      # asked for on every page (the menu), so worked out once
            self._blocs = [s for s in self.BLOCS if len(self.bloc_members(s)[0]) >= 2] if self.latest_year()[0] else []
        return self._blocs

    def bloc_href(self, slug):
        return f'/trade/bloc/{slug}'

    def _bloc_year(self, S, yy):
        """Exports, imports, exports to members, imports from members for one year, or None unless every member has the year."""
        if not all(yy in self.years_of(c) for c in S):
            return None
        inS = set(S); X = M = ix = im = 0
        for c in S:
            t = self._year_tot(c, yy); X += t[0]; M += t[1]
            for p, v in self.IM[c]['pa'][str(yy)].items():
                if p in inS:
                    ix += v[0]; im += v[1]
        return X, M, ix, im

    def bloc_title(self, slug):
        y, _ = self.latest_year()
        return f'{self.BLOCS[slug][0]} Trade {y}: Exports, Imports and Trade Between Members'

    def bloc_desc(self, slug):
        y, tot = self.latest_year(); S, _ = self.bloc_members(slug); b = self._bloc_year(S, y); nm = self.BLOCS[slug][0]
        top = sorted(S, key=lambda c: -tot[c][0])[:3]
        return (f'{nm}: {len(S)} economies exported {self.usd(b[0])} of goods in {y}; {self.share(b[2], b[0], 0)} of it went to other members. '
                f'Largest exporters: {", ".join(self.name(c) for c in top)}. Members ranked, outside partners, and totals since 2000.')

    def bloc_nav(self, current=None):
        return '<div class="pairgrid">' + ''.join(f'<a href="{self.bloc_href(s)}"' + (' aria-current="page" style="font-weight:700"' if s == current else '') + f'>{self.h["esc"](self.BLOCS[s][0])}</a>' for s in self.bloc_list()) + '</div>'

    def bloc(self, slug):
        h = self.h; e = h['esc']; y, tot = self.latest_year(); name, kind, _, note = self.BLOCS[slug]; N = e(name); S, missing = self.bloc_members(slug); inS = set(S)
        RX, RM, ix, im = self._bloc_year(S, y); WX = sum(v[0] for v in tot.values()); prev = self._bloc_year(S, y - 1)
        outx = {}; outm = {}
        for c in S:
            for p, v in self.IM[c]['pa'][str(y)].items():
                if p not in inS:
                    if v[0]: outx[p] = outx.get(p, 0) + v[0]
                    if v[1]: outm[p] = outm.get(p, 0) + v[1]
        signed = lambda v: ('+' if v >= 0 else '−') + self.usd(abs(v))
        lead = (f'<p class="ans">The {len(S)} economies counted here exported <b>{self.usd(RX)}</b> of goods and imported <b>{self.usd(RM)}</b> in {y}'
                + (f', with exports {self._chg(RX, prev[0])} on {y - 1}' if prev else '') + f'. <b>{self.share(ix, RX)}</b> of those exports, {self.usd(ix)}, went to other members; '
                f'the remaining {self.usd(RX - ix)} went to the rest of the world. Members&#39; exports add up to {self.share(RX, WX)} of the exports of all {len(tot)} economies on this site.</p>')
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(RX)}</b><span>Exports ({y})</span></div>'
                 f'<div class="s"><b class="im">{self.usd(RM)}</b><span>Imports ({y})</span></div>'
                 f'<div class="s"><b>{self.share(ix, RX)}</b><span>Exports going to members</span></div><div class="s"><b>{self.usd(RX - ix)}</b><span>Exports to the rest of the world</span></div></div>')
        top = sorted(S, key=lambda c: -tot[c][0]); any_cur = next((self.IM[c] for c in S if self.IM[c].get('cur')), None); span = self._span(any_cur) if any_cur else ''
        rows = []; yn = yt = 0
        for i, c in enumerate(top, 1):
            X, M = tot[c]; I = self.IM[c]; pv = self._year_tot(c, y - 1) if (y - 1) in self.years_of(c) else None
            ok = bool(I.get('cur') and self._span(I) == span)
            a = sum(I['x'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1)) if ok else 0
            b = sum(I['x'].get(f'{I["cur"] - 1}-{k:02d}', 0) for k in range(1, I['upto'] + 1)) if ok else 0
            if a and b:
                yn += a; yt += b
            tom = sum(v[0] for p, v in I['pa'][str(y)].items() if p in inS)
            est = self.EST if any(m.startswith(str(y)) for m in I.get('xe', [])) else ''
            rows.append([f'<span class="rkn">{i}</span> ' + self.clink(c) + est, self.usd(X), self._chg(X, pv[0]) if pv else '—', self.usd(M), signed(X - M), self.share(tom, X, 0)] + ([self.usd(a) if a else '—'] if span else []))
        tbl = self.table(['Economy', f'Exports {y}', f'Change on {y - 1}', f'Imports {y}', 'Balance', 'Exports to members'] + ([f'Exports {span}'] if span else []), rows)
        ytd = (f'<p>In {span}, the members with figures for those months exported {self.usd(yn)}, {self._chg(yn, yt)} on the same months a year earlier.</p>') if yn and yt else ''
        bars = self.barlist([(self.clink(c), tot[c][0], f'{self.usd(tot[c][0])} <small>{self.share(tot[c][0], RX)}</small>') for c in top[:10]], 'var(--exp)')
        ob = lambda d, tot_, col: self.barlist([(self.clink(p), v, f'{self.usd(v)} <small>{self.share(v, tot_)}</small>') for p, v in sorted(d.items(), key=lambda kv: -kv[1])[:10]], col)
        sec_out = (f'<section class="gsec gx"><h2>Where {N} sells outside the group</h2><p class="gk">Members&#39; exports to partners that are not members, {y}, added up. Shares are of exports to the rest of the world.</p>{ob(outx, RX - ix, "var(--exp)")}</section>' if outx else '') \
            + (f'<section class="gsec gm2"><h2>Where {N} buys outside the group</h2><p class="gk">Members&#39; imports from partners that are not members, {y}, added up.</p>{ob(outm, RM - im, "var(--imp)")}</section>' if outm else '')
        intra = [(yy, self._bloc_year(S, yy)) for yy in range(2019, y + 1)]; intra = [(yy, b) for yy, b in intra if b]
        sec_intra = (f'<section class="gsec"><h2>Trade between members, {intra[0][0]} to {intra[-1][0]}</h2><p class="gk">Exports of members to each other, and the share of all members&#39; exports that this makes up.</p>'
                     + self.table(['Year', 'Exports of all members', 'Of which to members', 'Share', 'To the rest of the world'], [(str(yy), self.usd(b[0]), self.usd(b[2]), self.share(b[2], b[0]), self.usd(b[0] - b[2])) for yy, b in intra[::-1]])
                     + '</section>') if len(intra) > 1 else ''
        L = [self.long_years(c) for c in S]; ys = sorted(set.intersection(*[set(l) for l in L])) if L else []
        hist = {str(yy): [sum(l[yy][0] for l in L), sum(l[yy][1] for l in L)] for yy in ys}
        sec_hist = (f'<section class="gsec"><h2>{N} exports and imports, {ys[0]} to {ys[-1]}</h2><p class="gk">Sums of the members&#39; totals for the years in which every member has figures. They include trade between members.</p>'
                    + self.year_cols(hist, 'Exports', 'Imports')
                    + '<details class="more"><summary>Year-by-year table</summary>' + self.table(['Year', 'Exports', 'Imports', 'Balance'], [(k, self.usd(v[0]), self.usd(v[1]), signed(v[0] - v[1])) for k, v in sorted(hist.items(), reverse=True)]) + '</details></section>') if len(hist) > 2 else ''
        miss = (f' No figures for {y}: {", ".join(e(self.name(c)) for c in missing)}.' if missing else '')
        return h['main'](h['back']('/trade/blocs', 'Regions and blocs') + f'<div class="ph"><h1 class="h2">{N}: trade in {y}</h1><p>{e(kind)}. {len(S)} economies with figures, ranked by exports.</p></div>'
                         + lead + tiles + ytd
                         + f'<section class="gsec"><h2>Who is counted</h2><p>{e(note)}{miss} Membership as of {self.BLOC_DATE}; the same list is used for every year, so earlier years show today&#39;s members, not the membership of the time.</p></section>'
                         + f'<section class="gsec gx"><h2>The largest exporters in {N}, {y}</h2>{bars}</section>'
                         + f'<section class="gsec"><h2>Every member, {y}</h2>{tbl}<p class="fine">{self.EST} Not yet reported by the economy for some or all of {y}; derived by the IMF from its partners&#39; records.</p></section>'
                         + sec_out + sec_intra + sec_hist + '<section class="gsec"><h2>Other blocs and groups</h2>' + self.bloc_nav(slug) + '<h3>Regions</h3>' + self.region_nav() + '</section>'
                         + h['src_box']('Source', f'<p><b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each economy&#39;s own customs figures in US dollars. '
                                        f'Group totals are sums of the members listed. Trade between members is taken from the exporting member&#39;s records. <a href="/about">About the data</a></p>', str(y)))

    def bloc_hub(self):
        h = self.h; e = h['esc']; y, tot = self.latest_year(); WX = sum(v[0] for v in tot.values()); rows = []
        for s in self.bloc_list():
            S, _ = self.bloc_members(s); b = self._bloc_year(S, y)
            rows.append((b[0], (f'<a href="{self.bloc_href(s)}"><b>{e(self.BLOCS[s][0])}</b></a> <small>{e(self.BLOCS[s][1])}</small>', str(len(S)), self.usd(b[0]), self.usd(b[1]), self.share(b[0], WX), self.share(b[2], b[0]))))
        tbl = self.table(['Group', 'Members', f'Exports {y}', f'Imports {y}', 'Share of all exports', 'Exports going to members'], [r for _, r in sorted(rows, key=lambda r: -r[0])])
        return h['main'](h['back']('/trade', 'World rankings') + f'<div class="ph"><h1 class="h2">Regions and trade blocs: trade in {y}</h1>'
                         f'<p>{len(rows)} blocs and groups and seven regions, each with its members ranked, trade between members, outside partners and totals since 2000.</p></div>'
                         f'<p class="ans">Groups overlap, so their shares do not add up to 100%. Each total is the sum of its members&#39; trade, including what members sell to each other; the last column shows how much that is.</p>'
                         f'<section class="gsec"><h2>Blocs and groups compared, {y}</h2>{tbl}<p class="fine">Membership as of {self.BLOC_DATE}. Each page states who is counted.</p></section>'
                         f'<section class="gsec"><h2>Regions</h2><p class="gk">Geographic grouping used by the World Bank. Every economy is in exactly one region.</p>{self.region_nav()}</section>'
                         + h['src_box']('Source', f'<p><b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each economy&#39;s own customs figures in US dollars. <a href="/about">About the data</a></p>', str(y)))

    def og_card(self, kind, c=None):
        """A 1200x630 share image as HTML (rendered to JPEG by scripts/world_og.py)."""
        h = self.h; e = h['esc']; y, tot = self.latest_year()
        if kind == 'country':
            iso = c['iso']; d = self.year_view(iso, self.years_of(iso)[-1]); yy = d['_y']
            big = f'<div class="of">{c["flag"]}</div><h1>{e(c["name"])}</h1><p class="os">Trade in {yy}</p>'
            stats = (f'<div class="og3"><div><b class="x">{self.usd(d["x"])}</b><span>Exports</span></div><div><b class="m">{self.usd(d["m"])}</b><span>Imports</span></div>'
                     + (f'<div><b>{e(self.name(d["xp"][0][0]))}</b><span>Largest market</span></div>' if d['xp'] else '') + '</div>')
        else:
            WX = sum(v[0] for v in tot.values()); top = sorted(tot, key=lambda k: -tot[k][0])[:2]
            big = f'<h1>Who sells what to whom</h1><p class="os">Exports and imports of {len(tot)} economies, {y}</p>'
            stats = ('<div class="og3">' + f'<div><b class="x">{self.usd(WX)}</b><span>Goods exported, {y}</span></div>'
                     + ''.join(f'<div><b>{h["CBYISO"][k]["flag"]} {self.usd(tot[k][0])}</b><span>{e(self.name(k))}</span></div>' for k in top) + '</div>')
        return (f'<div class="og"><div class="ob"><span>{h["MARK"]}</span><b>World Trade Data</b><i>world.customsnepal.com</i></div>{big}{stats}</div>')

    # ---------- trade under sanctions: economies whose trade is read from their partners' records
    # Programme names are as listed by the US Treasury (OFAC) on the retrieval date below; UN committee where one exists.
    SANC_DATE = '15 November 2026'
    SANC = {
        'RUS': dict(ofac=['Russian Harmful Foreign Activities Sanctions', 'Ukraine-/Russia-related Sanctions'], base=2021,
                    note='The European Union began restrictive measures in March 2014 and widened them from February 2022; by the retrieval date it had adopted 21 packages.',
                    links=[('Council of the EU: sanctions against Russia', 'https://www.consilium.europa.eu/en/policies/sanctions-against-russia/')],
                    more=[('Bruegel: Russian foreign trade tracker', 'https://www.bruegel.org/dataset/russian-foreign-trade-tracker', 'monthly, rebuilt from the customs data of 38 partner countries, with product detail'),
                          ('CREA: Russia Fossil Tracker', 'https://www.russiafossiltracker.com/', 'oil, gas and coal shipments by destination, from ship tracking and pipeline data')]),
        'IRN': dict(ofac=['Iran Sanctions']), 'VEN': dict(ofac=['Venezuela-Related Sanctions']), 'BLR': dict(ofac=['Belarus Sanctions']),
        'PRK': dict(ofac=['North Korea Sanctions'], un='1718 Sanctions Committee (DPRK)',
                    data_note='Partners sometimes record trade with the Republic of Korea under this economy&#39;s code by mistake, so small markets on this page may be recording errors.'), 'CUB': dict(ofac=['Cuba Sanctions']), 'MMR': dict(ofac=['Burma-Related Sanctions']),
    }
    EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
    SANC_SLUG = {'RUS': 'russia', 'IRN': 'iran', 'VEN': 'venezuela', 'BLR': 'belarus', 'PRK': 'north-korea', 'CUB': 'cuba', 'MMR': 'myanmar'}      # readable addresses
    OFAC_URL = 'https://ofac.treasury.gov/sanctions-programs-and-country-information'
    UN_URL = 'https://main.un.org/securitycouncil/en/sanctions/information'

    def sanc_list(self):
        return [c for c in self.SANC if c in self.h['CBYISO'] and c in self.SD]

    def sanc_href(self, iso):
        return f'/trade/sanctions/{self.SANC_SLUG[iso]}' if iso in self.SANC and iso in self.sanc_list() else None

    def _sd(self, iso):
        return self.SD[iso]

    def _sanc_years(self, iso):
        S = self._sd(iso); return list(range(min(int(y) for y in S['yx']), S['full'] + 1))

    def _sanc_tot(self, iso, side, y):
        return sum(self._sd(iso)['yx' if side == 'x' else 'ym'][str(y)].values())

    def _sanc_val(self, iso, side, p, y):
        d = self._sd(iso)['yx' if side == 'x' else 'ym'][str(y)]
        return sum(d.get(q, 0) for q in self.EU27) if p == 'EU27' else d.get(p, 0)

    def _sanc_cmp(self, iso):
        """The year the latest one is compared with: a stated base year, else the year recorded exports were highest."""
        ys = self._sanc_years(iso); base = self.SANC[iso].get('base')
        if base in ys:
            return base, True
        peak = max(ys[:-1], key=lambda y: self._sanc_tot(iso, 'x', y))
        return peak, False

    def sanc_title(self, iso=None):
        if not iso:
            return 'Trade Under Sanctions: Russia, Iran, Venezuela and Others, Year by Year'
        ys = self._sanc_years(iso)
        return f'{self.name(iso)} Trade Under Sanctions: Exports by Destination, {ys[0]}–{ys[-1]}'

    def sanc_desc(self, iso=None):
        if not iso:
            return ('Exports and imports of economies under sanctions programmes, read from what their trading partners record: where the goods went each year since 2010, '
                    'which markets grew and which shrank, what buyers still take by product, oil in barrels, and what such figures cannot show.')
        ys = self._sanc_years(iso); a = self._sanc_tot(iso, 'x', ys[0]); b = self._sanc_tot(iso, 'x', ys[-1])
        top = max(self._sd(iso)['yx'][str(ys[-1])].items(), key=lambda kv: kv[1])[0]
        return (f"Partners recorded {self.usd(a)} of imports from {self.name(iso)} in {ys[0]} and {self.usd(b)} in {ys[-1]}. Largest market in {ys[-1]}: {self.name(top)}. "
                'Markets and suppliers year by year, month by month, and the limits of the data.')

    def _sanc_caveat(self, nm):
        return ('<div class="outcome" style="margin-top:var(--s4)"><div><b>How to read these figures.</b> ' + nm + ' does not report complete trade figures, so every number here, for every year, is what its trading partners record: '
                'their imports from it and their exports to it, as collected by the IMF. That keeps the years comparable, and it leaves gaps. The first two mean the recorded totals understate the real trade.<ul class="abl" style="margin-top:8px">'
                '<li><b>Partners that do not report either.</b> Trade between two economies that both withhold data is missing, or is an IMF estimate.</li>'
                '<li><b>Goods declared under another origin.</b> Cargo that is relabelled or transshipped is recorded against the other country, not this one.</li>'
                '<li><b>Valuation.</b> Exports here are partners&#39; import records, which include freight and insurance, so they run a little above the figures on the country profile.</li></ul>'
                'This page reports the recorded figures only. It does not estimate unrecorded trade.</div></div>')

    def _sanc_cols(self, ys):
        first, last = ys[0], ys[-1]
        return sorted(set([first] + list(range(first + 3, last - 4, 3)) + list(range(last - 4, last + 1))))

    def _sanc_matrix(self, iso, side, ys):
        cols = self._sanc_cols(ys); first, last = ys[0], ys[-1]
        val = lambda p, y: self._sanc_val(iso, side, p, y); tot = {y: self._sanc_tot(iso, side, y) for y in ys}
        d_last = self._sd(iso)['yx' if side == 'x' else 'ym'][str(last)]; d_first = self._sd(iso)['yx' if side == 'x' else 'ym'][str(first)]
        order = sorted(d_last, key=lambda p: -d_last[p])[:10]
        for p in sorted(d_first, key=lambda p: -d_first[p])[:5]:
            if p not in order:
                order.append(p)
        rows = []
        has_eu = val('EU27', first) or val('EU27', last)
        if has_eu:
            rows.append(['<b>European Union (27)</b>'] + [self.usd(val('EU27', y)) if val('EU27', y) else '—' for y in cols] + [self.share(val('EU27', first), tot[first]), self.share(val('EU27', last), tot[last])])
        for p in order:
            rows.append([self.clink(p)] + [self.usd(val(p, y)) if val(p, y) else '—' for y in cols] + [self.share(val(p, first), tot[first]), self.share(val(p, last), tot[last])])
        rows.append(['<b>All partners</b>'] + [f'<b>{self.usd(tot[y])}</b>' for y in cols] + ['100%', '100%'])
        pairs = ([(('European Union (27)', None), val('EU27', first), val('EU27', last))] if has_eu else []) + [((self.name(p), p), val(p, first), val(p, last)) for p in order[:8]]
        return self.table(['Partner'] + [str(y) for y in cols] + [f'Share {first}', f'Share {last}'], rows), pairs, tot

    def _sanc_shift(self, pairs, tot, first, last, tone):
        """Paired bars: each partner's share of the flow in the first and the latest year, one scale."""
        e = self.h['esc']; out = []
        mx = max([100.0 * a / tot[first] for _, a, _ in pairs if tot[first]] + [100.0 * b / tot[last] for _, _, b in pairs if tot[last]] + [1])
        for (name, p), a, b in pairs:
            sa = 100.0 * a / tot[first] if tot[first] else 0; sb = 100.0 * b / tot[last] if tot[last] else 0
            lab = self.clink(p) if p else f'<b>{e(name)}</b>'
            out.append(f'<div class="shr"><span>{lab}</span><div><i class="p" style="width:{max(0.6, 100.0 * sa / mx):.1f}%"></i><i class="{tone}" style="width:{max(0.6, 100.0 * sb / mx):.1f}%"></i></div>'
                       f'<b>{sa:.1f}% → {sb:.1f}%</b></div>')
        return ('<div class="shs">' + ''.join(out) + f'<div class="dvk"><span><i style="background:var(--muted)"></i>{first}</span><span><i class="{"pos" if tone == "x" else "neg"}"></i>{last}</span></div></div>')

    def _sanc_months(self, iso, side):
        """Small multiples: one panel per market, monthly, all on one scale so heights compare."""
        e = self.h['esc']; S = self._sd(iso); M = S['mx' if side == 'x' else 'mm']; names = [k for k in M if k != 'TOTAL']
        months = sorted(M['TOTAL']); n = len(months)
        if n < 24 or not names:
            return ''
        mx = max(max(M[k].values() or [0]) for k in names) or 1
        W, H = 300.0, 110.0; cls = 'lx' if side == 'x' else 'lm'
        ticks = [(i, p[:4]) for i, p in enumerate(months) if p.endswith('-01') and int(p[:4]) % 5 == 0]
        panels = []
        for k in names:
            d = M[k]; pts = ' '.join(('M' if i == 0 else 'L') + f'{W * i / (n - 1):.1f},{H - (H - 6.0) * d.get(p, 0) / mx:.1f}' for i, p in enumerate(months))
            grid = ''.join(f'<line x1="{W * i / (n - 1):.1f}" y1="0" x2="{W * i / (n - 1):.1f}" y2="{H}" class="lg"/>' for i, _ in ticks)
            lasty = months[-1][:4]; ly = sum(v for p, v in d.items() if p[:4] == lasty); fy = sum(v for p, v in d.items() if p[:4] == months[0][:4])
            lab = '<b>European Union (27)</b>' if k == 'EU27' else self.clink(k)
            panels.append(f'<div class="smp"><div class="smh">{lab}<span>{self.usd(fy)} in {months[0][:4]} · {self.usd(ly)} in {lasty}</span></div>'
                          f'<svg viewBox="0 0 {W:.0f} {H:.0f}" preserveAspectRatio="none" role="img" aria-label="{e(self.name(k) if k != "EU27" else "European Union")}, monthly: {self.usd(fy)} in {months[0][:4]}, {self.usd(ly)} in {lasty}">'
                          f'{grid}<path d="{pts}" class="{cls}"/></svg><div class="smx">' + ''.join(f'<span style="left:{100.0 * i / (n - 1):.1f}%">{y}</span>' for i, y in ticks) + '</div></div>')
        return (f'<div class="sms">{"".join(panels)}</div><p class="fine">Monthly value recorded by each partner, {months[0][:4]} to {months[-1][:4]}. Every panel uses the same vertical scale, top of panel = {self.usd(mx)} a month.</p>')

    PROD_REP = [('EU', 'the European Union', 'The EU', 'Eurostat, EU trade by HS chapter (DS-045409), reporter EU-27; euros converted to US dollars at each month&#39;s average ECB reference rate'),
                ('UK', 'the United Kingdom', 'The UK', 'HM Revenue &amp; Customs, Overseas Trade Statistics; pounds converted at monthly average ECB reference rates'),
                ('BR', 'Brazil', 'Brazil', 'Ministry of Development, Industry, Trade and Services of Brazil, Comex Stat; US dollars, FOB')]

    def _sanc_products(self, iso, cmp_y):
        """What reporters with open product data buy from and sell to the economy, by product group: the comparison year, the latest
        year, and the current year so far. A reporter is shown when the trade reached $100 million in either year."""
        h = self.h; e = h['esc']; P = self._sd(iso).get('prod') or {}; nm = e(self.name(iso)); last = self._sd(iso)['full']; out = []; srcs = []
        for key, long_name, short, src in self.PROD_REP:
            E = P.get(key) or {}
            upto = E.get('upto', ''); cur = int(upto[:4]) if upto and int(upto[:4]) > last else None
            def block(side, verb):
                D = E.get(side) or {}
                a = D.get(str(cmp_y)) or {}; b = D.get(str(last)) or {}; c = (D.get(str(cur)) or {}) if cur else {}
                ta, tb, tc = sum(a.values()), sum(b.values()), sum(c.values())
                if max(ta, tb) < 100000:
                    return ''
                ga = {g: v for g, v, _ in self.groups(list(a.items()))}; gb = {g: v for g, v, _ in self.groups(list(b.items()))}; gc = {g: v for g, v, _ in self.groups(list(c.items()))}
                names = sorted(set(ga) | set(gb), key=lambda g: -max(ga.get(g, 0), gb.get(g, 0)))[:8]
                rows = [(f'<a href="/trade/product/{h["group_slug"](g)}">{e(g)}</a>', self.usd(ga[g]) if ga.get(g) else '—', self.usd(gb[g]) if gb.get(g) else '—', self._chg(gb.get(g, 0), ga.get(g, 0)))
                        + ((self.usd(gc[g]) if gc.get(g) else '—',) if cur else ()) for g in names]
                rows.append(('<b>All products</b>', f'<b>{self.usd(ta)}</b>', f'<b>{self.usd(tb)}</b>', self._chg(tb, ta)) + ((f'<b>{self.usd(tc)}</b>',) if cur else ()))
                heads = ['Product group', str(cmp_y), str(last), 'Change'] + ([f'{cur}, Jan–{self.MONTHS[int(upto[5:]) - 1]}'] if cur else [])
                return f'<h3>{verb}</h3>' + self.table(heads, rows)
            bx = block('x', f'What {long_name} bought from {nm}'); bm = block('m', f'What {long_name} sold to {nm}')
            if bx or bm:
                out.append(bx + bm); srcs.append(f'{short}: {src}.')
        if not out:
            return ''
        return (f'<section class="gsec"><h2>{nm}&#39;s trade by product, from the buyers&#39; own customs data</h2><p class="gk">Product detail from reporters that publish it openly, by product group, for {cmp_y}, {last} '
                f'and the current year so far. A reporter appears when its trade with {nm} reached $100 million in either year.</p>' + ''.join(out)
                + '<p class="fine">Sources: ' + ' '.join(srcs) + '</p></section>')

    def _sanc_oil(self, iso):
        """Crude oil in barrels a day, as the economy reported it to JODI, with the last month it reported."""
        O = self._sd(iso).get('oil'); nm = self.h['esc'](self.name(iso))
        if not O or not O.get('prod'):
            return ''
        have = sorted(set(O['prod']) | set(O.get('exp') or {})); years = [str(y) for y in range(int(have[0]), max(int(have[-1]), self._sd(iso)['full']) + 1)]      # empty years stay on the axis
        mx = max([v[0] for v in O['prod'].values()] + [v[0] for v in (O.get('exp') or {}).values()] + [1])
        kb = lambda v: (f'{v / 1000.0:.2f}M' if v >= 1000 else f'{v:,}K')
        cols = ''
        for y in years:
            a = (O['prod'].get(y) or [0])[0]; b = ((O.get('exp') or {}).get(y) or [0])[0]
            cols += (f'<div class="yc"><div class="ycb"><i class="x" style="height:{max(0.0, 100.0 * a / mx):.1f}%;background:var(--fg-2)" title="Production {y}: {kb(a)} barrels a day"></i>'
                     f'<i class="m" style="height:{max(0.0, 100.0 * b / mx):.1f}%;background:var(--gold, #B7791F)" title="Exports {y}: {kb(b) if b else "not reported"}"></i></div><span>{y}</span></div>')
        rows = [(y, kb(O['prod'][y][0]) if y in O['prod'] else 'not reported', kb(O['exp'][y][0]) if y in (O.get('exp') or {}) else 'not reported') for y in years[::-1]]
        mlab = lambda p: f'{self.MONTHS[int(p[5:]) - 1]} {p[:4]}' if p else 'never'
        return (f'<section class="gsec"><h2>{nm}&#39;s crude oil in barrels</h2><p class="gk">Dollar figures move with the oil price. These are volumes: crude oil produced and exported, in barrels a day, '
                f'as {nm} itself reported them to the Joint Organisations Data Initiative. The last month it reported production is {mlab(O.get("last_prod"))}, and exports {mlab(O.get("last_exp"))}.</p>'
                f'<div class="ycs many lots">{cols}</div><div class="dvk"><span><i style="background:var(--fg-2)"></i>Production</span><span><i style="background:var(--gold, #B7791F)"></i>Exports</span></div>'
                + '<details class="tml"><summary>The same figures as a table</summary>' + self.table(['Year', 'Production, barrels a day', 'Exports, barrels a day'], rows) + '</details>'
                f'<p class="fine">Top of the chart is {kb(mx)} barrels a day. Yearly average of the months reported; a year is shown only when at least nine months were reported, and an empty year means the economy did not report. '
                'Source: <a href="https://www.jodidata.org/oil/" target="_blank" rel="noopener">JODI-Oil World Database ↗</a>, primary products, crude oil.</p></section>')

    def sanc_country(self, iso):
        h = self.h; e = h['esc']; S = self.SANC[iso]; D = self._sd(iso); nm = e(self.name(iso)); ys = self._sanc_years(iso); first, last = ys[0], ys[-1]
        c = h['CBYISO'][iso]
        tx, px, totx = self._sanc_matrix(iso, 'x', ys); tm, pm, totm = self._sanc_matrix(iso, 'm', ys)
        topx = max(D['yx'][str(last)].items(), key=lambda kv: kv[1])
        cmp_y, stated = self._sanc_cmp(iso)
        ex, em = D['ye'][str(last)]
        lead = (f'<p class="ans">Partners recorded <b>{self.usd(totx[last])}</b> of goods bought from {nm} in {last} and <b>{self.usd(totm[last])}</b> sold to it. '
                f'In {first} the figures were {self.usd(totx[first])} and {self.usd(totm[first])}. '
                f'The largest recorded market in {last} was {self.clink(topx[0])}, with {self.share(topx[1], totx[last])} of the total.</p>'
                f'<p class="fine">Of the {last} figures, {100 - ex:.0f}% of the exports and {100 - em:.0f}% of the imports were reported directly by the partner; the IMF estimated the rest for partners that had not reported.</p>')
        val = lambda p, y: self._sanc_val(iso, 'x', p, y)
        allp = set(D['yx'][str(cmp_y)]) | set(D['yx'][str(last)])
        movers = sorted(allp, key=lambda p: val(p, last) - val(p, cmp_y))
        up = [(p, val(p, last) - val(p, cmp_y)) for p in movers[::-1][:6] if val(p, last) - val(p, cmp_y) > 0]
        down = [(p, val(p, last) - val(p, cmp_y)) for p in movers[:6] if val(p, last) - val(p, cmp_y) < 0]
        why = (f'{cmp_y} is the last full year before the measures of {cmp_y + 1}.' if stated else f'{cmp_y} is the year in which recorded exports were highest since {first}: {self.usd(totx[cmp_y])}.')
        eu_c, eu_l = val('EU27', cmp_y), val('EU27', last)
        move_sec = (f'<section class="gsec"><h2>{cmp_y} to {last}: which markets grew and which shrank</h2>'
                    f'<p class="gk">{why}' + (f' Recorded exports to the European Union were {self.usd(eu_c)} in {cmp_y} ({self.share(eu_c, totx[cmp_y])} of the total) and {self.usd(eu_l)} in {last} ({self.share(eu_l, totx[last])}).' if (eu_c or eu_l) else '')
                    + ' Change in recorded exports by market, the six largest each way, on one scale.</p>'
                    + self.balance_chart(up, down[::-1]).replace('Deficit: imports more than it exports', f'Fell between {cmp_y} and {last}').replace('>Surplus<', f'>Rose between {cmp_y} and {last}<') + '</section>') if (up or down) else ''
        hist = {str(y): [totx[y], totm[y]] for y in ys}
        prog = ''.join(f'<li><b>United States Treasury (OFAC):</b> {e(p)}</li>' for p in S['ofac'])
        if S.get('un'):
            prog += f'<li><b>United Nations Security Council:</b> {e(S["un"])}</li>'
        if S.get('note'):
            prog += f'<li>{S["note"]}</li>'
        links = [('US Treasury: sanctions programmes', self.OFAC_URL)] + ([('UN Security Council: sanctions committees', self.UN_URL)] if S.get('un') else []) + S.get('links', [])
        more = ''
        if S.get('more'):
            more = ('<h3>Other trackers</h3><p class="gk">Independent projects that follow this trade in more detail. Their data is theirs and is not reproduced here.</p><ul class="abl">'
                    + ''.join(f'<li><a href="{u}" target="_blank" rel="noopener">{e(t)} ↗</a>: {e(x)}.</li>' for t, u, x in S['more']) + '</ul>')
        sec_prog = (f'<section class="gsec"><h2>The sanctions programmes</h2><p class="gk">Programmes that name {nm}, as listed by the issuing authority on {self.SANC_DATE}. This is not a complete list of measures; '
                    'other governments have their own, and each programme has its own scope and exemptions.</p>'
                    f'<ul class="abl">{prog}</ul><p class="fine">' + ' · '.join(f'<a href="{u}" target="_blank" rel="noopener">{e(t)} ↗</a>' for t, u in links) + f'</p>{more}</section>')
        others = ''.join(f'<a href="{self.sanc_href(x)}">{self.flag(x)} {e(self.name(x))}</a>' for x in self.sanc_list() if x != iso)
        extra = f'<p class="fine">{S["data_note"]}</p>' if S.get('data_note') else ''
        return h['main'](h['back']('/trade/sanctions', 'Trade under sanctions') + f'<div class="ph"><h1 class="h2">{c["flag"]} {nm}: trade under sanctions, {first} to {last}</h1>'
                         f'<p>Where {nm}&#39;s goods went and came from each year, as its trading partners recorded it.</p></div>'
                         + lead + extra + self._sanc_caveat(nm)
                         + f'<section class="gsec"><h2>Recorded trade year by year</h2>' + self.year_cols(hist, 'Exports', 'Imports')
                         + '<details class="tml"><summary>The same figures as a table</summary>' + self.table(['Year', 'Exports', 'Imports'], [(str(y), self.usd(totx[y]), self.usd(totm[y])) for y in ys[::-1]]) + '</details></section>'
                         + f'<section class="gsec gx"><h2>Where {nm}&#39;s exports went</h2><p class="gk">Share of recorded exports in {first} and in {last}, for the largest markets of {last}.</p>'
                         + self._sanc_shift(px, totx, first, last, 'x')
                         + '<h3>Month by month, by market</h3>' + self._sanc_months(iso, 'x')
                         + '<h3>Recorded exports by market, selected years</h3>' + tx + '</section>'
                         + move_sec
                         + f'<section class="gsec gm2"><h2>Where {nm}&#39;s imports came from</h2><p class="gk">Share of recorded imports in {first} and in {last}, for the largest suppliers of {last}.</p>'
                         + self._sanc_shift(pm, totm, first, last, 'm')
                         + '<h3>Month by month, by supplier</h3>' + self._sanc_months(iso, 'm')
                         + '<h3>Recorded imports by supplier, selected years</h3>' + tm + '</section>'
                         + self._sanc_products(iso, cmp_y) + self._sanc_oil(iso) + sec_prog
                         + f'<section class="gsec"><h2>More on {nm}</h2><div class="two"><a class="nepalcard" href="/trade/{iso.lower()}"><span class="fl">{c["flag"]}</span><span><b>{nm}: full trade profile</b> {h["ic"]("right")}</span></a>'
                         f'<a class="nepalcard" href="/trade/sanctions"><span class="fl">🧭</span><span><b>Trade under sanctions: all economies</b> {h["ic"]("right")}</span></a></div>'
                         f'<h3>Other economies</h3><div class="pairgrid">{others}</div></section>'
                         + h['src_box']('Sources', f'<p>Trade: <b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.SD_DATE}: every reporting economy&#39;s own record of its trade with {nm}, '
                                        f'in current US dollars at each month&#39;s average exchange rate. Products: the buyers&#39; own customs offices, named in that section. Oil volumes: <b>JODI</b>. Sanctions programmes: as listed by each authority on {self.SANC_DATE}. <a href="/about">About the data</a></p>', f'{first}–{last}'))

    def sanc_hub(self):
        h = self.h; e = h['esc']; L = self.sanc_list(); rows = []
        for iso in sorted(L, key=lambda c: -self._sanc_tot(c, 'x', self._sanc_years(c)[-1])):
            ys = self._sanc_years(iso); cy, _ = self._sanc_cmp(iso); a = self._sanc_tot(iso, 'x', ys[0]); pk = self._sanc_tot(iso, 'x', cy); b = self._sanc_tot(iso, 'x', ys[-1])
            top = max(self._sd(iso)['yx'][str(ys[-1])].items(), key=lambda kv: kv[1])
            rows.append((f'<a href="{self.sanc_href(iso)}">{self.flag(iso)} {e(self.name(iso))}</a>', self.usd(a), f'{self.usd(pk)} <small>{cy}</small>', self.usd(b), self._chg(b, a),
                         self.clink(top[0]) + f' <small>{self.share(top[1], b, 0)}</small>'))
        y0 = self._sanc_years(L[0])[0]; y1 = self._sanc_years(L[0])[-1]
        cards = ''.join(f'<a class="nepalcard" href="{self.sanc_href(x)}"><span class="fl">{self.flag(x)}</span><span><b>{e(self.name(x))}</b> — markets and suppliers, {y0} to {y1} {h["ic"]("right")}</span></a>' for x in L)
        return h['main'](h['back']('/trade', 'World rankings') + '<div class="ph"><h1 class="h2">Trade under sanctions</h1>'
                         f'<p>{len(L)} economies that are named in sanctions programmes and do not report complete trade figures. Their trade is read here from what their partners record.</p></div>'
                         f'<p class="ans">When a country does not report its trade, that trade does not disappear from the record: every shipment is also an import or export in someone else&#39;s books. '
                         f'These pages follow each economy&#39;s recorded exports and imports by partner from {y0} to {y1}, year by year and month by month, and say plainly what that method misses.</p>'
                         + self._sanc_caveat('Each of these economies')
                         + f'<section class="gsec"><h2>Recorded exports, {y0} to {y1}</h2>' + self.table(['Economy', f'Exports {y0}', 'Comparison year', f'Exports {y1}', f'Change {y0} to {y1}', f'Largest market {y1}'], rows)
                         + '<p class="fine">Comparison year: the last full year before a stated set of measures where the page gives one, otherwise the year recorded exports were highest.</p></section>'
                         + f'<section class="gsec"><h2>Economy by economy</h2><div class="two">{cards}</div></section>'
                         + '<section class="gsec"><h2>Which economies are here</h2><p class="gk">An economy is included when it is named in a country sanctions programme of the United States Treasury on the retrieval date '
                         'and does not report complete trade figures to the IMF. It is a statement about the data, not a judgement on any programme. Many other governments and the United Nations run programmes of their own.</p>'
                         f'<p class="fine"><a href="{self.OFAC_URL}" target="_blank" rel="noopener">US Treasury: sanctions programmes ↗</a> · <a href="{self.UN_URL}" target="_blank" rel="noopener">UN Security Council: sanctions committees ↗</a></p></section>'
                         + h['src_box']('Sources', f'<p>Trade: <b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.SD_DATE}: partners&#39; own records. '
                                        f'Sanctions programmes: as listed by each authority on {self.SANC_DATE}. <a href="/about">About the data</a></p>', f'{y0}–{y1}'))

    # ---------- long history, comparison data, product headings, what changed
    def long_years(self, iso):
        """{year: (exports, imports)} from 2000 (where the IMF has complete years) to the latest complete year."""
        I = self.IM.get(iso) or {}; out = {}
        for y, v in (I.get('ax') or {}).items():
            if y in (I.get('am') or {}):
                out[int(y)] = (v, I['am'][y])
        for y in self.years_of(iso):
            out[y] = self._year_tot(iso, y)
        return dict(sorted(out.items()))

    def then_now(self, iso):
        """The largest markets and suppliers at intervals: 2000, 2010 and the latest year, side by side."""
        e = self.h['esc']; I = self.IM.get(iso) or {}; ph = I.get('ph') or {}; ys = self.years_of(iso); nm = e(self.name(iso))
        cols = [y for y in ('2000', '2010') if ph.get(y)]
        if not cols or not ys:
            return ''
        last = ys[-1]; lv = self.year_view(iso, last); ly = self.long_years(iso)
        def side(k, lst_last, tot_last):
            data = []
            for y in cols:
                tot = ly[int(y)][k]; top = sorted(((p, v[k]) for p, v in ph[y].items() if v[k] > 0), key=lambda r: -r[1])[:8]
                data.append([(p, 100.0 * v / tot if tot else 0) for p, v in top])
            data.append([(p, 100.0 * v / tot_last if tot_last else 0) for p, v in lst_last[:8]])
            rows = []
            for i in range(8):
                rows.append([str(i + 1)] + [(self.clink(d[i][0]) + f' <small>{d[i][1]:.1f}%</small>') if i < len(d) else '—' for d in data])
            return self.table(['#'] + cols + [str(last)], rows)
        return (f'<h3>{nm}&#39;s largest export markets, then and now</h3>' + side(0, lv['xp'], lv['x'])
                + f'<h3>{nm}&#39;s largest suppliers, then and now</h3>' + side(1, lv['mp'], lv['m'])
                + '<p class="fine">Share of that year&#39;s exports or imports. Over a span this long some economies changed how they report, so read the earlier years as an outline.</p>')

    def compare_data(self):
        """Compact data for the compare page: totals by year since 2000, the latest markets, suppliers and export groups."""
        known = self.h['CBYISO']; ly, tot = self.latest_year(); slug = self.h['SLUG']
        years = list(range(2000, ly + 1)); rx = {c: i + 1 for i, c in enumerate(sorted(tot, key=lambda c: -tot[c][0]))}
        any_cur = next((self.IM[c] for c in tot if self.IM[c].get('cur')), None); span = self._span(any_cur) if any_cur else ''
        out = {}
        for c in tot:
            L = self.long_years(c); I = self.IM[c]; v = self.year_view(c, ly)
            ytd = None
            if I.get('cur') and self._span(I) == span:
                a = sum(I['x'].get(f'{I["cur"]}-{k:02d}', 0) for k in range(1, I['upto'] + 1)); b = sum(I['x'].get(f'{I["cur"] - 1}-{k:02d}', 0) for k in range(1, I['upto'] + 1))
                ytd = [a, b]
            B = self.C.get(c) or {}; gs = self.groups(B.get('xc') or [])[:5] if B else []
            out[slug[c]] = dict(n=known[c]['name'], f=known[c]['flag'], i=c.lower(), r=rx[c], x=[L[y][0] if y in L else None for y in years], m=[L[y][1] if y in L else None for y in years], y=ytd,
                                tx=[[self.name(p), round(100.0 * val / v['x'], 1)] for p, val in v['xp'][:5]] if v['x'] else [],
                                tm=[[self.name(p), round(100.0 * val / v['m'], 1)] for p, val in v['mp'][:5]] if v['m'] else [],
                                g=[[g, round(100.0 * val / B['x'], 1)] for g, val, _ in gs] if (B and B.get('x')) else [])
        order = [slug[c] for c in sorted(tot, key=lambda c: known[c]['name'])]
        top = [slug[c] for c in sorted(tot, key=lambda c: -tot[c][0])[:3]]
        return dict(years=years, span=span, total=len(tot), py=self.Y, c=out, order=order, **{'def': top})

    def compare_href(self, iso):
        """Compare an economy with the two nearest in size in its region (or the two largest overall)."""
        known = self.h['CBYISO']; ly, tot = self.latest_year(); slug = self.h['SLUG']
        if iso not in tot:
            return None
        reg = (known[iso].get('region') or '').strip()
        peers = sorted((c for c in tot if c != iso and (known[c].get('region') or '').strip() == reg), key=lambda c: abs(tot[c][0] - tot[iso][0]))[:2]
        if len(peers) < 2:
            peers = [c for c in sorted(tot, key=lambda c: -tot[c][0]) if c != iso][:2]
        return '/compare?c=' + ','.join(slug[c] for c in [iso] + peers), [self.name(c) for c in peers]

    def compare_page(self):
        h = self.h; ly, tot = self.latest_year()
        return h['main'](h['back']('/trade', 'World rankings') + '<div class="ph"><h1 class="h2">Compare countries</h1>'
                         f'<p>Put two or three economies side by side: exports and imports since 2000, their largest markets and suppliers in {ly}, and what they export. Pick any of {len(tot)} economies.</p></div>'
                         '<div id="cmp"><p class="fine">Loading the comparison…</p></div>'
                         '<noscript><p class="fine">This tool needs JavaScript. Every figure is also on each economy&#39;s own page: see the <a href="/trade">rankings</a>.</p></noscript>'
                         + h['src_box']('Sources', f'<p>Totals, markets and suppliers: <b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: customs figures in US dollars. '
                                        f'Export groups for {self.Y}: <b>BACI</b> (CEPII). Over 25 years some economies changed how they report, so long comparisons are an outline. <a href="/about">About the data</a></p>', f'2000–{ly}'))

    def heading_ok(self, h4):
        d = self.HD.get(h4); return bool(d and d['w'].get(str(self.Y), 0) >= 100000 and d['x'])

    def heading_name(self, h4, n=60):
        s = self.h['HEADINGS'].get(h4, h4); s = s.split(';')[0].split(' (')[0].strip()
        if ',' in s and len(s.split(',')[0]) >= 4:
            s = s.split(',')[0].strip()
        return self.h['clip'](s, n)

    def heading_title(self, h4):
        if getattr(self, '_htitles', None) is None:      # shortened names can collide (several 'Woven fabrics of synthetic…'); those get a shorter name and always the code
            mk = lambda x: (lambda b: b + f' (HS {x})' if len(b) + 10 <= 65 else b)(f'{self.heading_name(x, 30)}: Top Exporters & Importers {self.Y}')
            first = {x: mk(x) for x in self.HD if self.heading_ok(x)}; seen = {}
            for x, v in first.items():
                seen[v] = seen.get(v, 0) + 1
            self._htitles = {x: (v if seen[v] == 1 else f'{self.heading_name(x, 22)}: Top Exporters & Importers {self.Y} (HS {x})') for x, v in first.items()}
        return self._htitles[h4]

    def heading_desc(self, h4):
        d = self.HD[h4]; w = d['w'][str(self.Y)]
        return (f'World trade in {self.heading_name(h4).lower()} was {self.usd(w)} in {self.Y}. Largest exporter: {self.name(d["x"][0][0])} ({self.share(d["x"][0][1], w, 0)}). '
                + (f'Largest importer: {self.name(d["m"][0][0])} ({self.share(d["m"][0][1], w, 0)}). ' if d['m'] else '') + 'Top 15 of each, the map, and the products inside the heading.')

    def heading(self, h4):
        h = self.h; e = h['esc']; d = self.HD[h4]; Y = self.Y; w = d['w'][str(Y)]; full = e(h['HEADINGS'].get(h4, h4)); nm = e(self.heading_name(h4)); ch = h4[:2]
        lead = (f'<p class="ans">World trade in this heading was <b>{self.usd(w)}</b> in {Y}, exported by {d["nx"]} economies and imported by {d["nm"]}. '
                f'The largest exporter was {self.clink(d["x"][0][0])} with {self.share(d["x"][0][1], w)} of the total'
                + (f', and the largest importer was {self.clink(d["m"][0][0])} with {self.share(d["m"][0][1], w)}.' if d['m'] else '.') + '</p>')
        rows = lambda lst: [(self.clink(c), v, f'{self.usd(v)} <small>{self.share(v, w)}</small>') for c, v in lst[:15]]
        ws = sorted(d['w'].items()); mxw = max(v for _, v in ws) or 1; prevv = None; wrows = ''
        for y, v in ws:
            wrows += (f'<div class="barrow"><span class="lb">{y}</span><span class="tr"><span class="fi" style="width:{max(2.0, 100.0 * v / mxw):.1f}%;background:var(--exp)"></span></span>'
                      f'<span class="vl">{self.usd(v)}' + (f' <small>{self._chg(v, prevv)}</small>' if prevv else '') + '</span></div>'); prevv = v
        kids = [(k, v) for k, v in d['k'] if h['has_code'](k)]
        ktab = self.table(['Product', 'World trade', 'Share of the heading'], [(self.prod(k), self.usd(v), self.share(v, w)) for k, v in kids]) if kids else ''
        return h['main'](h['back'](f'/hs/chapter/{ch}', f'Chapter {ch}') + f'<div class="ph"><h1 class="h2">{nm}: largest exporters and importers, {Y}</h1><p>HS heading {h4[:2]}.{h4[2:]}: {full}</p>' + (f'<p class="fine"><a href="{self.opp_href(h4)}">Where imports of {nm.lower()} grew, {self.OP["y0"]} to {self.OP["y1"]}</a></p>' if self.opp_ok(h4) else '') + '</div>'
                         + lead
                         + '<section class="gsec"><h2>On the map</h2>' + self.map_tabs('h' + h4, [('Exporters', self._map(None, d['x'], w, 'world exports')), ('Importers', self._map(None, d['m'], w, 'world imports'))], '',
                                                                                    'Shade shows each economy&#39;s share of world exports or imports of this heading. Hover or tap for the figure.') + '</section>'
                         + f'<section class="gsec gx"><h2>The {min(15, len(d["x"]))} largest exporters of {nm.lower()}</h2>' + self.barlist(rows(d['x']), 'var(--exp)') + '</section>'
                         + (f'<section class="gsec gm2"><h2>The {min(15, len(d["m"]))} largest importers of {nm.lower()}</h2>' + self.barlist(rows(d['m']), 'var(--imp)') + '</section>' if d['m'] else '')
                         + f'<section class="gsec"><h2>World trade in this heading, {ws[0][0]} to {ws[-1][0]}</h2><div class="bars dp">{wrows}</div></section>'
                         + (f'<section class="gsec"><h2>Products inside heading {h4[:2]}.{h4[2:]}</h2>{ktab}<p class="fine">Each product page lists its own exporters and importers.</p></section>' if ktab else '')
                         + h['src_box']('Source', f'<p><b>BACI</b> (CEPII), reconciled from what exporters and importers reported to UN Comtrade, HS 2022, current US dollars. Shares are of world trade in the heading. '
                                        f'{Y} is the newest year with product detail for every economy. <a href="/about">About the data</a></p>', str(Y)))

    # ------------------------------------------------------------ where import demand moved (BACI, oldest vs newest year)
    def _dchg(self, a, b):
        return ('+' if a >= b else '−') + self.usd(abs(a - b))

    def opp_ok(self, h4):
        return h4 in self.OP.get('headings', {}) and self.heading_ok(h4) and bool(self.OP['headings'][h4]['g'])

    def opp_href(self, h4):
        return f'/opportunities/product/{h4}'

    def copp_ok(self, iso):
        return iso in self.OP.get('c', {}) and iso in self.h['CBYISO'] and iso in self.h['SLUG'] and any(self.opp_ok(r[0]) for r in self.OP['c'][iso])

    def copp_href(self, iso):
        return '/opportunities/' + self.h['SLUG'][iso]

    def opp_title(self, h4):
        if getattr(self, '_otitles', None) is None:      # shortened names can collide; those always carry the code
            mk = lambda x: f'{self.heading_name(x, 30)}: Growing Import Markets {self.OP["y0"]}–{self.OP["y1"]}'
            first = {x: mk(x) for x in self.OP['headings'] if self.opp_ok(x)}; seen = {}
            for v in first.values():
                seen[v] = seen.get(v, 0) + 1
            self._otitles = {x: (v if seen[v] == 1 else f'{self.heading_name(x, 20)}: Growing Import Markets {self.OP["y0"]}–{self.OP["y1"]} (HS {x})') for x, v in first.items()}
        return self._otitles[h4]

    def opp_desc(self, h4):
        d = self.OP['headings'][h4]; g = d['g'][0]
        return (f'Which countries bought more {self.heading_name(h4).lower()} between {self.OP["y0"]} and {self.OP["y1"]}: imports into {self.name(g[0])} rose by {self.usd(g[2] - g[1])}. '
                'The markets that grew most, who supplies them, and the exporters that gained.')

    _OPP_NOTE = ('<section class="gsec"><h2>How to read this page</h2><p>These are recorded trade values, not forecasts. A rise in imports shows that a market bought more in dollar terms; it can reflect higher prices as well as larger volumes, '
                 'and it says nothing about tariffs, standards, licences or demand next year. Check the importing country&#39;s rules and current prices before acting on any figure here.</p></section>')

    def _opp_src(self):
        return self.h['src_box']('Source', f'<p><b>BACI</b> (CEPII), reconciled from what exporters and importers reported to UN Comtrade, HS 2022, current US dollars. '
                                 f'Changes compare {self.OP["y0"]} with {self.OP["y1"]}, the oldest and newest years in the current release. Markets below {self.usd(self.OP["floor"])} of imports are left out. '
                                 f'<a href="/about">About the data</a></p>', str(self.OP['y1']))

    def opp(self, h4):
        h = self.h; d = self.OP['headings'][h4]; y0, y1 = self.OP['y0'], self.OP['y1']; nm = h['esc'](self.heading_name(h4)); low = nm.lower()
        known = h['CBYISO']; ok = lambda c: c in known
        g = [r for r in d['g'] if ok(r[0])]; f = [r for r in d['f'] if ok(r[0])]; dn = [r for r in d['d'] if ok(r[0])]; xg = [r for r in d['xg'] if ok(r[0])]
        sup = lambda r: ', '.join(f'{self.flag(c)} {h["esc"](self.name(c))} {self.share(v, r[2], 0)}' for c, v in r[3])
        lead = (f'<p class="ans">World trade in {low} went from <b>{self.usd(d["w"][0])}</b> in {y0} to <b>{self.usd(d["w"][1])}</b> in {y1} ({self._chg(d["w"][1], d["w"][0])}). '
                f'Imports rose most in {self.clink(g[0][0])}, by {self.usd(g[0][2] - g[0][1])}'
                + (f', followed by {self.clink(g[1][0])} and {self.clink(g[2][0])}.' if len(g) > 2 else '.') + '</p>')
        row3 = lambda r: (self.clink(r[0]), self.usd(r[1]) if r[1] else '—', self.usd(r[2]), self._dchg(r[2], r[1]), self._chg(r[2], r[1]))
        return h['main'](h['back']('/opportunities', 'Market opportunities') + f'<div class="ph"><h1 class="h2">{nm}: where imports grew, {y0} to {y1}</h1>'
                         f'<p>HS heading {h4[:2]}.{h4[2:]}. Which markets bought more, who supplies them now, and which exporters gained. <a href="/hs/heading/{h4}">Largest exporters and importers of {low}</a></p></div>'
                         + lead
                         + f'<section class="gsec"><h2>Markets where imports of {low} rose most</h2><p class="gk">Ranked by the rise in dollars, {y0} to {y1}. The last column shows the three largest suppliers of each market in {y1} and their share of it.</p>'
                         + self.table(['Importing market', str(y0), str(y1), 'Change', '%', f'Largest suppliers, {y1}'], [row3(r) + (sup(r),) for r in g], 'opp') + '</section>'
                         + (f'<section class="gsec"><h2>Fastest-growing markets in per cent</h2><p class="gk">Markets that already imported at least {self.usd(self.OP["floor"])} in {y0}.</p>'
                            + self.table(['Importing market', str(y0), str(y1), 'Change', '%'], [row3(r) for r in f]) + '</section>' if f else '')
                         + (f'<section class="gsec"><h2>Markets where imports fell most</h2>' + self.table(['Importing market', str(y0), str(y1), 'Change', '%'], [row3(r) for r in dn]) + '</section>' if dn else '')
                         + (f'<section class="gsec"><h2>Exporters of {low} that gained most</h2><p class="gk">Ranked by the rise in export value, {y0} to {y1}.</p>'
                            + self.table(['Exporter', str(y0), str(y1), 'Change', '%'], [row3(r) for r in xg]) + '</section>' if xg else '')
                         + self._OPP_NOTE + self._opp_src())

    def copp_title(self, iso):
        return f'{self.name(iso)}: Export Markets With Rising Demand {self.OP["y0"]}–{self.OP["y1"]}'

    def copp_desc(self, iso):
        rs = [r for r in self.OP['c'][iso] if self.opp_ok(r[0])]
        return (f'For {self.name(iso)}&#39;s largest export products, the markets whose imports rose between {self.OP["y0"]} and {self.OP["y1"]} and where its share is below its share of world exports. '
                f'{len(rs)} products, led by {self.heading_name(rs[0][0]).lower()}.').replace('&#39;', "'")

    def copp(self, iso):
        h = self.h; e = h['esc']; y0, y1 = self.OP['y0'], self.OP['y1']; nm = e(self.name(iso)); known = h['CBYISO']
        rs = [r for r in self.OP['c'][iso] if self.opp_ok(r[0])]
        secs = ''
        for h4, v, ws, mk in rs:
            hn = e(self.heading_name(h4)); mk = [m for m in mk if m[0] in known]
            if not mk:
                continue
            rows = [(self.clink(m[0]), self.usd(m[1]) if m[1] else '—', self.usd(m[2]), self._dchg(m[2], m[1]), self.usd(m[3]) if m[3] else '—', self.share(m[3], m[2])) for m in mk]
            secs += (f'<section class="gsec"><h2>{hn}</h2><p class="gk">{nm} exported {self.usd(v)} of {hn.lower()} in {y1}, {ws:.1f}% of world exports. '
                     f'In each market below its share is smaller than that. <a href="{self.opp_href(h4)}">All growing markets for {hn.lower()}</a></p>'
                     + self.table(['Importing market', f'Imports {y0}', f'Imports {y1}', 'Change', f'From {nm}, {y1}', f'{nm}&#39;s share'], rows, 'opp') + '</section>')
        return h['main'](h['back']('/opportunities', 'Market opportunities') + f'<div class="ph"><h1 class="h2">{self.flag(iso)} {nm}: export markets with rising demand, {y0} to {y1}</h1>'
                         f'<p>For the products {nm} already exports at scale, the markets that bought more from the world and where {nm} holds a smaller share than it does worldwide. <a href="/trade/{iso.lower()}">{nm} trade profile</a></p></div>'
                         + f'<p class="ans">{len(rs)} of the 200 most-traded product headings are ones where {nm} supplies at least 1% of world exports. For each, the table lists up to four markets whose imports rose by at least $20M.</p>'
                         + secs + (f'<section class="gsec"><h2>Finding suppliers in {nm}</h2>{self.tpo_line(iso)}</section>' if self.tpo(iso) else '') + self._OPP_NOTE + self._opp_src())

    def opp_hub(self):
        h = self.h; e = h['esc']; y0, y1 = self.OP['y0'], self.OP['y1']
        hs = sorted([x for x in self.OP['headings'] if self.opp_ok(x)], key=lambda x: -self.OP['headings'][x]['w'][1])
        cs = sorted([c for c in self.OP['c'] if self.copp_ok(c)], key=lambda c: self.name(c))
        bych = {}
        for x in sorted(hs):
            bych.setdefault(x[:2], []).append(x)
        prod = ''.join(f'<h3>Chapter {ch}: {e(h["clip"](h["CHNAME"](ch), 70))}</h3><div class="pairgrid">' + ''.join(f'<a href="{self.opp_href(x)}">{e(self.heading_name(x, 40))}</a>' for x in xs) + '</div>' for ch, xs in bych.items())
        big = self.table(['Product', f'World trade {y1}', f'Change on {y0}', 'Market that grew most'],
                         [(f'<a href="{self.opp_href(x)}">{e(self.heading_name(x, 48))}</a>', self.usd(self.OP['headings'][x]['w'][1]), self._chg(self.OP['headings'][x]['w'][1], self.OP['headings'][x]['w'][0]),
                           next((self.clink(r[0]) + f' <small>{self._dchg(r[2], r[1])}</small>' for r in self.OP['headings'][x]['g'] if r[0] in h['CBYISO']), '—')) for x in hs[:25]])
        return h['main'](h['back']('/trade', 'World rankings') + f'<div class="ph"><h1 class="h2">Market opportunities: where import demand grew, {y0} to {y1}</h1>'
                         f'<p>For the {len(hs)} most-traded product headings: which countries bought more, who supplies them, and which exporters gained. For {len(cs)} exporting economies: the growing markets where their share is still small.</p></div>'
                         f'<section class="gsec"><h2>The 25 largest products</h2>{big}</section>'
                         f'<section class="gsec"><h2>By exporting country</h2><p class="gk">Pick an economy to see, for its main export products, the markets with rising imports where it is under-represented.</p><div class="pairgrid">'
                         + ''.join(f'<a href="{self.copp_href(c)}">{self.flag(c)} {e(self.name(c))}</a>' for c in cs) + '</div></section>'
                         f'<section class="gsec"><h2>All {len(hs)} products, by HS chapter</h2>{prod}</section>'
                         + (f'<section class="gsec"><h2>Open tenders</h2><p>Invitations to bid from World Bank-financed projects, loaded live and searchable by country. <a href="/tenders">See open tenders</a></p></section>')
                         + (f'<section class="gsec"><h2>Finding suppliers: official trade bodies</h2><p class="gk">Government or government-backed export promotion bodies. Most keep a directory of exporters or will point you to one. '
                            f'Links open their own sites; checked on {e(self.TPO.get("checked", ""))}.</p>{self.tpo_grid()}</section>' if self.TPO.get('bodies') else '')
                         + self._OPP_NOTE + self._opp_src())

    # ---------- finding suppliers: official trade bodies (data/world/tpo.json), and the tenders page
    def tpo(self, iso):
        return (self.TPO.get('bodies') or {}).get(iso)

    def tpo_line(self, iso):
        t = self.tpo(iso); e = self.h['esc']
        return (f'<p class="fine">Looking for exporters in {e(self.name(iso))}? Start with its official trade promotion body: '
                f'<a href="{e(t[1])}" target="_blank" rel="noopener">{e(t[0])}</a>.</p>') if t else ''

    def tpo_grid(self):
        e = self.h['esc']; b = self.TPO.get('bodies') or {}
        return '<div class="pairgrid">' + ''.join(f'<a href="{e(b[c][1])}" target="_blank" rel="noopener">{self.flag(c)} {e(self.name(c))}: {e(b[c][0])}</a>' for c in sorted(b, key=self.name) if c in self.h['CBYISO']) + '</div>'

    def tenders_page(self):
        h = self.h
        return h['main'](h['back']('/opportunities', 'Market opportunities') + '<div class="ph"><h1 class="h2">Open tenders: World Bank-financed projects</h1>'
                         '<p>Invitations to bid and requests for expressions of interest from projects the World Bank finances, newest first. Filter by country, category or words in the notice.</p></div>'
                         '<div id="tnd"><p class="tmsg">Loading notices…</p></div>'
                         '<noscript><p class="fine">This list needs JavaScript. The same notices are on the <a href="https://projects.worldbank.org/en/projects-operations/procurement">World Bank procurement page</a>.</p></noscript>'
                         '<section class="gsec"><h2>How to read this page</h2><p>Notices are loaded live from the World Bank each time you search, so the list is as current as its own. Each title opens the full notice on the World Bank site, '
                         'which has the documents, the contact and the rules for bidding. World Trade Data does not run these tenders and cannot answer questions about them. Always confirm the deadline on the notice itself.</p></section>'
                         + h['src_box']('Source', '<p><b>World Bank</b>, Procurement Notices, licensed under Creative Commons Attribution 4.0. Covers projects financed by the World Bank only; other lenders and national tenders are not included.</p>', 'Live'))

    def changes_title(self):
        I = next((self.IM[c] for c in self.IM if self.IM[c].get('cur')), None)
        return f'World Trade in {self._span(I)}: What Changed' if I else 'World Trade: What Changed'

    def changes(self):
        """The current year so far against the same months a year earlier: who moved most, by economy and by flow."""
        h = self.h; e = h['esc']; known = h['CBYISO']
        any_cur = next((self.IM[c] for c in self.IM if self.IM[c].get('cur')), None)
        if not any_cur:
            return None
        span = self._span(any_cur); cur = any_cur['cur']; upto = any_cur['upto']
        E = {}
        for c, I in self.IM.items():
            if c not in known or not I.get('cur') or self._span(I) != span:
                continue
            a = [sum(I[k].get(f'{y}-{mo:02d}', 0) for mo in range(1, upto + 1)) for k in ('x', 'm') for y in (cur, cur - 1)]
            if all(a):
                E[c] = a          # exports now, exports then, imports now, imports then
        WX = sum(v[0] for v in E.values()); WXp = sum(v[1] for v in E.values()); WM = sum(v[2] for v in E.values()); WMp = sum(v[3] for v in E.values())
        dx = sorted(E, key=lambda c: E[c][0] - E[c][1])
        up = [(c, E[c][0] - E[c][1]) for c in dx[::-1][:8] if E[c][0] > E[c][1]]; down = [(c, E[c][0] - E[c][1]) for c in dx[:8] if E[c][0] < E[c][1]]
        big = sorted(E, key=lambda c: -E[c][0])[:60]
        pct = sorted(big, key=lambda c: (E[c][0] - E[c][1]) / E[c][1])
        prow = lambda c: (self.clink(c), self.usd(E[c][1]), self.usd(E[c][0]), self._chg(E[c][0], E[c][1]))
        flows = []
        for c in E:
            for p, v in self.IM[c]['p'].items():
                if v[2] and v[3] and not v[8] and p in known:
                    flows.append((c, p, v[2], v[3]))
        fs = sorted(flows, key=lambda f: f[2] - f[3])
        frow = lambda f: (f'{self.flag(f[0])} {e(self.name(f[0]))} → {self.flag(f[1])} {e(self.name(f[1]))}' + (f' <a class="pl" href="{self.pair_href(f[0], f[1])}">pair</a>' if self.pair_href(f[0], f[1]) else ''),
                          self.usd(f[3]), self.usd(f[2]), ('+' if f[2] >= f[3] else '−') + self.usd(abs(f[2] - f[3]))[1:], self._chg(f[2], f[3]))
        chart = self.balance_chart(up, down[::-1]).replace('Deficit: imports more than it exports', f'Exports fell on {span.rsplit(" ", 1)[0]} {cur - 1}').replace('>Surplus<', '>Exports rose<')
        return h['main'](h['back']('/trade', 'World rankings') + f'<div class="ph"><h1 class="h2">World trade in {span}: what changed</h1>'
                         f'<p>The current year so far against the same months of {cur - 1}, for {len(E)} economies with figures to {self.MONTHS[upto - 1]} {cur}. Updated each month.</p></div>'
                         f'<p class="ans">These {len(E)} economies exported <b>{self.usd(WX)}</b> of goods in {span}, {self._chg(WX, WXp)} on the same months of {cur - 1}, and imported <b>{self.usd(WM)}</b>, {self._chg(WM, WMp)}.</p>'
                         f'<section class="gsec"><h2>Exports: the largest rises and falls in dollars</h2><p class="gk">Change in exports, {span} against the same months of {cur - 1}. The eight largest each way, on one scale.</p>{chart}</section>'
                         f'<section class="gsec"><h2>Fastest-growing exporters among the 60 largest</h2>' + self.table(['Economy', f'Same months {cur - 1}', span, 'Change'], [prow(c) for c in pct[::-1][:12]]) + '</section>'
                         f'<section class="gsec"><h2>Largest declines among the 60 largest</h2>' + self.table(['Economy', f'Same months {cur - 1}', span, 'Change'], [prow(c) for c in pct[:12] if E[c][0] < E[c][1]]) + '</section>'
                         f'<section class="gsec"><h2>Trade flows that grew most</h2><p class="gk">One country&#39;s exports to another, as the exporter reports them. Flows the IMF had to estimate are left out.</p>'
                         + self.table(['Flow', f'Same months {cur - 1}', span, 'Change', '%'], [frow(f) for f in fs[::-1][:15]]) + '</section>'
                         f'<section class="gsec"><h2>Trade flows that shrank most</h2>' + self.table(['Flow', f'Same months {cur - 1}', span, 'Change', '%'], [frow(f) for f in fs[:15]]) + '</section>'
                         + h['src_box']('Source', f'<p><b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each economy&#39;s own customs figures in current US dollars. '
                                        f'Changes are in dollar value, so they include price movements as well as volumes. <a href="/about">About the data</a></p>', span))

    def product_history(self, code):
        """World trade in one product for each BACI year on file."""
        ys = {int(y): d.get(code) for y, d in (self.YW or {}).items() if d.get(code)}
        if code in self.PW:
            ys[self.Y] = self.PW[code]['w']
        if len(ys) < 2:
            return ''
        mx = max(ys.values()); last = None; rows = []
        for y in sorted(ys):
            rows.append(f'<div class="barrow"><span class="lb">{y}</span><span class="tr"><span class="fi" style="width:{max(2.0, 100.0 * ys[y] / mx):.1f}%;background:var(--exp)"></span></span>'
                        f'<span class="vl">{self.usd(ys[y])}' + (f' <small>{self._chg(ys[y], last)}</small>' if last else '') + '</span></div>'); last = ys[y]
        return (f'<section class="gsec"><h2>World trade in this product, {min(ys)} to {max(ys)}</h2><div class="bars dp">{"".join(rows)}</div>'
                f'<p class="fine">World exports of this product in current US dollars, with the change on the year before. {max(ys)} is the newest year with product detail for every economy.</p></section>')

    # ---------- country
    def country_title(self, c):
        return f"{c['name']} Trade {self.Y}: Exports, Imports, Partners & Products"

    def country_desc(self, c):
        d = self.C[c['iso']]
        s = f"{c['name']} exported {self.usd(d['x'])} and imported {self.usd(d['m'])} of goods in {self.Y}."
        if d['xp']:
            s += f" Largest market: {self.name(d['xp'][0][0])} ({self.share(d['xp'][0][1], d['x'], 0)})."
        if d['mp']:
            s += f" Largest supplier: {self.name(d['mp'][0][0])} ({self.share(d['mp'][0][1], d['m'], 0)})."
        return s + f" All {len(set(p for p, _ in d['xp']) | set(p for p, _ in d['mp']))} partners and top products."

    def country(self, c):
        h = self.h; e = h['esc']; iso = c['iso']; d = self.C[iso]; Y = self.Y
        X, M = d['x'], d['m']; bal = X - M
        nm = e(c['name'])
        xp, mp = d['xp'], d['mp']
        lead = (f'<p class="ans">{nm} exported <b>{self.usd(X)}</b> of goods and imported <b>{self.usd(M)}</b> in {Y}, '
                f'a trade {"surplus" if bal >= 0 else "deficit"} of <b>{self.usd(abs(bal))}</b>.'
                + (f' Its largest export market was {self.clink(xp[0][0])} ({self.share(xp[0][1], X)} of exports)' if xp else '')
                + (f' and its largest supplier was {self.clink(mp[0][0])} ({self.share(mp[0][1], M)} of imports).' if mp else '.') + '</p>')
        rk = (f'{e(c["region"])} · ' if c.get('region') else '') + f'World rank <b>#{self.rank_x.get(iso, "–")}</b> exporter, <b>#{self.rank_m.get(iso, "–")}</b> importer of {len(self.rank_x)} economies ({Y}).'
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(X)}</b><span>Exports ({Y})</span></div>'
                 f'<div class="s"><b class="im">{self.usd(M)}</b><span>Imports ({Y})</span></div>'
                 f'<div class="s"><b style="color:{"var(--free)" if bal >= 0 else "var(--hi)"}">{"+" if bal >= 0 else "−"}{self.usd(abs(bal))[1:]}</b><span>Trade balance</span></div>'
                 f'<div class="s"><b>{len(xp)}</b><span>Export markets</span></div></div>')

        def partner_rows(lst, total, n=15):
            out = []
            for p, v in lst[:n]:
                ph = self.pair_href(iso, p)
                lab = self.clink(p) + (f' <a class="pl" href="{ph}">pair</a>' if ph else '')
                out.append((lab, v, f'{self.usd(v)} <small>{self.share(v, total)}</small>'))
            return out

        def conc(lst, total, what):
            if len(lst) < 3 or not total:
                return ''
            t3 = sum(v for _, v in lst[:3])
            return f'The top three {what} ({", ".join(e(self.name(p)) for p, _ in lst[:3])}) account for {self.share(t3, total, 0)}.'
        xg, mg = self.groups(d.get('xc') or []), self.groups(d.get('mc') or [])
        sec_x = (f'<section class="gsec gx"><h2>What {nm} sells, and to whom</h2><p class="gk">{nm} exported {self.usd(X)} of goods to {len(xp)} markets in {Y}. '
                 + (f'{e(xg[0][0])} is the largest product group at {self.share(xg[0][1], X, 0)} of exports. ' if xg else '') + conc(xp, X, 'markets') + '</p>'
                 + ('<h3>Exports by product group</h3>' + self.treemap(d.get('xc') or [], X, 'exp', c['name'], 'exports') if xg else '')
                 + f'<h3>Top {min(10, len(xp))} export markets</h3>' + self.barlist(partner_rows(xp, X, 10), 'var(--exp)') + '</section>')
        sec_m = (f'<section class="gsec gm2"><h2>What {nm} buys, and from whom</h2><p class="gk">{nm} imported {self.usd(M)} of goods from {len(mp)} suppliers in {Y}. '
                 + (f'{e(mg[0][0])} is the largest product group at {self.share(mg[0][1], M, 0)} of imports. ' if mg else '') + conc(mp, M, 'suppliers') + '</p>'
                 + ('<h3>Imports by product group</h3>' + self.treemap(d.get('mc') or [], M, 'imp', c['name'], 'imports') if mg else '')
                 + f'<h3>Top {min(10, len(mp))} suppliers</h3>' + self.barlist(partner_rows(mp, M, 10), 'var(--imp)') + '</section>')

        # surpluses and deficits by partner
        allp = {}
        for p, v in xp:
            allp.setdefault(p, [0, 0])[0] = v
        for p, v in mp:
            allp.setdefault(p, [0, 0])[1] = v
        bals = sorted(((p, a - b) for p, (a, b) in allp.items()), key=lambda kv: kv[1])
        sur = [x for x in bals[::-1] if x[1] > 0][:6]; dfc = [x for x in bals if x[1] < 0][:6]
        sec_bal = ''
        if sur or dfc:
            sec_bal = (f'<section class="gsec"><h2>Where {nm} runs a surplus, and where a deficit</h2>'
                       f'<p class="gk">Exports to each partner minus imports from it, {Y}. The six largest on each side, on one scale.</p>'
                       + self.balance_chart(sur, dfc[::-1]) + '</section>')

        # products
        def badge(r, s):
            return f' <span class="rk{r}">#{r} in world · {s}%</span>' if r else ''
        xrows = [(self.prod(k) + (f' <a class="pl" href="{self.pc_href(iso, k)}">buyers</a>' if self.pc_href(iso, k) else ''), self.usd(v), self.share(v, X), self.clink(tp) + f' <small>{self.share(tv, v, 0)}</small>', f'{ws}%' + (f' <span class="rk{r}">#{r}</span>' if r else ''))
                 for k, v, tp, tv, ws, r in d['xk'][:25]]
        mrows = [(self.prod(k), self.usd(v), self.share(v, M), self.clink(tp) + f' <small>{self.share(tv, v, 0)}</small>') for k, v, tp, tv in d['mk'][:25]]
        sec_xk = (f'<h2 class="h">What {nm} exports: top {len(xrows)} products</h2>'
                  + self.table(['Product', 'Exports', 'Share of exports', 'Main buyer', 'World share'], xrows)
                  + f'<p class="fine">{nm} exported {d["nx"]:,} different products in {Y}. World share is its part of all countries&#39; exports of that product.</p>') if xrows else ''
        sec_mk = (f'<h2 class="h">What {nm} imports: top {len(mrows)} products</h2>'
                  + self.table(['Product', 'Imports', 'Share of imports', 'Main supplier'], mrows)) if mrows else ''
        sec_lead = ''
        if d['lead']:
            sec_lead = (f'<h2 class="h">Where {nm} is a top-three world exporter</h2>'
                        + self.table(['Product', 'Exports', 'World rank', 'World share'],
                                     [(self.prod(k), self.usd(v), f'<span class="rk{r}">#{r}</span>', f'{s}%') for k, v, r, s in d['lead']]))
        sec_dep = ''
        if d['dep']:
            sec_dep = (f'<h2 class="h">Imports that come mostly from one country</h2>'
                       + self.table(['Product', 'Imports', 'Main supplier', 'Its share'],
                                    [(self.prod(k), self.usd(v), self.clink(p), f'{s}%') for k, v, p, s in d['dep']])
                       + '<p class="fine">Products worth at least 0.1% of imports where a single supplier provides three-quarters or more.</p>')

        # all partners
        prow = sorted(allp.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))
        allrows = [(self.clink(p), self.usd(a) if a else '—', self.usd(b) if b else '—', ('+' if a - b >= 0 else '−') + self.usd(abs(a - b))[1:]) for p, (a, b) in prow]
        sec_all = (f'<details class="dall"><summary>All {len(allrows)} trading partners of {nm}</summary>'
                   + self.table(['Partner', f'{nm} exports to', f'{nm} imports from', 'Balance'], allrows) + '</details>')

        hist = d.get('hist') or {}
        hrows = [(y, self.usd(v[0]), self.usd(v[1]), ('+' if v[0] - v[1] >= 0 else '−') + self.usd(abs(v[0] - v[1]))[1:]) for y, v in sorted(hist.items(), reverse=True)]
        sec_hist = '<h2 class="h">Recent years</h2>' + self.table(['Year', 'Exports', 'Imports', 'Balance'], hrows) if hrows else ''
        long_trend = (f'<div class="card" style="margin-top:var(--s4)"><b style="font-size:.9rem">Longer trend, World Bank series</b>{h["trend_svg"](c.get("trend") or [])}</div>'
                      if c.get('trend') else '')

        prs_all = self.pairs_of.get(iso, []); prs = prs_all[:30]
        sec_pairs = ''
        if prs:
            sec_pairs = (f'<h2 class="h">{nm} and its partners, pair by pair</h2><div class="pairgrid">'
                         + ''.join(f'<a href="{self.pair_href(iso, p)}">{self.flag(iso)} {nm} – {self.flag(p)} {e(self.name(p))}</a>' for p in prs) + '</div>'
                         + (f'<p class="fine">The 30 largest of {len(prs_all)} pair pages. <a href="/trade/pairs">All country pairs</a></p>' if len(prs_all) > 30 else ''))
        src = h['src_box']('Sources', f'<p>Partners, products and {Y} totals from <b>BACI</b> (CEPII), which reconciles what exporters and importers each reported to '
                           f'<b>UN Comtrade</b>, at the 6-digit HS level, in current US dollars. The longer trend chart is the <b>World Bank</b> merchandise trade series, '
                           f'which can differ slightly from BACI for the same year. '
                           f'<a href="https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37" target="_blank" rel="noopener">About BACI ↗</a></p>', str(Y))
        peers = self.peers(c)
        sec_time = ''
        if hrows or long_trend:
            sec_time = (f'<section class="gsec"><h2>{nm}&#39;s trade over time</h2>' + long_trend.replace(' style="margin-top:var(--s4)"', '')
                        + (self.table(['Year', 'Exports', 'Imports', 'Balance'], hrows) if hrows else '') + '</section>')
        prod_sec = (f'<section class="gsec"><h2>Products in detail</h2>' + sec_xk + sec_mk + sec_lead + sec_dep + '</section>') if (sec_xk or sec_mk) else ''
        return h['main'](h['back']('/trade', 'Global trade') + f'<div class="ph"><h1 class="h2">{c["flag"]} {nm}: trade in {Y}</h1><p>{rk}</p></div>'
                         + lead + tiles + self.highlights(iso, d)
                         + f'<p class="pdfl"><a href="{self.brief_href(iso)}" download>Download the {nm} trade brief (PDF)</a> <span>Key figures, partners, products and history on a few pages, free to share.</span></p>'
                         + (self.nepal_official() + '<p class="fine">More on Nepal: <a href="/nepal/exports">export explorer by market</a> and <a href="/nepal">world prices against what Nepal pays</a>.</p>' if iso == 'NPL' else '')
                         + self.latest(iso) + self.latest_products(iso) + self.flow(iso, d) + sec_x + sec_m + sec_bal + sec_time + prod_sec + sec_pairs
                         + f'<section class="gsec"><h2>{nm}&#39;s partners on the map</h2>' + self.map_block(iso, d) + sec_all + '</section>' + peers + src)

    def peers(self, c):
        known = self.h['CBYISO']
        if not c.get('region'):
            return ''
        ps = sorted((x for x in known.values() if x['iso'] != c['iso'] and x.get('region') == c.get('region') and x['iso'] in self.C),
                    key=lambda x: abs(self.C[x['iso']]['x'] - self.C[c['iso']]['x']))[:8]
        if not ps:
            return ''
        rh = self.region_href(c['region']) if self.IM else None
        return (f'<h2 class="h">Other economies in {self.h["esc"](c["region"].strip())}</h2>' + (f'<p class="fine" style="margin:0 0 10px"><a href="{rh}">{self.h["esc"](c["region"].strip())}: all economies ranked</a></p>' if rh else '') + '<div class="pairgrid">'
                + ''.join(f'<a href="/trade/{x["iso"].lower()}">{x["flag"]} {self.h["esc"](x["name"])} <small>{self.usd(self.C[x["iso"]]["x"])}</small></a>' for x in ps) + '</div>')

    # ---------- pairs
    def pair_keys(self):
        return self._pair_keys

    def pair_years(self, a, b):
        """{year: [a's reported exports to b, b's reported exports to a]} from the IMF series, for years both sides have. Empty when
        the latest complete year is missing on either side, and then the pair page stays on the BACI year."""
        ya, yb = self.years_of(a), self.years_of(b)
        if not ya or not yb or ya[-1] != yb[-1]:
            return {}
        out = {}
        for y in ya:
            if y in yb:
                v = [(self.IM[a]['pa'][str(y)].get(b) or [0])[0], (self.IM[b]['pa'][str(y)].get(a) or [0])[0]]
                if v[0] or v[1]:
                    out[y] = v
        return out if (ya[-1] in out and all(out[ya[-1]])) else {}

    def pair_title(self, a, b):
        return f'{self.name(a)}–{self.name(b)} Trade {self.year_label(a) if self.pair_years(a, b) else self.Y}: What Each Sells the Other'

    def pair_desc(self, a, b):
        p = self.P[a + '-' + b]; py = self.pair_years(a, b)
        if py:
            y = max(py)
            s = f'{self.name(a)} exported {self.usd(py[y][0])} to {self.name(b)} and imported {self.usd(py[y][1])} in {y}. Year by year since {min(py)}.'
        else:
            s = f'{self.name(a)} exported {self.usd(p["ab"])} to {self.name(b)} and imported {self.usd(p["ba"])} in {self.Y}.'
        if p['abk']:
            s += f' Top {self.name(a)} export: {self.h["clip"](self.h["hs_desc"](p["abk"][0][0]), 46)}.'
        if p['bak']:
            s += f' Top {self.name(b)} export: {self.h["clip"](self.h["hs_desc"](p["bak"][0][0]), 46)}.'
        return s

    def pair(self, a, b):
        h = self.h; e = h['esc']; p = self.P[a + '-' + b]; Y = self.Y
        A, B = e(self.name(a)), e(self.name(b)); fa, fb = self.flag(a), self.flag(b)
        ab, ba = p['ab'], p['ba']; tot = ab + ba; bal = ab - ba
        ca, cb = self.C[a], self.C[b]
        rank_in = lambda lst, x: next((i + 1 for i, (q, _) in enumerate(lst) if q == x), None)
        ra, rb = rank_in(ca['xp'], b), rank_in(cb['xp'], a)
        lead = (f'<p class="ans">{A} exported <b>{self.usd(ab)}</b> of goods to {B} in {Y}, and {B} exported <b>{self.usd(ba)}</b> to {A}. '
                f'Trade between the two totalled <b>{self.usd(tot)}</b>, with a {self.usd(abs(bal))} surplus for {A if bal >= 0 else B}.</p>')
        ctx = '<ul class="ctx">'
        if ra:
            ctx += f'<li>{B} is {A}&#39;s <b>#{ra}</b> export market, taking {self.share(ab, ca["x"])} of {A}&#39;s exports.</li>'
        if rb:
            ctx += f'<li>{A} is {B}&#39;s <b>#{rb}</b> export market, taking {self.share(ba, cb["x"])} of {B}&#39;s exports.</li>'
        ctx += f'<li>{A} supplies {self.share(ab, cb["m"])} of everything {B} imports; {B} supplies {self.share(ba, ca["m"])} of {A}&#39;s imports.</li></ul>'
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(ab)}</b><span>{A} → {B}</span></div>'
                 f'<div class="s"><b class="im">{self.usd(ba)}</b><span>{B} → {A}</span></div>'
                 f'<div class="s"><b>{self.usd(tot)}</b><span>Total trade ({Y})</span></div></div>')
        mx = max(ab, ba) or 1
        scale = (f'<div class="card pscale"><div class="pr"><span>{fa} {A} → {fb} {B}</span><div><i style="width:{max(1.5, 100.0 * ab / mx):.1f}%;background:var(--exp)"></i></div><b>{self.usd(ab)}</b></div>'
                 f'<div class="pr"><span>{fb} {B} → {fa} {A}</span><div><i style="width:{max(1.5, 100.0 * ba / mx):.1f}%;background:var(--imp)"></i></div><b>{self.usd(ba)}</b></div>'
                 f'<p class="fine" style="margin:6px 0 0">Both bars on the same scale.</p></div>')

        def prods(lst, total, n, who, to):
            if not lst:
                return f'<p class="fine">No recorded exports from {who} to {to} in {Y}.</p>'
            rows = [(self.prod(k), self.usd(v), self.share(v, total)) for k, v in lst]
            top3 = sum(v for _, v in lst[:3])
            return (self.table(['Product', 'Value', 'Share'], rows)
                    + f'<p class="fine">{who} sold {n:,} different products to {to}. The top three make up {self.share(top3, total, 0)} of the total.</p>')
        tm_ab = self.treemap(p.get('abc') or [], ab, 'exp', self.name(a), f'exports to {self.name(b)}') if ab else ''
        tm_ba = self.treemap(p.get('bac') or [], ba, 'imp', self.name(b), f'exports to {self.name(a)}') if ba else ''
        sec_ab = (f'<section class="gsec"><h2>What {A} sells to {B}</h2>' + ('<h3>By product group</h3>' + tm_ab if tm_ab else '')
                  + '<h3>Top products</h3>' + prods(p['abk'], ab, p['nab'], A, B) + '</section>')
        sec_ba = (f'<section class="gsec"><h2>What {B} sells to {A}</h2>' + ('<h3>By product group</h3>' + tm_ba if tm_ba else '')
                  + '<h3>Top products</h3>' + prods(p['bak'], ba, p['nba'], B, A) + '</section>')
        hist = p.get('hist') or {}
        hrows = [(y, self.usd(v[0]), self.usd(v[1]), self.usd(v[0] + v[1])) for y, v in sorted(hist.items(), reverse=True)]
        sec_hist = (f'<section class="gsec"><h2>The last three years</h2>' + self.year_cols(hist, f'{A} → {B}', f'{B} → {A}')
                    + self.table(['Year', f'{A} → {B}', f'{B} → {A}', 'Total'], hrows) + '</section>')
        more = lambda x, other: ''.join(f'<a href="{self.pair_href(x, q)}">{self.flag(x)} {e(self.name(x))} – {self.flag(q)} {e(self.name(q))}</a>'
                                        for q in [q for q in self.pairs_of.get(x, []) if q != other][:10])
        others = (f'<h2 class="h">More pairs</h2><div class="pairgrid">{more(a, b)}{more(b, a)}</div>')
        profiles = (f'<div class="two"><a class="nepalcard" href="/trade/{a.lower()}"><span class="fl">{fa}</span><span><b>{A}: full trade profile</b> {h["ic"]("right")}</span></a>'
                    f'<a class="nepalcard" href="/trade/{b.lower()}"><span class="fl">{fb}</span><span><b>{B}: full trade profile</b> {h["ic"]("right")}</span></a></div>')
        src = h['src_box']('Source', f'<p><b>BACI</b> (CEPII), reconciled from what both countries reported to <b>UN Comtrade</b>, 6-digit HS, current US dollars. '
                           f'BACI gives one agreed figure for each flow, so it can differ from either country&#39;s own national statistics.</p>', str(Y))
        npl = self.nepal_official(b if a == 'NPL' else a) if 'NPL' in (a, b) else ''
        py = self.pair_years(a, b)
        if py:
            y = max(py); xab, xba = py[y]; xt = xab + xba; xb = xab - xba; Ia = self.IM[a]; va, vb = self.year_view(a, y), self.year_view(b, y)
            prev = py.get(y - 1)
            lead = (f'<p class="ans">{A} exported <b>{self.usd(xab)}</b> of goods to {B} in {y}, and {B} exported <b>{self.usd(xba)}</b> to {A}. '
                    f'Trade between the two totalled <b>{self.usd(xt)}</b>, with a {self.usd(abs(xb))} surplus for {A if xb >= 0 else B}.'
                    + (f' Against {y - 1}, {A}&#39;s exports to {B} changed by {self._chg(xab, prev[0])} and {B}&#39;s to {A} by {self._chg(xba, prev[1])}.' if (prev and all(prev)) else '') + '</p>')
            ra, rb = rank_in(va['xp'], b), rank_in(vb['xp'], a)
            ctx = '<ul class="ctx">'
            if ra:
                ctx += f'<li>{B} was {A}&#39;s <b>#{ra}</b> export market in {y}, taking {self.share(xab, va["x"])} of {A}&#39;s exports.</li>'
            if rb:
                ctx += f'<li>{A} was {B}&#39;s <b>#{rb}</b> export market in {y}, taking {self.share(xba, vb["x"])} of {B}&#39;s exports.</li>'
            ctx += '</ul>'
            tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(xab)}</b><span>{A} → {B} ({y})</span></div>'
                     f'<div class="s"><b class="im">{self.usd(xba)}</b><span>{B} → {A} ({y})</span></div>'
                     f'<div class="s"><b>{self.usd(xt)}</b><span>Total trade ({y})</span></div></div>')
            mx = max(xab, xba) or 1
            scale = (f'<div class="card pscale"><div class="pr"><span>{fa} {A} → {fb} {B}</span><div><i style="width:{max(1.5, 100.0 * xab / mx):.1f}%;background:var(--exp)"></i></div><b>{self.usd(xab)}</b></div>'
                     f'<div class="pr"><span>{fb} {B} → {fa} {A}</span><div><i style="width:{max(1.5, 100.0 * xba / mx):.1f}%;background:var(--imp)"></i></div><b>{self.usd(xba)}</b></div>'
                     f'<p class="fine" style="margin:6px 0 0">Both bars on the same scale. Each is the exporting country&#39;s own customs figure for {y}.</p></div>')
            yrows = [(str(yy), self.usd(v[0]) if v[0] else '—', self.usd(v[1]) if v[1] else '—', self.usd(v[0] + v[1]) if all(v) else '—') for yy, v in sorted(py.items(), reverse=True)]
            sec_years = (f'<section class="gsec"><h2>Year by year, {min(py)} to {y}</h2><p class="gk">What each country reports exporting to the other, in US dollars.</p>'
                         + self.year_cols({str(k): v for k, v in py.items()}, f'{A} → {B}', f'{B} → {A}') + self.table(['Year', f'{A} → {B}', f'{B} → {A}', 'Total'], yrows) + '</section>')
            pnote = (f'<section class="gsec"><h2>What they trade: products in {Y}</h2><p class="gk">Product detail is published once a year, and {Y} is the newest year available. '
                     f'It comes from BACI, which reconciles both countries&#39; records into one figure per flow: {self.usd(ab)} from {A} to {B} and {self.usd(ba)} from {B} to {A} in {Y}. '
                     f'Those totals differ from the customs figures above; shares below are of the BACI totals.</p></section>')
            src = h['src_box']('Sources', f'<p>Totals for every year: <b>International Monetary Fund</b>, International Trade in Goods by partner country, retrieved {self.IM_DATE}: each exporter&#39;s own customs figures, '
                               f'converted to US dollars at the average exchange rate of each month. Products for {Y}: <b>BACI</b> (CEPII), reconciled from UN Comtrade, 6-digit HS. '
                               f'The two use different methods, so compare like with like. <a href="/about">About the data</a></p>', str(y))
            return h['main'](h['back']('/trade/pairs', 'Country pairs') + f'<div class="ph"><h1 class="h2">{fa} {A} – {fb} {B} trade, {y}' + (f' and {Ia["cur"]}' if Ia.get('cur') else '') + '</h1></div>'
                             + lead + tiles + scale + ctx + npl + self.pair_latest(a, b) + sec_years + pnote
                             + sec_ab.replace(f'<h2>What {A} sells to {B}</h2>', f'<h2>What {A} sells to {B}, {Y}</h2>') + sec_ba.replace(f'<h2>What {B} sells to {A}</h2>', f'<h2>What {B} sells to {A}, {Y}</h2>')
                             + profiles + others + src)
        return h['main'](h['back']('/trade/pairs', 'Country pairs') + f'<div class="ph"><h1 class="h2">{fa} {A} – {fb} {B} trade, {Y}</h1></div>'
                         + lead + tiles + scale + ctx + npl + self.pair_latest(a, b) + sec_ab + sec_ba + sec_hist + profiles + others + src)

    def pairs_index(self):
        h = self.h; e = h['esc']; keys = sorted(self.pair_keys(), key=lambda k: -(self.P[k]['ab'] + self.P[k]['ba']))
        rows = []
        for k in keys:
            a, b = k.split('-'); p = self.P[k]
            rows.append((f'<a href="/trade/{a.lower()}/{b.lower()}">{self.flag(a)} {e(self.name(a))} – {self.flag(b)} {e(self.name(b))}</a>',
                         self.usd(p['ab'] + p['ba']), self.usd(p['ab']), self.usd(p['ba'])))
        src = h['src_box']('Source', '<p><b>BACI</b> (CEPII), reconciled from UN Comtrade, current US dollars.</p>', str(self.Y))
        return h['main'](h['back']('/trade', 'Global trade') + f'<div class="ph"><h1 class="h2">Country pairs: bilateral trade in {self.Y}</h1>'
                         f'<p>{len(keys):,} pairs, largest first: every economy with each of its ten largest trading partners, plus every pair among the SAARC economies, China and the largest exporters. Each page shows what each side sells the other.</p></div>'
                         + self.table(['Pair', 'Total trade', 'First to second', 'Second to first'], rows)
                         + '<a class="nepalcard" href="/trade/region/south-asia" style="margin-top:var(--s5)"><span class="fl">\U0001F30F</span><span><b>South Asia hub</b>: the SAARC who-sells-to-whom table ' + h['ic']('right') + '</span></a>' + src)

    def nepal_official(self, other=None):
        """On pages about Nepal: point to customsnepal.com for the official rupee, fiscal-year figures.
        Keeps the two sites apart: this one is US dollars by calendar year, that one is Department of Customs data."""
        href = 'https://www.customsnepal.com/trade-partners'; label = 'Nepal&#39;s trade by country'
        if other:
            m = self.h['main_partner'](self.name(other))
            if m:
                href, label = 'https://www.customsnepal.com' + m, 'Nepal–' + self.h['esc'](self.name(other)) + ' trade'
        return (f'<a class="nepalcard" href="{href}"><span class="fl">\U0001F1F3\U0001F1F5</span><span><b>{label} in official figures</b>: Department of Customs data in rupees, '
                f'by fiscal year and 8-digit code, with duty, on customsnepal.com {self.h["ic"]("right")}</span></a>')

    # ---------- product by country ("Vietnam coffee exports")
    def pc_keys(self):
        return self._pc_keys

    def pc_href(self, iso, code):
        return f'/trade/{iso.lower()}/exports/{code}' if (iso + '-' + code) in self._pc_set else None

    _STOP = {'or', 'and', 'of', 'other', 'the', 'for', 'with', 'not', 'in', 'to', 'than', 'a', 'an', 'on', 'by', 'whether', 'including', 'n.e.c.', 'from', 'their', 'thereof', 'those', 'such'}

    def pc_short(self, code, n=38):
        """Product name cut at a word boundary, never ending on a joining word."""
        full = re.split(r'[;,]? n\.e\.c\.', self.h['hs_desc'](code).replace(' (', ', ').split(', excluding')[0])[0]
        words = full.split(); out = []
        for w in words:
            if len(' '.join(out + [w])) > n:
                break
            out.append(w)
        while len(out) > 1 and out[-1].strip('.,;:()').lower() in self._STOP:
            out.pop()
        return (' '.join(out) or full[:n]).rstrip('.,;:( ')

    def pc_title(self, iso, code):
        tail = f' Exports {self.Y} (HS {self.h["fmt_code"](code)})'
        room = 65 - len(self.name(iso)) - 1 - len(tail)
        return f'{self.name(iso)} {self.pc_short(code, max(12, room))}{tail}'

    def pc_desc(self, iso, code):
        p = self.PC[iso + '-' + code]
        s = (f'{self.name(iso)} exported {self.usd(p["v"])} of {self.pc_short(code, 50).lower()} (HS {self.h["fmt_code"](code)}) in {self.Y}, '
             f'{p["s"]:.1f}% of world exports, rank #{p["r"]}.')
        if p['b']:
            s += f' Largest buyer: {self.name(p["b"][0][0])} ({self.share(p["b"][0][1], p["v"], 0)}).'
        return s

    def product_country(self, iso, code):
        h = self.h; e = h['esc']; p = self.PC[iso + '-' + code]; Y = self.Y
        nm = e(self.name(iso)); fl = self.flag(iso); full = e(h['hs_desc'](code)); short = e(self.pc_short(code, 60))
        v = p['v']; b = p['b']
        lead = (f'<p class="ans">{nm} exported <b>{self.usd(v)}</b> of this product in {Y}. That is <b>{p["s"]:.1f}%</b> of world exports '
                f'({self.usd(p["w"])}), which ranks {nm} <b>#{p["r"]}</b> of {p["ne"]} exporting economies.'
                + (f' The largest buyer was {self.clink(b[0][0])}, taking {self.share(b[0][1], v)}.' if b else '') + '</p>')
        tiles = (f'<div class="statrow" style="margin-top:0"><div class="s"><b class="ex">{self.usd(v)}</b><span>Exports ({Y})</span></div>'
                 f'<div class="s"><b>{p["s"]:.1f}%</b><span>Share of world exports</span></div>'
                 f'<div class="s"><b>#{p["r"]}</b><span>World rank</span></div>'
                 f'<div class="s"><b>{p["nb"]}</b><span>Buying countries</span></div></div>')
        unit = ''
        if p.get('q', 0) > 0:
            per_kg = v / p['q']          # thousand USD per tonne = USD per kg
            unit = (f'<p class="fine">Average export value: <b>${per_kg:,.2f} per kg</b> ({p["q"]:,.0f} tonnes reported). '
                    f'An average across every grade and buyer, not a market price.</p>')
        top3 = sum(x for _, x in b[:3])
        brow = []
        for j, x in b:
            ph = self.pair_href(iso, j)
            brow.append((self.clink(j) + (f' <a class="pl" href="{ph}">pair</a>' if ph else ''), x, f'{self.usd(x)} <small>{self.share(x, v)}</small>'))
        brow = brow[:15]
        bmap = self.map_tabs('b', [('Buyers', self._map(iso, b, v, 'these exports'))], nm, f'Shade shows each buyer&#39;s share of {nm}&#39;s exports of this product.') if b else ''
        sec_b = (f'<section class="gsec"><h2>Who buys it</h2>' + bmap + f'<h3>Top {len(brow)} markets</h3>' + self.barlist(brow, 'var(--exp)')
                 + f'<p class="fine">{nm} sold this product to {p["nb"]} countries. The top three took {self.share(top3, v, 0)}.</p></section>') if brow else ''
        wt = self.WTOP.get(code) or []
        wrows = []
        for i, (c, x) in enumerate(wt, 1):
            href = self.pc_href(c, code)
            lab = f'<b>{self.flag(c)} {e(self.name(c))}</b>' if c == iso else (self.clink(c) if not href else f'<a href="{href}">{self.flag(c)} {e(self.name(c))}</a>')
            wrows.append((f'<small class="rkn">#{i}</small> ' + lab, x, f'{self.usd(x)} <small>{self.share(x, p["w"])}</small>'))
        if iso not in [c for c, _ in wt]:
            wrows.append((f'<small class="rkn">#{p["r"]}</small> <b>{fl} {nm}</b>', v, f'{self.usd(v)} <small>{p["s"]:.1f}%</small>'))
        sec_w = (f'<section class="gsec"><h2>The largest exporters of this product</h2>' + self.barlist(wrows, 'var(--exp)') + '</section>') if wrows else ''
        hist = dict(p.get('hist') or {}); hist[str(Y)] = v
        hrows = [(y, self.usd(x) if x else '—') for y, x in sorted(hist.items(), reverse=True)]
        sec_h = '<section class="gsec"><h2>The last three years</h2>' + self.table(['Year', f'{nm} exports'], hrows) + '</section>'
        others = [k for k in self._pc_by_country.get(iso, []) if k != code]
        sec_o = (f'<h2 class="h">Other leading exports of {nm}</h2><div class="pairgrid">'
                 + ''.join(f'<a href="{self.pc_href(iso, k)}">{e(self.pc_short(k, 44))} <small>{self.usd(self.PC[iso + "-" + k]["v"])}</small></a>' for k in others) + '</div>') if others else ''
        links = (f'<div class="two"><a class="nepalcard" href="/trade/{iso.lower()}"><span class="fl">{fl}</span><span><b>{nm}: full trade profile</b> {h["ic"]("right")}</span></a>'
                 f'<a class="nepalcard" href="{h["code_href"](code)}"><span class="fl">\U0001F50E</span><span><b>HS {h["fmt_code"](code)}</b>: definition and world trade {h["ic"]("right")}</span></a></div>')
        src = h['src_box']('Source', '<p><b>BACI</b> (CEPII), reconciled from what exporters and importers reported to <b>UN Comtrade</b>, 6-digit HS 2022, current US dollars. '
                           'Quantities are in tonnes where countries reported them.</p>', str(Y))
        return h['main'](h['back'](f'/trade/{iso.lower()}', self.name(iso)) + f'<div class="ph"><h1 class="h2">{fl} {nm} exports of {short}, {Y}</h1>'
                         f'<p>HS {h["fmt_code"](code)}: {full}</p></div>' + lead + tiles + unit + sec_b + sec_w + sec_h + links + sec_o + src)

    # ---------- South Asia hub
    def region_title(self):
        return f'South Asia Trade {self.Y}: SAARC Countries, Partners and Trade With Each Other'

    def region_desc(self):
        S = [c for c in self.D['saarc'] if c in self.C]
        intra = sum(v for a in S for p, v in self.C[a]['xp'] if p in S)
        tx = sum(self.C[c]['x'] for c in S)
        return (f'The eight SAARC economies exported {self.usd(tx)} of goods in {self.Y}; {self.share(intra, tx)} of it went to each other. '
                f'Profiles, a who-sells-to-whom matrix and every country pair.')

    def region(self):
        h = self.h; e = h['esc']; Y = self.Y
        S = [c for c in self.D['saarc'] if c in self.C and c in h['CBYISO']]
        tx = sum(self.C[c]['x'] for c in S); tm = sum(self.C[c]['m'] for c in S)
        ex = {a: dict(self.C[a]['xp']) for a in S}
        intra = sum(ex[a].get(b, 0) for a in S for b in S if a != b)
        lead = (f'<p class="ans">The eight SAARC economies exported <b>{self.usd(tx)}</b> of goods and imported <b>{self.usd(tm)}</b> in {Y}. '
                f'Only <b>{self.share(intra, tx)}</b> of their exports, {self.usd(intra)}, went to one another.</p>')
        rows = [(self.clink(c), self.usd(self.C[c]['x']), self.usd(self.C[c]['m']), self.share(sum(ex[c].get(b, 0) for b in S if b != c), self.C[c]['x']),
                 self.clink(self.C[c]['xp'][0][0]) if self.C[c]['xp'] else '—') for c in sorted(S, key=lambda c: -self.C[c]['x'])]
        t1 = self.table(['Economy', 'Exports', 'Imports', 'Share of exports going to SAARC', 'Largest market'], rows)
        head = ['Exporter ↓ / Importer →'] + [f'{self.flag(b)} {b}' for b in S]
        mrows = []
        for a in S:
            r = [self.clink(a)]
            for b in S:
                if a == b:
                    r.append('<span class="mu">·</span>')
                else:
                    v = ex[a].get(b, 0); ph = self.pair_href(a, b)
                    cell = self.usd(v) if v >= 1 else '—'
                    r.append(f'<a href="{ph}">{cell}</a>' if ph and v >= 1 else cell)
            mrows.append(r)
        t2 = self.table(head, mrows, 'mx')
        prs = [k for k in self.pair_keys() if all(x in S or x == 'CHN' for x in k.split('-')) and any(x in S for x in k.split('-'))]
        prs.sort(key=lambda k: -(self.P[k]['ab'] + self.P[k]['ba']))
        grid = '<div class="pairgrid">' + ''.join(
            f'<a href="/trade/{k.split("-")[0].lower()}/{k.split("-")[1].lower()}">{self.flag(k.split("-")[0])} {e(self.name(k.split("-")[0]))} – {self.flag(k.split("-")[1])} {e(self.name(k.split("-")[1]))} '
            f'<small>{self.usd(self.P[k]["ab"] + self.P[k]["ba"])}</small></a>' for k in prs) + '</div>'
        src = h['src_box']('Source', '<p><b>BACI</b> (CEPII), reconciled from UN Comtrade, 6-digit HS, current US dollars. SAARC here means Afghanistan, Bangladesh, Bhutan, India, '
                           'Maldives, Nepal, Pakistan and Sri Lanka.</p>', str(Y))
        return h['main'](h['back']('/trade', 'Global trade') + f'<div class="ph"><h1 class="h2">South Asia: trade in {Y}</h1><p>The eight SAARC economies, what they trade with the world and with each other.</p></div>'
                         + lead + '<h2 class="h">The eight economies</h2>' + t1
                         + '<h2 class="h">Who sells to whom inside South Asia</h2>' + t2
                         + '<p class="fine">Read across: the row country&#39;s exports to the column country. A linked figure opens that pair&#39;s page. A dash means BACI records no trade for that flow in the year; a small flow can be missing when neither country reported it.</p>'
                         + '<h2 class="h">Country pairs, including China</h2>' + grid + src)


CSS = '''
/* deep profiles + pair pages (scripts/world_deep.py) */
.ans{font-size:1.08rem;line-height:1.55;margin:var(--s3) 0 var(--s4);max-width:70ch}
.ans a,.ctx a,.dt a,.pl2 a{color:var(--accent)}
h2.h{font-size:1.15rem;margin:var(--s6) 0 var(--s3)}
.bars.dp .barrow .lb{white-space:normal}.bars.dp .vl{white-space:nowrap}.bars.dp .vl small{color:var(--muted);font-weight:500;margin-left:4px}
.bars.dp a{color:inherit;text-decoration:none}.bars.dp a:hover{text-decoration:underline}
.bars.dp a.pl{font-size:.68rem;font-weight:700;color:var(--accent);border:1px solid var(--border);border-radius:999px;padding:0 6px;margin-left:4px;text-decoration:none}
.dscroll{overflow-x:auto;border:1px solid var(--border);border-radius:var(--r,12px);background:var(--card)}
.dt{width:100%;border-collapse:collapse;font-size:.88rem}.dt th{font-size:.72rem;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);white-space:nowrap;font-weight:650}
.dt td{padding:8px 10px;border-top:1px solid var(--border);vertical-align:top}.dt tbody tr:first-child td{border-top:0}
.dt .r{text-align:right;white-space:nowrap}.dt td:first-child{min-width:190px}.dt small{color:var(--muted)}
.dt.mx td:first-child{min-width:130px;white-space:nowrap}.dt.mx .mu{color:var(--muted)}
.hsc{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;color:var(--muted)}
.rk1,.rk2,.rk3{display:inline-block;font-size:.7rem;font-weight:700;border-radius:999px;padding:0 7px;white-space:nowrap}
.rk1{background:#FDE68A;color:#713F12}.rk2{background:#E2E8F0;color:#334155}.rk3{background:#FED7AA;color:#7C2D12}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:var(--s3)}
.pl2{list-style:none;margin:8px 0 0;padding:0}.pl2 li{display:flex;justify-content:space-between;gap:10px;padding:5px 0;border-top:1px solid var(--border);font-size:.9rem}.pl2 li:first-child{border-top:0}
.tf{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;align-items:end;margin:6px 0 16px}.tf label{display:flex;flex-direction:column;gap:4px;font-size:.8rem;font-weight:600;color:var(--muted)}
.tf select,.tf input[type=search]{font:inherit;font-weight:400;color:var(--fg);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:9px 10px;min-height:42px;width:100%;box-sizing:border-box}
.tf .tck{flex-direction:row;align-items:center;gap:8px;min-height:42px;color:var(--fg)}.tbtn{font:inherit;font-weight:700;background:var(--accent);color:#fff;border:0;border-radius:10px;padding:10px 18px;min-height:42px;cursor:pointer}.tbtn:disabled{opacity:.6;cursor:default}
.tf :focus-visible,.tbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tnl{list-style:none;margin:0;padding:0;display:grid;gap:10px}.tn{border:1px solid var(--border);background:var(--card);border-radius:12px;padding:12px 14px;display:grid;gap:3px}.tn a{color:var(--fg);text-decoration:none}.tn a:hover b{text-decoration:underline}
.tn b{font-size:.98rem;line-height:1.35}.tn span{font-size:.84rem;color:var(--muted)}.tn .tn-m{color:var(--fg)}.tn.closed{opacity:.6}.tmsg{padding:18px;border:1px dashed var(--border);border-radius:12px;color:var(--muted)}
.pairgrid{display:flex;flex-wrap:wrap;gap:8px}.pairgrid a{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);background:var(--card);border-radius:999px;padding:6px 12px;font-size:.85rem;color:var(--fg);text-decoration:none}
.pairgrid a:hover{border-color:var(--accent)}.pairgrid small{color:var(--muted)}
.dall{margin-top:var(--s5)}.dall>summary{cursor:pointer;font-weight:650;padding:10px 0;color:var(--accent)}
.ctx{margin:var(--s4) 0;padding-left:1.1em;line-height:1.6}
.pscale{margin-top:var(--s4)}.pscale .pr{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center;margin-bottom:10px;font-size:.9rem}
.pscale .pr div{grid-column:1/-1;height:18px;border-radius:5px;background:var(--bg);overflow:hidden}.pscale .pr i{display:block;height:100%;border-radius:5px}
@media(max-width:600px){.dt{font-size:.82rem}.dt td:first-child{min-width:150px}}
'''


# World Trade Data: the site's own look (sea-chart ink, teal for exports, buoy orange for imports; Archivo headings).
SHELL_CSS = '''
@font-face{font-family:"IBM Plex Sans";font-weight:400;font-style:normal;font-display:swap;src:url(/assets/fonts/ibm-plex-sans-latin-400-normal.woff2) format("woff2")}
@font-face{font-family:"IBM Plex Sans";font-weight:600;font-style:normal;font-display:swap;src:url(/assets/fonts/ibm-plex-sans-latin-600-normal.woff2) format("woff2")}
@font-face{font-family:"IBM Plex Sans";font-weight:700;font-style:normal;font-display:swap;src:url(/assets/fonts/ibm-plex-sans-latin-700-normal.woff2) format("woff2")}
@font-face{font-family:"Archivo";font-weight:700;font-style:normal;font-display:swap;src:url(/assets/fonts/archivo-latin-700-normal.woff2) format("woff2")}
@font-face{font-family:"Archivo";font-weight:800;font-style:normal;font-display:swap;src:url(/assets/fonts/archivo-latin-800-normal.woff2) format("woff2")}
@font-face{font-family:"IBM Plex Mono";font-weight:500;font-style:normal;font-display:swap;src:url(/assets/fonts/ibm-plex-mono-latin-500-normal.woff2) format("woff2")}
:root{--fg2:var(--fg-2);--navy:var(--hero1);--mono:var(--f-mono);--f:var(--f-body);
  --f-body:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --f-mono:"IBM Plex Mono","SF Mono",SFMono-Regular,ui-monospace,Menlo,Consolas,monospace;
  --f-head:"Archivo","IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--gold:#B7791F;--gold-bg:#FBF0D9}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--gold:#F2C265;--gold-bg:#3A2C0C}}
:root[data-theme="dark"]{--gold:#F2C265;--gold-bg:#3A2C0C}
body{font-size:1rem;line-height:1.55;font-feature-settings:"ss01"}
b,strong,th{font-weight:600}td.r,.dt td,.statrow b,.vl{font-variant-numeric:tabular-nums}
#app{background:linear-gradient(180deg,var(--accent-bg) 0,var(--bg) 240px)}
.hsc,.mono,h1.dcode{font-family:var(--f-mono);font-weight:500}
a{text-underline-offset:3px}main a:not([class]):hover{text-decoration:underline}
.gsec.gx{border-top-color:var(--exp)}.gsec.gm2{border-top-color:var(--imp)}
.gsec.gx>h2::after,.gsec.gm2>h2::after{content:"Exports";display:inline-block;vertical-align:middle;margin-left:12px;padding:3px 9px;border-radius:999px;font-family:var(--f-body);font-size:.72rem;font-weight:700;letter-spacing:0;color:#fff;background:#0B6E6E}
.gsec.gm2>h2::after{content:"Imports";background:#C2461F}
.hc:first-child>b,.hc:last-child>b{color:var(--gold)}.hc.pos>b{color:var(--free)}.hc.neg>b{color:var(--hi)}
.dt thead th{font-size:.74rem;color:var(--muted);font-weight:600}.dt tbody tr:hover{background:var(--accent-bg)}
.wrap,.bar .wrap{max-width:1060px}.nav.topnav{margin-left:auto;overflow:visible}
.bar{background:var(--hero1)}
.logo{font-family:var(--f-head);font-size:1.06rem;letter-spacing:-.01em}.logo .mk{background:none;width:28px;height:28px;border-radius:0}
.logo .mk svg{width:28px;height:28px;display:block}
.gnm.cur>summary,.gnm:has([aria-selected="true"])>summary{box-shadow:inset 0 -2px 0 #4CC9C2}
footer.sf{background:linear-gradient(180deg,#0C2530,#071A21)}
footer.sf .sf-logo{font-family:var(--f-head)}footer.sf .sf-logo .mark{display:grid;place-items:center;width:30px;height:30px;background:none}
footer.sf .sf-logo .mark svg{width:28px;height:28px}
footer.sf .sf-track button{background:#0C7B79}footer.sf a:hover{color:#8FE3DD}
h1,h1.h2,h2.h,.statrow .s b,.ph h1,.wcol h2,.wstrip h2{font-family:var(--f-head);letter-spacing:-.015em}
h1.h2{font-size:clamp(1.6rem,3.4vw,2.2rem);line-height:1.1;font-weight:800}
a.row .d,.dtitle,.crumb{overflow-wrap:anywhere;min-width:0}table.bk td:last-child{white-space:normal}table.bk td:first-child{padding-right:14px}

.whero{background:none;border-bottom:1px solid var(--border)}
.whero .wrap{padding-top:clamp(36px,7vw,84px);padding-bottom:clamp(28px,5vw,56px)}
.whero h1{font-family:var(--f-head);font-weight:800;font-size:clamp(2.6rem,8.4vw,5.6rem);line-height:.94;letter-spacing:-.035em;margin:0 0 .28em;color:var(--fg);text-wrap:balance}
.whero p{font-size:1.1rem;line-height:1.5;color:var(--fg-2);margin:0 0 1.1em;max-width:54ch}
.wsearch{position:relative;display:flex;gap:8px;max-width:620px;background:var(--card);border:2px solid var(--fg);border-radius:14px;padding:6px}
.wsearch input{flex:1;min-width:0;border:0;background:none;font:inherit;font-size:1.08rem;padding:11px 12px;color:var(--fg);outline:none}
.wsearch button{border:0;border-radius:9px;background:var(--fg);color:var(--bg);font:inherit;font-weight:700;padding:0 20px;cursor:pointer}
.wsearch:focus-within{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-bg)}
.wsug{position:absolute;left:-2px;right:-2px;top:calc(100% + 8px);z-index:20;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:6px;box-shadow:0 18px 40px -20px rgba(8,30,40,.5)}
.wsug a{display:flex;justify-content:space-between;gap:12px;align-items:baseline;padding:10px 12px;border-radius:9px;color:var(--fg);text-decoration:none}
.wsug a:hover,.wsug a:focus-visible{background:var(--accent-bg)}.wsug small{color:var(--muted);font-size:.8rem;white-space:nowrap}
.whero .wtry{font-size:.9rem;color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;max-width:none}
.wtry a{color:var(--accent);font-weight:600}

.wstrip{margin-top:var(--s6)}
.wstrip h2{font-size:clamp(1.25rem,2.6vw,1.7rem);line-height:1.15;font-weight:800;margin:0 0 14px;max-width:26ch}
.ws{display:flex;height:112px;border-radius:12px;overflow:hidden;gap:2px;background:var(--bg)}
.ws-s{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:flex-end;gap:1px;padding:8px 8px 9px;background:#0E8583;color:#fff;text-decoration:none;overflow:hidden;white-space:nowrap}
.ws-s:nth-child(even){background:#0B6E6E}.ws-s.ws-r{background:var(--muted-bg);color:var(--fg-2)}
.ws-s span{font-size:1.1rem;line-height:1}.ws-s b{font-size:.8rem;font-weight:700;overflow:hidden;text-overflow:ellipsis}.ws-s i{font-style:normal;font-size:.78rem;opacity:.9;font-variant-numeric:tabular-nums}
.ws-s.sm b{display:none}.ws-s.sm{padding-left:5px;padding-right:2px}.wcol li a small{font-weight:400;color:var(--muted)}.ws-s:hover{filter:brightness(1.12);text-decoration:none}.ws-s:focus-visible{outline:3px solid var(--imp);outline-offset:-3px}
.wsl{display:none;list-style:none;margin:12px 0 0;padding:0}
.wsl li{display:grid;grid-template-columns:minmax(0,1fr) auto 3.6em;gap:10px;padding:7px 0;border-bottom:1px solid var(--border);font-size:.92rem}
.wsl span,.wsl i{font-style:normal;font-variant-numeric:tabular-nums;text-align:right}.wsl i{color:var(--muted)}
.wcols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px;margin-top:var(--s6);padding-top:var(--s5);border-top:2px solid var(--fg)}
.wcol h2{font-size:1.35rem;font-weight:800;margin:0 0 4px}.wcol>p{color:var(--muted);font-size:.9rem;margin:0 0 10px;min-height:3em}
.wcol ol{list-style:none;margin:0;padding:0}
.wcol li{display:flex;justify-content:space-between;gap:12px;align-items:baseline;padding:8px 0;border-top:1px solid var(--border);font-size:.95rem}
.wcol li a{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--fg);font-weight:600}.wcol li a:hover{color:var(--accent)}
.wcol li span{font-variant-numeric:tabular-nums;color:var(--fg-2);white-space:nowrap}
.wmore{display:inline-block;margin-top:12px;font-weight:700}
.wleads{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.wlead{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:10px;padding:13px 14px;background:var(--card);border:1px solid var(--border);border-radius:12px;color:var(--fg);text-decoration:none}
.wlead span{grid-row:span 3;font-size:1.5rem;line-height:1.1}.wlead b{font-size:.95rem}.wlead em{font-style:normal;color:var(--fg-2);font-size:.88rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wlead i{font-style:normal;font-size:.8rem;color:var(--accent);font-weight:700}.wlead:hover{border-color:var(--accent);text-decoration:none}
/* country profile graphics */
:root{--m0:#E3E9E6;--m2:#BFE1DD;--m3:#7CC3BD;--m4:#2F9A94;--m5:#0B5F5F;--mme:#E2572B;--msea:#FFFFFF}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--m0:#1A3540;--m2:#1F5458;--m3:#27807F;--m4:#4CC9C2;--m5:#B6F3EE;--mme:#FF7F57;--msea:#0E2630}}
:root[data-theme="dark"]{--m0:#1A3540;--m2:#1F5458;--m3:#27807F;--m4:#4CC9C2;--m5:#B6F3EE;--mme:#FF7F57;--msea:#0E2630}
.gmap{margin-top:var(--s4);background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px}
.gmap>input{position:absolute;opacity:0;pointer-events:none}
.gtabs{display:inline-flex;gap:4px;background:var(--muted-bg);border-radius:10px;padding:4px;margin-bottom:8px;max-width:100%;flex-wrap:wrap}
.gtabs label{padding:7px 12px;border-radius:7px;font-weight:700;font-size:.86rem;color:var(--fg-2);cursor:pointer}
.gmap>input:nth-of-type(1):checked~.gtabs label:nth-child(1),.gmap>input:nth-of-type(2):checked~.gtabs label:nth-child(2){background:var(--card);color:var(--fg);box-shadow:0 1px 2px rgba(0,0,0,.12)}
.gmap>input:focus-visible~.gtabs{outline:2px solid var(--accent);outline-offset:2px}
.gm{display:none;background:var(--msea);border-radius:10px}.gm svg{display:block;width:100%;height:auto}
.gmap>input:nth-of-type(1):checked~.gmx,.gmap>input:nth-of-type(2):checked~.gmm{display:block}
.gm use{stroke:var(--msea);stroke-width:.5;stroke-linejoin:round}.gm a:hover use,.gm a:focus use{stroke:var(--fg);stroke-width:1.2}
.m0{fill:var(--m0)}.m2{fill:var(--m2)}.m3{fill:var(--m3)}.m4{fill:var(--m4)}.m5{fill:var(--m5)}.me{fill:var(--mme)}
.mlg{display:flex;flex-wrap:wrap;gap:6px 14px;margin:10px 2px 0;font-size:.78rem;color:var(--fg-2)}
.mlg span{display:inline-flex;align-items:center;gap:6px}.mlg i{width:14px;height:10px;border-radius:3px;display:inline-block;background:var(--m0)}
.mlg i.m2{background:var(--m2)}.mlg i.m3{background:var(--m3)}.mlg i.m4{background:var(--m4)}.mlg i.m5{background:var(--m5)}.mlg i.me{background:var(--mme)}
.gmap .fine{margin:8px 2px 0}
.tm{position:relative;width:100%;aspect-ratio:16/7;margin-top:6px}
.tc{position:absolute;display:block;padding:1px;color:#fff;text-decoration:none;overflow:hidden}
.tc span{display:flex;flex-direction:column;justify-content:flex-end;height:100%;border-radius:5px;padding:7px 8px;overflow:hidden;background:#0B6E6E}
.tm.imp .tc span{background:#C2461F}
.tc b{font-size:.84rem;line-height:1.15;font-weight:700}.tc i{font-style:normal;font-family:var(--f-head);font-weight:800;font-size:1.5rem;line-height:1.05}.tc em{font-style:normal;font-size:.76rem;color:#fff}
.tc.md i{font-size:1.05rem}.tc.md em{display:none}.tc.md b{font-size:.74rem}.tc.sm b,.tc.sm em{display:none}.tc.sm i{font-size:.72rem}.tc.sm span{padding:2px 3px;justify-content:center;align-items:center}
.tc:hover span,.tc:focus-visible span{filter:brightness(1.15)}.tc:hover{text-decoration:none}
.tml{margin-top:8px;font-size:.88rem}.tml summary{cursor:pointer;color:var(--accent);font-weight:600}
.tml ol{list-style:none;margin:8px 0 0;padding:0}.tml li{display:grid;grid-template-columns:minmax(0,1fr) auto 3.6em;gap:10px;padding:6px 0;border-top:1px solid var(--border)}
.tml li span,.tml li i{font-style:normal;font-variant-numeric:tabular-nums;text-align:right}.tml li i{color:var(--muted)}
.gl{margin:var(--s4) 0 0}.glr{display:grid;grid-template-columns:5em minmax(0,1fr) 5.5em;gap:12px;align-items:center;padding:5px 0;font-size:.92rem}
.glr span{color:var(--fg-2);font-weight:600}.glr div{height:22px}.glr i{display:block;height:100%;border-radius:0 4px 4px 0}.glr i.x{background:var(--exp)}.glr i.m{background:var(--imp)}
.glr b{text-align:right;font-variant-numeric:tabular-nums}
.dv{margin-top:6px}.dvr{display:grid;grid-template-columns:minmax(0,10.5em) minmax(0,1fr) 5.2em;gap:10px;align-items:center;padding:5px 0;font-size:.9rem}
.dvr span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.dvr div{position:relative;height:18px;background:linear-gradient(var(--border),var(--border)) 50% 0/1px 100% no-repeat}
.dvr i{position:absolute;top:0;bottom:0}.dvr i.pos{background:var(--exp);border-radius:0 4px 4px 0}.dvr i.neg{background:var(--imp);border-radius:4px 0 0 4px}
.dvr b{text-align:right;font-variant-numeric:tabular-nums;font-weight:650}
.dvk{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:8px;font-size:.78rem;color:var(--fg-2)}.dvk span{display:inline-flex;gap:6px;align-items:center}
.dvk i{width:14px;height:10px;border-radius:3px}.dvk i.pos{background:var(--exp)}.dvk i.neg{background:var(--imp)}
.gsec{margin-top:var(--s6);padding-top:var(--s4);border-top:2px solid var(--fg)}.gsec>h2{font-family:var(--f-head);font-size:1.5rem;font-weight:800;margin:0 0 4px;letter-spacing:-.015em}
.ycs{display:flex;gap:18px;align-items:flex-end;height:190px;margin:26px 0 6px;max-width:560px}
.ycs.many{max-width:none;gap:12px}.ycs.huge{gap:3px;padding:0 10px;overflow-x:clip}.ycs.huge .ycb{gap:1px}.ycs.huge .yc>span{min-height:1.2em;white-space:nowrap;overflow:visible;display:flex;justify-content:center}@media(max-width:820px){.ycs.huge{gap:2px}.ycs.huge .ycb{gap:0}}.ycs.lots{gap:6px}.ycs.lots .ycb i b{display:none}.ycs.lots .yc>span{font-size:.72rem}@media(max-width:820px){.ycs.many{gap:6px}.ycs.many .ycb i b{display:none}}
.yc{flex:1;display:flex;flex-direction:column;height:100%;min-width:0}.ycb{flex:1;display:flex;gap:2px;align-items:flex-end;border-bottom:1px solid var(--border)}
.ycb i{flex:1;position:relative;border-radius:4px 4px 0 0;min-width:0}.ycb i.x{background:var(--exp)}.ycb i.m{background:var(--imp)}
.ycb i b{position:absolute;left:50%;bottom:100%;transform:translateX(-50%);font-style:normal;font-size:.72rem;font-weight:650;color:var(--fg);white-space:nowrap;padding-bottom:2px}
.yc>span{text-align:center;font-size:.82rem;color:var(--fg-2);padding-top:5px}.rkn{color:var(--muted);font-variant-numeric:tabular-nums}
.hcs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:var(--s5)}
.hc{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 16px 14px;display:flex;flex-direction:column}
main p a:not([class]),main a.pl{text-decoration:underline;text-underline-offset:2px;text-decoration-thickness:1px}
.hc>b{font-family:var(--f-head);font-weight:800;font-size:clamp(1.9rem,3.4vw,2.6rem);line-height:1;letter-spacing:-.02em;color:var(--fg)}
.hc.pos>b{color:var(--free)}.hc.neg>b{color:var(--hi)}
.hc>p{margin:6px 0 12px;color:var(--fg-2);font-size:.92rem;line-height:1.4;flex:1}
.hb{height:10px;border-radius:5px;background:var(--muted-bg);overflow:hidden;display:flex;gap:2px}.hb i{display:block;height:100%}.hb i.x{background:var(--exp)}.hb i.m{background:var(--imp)}
.hb.two{flex-direction:column;height:22px;background:none;gap:2px}.hb.two i{height:10px;border-radius:0 5px 5px 0}
.hr{position:relative;height:10px;border-radius:5px;background:linear-gradient(90deg,var(--exp),var(--muted-bg) 70%)}.hr i{position:absolute;top:-4px;width:4px;height:18px;margin-left:-2px;border-radius:2px;background:var(--fg);box-shadow:0 0 0 2px var(--card)}
.hrl{display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-top:5px}
.flw{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:0;align-items:center;margin-top:10px;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px}
.flw svg{display:block;width:100%;height:auto}.flw .fn{font-size:15px;font-weight:700;fill:var(--fg)}.flw .fv{font-size:13.5px;fill:var(--muted)}.flw a:hover .fn{fill:var(--accent);text-decoration:underline}
.flh{display:block;font-size:.8rem;color:var(--muted);font-weight:700;margin-bottom:8px}.flw>div:first-child .flh{text-align:left}.flw>div:last-child .flh{text-align:right}
.flc{display:flex;flex-direction:column;align-items:center;gap:2px;padding:14px 12px;text-align:center;min-width:120px}
.flc span{font-size:2.2rem;line-height:1}.flc b{font-family:var(--f-head);font-size:1.05rem}.flc i{font-style:normal;font-size:.8rem;color:var(--fg-2);font-variant-numeric:tabular-nums}
@media(max-width:820px){.hcs{grid-template-columns:repeat(2,minmax(0,1fr))}.flw{grid-template-columns:minmax(0,1fr);gap:14px}.flc{flex-direction:row;justify-content:center;gap:10px;padding:4px;order:-1}.flc span{font-size:1.6rem}.flw>div:last-child .flh{text-align:left}}
@media(max-width:460px){.hcs{grid-template-columns:minmax(0,1fr)}}
sup.est{color:var(--imp);font-weight:700;cursor:help;margin-left:2px}.ltl .s span small{font-weight:700;font-size:.8rem;margin-left:4px;color:var(--fg)}
.lch{position:relative;margin:18px 0 6px}.lch svg{display:block;width:100%;height:220px;border-bottom:1px solid var(--border);overflow:visible}
.lch path{fill:none;stroke-width:2.5;vector-effect:non-scaling-stroke;stroke-linejoin:round}.lch .lx{stroke:var(--exp)}.lch .lm{stroke:var(--imp)}
.lch .lg{stroke:var(--border);stroke-width:1;vector-effect:non-scaling-stroke}
.lmx{position:absolute;left:0;top:-16px;font-size:.72rem;color:var(--muted)}.lyr{position:relative;height:24px;overflow:hidden}.lyr span{position:absolute;top:5px;font-size:.78rem;color:var(--fg-2);padding-left:4px}
.ysw{display:flex;align-items:center;gap:8px;margin:14px 0 4px;max-width:100%}.ysl{font-size:.82rem;color:var(--muted);font-weight:600}
.ysc{display:flex;flex-wrap:wrap;gap:4px;background:var(--muted-bg);border-radius:12px;padding:4px;overflow-x:auto;scrollbar-width:none;min-width:0}.ysc::-webkit-scrollbar{display:none}
.ysc a{flex:0 0 auto;padding:8px 13px;border-radius:9px;font-weight:600;font-size:.95rem;color:var(--fg-2);text-decoration:none;font-variant-numeric:tabular-nums;white-space:nowrap}
.ysc a:hover{background:var(--card);text-decoration:none}.ysc a.on{background:var(--fg);color:var(--bg)}.ysc a small{font-weight:500;font-size:.72rem;opacity:.8;margin-left:4px}
.yar{flex:0 0 auto;width:36px;height:36px;display:grid;place-items:center;border-radius:50%;border:1px solid var(--border);background:var(--card);color:var(--fg);font-size:1.25rem;line-height:1;text-decoration:none}
.yar:hover{background:var(--fg);color:var(--bg);text-decoration:none}.yar.off{opacity:.3}.hb.two i.p{background:var(--muted)}
@media(max-width:560px){.ysl,.yar{display:none}.ysc a{padding:8px 11px}}
.sms{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;margin-top:10px}.smp{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px 8px}
.smh{font-weight:600;font-size:.95rem}.smh span{display:block;font-weight:400;font-size:.8rem;color:var(--muted);margin-top:2px}.smp svg{display:block;width:100%;height:92px;margin-top:8px;overflow:visible}
.smp path{fill:none;stroke-width:1.6;vector-effect:non-scaling-stroke}.smp path.lx{stroke:var(--exp)}.smp path.lm{stroke:var(--imp)}.smp line.lg{stroke:var(--border);stroke-width:1;vector-effect:non-scaling-stroke}
.smx{position:relative;height:16px;font-size:.7rem;color:var(--muted)}.smx span{position:absolute;transform:translateX(-50%)}
.cmb{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:14px 0}.cmc{display:inline-flex;align-items:center;gap:8px;padding:7px 8px 7px 12px;border:2px solid var(--border);border-radius:999px;background:var(--card);font-weight:600}
.cmc button{border:0;background:var(--muted-bg);color:var(--fg);width:24px;height:24px;border-radius:50%;cursor:pointer;font-size:1rem;line-height:1}.cmc button:hover{background:var(--fg);color:var(--bg)}
#cmadd{padding:9px 14px;border:1px solid var(--border);border-radius:999px;background:var(--card);color:var(--fg);font:inherit;min-width:190px}
.cmg{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:22px}.cmk{background:var(--card);border:1px solid var(--border);border-top:4px solid var(--fg);border-radius:12px;padding:14px 16px}
.cmk h3{margin:0 0 6px;font-size:1.15rem}.cmk h4{margin:14px 0 4px;font-size:.82rem;color:var(--muted);font-weight:600}.cml{list-style:none;margin:0;padding:0}.cml li{display:flex;justify-content:space-between;gap:10px;padding:4px 0;border-bottom:1px solid var(--border);font-size:.93rem}.cml li:last-child{border-bottom:0}.cml b{font-variant-numeric:tabular-nums}
#cmp .lch svg path{stroke-linejoin:round}
.shs{margin-top:10px}.shr{display:grid;grid-template-columns:minmax(110px,190px) 1fr auto;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--border)}
.shr>div{display:flex;flex-direction:column;gap:3px}.shr i{display:block;height:9px;border-radius:0 4px 4px 0}.shr i.p{background:var(--muted)}.shr i.x{background:var(--exp)}.shr i.m{background:var(--imp)}
.shr>b{font-variant-numeric:tabular-nums;font-size:.9rem;white-space:nowrap}@media(max-width:560px){.shr{grid-template-columns:1fr auto}.shr>div{grid-column:1/-1;order:3}}
.rkn{color:var(--muted);font-variant-numeric:tabular-nums;width:2.5em}span.rkn{display:inline-block;width:2em}#rkt tr[hidden]{display:none}
.pdfl{margin:14px 0 0;font-size:.92rem;color:var(--muted)}.pdfl a{display:inline-block;margin-right:10px;padding:9px 14px;border-radius:10px;background:var(--fg);color:var(--bg);font-weight:700;text-decoration:none}
.pdfl span{display:block;margin-top:8px}.absrc{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-top:10px}.absrc>div{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px}.absrc b{display:block;margin-bottom:6px}.absrc p{margin:0 0 6px;font-size:.92rem;color:var(--fg-2)}.absrc span{display:block;font-size:.78rem;color:var(--muted)}
.pdfl a:hover{background:var(--accent);text-decoration:none}.abl{margin:6px 0 0;padding-left:1.2em;max-width:76ch}.abl li{margin:0 0 10px;color:var(--fg-2)}.abl li b{color:var(--fg)}
.gsec>p.ans{margin-top:6px}
.gsec>p.gk{color:var(--fg-2);margin:0 0 10px;max-width:68ch}.gsec h3{font-size:1rem;margin:22px 0 4px}
@media(max-width:700px){.tm{aspect-ratio:4/5}.tc.md b{font-size:.68rem;overflow-wrap:anywhere}.tc.lg b{overflow-wrap:anywhere}.tc span{padding:5px 6px}.dvr{grid-template-columns:minmax(0,7em) minmax(0,1fr) 4.6em}.glr{grid-template-columns:4.2em minmax(0,1fr) 4.6em}}
@media(max-width:820px){.wcols{grid-template-columns:minmax(0,1fr);gap:22px}.wcol>p{min-height:0}.ws{height:64px}.ws-s,.ws-s.sm{padding:0}.ws-s b,.ws-s i,.ws-s span{display:none}.wsl{display:block}}
@media(max-width:720px){body{padding-bottom:calc(64px + env(safe-area-inset-bottom,0px))}.wsearch button{padding:0 14px}}
'''


# Print layout for the PDF trade briefs (A4). The brief reuses the profile's components; this only arranges them on paper.
BRIEF_CSS = '''
@page{size:A4;margin:13mm 12mm 14mm}
html{font-size:11.5px}body.brief{background:#fff;color:#0C2530;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body.brief #app,body.brief{background:#fff}
.bh{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #0C2530;padding-bottom:6px;margin-bottom:12px;font-size:.9rem;color:#58686B}
.bh div{display:flex;align-items:center;gap:7px;color:#0C2530;font-family:var(--f-head);font-size:1.1rem}.bm svg{width:20px;height:20px;display:block}
body.brief h1{font-size:2.3rem;line-height:1.05;margin:0 0 4px}.bsub{color:#58686B;margin:0 0 10px}
body.brief .ans{font-size:1.08rem;margin:0 0 6px}
body.brief .gsec{margin-top:16px;padding-top:10px;break-inside:auto}body.brief .gsec>h2{font-size:1.35rem;break-after:avoid}
body.brief h3{break-after:avoid;margin:12px 0 4px}
body.brief .hcs{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:10px}body.brief .hc{padding:10px 12px;break-inside:avoid}body.brief .hc>b{font-size:1.9rem}
body.brief .flw{grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);padding:8px;break-inside:avoid}body.brief .flc{flex-direction:column;order:0;min-width:90px}
body.brief .gsec:has(.flw){break-inside:avoid}body.brief .statrow{break-inside:avoid}body.brief .lch,body.brief .tm,body.brief table{break-inside:avoid}body.brief .lch svg{height:150px}
body.brief .tm{aspect-ratio:16/6}body.brief .tml,body.brief .pl,body.brief details>summary{display:none}
body.brief details.dall{display:block}body.brief details.dall>*:not(summary){display:block}
body.brief details.dall table tbody tr:nth-child(n+16){display:none}
body.brief .dt td,body.brief .dt th{padding:4px 8px;font-size:.92rem}body.brief a{color:inherit;text-decoration:none}
.b2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.b2 h3{margin-top:0}
.bsrc ul{margin:4px 0 8px;padding-left:1.2em}.bsrc li{margin-bottom:5px}.bsrc p{margin:0;color:#2F4A52}
'''


# Share image (1200x630), rendered by scripts/world_og.py
OG_CSS = '''
html,body{margin:0;background:#0C2530}
.og{width:1200px;height:630px;box-sizing:border-box;padding:56px 64px;background:linear-gradient(135deg,#0C2530 0%,#0F3B44 100%);color:#EAF2F1;font-family:"IBM Plex Sans",system-ui,sans-serif;display:flex;flex-direction:column;position:relative;overflow:hidden}
.ob{display:flex;align-items:center;gap:12px;font-size:26px}.ob svg{width:38px;height:38px;display:block}.ob b{font-family:Archivo,sans-serif;font-weight:800}.ob i{margin-left:auto;font-style:normal;color:#8FA5A6;font-size:22px}
.of{font-size:84px;line-height:1;margin-top:38px}
.og h1{font-family:Archivo,sans-serif;font-weight:800;font-size:92px;line-height:1;letter-spacing:-.02em;margin:14px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.og .of+h1{font-size:88px}.os{font-size:32px;color:#C3D3D2;margin:14px 0 0}
.og3{display:flex;gap:56px;margin-top:auto;border-top:2px solid rgba(255,255,255,.16);padding-top:26px}
.og3 b{display:block;font-family:Archivo,sans-serif;font-weight:800;font-size:52px;line-height:1.05;white-space:nowrap}.og3 b.x{color:#4CC9C2}.og3 b.m{color:#F08A63}
.og3 span{display:block;font-size:24px;color:#8FA5A6;margin-top:6px}
'''
