"""Deep country profiles, country-pair pages and the South Asia hub for world.customsnepal.com.

Rendered by scripts/world_prerender.py from data/world/deep.json (built by scripts/world_bilateral.py from BACI).
These pages are static: they ship without the SPA script, so what a crawler sees is exactly what a person sees.

Every number is a BACI figure or a ratio of two BACI figures. Sentences state what the data shows; none explains why.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
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

        sec_x = f'<h2 class="h">Where {nm} exports: top {min(15, len(xp))} markets</h2>' + self.barlist(partner_rows(xp, X), 'var(--exp)')
        sec_m = f'<h2 class="h">Where {nm} imports from: top {min(15, len(mp))} suppliers</h2>' + self.barlist(partner_rows(mp, M), 'var(--imp)')

        # surpluses and deficits by partner
        allp = {}
        for p, v in xp:
            allp.setdefault(p, [0, 0])[0] = v
        for p, v in mp:
            allp.setdefault(p, [0, 0])[1] = v
        bals = sorted(((p, a - b) for p, (a, b) in allp.items()), key=lambda kv: kv[1])
        sur = [x for x in bals[::-1] if x[1] > 0][:5]; dfc = [x for x in bals if x[1] < 0][:5]
        sec_bal = ''
        if sur or dfc:
            f = lambda lst, sign: ''.join(f'<li>{self.clink(p)} <b>{sign}{self.usd(abs(v))[1:]}</b></li>' for p, v in lst) or '<li>None</li>'
            sec_bal = (f'<h2 class="h">Largest surpluses and deficits</h2><div class="two"><div class="card"><b>Surplus with</b><ul class="pl2">{f(sur, "+")}</ul></div>'
                       f'<div class="card"><b>Deficit with</b><ul class="pl2">{f(dfc, "−")}</ul></div></div>')

        # products
        def badge(r, s):
            return f' <span class="rk{r}">#{r} in world · {s}%</span>' if r else ''
        xrows = [(self.prod(k), self.usd(v), self.share(v, X), self.clink(tp) + f' <small>{self.share(tv, v, 0)}</small>', f'{ws}%' + (f' <span class="rk{r}">#{r}</span>' if r else ''))
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

        prs = sorted(self.pairs_of.get(iso, []), key=lambda p: -(self.P['-'.join(sorted([iso, p]))]['ab'] + self.P['-'.join(sorted([iso, p]))]['ba']))
        sec_pairs = ''
        if prs:
            sec_pairs = (f'<h2 class="h">{nm} and its partners, pair by pair</h2><div class="pairgrid">'
                         + ''.join(f'<a href="{self.pair_href(iso, p)}">{self.flag(iso)} {nm} – {self.flag(p)} {e(self.name(p))}</a>' for p in prs) + '</div>')
        src = h['src_box']('Sources', f'<p>Partners, products and {Y} totals from <b>BACI</b> (CEPII), which reconciles what exporters and importers each reported to '
                           f'<b>UN Comtrade</b>, at the 6-digit HS level, in current US dollars. The longer trend chart is the <b>World Bank</b> merchandise trade series, '
                           f'which can differ slightly from BACI for the same year. '
                           f'<a href="https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37" target="_blank" rel="noopener">About BACI ↗</a></p>', str(Y))
        peers = self.peers(c)
        return h['main'](h['back']('/trade', 'Global trade') + f'<div class="ph"><h1 class="h2">{c["flag"]} {nm}: trade in {Y}</h1><p>{rk}</p></div>'
                         + lead + tiles + sec_x + sec_m + sec_bal + sec_xk + sec_mk + sec_lead + sec_dep + sec_hist + long_trend + sec_pairs + sec_all + peers + src)

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
        known = self.h['CBYISO']
        return [k for k in sorted(self.P) if all(x in known for x in k.split('-'))]

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
                                        for q in sorted(self.pairs_of.get(x, []), key=lambda q: -(self.P["-".join(sorted([x, q]))]["ab"] + self.P["-".join(sorted([x, q]))]["ba"])) if q != other)[:99999]
        others = (f'<h2 class="h">More pairs</h2><div class="pairgrid">{more(a, b)}{more(b, a)}</div>')
        profiles = (f'<div class="two"><a class="nepalcard" href="/trade/{a.lower()}"><span class="fl">{fa}</span><span><b>{A}: full trade profile</b> {h["ic"]("right")}</span></a>'
                    f'<a class="nepalcard" href="/trade/{b.lower()}"><span class="fl">{fb}</span><span><b>{B}: full trade profile</b> {h["ic"]("right")}</span></a></div>')
        src = h['src_box']('Source', f'<p><b>BACI</b> (CEPII), reconciled from what both countries reported to <b>UN Comtrade</b>, 6-digit HS, current US dollars. '
                           f'BACI gives one agreed figure for each flow, so it can differ from either country&#39;s own national statistics.</p>', str(Y))
        return h['main'](h['back']('/trade', 'Global trade') + f'<div class="ph"><h1 class="h2">{fa} {A} – {fb} {B} trade, {Y}</h1></div>'
                         + lead + tiles + scale + ctx + sec_ab + sec_ba + sec_hist + profiles + others + src)

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
