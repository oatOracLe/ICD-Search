"""Add the Thai names of ICD-9-CM chapters, blocks and codes to data/icd9/codes.json.

The ICD-9-CM book has no Thai. icd9_th.tsv holds a Thai rendering made for this website (not an official
translation), written with a Thai-English medical-terms glossary as the terminology reference.
Line format:  key<TAB>Thai   key = ch:<chapter id> | bl:<block id> | <code>
Every name written here gets "thx": 1 so the app shows that it is an unofficial translation.
Usage: python3 icd9_th.py [path/to/data]   (default ../../web/data, or $ICD_DATA)"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ICD_DATA', os.path.join(HERE, '..', '..', 'web', 'data'))
TH = {}
for line in open(os.path.join(HERE, 'icd9_th.tsv'), encoding='utf8'):
    if line.strip():
        k, v = line.rstrip('\n').split('\t')
        TH[k] = v.strip()

path = os.path.join(DATA, 'icd9', 'codes.json')
d = json.load(open(path, encoding='utf8'))
used, miss = set(), []
for kind, key, rows in (('ch', 'id', d['chapters']), ('bl', 'id', d['blocks']), ('', 'c', d['codes'])):
    for x in rows:
        k = (kind + ':' if kind else '') + x[key]
        if k in TH:
            x['th'] = TH[k]; x['thx'] = 1; used.add(k)
        elif not x.get('th'):
            miss.append(k)
src = d.get('source', '')
NOTE = 'ชื่อภาษาไทยแปลเพิ่มสำหรับเว็บนี้ ไม่ใช่ฉบับทางการ'
if NOTE not in src:
    d['source'] = src + ' · ' + NOTE
json.dump(d, open(path, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('thai names', len(used), 'of', len(TH), '| rows still without Thai', len(miss), miss[:10])
