// OFFLINE step (not part of `npm run build`): builds world/data/worldmap.json — one SVG path per
// country (Natural Earth 110m via the `world-atlas` package, public domain), Natural Earth
// projection fitted to 960x500, keyed by ISO-3. Re-run only if the map itself needs to change:
//   npm i world-atlas topojson-client d3-geo i18n-iso-countries   (anywhere, e.g. a temp dir)
//   node scripts/world_map.mjs <that node_modules dir>
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module';
const nm = path.resolve(process.argv[2] || 'node_modules');
const require = createRequire(nm + '/');
const topo = require('topojson-client'), d3 = require('d3-geo'), iso = require('i18n-iso-countries');
const world = JSON.parse(fs.readFileSync(nm + '/world-atlas/countries-110m.json', 'utf8'));
const fc = topo.feature(world, world.objects.countries);
fc.features = fc.features.filter(f => f.id !== '010');           // drop Antarctica
const proj = d3.geoNaturalEarth1().fitSize([960, 500], fc);
const gen = d3.geoPath(proj);
const out = {};
for (const f of fc.features) {
  const a3 = iso.numericToAlpha3(String(f.id).padStart(3, '0')); if (!a3) continue;
  const d = (gen(f) || '').replace(/(\d+\.\d)\d+/g, '$1');         // 1 decimal is plenty at this size
  if (d) out[a3] = d;
}
fs.writeFileSync('world/data/worldmap.json', JSON.stringify(out));
console.log('worldmap.json:', Object.keys(out).length, 'countries,', Math.round(fs.statSync('world/data/worldmap.json').size / 1024), 'KB');
