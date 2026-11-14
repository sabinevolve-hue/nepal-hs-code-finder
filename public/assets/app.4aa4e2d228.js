
(function(){
async function __boot(){
const __j = u => fetch(u).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
let D, ST, OF, INT;
try {
  [D, ST, OF, INT] = await Promise.all([__j('/t.json'), __j('/st.json'), __j('/of.json'), __j('/int.json').catch(() => ({}))]);
} catch (e) {
  var el = document.querySelector('#v-home') || document.body;
  if (el) el.innerHTML = '<div style="padding:48px 16px;text-align:center;color:#64748b;font:500 1rem system-ui">Couldn\'t load the tariff data. <a href="#" onclick="location.reload();return false" style="color:#5470C6">Tap to reload</a>.</div>';
  return;
}
const CHSHORT = {"1": "Live animals", "2": "Meat", "3": "Fish & seafood", "4": "Dairy, eggs & honey", "5": "Other animal products", "6": "Live plants & flowers", "7": "Vegetables", "8": "Fruit & nuts", "9": "Coffee, tea & spices", "10": "Cereals", "11": "Flour, malt & starch", "12": "Oil seeds & medicinal plants", "13": "Gums & resins", "14": "Vegetable materials", "15": "Edible oils & fats", "16": "Meat & fish preparations", "17": "Sugar & confectionery", "18": "Cocoa & chocolate", "19": "Cereal & bakery products", "20": "Processed fruit & vegetables", "21": "Misc. food preparations", "22": "Beverages & spirits", "23": "Animal feed & residues", "24": "Tobacco", "25": "Salt, stone, cement & lime", "26": "Ores & ash", "27": "Fuels, oils & gas", "28": "Inorganic chemicals", "29": "Organic chemicals", "30": "Pharmaceuticals", "31": "Fertilisers", "32": "Dyes, paints & inks", "33": "Cosmetics & perfumery", "34": "Soap & cleaning products", "35": "Glues & enzymes", "36": "Explosives & matches", "37": "Photographic goods", "38": "Misc. chemicals", "39": "Plastics", "40": "Rubber", "41": "Raw hides & leather", "42": "Leather goods & bags", "43": "Furskins", "44": "Wood & timber", "45": "Cork", "46": "Straw & basketware", "47": "Wood pulp", "48": "Paper & paperboard", "49": "Books & printed matter", "50": "Silk", "51": "Wool & animal hair", "52": "Cotton", "53": "Jute & other fibres", "54": "Synthetic filaments", "55": "Synthetic staple fibres", "56": "Wadding, felt & rope", "57": "Carpets", "58": "Special fabrics & lace", "59": "Coated & industrial textiles", "60": "Knitted fabrics", "61": "Knitted garments", "62": "Woven garments", "63": "Textile articles & rags", "64": "Footwear", "65": "Headgear", "66": "Umbrellas & sticks", "67": "Feathers & artificial flowers", "68": "Stone & cement articles", "69": "Ceramics", "70": "Glass", "71": "Gems, gold & jewellery", "72": "Iron & steel", "73": "Iron & steel articles", "74": "Copper", "75": "Nickel", "76": "Aluminium", "77": "Reserved", "78": "Lead", "79": "Zinc", "80": "Tin", "81": "Other base metals", "82": "Tools & cutlery", "83": "Misc. metal articles", "84": "Machinery & mechanical", "85": "Electrical & electronics", "86": "Railway", "87": "Vehicles & parts", "88": "Aircraft & drones", "89": "Ships & boats", "90": "Optical, medical & precision", "91": "Clocks & watches", "92": "Musical instruments", "93": "Arms & ammunition", "94": "Furniture & lighting", "95": "Toys, games & sports", "96": "Misc. manufactured", "97": "Art & antiques"};

const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const reflow = t => String(t || '').replace(/\n(?!(?:RULE|Notes?|Sub-?heading Notes?|Additional|TABLE|\d+\.-|\([a-z]\)|\([ivx]+\)|-|[A-Z][A-Z ]{3,}$))/g, ' ').replace(/ {2,}/g, ' ');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ic = (id, cls='i') => `<svg class="${cls}" aria-hidden="true"><use href="#${id}"/></svg>`;
const store = {
  get(k, d){ try{ const v = localStorage.getItem('nphs.'+k); return v ? JSON.parse(v) : d; }catch(e){ return d; } },
  set(k, v){ try{ localStorage.setItem('nphs.'+k, JSON.stringify(v)); }catch(e){} }
};
// session-scoped store for sensitive drafts (invoice parties/bank): cleared when the browser tab closes,
// so a new visitor — or the next person on a shared computer — always starts from a blank form.
const sstore = {
  get(k, d){ try{ const v = sessionStorage.getItem('nphs.'+k); return v ? JSON.parse(v) : d; }catch(e){ return d; } },
  set(k, v){ try{ sessionStorage.setItem('nphs.'+k, JSON.stringify(v)); }catch(e){} },
  del(k){ try{ sessionStorage.removeItem('nphs.'+k); }catch(e){} }
};

/* ---------- data ---------- */
const ROWS = D.rows.map((r, i) => {
  const [code, d, pids, u, s, g, pg, ldc] = r;
  const path = pids.map(p => D.strs[p]);
  const h = code.slice(0,2) + '.' + code.slice(2,4), ch = +code.slice(0,2);
  const head = D.heads[h] ? D.heads[h][0] : '';
  return { i, code, d, path, u, s, g, pg, ldc, h, ch, head, digits: code.replace(/\./g,''),
    own: (' ' + d + ' ').toLowerCase(),
    ctx: (' ' + path.join(' ') + ' ' + head + ' ' + (D.chapters[ch] ? D.chapters[ch].t : '') + ' ').toLowerCase() };
});
const BY = Object.fromEntries(ROWS.map(r => [r.code, r]));
const BYHEAD = {}; ROWS.forEach(r => (BYHEAD[r.h] = BYHEAD[r.h] || []).push(r));
const CHCOUNT = {}; ROWS.forEach(r => CHCOUNT[r.ch] = (CHCOUNT[r.ch] || 0) + 1);
const sectionOf = ch => { let s = null; D.sections.forEach(x => { if (x.f <= ch) s = x; }); return s; };
const label = r => { if (!r.path.length || !/^other\b/i.test(r.d)) return r.d; const p = [...r.path].reverse().find(x => !/^other$/i.test(x)); return p ? p + ' — ' + r.d : r.d; };

/* ---------- rates ---------- */
let origin = store.get('origin', 'gen');
const rateOf = r => origin === 'saarc' ? r.s : r.g;
const num = v => !v ? NaN : /^free$/i.test(v) ? 0 : /^\d+(\.\d+)?$/.test(v) ? parseFloat(v) : NaN;
/* integrated tax data (customs + excise + VAT + special fees + total effective rate by origin) */
function taxInfo(code){
  const r = BY[code]; if (!r) return null;
  const I = INT[code] || {}, e = I.e || {};
  const FEE = { ro:'Road construction fee', lu:'Luxury fee', gr:'Green tax', cl:'Clean-infrastructure fee', in:'Internal production fee', ot:'Other tax' };
  const fees = Object.keys(FEE).filter(k => e[k] != null).map(k => ({ label: FEE[k], rate: e[k] }));
  const sep = [];
  if (e.ag != null) sep.push({ label: 'Agriculture reform fee', rate: e.ag });
  if (e.he != null) sep.push({ label: 'Health-risk tax', rate: e.he });
  return { cgRaw:r.g, csRaw:r.s, cg:num(r.g), cs:num(r.s), excise:(e.ex != null ? e.ex : null),
           fees, sep, vat:(I.v != null ? I.v : 13), totals:(I.t || null), specific:!!I.sp, unit:r.u };
}
const ORIGIN_NAMES = ['India', 'Other SAARC', 'Tibet', 'Other'];
function taxBreakdown(code){
  const t = taxInfo(code); if (!t) return '';
  const row = (l, v, cls) => `<tr${cls ? ' class="' + cls + '"' : ''}><td>${l}</td><td>${v}</td></tr>`;
  let h = '<table class="bk"><tbody>';
  h += row('Customs duty — general', esc(pct(t.cgRaw)));
  if (t.csRaw) h += row('Customs duty — SAFTA', esc(pct(t.csRaw)));
  if (t.excise != null) h += row('Excise duty', t.excise + '%');
  t.fees.forEach(f => h += row(esc(f.label), f.rate + '%'));
  t.sep.forEach(f => h += row(esc(f.label) + ' <small>collected separately</small>', f.rate + '%'));
  h += row('VAT', t.vat ? t.vat + '%' : 'Exempt');
  if (t.totals && t.totals[3] != null) h += row('Total effective rate <small>from other countries</small>', t.totals[3] + '%', 'total');
  h += '</tbody></table>';
  if (t.totals) {
    const cells = t.totals.map((x, i) => x != null ? `<span style="display:inline-block;margin:0 12px 6px 0"><small style="color:var(--muted)">${ORIGIN_NAMES[i]}</small> <b>${x}%</b></span>` : '').join('');
    if (cells) h += `<p class="fine" style="margin-top:6px">Total effective rate by origin: ${cells}</p>`;
  }
  if (t.specific) h += '<p class="fine">This code also carries a specific (Rs per unit) duty — enter your quantity in the calculator for the exact amount.</p>';
  return h;
}
const pct = v => { const n = num(v); return isNaN(n) ? (v || 'Not stated') : n === 0 ? 'Free' : n + '%'; };
/* trust / provenance — ties every rate to the official source, fiscal year and page */
const DATA_FY = { ne: '2083/84', ad: (typeof D !== 'undefined' && D.v) || '2026/27', act: '2083',
                  start: Date.UTC(2026, 6, 16), end: Date.UTC(2027, 6, 16) };
const dataStatus = () => { const t = Date.now(); return t < DATA_FY.start ? 'Upcoming' : t <= DATA_FY.end ? 'In effect' : 'Latest edition'; };
function sourceNote(code){
  const r = code ? BY[code] : null, pg = r && r.pg ? r.pg : null;
  const st = dataStatus(), cls = st === 'In effect' ? 'ok' : st === 'Upcoming' ? 'soon' : 'old';
  return `<div class="src">
    <div class="src-h">${ic('i-shield')}<span>Official rates</span><span class="fy">FY ${DATA_FY.ne} · ${DATA_FY.ad}</span><span class="pill ${cls}">${st}</span></div>
    <p>Customs duty, excise, fees and VAT are taken from Nepal's <b>Customs Tariff ${DATA_FY.ad}</b> (Department of Customs) and the <b>Finance Act ${DATA_FY.act}</b> (Ministry of Finance), which set the rates for fiscal year ${DATA_FY.ne}.${pg ? ` Customs Tariff page <b>${pg}</b>.` : ''} <a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">customs.gov.np ↗</a></p>
  </div>`;
}
function dutyTag(v, withLabel){
  const n = num(v);
  if (isNaN(n)) return `<span class="duty d-spec"><b>${v ? 'Specific rate' : 'Not stated'}</b>${withLabel ? '<small>duty</small>' : ''}</span>`;
  const cls = n === 0 ? 'd-free' : n <= 10 ? 'd-low' : n <= 20 ? 'd-mid' : 'd-hi';
  return `<span class="duty ${cls}"><b>${n === 0 ? 'Free' : n + '%'}</b>${withLabel ? '<small>duty</small>' : ''}</span>`;
}

/* ---------- search engine ---------- */
const STOP = new Set(['of','and','the','for','or','a','an','in','with','to','by','other','not','hs','code','import','duty','tax','nepal','customs','tariff','rate','price']);
const stem = w => w.length > 4 && w.endsWith('ies') ? w.slice(0,-3)+'y' : w.length > 4 && /(ches|shes|sses|xes)$/.test(w) ? w.slice(0,-2) : w.length > 3 && w.endsWith('s') && !w.endsWith('ss') ? w.slice(0,-1) : w;
function wordHit(hay, w){
  let idx = hay.indexOf(w);
  while (idx !== -1){
    if (idx === 0 || !/[a-z0-9]/.test(hay[idx-1])){ const nc = hay[idx + w.length]; return (!nc || !/[a-z0-9]/.test(nc)) ? 2 : 1; }
    idx = hay.indexOf(w, idx + 1);
  }
  return 0;
}
// A term matches inside a longer query only on word boundaries (plural s/es allowed for terms of 4+ chars), so
// short local names such as "til" (sesame) or "car" do not fire inside "textile" or "carpet".
const ALL_TERMS = D.aliases.flatMap(([terms, pref], k) => terms.map(t => { const tl = t.toLowerCase();
  return { t, tl, k, re: new RegExp('(^|[^\\p{L}\\p{M}\\p{N}])' + tl.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + (tl.length >= 4 ? '(?:e?s)?' : '') + '(?=$|[^\\p{L}\\p{M}\\p{N}])', 'u') }; }));
function aliasHits(q){
  const ql = q.toLowerCase().trim(); if (ql.length < 2) return [];
  const best = new Map();
  ALL_TERMS.forEach(({t, tl, k, re}) => {
    const sc = tl === ql ? 3 : (tl.startsWith(ql) && ql.length >= 3) ? 2 : (tl.length >= 3 && re.test(ql)) ? 2 : 0;
    if (sc && (!best.has(k) || best.get(k).sc < sc)) best.set(k, { sc, term: t, pref: D.aliases[k][1] });
  });
  const hits = [...best.values()], exact = hits.filter(h => h.sc === 3);
  return (exact.length ? exact : hits).sort((a,b) => b.sc - a.sc).slice(0, 3); // an exact local name wins over prefix guesses ("til" ≠ "tiles")
}
function termSuggest(q){
  const ql = q.toLowerCase().trim(); if (ql.length < 2 || /^\d/.test(ql)) return [];
  const seen = new Set(), out = [];
  ALL_TERMS.forEach(({t, tl}) => { if (tl !== ql && (tl.startsWith(ql) || tl.includes(' ' + ql)) && !seen.has(tl)){ seen.add(tl); out.push(t); } });
  return out.sort((a,b) => a.length - b.length).slice(0, 6);
}
function search(q){
  q = q.trim();
  const digits = q.replace(/^hs\s*/i,'').replace(/[\s.\-]/g,'');
  if (/^\d{2,8}$/.test(digits)) return { kind:'code', rows: ROWS.filter(r => r.digits.startsWith(digits)), aliases: [], words: [] };
  const al = aliasHits(q), boost = new Map();
  al.forEach((a, k) => a.pref.forEach((p, j) => { const pd = p.replace(/\./g,''); ROWS.forEach(r => { if (r.digits.startsWith(pd)) boost.set(r.i, Math.max(boost.get(r.i)||0, 40 - k*6 - j + pd.length)); }); }));
  const words = q.toLowerCase().split(/[^a-z0-9ऀ-ॿ.%]+/).filter(w => w.length > 1 && !STOP.has(w)).map(stem);
  const latin = words.filter(w => /[a-z0-9]/.test(w));
  const score = (r, all) => {
    let sc = boost.get(r.i) || 0, hitAll = true, any = false;
    latin.forEach(w => { const a = wordHit(r.own, w), b = a ? 0 : wordHit(r.ctx, w);
      if (a){ sc += a === 2 ? 12 : 8; any = true; } else if (b){ sc += b === 2 ? 4 : 3; any = true; } else hitAll = false; });
    const bo = boost.has(r.i);
    if (latin.length && all && !hitAll && !bo) return -1;
    if (latin.length && !any && !bo) return -1;
    if (!latin.length && !bo) return -1;
    return sc - (/^other\b/i.test(r.d) ? 1 : 0);
  };
  let sc = []; ROWS.forEach(r => { const s = score(r, true); if (s > 0) sc.push([s, r]); });
  let loose = false;
  if (!sc.length && latin.length > 1){ loose = true; ROWS.forEach(r => { const s = score(r, false); if (s > 0) sc.push([s, r]); }); }
  sc.sort((a,b) => b[0] - a[0] || a[1].i - b[1].i);
  return { kind:'text', rows: sc.map(x => x[1]), aliases: al, words: latin, loose };
}
function hl(text, words){
  let t = esc(text);
  (words || []).forEach(w => { if (w.length < 2) return; t = t.replace(new RegExp('(^|[^a-z0-9])(' + w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + '[a-z]*)', 'gi'), '$1<mark>$2</mark>'); });
  return t;
}

/* ---------- search view ---------- */
let dutyF = 'all', chapF = '', shown = 40;
const passDuty = r => { if (dutyF === 'all') return true; const n = num(rateOf(r)); if (isNaN(n)) return false;
  return dutyF === 'free' ? n === 0 : dutyF === 'hi' ? n > 20 : n <= +dutyF; };
// Home "Browse by category": one card per HS section, consumer names, with import value and code count
const SECT = [['I','c-cow','Live animals & animal products'],['II','c-leaf','Vegetables, fruit, grains & spices'],['III','c-oil','Edible oils & fats'],['IV','c-food','Food, drinks & tobacco'],['V','c-brick','Fuels, minerals, cement & salt'],['VI','c-flask','Chemicals, medicines & cosmetics'],['VII','c-box','Plastics & rubber'],['VIII','c-leather','Leather, bags & furskins'],['IX','c-wood','Wood, cork & basketware'],['X','c-paper','Paper, books & printing'],['XI','c-shirt','Textiles & clothing'],['XII','c-shoe','Footwear, hats & umbrellas'],['XIII','c-brick','Stone, ceramics & glass'],['XIV','c-gem','Gold, gems & jewellery'],['XV','c-metal','Iron, steel & metals'],['XVI','c-chip','Machinery, electrical & electronics'],['XVII','c-car','Vehicles, aircraft & ships'],['XVIII','c-eye','Optical, medical & precision'],['XIX','c-gun','Arms & ammunition'],['XX','c-sofa','Furniture, toys & misc. goods'],['XXI','c-art','Art & antiques']];
const secImports = {}; ST.chapters.forEach(c => { const sn = sectionOf(c[0]); if (sn) secImports[sn.n] = (secImports[sn.n] || 0) + c[2]; });
const secCodes = {}; ROWS.forEach(r => { const sn = sectionOf(r.ch); if (sn) secCodes[sn.n] = (secCodes[sn.n] || 0) + 1; });
const QUICK = [['LED display','8528 · 8531'],['Mobile phone','8517.13'],['Solar panel','8541.43'],['CCTV camera','8525'],['Laptop','8471.30'],['Electric vehicle','8703.80'],['Cement','2523'],['Cosmetics','3304'],['Medicine','3004'],['Rice','1006'],['Steel rod','7214'],['Furniture','94']];
function rowHTML(r, words, showHead){
  const ctx = r.path.length ? `<span class="p">${esc(r.path[r.path.length-1])} › </span>` : '';
  return `<button class="row" data-code="${r.code}">
    <span class="code">${r.code}</span>
    <span class="d">${ctx}${hl(r.d, words)}</span>
    <span class="end">${dutyTag(rateOf(r), true)}${ic('i-right')}</span></button>`;
}
function groupedHTML(rows, words){
  const order = [], groups = {};
  rows.forEach(r => { if (!groups[r.h]){ groups[r.h] = []; order.push(r.h); } groups[r.h].push(r); });
  return order.map(h => `<div class="group"><div class="ghead"><span class="mono">${h}</span><span>${esc(D.heads[h] ? D.heads[h][0] : '')}</span></div>${groups[h].map(r => rowHTML(r, words)).join('')}</div>`).join('');
}
function renderHome(){
  const recent = store.get('recent', []);
  const cur = ST.current, ov = ST.overview;
  $('#hero-stats').innerHTML = `<div><b>${ROWS.length.toLocaleString()}</b>tariff lines</div><div><b>${rs(ov.imports[1], true)}</b>imports FY ${ST.fy}</div><div><b>${FY.length + (cur ? 1 : 0)}</b>years of trade data</div>`;
  const SECTSHORT = {I:'Animals',II:'Vegetables & grains',III:'Edible oils',IV:'Food & drinks',V:'Fuels & minerals',VI:'Chemicals & medicine',VII:'Plastics & rubber',VIII:'Leather & bags',IX:'Wood & cork',X:'Paper & books',XI:'Textiles & clothing',XII:'Footwear & hats',XIII:'Stone, glass & ceramics',XIV:'Gold & gems',XV:'Metals & steel',XVI:'Machinery & electronics',XVII:'Vehicles & transport',XVIII:'Optical & medical',XIX:'Arms & ammunition',XX:'Furniture & toys',XXI:'Art & antiques'};
  const topSec = [...SECT].sort((a, b) => (secImports[b[0]] || 0) - (secImports[a[0]] || 0)).slice(0, 8);
  $('#results').innerHTML = `
    <h2 class="sec">Explore</h2>
    <div class="xgrid">
      <button class="xcard" data-go="ai"><span class="ic" style="background:#5470C6">${ic('i-spark')}</span><span class="xt"><b>Ask AI</b><small>Describe a product, get ranked HS codes</small></span></button>
      <button class="xcard" data-go="calc"><span class="ic" style="background:#5FB365">${ic('i-calc')}</span><span class="xt"><b>Duty calculator</b><small>Duty, VAT &amp; landed cost in NPR</small></span></button>
      <a class="xcard" href="/import-duty"><span class="ic" style="background:#C2410C">${ic('i-tag')}</span><span class="xt"><b>Import duty by product</b><small>Customs duty &amp; landed cost, product by product</small></span></a>
      <button class="xcard" data-go="imports"><span class="ic" style="background:#1D81A2">${ic('i-down')}</span><span class="xt"><b>Imports</b><small>What Nepal buys, by product &amp; country</small></span></button>
      <button class="xcard" data-go="exports"><span class="ic" style="background:#2E9E6B">${ic('i-up')}</span><span class="xt"><b>Exports</b><small>What Nepal sells, by product &amp; country</small></span></button>
      <a class="xcard" href="/export"><span class="ic" style="background:#0EA5A0">${ic('i-doc')}</span><span class="xt"><b>Export guides</b><small>How to export carpets, cardamom, tea…</small></span></a>
      <a class="xcard" href="/safta"><span class="ic" style="background:#E0A33E">${ic('i-tag')}</span><span class="xt"><b>SAFTA duty</b><small>Lower duty from South Asia</small></span></a>
      <a class="xcard" href="/shipping"><span class="ic" style="background:#EE8A4B">${ic('i-ship')}</span><span class="xt"><b>Shipping to Nepal</b><small>Gateway ports, routes &amp; transit</small></span></a>
      <a class="xcard" href="/shipping/track"><span class="ic" style="background:#E0655B">${ic('i-box')}</span><span class="xt"><b>Track a shipment</b><small>Container or B/L → the right tracker</small></span></a>
      <button class="xcard" data-go="stats"><span class="ic" style="background:#7A5EA8">${ic('i-chart')}</span><span class="xt"><b>Trade data</b><small>Compare years, products &amp; partners</small></span></button>
      <a class="xcard" href="https://world.customsnepal.com/"><span class="ic" style="background:#2563C9">${ic('i-globe')}</span><span class="xt"><b>World trade</b><small>Global HS codes &amp; 200+ countries</small></span></a>
      <button class="xcard" data-go="browse"><span class="ic" style="background:#9A60B4">${ic('i-list')}</span><span class="xt"><b>Browse tariff</b><small>Sections, chapters, notes &amp; rules</small></span></button>
      <a class="xcard" href="/faq"><span class="ic" style="background:#64748B">${ic('i-info')}</span><span class="xt"><b>FAQ &amp; help</b><small>Duty, VAT, HS codes &amp; landed cost</small></span></a>
    </div>
    <h2 class="sec">Browse by product</h2>
    <div class="catgrid">
      ${topSec.map(([n, i, t]) => `<button class="cattile" data-sec="${n}" title="${esc(t)}"><span class="ci">${ic(i)}</span><b>${esc(SECTSHORT[n] || t)}</b></button>`).join('')}
      <button class="cattile more" data-go="browse"><span class="ci">${ic('i-list')}</span><b>All 21 categories</b></button>
    </div>`;
  ecClear();
}
function track(n,p){ try{ if(window.gtag) gtag('event', n, p||{}); }catch(e){} }
let calcTracked = false;
let lastShown = { q: null, n: 0 }; // last count shown by renderResults(), reused by remember() for hs_search
// Answer card: the best match drawn as a picture before the list — what it costs to bring in, where Nepal buys it,
// and the trend. Uses the same tax data as the detail sheet (int.json totals by origin) and trade data (st.json).
function costSplit(code, r, k){
  // k: index into totals (0 India, 3 other countries). Returns {duty, vat, total} for NPR 1,00,000 CIF, or null.
  const TI = taxInfo(code), base = 100000;
  if (TI && TI.totals && TI.totals[k] != null){
    const T = base * TI.totals[k] / 100, v = (TI.vat || 0) / 100;
    const nonvat = v ? (T - base * v) / (1 + v) : T;
    return { duty: Math.max(0, nonvat), vat: Math.max(0, T - Math.max(0, nonvat)), total: T, excise: TI.excise != null || TI.fees.length > 0 };
  }
  // no official total: compute the same way calc() does — duty, then excise, then fees, then VAT
  const n = num(k === 0 ? (r.s || r.g) : r.g); if (isNaN(n)) return null;
  const cd = base * n / 100, ex = TI && TI.excise != null ? (base + cd) * TI.excise / 100 : 0;
  let fees = 0; if (TI && TI.fees.length){ let b = base + cd + ex; TI.fees.forEach(f => { const a = b * f.rate / 100; fees += a; b += a; }); }
  const vat = (TI && TI.vat === 0) ? 0 : (base + cd + ex + fees) * ((TI && TI.vat) || 13) / 100;
  return { duty: cd + ex + fees, vat, total: cd + ex + fees + vat, excise: ex > 0 || fees > 0 };
}
/* family ladder: every line in the heading, its duty as a bar, and only the words that decide between them */
function famWords(x, me){ const p = [...x.path, x.d], m = [...me.path, me.d]; let k = 0;
  while (k < Math.min(p.length, m.length) - 1 && p[k] === m[k]) k++;
  return p.slice(k).map(s => /^others?$/i.test(s.trim()) ? 'Other (none of the above)' : s); }
function famShared(x, me){ const p = [...x.path, x.d], m = [...me.path, me.d]; let k = 0; while (k < Math.min(p.length, m.length) && p[k] === m[k]) k++; return k; }
function famCheaper(r){ const sib = BYHEAD[r.h] || [], mine = num(rateOf(r)); if (isNaN(mine)) return [];
  return sib.filter(x => x.code !== r.code && !isNaN(num(rateOf(x))) && num(rateOf(x)) < mine)
    .sort((a, b) => famShared(b, r) - famShared(a, r) || num(rateOf(a)) - num(rateOf(b))); }
let famOrd = 'd', famStep = null, famFor = null;
function familyHTML(r){
  const sib = BYHEAD[r.h] || []; if (sib.length < 2) return '';
  if (famFor !== r.h){ famFor = r.h; famStep = null; }
  const N = x => { const n = num(rateOf(x)); return isNaN(n) ? 1e9 : n; };
  const key = x => { const n = num(rateOf(x)); return isNaN(n) ? 'spec' : String(n); };
  const tone = v => { const n = num(v); return isNaN(n) ? 'sp' : n === 0 ? 'fr' : n <= 10 ? 'lo' : n <= 20 ? 'md' : 'hi'; };
  const chip = v => `<span class="fl-chip ${tone(v)}">${esc(pct(v))}</span>`;
  // overall border tax (customs + excise + VAT + fees) from the official integrated tariff: index 3 = other countries, 0 = India
  const all = (x, k) => { const T = (INT[x.code] || {}).t; return T && T[k] != null ? `<small class="fl-all">${T[k]}% total</small>` : ''; };
  const fix = s => /^others?$/i.test(s.trim()) ? 'Other (none of the above)' : s;
  const vals = sib.map(x => num(rateOf(x))).filter(v => !isNaN(v)), lo = Math.min(...vals), hi = Math.max(...vals), mine = num(rateOf(r));
  // 1. staircase: one step per duty rate, this line's step marked; a step filters the table
  const steps = {}; sib.forEach(x => { (steps[key(x)] = steps[key(x)] || []).push(x); });
  const ks = Object.keys(steps).sort((a, b) => (a === 'spec') - (b === 'spec') || a - b);
  let h = '';
  if (ks.length > 1) h += `<div class="fl-stairs" role="group" aria-label="Duty rates in this family">${ks.map(k => { const n = k === 'spec' ? NaN : +k, me = key(r) === k, c = steps[k].length;
      return `<button class="fl-step ${tone(rateOf(steps[k][0]))}${me ? ' me' : ''}${famStep === k ? ' sel' : ''}" data-famstep="${k}" aria-pressed="${famStep === k}" style="height:${isNaN(n) ? 34 : 34 + Math.round(70 * n / Math.max(hi, 1))}px">${me ? '<em>This line</em>' : ''}<b>${isNaN(n) ? 'Per unit' : esc(pct(rateOf(steps[k][0])))}</b><small>${c} line${c === 1 ? '' : 's'}</small></button>`; }).join('')}</div>
    <p class="fine" style="margin:6px 0 10px">Each step is a duty rate in this family. Tap a step to see only its lines.</p>`;
  else h += `<p class="fine" style="margin:0 0 10px">Every line in this family pays the same duty.</p>`;
  // 2. table
  let list = famOrd === 'd' ? sib.map((x, i) => [x, i]).sort((a, b) => N(a[0]) - N(b[0]) || a[1] - b[1]).map(a => a[0]) : sib;
  if (famStep !== null) list = list.filter(x => key(x) === famStep);
  const rows = list.map(x => { const me = x.code === r.code, pth = [...x.path, x.d].map(fix), k = pth.length > 2 && pth[pth.length - 1].length < 28 ? 2 : 1;
    return `<button class="fl-r${me ? ' cur' : ''}" data-code="${x.code}"${me ? ' aria-current="true"' : ''}><span class="c">${x.code}${me ? '<em class="fl-b">This line</em>' : ''}</span><span class="n">${chip(x.g)}${all(x, 3)}</span><span class="n">${chip(x.s)}${all(x, 0)}</span><span class="d"><b>${esc(pth.slice(-k).join(' › '))}</b>${pth.length > k ? `<small>${esc(pth.slice(0, -k).join(' › '))}</small>` : ''}</span></button>`; }).join('');
  h += `<div class="fl-tools" role="group" aria-label="Order"><button data-famord="d" class="${famOrd === 'd' ? 'on' : ''}">Lowest duty first</button><button data-famord="o" class="${famOrd === 'o' ? 'on' : ''}">Tariff order</button></div>
    <div class="fl-tb"><div class="fl-h"><span>HS code and what the goods must be</span><span>General</span><span>SAARC</span></div>${rows}</div>`;
  // 3. closest cheaper lines, each with its condition
  const cards = [], sa = num(r.s), ge = num(r.g);
  if (!isNaN(sa) && !isNaN(ge) && sa < ge) cards.push(`<div class="fl-card">${chip(r.s)}<span class="was">instead of ${esc(pct(r.g))}</span><b>Same goods, made in India or SAARC</b><span class="if">Needs a SAFTA certificate of origin. The code stays ${r.code}.</span></div>`);
  famCheaper(r).slice(0, 3).forEach(x => cards.push(`<button class="fl-card" data-code="${x.code}">${chip(rateOf(x))}<span class="was">instead of ${esc(pct(rateOf(r)))}</span><b class="mono">HS ${x.code}</b><span class="if">Only if your goods are: ${esc(famWords(x, r).join(' › '))}</span></button>`));
  if (cards.length) h += `<h3 class="h" style="margin-top:14px">Closest lines with lower duty, and the condition for each</h3><div class="fl-cards">${cards.join('')}</div>`;
  const notes = [];
  if (!isNaN(mine) && mine === lo && ks.length > 1) notes.push('This line already has the lowest duty in its family.');
  notes.push('The chip is customs duty. “Total” under it is everything charged at the border (customs duty, excise, VAT and other fees) as a share of CIF value, for goods from other countries and from India.');
  notes.push('Declaring a lower-duty line that does not match the goods leads to reclassification, the duty difference and a fine. When unsure, ask the Department of Customs for an advance ruling.');
  return h + `<p class="fine" style="margin:8px 0 0">${notes.join(' ')}</p>`;
}
/* average declared import value per unit: official value / official quantity (a yardstick, not a price list) */
const UNIT_NAMES = { KG:'kg', PCS:'piece', SQM:'square metre', LTR:'litre', MTQ:'cubic metre', PAIR:'pair', PR:'pair', GRM:'gram', MTR:'metre', KL:'kilolitre', DZN:'dozen', TNE:'tonne', NOS:'piece', SET:'set' };
function unitLine(im){
  const u = UNIT_NAMES[String(im[1] || '').trim().toUpperCase()], q = +im[2], v = +im[3] * 1000;
  if (!u || !(q >= 10) || !(v > 0)) return '';
  const per = v / q, f = per >= 100 ? Math.round(per).toLocaleString('en-IN') : per >= 10 ? per.toFixed(1) : per.toFixed(2);
  return `<p class="ac-k" style="margin-top:8px">Average declared value</p><p style="margin:0"><b>Rs ${f}</b> per ${u} <span class="fine">(all grades and origins)</span></p>`;
}
function answerCard(r){
  try {
    const code = r.code, d = r.digits, im = ST.imports[d], hist = (typeof H !== 'undefined' && H.codes) ? H.codes[d] : null;
    const other = costSplit(code, r, 3), india = costSplit(code, r, 0);
    const bar = (lab, c) => { if (!c) return ''; const tot = 100000 + c.total;
      const seg = (cls, v, txt) => v > 0 ? `<i class="${cls}" style="flex:${v.toFixed(0)}" title="${txt}">${v / tot > 0.12 ? txt : ''}</i>` : '';
      return `<div class="ac-row"><div class="ac-l"><span>${lab}</span><b>${npr(tot)}</b></div><div class="ac-bar" role="img" aria-label="${lab}: goods NPR 1,00,000, duties ${npr(c.duty)}, VAT ${npr(c.vat)}">`
        + seg('g', 100000, 'Goods 1,00,000') + seg('d', c.duty, (c.excise ? 'Duty & excise ' : 'Duty ') + Math.round(c.duty).toLocaleString('en-IN')) + seg('v', c.vat, 'VAT ' + Math.round(c.vat).toLocaleString('en-IN')) + `</div></div>`; };
    const showIndia = india && other && Math.abs(india.total - other.total) > 1;
    const TIc = taxInfo(code), noVat = TIc && TIc.vat === 0;
    const extra = TIc && TIc.specific && (other || india) ? `<p class="fine" style="margin:6px 0 0">Plus a per-unit duty on this line — enter your quantity in the calculator for the full amount.</p>` : '';
    const specNote = !other && !india ? `<p class="fine" style="margin:0">This line has a per-unit (specific) duty: <b style="color:var(--fg)">${esc(rateOf(r) || 'see tariff')}</b>. Use the calculator with your quantity for the exact amount.</p>` : '';
    let h = `<article class="ac" aria-label="Best match">
      <div class="ac-top"><div><span class="ac-k">Best match</span><h3>${esc(label(r))}</h3><p class="ac-sub">${esc(r.head)}</p></div>
        <div class="ac-code"><span class="mono">${r.code}</span>${dutyTag(rateOf(r), true)}</div></div>
      <div class="ac-grid"><div><h4>What NPR 1,00,000 of goods costs you</h4>${specNote}${bar(showIndia ? 'From China &amp; others' : 'Landed cost', other || india)}${showIndia ? bar('From India with SAFTA certificate', india) : ''}
        ${specNote ? '' : `<p class="ac-key"><span><i class="g"></i>Goods (CIF)</span><span><i class="d"></i>Customs duty${other && other.excise ? ', excise &amp; fees' : ''}</span>${noVat ? '' : '<span><i class="v"></i>VAT</span>'}</p>`}${extra}</div>`;
    if (im && im[3] > 0){
      const top = (im[5] || []).slice(0, 3), m = top.length ? top[0][1] : 1;
      h += `<div><h4>Nepal imported ${rs(im[3], true)} last year</h4>${top.map(x => `<div class="ac-sup"><span>${esc(x[0])}</span><i style="width:${(x[1] / m * 100).toFixed(0)}%"></i><b>${Math.round(x[1] / im[3] * 100)}%</b></div>`).join('')}${unitLine(im)}`
        + (hist && hist.some(x => x[0]) ? `<p class="ac-k" style="margin-top:8px">Imports, FY ${FY[0]}–${FY[FY.length - 1]}</p>${sparkHTML(hist.map(x => x[0]), 0, '')}` : '') + `</div>`;
    } else h += `<div><h4>Nepal trade</h4><p class="fine" style="margin:0">No recorded imports under this exact line last year.</p></div>`;
    const ch = famCheaper(r);
    const famLine = !ch.length ? '' : `<p class="ac-fam">Lines in the same family start at <b>${esc(pct(rateOf(ch.slice().sort((a, b) => num(rateOf(a)) - num(rateOf(b)))[0])))}</b>. Whether one fits depends on what your goods are: <button class="lnk" data-code="${code}">compare the family</button>.</p>`;
    h += `</div>${famLine}<div class="ac-act"><button class="btn" data-code="${code}">Full details &amp; nearby lines</button><button class="btn ghost" data-calc="${code}">Calculate for my shipment</button></div>
      <p class="fine" style="margin:8px 0 0">Not your product? Pick the right line from the list below — the code depends on what it is made of and how it is used.</p></article>`;
    return h;
  } catch (e) { return ''; }
}
function renderResults(){
  const q = $('#q').value, has = !!q.trim();
  $('#qclear').hidden = !q;
  $('#hero').classList.toggle('compact', has);
  $('#toolbar').hidden = !has;
  const sug = has ? termSuggest(q) : [];
  $('#suggest').innerHTML = sug.map(t => `<button data-q="${esc(t)}">${ic('i-search')}${esc(t)}</button>`).join('');
  if (!has){ renderHome(); return; }
  $('#hero-stats').innerHTML = '';
  const res = search(q);
  const rows = res.rows.filter(r => passDuty(r) && (!chapF || r.ch === +chapF));
  lastShown = { q: q.trim(), n: rows.length };
  let html = '';
  if (res.aliases.length){
    const prefs = [...new Set(res.aliases.flatMap(a => a.pref))].slice(0, 5);
    html += `<div class="hint"><div class="t">${ic('i-bulb')}<span>“${esc(res.aliases[0].term)}” is usually found under</span></div><div class="opts">` +
      prefs.map(p => { const pd = p.replace(/\./g,''); const hk = pd.slice(0,2)+'.'+pd.slice(2,4);
        const r0 = ROWS.find(r => r.digits.startsWith(pd)); const cnt = ROWS.filter(r => r.digits.startsWith(pd)).length;
        const ht = (D.heads[hk] || [''])[0]; const txt = pd.length <= 4 ? ht : pd.length >= 8 && r0 ? label(r0) : (r0 && r0.path.length && !/^other$/i.test(r0.path[r0.path.length-1]) ? r0.path[r0.path.length-1] + ' · ' : '') + ht;
        const show = pd.length === 4 ? hk : p;
        return `<button class="opt" data-q="${show}"><span class="mono">${show}</span><span>${esc(txt)}</span><span class="c" style="font-size:.78rem;color:var(--muted)">${cnt}</span></button>`; }).join('') +
      `</div><p>A starting point. The exact line depends on what the product is, what it is made of and how it is used.</p></div>`;
  }
  if (res.kind === 'code'){
    const d = q.replace(/[^\d]/g,'');
    const hk = d.length >= 4 ? d.slice(0,2)+'.'+d.slice(2,4) : null;
    const title = hk && D.heads[hk] ? ['Heading ' + hk, D.heads[hk][0]] : D.chapters[+d.slice(0,2)] ? ['Chapter ' + (+d.slice(0,2)), D.chapters[+d.slice(0,2)].t] : null;
    if (title) html += `<div class="hint"><div class="t">${ic('i-info')}<span>${title[0]}</span></div><p style="margin:0;color:var(--fg);font-size:.92rem">${esc(title[1])}</p></div>`;
  }
  html += `<div class="count"><span><b>${rows.length.toLocaleString()}</b> matching code${rows.length === 1 ? '' : 's'}${res.loose ? ' (partial match)' : ''}</span><span>${origin === 'saarc' ? 'SAARC' : 'General'} duty</span></div>`;
  if (!rows.length){
    const tips = ['LED display','solar panel','mobile','cotton fabric','steel pipe'];
    html += `<div class="empty"><b>No codes match “${esc(q)}”</b><p>${dutyF !== 'all' || chapF ? 'A filter is hiding results. Clear it, or try' : 'Try the material (steel, plastic, cotton), what it does (pump, lamp, charger) or a shorter word. For example'}:</p><div class="suggest">${(dutyF !== 'all' || chapF ? '<button data-clear="1">Clear filters</button>' : '<button data-go="ai">' + ic('i-spark') + 'Ask the assistant</button>') + tips.map(t => `<button data-q="${t}">${t}</button>`).join('')}</div></div>`;
  } else {
    if (rows[0] && rows[0].digits && rows[0].digits.length === 8 && (res.kind !== 'code' || q.replace(/[^\d]/g,'').length >= 6)){
      // among the top few equally relevant lines, lead with the one Nepal actually imports most
      let best = rows[0];
      if (res.kind !== 'code'){ const v = r => (ST.imports[r.digits] || [0,0,0,0])[3] || 0; rows.slice(0, 5).forEach(r => { if (v(r) > v(best)) best = r; }); }
      html += answerCard(best);
    }
    html += res.kind === 'code' ? groupedHTML(rows.slice(0, shown), []) : groupedHTML(rows.slice(0, shown), res.words);
    if (rows.length > shown) html += `<button class="more" id="more">Show more codes ${ic('i-chev')}</button>`;
  }
  $('#results').innerHTML = html;
}
let tmr;
$('#q').addEventListener('input', () => { shown = 40; clearTimeout(tmr); tmr = setTimeout(renderResults, 110); });
$('#q').addEventListener('keydown', e => { if (e.key === 'Enter'){ $('#q').blur(); remember($('#q').value.trim()); } });
$('#qclear').addEventListener('click', () => { $('#q').value = ''; renderResults(); $('#q').focus(); });
// Matches the count line in renderResults(): search() + the duty-band and chapter filters in effect.
function shownCount(q){ if (lastShown.q === q) return lastShown.n; return search(q).rows.filter(r => passDuty(r) && (!chapF || r.ch === +chapF)).length; }
const searchLang = q => /[\u0900-\u097F]/.test(q) ? 'ne' : 'en';
function remember(q){ if (q.length < 2) return; const n = shownCount(q); track('hs_search', { search_term: q.slice(0,80), results: n, zero_results: n === 0, search_lang: searchLang(q) }); const r = store.get('recent', []).filter(x => x.toLowerCase() !== q.toLowerCase()); r.unshift(q); store.set('recent', r.slice(0, 6)); }
function runQuery(q){ $('#q').value = q; shown = 40; renderResults(); remember(q); window.scrollTo({top:0}); }
document.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.closest('#v-search') || b.closest('#suggest')){
    if (b.id === 'more'){ shown += 40; renderResults(); return; }
    if (b.dataset.clear){ dutyF = 'all'; chapF = ''; $('#fchap').value = ''; $$('[data-duty]').forEach(x => x.setAttribute('aria-pressed', x.dataset.duty === 'all')); renderResults(); return; }
    if (b.dataset.q !== undefined){ runQuery(b.dataset.q); return; }
    if (b.dataset.go){ go(b.dataset.go); return; }
    if (b.dataset.chap && b.classList.contains('cat')){ browseChap = +b.dataset.chap; go('browse'); return; }
    if (b.dataset.sec){ browseChap = null; browsePage = ''; browseQ = ''; openSec = b.dataset.sec; go('browse'); setTimeout(() => { const el = document.querySelector(`[data-sec="${b.dataset.sec}"][aria-expanded]`); if (el) el.scrollIntoView({ block: 'start' }); }, 50); return; }
    if (b.dataset.duty){ dutyF = b.dataset.duty; $$('[data-duty]').forEach(x => x.setAttribute('aria-pressed', x === b)); shown = 40; renderResults(); return; }
    if (b.dataset.calc){ remember($('#q').value.trim()); pickCalc(b.dataset.calc); go('calc', 'push'); window.scrollTo({ top: 0 }); return; }
    if (b.dataset.code){ remember($('#q').value.trim()); openDetail(b.dataset.code); if (b.classList.contains('lnk')){ const f = document.getElementById('sh-fam'); if (f) f.scrollIntoView({ block: 'start' }); } }
  }
});
const fchap = $('#fchap');
Object.keys(CHCOUNT).map(Number).sort((a,b)=>a-b).forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = `Ch ${c} · ${CHSHORT[c] || D.chapters[c].t.split(/[;,]/)[0]}`; fchap.appendChild(o); });
fchap.addEventListener('change', () => { chapF = fchap.value; shown = 40; renderResults(); });

