"""Fit page titles and meta descriptions to what search results show (~65 and ~160 characters) without
cutting words in half. Used by product_pages.py (at the template) and meta_pass.py (every other page)."""
import re

_TAIL = re.compile(r'[\s,;:(\-–—/&]+$')
_SMALL = {'of', 'and', 'or', 'the', 'a', 'an', 'for', 'with', 'in', 'on', 'to', 'by', 'not', 'nes', 'etc', 'whether', 'than', 'but', 'other', 'their', 'its', 'such', 'these', 'this', 'that', 'which'}


def clip_words(s, limit):
    """Shorten s to <= limit characters at a word boundary; drop dangling connector words and punctuation."""
    s = ' '.join(str(s).split())
    if len(s) <= limit:
        return s
    cut = s[:limit + 1]
    cut = cut[:cut.rfind(' ')] if ' ' in cut else s[:limit]
    words = cut.split(' ')
    while len(words) > 1 and (words[-1].lower().strip(',.;:') in _SMALL or len(words[-1].strip(',.;:')) <= 1):
        words.pop()
    out = _TAIL.sub('', ' '.join(words))
    # never leave an unclosed bracket: cut back to before it
    if out.count('(') > out.count(')'):
        out = _TAIL.sub('', out[:out.rfind('(')])
    return out


def fit_title(t, limit=65, brand=' | Customs Nepal'):
    t = ' '.join(t.split())
    if len(t) <= limit:
        return t
    if t.endswith(brand):
        t = t[:-len(brand)].rstrip()
        if len(t) <= limit:
            return t
    # cut at the last natural separator that leaves a meaningful title
    for sep in (' — ', ' | ', ': ', ' · ', '; ', ' – ', ', '):
        i = t.rfind(sep, 0, limit + 1)
        while i >= 30:
            head = t[:i].rstrip()
            if len(head) <= limit:
                return head
            i = t.rfind(sep, 0, i)
    return clip_words(t, limit)


def fit_desc(d, limit=160):
    d = ' '.join(d.split())
    if len(d) <= limit:
        return d
    # end on a full sentence if one fits and keeps most of the meaning
    i = max(d.rfind('. ', 0, limit), d.rfind('? ', 0, limit))
    if i >= 90:
        return d[:i + 1]
    return clip_words(d, limit - 1) + '…'


_HS_JOIN = {'for', 'of', 'with', 'used', 'in', 'on', 'from', 'containing', 'having', 'whether', 'not', 'n.e.c.', 'excluding',
            'including', 'by', 'to', 'designed', 'suitable', 'made', 'put', 'as'}


def hs_phrase(desc):
    """Readable product phrase from a WCO description ('Machinery; for working rubber or plastics…' ->
    'Machinery for working rubber or plastics…'). The text before the first ';' is often a single generic word
    (Machinery, Vehicles, Boilers), so the next clause is joined on: with a space when it starts with a preposition,
    otherwise with a comma. Later ';' become commas."""
    parts = [p.strip() for p in ' '.join(str(desc).split()).split(';') if p.strip()]
    if not parts:
        return ''
    out = parts[0]
    for p in parts[1:]:
        first = p.split()[0].lower()
        out += (' ' if first in _HS_JOIN else ', ') + p
    return out


_HS_DANGLING = re.compile(r'(\s+(of a kind|of a|a kind)(\s+used)?(\s+primarily|\s+solely|\s+principally)?|\s+used(\s+primarily|\s+solely)?|\s+with(\s+a|\s+an)?)$', re.I)


def hs_name(desc, limit):
    """hs_phrase clipped to `limit` characters at a word boundary (no dangling connectors, no ellipsis). When the
    phrase had to be cut, a half-finished trailing clause is dropped back to the last comma if most of the room
    stays used."""
    full = hs_phrase(desc)
    out = clip_words(full, limit)
    if out != full:
        out = _TAIL.sub('', _HS_DANGLING.sub('', out)) or out
        i = out.rfind(', ')
        if i >= limit * 0.6:
            out = out[:i]
    return out
