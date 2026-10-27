"""Parse the WHO ICD-10 2016 Alphabetical Index (Volume 3) from idx_lines.jsonl.

Writes /home/claude/who/who_index.json:
  entries: [[level, text, code1, code2, section, 0], ...]  section 'I' diseases, 'II' external causes
  neoplasm: {"rows": [[level, term, c1..c5, 0], ...], "notes": [...]}
  drugs: {"rows": [[level, term, c1..c5, 0], ...]}
"""
import json, re
from collections import defaultdict

L = [json.loads(l) for l in open('/home/claude/who/idx_lines.jsonl', encoding='utf8')]
by_page = defaultdict(list)
for l in L:
    by_page[l['p']].append(l)

SEC1 = range(18, 672)
NEO = range(446, 481)
SEC2 = range(674, 726)
DRUG = range(728, 852)
CODE = r'[A-Z]\d\d(?:\.[\d-]{1,2})?[†*]?'
CODE_TAIL = re.compile(r'\s+((?:' + CODE + r'\s*){1,2})$')
CODE_ONLY = re.compile(r'^(?:' + CODE + r'\s*)+$')


def join_spans(spans):
    out = ''
    for x, t, b, x1 in spans:
        t = t.strip()
        if not t:
            continue
        glue = out and (out[-1].isalpha() or out[-1] in "'’-(") and (t[0].islower() or t[0] in "'’)")
        out += ('' if not out or glue else ' ') + t
    out = re.sub(r'\s+\*', '*', out)
    out = re.sub(r'\s+†', '†', out)
    out = re.sub(r'\bN EC\b', 'NEC', out)
    return ' '.join(out.split())


def margin(p):
    xs = [s[0] for l in by_page[p] for s in l['spans'] if 100 < l['y'] < 700]
    return 71 if xs and min(xs) < 120 else 181


def body(p):
    return [l for l in by_page[p] if 125 < l['y'] < 700]


# ---------------------------------------------------------------- neoplasm table
def table_header(p):
    for l in by_page[p]:
        for s in l['spans']:
            if s[1].startswith('Primary'):
                return s[0], l['y']
    return None


neo_rows, neo_notes, table_cut = [], [], {}
for p in NEO:
    h = table_header(p)
    if not h:
        continue
    base, hy = h
    m = margin(p)
    lines = [l for l in body(p) if l['y'] > hy + 5]
    # the two-column index resumes where a line has a span starting at the second column
    rows_y = [l['y'] for l in lines if any(abs(s[0] - base) < 8 and CODE_ONLY.match(s[1].strip()) for s in l['spans']) or '....' in l['t']]
    last = max(rows_y) if rows_y else 0
    after = [l for l in lines if l['y'] > last + 1]
    two_col = [l for l in after if any(m + 160 <= s[0] <= m + 195 and re.match(r'^[–A-Z]', s[1].strip()) for s in l['spans'])]
    y_end = (last + 1) if len(two_col) >= 2 else 10 ** 6
    table_cut[p] = y_end
    for l in lines:
        if l['y'] >= y_end or 'continued' in l['t']:
            continue
        term_sp = [s for s in l['spans'] if s[0] < base - 8]
        code_sp = [s for s in l['spans'] if s[0] >= base - 8]
        term = join_spans(term_sp)
        term = re.sub(r'\.{3,}', '', term).strip()
        vals = [''] * 5
        for s in code_sp:
            k = round((s[0] - base) / 34.3)
            for c in s[1].split():
                if re.match(CODE, c) and 0 <= k < 5:
                    vals[k] = c
                    k += 1
        if term.startswith('Note:') or (neo_notes and not neo_rows and not any(vals) and not term.startswith('–')):
            neo_notes.append(term.replace('Note:', '').strip()); continue
        mm = re.match(r'^((?:[–-]\s*)+)', term)
        lvl = len(re.findall('[–-]', mm.group(1))) if mm else 0
        t = term[mm.end():].strip() if mm else term
        indent = (term_sp[0][0] - m) if term_sp else 0
        if neo_rows and (not mm and indent > 5 or not t) and not term.startswith('Neoplasm'):
            r = neo_rows[-1]
            if t:
                r[1] = (r[1] + ' ' + t).strip()
            r[2:7] = [a or b for a, b in zip(r[2:7], vals)]
            continue
        neo_rows.append([lvl, t.replace('', '◊').strip()] + vals + [0])
# paragraphs of the notes
paras = []
for t in neo_notes:
    if re.match(r'^\d\.\s', t) or not paras:
        paras.append(t)
    else:
        paras[-1] += ' ' + t
neo_notes = [p.replace('', '◊') for p in paras]

