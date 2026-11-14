"""Deep country profiles, country-pair pages and the South Asia hub for world.customsnepal.com.

Rendered by scripts/world_prerender.py from data/world/deep.json (built by scripts/world_bilateral.py from BACI).
These pages are static: they ship without the SPA script, so what a crawler sees is exactly what a person sees.

Every number is a BACI figure or a ratio of two BACI figures. Sentences state what the data shows; none explains why.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODC_FILE = ROOT / 'data' / 'world' / 'prodc.json'
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
        self._pc_keys = sorted(self.PC); self._pc_set = set(self.PC); self._pc_by_country = {}
        for k in sorted(self.PC, key=lambda k: -self.PC[k]['v']):
            self._pc_by_country.setdefault(k.split('-')[0], []).append(k.split('-')[1])

    # ---------- small helpers
    def usd(self, vk):
        return self.h['money'](vk * 1000.0)

    def name(self, iso):
        c = self.h['CBYISO'].get(iso)
        if c:
            return c['name']
        n = (self.C.get(iso) or {}).get('n') or iso
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
        return f'<a href="{self.h["code_href"](code)}">{e(self.h["clip"](self.h["hs_desc"](code), n))}</a> <small class="hsc">{self.h["fmt_code"](code)}</small>'

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
        return f'<div class="dscroll"><table class="dt {cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'

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
        if iso in shapes:
            out.append(f'<use href="/assets/worldmap.svg#{iso}" class="me"><title>{e(self.name(iso))}</title></use>')
        return f'<svg viewBox="0 60 960 400" role="img" aria-label="World map shaded by share of {e(self.name(iso))}&#39;s {verb}">{"".join(out)}</svg>'

    def map_block(self, iso, d):
        nm = self.h['esc'](self.name(iso)); k = iso.lower()
        legend = ('<div class="mlg"><span><i class="me"></i>' + nm + '</span>' + ''.join(f'<span><i class="m{c}"></i>{lab}</span>' for _, c, lab in self.MAP_BINS)
                  + '<span><i class="m0"></i>Under 0.1% or none</span></div>')
        return (f'<div class="gmap"><input type="radio" name="gm-{k}" id="gmx-{k}" checked><input type="radio" name="gm-{k}" id="gmm-{k}">'
                f'<div class="gtabs" role="group" aria-label="Map shows"><label for="gmx-{k}">Export markets</label><label for="gmm-{k}">Import suppliers</label></div>'
                f'<div class="gm gmx">{self._map(iso, d["xp"], d["x"], "exports")}</div><div class="gm gmm">{self._map(iso, d["mp"], d["m"], "imports")}</div>'
                f'{legend}<p class="fine">Shade shows each partner&#39;s share of {nm}&#39;s exports or imports. Hover or tap a country for the figure; every partner is in the table further down.</p></div>')

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
        return (f'<div class="tm {tone}" role="img" aria-label="{e(who)} {verb} by product group, area in proportion to value">{"".join(cells)}</div>'
                f'<details class="tml"><summary>The same figures as a list</summary><ol>{lst}</ol></details>')

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
        sec_x = (f'<section class="gsec"><h2>What {nm} sells, and to whom</h2><p class="gk">{nm} exported {self.usd(X)} of goods to {len(xp)} markets in {Y}. '
                 + (f'{e(xg[0][0])} is the largest product group at {self.share(xg[0][1], X, 0)} of exports. ' if xg else '') + conc(xp, X, 'markets') + '</p>'
                 + ('<h3>Exports by product group</h3>' + self.treemap(d.get('xc') or [], X, 'exp', c['name'], 'exports') if xg else '')
                 + f'<h3>Top {min(10, len(xp))} export markets</h3>' + self.barlist(partner_rows(xp, X, 10), 'var(--exp)') + '</section>')
        sec_m = (f'<section class="gsec"><h2>What {nm} buys, and from whom</h2><p class="gk">{nm} imported {self.usd(M)} of goods from {len(mp)} suppliers in {Y}. '
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
                         + lead + tiles + self.glance(X, M)
                         + (self.nepal_official() + '<p class="fine">More on Nepal: <a href="/nepal/exports">export explorer by market</a> and <a href="/nepal">world prices against what Nepal pays</a>.</p>' if iso == 'NPL' else '')
                         + self.map_block(iso, d) + sec_x + sec_m + sec_bal + sec_time + prod_sec + sec_pairs + sec_all + peers + src)

    def peers(self, c):
        known = self.h['CBYISO']
        if not c.get('region'):
            return ''
        ps = sorted((x for x in known.values() if x['iso'] != c['iso'] and x.get('region') == c.get('region') and x['iso'] in self.C),
                    key=lambda x: abs(self.C[x['iso']]['x'] - self.C[c['iso']]['x']))[:8]
        if not ps:
            return ''
        return (f'<h2 class="h">Other economies in {self.h["esc"](c["region"])}</h2><div class="pairgrid">'
                + ''.join(f'<a href="/trade/{x["iso"].lower()}">{x["flag"]} {self.h["esc"](x["name"])} <small>{self.usd(self.C[x["iso"]]["x"])}</small></a>' for x in ps) + '</div>')

    # ---------- pairs
    def pair_keys(self):
        return self._pair_keys

    def pair_title(self, a, b):
        return f'{self.name(a)}–{self.name(b)} Trade {self.Y}: What Each Sells the Other'

    def pair_desc(self, a, b):
        p = self.P[a + '-' + b]
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
        sec_ab = f'<h2 class="h">What {A} sells to {B}</h2>' + prods(p['abk'], ab, p['nab'], A, B)
        sec_ba = f'<h2 class="h">What {B} sells to {A}</h2>' + prods(p['bak'], ba, p['nba'], B, A)
        hist = p.get('hist') or {}
        hrows = [(y, self.usd(v[0]), self.usd(v[1]), self.usd(v[0] + v[1])) for y, v in sorted(hist.items(), reverse=True)]
        sec_hist = '<h2 class="h">Recent years</h2>' + self.table(['Year', f'{A} → {B}', f'{B} → {A}', 'Total'], hrows)
        more = lambda x, other: ''.join(f'<a href="{self.pair_href(x, q)}">{self.flag(x)} {e(self.name(x))} – {self.flag(q)} {e(self.name(q))}</a>'
                                        for q in [q for q in self.pairs_of.get(x, []) if q != other][:10])
        others = (f'<h2 class="h">More pairs</h2><div class="pairgrid">{more(a, b)}{more(b, a)}</div>')
        profiles = (f'<div class="two"><a class="nepalcard" href="/trade/{a.lower()}"><span class="fl">{fa}</span><span><b>{A}: full trade profile</b> {h["ic"]("right")}</span></a>'
                    f'<a class="nepalcard" href="/trade/{b.lower()}"><span class="fl">{fb}</span><span><b>{B}: full trade profile</b> {h["ic"]("right")}</span></a></div>')
        src = h['src_box']('Source', f'<p><b>BACI</b> (CEPII), reconciled from what both countries reported to <b>UN Comtrade</b>, 6-digit HS, current US dollars. '
                           f'BACI gives one agreed figure for each flow, so it can differ from either country&#39;s own national statistics.</p>', str(Y))
        npl = self.nepal_official(b if a == 'NPL' else a) if 'NPL' in (a, b) else ''
        return h['main'](h['back']('/trade/pairs', 'Country pairs') + f'<div class="ph"><h1 class="h2">{fa} {A} – {fb} {B} trade, {Y}</h1></div>'
                         + lead + tiles + scale + ctx + npl + sec_ab + sec_ba + sec_hist + profiles + others + src)

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
        sec_b = (f'<h2 class="h">Who buys it: top {len(brow)} markets</h2>' + self.barlist(brow, 'var(--exp)')
                 + f'<p class="fine">{nm} sold this product to {p["nb"]} countries. The top three took {self.share(top3, v, 0)}.</p>') if brow else ''
        wt = self.WTOP.get(code) or []
        wrows = []
        for i, (c, x) in enumerate(wt, 1):
            href = self.pc_href(c, code)
            lab = self.clink(c) if not href else f'<a href="{href}">{self.flag(c)} {e(self.name(c))}</a>'
            if c == iso:
                lab = f'<b>{self.flag(c)} {e(self.name(c))}</b>'
            wrows.append((lab, self.usd(x), self.share(x, p['w']), f'<span class="rk{i}">#{i}</span>' if i <= 3 else f'#{i}'))
        if iso not in [c for c, _ in wt]:
            wrows.append((f'<b>{fl} {nm}</b>', self.usd(v), f'{p["s"]:.1f}%', f'#{p["r"]}'))
        sec_w = (f'<h2 class="h">The largest exporters of this product</h2>' + self.table(['Exporter', 'Exports', 'World share', 'Rank'], wrows)) if wrows else ''
        hist = dict(p.get('hist') or {}); hist[str(Y)] = v
        hrows = [(y, self.usd(x) if x else '—') for y, x in sorted(hist.items(), reverse=True)]
        sec_h = '<h2 class="h">Recent years</h2>' + self.table(['Year', f'{nm} exports'], hrows)
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
:root{--fg2:var(--fg-2);--navy:var(--hero1);--mono:var(--f-mono);--f:var(--f-body);--f-head:"Archivo",var(--f-body)}
.wrap,.bar .wrap{max-width:1060px}.nav.topnav{margin-left:auto;overflow:visible}
.bar{background:var(--hero1)}
.logo{font-family:var(--f-head);font-size:1.06rem;letter-spacing:-.01em}.logo .mk{background:none;width:28px;height:28px;border-radius:0}
.logo .mk svg{width:28px;height:28px;display:block}
.gnm.cur>summary,.gnm:has([aria-selected="true"])>summary{box-shadow:inset 0 -2px 0 #4CC9C2}
footer.sf{background:linear-gradient(180deg,#0C2530,#071A21)}
footer.sf .sf-logo{font-family:var(--f-head)}footer.sf .sf-logo .mark{display:grid;place-items:center;width:30px;height:30px;background:none}
footer.sf .sf-logo .mark svg{width:28px;height:28px}
footer.sf .sf-track button{background:#0E8583}footer.sf a:hover{color:#8FE3DD}
h1,h1.h2,h2.h,.statrow .s b,.ph h1,.wcol h2,.wstrip h2{font-family:var(--f-head);letter-spacing:-.015em}
h1.h2{font-size:clamp(1.6rem,3.4vw,2.2rem);line-height:1.1;font-weight:800}
table.bk td:last-child{white-space:normal}table.bk td:first-child{padding-right:14px}

.whero{background:var(--bg);border-bottom:1px solid var(--border)}
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
.tc b{font-size:.84rem;line-height:1.15;font-weight:700}.tc i{font-style:normal;font-family:var(--f-head);font-weight:800;font-size:1.5rem;line-height:1.05}.tc em{font-style:normal;font-size:.76rem;opacity:.9}
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
.gsec>p.gk{color:var(--fg-2);margin:0 0 10px;max-width:68ch}.gsec h3{font-size:1rem;margin:22px 0 4px}
@media(max-width:700px){.tm{aspect-ratio:4/5}.tc.md b{font-size:.68rem;overflow-wrap:anywhere}.tc.lg b{overflow-wrap:anywhere}.tc span{padding:5px 6px}.dvr{grid-template-columns:minmax(0,7em) minmax(0,1fr) 4.6em}.glr{grid-template-columns:4.2em minmax(0,1fr) 4.6em}}
@media(max-width:820px){.wcols{grid-template-columns:minmax(0,1fr);gap:22px}.wcol>p{min-height:0}.ws{height:64px}.ws-s,.ws-s.sm{padding:0}.ws-s b,.ws-s i,.ws-s span{display:none}.wsl{display:block}}
@media(max-width:720px){body{padding-bottom:calc(64px + env(safe-area-inset-bottom,0px))}.wsearch button{padding:0 14px}}
'''
