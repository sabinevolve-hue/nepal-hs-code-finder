#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver, ...) which sitemap URLs changed since the last submission.

Sites:
  www.customsnepal.com    sitemap public/sitemap.xml,  key file public/<key>.txt
  world.customsnepal.com  sitemap world/sitemap.xml (a sitemap index; its child sitemaps are read too),
                          key file world/<key>.txt

How "changed" is decided: every sitemap URL is mapped to the built file that serves it (public/<path>.html,
<path>/index.html, or index.html for "/"), and the file's SHA-256 is compared with scripts/indexnow_state.json.
Bare ISO dates (YYYY-MM-DD) are blanked before hashing, so a rebuild that only bumps "updated" dates does not count
as a change (the main sitemap stamps every <lastmod> with the build date). A URL whose file cannot be found falls
back to its <lastmod>. New URLs count as changed; removed URLs are dropped from the state.

Run AFTER the deploy is live (IndexNow fetches the key file and search engines then crawl the URLs):
  python3 scripts/indexnow_submit.py --dry-run         # list what would be sent, change nothing
  python3 scripts/indexnow_submit.py                   # submit changed URLs for both hosts, then save the state
  python3 scripts/indexnow_submit.py --site world      # one host only (www | world)
  python3 scripts/indexnow_submit.py --mark-only       # record the current state without submitting (baseline)
Then commit scripts/indexnow_state.json.

Protocol: POST https://api.indexnow.org/indexnow, JSON {host, key, keyLocation, urlList}, at most 10,000 URLs per
request. 200/202 = accepted. The state for a host is saved only after all its batches were accepted, so a failed
run is simply retried. Standard library only.
"""
import argparse, hashlib, json, pathlib, re, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / 'scripts' / 'indexnow_state.json'
ENDPOINT = 'https://api.indexnow.org/indexnow'
BATCH = 10_000
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
SITES = {
    'www':   {'host': 'www.customsnepal.com',   'dir': ROOT / 'public', 'sitemap': 'sitemap.xml'},
    'world': {'host': 'world.customsnepal.com', 'dir': ROOT / 'world',  'sitemap': 'sitemap.xml'},
}
DATE = re.compile(rb'\b20\d\d-[01]\d-[0-3]\d\b')


def find_key(d):
    """The one <32 hex>.txt in the site root whose content equals its own name."""
    keys = [f for f in d.glob('*.txt') if re.fullmatch(r'[0-9a-f]{32}', f.stem) and f.read_text().strip() == f.stem]
    if len(keys) != 1:
        sys.exit(f'indexnow: expected exactly one valid <key>.txt in {d}, found {len(keys)}')
    return keys[0].stem


def sitemap_urls(d, name, host):
    """[(loc, lastmod)] from a sitemap or sitemap index (child sitemaps resolved to local files)."""
    tree = ET.parse(d / name).getroot()
    out = []
    if tree.tag == NS + 'sitemapindex':
        for sm in tree.iter(NS + 'sitemap'):
            loc = sm.findtext(NS + 'loc').strip()
            out += sitemap_urls(d, loc.split(host, 1)[1].lstrip('/'), host)
        return out
    for u in tree.iter(NS + 'url'):
        out.append((u.findtext(NS + 'loc').strip(), (u.findtext(NS + 'lastmod') or '').strip()))
    return out


def local_file(d, loc, host):
    path = loc.split(host, 1)[1].split('?', 1)[0].split('#', 1)[0].strip('/')
    for c in ([d / 'index.html'] if not path else [d / (path + '.html'), d / path / 'index.html', d / path]):
        if c.is_file():
            return c
    return None


def fingerprint(d, loc, host, lastmod):
    f = local_file(d, loc, host)
    if f is None:
        return 'lastmod:' + lastmod
    return hashlib.sha256(DATE.sub(b'', f.read_bytes())).hexdigest()[:20]


def submit(host, key, urls):
    for i in range(0, len(urls), BATCH):
        body = json.dumps({'host': host, 'key': key, 'keyLocation': f'https://{host}/{key}.txt',
                           'urlList': urls[i:i + BATCH]}).encode()
        req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
            print(f'  {host}: HTTP {code} {e.read()[:300]!r}')
        if code not in (200, 202):
            return False
        print(f'  {host}: batch {i // BATCH + 1} — {len(urls[i:i + BATCH])} URLs accepted (HTTP {code})')
        time.sleep(1)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--site', choices=sorted(SITES), action='append', help='limit to one host (repeatable)')
    ap.add_argument('--dry-run', action='store_true', help='show what would be submitted; change nothing')
    ap.add_argument('--mark-only', action='store_true', help='save the current state without submitting')
    a = ap.parse_args()

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    rc = 0
    for name in a.site or sorted(SITES):
        s = SITES[name]; host, d = s['host'], s['dir']
        key = find_key(d)
        prev = state.get(host, {})
        cur = {loc: fingerprint(d, loc, host, lm) for loc, lm in sitemap_urls(d, s['sitemap'], host)}
        changed = [u for u, fp in cur.items() if prev.get(u) != fp]
        print(f'{host}: {len(cur)} sitemap URLs, {len(changed)} new/changed (key {key[:6]}…)')
        if a.dry_run:
            for u in changed[:20]: print('   ', u)
            if len(changed) > 20: print(f'    … and {len(changed) - 20} more')
            continue
        if changed and not a.mark_only and not submit(host, key, changed):
            print(f'  {host}: submission failed — state not updated, re-run later'); rc = 1; continue
        state[host] = cur
    if not a.dry_run:
        STATE.write_text(json.dumps(state, indent=0, sort_keys=True) + '\n')
        print(f'state saved: {STATE.relative_to(ROOT)}')
    return rc


if __name__ == '__main__':
    sys.exit(main())
