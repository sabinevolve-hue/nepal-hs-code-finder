"""/compare — put two of Nepal's trading partners side by side (client-side, one static page).

Build-time, stdlib only. Embeds a slim extract of world/data/country.json (partners that have a page);
the picker reads ?a=<slug>&b=<slug> so any comparison is a shareable link. Without JavaScript the page
still shows the default pair as a plain table.
"""
import json
import pagekit as k
from pagekit import esc, money, pub, root
import links

CO = json.loads((root / 'world/data/country.json').read_text(encoding='utf-8'))
FY, YEARS = CO['fy'], CO.get('hist_years') or []
D = {}
for iso in links.TOP_PARTNERS:
    c = CO['countries'][iso]
    D[links.PARTNER_PAGE[iso][0].rsplit('/', 1)[1]] = {
        'n': c['name'], 'f': c.get('flag', ''), 'i': c['imp'], 'e': c['exp'], 'r': c.get('rev', 0), 'h': c.get('hist') or [],
        'ti': [[x[1][:44], x[2]] for x in (c.get('impP') or [])[:3]], 'te': [[x[1][:44], x[2]] for x in (c.get('expP') or [])[:3]]}
A, B = 'india', 'china'
timp, texp = CO['totals']['imp'], CO['totals']['exp']


def static_rows(a, b):
    x, y = D[a], D[b]
    r = lambda lab, f: '<tr><th scope="row">%s</th><td class="r">%s</td><td class="r">%s</td></tr>' % (lab, f(x), f(y))
    return (r('Nepal imports', lambda c: money(c['i'])) + r('Share of Nepal’s imports', lambda c: '%.1f%%' % (c['i'] / timp * 100))
            + r('Nepal exports', lambda c: money(c['e'])) + r('Share of Nepal’s exports', lambda c: '%.1f%%' % (c['e'] / texp * 100))
            + r('Trade balance', lambda c: money(c['e'] - c['i'])) + r('Collected at customs', lambda c: money(c['r']))
            + r('Top import', lambda c: esc(c['ti'][0][0]) if c['ti'] else '—') + r('Top export', lambda c: esc(c['te'][0][0]) if c['te'] else '—'))


title = 'Compare Nepal’s trade partners side by side — FY %s' % FY
desc = ('Pick any two countries and compare Nepal’s imports, exports, trade balance, customs revenue, top products and '
        '%d-year trend. Official Department of Customs figures, FY %s.' % (len(YEARS), FY))
bc = [('Home', '/'), ('Trade partners', '/trade-partners'), ('Compare', '')]
opts = lambda sel: ''.join('<option value="%s"%s>%s %s</option>' % (s, ' selected' if s == sel else '', v['f'], esc(v['n'])) for s, v in D.items())
out = [k.page_head(title, desc, '/compare', bc), k.crumb_html(bc)]
out.append('<h1>Compare two of Nepal’s trading partners</h1>'
           '<p class="lede">Choose two countries. The link in your address bar updates, so you can share the exact comparison.</p>'
           '<div class="cmppick"><label>First country<select id="ca">%s</select></label>'
           '<label>Second country<select id="cb">%s</select></label></div>' % (opts(A), opts(B)))
out.append('<div id="cmpbars" class="cmpbars" aria-live="polite"></div>')
out.append('<div class="tbltools"><button type="button" data-act="tcopy">Copy table</button>'
           '<button type="button" data-act="tcsv" data-name="nepal-trade-comparison-fy-%s">Download CSV</button></div>' % FY.replace('/', '-'))
out.append('<div class="tblwrap"><table class="ptbl" id="cmptbl"><thead><tr><th>FY %s</th><th class="r" id="ha">%s</th><th class="r" id="hb">%s</th></tr></thead>'
           '<tbody id="cmpbody">%s</tbody></table></div>' % (FY, esc(D[A]['n']), esc(D[B]['n']), static_rows(A, B)))
out.append('<p class="xlink" id="cmplinks"><b>Full profiles:</b> <a href="/trade-partner/%s">%s</a> · <a href="/trade-partner/%s">%s</a> · '
           '<a href="/trade-partners">all trading partners</a></p>' % (A, esc(D[A]['n']), B, esc(D[B]['n'])))
out.append('<p class="fineprint">“Collected at customs” is the revenue the Department of Customs reports on imports from that country '
           '(customs duty plus other taxes charged at the border). Source: Department of Customs, Nepal — Foreign Trade Statistics FY %s.</p>' % FY)
