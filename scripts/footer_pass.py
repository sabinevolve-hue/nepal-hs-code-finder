"""Last build step before check_pages: give every static page the shared footer (scripts/footer.py).

Each generator still writes its own <footer>; the paragraphs BEFORE its "Not a government website" line are the
page's own source note, kept as "About this page's data". Everything after (disclaimer, link lines, explore,
other sites) is replaced by the shared footer. Pages that already carry footer.sf (the app shell) are skipped,
and /world is left alone (other host). Idempotent.
"""
import pathlib, re, sys
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from footer import site_footer, FOOTER_CSS

pub = root / 'public'
FOOT_RE = re.compile(r'<footer[^>]*>(.*?)</footer>', re.S)
P_RE = re.compile(r'<p\b[^>]*>.*?</p>', re.S)
cache = {}
n = kept = 0
for f in pub.rglob('*.html'):
    if f.relative_to(pub).parts[0] == 'world':
        continue
    h = f.read_text(encoding='utf-8')
    if 'class="sf"' in h:
        continue
    m = FOOT_RE.search(h)
    if not m:
        continue
    srcs = []
    for p in P_RE.findall(m.group(1)):
        txt = re.sub(r'<[^>]+>', '', p)
        if txt.strip().startswith('Not a government website') or txt.strip().startswith('Home ·'):
            break
        srcs.append(p)
    key = ''.join(srcs)
    if key not in cache:
        cache[key] = site_footer(key)
    kept += bool(srcs)
    # some generators leave the page's .wrap open when the footer starts; close any open <div> so the dark
    # footer runs full width (a stray closing tag later on is ignored by browsers)
    pre = h[:m.start()]
    open_divs = max(0, len(re.findall(r'<div\b', pre)) - pre.count('</div>'))
    h = pre + '</div>' * open_divs + cache[key] + h[m.end():]
    f.write_text(h, encoding='utf-8')
    n += 1
css = pub / 'seo.css'
c = css.read_text(encoding='utf-8')
c = re.sub(r'/\*SFOOT\*/.*?/\*/SFOOT\*/', '', c, flags=re.S) + '/*SFOOT*/' + FOOTER_CSS + '/*/SFOOT*/'
css.write_text(c, encoding='utf-8')
print('footer_pass: %d pages given the shared footer (%d kept a page source note); %d footer variants' % (n, kept, len(cache)))
