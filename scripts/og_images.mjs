// Share images (1200x630) for the trade-partner pages — one per partner + the hub.
// OFFLINE step, like world_country.py: run after a new FTS drop, commit public/og/*.jpg.
//   node scripts/og_images.mjs [path-to-playwright]      (not part of `npm run build`)
// Every number comes from world/data/country.json (Department of Customs FTS); nothing is estimated.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pw = (await import(process.argv[2] || 'playwright')).default;
const D = JSON.parse(fs.readFileSync(path.join(root, 'world/data/country.json'), 'utf8'));
const out = path.join(root, 'public/og'); fs.mkdirSync(out, { recursive: true });
const slug = n => n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function money(th) {
  let r = Math.abs(th * 1000), s;
  if (r >= 1e11) s = (r / 1e11).toFixed(2) + ' kharba';
  else if (r >= 1e9) s = (r / 1e9).toFixed(2) + ' arba';
  else if (r >= 1e7) s = (r / 1e7).toFixed(2) + ' crore';
  else if (r >= 1e5) s = (r / 1e5).toFixed(2) + ' lakh';
  else s = Math.round(r).toLocaleString('en-IN');
  return (th < 0 ? '−' : '') + 'Rs ' + s;
}
const page = (flag, head, imp, exp, foot) => {
  const mx = Math.max(imp, exp, 1), bal = exp - imp;
  const bar = (v, c) => `<div class="bar"><i style="width:${Math.max(1.2, v / mx * 100)}%;background:${c}"></i></div>`;
  return `<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0}body{width:1200px;height:630px;font-family:"DejaVu Sans","Noto Sans",Arial,sans-serif;color:#fff;
background:linear-gradient(135deg,#0A1530,#13306B 60%,#0D5A6B);padding:54px 64px;position:relative;overflow:hidden}
body:before{content:"";position:absolute;right:-140px;top:-160px;width:560px;height:560px;border-radius:50%;background:radial-gradient(circle,rgba(90,162,255,.3),transparent 65%)}
.k{font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#9FD8FF;font-weight:700}
h1{font-size:${head.length > 26 ? 62 : 78}px;line-height:1.02;letter-spacing:-.03em;margin:14px 0 30px;font-weight:800;max-width:1000px}
.fl{position:absolute;right:64px;top:44px;font-size:120px;line-height:1;font-family:"Noto Color Emoji"}
.row{display:grid;grid-template-columns:250px 1fr 330px;align-items:center;gap:22px;margin:16px 0;font-size:30px}
.row span{color:rgba(255,255,255,.75)}.row b{text-align:right;font-size:36px;font-weight:800}
.bar{height:26px;border-radius:13px;background:rgba(255,255,255,.13);overflow:hidden}.bar i{display:block;height:100%;border-radius:13px}
.bal{margin-top:26px;font-size:30px;color:rgba(255,255,255,.8)}.bal b{color:${bal < 0 ? '#FF9B9B' : '#7EE2A8'};font-size:36px}
.ft{position:absolute;left:64px;right:64px;bottom:40px;display:flex;justify-content:space-between;font-size:22px;color:rgba(255,255,255,.72)}
.ft b{color:#fff}</style>
<div class="fl">${flag}</div><div class="k">Nepal trade · FY ${esc(D.fy)}</div><h1>${esc(head)}</h1>
<div class="row"><span>Nepal imports</span>${bar(imp, '#5AA2FF')}<b style="color:#8EC0FF">${money(imp)}</b></div>
<div class="row"><span>Nepal exports</span>${bar(exp, '#FF9A5A')}<b style="color:#FFB08A">${money(exp)}</b></div>
<div class="bal">Trade balance <b>${money(bal)}</b></div>
<div class="ft"><span>Source: Department of Customs, Nepal</span><b>${esc(foot)}</b></div>`;
};
const browser = await pw.chromium.launch();
const pg = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
let n = 0;
const shot = async (html, name) => { await pg.setContent(html); await pg.screenshot({ path: path.join(out, name), type: 'jpeg', quality: 84 }); n++; };
for (const iso of D.order) {
  const c = D.countries[iso]; if (!c.impP) continue;
  await shot(page(c.flag, `Nepal ⇄ ${c.name}`, c.imp, c.exp, `customsnepal.com/trade-partner/${slug(c.name)}`), `trade-${slug(c.name)}.jpg`);
}
await shot(page('🌍', 'Who Nepal trades with', D.totals.imp, D.totals.exp, 'customsnepal.com/trade-partners'), 'trade-partners.jpg');
await browser.close();
console.log('og_images: ' + n + ' images in public/og');