JS = r'''
(function(){
var D=__DATA__,Y=__YEARS__,TI=__TI__,TE=__TE__,$=function(i){return document.getElementById(i)};
function m(t){var r=Math.abs(t*1000),s;if(r>=1e11)s='Rs '+(r/1e11).toFixed(2)+' kharba';else if(r>=1e9)s='Rs '+(r/1e9).toFixed(2)+' arba';
 else if(r>=1e7)s='Rs '+(r/1e7).toFixed(1)+' crore';else if(r>=1e5)s='Rs '+(r/1e5).toFixed(0)+' lakh';else s='Rs '+r.toFixed(0);return (t<0?'−':'')+s}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function row(l,a,b){var tr=el('tr'),th=el('th',null,l);th.scope='row';tr.appendChild(th);tr.appendChild(el('td','r',a));tr.appendChild(el('td','r',b));return tr}
function bar(label,va,vb,na,nb){var w=el('div','cmprow');w.appendChild(el('div','cmplab',label));var mx=Math.max(va,vb,1);
 [[na,va,'a'],[nb,vb,'b']].forEach(function(x){var r=el('div','cmpbar'),i=el('i',x[2]);i.style.width=Math.max(.6,x[1]/mx*100)+'%';
 r.appendChild(el('span','cmpn',x[0]));var t=el('div','cmptrack');t.appendChild(i);r.appendChild(t);r.appendChild(el('b',null,m(x[1])));w.appendChild(r)});return w}
function draw(){var a=$('ca').value,b=$('cb').value,x=D[a],y=D[b];if(!x||!y)return;
 $('ha').textContent=x.n;$('hb').textContent=y.n;var tb=$('cmpbody');tb.textContent='';
 var p=function(v,t){return (v/t*100).toFixed(1)+'%'};
 tb.appendChild(row('Nepal imports',m(x.i),m(y.i)));tb.appendChild(row('Share of Nepal’s imports',p(x.i,TI),p(y.i,TI)));
 tb.appendChild(row('Nepal exports',m(x.e),m(y.e)));tb.appendChild(row('Share of Nepal’s exports',p(x.e,TE),p(y.e,TE)));
 tb.appendChild(row('Trade balance',m(x.e-x.i),m(y.e-y.i)));tb.appendChild(row('Collected at customs',m(x.r),m(y.r)));
 for(var k=0;k<3;k++)tb.appendChild(row('Import #'+(k+1),x.ti[k]?x.ti[k][0]+' — '+m(x.ti[k][1]):'—',y.ti[k]?y.ti[k][0]+' — '+m(y.ti[k][1]):'—'));
 for(k=0;k<3;k++)tb.appendChild(row('Export #'+(k+1),x.te[k]?x.te[k][0]+' — '+m(x.te[k][1]):'—',y.te[k]?y.te[k][0]+' — '+m(y.te[k][1]):'—'));
 Y.forEach(function(yr,i){if(x.h[i]&&y.h[i])tb.appendChild(row('Imports FY '+yr,m(x.h[i][0]),m(y.h[i][0])))});
 Y.forEach(function(yr,i){if(x.h[i]&&y.h[i])tb.appendChild(row('Exports FY '+yr,m(x.h[i][1]),m(y.h[i][1])))});
 var bx=$('cmpbars');bx.textContent='';bx.appendChild(bar('Nepal imports from',x.i,y.i,x.f+' '+x.n,y.f+' '+y.n));
 bx.appendChild(bar('Nepal exports to',x.e,y.e,x.f+' '+x.n,y.f+' '+y.n));bx.appendChild(bar('Collected at customs',x.r,y.r,x.f+' '+x.n,y.f+' '+y.n));
 var L=$('cmplinks');L.textContent='';L.appendChild(el('b',null,'Full profiles: '));
 [[a,x.n],[b,y.n]].forEach(function(z){var A=el('a',null,z[1]);A.href='/trade-partner/'+z[0];L.appendChild(A);L.appendChild(document.createTextNode(' · '))});
 var A=el('a',null,'all trading partners');A.href='/trade-partners';L.appendChild(A);
 try{history.replaceState(null,'','/compare?a='+a+'&b='+b)}catch(e){}
 document.title='Nepal trade: '+x.n+' vs '+y.n+' — Customs Nepal'}
var q=new URLSearchParams(location.search);if(D[q.get('a')])$('ca').value=q.get('a');if(D[q.get('b')])$('cb').value=q.get('b');
$('ca').addEventListener('change',draw);$('cb').addEventListener('change',draw);draw()})();
'''
JS = (JS.replace('__DATA__', json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
        .replace('__YEARS__', json.dumps(YEARS)).replace('__TI__', repr(timp)).replace('__TE__', repr(texp)))
CSS = ('<style>.cmppick{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:1em 0}'
       '.cmppick label{display:grid;gap:6px;font-size:.82rem;font-weight:600;color:var(--fg2)}'
       '.cmppick select{font:inherit;font-size:1rem;padding:11px 12px;border:1px solid var(--border);border-radius:12px;background:var(--card);color:var(--fg);min-width:0;width:100%}'
       '.cmppick select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}'
       '.cmpbars{display:grid;gap:14px;margin:1em 0 1.4em}.cmprow{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 14px}'
       '.cmplab{font-weight:700;margin-bottom:8px}.cmpbar{display:grid;grid-template-columns:minmax(0,150px) minmax(0,1fr) auto;gap:10px;align-items:center;margin:6px 0;font-size:.9rem}'
       '.cmpn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.cmptrack{height:16px;border-radius:8px;background:var(--border);overflow:hidden}'
       '.cmptrack i{display:block;height:100%;border-radius:8px}.cmptrack i.a{background:var(--v1)}.cmptrack i.b{background:var(--v2)}'
       '.cmpbar b{font-variant-numeric:tabular-nums;white-space:nowrap}'
       '#cmptbl{table-layout:fixed;width:100%}#cmptbl th{text-align:left;width:26%;font-weight:600}#cmptbl thead th.r,#cmptbl td.r{text-align:left;white-space:normal;overflow-wrap:anywhere;vertical-align:top}'
       '@media(max-width:560px){.cmppick{grid-template-columns:minmax(0,1fr)}.cmpbar{grid-template-columns:minmax(0,92px) minmax(0,1fr) auto;font-size:.8rem}}</style>')
foot = k.foot('<b>Trade figures:</b> Department of Customs, Nepal — Foreign Trade Statistics, FY ' + FY + '. Values in Nepali rupees '
              '(1 arba = 1 billion; 1 kharba = 100 billion).')
out.append(CSS + '</div>' + foot.replace('<script src="/cn-tools.js" defer></script>', '<script src="/cn-tools.js" defer></script><script>' + JS + '</script>'))
(pub / 'compare.html').write_text(''.join(out), encoding='utf-8')
print('compare_page: /compare with %d partners; +%d sitemap URL' % (len(D), k.add_to_sitemap(['/compare'])))
