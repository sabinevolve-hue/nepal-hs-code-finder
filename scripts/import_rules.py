"""/import-rules — which authority to ask before importing a product into Nepal, by HS code.

One static page with a small lookup (chapter and heading rules from permits_data.py, embedded as JSON) and the same
rules as a table with the source of each. It also adds a one-line pointer to every product page whose heading or
chapter has a rule. Runs after product_pages.py. Stdlib only.

The page never says a product needs no permit: where no rule matches it says the page has nothing on that code.
"""
import json, re
import pagekit as k
from pagekit import esc, pub
from permits_data import RULES, BY_KEY, CH, HD, NOT_COVERED, CHECKED, rules_for

KIND = {'law': 'Law', 'official': 'Official page', 'reported': 'Reported'}
ext = lambda url, label: '<a href="%s" target="_blank" rel="noopener noreferrer nofollow">%s</a>' % (esc(url), esc(label))

title = 'Import permits in Nepal: which authority, by HS code'
desc = ('Enter an HS code to see which Nepali authority to ask before importing: plant and animal quarantine, DFTQC for food, '
        'DDA for medicines, NTA for phones, NBSM for standards. Each rule shows its source.')
bc = [('Home', '/'), ('Import permits', '')]
faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": "What is an EXIM code in Nepal?",
     "acceptedAnswer": {"@type": "Answer", "text": "An Export Import (EXIM) code is the registration required for a person importing or "
                        "exporting goods from Nepal. It is issued by the Department of Customs and applied for through the Nepal "
                        "National Single Window (nnsw.gov.np)."}},
    {"@type": "Question", "name": "Which imports into Nepal need a permit from another authority?",
     "acceptedAnswer": {"@type": "Answer", "text": "Plants and plant products need an entry permit from a plant quarantine office. Animals "
                        "and animal products must enter through an Animal Quarantine Check Post. Medicines must be registered with the "
                        "Department of Drug Administration before import. Other goods have their own rules; confirm with the authority "
                        "and the Department of Customs before shipping."}}]}

out = [k.page_head(title, desc, '/import-rules', bc, extra_ld=[faq]), k.crumb_html(bc)]
out.append('<h1>Do I need a permit to import this into Nepal?</h1>')
out.append('<p class="lede">Customs duty is one question. Whether another authority has to approve the goods first is a separate one. '
           'Enter an HS code to see which authority to ask, and where that rule comes from.</p>')
out.append('<form class="trkbox" id="irform" role="search" aria-label="Find the authority for an HS code">'
           '<input id="irin" type="search" inputmode="numeric" autocomplete="off" spellcheck="false" '
           'placeholder="HS code, for example 0803 or 3004.90.00" aria-label="HS code">'
           '<button type="submit" class="trkgo">Find authority</button></form>'
           '<div id="irresult" class="trkresult" aria-live="polite"></div>'
           '<p class="trkhint">Don’t know the code? <a href="/">Search by product name</a> first.</p>')

out.append('<h2 class="sec">Every commercial import</h2><div class="guidegrid">'
           '<div class="chcard irc"><span class="t">EXIM code</span><span class="c">The registration required for anyone importing or exporting goods. '
           'Issued by the Department of Customs; apply through the %s.</span></div>'
           '<div class="chcard irc"><span class="t">Permits go through one portal</span><span class="c">Licences, permits and certificates from '
           'government agencies are applied for on the Nepal National Single Window. The system does not allow more goods than the agency approved.</span></div>'
           '<div class="chcard irc"><span class="t">Customs declaration</span><span class="c">Duty and 13%% VAT are paid on declaration. '
           'See the rate for your product in <a href="/import-duty">import duty by product</a> or work it out in the <a href="/calculator">calculator</a>.</span></div>'
           '</div><p class="trkhint">Source for the first two: %s, read %s.</p>'
           % (ext('https://nnsw.gov.np', 'Nepal National Single Window'),
              ext('https://nnsw.gov.np/trade/adminFaq/list', 'NNSW frequently asked questions'), CHECKED))

rows = []
for r in RULES:
    rows.append('<tr id="r-%s"><td><b>%s</b></td><td>%s</td><td>%s</td><td><span class="irk irk-%s">%s</span> %s %s</td></tr>'
                % (r['key'], esc(r['goods']), ext(r['url'], r['who']), esc(r['what']), r['kind'], KIND[r['kind']],
                   esc(r['basis']), ext(r['src'], r['srcname'])))
