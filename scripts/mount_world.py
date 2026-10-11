#!/usr/bin/env python3
"""Mount the world.customsnepal.com SPA under the main site at customsnepal.com/world.
Copies world/index.html + world/data/*.json into public/world/ so the main Vercel
project serves the world site at /world. Source of truth stays world/ — this runs
as part of `npm run build`, so every deploy re-syncs. Config files (vercel.json,
robots.txt, sitemap.xml) belong to the standalone project and are intentionally skipped."""
import shutil, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = ROOT / 'world'
dst = ROOT / 'public' / 'world'

if not (src / 'index.html').exists():
    sys.exit('mount_world: world/index.html not found — nothing to mount')

(dst / 'data').mkdir(parents=True, exist_ok=True)
shutil.copy2(src / 'index.html', dst / 'index.html')

n = 0
for f in sorted((src / 'data').glob('*.json')):
    shutil.copy2(f, dst / 'data' / f.name)
    n += 1
# drop any stale data file no longer present in the source
for f in (dst / 'data').glob('*.json'):
    if not (src / 'data' / f.name).exists():
        f.unlink()

total = sum(x.stat().st_size for x in dst.rglob('*') if x.is_file())
print(f'mount_world: public/world/ <- index.html + {n} data files ({total/1024:.0f} KB)')