function setOrigin(o){
  origin = o; store.set('origin', o);
  $('#o-gen').setAttribute('aria-pressed', o === 'gen'); $('#o-saarc').setAttribute('aria-pressed', o === 'saarc');
  renderResults(); if (curTab === 'browse') renderBrowse(); if (curTab === 'saved') renderSaved();
  if (calcRow) pickCalc(calcRow.code);
  if (curDetail) openDetail(curDetail, true);
}
$('#o-gen').onclick = () => setOrigin('gen'); $('#o-saarc').onclick = () => setOrigin('saarc');

/* ---------- detail ---------- */
let curDetail = null, lastFocus = null;
const npr = n => 'NPR ' + Math.round(n).toLocaleString('en-IN');
function openDetail(code, keep){
  const r = BY[code]; if (!r) return;
  if (!keep) track('view_hs_code', { hs_code: code });
  if (!keep) lastFocus = document.activeElement;
  curDetail = code;
  const sec = sectionOf(r.ch), chap = D.chapters[r.ch] || {}, exp = D.export[code];
  const v = rateOf(r), n = num(v), other = origin === 'saarc' ? r.g : r.s;
  const TI = taxInfo(code), effOther = TI && TI.totals ? TI.totals[3] : null, effIndia = TI && TI.totals ? TI.totals[0] : null;
  const combined = isNaN(n) ? null : ((1 + n/100) * 1.13 - 1) * 100;
  const sib = BYHEAD[r.h] || [];
  $('#sh-eb').textContent = `Chapter ${r.ch} · Heading ${r.h}`;
  $('#sh-body').innerHTML = `
    <div class="code-xl"><span class="mono" id="sh-title">${r.code}</span><button class="copy-sm" id="sh-copy">${ic('i-copy')}Copy</button></div>
    <p class="title">${esc(label(r))}</p>
    <p class="sub">${esc(r.head)}</p>
    <div class="glance">
      <div class="on"><span>${origin === 'saarc' ? 'SAARC' : 'General'} duty</span><b class="${isNaN(n) ? 'sm' : ''}">${esc(pct(v))}</b></div>
      <div><span>${origin === 'saarc' ? 'General' : 'SAARC'} duty</span><b class="${isNaN(num(other)) ? 'sm' : ''}">${esc(pct(other))}</b></div>
      <div><span>VAT</span><b>${TI && TI.vat === 0 ? 'Exempt' : (TI ? TI.vat : 13) + '%'}</b></div>
      <div><span>Unit</span><b class="sm" style="font-size:1rem">${esc(r.u || '–')}</b></div>
    </div>
    ${effOther !== null ? `<div class="outcome">${ic('i-info')}<div>Every <b>NPR 1,00,000</b> of goods (CIF) from other countries pays about <b>${npr(effOther * 1000)}</b> in all duties and taxes — a total effective rate of <b>${effOther}%</b>.${effIndia !== null && effIndia !== effOther ? ` From India it's <b>${effIndia}%</b>.` : ''}</div></div>`
      : combined !== null ? `<div class="outcome">${ic('i-info')}<div>Every <b>NPR 1,00,000</b> of goods (CIF) pays about <b>${npr(combined * 1000)}</b> in customs duty and VAT, or <b>${combined.toFixed(1)}%</b>.</div></div>`
      : `<div class="outcome">${ic('i-info')}<div>This line has a specific or special rate: <b>${esc(v || 'not stated in the tariff')}</b>. The calculator applies it from your quantity.</div></div>`}
    <h3 class="h">Duty &amp; taxes on this code</h3>
    ${taxBreakdown(code)}
    ${r.ldc ? `<p class="fine">Imports from Least Developed Countries: ${r.ldc}% duty.</p>` : ''}
    ${tradeCard(r.digits)}
    ${exp ? `<p class="fine">Export duty on this line: <b style="color:var(--fg)">${esc(exp[1])}</b>.</p>` : ''}
    <h3 class="h">Where it sits in the tariff</h3>
    <ol class="tree">
      <li><small>Section ${sec ? sec.n : ''}</small>${esc(sec ? sec.t : '')}</li>
      <li><small>Chapter ${r.ch}</small>${esc(chap.t || '')}</li>
      <li><small>Heading ${r.h}</small>${esc(r.head)}</li>
      ${r.path.map(p => `<li>${esc(p)}</li>`).join('')}
      <li class="me"><small>${r.code}</small>${esc(r.d)}</li>
    </ol>
    <h3 class="h" id="sh-fam">Same family: the ${sib.length} lines in heading ${r.h}</h3>
    ${familyHTML(r)}
    <h3 class="h">How import tax is worked out</h3>
    <div class="flow"><span>CIF value</span><i>+</i><span>Customs duty</span><i>+</i><span>Excise</span><i>→</i><span>VAT 13%</span><i>=</i><span>Landed cost</span></div>
    <p class="fine">Customs duty is charged on the CIF value. Excise, where it applies, is charged on value plus duty. VAT is charged on the total. SAARC rates generally need a valid certificate of origin.</p>
    ${chap.n ? `<h3 class="h">Legal notes</h3><details class="notes"><summary>Chapter ${r.ch} notes</summary><pre>${esc(reflow(chap.n))}</pre></details>` : ''}
    ${sourceNote(code)}`;
  const saved = store.get('saved', []).includes(code);
  $('#sh-save').classList.toggle('on', saved); $('#sh-save').setAttribute('aria-label', saved ? 'Remove from saved' : 'Save code');
  $('#sh-save').innerHTML = ic('i-bookmark').replace('<svg', saved ? '<svg style="fill:currentColor"' : '<svg');
  const was = $('#sheet').hidden;
  $('#sheet').hidden = false; $('#scrim').hidden = false; document.body.style.overflow = 'hidden';
  if (!keep) $('#sh-body').scrollTop = 0;
  if (was) $('#sh-x').focus();
  try { history.replaceState(null, '', '#hs-' + code); } catch(e){}
}
function closeDetail(){
  $('#sheet').hidden = true; $('#scrim').hidden = true; document.body.style.overflow = ''; curDetail = null;
  try{ history.replaceState(null, '', '#' + curTab); }catch(e){}
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
$('#scrim').onclick = closeDetail; $('#sh-x').onclick = closeDetail;
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('#sheet').hidden) closeDetail(); });
$('#sh-body').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return;
  if (b.id === 'sh-copy') return copy(curDetail, 'Copied ' + curDetail);
  if (b.dataset.famstep !== undefined){ famStep = famStep === b.dataset.famstep ? null : b.dataset.famstep; const st = $('#sh-body').scrollTop; openDetail(curDetail, true); $('#sh-body').scrollTop = st; return; }
  if (b.dataset.famord){ famOrd = b.dataset.famord; const st = $('#sh-body').scrollTop; openDetail(curDetail, true); $('#sh-body').scrollTop = st; return; }
  if (b.dataset.code) openDetail(b.dataset.code); });
$('#sh-save').onclick = () => { let s = store.get('saved', []); const had = s.includes(curDetail); s = had ? s.filter(x => x !== curDetail) : [curDetail, ...s]; store.set('saved', s); openDetail(curDetail, true); toast(had ? 'Removed from saved' : 'Saved'); if (curTab === 'saved') renderSaved(); };
$('#sh-link').onclick = () => copy(location.href.split('#')[0] + '#hs-' + curDetail, 'Link copied');
$('#sh-calc').onclick = () => { const c = curDetail; closeDetail(); pickCalc(c); go('calc'); };
function toast(t){ const el = $('#toast'); el.textContent = t; el.hidden = false; clearTimeout(el._t); el._t = setTimeout(() => el.hidden = true, 1800); }
function copy(text, msg){
  const fb = () => { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); try{ document.execCommand('copy'); toast(msg); }catch(e){ toast(text); } ta.remove(); };
  try { navigator.clipboard.writeText(text).then(() => toast(msg), fb); } catch(e){ fb(); }
}

