/* Compare two or three economies side by side. Data: /data/compare.json (built by world_prerender.py). No dependencies. */
(function () {
  var root = document.getElementById('cmp'), D = null, MAX = 3;
  var COL = ['var(--exp)', 'var(--imp)', 'var(--fg)'];
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function usd(k) { var v = k * 1000, a = Math.abs(v); if (a >= 1e12) return '$' + (v / 1e12).toFixed(2) + 'T'; if (a >= 1e9) return '$' + (v / 1e9).toFixed(a >= 1e10 ? 0 : 1) + 'B'; if (a >= 1e6) return '$' + (v / 1e6).toFixed(a >= 1e7 ? 0 : 1) + 'M'; return '$' + Math.round(v).toLocaleString('en'); }
  function chg(a, b) { return (!a || !b) ? '—' : (a >= b ? '+' : '−') + Math.abs(100 * (a - b) / b).toFixed(1) + '%'; }
  function pick() { var q = new URLSearchParams(location.search).get('c') || ''; var s = q.split(',').map(function (x) { return x.trim().toLowerCase(); }).filter(function (x) { return D.c[x]; }); return s.slice(0, MAX); }
  function setUrl(sel) { history.replaceState(null, '', sel.length ? '?c=' + sel.join(',') : location.pathname); }
  function chart(sel, key, label) {
    var W = 1000, H = 300, ys = D.years, mx = 1;
    sel.forEach(function (s) { D.c[s][key].forEach(function (v) { if (v > mx) mx = v; }); });
    var px = function (i) { return W * i / (ys.length - 1); }, py = function (v) { return H - (H - 10) * v / mx; };
    var lines = sel.map(function (s, n) { var d = '', pen = false; D.c[s][key].forEach(function (v, i) { if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + px(i).toFixed(1) + ',' + py(v).toFixed(1) + ' '; pen = true; });
      return '<path d="' + d + '" fill="none" stroke="' + COL[n] + '" stroke-width="2.2" vector-effect="non-scaling-stroke"/>'; }).join('');
    var ticks = ys.map(function (y, i) { return (y % 5 === 0) ? '<span style="left:' + (100 * i / (ys.length - 1)).toFixed(1) + '%">' + y + '</span>' : ''; }).join('');
    var grid = ys.map(function (y, i) { return (y % 5 === 0) ? '<line x1="' + px(i).toFixed(1) + '" y1="0" x2="' + px(i).toFixed(1) + '" y2="' + H + '" class="lg"/>' : ''; }).join('');
    var legend = sel.map(function (s, n) { var c = D.c[s], last = c[key][c[key].length - 1]; return '<span><i style="background:' + COL[n] + '"></i>' + esc(c.n) + ': ' + (last == null ? '—' : usd(last)) + ' in ' + ys[ys.length - 1] + '</span>'; }).join('');
    return '<h3>' + label + ', ' + ys[0] + ' to ' + ys[ys.length - 1] + '</h3><div class="lch"><span class="lmx">' + usd(mx) + '</span><svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="' + esc(label) + ' by year for ' + sel.map(function (s) { return esc(D.c[s].n); }).join(', ') + '">' + grid + lines + '</svg><div class="lyr">' + ticks + '</div></div><div class="dvk">' + legend + '</div>';
  }
  function list(title, rows) { return '<h4>' + title + '</h4><ol class="cml">' + rows.map(function (r) { return '<li><span>' + esc(r[0]) + '</span><b>' + r[1] + '%</b></li>'; }).join('') + '</ol>'; }
  function render() {
    var sel = pick(); if (!sel.length) { sel = D.def.slice(); }
    var ly = D.years[D.years.length - 1], opts = D.order.map(function (s) { return '<option value="' + esc(D.c[s].n) + '">'; }).join('');
    var chips = sel.map(function (s, n) { return '<span class="cmc" style="border-color:' + COL[n] + '">' + D.c[s].f + ' ' + esc(D.c[s].n) + '<button type="button" data-rm="' + s + '" aria-label="Remove ' + esc(D.c[s].n) + '">×</button></span>'; }).join('');
    var add = sel.length < MAX ? '<input id="cmadd" list="cmopts" placeholder="Add a country…" aria-label="Add a country to compare" autocomplete="off"><datalist id="cmopts">' + opts + '</datalist>' : '';
    var last = function (a) { return a[a.length - 1]; }, prev = function (a) { return a[a.length - 2]; };
    var rows = [
      ['Exports, ' + ly, function (c) { return usd(last(c.x)); }], ['Change on ' + (ly - 1), function (c) { return chg(last(c.x), prev(c.x)); }],
      ['Imports, ' + ly, function (c) { return usd(last(c.m)); }], ['Change on ' + (ly - 1), function (c) { return chg(last(c.m), prev(c.m)); }],
      ['Balance, ' + ly, function (c) { var b = last(c.x) - last(c.m); return (b >= 0 ? '+' : '−') + usd(Math.abs(b)).slice(1); }],
      ['Export rank', function (c) { return '#' + c.r + ' of ' + D.total; }],
      ['Exports, ' + D.span, function (c) { return c.y ? usd(c.y[0]) : '—'; }], ['Change on a year earlier', function (c) { return c.y ? chg(c.y[0], c.y[1]) : '—'; }],
      ['Exports in ' + D.years[0], function (c) { return c.x[0] == null ? '—' : usd(c.x[0]); }]];
    var tbl = '<div class="dscroll"><table class="dt"><thead><tr><th></th>' + sel.map(function (s) { return '<th class=r><a href="/trade/' + s + '">' + D.c[s].f + ' ' + esc(D.c[s].n) + '</a></th>'; }).join('') + '</tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td>' + r[0] + '</td>' + sel.map(function (s) { return '<td class=r>' + r[1](D.c[s]) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';
    var cols = '<div class="cmg">' + sel.map(function (s, n) { var c = D.c[s];
      return '<div class="cmk" style="border-top-color:' + COL[n] + '"><h3><a href="/trade/' + s + '">' + c.f + ' ' + esc(c.n) + '</a></h3>' + list('Largest markets, ' + ly, c.tx) + list('Largest suppliers, ' + ly, c.tm) + (c.g.length ? list('Largest export groups, ' + D.py, c.g) : '') +
        '<p class="fine"><a href="/trade/' + s + '">Full profile</a> · <a href="/reports/' + c.i + '-trade-brief.pdf">PDF brief</a></p></div>'; }).join('') + '</div>';
    root.innerHTML = '<div class="cmb">' + chips + add + '</div>' + tbl + chart(sel, 'x', 'Exports') + chart(sel, 'm', 'Imports') + cols;
    var inp = document.getElementById('cmadd');
    if (inp) inp.addEventListener('change', function () { var v = inp.value.trim().toLowerCase(); var s = D.order.filter(function (k) { return D.c[k].n.toLowerCase() === v; })[0]; if (s && sel.indexOf(s) < 0) { sel.push(s); setUrl(sel); render(); } });
    root.querySelectorAll('[data-rm]').forEach(function (b) { b.addEventListener('click', function () { var s = sel.filter(function (k) { return k !== b.getAttribute('data-rm'); }); if (!s.length) return; setUrl(s); render(); }); });
    document.title = sel.map(function (s) { return D.c[s].n; }).join(' vs ') + ': trade compared — World Trade Data';
  }
  fetch('/data/compare.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) { D = d; render(); })
    .catch(function () { root.innerHTML = '<p class="fine">The comparison data could not be loaded. Check your connection and <a href="/compare">try again</a>.</p>'; });
})();
