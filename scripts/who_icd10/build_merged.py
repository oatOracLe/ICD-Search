"""Build icd10.json with WHO ICD-10 (2016 edition, with updates printed in S0052) as the reference.

- Every WHO code is present with the WHO English title.
- Thai titles and bilingual notes come from ICD-10-TM 2009 where the TM code means the same thing;
  otherwise a project translation (th_new.TH, flagged thx) is used.
- TM codes that are the same concept under another number are moved to the WHO number
  (the TM number stays as an alias flagged who_del with rep -> WHO code).
- TM codes the WHO edition no longer has are kept, flagged who_del, with replacement codes.
- TM extensions (# codes, TM 5th characters, template-generated 4th characters) are kept, flagged tm/gen.
"""
import json, re, difflib, copy
from th_new import TH, EN_FIX
from thfix import fix_all, fix

T = json.load(open('/home/claude/who/icd10_tm_backup.json', encoding='utf8'))
W = json.load(open('/home/claude/who/who_tab.json', encoding='utf8'))
X = json.load(open('/home/claude/who/who_index.json', encoding='utf8'))
fix_all(T)

wb = {}
for c in W['codes']:
    if c['c'] not in wb or len(c['notes']) >= len(wb[c['c']]['notes']):
        wb[c['c']] = c
tb = {c['c']: c for c in T['codes']}

# ---------- English title clean-up (lost fi/fl ligatures, run-in text from the next line)
vocab = set()
for c in T['codes']:
    vocab.update(re.findall(r"[a-z]+", c['en'].lower()))
for c in wb.values():
    vocab.update(re.findall(r"[a-z]+", c['en'].lower()))
freq = {}
for c in wb.values():
    for w in re.findall(r"[a-z]+", c['en'].lower()):
        freq[w] = freq.get(w, 0) + 1


def fix_en(s):
    def rep(m):
        w = m.group(0)
        lw = w.lower()
        if freq.get(lw, 0) > 2:
            return w
        for i, ch in enumerate(lw):
            if ch == 'f':
                for ins in ('i', 'l'):
                    cand = lw[:i + 1] + ins + lw[i + 1:]
                    if cand in vocab and freq.get(cand, 0) >= freq.get(lw, 0):
                        return w[:i + 1] + ins + w[i + 1:]
        return w
    s = re.sub(r"[A-Za-z]+", rep, s)
    s = re.sub(r'\s+(Incl\.:|Excl\.:).*$', '', s)
    s = re.sub(r'\s+[A-Z]\d\d(\.\d)?$', '', s)          # next category number run into the title
    return ' '.join(s.split())


for k, c in wb.items():
    c['en'] = EN_FIX.get(k) or fix_en(c['en'])
    for n in c['notes']:
        n['en'] = [fix_en(x) for x in n['en']]


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower().replace('’', '').replace("'", ''))


def sim(a, b):
    a, b = norm(a), norm(b)
    return 1.0 if (a == b) else difflib.SequenceMatcher(None, a, b).ratio()


# ---------- same concept under a different number in TM (or a misread code)
RENAME = {'H33.9': 'H33.5', 'I05.3': 'I05.8', 'I84.6': 'K64.4', 'J03.1': 'J03.8', 'K35.0': 'K35.2',
          'N84.4': 'N84.8', 'O80.2': 'O80.8', 'R04.3': 'R04.8', 'S19.0': 'S19.7', 'T53.8': 'T53.9'}
MISREAD = {'O04.0': 'C04.0'}      # TM data had the C04.0 line under a wrong letter
REP = {  # TM 2009 codes the WHO edition no longer has -> codes to use instead
    'A90': ['A97.0', 'A97.9'], 'A91': ['A97.1', 'A97.2'],
    'I84': ['K64'], 'I84.0': ['K64.5', 'K64.8'], 'I84.1': ['K64.8'], 'I84.2': ['K64.9'], 'I84.3': ['K64.5'],
    'I84.4': ['K64.8'], 'I84.5': ['K64.9'], 'I84.7': ['K64.5'], 'I84.8': ['K64.8'], 'I84.9': ['K64.9'],
    'K35.1': ['K35.3'], 'K35.9': ['K35.8'], 'N18.0': ['N18.5'], 'C14.1': ['C13.9'],
    'D75.2': ['D47.3'], 'D76.0': ['C96.5', 'C96.6'], 'G90.3': ['G23.2', 'G23.3'], 'H54.7': ['H54.9'],
    'L41.2': ['C86.6'], 'C94.5': ['C94.4'], 'C96.1': ['C96.8'], 'D46.3': ['C92.0'], 'C94.1': ['D45'],
    'Q35.0': ['Q35.1'], 'Q35.2': ['Q35.3'], 'Q35.4': ['Q35.5'], 'Q35.6': ['Q35.5'], 'Q35.8': ['Q35.9'],
    'R50.0': ['R50.8'], 'R50.1': ['R50.8'], 'S32.6': ['S32.8'], 'Z22.5': ['B18.1', 'B18.2'],
    'U80': ['U82'], 'U80.0': ['U82.0'], 'U80.1': ['U82.1'], 'U80.8': ['U82.8'], 'U81': ['U83'], 'U81.0': ['U83.0'],
    'U81.8': ['U83.1'], 'U88': ['U83.7'], 'U89': ['U83'], 'U89.8': ['U83.8'], 'U89.9': ['U83.9'],
}
for a, b in RENAME.items():
    REP.setdefault(a, [b])

