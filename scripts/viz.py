"""Server-rendered SVG charts + copy/export tools for the static pages.

Charts are plain inline SVG (crawlable, no chart library, theme-aware through CSS
variables). Every figure carries its data as TSV for "Copy data" and can be saved
as a PNG; every table gets "Copy table" / "Download CSV". The behaviour lives in
/cn-tools.js, written by write_assets().

Colours: the dataviz categorical palette, validated (CVD + contrast) against this
site's light (#fff) and dark (#131C2E) card surfaces. Imports = slot 1 (blue),
exports = slot 2 (orange) everywhere.
"""
import html, math

W = 600

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def cut(s, n):
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'

# ---- HS chapter icon + short name ----
def chap_icon(ch):
    try:
        n = int(ch)
    except Exception:
        return '📦'
    table = [(5, '🐄'), (14, '🌾'), (15, '🫒'), (24, '🥫'), (26, '⛏️'), (27, '⛽'), (29, '🧪'), (30, '💊'),
             (31, '🌱'), (38, '🧪'), (40, '🧴'), (43, '👜'), (46, '🪵'), (49, '📄'), (56, '🧵'), (57, '🧶'),
             (60, '🧵'), (63, '👕'), (67, '👟'), (70, '🧱'), (71, '💎'), (83, '🔩'), (84, '⚙️'), (85, '🔌'),
             (86, '🚆'), (87, '🚗'), (88, '✈️'), (89, '🚢'), (92, '🔬'), (93, '🎯'), (96, '🛋️'), (99, '🎨')]
    for lim, ic in table:
        if n <= lim:
            return ic
    return '📦'

SHORT = {
    '02': 'Meat', '03': 'Fish', '04': 'Dairy & eggs', '07': 'Vegetables', '08': 'Fruit & nuts', '09': 'Coffee, tea & spices',
    '10': 'Cereals', '11': 'Flour & malt', '12': 'Oil seeds & herbs', '15': 'Edible oils & fats', '17': 'Sugar',
    '19': 'Bakery & noodles', '20': 'Processed fruit & veg', '21': 'Food preparations', '22': 'Beverages & alcohol',
    '23': 'Animal feed', '24': 'Tobacco', '25': 'Salt, stone & cement', '26': 'Ores', '27': 'Fuel & petroleum',
    '28': 'Inorganic chemicals', '29': 'Organic chemicals', '30': 'Pharmaceuticals', '31': 'Fertilisers',
    '32': 'Paints & dyes', '33': 'Cosmetics & perfumery', '34': 'Soap & detergents', '38': 'Chemical products',
    '39': 'Plastics', '40': 'Rubber & tyres', '42': 'Leather goods & bags', '44': 'Wood', '48': 'Paper & board',
    '49': 'Printed matter', '52': 'Cotton', '53': 'Jute & plant fibres', '54': 'Synthetic filament', '55': 'Synthetic staple fibres',
    '56': 'Felt & nonwovens', '57': 'Carpets', '59': 'Coated textiles', '60': 'Knitted fabrics', '61': 'Knitted apparel',
    '62': 'Woven apparel', '63': 'Home textiles', '64': 'Footwear', '69': 'Ceramics', '70': 'Glass',
    '71': 'Gold, silver & gems', '72': 'Iron & steel', '73': 'Steel articles', '74': 'Copper', '76': 'Aluminium',
    '82': 'Tools & cutlery', '83': 'Metal fittings', '84': 'Machinery', '85': 'Electronics & electrical',
    '87': 'Vehicles', '88': 'Aircraft & parts', '90': 'Instruments & medical', '94': 'Furniture & lighting',
    '95': 'Toys & sports', '96': 'Misc. manufactures', '97': 'Art & antiques',
}
def chap_short(ch, full=''):
    if ch in SHORT:
        return SHORT[ch]
    base = (full or ('Chapter ' + ch)).split(';')[0].split(',')[0]
    return cut(base, 28)

def _svg(h, body, label):
    return ('<svg class="vz" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">%s</svg>'
            % (W, h, esc(label), body))