/* ---------- browse ---------- */
let browseChap = null, openSec = null, browseQ = '', browsePage = '', offType = 'all', offProv = 'all';
const bmatch = r => { const q = browseQ.toLowerCase(); return r.digits.startsWith(q.replace(/\D/g,'')) && /\d/.test(q) || r.own.includes(q) || r.ctx.includes(q); };
function renderBrowse(){
  const v = $('#v-browse');
  if (browseChap){
    const c = browseChap, chap = D.chapters[c], sec = sectionOf(c);
    const heads = Object.keys(D.heads).filter(h => +h.slice(0,2) === c).sort();
    v.innerHTML = `<div class="page-h"><button class="back" id="b-back">${ic('i-left')}All chapters</button>
      <p style="margin-top:8px">Section ${sec.n} · Chapter ${c}</p><h2 style="text-wrap:balance;font-size:1.35rem;line-height:1.25;font-weight:800">${esc(CHSHORT[c] || chap.t)}</h2><p style="font-size:.88rem">${esc(chap.t)}</p></div>
      <div class="bfilter">${ic('i-search')}<input id="bq" type="search" placeholder="Filter within chapter ${c}…" aria-label="Filter codes in this chapter" value="${esc(browseQ)}"></div>
      ${chap.n && !browseQ ? `<details class="notes"><summary>Chapter notes</summary><pre>${esc(reflow(chap.n))}</pre></details>` : ''}
      ${heads.filter(h => !browseQ || (BYHEAD[h] || []).some(r => bmatch(r))).map(h => { const rs = BYHEAD[h] || []; let lastG = null;
        const shown = browseQ ? rs.filter(bmatch) : rs;
        return `<div class="head"><button data-h="${h}" aria-expanded="${!!browseQ}"><span class="hn">${h}</span><span class="ht">${esc(D.heads[h][0])} <small>· ${shown.length} code${shown.length === 1 ? '' : 's'}</small></span>${ic('i-chev')}</button>
        <div class="lines" ${browseQ ? '' : 'hidden'}>${shown.map(r => { const g = r.path.join(' › '); const gh = g && g !== lastG ? `<div class="gl">${esc(g)}</div>` : ''; lastG = g;
          return gh + `<button class="row" data-code="${r.code}"><span class="code">${r.code}</span><span class="d">${esc(r.d)}</span><span class="end">${dutyTag(rateOf(r))}</span></button>`; }).join('')}</div></div>`; }).join('')}
      ${!heads.length ? '<div class="empty"><b>Reserved chapter</b><p>Chapter 77 is kept for future use in the Harmonized System and has no codes.</p></div>' : ''}`;
    return;
  }
  const sq = browseQ.toLowerCase();
  if (browsePage === 'gri'){ v.innerHTML = `<div class="page-h"><button class="back" data-page="">${ic('i-left')}Browse</button><h2 style="margin-top:8px">Rules of classification</h2><p>The six General Rules for the Interpretation of the Harmonized System, as printed in the Customs Tariff 2026/27. Customs applies them in order.</p></div><div class="card"><pre style="white-space:pre-wrap;font:inherit;font-size:.92rem;line-height:1.6;margin:0">${esc(reflow(D.gri))}</pre></div><details class="notes" style="margin-top:var(--s3)"><summary>Abbreviations and symbols used in the tariff</summary><pre>${esc(D.abbr)}</pre></details>`; return; }
  if (browsePage === 'offices'){ const q = browseQ.toLowerCase(); const TY = { india: 'India border', china: 'China border', airport: 'Airport', dryport: 'Dry port', office: 'Head office' };
    const list = OF.offices.filter(o => (offType === 'all' || o.type === offType) && (offProv === 'all' || o.province === offProv) && (!q || [o.name, o.location, o.district, o.province, o.border, o.np].join(' ').toLowerCase().includes(q)));
    const provs = [...new Set(OF.offices.map(o => o.province))].sort();
    const chief = o => o.chief ? o.chief.replace(/^(\S+\.)\s*/, (m, r) => (OF.roles[r] ? OF.roles[r] + ' · ' : '')).replace(/श्री\s*/, '') : '';
    v.innerHTML = `<div class="page-h"><button class="back" data-page="">${ic('i-left')}Browse</button><h2 style="margin-top:8px">Customs offices</h2><p>${OF.offices.length} customs offices and border points of the Department of Customs, with addresses and contacts in English.</p></div>
      <div class="bfilter">${ic('i-search')}<input id="bq" type="search" placeholder="Find an office: Birgunj, Kerung, airport…" aria-label="Find a customs office" value="${esc(browseQ)}"></div>
      <div class="toolbar" style="padding-top:var(--s2)">${[['all', 'All'], ['india', 'India border'], ['china', 'China border'], ['airport', 'Airports'], ['dryport', 'Dry port']].map(([k, l]) => `<button class="chip" data-otype="${k}" aria-pressed="${offType === k}">${l}</button>`).join('')}
        <select class="chip" id="oprov" aria-label="Province">${['all', ...provs].map(p => `<option value="${p}" ${offProv === p ? 'selected' : ''}>${p === 'all' ? 'All provinces' : p + ' Province'}</option>`).join('')}</select></div>
      <p style="margin:var(--s2) 0 var(--s3);color:var(--muted);font-size:.86rem">${list.length} office${list.length === 1 ? '' : 's'}</p>
      <div class="off">${list.map(o => `<div class="card"><h3>${esc(o.name)}</h3><div class="np">${esc(o.np)}</div>
        <div class="meta"><span class="b-${o.type}">${TY[o.type]}</span><span>${esc(o.location)}${o.district && !o.location.includes(o.district) ? ', ' + esc(o.district) : ''}</span><span>${esc(o.province)}</span></div>
        ${o.border && o.type !== 'office' ? `<div class="chief">${esc(o.border)}</div>` : ''}
        <div class="ct">${o.phone ? `<a href="tel:${o.phone.replace(/[^\d+]/g, '')}">${ic('i-phone')}${esc(o.phone)}</a>` : ''}${o.mobile ? `<a href="tel:${o.mobile.replace(/[^\d+]/g, '')}">${ic('i-phone')}${esc(o.mobile)}</a>` : ''}${o.email ? `<a href="mailto:${o.email}">${ic('i-mail')}${esc(o.email)}</a>` : ''}</div>
        ${o.chief ? `<div class="chief">Head: ${esc(chief(o))}</div>` : ''}
        <div class="links">${o.stat && H.customs[o.stat] ? `<button data-cu="${esc(o.stat)}">${ic('i-chart')}Trade data</button>` : ''}${o.web ? `<a href="https://${o.web}" target="_blank" rel="noopener">${ic('i-up')}${esc(o.web)}</a>` : ''}</div></div>`).join('')}
      ${!list.length ? '<div class="empty"><b>No office matches</b><p>Try another name or clear the filters.</p></div>' : ''}</div>
      <p style="margin-top:var(--s4);font-size:.78rem;color:var(--muted)">Source: ${esc(OF.source)}. Office heads change on transfer; call ahead to confirm.</p>`; return; }
  if (browsePage === 'about'){ const d = OF.department;
    v.innerHTML = `<div class="page-h"><button class="back" data-page="">${ic('i-left')}Browse</button><h2 style="margin-top:8px">About Nepal Customs</h2><p>${esc(d.name)}</p></div>
      <div class="card"><h3 style="margin:0 0 var(--s3);font-size:1rem">Contact the department</h3><dl class="kv"><dt>Address</dt><dd>${esc(d.address)}</dd><dt>Phone</dt><dd><a href="tel:${d.phone.replace(/\D/g, '')}">${esc(d.phone)}</a></dd><dt>Toll-free</dt><dd><a href="tel:${d.toll_free.replace(/\D/g, '')}">${esc(d.toll_free)}</a></dd><dt>Email</dt><dd><a href="mailto:${d.email}">${esc(d.email)}</a></dd><dt>Website</dt><dd><a href="https://${d.website}" target="_blank" rel="noopener">${esc(d.website)}</a></dd><dt>Hours</dt><dd>${esc(d.hours)}</dd></dl></div>
      <div class="card"><h3 style="margin:0 0 6px;font-size:1rem">What the department does</h3><p style="margin:0;font-size:.92rem;line-height:1.6;color:var(--fg-2)">${esc(d.about)}</p></div>
      <div class="card"><h3 style="margin:0 0 6px;font-size:1rem">Vision</h3><p style="margin:0;font-size:.92rem;color:var(--fg-2)">${esc(d.vision)}</p><div class="vals">${d.values.map(x => `<span>${esc(x)}</span>`).join('')}</div></div>
      <div class="card"><h3 style="margin:0 0 6px;font-size:1rem">How import clearance works</h3><ol style="margin:0;padding-left:20px;font-size:.92rem;line-height:1.6;color:var(--fg-2)"><li>Goods arrive at a customs point (border, airport or dry port).</li><li>The importer or a licensed customs agent files a declaration in NECAS with the HS code, value, origin and invoices.</li><li>NECAS assesses customs duty, excise and VAT and assigns a risk lane (green, yellow or red).</li><li>Duty is paid electronically or at the bank counter; documents and goods are checked according to the lane.</li><li>Goods are released. Declarations can be audited after clearance.</li></ol><div class="suggest"><button data-page="offices">${ic('i-list')}Customs offices</button><button data-page="gri">${ic('i-info')}Rules of classification</button></div></div>
      <p style="margin-top:var(--s4);font-size:.78rem;color:var(--muted)">Source: ${esc(OF.source)}. Summarised in English from the department's Nepali pages.</p>`; return; }
  if (browsePage === 'export'){ const ks = Object.keys(D.export).sort(); const q = browseQ.toLowerCase();
    v.innerHTML = `<div class="page-h"><button class="back" data-page="">${ic('i-left')}Browse</button><h2 style="margin-top:8px">Export duty schedule</h2><p>${ks.length} lines carry export customs duty. No export duty applies to goods not listed here.</p></div>
      <div class="bfilter">${ic('i-search')}<input id="bq" type="search" placeholder="Filter export lines" aria-label="Filter export lines" value="${esc(browseQ)}"></div>
      <div class="group">${ks.filter(k => !q || k.includes(q) || D.export[k][0].toLowerCase().includes(q) || (BY[k] && BY[k].own.includes(q))).map(k => `<button class="row" data-code="${k}"><span class="code">${k}</span><span class="d">${esc(BY[k] ? label(BY[k]) : D.export[k][0])}</span><span class="end"><span class="duty d-spec"><b>${esc(D.export[k][1])}</b></span></span></button>`).join('')}</div>`; return; }
  v.innerHTML = `<div class="page-h"><h2>Browse the tariff</h2><p>21 sections and 97 chapters. Open a section, pick a chapter, then open a heading to see its codes.</p></div>
    <div class="bfilter">${ic('i-search')}<input id="bq" type="search" placeholder="Find a chapter: textiles, machinery, 85…" aria-label="Find a chapter" value="${esc(browseQ)}"></div>
    ${browseQ ? '' : `<div class="cats" style="margin-bottom:var(--s3)"><button class="cat" data-page="gri"><span class="ic">${ic('i-info')}</span><span>Rules of classification<small>General Rules 1–6</small></span></button><button class="cat" data-page="export"><span class="ic">${ic('i-up')}</span><span>Export duty schedule<small>${Object.keys(D.export).length} lines</small></span></button><button class="cat" data-page="offices"><span class="ic">${ic('i-list')}</span><span>Customs offices<small>${OF.offices.length} offices · contacts</small></span></button><button class="cat" data-page="about"><span class="ic">${ic('i-info')}</span><span>About Nepal Customs<small>Department, hours, NECAS</small></span></button></div>`}` +
    D.sections.filter(s => !sq || s.t.toLowerCase().includes(sq) || Object.keys(D.chapters).some(c => sectionOf(+c) === s && (D.chapters[c].t.toLowerCase().includes(sq) || c === sq))).map(s => { const chs = Object.keys(D.chapters).map(Number).filter(c => sectionOf(c) === s).sort((a,b)=>a-b); const open = openSec === s.n;
      const sh = (SECT.find(x => x[0] === s.n) || [0, 0, s.t])[2];
      return `<div class="acc"><button data-sec="${s.n}" aria-expanded="${open}"><span class="num">${s.n}</span><span class="t">${esc(sh)}<small>${chs[0] === chs[chs.length-1] ? 'Chapter ' + chs[0] : 'Chapters ' + chs[0] + '–' + chs[chs.length-1]} · ${esc(s.t.length > 90 ? s.t.slice(0, 88) + '…' : s.t)}</small></span>${ic('i-chev')}</button>
      <div class="body" ${open ? '' : 'hidden'}>${s.n && s.n !== undefined && s.notes ? `<details class="notes" style="margin:var(--s2)"><summary>Section ${s.n} notes</summary><pre>${esc(reflow(s.notes))}</pre></details>` : ''}${chs.filter(c => !sq || D.chapters[c].t.toLowerCase().includes(sq) || String(c) === sq || s.t.toLowerCase().includes(sq)).map(c => `<button class="chap" data-chapter="${c}"><span class="num">${String(c).padStart(2,'0')}</span><span><b style="font-weight:700">${esc(CHSHORT[c] || D.chapters[c].t)}</b><small style="display:block;color:var(--muted);font-size:.78rem;line-height:1.3">${esc(D.chapters[c].t.length > 80 ? D.chapters[c].t.slice(0, 78) + '…' : D.chapters[c].t)}</small></span><span class="c">${CHCOUNT[c] || 0}</span></button>`).join('')}</div></div>`; }).join('');
}
$('#v-browse').addEventListener('change', e => { if (e.target.id === 'oprov'){ offProv = e.target.value; renderBrowse(); } });
$('#v-browse').addEventListener('input', e => { if (e.target.id === 'bq'){ browseQ = e.target.value.trim(); const pos = e.target.selectionStart; renderBrowse(); const el = $('#bq'); if (el){ el.focus(); try{ el.setSelectionRange(pos, pos); }catch(x){} } } });
$('#v-browse').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.page !== undefined){ browsePage = b.dataset.page; browseQ = ''; renderBrowse(); window.scrollTo({top:0}); return; }
  if (b.dataset.otype){ offType = b.dataset.otype; renderBrowse(); return; }
  if (b.dataset.cu){ stView = 'customs'; go('stats'); window.scrollTo({top:0}); return; }
  if (b.id === 'b-back'){ browseChap = null; browseQ = ''; renderBrowse(); window.scrollTo({top:0}); return; }
  if (b.dataset.sec){ openSec = openSec === b.dataset.sec ? null : b.dataset.sec; renderBrowse(); return; }
  if (b.dataset.chapter){ browseChap = +b.dataset.chapter; browseQ = ''; openSec = sectionOf(browseChap).n; renderBrowse(); window.scrollTo({top:0}); return; }
  if (b.dataset.h){ const l = b.nextElementSibling; l.hidden = !l.hidden; b.setAttribute('aria-expanded', !l.hidden); return; }
  if (b.dataset.code) openDetail(b.dataset.code);
});

/* ---------- calculator ---------- */
let calcRow = null, calcTI = null;
function pickCalc(code){
  const r = BY[code]; if (!r) return;
  calcRow = r; calcTI = taxInfo(code); $('#c-code').value = r.code;
  const v = rateOf(r); $('#c-cd').value = isNaN(num(v)) ? '' : num(v);
  $('#c-ex').value = calcTI && calcTI.excise != null ? calcTI.excise : 0;
  if (calcTI) $('#c-vat').checked = calcTI.vat !== 0;
  $('#c-qtyu').textContent = `Tariff unit: ${r.u || '–'}. Used for cost per unit and per-unit duties.`;
  store.set('calcCode', code); calc();
}
$('#c-code').addEventListener('input', () => {
  const v = $('#c-code').value.trim(), d = v.replace(/[^\d]/g,'');
  if (d.length === 8){ const c = d.slice(0,4)+'.'+d.slice(4,6)+'.'+d.slice(6); if (BY[c]){ pickCalc(c); return; } }
  if (v.length >= 2) $('#c-dl').innerHTML = search(v).rows.slice(0, 12).map(r => `<option value="${r.code}">${esc(label(r).slice(0,70))}</option>`).join('');
});
$('#c-code').addEventListener('change', () => { const v = $('#c-code').value.trim(); if (BY[v]) pickCalc(v); });
['c-val','c-fx','c-frt','c-ins','c-qty','c-cd','c-ex','c-oth','c-vat'].forEach(id => $('#'+id).addEventListener('input', calc));
$('#c-cur').addEventListener('change', () => { if ($('#c-cur').value === 'NPR') $('#c-fx').value = 1; calc(); });
function specific(txt, av, qty){
  const rs = /Rs\.?\s*([\d,]+(?:\.\d+)?)/i.exec(txt); if (!rs) return null;
  const per = parseFloat(rs[1].replace(/,/g,'')), p = /or\s+(\d+(?:\.\d+)?)\s*Percent/i.exec(txt);
  const unit = (/Per\s+([a-z .]+?)\s*Rs/i.exec(txt) || [,'unit'])[1].trim();
  const byQty = per * (qty || 0) / (/thousand/i.test(unit) ? 1000 : 1), byPct = p ? av * parseFloat(p[1]) / 100 : 0;
  return { amt: Math.max(byQty, byPct), unit, per, p: p ? +p[1] : null, which: byPct > byQty ? 'the percentage' : 'the per-unit rate' };
}
function calc(){
  const r = calcRow, out = $('#c-out');
  const f = id => parseFloat($('#' + id).value) || 0;
  const val = f('c-val'), fx = f('c-fx'), frt = f('c-frt'), ins = f('c-ins'), qty = f('c-qty'), exp = f('c-ex'), oth = f('c-oth');
  const cdRaw = $('#c-cd').value, vatOn = $('#c-vat').checked;
  $('#c-picked').innerHTML = r ? `<div class="d"><b>${r.code}</b>${esc(label(r))}</div>${dutyTag(rateOf(r), true)}` : '<div class="d">Search for a code to load its duty rate.</div>';
  if (!val || !fx){ out.innerHTML = `<div class="empty" style="border:0"><b>Add the invoice value and exchange rate</b><p>Your tax breakdown and landed cost appear here.</p></div>`; return; }
  if (!calcTracked){ calcTracked = true; track('duty_calculate'); }
  const av = (val + frt + ins) * fx, raw = r ? rateOf(r) : '';
  const isSpec = r && isNaN(num(raw)) && cdRaw === '';
  let cd = 0, note = '';
  if (isSpec){ const s = specific(raw, av, qty);
    if (s){ cd = s.amt; note = `Rs. ${s.per.toLocaleString('en-IN')} per ${esc(s.unit)}${s.p ? ` or ${s.p}% of value, whichever is higher (using ${s.which})` : ''}`; }
    else note = 'Special rate: enter a duty % above'; }
  else { const p = parseFloat(cdRaw) || 0; cd = av * p / 100; note = `${p}% of CIF value`; }
  const ex = (av + cd) * exp / 100;
  let feeTot = 0; const feeRows = [];
  if (calcTI && calcTI.fees.length){ let base = av + cd + ex; calcTI.fees.forEach(f => { const amt = base * f.rate / 100; feeRows.push([f.label, f.rate, amt]); base += amt; feeTot += amt; }); }
  const vat = vatOn ? (av + cd + ex + feeTot) * 0.13 : 0, taxes = cd + ex + feeTot + vat, landed = av + taxes + oth;
  const seg = [['Goods (CIF)', av, 'var(--seg-goods)'], ['Customs duty', cd, 'var(--seg-duty)'], ['Excise', ex, 'var(--seg-excise)'], ['Special fees', feeTot, 'var(--seg-excise)'], ['VAT', vat, 'var(--seg-vat)'], ['Other costs', oth, 'var(--seg-other)']].filter(s => s[1] > 0);
  out.innerHTML = `
    <div class="big">
      <div class="main"><span>Landed cost</span><b>${npr(landed)}</b></div>
      <div><span>Import taxes</span><b>${npr(taxes)}</b></div>
      ${qty ? `<div><span>Per unit</span><b>${npr(landed / qty)}</b></div>` : ''}
      <div><span>Tax rate on CIF</span><b>${(taxes / av * 100).toFixed(1)}%</b></div>
    </div>
    <div class="stack" role="img" aria-label="Landed cost split">${seg.map(s => `<i style="width:${s[1] / landed * 100}%;background:${s[2]}"></i>`).join('')}</div>
    <p class="legcap">Share of landed cost</p>
    <div class="legend">${seg.map(s => `<span><i style="background:${s[2]}"></i>${s[0]} ${Math.round(s[1] / landed * 100)}%</span>`).join('')}</div>
    <table class="bk"><tbody>
      <tr><td>Goods value<small>${val.toLocaleString()} ${$('#c-cur').value} × ${fx}</small></td><td>${npr(val * fx)}</td></tr>
      <tr><td>Freight and insurance</td><td>${npr((frt + ins) * fx)}</td></tr>
      <tr class="sub"><td>CIF (assessable) value</td><td>${npr(av)}</td></tr>
      <tr><td>Customs duty<small>${note}</small></td><td>${npr(cd)}</td></tr>
      ${exp ? `<tr><td>Excise duty<small>${exp}% of CIF + customs duty</small></td><td>${npr(ex)}</td></tr>` : ''}
      ${feeRows.map(f => `<tr><td>${esc(f[0])}<small>${f[1]}% of CIF + duties</small></td><td>${npr(f[2])}</td></tr>`).join('')}
      ${vatOn ? `<tr><td>VAT<small>13% of CIF + customs duty${exp || feeTot ? ' + other taxes' : ''}</small></td><td>${npr(vat)}</td></tr>` : ''}
      ${oth ? `<tr><td>Other costs</td><td>${npr(oth)}</td></tr>` : ''}
      <tr class="total"><td>Estimated landed cost</td><td>${npr(landed)}</td></tr>
    </tbody></table>
    ${(() => { if (!r || isSpec) return ''; const g = num(r.g), s = num(r.s); if (isNaN(g) || isNaN(s) || g === s) return '';
        const alt = origin === 'saarc' ? g : s, altCd = av * alt / 100, altEx = (av + altCd) * exp / 100;
        let altFee = 0; if (calcTI && calcTI.fees.length){ let base = av + altCd + altEx; calcTI.fees.forEach(f => { const a = base * f.rate / 100; altFee += a; base += a; }); }
        const altLanded = av + altCd + altEx + altFee + (vatOn ? (av + altCd + altEx + altFee) * 0.13 : 0) + oth, diff = landed - altLanded;
        return `<div class="cmpo">${ic('i-info')}<div>${origin === 'saarc' ? 'Without a SAFTA certificate (general rate ' + g + '%)' : 'From India or SAARC with a SAFTA certificate (' + s + '%)'}: <b>${npr(altLanded)}</b> — ${diff > 0 ? 'you would save <b>' + npr(diff) + '</b>' : 'it would cost <b>' + npr(-diff) + '</b> more'}.</div></div>`; })()}
    ${isSpec && !qty ? `<div class="warn">${ic('i-alert')}<span>This code has a per-unit duty. Enter the quantity in ${esc(r.u)} to include it.</span></div>` : ''}
    ${calcTI && calcTI.sep.length ? `<p class="fine">Also collected at customs (not in the landed total above): ${calcTI.sep.map(s => `${esc(s.label)} ${s.rate}%`).join(', ')}.</p>` : ''}
    ${calcTI && calcTI.totals ? `<p class="fine">Official total effective rate — ${['India', 'other SAARC', 'Tibet', 'other countries'].map((nm, i) => calcTI.totals[i] != null ? `${nm} <b style="color:var(--fg)">${calcTI.totals[i]}%</b>` : '').filter(Boolean).join(' · ')}.</p>` : ''}
    ${sourceNote(r ? r.code : null)}
    <p class="fine">Exemptions and the current Finance Act can change these rates — check with customs or your clearing agent before pricing a shipment.</p>`;
}
function initCalc(){
  const c = store.get('calcCode', '8528.59.00');
  $('#c-val').value = 10000; $('#c-fx').value = 137; $('#c-frt').value = 600; $('#c-ins').value = 50; $('#c-qty').value = 1; $('#c-ex').value = 0; $('#c-oth').value = 0;
  pickCalc(BY[c] ? c : '8528.59.00');
}

