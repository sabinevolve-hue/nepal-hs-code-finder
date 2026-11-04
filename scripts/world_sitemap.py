#!/usr/bin/env python3
"""Sitemaps for world.customsnepal.com are now produced by scripts/world_prerender.py, because each URL's
<lastmod> comes from the prerendered page's own content hash (scripts/world_lastmod.json). Output:
world/sitemap.xml (sitemap index) + world/sitemap-{hubs,product-groups,hs-chapters,countries,nepal-exports,hs-codes}.xml.
Kept as an entry point for old habits/docs — it simply runs the full prerender."""
import pathlib, runpy

runpy.run_path(str(pathlib.Path(__file__).resolve().parent / 'world_prerender.py'), run_name='__main__')
