"""Web files for the ICD-10 index and tables from the WHO 2016 index (who_index.json).

  data/idx10/manifest.json, data/idx10/<sec>-<L>.json   [[level, text, code1, code2, tm], ...]
  data/icd10-kw.json                                      {code: "index words"} for search
  data/tables10.json                                      drugs + neoplasm from WHO; abortion 4th-character table kept
"""
import json, os, re, shutil
from collections import defaultdict

X = json.load(open('/home/claude/who/who_index.json', encoding='utf8'))
D = json.load(open('/home/claude/icd-site/data/icd10/codes.json', encoding='utf8'))
OLD_T = json.load(open('/home/claude/who/tables10_tm_backup.json', encoding='utf8'))
codes = {c['c'] for c in D['codes']}
OUT = '/home/claude/icd-site/data/icd10/index'
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)

E = [e for e in X['entries'] if not e[1].startswith('Section I') and len(re.findall(r'\b[VWXY]\d\d\b|[A-Z]\d\d\.\d', e[1])) < 4]


def insert_after(pred, row):
    for i, e in enumerate(E):
        if pred(e):
            E.insert(i + 1, row)
            return True
    return False


insert_after(lambda e: e[0] == 0 and e[1].startswith('Abortion'), [1, 'complicated (by) — ดูตารางภาวะแทรกซ้อนของการแท้ง', 'TABLE:abortion', None, 'I', 0])
pos = next(i for i, e in enumerate(E) if e[0] == 0 and e[4] == 'I' and e[1] > 'Neoplasm' and e[1][0] == 'N' and not e[1].startswith('Neoplasia'))
E.insert(pos, [0, 'Neoplasm, neoplastic — ดูตารางเนื้องอก', 'TABLE:neoplasm', None, 'I', 0])

_pa = next(i for i, e in enumerate(E) if e[4] == 'II' and e[0] == 0 and e[1].startswith('Accident'))
E.insert(_pa + 1, [1, 'transport (land) — ดูตารางอุบัติเหตุการขนส่งทางบก', 'TABLE:transport', None, 'II', 0])
by = defaultdict(list)
cur = {'I': 'A', 'II': 'A'}
stack, kw = [], defaultdict(list)
for lvl, text, c1, c2, sec, tm in E:
    if lvl == 0 and text and 'A' <= text[0].upper() <= 'Z':
        cur[sec] = text[0].upper()
    by[(sec, cur[sec])].append([lvl, text, c1, c2, 0])
    stack = stack[:lvl] + [text]
    for c in (c1, c2):
        if c and not c.startswith('TABLE:'):
            base = c.rstrip('†*')
            if base in codes:
                kw[base].append(' '.join(re.sub(r'\s*[–-]\s*see.*$', '', s) for s in stack))
manifest = {'sections': {'I': 'โรคและลักษณะการบาดเจ็บ', 'II': 'สาเหตุภายนอกของการบาดเจ็บ'}, 'letters': {}, 'source': 'WHO ICD-10 2016 Alphabetical Index'}
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

# ---- tables
neo = X['neoplasm']['rows']
first_sub = next(i for i, r in enumerate(neo) if r[0] >= 1)
head = next(r for r in neo[:first_sub] if r[1].startswith('Neoplasm'))
neo = [head] + neo[first_sub:]
clean = []
for r in neo:
    r[1] = r[1].replace('\uf0b2', '◊')
    if clean and r[0] == 0 and not any(r[2:7]):
        if r[1].startswith('Neoplasm'):
            continue
        prev = clean[-1]
        if len(prev) < 9:
            prev.append(r[1])
        else:
            prev[8] += ' ' + r[1]
        continue
    clean.append(r)
NEO_NOTES = {
    'bone': 'Note – Carcinomas and adenocarcinomas, of any type other than intraosseous or odontogenic, of the sites listed under “Neoplasm, bone” should be considered as metastatic from an unspecified primary site and coded to C79.5.',
    'connective tissue': 'Note – For neoplasms of connective tissue (blood vessels, bursa, fascia, ligament, muscle, peripheral nerves, sympathetic and parasympathetic nerves and ganglia, synovia, tendon, etc.) or of morphological types that indicate connective tissue, code according to the list under “Neoplasm, connective tissue”; for sites that do not appear in this list, code to neoplasm of that site, e.g. fibrosarcoma, pancreas C25.9; leiomyosarcoma, stomach C16.9. Morphological types that indicate connective tissue appear in their proper place in the alphabetical index with the instruction “see Neoplasm, connective tissue, …”.',
    'skin': 'Note – For neoplasms of skin or of morphological types that indicate skin, code according to the list under “Neoplasm, skin”; for sites that do not appear in this list, code to neoplasm of that site, e.g. basal cell carcinoma, palate C05.9. Morphological types that indicate skin appear in their proper place in the alphabetical index with the instruction “see Neoplasm, skin, …”.',
}
for r in clean:
    if len(r) > 8:
        key = next((k for k in NEO_NOTES if r[1].startswith(k)), None)
        if key:
            r[8] = NEO_NOTES[key]
