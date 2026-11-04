"""Shared field layout + sanity checks for data/stats.json, used by the static-page generators.

stats.json (built by stats.py) stores per-code trade rows as positional lists to stay small enough to inline:
  imports[code8] = [description, unit, quantity, value, revenue, partners, n_partners]
  exports[code8] = [description, unit, quantity, value, partners, n_partners]
All money is Rs. thousand. partners = top-6 [[country, value], ...] by value.

Index 2 is the QUANTITY (pieces / kg / litres), not money. Reading it as a value is exactly the bug that put
"Rs 15.50 Crore" (= 154,991 laptops) on /import-duty pages. Always use these names.
"""

IMP_DESC, IMP_UNIT, IMP_QTY, IMP_VALUE, IMP_REVENUE, IMP_PARTNERS, IMP_NPARTNERS = range(7)
EXP_DESC, EXP_UNIT, EXP_QTY, EXP_VALUE, EXP_PARTNERS, EXP_NPARTNERS = range(6)

# Tariff year of data/customs-tariff-2026-27.txt ("Customs Tariff 2026/2027", Department of Customs,
# published Bhadra 2083) = Nepali fiscal year 2083/84 (mid-July 2026 to mid-July 2027).
TARIFF_FY = '2083/84'
TARIFF_FY_AD = '2026/27'


def validate_import_rows(rows, stats):
    """Return a list of human-readable problems with the import rows a page will print.

    Checks, per code:
      * value is a positive number;
      * the listed partner countries do not add up to more than the code's total
        (tolerance: 1 Rs-thousand of rounding per listed country + 0.1 %);
      * no single country exceeds the total;
      * the total is not larger than its whole HS chapter's imports, nor than Nepal's total imports;
      * the value agrees with the same code's latest-year entry in the multi-year history.
    """
    errs = []
    chap = {int(c[0]): float(c[2]) for c in stats.get('chapters', [])}
    total_imports = float(stats.get('overview', {}).get('imports', [0, 0])[1]) or float('inf')
    hist = stats.get('history', {}).get('codes', {})
    for code, r in rows.items():
        try:
            v = float(r[IMP_VALUE])
        except Exception:
            errs.append('%s: non-numeric value %r' % (code, r[IMP_VALUE] if len(r) > IMP_VALUE else None)); continue
        if v <= 0:
            errs.append('%s: value %s <= 0' % (code, v)); continue
        parts = r[IMP_PARTNERS] if len(r) > IMP_PARTNERS and isinstance(r[IMP_PARTNERS], list) else []
        psum = sum(float(p[1]) for p in parts)
        if psum > v * 1.001 + len(parts):
            errs.append('%s: partner countries sum to %s > total %s (Rs thousand)' % (code, psum, v))
        for p in parts:
            if float(p[1]) > v + 1:
                errs.append('%s: %s alone %s > total %s' % (code, p[0], p[1], v))
        ch = int(code[:2])
        if ch in chap and v > chap[ch] * 1.001 + 1:
            errs.append('%s: total %s > its chapter %02d imports %s' % (code, v, ch, chap[ch]))
        if v > total_imports:
            errs.append('%s: total %s > Nepal total imports %s' % (code, v, total_imports))
        h = hist.get(code)
        if h and abs(float(h[-1][0]) - v) > 1:
            errs.append('%s: total %s != latest-year history value %s' % (code, v, h[-1][0]))
    return errs


# ---- /import-duty/<slug>-<code> URL scheme (single source for product_pages.py and app_pages.py) ----
import re as _re, unicodedata as _ud


def clean_name(s):
    s = _re.sub(r'\s+', ' ', str(s)).strip()
    s = _re.sub(r'\s*\.\s*$', '', s)             # drop a trailing " ."
    s = s.strip(' ,;:-')
    return s or 'product'


def slug(s):
    s = _ud.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')
    s = _re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return (_re.sub(r'-{2,}', '-', s)[:60].strip('-')) or 'product'


def import_duty_path(code8, name):
    return '/import-duty/' + slug(clean_name(name)) + '-' + code8
