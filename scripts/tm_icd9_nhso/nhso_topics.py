"""Extract topics from the NHSO 2562 medical-record audit manual.

Output /home/claude/icd-site/data/shared/nhso2562.json:
  {source, topics: [{id, sec, sys, n, title, page, codes: [patterns], text}]}
A pattern is an exact code ("I21.0"), a category ("A27"), a range ("E10-E14"),
optionally with a forced 4th character ("E10-E14.2").
"""
import json, re, subprocess
import pymupdf
from nhso_decode import decode

SRC = '/mnt/user-data/uploads/Newspaper_documents_claiming_expenses_for_testing_services_in_2019.pdf'
toc = subprocess.run(['pdftotext', '-f', '4', '-l', '17', '-layout', SRC, '-'], capture_output=True, text=True).stdout
toc = toc.replace('ำา', 'ำ').replace('�', '')

# ---- table of contents
sections, topics = [], []
sec = None
pending = None
for raw in toc.split('\n'):
    line = raw.strip()
    if not line:
        continue
    ms = re.match(r'^\((การสรุปและให้รหัส.*?)\)\s*\.{3,}\s*(\d+)$', line)
    if ms:
        title = re.sub(r'\s+', ' ', ms.group(1)).replace('การสรุปและให้รหัส', '').strip()
        sec = {'name': title, 'proc': 'หัตถการ' in title, 'page': int(ms.group(2))}
        sections.append(sec); pending = None
        continue
    if sec is None:
        continue
    mt = re.match(r'^(\d{1,3})\.\s*(.*?)\s*(?:\.{3,}\s*(\d+))?$', line)
    if mt and (pending is None or not pending.get('open')):
        pending = {'n': int(mt.group(1)), 'title': mt.group(2).strip(), 'page': int(mt.group(3)) if mt.group(3) else None,
                   'sec': sec['name'], 'proc': sec['proc'], 'open': mt.group(3) is None}
        if not pending['open']:
            topics.append(pending)
        continue
    if pending is not None and pending.get('open'):
        m2 = re.match(r'^(.*?)\s*\.{3,}\s*(\d+)$', line)
        if m2:
            pending['title'] += ' ' + m2.group(1).strip(); pending['page'] = int(m2.group(2)); pending['open'] = False
            topics.append(pending)
        else:
            pending['title'] += ' ' + line

# ---- body text
d = pymupdf.open(SRC)
pages = {i + 1: decode(d[i].get_text()) for i in range(len(d))}
OFFSET = 1   # printed page + 1 = PDF page


def find_header(text, n, title, start=0):
    key = re.findall(r'[A-Za-z]{4,}|[A-Z]\d\d', title)
    for m in re.finditer(rf'(?m)^\s*{n}\s*\.\s*', text[start:]):
        s = start + m.start()
        if not key or any(k.lower() in text[s:s + 160].lower() for k in key[:3]):
            return s
    m = re.search(rf'(?m)^\s*{n}\s*\.', text[start:])
    return start + m.start() if m else None


out = []
for i, t in enumerate(topics):
    if t['page'] is None:
        continue
    p0 = t['page'] + OFFSET
    nxt = topics[i + 1] if i + 1 < len(topics) else None
    p1 = (nxt['page'] + OFFSET) if nxt and nxt['page'] else p0 + 1
    p1 = max(p0, min(p1, p0 + 8))
    text = '\n'.join(pages.get(p, '') for p in range(p0, p1 + 1))
    a = find_header(text, t['n'], t['title'])
    if a is None:
        a = 0
    b = None
    if nxt and nxt['sec'] == t['sec']:
        b = find_header(text, nxt['n'], nxt['title'], a + 5)
    body = text[a:b] if b else text[a:a + 6000]
    # drop running headers / footers
    body = re.sub(r'(?m)^.*Guideline for Medical Document Audit 2019.*$', '', body)
    body = re.sub(r'(?m)^\s*แนวทางปฏิบัติในการตรวจสอบเอกสารหลักฐาน.*$', '', body)
    body = re.sub(r'(?m)^\s*ของคณะกรรมการตรวจสอบเวชระเบียน.*$', '', body)
    body = re.sub(r'(?m)^\s*\(การสรุปและให้รหัส.*$', '', body)
    body = re.sub(r'[ \t ]+', ' ', body)
    body = re.sub(r'\n\s*\n+', '\n', body).strip()
    lines = body.split('\n')
    if lines and re.match(rf'^\s*{t["n"]}\s*\.', lines[0]):
        lines = lines[1:]
    body = '\n'.join(l.strip() for l in lines).strip()
    title = re.sub(r'\s+', ' ', t['title']).strip()
    sys_ = 'icd9' if t['proc'] else 'icd10'
    pats = []
    for m in re.finditer(r'([A-Z]\d\d)(?:\.(\d{1,2}|-))?\s*(?:[-–]\s*([A-Z]\d\d)(?:\.(\d{1,2}|-))?)?', title):
        a1, d1, b1, d2 = m.groups()
        if b1:
            fourth = re.search(r'(?:สี่|ที่ 4)\D*\.(\d)', title)
            pats.append(f'{a1}-{b1}' + (f'.{fourth.group(1)}' if fourth else ''))
        elif d1 and d1 != '-':
            pats.append(f'{a1}.{d1}')
        else:
            pats.append(a1)
    if sys_ == 'icd9':
        for m in re.finditer(r'\b(\d\d)\.(\d{1,2})\b(?:\s*[-–]\s*(\d\d)\.(\d{1,2}))?', title + '\n' + body[:400]):
            pats.append(f'{m.group(1)}.{m.group(2)}' + (f'-{m.group(3)}.{m.group(4)}' if m.group(3) else ''))
    out.append({'id': f"{len(out) + 1}", 'sec': t['sec'], 'sys': sys_, 'n': t['n'], 'title': title, 'page': t['page'],
                'codes': sorted(set(pats)), 'text': body[:5000]})

json.dump({'source': 'คู่มือแนวทางปฏิบัติในการตรวจสอบเอกสารหลักฐานการเรียกเก็บค่าใช้จ่ายเพื่อบริการสาธารณสุข ปี 2562 (สปสช.)',
           'sections': [s['name'] for s in sections], 'topics': out},
          open('/home/claude/icd-site/data/shared/nhso2562.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('sections', len(sections), 'topics', len(out), 'with codes', sum(1 for t in out if t['codes']))
for t in out[:4] + out[-3:]:
    print(t['sec'], t['n'], t['title'][:60], t['codes'][:5], t['page'], len(t['text']))