/* ---------- invoice generator ---------- */
let invItems = [], invDoc = 'proforma', invReady = false, invBound = false, invSaveT = null;
const invDuty = code => { const r = BY[code]; if (!r) return null; const n = num(r.g); return isNaN(n) ? null : n / 100; };
const dutyLabel = hs => { const d = invDuty(hs); return d === 0 ? 'Free' : d == null ? (hs ? 'spec.' : '—') : Math.round(d * 100) + '%'; };
const blankItem = () => ({ desc: '', model: '', hs: '', qty: '', unit: 'PCS', price: '', note: '' });
const lineAmt = it => (parseFloat(it.qty) || 0) * (parseFloat(it.price) || 0);
const invCur = () => $('#inv-cur').value;
const fmtC = n => (Math.round(n * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function invRowHTML(it, i) {
  return `<tr data-i="${i}">
    <td class="c-sn">${i + 1}</td>
    <td class="c-desc" data-label="Description"><input value="${esc(it.desc || '')}" data-f="desc" placeholder="Product description"></td>
    <td class="c-model" data-label="Model"><input value="${esc(it.model || '')}" data-f="model" placeholder="Model / item code"></td>
    <td class="c-hs" data-label="HS code"><input value="${esc(it.hs || '')}" data-f="hs" placeholder="0000.00.00" autocomplete="off"></td>
    <td class="c-duty" data-label="Duty" data-duty>${dutyLabel(it.hs)}</td>
    <td class="c-num" data-label="Qty"><input value="${it.qty ?? ''}" data-f="qty" type="number" inputmode="decimal" min="0" step="any"></td>
    <td class="c-unit" data-label="Unit"><input value="${esc(it.unit || '')}" data-f="unit"></td>
    <td class="c-num" data-label="Unit price"><input value="${it.price ?? ''}" data-f="price" type="number" inputmode="decimal" min="0" step="any"></td>
    <td class="c-amt" data-label="Amount" data-amt>${fmtC(lineAmt(it))}</td>
    <td class="c-del"><button data-del aria-label="Remove line">${ic('i-x')}</button></td>
  </tr>`;
}
function renderInvRows() { $('#inv-rows').innerHTML = invItems.map(invRowHTML).join(''); }
function renderInvTotals() {
  const cur = invCur(), sub = invItems.reduce((a, it) => a + lineAmt(it), 0), disc = parseFloat($('#inv-disc').value) || 0, total = sub - disc;
  const fx = parseFloat($('#inv-fx').value) || 0, fr = (parseFloat($('#inv-freight').value) || 0) / 100, vat = (parseFloat($('#inv-vat').value) || 0) / 100;
  let cifn = 0, duty = 0;
  invItems.forEach(it => { const d = invDuty(it.hs) || 0, cif = lineAmt(it) * (1 + fr) * fx; cifn += cif; duty += Math.round(cif * d); });
  const vatN = Math.round((cifn + duty) * vat), tax = duty + vatN, landed = cifn + duty;
  $('#inv-tot').innerHTML = `
    <div class="row"><span>Sub-total</span><b>${cur} ${fmtC(sub)}</b></div>
    ${disc ? `<div class="row"><span>Less discount</span><b>− ${cur} ${fmtC(disc)}</b></div>` : ''}
    <div class="row big"><span>Invoice total</span><b>${cur} ${fmtC(total)}</b></div>
    <div class="row" style="margin-top:6px"><span>Est. customs duty</span><b>${npr(duty)}</b></div>
    <div class="row"><span>Est. VAT ${Math.round(vat * 100)}%</span><b>${npr(vatN)}</b></div>
    <div class="row"><span>Est. total import tax</span><b>${npr(tax)}</b></div>
    <div class="row big"><span>Est. landed cost (excl. VAT)</span><b>${npr(landed)}</b></div>`;
}
function invSchedule() { renderInvTotals(); clearTimeout(invSaveT); invSaveT = setTimeout(saveInvDraft, 600); }

function bindInvoice() {
  if (invBound) return; invBound = true;
  $('#inv-doc').addEventListener('click', e => { const b = e.target.closest('[data-doc]'); if (!b) return; invDoc = b.dataset.doc; $$('#inv-doc .segbtn').forEach(x => { const on = x.dataset.doc === invDoc; x.classList.toggle('on', on); x.setAttribute('aria-selected', on); }); $('#v-invoice').classList.toggle('dt-commercial', invDoc === 'commercial'); invSchedule(); });
  $('#inv-rows').addEventListener('input', e => { const tr = e.target.closest('tr'); if (!tr) return; const i = +tr.dataset.i, f = e.target.dataset.f; if (f === undefined) return; invItems[i][f] = e.target.value; if (f === 'hs') { tr.querySelector('[data-duty]').textContent = dutyLabel(e.target.value.trim()); } if (f === 'qty' || f === 'price') tr.querySelector('[data-amt]').textContent = fmtC(lineAmt(invItems[i])); invSchedule(); });
  $('#inv-rows').addEventListener('click', e => { const del = e.target.closest('[data-del]'); if (!del) return; const i = +del.closest('tr').dataset.i; invItems.splice(i, 1); if (!invItems.length) invItems.push(blankItem()); renderInvRows(); invSchedule(); });
  $('#inv-add').addEventListener('click', () => { invItems.push(blankItem()); renderInvRows(); const inps = $('#inv-rows').querySelectorAll('tr:last-child input'); if (inps[0]) inps[0].focus(); });
  ['inv-disc','inv-fx','inv-freight','inv-vat','inv-margin'].forEach(id => $('#' + id).addEventListener('input', invSchedule));
  $('#inv-cur').addEventListener('change', () => { if (invCur() === 'NPR') $('#inv-fx').value = 1; renderInvRows(); invSchedule(); });
  $('#inv-suggest').addEventListener('click', suggestHS);
  $('#inv-xlsx').addEventListener('click', downloadInvExcel);
  $('#inv-pdf').addEventListener('click', downloadInvPDF);
  $('#inv-clear').addEventListener('click', () => { if (invItems.some(it => it.desc || it.hs || it.price) || $('#inv-b-name').value || $('#inv-s-name').value) { if (!confirm('Clear this invoice and start a new blank one? This cannot be undone.')) return; } clearInvoice(); });
  $('#inv-file').addEventListener('change', e => { const f = e.target.files[0]; if (f) importInvoiceFile(f); e.target.value = ''; });
  const dz = $('#inv-drop');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag'); const f = e.dataTransfer.files[0]; if (f) importInvoiceFile(f); });
  [...'inv-s-name inv-s-addr inv-s-contact inv-b-name inv-b-addr inv-b-contact inv-b-pan inv-no inv-date inv-validity inv-term inv-origin inv-pol inv-entry inv-dest inv-mode inv-bk-name inv-bk-bank inv-bk-addr inv-bk-swift inv-bk-acct'.split(' ')].forEach(id => { const el = $('#' + id); if (el) el.addEventListener('input', () => { clearTimeout(invSaveT); invSaveT = setTimeout(saveInvDraft, 600); }); });
}
function initInvoice() {
  if (invReady) return; invReady = true;
  $('#inv-offices').innerHTML = OF.offices.map(o => `<option value="${esc(o.name)}"></option>`).join('');
  try { localStorage.removeItem('nphs.invDraft'); } catch (e) {}  // wipe any legacy persisted draft (pre session-storage)
  const draft = sstore.get('invDraft', null);
  if (draft && draft.items) { invItems = draft.items.map(it => Object.assign(blankItem(), it)); invDoc = draft.docType || 'proforma'; applyInvFields(draft.fields || {}); }
  if (!invItems.length) invItems = [blankItem(), blankItem(), blankItem()];
  $$('#inv-doc .segbtn').forEach(x => { const on = x.dataset.doc === invDoc; x.classList.toggle('on', on); x.setAttribute('aria-selected', on); });
  $('#v-invoice').classList.toggle('dt-commercial', invDoc === 'commercial');
  if (!$('#inv-date').value) $('#inv-date').value = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  renderInvRows(); renderInvTotals(); bindInvoice();
}
const INV_FIELDS = 'inv-s-name inv-s-addr inv-s-contact inv-b-name inv-b-addr inv-b-contact inv-b-pan inv-no inv-date inv-validity inv-term inv-origin inv-pol inv-entry inv-dest inv-mode inv-bk-name inv-bk-bank inv-bk-addr inv-bk-swift inv-bk-acct inv-cur inv-fx inv-freight inv-vat inv-margin inv-disc'.split(' ');
function collectInvFields() { const o = {}; INV_FIELDS.forEach(id => { const el = $('#' + id); if (el) o[id] = el.value; }); return o; }
function applyInvFields(o) { INV_FIELDS.forEach(id => { const el = $('#' + id); if (el && o[id] != null) el.value = o[id]; }); }
function saveInvDraft() { sstore.set('invDraft', { docType: invDoc, items: invItems, fields: collectInvFields() }); }
function clearInvoice() {
  sstore.del('invDraft');
  INV_FIELDS.forEach(id => { const el = $('#' + id); if (el && !['inv-cur', 'inv-fx', 'inv-freight', 'inv-vat', 'inv-margin', 'inv-disc'].includes(id)) el.value = ''; });
  $('#inv-fx').value = 140; $('#inv-freight').value = 10; $('#inv-vat').value = 13; $('#inv-margin').value = 25; $('#inv-disc').value = 0; $('#inv-cur').value = 'USD';
  $('#inv-date').value = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  invItems = [blankItem(), blankItem(), blankItem()];
  renderInvRows(); renderInvTotals();
  ['inv-upmsg', 'inv-ai-msg'].forEach(id => { const el = $('#' + id); if (el) el.hidden = true; });
  const p = $('#inv-parties'); if (p) p.open = false;
}
function invMsg(id, text, cls) { const el = $('#' + id); if (!el) return; el.hidden = false; el.className = 'upmsg' + (cls ? ' ' + cls : ''); el.textContent = text; }

function invData() {
  const g = id => ($('#' + id).value || '').trim(), n = id => parseFloat($('#' + id).value) || 0, cur = invCur();
  const items = invItems.filter(it => it.desc || it.hs || parseFloat(it.price)).map(it => ({ description: it.desc, model: it.model, hs: it.hs, qty: parseFloat(it.qty) || 0, unit: it.unit || 'PCS', unitPrice: parseFloat(it.price) || 0, duty: invDuty(it.hs), note: it.note || '' }));
  const d = { docType: invDoc, seller: { name: g('inv-s-name') || 'Exporter', address: g('inv-s-addr'), contact: g('inv-s-contact') },
    buyer: { name: g('inv-b-name') || 'Importer', address: g('inv-b-addr'), contact: g('inv-b-contact'), pan: g('inv-b-pan') },
    shipment: { piNo: g('inv-no'), date: g('inv-date'), validity: g('inv-validity'), currency: cur, priceTerm: g('inv-term'), origin: g('inv-origin'), pol: g('inv-pol'), entry: g('inv-entry'), dest: g('inv-dest'), mode: g('inv-mode') },
    assumptions: { fx: n('inv-fx') || 1, freightPct: n('inv-freight') / 100, vat: n('inv-vat') / 100, otherPct: 0, margin: n('inv-margin') / 100, discount: n('inv-disc') },
    declaration: 'We certify that this invoice shows the actual price and description of the goods, and that all particulars are true and correct.',
    items };
  if (g('inv-bk-name') || g('inv-bk-acct')) d.bank = { name: g('inv-bk-name'), bank: g('inv-bk-bank'), address: g('inv-bk-addr'), swift: g('inv-bk-swift'), account: g('inv-bk-acct') };
  if (invDoc === 'proforma' && g('inv-term')) d.terms = ['Payment by T/T through banking channel, quoting this invoice number.'];
  return d;
}

/* --- number to words (for amount chargeable) --- */
const INV_ONES = ['','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN','ELEVEN','TWELVE','THIRTEEN','FOURTEEN','FIFTEEN','SIXTEEN','SEVENTEEN','EIGHTEEN','NINETEEN'];
const INV_TENS = ['','','TWENTY','THIRTY','FORTY','FIFTY','SIXTY','SEVENTY','EIGHTY','NINETY'];
function invWords(n){ n = Math.floor(n); if (n === 0) return 'ZERO';
  const ch = x => x < 20 ? INV_ONES[x] : x < 100 ? INV_TENS[Math.floor(x/10)] + (x%10 ? '-' + INV_ONES[x%10] : '') : INV_ONES[Math.floor(x/100)] + ' HUNDRED' + (x%100 ? ' AND ' + ch(x%100) : '');
  let out = ''; for (const [v,name] of [[1e9,'BILLION'],[1e6,'MILLION'],[1e3,'THOUSAND'],[1,'']]) { if (n >= v){ out += (out ? ' ' : '') + ch(Math.floor(n/v)) + (name ? ' ' + name : ''); n %= v; } } return out.trim(); }
function invAmountWords(total, cur){ const d = Math.floor(total), c = Math.round((total-d)*100); return `${cur === 'USD' ? 'US DOLLARS' : cur} ${invWords(d)}${c ? ' AND CENTS ' + invWords(c) : ''} ONLY`; }

/* --- browser ExcelJS workbook (ported from the validated generator) --- */
function loadExcelJS(){ if (window.ExcelJS) return Promise.resolve(); if (loadExcelJS._p) return loadExcelJS._p;
  return loadExcelJS._p = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/exceljs@4.4.0/dist/exceljs.min.js'; s.onload = res; s.onerror = () => rej(new Error('Could not load the spreadsheet library (check your connection).')); document.head.appendChild(s); }); }
function dlBlob(blob, name){ const u = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 1500); }

function buildInvoiceWorkbook(data){
  const NAVY = 'FF0F172A', LIGHT = 'FFF1F5F9', ACCENT = 'FF1E3A8A', BORDER = 'FFCBD5E1';
  const thin = { style: 'thin', color: { argb: BORDER } }, box = { top: thin, left: thin, bottom: thin, right: thin };
  const wb = new ExcelJS.Workbook(); wb.creator = 'customsnepal.com'; wb.created = new Date();
  const A = data.assumptions, s = data.shipment, cur = s.currency;
  const items = data.items.map(it => ({ ...it, duty: it.duty != null ? it.duty : 0 }));
  const hcell = (c, t) => { c.value = t; c.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 9 }; c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: NAVY } }; c.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true }; c.border = box; };
  const money = (c, f) => { c.numFmt = f; c.alignment = { horizontal: 'right', vertical: 'middle' }; c.border = box; };
  // one invoice sheet per requested type (Proforma / Commercial)
  const addInvoiceSheet = (kind) => {
  const isCom = kind === 'commercial', title = isCom ? 'COMMERCIAL INVOICE' : 'PROFORMA INVOICE';
  const pi = wb.addWorksheet(isCom ? 'Commercial Invoice' : 'Proforma Invoice', { pageSetup: { paperSize: 9, orientation: 'portrait', fitToPage: true, fitToWidth: 1, fitToHeight: 0, margins: { left: 0.4, right: 0.4, top: 0.5, bottom: 0.5, header: 0.3, footer: 0.3 } } });
  pi.columns = [{ width: 5 }, { width: 34 }, { width: 12 }, { width: 13 }, { width: 6 }, { width: 6 }, { width: 12 }, { width: 13 }];
  let R = 1; const merge = (r, a, b) => pi.mergeCells(r, a, r, b);
  merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.name; pi.getCell(R, 1).font = { bold: true, size: 14, color: { argb: NAVY } }; pi.getCell(R, 1).alignment = { horizontal: 'center' }; pi.getRow(R).height = 20; R++;
  if (data.seller.address){ merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.address; pi.getCell(R, 1).alignment = { horizontal: 'center', wrapText: true }; pi.getCell(R, 1).font = { size: 8 }; R++; }
  if (data.seller.contact){ merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.contact; pi.getCell(R, 1).alignment = { horizontal: 'center' }; pi.getCell(R, 1).font = { size: 8 }; R++; }
  R++; merge(R, 1, 8); const tt = pi.getCell(R, 1); tt.value = title; tt.font = { bold: true, size: 13, color: { argb: 'FFFFFFFF' } }; tt.alignment = { horizontal: 'center', vertical: 'middle' }; tt.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: NAVY } }; pi.getRow(R).height = 20; R += 2;
  const rt = (l, v) => ({ richText: [{ font: { bold: true, size: 8 }, text: l + '  ' }, { font: { size: 8 }, text: String(v == null ? '' : v) }] });
  const bl = [{ t: 'APPLICANT / BUYER / CONSIGNEE:', b: 1 }, { t: data.buyer.name, b: 1 }, { t: data.buyer.address }, { t: data.buyer.contact }, { rt: rt('PAN / VAT No.:', data.buyer.pan || '') }].filter(x => x.b || x.rt || x.t);
  const sl = [['INVOICE NO.:', s.piNo], ['DATE:', s.date]]; if (!isCom && s.validity) sl.push(['VALIDITY:', s.validity]);
  sl.push(['CURRENCY:', cur]); if (s.priceTerm) sl.push(['PRICE TERM:', s.priceTerm]); if (s.origin) sl.push(['COUNTRY OF ORIGIN:', s.origin]);
  if (s.pol) sl.push(['PORT OF LOADING:', s.pol]); if (s.entry) sl.push(['ENTRY POINT:', s.entry]); if (s.dest) sl.push(['FINAL DESTINATION:', s.dest]); if (s.mode) sl.push(['MODE OF SHIPMENT:', s.mode]);
  const b0 = R;
  bl.forEach((l, i) => { pi.mergeCells(b0 + i, 1, b0 + i, 4); const c = pi.getCell(b0 + i, 1); if (l.rt) c.value = l.rt; else { c.value = l.t; c.font = { bold: !!l.b, size: 8 }; } c.alignment = { wrapText: true, vertical: 'top' }; });
  sl.forEach((row, i) => { pi.mergeCells(b0 + i, 5, b0 + i, 8); const c = pi.getCell(b0 + i, 5); c.value = rt(row[0], row[1]); c.alignment = { wrapText: true, vertical: 'top' }; });
  if (bl.length > 2) pi.getRow(b0 + 2).height = 22;
  R = b0 + Math.max(bl.length, sl.length) + 1;
  const head = ['SN', 'DESCRIPTION', 'ITEM / MODEL', 'H.S. CODE', 'QTY', 'UNIT', 'UNIT PRICE (' + cur + ')', 'AMOUNT (' + cur + ')'];
  head.forEach((h, i) => hcell(pi.getCell(R, i + 1), h)); pi.getRow(R).height = 26; R++;
  let sub = 0;
  items.forEach((it, i) => { const amt = Math.round(it.qty * it.unitPrice * 100) / 100; sub += amt;
    [i + 1, it.description, it.model || '', it.hs, it.qty, it.unit || 'PCS', it.unitPrice, amt].forEach((v, c) => { const cell = pi.getCell(R, c + 1); cell.value = v; cell.border = box; cell.font = { size: 8 }; cell.alignment = { vertical: 'middle', horizontal: c === 0 || c === 3 || c === 4 || c === 5 ? 'center' : c >= 6 ? 'right' : 'left', wrapText: c === 1 }; if (c >= 6) cell.numFmt = '#,##0.00'; }); R++; });
  const disc = A.discount || 0, total = Math.round((sub - disc) * 100) / 100;
  const trow = (l, v, bold) => { pi.mergeCells(R, 1, R, 7); const a = pi.getCell(R, 1); a.value = l; a.alignment = { horizontal: 'right' }; a.font = { bold: !!bold, size: 9 }; a.border = box; const b = pi.getCell(R, 8); b.value = v; money(b, '#,##0.00'); b.font = { bold: !!bold, size: 9 }; if (bold){ a.fill = b.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: LIGHT } }; } R++; };
  trow('SUB-TOTAL', sub); if (disc) trow('LESS: DISCOUNT', -disc); trow('TOTAL AMOUNT (' + cur + ')', total, true);
  merge(R, 1, 8); pi.getCell(R, 1).value = 'AMOUNT IN WORDS: ' + invAmountWords(total, cur); pi.getCell(R, 1).font = { italic: true, bold: true, size: 8 }; pi.getCell(R, 1).alignment = { wrapText: true }; pi.getRow(R).height = 22; R += 2;
  if (data.terms && data.terms.length){ merge(R, 1, 8); pi.getCell(R, 1).value = 'TERMS OF PAYMENT'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; data.terms.forEach(t => { merge(R, 1, 8); pi.getCell(R, 1).value = '• ' + t; pi.getCell(R, 1).font = { size: 8 }; pi.getCell(R, 1).alignment = { wrapText: true }; R++; }); R++; }
  if (data.bank && (data.bank.name || data.bank.account)){ merge(R, 1, 8); pi.getCell(R, 1).value = 'BENEFICIARY ACCOUNT DETAILS'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; [['BENEFICIARY:', data.bank.name], ['BENEFICIARY BANK:', data.bank.bank], ['BANK ADDRESS:', data.bank.address], ['SWIFT CODE:', data.bank.swift], ['ACCOUNT NO.:', data.bank.account]].filter(x => x[1]).forEach(row => { merge(R, 1, 8); pi.getCell(R, 1).value = rt(row[0], row[1]); pi.getCell(R, 1).alignment = { wrapText: true }; R++; }); R++; }
  merge(R, 1, 8); pi.getCell(R, 1).value = 'DECLARATION'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; merge(R, 1, 8); pi.getCell(R, 1).value = data.declaration; pi.getCell(R, 1).font = { size: 8, italic: true }; pi.getCell(R, 1).alignment = { wrapText: true }; pi.getRow(R).height = 22; R += 2;
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = 'ACCEPTED BY APPLICANT:'; pi.getCell(R, 1).font = { bold: true, size: 8 }; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = 'For and on behalf of ' + data.seller.name; pi.getCell(R, 5).font = { bold: true, size: 8 }; R += 3;
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = '__________________________'; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = '__________________________'; R++;
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = 'Authorised Signature & Company Stamp'; pi.getCell(R, 1).font = { size: 7, color: { argb: 'FF64748B' } }; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = 'Authorised Signature & Company Stamp'; pi.getCell(R, 5).font = { size: 7, color: { argb: 'FF64748B' } }; R += 2;
  merge(R, 1, 8); pi.getCell(R, 1).value = 'Prepared with customsnepal.com — Nepal customs tariff, duty & landed-cost tools. Estimate only; confirm final classification and taxes with the customs office or your clearing agent.'; pi.getCell(R, 1).font = { size: 7, italic: true, color: { argb: 'FF94A3B8' } }; pi.getCell(R, 1).alignment = { wrapText: true, horizontal: 'center' };
  };
  const chk = (id, def) => { const el = document.getElementById(id); return el ? el.checked : def; };
  if (chk('inv-sh-pi', data.docType === 'proforma')) addInvoiceSheet('proforma');
  if (chk('inv-sh-ci', data.docType === 'commercial')) addInvoiceSheet('commercial');
  if (!wb.worksheets.length) addInvoiceSheet(data.docType || 'proforma');

  // sheet: customs & landed cost
  if ($('#inv-lc').checked){
    const lc = wb.addWorksheet('Customs & Landed Cost', { pageSetup: { paperSize: 9, orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 } });
    lc.columns = [{ width: 4 }, { width: 26 }, { width: 12 }, { width: 5 }, { width: 11 }, { width: 11 }, { width: 12 }, { width: 6 }, { width: 13 }, { width: 12 }, { width: 12 }, { width: 14 }, { width: 15 }];
    let r2 = 1; lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = 'CUSTOMS DUTY, TAXES & LANDED COST (ESTIMATE)'; lc.getCell(r2, 1).font = { bold: true, size: 12, color: { argb: NAVY } }; r2++;
    lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = `Duty from Nepal Customs Tariff 2026/27. FX 1 ${cur} = NPR ${A.fx} · Freight+insurance ${(A.freightPct*100).toFixed(0)}% · VAT ${(A.vat*100).toFixed(0)}% · Target margin ${(A.margin*100).toFixed(0)}%.`; lc.getCell(r2, 1).font = { size: 8, italic: true, color: { argb: 'FF64748B' } }; r2 += 2;
    ['NO.','MODEL / DESC','NEPAL HS','DUTY %','EXW (' + cur + ')','CIF (' + cur + ')','CIF (NPR)','QTY','CUSTOMS DUTY','VAT ' + (A.vat*100).toFixed(0) + '%','TOTAL TAX','LANDED (excl VAT)','SELL/UNIT excl VAT'].forEach((h, i) => hcell(lc.getCell(r2, i + 1), h)); lc.getRow(r2).height = 26; r2++;
    const T = { exw: 0, cif: 0, cifn: 0, duty: 0, vat: 0, tax: 0, landed: 0 };
    items.forEach((it, i) => { const exw = it.qty * it.unitPrice, cif = exw * (1 + A.freightPct), cifn = cif * A.fx, duty = Math.round(cifn * it.duty), vat = Math.round((cifn + duty) * A.vat), tax = duty + vat, landed = cifn + duty, perU = it.qty ? landed / it.qty : 0, sell = A.margin < 1 ? perU / (1 - A.margin) : 0;
      T.exw += exw; T.cif += cif; T.cifn += cifn; T.duty += duty; T.vat += vat; T.tax += tax; T.landed += landed;
      [i + 1, it.model || it.description.slice(0, 24), it.hs, it.duty, exw, cif, cifn, it.qty, duty, vat, tax, landed, sell].forEach((v, c) => { const cell = lc.getCell(r2, c + 1); cell.value = v; cell.border = box; cell.font = { size: 8 };
        if (c === 0 || c === 2 || c === 7) cell.alignment = { horizontal: 'center', vertical: 'middle' };
        else if (c === 1) cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
        else if (c === 3){ cell.numFmt = '0%'; cell.alignment = { horizontal: 'center' }; }
        else if (c === 4 || c === 5) money(cell, '#,##0.00'); else money(cell, '#,##0'); }); r2++; });
    ['', 'TOTAL', '', '', T.exw, T.cif, T.cifn, items.reduce((a, x) => a + x.qty, 0), T.duty, T.vat, T.tax, T.landed, ''].forEach((v, c) => { const cell = lc.getCell(r2, c + 1); cell.value = v; cell.border = box; cell.font = { bold: true, size: 8 }; cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: LIGHT } }; if (c === 4 || c === 5) money(cell, '#,##0.00'); else if (c >= 6 && c !== 7) money(cell, '#,##0'); else cell.alignment = { horizontal: 'center' }; }); r2 += 2;
    ['Customs duty = CIF (NPR) × tariff rate.  VAT = (CIF + customs duty) × rate.', 'Landed cost excludes VAT (claimable as input credit by a VAT-registered importer).', 'Freight + insurance spread across value; replace with your forwarder’s actual split for a firmer figure.', 'Estimate only — confirm classification, excise and other levies with the customs office or your clearing agent.'].forEach(t => { lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = '• ' + t; lc.getCell(r2, 1).font = { size: 8, color: { argb: 'FF475569' } }; r2++; });
  }
  // sheet 3: HS code review (AI notes)
  if ($('#inv-hsr').checked && items.some(it => it.note)){
    const hr = wb.addWorksheet('HS Code Review', { pageSetup: { orientation: 'landscape', fitToWidth: 1, fitToHeight: 0 } });
    hr.columns = [{ width: 4 }, { width: 30 }, { width: 12 }, { width: 8 }, { width: 70 }]; let r3 = 1;
    hr.mergeCells(r3, 1, r3, 5); hr.getCell(r3, 1).value = 'HS CODE REVIEW — Nepal Customs Tariff 2026/27 (AI suggestions)'; hr.getCell(r3, 1).font = { bold: true, size: 12, color: { argb: NAVY } }; r3 += 2;
    ['NO.', 'DESCRIPTION', 'NEPAL HS', 'DUTY %', 'CLASSIFICATION BASIS / NOTE'].forEach((h, i) => hcell(hr.getCell(r3, i + 1), h)); r3++;
    items.forEach((it, i) => { [i + 1, it.description, it.hs, it.duty, it.note || ''].forEach((v, c) => { const cell = hr.getCell(r3, c + 1); cell.value = v; cell.border = box; cell.font = { size: 8 }; cell.alignment = { vertical: 'top', wrapText: c === 1 || c === 4, horizontal: c === 0 || c === 2 || c === 3 ? 'center' : 'left' }; if (c === 3) cell.numFmt = '0%'; }); r3++; });
    hr.mergeCells(r3 + 1, 1, r3 + 1, 5); hr.getCell(r3 + 1, 1).value = 'AI-assisted suggestions from the Nepal tariff — verify with the customs office or your clearing agent before declaring.'; hr.getCell(r3 + 1, 1).font = { size: 8, italic: true, color: { argb: 'FF64748B' } };
  }
  // disclaimer sheet (always last)
  const dc = wb.addWorksheet('Disclaimer', { pageSetup: { orientation: 'portrait', fitToWidth: 1, fitToHeight: 0, margins: { left: 0.6, right: 0.6, top: 0.6, bottom: 0.6, header: 0.3, footer: 0.3 } } });
  dc.columns = [{ width: 104 }]; let d1 = 1;
  dc.getCell(d1, 1).value = 'IMPORTANT — PLEASE READ (DISCLAIMER)'; dc.getCell(d1, 1).font = { bold: true, size: 13, color: { argb: NAVY } }; d1 += 2;
  const dp = t => { dc.getCell(d1, 1).value = t; dc.getCell(d1, 1).font = { size: 10, color: { argb: 'FF334155' } }; dc.getCell(d1, 1).alignment = { wrapText: true, vertical: 'top' }; dc.getRow(d1).height = Math.max(16, Math.ceil(t.length / 96) * 14); d1 += 2; };
  dp('This workbook is a computer-generated planning aid prepared with customsnepal.com. The Proforma Invoice and Commercial Invoice sheets are DRAFTS built from the details you entered or uploaded — verify every party name, address, bank detail, quantity, price and HS code before issuing or submitting them anywhere.');
  dp('The Customs Duty & Landed Cost figures are an APPROXIMATE ESTIMATE. Customs duty is applied at the general Nepal Customs Tariff 2026/27 rate for each HS code, and VAT at ' + (A.vat * 100).toFixed(0) + '% on (CIF + customs duty). The estimate does NOT capture every case: the final amount payable depends on the customs officer’s valuation and classification, the exchange rate on the declaration date, excise duty, agriculture / road / infrastructure and other levies, advance income tax, exemptions, anti-dumping or safeguard duties, and any SAARC/BIMSTEC preferential rate or fees charged by your agent or bank.');
  dp('HS-code suggestions, where shown, are AI-assisted from the Nepal tariff text and can be wrong for your specific goods. Classification is ultimately decided by the Department of Customs, and an incorrect code may lead to re-assessment, fines or seizure.');
  dp('Before relying on any figure in this file for pricing, a letter of credit, a bank submission or customs clearance, CROSS-CHECK with the Department of Customs (customs.gov.np), a licensed customs clearing agent, your bank, or another competent authority. customsnepal.com and its authors accept no liability for any decision made on the basis of this file.');
  dp('Duty source: Department of Customs, Government of Nepal — Customs Tariff 2026/27 (HS 2022 nomenclature). Prepared ' + new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) + ' · customsnepal.com');
  return wb;
}
async function downloadInvExcel(){
  const d = invData(); if (!d.items.length){ invMsg('inv-ai-msg', 'Add at least one line item (description or price) first.', 'err'); return; }
  const btn = $('#inv-xlsx'), old = btn.innerHTML; btn.disabled = true; btn.textContent = 'Building…';
  try { await loadExcelJS(); const wb = buildInvoiceWorkbook(d); const buf = await wb.xlsx.writeBuffer(); const names = wb.worksheets.map(w => w.name); dlBlob(new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }), 'Invoice_Master_' + (d.shipment.piNo || 'draft').replace(/[^\w-]+/g, '_') + '.xlsx'); invMsg('inv-ai-msg', 'Master file downloaded — sheets: ' + names.join(', ') + '.', 'ok'); saveInvDraft(); track('invoice_generate', { format:'excel' }); }
  catch (e){ invMsg('inv-ai-msg', 'Could not build the Excel file: ' + (e && e.message || e), 'err'); }
  finally { btn.disabled = false; btn.innerHTML = old; }
}
/* --- PDF via print --- */
function invHTML(d){
  const s = d.shipment, cur = s.currency, A = d.assumptions, isCom = d.docType === 'commercial', title = isCom ? 'COMMERCIAL INVOICE' : 'PROFORMA INVOICE';
  let sub = 0; const rows = d.items.map((it, i) => { const amt = it.qty * it.unitPrice; sub += amt; return `<tr><td class=c>${i+1}</td><td>${esc(it.description)}</td><td>${esc(it.model||'')}</td><td class=c>${esc(it.hs||'')}</td><td class=r>${it.qty}</td><td class=c>${esc(it.unit||'PCS')}</td><td class=r>${fmtC(it.unitPrice)}</td><td class=r>${fmtC(amt)}</td></tr>`; }).join('');
  const disc = A.discount || 0, total = sub - disc;
  const kv = (l, v) => v ? `<div><b>${l}</b> ${esc(v)}</div>` : '';
  const bank = d.bank && (d.bank.name || d.bank.account) ? `<h3>Beneficiary account details</h3><div class=blk>${kv('Beneficiary:', d.bank.name)}${kv('Bank:', d.bank.bank)}${kv('Address:', d.bank.address)}${kv('SWIFT:', d.bank.swift)}${kv('Account:', d.bank.account)}</div>` : '';
  const terms = d.terms && d.terms.length ? `<h3>Terms of payment</h3><ul>${d.terms.map(t => '<li>' + esc(t) + '</li>').join('')}</ul>` : '';
  return `<!doctype html><html><head><meta charset=utf-8><title>${title} ${esc(s.piNo||'')}</title><style>
    *{box-sizing:border-box}body{font:12px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;margin:28px;max-width:800px}
    h1{text-align:center;margin:0;font-size:18px}.sub{text-align:center;font-size:10px;color:#475569;margin:2px 0 12px}
    .title{background:#0f172a;color:#fff;text-align:center;padding:7px;font-weight:700;letter-spacing:1px;margin:10px 0}
    .grid{display:flex;justify-content:space-between;gap:24px;font-size:11px}.grid>div{flex:1}.grid b{font-weight:700}
    table{width:100%;border-collapse:collapse;margin:14px 0;font-size:11px}th,td{border:1px solid #cbd5e1;padding:5px 7px}th{background:#0f172a;color:#fff;font-size:10px}
    td.r,th.r{text-align:right}td.c,th.c{text-align:center}tfoot td{font-weight:700;background:#f1f5f9}
    h3{font-size:11px;color:#1e3a8a;margin:14px 0 4px}.blk div,ul{font-size:11px}ul{margin:4px 0;padding-left:18px}
    .words{font-style:italic;font-weight:700;font-size:11px;margin:6px 0}
    .sign{display:flex;justify-content:space-between;margin-top:40px;font-size:10px;color:#475569}.sign div{width:45%;border-top:1px solid #94a3b8;padding-top:4px}
    .foot{margin-top:24px;font-size:9px;color:#94a3b8;text-align:center;font-style:italic}
    @media print{body{margin:0;padding:16px}}
  </style></head><body>
    <h1>${esc(d.seller.name)}</h1><div class=sub>${esc(d.seller.address||'')}${d.seller.contact ? ' · ' + esc(d.seller.contact) : ''}</div>
    <div class=title>${title}</div>
    <div class=grid>
      <div><b>APPLICANT / BUYER / CONSIGNEE</b><br>${esc(d.buyer.name)}<br>${esc(d.buyer.address||'')}<br>${esc(d.buyer.contact||'')}${d.buyer.pan ? '<br>PAN/VAT: ' + esc(d.buyer.pan) : ''}</div>
      <div>${kv('Invoice No.:', s.piNo)}${kv('Date:', s.date)}${!isCom ? kv('Validity:', s.validity) : ''}${kv('Currency:', cur)}${kv('Price term:', s.priceTerm)}${kv('Country of origin:', s.origin)}${kv('Port of loading:', s.pol)}${kv('Entry point:', s.entry)}${kv('Final destination:', s.dest)}${kv('Mode:', s.mode)}</div>
    </div>
    <table><thead><tr><th class=c>SN</th><th>Description</th><th>Model</th><th class=c>H.S. Code</th><th class=r>Qty</th><th class=c>Unit</th><th class=r>Unit price</th><th class=r>Amount (${cur})</th></tr></thead>
    <tbody>${rows}</tbody>
    <tfoot><tr><td colspan=7 class=r>SUB-TOTAL</td><td class=r>${fmtC(sub)}</td></tr>${disc ? `<tr><td colspan=7 class=r>LESS: DISCOUNT</td><td class=r>-${fmtC(disc)}</td></tr>` : ''}<tr><td colspan=7 class=r>TOTAL (${cur})</td><td class=r>${fmtC(total)}</td></tr></tfoot></table>
    <div class=words>Amount in words: ${invAmountWords(total, cur)}</div>
    ${terms}${bank}
    <h3>Declaration</h3><div style="font-size:11px;font-style:italic">${esc(d.declaration)}</div>
    <div class=sign><div>Accepted by applicant<br>&nbsp;</div><div>For and on behalf of ${esc(d.seller.name)}<br>&nbsp;</div></div>
    <div class=foot>Prepared with customsnepal.com — Nepal customs tariff, duty &amp; landed-cost tools. Estimate only; confirm final classification and taxes with the customs office or your clearing agent.</div>
  </body></html>`;
}
function downloadInvPDF(){
  const d = invData(); if (!d.items.length){ invMsg('inv-ai-msg', 'Add at least one line item first.', 'err'); return; }
  const w = window.open('', '_blank'); if (!w){ invMsg('inv-ai-msg', 'Allow pop-ups to export a PDF, or use Download Excel.', 'err'); return; }
  w.document.write(invHTML(d)); w.document.close(); w.focus(); setTimeout(() => { try { w.print(); } catch (e){} }, 500);
  track('invoice_generate', { format:'pdf' });
}
/* --- AI: suggest HS codes for the current line items --- */
async function suggestHS(){
  const rows = invItems.map((it, i) => ({ it, i })).filter(x => (x.it.desc || '').trim());
  if (!rows.length){ invMsg('inv-ai-msg', 'Add product descriptions first — then AI suggests the HS codes.', 'err'); return; }
  const btn = $('#inv-suggest'); btn.disabled = true; track('ai_suggest_codes', { items: rows.length }); invMsg('inv-ai-msg', 'Classifying' + rows.length + ' item(s) with AI…', '');
  try {
    await initAI();
    if (!sampleFn){ invMsg('inv-ai-msg', 'The AI assistant is not switched on for this site.', 'err'); return; }
    const list = rows.map((x, k) => { const cand = search(x.it.desc + ' ' + (x.it.model || '')).rows.slice(0, 8).map(r => r.code + ' ' + label(r).slice(0, 46)).join(' | '); return `${k + 1}. ${x.it.desc}${x.it.model ? ' (model ' + x.it.model + ')' : ''}\n   options: ${cand || 'none found'}`; }).join('\n');
    const sys = `You classify products into Nepal 8-digit customs HS codes (Customs Tariff 2026/27). For each numbered product pick the single most appropriate Nepal HS code, preferring one of its listed options but choosing a better real Nepal code if none fit. Reply ONLY with JSON, no other text: {"items":[{"n":1,"hs":"8518.10.00","note":"short classification basis"}]}`;
    const data = await sampleFn.json([{ role: 'user', content: sys }, { role: 'user', content: 'Products:\n' + list }], { cache: false, task: 'classify' });
    const arr = (data && data.items) || [];
    let filled = 0;
    arr.forEach(a => { const idx = rows[(a.n || 0) - 1]; if (!idx) return; const code = String(a.hs || '').trim(); if (code){ invItems[idx.i].hs = code; invItems[idx.i].note = a.note || ''; filled++; } });
    renderInvRows(); renderInvTotals(); saveInvDraft();
    invMsg('inv-ai-msg', filled ? `AI suggested HS codes for ${filled} item(s). Review the codes and duty, then generate your documents. Tick “HS Code Review sheet” to include the notes.` : 'AI could not confidently classify these — try more specific descriptions.', filled ? 'ok' : 'err');
    if (filled) $('#inv-hsr').checked = true;
  } catch (e){ const code = e && e.code || ''; invMsg('inv-ai-msg', code === 'rate_limited' ? 'Too many requests — wait a minute and try again.' : 'The AI could not classify these right now. You can enter HS codes manually.', 'err'); }
  finally { btn.disabled = false; }
}
/* --- import invoice file (Excel/CSV now; PDF/photo guided) --- */
function loadSheetJS(){ if (window.XLSX) return Promise.resolve(); if (loadSheetJS._p) return loadSheetJS._p; return loadSheetJS._p = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js'; s.onload = res; s.onerror = () => rej(new Error('Could not load the spreadsheet reader.')); document.head.appendChild(s); }); }
function pickCol(headers, re){ for (let i = 0; i < headers.length; i++) if (re.test(headers[i])) return i; return -1; }
function loadPdfJS(){ if (window.pdfjsLib) return Promise.resolve(); if (loadPdfJS._p) return loadPdfJS._p; return loadPdfJS._p = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js'; s.onload = () => { try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js'; } catch (e){} res(); }; s.onerror = () => rej(new Error('Could not load the PDF reader.')); document.head.appendChild(s); }); }
function loadTesseract(){ if (window.Tesseract) return Promise.resolve(); if (loadTesseract._p) return loadTesseract._p; return loadTesseract._p = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js'; s.onload = res; s.onerror = () => rej(new Error('Could not load the photo text reader.')); document.head.appendChild(s); }); }
// pull raw text from a file: Excel/CSV (SheetJS), PDF (pdf.js text layer), image (OCR)
async function extractFileText(file){
  const name = (file.name || '').toLowerCase(), CAP = 9000;
  if (/\.(xlsx|xls|csv)$/.test(name)){ await loadSheetJS(); const buf = await file.arrayBuffer(), wb = XLSX.read(buf, { type: 'array' }); let t = ''; for (const sn of wb.SheetNames.slice(0, 3)){ t += '### ' + sn + '\n' + XLSX.utils.sheet_to_csv(wb.Sheets[sn]) + '\n'; if (t.length > CAP) break; } return t.slice(0, CAP); }
  if (/\.pdf$/.test(name) || file.type === 'application/pdf'){ await loadPdfJS(); const buf = await file.arrayBuffer(), pdf = await pdfjsLib.getDocument({ data: buf }).promise; let t = ''; for (let i = 1; i <= Math.min(pdf.numPages, 8); i++){ const pg = await pdf.getPage(i), c = await pg.getTextContent(); t += c.items.map(x => x.str).join(' ') + '\n'; if (t.length > CAP) break; } return t.slice(0, CAP); }
  if (/^image\//.test(file.type) || /\.(png|jpe?g|webp|gif|bmp|tiff?)$/.test(name)){ invMsg('inv-upmsg', 'Reading the photo… the text reader downloads on first use, please wait.', ''); await loadTesseract(); const r = await Tesseract.recognize(file, 'eng'); return ((r.data && r.data.text) || '').slice(0, CAP); }
  return '';
}
async function aiExtractInvoice(text){
  const sys = 'You extract structured data from an import/export invoice (proforma or commercial). Reply ONLY with JSON, no other text, exactly this shape: {"seller":{"name":"","address":"","contact":""},"buyer":{"name":"","address":"","contact":"","pan":""},"bank":{"name":"","bank":"","address":"","swift":"","account":""},"shipment":{"piNo":"","date":"","currency":"USD","priceTerm":"","origin":"","pol":"","entry":"","dest":"","mode":""},"items":[{"description":"","model":"","hs":"","qty":0,"unit":"PCS","unitPrice":0}]}. Fill only fields present in the document; leave the rest as empty strings. For each item, if the HS code is missing or clearly not a Nepal code, suggest the most likely Nepal 8-digit HS code (Customs Tariff 2026/27). Numbers must be plain numbers with no symbols or commas.';
  return await sampleFn.json([{ role: 'user', content: sys }, { role: 'user', content: 'INVOICE:\n' + text }], { cache: false, task: 'extract' });
}
function applyExtracted(d){
  const setV = (id, v) => { const el = $('#' + id); if (el && v != null && String(v).trim() !== '') el.value = String(v).trim(); };
  const s = d.seller || {}, b = d.buyer || {}, bk = d.bank || {}, sh = d.shipment || {};
  setV('inv-s-name', s.name); setV('inv-s-addr', s.address); setV('inv-s-contact', s.contact);
  setV('inv-b-name', b.name); setV('inv-b-addr', b.address); setV('inv-b-contact', b.contact); setV('inv-b-pan', b.pan);
  setV('inv-bk-name', bk.name); setV('inv-bk-bank', bk.bank); setV('inv-bk-addr', bk.address); setV('inv-bk-swift', bk.swift); setV('inv-bk-acct', bk.account);
  setV('inv-no', sh.piNo); setV('inv-date', sh.date); setV('inv-term', sh.priceTerm); setV('inv-origin', sh.origin); setV('inv-pol', sh.pol); setV('inv-entry', sh.entry); setV('inv-dest', sh.dest); setV('inv-mode', sh.mode);
  if (sh.currency && [...$('#inv-cur').options].some(o => o.value === sh.currency)) $('#inv-cur').value = sh.currency;
  if ((s.name || b.name || bk.name || bk.account) && $('#inv-parties')) $('#inv-parties').open = true;
  const items = (d.items || []).filter(it => it && (it.description || it.hs || it.unitPrice));
  if (items.length) invItems = items.map(it => { let hs = String(it.hs || '').replace(/[^\d.]/g, ''); if (/^\d{8}$/.test(hs)) hs = hs.slice(0,4) + '.' + hs.slice(4,6) + '.' + hs.slice(6); return Object.assign(blankItem(), { desc: it.description || '', model: it.model || '', hs, qty: parseFloat(it.qty) || '', unit: it.unit || 'PCS', price: parseFloat(it.unitPrice) || '' }); });
  renderInvRows(); renderInvTotals(); saveInvDraft();
  return items.length;
}
async function parseSheetItems(file){
  try {
    await loadSheetJS();
    const buf = await file.arrayBuffer(), wb = XLSX.read(buf, { type: 'array' }), ws = wb.Sheets[wb.SheetNames[0]];
    const grid = XLSX.utils.sheet_to_json(ws, { header: 1, blankrows: false });
    let hi = grid.findIndex(r => r && r.some(c => /descrip|item|product/i.test(String(c))) && r.some(c => /qty|quant|price|rate|amount|hs|code/i.test(String(c))));
    if (hi < 0) hi = 0;
    const headers = (grid[hi] || []).map(c => String(c || '').toLowerCase());
    const cD = pickCol(headers, /descrip|product|item name|goods/), cM = pickCol(headers, /model|item.?code|part/), cH = pickCol(headers, /h\.?s|hs.?code|tariff/), cQ = pickCol(headers, /qty|quant/), cU = pickCol(headers, /unit(?!.?price)/), cP = pickCol(headers, /unit.?price|price|rate/);
    if (cD < 0 && cH < 0){ invMsg('inv-upmsg', 'Could not find a description or HS-code column. Type the items in below.', 'err'); return; }
    const out = [];
    for (let r = hi + 1; r < grid.length; r++){ const row = grid[r] || []; const desc = cD >= 0 ? String(row[cD] || '').trim() : ''; const hsRaw = cH >= 0 ? String(row[cH] || '').trim() : ''; const price = cP >= 0 ? parseFloat(String(row[cP]).replace(/[^\d.]/g, '')) : 0;
      if (!desc && !hsRaw && !price) continue;
      let hs = hsRaw.replace(/[^\d.]/g, ''); if (/^\d{8}$/.test(hs)) hs = hs.slice(0,4) + '.' + hs.slice(4,6) + '.' + hs.slice(6);
      out.push(Object.assign(blankItem(), { desc, model: cM >= 0 ? String(row[cM] || '').trim() : '', hs, qty: cQ >= 0 ? (parseFloat(String(row[cQ]).replace(/[^\d.]/g, '')) || '') : '', unit: cU >= 0 ? (String(row[cU] || '').trim() || 'PCS') : 'PCS', price: price || '' })); }
    if (!out.length){ invMsg('inv-upmsg', 'No line items found in the sheet. Type them in below.', 'err'); return; }
    invItems = out; renderInvRows(); renderInvTotals(); saveInvDraft();
    const noHS = out.filter(x => !x.hs).length;
    invMsg('inv-upmsg', `Loaded ${out.length} item(s) from ${file.name}.` + (noHS ? ` ${noHS} have no HS code — tap "Suggest HS codes with AI".` : ''), 'ok');
  } catch (e){ invMsg('inv-upmsg', 'Could not read that file: ' + (e && e.message || e) + '. Type the items in below.', 'err'); }
}
async function importInvoiceFile(file){
  const isSheet = /\.(xlsx|xls|csv)$/.test((file.name || '').toLowerCase());
  invMsg('inv-upmsg', 'Reading ' + file.name + '…', '');
  let text = '';
  try { text = await extractFileText(file); }
  catch (e){ invMsg('inv-upmsg', 'Could not read that file: ' + (e && e.message || e) + (isSheet ? '' : ' Try an Excel/CSV, or type the items in below.'), 'err'); return; }
  if (!text || text.trim().length < 8){ if (isSheet) return parseSheetItems(file); invMsg('inv-upmsg', 'No readable text found. If it is a photo, use a clearer image, or type the items in below.', 'err'); return; }
  await initAI();
  if (sampleFn){
    invMsg('inv-upmsg', 'AI is reading the invoice — parties, bank and line items…', '');
    try {
      const d = await aiExtractInvoice(text), n = applyExtracted(d);
      if ($('#inv-hsr')) $('#inv-hsr').checked = true;
      invMsg('inv-upmsg', n ? `Read ${n} item(s) plus party, shipment and bank details from ${file.name}. Review anything the AI got wrong, then download.` : 'Read the file but found no clear line items — check it or type the items in below.', n ? 'ok' : 'err');
      return;
    } catch (e){ if (isSheet) return parseSheetItems(file); }
  }
  if (isSheet) return parseSheetItems(file);
  invMsg('inv-upmsg', 'The AI reader is off for this copy of the site, so PDF/photo reading is unavailable. Upload an Excel or CSV, or type the items in below.', 'err');
}

/* saved */
function renderSaved(){
  const s = store.get('saved', []).filter(c => BY[c]);
  $('#v-saved').innerHTML = `<div class="page-h"><h2>Saved codes</h2><p>Kept in this browser for quick reference.</p></div>` + (s.length
    ? `<div class="group">${s.map(c => rowHTML(BY[c])).join('')}</div>`
    : `<div class="empty"><b>Nothing saved yet</b><p>Open any HS code and tap the bookmark button to keep it here.</p><div class="suggest"><button data-go="search">Search codes</button></div></div>`);
}
$('#v-saved').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.go) go(b.dataset.go); else if (b.dataset.code) openDetail(b.dataset.code); });


