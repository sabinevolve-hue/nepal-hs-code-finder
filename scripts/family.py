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
    """HTML block for the product page: one compact table, lowest duty first. href(dotted_code) -> link or None."""
    fam = family(dotted)
    if len(fam) < 2:
        return ''
    mine = next((r for r in fam if r[0] == dotted), None)
    if mine is None:
        return ''
    my_g = rate(mine[5])[0]
    nums = [rate(r[5])[0] for r in fam if rate(r[5])[0] is not None]
    lo, hi = (min(nums), max(nums)) if nums else (None, None)

    def tone(n):
        return 'spec' if n is None else ('free' if n == 0 else ('low' if n <= 10 else ('mid' if n <= 20 else 'hi')))

    def chip(x):
        n, d = rate(x)
        return '<span class="fam-chip t-%s">%s</span>' % (tone(n), esc(d))

    ranked = sorted(enumerate(fam), key=lambda ir: (rate(ir[1][5])[0] is None, rate(ir[1][5])[0] or 0, ir[0]))
    LIMIT = 10
    rows = []
    for pos, (i, r) in enumerate(ranked):
        is_me = r[0] == dotted
        pth = [('Other (none of the above)' if w.strip().lower() in ('other', 'others') else w) for w in path_of(r)]
        # the deciding words lead; the subheading they sit under follows in small type
        k = 2 if (len(pth) > 2 and len(pth[-1]) < 28) else 1          # a short leaf ("Other", "Upto 48 Inch") needs its parent to make sense
        words = '<b>%s</b>' % esc(' › '.join(pth[-k:])) + (('<small>%s</small>' % esc(' › '.join(pth[:-k]))) if len(pth) > k else '')
        link = href(r[0]) if not is_me else None
        code_html = ('<a href="%s">%s</a>' % (esc(link), esc(r[0]))) if link else esc(r[0])
        tag = '<span class="fam-b me">Your line</span>' if is_me else ''
        hide = ' fam-x' if (len(fam) > LIMIT + 2 and pos >= LIMIT and not is_me) else ''
        rows.append('<tr class="%s%s" data-o="%d" data-d="%d"><td class="fam-c">%s%s</td><td class="fam-d"><span>%s</span></td>'
                    '<td class="fam-n">%s</td><td class="fam-n">%s</td></tr>'
                    % ('is-me' if is_me else '', hide, i, pos, code_html, tag, words, chip(r[5]), chip(r[4])))
    hidden = sum(1 for x in rows if ' fam-x"' in x)

    out = ['<section class="fam" aria-labelledby="fam-h">',
           '<h2 class="sec" id="fam-h">Same family, compared by duty: heading %s</h2>' % esc(dotted[:5].rstrip('.')),
           '<p class="fam-lede">%s. %d lines, lowest customs duty first. The code follows from what the goods are, '
           'so read the description before the rate.</p>' % (esc(heading_text(dotted.replace('.', ''))), len(fam)),
           '<div class="fam-tools" role="group" aria-label="Order"><button type="button" class="on" data-ford="d">Lowest duty first</button>'
           '<button type="button" data-ford="o">Tariff order</button></div>',
           '<div class="fam-wrap"><table class="famt"><thead><tr><th>HS code</th><th>What the goods must be</th>'
           '<th>General</th><th>SAFTA</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(rows)]
    if hidden:
        out.append('<button type="button" class="fam-more">Show all %d lines</button>' % len(fam))
    notes = []
    sn, sd = rate(mine[4])
    if my_g is not None and sn is not None and sn < my_g:
        notes.append('From India or another SAARC country, with a certificate of origin, your line pays <b>%s</b> instead of %s. '
                     '<a href="/safta">How SAFTA works</a>.' % (esc(sd), esc(rate(mine[5])[1])))
    if my_g is not None and lo is not None and my_g == lo:
        notes.append('Your line already has the lowest general duty in its family.')
    notes.append('Declaring a lower-duty line that does not match the goods leads to reclassification, the duty difference and a fine. '
                 'When unsure, ask the Department of Customs for an advance ruling.')
    out.append('<p class="fam-note">%s</p>' % ' '.join(notes))
    out.append('<script>(function(){var s=document.currentScript.parentNode,tb=s.querySelector("tbody");'
               's.addEventListener("click",function(e){var b=e.target.closest("button"),c=e.target.closest(".fam-d");'
               'if(c){c.classList.toggle("open");return}if(!b)return;'
               'if(b.classList.contains("fam-more")){s.classList.add("all");b.remove();return}'
               'var k=b.getAttribute("data-ford");if(!k)return;'
               '[].slice.call(tb.rows).sort(function(a,z){return a.dataset[k]-z.dataset[k]}).forEach(function(r){tb.appendChild(r)});'
               'if(k==="o"){s.classList.add("all");var m=s.querySelector(".fam-more");if(m)m.remove()}'
               '[].forEach.call(s.querySelectorAll("[data-ford]"),function(x){x.classList.toggle("on",x===b)})})})();</script>')
    out.append('</section>')
    return ''.join(out)


CSS = """
/*FAMILY*/
.fam{margin:1.6em 0}.fam-lede{color:var(--fg2);margin:.2em 0 .7em}
.fam-tools{display:inline-flex;border:1px solid var(--border);border-radius:999px;padding:2px;background:var(--card);margin-bottom:8px}
.fam-tools button{border:0;background:none;color:var(--fg2);font:inherit;font-size:.85rem;padding:5px 12px;border-radius:999px;cursor:pointer}
.fam-tools button.on{background:var(--navy);color:var(--bg);font-weight:650}
.fam-wrap{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.famt{width:100%;border-collapse:collapse;font-size:.9rem}
.famt th{text-align:left;font-size:.75rem;font-weight:650;color:var(--muted);padding:8px 12px;border-bottom:1px solid var(--border);white-space:nowrap}
.famt td{padding:8px 12px;border-top:1px solid var(--border);vertical-align:top}
.famt tbody tr:first-child td{border-top:0}
.famt th:nth-child(n+3),.famt .fam-n{text-align:right;white-space:nowrap;width:1%}
.famt .fam-c{font-family:var(--mono);font-size:.84rem;white-space:nowrap;width:1%}
.famt .fam-d{color:var(--fg2);line-height:1.4;cursor:pointer}
.famt .fam-d b{font-weight:600;color:var(--fg);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.famt .fam-d small{color:var(--muted);font-size:.8rem;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.famt .fam-d span{display:block;min-width:0}.famt .fam-d{max-width:0}
.famt .fam-d.open b{display:block}.famt .fam-d.open small{display:block}
.famt tr.is-me td{background:var(--accent-bg)}.famt tr.is-me td:first-child{box-shadow:inset 3px 0 0 var(--accent)}
.fam-b{display:block;width:max-content;font-family:var(--f);font-size:.68rem;font-weight:700;border-radius:999px;padding:1px 7px;margin-top:3px}
.fam-b.me{background:var(--accent);color:#fff}
.fam-chip{display:inline-block;min-width:3.4em;text-align:center;font-weight:700;font-size:.84rem;border-radius:7px;padding:2px 7px}
.fam-chip.t-free{background:var(--free-bg);color:var(--free)}.fam-chip.t-low{background:var(--low-bg);color:var(--low)}
.fam-chip.t-mid{background:var(--mid-bg);color:var(--mid)}.fam-chip.t-hi{background:var(--hi-bg);color:var(--hi)}.fam-chip.t-spec{background:var(--spec-bg);color:var(--spec)}
.fam:not(.all) .fam-x{display:none}
.fam-more{margin-top:8px;border:1px solid var(--border);background:var(--card);color:var(--accent);font:inherit;font-weight:650;border-radius:10px;padding:8px 14px;cursor:pointer}
.fam-note{margin:.8em 0 0;font-size:.85rem;color:var(--fg2)}
@media(max-width:600px){.famt{font-size:.85rem}.famt th,.famt td{padding:7px 8px}
.famt thead th:nth-child(2){display:none}.famt thead th:first-child{}
.famt tr{display:grid;grid-template-columns:minmax(0,1fr) auto auto;column-gap:6px}
.famt thead tr{grid-template-columns:minmax(0,1fr) 4.6em 4.6em}.famt tbody tr{grid-template-columns:minmax(0,1fr) 4.6em 4.6em;border-top:1px solid var(--border)}
.famt tbody tr:first-child{border-top:0}.famt td{border-top:0;width:auto!important}
.famt .fam-c{grid-column:1;grid-row:1;padding-bottom:0;white-space:normal}.famt .fam-b{display:inline-block;margin:0 0 0 6px}
.famt .fam-d{grid-column:1/-1;grid-row:2;padding-top:2px;max-width:none;min-width:0}.famt .fam-n{grid-row:1;text-align:right}.famt th:nth-child(n+3){text-align:right}}
/*/FAMILY*/
"""
