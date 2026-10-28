"""Build web/data/shared/guide.json for the guide page: SCG 2026 items split into sections with reading format (lists, sub-headings,
tagged codes / diagnosis roles / thresholds), the coding summaries from summ.py, and the NHSO 2562 topics in the same format.
Usage: ICD_DATA=web/data python3 scripts/guide/build_guide.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmt import body, unwrap, segs
from summ import SUMS
D = os.environ.get('ICD_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'web', 'data'))
S = json.load(open(os.path.join(D, 'shared', 'scg2026.json'), encoding='utf8'))
N = json.load(open(os.path.join(D, 'shared', 'nhso2562.json'), encoding='utf8'))
GROUPS = [('inf', 'ติดเชื้อ', 'AB'), ('onc', 'มะเร็งและเลือด', 'CD'), ('endo', 'ต่อมไร้ท่อและโภชนาการ', 'E'), ('neuro', 'สมองและหลอดเลือดสมอง', 'G'),
          ('cvs', 'หัวใจและหลอดเลือด', 'I'), ('resp', 'ระบบหายใจ', 'J'), ('gi', 'ระบบทางเดินอาหาร', 'K'), ('skin', 'ผิวหนัง', 'L'), ('renal', 'ไตและทางเดินปัสสาวะ', 'N')]
OVR = {'1': 'inf', '30': 'cvs', '33': 'neuro', '34': 'neuro', '35': 'cvs', '40': 'resp', '41': 'resp', '43': 'gi', '51': 'renal', '21': 'neuro', '22': 'neuro', '23': 'neuro'}
def gid(it):
    if it['n'] in OVR: return OVR[it['n']]
    c = it['codes'][0][0] if it['codes'] else 'Z'
    for g, _, L in GROUPS:
        if c in L: return g
    return 'inf'
CODE = re.compile(r'^\s*([A-Z]\d\d(?:\.\d{1,2})?|[A-Z]\d{3}|[A-Z]\d\d\.-)\s*(.*)$')
def split_code(s):
    m = CODE.match(s or '')
    if not m: return '', s or ''
    c = m.group(1)
    if re.fullmatch(r'[A-Z]\d{3}', c): c = c[:3] + '.' + c[3]
    return c, m.group(2)
ROLE = {'Principal diagnosis': 'วินิจฉัยหลัก', 'Comorbidity': 'วินิจฉัยร่วม', 'Complication': 'โรคแทรก', 'Other': 'อื่น ๆ', 'External cause': 'สาเหตุภายนอก'}
items = []
for it in S['items']:
    secs, exs, cur, ex = [], [], None, None
    def sec(title):
        s = {'title': title, 'blocks': []}; secs.append(s); return s
    for b in it['blocks']:
        if 'h' in b:
            ex = None; cur = sec(b['h']); continue
        if 'tbl' in b:
            if ex is None: ex = {'title': 'ตัวอย่าง', 'text': [], 'rows': [], 'note': ''}; exs.append(ex)
            role = ''
            for r in b['tbl']:
                r = (r + ['', '', ''])[:3]
                if r[0]: role = ROLE.get(r[0].strip(), r[0].replace('การวินิจฉัย', 'วินิจฉัย'))
                c, name = split_code(r[2])
                ex['rows'].append({'role': role if r[0] else '', 'dx': r[1], 'code': c, 'name': name})
            continue
        t = b.get('t')
        if 'grid' in b:
            if cur is None: cur = sec('ภาพรวม')
            w = max(len(r) for r in b['grid'])
            rows = [(['' for _ in range(w - len(r))] + r) if 1 < len(r) < w else r for r in b['grid']]
            cur['blocks'].append({'grid': rows[1:], 'head': rows[0], 'w': w}); continue
        if t.startswith('ตัวอย่างที่'):
            m = re.match(r'(ตัวอย่างที่\s*\d+)\s*(.*)', t)
            ex = {'title': m.group(1) if m else 'ตัวอย่าง', 'text': [m.group(2) if m else t], 'rows': [], 'note': ''}; exs.append(ex); continue
        if ex is not None and not ex['rows']:
            ex['text'].append(t); continue
        if ex is not None and ex['rows'] and t.startswith('หมายเหตุ'):
            ex['note'] = t.replace('หมายเหตุ', '', 1).strip(); continue
        ex = None
        if cur is None: cur = sec('ภาพรวม')
        cur['blocks'].append({'t': t})
    # merge duplicate section names (the book repeats "เกณฑ์การวินิจฉัย" for sub-topics)
    for e in exs: e['text'] = ' '.join(e['text'])
    items.append({'id': 'scg-' + it['n'], 'n': it['n'], 'title': it['title'].split(' เลิกใช้')[0] if it['n'] == '1' else it['title'],
                  'full': it['title'], 'page': it['page'], 'codes': it['codes'], 'icd11': it['icd11'], 'g': gid(it),
                  'secs': [s for s in secs if s['blocks']], 'exs': exs})
for it in items:
    for sc in it['secs']:
        out, buf = [], []
        for b in sc['blocks']:
            if 'grid' in b:
                out += body(buf); buf = []
                out.append({'k': 'grid', 'head': b['head'], 'rows': b['grid']})
            else: buf.append(b['t'])
        out += body(buf); sc['raw'] = [b['t'] for b in sc['blocks'] if 't' in b]; sc['blocks'] = out
    for e in it['exs']:
        e['segs'] = segs(e['text']); e['nsegs'] = segs(e['note']) if e['note'] else []
    sm = SUMS.get(it['n'])
    if sm:
        it['sum'] = {'ref': sm['ref'], 'notes': [segs(x) for x in sm['notes']], 'tables': [
            {'cap': tb['cap'], 'cols': tb['cols'], 'rows': [[{'fix': c.startswith('\u26a0'), 'segs': segs(c.lstrip('\u26a0 '))} for c in row] for row in tb['rows']]}
            for tb in sm['tables']]}
nh = []
for t in N['topics']:
    tt = t['text'].rstrip()
    mm = re.search(r'\s(\d{1,3})$', tt)
    if mm and abs(int(mm.group(1)) - int(t['page'])) <= 40: tt = tt[:mm.start()]
    nh.append({'id': t['id'], 'blocks': body(unwrap(tt), None, t['sys'])})
groups = [{'id': g, 'name': n} for g, n, _ in GROUPS]
out = os.path.join(D, 'shared', 'guide.json')
json.dump({'note': 'generated by scripts/guide/build_guide.py from scg2026.json and nhso2562.json', 'groups': groups, 'scg': items, 'nhso': nh},
          open(out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(out, os.path.getsize(out), len(items), sum(1 for i in items if 'sum' in i), len(nh))