neo = clean
drugs = [r for r in X['drugs']['rows'] if not (r[0] == 0 and re.fullmatch(r'[A-Z]', r[1]) and not any(r[2:7]))]
tables = dict(OLD_T)
tables['drugs'] = dict(OLD_T['drugs'], rows=drugs)
tables['neoplasm'] = dict(OLD_T['neoplasm'], rows=neo)
tables['drugs']['src'] = tables['neoplasm']['src'] = 'WHO ICD-10 2016 Alphabetical Index'
tables['abortion']['src'] = 'ICD-10-TM 2009 Alphabetical Index'
# ---- Table of land transport accidents (WHO Index Section II, printed sideways on p. 680; read from the page image)
def vrow(lvl, en, th, base):
    return [lvl, en + ' — ' + th] + base + [0]
rng = lambda a: ['V%02d' % (a + k) for k in (0, 1, 2, 3, 4, 9, 5, 6, 7, 8, 9)]
transport_rows = [
    [0, 'Pedestrian — คนเดินเท้า', '(W51)', 'V01', 'V02', 'V03', 'V04', 'V09', 'V05', 'V06', '(W22)', '', 'V09', 0],
    vrow(0, 'Pedal cyclist', 'ผู้ใช้รถจักรยาน', rng(10)),
    vrow(0, 'Motorcycle rider', 'ผู้ใช้รถจักรยานยนต์', rng(20)),
    [0, 'Occupant of — ผู้ใช้ยานพาหนะ', '', '', '', '', '', '', '', '', '', '', '', 0],
    vrow(1, 'three-wheeled motor vehicle', 'ยานยนต์สามล้อ', rng(30)),
    vrow(1, 'car (automobile)', 'รถยนต์', rng(40)),
    vrow(1, 'pick-up truck or van', 'รถกระบะหรือรถตู้', rng(50)),
    vrow(1, 'heavy transport vehicle', 'รถบรรทุกหนัก', rng(60)),
    vrow(1, 'bus (coach)', 'รถโดยสาร', rng(70)),
    [1, 'animal-drawn vehicle (or animal rider) — พาหนะเทียมสัตว์ หรือผู้ขี่สัตว์', 'V80.1', 'V80.2', 'V80.3', 'V80.4', 'V80.4', 'V80.5', 'V80.6', 'V80.7', 'V80.8', 'V80.0', 'V80.9', 0],
]
tables['transport'] = {
    'title': 'ตารางอุบัติเหตุการขนส่งทางบก', 'en': 'Table of land transport accidents', 'src': 'WHO ICD-10 2016 Alphabetical Index, Section II',
    'note': ('เลือกแถวตามผู้บาดเจ็บ (ใช้ยานพาหนะอะไร) และคอลัมน์ตามคู่กรณีหรือลักษณะอุบัติเหตุ แล้วเติมหลักที่ 4 ตามรายการในหมวด '
             'ว่าเป็นผู้ขับขี่หรือผู้โดยสาร และเป็นอุบัติเหตุจราจรหรือไม่ใช่อุบัติเหตุจราจร รหัสในวงเล็บ (W51, W22) ไม่ใช่อุบัติเหตุการขนส่ง'),
    'cols': [{'th': 'คนเดินเท้าหรือสัตว์', 'en': 'Pedestrian or animal'}, {'th': 'รถจักรยาน', 'en': 'Pedal cycle'},
             {'th': 'ยานยนต์สองหรือสามล้อ', 'en': 'Two- or three-wheeled motor vehicle'},
             {'th': 'รถยนต์ รถกระบะ หรือรถตู้', 'en': 'Car, pick-up truck or van'},
             {'th': 'รถบรรทุกหนักหรือรถโดยสาร', 'en': 'Heavy transport vehicle or bus'},
             {'th': 'ยานยนต์อื่น', 'en': 'Other motor vehicle'}, {'th': 'รถไฟ', 'en': 'Railway train or vehicle'},
             {'th': 'พาหนะไม่มีเครื่องยนต์อื่น', 'en': 'Other nonmotor vehicle incl. animal-drawn'},
             {'th': 'วัตถุที่ติดตั้งหรืออยู่กับที่', 'en': 'Fixed or stationary object'},
             {'th': 'ไม่ได้ชน', 'en': 'Noncollision transport accident'},
             {'th': 'อื่นหรือไม่ระบุ', 'en': 'Other or unspecified transport accident'}],
    'rows': transport_rows}
for r in transport_rows:
    for c in r[2:13]:
        cc = c.strip('()')
        assert not cc or cc in codes, cc
pos = next(i for i, e in enumerate(E) if e[4] == 'II' and e[0] == 0 and e[1].startswith('Accident'))
by_ii = None
json.dump(tables, open('/home/claude/icd-site/data/icd10/tables.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

# ---- consistency report
refs = defaultdict(int)
for e in E:
    for c in e[2:4]:
        if c and not c.startswith('TABLE:'):
            refs[c.rstrip('†*')] += 1
for r in neo + drugs:
    for c in r[2:7]:
        if c:
            refs[re.sub(r'[†*#]', '', c)] += 1
bad = sorted(c for c in refs if c not in codes and not re.search(r'-', c))
print('index entries', len(E), 'files', len(by), 'kw', len(kwout), 'neoplasm rows', len(neo), 'drug rows', len(drugs))
print('codes referenced but not in data:', len(bad), bad[:40])
