"""Refresh only the year-to-date part of data/stats.json from the newest FTS workbook of the running fiscal year.

stats.py rebuilds everything and needs every yearly workbook since FY 2076/77. The monthly update only has the new
cumulative file, so this script patches just two blocks and leaves the annual detail and history untouched:
  - current: fy, months, overview, chapters, top-40 countries (what the app and /insights read for "this year so far")
  - monthly[<fy>][month]: the month's own value = this cumulative file minus the previous month's cumulative totals

Usage: python3 scripts/stats_current.py            (newest workbook under data/fts/<latest fy>/)
       python3 scripts/stats_current.py path.xlsx  (a specific file; its month is read from the file name)
Then run `npm run build`.
"""
import json, pathlib, sys
import stats

root = pathlib.Path(__file__).resolve().parents[1]
OUT = root / 'data' / 'stats.json'


def newest():
    fy_dir = sorted(p for p in (root / 'data' / 'fts').iterdir() if p.is_dir())[-1]
    files = [(stats.month_of(f.name), f) for f in fy_dir.glob('*.xlsx')]
    files = [x for x in files if x[0] is not None]
    if not files:
        sys.exit('no dated workbook in %s' % fy_dir)
    return max(files, key=lambda x: x[0])[1]


def main():
    f = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else newest()
    mo = stats.month_of(f.name)
    if mo is None:
        sys.exit('cannot read the month from the file name: %s' % f.name)
    S = json.loads(OUT.read_text(encoding='utf-8'))
    fy_dir = f.parent.name.replace('_', '-')
    P = stats.read(f, fy_dir[:4] + '/' + fy_dir[-2:])
    fy = P['fy']
    if fy == S['fy']:
        sys.exit('%s is the full year already in stats.json; run stats.py for a new annual file' % fy)
    cur = S.get('current') or {}
    if cur.get('fy') == fy and cur.get('months', 0) > mo + 1:
        sys.exit('stats.json already holds %d months of %s; %s is older' % (cur['months'], fy, f.name))

    S['current'] = dict(fy=fy, months=mo + 1, overview=P['overview'],
                        chapters=[[c, iv, ev, rv] for c, iv, ev, rv in P['chapters']],
                        countries=sorted(P['countries'], key=lambda x: -x[1])[:40])

    series = S['monthly'].get(fy) or [None] * 12
    series = (series + [None] * 12)[:12]
    prev = next((series[i] for i in range(mo - 1, -1, -1) if series[i]), None)
    prev_t = prev['cum'] if prev else [0, 0]
    # per-chapter month value needs the previous cumulative chapters, which are not stored: rebuild them from the month diffs
    prev_ch = {}
    for i in range(mo):
        for c, v in ((series[i] or {}).get('ch') or {}).items():
            a = prev_ch.setdefault(str(c), [0, 0]); a[0] += v[0]; a[1] += v[1]
    t = [P['overview']['imports'][1], P['overview']['exports'][1]]
    ch = {str(c): [iv, ev] for c, iv, ev, _ in P['chapters']}
    series[mo] = dict(m=mo, cum=t, val=[round(t[0] - prev_t[0], 2), round(t[1] - prev_t[1], 2)],
                      ch={c: [ch[c][0] - prev_ch.get(c, [0, 0])[0], ch[c][1] - prev_ch.get(c, [0, 0])[1]] for c in ch})
    S['monthly'][fy] = series
    OUT.write_text(json.dumps(S, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('stats_current: %s up to %s (%d months) | imports %s exports %s | month value %s'
          % (fy, stats.MONTHS[mo], mo + 1, t[0], t[1], series[mo]['val']))


if __name__ == '__main__':
    main()
