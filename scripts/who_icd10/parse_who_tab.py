"""Parse WHO ICD-10 2016 Volume 1 (S0052) lines into codes with titles and notes.

Writes /home/claude/who/who_tab.json: {"codes": [{c, dag, en, notes:[{t, en:[...]}]}], "templates": {...}}
"""
import json, re

CODE = re.compile(r'^([A-Z]\d\d(?:\.\d{1,2})?)\s*([†*]?)$')
TPL = re.compile(r'^(\.\d{1,2})$')
L = [json.loads(l) for l in open('/home/claude/who/tab_lines.jsonl', encoding='utf8')]

# the tabular list runs from Chapter I (page 19 of the PDF) to the end of Chapter XXII
start = next(i for i, l in enumerate(L) if l['t'].startswith('CHAPTER I') and l['p'] > 15)
end = next(i for i, l in enumerate(L) if l['p'] > 900 and l['t'].startswith('Morphology of neoplasms'))
LBL = {'Incl.:': 'includes', 'Excl.:': 'excludes', 'Note:': 'note'}

codes, templates = [], {}
cur = None          # current code dict
state = None        # 'title' while bold title lines continue
note = None
margin = {}
for l in L[start:end]:
    p = l['p']
    if l['y'] < 62 or l['y'] > 626:          # running heads, page numbers, printer marks
        continue
    if p not in margin:
        xs = [s[0] for x in L[start:end] if x['p'] == p for s in x['spans'][:1] if CODE.match(s[1]) or TPL.match(s[1])]
        margin[p] = min(xs) if xs else min(x['x'] for x in L[start:end] if x['p'] == p)
    m0 = margin[p]
    sp = [s for s in l['spans'] if s[0] >= m0 - 4]     # drop marks in the outer margin
    if not sp:
        continue
    # a code can be split over several spans ("E" + "27"); merge spans that sit in the code column
    k = 0
    while k + 1 < len(sp) and sp[k + 1][0] < m0 + 40 and re.match(r'^[A-Z0-9.†*]+$', sp[k + 1][1].strip()):
        k += 1
    if k:
        sp = [[sp[0][0], ''.join(s[1].strip() for s in sp[:k + 1]), sp[0][2], sp[k][3]]] + sp[k + 1:]
    m_inl = re.match(r'^([A-Z]\d\d(?:\.\d{1,2})?[†*]?)\s+(\S.*)$', sp[0][1].strip())
    if m_inl and sp[0][0] - m0 < 8 and sp[0][2]:
        sp = [[sp[0][0], m_inl.group(1), True, sp[0][3]], [sp[0][0] + 50, m_inl.group(2), True, sp[0][3]]] + sp[1:]
    first = sp[0][1].strip()
    mc = CODE.match(first)
    rel = sp[0][0] - m0
    if mc and rel < 8:
        title = re.sub(r'[\u0e00-\u0e7f]+', '', ' '.join(s[1] for s in sp[1:])).strip()
        dag = mc.group(2)
        if not dag and title[:1] in '†*':
            dag, title = title[0], title[1:].strip()
        cur = {'c': mc.group(1), 'dag': dag, 'en': title, 'notes': [], 'p': p}
        codes.append(cur)
        state, note = 'title', None
        continue
    mt = TPL.match(first)
    if mt and rel < 8 and l['b']:
        cur = {'c': mt.group(1), 'tpl': True, 'en': ' '.join(s[1] for s in sp[1:]).strip(), 'notes': [], 'p': p}
        templates.setdefault(p, []).append(cur)
        state, note = 'title', None
        continue
    if cur is None:
        continue
    lab = next((k for k in LBL if first.startswith(k)), None)
    if lab:
        rest = l['t'][len(lab):].strip()
        note = {'t': LBL[lab], 'en': [rest] if rest else []}
        cur['notes'].append(note)
        state = 'note'
        continue
    if state == 'title' and l['b'] and rel > 30:
        cur['en'] = (cur['en'] + ' ' + re.sub(r'[\u0e00-\u0e7f]+', '', l['t'])).strip()
        continue
    if rel < 8 and not l['b']:
        # block heading (e.g. "Other bacterial diseases" / "(A30–A49)") ends the current code
        state, note = None, None
        cur = None
        continue
    text = re.sub(r'\s*[\u0e00-\u0e7f][\u0e00-\u0e7f ]*', ' ', l['t']).strip()
    if not text:
        continue
    if re.match(r'^(Use additional code|Code first|Use additional)', text):
        note = {'t': 'use_additional' if text.startswith('Use') else 'code_first', 'en': [text], '_ind': rel}
        cur['notes'].append(note)
        state = 'note'
        continue
    if note is not None and note['t'] in ('use_additional', 'code_first') and rel <= note.get('_ind', 0) + 4 and not text.startswith('•'):
        note = None
    if note is None:
        note = {'t': 'inclusion', 'en': []}
        cur['notes'].append(note)
    state = 'note'
    # continuation of a wrapped item: deeper indent than the item start, or starts lower-case after a non-ending line
    indent = rel
    if note['en'] and (indent > note.get('_ind', 0) + 4 and not text.startswith('•')):
        note['en'][-1] += ' ' + text
    else:
        note['en'].append(text)
        note['_ind'] = indent

def joinable(a, b):
    return a and b and not a.rstrip().endswith(('.', ':', ';', ')', ']')) and (b[0].islower() or b[0].isdigit()) and not b.startswith('•')


for c in codes + [t for v in templates.values() for t in v]:
    for n in c['notes']:
        n.pop('_ind', None)
        n['en'] = [re.sub(r'\s+', ' ', x).strip() for x in n['en'] if x.strip()]
        merged = []
        for x in n['en']:
            if merged and joinable(merged[-1], x):
                merged[-1] += ' ' + x
            else:
                merged.append(x)
        n['en'] = merged
    # a wrapped "Use additional code ..." line whose tail was read as a new inclusion note
    keep = []
    for n in c['notes']:
        if keep and keep[-1]['t'] in ('use_additional', 'code_first') and n['t'] == 'inclusion' and n['en'] and joinable(keep[-1]['en'][-1], n['en'][0]):
            keep[-1]['en'][-1] += ' ' + n['en'][0]
            n['en'] = n['en'][1:]
            if not n['en']:
                continue
        keep.append(n)
    c['notes'] = keep
    c['en'] = re.sub(r'\s+', ' ', c['en']).strip()

seen = {}
for c in codes:
    seen.setdefault(c['c'], 0)
    seen[c['c']] += 1
dups = [k for k, v in seen.items() if v > 1]
json.dump({'codes': codes, 'templates': templates}, open('/home/claude/who/who_tab.json', 'w', encoding='utf8'), ensure_ascii=False)
print('codes', len(codes), 'unique', len(seen), 'dups', dups[:20], 'templates pages', len(templates))
print('3-char', sum(1 for c in seen if '.' not in c), '4-char', sum(1 for c in seen if len(c) == 5), '5-char', sum(1 for c in seen if len(c) == 6))
