"""Remove ICD-10 codes that exist only in ICD-10-TM 2009 (not in WHO ICD-10 2016).

Removed:  TM extensions (flag tm, e.g. H36.00, J45.2) and TM 2009 codes WHO 2016 no longer has (flag who_del, e.g. A91).
Kept:     every WHO code, and 4th characters generated from WHO subdivision lists (flag gen) because WHO defines them
          once per block instead of under each category.

Used by build_merged.py, and runnable on the published data:
    python3 scripts/who_icd10/drop_tm_only.py web/data/icd10/codes.json
"""
import json
import sys

SOURCE = ('ICD-10 WHO ฉบับ 2016 (Volume 1, เอกสาร S0052 รวมรหัสที่ WHO ปรับปรุงภายหลัง) เป็นหลัก '
          'ชื่อภาษาไทยและหมายเหตุสองภาษาจาก ICD-10-TM 2009 ไม่รวมรหัสที่มีเฉพาะใน ICD-10-TM 2009')


def tm_only(x):
    return not x.get('who') and bool(x.get('tm') or x.get('who_del'))


def drop_tm_only(doc):
    codes = doc['codes']
    gone = {x['c'] for x in codes if tm_only(x)}
    keep = [x for x in codes if x['c'] not in gone]
    have_kids = {x['p'] for x in keep if x.get('p')}
    for x in keep:
        if x.get('p') in gone:          # never happens today; keep the tree valid if it ever does
            x.pop('p')
        x['leaf'] = x['c'] not in have_kids
        for k in ('tm', 'who_del', 'rep'):
            x.pop(k, None)
    doc['codes'] = keep
    doc['source'] = SOURCE
    return sorted(gone)


if __name__ == '__main__':
    path = sys.argv[1]
    doc = json.load(open(path, encoding='utf8'))
    before = len(doc['codes'])
    gone = drop_tm_only(doc)
    json.dump(doc, open(path, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{path}: {before} -> {len(doc["codes"])} codes, removed {len(gone)}')