# ---------------------------------------------------------------- plain index (two columns)
def columns(p):
    m = margin(p)
    cut = table_cut.get(p)
    cols = [[], []]
    from collections import Counter
    starts = Counter(round(s[0]) for l in body(p) for s in l['spans'] if m + 160 <= s[0] <= m + 195 and s[1].strip().startswith('–'))
    split = (starts.most_common(1)[0][0] - 3) if starts else m + 175
    for l in body(p):
        if cut is not None and l['y'] < cut:
            continue
        for k, rng in enumerate(((m - 5, split), (split, m + 400))):
            sp = [s for s in l['spans'] if rng[0] <= s[0] < rng[1]]
            if sp:
                cols[k].append((l['y'], sp, m if k == 0 else split + 2))
    return cols[0] + cols[1]


entries = []
for rng, sec in ((SEC1, 'I'), (SEC2, 'II')):
    for p in rng:
        if p in table_cut and table_cut[p] > 10 ** 5:
            continue
        for y, sp, cx in columns(p):
            t = join_spans(sp)
            if not t or re.search(r'continued$', t) or re.fullmatch(r'[A-Z]|\d+', t):
                continue
            indent = sp[0][0] - cx
            mm = re.match(r'^((?:[–-]\s*)+)', t)
            if not mm and indent > 5 and entries:
                prev = entries[-1]
                joined = (prev[1] + ' ' + ' '.join(c for c in prev[2:4] if c) + ' ' + t).strip() if prev[2] else (prev[1] + ' ' + t).strip()
                joined = ' '.join(joined.split())
                mt = CODE_TAIL.search(' ' + joined)
                if mt:
                    cs = mt.group(1).split()
                    prev[1] = joined[:len(joined) - len(mt.group(1))].strip()
                    prev[2] = cs[0]; prev[3] = cs[1] if len(cs) > 1 else None
                else:
                    prev[1] = joined
                continue
            lvl = len(re.findall('[–-]', mm.group(1))) if mm else 0
            text = t[mm.end():].strip() if mm else t
            c1 = c2 = None
            mt = CODE_TAIL.search(' ' + text)
            if mt:
                cs = mt.group(1).split()
                c1 = cs[0]; c2 = cs[1] if len(cs) > 1 else None
                text = text[:len(text) - len(mt.group(1))].strip()
            entries.append([lvl, text, c1, c2, sec, 0])
for e in entries:
    for i in (2, 3):
        if e[i]:
            e[i] = e[i].replace('.-', '').rstrip('-')

# ---------------------------------------------------------------- drugs
def drug_col(c):
    if c.startswith('T'):
        return 0
    n = int(c[1:3])
    if c[0] == 'X' and 40 <= n <= 49:
        return 1
    if c[0] == 'X' and 60 <= n <= 69:
        return 2
    if c[0] == 'Y' and 10 <= n <= 19:
        return 3
    if c[0] == 'Y' and 40 <= n <= 59:
        return 4
    return None


drugs = []
for p in DRUG:
    for l in body(p):
        if l['y'] < 236 and any(s[1].startswith(('Substance', 'Poisoning', 'Intentional', 'in therapeutic', 'use', 'Adverse')) for s in l['spans']):
            continue
        sp = l['spans']
        term_sp = [s for s in sp if not CODE_ONLY.match(s[1].strip()) and s[1].strip() not in ('–', '-')]
        code_sp = [s for s in sp if CODE_ONLY.match(s[1].strip())]
        term = join_spans(term_sp)
        if not term and not code_sp:
            continue
        if re.fullmatch(r'[A-Z]|\d+|TABLE OF DRUGS AND CHEMICALS', term):
            continue
        vals = [''] * 5
        for s in code_sp:
            for c in s[1].split():
                k = drug_col(c)
                if k is not None:
                    vals[k] = c
        mm = re.match(r'^((?:[–-]\s*)+)', term)
        lvl = len(re.findall('[–-]', mm.group(1))) if mm else 0
        t = term[mm.end():].strip() if mm else term
        if drugs and not mm and t and t[:1].islower() and not any(drugs[-1][2:7]) is False and term_sp and term_sp[0][0] > 76:
            drugs[-1][1] += ' ' + t
            drugs[-1][2:7] = [a or b for a, b in zip(drugs[-1][2:7], vals)]
            continue
        if drugs and not t and any(vals):
            drugs[-1][2:7] = [a or b for a, b in zip(drugs[-1][2:7], vals)]
            continue
        drugs.append([lvl, t] + vals + [0])

json.dump({'entries': entries, 'neoplasm': {'rows': neo_rows, 'notes': neo_notes}, 'drugs': {'rows': drugs}},
          open('/home/claude/who/who_index.json', 'w', encoding='utf8'), ensure_ascii=False)
print('entries', len(entries), 'sec II', sum(1 for e in entries if e[4] == 'II'), 'with code', sum(1 for e in entries if e[2]))
print('neoplasm rows', len(neo_rows), 'notes', len(neo_notes), 'table pages', sorted(table_cut)[:3], '...', sorted(table_cut)[-3:])
print('drugs rows', len(drugs))