codes = {}
for k, w in wb.items():
    src = None
    if k in tb:
        src = tb[k]
    else:
        old = next((a for a, b in list(RENAME.items()) + list(MISREAD.items()) if b == k), None)
        if old:
            src = tb[old]
    x = {'c': k, 'en': w['en'], 'th': '', 'who': 1}
    if w['dag']:
        x['da'] = w['dag']
    same = src is not None and (sim(w['en'], src['en']) >= 0.75 or norm(src['en']) in norm(w['en']) or norm(w['en']) in norm(src['en']))
    if same:
        x['th'] = src['th'] or TH.get(k, '')
        if not src['th'] and k in TH:
            x['thx'] = 1
        x['notes'] = src.get('notes') or [{'t': n['t'], 'en': n['en']} for n in w['notes'] if n['en']]
    else:
        x['th'] = TH.get(k, '')
        if k in TH:
            x['thx'] = 1
        x['notes'] = [{'t': n['t'], 'en': n['en']} for n in w['notes'] if n['en']]
        if src is not None:
            x['tm_old'] = {'en': src['en'], 'th': src['th']}
    if src is not None and src.get('place'):
        x['place'] = src['place']
    if src is not None and src.get('bad'):
        x['tm_bad'] = 1                      # TM 2009 marks it '@' (not for use in Thailand); WHO keeps it
    if src is not None and src.get('tm'):
        x['tm_mark'] = 1                     # printed with '#' in TM 2009 although WHO has the code
    if not x['notes']:
        x.pop('notes')
    codes[k] = x

# TM records with no WHO counterpart
for k, t in tb.items():
    if k in codes or k in MISREAD:
        continue
    x = copy.deepcopy(t)
    x.pop('leaf', None); x.pop('b', None); x.pop('p', None)
    cat = k[:3]
    if k in REP or (cat in REP and cat not in wb):
        x['who_del'] = 1
        x['rep'] = REP.get(k) or REP.get(cat, [])
    elif t.get('gen') and cat in wb:
        pass                                   # 4th character from a WHO subdivision template
    elif t.get('tm'):
        pass                                   # TM extension (#)
    elif cat in wb and (len(k) == 6 and k[:5] in wb or len(k) == 5 and not any(c.startswith(cat + '.') for c in wb)):
        x['tm'] = True                         # TM subdivision of a WHO code that has none
    else:
        x['who_del'] = 1
        x['rep'] = []
    codes[k] = x

# misread code: O04.0 is a template code like O03.0
if 'O04.0' not in codes and 'O03.0' in codes:
    o = copy.deepcopy(codes['O03.0'])
    o.update({'c': 'O04.0', 'gen': True})
    o['en'] = o['en'].replace('Spontaneous abortion', 'Medical abortion')
    o['th'] = o['th'].replace('การแท้งที่เกิดขึ้นเอง', 'การทำแท้งโดยแพทย์')
    o.pop('who', None)
    codes['O04.0'] = o

# 4th characters printed once per block ("[See before X for subdivisions]") that TM did not generate
def see_before(x):
    return any('See before' in s for n in x.get('notes', []) for s in n.get('en', []))


for k in list(codes):
    x = codes[k]
    if len(k) == 3 and see_before(x) and not any(c.startswith(k + '.') for c in codes):
        m = next((re.search(r'See before ([A-Z]\d\d)', s) for n in x['notes'] for s in n['en'] if 'See before' in s), None)
        sib = None
        if m:
            first = m.group(1)
            sib = next((c for c in sorted(codes) if c[:3] >= first and c[:3] < k and any(d.startswith(c + '.') for d in codes) and see_before(codes[c])), None)
        if sib:
            for d in sorted(c for c in codes if c.startswith(sib + '.') and len(c) == 5):
                y = copy.deepcopy(codes[d])
                y['c'] = k + d[3:]
                y['gen'] = True
                y['en'] = y['en'].replace(codes[sib]['en'], x['en'])
                y['th'] = y['th'].replace(codes[sib]['th'], x['th']) if codes[sib]['th'] and x['th'] else ''
                y.pop('who', None)
                codes[y['c']] = y

# codes referenced by the WHO index that only exist as template subdivisions
refs = set()
for e in X['entries']:
    for c in e[2:4]:
        if c:
            refs.add(c.rstrip('†*'))
for r in X['neoplasm']['rows'] + X['drugs']['rows']:
    for c in r[2:7]:
        if c:
            refs.add(c.rstrip('†*'))
