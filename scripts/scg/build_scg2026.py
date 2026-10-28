"""Build data/shared/scg2026.json from "แนวทางมาตรฐานการให้รหัสโรค (Standard Coding Guidelines) ฉบับปรับปรุง (2026)".

The PDF has a text layer. Lines are rebuilt from character positions so the worked-example tables
("แพทย์วินิจฉัย | Coder ให้รหัส") keep their columns: diagnosis and code stay on the same row.
Thai sara am, written in the PDF as "<consonant> <tone>า", is repaired to "ำ".
Usage: python3 build_scg2026.py <pdf> <codes.json> <out.json>
"""
import json, re, sys
import pymupdf
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import scg_layout as L

PDF, CODES, OUT = sys.argv[1:4]
codes = {c['c'] for c in json.load(open(CODES, encoding='utf8'))['codes']}
cats = {c[:3] for c in codes}
HEADS = ('เกณฑ์การวินิจฉัย', 'แนวการวินิจฉัย', 'แนวทางการวินิจฉัย', 'เกณฑ์การให้รหัส', 'แนวทางการให้รหัส', 'การให้รหัส', 'คำจำกัดความ', 'นิยาม')
ITEM = re.compile(r'^ข้อ\s*\.?\s*(\d+(?:\s*-\s*\d+)?)\s*\.?\s*(.*)$')
CODE_LIKE = re.compile(r'^([A-Z]\d\d|\d\d\.\d|M\d{4}|\d{4,5}/)')
THAI = re.compile(r'[฀-๿]')

def join_text(a, b):
    if not a: return b
    return a + ('' if THAI.match(a[-1]) and THAI.match(b[0]) else ' ') + b

def merge_table(rows):
    out = []
    for r in rows:
        r = (r + ['', '', ''])[:3]
        cont = out and not r[0] and (not r[2] or not CODE_LIKE.match(r[2])) and (not r[1] or not r[1][0].isupper() or not r[2])
        if cont:
            p = out[-1]
            for k in (1, 2):
                if r[k]: p[k] = join_text(p[k], r[k])
        else:
            out.append(r)
    return [r for r in out if any(r)]

doc = pymupdf.open(PDF)
items, cur = [], None
head_lines = []
LIST = re.compile(r'^(\d+\s*[.)]|[-•▪๏◦]|\(\d+\)|[ก-ฮ]\.\s|ตัวอย่างที่|หมายเหตุ|Stage\b|ระยะ)')

def add(block):
    if cur is not None: cur['blocks'].append(block)

for pn, pg in enumerate(doc, 1):
    blocks = L.page_blocks(pg)
    right = max([b['x1'] for b in blocks if b['type'] == 'line'] or [520])
    i = 0; para = None; para_full = False; para_x = 72
    def flush():
        global para
    while i < len(blocks):
        b = blocks[i]
        if b['type'] == 'table':
            if para: add(para); para = None
            add({'tbl': merge_table(b['rows'])}); i += 1; continue
        t = b['t']
        m = ITEM.match(t)
        if m and b['x'] < 90:
            if para: add(para); para = None
            cur = {'n': re.sub(r'\s+', '', m.group(1)), 'title': m.group(2).strip(), 'page': pn, 'blocks': []}
            items.append(cur); i += 1; continue
        if cur is None:
            head_lines.append(t); i += 1; continue
        # printed table without the doctor/coder header: two or more rows split into columns by wide gaps
        if len(b['cells']) >= 2:
            j = i; grid = []
            while j < len(blocks) and blocks[j]['type'] == 'line' and not ITEM.match(blocks[j]['t']):
                bj = blocks[j]
                if len(bj['cells']) >= 2: grid.append(bj['cells']); j += 1
                elif grid and j + 1 < len(blocks) and blocks[j + 1]['type'] == 'line' and len(blocks[j + 1]['cells']) >= 2 and bj['x1'] < right - 120:
                    grid.append([bj['t']]); j += 1
                else: break
            if len(grid) >= 2:
                if para: add(para); para = None
                add({'grid': grid}); i = j; continue
            if b['cells'][0].rstrip(' :') in HEADS:  # "เกณฑ์การวินิจฉัย    1. ..." printed side by side
                if para: add(para); para = None
                add({'h': b['cells'][0].rstrip(' :')})
                para = {'t': '  '.join(b['cells'][1:])}; para_x = 999; para_full = b['x1'] >= right - 80; i += 1; continue
            t = '  '.join(b['cells'])
        if t.rstrip(' :') in HEADS:
            if para: add(para); para = None
            add({'h': t.rstrip(' :')}); i += 1; continue
        # a line continues the paragraph when the line above ran to the right margin and this one is not
        # indented further (a new paragraph has a first-line indent; list items keep a hanging indent)
        cont = para is not None and para_full and not LIST.match(t) and b['x'] <= para_x + (24 if LIST.match(para['t']) else 12)
        if cont:
            para['t'] = join_text(para['t'], t)
        else:
            if para: add(para)
            para = {'t': t}
            para_x = b['x']
        para_full = b['x1'] >= right - 80
        i += 1
    if para: add(para)

