"""Build the web app's ICD-10-TM data file from tm_en.json + tm_th.json.

Steps: fix the book's misprinted codes from context, merge English and Thai columns,
generate 4th-character codes from subdivision templates (e.g. E10–E14 .0–.9),
derive parent/leaf, and write /home/claude/icd-site/data/icd10/codes.json.
"""
import json, re
from collections import defaultdict, OrderedDict

ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI',
         'XVII', 'XVIII', 'XIX', 'XX', 'XXI', 'XXII']
GEN_SKIP_TEMPLATE = re.compile(r'W00|place of occurrence|activity', re.I)
report = defaultdict(list)


def fix_codes(codes, lang, other=None):
    """Correct misprinted codes using the category they are printed under."""
    out, seen = [], {}
    cat3 = cat4 = None
    seen4 = set()
    for c in codes:
        code = c['c']
        orig = code
        if '.' not in code:
            cat3 = code; cat4 = None
        else:
            trust = lang == 'en' or code in seen or (other is not None and code not in other)
            if trust and cat3 and code[:3] != cat3 and code[0] == cat3[0]:
                code = cat3 + code[3:]
            if len(code.split('.')[1]) == 1:
                cat4 = code; seen4.add(code)
            elif len(code.split('.')[1]) >= 2 and cat4 and cat4[:3] == code[:3]:
                p4 = code[:5]
                if trust and p4 != cat4 and p4 in seen4:
                    code = cat4 + code[5:]
        if code in seen:
            prev = seen[code]
            if prev['title'].strip().lower() == c['title'].strip().lower():
                report[lang + ' dropped exact duplicate'].append(code)
                continue
            if code.endswith('.8') and 'unspecified' in c['title'].lower() + c['title']:
                code = code[:-1] + '9'
            elif lang == 'th' and code.endswith('.8') and 'ไม่ระบุ' in c['title']:
                code = code[:-1] + '9'
        if code in seen:
            report[lang + ' unresolved duplicate'].append(code)
            continue
        if code != orig:
            report[lang + ' corrected'].append(f'{orig}→{code}')
        c = dict(c); c['c'] = code
        seen[code] = c
        out.append(c)
    return out


def template_range(text):
    m = re.search(r'categor(?:y|ies)\s+([A-Z]\d\d)(?:\.\d)?\s*[-–]\s*([A-Z]\d\d)', text)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r'([A-Z]\d\d)\s*[-–]\s*([A-Z]\d\d)', text)
    return (m.group(1), m.group(2)) if m else None


def in_range(code3, rng):
    a, b = rng
    return a[0] == code3[0] == b[0] and int(a[1:]) <= int(code3[1:]) <= int(b[1:])


def collect_templates(doc):
    temps = []
    for kind in ('chapters', 'blocks', 'codes'):
        for o in doc[kind]:
            for sd in o.get('subdivs', []):
                rng = template_range(sd['text'])
                if not rng and kind == 'blocks':
                    rr = o['range'].split('-')
                    rng = (rr[0], rr[-1])
                owner = (kind, o.get('range') or o.get('c') or o.get('n'))
                temps.append({'rng': rng, 'level': sd['level'], 'text': sd['text'], 'entries': sd['entries'], 'owner': owner})
    return temps


def norm_items(items):
    out = []
    for i in items:
        i = re.sub(r'\s+', ' ', i or '').strip()
        i = re.sub(r'^[@#]\s+', '', i)
        if i:
            out.append(i)
    return out


def merge_notes(en_notes, th_notes):
    out = []
    th_by_type = defaultdict(list)
    for n in th_notes:
        th_by_type[n['t']].append(n)
    used = defaultdict(int)
    for n in en_notes:
        k = used[n['t']]; used[n['t']] += 1
        th = th_by_type[n['t']][k] if k < len(th_by_type[n['t']]) else None
        item = {'t': n['t'], 'en': norm_items(n['items'])}
        if th:
            item['th'] = norm_items(th['items'])
        if item['en'] or item.get('th'):
            out.append(item)
    return out