/* ---------- AI assistant ---------- */
let sampleFn, aiReady = false, aiTurns = [], aiCtl = null, aiPhoto = null, aiLimits = null, aiAnswers = {};
const compact = r => `${r.code} | ${label(r)} | heading ${r.h}: ${r.head.slice(0,90)} | duty ${pct(r.g)} (SAARC ${pct(r.s)}) | unit ${r.u}`;
const AI_RULES = `You are a Nepal customs classification assistant inside a web app that holds the full Nepal Customs Tariff 2026/27 (HS 2022, 8-digit Nepal lines). The user describes a product they want to import into Nepal, in English or Nepali. Your job: find the most likely Nepal HS code lines.
Rules:
- Use the search_tariff tool to look up candidate lines by product words, materials, functions and synonyms; use lines_under_heading to see every line under a heading before choosing between them. Search several ways (product name, material, function, part/complete, generic HS wording like "other" articles) before answering. Never invent a code; only return codes the tools returned.
- Apply the General Rules of Interpretation: complete vs parts, essential character, most specific description, sets. Parts that have their own heading go there.
- If the description is a shipment with several distinct products, classify each product separately.
- If the classification really depends on something the user did not say (material, size, complete/parts, power, use), ask up to 3 short multiple-choice questions.
- Reply ONLY with JSON of this shape, no other text:
{"summary": "one or two plain sentences about what the product is and the classification logic",
 "items": [{"product": "short name", "candidates": [{"code": "8528.59.00", "confidence": 0.0-1.0, "reason": "one sentence why, mention the deciding feature"}]}],
 "questions": [{"q": "question text", "options": ["a","b","c"]}],
 "tips": ["short practical note about duty, SAARC origin certificate, licensing, etc."]}
Give 1-3 candidates per product, best first, confidence honest (below 0.6 when unsure). Answer in the language the user wrote in for text fields, but keep codes as-is. Keep reasons short.`;
const AI_TOOLS = [
  { name: 'search_tariff', description: 'Search Nepal tariff lines by words (product, material, function, synonyms; English only). Returns up to 25 lines as "code | description | heading | duty | unit". Try different wording if nothing relevant comes back.',
    inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
    execute: ({ query }) => { const q = String(query || ''); aiProgress(`Searching the tariff for “${q}”…`); const rs = search(q).rows.slice(0, 25); return rs.length ? rs.map(compact).join('\n') : 'No lines match. Try other words (material, function, generic term).'; } },
  { name: 'lines_under_heading', description: 'List every tariff line under a 4-digit heading such as "85.28" or "8528". Use it to pick the exact 8-digit line.',
    inputSchema: { type: 'object', properties: { heading: { type: 'string' } }, required: ['heading'] },
    execute: ({ heading }) => { const d = String(heading || '').replace(/\D/g,'').slice(0,4); const h = d.slice(0,2)+'.'+d.slice(2,4); aiProgress(`Reading all lines under heading ${h}…`); const rs = BYHEAD[h]; if (!rs) throw new Error('No such heading'); return `Heading ${h}: ${D.heads[h][0]}\n` + rs.map(r => `${r.code} | ${(r.path.length ? r.path.join(' > ') + ' > ' : '') + r.d} | duty ${pct(r.g)} (SAARC ${pct(r.s)}) | unit ${r.u}`).join('\n'); } }
];

