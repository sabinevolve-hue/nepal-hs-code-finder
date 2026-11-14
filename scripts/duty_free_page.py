"""/duty-free — what Nepal lets in at 0% and 5% customs duty.

One static page: where the whole tariff sits by duty rate (a staircase), which chapters hold the duty-free lines,
then the duty-free and low-duty lines Nepal actually imports most, each linked to its product page.

Data: data/tariff.json (general rate = row[5]) and data/stats.json imports (VALUE at IMP_VALUE, Rs thousand).
Runs after product_pages.py so product links can be checked against the built files. Stdlib only.
"""
import json, re
import pagekit as k
from pagekit import esc, money, pub, root
from statsfields import IMP_VALUE, TARIFF_FY, slug, clean_name
import family

T = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
ST = json.loads((root / 'data/stats.json').read_text(encoding='utf-8'))
import statsfields as _sf; _sf.fix_names(ST)
FY = ST.get('fy', '')
CH = T.get('chapters', {})
c8 = lambda s: re.sub(r'\D', '', str(s))

IMP = {}
for raw, v in ST.get('imports', {}).items():
    try:
        IMP[c8(raw)] = (float(v[IMP_VALUE]), v[0] or '')
    except (ValueError, IndexError, TypeError):
        pass

bands, free, low = {}, [], []
for r in T['rows']:
    n, d = family.rate(r[5])
    key = 'Per unit' if n is None else d
    bands.setdefault(key, [n, 0]); bands[key][1] += 1
    code = c8(r[0]); val, nm = IMP.get(code, (0.0, ''))
    rec = (code, r, val, clean_name(nm or r[1]))
    if n == 0:
        free.append(rec)
    elif n is not None and n <= 5:
        low.append(rec)
free.sort(key=lambda x: -x[2]); low.sort(key=lambda x: -x[2])
NF, NL, NALL = len(free), len(low), len(T['rows'])
free_val = sum(x[2] for x in free); low_val = sum(x[2] for x in low)
tot_val = sum(v for v, _ in IMP.values()) or 1


def href(code, name):
    f = pub / 'import-duty' / ('%s-%s.html' % (slug(name), code))
    return ('/import-duty/%s-%s' % (slug(name), code)) if f.exists() else '/#hs-' + code


def tone(n):
    return 'spec' if n is None else ('free' if n == 0 else ('low' if n <= 10 else ('mid' if n <= 20 else 'hi')))


title = 'Duty-free imports to Nepal: every 0%% and 5%% line, %s' % TARIFF_FY
desc = ('%d tariff lines enter Nepal at 0%% customs duty and %d more at 5%%. See which goods they are, how much Nepal '
        'imports of each, and what still applies (13%% VAT).' % (NF, NL))
bc = [('Home', '/'), ('Import duty', '/import-duty'), ('Duty-free and low-duty', '')]
faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": "What can be imported into Nepal duty-free?",
     "acceptedAnswer": {"@type": "Answer", "text": "%d of the %d lines in the Nepal Customs Tariff %s carry 0%% general customs duty, "
                        "and a further %d carry 5%%. Duty-free means customs duty only: 13%% VAT still applies unless the goods are VAT-exempt."
                        % (NF, NALL, TARIFF_FY, NL)}},
    {"@type": "Question", "name": "Do duty-free imports still pay VAT in Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": "Yes. A 0% customs duty line still pays 13% VAT on the CIF value unless the goods are "
                        "separately VAT-exempt, and a few goods also pay excise."}}]}

out = [k.page_head(title, desc, '/duty-free', bc, extra_ld=[faq]), k.crumb_html(bc)]
out.append('<h1>Duty-free and low-duty imports to Nepal</h1>')
out.append('<p class="lede"><b>%d</b> tariff lines enter Nepal at <b>0%% customs duty</b> and <b>%d</b> more at <b>5%%</b>. '
           'Together that is %.0f%% of the %s lines in the tariff and about %.0f%% of what Nepal imports by value.</p>'
           % (NF, NL, 100.0 * (NF + NL) / NALL, '{:,}'.format(NALL), 100.0 * (free_val + low_val) / tot_val))

# staircase of the whole tariff by duty rate
order = sorted(bands.items(), key=lambda kv: (kv[1][0] is None, kv[1][0] or 0))
mx = max(v[1] for _, v in order)
steps = []
for lab, (n, cnt) in order:
    steps.append('<div class="fam-step t-%s%s" style="height:%dpx"><b>%s</b><small>%s lines</small></div>'
                 % (tone(n), ' is-me' if (n is not None and n <= 5) else '', 38 + round(110 * cnt / mx), esc(lab), '{:,}'.format(cnt)))
