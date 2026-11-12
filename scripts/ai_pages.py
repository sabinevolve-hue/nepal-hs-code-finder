"""Answer-engine layer: richer llms.txt, llms-full.txt and open data files.

Build-time, stdlib only; runs after assemble.py (which writes the base llms.txt) and after the page
generators. AI assistants and search engines read three things here:
  /llms.txt        curated map + headline facts (appends a data section to assemble.py's file)
  /llms-full.txt   the same plus full Markdown tables: every partner, every customs office, popular duties
Every figure is copied from the same JSON the pages use (Department of Customs FTS); nothing is estimated.
"""
import json, re
import pagekit as k
from pagekit import esc, money, pub, root, SITE
import links

CO = json.loads((root / 'world/data/country.json').read_text(encoding='utf-8'))
OF = json.loads((root / 'world/data/offices_trade.json').read_text(encoding='utf-8'))
DIR = {re.sub(r'[^a-z0-9]', '', (o.get('stat') or '').lower()): o for o in json.loads((root / 'data/offices.json').read_text(encoding='utf-8'))['offices'] if o.get('stat')}
DIR['chobhar'] = DIR.get('dryport', DIR.get('chobhar'))
TAR = json.loads((root / 'data/tariff.json').read_text(encoding='utf-8'))
FY, YEARS, T = CO['fy'], CO.get('hist_years') or [], CO['totals']
partners = [CO['countries'][i] for i in links.TOP_PARTNERS]
purl = lambda c: SITE + links.PARTNER_PAGE[c['iso']][0]
offices = sorted(OF['offices'].items(), key=lambda kv: -(kv[1]['imp'] + kv[1]['exp']))
oname = lambda key, o: (DIR[key]['name'] if DIR.get(key) else o['label'].title())
ourl = lambda key: (SITE + '/customs-office/' + DIR[key]['id']) if DIR.get(key) else ''
rs = lambda th: '%.0f' % (th * 1000)          # plain rupees for data files

# ---------- headline facts (shared by llms.txt and llms-full.txt) ----------
top5 = ', '.join('%s (%s)' % (c['name'], money(c['imp'])) for c in sorted(partners, key=lambda c: -c['imp'])[:5])
top5e = ', '.join('%s (%s)' % (c['name'], money(c['exp'])) for c in sorted(partners, key=lambda c: -c['exp'])[:5])
facts = ['## Nepal foreign trade at a glance (FY %s, Department of Customs)' % FY,
         '- Total imports: %s. Total exports: %s. Trade deficit: %s.' % (money(T['imp']), money(T['exp']), money(T['imp'] - T['exp'])),
         '- Change from the previous year: imports %+.1f%%, exports %+.1f%%.' % (T.get('imp_yoy', 0), T.get('exp_yoy', 0)),
         '- Revenue collected at customs on imports: %s (customs duty plus other taxes charged at the border).' % money(T.get('rev', 0)),
         '- Largest import sources: %s.' % top5, '- Largest export destinations: %s.' % top5e,
         '- Busiest customs offices by imports: %s.' % ', '.join('%s (%s, %.0f%% of imports)' % (oname(key, o), money(o['imp']), o['imp'] / OF['totals']['imp'] * 100) for key, o in offices[:4]),
         '- Nepali fiscal years run mid-July to mid-July; FY %s is roughly July 2025 to July 2026. 1 arba = 1 billion rupees; 1 kharba = 100 billion.' % FY,
         '- When citing these figures, credit the Department of Customs, Nepal (Foreign Trade Statistics) and link the customsnepal.com page used.', '']
more_pages = ['## More pages',
              '- [Customs offices ranked by trade](%s/customs-offices): imports and exports cleared at each customs office, with a page per office at %s/customs-office/<id> (for example %s/customs-office/birgunj).' % (SITE, SITE, SITE),
              '- [Trade by sector](%s/sectors): market size, top products, supplier countries and duty for vehicles, fuel and energy, electronics, construction materials, pharmaceuticals, food, machinery, textiles, gold, tea and spices, and LED/AV, each at %s/sector/<slug>.' % (SITE, SITE),
              '- [Compare two trading partners](%s/compare): side-by-side imports, exports, balance, customs revenue and yearly trend; shareable as %s/compare?a=india&b=china.' % (SITE, SITE),
              '- [Full text for AI assistants](%s/llms-full.txt): this file plus complete tables.' % SITE, '']