# ---- snapshot card: the shareable "at a glance" image ----
def snapshot(flag, name, fy, imp_s, exp_s, bal_s, imp, exp, deficit):
    mx = max(imp, exp, 1.0)
    wi = max(3.0, 560.0 * imp / mx); we = max(3.0, 560.0 * exp / mx)
    b = []
    b.append('<text x="20" y="36" class="t" font-size="20" font-weight="700">%s Nepal–%s trade</text>' % (flag, esc(name)))
    b.append('<text x="580" y="36" class="m" font-size="12" text-anchor="end">FY %s</text>' % esc(fy))
    cols = [(20, 'Nepal imports', imp_s, 't'), (215, 'Nepal exports', exp_s, 't'), (410, 'Trade balance', bal_s, 'cb' if deficit else 't')]
    for x, lab, val, cls in cols:
        b.append('<text x="%d" y="68" class="m" font-size="11.5">%s</text>' % (x, lab))
        b.append('<text x="%d" y="94" class="%s" font-size="19" font-weight="700">%s</text>' % (x, cls, esc(val)))
    b.append('<text x="20" y="126" class="m" font-size="11.5">Imports from %s</text>' % esc(name))
    b.append('<rect x="20" y="132" width="%.1f" height="22" rx="4" class="c1"><title>Imports %s</title></rect>' % (wi, esc(imp_s)))
    b.append('<text x="20" y="180" class="m" font-size="11.5">Exports to %s</text>' % esc(name))
    b.append('<rect x="20" y="186" width="%.1f" height="22" rx="4" class="c2"><title>Exports %s</title></rect>' % (we, esc(exp_s)))
    b.append('<text x="20" y="238" class="m" font-size="10.5">Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s · customsnepal.com</text>' % esc(fy))
    return _svg(250, ''.join(b), 'Nepal–%s trade at a glance' % name)

