(function(){
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
  var p0=fig.getAttribute('data-pad')==='0',pad=p0?0:24,head=p0?0:(bare?16:50),foot=p0?0:(bare?12:38),S=2,fs=getComputedStyle(fig),body=getComputedStyle(document.body);
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
  else if(act==='pngsib'){var w=b.closest('.cpshare');var f2=w&&w.querySelector('.vzfig');if(f2)png(f2,b)}
  else if(act==='tcopy'||act==='tcsv'){var t=nextTable(b.parentNode);if(!t)return;var r=rows(t);
    if(act==='tcopy'){copy(r.map(function(x){return x.join('\t')}).join('\n'),b)}
    else{var csv=r.map(function(x){return x.map(function(c){return '"'+c.replace(/"/g,'""')+'"'}).join(',')}).join('\r\n');
      save((b.getAttribute('data-name')||'table')+'.csv',new Blob(['﻿'+csv],{type:'text/csv;charset=utf-8'}));flash(b,'Downloaded ✓')}}
});
var rm=window.matchMedia&&matchMedia('(prefers-reduced-motion:reduce)').matches;
if(rm){[].forEach.call(document.querySelectorAll('animateMotion'),function(a){var t=a.parentNode;if(t&&t.parentNode)t.parentNode.removeChild(t)})}
else{[].forEach.call(document.querySelectorAll('[data-count]'),function(el){var t=el.textContent,m=t.match(/[\d.]+/);if(!m)return;
  var n=parseFloat(m[0]),d=(m[0].split('.')[1]||'').length,t0=null;
  function f(ts){if(!t0)t0=ts;var p=Math.min(1,(ts-t0)/900),e=1-Math.pow(1-p,3);el.textContent=t.replace(m[0],(n*e).toFixed(d));if(p<1)requestAnimationFrame(f);else el.textContent=t}
  requestAnimationFrame(f)})}
})();