// Fallback agent loop against /api/classify (a thin proxy to the Anthropic Messages API). Same call shape as claude.use('sample').json.
async function apiSample(){ throw { code: 'invalid_request', message: 'use apiSample.json' }; }
apiSample.json = async function(input, opts){
  const task = opts.task || 'assistant', msgs = input.slice(1).map(t => ({ role: t.role, content: t.content }));
  const tools = (opts.tools || []).map(t => ({ name: t.name, description: t.description, input_schema: t.inputSchema || { type: 'object', properties: {} } }));
  for (let round = 0; round < 8; round++){
    let r;
    try { r = await fetch('/api/classify', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ task, messages: msgs, tools }), signal: opts.signal }); }
    catch(e){ throw { code: e && e.name === 'AbortError' ? 'cancelled' : 'upstream_error', message: String(e) }; }
    if (r.status === 429) throw { code: 'rate_limited', message: 'rate limited' };
    if (!r.ok) throw { code: 'upstream_error', message: 'HTTP ' + r.status };
    const j = await r.json();
    if (!Array.isArray(j.content)) throw { code: 'upstream_error', message: 'bad response' };
    msgs.push({ role: 'assistant', content: j.content });
    if (j.stop_reason === 'tool_use'){
      const results = [];
      for (const b of j.content.filter(b => b.type === 'tool_use')){
        const t = (opts.tools || []).find(x => x.name === b.name); let out;
        try { out = t ? await t.execute(b.input || {}, { signal: opts.signal }) : 'Error: unknown tool'; } catch(e){ out = 'Error: ' + (e && e.message || e); }
        results.push({ type: 'tool_result', tool_use_id: b.id, content: typeof out === 'string' ? out : JSON.stringify(out) });
      }
      msgs.push({ role: 'user', content: results }); continue;
    }
    const text = j.content.filter(b => b.type === 'text').map(b => b.text).join('\n');
    const m = /```(?:json)?\s*([\s\S]*?)```/.exec(text); const body = m ? m[1] : text;
    const a = body.indexOf('{'), z = body.lastIndexOf('}');
    try { return JSON.parse(a >= 0 ? body.slice(a, z + 1) : body); } catch(e){ throw { code: 'invalid_json', message: 'no json', text }; }
  }
  throw { code: 'upstream_error', message: 'too many rounds' };
};
function aiProgress(t){ const el = $('#ai-status-t'); if (el) el.textContent = t; }
async function initAI(){
  if (aiReady) return; aiReady = true;
  sampleFn = window.claude && window.claude.use ? await window.claude.use('sample') : null;
  if (!sampleFn){
    // Hosted build: use the site's own /api/classify function (needs ANTHROPIC_API_KEY on the server)
    let ok = false;
    if (/^https?:/.test(location.protocol)) { try { const r = await fetch('/api/classify', { method: 'GET' }); ok = r.ok && (await r.json()).configured === true; } catch(e){ ok = false; } }
    if (ok){ sampleFn = apiSample; aiLimits = { tools: { maxCount: 8 } }; return; }
    $('#ai-go').disabled = true; $('#ai-out').innerHTML = `<div class="ai-off">The assistant is not switched on for this copy of the site. Search and Browse still work with the full tariff.</div>`; return; }
  aiLimits = await sampleFn.limits().catch(() => null);
  if (aiLimits && aiLimits.images){ $('#ai-photo-l').hidden = false; $('#ai-photo').accept = aiLimits.images.mediaTypes.join(','); }
}
$('#ai-ex').addEventListener('click', e => { const b = e.target.closest('[data-ex]'); if (b){ $('#ai-q').value = b.dataset.ex; $('#ai-q').focus(); } });
$('#ai-photo').addEventListener('change', e => { aiPhoto = e.target.files[0] || null; $('#ai-photo-l').classList.toggle('has', !!aiPhoto); $('#ai-photo-t').textContent = aiPhoto ? aiPhoto.name.slice(0, 18) : 'Add photo'; });
$('#ai-go').addEventListener('click', () => { const q = $('#ai-q').value.trim(); if (!q && !aiPhoto) { $('#ai-q').focus(); return; } aiTurns = []; aiAnswers = {}; askAI(q || 'Identify the product in the photo and classify it.'); });
const AI_COPY = { not_granted: 'You have not allowed this page to use Claude, so the assistant is off. Search and Browse still work.', sampling_disabled: 'Claude is not available on this account.', rate_limited: 'Too many requests right now. Wait a minute and try again.', refused: 'The assistant could not answer this request. Try describing the product differently.', invalid_json: 'The answer came back in an unexpected form. Try again or shorten the description.', empty_completion: 'No answer came back. Try a shorter description.', upstream_error: 'The connection dropped. Try again.', prompt_too_large: 'The description is too long. Shorten it.', session_expired: 'Your Claude session expired. Sign in again and retry.', tools_unavailable: 'This viewer cannot run the assistant tools yet.' };
// Analytics for the assistant: only a coarse topic worked out here in the browser and a 2-digit HS chapter.
// The question text, the answer and anything personal never go to analytics.
const AI_TOPICS = [
  ['vat', /\bvat\b|value added|भ्याट|मूल्य अभिवृद्धि/i],
  ['export', /\bexport|निर्यात/i],
  ['documents', /\bdocument|certificate|licen[cs]e|permit|\bpan\b|exim|invoice|packing list|bill of lading|\bl\/?c\b|कागजात|प्रमाणपत्र|इजाजत/i],
  ['shipping', /\bship|freight|container|transit|courier|cargo|kolkata|birgunj|\bport\b|ढुवानी/i],
  ['calculation', /calculat|landed cost|how much (duty|tax)|total (duty|tax|cost)|\bcif\b|हिसाब|कति (कर|भन्सार)/i],
  ['duty_rate', /\bduty|tariff|\btax|\brate\b|customs charge|भन्सार|महसुल|कर /i],
  ['classification', /\bhs\b|h\.s\.|classif|which code|what code|\bcode\b|heading|chapter|कोड|वर्गीकरण/i]
];
// Anything else that reads as a general question is 'other'; a plain product description is 'classification'.
function aiTopic(t){ for (const [k, re] of AI_TOPICS) if (re.test(t)) return k; return /\?|^\s*(how|what|why|when|where|who|can|is|are|do|does|should)\b|कसरी|किन|के हो/i.test(t) ? 'other' : 'classification'; }
function hsChapterOf(t){
  t = String(t || '');
  let m = /chapter\s*(\d{1,2})(?!\d)/i.exec(t);
  if (!m){ const re = /(?:^|[^\d])(\d{2})(\d{2}|[.\s]\d{2})((?:[.\s]?\d{2}){0,2})(?!\d)/g; let x;
    while ((x = re.exec(t))){ if (/^\d{4}$/.test(x[1] + x[2]) && !x[3] && /^(19|20)/.test(x[1])) continue; m = x; break; } } // skip bare years like 2082
  if (!m) return ''; const c = +m[1]; return c >= 1 && c <= 97 && D.chapters[c] ? String(c).padStart(2, '0') : ''; }
let aiTopicNow = 'other';
async function askAI(userText){
  const firstTurn = !aiTurns.length;
  if (firstTurn || aiTopicNow === 'other') aiTopicNow = aiTopic(userText);
  const askCh = hsChapterOf(userText);
  track('ask_ai', Object.assign({ ai_topic: aiTopicNow, ai_turn: firstTurn ? 'first' : 'follow_up', search_lang: searchLang(userText) }, askCh ? { hs_chapter: askCh } : {}));
  const out = $('#ai-out'), go = $('#ai-go');
  aiTurns.push({ role: 'user', content: userText });
  go.disabled = true;
  aiCtl = new AbortController();
  out.innerHTML = `<div class="chatlog">${aiTurns.map(t => `<div class="bub ${t.role === 'user' ? 'u' : 'a'}">${esc(t.content)}</div>`).join('')}</div><div class="ai-status"><span class="dot"></span><span id="ai-status-t">Reading your description…</span><button class="stop" id="ai-stop">Stop</button></div>`;
  $('#ai-stop').onclick = () => aiCtl.abort();
  const input = [{ role: 'user', content: AI_RULES }, ...aiTurns];
  const useTools = !!(aiLimits && aiLimits.tools);
  let opts = { signal: aiCtl.signal, cache: false, task: 'assistant' };
  if (useTools) opts.tools = AI_TOOLS;
  else {
    // no tool support: pre-fetch candidates locally and pass them in the prompt
    const rs = search(userText).rows.slice(0, 40);
    input[input.length-1] = { role: 'user', content: userText + '\n\nCandidate tariff lines found by keyword search (pick only from these or say none fit):\n' + rs.map(compact).join('\n') };
  }
  if (aiPhoto && aiLimits && aiLimits.images) opts.images = aiPhoto;
  try {
    const data = await sampleFn.json(input, opts);
    aiTurns.push({ role: 'assistant', content: JSON.stringify(data) });
    renderAI(data);
    try {
      const top = (Array.isArray(data.items) ? data.items : []).flatMap(it => Array.isArray(it && it.candidates) ? it.candidates : []).map(c => BY[String(c && c.code || '').trim()]).find(Boolean);
      const ch = top ? String(top.ch).padStart(2, '0') : askCh;
      track('ai_answer', Object.assign({ ai_topic: aiTopicNow, ai_result: top ? 'codes' : (Array.isArray(data.questions) && data.questions.length ? 'questions' : 'none') }, ch ? { hs_chapter: ch } : {}));
    } catch(e){}
  } catch (e) {
    const code = e && e.code || 'upstream_error';
    if (code === 'cancelled'){ out.innerHTML = `<div class="ai-off">Stopped.</div>`; }
    else if (code === 'not_granted' || code === 'sampling_disabled'){ out.innerHTML = `<div class="ai-off">${AI_COPY[code]}</div>`; go.disabled = true; return; }
    else out.innerHTML = `<div class="ai-off">${AI_COPY[code] || AI_COPY.upstream_error}</div>`;
    aiTurns.pop();
  } finally { go.disabled = false; }
}
function renderAI(d){
  const out = $('#ai-out');
  const items = Array.isArray(d.items) ? d.items : [];
  const qs = Array.isArray(d.questions) ? d.questions.filter(q => q && q.q).slice(0, 3) : [];
  let html = `<div class="chatlog">${aiTurns.filter(t => t.role === 'user').map(t => `<div class="bub u">${esc(t.content)}</div>`).join('')}${d.summary ? `<div class="bub a">${esc(String(d.summary))}</div>` : ''}</div>`;
  let any = false;
  items.forEach(it => {
    const cands = (Array.isArray(it.candidates) ? it.candidates : []).map(c => ({ ...c, r: BY[String(c.code || '').trim()] })).filter(c => c.r).slice(0, 3);
    if (!cands.length) return; any = true;
    if (items.length > 1) html += `<h2 class="sec" style="margin-top:var(--s5)">${esc(String(it.product || ''))}</h2>`;
    cands.forEach((c, k) => { const conf = Math.max(0, Math.min(1, +c.confidence || 0)), r = c.r;
      html += `<div class="cand ${k === 0 ? 'top' : ''}"><div class="ch"><span class="mono">${r.code}</span><span class="conf ${conf < .6 ? 'lo' : ''}"><i><b style="width:${Math.round(conf*100)}%"></b></i>${Math.round(conf*100)}% match</span></div>
        <p class="desc">${esc(label(r))}</p><p class="why">${esc(String(c.reason || ''))}</p>
        <div class="ch" style="justify-content:flex-start;gap:var(--s3)">${dutyTag(rateOf(r), true)}<span style="font-size:.82rem;color:var(--muted)">${esc(r.head.slice(0, 80))}${r.head.length > 80 ? '…' : ''}</span></div>
        <div class="ca"><button class="btn" data-code="${r.code}">Details &amp; nearby lines</button><button class="btn" data-calc="${r.code}">Calculate tax</button></div></div>`; });
  });
  if (!any && !qs.length) html += `<div class="ai-off">No matching tariff lines were found. Try describing the material, the function and whether it is a complete product or parts.</div>`;
  if (qs.length){
    html += `<div class="qs"><h3>A few details would narrow this down</h3><p>Pick what applies, or type more below.</p>${qs.map((q, i) => `<div class="q"><b>${esc(String(q.q))}</b><div class="opts" data-qi="${i}">${(Array.isArray(q.options) ? q.options : []).slice(0, 6).map(o => `<button data-opt="${esc(String(o))}">${esc(String(o))}</button>`).join('')}</div></div>`).join('')}
      <div style="display:flex;gap:var(--s2);margin-top:var(--s3);flex-wrap:wrap"><input id="ai-more" placeholder="Anything else…" style="flex:1 1 200px;height:44px;border:1.5px solid var(--border);border-radius:10px;padding:0 12px;background:var(--bg);color:var(--fg)"><button class="btn primary" id="ai-refine" style="flex:0 0 auto">Refine</button></div></div>`;
  }
  if (Array.isArray(d.tips) && d.tips.length) html += `<div class="outcome" style="margin-top:var(--s4);align-items:flex-start">${ic('i-info')}<div>${d.tips.slice(0,4).map(t => `<div>${esc(String(t))}</div>`).join('')}</div></div>`;
  html += `<div style="margin-top:var(--s4)"><button class="btn" id="ai-reset">Start over</button></div>`;
  out.innerHTML = html;
  out.querySelectorAll('.qs .opts').forEach(g => g.addEventListener('click', e => { const b = e.target.closest('[data-opt]'); if (!b) return; const qi = g.dataset.qi; const on = b.getAttribute('aria-pressed') === 'true'; g.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', 'false')); if (!on){ b.setAttribute('aria-pressed', 'true'); aiAnswers[qi] = { q: qs[qi].q, a: b.dataset.opt }; } else delete aiAnswers[qi]; }));
  const refine = $('#ai-refine'); if (refine) refine.onclick = () => { const more = $('#ai-more').value.trim(); const parts = Object.values(aiAnswers).map(x => `${x.q} ${x.a}`); if (more) parts.push(more); if (!parts.length){ $('#ai-more').focus(); return; } aiAnswers = {}; askAI(parts.join('. ') + '. Please update the classification.'); };
  $('#ai-reset').onclick = () => { aiTurns = []; aiAnswers = {}; out.innerHTML = ''; $('#ai-q').value = ''; $('#ai-q').focus(); };
}
$('#ai-out').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.code) openDetail(b.dataset.code); else if (b.dataset.calc){ pickCalc(b.dataset.calc); go('calc'); } });


/* ---------- trade statistics ---------- */
const K = 1000; // stats values are Rs. thousand
let UNITS = store.get('units', 'np'); // 'np' = Arab/Crore/Lakh, 'intl' = billion/million
function rs(th, short){
  const v = th * K, a = Math.abs(v);
  if (UNITS === 'intl'){
    const g = (x, d) => x.toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: 0 });
    if (a >= 1e9) return (short ? '' : 'NPR ') + g(v / 1e9, a >= 1e11 ? 0 : 1) + ' bn';
    if (a >= 1e6) return (short ? '' : 'NPR ') + g(v / 1e6, a >= 1e8 ? 0 : 1) + ' mn';
    if (a >= 1e3) return (short ? '' : 'NPR ') + g(v / 1e3, 0) + ' k';
    return (short ? '' : 'NPR ') + g(v, 0);
  }
  const f = (x, d) => x.toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: 0 });
  if (a >= 1e9) return (short ? '' : 'NPR ') + f(v / 1e9, a >= 1e11 ? 0 : 1) + ' Arab';
  if (a >= 1e7) return (short ? '' : 'NPR ') + f(v / 1e7, a >= 1e9 ? 0 : 1) + ' Cr';
  if (a >= 1e5) return (short ? '' : 'NPR ') + f(v / 1e5, 1) + ' Lakh';
  return (short ? '' : 'NPR ') + f(v, 0);
}
const pctc = (a, b) => b ? ((a - b) / b * 100) : 0;
const qty = (q, u) => (q >= 1e6 ? (q / 1e6).toLocaleString('en-IN', { maximumFractionDigits: 1 }) + ' M' : q.toLocaleString('en-IN', { maximumFractionDigits: q < 100 ? 1 : 0 })) + ' ' + (u || '').toLowerCase();
function kpiTiles(compact){
  const o = compact ? ST.overview : OV(), fyp = compact ? ST.fy_prev : (stYear ? FY[stYear-1] : ''), t = (label, key, inverse) => { const [p, c] = o[key]; const ch = pctc(c, p); const good = inverse ? ch < 0 : ch > 0;
    return `<div class="tile"><span>${label}</span><b>${rs(c, true)}</b><small class="${Math.abs(ch) < .05 ? 'neutral' : good ? 'up' : 'down'}">${ic(ch >= 0 ? 'i-up' : 'i-down').replace('class="i"', 'class="i" style="width:14px;height:14px"')}${Math.abs(ch).toFixed(1)}%&nbsp;vs&nbsp;${fyp || 'previous'}</small></div>`; };
  return t('Imports', 'imports') + t('Exports', 'exports') + t('Trade deficit', 'trade_deficit', true) + (compact ? `<div class="tile"><span>Exports cover</span><b>${(o.exports[1] / o.imports[1] * 100).toFixed(1)}%</b><small class="neutral">of imports</small></div>` : `<div class="tile"><span>Imports per NPR 1 exported</span><b>NPR ${o.imports_exports_ratio[1].toFixed(1)}</b><small class="${o.imports_exports_ratio[1] < o.imports_exports_ratio[0] ? 'up' : 'down'}">was ${o.imports_exports_ratio[0].toFixed(1)}</small></div>`);
}
function barRows(items, opts){
  const max = Math.max(...items.map(x => Math.max(x.a || 0, x.b || 0)), 1);
  const two = items.some(x => x.b !== undefined);
  const seg = (v, cls) => `<span class="s ${two ? 'two' : ''}"><i class="${cls}" style="width:${(v / max * 68).toFixed(1)}%"></i><b>${v ? rs(v, true) : ''}</b></span>`;
  return `<div class="bars">${items.map(x => {
    const tag = x.k !== undefined ? 'button' : 'div';
    return `<${tag} class="br" ${x.k !== undefined ? `data-k="${esc(String(x.k))}"` : ''} title="${esc(x.label)}: ${rs(x.a)}${two ? ' imports · ' + rs(x.b) + ' exports' : ''}">
      <span class="l">${x.sub ? `<small class="${x.sub.length <= 2 ? 'in' : ''}">${esc(x.sub)}</small>` : ''}${esc(x.label)}</span>
      <span class="t">${seg(x.a, opts && opts.cls || '')}${two ? seg(x.b, 'e') : ''}</span></${tag}>`; }).join('')}</div>`;
}
const fig = (title, cap, body, legend) => `<div class="fig"><header>${title ? `<h3>${title}</h3>` : ''}${cap ? `<span class="cap">${cap}</span>` : ''}${legend ? `<div class="legend2">${legend}</div>` : ''}</header>${body}<p class="src">Source: Department of Customs, Nepal · FY ${typeof yFY === 'function' && stView === 'compare' ? FY[cmpA] + ' and ' + FY[cmpB] : yFY()} · NPR</p></div>`;
const LEG2 = `<span><i style="background:var(--imp)"></i>Imports</span><span><i style="background:var(--exp)"></i>Exports</span>`;
const chapName = c => CHSHORT[c] || (ST.chapters.find(x => x[0] === c) || [0, ''])[1];

/* ---------- ECharts helpers (theme from tokens) ---------- */
const HAS_EC = typeof echarts !== 'undefined';
const tok = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const charts = [];
function ecInit(el, opt){
  if (!HAS_EC || !el) return null;
  const c = echarts.init(el, null, { renderer: 'canvas' });
  c.setOption(Object.assign({ textStyle: { fontFamily: tok('--f-body'), color: tok('--fg-2') }, animationDuration: 300 }, opt));
  charts.push(c); return c;
}
function ecClear(){ while (charts.length){ const c = charts.pop(); try{ c.dispose(); }catch(e){} } }
window.addEventListener('resize', () => charts.forEach(c => c.resize()));
const tip = { trigger: 'axis', backgroundColor: tok('--card'), borderColor: tok('--border'), textStyle: { color: tok('--fg'), fontSize: 12 }, confine: true,
  valueFormatter: v => rs(v) };
