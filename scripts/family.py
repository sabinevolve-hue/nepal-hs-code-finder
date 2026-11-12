"""Family view: every tariff line under the same 4-digit heading, with the words that decide between them.

Importers often look for the line with the lowest duty. The code is not a choice, though: it follows from what the
goods are (material, use, size, assembled or not). This module shows the whole heading as a ladder of duty rates and,
for each line, only the part of its description that differs from the reader's line, so the reader sees WHY the
duty differs and which lower-duty line their goods could honestly fall under.

Data: data/tariff.json rows = [code 'dddd.dd.dd', description, [ancestor string ids], unit, SAARC rate,
general rate, page, note]; strs = ancestor texts; heads['dd.dd'] = [heading text, ...]. Nothing is invented: the
deciding words are the tariff's own text.

Used by product_pages.py (static pages). The app (src.html) has its own JS version over t.json.
"""
import html, json, pathlib, re

root = pathlib.Path(__file__).resolve().parents[1]
_T = json.loads((root / 'data' / 'tariff.json').read_text(encoding='utf-8'))
_S = _T.get('strs', [])
HEADS = _T.get('heads', {})
FREE = {'free', 'nil', 'exempt'}

by_heading = {}
for _r in _T['rows']:
    by_heading.setdefault(_r[0][:5], []).append(_r)

CKD_RE = re.compile(r'\b(unassembled|CKD|SKD|semi[- ]knocked|completely knocked|parts? of)\b', re.I)


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def rate(x):
    """-> (number or None, display)."""
    s = str(x).strip()
    if not s:
        return None, '—'
    if s.lower() in FREE:
        return 0.0, 'Free'
    try:
        n = float(s)
        return n, '%g%%' % n
    except ValueError:
        return None, s


def path_of(r):
    return [_S[i] for i in r[2] if 0 <= i < len(_S)] + [r[1]]


def deciding(r, mine):
    """The part of r's description below what it shares with the reader's line."""
    p, m = path_of(r), path_of(mine)
    k = 0
    while k < min(len(p), len(m)) - 1 and p[k] == m[k]:
        k += 1
    rest = p[k:]
    return [('Other (none of the above)' if s.strip().lower() in ('other', 'others') else s) for s in rest]


def heading_text(code):
    h = HEADS.get(code[:2] + '.' + code[2:4])
    return h[0] if h else ''


def family(dotted):
    return by_heading.get(dotted[:5], [])


def render(dotted, href):
    """HTML block for the product page. href(dotted_code) -> link or None."""
    fam = family(dotted)
    if len(fam) < 2:
        return ''
    mine = next((r for r in fam if r[0] == dotted), None)
    if mine is None:
        return ''
    my_g = rate(mine[5])[0]
    nums = [rate(r[5])[0] for r in fam if rate(r[5])[0] is not None]
    lo, hi = (min(nums), max(nums)) if nums else (None, None)
    top = max(hi or 0, 1)

    # group by first ancestor (the subheading), keep tariff order
    groups, order = {}, []
    for r in fam:
        g = path_of(r)[0] if len(path_of(r)) > 1 else ''
        if g not in groups:
            groups[g] = []; order.append(g)
        groups[g].append(r)
    my_group = path_of(mine)[0] if len(path_of(mine)) > 1 else ''
    many = len(fam) > 14

    out = ['<section class="fam" aria-labelledby="fam-h">',
           '<h2 class="sec" id="fam-h">Same family: every line under heading %s</h2>' % esc(dotted[:5].rstrip('.')),
           '<p class="fam-lede"><b>%s</b> — %d lines. The bar is the general customs duty; the text is what decides '
           'between them, in the tariff&rsquo;s own words.</p>' % (esc(heading_text(dotted.replace('.', ''))), len(fam))]
    for g in order:
        rows = groups[g]
        open_ = (not many) or g == my_group
        body = []
        for r in rows:
            gn, gd = rate(r[5]); sn, sd = rate(r[4])
            is_me = r[0] == dotted
            words = path_of(r)[1:] if g else path_of(r)
            text = ' › '.join(('Other (none of the above)' if w.strip().lower() in ('other', 'others') else w) for w in words)
            w = 0 if gn is None else max(1.5, 55.0 * gn / top)
            tone = 'spec' if gn is None else ('free' if gn == 0 else ('low' if gn <= 10 else ('mid' if gn <= 20 else 'hi')))
            badge = ''
            if is_me:
                badge = '<span class="fam-b me">Your line</span>'
            elif gn is not None and gn == lo and lo != hi:
                badge = '<span class="fam-b lo">Lowest in family</span>'
            link = href(r[0]) if not is_me else None
            code_html = ('<a href="%s">%s</a>' % (esc(link), esc(r[0]))) if link else esc(r[0])
            saarc = ('<span class="fam-s">SAFTA %s</span>' % esc(sd)) if sd not in ('—', gd) else ''
            body.append('<li class="fam-r%s"><div class="fam-t"><span class="fam-c">%s</span>%s<span class="fam-d">%s</span></div>'
                        '<div class="fam-bar"><i class="t-%s" style="width:%.1f%%"></i><b>%s</b>%s</div></li>'
                        % (' is-me' if is_me else '', code_html, badge, esc(text), tone, w, esc(gd), saarc))
        label = esc(g) if g else 'Lines in this heading'
        out.append('<details class="fam-g"%s><summary>%s <span>%d line%s</span></summary><ul>%s</ul></details>'
                   % (' open' if open_ else '', label, len(rows), '' if len(rows) == 1 else 's', ''.join(body)))

    # honest ways to pay less
    tips = []
    sn, sd = rate(mine[4])
    if my_g is not None and sn is not None and sn < my_g:
        tips.append('<li><b>Origin:</b> made in India or another SAARC country, with a certificate of origin, this line '
                    'pays <b>%s</b> instead of %s under SAFTA. <a href="/safta">How SAFTA works</a></li>' % (esc(sd), esc(rate(mine[5])[1])))
    if my_g is not None:
        def shared(r):          # how much of the description r shares with the reader's line: closest siblings first
            p, m = path_of(r), path_of(mine); k = 0
            while k < min(len(p), len(m)) and p[k] == m[k]:
                k += 1
            return k
        cheaper = sorted([r for r in fam if r[0] != mine[0] and rate(r[5])[0] is not None and rate(r[5])[0] < my_g],
                         key=lambda r: (-shared(r), rate(r[5])[0]))[:3]
        for r in cheaper:
            tips.append('<li><b>%s at %s</b> applies only if your goods are: <i>%s</i>.</li>'
                        % (esc(r[0]), esc(rate(r[5])[1]), esc(' › '.join(deciding(r, mine)))))
        ckd = [r for r in fam if r[0] != mine[0] and path_of(r)[0] == path_of(mine)[0] and CKD_RE.search(' '.join(path_of(r)))
               and rate(r[5])[0] is not None and rate(r[5])[0] < my_g]
        if ckd and not CKD_RE.search(' '.join(path_of(mine))):
            tips.append('<li><b>Build state:</b> this heading rates unassembled kits or parts lower. That applies only to '
                        'goods that genuinely arrive unassembled.</li>')
    if tips:
        out.append('<div class="fam-pay"><h3>Ways the duty can be lower, and the condition for each</h3><ul>%s</ul>'
                   '<p class="fam-warn">The HS code is set by what the goods are, not chosen. Declaring a lower-duty line '
                   'that does not match the goods leads to reclassification, the duty difference, a fine and possible '
                   'seizure. If you are unsure, ask for an advance ruling from the Department of Customs.</p></div>'
                   % ''.join(tips))
    elif lo is not None and my_g == lo:
        out.append('<p class="fam-ok">This is already the lowest general duty in its family.</p>')
    out.append('</section>')
    return ''.join(out)


