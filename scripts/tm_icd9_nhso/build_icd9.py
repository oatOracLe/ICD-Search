"""Build /home/claude/icd-site/data/icd9/codes.json from icd9_parsed.json."""
import json, re
from collections import defaultdict

P = json.load(open('/home/claude/src/icd9_parsed.json', encoding='utf8'))
CH_EN = {}
chapters = []
for c in P['chapters']:
    title = c['title'].title().replace(' And ', ' and ').replace(' On ', ' on ').replace(' The ', ' the ').replace(' Of ', ' of ').replace(' Not ', ' not ')
    chapters.append({'id': c['id'], 'range': c['range'], 'en': title, 'th': '', 'notes': [{'t': n['t'], 'en': n['items']} for n in c['notes']]})
# fill missing chapter ranges from category ids
ch_cats = defaultdict(list)
for k in P['cats']:
    ch_cats[k['ch']].append(k['id'])
for c in chapters:
    if not c['range'] and ch_cats.get(c['id']):
        ids = sorted(ch_cats[c['id']])
        c['range'] = ids[0] + ('–' + ids[-1] if len(ids) > 1 else '')

blocks = [{'id': k['id'], 'ch': k['ch'], 'range': k['id'], 'en': k['title'], 'th': '',
           'notes': [{'t': n['t'], 'en': n['items']} for n in k['notes']]} for k in P['cats']]
codes = []
allc = {c['c'] for c in P['codes']}
kids = defaultdict(int)
for c in P['codes']:
    a, b = c['c'].split('.')
    p = f'{a}.{b[0]}' if len(b) == 2 and f'{a}.{b[0]}' in allc else None
    if p:
        kids[p] += 1
for c in P['codes']:
    a, b = c['c'].split('.')
    p = f'{a}.{b[0]}' if len(b) == 2 and f'{a}.{b[0]}' in allc else None
    x = {'c': c['c'], 'b': a, 'en': c['title'], 'th': '', 'leaf': kids[c['c']] == 0}
    if c.get('gen'):
        x['gen'] = True
    if p:
        x['p'] = p
    if c['box']:
        x['drg'] = c['box']          # 'or' = OR procedure, 'drg' = non-OR but affects ThaiDRG
    notes = [{'t': n['t'], 'en': n['items']} for n in c['notes'] if n['items']]
    if notes:
        x['notes'] = notes
    codes.append(x)

out = {'system': 'icd9', 'label': 'ICD-9-CM', 'kind': 'procedure', 'version': 'FY15 (ThaiDRG)', 'sample': False,
       'source': 'ICD-9-CM Tabular List of Procedures FY15 พร้อมเครื่องหมาย OR / ThaiDRG (เอกสาร S0034, แปลงด้วย OCR)',
       'ocr': True, 'chapters': chapters, 'blocks': blocks, 'codes': codes}
json.dump(out, open('/home/claude/icd-site/data/icd9/codes.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('chapters', len(chapters), 'blocks', len(blocks), 'codes', len(codes), 'leaf', sum(c['leaf'] for c in codes),
      'or', sum(1 for c in codes if c.get('drg') == 'or'), 'drg', sum(1 for c in codes if c.get('drg') == 'drg'))