const axisBase = () => ({ axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: tok('--muted'), fontSize: 11 }, splitLine: { lineStyle: { color: tok('--grid'), type: 'dashed' } } });
const FY = ST.history.years, H = ST.history;
const yoy = (arr, i) => { const a = arr[i], b = arr[i-1]; return b ? (a - b) / b * 100 : null; };
function sparkHTML(vals, cur, cls){
  const max = Math.max(...vals.map(Math.abs), cur || 0, 1);
  return `<div class="spark">${vals.map((v, i) => `<i class="${cls || ''}" style="height:${Math.max(2, v / max * 100)}%" title="${FY[i]}: ${rs(v)}"></i>`).join('')}${cur ? `<i class="${cls || ''} cur" style="height:${Math.max(2, cur / max * 100)}%" title="${ST.current.fy} (${ST.current.months} months): ${rs(cur)}"></i>` : ''}</div><div class="spark-l"><span>${FY[0]}</span><span>${cur ? ST.current.fy + ' YTD' : FY[FY.length-1]}</span></div>`;
}
function yoyTag(arr){ const i = arr.length - 1, p = yoy(arr, i); if (p === null || !isFinite(p)) return ''; return `<span class="yoy ${p >= 0 ? 'up' : 'down'}">${ic(p >= 0 ? 'i-up' : 'i-down').replace('class="i"', 'class="i" style="width:12px;height:12px"')}${Math.abs(p).toFixed(0)}% vs ${FY[i-1]}</span>`; }
function yearBars(el, series, names){
  // series: [{name, data:[...per FY]}]
  return ecInit(el, { grid: { left: 8, right: 8, top: 28, bottom: 24, containLabel: true }, tooltip: tip, legend: names.length > 1 ? { top: 0, textStyle: { color: tok('--fg-2') } } : undefined,
    xAxis: Object.assign(axisBase(), { type: 'category', data: FY.map(y => y.slice(0, 4) + '/' + y.slice(5)) }),
    yAxis: Object.assign(axisBase(), { type: 'value', axisLabel: { color: tok('--muted'), fontSize: 11, formatter: v => rs(v, true) } }),
    series: series.map((sr, k) => ({ name: sr.name, type: 'bar', data: sr.data, itemStyle: { color: [tok('--imp'), tok('--exp'), tok('--rev')][k], borderRadius: [2, 2, 0, 0] }, barMaxWidth: 22, barGap: '25%' })) });
}
function monthlyLine(el, key){
  const idx = key === 'exp' ? 1 : 0, yrs = Object.keys(ST.monthly);
  const cols = [tok('--muted'), tok('--imp'), tok('--exp'), tok('--rev')];
  const series = yrs.map((fy, k) => ({ name: fy.slice(2, 4) + '/' + fy.slice(5), type: 'line', smooth: .25, showSymbol: false, lineStyle: { width: k === yrs.length - 1 ? 3 : 2, color: k === yrs.length - 1 ? tok('--imp') : k === yrs.length - 2 ? tok('--exp') : cols[0] }, itemStyle: { color: k === yrs.length - 1 ? tok('--imp') : k === yrs.length - 2 ? tok('--exp') : cols[0] },
    data: ST.monthly[fy].map(x => x ? x.val[idx] : null), connectNulls: false }));
  return ecInit(el, { grid: { left: 8, right: 12, top: 40, bottom: 24, containLabel: true }, tooltip: tip, legend: { top: 0, left: 'center', textStyle: { color: tok('--fg-2'), fontSize: 11 }, itemWidth: 12, itemGap: 8 },
    xAxis: Object.assign(axisBase(), { type: 'category', boundaryGap: false, data: ST.month_names.map(m => m.slice(0, 3)) }),
    yAxis: Object.assign(axisBase(), { type: 'value', axisLabel: { color: tok('--muted'), fontSize: 11, formatter: v => rs(v, true) } }), series });
}
function treemapChart(el, dir){
  const vi = dir === 'exp' ? 3 : 2, tot = (dir === 'exp' ? OV().exports[1] : OV().imports[1]) || 1, lbl = dir === 'exp' ? 'exports' : 'imports';
  const secs = {};
  CH().forEach(c => { const s = sectionOf(c[0]); if (!s || !c[vi]) return; (secs[s.n] = secs[s.n] || { name: 'Section ' + s.n + ' · ' + s.t.split(';')[0].slice(0, 40), children: [] }).children.push({ name: chapName(c[0]), value: c[vi], ch: c[0] }); });
  const pal = ['#1D81A2', '#2E9E6B', '#E8722E', '#7C5CBF', '#B8860B', '#C0392B', '#3A7CA5', '#5B8C5A', '#8E44AD', '#D35400', '#16A085', '#7F8C8D', '#2C3E50', '#27AE60', '#E67E22', '#2980B9', '#8D6E63', '#00838F', '#AD1457', '#6D4C41', '#455A64'];
  return ecInit(el, { tooltip: { confine: true, backgroundColor: tok('--card'), borderColor: tok('--border'), textStyle: { color: tok('--fg'), fontSize: 12 }, formatter: p => `${esc(p.name)}<br><b>${rs(p.value)}</b> · ${(p.value / tot * 100).toFixed(1)}% of ${lbl}` },
    series: [{ type: 'treemap', roam: false, nodeClick: 'zoomToNode', breadcrumb: { show: false }, label: { fontSize: 11, color: '#fff', formatter: p => p.name.replace(/^Section [IVX]+ · /, '') },
      upperLabel: { show: true, height: 20, fontSize: 11, color: '#fff' }, itemStyle: { borderColor: tok('--card'), borderWidth: 1, gapWidth: 1 },
      levels: [{ itemStyle: { borderWidth: 0, gapWidth: 3 } }, { colorSaturation: [.35, .6], itemStyle: { gapWidth: 2, borderColorSaturation: .5 } }],
      data: Object.values(secs).map((x, i) => ({ name: x.name, children: x.children, itemStyle: { color: pal[i % pal.length] } })) }] });
}
function slugify(s){ return String(s).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
function sankeyChart(el){
  const mob = window.innerWidth < 640, N = mob ? 8 : 12;
  const cos = Object.keys(ST.flow).slice(0, N);
  const chTot = {}; cos.forEach(c => ST.flow[c].forEach(([ch, v]) => chTot[ch] = (chTot[ch] || 0) + v));
  const topCh = Object.entries(chTot).sort((a, b) => b[1] - a[1]).slice(0, N).map(x => +x[0]);
  const links = []; cos.forEach(c => { let other = 0; ST.flow[c].forEach(([ch, v]) => { if (topCh.includes(ch)) links.push({ source: c, target: chapName(ch), value: v }); else other += v; }); if (other) links.push({ source: c, target: 'Other goods', value: other }); });
  const nodes = [...cos.map(c => ({ name: c, co: c, itemStyle: { color: tok('--imp') }, label: { position: 'right' } })), ...topCh.map(ch => ({ name: chapName(ch), ch, itemStyle: { color: tok('--exp') }, label: { position: 'left' } })), { name: 'Other goods', itemStyle: { color: tok('--muted') }, label: { position: 'left' } }];
  const chart = ecInit(el, { tooltip: { confine: true, backgroundColor: tok('--card'), borderColor: tok('--border'), textStyle: { color: tok('--fg'), fontSize: 12 }, formatter: p => (p.dataType === 'edge' || p.data.source) ? `${esc(p.data.source)} → ${esc(p.data.target)}<br><b>${rs(p.data.value)}</b>` : `${esc(p.name)}<br><b>${rs(p.value)}</b>${(p.data.co || p.data.ch != null) ? '<br><span style="opacity:.6;font-size:11px">tap to open trade page</span>' : ''}` },
    series: [{ type: 'sankey', left: 4, right: 4, top: 8, bottom: 8, nodeWidth: 10, nodeGap: mob ? 10 : 8, orient: 'horizontal', nodeAlign: 'justify', draggable: false, emphasis: { focus: 'adjacency' }, lineStyle: { color: 'gradient', opacity: .35, curveness: .5 },
      label: { fontSize: mob ? 9 : 11, color: tok('--fg') }, data: nodes, links }] });
  if (chart) { try { chart.getZr().setCursorStyle('pointer'); } catch (e) {} chart.on('click', p => { const d = (p && p.data) || {}; if (d.co) location.href = '/trade/country/' + slugify(d.co); else if (d.ch != null) location.href = '/trade/category/' + String(d.ch).padStart(2, '0'); else if (d.name === 'Other goods') location.href = '/trade/categories'; }); }
  return chart;
}

let stView = 'overview', stSort = 'imp', stCountry = null, stChapter = null, stQ = '';
let stYear = FY.length - 1;
let cmpA = Math.max(0, FY.length - 2), cmpB = FY.length - 1, cmpQ = '';
const isLatest = () => stYear === FY.length - 1;
const yFY = () => FY[stYear];
const OV = () => H.overview[stYear];
const CH = () => Object.keys(H.chapters).map(Number).map(c => [c, '', H.chapters[c][stYear][0], H.chapters[c][stYear][1], H.chapters[c][stYear][2]]).filter(x => x[2] || x[3]);
const CO = () => Object.keys(H.countries).map(nm => [nm, H.countries[nm][stYear][0], H.countries[nm][stYear][1]]).filter(x => x[1] || x[2]);
// customs offices as the FTS 'customswise' sheet names them; the sheet's own Total row is not an office
const CU_NAME = { Ti_Airport: 'Tribhuvan International Airport', Dryport: 'Dry Port', Maheshpaur: 'Maheshpur' };
const CU = () => Object.keys(H.customs).filter(nm => nm.toLowerCase() !== 'total').map(nm => [CU_NAME[nm] || nm, H.customs[nm][stYear][0], H.customs[nm][stYear][1]]).filter(x => x[1] || x[2]);
const BD = () => H.bands[stYear] || [];
const impV = c => isLatest() ? (ST.imports[c] ? ST.imports[c][3] : 0) : (H.codes[c] ? H.codes[c][stYear][0] : 0);
const expV = c => isLatest() ? (ST.exports[c] ? ST.exports[c][3] : 0) : (H.codes[c] ? H.codes[c][stYear][1] : 0);
const codeLabel = c => { const r = BY[c.slice(0,4)+'.'+c.slice(4,6)+'.'+c.slice(6)]; return r ? label(r) : (ST.imports[c] || ST.exports[c] || [c])[0]; };
function renderYearSel(){
  $('#yearsel').innerHTML = FY.map((y, i) => `<button data-year="${i}" aria-pressed="${i === stYear}">${y}</button>`).join('') + (ST.current ? `<button class="ytd" disabled title="Current year, ${ST.current.months} months so far">${ST.current.fy} · ${ST.current.months} mo</button>` : '');
}
const impRow = c => ST.imports[c], expRow = c => ST.exports[c];
function tradeCard(code8){
  const im = impRow(code8), ex = expRow(code8);
  if (!im && !ex) return `<div class="trade"><h3 class="h" style="margin:0 0 6px">Nepal trade, FY ${ST.fy}</h3><p class="fine" style="margin:0">No recorded imports or exports under this code last year.</p></div>`;
  const part = (p, cls) => { const m = Math.max(...p.map(x => x[1]), 1); return `<div class="mini">${p.map(x => `<div><span class="n">${esc(x[0])}</span><i class="${cls}" style="width:${(x[1] / m * 100).toFixed(0)}%"></i><b>${rs(x[1], true)}</b></div>`).join('')}</div>`; };
  const hist = H.codes[code8];
  let h = `<div class="trade"><h3 class="h" style="margin:0">Nepal trade, FY ${ST.fy}</h3>`;
  if (hist && hist.some(x => x[0])) h += `<div style="margin-top:var(--s2);font-size:.8rem;color:var(--muted)">Imports by year ${yoyTag(hist.map(x => x[0]))}</div>${sparkHTML(hist.map(x => x[0]), 0, '')}`;
  if (im){ const eff = im[3] ? (im[4] / im[3] * 100) : 0;
    h += `<div class="row2"><div><span>Imported</span><b>${rs(im[3], true)}</b></div><div><span>Quantity</span><b>${esc(qty(im[2], im[1]))}</b></div><div><span>Duty collected</span><b>${rs(im[4], true)}</b></div></div>
      <p class="fine" style="margin:0 0 4px">Import sources${im[6] > 6 ? ` (top 6 of ${im[6]})` : ''} · effective duty ${eff.toFixed(1)}% of value</p>${part(im[5], '')}`; }
  if (ex && hist && hist.some(x => x[1])) h += `<div style="margin-top:var(--s4);font-size:.8rem;color:var(--muted)">Exports by year ${yoyTag(hist.map(x => x[1]))}</div>${sparkHTML(hist.map(x => x[1]), 0, 'e')}`;
  if (ex){ h += `<div class="row2" style="margin-top:var(--s3)"><div><span>Exported</span><b>${rs(ex[3], true)}</b></div><div><span>Quantity</span><b>${esc(qty(ex[2], ex[1]))}</b></div><div><span>Markets</span><b>${ex[5]}</b></div></div>${part(ex[4], 'e')}`; }
  return h + '</div>';
}
function renderStats(){
  $('#st-sub').textContent = `Pick a fiscal year. Full detail from FY ${FY[0]} to ${FY[FY.length-1]}${ST.current ? ', plus ' + ST.current.fy + ' so far' : ''} · NPR`;
  $('#st-src-t').textContent = UNITS === 'intl' ? 'NPR 1 bn = 1 Arab = 100 Crore. Values as published by the Department of Customs.' : '1 Arab = 100 Crore = NPR 1 billion. Values as published by the Department of Customs.'; $('#u-np').setAttribute('aria-pressed', UNITS === 'np'); $('#u-intl').setAttribute('aria-pressed', UNITS === 'intl');
  $$('[data-sv]').forEach(b => b.setAttribute('aria-selected', b.dataset.sv === stView));
  renderYearSel();
  ecClear();
  const body = $('#st-body'); let h = '';
  const topN = (arr, key, n) => [...arr].sort((a, b) => b[key] - a[key]).slice(0, n);
  if (stView === 'overview'){
    const ch = CH(), co = CO(), ov = OV();
    h += `<div class="tiles">${kpiTiles(false)}</div>`;
    { const topCh = topN(ch, 2, 1)[0], topCo = topN(co, 1, 1)[0], topEx = topN(co, 2, 1)[0], topExCh = topN(ch, 3, 1)[0];
      const gi = pctc(ov.imports[1], ov.imports[0]), ge = pctc(ov.exports[1], ov.exports[0]);
      h += `<div class="facts-box"><h3>In plain words</h3><ul>
        <li>Nepal imported <b>${rs(ov.imports[1])}</b> of goods in FY ${yFY()}, ${gi >= 0 ? 'up' : 'down'} ${Math.abs(gi).toFixed(1)}% on the year before, and exported <b>${rs(ov.exports[1])}</b> (${ge >= 0 ? 'up' : 'down'} ${Math.abs(ge).toFixed(1)}%).</li>
        <li>For every NPR 100 exported, NPR ${(ov.imports_exports_ratio[1] * 100).toFixed(0)} was imported: a trade deficit of <b>${rs(ov.trade_deficit[1])}</b>.</li>
        <li><b>${esc(topCo[0])}</b> supplied ${(topCo[1] / ov.imports[1] * 100).toFixed(0)}% of all imports; <b>${esc(chapName(topCh[0]))}</b> was the largest import category (${(topCh[2] / ov.imports[1] * 100).toFixed(0)}%).</li>
        <li>The biggest export market was <b>${esc(topEx[0])}</b> (${(topEx[2] / ov.exports[1] * 100).toFixed(0)}% of exports); the top export category was <b>${esc(chapName(topExCh[0]))}</b>.</li></ul></div>`; }
    if (ST.current && isLatest()) h += `<div class="ytd">${ic('i-info')}<div>FY ${ST.current.fy} so far (${ST.current.months} month${ST.current.months > 1 ? 's' : ''}): imports <b>${rs(ST.current.overview.imports[1], true)}</b> (${pctc(ST.current.overview.imports[1], ST.current.overview.imports[0]) >= 0 ? '+' : ''}${pctc(ST.current.overview.imports[1], ST.current.overview.imports[0]).toFixed(1)}% on the same months last year), exports <b>${rs(ST.current.overview.exports[1], true)}</b>.</div></div>`;
    h += fig('Seven years of trade', 'Annual imports and exports, FY ' + FY[0] + ' to ' + FY[FY.length-1], `<div class="ech" id="ec-years"></div>`);
    h += fig('Map of imports', 'Every chapter sized by import value, FY ' + yFY() + '; tap a block to open it', `<div class="ech tall" id="ec-tree"></div>`);
    h += fig('Top import categories', 'Import value by tariff chapter, 10 largest', barRows(topN(ch, 2, 10).map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]), a: x[2] }))), '');
    h += fig('Top export categories', 'Export value by tariff chapter, 10 largest', barRows(topN(ch, 3, 10).map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]), a: x[3] })), { cls: 'e' }), '');
    h += fig('Where imports come from', 'Import value by partner country', barRows(topN(co, 1, 10).map(x => ({ k: 'co:' + x[0], label: x[0], a: x[1] }))), '');
    h += fig('Where exports go', 'Export value by destination', barRows(topN(co, 2, 10).map(x => ({ k: 'co:' + x[0], label: x[0], a: x[2] })), { cls: 'e' }), '');
    h += fig('Busiest customs points', 'Import and export value cleared per customs office', barRows(topN(CU(), 1, 8).map(x => ({ k: 'cu', label: x[0], a: x[1], b: x[2] }))), LEG2);
  }
  if (stView === 'trends'){
    h += fig('Imports by month', 'Monthly import value, last three fiscal years and ' + (ST.current ? ST.current.fy + ' so far' : ''), `<div class="ech" id="ec-mimp"></div>`);
    h += fig('Exports by month', 'Monthly export value', `<div class="ech" id="ec-mexp"></div>`);
    h += fig('Trade deficit by year', 'Imports minus exports', `<div class="ech short" id="ec-def"></div>`);
    const gr = [...ST.chapters].filter(c => H.chapters[c[0]] && H.chapters[c[0]][0][0] > 0).map(c => [c[0], H.chapters[c[0]][FY.length-1][0] / H.chapters[c[0]][0][0]]).sort((a, b) => b[1] - a[1]);
    h += fig('Fastest growing import categories', `Import value FY ${FY[FY.length-1]} compared with FY ${FY[0]}, chapters over NPR 5 Arab`, barRows(gr.filter(x => H.chapters[x[0]][FY.length-1][0] > 5e6).slice(0, 10).map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]) + ' · ×' + x[1].toFixed(1), a: H.chapters[x[0]][FY.length-1][0] }))));
  }
  if (stView === 'flows'){
    if (!isLatest()) h += `<p class="fine">Country-to-product flows are available for FY ${ST.fy}; showing that year.</p>`;
    h += fig('Where imports come from, and what they are', 'Largest source countries (left) flowing into the largest import categories (right), FY ' + ST.fy + ' — tap any country or category to open its trade page', `<div class="ech tall" id="ec-sankey" style="height:${window.innerWidth < 640 ? 520 : 460}px"></div>`);
    h += fig('Import sources over time', 'Top 6 sources by year', `<div class="ech" id="ec-co"></div>`);
  }
  if (stView === 'compare'){
    const opts = FY.map((y, i) => `<option value="${i}">${y}</option>`).join('');
    h += `<div class="cmp-ctl"><select id="cmp-a" aria-label="First year">${opts}</select><span>vs</span><select id="cmp-b" aria-label="Second year">${opts}</select></div>`;
    const A = cmpA, B = cmpB, ta = H.totals[A], tb = H.totals[B];
    const d = (a, b) => { const p = b ? (a - b) / b * 100 : 0; return `<small class="${p >= 0 ? 'up' : 'down'}">${p >= 0 ? '+' : ''}${p.toFixed(1)}%</small>`; };
    h += `<div class="tiles"><div class="tile"><span>Imports</span><b>${rs(tb[0], true)}</b>${d(tb[0], ta[0])}</div><div class="tile"><span>Exports</span><b>${rs(tb[1], true)}</b>${d(tb[1], ta[1])}</div><div class="tile"><span>Trade deficit</span><b>${rs(tb[0] - tb[1], true)}</b>${d(tb[0] - tb[1], ta[0] - ta[1])}</div><div class="tile"><span>Exports cover</span><b>${(tb[1] / tb[0] * 100).toFixed(1)}%</b><small class="neutral">was ${(ta[1] / ta[0] * 100).toFixed(1)}%</small></div></div>
      <p class="fine" style="margin-top:6px">FY ${FY[B]} compared with FY ${FY[A]}.</p>`;
    h += fig('Import categories, side by side', `Top 10 of FY ${FY[B]}`, `<div class="ech tall" id="ec-cmp-ch"></div>`);
    h += fig('Import sources, side by side', `Top 10 of FY ${FY[B]}`, `<div class="ech tall" id="ec-cmp-co"></div>`);
    const mv = Object.keys(H.chapters).map(Number).map(c => [c, H.chapters[c][B][0] - H.chapters[c][A][0]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 10);
    h += fig('Biggest changes in imports', `Chapters that moved most between FY ${FY[A]} and FY ${FY[B]}`, `<div class="bars">${mv.map(x => `<button class="br" data-k="ch:${x[0]}"><span class="l"><small class="in">${String(x[0]).padStart(2,'0')}</small>${esc(chapName(x[0]))}</span><span class="t"><span class="s"><i class="${x[1] < 0 ? 'e' : ''}" style="width:${(Math.abs(x[1]) / Math.abs(mv[0][1]) * 68).toFixed(1)}%"></i><b>${x[1] >= 0 ? '+' : '−'}${rs(Math.abs(x[1]), true)}</b></span></span></button>`).join('')}</div>`);
    h += `<div class="tsearch" style="margin-top:var(--s5)">${ic('i-search')}<input id="cmp-q" type="search" placeholder="Track any product, chapter or country across all years…" aria-label="Track across years" value="${esc(cmpQ)}"></div>`;
    if (cmpQ.trim()){
      const q = cmpQ.trim().toLowerCase();
      const cos = Object.keys(H.countries).filter(n => n.toLowerCase().includes(q)).slice(0, 3);
      const chs = Object.keys(H.chapters).map(Number).filter(c => chapName(c).toLowerCase().includes(q)).slice(0, 3);
      const codes = search(cmpQ).rows.map(r => r.digits).filter(c => H.codes[c] && H.codes[c].some(x => x[0] || x[1])).slice(0, 6);
      if (!cos.length && !chs.length && !codes.length) h += `<div class="empty"><b>Nothing matches</b><p>Try a product word, a chapter name or a country.</p></div>`;
      cos.forEach((n, i) => h += fig(esc(n), 'Imports from and exports to, by year', `<div class="ech short" id="ec-tr-co${i}"></div>`));
      chs.forEach((c, i) => h += fig(esc(chapName(c)) + ' (chapter ' + c + ')', 'Imports and exports by year', `<div class="ech short" id="ec-tr-ch${i}"></div>`));
      codes.forEach((c, i) => h += fig(`<span class="mono" style="font-size:.9rem">${c.slice(0,4)}.${c.slice(4,6)}.${c.slice(6)}</span> ${esc(codeLabel(c))}`, 'Imports and exports by year', `<div class="ech short" id="ec-tr-hs${i}"></div>`));
      h += `<script type="text/plain" id="cmp-track">${JSON.stringify({ cos, chs, codes })}<\/script>`;
    }
  }
  if (stView === 'products'){
    const q = stQ.trim();
    h += `<div class="tsearch">${ic('i-search')}<input id="st-q" type="search" placeholder="Product or HS code: cement, 8703, solar…" aria-label="Search traded products" value="${esc(stQ)}"></div>`;
    let list;
    if (q){ list = search(q).rows.map(r => r.digits).filter(c => impV(c) || expV(c)).slice(0, 40); }
    else { list = Object.keys(H.codes).sort((a, b) => impV(b) - impV(a)).slice(0, 25); h += `<h3 class="h" style="margin-top:var(--s2)">Top 25 imported products, FY ${yFY()}</h3>`; }
    if (!list.length) h += `<div class="empty"><b>No traded products match</b><p>Try another word or a 4-digit heading.</p></div>`;
    else h += fig(q ? `${list.length} matching products, FY ${yFY()}` : '', '', barRows(list.map(c => ({ k: 'hs:' + c, sub: c.slice(0,4)+'.'+c.slice(4,6)+'.'+c.slice(6), label: codeLabel(c), a: impV(c), b: expV(c) }))), LEG2);
  }
  if (stView === 'chapters'){
    if (stChapter){
      const c = stChapter, codes = Object.keys(H.codes).filter(k => +k.slice(0,2) === c && impV(k)).sort((a, b) => impV(b) - impV(a)).slice(0, 20);
      const ecodes = Object.keys(H.codes).filter(k => +k.slice(0,2) === c && expV(k)).sort((a, b) => expV(b) - expV(a)).slice(0, 10);
      const row = CH().find(x => x[0] === c) || [c, '', 0, 0, 0];
      h += `<button class="back" data-back="ch">${ic('i-left')}All chapters</button><h2 style="font-size:1.1rem;margin:8px 0 4px">Chapter ${c} · ${esc(chapName(c))}</h2>
        <div class="tiles" style="margin-bottom:var(--s2)"><div class="tile"><span>Imports</span><b>${rs(row[2], true)}</b></div><div class="tile"><span>Exports</span><b>${rs(row[3], true)}</b></div><div class="tile"><span>Duty collected</span><b>${rs(row[4], true)}</b></div><div class="tile"><span>Effective duty</span><b>${row[2] ? (row[4] / row[2] * 100).toFixed(1) : 0}%</b></div></div>`;
      if (H.chapters[c]) h += fig('Seven-year trend', 'Imports, exports and duty collected by year', `<div class="ech short" id="ec-chap"></div>`);
      if (codes.length) h += fig('Most imported lines', 'FY ' + yFY(), barRows(codes.map(k => ({ k: 'hs:' + k, sub: k.slice(0,4)+'.'+k.slice(4,6)+'.'+k.slice(6), label: codeLabel(k), a: impV(k) }))));
      if (ecodes.length) h += fig('Most exported lines', 'FY ' + yFY(), barRows(ecodes.map(k => ({ k: 'hs:' + k, sub: k.slice(0,4)+'.'+k.slice(4,6)+'.'+k.slice(6), label: codeLabel(k), a: expV(k) })), { cls: 'e' }));
    } else {
      const key = { imp: 2, exp: 3, rev: 4 }[stSort];
      const rows = CH().sort((a, b) => b[key] - a[key]);
      h += `<div class="sortbar">Sort by ${['imp','exp','rev'].map(k => `<button data-sort="${k}" aria-pressed="${stSort === k}">${{ imp: 'Imports', exp: 'Exports', rev: 'Duty collected' }[k]}</button>`).join('')}</div>`;
      h += fig('All chapters, FY ' + yFY(), '', barRows(rows.map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]), a: x[key] })), { cls: stSort === 'exp' ? 'e' : stSort === 'rev' ? 'r' : '' }));
    }
  }
  if (stView === 'countries'){
    if (stCountry){
      const row = CO().find(x => x[0] === stCountry) || [stCountry, 0, 0], top = isLatest() ? (ST.country_top[stCountry] || [[], []]) : [[], []];
      h += `<button class="back" data-back="co">${ic('i-left')}All countries</button><h2 style="font-size:1.1rem;margin:8px 0 4px">${esc(stCountry)}</h2>
        <div class="tiles" style="margin-bottom:var(--s2)"><div class="tile"><span>Imports from</span><b>${rs(row[1], true)}</b></div><div class="tile"><span>Exports to</span><b>${rs(row[2], true)}</b></div></div>`;
      if (H.countries[stCountry]) h += fig('Seven-year trend', 'Imports from and exports to ' + esc(stCountry), `<div class="ech short" id="ec-cty"></div>`);
      if (!isLatest()) h += `<p class="fine">Product breakdown by country is available for FY ${ST.fy} (select it above).</p>`;
      const cp = isLatest() ? (ST.country_prod && ST.country_prod[stCountry]) : null;
      const prodFig = (list, rem, total, sell) => {
        if (!list || !list.length) return '';
        const items = list.map(([c, v]) => ({ k: 'hs:' + c, sub: c.slice(0,4) + '.' + c.slice(4,6) + '.' + c.slice(6), label: codeLabel(c) + (total ? ' · ' + (v / total * 100).toFixed(1) + '%' : ''), a: v }));
        if (rem && rem[0]) items.push({ sub: '', label: rem[1] + ' other products', a: rem[0] });
        return fig(sell ? 'What Nepal sells to ' + esc(stCountry) : 'What Nepal buys from ' + esc(stCountry), 'Top ' + list.length + ' products by value · tap a bar for its trend', barRows(items, sell ? { cls: 'e' } : undefined));
      };
      if (cp){ h += prodFig(cp[0], cp[1], row[1], false); h += prodFig(cp[2], cp[3], row[2], true); }
      else if (top[0].length || top[1].length){
        if (top[0].length) h += fig('What Nepal buys from ' + esc(stCountry), '', barRows(top[0].map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]), a: x[1] }))));
        if (top[1].length) h += fig('What Nepal sells to ' + esc(stCountry), '', barRows(top[1].map(x => ({ k: 'ch:' + x[0], sub: String(x[0]).padStart(2, '0'), label: chapName(x[0]), a: x[1] })), { cls: 'e' }));
      }
    } else {
      const q = stQ.trim().toLowerCase();
      h += `<div class="tsearch">${ic('i-search')}<input id="st-q" type="search" placeholder="Find a country" aria-label="Find a country" value="${esc(stQ)}"></div>`;
      const key = stSort === 'exp' ? 2 : 1;
      h += `<div class="sortbar">Sort by ${['imp','exp'].map(k => `<button data-sort="${k}" aria-pressed="${stSort === k}">${{ imp: 'Imports', exp: 'Exports' }[k]}</button>`).join('')}</div>`;
      const rows = CO().filter(x => !q || x[0].toLowerCase().includes(q)).sort((a, b) => b[key] - a[key]).slice(0, q ? 200 : 40);
      h += fig(q ? `${rows.length} countries` : 'Top 40 trading partners, FY ' + yFY(), '', barRows(rows.map(x => ({ k: 'co:' + x[0], label: x[0], a: x[1], b: x[2] }))), LEG2);
    }
  }
  if (stView === 'customs'){
    const cu = CU(), ti = cu.reduce((a, x) => a + x[1], 0), te = cu.reduce((a, x) => a + x[2], 0);
    h += fig('Imports and exports by customs office', 'FY ' + yFY(), barRows([...cu].sort((a, b) => b[1] - a[1]).map(x => ({ label: x[0], a: x[1], b: x[2] }))), LEG2);
    h += `<div class="suggest" style="margin:0 0 var(--s3)"><button data-k="offices">${ic('i-list')}Office addresses and contacts</button></div>`;
    h += `<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Customs office</th><th>Imports</th><th>Share</th><th>Exports</th><th>Share</th></tr></thead><tbody>${[...cu].sort((a, b) => b[1] - a[1]).map(x => `<tr><td>${esc(x[0])}</td><td>${rs(x[1], true)}</td><td>${(x[1] / ti * 100).toFixed(1)}%</td><td>${rs(x[2], true)}</td><td>${(x[2] / te * 100).toFixed(1)}%</td></tr>`).join('')}</tbody></table></div>`;
  }
  if (stView === 'duty'){
    const bd = BD(), tv = bd.reduce((a, x) => a + x[2], 0), td = bd.reduce((a, x) => a + x[1], 0);
    h += fig('Import value by customs duty rate', 'How much of what Nepal imported in FY ' + yFY() + ' falls in each duty band', barRows(bd.map(x => ({ label: (x[0] === '0' ? 'Duty free' : isNaN(+x[0]) ? x[0].replace(/^./, c => c.toUpperCase()) : +x[0] + '% duty'), a: x[2] }))));
    h += fig('Duty collected by rate', '', barRows(bd.map(x => ({ label: (x[0] === '0' ? 'Duty free' : isNaN(+x[0]) ? x[0].replace(/^./, c => c.toUpperCase()) : +x[0] + '% duty'), a: x[1] })), { cls: 'r' }));
    h += `<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Duty rate</th><th>Import value</th><th>Share</th><th>Duty collected</th><th>Share</th></tr></thead><tbody>${bd.map(x => `<tr><td>${x[0] === '0' ? 'Duty free' : isNaN(+x[0]) ? esc(x[0]) : +x[0] + '%'}</td><td>${rs(x[2], true)}</td><td>${(x[2] / tv * 100).toFixed(1)}%</td><td>${rs(x[1], true)}</td><td>${(x[1] / td * 100).toFixed(1)}%</td></tr>`).join('')}</tbody></table></div>`;
  }
  body.innerHTML = h;
  if (!HAS_EC) return;
  if (stView === 'overview'){ yearBars($('#ec-years'), [{ name: 'Imports', data: H.totals.map(t => t[0]) }, { name: 'Exports', data: H.totals.map(t => t[1]) }], ['Imports', 'Exports']); treemapChart($('#ec-tree')); const tc = charts[charts.length-1]; if (tc) tc.on('click', p => { if (p.data && p.data.ch){ stView = 'chapters'; stChapter = p.data.ch; renderStats(); window.scrollTo({top:0}); } }); }
  if (stView === 'compare'){
    const A = cmpA, B = cmpB, two = (el, cats, fa, fb) => ecInit(el, { grid: { left: 8, right: 12, top: 30, bottom: 8, containLabel: true }, tooltip: Object.assign({}, tip, { trigger: 'axis' }), legend: { top: 0, textStyle: { color: tok('--fg-2') } },
      yAxis: Object.assign(axisBase(), { type: 'category', inverse: true, data: cats, axisLabel: { color: tok('--fg-2'), fontSize: 11, width: 110, overflow: 'truncate' } }), xAxis: Object.assign(axisBase(), { type: 'value', splitNumber: 3, axisLabel: { color: tok('--muted'), fontSize: 11, formatter: v => rs(v, true) } }),
      series: [{ name: 'FY ' + FY[A], type: 'bar', data: fa, itemStyle: { color: tok('--muted') }, barMaxWidth: 12 }, { name: 'FY ' + FY[B], type: 'bar', data: fb, itemStyle: { color: tok('--imp') }, barMaxWidth: 12 }] });
    const topCh = Object.keys(H.chapters).map(Number).sort((a, b) => H.chapters[b][B][0] - H.chapters[a][B][0]).slice(0, 10);
    two($('#ec-cmp-ch'), topCh.map(chapName), topCh.map(c => H.chapters[c][A][0]), topCh.map(c => H.chapters[c][B][0]));
    const topCo = Object.keys(H.countries).sort((a, b) => H.countries[b][B][0] - H.countries[a][B][0]).slice(0, 10);
    two($('#ec-cmp-co'), topCo, topCo.map(c => H.countries[c][A][0]), topCo.map(c => H.countries[c][B][0]));
    const tr = $('#cmp-track'); if (tr){ const t = JSON.parse(tr.textContent);
      t.cos.forEach((n, i) => yearBars($('#ec-tr-co' + i), [{ name: 'Imports from', data: H.countries[n].map(x => x[0]) }, { name: 'Exports to', data: H.countries[n].map(x => x[1]) }], ['a', 'b']));
      t.chs.forEach((c, i) => yearBars($('#ec-tr-ch' + i), [{ name: 'Imports', data: H.chapters[c].map(x => x[0]) }, { name: 'Exports', data: H.chapters[c].map(x => x[1]) }], ['a', 'b']));
      t.codes.forEach((c, i) => yearBars($('#ec-tr-hs' + i), [{ name: 'Imports', data: H.codes[c].map(x => x[0]) }, { name: 'Exports', data: H.codes[c].map(x => x[1]) }], ['a', 'b'])); }
    $('#cmp-a').value = A; $('#cmp-b').value = B;
  }
  if (stView === 'trends'){ monthlyLine($('#ec-mimp'), 'imp'); monthlyLine($('#ec-mexp'), 'exp'); yearBars($('#ec-def'), [{ name: 'Trade deficit', data: H.totals.map(t => t[0] - t[1]) }], ['Trade deficit']); }
  if (stView === 'flows'){ sankeyChart($('#ec-sankey')); const top6 = [...ST.countries].sort((a, b) => b[1] - a[1]).slice(0, 6).map(x => x[0]);
    ecInit($('#ec-co'), { grid: { left: 8, right: 12, top: 34, bottom: 24, containLabel: true }, tooltip: tip, legend: { top: 0, textStyle: { color: tok('--fg-2') }, itemWidth: 14 },
      xAxis: Object.assign(axisBase(), { type: 'category', data: FY }), yAxis: Object.assign(axisBase(), { type: 'value', axisLabel: { color: tok('--muted'), fontSize: 11, formatter: v => rs(v, true) } }),
      series: top6.map((nm, k) => ({ name: nm, type: 'line', smooth: .2, showSymbol: false, lineStyle: { width: 2 }, data: (H.countries[nm] || []).map(x => x[0]) })), color: ['#1D81A2', '#E8722E', '#2E9E6B', '#7C5CBF', '#B8860B', '#7F8C8D'] }); }
  if (stView === 'chapters' && stChapter && H.chapters[stChapter]) yearBars($('#ec-chap'), [{ name: 'Imports', data: H.chapters[stChapter].map(x => x[0]) }, { name: 'Exports', data: H.chapters[stChapter].map(x => x[1]) }, { name: 'Duty collected', data: H.chapters[stChapter].map(x => x[2]) }], ['Imports', 'Exports', 'Duty collected']);
  if (stView === 'countries' && stCountry && H.countries[stCountry]) yearBars($('#ec-cty'), [{ name: 'Imports from', data: H.countries[stCountry].map(x => x[0]) }, { name: 'Exports to', data: H.countries[stCountry].map(x => x[1]) }], ['Imports from', 'Exports to']);
}
function renderExports(){
  var exb = document.getElementById('ex-body'); if (!exb) return;
  var sub = document.getElementById('ex-sub'); if (sub) sub.textContent = 'What Nepal sells abroad — by product and destination. FY ' + yFY() + ' · NPR';
  ecClear();
  var ch = CH(), co = CO(), ov = OV();
  var topN = function(arr, key, n){ return arr.slice().sort(function(a,b){return b[key]-a[key];}).slice(0, n); };
  var expTot = ov.exports[1] || 1;
  var ge = pctc(ov.exports[1], ov.exports[0]);
  var topCo = topN(co, 2, 1)[0], topCh = topN(ch, 3, 1)[0];
  var top5 = topN(ch, 3, 5).reduce(function(a,x){return a + x[3];}, 0);
  var share = ov.exports[1] / ((ov.imports[1] + ov.exports[1]) || 1) * 100;
  var arrow = function(g){ return ic(g >= 0 ? 'i-up' : 'i-down').replace('class="i"', 'class="i" style="width:14px;height:14px"'); };
  var h = '';
  h += '<div class="tiles">'
    + '<div class="tile"><span>Exports FY ' + yFY() + '</span><b>' + rs(ov.exports[1], true) + '</b><small class="' + (ge>=0?'up':'down') + '">' + arrow(ge) + Math.abs(ge).toFixed(1) + '%&nbsp;vs&nbsp;' + (FY[stYear-1]||'prev') + '</small></div>'
    + '<div class="tile"><span>Share of total trade</span><b>' + share.toFixed(1) + '%</b><small class="neutral">exports of all trade</small></div>'
    + '<div class="tile"><span>Top market</span><b>' + esc(topCo[0]) + '</b><small class="neutral">' + (topCo[2]/expTot*100).toFixed(0) + '% of exports</small></div>'
    + '<div class="tile"><span>Top product</span><b style="font-size:.98rem;line-height:1.2">' + esc(chapName(topCh[0])) + '</b><small class="neutral">' + (topCh[3]/expTot*100).toFixed(0) + '% of exports</small></div>'
    + '</div>';
  h += '<div class="facts-box"><h3>In plain words</h3><ul>'
    + '<li>Nepal exported <b>' + rs(ov.exports[1]) + '</b> in FY ' + yFY() + ', ' + (ge>=0?'up':'down') + ' ' + Math.abs(ge).toFixed(1) + '% on the year before.</li>'
    + '<li><b>' + esc(topCo[0]) + '</b> took ' + (topCo[2]/expTot*100).toFixed(0) + '% of all exports, and the top five product groups make up <b>' + (top5/expTot*100).toFixed(0) + '%</b> — exports are highly concentrated.</li>'
    + '<li>The largest export category was <b>' + esc(chapName(topCh[0])) + '</b> (' + (topCh[3]/expTot*100).toFixed(0) + '%).</li>'
    + '<li>Exports cover only <b>' + (ov.exports[1]/(ov.imports[1]||1)*100).toFixed(0) + '%</b> of what Nepal imports — a trade deficit of <b>' + rs(ov.imports[1]-ov.exports[1]) + '</b>.</li></ul></div>';
  if (ST.current && isLatest()){ var cex = ST.current.overview.exports, cg = pctc(cex[1], cex[0]); h += '<div class="ytd">' + ic('i-info') + '<div>FY ' + ST.current.fy + ' so far (' + ST.current.months + ' mo): exports <b>' + rs(cex[1], true) + '</b> (' + (cg>=0?'+':'') + cg.toFixed(1) + '% on the same months last year).</div></div>'; }
  h += fig('Exports by year', 'Annual export value, FY ' + FY[0] + ' to ' + FY[FY.length-1], '<div class="ech short" id="ecx-trend"></div>');
  h += fig('Map of exports', 'Every chapter sized by export value, FY ' + yFY() + '; tap a block to open it', '<div class="ech tall" id="ecx-tree"></div>');
  h += fig('Top export categories', 'Export value by tariff chapter, 12 largest', barRows(topN(ch,3,12).map(function(x){return {k:'ch:'+x[0], sub:String(x[0]).padStart(2,'0'), label:chapName(x[0]), a:x[3]};}), {cls:'e'}));
  h += fig('Where exports go', 'Export value by destination country, 12 largest', barRows(topN(co,2,12).map(function(x){return {k:'co:'+x[0], label:x[0], a:x[2]};}), {cls:'e'}));
  if (isLatest() && FY.length > 1){
    var mv = ch.map(function(c){ var cur=c[3], prev=(H.chapters[c[0]]&&H.chapters[c[0]][stYear-1])?H.chapters[c[0]][stYear-1][1]:0; return {ch:c[0], cur:cur, g: prev>0?((cur-prev)/prev*100):null}; }).filter(function(x){return x.cur>5e5 && x.g!==null;});
    var up = mv.slice().sort(function(a,b){return b.g-a.g;}).slice(0,6);
    var dn = mv.slice().sort(function(a,b){return a.g-b.g;}).slice(0,6);
    if (up.length) h += fig('Fastest rising exports', 'Biggest year-on-year gains, chapters over NPR 50 Crore', barRows(up.map(function(x){return {k:'ch:'+x.ch, sub:(x.g>=0?'+':'')+x.g.toFixed(0)+'%', label:chapName(x.ch), a:x.cur};}), {cls:'e'}));
    if (dn.length) h += fig('Falling exports', 'Biggest year-on-year declines', barRows(dn.map(function(x){return {k:'ch:'+x.ch, sub:x.g.toFixed(0)+'%', label:chapName(x.ch), a:x.cur};}), {cls:'e'}));
  }
  h += '<div class="facts-box"><h3>How exporting from Nepal works</h3><ul>'
    + '<li><b>No export duty on most goods.</b> It applies only to a set list of raw materials (hides, wool, aggregates, some scrap) — finished goods usually leave duty-free.</li>'
    + '<li><b>Exports are zero-rated for VAT</b>, and exporters reclaim VAT paid on inputs.</li>'
    + '<li><b>Cash incentive:</b> the government pays about 3–5% cash back on export value, scaled by domestic value addition.</li>'
    + '<li><b>LDC-graduation watch:</b> duty-free access to the EU and other markets rests on Nepal&rsquo;s LDC status; the UN has extended Nepal&rsquo;s LDC preparatory period to November 2029, after which graduation would phase those out. Access to India is treaty-based and unaffected.</li></ul></div>';
  h += fig('Exports by month', 'Monthly export value, recent fiscal years', '<div class="ech" id="ecx-month"></div>');
  exb.innerHTML = h;
  if (!HAS_EC) return;
  yearBars($('#ecx-trend'), [{name:'Exports', data:H.totals.map(function(t){return t[1];})}], ['Exports']);
  treemapChart($('#ecx-tree'), 'exp'); var tc = charts[charts.length-1]; if (tc) tc.on('click', function(p){ if (p.data && p.data.ch){ stView='chapters'; stChapter=p.data.ch; stCountry=null; go('stats','push'); } });
  monthlyLine($('#ecx-month'), 'exp');
}
$('#v-exports').addEventListener('click', function(e){ var b = e.target.closest('[data-k]'); if (!b) return; var k = b.dataset.k || ''; if (k.indexOf('ch:')===0){ stView='chapters'; stChapter=+k.slice(3); stCountry=null; go('stats','push'); } else if (k.indexOf('co:')===0){ stView='countries'; stCountry=k.slice(3); stChapter=null; go('stats','push'); } });
function renderImports(){
  var imb = document.getElementById('im-body'); if (!imb) return;
  var sub = document.getElementById('im-sub'); if (sub) sub.textContent = 'What Nepal buys from abroad — by product and source. FY ' + yFY() + ' · NPR';
  ecClear();
  var ch = CH(), co = CO(), ov = OV();
  var topN = function(arr, key, n){ return arr.slice().sort(function(a,b){return b[key]-a[key];}).slice(0, n); };
  var impTot = ov.imports[1] || 1;
  var gi = pctc(ov.imports[1], ov.imports[0]);
  var topCo = topN(co, 1, 1)[0], topCh = topN(ch, 2, 1)[0];
  var top5 = topN(ch, 2, 5).reduce(function(a,x){return a + x[2];}, 0);
  var share = ov.imports[1] / ((ov.imports[1] + ov.exports[1]) || 1) * 100;
  var arrow = function(g){ return ic(g >= 0 ? 'i-up' : 'i-down').replace('class="i"', 'class="i" style="width:14px;height:14px"'); };
  var h = '';
  h += '<div class="tiles">'
    + '<div class="tile"><span>Imports FY ' + yFY() + '</span><b>' + rs(ov.imports[1], true) + '</b><small class="' + (gi>=0?'up':'down') + '">' + arrow(gi) + Math.abs(gi).toFixed(1) + '%&nbsp;vs&nbsp;' + (FY[stYear-1]||'prev') + '</small></div>'
    + '<div class="tile"><span>Share of total trade</span><b>' + share.toFixed(1) + '%</b><small class="neutral">imports of all trade</small></div>'
    + '<div class="tile"><span>Top source</span><b>' + esc(topCo[0]) + '</b><small class="neutral">' + (topCo[1]/impTot*100).toFixed(0) + '% of imports</small></div>'
    + '<div class="tile"><span>Top product</span><b style="font-size:.98rem;line-height:1.2">' + esc(chapName(topCh[0])) + '</b><small class="neutral">' + (topCh[2]/impTot*100).toFixed(0) + '% of imports</small></div>'
    + '</div>';
  h += '<div class="facts-box"><h3>In plain words</h3><ul>'
    + '<li>Nepal imported <b>' + rs(ov.imports[1]) + '</b> in FY ' + yFY() + ', ' + (gi>=0?'up':'down') + ' ' + Math.abs(gi).toFixed(1) + '% on the year before.</li>'
    + '<li><b>' + esc(topCo[0]) + '</b> supplied ' + (topCo[1]/impTot*100).toFixed(0) + '% of all imports; the top five product groups make up <b>' + (top5/impTot*100).toFixed(0) + '%</b>.</li>'
    + '<li>The largest import category was <b>' + esc(chapName(topCh[0])) + '</b> (' + (topCh[2]/impTot*100).toFixed(0) + '%).</li>'
    + '<li>Imports are <b>' + (ov.imports[1]/(ov.exports[1]||1)).toFixed(1) + '×</b> exports — a trade deficit of <b>' + rs(ov.imports[1]-ov.exports[1]) + '</b>.</li></ul></div>';
  if (ST.current && isLatest()){ var cim = ST.current.overview.imports, cg = pctc(cim[1], cim[0]); h += '<div class="ytd">' + ic('i-info') + '<div>FY ' + ST.current.fy + ' so far (' + ST.current.months + ' mo): imports <b>' + rs(cim[1], true) + '</b> (' + (cg>=0?'+':'') + cg.toFixed(1) + '% on the same months last year).</div></div>'; }
  h += fig('Imports by year', 'Annual import value, FY ' + FY[0] + ' to ' + FY[FY.length-1], '<div class="ech short" id="eci-trend"></div>');
  h += fig('Map of imports', 'Every chapter sized by import value, FY ' + yFY() + '; tap a block to open it', '<div class="ech tall" id="eci-tree"></div>');
  h += fig('Top import categories', 'Import value by tariff chapter, 12 largest', barRows(topN(ch,2,12).map(function(x){return {k:'ch:'+x[0], sub:String(x[0]).padStart(2,'0'), label:chapName(x[0]), a:x[2]};})));
  h += fig('Where imports come from', 'Import value by source country, 12 largest', barRows(topN(co,1,12).map(function(x){return {k:'co:'+x[0], label:x[0], a:x[1]};})));
  if (isLatest() && FY.length > 1){
    var mv = ch.map(function(c){ var cur=c[2], prev=(H.chapters[c[0]]&&H.chapters[c[0]][stYear-1])?H.chapters[c[0]][stYear-1][0]:0; return {ch:c[0], cur:cur, g: prev>0?((cur-prev)/prev*100):null}; }).filter(function(x){return x.cur>5e6 && x.g!==null;});
    var up = mv.slice().sort(function(a,b){return b.g-a.g;}).slice(0,6);
    var dn = mv.slice().sort(function(a,b){return a.g-b.g;}).slice(0,6);
    if (up.length) h += fig('Fastest rising imports', 'Biggest year-on-year gains, chapters over NPR 5 Arab', barRows(up.map(function(x){return {k:'ch:'+x.ch, sub:(x.g>=0?'+':'')+x.g.toFixed(0)+'%', label:chapName(x.ch), a:x.cur};})));
    if (dn.length) h += fig('Falling imports', 'Biggest year-on-year declines', barRows(dn.map(function(x){return {k:'ch:'+x.ch, sub:x.g.toFixed(0)+'%', label:chapName(x.ch), a:x.cur};})));
  }
  h += '<div class="facts-box"><h3>Imports &amp; customs revenue</h3><ul>'
    + '<li><b>Imports are where government revenue comes from</b> — customs duty, 13% VAT and excise on the landed (CIF) value.</li>'
    + '<li><b>India is the biggest source</b>, followed by China; fuels, oils &amp; gas and machinery are the largest categories.</li>'
    + '<li>Use the <a href="/calculator">tax calculator</a> to estimate duty + VAT + landed cost, or <a href="/trade-data">compare years and duty bands</a> in the full trade view.</li></ul></div>';
  h += fig('Imports by month', 'Monthly import value, recent fiscal years', '<div class="ech" id="eci-month"></div>');
  imb.innerHTML = h;
  if (!HAS_EC) return;
  yearBars($('#eci-trend'), [{name:'Imports', data:H.totals.map(function(t){return t[0];})}], ['Imports']);
  treemapChart($('#eci-tree')); var tc = charts[charts.length-1]; if (tc) tc.on('click', function(p){ if (p.data && p.data.ch){ stView='chapters'; stChapter=p.data.ch; stCountry=null; go('stats','push'); } });
  monthlyLine($('#eci-month'), 'imp');
}
$('#v-imports').addEventListener('click', function(e){ var b = e.target.closest('[data-k]'); if (!b) return; var k = b.dataset.k || ''; if (k.indexOf('ch:')===0){ stView='chapters'; stChapter=+k.slice(3); stCountry=null; go('stats','push'); } else if (k.indexOf('co:')===0){ stView='countries'; stCountry=k.slice(3); stChapter=null; go('stats','push'); } });
$('#v-stats').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.id === 'u-np' || b.id === 'u-intl'){ UNITS = b.id === 'u-np' ? 'np' : 'intl'; store.set('units', UNITS); renderStats(); return; }
  if (b.dataset.year !== undefined){ stYear = +b.dataset.year; renderStats(); return; }
  if (b.dataset.sv){ stView = b.dataset.sv; stQ = ''; stCountry = null; stChapter = null; renderStats(); return; }
  if (b.dataset.sort){ stSort = b.dataset.sort; renderStats(); return; }
  if (b.dataset.back){ if (b.dataset.back === 'co') stCountry = null; else stChapter = null; renderStats(); window.scrollTo({top:0}); return; }
  const k = b.dataset.k; if (!k) return;
  if (k.startsWith('hs:')){ const c = k.slice(3); const code = c.slice(0,4)+'.'+c.slice(4,6)+'.'+c.slice(6); if (BY[code]) openDetail(code); else toast('Code not in the 2026/27 tariff'); return; }
  if (k.startsWith('ch:')){ stView = 'chapters'; stChapter = +k.slice(3); renderStats(); window.scrollTo({top:0}); return; }
  if (k.startsWith('co:')){ stView = 'countries'; stCountry = k.slice(3); renderStats(); window.scrollTo({top:0}); return; }
  if (k === 'cu'){ stView = 'customs'; renderStats(); window.scrollTo({top:0}); }
  if (k === 'offices'){ browsePage = 'offices'; browseChap = null; browseQ = ''; go('browse'); renderBrowse(); window.scrollTo({top:0}); }
});
$('#v-stats').addEventListener('change', e => { if (e.target.id === 'cmp-a'){ cmpA = +e.target.value; renderStats(); } if (e.target.id === 'cmp-b'){ cmpB = +e.target.value; renderStats(); } });
$('#v-stats').addEventListener('input', e => { if (e.target.id === 'cmp-q'){ cmpQ = e.target.value; clearTimeout(window._cq); window._cq = setTimeout(() => { const pos = e.target.selectionStart; renderStats(); const el = $('#cmp-q'); if (el){ el.focus(); try{ el.setSelectionRange(pos, pos); }catch(x){} } }, 250); return; }
  if (e.target.id === 'st-q'){ stQ = e.target.value; const pos = e.target.selectionStart; renderStats(); const el = $('#st-q'); if (el){ el.focus(); try{ el.setSelectionRange(pos, pos); }catch(x){} } } });