# ---- segmented composition bar (one whole split into parts) ----
def segbar(items, label):
    """items: [(name, icon, value)] already limited (last may be 'Other'); returns (svg, tsv)."""
    total = sum(v for _, _, v in items) or 1.0
    n = len(items)
    cls = ['c1', 'c2', 'c3', 'c4', 'c5', 'cg']
    avail = W - 2.0 * (n - 1)
    x = 0.0; b = []
    for i, (nm, ic, v) in enumerate(items):
        c = 'cg' if nm == 'Other' else cls[min(i, 4)]
        w = max(2.0, avail * v / total)
        pct = v / total * 100
        b.append('<rect x="%.1f" y="6" width="%.1f" height="28" rx="4" class="%s"><title>%s — %.1f%%</title></rect>'
                 % (x, w, c, esc(nm), pct))
        if w > 46:
            b.append('<text x="%.1f" y="25" font-size="11.5" font-weight="700" class="%s">%.0f%%</text>'
                     % (x + 7, 'onc' if c in ('c1', 'c2') else 'ond', pct))
        x += w + 2.0
    y0 = 58
    for i, (nm, ic, v) in enumerate(items):
        c = 'cg' if nm == 'Other' else cls[min(i, 4)]
        cx = 0 if i % 2 == 0 else 305
        cy = y0 + (i // 2) * 23
        b.append('<rect x="%d" y="%d" width="11" height="11" rx="2.5" class="%s"/>' % (cx, cy - 10, c))
        b.append('<text x="%d" y="%d" class="t" font-size="12.5">%s %s</text>' % (cx + 18, cy, ic, esc(cut(nm, 30))))
        b.append('<text x="%d" y="%d" class="m" font-size="12.5" text-anchor="end">%.1f%%</text>' % (cx + 290, cy, v / total * 100))
    h = y0 + ((n + 1) // 2 - 1) * 23 + 10
    tsv = 'Group\tShare %\n' + '\n'.join('%s\t%.1f' % (nm, v / total * 100) for nm, _, v in items)
    return _svg(h, ''.join(b), label), tsv

# ---- ranked horizontal bars ----
def hbars(items, cls, label, head=('Item', 'Value')):
    """items: [(label, value_string, value)]"""
    mx = max((v for _, _, v in items), default=1.0) or 1.0
    b = []
    for i, (lab, vs, v) in enumerate(items):
        y = i * 28
        w = max(3.0, 245.0 * v / mx)
        b.append('<text x="0" y="%d" class="t" font-size="12">%s</text>' % (y + 17, esc(cut(lab, 38))))
        b.append('<rect x="245" y="%d" width="%.1f" height="14" rx="4" class="%s"><title>%s — %s</title></rect>'
                 % (y + 6, w, cls, esc(lab), esc(vs)))
        b.append('<text x="%.1f" y="%d" class="t" font-size="12" font-weight="600">%s</text>' % (245 + w + 8, y + 17, esc(vs)))
    tsv = '%s\t%s\n' % head + '\n'.join('%s\t%s' % (lab, vs) for lab, vs, _ in items)
    return _svg(len(items) * 28 + 4, ''.join(b), label), tsv

# ---- two share rings ----
def rings(p_imp, p_exp, name):
    r = 44; circ = 2 * math.pi * r
    def ring(cx, p, scls, l1, l2):
        arc = circ * min(max(p, 0.0), 100.0) / 100.0
        return ('<circle cx="%d" cy="65" r="%d" class="trk" stroke-width="12"/>'
                '<circle cx="%d" cy="65" r="%d" class="%s" stroke-width="12" stroke-linecap="round" '
                'stroke-dasharray="%.1f %.1f" transform="rotate(-90 %d 65)"/>'
                '<text x="%d" y="70" class="t" font-size="15" font-weight="700" text-anchor="middle">%s%%</text>'
                '<text x="%d" y="60" class="t" font-size="13" font-weight="600">%s</text>'
                '<text x="%d" y="79" class="m" font-size="12">%s</text>'
                % (cx, r, cx, r, scls, max(arc, 0.01), circ, cx, cx, ('%.1f' % p) if p < 99.95 else '100',
                   cx + 62, l1, cx + 62, esc(l2)))
    body = ring(60, p_imp, 's1', 'of Nepal’s imports', 'come from ' + name) + \
           ring(360, p_exp, 's2', 'of Nepal’s exports', 'go to ' + name)
    tsv = 'Measure\tShare %%\nShare of Nepal imports from %s\t%.1f\nShare of Nepal exports to %s\t%.1f' % (name, p_imp, name, p_exp)
    return _svg(130, body, 'Share of Nepal’s trade with %s' % name), tsv

# ---- route diagram ----
def route(nodes, label):
    """nodes: [(icon, label, sub)]"""
    n = len(nodes)
    xs = [44 + i * (512.0 / (n - 1)) for i in range(n)]
    b = ['<line x1="%.0f" y1="34" x2="%.0f" y2="34" class="ln" stroke-width="2" stroke-dasharray="5 5"/>' % (xs[0], xs[-1])]
    for x, (ic, lab, sub) in zip(xs, nodes):
        b.append('<circle cx="%.0f" cy="34" r="23" class="nd" stroke-width="1.5"/>' % x)
        b.append('<text x="%.0f" y="41" font-size="20" text-anchor="middle">%s</text>' % (x, ic))
        b.append('<text x="%.0f" y="78" class="t" font-size="11" font-weight="600" text-anchor="middle">%s</text>' % (x, esc(lab)))
        if sub:
            b.append('<text x="%.0f" y="93" class="m" font-size="10" text-anchor="middle">%s</text>' % (x, esc(sub)))
    tsv = 'Step\tStage\tDetail\n' + '\n'.join('%d\t%s\t%s' % (i + 1, lab, sub) for i, (_, lab, sub) in enumerate(nodes))
    return _svg(104, ''.join(b), label), tsv

# ---- grouped bars (hub) ----
def grouped(items, label, money):
    """items: [(label, imp, exp)]"""
    mx = max((max(i, e) for _, i, e in items), default=1.0) or 1.0
    b = []
    for k, (lab, i, e) in enumerate(items):
        y = k * 40
        wi = max(2.0, 300.0 * i / mx); we = max(2.0, 300.0 * e / mx)
        b.append('<text x="0" y="%d" class="t" font-size="12.5" font-weight="600">%s</text>' % (y + 22, esc(cut(lab, 22))))
        b.append('<rect x="170" y="%d" width="%.1f" height="12" rx="3.5" class="c1"><title>%s imports %s</title></rect>' % (y + 5, wi, esc(lab), esc(money(i))))
        b.append('<rect x="170" y="%d" width="%.1f" height="12" rx="3.5" class="c2"><title>%s exports %s</title></rect>' % (y + 19, we, esc(lab), esc(money(e))))
        b.append('<text x="%.1f" y="%d" class="m" font-size="11">%s</text>' % (170 + wi + 6, y + 15, esc(money(i))))
        b.append('<text x="%.1f" y="%d" class="m" font-size="11">%s</text>' % (170 + we + 6, y + 30, esc(money(e))))
    tsv = 'Partner\tImports\tExports\n' + '\n'.join('%s\t%s\t%s' % (lab, money(i), money(e)) for lab, i, e in items)
    return _svg(len(items) * 40 + 2, ''.join(b), label), tsv

# ---- wrappers ----
def figure(title, svg, tsv, source, bare=False, legend=''):
    return ('<figure class="vzfig" data-title="%s" data-src="%s"%s><figcaption><b>%s</b>%s'
            '<span class="vzbtns"><button type="button" data-act="copy">Copy data</button>'
            '<button type="button" data-act="png">Save image</button></span></figcaption>'
            '<div class="vzwrap">%s</div><textarea class="vztsv" hidden>%s</textarea></figure>'
            % (esc(title), esc(source), ' data-bare="1"' if bare else '', esc(title), legend, svg, esc(tsv)))

LEGEND_IE = ('<span class="vzleg"><i class="k1"></i>Imports<i class="k2"></i>Exports</span>')

def table_tools(name):
    return ('<div class="tbltools"><button type="button" data-act="tcopy">Copy table</button>'
            '<button type="button" data-act="tcsv" data-name="%s">Download CSV</button></div>' % esc(name))

CSS = """
:root{--v1:#2a78d6;--v2:#eb6834;--v3:#1baf7a;--v4:#eda100;--v5:#e87ba4;--vg:#94a3b8;--vcrit:#d03b3b}
@media(prefers-color-scheme:dark){:root{--v1:#3987e5;--v2:#d95926;--v3:#199e70;--v4:#c98500;--v5:#d55181;--vg:#64748b;--vcrit:#e66767}}
.vzfig{margin:1em 0 1.3em;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 14px}
.vzfig figcaption{display:flex;justify-content:space-between;align-items:center;gap:8px 12px;flex-wrap:wrap;margin-bottom:10px;font-size:.92rem}
.vzbtns,.tbltools{display:flex;gap:6px;flex-wrap:wrap}
.vzbtns{margin-left:auto}
.vzbtns button,.tbltools button,.keycopy{font:600 .74rem var(--f);color:var(--fg2);background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:5px 10px;cursor:pointer;transition:border-color .15s,color .15s}
.vzbtns button:hover,.tbltools button:hover,.keycopy:hover{border-color:var(--accent);color:var(--accent)}
.vzbtns button:focus-visible,.tbltools button:focus-visible,.keycopy:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tbltools{justify-content:flex-end;margin:.7em 0 .3em}
.vzwrap{overflow-x:auto}
svg.vz{display:block;width:100%;min-width:470px;height:auto;font-family:var(--f)}
.vz .t{fill:var(--fg)}.vz .m{fill:var(--muted)}.vz .cb{fill:var(--vcrit)}
.vz .c1{fill:var(--v1)}.vz .c2{fill:var(--v2)}.vz .c3{fill:var(--v3)}.vz .c4{fill:var(--v4)}.vz .c5{fill:var(--v5)}.vz .cg{fill:var(--vg)}
.vz .trk{stroke:var(--border);fill:none}.vz .s1{stroke:var(--v1);fill:none}.vz .s2{stroke:var(--v2);fill:none}
.vz .ln{stroke:var(--border)}.vz .nd{fill:var(--accent-bg);stroke:var(--border)}
.vz .onc{fill:#fff}.vz .ond{fill:#0b1220}
.vzleg{display:inline-flex;align-items:center;gap:6px;font-size:.78rem;color:var(--muted)}
.vzleg i{width:11px;height:11px;border-radius:3px;display:inline-block;margin-left:6px}.vzleg .k1{background:var(--v1)}.vzleg .k2{background:var(--v2)}
.keycopy{margin:.2em 0 0}
@media(max-width:560px){svg.vz{min-width:430px}.vzfig::after{content:"Swipe the chart sideways to see it all →";display:block;margin-top:6px;font-size:.72rem;color:var(--muted)}}
"""

JS = r"""(function(){
"use strict";
function flash(b,t){var o=b.getAttribute('data-l')||b.textContent;b.setAttribute('data-l',o);b.textContent=t;setTimeout(function(){b.textContent=o},1500)}
function copy(text,b){
  function fb(){var ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();
    try{document.execCommand('copy');flash(b,'Copied ✓')}catch(e){flash(b,'Copy failed')}document.body.removeChild(ta)}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){flash(b,'Copied ✓')},fb)}else fb();
}
function rows(t){return [].map.call(t.rows,function(r){return [].map.call(r.cells,function(c){return (c.textContent||'').replace(/\s+/g,' ').trim()})})}
function save(name,blob){var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},800)}
function slug(s){return String(s).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'chart'}
function nextTable(el){var n=el.nextElementSibling;while(n){var t=n.matches&&n.matches('table')?n:(n.querySelector&&n.querySelector('table'));if(t)return t;n=n.nextElementSibling}return null}
var PROPS=['fill','stroke','stroke-width','stroke-dasharray','stroke-linecap','font-family','font-size','font-weight','opacity','text-anchor'];
function png(fig,b){
  var svg=fig.querySelector('svg');if(!svg)return;
  var clone=svg.cloneNode(true),src=svg.querySelectorAll('*'),dst=clone.querySelectorAll('*');
  for(var i=0;i<src.length;i++){var cs=getComputedStyle(src[i]),st='';for(var j=0;j<PROPS.length;j++){st+=PROPS[j]+':'+cs.getPropertyValue(PROPS[j])+';'}dst[i].setAttribute('style',st)}
  var vb=svg.viewBox.baseVal,W=vb.width,H=vb.height,bare=fig.getAttribute('data-bare')==='1';
  clone.setAttribute('width',W);clone.setAttribute('height',H);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
  clone.setAttribute('style','font-family:'+getComputedStyle(svg).fontFamily);
  var pad=24,head=bare?16:50,foot=bare?12:38,S=2,fs=getComputedStyle(fig),body=getComputedStyle(document.body);
  var cv=document.createElement('canvas');cv.width=(W+pad*2)*S;cv.height=(H+head+foot)*S;var g=cv.getContext('2d');g.scale(S,S);
  g.fillStyle=fs.backgroundColor||'#fff';g.fillRect(0,0,W+pad*2,H+head+foot);
  var fam=body.fontFamily||'sans-serif';
  if(!bare){g.fillStyle=body.color;g.font='700 17px '+fam;g.fillText(fig.getAttribute('data-title')||'',pad,32)}
  var img=new Image();
  img.onload=function(){g.drawImage(img,pad,head,W,H);
    if(!bare){g.fillStyle=getComputedStyle(fig.querySelector('figcaption')).color;g.globalAlpha=.7;g.font='11px '+fam;g.fillText(fig.getAttribute('data-src')||'',pad,H+head+22);g.globalAlpha=1}
    cv.toBlob(function(bl){if(bl){save(slug(fig.getAttribute('data-title'))+'.png',bl);flash(b,'Saved ✓')}else flash(b,'Could not save')},'image/png')};
  img.onerror=function(){flash(b,'Could not save')};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(clone));
}
document.addEventListener('click',function(e){
  var b=e.target.closest&&e.target.closest('[data-act]');if(!b)return;
  var act=b.getAttribute('data-act'),fig=b.closest('.vzfig');
  if(act==='copy'&&fig){var ta=fig.querySelector('.vztsv');copy((fig.getAttribute('data-title')||'')+'\n'+(ta?ta.value:'')+'\n'+(fig.getAttribute('data-src')||''),b)}
  else if(act==='png'&&fig){png(fig,b)}
  else if(act==='text'){copy(b.getAttribute('data-text')||'',b)}
  else if(act==='tcopy'||act==='tcsv'){var t=nextTable(b.parentNode);if(!t)return;var r=rows(t);
    if(act==='tcopy'){copy(r.map(function(x){return x.join('\t')}).join('\n'),b)}
    else{var csv=r.map(function(x){return x.map(function(c){return '"'+c.replace(/"/g,'""')+'"'}).join(',')}).join('\r\n');
      save((b.getAttribute('data-name')||'table')+'.csv',new Blob(['﻿'+csv],{type:'text/csv;charset=utf-8'}));flash(b,'Downloaded ✓')}}
});
})();
"""

def write_assets(pub):
    (pub / 'cn-tools.js').write_text(JS, encoding='utf-8')
    css_path = pub / 'seo.css'
    cur = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
    if '.vzfig{' not in cur:
        css_path.write_text(cur + '\n' + CSS.strip() + '\n', encoding='utf-8')
