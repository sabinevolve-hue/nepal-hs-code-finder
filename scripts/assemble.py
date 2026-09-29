"""Inline data/tariff.json into src.html and write public/index.html (single self-contained page)."""
import pathlib, re
root = pathlib.Path(__file__).resolve().parents[1]
src = (root / 'src.html').read_text(encoding='utf-8')
data = (root / 'data' / 'tariff.json').read_text(encoding='utf-8').replace('</', '<\\/')
page = src.replace('/*DATA*/', data)
# standalone page: add the doctype + head the artifact host normally supplies
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0F172A">'
        '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E">'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
(root / 'public').mkdir(exist_ok=True)
(root / 'public' / 'index.html').write_text(head + page + '</body></html>', encoding='utf-8')
print('wrote public/index.html', len(page) // 1024, 'KB')
