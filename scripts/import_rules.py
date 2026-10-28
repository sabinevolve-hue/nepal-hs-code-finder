"""Import permits & restrictions checker — "Can I import this?" (Phase 2).

A crawlable /import-rules page explaining what it takes to legally import a
product into Nepal: the universal requirements (EXIM code, payment/LC, customs
declaration) plus the product-specific permits by authority (plant/animal
quarantine, DFTQC food, DDA drugs, NTA telecom, NBSM standards, MoHA arms).

Includes a small client-side lookup: paste an HS code -> the authorities whose
permit is likely to apply (heading-level where known, else chapter-level).
Honest, indicative mapping; every result points to the authority to confirm with.

Emits public/import-rules.html; appends the URL to sitemap.xml. Mirrors
seo_pages/product_pages (canonical -> www.customsnepal.com, shared seo.css, nav).

Run after seo_pages.py:  python3 scripts/import_rules.py
"""
import pathlib, json, datetime, html

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'
SITE = 'https://www.customsnepal.com'
TODAY = datetime.date.today().isoformat()


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E"
           "%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230F172A%27/%3E"
           "%3Ctext x=%2716%27 y=%2721%27 font-family=%27monospace%27 font-size=%2713%27 font-weight=%27700%27 "
           "fill=%27white%27 text-anchor=%27middle%27%3EHS%3C/text%3E%3C/svg%3E")
ANALYTICS = ("<script>(function(){var h=location.hostname;"
             "if(h.indexOf('customsnepal.com')<0&&h.indexOf('vercel.app')<0)return;"
             "var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id=G-T1FQWWL2VV';document.head.appendChild(g);"
             "window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-T1FQWWL2VV');"
             "})();</script>")

from nav import render_nav


def page_head(title, desc, path, breadcrumb, extra_ld=None):
    lds = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": b[0],
                                 **({"item": SITE + b[1]} if b[1] else {})} for i, b in enumerate(breadcrumb)]}]
    if extra_ld:
        lds += extra_ld
    ldj = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script>' for x in lds)
    nav = render_nav(path, esc)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0F172A">'
        '<title>' + esc(title) + '</title>'
        '<meta name="description" content="' + esc(desc) + '">'
        '<link rel="canonical" href="' + SITE + path + '">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Customs Nepal">'
        '<meta property="og:title" content="' + esc(title) + '">'
        '<meta property="og:description" content="' + esc(desc) + '">'
        '<meta property="og:url" content="' + SITE + path + '">'
        '<meta property="og:image" content="' + SITE + '/og.png">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="icon" href="' + FAVICON + '"><link rel="apple-touch-icon" href="/icon-180.png">'
        '<link rel="stylesheet" href="/seo.css">'
        + ldj + ANALYTICS +
        '</head><body>'
        '<header class="top"><div class="wrap topbar">'
        '<a class="logo" href="/" aria-label="Customs Nepal — home"><span class="mark">HS</span><span class="lt">Customs Nepal<small>HS codes, duty &amp; trade</small></span></a>'
        '<nav class="topnav">' + nav + '</nav></div></header>'
        '<div class="wrap">'
    )


def crumb_html(breadcrumb):
    parts = ['<a href="' + p + '">' + esc(n) + '</a>' if p else esc(n) for n, p in breadcrumb]
    return '<nav class="crumb">' + ' › '.join(parts) + '</nav>'


FOOT = ('<footer><div class="wrap">'
        '<p><b>Indicative guidance only.</b> Permit requirements depend on the exact product, its end use and current '
        'government notices, and they change. This page maps the <i>likely</i> authority by HS chapter/heading — always '
        'confirm with the authority named and with the '
        '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs</a> and the '
        '<a href="https://nepaltradeportal.gov.np" target="_blank" rel="noopener noreferrer">Nepal Trade Information Portal</a> '
        'before you ship or pay.</p>'
        '<p><b>Not a government website.</b> Customs Nepal is an independent reference tool, not affiliated with the Government of Nepal.</p>'
        '<p><a href="/">Home</a> · <a href="/import-duty">Import duty by product</a> · <a href="/calculator">Calculator</a> · '
        '<a href="/shipping">Shipping</a> · © customsnepal.com</p></div></footer>'
        '</body></html>')

