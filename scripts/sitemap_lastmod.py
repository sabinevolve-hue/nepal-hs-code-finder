#!/usr/bin/env python3
"""Give every sitemap URL the date its page last changed, instead of the build date.

The generators write <lastmod> as the day of the build, so each build tells search engines that all ~5,000 pages
changed. Google ignores lastmod that is not reliably accurate. This pass sets each URL's lastmod to:
  - today, if the built page differs from the committed one (or is new);
  - otherwise the date of the last commit that changed that page.
Runs at the end of the build, before check_pages. Needs git; without it the sitemap is left as it is.
"""
import pathlib, re, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUB = ROOT / 'public'
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()


def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def page_file(loc):
    p = loc[len(SITE):].strip('/') or 'index'
    for cand in (PUB / (p + '.html'), PUB / p / 'index.html'):
        if cand.exists():
            return cand.relative_to(ROOT).as_posix()
    return None


if __name__ == '__main__':
    sm = PUB / 'sitemap.xml'
    try:
        changed = {l[3:].strip() for l in git('status', '--porcelain', '--untracked-files=all', '--', 'public').splitlines()}
        last = {}
        date = None
        for line in git('log', '--format=@%cs', '--name-only', '--', 'public').splitlines():
            if line.startswith('@'):
                date = line[1:]
            elif line and line not in last:
                last[line] = date
    except Exception as e:                                   # no git (e.g. a plain download): keep the build date
        sys.stderr.write('sitemap_lastmod: git unavailable (%s); sitemap left as built\n' % e)
        sys.exit(0)
    s = sm.read_text(encoding='utf-8'); n = {'today': 0, 'kept': 0, 'none': 0}

    def fix(m):
        loc = m.group(1); f = page_file(loc)
        if f is None:
            n['none'] += 1; return m.group(0)
        d = TODAY if (f in changed or f not in last) else last[f]
        n['today' if d == TODAY else 'kept'] += 1
        return m.group(0).replace('<lastmod>%s</lastmod>' % m.group(2), '<lastmod>%s</lastmod>' % d)
    s = re.sub(r'<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>', fix, s)
    sm.write_text(s, encoding='utf-8')
    sys.stderr.write('sitemap_lastmod: %d URLs changed today, %d keep their last-change date, %d without a page file\n'
                     % (n['today'], n['kept'], n['none']))
