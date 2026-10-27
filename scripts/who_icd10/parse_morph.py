"""ICD-O morphology codes (M8000/0 ...) from the ICD-10-TM 2009 book, pages 922-929
('Coded nomenclature for morphology of neoplasms', reproduced from ICD-O-2 as in WHO ICD-10 up to 2015).

S0052 (WHO ICD-10 2016) no longer prints this list; its explanatory text and the behaviour-code
table are used for the notes.

Writes /home/claude/icd-site/data/icd10/morph.json:
  {groups: [{id, en}], codes: [{c, g, en, beh, site, siteCode}], behaviour: [...], note_th, note_en}
"""
import json, re
import pymupdf

SRC = '/mnt/user-data/uploads/-10-TM_2009_AllOK.pdf'
d = pymupdf.open(SRC)
CODE = re.compile(r'^M\d{4}/\d$')
GRP = re.compile(r'^M\d{3}(?:\s*[-–]\s*M\d{3})?$')

lines = []
for p in range(922, 930):
    pg = d[p - 1]
    rows = []
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            y = l['bbox'][1]
            if not t or y < 60 or y > 780:
                continue
            rows.append((round(y), l['bbox'][0], t, 'Bold' in l['spans'][0]['font'] or 'Tahoma' in l['spans'][0]['font']))
    rows.sort()
    xs = sorted(r[1] for r in rows if CODE.match(r[2]) or GRP.match(r[2]))
    if not xs:
        continue
    cols = [xs[0]]
    for x in xs:
        if x - cols[-1] > 100:
            cols.append(x)
    for ci, cx in enumerate(cols):
        hi = cols[ci + 1] - 5 if ci + 1 < len(cols) else 10 ** 4
        merged = []
        for y, x, t, b in rows:
            if not (cx - 5 <= x < hi):
                continue
            if merged and abs(merged[-1][0] - y) <= 2:
                merged[-1][2].append((x, t))
            else:
                merged.append([y, b, [(x, t)]])
        for y, b, parts in merged:
            parts.sort()
            left = [t for x, t in parts if x < cx + 40]
            right = ' '.join(t for x, t in parts if x >= cx + 40)
            lines.append((p, left[0] if left else '', right))

groups, codes = [], []
cur_g = None
for p, left, right in lines:
    if CODE.match(left):
        codes.append({'c': left, 'g': cur_g, 'en': right})
    elif GRP.match(left):
        cur_g = re.sub(r'\s*[-–]\s*', '–', left)
        groups.append({'id': cur_g, 'en': right})
    elif not left and right and codes and not right.startswith(('Coded nomenclature', 'of neoplasms')):
        if groups and groups[-1]['id'] == cur_g and codes[-1]['g'] != cur_g:
            groups[-1]['en'] += ' ' + right
        else:
            codes[-1]['en'] += ' ' + right

BEH = {'0': 'benign', '1': 'uncertain', '2': 'in situ', '3': 'malignant', '6': 'metastatic', '9': 'uncertain primary/metastatic'}
fixed = []
for c in codes:
    c['en'] = ' '.join(c['en'].split()).replace('’', "'")
    beh = c['c'][-1]
    # misprints in the book: behaviour digit that contradicts the term
    if 'uncertain whether benign or malignant' in c['en'] and beh != '1':
        fixed.append(c['c']); c['c'] = c['c'][:-1] + '1'; beh = '1'
    c['beh'] = beh
    m = re.search(r'\(([A-Z]\d\d(?:\.[\d-]{1,2})?)\)\s*$', c['en'])
    if m:
        c['site'] = {'C82.8': 'C82.7'}.get(m.group(1), m.group(1))
        c['en'] = c['en'][:m.start()].strip()
    if c['g'] is None:
        c['g'] = c['c'][:4]

D = json.load(open('/home/claude/icd-site/data/icd10/codes.json', encoding='utf8'))
byc = {x['c']: x for x in D['codes']}
for c in codes:
    c['en'] = c['en'].replace('Trus histiocytic', 'True histiocytic')
    s = c.get('site', '').replace('.-', '')
    if s and (byc.get(s, {}).get('who_del') or byc.get(s, {}).get('tm_old')):
        c['old'] = 1          # the site code follows ICD-10 before 2016; WHO 2016 changed or removed it
out = {
    'source': 'ICD-O-2 morphology nomenclature as printed in ICD-10-TM 2009 Tabular List (pp. 922–929); behaviour table from WHO ICD-10 2016 Vol. 1 (S0052)',
    'behaviour': [
        {'d': '0', 'en': 'Benign', 'th': 'เนื้องอกไม่ร้าย', 'chap': 'D10–D36'},
        {'d': '1', 'en': 'Uncertain whether benign or malignant (borderline, low malignant potential)', 'th': 'ไม่แน่ชัดว่าไม่ร้ายหรือร้าย', 'chap': 'D37–D48'},
        {'d': '2', 'en': 'Carcinoma in situ (intraepithelial, noninfiltrating, noninvasive)', 'th': 'มะเร็งระยะเริ่มแรก (in situ)', 'chap': 'D00–D09'},
        {'d': '3', 'en': 'Malignant, primary site', 'th': 'มะเร็ง ตำแหน่งปฐมภูมิ', 'chap': 'C00–C76, C80–C97'},
        {'d': '6', 'en': 'Malignant, metastatic site (secondary)', 'th': 'มะเร็ง ตำแหน่งที่แพร่กระจาย (ทุติยภูมิ)', 'chap': 'C77–C79'},
        {'d': '9', 'en': 'Malignant, uncertain whether primary or metastatic', 'th': 'มะเร็ง ไม่แน่ชัดว่าปฐมภูมิหรือแพร่กระจาย', 'chap': 'ใน ICD-10 ให้ถือเป็นปฐมภูมิ (/3) หรือทุติยภูมิ (/6) ตามข้อมูลในเวชระเบียน'},
    ],
    'note_th': ('รหัสสัณฐานวิทยา (ICD-O) มีห้าหลัก สี่หลักแรกบอกชนิดเนื้อเยื่อ หลักหลังเส้นเฉียงบอกพฤติกรรมของเนื้องอก '
                'ใช้คู่กับรหัสตำแหน่งในบทที่ 2 โดยเลือกคอลัมน์ในตารางเนื้องอกตามพฤติกรรม รหัสในวงเล็บคือรหัสบทที่ 2 '
                'ที่ใช้เมื่อคำวินิจฉัยไม่ระบุตำแหน่ง ถ้าระบุตำแหน่งอื่นให้ใช้รหัสตามตำแหน่งนั้น '
                'WHO เลิกพิมพ์รายการนี้ใน ICD-10 ตั้งแต่ฉบับ 2016 ควรตรวจกับ ICD-O ฉบับปัจจุบัน (ICD-O-3) ก่อนใช้'),
    'groups': groups,
    'codes': codes,
}
json.dump(out, open('/home/claude/icd-site/data/icd10/morph.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('groups', len(groups), 'codes', len(codes), 'with site', sum(1 for c in codes if c.get('site')), 'fixed', fixed)
from collections import Counter
print(Counter(c['beh'] for c in codes))
dup = [k for k, v in Counter(c['c'] for c in codes).items() if v > 1]
print('dup codes', dup[:20])