# ---------------- the mapping ----------------
AUTH = {
    'animalq': dict(n='Animal Quarantine (Dept. of Livestock Services)', u='https://dls.gov.np',
                    p='Veterinary import permit + animal health / quarantine certificate',
                    g='Live animals, meat, fish, eggs, dairy and other animal products'),
    'plantq': dict(n='Plant Quarantine — NPPO Nepal', u='https://npponepal.gov.np',
                   p='Import permit + a phytosanitary certificate from the exporting country',
                   g='Plants, seeds, fruit, vegetables, grains, spices and other plant products'),
    'dftqc': dict(n='Food Technology & Quality Control (DFTQC)', u='https://dftqc.gov.np',
                  p='Food-import recommendation + laboratory testing / quality certificate',
                  g='Processed food, edible oils, beverages, dairy and other food items'),
    'dda': dict(n='Drug Administration (DDA)', u='https://dda.gov.np',
                p='Product registration + import licence (the importer itself must be DDA-licensed)',
                g='Medicines, vaccines, cosmetics and medical devices'),
    'nta': dict(n='Telecommunications Authority (NTA)', u='https://nta.gov.np',
                p='Type Approval Certificate (TAC)',
                g='Mobile phones and radio / wireless telecom equipment'),
    'nbsm': dict(n='Bureau of Standards & Metrology (NBSM)', u='https://nbsm.gov.np',
                 p='Mandatory NS standard certification / NS mark',
                 g='Goods under compulsory standards — steel & rebar, cement, cables, LPG cylinders, helmets, bottled water and more'),
    'pesticide': dict(n='Pesticide Registration & Management Centre', u='https://npponepal.gov.np',
                      p='Pesticide registration + import permit',
                      g='Insecticides, herbicides, fungicides and other pesticides'),
    'fertilizer': dict(n='Fertilizer regulation (MoALD)', u='https://moald.gov.np',
                       p='Government-regulated; import permit / quality control',
                       g='Chemical fertilizers'),
    'vehicle': dict(n='Transport Management (DoTM)', u='https://dotm.gov.np',
                    p='Emission & safety standards, then registration after import',
                    g='Motor vehicles and motorcycles'),
    'home': dict(n='Ministry of Home Affairs', u='https://moha.gov.np',
                 p='Special licence — heavily restricted or prohibited',
                 g='Arms, ammunition and explosives'),
}
# order for the static reference
AUTH_ORDER = ['plantq', 'animalq', 'dftqc', 'dda', 'nta', 'nbsm', 'pesticide', 'fertilizer', 'vehicle', 'home']

CHRULES = {
    1: ['animalq'], 2: ['animalq', 'dftqc'], 3: ['animalq', 'dftqc'], 4: ['animalq', 'dftqc'], 5: ['animalq'],
    6: ['plantq'], 7: ['plantq', 'dftqc'], 8: ['plantq', 'dftqc'], 9: ['plantq', 'dftqc'], 10: ['plantq', 'dftqc'],
    11: ['plantq', 'dftqc'], 12: ['plantq'], 13: ['plantq'], 14: ['plantq'], 15: ['dftqc'],
    16: ['dftqc'], 17: ['dftqc'], 18: ['dftqc'], 19: ['dftqc'], 20: ['dftqc'], 21: ['dftqc'], 22: ['dftqc'],
    23: ['animalq'], 24: ['dftqc'], 30: ['dda'], 31: ['fertilizer'], 72: ['nbsm'], 73: ['nbsm'],
    87: ['vehicle'], 93: ['home'],
}
HDRULES = {
    '2523': ['nbsm'],
    '3303': ['dda'], '3304': ['dda'], '3305': ['dda'], '3306': ['dda'], '3307': ['dda'],
    '3808': ['pesticide'],
    '3601': ['home'], '3602': ['home'], '3603': ['home'], '3604': ['home'],
    '8517': ['nta'], '8525': ['nta'], '8526': ['nta'], '8527': ['nta'], '8528': ['nta'],
    '9018': ['dda'], '9019': ['dda'], '9020': ['dda'], '9021': ['dda'], '9022': ['dda'],
}

