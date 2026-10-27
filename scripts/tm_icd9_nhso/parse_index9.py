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


CONT = re.compile(r'-{2,}\s*Cont\.?|—+\s*Cont|Cont\.$')


def col_parts(page):
    L = [l for l in lines(f'/home/claude/src/ocr9/p{page:03d}.tsv') if 215 < l['y'] < 2290]
    words = [w for l in L for w in l['words']]
    if not words:
        return []
    xs = sorted(w[0] for w in words)
    left0 = xs[0]
    # The right column starts at the first word that follows a wide gap in a line and is text, not a code:
    # codes are right-aligned at the end of the left column and used to be mistaken for the column start,
    # which pushed every right-column line several indent levels too deep (e.g. the lead term Repair at level 5).
    cand = []
    for l in L:
        ws = l['words']
        for i in range(1, len(ws)):
            if ws[i][0] - (ws[i - 1][0] + ws[i - 1][2]) > 40 and ws[i][0] > left0 + 600 \
                    and re.match(r'[A-Za-z(\[]', ws[i][4]) and not CODE_TOKEN.match(ws[i][4]):
                cand.append(ws[i][0])
        if ws and ws[0][0] > left0 + 600:
            cand.append(ws[0][0])
    right0 = min(cand, default=None)
    mid = (right0 - 20) if right0 else 10 ** 6
    cols = ([], [])
    for l in L:
        lw = [w for w in l['words'] if w[0] < mid]
        rw = [w for w in l['words'] if w[0] >= mid]
        for i, ws in enumerate((lw, rw)):
            if ws:
                cols[i].append({'x': ws[0][0], 'y': l['y'], 'words': [w[4] for w in ws]})
    # Indent levels are measured from where lead terms start in that column. Lead terms are capitalised and
    # subterms are not, so if the least-indented lines of a column are lowercase the column is a continuation
    # ("Repair---Cont.") that starts at level 1, and the lead-term position is one step (35px) further left.
    out = []
    for col in cols:
        body = [c for c in col if not CONT.search(' '.join(c['words']))]
        if not body:
            continue
        m = min(c['x'] for c in body)
        # a "Lead---Cont." header at the top of the column sits where lead terms start; trust it unless the page
        # is skewed so badly that body lines start left of it
        hdr = [c['x'] for c in col if c['y'] < 260 and CONT.search(' '.join(c['words']))]
        if hdr and hdr[0] <= m + 8:
            base = hdr[0]
        else:
            at_min = [c['words'][0] for c in body if c['x'] <= m + 8]
            lead_here = any(re.match(r'[A-Z]', w) and not w.startswith('Note') for w in at_min)
            base = m if lead_here else m - 35
        for c in col:
            c['x'] -= base
            out.append(c)
    return out


entries = []
for pg in range(FIRST, LAST + 1):
    for part in col_parts(pg):
        ws = part['words']
        text = ' '.join(ws)
        if CONT.search(text) or re.fullmatch(r'[A-Z][.\s|]*', text) or 'INDEX TO PROCEDURES' in text:
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

# Lead terms that OCR indentation put one or more levels deep (skewed scans): a capitalised entry that sorts
# between the lead term above it and the next lead term is itself a lead term. Eponyms under "Operation"
# (Ammon, Winiwarter ...) do not sort between their neighbours, so they stay where they are.
def sort_key(t):
    return re.sub(r'[^a-z ]', '', t.lower()).strip()


# stray OCR marks before a term ("Ss Sauer-Bacon", "v | Vagotomy") would also spoil the sort order used below
for e in entries:
    t = re.sub(r'^(?:[A-Za-z]{1,2}\s*\|\s*|[Ss]s?\s+|[vV]\s+|[|~]\s*)(?=[A-Z][a-z])', '', e[1])
    if t != e[1]:
        report['stray mark removed'] += 1
        e[1] = t

lead_idx = [i for i, e in enumerate(entries) if e[0] == 0]
for i, e in enumerate(entries):
    if e[0] == 0 or not re.match(r'[A-Z][a-z]{3,}', e[1]) or e[1].startswith('Note'):
        continue
    prev = max((j for j in lead_idx if j < i), default=None)
    nxt = min((j for j in lead_idx if j > i), default=None)
    if prev is None:
        continue
    k, kp = sort_key(e[1]), sort_key(entries[prev][1])
    kn = sort_key(entries[nxt][1]) if nxt is not None else '~'
    if k[:1] == kp[:1] and kp < k < kn:
        d = e[0]
        e[0] = 0
        j = i + 1
        while j < len(entries) and entries[j][0] > d:
            entries[j][0] -= d
            j += 1
        lead_idx.append(i)
        lead_idx.sort()
        report['lead term re-levelled'] += 1

# a subterm can only be one level below the line above it; deeper jumps are indentation misreads
prev_lvl = 0
for e in entries:
    if e[0] > prev_lvl + 1:
        e[0] = prev_lvl + 1
        report['level jump clamped'] += 1
    prev_lvl = e[0]

# cross references: OCR writes the dash before "see" as --, —, -, ~- or nothing, and "also" as a/so, afso ...
# Normalise to "<term> – see (also) <Target>" so the web page can link it like the ICD-10 index.
GENERIC = ('category', 'categories', 'specific', 'condition')


def clean_see(t):
    t = re.sub(r'\bsee\s+(?:a/so|afso|aIso|als0|a1so|alsa|aiso)\b', 'see also', t)
    t = re.sub(r'\s*(?:—+|~-|-{1,3}|–)\s*(?=see\b)', ' – ', t)
    t = re.sub(r'(?<=[^\s–])\s+(?=see\s+(?:also\s+)?(?:[A-Z]|' + '|'.join(GENERIC) + r'))', ' – ', t)
    t = re.sub(r'\bsee\s+(also\s+)?(?!also\b)([a-z])', lambda m: m.group(0) if t[m.start(2):].startswith(GENERIC) else 'see ' + (m.group(1) or '') + m.group(2).upper(), t)
    if t.startswith(' – '):
        t = t[3:]
    return t


for e in entries:
    new = clean_see(e[1])
    if new != e[1]:
        report['see text normalised'] += 1
        e[1] = new

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
