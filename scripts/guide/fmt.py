"""Level-1 reading format: turn book paragraphs into lists, sub-headings and tagged segments (codes, diagnosis roles, thresholds).
No wording is rewritten except known extraction slips (FIX) and dotless codes."""
import json, re
import os
_D = os.environ.get('ICD_DATA', os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'data'))
_C = json.load(open(os.path.join(_D, 'icd10', 'codes.json'), encoding='utf8'))['codes']
CODES9 = {c['c'] for c in json.load(open(os.path.join(_D, 'icd9', 'codes.json'), encoding='utf8'))['codes']}
CODES = {c['c']: c for c in _C}
def cname(c):
    e = CODES.get(c)
    if not e: return None
    en = re.split(r'\s+(?:CHAPTER|Chapter)\b', e.get('en', ''))[0]
    en = re.sub(r'\s+(Neoplasms|Diseases of .*|Certain .*)$', '', en) if e['c'] == 'B99' else en
    return {'c': c, 'th': e.get('th', ''), 'en': en}

FIX = [(r'Gl\s*as\s*-\s*Glow coma score', 'Glasgow coma score'), (r'\s+,', ','), (r',(?=[^\s\d])', ', '), (r'\)(?=[ก-๙A-Za-z])', ') '),
       (r'\s{2,}', ' ')]
def fix(t):
    for a, b in FIX: t = re.sub(a, b, t)
    return t.strip()

TOK = re.compile(
    r'(?P<cd>\b[A-Z]\d\d(?:\.\d{1,2}|\.-|\d(?!\d))?[†*]?(?:\s*[-–]\s*[A-Z]\d\d(?:\.\d{1,2})?)?(?![A-Za-z0-9]))'
    r'|(?P<pd>(?:การ)?วินิจฉัยหลัก|โรคหลัก|Principal diagnosis)'
    r'|(?P<sd>(?:การ)?วินิจฉัยร่วม|โรคร่วม|Comorbidity)'
    r'|(?P<cx>โรคแทรกซ้อน|โรคแทรก|Complication)'
    r'|(?P<nm>(?:[<>≤≥]=?\s*|(?:ต่ำกว่า|สูงกว่า|มากกว่า|น้อยกว่า|ไม่เกิน|อย่างน้อย)\s*(?:เดิม\s*)?)\d+(?:[.,]\d+)?(?:\s*(?:ครั้งต่อนาที|ครั้ง/นาที|มิลลิเมตรปรอท|มม\.ปรอท|mmHg|มิลลิโมล/ลิตร|mmol/L|mg/dL|mg/dl|ng/ml|µg/dl|g/dL|g/dl|%|ชั่วโมง|วัน|สัปดาห์|เดือน|ปี|ครั้ง|กรัม|kg|องศา(?:เซลเซียส)?))?)')
def norm_code(s):
    s = re.sub(r'\s+', '', s).replace('–', '-')
    def one(x):
        m = re.fullmatch(r'([A-Z]\d\d)(\d)([†*]?)', x)
        if m and (m.group(1) + '.' + m.group(2)) in CODES: return m.group(1) + '.' + m.group(2) + m.group(3)
        return x
    return '-'.join(one(p) for p in s.split('-')) if not s.endswith('.-') else s
def code_ok(s):
    a = s.split('-')[0].rstrip('†*').replace('.-', '')
    if a.endswith('.'): a = a[:-1]
    return a in CODES or a[:3] in CODES and len(a) == 3
TOK9 = re.compile(r'(?P<cd>\b\d\d\.\d{1,2}\b)|(?P<pd>' + TOK.pattern.split('|(?P<pd>', 1)[1])
def segs(t, names=None, sys='icd10'):
    names = {} if names is None else names
    out, i = [], 0
    def tx(s):
        if s: out.append({'k': 'tx', 's': s})
    for m in (TOK9 if sys == 'icd9' else TOK).finditer(t):
        k = m.lastgroup; s = m.group(0)
        if k == 'cd' and sys == 'icd9':
            if s not in CODES9: continue
            tx(t[i:m.start()]); i = m.end(); out.append({'k': 'cd', 's': s, 'key': s}); continue
        if k == 'cd':
            s2 = norm_code(s)
            if not code_ok(s2): continue
            tx(t[i:m.start()]); i = m.end()
            key = s2.split('-')[0].rstrip('†*').replace('.-', '')
            if key not in CODES and key[:3] in CODES: key = key[:3]
            out.append({'k': 'cd', 's': s2, 'key': key if key in CODES else ''}); continue
        tx(t[i:m.start()]); i = m.end()
        out.append({'k': k, 's': s})
    tx(t[i:])
    return out

LI = re.compile(r'^\s*(\d{1,2}[.)]|[ก-ฮ][.)]|[▪•●○\-–]|\(\d{1,2}\))\s*(?=\S)')
HEAD_START = re.compile(r'^(เกณฑ์|แนวทาง|แนวการ|หลักเกณฑ์|การวินิจฉัย|การให้รหัส|ส่วน ICD|Clinical stage|ข้อควรระวัง|หมายเหตุ|สรุป)')
STRAY = {'วินิจฉัยหลัก', 'วินิจฉัยร่วม', 'การวินิจฉัยหลัก', 'การวินิจฉัยร่วม', 'รหัส', 'การวินิจฉัย'}
def is_head(t):
    t = t.strip()
    return len(t) <= 60 and not LI.match(t) and HEAD_START.match(t) and not re.search(r'[.;]$', t) and not re.search(r'\d\.\s', t)

def body(lines, names=None, sys='icd10'):
    """lines: list of text lines (paragraph strings or wrapped PDF lines) -> display blocks"""
    blocks = []
    def last_list():
        return blocks[-1] if blocks and blocks[-1]['k'] == 'ol' else None
    shortrun = []
    def flush_short():
        if len(shortrun) >= 3:
            blocks.append({'k': 'ol', 'plain': True, 'items': [{'m': '•', 'segs': segs(x, names, sys)} for x in shortrun]})
        else:
            for x in shortrun: blocks.append({'k': 'p', 'segs': segs(x, names, sys)})
        shortrun.clear()
    for raw in lines:
        t = fix(raw)
        if not t or t in STRAY: continue
        if is_head(t):
            flush_short(); blocks.append({'k': 'h', 's': t.rstrip(':')}); continue
        m = LI.match(t)
        if m:
            flush_short()
            mk = m.group(1); txt = t[m.end():]
            mk = '•' if mk in '▪•●○-–' else mk.rstrip('.)').strip('()')
            ol = last_list()
            if not ol or ol.get('plain') != (mk == '•') or (mk in ('1', 'ก') and ol['items']):
                ol = {'k': 'ol', 'plain': mk == '•', 'items': []}; blocks.append(ol)
            ol['items'].append({'m': mk, 'segs': segs(txt, names, sys)}); continue
        if len(t) <= 45 and not re.search(r'[.:]$', t):
            shortrun.append(t); continue
        flush_short()
        blocks.append({'k': 'p', 'segs': segs(t, names, sys)})
    flush_short()
    return blocks

def unwrap(text):
    """Join PDF hard-wrapped lines: a line continues the previous one unless it starts a list item or a heading."""
    out = []
    for l in text.split('\n'):
        l = l.strip()
        if not l: continue
        if out and not LI.match(l) and not is_head(l) and not is_head(out[-1]) and not re.search(r'(ดังนี้|:)\s*$', out[-1]) and not l.startswith('('):
            out[-1] += ' ' + l
        else: out.append(l)
    return out