UNIVERSAL = [
    ('An importer registration', 'A registered firm with a PAN/VAT number and an <b>EXIM (export-import) code</b> from the Department of Customs.'),
    ('A compliant payment route', 'Most commercial imports need a <b>letter of credit (L/C)</b> or another Nepal Rastra Bank–permitted payment method; some require advance-payment or document-against-payment approval.'),
    ('A customs declaration', 'A declaration through <b>ASYCUDA</b> at the customs office / dry port, with the invoice, packing list, bill of lading / airway bill and certificate of origin, and payment of duty + 13% VAT (and any excise).'),
]

# ---------------- page ----------------
title = 'Can I import this? Import permits & restrictions for Nepal | Customs Nepal'
desc = ('What it takes to legally import a product into Nepal — the EXIM code and payment rules that always apply, '
        'plus the product-specific permits (plant/animal quarantine, DFTQC food, DDA drugs, NTA telecom, NBSM '
        'standards). Enter an HS code to see which authority is likely involved.')
bc = [('Home', '/'), ('Import rules', '')]
faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": "What do I need to import goods into Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": (
         "Every commercial import needs a registered firm with a PAN/VAT number and an EXIM (export-import) code from "
         "the Department of Customs, a compliant payment route (usually a letter of credit or another Nepal Rastra "
         "Bank–permitted method) and a customs declaration through ASYCUDA with duty and 13% VAT paid. Many products "
         "also need a product-specific permit — for example a phytosanitary certificate for plants, animal-quarantine "
         "clearance for animal products, a DFTQC recommendation for food, DDA registration for medicines and "
         "cosmetics, an NTA Type Approval for telecom equipment, or NBSM standard certification.")}},
    {"@type": "Question", "name": "Which products need a special permit to import into Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": (
         "Plants and seeds need plant-quarantine clearance; animals, meat and dairy need animal-quarantine clearance; "
         "food needs a DFTQC recommendation; medicines, cosmetics and medical devices need DDA registration and an "
         "import licence; mobile phones and wireless equipment need an NTA Type Approval Certificate; and goods under "
         "compulsory standards (steel, cement, cables, LPG cylinders, helmets, bottled water) need NBSM certification. "
         "Arms, ammunition and explosives are heavily restricted and need a Ministry of Home Affairs licence.")}}]}

out = [page_head(title, desc, '/import-rules', bc, extra_ld=[faq]), crumb_html(bc)]
out.append('<h1>Can I import this into Nepal?</h1>')
out.append('<p class="lede">Before the duty, there are the <b>rules</b>. Every commercial import needs an EXIM code, a '
           'compliant payment route and a customs declaration — and many products also need a permit from a specific '
           'authority. Paste an HS code to see which authority is likely involved, or read the full breakdown below.</p>')

# lookup
out.append('<form class="trkbox" id="irform" role="search" aria-label="Check import rules">'
           '<input id="irin" type="search" inputmode="latin" autocomplete="off" spellcheck="false" '
           'placeholder="Enter an HS code — e.g. 8517.12.00 or 0803" aria-label="HS code">'
           '<button type="submit" class="trkgo">Check</button></form>'
           '<div id="irresult" class="trkresult" aria-live="polite"></div>')

# universal requirements (always)
out.append('<h2 class="sec">Always required (any commercial import)</h2>')
out.append('<div class="guidegrid">')
for t, d in UNIVERSAL:
    out.append('<div class="chcard" style="cursor:default"><span class="t">%s</span><span class="c">%s</span></div>' % (esc(t), d))
out.append('</div>')

# authority reference
out.append('<h2 class="sec">Product-specific permits — who governs what</h2>')
out.append('<p>On top of the universal requirements, these authorities control imports of particular products. '
           'The checker above maps your HS code to the ones likely to apply.</p>')
out.append('<div class="tscroll"><table class="tbl"><thead><tr><th>Product category</th><th>Authority</th>'
           '<th>What you need</th></tr></thead><tbody>')
for k in AUTH_ORDER:
    a = AUTH[k]
    out.append('<tr><td>%s</td><td><a href="%s" target="_blank" rel="noopener noreferrer nofollow">%s ↗</a></td><td>%s</td></tr>'
               % (esc(a['g']), esc(a['u']), esc(a['n']), esc(a['p'])))
out.append('</tbody></table></div>')

