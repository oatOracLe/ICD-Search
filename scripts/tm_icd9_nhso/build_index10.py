"""Turn index10.json into web files:
  data/idx10/manifest.json           sections → letters → entry counts
  data/idx10/<sec>-<L>.json          [[level, text, code1, code2, tm], ...]
  data/icd10-kw.json                 {code: "index terms"} used as extra search keywords
"""
import json, os, re
from collections import defaultdict

OUT = '/home/claude/icd-site/data/icd10/index'
os.makedirs(OUT, exist_ok=True)
E = json.load(open('/home/claude/src/index10.json', encoding='utf8'))
codes = {c['c'] for c in json.load(open('/home/claude/icd-site/data/icd10/codes.json', encoding='utf8'))['codes']}

# point the plain index at the tables that were cut out of it
def insert_after(pred, row):
    for i, e in enumerate(E):
        if pred(e):
            E.insert(i + 1, row); return True
    return False
insert_after(lambda e: e[0] == 0 and e[1].startswith('Abortion (complete)'), [1, 'complicated (by) — ดูตารางภาวะแทรกซ้อนของการแท้ง', 'TABLE:abortion', None, 'I', False])
pos = next(i for i, e in enumerate(E) if e[0] == 0 and e[4] == 'I' and e[1] > 'Neoplasm' and e[1][0] == 'N' and not e[1].startswith('Neoplasia'))
E.insert(pos, [0, 'Neoplasm, neoplastic — ดูตารางเนื้องอก', 'TABLE:neoplasm', None, 'I', False])
by = defaultdict(list)
cur_letter = {'I': 'A', 'II': 'A'}
stack = []
kw = defaultdict(list)
for lvl, text, c1, c2, sec, tm in E:
    if lvl == 0 and text:
        ch = text[0].upper()
        if 'A' <= ch <= 'Z':
            cur_letter[sec] = ch
    by[(sec, cur_letter[sec])].append([lvl, text, c1, c2, 1 if tm else 0])
    stack = stack[:lvl] + [text]
    if c1 and not c1.startswith('TABLE:'):
        base = c1.rstrip('†*')
        if base in codes:
            path = ' '.join(re.sub(r'\s*-\s*see.*$', '', s) for s in stack)
            kw[base].append(path)

manifest = {'sections': {'I': 'โรคและลักษณะการบาดเจ็บ', 'II': 'สาเหตุภายนอกของการบาดเจ็บ'}, 'letters': {}}
for (sec, L), rows in sorted(by.items()):
    json.dump(rows, open(f'{OUT}/{sec}-{L}.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    manifest['letters'].setdefault(sec, {})[L] = len(rows)
json.dump(manifest, open(f'{OUT}/manifest.json', 'w', encoding='utf8'), ensure_ascii=False)

STOP = {'see', 'also', 'code', 'with', 'without', 'fourth', 'character', 'and', 'the', 'for', 'due', 'other', 'condition'}
kwout = {}
for c, paths in kw.items():
    words, seen = [], set()
    for p in paths:
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p.lower()):
            if w not in seen and len(w) > 2 and w not in STOP:
                seen.add(w); words.append(w)
    kwout[c] = ' '.join(words)[:400]
json.dump(kwout, open('/home/claude/icd-site/data/icd10/keywords.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('files', len(by), 'kw codes', len(kwout), 'manifest', {k: sum(v.values()) for k, v in manifest['letters'].items()})
