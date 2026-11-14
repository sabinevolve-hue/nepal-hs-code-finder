"""Repair product names that arrive damaged in the Department of Customs trade workbooks.

The FTS workbooks carry short product names with two kinds of damage:
  1. a letter lost where the source wrapped a line ("direct reduct on" for "reduction", "st inless", "co ton"),
     or a stray space inside a word ("appara tus");
  2. plain misspellings ("Liquidified Petrolium Gas", "Feul Oil", "kintted").
This module fixes both for DISPLAY only. Page addresses keep using the original text (see statsfields.Name), so
no URL changes.

How: a vocabulary is built from the official tariff's own wording (data/tariff.json). A two-token gap is joined
only when the joined word (with one inserted letter, or none) is in that vocabulary and at least one of the two
fragments is not itself a word. Misspellings come from the reviewed list in FIXES. Nothing is guessed beyond that.
"""
import json, pathlib, re

root = pathlib.Path(__file__).resolve().parents[1]
_T = json.loads((root / 'data' / 'tariff.json').read_text(encoding='utf-8'))
_text = ' '.join([r[1] for r in _T['rows']] + list(_T.get('strs', [])) + [h[0] for h in _T.get('heads', {}).values()]
                 + [c.get('t', '') for c in _T.get('chapters', {}).values()])
VOCAB = {}
for w in re.findall(r"[A-Za-z]{2,}", _text):
    VOCAB[w.lower()] = VOCAB.get(w.lower(), 0) + 1
# everyday words the tariff also uses, so short real words are never treated as fragments
SMALL = set('a an and are as at be by for from in is it of on or the to with not no nor than that this up use used per its into over under other others etc incl excl nes new old raw dry wet big tea oil gas car van bus air sea'.split())

# reviewed misspellings in the source (whole words, case-insensitive) -> correction
FIXES = {
    'liquidified': 'liquefied', 'petrolium': 'petroleum', 'feul': 'fuel', 'kintted': 'knitted', 'preparetions': 'preparations',
    'chasis': 'chassis', 'acumulators': 'accumulators', 'doss': 'doses', 'colis': 'coils', 'trycycle': 'tricycle',
    'alcohalic': 'alcoholic', 'exceedubg': 'exceeding', 'exced': 'exceeding', 'enginee': 'engine', 'wal': 'wall',
    'soyabean': 'soya bean', 'excel': 'excl', 'sugarm': 'sugar', 'mustards': 'mustard',
}
PHRASES = [(re.compile(r'^Others Paddy$', re.I), 'Paddy (other)'), (re.compile(r'\bspilt-system\b', re.I), 'split-system'),
           (re.compile(r'\bnon-allo\b', re.I), 'non-alloy'), (re.compile(r'\b360o\b'), '360°'), (re.compile(r'\s+\.$'), ''),
           (re.compile(r'\(\s+'), '('), (re.compile(r'\s+\)'), ')'), (re.compile(r'\s+,'), ','), (re.compile(r',(?=[A-Za-z])'), ', ')]
LETTERS = 'abcdefghijklmnopqrstuvwxyz'


def _is_word(w):
    w = w.lower()
    return w in SMALL or VOCAB.get(w, 0) >= 2


def _join(a, b):
    """Return the repaired word for fragments a b, or None."""
    al, bl = a.lower(), b.lower()
    if _is_word(al) and _is_word(bl):
        return None
    cands = []
    if VOCAB.get(al + bl, 0) >= 2:
        cands.append((VOCAB[al + bl], a + b))
    for ch in LETTERS:
        w = al + ch + bl
        if VOCAB.get(w, 0) >= 2:
            cands.append((VOCAB[w], a + ch + b))
    if not cands:
        return None
    cands.sort(reverse=True)
    if len(cands) > 1 and cands[0][0] < 3 * cands[1][0]:
        return None                      # ambiguous: leave the source text alone
    return cands[0][1]


_TOK = re.compile(r"[A-Za-z]+| +|[^A-Za-z ]+")


def _best(cands):
    if not cands:
        return None
    cands.sort(reverse=True)
    if len(cands) > 1 and cands[0][0] < 3 * cands[1][0]:
        return None                      # ambiguous: leave the source text alone
    return cands[0][1]


def _gap(a, b):
    """A double space in the source marks a lost letter. Returns the repaired text for 'a  b', or None."""
    al, bl = a.lower(), b.lower()
    j = _best([(VOCAB[al + ch + bl], a + ch + b) for ch in LETTERS if VOCAB.get(al + ch + bl, 0) >= 2])
    if j and not (_is_word(al) and _is_word(bl) and len(al) > 3 and len(bl) > 3):
        return j
    if not _is_word(bl) and len(bl) >= 3:          # letter lost at the start of the second word
        k = _best([(VOCAB[ch + bl], ch + b) for ch in LETTERS if VOCAB.get(ch + bl, 0) >= 2])
        if k:
            return a + ' ' + k
    if not _is_word(al) and len(al) >= 3:          # letter lost at the end of the first word
        k = _best([(VOCAB[al + ch], a + ch) for ch in LETTERS if VOCAB.get(al + ch, 0) >= 2])
        if k:
            return k + ' ' + b
    return None


def fix(name):
    """name: the RAW source text (spacing intact)."""
    toks = _TOK.findall(str(name).strip())
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t.isalpha() and i + 2 < len(toks) and toks[i + 2].isalpha() and toks[i + 1].isspace():
            a, b, sp = t, toks[i + 2], toks[i + 1]
            j = None
            if len(sp) >= 2:
                j = _gap(a, b)
            elif (not _is_word(a) or not _is_word(b)) and len(a) + len(b) >= 6:
                j = _join(a, b)          # single stray space inside a word ("appara tus")
            if j:
                # keep going from the repaired text so a following fix can still apply
                toks[i:i + 3] = _TOK.findall(j)
                out.append(toks[i]); i += 1
                continue
        # a gap right after punctuation: the lost letter belongs to the start of the next word ("machines,  elf-contained")
        if t.isspace() and len(t) >= 2 and i + 1 < len(toks) and toks[i + 1].isalpha() and out and not out[-1].isalpha():
            b = toks[i + 1]
            if not _is_word(b) and len(b) >= 3:
                k = _best([(VOCAB[ch + b.lower()], ch + b) for ch in LETTERS if VOCAB.get(ch + b.lower(), 0) >= 2])
                if k:
                    out.append(' '); out.append(k); i += 2; continue
        if t.isalpha() and t.lower() in FIXES:
            rep = FIXES[t.lower()]
            t = (rep[0].upper() + rep[1:]) if t[0].isupper() else rep
        out.append(t); i += 1
    s = ''.join(out)
    s = re.sub(r'\s+', ' ', s)
    for rx, rep in PHRASES:
        s = rx.sub(rep, s)
    s = re.sub(r'(\s*\.)+\s*$', '', s)
    return re.sub(r'\s{2,}', ' ', s).strip(' ,;:-')


if __name__ == '__main__':
    import sys
    S = json.loads((root / 'data' / 'stats.json').read_text(encoding='utf-8'))
    names = {}
    for k in ('imports', 'exports'):
        for c, v in S[k].items():
            names[v[0]] = max(names.get(v[0], 0), v[3])
    ch = [(v, n, fix(n)) for n, v in names.items() if fix(n) != n]
    ch.sort(reverse=True)
    print(len(names), 'names;', len(ch), 'changed')
    for v, a, b in ch[:int(sys.argv[1]) if len(sys.argv) > 1 else 60]:
        print(' ', a, '\n   ->', b)