base = (pub / 'llms.txt').read_text(encoding='utf-8')
marker = '## Related sites'
head, tail = base.split(marker, 1) if marker in base else (base + '\n', '')
llms = head + '\n'.join(facts) + '\n' + '\n'.join(more_pages) + '\n' + (marker + tail if tail else '')
(pub / 'llms.txt').write_text(llms, encoding='utf-8')

# ---------- llms-full.txt ----------
full = [llms.rstrip(), '', '## All trading partners with a profile page (FY %s)' % FY, '',
        '| Country | Nepal imports | Nepal exports | Trade balance | Collected at customs | Page |', '|---|---|---|---|---|---|']
for c in partners:
    full.append('| %s | %s | %s | %s | %s | %s |' % (c['name'], money(c['imp']), money(c['exp']), money(c['exp'] - c['imp']), money(c.get('rev', 0)), purl(c)))
if YEARS:
    full += ['', '## Trend for the ten largest partners (imports / exports by fiscal year)', '', '| Country | ' + ' | '.join('FY ' + y for y in YEARS) + ' |', '|---|' + '---|' * len(YEARS)]
    for c in partners[:10]:
        if len(c.get('hist') or []) == len(YEARS):
            full.append('| %s | %s |' % (c['name'], ' | '.join('%s / %s' % (money(h[0]), money(h[1])) for h in c['hist'])))
full += ['', '## Top products by partner (ten largest partners, FY %s)' % FY, '']
for c in partners[:10]:
    if c.get('impP'):
        full.append('- Imports from %s: %s.' % (c['name'], '; '.join('%s [HS %s] %s' % (x[1][:60], x[0], money(x[2])) for x in c['impP'][:5])))
    if c.get('expP'):
        full.append('- Exports to %s: %s.' % (c['name'], '; '.join('%s [HS %s] %s' % (x[1][:60], x[0], money(x[2])) for x in c['expP'][:5])))
full += ['', '## Customs offices (FY %s)' % OF['fy'], '', '| Office | Imports cleared | Share of imports | Exports cleared | Share of exports | Page |', '|---|---|---|---|---|---|']
for key, o in offices:
    full.append('| %s | %s | %.1f%% | %s | %.1f%% | %s |' % (oname(key, o), money(o['imp']), o['imp'] / OF['totals']['imp'] * 100, money(o['exp']),
                                                           (o['exp'] / OF['totals']['exp'] * 100) if OF['totals']['exp'] else 0, ourl(key)))
full += ['', '## Import duty by product name (Customs Tariff %s)' % TAR.get('v', ''), '',
         'General customs duty and SAARC (SAFTA) rate for the first matching tariff lines of each product. VAT of 13% applies on top unless exempt; '
         'vehicles, alcohol and tobacco also carry excise, which is not shown here.', '',
         '| Product | HS code | Description | General duty | SAARC duty | Page |', '|---|---|---|---|---|---|']
rate = lambda v: ('Free' if str(v).strip() in ('0', '0.0', 'Free', 'free') else (str(v).strip() + ('%' if re.fullmatch(r'\d+(\.\d+)?', str(v).strip()) else ''))) if v not in (None, '') else '—'
for slug, name, codes in links.ALIAS_RECS:
    n = 0
    for r in TAR['rows']:
        if any(str(r[0]).startswith(p) for p in codes):
            full.append('| %s | %s | %s | %s | %s | %s/import-duty/%s |' % (name, r[0], ' '.join(str(r[1]).split())[:70].replace('|', '/'), rate(r[5]), rate(r[4]), SITE, slug))
            n += 1
            if n == 3:
                break
(pub / 'llms-full.txt').write_text('\n'.join(full) + '\n', encoding='utf-8')

# The /data page and CSV downloads were removed on 2026-11-12 at the owner's request (no bulk data hand-out).
import shutil
shutil.rmtree(pub / 'data', ignore_errors=True)
(pub / 'data.html').unlink(missing_ok=True)
print('ai_pages: llms.txt %d KB, llms-full.txt %d KB' % ((pub / 'llms.txt').stat().st_size // 1024, (pub / 'llms-full.txt').stat().st_size // 1024))