out.append('<h2 class="sec">Who controls what</h2>'
           '<p>The rules this page knows, each with where it was read. “Reported” means a news report or a foreign government guide, '
           'not the authority’s own text.</p>'
           '<div class="tscroll" tabindex="0" role="region" aria-label="Import rules by product group"><table class="tbl irt"><thead><tr>'
           '<th>Goods</th><th>Authority</th><th>What the rule says</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(rows))

out.append('<h2 class="sec">What this page does not cover</h2>'
           '<div class="note">These goods have rules of their own that this page has not tied to a source yet: <b>%s</b>. '
           'Some goods are also banned or limited by government notice, and that list changes. '
           'If the checker shows nothing for your code, that is not a statement that no permit is needed. '
           'Ask the %s or your customs agent before you pay a supplier.</div>'
           % (esc(', '.join(NOT_COVERED)), ext('https://customs.gov.np', 'Department of Customs')))
out.append('<div class="tools"><a class="btn" href="/import-duty">Import duty by product</a>'
           '<a class="btn ghost" href="/calculator">Landed-cost calculator</a><a class="btn ghost" href="/shipping">Shipping to Nepal</a></div>')
out.append('<style>.irc{cursor:default}.irt td:first-child{min-width:150px}.irt td:nth-child(3){min-width:220px}.irt td:nth-child(4){min-width:200px;font-size:.84rem;color:var(--fg-2)}'
           '.irk{display:inline-block;font-size:.7rem;font-weight:600;padding:1px 7px;border-radius:6px;border:1px solid var(--border);color:var(--fg-2);margin-right:4px;white-space:nowrap}'
           '.trkresult{min-height:0}.irsrc{display:block;font-size:.78rem;color:var(--muted);margin-top:2px}.irn a{font-weight:600}.irsrc a,.irn a,.irt a,.irc a,.trktl-m a{text-decoration:underline}</style>')

DATA = {'R': {r['key']: {x: r[x] for x in ('goods', 'who', 'url', 'what', 'basis', 'kind')} for r in RULES}, 'CH': CH, 'HD': HD, 'K': KIND}
out.append("""<script>
(function(){
 var D=%s;
 function esc(s){var d=document.createElement('div');d.textContent=(s==null?'':s);return d.innerHTML;}
 function keys(cn){var o=[];(D.HD[cn.slice(0,4)]||[]).concat(D.CH[String(parseInt(cn.slice(0,2),10))]||[]).forEach(function(x){if(o.indexOf(x)<0)o.push(x);});return o;}
 function render(raw){
  var box=document.getElementById('irresult'),cn=String(raw||'').replace(/[^0-9]/g,'');
  if(!cn){box.innerHTML='';return;}
  if(cn.length<4){box.innerHTML='<div class="trkcard warn"><p class="trkhdr">Enter at least the first four digits of the HS code.</p></div>';return;}
  var ks=keys(cn),h;
  if(ks.length){
   h='<div class="trkcard"><p class="trkhdr">HS '+esc(cn.slice(0,4))+': ask '+(ks.length>1?'these authorities':'this authority')+' before you ship</p><ol class="trktl-list">';
   ks.forEach(function(x){var r=D.R[x];
    h+='<li><span class="trktl-m"><a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer nofollow">'+esc(r.who)+'</a></span>'
      +'<span class="trktl-l">'+esc(r.what)+'</span><span class="irsrc">'+esc(D.K[r.kind])+': '+esc(r.basis)+' <a href="#r-'+x+'">Source</a></span></li>';});
   h+='</ol><p class="trkhint">A rule applies only if your goods match its description. Other rules may apply that this page does not list.</p></div>';
  }else{
   h='<div class="trkcard warn"><p class="trkhdr">This page has no rule for HS '+esc(cn.slice(0,4))+'</p>'
    +'<p class="trkhint">That is not a statement that no permit is needed. See <a href="#r-plant">the rules it does cover</a> and what it leaves out, and confirm with the Department of Customs.</p></div>';
  }
  box.innerHTML=h;
  if(window.gtag){try{gtag('event','import_rules_lookup',{matched:ks.length});}catch(e){}}
 }
 var f=document.getElementById('irform'),i=document.getElementById('irin');
 f.addEventListener('submit',function(e){e.preventDefault();render(i.value);});
 function fromHash(){var m=/^#hs=([0-9.]+)$/.exec(location.hash);if(m){i.value=m[1];render(m[1]);}}
 window.addEventListener('hashchange',fromHash);fromHash();
})();
</script>""" % json.dumps(DATA, ensure_ascii=False).replace('</', '<\\/'))
out.append(k.foot('<b>Reference only.</b> Rules were read on %s from the sources linked in the table; they change, and the authority named '
                  'decides. Confirm with it and with the Department of Customs before you ship or pay.' % CHECKED))
(pub / 'import-rules.html').write_text(''.join(out), encoding='utf-8')

# one-line pointer on each product page that has a rule
MARK = '<h2 class="sec">Landed cost'
n = 0
for f in (pub / 'import-duty').glob('*.html'):
    m = re.search(r'-(\d{8})\.html$', f.name)
    if not m:
        continue
    ks = rules_for(m.group(1))
    if not ks:
        continue
    s = f.read_text(encoding='utf-8')
    if 'class="note irn"' in s or MARK not in s:
        continue
    who = ' and '.join(esc(BY_KEY[x]['who']) for x in ks[:2]) + (' and others' if len(ks) > 2 else '')
    note = ('<div class="note irn"><b>Before you ship:</b> goods under heading %s may need approval from the %s. '
            '<a href="/import-rules#hs=%s">See the import rule and its source</a></div>' % (m.group(1)[:4], who, m.group(1)[:4]))
    f.write_text(s.replace(MARK, note + MARK, 1), encoding='utf-8')
    n += 1
print('import_rules: /import-rules (%d rules); note on %d product pages; +%d sitemap URL' % (len(RULES), n, k.add_to_sitemap(['/import-rules'])))