/* ---------- tabs ---------- */
const TITLES = {
  search: 'HS Code Nepal & Nepal Customs Tariff 2083/84 | Customs Nepal',
  ai: 'Ask AI — Nepal HS Code Classifier | Customs Nepal',
  stats: 'Nepal Foreign Trade Data — Imports & Exports | Customs Nepal',
  exports: 'Nepal Exports Data — by Product & Country | Customs Nepal',
  imports: 'Nepal Imports Data — by Product & Country | Customs Nepal',
  browse: 'Browse the Nepal Customs Tariff 2026/27 | Customs Nepal',
  calc: 'Nepal Import Duty & Landed Cost Calculator 2083/84 | Customs Nepal',
  invoice: 'Proforma & Commercial Invoice Generator | Customs Nepal',
  saved: 'Saved HS Codes | Customs Nepal',
  about: 'About Customs Nepal — Nepal HS Code, Customs Tariff & Trade Portal',
  privacy: 'Privacy Policy | Customs Nepal'
};
const TABPATH = { search:'/', ai:'/ask-ai', stats:'/trade-data', exports:'/exports', imports:'/imports', browse:'/browse', calc:'/calculator', invoice:'/invoice', saved:'/saved', about:'/about', privacy:'/privacy' };
let curTab = 'search';
function go(t, hist){
  curTab = t;
  // hist === 'init': first paint of a route that has its own static page (scripts/app_pages.py) — keep its server <title>
  try { if (hist !== 'init') document.title = TITLES[t] || TITLES.search; } catch(e){}
  ['search','ai','stats','exports','imports','browse','calc','invoice','saved','about','privacy'].forEach(x => { var el = $('#v-' + x); if (el) el.hidden = x !== t; });
  if (t === 'stats') renderStats(); else if (t === 'exports') renderExports(); else if (t === 'imports') renderImports(); else ecClear();
  if (t === 'ai') initAI();
  $$('[data-tab]').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === t));
  try { $$('[data-toolt]').forEach(b => b.setAttribute('aria-selected', b.dataset.toolt === t)); if (t === 'invoice') $$('[data-tab="calc"]').forEach(b => b.setAttribute('aria-selected', 'true')); } catch(e){}
  if (t === 'browse') renderBrowse(); if (t === 'saved') renderSaved(); if (t === 'calc'){ calcTracked = false; calc(); } if (t === 'invoice') initInvoice();
  try { var _p = TABPATH[t] || '/', _u = 'https://www.customsnepal.com' + _p;
        var _c = document.querySelector('link[rel="canonical"]'); if (_c) _c.setAttribute('href', _u);
        var _ou = document.querySelector('meta[property="og:url"]'); if (_ou) _ou.setAttribute('content', _u);
        var _ot = document.querySelector('meta[property="og:title"]'); if (_ot && hist !== 'init') _ot.setAttribute('content', TITLES[t] || TITLES.search);
        if (hist === 'push') history.pushState(null,'',_p); else if (hist !== false) history.replaceState(null,'',_p); } catch(e){}
  window.scrollTo({top:0});
}
$$('[data-tab]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); go(b.dataset.tab, 'push'); }));
$$('[data-toolt]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); go(b.dataset.toolt, 'push'); }));

setOrigin(origin);
initCalc();
renderResults();
try { const uq = new URLSearchParams(location.search).get('q'); if (uq && uq.trim()) runQuery(uq.trim()); } catch(e){}
const PATHS = { '/':'search','/index.html':'search','/search':'search','/ask-ai':'ai','/trade-data':'stats','/exports':'exports','/imports':'imports','/browse':'browse','/calculator':'calc','/invoice':'invoice','/saved':'saved','/about':'about','/privacy':'privacy' };
const _pt = PATHS[location.pathname];
if (_pt && _pt !== 'search') go(_pt, 'init');
window.addEventListener('popstate', function(){ var t = PATHS[location.pathname]; if (t) go(t, false); });
const h = (location.hash || '').slice(1);
if (h.startsWith('hs-') && BY[h.slice(3)]) openDetail(h.slice(3));
else if (!_pt && ['ai','stats','exports','imports','browse','calc','invoice','saved','about','privacy'].includes(h)) go(h);
// expose a minimal API for the account module (below)
try { window.CN = { invData, applyExtracted, go, openDetail, BY }; } catch(e){}
}
__boot();
})();