# banned / restricted
out.append('<h2 class="sec">Banned &amp; restricted goods</h2>')
out.append('<div class="note">A few goods are <b>prohibited or quantity-restricted</b> under the Export Import '
           '(Control) Act and periodic government notices (the list changes — past examples have included certain '
           'luxury items during balance-of-payments measures). Narcotics, counterfeit goods and unlicensed arms are '
           'always prohibited. Check the current control list on the '
           '<a href="https://www.customs.gov.np" target="_blank" rel="noopener noreferrer">Department of Customs</a> and '
           '<a href="https://nepaltradeportal.gov.np" target="_blank" rel="noopener noreferrer">Nepal Trade Information Portal</a> '
           'before committing.</div>')

out.append('<div class="tools"><a class="btn" href="/import-duty">Import duty by product</a>'
           '<a class="btn ghost" href="/calculator">Landed-cost calculator</a>'
           '<a class="btn ghost" href="/shipping">Shipping to Nepal</a></div>')

# ---------------- lookup script ----------------
DATA = {'AUTH': AUTH, 'CH': {str(k): v for k, v in CHRULES.items()}, 'HD': HDRULES,
        'ORDER': AUTH_ORDER}
SCRIPT = """<script>
(function(){
 var D=%s;
 function norm(s){return (s||'').toUpperCase().replace(/[^0-9]/g,'');}
 function keysFor(cn){
  var hd=cn.slice(0,4), ch=String(parseInt(cn.slice(0,2),10));
  var out=[], seen={};
  (D.HD[hd]||[]).concat(D.CH[ch]||[]).forEach(function(k){if(!seen[k]){seen[k]=1;out.push(k);}});
  return out;
 }
 function esc(s){var d=document.createElement('div');d.textContent=(s==null?'':s);return d.innerHTML;}
 function render(raw){
  var box=document.getElementById('irresult'); if(!box) return;
  var cn=norm(raw); if(!cn){box.innerHTML='';return;}
  if(cn.length<2){box.innerHTML='<div class="trkcard warn"><p class="trkhdr">Enter at least the 2-digit chapter</p></div>';return;}
  var ch=cn.slice(0,2), keys=keysFor(cn);
  var h='<div class="trkcard ok"><p class="trkhdr">HS <b>'+esc(cn.slice(0,4))+'</b> — chapter '+esc(ch)+'</p>';
  if(keys.length){
   h+='<p class="trkhint">Likely permit(s) in addition to the universal requirements:</p><ol class="trktl-list">';
   keys.forEach(function(k){var a=D.AUTH[k];
     h+='<li class="act"><span class="trktl-m">'+esc(a.n)+'</span><span class="trktl-l">'+esc(a.p)+'</span>'
       +'<span class="trktl-t"><a href="'+esc(a.u)+'" target="_blank" rel="noopener noreferrer nofollow">'+esc(a.u.replace(/^https?:\\/\\//,''))+' ↗</a></span></li>';});
   h+='</ol>';
  }else{
   h+='<p class="trkhint">No product-specific permit is flagged for this chapter — but the <b>universal requirements</b> (EXIM code, payment route, customs declaration) still apply, and a specific heading can still trigger a standard or licence. Confirm with the Department of Customs.</p>';
  }
  h+='<p class="trkhint">Indicative only — confirm with the authority named and the Department of Customs. '
    +'<a href="/import-duty">See the duty on this product →</a></p></div>';
  box.innerHTML=h;
  if(window.gtag){try{gtag('event','import_rules_lookup');}catch(e){}}
 }
 var f=document.getElementById('irform'), i=document.getElementById('irin');
 if(f&&i){f.addEventListener('submit',function(e){e.preventDefault();render(i.value);});}
 try{var q=new URLSearchParams(location.search).get('hs'); if(q&&i){i.value=q;render(q);}}catch(e){}
})();
</script>""" % json.dumps(DATA, ensure_ascii=False)
out.append(SCRIPT)
out.append(FOOT)
(pub / 'import-rules.html').write_text(''.join(out), encoding='utf-8')

# ---------------- sitemap ----------------
sm_path = pub / 'sitemap.xml'
sm = sm_path.read_text(encoding='utf-8')
row = '  <url><loc>%s/import-rules</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>' % (SITE, TODAY)
if '/import-rules</loc>' not in sm and '</urlset>' in sm:
    sm_path.write_text(sm.replace('</urlset>', row + '\n</urlset>'), encoding='utf-8')

print('import_rules: /import-rules built (%d authorities, %d chapter + %d heading rules)' % (len(AUTH), len(CHRULES), len(HDRULES)))