CSS = """
/*FAMILY*/
.fam{margin:1.6em 0}.fam-lede{color:var(--fg2);margin:.2em 0 .8em}
.fam-g{background:var(--card);border:1px solid var(--border);border-radius:12px;margin:0 0 8px;overflow:hidden}
.fam-g>summary{cursor:pointer;padding:10px 14px;font-weight:650;list-style:none;display:flex;justify-content:space-between;gap:12px}
.fam-g>summary::-webkit-details-marker{display:none}
.fam-g>summary::after{content:"+";color:var(--muted);font-weight:400}.fam-g[open]>summary::after{content:"\\2212"}
.fam-g>summary span{margin-left:auto;color:var(--muted);font-weight:400;font-size:.85rem;white-space:nowrap}
.fam-g ul{list-style:none;margin:0;padding:0 0 4px}
.fam-r{display:grid;grid-template-columns:minmax(0,1fr) minmax(150px,34%);gap:6px 16px;align-items:center;padding:9px 14px;border-top:1px solid var(--border)}
.fam-r.is-me{background:var(--accent-bg);box-shadow:inset 3px 0 0 var(--accent)}
.fam-t{min-width:0}.fam-c{font-family:var(--mono);font-size:.85rem;margin-right:8px;white-space:nowrap}
.fam-d{display:block;color:var(--fg2);font-size:.9rem;line-height:1.4;overflow-wrap:anywhere}
.fam-b{display:inline-block;font-size:.72rem;font-weight:700;border-radius:999px;padding:1px 8px;vertical-align:1px}
.fam-b.me{background:var(--accent);color:#fff}.fam-b.lo{background:var(--free-bg);color:var(--free)}
.fam-bar{display:flex;align-items:center;gap:8px;font-size:.9rem}
.fam-bar i{display:block;height:10px;border-radius:5px;flex:0 0 auto}
.fam-bar b{white-space:nowrap}.fam-s{color:var(--muted);font-size:.8rem;white-space:nowrap}
.t-free{background:var(--free)}.t-low{background:var(--low)}.t-mid{background:var(--mid)}.t-hi{background:var(--hi)}.t-spec{background:var(--spec)}
.fam-pay{border:1px solid var(--border);border-left:4px solid var(--free);border-radius:12px;padding:12px 16px;margin-top:12px;background:var(--card)}
.fam-pay h3{margin:0 0 6px;font-size:1rem}.fam-pay ul{margin:0;padding-left:1.1em}.fam-pay li{margin:.35em 0}
.fam-warn{margin:.7em 0 0;font-size:.85rem;color:var(--fg2)}.fam-ok{color:var(--free);font-weight:600}
@media(max-width:600px){.fam-r{grid-template-columns:1fr}}
/*/FAMILY*/
"""
