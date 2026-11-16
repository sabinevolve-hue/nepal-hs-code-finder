"""Which Nepali authority an importer should ask, by HS chapter or heading.

Every rule here is tied to a source that was read on CHECKED. Nothing is inferred: a product group that could not be
tied to a law, an official page or a dated report is left out and named in NOT_COVERED instead, so the page never says
"no permit needed". Wording stays at "ask this authority" level; this site is a reference, not the authority.

kind: 'law' (text of an act or rules), 'official' (a government page), 'reported' (a news report or a foreign
government guide, named as such on the page).
"""
CHECKED = '16 November 2026'

RULES = [
    dict(key='plant', goods='Plants, seeds, fruit, vegetables, grain, spices',
         who='National Center for Plant Quarantine and Biosecurity', url='https://npponepal.gov.np',
         what='Plant quarantine offices issue an entry permit for imports of plants and plant products. Ask the office before shipping.',
         basis='Plant Quarantine and Protection Act 2007 and Plant Protection Rules 2010, as described on the centre’s own site.',
         src='https://npponepal.gov.np', srcname='National Center for Plant Quarantine and Biosecurity', kind='official',
         chapters=[6, 7, 8, 9, 10, 12], headings=[]),
    dict(key='animal', goods='Live animals, meat, fish, milk, eggs, other animal products',
         who='Department of Livestock Services, Animal Quarantine', url='https://dls.gov.np',
         what='Imports must enter through an Animal Quarantine Check Post and are held there for inspection at the importer’s cost. '
              'The law counts birds and fish as animals.',
         basis='Animal Health and Livestock Services Act 2055 (1998), sections 2, 6, 7 and 9.',
         src='https://faolex.fao.org/docs/pdf/nep40217.pdf', srcname='Act text on FAOLEX', kind='law',
         chapters=[1, 2, 3, 4, 5], headings=[]),
    dict(key='feed', goods='Animal feed, chicks, fingerlings, veterinary biological products',
         who='Department of Livestock Services', url='https://dls.gov.np',
         what='A recommendation letter is needed before importing biological products, chicks, fingerlings or animal feed.',
         basis='Animal Health and Livestock Services Act 2055 (1998), section 18.',
         src='https://faolex.fao.org/docs/pdf/nep40217.pdf', srcname='Act text on FAOLEX', kind='law',
         chapters=[], headings=['2309', '0105', '0301', '3002']),
    dict(key='food', goods='Food and drink',
         who='Department of Food Technology and Quality Control (DFTQC)', url='https://dftqc.gov.np',
         what='Imported food can be sampled and tested by DFTQC at the border. Ask DFTQC what your product needs.',
         basis='U.S. Commercial Service, Nepal Country Commercial Guide, “Standards for Trade” (June 2026). A foreign government guide, not Nepali law.',
         src='https://www.trade.gov/country-commercial-guides/nepal-standards-trade', srcname='trade.gov guide', kind='reported',
         chapters=[2, 3, 4, 7, 8, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21, 22], headings=[]),
    dict(key='drug', goods='Medicines and vaccines',
         who='Department of Drug Administration (DDA)', url='https://dda.gov.np',
         what='A drug must be registered before it is imported, and the importer needs a recommendation letter for the import.',
         basis='Drugs Registration Rules 2038 (1981), rules 4B and 5, as summarised by FAOLEX.',
         src='https://leap.unep.org/en/countries/np/national-legislation/drugs-registration-rules-2038-1981', srcname='FAOLEX summary', kind='law',
         chapters=[], headings=['3002', '3003', '3004', '3006']),
    dict(key='phone', goods='Mobile phones',
         who='Nepal Telecommunications Authority (NTA)', url='https://nta.gov.np',
         what='Importers and distributors of mobile handsets are reported to need a Type Approval Certificate for each model.',
         basis='Reported by Republica. Not read on the NTA site, which did not load when this page was checked.',
         src='https://myrepublica.nagariknetwork.com/news/tac-mandatory-for-mobile-set-distributors', srcname='Republica report', kind='reported',
         chapters=[], headings=['8517']),
    dict(key='ns', goods='Cement, iron rods, GI wire and sheet, LPG cylinders, regulators and valves, dry cells, PVC cable',
         who='Nepal Bureau of Standards and Metrology (NBSM)', url='https://nbsm.gov.np',
         what='In April 2017 NBSM made the Nepal Standard mark compulsory for these imported goods. The list has changed since; ask NBSM for the current one.',
         basis='Reported by The Kathmandu Post, 24 April 2017. The current list was not read on the NBSM site.',
         src='https://kathmandupost.com/money/2017/04/24/quality-mark-mandatory-for-12-imported-goods', srcname='Kathmandu Post report', kind='reported',
         chapters=[], headings=['2523', '7214', '7217', '7210', '7311', '8481', '8506', '8544']),
]

# Product groups that have their own rules which this page has not tied to a source. Named so nobody reads silence as "no permit".
NOT_COVERED = ['vehicles', 'pesticides', 'fertiliser', 'cosmetics', 'medical devices', 'tobacco and alcohol', 'arms and explosives',
               'radio and broadcasting equipment', 'chemicals and ozone-depleting gases', 'wildlife and forest products',
               'gold and silver', 'used goods']

BY_KEY = {r['key']: r for r in RULES}
CH = {}
HD = {}
for _r in RULES:
    for _c in _r['chapters']:
        CH.setdefault(str(_c), []).append(_r['key'])
    for _h in _r['headings']:
        HD.setdefault(_h, []).append(_r['key'])


def rules_for(code):
    """Rule keys for an HS code of 4+ digits: heading rules first, then chapter rules, no repeats."""
    d = ''.join(ch for ch in str(code) if ch.isdigit())
    if len(d) < 2:
        return []
    out = []
    for kk in HD.get(d[:4], []) + CH.get(str(int(d[:2])), []):
        if kk not in out:
            out.append(kk)
    return out
