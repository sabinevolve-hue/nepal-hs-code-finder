(function(){
const $=s=>document.querySelector(s), app=document.getElementById('app');
// Works at the subdomain root (BASE='') and under a /world/ subpath (preview on the main domain).
const BASE=(location.pathname.match(/^\/world(?=\/|$)/)?'/world':'');
const ic=(p)=>`<svg class="i" viewBox="0 0 24 24">${p}</svg>`;
const I={search:'<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',right:'<path d="M9 6l6 6-6 6"/>',left:'<path d="M15 6l-6 6 6 6"/>',info:'<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',shield:'<path d="M12 2 4 5v6c0 5 3.4 8.3 8 11 4.6-2.7 8-6 8-11V5z"/><path d="m9 12 2 2 4-4"/>',globe:'<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20"/>',box:'<path d="M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8"/>',chart:'<path d="M3 3v18h18"/><path d="M7 15v-4M12 15V7M17 15v-6"/>'};
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// money in USD -> $1.23T / $456B / $12.3M
function money(v){ if(v==null||isNaN(v))return'—'; const a=Math.abs(v);
  if(a>=1e12)return'$'+(v/1e12).toFixed(2)+'T'; if(a>=1e9)return'$'+(v/1e9).toFixed(a<1e10?1:0)+'B';
  if(a>=1e6)return'$'+(v/1e6).toFixed(0)+'M'; return'$'+Math.round(v).toLocaleString();}

// Shared reference data (official sources, product groups, export guides) lives in world-src/meta.json —
// the prerender (scripts/world_prerender.py) inlines it here so the SPA and the static pages use one source.
const META=/*@META@*/null;
const {OFFICIAL,EUROSTAT,PGROUPS,EXGUIDES}=META;
const groupSlug=l=>l.toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');
const chapterGroup=ch=>{ch=+ch;return PGROUPS.find(g=>ch>=g[1]&&ch<=g[2]);};
function productTraders(label,flow){const key=flow==='exp'?'expProducts':'impProducts';const out=[];TRADE.countries.forEach(c=>{if(!c[key])return;const e=c[key].find(p=>p[0]===label);if(e&&e[1]>0)out.push([c.iso,c.name,c.flag,e[1]]);});out.sort((a,b)=>b[3]-a[3]);return out;}
// Per-HS6 global trade + Nepal's real trade (BACI 2024) — lazy-loaded; values in millions USD.
let PROD=null, PRODp=null, NEP=null, NEPp=null, DUTY=null, DUTYp=null, curHS=null;
function loadProd(){ if(PRODp)return PRODp; PRODp=fetch(BASE+'/data/prod.json').then(r=>r.ok?r.json():{}).then(d=>(PROD=d)).catch(()=>(PROD={})); return PRODp; }
function loadNep(){ if(NEPp)return NEPp; NEPp=fetch(BASE+'/data/nepal.json').then(r=>r.ok?r.json():{}).then(d=>(NEP=d)).catch(()=>(NEP={})); return NEPp; }
function loadDuty(){ if(DUTYp)return DUTYp; DUTYp=fetch(BASE+'/data/nepduty.json').then(r=>r.ok?r.json():{}).then(d=>(DUTY=d)).catch(()=>(DUTY={})); return DUTYp; }
function fmtUSD(n){ return '$'+Math.round(n).toLocaleString('en-US'); }
// Landed cost into Nepal on a $1,000 CIF shipment: SAARC/SAFTA origin vs general origin (customs duty + 13% VAT).
function landedBlock(code){
  if(DUTY===null){ loadDuty().then(()=>{ if(curHS===code) hsDetail(code,true); }); return ''; }
  const d=DUTY[code]; if(!d||d[0]==null) return '';
  const gen=d[0], saarc=(d[1]==null?gen:d[1]);
  const CIF=1000, V=0.13, landed=r=>CIF*(1+r/100)*(1+V);
  const lg=landed(gen), ls=landed(saarc), pref=saarc<gen;
  const save=Math.round(lg-ls), savePct=Math.round((lg-ls)/lg*100);
  const dl=r=>r===0?'Free':r+'%';
  let verdict;
  if(pref) verdict=`<div class="outcome" style="margin-top:var(--s3)"><span style="font-size:1.3rem">🇳🇵</span><div>Sourcing from <b>India or another SAARC country</b> lands this <b style="color:var(--free)">${fmtUSD(save)} cheaper per $1,000</b> (${savePct}% lower) than from China or the rest of the world — that gap is the SAFTA duty preference.</div></div>`;
  else if(gen===0) verdict=`<div class="outcome" style="margin-top:var(--s3)">${ic(I.info)}<div>This code is <b style="color:var(--free)">duty-free</b> into Nepal whatever the origin — you pay only the 13% VAT.</div></div>`;
  else verdict=`<div class="outcome" style="margin-top:var(--s3)">${ic(I.info)}<div>Nepal charges the same <b>${dl(gen)}</b> customs duty on this code regardless of origin — there's no SAARC/SAFTA preference to capture here.</div></div>`;
  return `<h3 class="h">Import into Nepal — landed cost by origin</h3>
    <p class="fine" style="margin:0 0 10px">On a <b style="color:var(--fg)">$1,000</b> shipment (CIF value), Nepal customs duty + 13% VAT comes to:</p>
    <table class="bk"><tbody>
      <tr><td>From India / a SAARC member <span class="fine">· ${dl(saarc)} duty (SAFTA)</span></td><td>${fmtUSD(ls)}</td></tr>
      <tr><td>From China / rest of world <span class="fine">· ${dl(gen)} duty (general)</span></td><td>${fmtUSD(lg)}</td></tr>
    </tbody></table>
    ${verdict}
    <p class="fine" style="margin-top:10px">Customs duty and 13% VAT only — excise duty, vehicle taxes and any product-specific levies are <b>not</b> included. <a href="https://customsnepal.com/?q=${code}" target="_blank" rel="noopener">Run the full Nepal calculator ↗</a> for the exact all-in figure.</p>`;
}
function isoMeta(iso){ const c=TRADE.countries.find(x=>x.iso===iso); return c?[c.name,c.flag]:[iso,'']; }
const isoName=iso=>isoMeta(iso)[0];
function nepalProd(code){
  const z=NEP&&NEP[code]; if(!z||!(z.im||z.ex)) return '';
  const p=PROD&&PROD[code]; const parts=[];
  if(z.im){ const src=(z.ims||[]).map(x=>esc(isoName(x[0]))).slice(0,3).join(', ');
    let pr='';
    if(z.iu&&p&&p.u){ const d=Math.round((z.iu/p.u-1)*100);
      pr=` at <b>$${z.iu}/kg</b> — ${d>8?`<b style="color:var(--hi)">${d}% above</b>`:d<-8?`<b style="color:var(--free)">${Math.abs(d)}% below</b>`:'about'} the world average ($${p.u}/kg)`; }
    parts.push(`imports <b>${money(z.im*1e6)}</b>${src?` (mainly from ${src})`:''}${pr}`); }
  if(z.ex){ const dst=(z.exs||[]).map(x=>esc(isoName(x[0]))).slice(0,3).join(', '); parts.push(`exports <b>${money(z.ex*1e6)}</b>${dst?` (to ${dst})`:''}`); }
  return `<div class="outcome" style="margin-top:var(--s4)"><span style="font-size:1.3rem">🇳🇵</span><div><b>Nepal's trade in this product (2024):</b> ${parts.join('; ')}. <a href="https://customsnepal.com/?q=${code}" target="_blank" rel="noopener">Nepal duty &amp; taxes ↗</a></div></div>`;
}
function prodBlock(code){
  if(PROD===null||NEP===null){ Promise.all([loadProd(),loadNep()]).then(()=>{ if(curHS===code) hsDetail(code,true); }); return '<p class="fine" style="margin-top:var(--s4)">Loading global trade for this product…</p>'; }
  const p=PROD[code]; if(!p||!(p.x&&p.x.length)) return nepalProd(code);
  const mk=a=>a.map(([iso,v])=>{const m=isoMeta(iso);return [iso,m[0],m[1],v*1e6];});
  const ex=mk(p.x), im=mk(p.m||[]);
  const price=p.u?` World average price: <b style="color:var(--fg)">$${p.u}/kg</b>.`:'';
  return `<h3 class="h">Who trades this worldwide</h3>
    <p class="fine" style="margin:0 0 10px">World trade in HS ${fmtCode(code)} was <b style="color:var(--fg)">${money(p.w*1e6)}</b> in 2024.${price} Leading exporters and importers:</p>
    <p class="fine" style="margin:0 0 6px"><b style="color:var(--exp)">Top exporters</b></p>${leaderboard(ex,'var(--exp)')}
    ${im.length?`<p class="fine" style="margin:14px 0 6px"><b style="color:var(--imp)">Top importers</b></p>${leaderboard(im,'var(--imp)')}`:''}
    ${nepalProd(code)}
    <div class="src"><div class="src-h">${ic(I.shield)}<span>Source</span><span style="margin-left:auto;font-weight:600;color:var(--muted)">2024</span></div>
      <p><b>BACI</b> (CEPII) — bilateral trade at HS 6-digit, reconciled from <b>UN Comtrade</b> across ~200 countries; unit values = value ÷ quantity. Current US$.</p></div>`;
}
let HS=null, TRADE=null, SUBS=[], HEADINGS={}, CHByNum={}, SECByRoman={};
async function boot(){
  try{
    const j=u=>fetch(u).then(r=>{if(!r.ok)throw 0;return r.json();});
    // Start the lazy per-product files in parallel, and wait for them before the first render, so the SPA doesn't
    // replace the server-rendered page with a "Loading…" placeholder (no flash, no layout shift).
    const p0=location.pathname.slice(BASE.length)||'/', extra=[];
    if(p0.indexOf('/hs/code/')===0) extra.push(loadProd(),loadNep(),loadDuty());
    else if(p0.indexOf('/nepal')===0) extra.push(loadNep(),loadProd());
    [HS,TRADE]=await Promise.all([j(BASE+'/data/hs.json'),j(BASE+'/data/trade.json')]);
    await Promise.all(extra);
  }catch(e){ app.innerHTML='<div class="empty"><b>Couldn\'t load data.</b><p>Please refresh.</p></div>'; return; }
  SUBS=HS.subs; HEADINGS=HS.headings;
  HS.chapters.forEach(c=>CHByNum[c[0]]=c);
  HS.sections.forEach(s=>SECByRoman[s[0]]=s);
  window.addEventListener('popstate',route); route();
}
function nav(path){ history.pushState(null,'',BASE+path); route(); window.scrollTo(0,0); }
document.addEventListener('click',e=>{ if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey) return;
  const a=e.target.closest('a[data-nav]'); if(!a) return; let h=a.getAttribute('href')||''; if(!h.startsWith('/')) return;
  // Country profiles are full static pages on the subdomain (deep partner/product data the SPA does not hold): load them normally.
  if(!BASE&&(h==='/'||/^\/trade\/[a-z]{3}$/i.test(h))) return;      // the home page and country profiles are full static pages
  e.preventDefault(); if(BASE&&h.indexOf(BASE)===0) h=h.slice(BASE.length)||'/'; nav(h); });

const MAIN_GUIDES=(META&&META.MAIN_GUIDES)||[];   // export guides that live on customsnepal.com/export
function setNav(k){ document.querySelectorAll('details.gnm[data-k]').forEach(d=>d.classList.toggle('cur',d.dataset.k===k)); }

/* ---------------- Page titles — mirrored 1:1 in scripts/world_prerender.py (keep in sync) ---------------- */
const clip=(s,n)=>{ s=String(s); if(s.length<=n) return s; const c=s.slice(0,n), i=c.lastIndexOf(' '); return (i>n*0.6?c.slice(0,i):c).replace(/[;,:\s]+$/,'')+'…'; };
const PT={
  home:()=>'World HS Codes & Global Trade Data — Customs Nepal',
  hs:()=>`World HS Code Finder — Search ${SUBS.length.toLocaleString('en-US')} HS 2022 Codes`,
  chapter:(ch,name)=>`HS Chapter ${ch}: ${clip(name,60)} — HS Codes List`,
  code:(code,desc)=>{ const b=`HS Code ${code} (${fmtCode(code)}) — ${clip(desc,48)}`; return b.length<=58?b+(PROD&&PROD[code]&&PROD[code].x&&PROD[code].x.length?' — World Trade & Prices':' — HS 2022 Code'):b; },
  trade:()=>`Global Trade Data — World Rankings & ${TRADE.countries.length} Country Profiles`,
  country:c=>`${c.name} Trade Profile${c.expYear?' '+c.expYear:''} — Exports, Imports${c.deep?', Partners & Products':' & Trade Balance'}`,
  group:label=>`Global Trade in ${label} — Top Exporters & Importers`,
  nepal:()=>'Nepal in World Trade — Imports, Exports & Opportunities (2024)',
  nepEx:()=>'Nepal Export Explorer — What Nepal Exports & Where (2024)',
  nepMkt:name=>`Nepal's Exports to ${name} — Products & Values (2024)`,
  guide:g=>`${g.h1} — Trade Data & Export Steps`
};
// Every public URL is prerendered (scripts/world_prerender.py) with its own <head>. On the first route we keep that
// server-rendered head (title/description/canonical/JSON-LD) instead of rewriting it; later client-side navigations update it.
const PRE=(document.querySelector('meta[name="cn-route"]')||{}).content||null;
let lockHead=false, firstRoute=true;
function setTitle(t){ if(!lockHead) document.title=t; }

/* ---------------- SEO + analytics (per-route meta, canonical, JSON-LD, GA4) ---------------- */
const CANON='https://world.customsnepal.com';
function setMeta(attr,key,val){ let el=document.head.querySelector(`meta[${attr}="${key}"]`); if(!el){ el=document.createElement('meta'); el.setAttribute(attr,key); document.head.appendChild(el); } el.setAttribute('content',val||''); }
function setLink(rel,href){ let el=document.head.querySelector(`link[rel="${rel}"]`); if(!el){ el=document.createElement('link'); el.setAttribute('rel',rel); document.head.appendChild(el); } el.setAttribute('href',href); }
function seoDesc(p){ let m;
  if(p==='/'||p==='') return 'Search 5,613 international HS codes and explore the import/export trade of 207 economies — world prices, top exporters and importers, and Nepal\'s landed cost by origin.';
  if(p==='/hs') return 'Search the full international Harmonized System — '+(SUBS?SUBS.length.toLocaleString():'5,613')+' six-digit codes'+(HS?' across '+HS.chapters.length+' chapters ('+HS.edition+')':'')+' — and see how Nepal taxes each one.';
  if(p==='/nepal') return 'Nepal in world trade: $10.3B imports, $1.2B exports and a $9.1B deficit (2024) — where Nepal overpays versus the world price, and its biggest export openings.';
  if(p==='/nepal/exports') return 'What Nepal exports to the world — by destination country and by product, with world-price benchmarks. Total merchandise exports $1.24B (2024).';
  if((m=p.match(/^\/nepal\/exports\/guide\/([a-z-]+)$/))){ const g=EXGUIDES[m[1]]; return g?g.sub:'How to export this product from Nepal, with the latest trade data.'; }
  if((m=p.match(/^\/nepal\/exports\/([a-z]{3})$/i))){ const iso=m[1].toUpperCase(); const c=TRADE&&TRADE.countries.find(x=>x.iso===iso); return 'Nepal\'s exports to '+(c?c.name:iso)+' (2024) — every product Nepal ships there, with values and world-price benchmarks.'; }
  if(p==='/trade') return 'Global merchandise trade: world rankings, every economy\'s exports and imports, regional shares and trade by product group.';
  if((m=p.match(/^\/hs\/chapter\/(\d{2})$/))){ const c=CHByNum&&CHByNum[m[1]]; return c?('HS Chapter '+m[1]+' — '+c[1]+'. Browse every six-digit code in this chapter and how Nepal taxes them.'):'HS chapter — six-digit codes and Nepal duty.'; }
  if((m=p.match(/^\/hs\/code\/(\d{6})$/))){ const s=SUBS&&SUBS.find(x=>x[0]===m[1]); const pr=m[1].slice(0,4)+'.'+m[1].slice(4); return s?('HS code '+pr+' — '+s[1]+'. World trade, top exporters and importers, world price per kg, and Nepal import duty by origin.'):'HS code '+pr+' — world trade and Nepal import duty.'; }
  if((m=p.match(/^\/trade\/([a-z]{3})$/i))){ const iso=m[1].toUpperCase(); const c=TRADE&&TRADE.countries.find(x=>x.iso===iso); return c?(c.name+' trade profile: exports, imports, top partners and product mix, with its world rank.'):'Country trade profile — exports, imports and partners.'; }
  if(p.indexOf('/trade/product/')===0) return 'Global trade in this product group — the world\'s top exporting and importing economies.';
  return 'International HS codes and global trade data from Customs Nepal.';
}
function setBreadcrumb(p){ const B=CANON, cr=[['Home','/']]; let m;
  if(p==='/hs') cr.push(['HS Codes','/hs']);
  else if((m=p.match(/^\/hs\/chapter\/(\d{2})$/))){ cr.push(['HS Codes','/hs']); const c=CHByNum&&CHByNum[m[1]]; cr.push(['Chapter '+m[1]+(c?' — '+c[1]:''),'/hs/chapter/'+m[1]]); }
  else if((m=p.match(/^\/hs\/code\/(\d{6})$/))){ cr.push(['HS Codes','/hs']); const ch=m[1].slice(0,2),c=CHByNum&&CHByNum[ch]; cr.push(['Chapter '+ch+(c?' — '+c[1]:''),'/hs/chapter/'+ch]); cr.push([m[1].slice(0,4)+'.'+m[1].slice(4),'/hs/code/'+m[1]]); }
  else if(p==='/trade') cr.push(['Trade','/trade']);
  else if(p==='/nepal/exports'){ cr.push(['Trade','/trade']); cr.push(['Nepal','/nepal']); cr.push(['Exports','/nepal/exports']); }
  else if((m=p.match(/^\/nepal\/exports\/guide\/([a-z-]+)$/))){ cr.push(['Trade','/trade']); cr.push(['Nepal','/nepal']); cr.push(['Exports','/nepal/exports']); const g=EXGUIDES[m[1]]; cr.push([g?g.name:m[1],'/nepal/exports/guide/'+m[1]]); }
  else if((m=p.match(/^\/nepal\/exports\/([a-z]{3})$/i))){ cr.push(['Trade','/trade']); cr.push(['Nepal','/nepal']); cr.push(['Exports','/nepal/exports']); const iso=m[1].toUpperCase(),c=TRADE&&TRADE.countries.find(x=>x.iso===iso); cr.push([(c?c.name:iso),'/nepal/exports/'+m[1].toLowerCase()]); }
  else if(p==='/nepal'){ cr.push(['Trade','/trade']); cr.push(['Nepal','/nepal']); }
  else if((m=p.match(/^\/trade\/product\/([a-z0-9-]+)$/))){ cr.push(['Trade','/trade']); cr.push(['Product group','/trade/product/'+m[1]]); }
  else if((m=p.match(/^\/trade\/([a-z]{3})$/i))){ cr.push(['Trade','/trade']); const iso=m[1].toUpperCase(),c=TRADE&&TRADE.countries.find(x=>x.iso===iso); cr.push([c?c.name:iso,'/trade/'+m[1].toLowerCase()]); }
  const ld={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':cr.map((x,i)=>({'@type':'ListItem','position':i+1,'name':x[0],'item':B+(x[1]==='/'?'/':x[1])}))};
  let el=document.getElementById('bc-ld'); if(!el){ el=document.createElement('script'); el.type='application/ld+json'; el.id='bc-ld'; document.head.appendChild(el); } el.textContent=JSON.stringify(ld);
}
function seoSync(p){ const url=CANON+(p==='/'||p===''?'/':p); setLink('canonical',url); setMeta('property','og:url',url);
  const t=document.title; setMeta('property','og:title',t); setMeta('name','twitter:title',t);
  const d=seoDesc(p); setMeta('name','description',d); setMeta('property','og:description',d); setMeta('name','twitter:description',d);
  try{ setBreadcrumb(p); }catch(e){} }
function pageview(p){ try{ if(window.gtag) gtag('event','page_view',{page_path:p,page_location:CANON+(p==='/'||p===''?'/':p),page_title:document.title}); }catch(e){} }
function track(n,params){ try{ if(window.gtag) gtag('event',n,params||{}); }catch(e){} }

function route(){
  let p=decodeURIComponent(location.pathname);
  if(BASE&&p.indexOf(BASE)===0)p=p.slice(BASE.length)||'/';
  lockHead=firstRoute&&PRE!==null&&PRE===p; firstRoute=false;
  let m;
  if(p.indexOf('/hs')===0){ loadProd(); loadNep(); loadDuty(); }
  if(p.indexOf('/nepal')===0){ loadNep(); loadProd(); }
  if((p==='/'||p==='')&&!BASE){ location.reload(); return; }      // the home page is a full static page
  if(p==='/'||p===''){ setNav(''); home(); }
  else if(p==='/nepal/exports'){ nepExportsHome(); }
  else if((m=p.match(/^\/nepal\/exports\/guide\/([a-z-]+)$/))){ nepExportGuide(m[1]); }
  else if((m=p.match(/^\/nepal\/exports\/([a-z]{3})$/i))){ nepExportMarket(m[1].toUpperCase()); }
  else if(p==='/nepal'){ setNav('exports'); nepalView(); }
  else if(p==='/hs'){ setNav('hs'); hsHome(); }
  else if((m=p.match(/^\/hs\/chapter\/(\d{2})$/))){ setNav('hs'); hsChapter(m[1]); }
  else if((m=p.match(/^\/hs\/code\/(\d{6})$/))){ setNav('hs'); hsDetail(m[1]); }
  else if(p==='/trade'){ setNav('trade'); tradeHome(); }
  else if((m=p.match(/^\/trade\/product\/([a-z0-9-]+)$/))){ setNav('trade'); productView(m[1]); }
  else if((m=p.match(/^\/trade\/([a-z]{3})$/i))){ setNav('trade'); country(m[1].toUpperCase()); }
  else { setNav(''); home(); p='/'; }
  try{ if(!lockHead) seoSync(p); pageview(p); }catch(e){}
}

/* ---------------- HOME ---------------- */
function home(){
  setTitle(PT.home());
  app.innerHTML=`
  <section class="hero"><div class="wrap">
    <h1>The world's HS codes and trade, in one place.</h1>
    <p>Search the international Harmonized System — the classification behind every customs tariff on earth — and explore the import/export profiles of the largest economies.</p>
    <div class="chips"><span>${SUBS.length.toLocaleString()} six-digit HS codes</span><span>${HS.chapters.length} chapters</span><span>${TRADE.countries.length} economies</span><span>Official sources</span></div>
  </div></section>
  <main><div class="wrap">
    <div class="grid2">
      <a class="bigcard" href="${BASE}/hs" data-nav><div class="ic">${ic(I.box)}</div><h3>World HS Code Finder</h3><p>Look up any product's 6-digit Harmonized System code and see how Nepal taxes it. The same code works in 200+ countries.</p><span class="go">Find a code ${ic(I.right)}</span></a>
      <a class="bigcard" href="${BASE}/trade" data-nav><div class="ic">${ic(I.globe)}</div><h3>Global Trade Data</h3><p>World rankings and a trade profile for every one of ${TRADE.world.count} economies — exports, imports, partners and product mix.</p><span class="go">Explore trade ${ic(I.right)}</span></a>
    </div>
    <div class="statrow">
      <div class="s"><b>${money(TRADE.world.totalExp)}</b><span>World merchandise trade (${TRADE.world.year})</span></div>
      <div class="s"><b>${TRADE.world.count}</b><span>Economies profiled</span></div>
      <div class="s"><b>${SUBS.length.toLocaleString()}</b><span>HS codes linked to trade</span></div>
    </div>
  </div></main>`;
}

/* ---------------- PILLAR 1: HS ---------------- */
function hsHome(){
  setTitle(PT.hs());
  app.innerHTML=`<main><div class="wrap">
    <div class="ph"><h1 class="h2">World HS Code Finder</h1><p>Search ${SUBS.length.toLocaleString()} international six-digit codes by product or number, or browse by section. ${HS.edition} nomenclature.</p></div>
    <div class="sbox">${ic(I.search)}<input id="q" type="search" placeholder="e.g. coffee, lithium battery, 8471, 0901…" autocomplete="off"></div>
    <div id="res"></div>
    <div id="browse"><h3 class="h">Browse by section</h3><div class="secs">${HS.sections.map(s=>{
      const n=SUBS.filter(x=>{const ch=+x[0].slice(0,2);return ch>=s[2]&&ch<=s[3];}).length;
      return `<a class="sec" href="${BASE}/hs/chapter/${String(s[2]).padStart(2,'0')}" data-nav><span class="n">Section ${s[0]}</span><span class="t">${esc(s[1])}</span><span class="c">Ch ${s[2]}–${s[3]} · ${n} codes</span></a>`;}).join('')}</div>
    <h3 class="h">All ${HS.chapters.length} chapters</h3>${HS.chapters.map(c=>`<a class="row" href="${BASE}/hs/chapter/${c[0]}" data-nav><span class="code">Ch ${c[0]}</span><span class="d">${esc(c[1])}</span><span class="end">${ic(I.right)}</span></a>`).join('')}</div>`;
  const q=$('#q'); q.focus(); q.addEventListener('input',()=>runSearch(q.value));
  try{ const uq=new URLSearchParams(location.search).get('q'); if(uq&&uq.trim()){ q.value=uq.trim(); runSearch(q.value); } }catch(e){}
}
function runSearch(qv){
  const res=$('#res'), br=$('#browse'); qv=qv.trim();
  if(qv.length<2){ res.innerHTML=''; br.style.display=''; return; }
  br.style.display='none';
  const digits=qv.replace(/[^\d]/g,'');
  let hits=[];
  if(digits.length>=2){ hits=SUBS.filter(s=>s[0].startsWith(digits)).slice(0,60); }
  else{ const words=qv.toLowerCase().split(/\s+/).filter(w=>w.length>1);
    const scored=[];
    for(const s of SUBS){ const d=s[1].toLowerCase(); let sc=0; for(const w of words){ const i=d.indexOf(w); if(i<0){sc=-1;break;} sc+=(i===0?3:1);} if(sc>0)scored.push([sc,s]); }
    scored.sort((a,b)=>b[0]-a[0]); hits=scored.slice(0,60).map(x=>x[1]); }
  if(!hits.length){ res.innerHTML='<div class="empty">No codes match. Try a simpler word or an HS number.</div>'; return; }
  res.innerHTML=hits.map(s=>rowHTML(s)).join('');
}
function fmtCode(c){ return c.slice(0,4)+'.'+c.slice(4,6); }
function dutyChip(s){ const np=s[3]; if(!np||np.g==null)return ''; const g=np.g; const txt=Array.isArray(g)?g[0]+'–'+g[1]+'%':(g===0?'Free':g+'%'); return `<span class="chip dutychip">NP ${txt}</span>`; }
function rowHTML(s){ return `<a class="row" href="${BASE}/hs/code/${s[0]}" data-nav><span class="code">${fmtCode(s[0])}</span><span class="d">${esc(s[1])}</span><span class="end">${dutyChip(s)} ${ic(I.right)}</span></a>`; }

function hsChapter(ch){
  const cn=CHByNum[ch]; if(!cn)return hsHome();
  const sec=SECByRoman[cn[2]];
  const rows=SUBS.filter(s=>s[0].startsWith(ch));
  const byHead={}; rows.forEach(s=>{(byHead[s[2]]=byHead[s[2]]||[]).push(s);});
  setTitle(PT.chapter(ch,cn[1]));
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/hs" data-nav>${ic(I.left)}HS finder</a>
    <div class="ph"><p style="margin:0;color:var(--muted);font-size:.85rem">Section ${cn[2]} · Chapter ${ch}</p><h1 class="h2">${esc(cn[1])}</h1><p>${rows.length} six-digit codes${sec?' · '+esc(sec[1]):''}.</p></div>
    ${Object.keys(byHead).sort().map(h=>`<h3 class="h">${h.slice(0,2)}.${h.slice(2)} — ${esc(HEADINGS[h]||'')}</h3>${byHead[h].map(s=>rowHTML(s)).join('')}`).join('')}
  </div></main>`;
}

function hsDetail(code){
  curHS=code;
  track('view_hs_code',{hs_code:code});
  const s=SUBS.find(x=>x[0]===code); if(!s)return hsHome();
  const ch=code.slice(0,2), head=code.slice(0,4), cn=CHByNum[ch]||[ch,'',''], sec=SECByRoman[cn[2]]||['','',''];
  const np=s[3];
  setTitle(PT.code(code,s[1]));
  let nepal='';
  if(np&&np.g!=null){ const g=np.g; const txt=Array.isArray(g)?`${g[0]}–${g[1]}%`:(g===0?'Free':g+'%');
    nepal=`<div class="outcome">${ic(I.info)}<div>Nepal applies a general customs duty of <b>${txt}</b> on this code (${np.n} national line${np.n>1?'s':''}), plus excise/VAT where applicable. <a href="https://customsnepal.com/?q=${code}" target="_blank" rel="noopener">See full Nepal duty &amp; taxes ↗</a></div></div>`;
  }else if(np){ nepal=`<div class="outcome">${ic(I.info)}<div>Nepal lists this code (${np.n} line${np.n>1?'s':''}). <a href="https://customsnepal.com/?q=${code}" target="_blank" rel="noopener">See Nepal duty &amp; taxes ↗</a></div></div>`; }
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/hs/chapter/${ch}" data-nav>${ic(I.left)}Chapter ${ch}</a>
    <h1 class="dcode">${fmtCode(code)}</h1><p class="dtitle">${esc(s[1])}</p>
    <p class="crumb">Section ${cn[2]} · <b>${esc(sec[1])}</b></p>
    ${nepal}
    <table class="bk"><tbody>
      <tr><td>Six-digit HS code</td><td>${fmtCode(code)} <span class="fine">(${code})</span></td></tr>
      <tr><td>Heading</td><td>${head.slice(0,4)}</td></tr>
      <tr><td>Chapter</td><td>${ch} — ${esc(cn[1])}</td></tr>
      <tr><td>Section</td><td>${cn[2]}</td></tr>
    </tbody></table>
    <p class="crumb" style="margin-top:14px"><b>Heading ${head.slice(0,2)}.${head.slice(2)}:</b> ${esc(HEADINGS[head]||'')}</p>
    ${prodBlock(code)}
    ${landedBlock(code)}
    <div class="src"><div class="src-h">${ic(I.shield)}<span>International standard</span></div>
      <p>This is the global 6-digit Harmonized System code (${HS.edition}), identical across 200+ countries. Each country adds its own 8–10 digit extension and duty rates. <a href="https://www.wcoomd.org/en/topics/nomenclature/overview.aspx" target="_blank" rel="noopener">About the HS ↗</a></p></div>
    ${chapterGroup(ch)?`<a class="nepalcard" href="${BASE}/trade/product/${groupSlug(chapterGroup(ch)[0])}" data-nav><span class="fl">${ic(I.globe)}</span><span><b>Global trade in ${esc(chapterGroup(ch)[0])}</b> — see the world's top exporters &amp; importers ${ic(I.right)}</span></a>`:''}
    <h3 class="h">Other codes in heading ${head.slice(0,2)}.${head.slice(2)}</h3>
    ${SUBS.filter(x=>x[0].startsWith(head)).map(x=>`<a class="row" href="${BASE}/hs/code/${x[0]}" data-nav${x[0]===code?' aria-current="page"':''}><span class="code">${fmtCode(x[0])}</span><span class="d">${esc(x[1])}</span><span class="end">${dutyChip(x)} ${ic(I.right)}</span></a>`).join('')}
  </div></main>`;
}

/* ---------------- PILLAR 2: TRADE ---------------- */
let tFlow='exp';
function leaderboard(list,color){const mx=Math.max(...list.map(x=>x[3]),1);
  return `<div class="bars">${list.map((x,i)=>`<a class="lbrow" href="${BASE}/trade/${x[0].toLowerCase()}" data-nav><span class="rk">${i+1}</span><span class="lb">${x[2]} ${esc(x[1])}</span><span class="tr"><span class="fi" style="width:${Math.max(2,x[3]/mx*100)}%;background:${color}"></span></span><span class="vl">${money(x[3])}</span></a>`).join('')}</div>`;}
function countryRows(q){
  const ql=(q||'').toLowerCase().trim();
  const list=TRADE.countries.filter(c=>c.exp!=null&&(!ql||c.name.toLowerCase().includes(ql)));
  if(!list.length)return '<p class="fine">No economy matches.</p>';
  return list.map(c=>`<a class="row" href="${BASE}/trade/${c.iso.toLowerCase()}" data-nav><span class="code" style="color:var(--muted);min-width:30px;text-align:right">#${c.rankExp||'–'}</span><span class="d">${c.flag} ${esc(c.name)}</span><span class="end"><b class="ex">${money(c.exp)}</b> ${ic(I.right)}</span></a>`).join('');
}
function tradeHome(){
  const W=TRADE.world, np=TRADE.countries.find(c=>c.iso==='NPL');
  setTitle(PT.trade());
  renderT();
  function renderT(){
    const top=tFlow==='exp'?W.topExp:W.topImp, col=tFlow==='exp'?'var(--exp)':'var(--imp)';
    const rmax=Math.max(...W.regions.map(r=>r[1]),1);
    app.innerHTML=`<main><div class="wrap">
      <div class="ph"><h1 class="h2">Global trade</h1><p>World merchandise trade reached <b>${money(W.totalExp)}</b> in ${W.year}, across ${W.count} economies. Explore the rankings below, or open any country.</p></div>
      <div class="statrow" style="margin-top:0">
        <div class="s"><b class="ex">${money(W.totalExp)}</b><span>World exports (${W.year})</span></div>
        <div class="s"><b class="im">${money(W.totalImp)}</b><span>World imports (${W.year})</span></div>
        <div class="s"><b>${W.count}</b><span>Economies</span></div>
      </div>
      <div class="card" style="margin-top:var(--s4)"><b style="font-size:.9rem">World trade over time</b>${trendSVG(W.trend)}</div>
      ${np?`<a class="nepalcard" href="${BASE}/nepal" data-nav><span class="fl">${np.flag}</span><span><b>Nepal in the world</b> — real imports, exports &amp; sourcing opportunities by product ${ic(I.right)}</span></a>`:''}
      <a class="nepalcard" href="${BASE?CANON:''}/trade/region/south-asia"><span class="fl">🌏</span><span><b>South Asia</b> — the eight SAARC economies and what they trade with each other ${ic(I.right)}</span></a>
      <div class="sub2" style="margin-top:var(--s5)"><button class="${tFlow==='exp'?'on':''}" onclick="__tflow('exp')">Top exporters</button><button class="${tFlow==='imp'?'on':''}" onclick="__tflow('imp')">Top importers</button></div>
      ${leaderboard(top,col)}
      <h3 class="h">By region</h3>
      ${bars(W.regions.map(r=>[r[0],r[1]]),rmax,money,'var(--exp)')}
      <h3 class="h">Trade by product</h3>
      <p class="fine" style="margin:0 0 10px">Who leads world trade in each product family — and the HS codes behind it:</p>
      <div class="secs">${PGROUPS.map(x=>`<a class="sec" href="${BASE}/trade/product/${groupSlug(x[0])}" data-nav><span class="t">${esc(x[0])}</span><span class="c">HS ${x[1]}–${x[2]}</span></a>`).join('')}</div>
      <h3 class="h">All economies</h3>
      <div class="sbox">${ic(I.search)}<input id="cq" type="search" placeholder="Find a country…" autocomplete="off"></div>
      <div id="clist">${countryRows('')}</div>
      <h3 class="h">Freshest 2025 data — official national sources</h3>
      <p class="fine" style="margin:0 0 10px">The figures above are the World Bank's comparable cross-country series (to 2023). For the latest <b>2025</b> import/export data, each economy's own customs or statistics office is the authoritative source:</p>
      <div class="osrc">${Object.keys(OFFICIAL).filter(k=>k!=='NPL').map(k=>[k,TRADE.countries.find(c=>c.iso===k)]).filter(x=>x[1]).sort((a,b)=>(b[1].exp||0)-(a[1].exp||0)).slice(0,12).map(([k,c])=>`<a class="osrc-i" href="${OFFICIAL[k][1]}" target="_blank" rel="noopener">${c.flag} <span>${esc(OFFICIAL[k][0])}</span>${ic(I.right)}</a>`).join('')}<a class="osrc-i" href="${EUROSTAT[1]}" target="_blank" rel="noopener">🇪🇺 <span>${esc(EUROSTAT[0])}</span>${ic(I.right)}</a></div>
      <div class="src" style="margin-top:var(--s4)"><div class="src-h">${ic(I.shield)}<span>Official sources</span></div>
        <p>World and country totals from the <b>World Bank</b> (merchandise trade, current US$); partners and product mix from <b>World Bank WITS</b>, sourced from <b>UN Comtrade</b>. Rankings cover ${W.count} reporting economies.</p></div>
    </div></main>`;
    const cq=$('#cq'); if(cq)cq.addEventListener('input',()=>{$('#clist').innerHTML=countryRows(cq.value);});
  }
  window.__tflow=f=>{tFlow=f;renderT();window.scrollTo(0,0);};
}

function bars(items,max,fmt,color){ const c=color||'var(--accent)'; return `<div class="bars">${items.map(it=>{const v=it[it.length-1];return `<div class="barrow"><span class="lb">${esc(it[it.length-2])}</span><span class="tr"><span class="fi" style="width:${Math.max(2,v/max*100)}%;background:${c}"></span></span><span class="vl">${fmt(v)}</span></div>`;}).join('')}</div>`; }

function trendSVG(trend){
  const pts=trend.filter(r=>r[1]!=null||r[2]!=null); if(pts.length<2)return'';
  const W=600,H=150,pad=4; const xs=pts.map(r=>r[0]); const minY=xs[0],maxY=xs[xs.length-1];
  const vals=pts.flatMap(r=>[r[1],r[2]]).filter(v=>v!=null); const mx=Math.max(...vals)*1.05;
  const X=y=>pad+(y-minY)/(maxY-minY)*(W-2*pad); const Y=v=>H-pad-(v/mx)*(H-2*pad);
  const line=idx=>pts.filter(r=>r[idx]!=null).map((r,i)=>(i?'L':'M')+X(r[0]).toFixed(1)+' '+Y(r[idx]).toFixed(1)).join(' ');
  const area=idx=>{const p=pts.filter(r=>r[idx]!=null);if(!p.length)return'';return 'M'+X(p[0][0]).toFixed(1)+' '+H+' L'+p.map(r=>X(r[0]).toFixed(1)+' '+Y(r[idx]).toFixed(1)).join(' L')+' L'+X(p[p.length-1][0]).toFixed(1)+' '+H+' Z';};
  return `<svg class="trend" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Exports and imports trend">
    <path d="${area(1)}" fill="var(--exp)" opacity=".10"/><path d="${line(1)}" fill="none" stroke="var(--exp)" stroke-width="2.5"/>
    <path d="${line(2)}" fill="none" stroke="var(--imp)" stroke-width="2.5" stroke-dasharray="1"/>
  </svg>
  <div class="lgnd"><span><i style="background:var(--exp)"></i>Exports</span><span><i style="background:var(--imp)"></i>Imports</span><span style="color:var(--muted)">${minY}–${maxY}</span></div>`;
}

// Year-by-year table + nearby economies in the same region (mirrored in scripts/world_prerender.py: country_extras)
function countryExtras(c){
  const yrs=(c.trend||[]).filter(r=>r[1]!=null||r[2]!=null).slice(-6).reverse();
  const tbl=yrs.length?`<h3 class="h">Trade by year</h3><table class="bk"><tbody><tr><td><b>Year</b></td><td>Exports · Imports</td></tr>${yrs.map(r=>`<tr><td>${r[0]}</td><td><span class="ex">${money(r[1])}</span> · <span class="im">${money(r[2])}</span></td></tr>`).join('')}</tbody></table>`:'';
  const peers=c.region?TRADE.countries.filter(x=>x.iso!==c.iso&&x.region===c.region&&x.exp!=null).sort((a,b)=>Math.abs(a.exp-(c.exp||0))-Math.abs(b.exp-(c.exp||0))).slice(0,8):[];
  const pl=peers.length?`<h3 class="h">Other economies in ${esc(c.region)}</h3>${peers.map(x=>`<a class="row" href="${BASE}/trade/${x.iso.toLowerCase()}" data-nav><span class="d">${x.flag} ${esc(x.name)}</span><span class="end"><b class="ex">${money(x.exp)}</b> ${ic(I.right)}</span></a>`).join('')}`:'';
  return tbl+pl;
}
let cFlow='exp';
function country(iso){
  const c=TRADE.countries.find(x=>x.iso===iso); if(!c)return tradeHome();
  const W=TRADE.world, deep=!!c.deep, bal=(c.exp||0)-(c.imp||0);
  setTitle(PT.country(c));
  track('view_country',{country:iso});
  render();
  function render(){
    const parts=deep?(cFlow==='exp'?c.expPartners:c.impPartners):[];
    const prods=deep?(cFlow==='exp'?c.expProducts:c.impProducts):[];
    const fcol=cFlow==='exp'?'var(--exp)':'var(--imp)';
    const pmax=Math.max(...parts.map(p=>p[2]),1), rmax=Math.max(...prods.map(p=>p[1]),1);
    app.innerHTML=`<main><div class="wrap">
      <a class="back" href="${BASE}/trade" data-nav>${ic(I.left)}Global trade</a>
      <div class="ph"><h1 class="h2">${c.flag} ${esc(c.name)}</h1><p>${c.region?esc(c.region)+' · ':''}World rank <b>#${c.rankExp||'–'}</b> exporter, <b>#${c.rankImp||'–'}</b> importer, of ${W.count} economies.</p></div>
      <div class="statrow" style="margin-top:0">
        <div class="s"><b class="ex">${money(c.exp)}</b><span>Exports (${c.expYear})</span></div>
        <div class="s"><b class="im">${money(c.imp)}</b><span>Imports (${c.impYear})</span></div>
        <div class="s"><b style="color:${bal>=0?'var(--free)':'var(--hi)'}">${bal>=0?'+':'−'}${money(Math.abs(bal)).slice(1)}</b><span>Trade balance</span></div>
      </div>
      <div class="card" style="margin-top:var(--s4)"><b style="font-size:.9rem">Exports vs imports</b>${trendSVG(c.trend)}</div>
      ${deep?`
      <div class="sub2"><button class="${cFlow==='exp'?'on':''}" onclick="__flow('exp')">Exports</button><button class="${cFlow==='imp'?'on':''}" onclick="__flow('imp')">Imports</button></div>
      <h3 class="h">Top ${cFlow==='exp'?'export destinations':'import sources'} <small style="font-weight:600;color:var(--muted)">(${c.pYear})</small></h3>
      ${parts.length?bars(parts.map(p=>[p[1],p[2]]),pmax,money,fcol):'<p class="fine">No partner data.</p>'}
      <h3 class="h">${cFlow==='exp'?'What it exports':'What it imports'}</h3>
      ${prods.length?bars(prods.map(p=>[p[0],p[1]]),rmax,money,fcol):'<p class="fine">No product data.</p>'}`
      :`<div class="outcome" style="margin-top:var(--s4)">${ic(I.info)}<div>Partner and product breakdowns are live for the ~30 largest traders and Nepal, and rolling out to more economies. The totals and trend above are from the World Bank.</div></div>`}
      ${countryExtras(c)}
      <div class="src"><div class="src-h">${ic(I.shield)}<span>Official sources</span>${deep?`<span style="margin-left:auto;font-weight:600;color:var(--muted)">${c.pYear}</span>`:''}</div>
        <p>Trade totals from the <b>World Bank</b> (merchandise trade, current US$)${deep?'; partners and product mix from <b>World Bank WITS</b>, sourced from <b>UN Comtrade</b>':''}. <a href="https://wits.worldbank.org/CountryProfile/en/${c.iso}" target="_blank" rel="noopener">World Bank profile ↗</a></p>
        ${OFFICIAL[c.iso]?`<p style="margin-top:8px"><b style="color:var(--fg-2)">Freshest 2025 data →</b> <a href="${OFFICIAL[c.iso][1]}" target="_blank" rel="noopener">${esc(OFFICIAL[c.iso][0])} ↗</a>${c.region==='Europe & Central Asia'?` · <a href="${EUROSTAT[1]}" target="_blank" rel="noopener">Eurostat ↗</a>`:''}</p>`:(c.region==='Europe & Central Asia'?`<p style="margin-top:8px"><b style="color:var(--fg-2)">Freshest 2025 data →</b> <a href="${EUROSTAT[1]}" target="_blank" rel="noopener">${esc(EUROSTAT[0])} ↗</a></p>`:'')}</div>
      ${deep?'<p class="fine">Mirror-statistics note: a country&#39;s reported exports to a partner may differ from that partner&#39;s reported imports. Product groups follow HS chapter ranges.</p>':''}
    </div></main>`;
  }
  window.__flow=f=>{cFlow=f;render();window.scrollTo(0,0);};
}
let pFlow='exp';
function productView(slug){
  const g=PGROUPS.find(x=>groupSlug(x[0])===slug); if(!g)return tradeHome();
  const label=g[0], yr=(TRADE.countries.find(c=>c.deep)||{}).pYear;
  setTitle(PT.group(label));
  track('view_product_group',{group:slug});
  render();
  function render(){
    const lb=productTraders(label,pFlow).slice(0,15), col=pFlow==='exp'?'var(--exp)':'var(--imp)';
    app.innerHTML=`<main><div class="wrap">
      <a class="back" href="${BASE}/trade" data-nav>${ic(I.left)}Global trade</a>
      <div class="ph"><h1 class="h2">${esc(label)}</h1><p>Who trades this worldwide — HS chapters ${g[1]}–${g[2]}. Leading exporters and importers among the major economies${yr?' ('+yr+')':''}.</p></div>
      <div class="sub2"><button class="${pFlow==='exp'?'on':''}" onclick="__pflow('exp')">Top exporters</button><button class="${pFlow==='imp'?'on':''}" onclick="__pflow('imp')">Top importers</button></div>
      <h3 class="h">Leading ${pFlow==='exp'?'exporters':'importers'} of ${esc(label.toLowerCase())}</h3>
      ${lb.length?leaderboard(lb,col):'<p class="fine">No data for this group.</p>'}
      <a class="nepalcard" href="${BASE}/hs/chapter/${String(g[1]).padStart(2,'0')}" data-nav><span class="fl">${ic(I.box)}</span><span><b>Find the exact HS codes</b> — browse the ${SUBS.filter(s=>{const c=+s[0].slice(0,2);return c>=g[1]&&c<=g[2];}).length} six-digit codes in chapters ${g[1]}–${g[2]} ${ic(I.right)}</span></a>
      <h3 class="h">All product groups</h3>
      <div class="secs">${PGROUPS.map(x=>`<a class="sec" href="${BASE}/trade/product/${groupSlug(x[0])}" data-nav${groupSlug(x[0])===slug?' aria-current="page"':''}><span class="t">${esc(x[0])}</span><span class="c">HS ${x[1]}–${x[2]}</span></a>`).join('')}</div>
      <div class="src"><div class="src-h">${ic(I.shield)}<span>Official sources</span>${yr?`<span style="margin-left:auto;font-weight:600;color:var(--muted)">${yr}</span>`:''}</div>
        <p>Rankings computed from <b>World Bank WITS</b> product data (sourced from <b>UN Comtrade</b>) across the major trading economies — each country's merchandise ${pFlow==='exp'?'exports':'imports'} in this HS group. Smaller economies are not yet included, so treat it as "leading major-economy traders".</p></div>
    </div></main>`;
  }
  window.__pflow=f=>{pFlow=f;render();window.scrollTo(0,0);};
}
function hsDesc(code){ const s=SUBS.find(x=>x[0]===code); return s?s[1]:(HEADINGS[code.slice(0,4)]||code); }
function nepalView(){
  if(NEP===null||PROD===null){ Promise.all([loadNep(),loadProd()]).then(()=>{ if(location.pathname.indexOf('/nepal')>=0) nepalView(); }); app.innerHTML='<main><div class="wrap"><div class="empty" style="padding-top:70px">Loading Nepal trade…</div></div></main>'; return; }
  setTitle(PT.nepal());
  const T=NEP._t||{im:0,ex:0}, bal=T.ex-T.im;
  const row=(code,val,extra)=>`<a class="row" href="${BASE}/hs/code/${code}" data-nav><span class="code">${fmtCode(code)}</span><span class="d">${esc(hsDesc(code))}${extra?`<small style="display:block;color:var(--muted)">${extra}</small>`:''}</span><span class="end"><b>${money(val*1e6)}</b> ${ic(I.right)}</span></a>`;
  const over=[];
  (NEP._im||[]).forEach(([code,val])=>{ const z=NEP[code],p=PROD[code]; if(z&&z.iu&&p&&p.u&&z.iu>p.u*1.2&&val>=1) over.push([code,val,Math.round((z.iu/p.u-1)*100),z.iu,p.u]); });
  over.sort((a,b)=>b[1]*b[2]-a[1]*a[2]);
  const open=[];
  (NEP._ex||[]).forEach(([code,val])=>{ const p=PROD[code]; if(p&&p.w){ const sh=val/p.w*100; if(sh<20) open.push([code,val,p.w,sh]); } });
  open.sort((a,b)=>b[2]-a[2]);
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/trade" data-nav>${ic(I.left)}Global trade</a>
    <div class="ph"><h1 class="h2">🇳🇵 Nepal in world trade</h1><p>Nepal's real merchandise trade by product (BACI 2024) — and where the data points to openings.</p></div>
    <div class="statrow" style="margin-top:0">
      <div class="s"><b class="im">${money(T.im*1e6)}</b><span>Imports (2024)</span></div>
      <div class="s"><b class="ex">${money(T.ex*1e6)}</b><span>Exports (2024)</span></div>
      <div class="s"><b style="color:var(--hi)">−${money(Math.abs(bal)*1e6).slice(1)}</b><span>Trade deficit</span></div>
    </div>
    <a class="nepalcard" href="${BASE}/nepal/exports" data-nav><span class="fl">📦</span><span><b>Nepal Export Explorer</b> — what Nepal sells to each country, by product, with world-price benchmarks and export guides ${ic(I.right)}</span></a>
    <h3 class="h">Sourcing watch — imports Nepal may overpay for</h3>
    <p class="fine" style="margin:0 0 8px">Products where Nepal's import price sits well above the world average — worth checking a cheaper origin.</p>
    ${over.length?over.slice(0,12).map(([code,val,d,iu,u])=>row(code,val,`Nepal $${iu}/kg vs $${u}/kg world · ${d}% higher`)).join(''):'<p class="fine">—</p>'}
    <h3 class="h">Export openings — big world demand, small Nepal share</h3>
    <p class="fine" style="margin:0 0 8px">Products Nepal already exports, where world import demand dwarfs Nepal's current sales.</p>
    ${open.length?open.slice(0,12).map(([code,val,w,sh])=>row(code,val,`World imports ${money(w*1e6)} · Nepal ${sh<1?'<1':Math.round(sh)}%`)).join(''):'<p class="fine">—</p>'}
    <h3 class="h">Nepal's top imports</h3>${(NEP._im||[]).slice(0,10).map(([code,val])=>row(code,val)).join('')}
    <h3 class="h">Nepal's top exports</h3>${(NEP._ex||[]).slice(0,10).map(([code,val])=>row(code,val)).join('')}
    <div class="src"><div class="src-h">${ic(I.shield)}<span>Source</span><span style="margin-left:auto;color:var(--muted);font-weight:600">2024</span></div>
      <p>Nepal's bilateral trade from <b>BACI</b> (CEPII, reconciled from UN Comtrade). "Overpay" compares Nepal's import unit value to the world average — a signal to investigate, not proof (grade/quality and freight differ). For duty on any line, see <a href="https://customsnepal.com/" target="_blank" rel="noopener">customsnepal.com ↗</a>.</p></div>
  </div></main>`;
}
/* ---------------- NEPAL EXPORT EXPLORER ---------------- */
let NEPEXP=null;
function nepExports(){
  if(NEPEXP) return NEPEXP;
  const cc={}, cp={};
  for(const k in NEP){ if(k[0]==='_'||!NEP[k].exs) continue;
    for(const d of NEP[k].exs){ const iso=d[0], val=d[1]; if(!(val>0)) continue; cc[iso]=(cc[iso]||0)+val; (cp[iso]=cp[iso]||[]).push([k,val]); } }
  Object.keys(cp).forEach(i=>cp[i].sort((a,b)=>b[1]-a[1]));
  NEPEXP={cc,cp, order:Object.keys(cc).sort((a,b)=>cc[b]-cc[a]),
    tot:Object.keys(cc).reduce((s,i)=>s+cc[i],0),
    nprod:Object.keys(NEP).filter(k=>k[0]!=='_'&&NEP[k].ex>0).length};
  return NEPEXP;
}
function exReady(then){ if(NEP===null||PROD===null){ Promise.all([loadNep(),loadProd()]).then(()=>{ if(location.pathname.indexOf('/nepal/exports')>=0) then(); }); app.innerHTML='<main><div class="wrap"><div class="empty" style="padding-top:70px">Loading Nepal export data…</div></div></main>'; return false; } return true; }
function exRow(code,val,extra){ return `<a class="row" href="${BASE}/hs/code/${code}" data-nav><span class="code">${fmtCode(code)}</span><span class="d">${esc(hsDesc(code))}${extra?`<small style="display:block;color:var(--muted)">${extra}</small>`:''}</span><span class="end"><b class="ex">${money(val*1e6)}</b> ${ic(I.right)}</span></a>`; }
function exsText(code){ const z=NEP[code]; if(!z||!z.exs) return ''; const d=z.exs.filter(x=>x[1]>0).slice(0,3).map(x=>esc(isoName(x[0]))); return d.length?('→ '+d.join(', ')):''; }
function exDestRows(dests,X){ const mx=Math.max(...dests.map(i=>X.cc[i]),1);
  return `<div class="bars">${dests.map((i,n)=>{const m=isoMeta(i);return `<a class="lbrow" href="${BASE}/nepal/exports/${i.toLowerCase()}" data-nav><span class="rk">${n+1}</span><span class="lb">${m[1]} ${esc(m[0])}</span><span class="tr"><span class="fi" style="width:${Math.max(2,X.cc[i]/mx*100)}%;background:var(--exp)"></span></span><span class="vl">${money(X.cc[i]*1e6)}</span></a>`;}).join('')}</div>`; }


function nepExportsHome(){
  if(!exReady(nepExportsHome)) return;
  setNav('exports');
  setTitle(PT.nepEx());
  const X=nepExports(), T=NEP._t||{ex:0};
  const dests=X.order.filter(i=>X.cc[i]>0);
  const indiaShare=Math.round((X.cc['IND']||0)/(T.ex||X.tot)*100);
  const open=[]; (NEP._ex||[]).forEach(d=>{ const code=d[0],val=d[1],p=PROD[code]; if(p&&p.w){ const sh=val/p.w*100; if(sh<20) open.push([code,val,p.w,sh]); } }); open.sort((a,b)=>b[2]-a[2]);
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/nepal" data-nav>${ic(I.left)}Nepal in world trade</a>
    <div class="ph"><h1 class="h2">🇳🇵 Nepal Export Explorer</h1><p>What Nepal sells to the world — by destination and by product, with world-price benchmarks (BACI 2024).</p></div>
    <div class="statrow" style="margin-top:0">
      <div class="s"><b class="ex">${money(T.ex*1e6)}</b><span>Total exports (2024)</span></div>
      <div class="s"><b>${dests.length}</b><span>Destination markets</span></div>
      <div class="s"><b>${X.nprod}</b><span>Products exported</span></div>
    </div>
    <div class="outcome" style="margin-top:var(--s4)">${ic(I.info)}<div><b>${indiaShare}% of Nepal's exports go to India</b> — and a large part of that is refined soybean &amp; palm oil re-exported after processing (a duty-driven flow, not domestic production). Nepal's real manufactured and agri exports — carpets, cardamom, pashmina, tea, felt — are spread across the US, the EU and beyond.</div></div>
    <h3 class="h">Explore by market</h3>
    <p class="fine" style="margin:0 0 8px">Nepal's biggest export destinations — open one to see every product Nepal ships there.</p>
    ${exDestRows(dests.slice(0,15),X)}
    <h3 class="h">Explore by product</h3>
    <p class="fine" style="margin:0 0 8px">Nepal's top exports — open one for who buys it worldwide and the price Nepal gets.</p>
    ${(NEP._ex||[]).filter(d=>d[1]>0).slice(0,15).map(d=>exRow(d[0],d[1],exsText(d[0]))).join('')}
    <h3 class="h">Export guides</h3>
    <div class="secs">${Object.keys(EXGUIDES).map(s=>`<a class="sec" href="${MAIN_GUIDES.indexOf(s)>=0?'https://www.customsnepal.com/export/'+s:BASE+'/nepal/exports/guide/'+s}"${MAIN_GUIDES.indexOf(s)>=0?'':' data-nav'}><span class="t">${EXGUIDES[s].fl} ${esc(EXGUIDES[s].name)}</span><span class="c">${MAIN_GUIDES.indexOf(s)>=0?'How to export, on customsnepal.com':'Trade data + how to export'}</span></a>`).join('')}</div>
    <h3 class="h">Export openings — big world demand, small Nepal share</h3>
    <p class="fine" style="margin:0 0 8px">Products Nepal already exports, where world import demand dwarfs Nepal's current sales.</p>
    ${open.length?open.slice(0,10).map(o=>exRow(o[0],o[1],`World imports ${money(o[2]*1e6)} · Nepal ${o[3]<1?'<1':Math.round(o[3])}%`)).join(''):'<p class="fine">—</p>'}
    <div class="src"><div class="src-h">${ic(I.shield)}<span>Source</span><span style="margin-left:auto;color:var(--muted);font-weight:600">2024</span></div>
      <p>Nepal's exports by product and partner from <b>BACI</b> (CEPII, reconciled from UN Comtrade). Destination totals cover the major flows (top partners per product) — about 87% of the headline total; the rest is a long tail of small shipments. For the official, 8-digit, fiscal-year figures see the <b>Department of Customs</b> and <b>TEPC</b>.</p></div>
    <h3 class="h">All ${dests.length} destination markets</h3><div class="secs">${dests.map(i=>{const m=isoMeta(i);return `<a class="sec" href="${BASE}/nepal/exports/${i.toLowerCase()}" data-nav><span class="t">${m[1]} ${esc(m[0])}</span><span class="c">${money(X.cc[i]*1e6)}</span></a>`;}).join('')}</div>
  </div></main>`;
}

function nepExportMarket(iso){
  if(!exReady(()=>nepExportMarket(iso))) return;
  setNav('exports');
  const X=nepExports(), m=isoMeta(iso), name=m[0], prods=(X.cp[iso]||[]).filter(x=>x[1]>0);
  setTitle(PT.nepMkt(name));
  track('view_nepal_export_market',{country:iso});
  if(!prods.length){ app.innerHTML=`<main><div class="wrap"><a class="back" href="${BASE}/nepal/exports" data-nav>${ic(I.left)}Export Explorer</a><div class="empty" style="padding-top:40px"><b>${m[1]} ${esc(name)}</b><p>No tracked Nepali exports to this market in 2024.</p></div></div></main>`; return; }
  const tot=X.cc[iso]||0, share=Math.round(tot/((NEP._t&&NEP._t.ex)||X.tot)*100);
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/nepal/exports" data-nav>${ic(I.left)}Export Explorer</a>
    <div class="ph"><h1 class="h2">${m[1]} Nepal → ${esc(name)}</h1><p>Every product Nepal exports to ${esc(name)} (BACI 2024), largest first.</p></div>
    <div class="statrow" style="margin-top:0">
      <div class="s"><b class="ex">${money(tot*1e6)}</b><span>Nepal's exports here</span></div>
      <div class="s"><b>${prods.length}</b><span>Products</span></div>
      <div class="s"><b>${share<1?'<1':share}%</b><span>of Nepal's exports</span></div>
    </div>
    <h3 class="h">Products Nepal exports to ${esc(name)}</h3>
    ${prods.map(x=>{ const p=PROD[x[0]]; return exRow(x[0],x[1], p&&p.u?`world price $${p.u}/kg`:''); }).join('')}
    <a class="nepalcard" href="${BASE}/trade/${iso.toLowerCase()}" data-nav><span class="fl">${m[1]}</span><span><b>${esc(name)}'s full trade profile</b> — its total exports, imports &amp; top partners ${ic(I.right)}</span></a>
    <div class="src"><div class="src-h">${ic(I.shield)}<span>Source</span><span style="margin-left:auto;color:var(--muted);font-weight:600">2024</span></div>
      <p>From <b>BACI</b> (CEPII, reconciled UN Comtrade). Values are Nepal→${esc(name)} merchandise exports at HS-6, current US$. For official 8-digit, fiscal-year figures, see Nepal's Department of Customs and TEPC; for Nepal duty and taxes see <a href="https://customsnepal.com/" target="_blank" rel="noopener">customsnepal.com ↗</a>.</p></div>
  </div></main>`;
}

function nepExportGuide(slug){
  const g=EXGUIDES[slug]; if(!g){ nepExportsHome(); return; }
  if(!exReady(()=>nepExportGuide(slug))) return;
  setNav('exports');
  setTitle(PT.guide(g));
  track('view_export_guide',{guide:slug});
  const hs=g.hs, z=NEP[hs]||{}, p=PROD[hs]||{};
  const dests=(z.exs||[]).filter(x=>x[1]>0).slice(0,5);
  app.innerHTML=`<main><div class="wrap">
    <a class="back" href="${BASE}/nepal/exports" data-nav>${ic(I.left)}Export Explorer</a>
    <div class="ph"><h1 class="h2">${g.fl} ${esc(g.h1)}</h1><p>${esc(g.sub)}</p></div>
    <div class="statrow" style="margin-top:0">
      <div class="s"><b class="ex">${z.ex?money(z.ex*1e6):'—'}</b><span>Nepal exports (2024)</span></div>
      <div class="s"><b>${p.w?money(p.w*1e6):'—'}</b><span>World market</span></div>
      <div class="s"><b>${p.u?'$'+p.u+'/kg':'—'}</b><span>World price</span></div>
    </div>
    ${g.body}
    <h3 class="h">Where Nepal sells it (2024)</h3>
    ${dests.length?`<div class="bars">${dests.map((x,i)=>{const mm=isoMeta(x[0]);return `<a class="lbrow" href="${BASE}/nepal/exports/${x[0].toLowerCase()}" data-nav><span class="rk">${i+1}</span><span class="lb">${mm[1]} ${esc(mm[0])}</span><span class="tr"><span class="fi" style="width:${Math.max(2,x[1]/Math.max(dests[0][1],1)*100)}%;background:var(--exp)"></span></span><span class="vl">${money(x[1]*1e6)}</span></a>`;}).join('')}</div>`:'<p class="fine">—</p>'}
    <h3 class="h">The HS code</h3>
    <a class="row" href="${BASE}/hs/code/${hs}" data-nav><span class="code">${fmtCode(hs)}</span><span class="d">${esc(hsDesc(hs))}</span><span class="end">${ic(I.right)}</span></a>
    <div class="src"><div class="src-h">${ic(I.shield)}<span>Sources</span></div><p>Trade figures: <b>BACI</b> (CEPII / UN Comtrade), 2024. Export procedure: ${g.sources} Incentive rates and GSP eligibility change yearly — confirm current terms with the official source before relying on them.</p></div>
  </div></main>`;
}

window.__go=nav;
boot();
})();
