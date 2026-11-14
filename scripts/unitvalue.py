"""Average declared import value per unit, from the Department of Customs trade statistics.

stats.json holds, per 8-digit line, the unit, the quantity, the import value and the revenue collected (Rs thousand).
Value divided by quantity is the average value importers declared per unit over the year. It mixes every grade,
brand and origin under the line, so it is a yardstick for a quote, not a price list. Nothing here is estimated:
it is one official number divided by another.
"""
from statsfields import IMP_UNIT, IMP_QTY, IMP_VALUE, IMP_REVENUE

UNITS = {'KG': ('kg', 'kg'), 'PCS': ('piece', 'pieces'), 'SQM': ('square metre', 'square metres'), 'LTR': ('litre', 'litres'),
         'MTQ': ('cubic metre', 'cubic metres'), 'PAIR': ('pair', 'pairs'), 'PR': ('pair', 'pairs'), 'GRM': ('gram', 'grams'),
         'MTR': ('metre', 'metres'), 'KL': ('kilolitre', 'kilolitres'), 'DZN': ('dozen', 'dozen'), 'TNE': ('tonne', 'tonnes'),
         'NOS': ('piece', 'pieces'), 'SET': ('set', 'sets'), 'KWH': ('kWh', 'kWh'), 'CRT': ('carat', 'carats')}
MIN_QTY = 10          # below this an average means nothing


def inr(n):
    """Indian digit grouping: 1234567 -> 12,34,567."""
    n = int(round(n)); s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ','.join(parts + [tail])
    return ('-' if n < 0 else '') + s


def rs(n):
    """Rupees with sensible precision for small unit values."""
    if n >= 100:
        return 'Rs ' + inr(n)
    if n >= 10:
        return 'Rs %.1f' % n
    return 'Rs %.2f' % n


def qty_words(q, plural):
    if q >= 1e7:
        return '%.2f crore %s' % (q / 1e7, plural)
    if q >= 1e5:
        return '%.2f lakh %s' % (q / 1e5, plural)
    return '%s %s' % (inr(q), plural)


def unit_value(row):
    """row: a stats.json imports row. -> dict(per, tax, qty, one, many) or None."""
    try:
        u = str(row[IMP_UNIT] or '').strip().upper(); q = float(row[IMP_QTY] or 0); v = float(row[IMP_VALUE] or 0) * 1000.0
        r = float(row[IMP_REVENUE] or 0) * 1000.0
    except (ValueError, TypeError, IndexError):
        return None
    if u not in UNITS or q < MIN_QTY or v <= 0:
        return None
    one, many = UNITS[u]
    return dict(per=v / q, tax=r / q, qty=q, one=one, many=many, share=(r / v if v else 0))
