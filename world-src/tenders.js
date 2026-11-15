/* Tender notices from World Bank-financed projects. Reads /api/wb-notices, which vercel.json forwards to the World Bank's
   public procurement-notices API (the API sends no cross-origin header, so the browser cannot call it directly).
   Only the fields listed in FL are requested: contact names, emails and phone numbers are never loaded. No dependencies. */
(function () {
  var root = document.getElementById('tnd'); if (!root) return;
  var API = '/api/wb-notices', ROWS = 50;
  var FL = 'id,notice_type,noticedate,submission_deadline_date,project_ctry_name,project_name,bid_description,procurement_group';
  var OPEN = ['Invitation for Bids', 'Request for Expression of Interest', 'Invitation for Prequalification', 'General Procurement Notice'];
  var GROUPS = { GO: 'Goods', CW: 'Works', CS: 'Consulting services', NC: 'Non-consulting services' };
  var st = { country: '', group: '', q: '', os: 0, total: 0, rows: [], openOnly: true };
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function day(s) { var d = s ? new Date(s) : null; return d && !isNaN(d) ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '—'; }
  function url(extra) {
    var p = ['format=json', 'apilang=en', 'srt=submission_date', 'order=desc', 'fl=' + FL, 'notice_type_exact=' + encodeURIComponent(OPEN.join('^'))];
    if (st.country) p.push('project_ctry_name_exact=' + encodeURIComponent(st.country));
    if (st.group) p.push('procurement_group_exact=' + st.group);
    if (st.q) p.push('qterm=' + encodeURIComponent(st.q));
    return API + '?' + p.concat(extra || []).join('&');
  }
  function get(u) { return fetch(u, { headers: { Accept: 'application/json' } }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }); }
  function card(n) {
    var dl = n.submission_deadline_date ? new Date(n.submission_deadline_date) : null, closed = dl && dl < new Date(new Date().toISOString().slice(0, 10));
    return '<li class="tn' + (closed ? ' closed' : '') + '"><a href="https://projects.worldbank.org/en/projects-operations/procurement-detail/' + encodeURIComponent(n.id) + '" target="_blank" rel="noopener nofollow">'
      + '<b>' + esc(n.bid_description || n.project_name || n.id) + '</b></a>'
      + '<span class="tn-m">' + esc(n.project_ctry_name || '') + ' · ' + esc(n.notice_type || '') + (GROUPS[n.procurement_group] ? ' · ' + GROUPS[n.procurement_group] : '') + '</span>'
      + (n.project_name ? '<span class="tn-p">Project: ' + esc(n.project_name) + '</span>' : '')
      + '<span class="tn-d">Published ' + esc(n.noticedate ? n.noticedate.replace(/-/g, ' ') : '—') + ' · ' + (dl ? (closed ? 'Deadline passed ' : 'Deadline ') + day(n.submission_deadline_date) : 'No deadline stated') + '</span></li>';
  }
  function list() {
    var box = document.getElementById('tnd-list'), rows = st.rows.filter(function (n) {
      if (!st.openOnly) return true; var d = n.submission_deadline_date ? new Date(n.submission_deadline_date) : null; return !d || d >= new Date(new Date().toISOString().slice(0, 10)); });
    if (!st.rows.length) { box.innerHTML = '<p class="tmsg">No notices match. Try another country, a different category or fewer words.</p>'; return; }
    box.innerHTML = '<p class="fine">' + st.total.toLocaleString('en') + ' notices match; showing the ' + st.rows.length.toLocaleString('en') + ' most recent' + (st.openOnly ? ', ' + rows.length + ' of them still open' : '') + '.</p>'
      + (rows.length ? '<ul class="tnl">' + rows.map(card).join('') + '</ul>' : '<p class="tmsg">None of the most recent notices is still open. Untick “Open only” to see them, or load more.</p>')
      + (st.rows.length < st.total ? '<p><button type="button" class="tbtn" id="tnd-more">Load more</button></p>' : '');
    var m = document.getElementById('tnd-more'); if (m) m.onclick = function () { load(true); };
  }
  function load(more) {
    var box = document.getElementById('tnd-list'); if (!more) { st.os = 0; st.rows = []; box.innerHTML = '<p class="tmsg">Loading notices…</p>'; }
    else { var b = document.getElementById('tnd-more'); if (b) { b.disabled = true; b.textContent = 'Loading…'; } }
    get(url(['rows=' + ROWS, 'os=' + st.os])).then(function (d) {
      var rows = d.procnotices || []; if (!Array.isArray(rows)) rows = Object.keys(rows).map(function (k) { return rows[k]; });
      st.total = +d.total || 0; st.rows = st.rows.concat(rows); st.os += ROWS; list();
    }).catch(function () {
      box.innerHTML = '<p class="tmsg">The World Bank notice service did not answer. <button type="button" class="tbtn" id="tnd-retry">Try again</button> or open the <a href="https://projects.worldbank.org/en/projects-operations/procurement" target="_blank" rel="noopener">World Bank procurement page</a>.</p>';
      document.getElementById('tnd-retry').onclick = function () { load(false); };
    });
  }
  function build(countries) {
    var q = new URLSearchParams(location.search); st.country = q.get('country') || ''; st.group = q.get('type') || ''; st.q = q.get('q') || '';
    root.innerHTML = '<form class="tf" id="tnd-f"><label>Country<select id="tnd-c"><option value="">All countries</option>' + countries.map(function (c) { return '<option' + (c === st.country ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') + '</select></label>'
      + '<label>Category<select id="tnd-g"><option value="">All categories</option>' + Object.keys(GROUPS).map(function (g) { return '<option value="' + g + '"' + (g === st.group ? ' selected' : '') + '>' + GROUPS[g] + '</option>'; }).join('') + '</select></label>'
      + '<label>Words in the notice<input id="tnd-q" type="search" maxlength="80" placeholder="for example: solar, medical equipment" value="' + esc(st.q) + '"></label>'
      + '<label class="tck"><input id="tnd-o" type="checkbox" checked> Open only</label><button class="tbtn" type="submit">Search</button></form><div id="tnd-list" aria-live="polite"></div>';
    var go = function () {
      st.country = document.getElementById('tnd-c').value; st.group = document.getElementById('tnd-g').value; st.q = document.getElementById('tnd-q').value.trim().slice(0, 80);
      var p = []; if (st.country) p.push('country=' + encodeURIComponent(st.country)); if (st.group) p.push('type=' + st.group); if (st.q) p.push('q=' + encodeURIComponent(st.q));
      history.replaceState(null, '', p.length ? '?' + p.join('&') : location.pathname); load(false);
    };
    document.getElementById('tnd-f').onsubmit = function (e) { e.preventDefault(); go(); };
    document.getElementById('tnd-c').onchange = go; document.getElementById('tnd-g').onchange = go;
    document.getElementById('tnd-o').onchange = function () { st.openOnly = this.checked; list(); };
    load(false);
  }
  get(API + '?format=json&rows=0&fct=project_ctry_name_exact&notice_type_exact=' + encodeURIComponent(OPEN.join('^'))).then(function (d) {
    var f = (d.facets || {}).project_ctry_name_exact || {}; build(Object.keys(f).map(function (k) { return f[k].name; }).filter(Boolean).sort());
  }).catch(function () { build([]); });
})();
