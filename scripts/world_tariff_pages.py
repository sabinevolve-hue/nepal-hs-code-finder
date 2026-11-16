"""Import tariff pages for world.customsnepal.com, from official national schedules (data/world/tariffs/<iso>.json).

  /tariffs              which countries are covered, and why only those
  /tariffs/<country>    one country's schedule: headline figures, the 21 HS sections, a code lookup, the highest duties
  plus a short block on each /hs/code/<code> page with that code's lines in each covered schedule

Rates are shown exactly as the schedule prints them. Averages are this site's own arithmetic over the lines whose
rate is a plain percentage (Free counts as 0); per-unit and compound duties are counted but left out of averages.
The lookup reads one small file per chapter (/data/tariffs/<iso>/<chapter>.json) so no page carries the whole schedule.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLUGS = {'USA': 'united-states', 'GBR': 'united-kingdom', 'EUU': 'european-union'}
# What each schedule's main rate is called, what the page must say it leaves out, and whether lines carry the extra US columns.
PROFILE = {
    'USA': {'rate': 'General rate', 'ext': True,
            'notice': lambda d, e: ('These are the schedule&#39;s <b>general</b> rates, for goods from countries with normal trade relations. '
                                    f'Chapter 99 of the same schedule lists <b>{d.get("n99", 0)}</b> provisions that add duty on top of the general rate, many of them depending on the country of origin or the product; '
                                    'they are not included below. Lower rates under trade agreements and preference programmes are shown in the lookup as the schedule prints them. '
                                    f'<a style="text-decoration:underline" href="{e(d["meta"]["ch99"])}" target="_blank" rel="noopener">See chapter 99 on the official site</a>.'),
            'sub': 'General rate, before anything in chapter 99.'},
    'GBR': {'rate': 'Third-country duty', 'ext': False,
            'notice': lambda d, e: ('These are the UK&#39;s <b>third-country duties</b>, the rate for goods from any country without a better arrangement. '
                                    'Goods from countries with a UK trade agreement, or under the UK&#39;s preference scheme for developing countries, may pay less if they meet the rules of origin. '
                                    'Quotas, anti-dumping and other trade remedy duties can apply to particular goods and origins, and import VAT is charged on top. None of these are included below. '
                                    f'<a style="text-decoration:underline" href="{e(d["meta"]["search"])}" target="_blank" rel="noopener">Check a commodity on the official Trade Tariff</a>.'),
            'sub': 'Third-country duty, before quotas, trade remedies or preferences.'},
    'EUU': {'rate': 'Third-country duty', 'ext': False,
            'notice': lambda d, e: ('These are the EU&#39;s <b>third-country duties</b> from its Common Customs Tariff, charged at the border of all 27 member states. '
                                    'Goods from countries with an EU trade agreement, or under the EU&#39;s preference scheme for developing countries, may pay less if they meet the rules of origin. '
                                    'Quotas, anti-dumping and other measures can apply to particular goods and origins, and import VAT and excise are set by each member state and charged on top. None of these are included below. '
                                    f'<a style="text-decoration:underline" href="{e(d["meta"]["search"])}" target="_blank" rel="noopener">Check a code in TARIC, the EU&#39;s official database</a>. '
                                    'Member states and trade: <a style="text-decoration:underline" href="/trade/bloc/european-union">European Union</a>.'),
            'sub': 'Third-country duty, before quotas, trade remedies or preferences.'},
}
_PCT = re.compile(r'^(\d+(?:\.\d+)?)%$')


def rate(txt):
    """'Free' -> 0.0, '12.5%' -> 12.5, anything else (per-unit, compound, text) -> None."""
    t = (txt or '').strip()
    if t.lower() == 'free':
        return 0.0
    m = _PCT.match(t)
    return float(m.group(1)) if m else None


def fcode(c):
    """US-style dotted code: 61091000 -> 6109.10.00, 0201300200 -> 0201.30.02.00."""
    return '.'.join([c[:4]] + [c[i:i + 2] for i in range(4, len(c), 2)])


def num(x):
    return ('%.1f' % x).rstrip('0').rstrip('.') if x is not None else '–'


class Tariffs:
    def __init__(self, h):
        self.h = h; self.C = {}
        for f in sorted((ROOT / 'data' / 'world' / 'tariffs').glob('*.json')):
            d = json.loads(f.read_text(encoding='utf-8'))
            iso = d['meta']['iso']
            if iso not in SLUGS:
                continue
            d['lines'] = [l for l in d['lines'] if l[0][:2] not in ('98', '99')]     # national special provisions, not goods
            by6 = {}
            for ln in d['lines']:
                by6.setdefault(ln[0][:6], []).append(ln)
            d['by6'] = by6
            self.C[iso] = d

    # ---------- helpers
    def href(self, iso):
        return '/tariffs/' + SLUGS[iso]

    def stats(self, lines):
        r = [rate(l[2]) for l in lines]
        adv = [x for x in r if x is not None]
        return {'n': len(lines), 'free': sum(1 for x in r if x == 0), 'adv': len(adv), 'other': len(r) - len(adv),
                'avg': (sum(adv) / len(adv)) if adv else None, 'max': max(adv) if adv else None}

    def title(self, iso):
        d = self.C[iso]['meta']
        return f'{d["name"]} Import Tariff {_year(d)}: Duty Rates by Product'

    def desc(self, iso):
        m = self.C[iso]['meta']; s = self.stats(self.C[iso]['lines'])
        return (f'Import duty rates of the {m["name"]} for {s["n"]:,} tariff lines, from the official {m["source"]} ({m["edition"]}). '
                f'Look up any HS code; {100 * s["free"] / s["n"]:.0f}% of lines are duty-free.')

    # ---------- pages
    def hub(self):
        h = self.h; e = h['esc']
        rows = []
        for iso, d in self.C.items():
            m = d['meta']; s = self.stats(d['lines'])
            rows.append((f'<a href="{self.href(iso)}">{e(m["name"])}</a>', e(m['edition']), f'{s["n"]:,}', f'{100 * s["free"] / s["n"]:.0f}%', num(s['avg']) + '%'))
        tbl = self._table(['Tariff', 'Schedule edition', 'Tariff lines', 'Duty-free lines', 'Average of percentage rates'], rows, 'Countries covered', 2)
        return h['main']('<div class="ph"><h1 class="h2">Import tariffs, from the official schedules</h1>'
                         '<p>What each country charges at the border, product by product, taken from the schedule the country itself publishes. '
                         'Only schedules whose publisher allows them to be republished are shown, so the list starts small.</p></div>'
                         f'<section class="gsec"><h2>Schedules covered</h2>{tbl}</section>'
                         '<section class="gsec"><h2>Why not every country yet</h2>'
                         '<p>The global tariff databases kept by the WTO and its partners may be used freely only for non-commercial purposes, and republishing them needs the WTO&#39;s permission. '
                         'This site therefore adds countries one at a time from their own official tariff, where the licence allows it. '
                         'For any other country, the <a href="https://www.wto.org/english/res_e/publications_e/world_tariff_profiles25_e.htm" target="_blank" rel="noopener">World Tariff Profiles</a> '
                         'published by the WTO, ITC and UNCTAD give each country&#39;s average duties by product group.</p></section>'
                         '<section class="gsec"><h2>How to read a tariff</h2>'
                         '<p>A schedule gives the normal duty for each product. What a shipment actually pays can differ: trade agreements and preference programmes lower it, '
                         'some countries add duties by country of origin or for trade remedies, and sales taxes such as VAT are charged on top. '
                         'Each country page says what its schedule leaves out. Confirm the rate with the customs authority or a licensed broker before you ship.</p></section>')

    def country(self, iso):
        h = self.h; e = h['esc']; d = self.C[iso]; m = d['meta']; lines = d['lines']; s = self.stats(lines)
        CH = h['CH']; SEC = h['SEC']
        secs = {}
        for l in lines:
            sec = (CH.get(l[0][:2]) or ['', '', ''])[2]
            secs.setdefault(sec, []).append(l)
        srows = []
        for sec in sorted(secs, key=lambda x: _roman(x)):
            st = self.stats(secs[sec])
            srows.append((f'<b>{e(sec)}</b> {e((SEC.get(sec) or ["", ""])[1])}', f'{st["n"]:,}', f'{100 * st["free"] / st["n"]:.0f}%',
                          num(st['avg']) + ('%' if st['avg'] is not None else ''), num(st['max']) + ('%' if st['max'] is not None else ''), f'{st["other"]:,}'))
        top = sorted((l for l in lines if rate(l[2])), key=lambda l: -rate(l[2]))[:15]
        trows = [(f'<a class="pl" href="#hs={l[0]}">{fcode(l[0])}</a>', e(_short(l[1])), e(l[2])) for l in top]
        P = PROFILE[iso]
        notice = '<div class="outcome">' + h['ic']('info') + '<div><b>Not the whole bill.</b> ' + P['notice'](d, e) + '</div></div>'
        look = ('<section class="gsec" id="look"><h2>Look up a product</h2>'
                '<form class="tfl" id="tfform" role="search" aria-label="Look up an HS code in this tariff">'
                '<label for="tfin" class="gk">HS code, 4 to 10 digits</label><div class="tfrow">'
                '<input id="tfin" type="search" inputmode="numeric" autocomplete="off" placeholder="for example 8703 or 6109.10" aria-describedby="tfhelp">'
                '<button type="submit">Show rates</button></div>'
                '<p class="fine" id="tfhelp">Don&#39;t know the code? <a href="/hs">Search products by name</a>.</p></form>'
                '<div id="tfout" aria-live="polite"></div></section>')
        body = (h['back']('/tariffs', 'Import tariffs') + f'<div class="ph"><h1 class="h2">{e(m["name"])} import tariff</h1>'
                f'<p>The official <b>{e(m["source"])}</b>, {e(m["edition"])}' + (f', in force from {e(_date(m["release"]))}' if iso == 'USA' else '') + '.</p></div>'
                f'<div class="statrow" style="margin-top:0"><div class="s"><b>{s["n"]:,}</b><span>Tariff lines with a rate</span></div>'
                f'<div class="s"><b>{100 * s["free"] / s["n"]:.0f}%</b><span>Duty-free lines</span></div>'
                f'<div class="s"><b>{num(s["avg"])}%</b><span>Average of percentage rates</span></div>'
                f'<div class="s"><b>{s["other"]:,}</b><span>Lines charged per unit or mixed</span></div></div>'
                + notice + look
                + '<section class="gsec"><h2>Duty by product section</h2><p class="gk">The 21 sections of the Harmonized System. Averages count Free as 0 and leave out per-unit and mixed duties.</p>'
                + self._table(['Section', 'Lines', 'Duty-free', 'Average %', 'Highest %', 'Per-unit or mixed'], srows, 'Duty by product section') + '</section>'
                + '<section class="gsec"><h2>Highest percentage duties</h2>'
                + f'<p class="gk">{P["sub"]}</p>'
                + self._table(['Code', 'Product', P['rate']], trows, 'Highest percentage duties', 2) + '</section>')
        body += h['src_box']('Source', f'<p><b>{e(m["publisher"])}</b>, {e(m["source"])}, {e(m["edition"])} (<a href="{e(m["file"])}" target="_blank" rel="noopener">{"data file" if m["file"].endswith(".json") else "official service"}</a>), read on {e(_date(m["read"]))}. '
                             f'{e(m["licence"])}. Averages and counts are this site&#39;s arithmetic. The <a href="{e(m["search"])}" target="_blank" rel="noopener">official search</a> is the authority; '
                             'a binding classification comes only from the customs authority.</p>', m['read'][:4])
        body += self._script(iso)
        return h['main'](body)

    def code_block(self, code):
        """Short block for /hs/code/<code>: the code's lines in each covered schedule."""
        h = self.h; e = h['esc']; out = []
        for iso, d in self.C.items():
            ls = d['by6'].get(code)
            if not ls:
                continue
            rows = ''.join(f'<tr><td>{fcode(l[0])}</td><td>{e(_short(l[1], 1))}</td><td class=r>{e(l[2])}</td></tr>' for l in ls[:6])
            more = f'<p class="fine">{len(ls) - 6} more lines in the full schedule.</p>' if len(ls) > 6 else ''
            out.append(f'<h3 class="h">Import duty in the {e(d["meta"]["name"])}</h3>'
                       f'<div class="dscroll" tabindex="0" role="region" aria-label="{e(d["meta"]["name"])} tariff lines for this code"><table class="dt"><thead><tr><th>National code</th><th>Description</th><th class=r>{PROFILE[iso]["rate"]}</th></tr></thead><tbody>{rows}</tbody></table></div>{more}'
                       f'<p class="fine">{e(d["meta"]["source"])}, {e(d["meta"]["edition"])}. {PROFILE[iso]["rate"]} only; extra duties by origin and lower rates under agreements are not shown here. '
                       f'<a href="{self.href(iso)}#hs={code}">All rates and notes for this code</a></p>')
        return ''.join(out)

    def write_lookup(self, outdir):
        """One JSON file per chapter: [[code, description path, general, special, column 2, notes], ...]."""
        for iso, d in self.C.items():
            dd = outdir / iso.lower(); dd.mkdir(parents=True, exist_ok=True)
            ch = {}
            for l in d['lines']:
                ch.setdefault(l[0][:2], []).append(l)
            for c, ls in ch.items():
                (dd / f'{c}.json').write_text(json.dumps(ls, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # ---------- small pieces
    def _table(self, heads, rows, label='Table', left=1):
        """Columns before `left` are left-aligned text; the rest are right-aligned figures."""
        th = ''.join(f'<th{" class=r" if i >= left else ""}>{x}</th>' for i, x in enumerate(heads))
        tr = ''.join('<tr>' + ''.join(f'<td{" class=r" if i >= left else ""}>{x}</td>' for i, x in enumerate(r)) + '</tr>' for r in rows)
        return f'<div class="dscroll" tabindex="0" role="region" aria-label="{label}, scrolls sideways on small screens"><table class="dt"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'

    def _script(self, iso):
        P = PROFILE[iso]; ext = P['ext']
        cols = ('<th>Lower rates under agreements and programmes</th><th class=r>Column 2</th>' if ext else '')
        cells = ('+"<td class=\\"tfn\\">"+esc(l[3]||"–")+"</td><td class=r>"+esc(l[4]||"–")+"</td>"' if ext else '')
        foot = ('Column 2 applies only to the countries named in general note 3(b) of the schedule. Letters in the agreements column are the schedule&#39;s own programme codes, explained in its general notes.' if ext
                else 'Rates as printed by the official service. Where a line shows two rates joined by &#34;or&#34;, the schedule sets more than one rate for that code; check the official entry.')
        return ('<style>.tfl{margin:0 0 10px}.tfrow{display:flex;gap:8px;flex-wrap:wrap}.tfrow input{flex:1 1 220px;min-width:0;height:46px;padding:0 12px;border:1.5px solid var(--border);border-radius:10px;background:var(--card);color:var(--fg);font-size:1rem}'
                '.tfrow button{height:46px;padding:0 18px;border:0;border-radius:10px;background:var(--accent);color:#fff;font-weight:700;font-size:.95rem;cursor:pointer}'
                '.tfc{font-family:var(--mono,monospace);white-space:nowrap}.tfd small{display:block;color:var(--muted)}.tfn{font-size:.8rem;color:var(--muted)}</style>'
                '<script>(function(){var f=document.getElementById("tfform"),i=document.getElementById("tfin"),o=document.getElementById("tfout"),cache={};'
                'function esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}'
                'function fc(c){var p=[c.slice(0,4)];for(var k=4;k<c.length;k+=2)p.push(c.slice(k,k+2));return p.join(".");}'
                'function show(raw){var c=String(raw||"").replace(/[^0-9]/g,"");if(!c){o.innerHTML="";return;}'
                'if(c.length<4){o.innerHTML="<p class=\\"fine\\">Enter at least four digits.</p>";return;}'
                'var ch=c.slice(0,2);o.innerHTML="<p class=\\"fine\\">Loading chapter "+esc(ch)+"…</p>";'
                'var go=function(ls){var m=ls.filter(function(l){return l[0].indexOf(c)===0;});'
                'if(!m.length){o.innerHTML="<p>No tariff line starts with "+esc(fc(c))+". Try fewer digits.</p>";return;}'
                'var h="<p class=\\"gk\\">"+m.length+" line"+(m.length>1?"s":"")+" for "+esc(fc(c))+(m.length>80?", first 80 shown":"")+"</p><div class=\\"dscroll\\" tabindex=\\"0\\" role=\\"region\\" aria-label=\\"Matching tariff lines\\"><table class=\\"dt\\"><thead><tr><th>Code</th><th>Product</th><th class=r>' + P['rate'] + '</th>' + cols.replace('"', '\\"') + '</tr></thead><tbody>";'
                'm.slice(0,80).forEach(function(l){var p=l[1].split(" › "),last=p.pop();h+="<tr><td class=\\"tfc\\">"+esc(fc(l[0]))+"</td><td class=\\"tfd\\">"+esc(last)+(p.length?"<small>"+esc(p.join(" › "))+"</small>":"")'
                '+(l[5]&&l[5].length?"<small>Note: "+esc(l[5].join(" "))+"</small>":"")+"</td><td class=r>"+esc(l[2])+"</td>"' + cells + '+"</tr>";});'
                'o.innerHTML=h+"</tbody></table></div><p class=\\"fine\\">' + foot + '</p>";'
                'if(window.gtag){try{gtag("event","tariff_lookup",{country:"' + iso + '"});}catch(e){}}};'
                'if(cache[ch])return go(cache[ch]);'
                'fetch("/data/tariffs/' + iso.lower() + '/"+ch+".json").then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(ls){cache[ch]=ls;go(ls);})'
                '.catch(function(){o.innerHTML="<p>There is no chapter "+esc(ch)+" in this schedule, or it could not be loaded. Check the code and try again.</p>";});}'
                'f.addEventListener("submit",function(ev){ev.preventDefault();show(i.value);try{history.replaceState(null,"","#hs="+i.value.replace(/[^0-9]/g,""));}catch(e){}});'
                'function fromHash(){var m=/^#hs=(\\d{4,10})$/.exec(location.hash);if(m){i.value=m[1];show(m[1]);document.getElementById("look").scrollIntoView();}}'
                'window.addEventListener("hashchange",fromHash);fromHash();})();</script>')


def _year(m):
    """Year of the schedule: from the US edition title, otherwise the day it was read."""
    y = re.search(r'(20\d\d)', m.get('edition', ''))
    return y.group(1) if y else m['read'][:4]


def _short(path, keep=2):
    """Heading (cut) plus the last parts of the description path, so 'Other › Other' still says what the product is."""
    p = path.split(' › ')
    if len(p) <= keep:
        return ' › '.join(p)
    head = p[0] if len(p[0]) <= 60 else p[0][:57].rsplit(' ', 1)[0] + '…'
    return ' › '.join([head] + p[-keep:])


def _date(s):
    import datetime
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            d = datetime.datetime.strptime(s, fmt)
            return f'{d.day} {d:%B %Y}'
        except (ValueError, TypeError):
            pass
    return s or ''


def _roman(r):
    v = {'I': 1, 'V': 5, 'X': 10, 'L': 50}; t = 0
    for i, ch in enumerate(r or ''):
        n = v.get(ch, 0)
        t += -n if i + 1 < len(r) and v.get(r[i + 1], 0) > n else n
    return t