def main():
    E = json.load(open('/home/claude/src/tm_en.json', encoding='utf8'))
    T = json.load(open('/home/claude/src/tm_th.json', encoding='utf8'))
    en_codes = fix_codes(E['codes'], 'en')
    th_codes = fix_codes(T['codes'], 'th', {c['c'] for c in en_codes})
    th_map = {c['c']: c for c in th_codes}

    # chapters
    th_ch = {c['n']: c for c in T['chapters']}
    chapters = []
    for c in E['chapters']:
        t = th_ch.get(c['n'], {})
        chapters.append({'id': ROMAN[c['n']], 'n': c['n'], 'range': c['range'], 'en': c['title'], 'th': t.get('title', ''),
                         'notes': merge_notes(c['notes'], t.get('notes', []))})
    # blocks
    th_bl = {b['range']: b for b in T['blocks']}
    blocks, seen_bl = [], set()
    for b in E['blocks']:
        if b['range'] in seen_bl:
            continue
        seen_bl.add(b['range'])
        t = th_bl.get(b['range'], {})
        blocks.append({'id': b['range'], 'ch': ROMAN[b['ch']] if b['ch'] else '', 'range': b['range'].replace('-', '–'),
                       'en': b['title'], 'th': t.get('title', ''), 'notes': merge_notes(b['notes'], t.get('notes', []))})

    # templates
    temps_en = collect_templates(E)
    temps_th = collect_templates(T)
    th_temp_by_owner = {}
    for t in temps_th:
        th_temp_by_owner.setdefault(t['owner'], t)

    codes = OrderedDict()
    for c in en_codes:
        t = th_map.get(c['c'], {})
        codes[c['c']] = {
            'c': c['c'], 'b': c['blk'], 'en': c['title'], 'th': t.get('title', ''),
            'da': c['da'] or t.get('da', ''), 'tm': c['mark'] == '#' or t.get('mark') == '#', 'bad': c['mark'] == '@' or t.get('mark') == '@',
            'notes': merge_notes(c['notes'], t.get('notes', [])),
        }
        if not t:
            report['en code without thai title'].append(c['c'])

    # generate children from 4th-character templates
    has_child = defaultdict(bool)
    for k in codes:
        if '.' in k:
            has_child[k.split('.')[0]] = True
    generated = 0
    template_notes = {}
    for tp in temps_en:
        if not tp['rng'] or tp['level'] != 4 or not tp['entries']:
            continue
        thp = th_temp_by_owner.get(tp['owner'])
        th_entries = {e['d']: e for e in (thp['entries'] if thp else [])}
        if GEN_SKIP_TEMPLATE.search(tp['text']):
            continue
        for k in list(codes.keys()):
            if '.' in k or has_child[k] or not in_range(k, tp['rng']):
                continue
            parent = codes[k]
            for e in tp['entries']:
                cc = f"{k}.{e['d']}"
                if cc in codes:
                    continue
                te = th_entries.get(e['d'], {})
                sub_en = e['title'][:1].lower() + e['title'][1:] if len(e['title']) > 1 and e['title'][1].islower() else e['title']
                if te.get('title'):
                    te = dict(te, title=re.split(r'\s\.\d\s', te['title'])[0])
                codes[cc] = {
                    'c': cc, 'b': parent['b'], 'en': f"{parent['en']}, {sub_en}",
                    'th': (parent['th'] + ' ' + te['title']).strip() if te.get('title') else parent['th'],
                    'da': e['da'], 'tm': False, 'bad': False, 'gen': True,
                    'notes': merge_notes(e['notes'], te.get('notes', [])) if e.get('notes') else [],
                }
                generated += 1
            has_child[k] = True
    report['generated from templates'] = [str(generated)]

    # place-of-occurrence guidance for W00–Y34 (separate variable in TM)
    place = next((t for t in temps_en if GEN_SKIP_TEMPLATE.search(t['text']) or (t['rng'] is None and len(t['entries']) == 10)), None)

    # order, parents, leaf
    def key(code):
        a, _, b = code.partition('.')
        return (a[0], int(a[1:3]), b)
    ordered = sorted(codes.values(), key=lambda x: key(x['c']))
    allc = {x['c'] for x in ordered}
    kids = defaultdict(int)
    for x in ordered:
        c = x['c']
        if '.' in c:
            p = c[:-1] if len(c.split('.')[1]) > 1 else c.split('.')[0]
            if p.endswith('.'):
                p = p[:-1]
            if p not in allc and len(c.split('.')[1]) > 1:
                p = c.split('.')[0]
            if p in allc:
                x['p'] = p; kids[p] += 1
    for x in ordered:
        x['leaf'] = kids[x['c']] == 0
        if not x['b']:
            report['code without block'].append(x['c'])
        if x['c'][:3] >= 'W00' and x['c'][:3] <= 'Y34' and x['c'][0] in 'WXY' and not x['c'].startswith(('Y06', 'Y07')):
            x['place'] = True
        # compact
        for f in ('tm', 'bad', 'da', 'notes'):
            if not x.get(f):
                x.pop(f, None)

    out = {
        'system': 'icd10', 'label': 'ICD-10-TM', 'kind': 'diagnosis', 'version': '2009', 'sample': False,
        'source': 'ICD-10-TM 2009 Tabular List of Diseases (ฉบับอังกฤษ-ไทย), สำนักนโยบายและยุทธศาสตร์ กระทรวงสาธารณสุข',
        'chapters': chapters, 'blocks': blocks, 'codes': ordered,
        'place': {'en': [e['title'] for e in place['entries']]} if place else None,
    }
    json.dump(out, open('/home/claude/icd-site/data/icd10/codes.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    for k, v in report.items():
        print(f'{k}: {len(v)}', v[:25])
    print('codes', len(ordered), 'leaf', sum(x['leaf'] for x in ordered), 'tm', sum(1 for x in ordered if x.get('tm')),
          'bad', sum(1 for x in ordered if x.get('bad')), 'no th', sum(1 for x in ordered if not x['th']))


if __name__ == '__main__':
    main()
