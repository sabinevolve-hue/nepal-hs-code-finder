"""Fit page titles and meta descriptions to what search results show (~65 and ~160 characters) without
cutting words in half. Used by product_pages.py (at the template) and meta_pass.py (every other page)."""
import re

_TAIL = re.compile(r'[\s,;:(\-–—/&]+$')
_SMALL = {'of', 'and', 'or', 'the', 'a', 'an', 'for', 'with', 'in', 'on', 'to', 'by', 'not', 'nes', 'etc', 'whether', 'than', 'but', 'other'}


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
