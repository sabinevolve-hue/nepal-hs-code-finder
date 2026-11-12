// OFFLINE: South Asia base map for the shipping route diagram (world/data/route_map.json).
// Natural Earth 1:50m countries via world-atlas, Mercator fitted to the Nepal-gateway region. The file also
// stores the projection's scale and translate so shipping_pages.py (Python, stdlib) can place ports itself:
//   x = tx + k * lon_rad ;  y = ty - k * ln(tan(pi/4 + lat_rad/2))
// Run: node scripts/route_map.mjs <node_modules dir with world-atlas, topojson-client, d3-geo, i18n-iso-countries>
import fs from 'node:fs'; import path from 'node:path'; import { createRequire } from 'node:module'; import { fileURLToPath } from 'node:url';
const nm = process.argv[2]; const req = createRequire(path.join(nm, 'x.js'));
const topo = req('topojson-client'); const d3 = req('d3-geo'); const iso = req('i18n-iso-countries');
const world = JSON.parse(fs.readFileSync(path.join(nm, 'world-atlas/countries-50m.json'), 'utf8'));
const fc = topo.feature(world, world.objects.countries);
const W = 1000, H = 640, BOX = [[67.5, 16.2], [93.2, 30.9]];          // lon/lat corners of the area to show
const proj = d3.geoMercator().fitExtent([[0, 0], [W, H]], { type: 'MultiPoint', coordinates: BOX });
const pathGen = d3.geoPath(proj);
const KEEP = new Set(['IND', 'NPL', 'BGD', 'BTN', 'PAK', 'CHN', 'MMR', 'LKA']);
const paths = {};
for (const f of fc.features) {
  const a3 = iso.numericToAlpha3(String(f.id).padStart(3, '0'));
  if (!KEEP.has(a3)) continue;
  const d = pathGen(f); if (!d) continue;
  paths[a3] = d.replace(/(\d+\.\d)\d+/g, '$1');
}
const out = { source: 'Natural Earth 1:50m via world-atlas', w: W, h: H, k: proj.scale(), t: proj.translate(), paths };
const dst = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'world', 'data', 'route_map.json');
fs.writeFileSync(dst, JSON.stringify(out));
console.log('route_map.json', Object.keys(paths).join(' '), Math.round(fs.statSync(dst).size / 1024) + ' KB', 'k=' + proj.scale().toFixed(1));
