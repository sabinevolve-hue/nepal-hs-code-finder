
(function(){
  var URL_='https://makkuigesutsvetnijtl.supabase.co', KEY_='sb_publishable_BUsiSaEew6X0Q7QKfkshWA_thflc424';
  var sb=null, USER=null, cur='overview';
  function $(s){return document.querySelector(s);}
  function el(t,c,h){var e=document.createElement(t); if(c)e.className=c; if(h!=null)e.innerHTML=h; return e;}
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  var tt; function toast(m){var t=$('#cn-toast'); if(!t)return; t.textContent=m; t.classList.add('on'); clearTimeout(tt); tt=setTimeout(function(){t.classList.remove('on');},2800);}

  var host=el('div',null,''+
    '<div class="cn-toast" id="cn-toast"></div>'+
    '<div class="cn-scrim" id="cn-scrim"><div class="cn-modal">'+
      '<button class="cn-xb" id="cn-mx" aria-label="Close">&times;</button>'+
      '<span class="cn-mark">HS</span><h3>Sign in to Customs Nepal</h3>'+
      '<p class="cn-sub">Save your invoices, estimates and HS codes, on any device.</p>'+
      '<button class="cn-g" id="cn-google"><svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.9 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.2C12.4 13.5 17.7 9.5 24 9.5z"/><path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.1 5.3-4.6 6.9l7.1 5.5C43.3 37.5 46.1 31.6 46.1 24.5z"/><path fill="#FBBC05" d="M10.5 28.6c-.5-1.5-.8-3-.8-4.6s.3-3.1.8-4.6l-7.9-6.2C1 16.4 0 20.1 0 24s1 7.6 2.6 10.8z"/><path fill="#34A853" d="M24 48c6.3 0 11.6-2.1 15.5-5.7l-7.1-5.5c-2 1.3-4.6 2.1-8.4 2.1-6.3 0-11.6-4-13.5-9.9l-7.9 6.2C6.5 42.6 14.6 48 24 48z"/></svg> Continue with Google</button>'+
      '<div class="cn-div">or</div>'+
      '<input type="email" id="cn-email" placeholder="you@company.com" autocomplete="email">'+
      '<button class="cn-ml" id="cn-magic">Email me a magic link</button>'+
      '<p class="cn-fine">The site stays free and open. You only sign in to save your work.</p>'+
    '</div></div>'+
    '<div class="cn-dash" id="cn-dash">'+
      '<aside class="cn-side" id="cn-side">'+
        '<div class="cn-brand"><span class="m">HS</span> Customs Nepal</div>'+
        '<nav class="cn-nav" id="cn-navm">'+
          '<button data-p="overview" class="on">Dashboard</button>'+
          '<button data-p="invoices">My Invoices</button>'+
          '<button data-p="estimates">My Estimates</button>'+
          '<button data-p="codes">Saved HS Codes</button>'+
          '<button data-p="account">Account</button>'+
        '</nav>'+
        '<div class="cn-foot"><div class="em" id="cn-em"></div><button class="cn-out" id="cn-out">Sign out</button></div>'+
      '</aside>'+
      '<div class="cn-main">'+
        '<div class="cn-top"><button class="cn-burger" id="cn-burger">&#9776;</button><h2 id="cn-title">Dashboard</h2><button class="cn-close" id="cn-dclose">Back to site</button></div>'+
        '<div class="cn-body" id="cn-panel"></div>'+
      '</div>'+
    '</div>');
  document.body.appendChild(host);

  var slot=null; try{ slot=document.querySelector('.bar-row').lastElementChild; }catch(e){}
  var hbtn=el('button','cn-signin','Sign in'); hbtn.id='cn-hdr';
  if(slot) slot.appendChild(hbtn);
  hbtn.addEventListener('click', function(){ if(USER) openDash(); else openModal(); });
  function updateHeader(){ if(USER){ hbtn.className='cn-av'; hbtn.textContent=(USER.email||'?').slice(0,1).toUpperCase(); hbtn.title=USER.email; } else { hbtn.className='cn-signin'; hbtn.textContent='Sign in'; hbtn.title='Sign in'; } }

  function openModal(){ $('#cn-scrim').classList.add('on'); }
  function closeModal(){ $('#cn-scrim').classList.remove('on'); }
  $('#cn-mx').addEventListener('click', closeModal);
  $('#cn-scrim').addEventListener('click', function(e){ if(e.target===this) closeModal(); });

  function openDash(noPush){ $('#cn-dash').classList.add('on'); $('#cn-em').textContent=USER?USER.email:''; select(cur); try{ if(!noPush && location.pathname!=='/account') history.pushState(null,'','/account'); }catch(e){} }
  function closeDash(){ $('#cn-dash').classList.remove('on'); $('#cn-side').classList.remove('open'); try{ if(location.pathname==='/account') history.replaceState(null,'','/'); }catch(e){} }
  $('#cn-dclose').addEventListener('click', closeDash);
  $('#cn-burger').addEventListener('click', function(){ $('#cn-side').classList.toggle('open'); });
  var TT={overview:'Dashboard',invoices:'My Invoices',estimates:'My Estimates',codes:'Saved HS Codes',account:'Account'};
  $('#cn-navm').addEventListener('click', function(e){ var b=e.target.closest('button[data-p]'); if(!b)return; select(b.dataset.p); $('#cn-side').classList.remove('open'); });
  function select(p){ cur=p; $('#cn-title').textContent=TT[p]; var ch=$('#cn-navm').children; for(var i=0;i<ch.length;i++) ch[i].classList.toggle('on',ch[i].dataset.p===p); render(p); }

  function date(s){ try{ return new Date(s).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}); }catch(e){ return ''; } }
  function count(t){ return sb.from(t).select('id',{count:'exact',head:true}).then(function(r){ return r.count||0; }, function(){ return 0; }); }
  function tbl(h,body){ return '<div class="cn-card"><div class="cn-tw"><table class="cn-tbl"><thead><tr>'+h.map(function(x){return '<th>'+x+'</th>';}).join('')+'</tr></thead><tbody>'+body+'</tbody></table></div></div>'; }
  function render(p){
    var box=$('#cn-panel'); if(!sb){ box.innerHTML='<div class="cn-empty">Loading...</div>'; return; }
    if(p==='account'){ box.innerHTML='<div class="cn-card"><h3>Profile</h3><div style="padding:15px 16px"><div style="color:var(--muted);font-size:.77rem">Email</div><div style="font-weight:600;margin-top:3px">'+esc(USER.email)+'</div></div></div><p style="color:var(--muted);font-size:.83rem;margin-top:14px">Your saved items are private to your account and protected by row-level security. Sign out and back in on any device to see them.</p>'; return; }
    box.innerHTML='<div class="cn-empty">Loading...</div>';
    if(p==='overview'){ Promise.all([count('invoices'),count('estimates'),count('saved_codes')]).then(function(r){ box.innerHTML='<div class="cn-tiles"><div class="cn-tile"><div class="k">Saved invoices</div><div class="v">'+r[0]+'</div></div><div class="cn-tile"><div class="k">Estimates</div><div class="v">'+r[1]+'</div></div><div class="cn-tile"><div class="k">Saved HS codes</div><div class="v">'+r[2]+'</div></div></div><p style="color:var(--muted);font-size:.86rem">Use the menu to open your saved work. Save a new invoice from the <b>Invoice</b> tab, then "Save to my account".</p>'; }); return; }
    var table=(p==='codes')?'saved_codes':p;
    sb.from(table).select('*').order('created_at',{ascending:false}).then(function(res){
      if(res.error){ box.innerHTML='<div class="cn-card"><div class="cn-empty">Could not load: '+esc(res.error.message)+'</div></div>'; return; }
      var rows=res.data||[];
      if(!rows.length){ box.innerHTML='<div class="cn-card"><div class="cn-empty">Nothing saved here yet.</div></div>'; return; }
      if(p==='invoices'){ box.innerHTML=tbl(['No.','Buyer','Total','Date',''],rows.map(function(x){ var curc=(x.data&&x.data.shipment&&x.data.shipment.currency)||''; return '<tr><td class="mono">'+esc(x.pi_no||'-')+'</td><td>'+esc(x.buyer||'-')+'</td><td>'+esc(curc+' '+(x.total!=null?Number(x.total).toLocaleString():'-'))+'</td><td>'+date(x.created_at)+'</td><td style="text-align:right"><button class="cn-mini" data-open="'+x.id+'">Open</button><button class="cn-mini danger" data-del="invoices:'+x.id+'">Delete</button></td></tr>'; }).join('')); }
      else if(p==='estimates'){ box.innerHTML=tbl(['Ref','Product','HS','Landed',''],rows.map(function(x){ return '<tr><td class="mono">'+esc(x.ref||'-')+'</td><td>'+esc(x.product||'-')+'</td><td class="mono">'+esc(x.hs||'-')+'</td><td>'+esc(x.landed!=null?Number(x.landed).toLocaleString():'-')+'</td><td style="text-align:right"><button class="cn-mini danger" data-del="estimates:'+x.id+'">Delete</button></td></tr>'; }).join('')); }
      else { box.innerHTML=tbl(['Code','Description','Duty',''],rows.map(function(x){ return '<tr><td class="mono">'+esc(x.code)+'</td><td>'+esc(x.description||'')+'</td><td>'+esc((x.gen||'')+(x.saarc?' / '+x.saarc:''))+'</td><td style="text-align:right"><button class="cn-mini" data-code="'+esc(x.code)+'">View</button><button class="cn-mini danger" data-del="saved_codes:'+x.id+'">Delete</button></td></tr>'; }).join('')); }
      wire(rows);
    });
  }
  function wire(rows){
    var box=$('#cn-panel');
    var d=box.querySelectorAll('[data-del]'); for(var i=0;i<d.length;i++){ (function(b){ b.addEventListener('click',function(){ var pr=b.dataset.del.split(':'); sb.from(pr[0]).delete().eq('id',pr[1]).then(function(r){ if(r.error) toast('Delete failed'); else { toast('Deleted'); render(cur); } }); }); })(d[i]); }
    var o=box.querySelectorAll('[data-open]'); for(var j=0;j<o.length;j++){ (function(b){ b.addEventListener('click',function(){ var row=null; for(var k=0;k<rows.length;k++) if(rows[k].id===b.dataset.open) row=rows[k]; if(row&&row.data&&window.CN&&window.CN.applyExtracted){ try{ window.CN.applyExtracted(row.data); window.CN.go('invoice'); closeDash(); toast('Loaded into the invoice generator'); }catch(e){ toast('Could not open'); } } }); })(o[j]); }
    var c=box.querySelectorAll('[data-code]'); for(var m=0;m<c.length;m++){ (function(b){ b.addEventListener('click',function(){ if(window.CN&&window.CN.openDetail){ try{ window.CN.openDetail(b.dataset.code); closeDash(); }catch(e){} } }); })(c[m]); }
  }

  var saveBtn=document.getElementById('inv-save');
  if(saveBtn) saveBtn.addEventListener('click', function(){
    if(!sb){ toast('Sign-in is still loading, try again in a moment'); return; }
    if(!USER){ openModal(); toast('Sign in to save your work'); return; }
    var dd; try{ dd=window.CN.invData(); }catch(e){ toast('Nothing to save'); return; }
    if(!dd.items||!dd.items.length){ toast('Add at least one line item first'); return; }
    var tot=0; try{ dd.items.forEach(function(it){ tot+=(it.qty||0)*(it.unitPrice||0); }); }catch(e){}
    sb.from('invoices').insert({ pi_no:(dd.shipment&&dd.shipment.piNo)||null, buyer:(dd.buyer&&dd.buyer.name)||null, goods:(dd.items[0]&&dd.items[0].description)||'', total:tot||null, status:dd.docType||'draft', data:dd }).then(function(r){ if(r.error) toast('Save failed: '+r.error.message); else toast('Saved to your account'); });
  });

  function boot(){ try{
    sb=window.supabase.createClient(URL_,KEY_);
    sb.auth.getSession().then(function(r){ USER=(r.data&&r.data.session&&r.data.session.user)||null; updateHeader(); if(location.pathname==='/account'){ if(USER) openDash(true); else openModal(); } });
    sb.auth.onAuthStateChange(function(_e,s){ var was=!!USER; USER=(s&&s.user)||null; updateHeader(); if(USER&&!was&&_e==='SIGNED_IN'){ closeModal(); toast('Signed in'); track('login', { method: (s.user && s.user.app_metadata && s.user.app_metadata.provider) || 'email' }); } });
  }catch(e){} }
  $('#cn-google').addEventListener('click', function(){ if(!sb){ toast('Still loading'); return; } sb.auth.signInWithOAuth({provider:'google',options:{redirectTo:location.origin}}).then(function(r){ if(r&&r.error){ var m=(r.error.message||'').toLowerCase(); if(m.indexOf('provider')>-1||m.indexOf('not enabled')>-1||m.indexOf('unsupported')>-1) toast('Google sign-in is being set up. Please use the email magic link for now.'); else toast(r.error.message); } }).catch(function(){ toast('Google sign-in is being set up. Please use the email magic link for now.'); }); });
  $('#cn-magic').addEventListener('click', function(){ if(!sb){ toast('Still loading'); return; } var em=($('#cn-email').value||'').trim(); if(!em){ $('#cn-email').focus(); return; } sb.auth.signInWithOtp({email:em,options:{emailRedirectTo:location.origin}}).then(function(r){ if(r.error) toast(r.error.message); else toast('Check your email for the sign-in link'); }); });
  $('#cn-out').addEventListener('click', function(){ if(sb) sb.auth.signOut(); closeDash(); toast('Signed out'); });

  var s=document.createElement('script'); s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2'; s.onload=boot; s.onerror=function(){}; document.head.appendChild(s);
})();
