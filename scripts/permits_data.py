"""Shared Nepal import-permit mapping.

Used by import_rules.py (the /import-rules checker page) and product_pages.py
(the inline "likely needs a permit" note on each product page). Indicative only:
maps an HS code to the authority / permit likely to apply, by 4-digit heading
where known, else by 2-digit chapter. Always framed as "confirm with the authority".
"""
import re

AUTH = {
    'animalq': dict(n='Animal Quarantine (Dept. of Livestock Services)', u='https://dls.gov.np',
                    p='Veterinary import permit + animal health / quarantine certificate',
                    g='Live animals, meat, fish, eggs, dairy and other animal products'),
    'plantq': dict(n='Plant Quarantine — NPPO Nepal', u='https://npponepal.gov.np',
                   p='Import permit + a phytosanitary certificate from the exporting country',
                   g='Plants, seeds, fruit, vegetables, grains, spices and other plant products'),
    'dftqc': dict(n='Food Technology & Quality Control (DFTQC)', u='https://dftqc.gov.np',
                  p='Food-import recommendation + laboratory testing / quality certificate',
                  g='Processed food, edible oils, beverages, dairy and other food items'),
    'dda': dict(n='Drug Administration (DDA)', u='https://dda.gov.np',
                p='Product registration + import licence (the importer itself must be DDA-licensed)',
                g='Medicines, vaccines, cosmetics and medical devices'),
    'nta': dict(n='Telecommunications Authority (NTA)', u='https://nta.gov.np',
                p='Type Approval Certificate (TAC)',
                g='Mobile phones and radio / wireless telecom equipment'),
    'nbsm': dict(n='Bureau of Standards & Metrology (NBSM)', u='https://nbsm.gov.np',
                 p='Mandatory NS standard certification / NS mark',
                 g='Goods under compulsory standards — steel & rebar, cement, cables, LPG cylinders, helmets, bottled water and more'),
    'pesticide': dict(n='Pesticide Registration & Management Centre', u='https://npponepal.gov.np',
                      p='Pesticide registration + import permit',
                      g='Insecticides, herbicides, fungicides and other pesticides'),
    'fertilizer': dict(n='Fertilizer regulation (MoALD)', u='https://moald.gov.np',
                       p='Government-regulated; import permit / quality control',
                       g='Chemical fertilizers'),
    'vehicle': dict(n='Transport Management (DoTM)', u='https://dotm.gov.np',
                    p='Emission & safety standards, then registration after import',
                    g='Motor vehicles and motorcycles'),
    'home': dict(n='Ministry of Home Affairs', u='https://moha.gov.np',
                 p='Special licence — heavily restricted or prohibited',
                 g='Arms, ammunition and explosives'),
}
AUTH_ORDER = ['plantq', 'animalq', 'dftqc', 'dda', 'nta', 'nbsm', 'pesticide', 'fertilizer', 'vehicle', 'home']

CHRULES = {
    1: ['animalq'], 2: ['animalq', 'dftqc'], 3: ['animalq', 'dftqc'], 4: ['animalq', 'dftqc'], 5: ['animalq'],
    6: ['plantq'], 7: ['plantq', 'dftqc'], 8: ['plantq', 'dftqc'], 9: ['plantq', 'dftqc'], 10: ['plantq', 'dftqc'],
    11: ['plantq', 'dftqc'], 12: ['plantq'], 13: ['plantq'], 14: ['plantq'], 15: ['dftqc'],
    16: ['dftqc'], 17: ['dftqc'], 18: ['dftqc'], 19: ['dftqc'], 20: ['dftqc'], 21: ['dftqc'], 22: ['dftqc'],
    23: ['animalq'], 24: ['dftqc'], 30: ['dda'], 31: ['fertilizer'], 72: ['nbsm'], 73: ['nbsm'],
    87: ['vehicle'], 93: ['home'],
}
HDRULES = {
    '2523': ['nbsm'],
    '3303': ['dda'], '3304': ['dda'], '3305': ['dda'], '3306': ['dda'], '3307': ['dda'],
    '3808': ['pesticide'],
    '3601': ['home'], '3602': ['home'], '3603': ['home'], '3604': ['home'],
    '8517': ['nta'], '8525': ['nta'], '8526': ['nta'], '8527': ['nta'], '8528': ['nta'],
    '9018': ['dda'], '9019': ['dda'], '9020': ['dda'], '9021': ['dda'], '9022': ['dda'],
}


def permits_for(code):
    """-> list of auth dicts (with 'key') likely to apply to this HS code; [] if none flagged."""
    cn = re.sub(r'\D', '', str(code))
    if len(cn) < 2:
        return []
    hd = cn[:4]
    try:
        ch = int(cn[:2])
    except ValueError:
        return []
    keys, seen = [], set()
    for k in (HDRULES.get(hd, []) + CHRULES.get(ch, [])):
        if k not in seen:
            seen.add(k)
            keys.append(k)
    return [dict(key=k, **AUTH[k]) for k in keys]