added_ref = []
for r in sorted(refs):
    if r not in codes and re.fullmatch(r'[A-Z]\d\d\.\d', r) and r[:3] in codes:
        sib = next((c for c in sorted(codes) if c[3:] == r[3:] and codes[c].get('gen') and c[:1] == r[:1]), None)
        if sib:
            y = copy.deepcopy(codes[sib]); y['c'] = r; y['gen'] = True
            ps, pr = codes[sib[:3]], codes[r[:3]]
            y['en'] = y['en'].replace(ps['en'], pr['en'])
            y['th'] = y['th'].replace(ps['th'], pr['th']) if ps['th'] and pr['th'] else ''
            codes[r] = y; added_ref.append(r)

# ---------- E10/E11 renamed by WHO: carry the new wording into generated 4th characters
for k, x in codes.items():
    if k[:3] in ('E10', 'E11') and x.get('gen'):
        x['en'] = x['en'].replace('Non-insulin-dependent diabetes mellitus', 'Type 2 diabetes mellitus').replace('Insulin-dependent diabetes mellitus', 'Type 1 diabetes mellitus')
        x['th'] = x['th'].replace('เบาหวานชนิดไม่พึ่งอินซูลิน', 'เบาหวานชนิดที่ 2').replace('เบาหวานชนิดพึ่งอินซูลิน', 'เบาหวานชนิดที่ 1')

# ---------- blocks, parents, leaves
blocks = T['blocks']


def rng(b):
    lo, _, hi = b['id'].partition('-')
    return lo, (hi or lo)


def find_block(cat):
    for b in blocks:
        lo, hi = rng(b)
        if len(lo) == 3 and lo <= cat <= hi:
            return b['id']
    return None


for b in blocks:   # widen blocks WHO extended (e.g. B95-B97 -> B95-B98)
    pass
for k, x in codes.items():
    cat = k[:3]
    bid = find_block(cat)
    if not bid:
        cand = [b for b in blocks if b['id'][:1] == cat[:1] and len(rng(b)[1]) == 3 and rng(b)[1] < cat]
        if cand:
            b = max(cand, key=lambda b: rng(b)[1])
            lo, hi = rng(b)
            b['range'] = f'{lo}–{cat}'
            b['wid'] = f'{lo}-{cat}'
            bid = b['id']
    x['b'] = bid
    if len(k) == 5 and k[:3] in codes:
        x['p'] = k[:3]
    elif len(k) == 6 and k[:5] in codes:
        x['p'] = k[:5]
    elif len(k) == 6 and k[:3] in codes:
        x['p'] = k[:3]
kids = {}
for k, x in codes.items():
    if x.get('p'):
        kids[x['p']] = kids.get(x['p'], 0) + 1
for k, x in codes.items():
    x['leaf'] = not kids.get(k)

# ---------- note text: misprinted references, and TM code lines that ended up inside notes
NOTE_FIX = {'A18.43†': 'A18.4†', 'N18.8†': 'N18.5†', 'B06.6†': 'B06.0†', '(A69.10)': '(A69.1)', '(D76.00)': '(C96.6)',
            '(M26.3)': '(M62.3)', '(S52.02)': '(S52.0)'}
for x in codes.values():
    for n in x.get('notes', []):
        keep_en, keep_th = [], []
        ths = n.get('th') or []
        for i, s in enumerate(n.get('en', [])):
            if s.lstrip().startswith('@#') or s.lstrip().startswith('@ #'):
                continue
            for a, b in NOTE_FIX.items():
                s = s.replace(a, b)
            keep_en.append(s)
            if i < len(ths):
                keep_th.append(ths[i])
        n['en'] = keep_en
        if 'th' in n and len(ths) == len(n.get('en', [])) + 0:
            pass
        if 'th' in n:
            n['th'] = [t for t in ths if not t.lstrip().startswith('@')]
            for a, b in NOTE_FIX.items():
                n['th'] = [t.replace(a, b) for t in n['th']]

# block titles: WHO 2016 renamed a few; keep TM Thai
order = sorted(codes.values(), key=lambda x: (x['c'][:3], x['c']))
out = dict(T)
out['codes'] = order
out['blocks'] = blocks
out['version'] = 'WHO 2016 (ชื่อไทยจาก TM 2009)'
out['label'] = 'ICD-10'
out['source'] = ('ICD-10 WHO ฉบับ 2016 (Volume 1, เอกสาร S0052 รวมรหัสที่ WHO ปรับปรุงภายหลัง) เป็นหลัก '
                 'ชื่อภาษาไทยและหมายเหตุสองภาษาจาก ICD-10-TM 2009 รหัสที่ TM เพิ่มเอง (#) ยังเก็บไว้และติดป้าย TM')
json.dump(out, open('/home/claude/icd-site/data/icd10/codes.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

n_who = sum(1 for x in codes.values() if x.get('who'))
print('codes', len(codes), 'WHO', n_who, 'TM ext', sum(1 for x in codes.values() if x.get('tm') and not x.get('who')),
      'gen', sum(1 for x in codes.values() if x.get('gen')), 'who_del', sum(1 for x in codes.values() if x.get('who_del')),
      'thx', sum(1 for x in codes.values() if x.get('thx')), 'no th', sum(1 for x in codes.values() if not x['th']),
      'no block', [k for k, x in codes.items() if not x['b']][:10], 'added from index', added_ref[:20])
print('who_del without rep:', sorted(k for k, x in codes.items() if x.get('who_del') and not x['rep']))
