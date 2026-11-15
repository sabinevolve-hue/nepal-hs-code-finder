#!/usr/bin/env python3
"""Countries and regions that have World Bank procurement notices -> data/world/tender_places.json.

The tenders page links each place to the World Bank's own procurement search; it shows no notices itself. (A live list
was tried: the World Bank's firewall refuses requests forwarded from the site, so visitors saw an error.)
Source: World Bank Procurement Notices API, CC BY 4.0. Names are the World Bank's. Run occasionally; the list is stable.
Usage:  python3 scripts/world_tenders.py
"""
import datetime, json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'world', 'tender_places.json')
TYPES = 'Invitation for Bids^Request for Expression of Interest^Invitation for Prequalification^General Procurement Notice'
u = 'https://search.worldbank.org/api/v2/procnotices?' + urllib.parse.urlencode(dict(format='json', rows=0, fct='project_ctry_name_exact', notice_type_exact=TYPES))
with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'world.customsnepal.com data build'}), timeout=120) as r:
    f = json.load(r)['facets']['project_ctry_name_exact']
names = sorted({v['name'].strip() for v in f.values() if v.get('name') and v.get('count', 0) >= 20 and v['name'].strip().lower() not in ('world', 'multi-regional', '')})
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(source='World Bank, Procurement Notices (CC BY 4.0)', checked=datetime.date.today().isoformat(), places=names), fh, ensure_ascii=False, indent=0)
print(len(names), 'places')
