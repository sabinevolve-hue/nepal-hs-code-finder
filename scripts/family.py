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
    """HTML block for the product page: duty staircase, compact table (lowest duty first), closest cheaper lines."""
    fam = family(dotted)
    if len(fam) < 2:
        return ''
    mine = next((r for r in fam if r[0] == dotted), None)
    if mine is None:
        return ''
    my_g, my_d = rate(mine[5])
    nums = [rate(r[5])[0] for r in fam if rate(r[5])[0] is not None]
    lo, hi = (min(nums), max(nums)) if nums else (None, None)

    def tone(n):
        return 'spec' if n is None else ('free' if n == 0 else ('low' if n <= 10 else ('mid' if n <= 20 else 'hi')))

    def chip(x):
        n, d = rate(x)
        return '<span class="fam-chip t-%s">%s</span>' % (tone(n), esc(d))

    def key(r):                       # filter key shared by a step and its rows
        n, d = rate(r[5])
        return ('%g' % n) if n is not None else 'spec'

    def words_of(r):
        return [('Other (none of the above)' if w.strip().lower() in ('other', 'others') else w) for w in path_of(r)]

    out = ['<section class="fam" aria-labelledby="fam-h">',
           '<h2 class="sec" id="fam-h">Same family, compared by duty: heading %s</h2>' % esc(dotted[:5].rstrip('.')),
           '<p class="fam-lede">%s. %d lines. The code follows from what the goods are, so read the description before the rate.</p>'
           % (esc(heading_text(dotted.replace('.', ''))), len(fam))]

    # 1. the duty staircase: one step per rate in the family, the reader's step marked; a step filters the table
    steps = {}
    for r in fam:
        steps.setdefault(key(r), []).append(r)
    order = sorted(steps, key=lambda k: (k == 'spec', float(k) if k != 'spec' else 0))
    if len(order) > 1:
        top = max(hi or 0, 1)
        s = []
        for k in order:
            n = None if k == 'spec' else float(k)
            me = key(mine) == k
            hgt = 34 if n is None else 34 + round(74 * n / top)
            cnt = len(steps[k])
            s.append('<button type="button" class="fam-step t-%s%s" data-step="%s" style="height:%dpx" aria-pressed="false" '
                     'aria-label="%s duty: %d line%s%s">%s<b>%s</b><small>%d line%s</small></button>'
                     % (tone(n), ' is-me' if me else '', k, hgt, 'Per-unit' if n is None else rate(steps[k][0][5])[1], cnt,
                        '' if cnt == 1 else 's', ', includes your line' if me else '',
                        '<em>Your line</em>' if me else '', 'Per unit' if n is None else esc(rate(steps[k][0][5])[1]), cnt, '' if cnt == 1 else 's'))
        out.append('<div class="fam-stairs" role="group" aria-label="Duty rates in this family">%s</div>'
                   '<p class="fam-hint">Each step is a duty rate in this family. Tap a step to see only its lines.</p>' % ''.join(s))
    else:
        out.append('<p class="fam-same">Every line in this family pays the same general duty: <b>%s</b>.</p>' % esc(my_d))

    # 2. the table
    ranked = sorted(enumerate(fam), key=lambda ir: (rate(ir[1][5])[0] is None, rate(ir[1][5])[0] or 0, ir[0]))
    LIMIT = 10
    rows = []
    for pos, (i, r) in enumerate(ranked):
        is_me = r[0] == dotted
        pth = words_of(r)
        k = 2 if (len(pth) > 2 and len(pth[-1]) < 28) else 1          # a short leaf ("Other", "Upto 48 Inch") needs its parent to make sense
        words = '<b>%s</b>' % esc(' › '.join(pth[-k:])) + (('<small>%s</small>' % esc(' › '.join(pth[:-k]))) if len(pth) > k else '')
        link = href(r[0]) if not is_me else None
        code_html = ('<a href="%s">%s</a>' % (esc(link), esc(r[0]))) if link else esc(r[0])
        tag = '<span class="fam-b me">Your line</span>' if is_me else ''
        hide = ' fam-x' if (len(fam) > LIMIT + 2 and pos >= LIMIT and not is_me) else ''
        rows.append('<tr class="%s%s" data-o="%d" data-d="%d" data-r="%s"><td class="fam-c">%s%s</td><td class="fam-d"><span>%s</span></td>'
                    '<td class="fam-n">%s</td><td class="fam-n">%s</td></tr>'
                    % ('is-me' if is_me else '', hide, i, pos, key(r), code_html, tag, words, chip(r[5]), chip(r[4])))
    hidden = sum(1 for x in rows if ' fam-x"' in x)
    out.append('<div class="fam-tools" role="group" aria-label="Order"><button type="button" class="on" data-ford="d">Lowest duty first</button>'
               '<button type="button" data-ford="o">Tariff order</button></div>'
               '<div class="fam-wrap"><table class="famt"><thead><tr><th>HS code</th><th>What the goods must be</th>'
               '<th>General</th><th>SAFTA</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(rows))
    if hidden:
        out.append('<button type="button" class="fam-more">Show all %d lines</button>' % len(fam))

    # 3. the closest cheaper lines, each with its condition, and the SAFTA route
    cards = []
    sn, sd = rate(mine[4])
    if my_g is not None and sn is not None and sn < my_g:
        cards.append('<a class="fam-card" href="/safta"><span class="fam-chip t-%s">%s</span><span class="fam-step2">instead of %s</span>'
                     '<b>Same goods, made in India or SAARC</b><span class="fam-if">Needs a SAFTA certificate of origin. The code stays %s.</span></a>'
                     % (tone(sn), esc(sd), esc(my_d), esc(dotted)))
    if my_g is not None:
        def shared(r):
            p, m = path_of(r), path_of(mine); k = 0
            while k < min(len(p), len(m)) and p[k] == m[k]:
                k += 1
            return k
        cheaper = sorted([r for r in fam if r[0] != mine[0] and rate(r[5])[0] is not None and rate(r[5])[0] < my_g],
                         key=lambda r: (-shared(r), rate(r[5])[0]))[:3]
        for r in cheaper:
            n, d = rate(r[5])
            cards.append('<a class="fam-card" href="%s"><span class="fam-chip t-%s">%s</span><span class="fam-step2">instead of %s</span>'
                         '<b>HS %s</b><span class="fam-if">Only if your goods are: %s</span></a>'
                         % (esc(href(r[0])), tone(n), esc(d), esc(my_d), esc(r[0]), esc(' › '.join(deciding(r, mine)))))
    if cards:
        out.append('<h3 class="fam-h3">Closest lines with lower duty, and the condition for each</h3><div class="fam-cards">%s</div>' % ''.join(cards))
    notes = []
    if my_g is not None and lo is not None and my_g == lo and len(order) > 1:
        notes.append('Your line already has the lowest general duty in its family.')
    notes.append('Declaring a lower-duty line that does not match the goods leads to reclassification, the duty difference and a fine. '
                 'When unsure, ask the Department of Customs for an advance ruling.')
    out.append('<p class="fam-note">%s</p>' % ' '.join(notes))
    out.append('<script>(function(){var s=document.currentScript.parentNode,tb=s.querySelector("tbody"),cur=null;'
               's.addEventListener("click",function(e){var b=e.target.closest("button"),c=e.target.closest(".fam-d");'
               'if(c){c.classList.toggle("open");return}if(!b)return;'
               'if(b.classList.contains("fam-more")){s.classList.add("all");b.remove();return}'
               'var st=b.getAttribute("data-step");if(st!==null){cur=cur===st?null:st;'
               '[].forEach.call(s.querySelectorAll(".fam-step"),function(x){var on=x.getAttribute("data-step")===cur;x.classList.toggle("sel",on);x.setAttribute("aria-pressed",on)});'
               's.classList.toggle("filt",cur!==null);[].forEach.call(tb.rows,function(r){r.classList.toggle("fam-off",cur!==null&&r.dataset.r!==cur)});return}'
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
.fam:not(.all):not(.filt) .fam-x{display:none}.famt tr.fam-off{display:none!important}.fam.filt .fam-more{display:none}
.fam-stairs{display:flex;align-items:flex-end;gap:5px;margin:.4em 0 0;padding-top:22px;border-bottom:2px solid var(--border)}
.fam-step{position:relative;flex:1 1 0;min-width:0;border:0;border-radius:9px 9px 0 0;font:inherit;cursor:pointer;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;padding:6px 2px 0;line-height:1.15;transition:filter .15s,transform .15s}
.fam-step b{font-size:.95rem}.fam-step small{font-size:.68rem;opacity:.85;white-space:nowrap}
.fam-step.t-free{background:var(--free-bg);color:var(--free)}.fam-step.t-low{background:var(--low-bg);color:var(--low)}
.fam-step.t-mid{background:var(--mid-bg);color:var(--mid)}.fam-step.t-hi{background:var(--hi-bg);color:var(--hi)}.fam-step.t-spec{background:var(--spec-bg);color:var(--spec)}
.fam-step:hover{filter:brightness(.96)}.fam-step:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.fam-step.is-me{box-shadow:inset 0 3px 0 var(--accent)}
.fam-step em{position:absolute;top:-21px;left:50%;transform:translateX(-50%);font-style:normal;font-size:.66rem;font-weight:700;white-space:nowrap;background:var(--accent);color:#fff;border-radius:999px;padding:1px 7px}
.fam-step.sel{box-shadow:inset 0 0 0 2px currentColor}.fam.filt .fam-step:not(.sel){opacity:.45}
.fam-hint{font-size:.8rem;color:var(--muted);margin:.4em 0 1em}.fam-same{margin:.2em 0 1em}
.fam-h3{font-size:1rem;margin:1.3em 0 .5em}
.fam-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.fam-card{display:grid;grid-template-columns:auto 1fr;gap:4px 8px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;color:var(--fg);text-decoration:none}
.fam-card:hover{border-color:var(--accent);text-decoration:none}
.fam-card .fam-chip{font-size:1.05rem;padding:3px 10px}.fam-card .fam-step2{font-size:.8rem;color:var(--muted)}
.fam-card b{grid-column:1/-1;font-family:var(--mono);font-size:.9rem;margin-top:4px}.fam-card b:not(:empty){word-break:break-word}
.fam-card .fam-if{grid-column:1/-1;font-size:.85rem;color:var(--fg2);line-height:1.4}
@media(max-width:600px){.fam-step small{font-size:.6rem}.fam-step b{font-size:.82rem}.fam-stairs{gap:3px}}
@media(prefers-reduced-motion:reduce){.fam-step{transition:none}}
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
