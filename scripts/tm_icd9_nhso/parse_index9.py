"""Parse the OCR'd ICD-9-CM Index to Procedures (pages 285–487, two columns).

Levels come from indentation (~35px per level at 300dpi). Codes are validated against
the tabular list; single OCR digit errors are repaired when exactly one valid code fits.
Writes data/idx9/manifest.json, data/idx9/I-<L>.json and data/icd9-kw.json.
"""
import json, os, re
from collections import defaultdict, Counter
from ocrlines import lines

FIRST, LAST = 285, 487
OUT = '/home/claude/icd-site/data/icd9/index'
os.makedirs(OUT, exist_ok=True)
codes = {c['c'] for c in json.load(open('/home/claude/icd-site/data/icd9/codes.json', encoding='utf8'))['codes']}
CODE_TOKEN = re.compile(r'^[\d$SOIl]{2}\.[\d$SOIl]{1,2}[,;.]?$')
TRANS = str.maketrans({'$': '5', 'S': '5', 'O': '0', 'I': '1', 'l': '1'})
CONFUSE = {'0': '689', '1': '74', '2': '7', '3': '85', '4': '19', '5': '63', '6': '0858', '7': '12', '8': '360', '9': '40'}
report = Counter()


def fix_code(tok):
    c = tok.translate(TRANS).rstrip(',;.')
    if c in codes:
        return c
    a, b = c.split('.')
    cands = set()
    for i, ch in enumerate(a + b):
        for alt in CONFUSE.get(ch, ''):
            s = (a + b)[:i] + alt + (a + b)[i + 1:]
            cand = s[:2] + '.' + s[2:]
            if cand in codes:
                cands.add(cand)
    if len(cands) == 1:
        report['code repaired'] += 1
        return cands.pop()
    report['code not in tabular'] += 1
    return c


def col_parts(page):
    L = [l for l in lines(f'/home/claude/src/ocr9/p{page:03d}.tsv') if 215 < l['y'] < 2290]
    words = [w for l in L for w in l['words']]
    if not words:
        return []
    xs = sorted(w[0] for w in words)
    left0 = xs[0]
    right0 = min((w[0] for w in words if w[0] > left0 + 560), default=None)
    mid = (right0 - 20) if right0 else 10 ** 6
    cols = ([], [])
    for l in L:
        lw = [w for w in l['words'] if w[0] < mid]
        rw = [w for w in l['words'] if w[0] >= mid]
        for i, ws in enumerate((lw, rw)):
            if ws:
                cols[i].append({'x': ws[0][0] - (left0 if i == 0 else right0), 'y': l['y'], 'words': [w[4] for w in ws]})
    return cols[0] + cols[1]


entries = []
for pg in range(FIRST, LAST + 1):
    for part in col_parts(pg):
        ws = part['words']
        text = ' '.join(ws)
        if re.search(r'-{2,}\s*Cont\.?|—+\s*Cont|Cont\.$', text) or re.fullmatch(r'[A-Z][.\s|]*', text) or 'INDEX TO PROCEDURES' in text:
            continue
        code = None
        if ws and CODE_TOKEN.match(ws[-1]):
            code = fix_code(ws[-1]); ws = ws[:-1]
        body = ' '.join(ws).strip(' —-')
        lvl = max(0, round(part['x'] / 35.5))
        prev = entries[-1] if entries else None
        if prev and not prev[2] and part['x'] > prev[4] + 40:
            prev[1] = (prev[1] + ' ' + body).strip()
            if code:
                prev[2] = code
            continue
        if not body and code and prev and not prev[2]:
            prev[2] = code
            continue
        entries.append([min(lvl, 6), body, code, pg, part['x']])

# lead-term letters and output
by = defaultdict(list)
letter = 'A'
stack = []
kw = defaultdict(list)
for lvl, text, code, pg, x in entries:
    if lvl == 0 and text[:1].isalpha():
        letter = text[0].upper()
    by[letter].append([lvl, text, code, None, 0])
    stack = stack[:lvl] + [text]
    if code and code in codes:
        kw[code].append(' '.join(stack))
manifest = {'sections': {'I': 'ดัชนีหัตถการ'}, 'letters': {'I': {}}}
for L, rows in sorted(by.items()):
    json.dump(rows, open(f'{OUT}/I-{L}.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    manifest['letters']['I'][L] = len(rows)
json.dump(manifest, open(f'{OUT}/manifest.json', 'w', encoding='utf8'), ensure_ascii=False)
STOP = {'see', 'also', 'code', 'with', 'without', 'and', 'the', 'for', 'other', 'nec', 'nos', 'by', 'of', 'or'}
kwout = {}
for c, paths in kw.items():
    seen, words = set(), []
    for p in paths:
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p.lower()):
            if w not in seen and len(w) > 2 and w not in STOP:
                seen.add(w); words.append(w)
    kwout[c] = ' '.join(words)[:400]
json.dump(kwout, open('/home/claude/icd-site/data/icd9/keywords.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
ref = {e[2] for e in entries if e[2]}
print('entries', len(entries), 'leads', sum(1 for e in entries if e[0] == 0), 'with code', sum(1 for e in entries if e[2]), dict(report))
print('tabular leaf codes never referenced by index', len([c for c in codes if c not in ref]))