out.append('<h2 class="sec">Where the tariff sits, by duty rate</h2>'
           '<div class="fam-stairs dfs" role="img" aria-label="Number of tariff lines at each general duty rate: %s">%s</div>'
           '<p class="fam-hint">Height shows how many of the %s tariff lines carry that general duty. The two marked steps are this page. '
           '&ldquo;Per unit&rdquo; lines are charged by quantity (alcohol, tobacco, fuel).</p>'
           % (esc(', '.join('%s %d' % (l, v[1]) for l, v in order)), ''.join(steps), '{:,}'.format(NALL)))

# chapters holding the duty-free lines
by_ch = {}
for code, r, val, nm in free:
    c = by_ch.setdefault(code[:2], [0, 0.0]); c[0] += 1; c[1] += val
tiles = []
for ch, (cnt, val) in sorted(by_ch.items(), key=lambda kv: -kv[1][1])[:12]:
    ct = (CH.get(str(int(ch))) or {}).get('t', '')
    tiles.append('<a class="chcard" href="/tariff/%s"><span class="t">%s</span><span class="c">Chapter %s · %d duty-free line%s · %s imported</span></a>'
                 % (ch, esc(ct[:70]), ch, cnt, '' if cnt == 1 else 's', money(val)))
out.append('<h2 class="sec">Which goods are duty-free</h2><p>The chapters whose duty-free lines Nepal imports most, FY %s.</p>'
           '<div class="guidegrid">%s</div>' % (esc(FY), ''.join(tiles)))


def table(recs, limit):
    rows = []
    for code, r, val, nm in recs[:limit]:
        if val <= 0:
            break
        n, d = family.rate(r[5]); sn, sd = family.rate(r[4])
        rows.append('<tr><td><a href="%s">%s</a></td><td class="mono">%s</td><td><span class="fam-chip t-%s">%s</span></td>'
                    '<td><span class="fam-chip t-%s">%s</span></td><td class="r">%s</td></tr>'
                    % (esc(href(code, nm)), esc(nm), esc(r[0]), tone(n), esc(d), tone(sn), esc(sd), money(val)))
    return ('<div class="tscroll"><table class="tbl dft"><thead><tr><th>Product</th><th>HS code</th><th>General</th><th>SAFTA</th>'
            '<th class="r">Nepal imports, FY %s</th></tr></thead><tbody>%s</tbody></table></div>' % (esc(FY), ''.join(rows)), len(rows))

t1, n1 = table(free, 100)
t2, n2 = table(low, 100)
out.append('<h2 class="sec">Most-imported duty-free goods (0%%)</h2><p>The %d duty-free lines Nepal imports most, by value.</p>%s' % (n1, t1))
out.append('<h2 class="sec">Most-imported low-duty goods (5%%)</h2><p>The top %d of %d lines at 5%%, by value.</p>%s' % (n2, NL, t2))
out.append('<div class="note"><b>Duty-free is not tax-free.</b> 0% customs duty still leaves 13% VAT on the CIF value unless the goods are '
           'VAT-exempt, and a few goods also pay excise. The <a href="/calculator">calculator</a> gives the full landed cost. '
           'A line applies only to goods that match its description; each product page shows the '
           'other lines in the same family and what decides between them.</div>')
out.append('<div class="tools"><a class="btn" href="/import-duty">Import duty by product</a>'
           '<a class="btn ghost" href="/safta">SAFTA rates for India and SAARC</a><a class="btn ghost" href="/tariff">Browse the full tariff</a></div>')
out.append('<style>.dfs .fam-step{cursor:default}.dfs .fam-step.is-me{box-shadow:inset 0 3px 0 var(--accent)}'
           '.dft td:first-child{min-width:170px}.dft .mono{font-family:var(--mono);font-size:.85rem;white-space:nowrap}.dft .r{text-align:right;white-space:nowrap}</style>')
out.append(k.foot('<b>Duty rates:</b> Nepal Customs Tariff %s (Department of Customs). <b>Import values:</b> Department of Customs, '
                  'Foreign Trade Statistics, FY %s. Values in Nepali rupees.' % (TARIFF_FY, FY)))
(pub / 'duty-free.html').write_text(''.join(out), encoding='utf-8')
print('duty_free_page: /duty-free (%d free, %d at 5%%); +%d sitemap URL' % (NF, NL, k.add_to_sitemap(['/duty-free'])))
