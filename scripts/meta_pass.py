"""Build step (after every generator, before footer_pass): fit every page's <title> and meta description to
search-result length without cutting words, and keep the og:/twitter: copies identical. Idempotent.
/world is left alone (other host)."""
import pathlib, re, sys, html
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from textfit import fit_title, fit_desc

pub = root / 'public'
T_RE = re.compile(r'<title>(.*?)</title>', re.S)
nt = nd = 0
for f in pub.rglob('*.html'):
    if f.relative_to(pub).parts[0] == 'world':
        continue
    h = f.read_text(encoding='utf-8')
    orig = h
    m = T_RE.search(h)
    if m:
        old = html.unescape(m.group(1))
        new = fit_title(old)
        if new != ' '.join(old.split()):
            e = html.escape(new, quote=True)
            h = h[:m.start(1)] + html.escape(new, quote=False) + h[m.end(1):]
            h = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*(")', lambda x: x.group(1) + e + x.group(2), h)
            nt += 1
    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    if m:
        old = html.unescape(m.group(1))
        new = fit_desc(old)
        if new != ' '.join(old.split()):
            e = html.escape(new, quote=True)
            h = re.sub(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*(")',
                       lambda x: x.group(1) + e + x.group(2), h)
            nd += 1
    if h != orig:
        f.write_text(h, encoding='utf-8')
print('meta_pass: %d titles and %d descriptions fitted to search-result length' % (nt, nd))