# ---- codes mentioned in each item
RX10 = re.compile(r'(?<![A-Z0-9])([A-Z])(\d\d)(?:\.(\d{1,2}|-)|(\d{1,2}))?(?![A-Za-z0-9/])')  # not ICD-O M8140/3
RANGE = re.compile(r'(?<![A-Z0-9])([A-Z]\d\d)\s*[-–]\s*([A-Z]\d\d)(?![\d.])')
RX11 = re.compile(r'(?<![A-Za-z0-9.])([0-9A-HJ-NP-Z][A-HJ-NP-Z]\d[0-9A-HJ-NP-Z](?:\.[0-9A-HJ-NP-Z]{1,2})?)(?![A-Za-z0-9])')
unresolved = {}
def rng(a, z): return ['%s%02d' % (a[0], k) for k in range(int(a[1:]), int(z[1:]) + 1)]
BY_TITLE = {'4': rng('B15', 'B19'), '8': rng('D50', 'D64'), '10': ['D62'], '11': ['D63'], '16': rng('E40', 'E46'),
            '20': ['E87'], '23': ['G47.3'], '44': ['K30'], '47': ['K74'], '50': ['N10'], '52': ['N18'], '53': ['N19']}
def item_text(it):
    parts = [it['title']]
    for bl in it['blocks']:
        if 'tbl' in bl: parts += [c for r in bl['tbl'] for c in r]
        elif 'grid' in bl: parts += [c for r in bl['grid'] for c in r]
        else: parts.append(bl.get('t') or bl.get('h') or '')
    return '\n'.join(parts)
for it in items:
    txt = item_text(it); found = []
    for m in RANGE.finditer(txt):
        a, z = m.group(1), m.group(2)
        if a[0] == z[0] and int(a[1:]) < int(z[1:]) <= int(a[1:]) + 30:
            for k in range(int(a[1:]), int(z[1:]) + 1):
                c = '%s%02d' % (a[0], k)
                if c in cats: found.append(c)
    for m in RX10.finditer(txt):
        cat = m.group(1) + m.group(2); sub = m.group(3) or m.group(4)
        if sub in (None, '-'): c = cat
        else: c = cat + '.' + sub
        if c in codes or (c == cat and cat in cats): found.append(c)
        elif cat in cats and sub and (cat + '.' + sub[:1]) in codes: found.append(cat + '.' + sub[:1])
        elif cat in cats: found.append(cat); unresolved.setdefault(c, it['n'])
        else: unresolved.setdefault(c, it['n'])
    it['codes'] = sorted(set(found), key=lambda c: (c[:3], len(c), c))
    # items whose text names no ICD-10 code: categories for the condition in the title, so the code pages can show them
    if not it['codes'] and it['n'] in BY_TITLE:
        it['codesFromTitle'] = BY_TITLE[it['n']]
        it['codes'] = [c for c in BY_TITLE[it['n']] if c in cats or c in codes]
    icd11 = set()
    for m in RX11.finditer(txt):
        v = m.group(1)
        if re.match(r'^[A-Z]\d\d', v): continue  # an ICD-10 code, handled above
        if v in ('COVID', 'HIV1', 'HIV2'): continue
        icd11.add(v)
    it['icd11'] = sorted(icd11)

title = ' '.join(l for l in head_lines if 'แนวทาง' in l or 'ฉบับ' in l)
out = {
    'title': 'แนวทางมาตรฐานการให้รหัสโรค (Standard Coding Guidelines) ฉบับปรับปรุง (2026)',
    'publisher': 'กองยุทธศาสตร์และแผนงาน สำนักงานปลัดกระทรวงสาธารณสุข',
    'source': 'Final_SCG-2017_Modify_2026_1.pdf (51 หน้า)',
    'note': 'ปรับปรุงจาก Standard Coding Guidelines 2017 เฉพาะหัวข้อที่แก้ไข ไม่ใช่คู่มือฉบับเต็ม รหัสที่ขึ้นต้นด้วยตัวอักษร 2 ตัว เช่น BB01, CA22 เป็นรหัส ICD-11 ที่เอกสารอ้างถึง ไม่ใช่รหัส ICD-10',
    'items': items,
}
json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('items', len(items), [it['n'] for it in items])
print('blocks', sum(len(i['blocks']) for i in items), 'tables', sum(1 for i in items for b in i['blocks'] if 'tbl' in b), 'grids', sum(1 for i in items for b in i['blocks'] if 'grid' in b))
print('codes linked', sum(len(i['codes']) for i in items), 'unresolved', unresolved)
print('icd11', {i['n']: i['icd11'] for i in items if i['icd11']})
