"""One-command refresh: crawl customs.gov.np for new FTS workbooks, download any that are missing into
data/fts/<fy>/, then rebuild stats.json and public/index.html.
Usage: python3 scripts/refresh.py            (needs network access to customs.gov.np / giwmscdnone.gov.np)
"""
import re, json, pathlib, subprocess, sys, urllib.request, urllib.parse, time, html
root = pathlib.Path(__file__).resolve().parents[1]
UA = {'User-Agent': 'Mozilla/5.0'}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
base = 'https://customs.gov.np'
home = get(base + '/content/1139/ftskkksss/').decode('utf-8', 'ignore')
cats = sorted(set(c.strip() for c in re.findall(r'href="\s*(/category/[^"]+?)\s*"', home)))
cats = [c for c in cats if re.search(r'fts-20|foreign-trade|a-v-20', c)]
new = 0
for c in cats:
    h = get(base + c).decode('utf-8', 'ignore')
    cards = re.findall(r'class="grid__card".*?</h3>', h, re.S)
    for cd in cards[:1]:  # first card is the category's own page; the rest are "related" links
        m = re.search(r'href="\s*(/content/[^"]+?)\s*"', cd)
        if not m: continue
        ph = get(base + m.group(1)).decode('utf-8', 'ignore')
        fys = re.findall(r'20(\d\d)\s*[/\-–]\s*0?(\d\d)', html.unescape(re.sub(r'<[^>]+>', ' ', ph))[:2000])
        fy = ('20' + fys[0][0] + '-' + fys[0][1]) if fys else None
        for f in re.findall(r'href="\s*(https?://[^"]+?\.xlsx)\s*"', ph, re.I):
            name = urllib.parse.unquote(f.split('/')[-1])
            if not fy: continue
            d = root / 'data' / 'fts' / fy; d.mkdir(parents=True, exist_ok=True)
            p = d / re.sub(r'[\\/:*?"<>|]', '_', name)
            if p.exists(): continue
            print('downloading', fy, name); p.write_bytes(get(html.unescape(f))); new += 1; time.sleep(0.5)
print('new files:', new)
if new or '--force' in sys.argv:
    subprocess.check_call([sys.executable, str(root / 'scripts' / 'stats.py')])
    subprocess.check_call([sys.executable, str(root / 'scripts' / 'assemble.py')])
    print('rebuilt public/index.html — commit and push to deploy')
