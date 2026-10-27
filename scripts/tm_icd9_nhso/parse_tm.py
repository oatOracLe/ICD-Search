"""Parse tm_lines.jsonl (one language column at a time) into chapters / blocks / codes / notes.

Run: python3 parse_tm.py  -> writes tm_en.json and tm_th.json
"""
import json, re, sys
from collections import defaultdict

CODE_RX = re.compile(r'^(?:([@#])\s*)?([A-Z]\d\d(?:\.\d{1,3})?)(?:\.-)?\s*([†*]?)(?:\s+(.*))?$')
RANGE_RX = re.compile(r'\(([A-Z]\d\d(?:\.\d)?)\s*[-–]\s*([A-Z]\d\d(?:\.\d)?)\)\s*$')
RANGE_ONE_RX = re.compile(r'\(([A-Z]\d\d)\)\s*$')
SUB_RX = re.compile(r'^\.(\d{1,2})\s*([†*]?)\s+(.*)$')
CHAPTER_EN = re.compile(r'^CHAPTER\s+([IVXL]+)\s*$')
CHAPTER_TH = re.compile(r'^บทที่\s*(\d+)')
ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50}


def roman_to_int(s):
    n = 0
    for i, c in enumerate(s):
        v = ROMAN[c]
        n += -v if i + 1 < len(s) and ROMAN[s[i + 1]] > v else v
    return n


LABELS = {
    'en': [('includes', re.compile(r'^Includes?\s*:\s*(.*)$', re.I)),
           ('excludes', re.compile(r'^Excludes?\s*:?\s*(.*)$', re.I)),
           ('note', re.compile(r'^Note\s*:\s*(.*)$', re.I)),
           ('use_additional', re.compile(r'^(Use additional .*)$', re.I)),
           ('code_first', re.compile(r'^(Code first .*)$', re.I)),
           ('see', re.compile(r'^(\[See .*)$', re.I))],
    'th': [('includes', re.compile(r'^รวม\s*:\s*(.*)$')),
           ('excludes', re.compile(r'^ไม่รวม\s*:\s*(.*)$')),
           ('note', re.compile(r'^หมายเหตุ\s*:?\s*(.*)$')),
           ('use_additional', re.compile(r'^((?:หากต้องการ\s*)?(?:อาจ)?ใช้รหัส(?:เสริม|เพิ่ม).*)$')),
           ('code_first', re.compile(r'^(ให้รหัส.*ก่อน.*)$')),
           ('see', re.compile(r'^(\[ดู.*)$'))],
}
SUBDIV_START = {
    'en': re.compile(r'following (fourth|fifth)[- ]character sub(?:divisions|classification)', re.I),
    'th': re.compile(r'(?:แบ่ง(?:กลุ่ม)?ย่อย|รหัสย่อย).*(?:หลักที่|ตัวที่)\s*([45])'),
}
CHAPTER_BLOCK_LIST = {'en': re.compile(r'^This chapter contains the following', re.I),
                      'th': re.compile(r'^บทนี้ประกอบด้วย')}


def is_code_line(r):
    m = CODE_RX.match(r['text'])
    if not m or not r['bold'] or r['x'] > (110 if r['col'] == 'en' else 350):
        return None
    f = r['font']
    if not (f.startswith('Arial') or f.startswith('Tahoma') or f.startswith('TimesNewRomanPS-Bold') or m.group(1)):
        return None
    return m


THAI_CH = re.compile(r'[\u0E00-\u0E7F]')


def join(a, b):
    a = a.rstrip(); b = b.lstrip()
    if a and b and THAI_CH.match(a[-1]) and THAI_CH.match(b[0]):
        return a + b
    return (a + ' ' + b).strip()


def title_x(r, code):
    for i, (x, w) in enumerate(r['w']):
        if w.startswith(code):
            return r['w'][i + 1][0] if i + 1 < len(r['w']) else x + 30
    return r['x'] + 30


def is_heading(r, lang):
    return r['font'].startswith('Tahoma-Bold') and r['size'] >= 11.5


def parse(lang):
    L = [json.loads(l) for l in open('/home/claude/src/tm_lines.jsonl', encoding='utf8')]
    L = [r for r in L if r['col'] == lang and r['y'] < 790 and 'Tabular List of Diseases' not in r['text']]
    L.sort(key=lambda r: (r['pg'], r['y'], r['x']))

    chapters, blocks, codes = [], [], []
    ch = blk = code = None
    note = None          # current note dict {t, items, base}
    target = None        # list receiving notes (chapter / block / code / subdiv entry)
    heading_buf = []
    chapter_pending = False
    skip_list = False
    sub = None           # current subdivision template
    sub_entry = None
    title_cont = None    # code being continued (title wrap)

    def start_note(t, first_text, base_x):
        nonlocal note
        note = {'t': t, 'items': [], 'base': base_x}
        if first_text:
            note['items'].append(first_text)
        target.append(note)

    def add_item(r):
        nonlocal note
        text = r['text']
        if note is None:
            start_note('inclusion', None, r['x'])
        bullet = text.startswith('•')
        if bullet:
            note['items'].append('• ' + text.lstrip('• ').strip())
            note['bx'] = r['w'][1][0] if len(r['w']) > 1 else r['x']
            return
        base = note['base'] if note['base'] is not None else r['x']
        if note['base'] is None:
            note['base'] = r['x']
        last = note['items'][-1] if note['items'] else None
        if last is not None:
            if last.startswith('• ') and abs(r['x'] - note.get('bx', -99)) < 3:
                note['items'][-1] = join(last, text)      # wrapped bullet item
                return
            if r['x'] > base + 3 and not last.startswith('• '):
                note['items'][-1] = join(last, text)      # wrapped plain item
                return
            if note['t'] in ('use_additional', 'code_first', 'note', 'see') and r['x'] >= base - 1:
                note['items'][-1] = join(last, text)      # sentence-type notes run on
                return
        note['items'].append(text)

    for r in L:
        t = r['text']
        if re.match(r'^[@#]\s+\[', t):
            t = re.sub(r'^[@#]\s+', '', t); r = dict(r, text=t)
        # ---- chapter heading
        mch = (CHAPTER_EN if lang == 'en' else CHAPTER_TH).match(t)
        if mch and r['size'] >= 11.5 and (r['font'].startswith('Tahoma') or r['font'].startswith('Arial')):
            n = roman_to_int(mch.group(1).upper()) if lang == 'en' else int(mch.group(1))
            ch = {'n': n, 'title': '', 'range': '', 'notes': []}
            chapters.append(ch)
            blk = code = None; note = None; target = ch['notes']; heading_buf = []; chapter_pending = True
            sub = sub_entry = None; skip_list = False; title_cont = None
            continue
        if chapter_pending and is_heading(r, lang):
            m = RANGE_RX.search(t)
            if m:
                ch['range'] = m.group(1) + '-' + m.group(2)
                ch['title'] = ' '.join(heading_buf + [t[:m.start()].strip()]).strip() if lang == 'en' else ''.join(heading_buf + [t[:m.start()].strip()]).strip()
                chapter_pending = False; heading_buf = []
            else:
                heading_buf.append(t)
            continue
        # ---- block heading
        if is_heading(r, lang):
            heading_buf.append(t)
            m = RANGE_RX.search(t) or RANGE_ONE_RX.search(t)
            if m:
                full = ' '.join(heading_buf)
                mm = RANGE_RX.search(full) or RANGE_ONE_RX.search(full)
                title = full[:mm.start()].strip()
                rng = mm.group(1) + ('-' + mm.group(2) if mm.re is RANGE_RX else '')
                blk = {'range': rng, 'title': title, 'ch': ch['n'] if ch else None, 'notes': [], 'pg': r['pg']}
                blocks.append(blk)
                heading_buf = []; code = None; note = None; target = blk['notes']
                sub = sub_entry = None; skip_list = False; title_cont = None
            continue
        if heading_buf and not is_heading(r, lang):
            heading_buf = []
        # ---- chapter's list of blocks: skip until first real content label/heading
        if CHAPTER_BLOCK_LIST[lang].match(t):
            skip_list = True; note = None
            continue
        if skip_list:
            if re.match(r'^[A-Z]\d\d[-–]', t) or re.match(r'^[A-Z]\d\d\*', t) or not r['bold'] and not any(rx.match(t) for _, rx in LABELS[lang]):
                continue
            skip_list = False
        # ---- code line
        m = is_code_line(r)
        if m:
            mark, c, da, title = m.group(1), m.group(2), m.group(3), (m.group(4) or '').strip()
            code = {'c': c, 'mark': mark or '', 'da': da, 'title': title, 'notes': [], 'pg': r['pg'],
                    'blk': blk['range'] if blk else None, 'ch': ch['n'] if ch else None, 'tx': title_x(r, c), 'cx': r['x']}
            codes.append(code)
            target = code['notes']; note = None; title_cont = code; sub = sub_entry = None
            continue
        # ---- title continuation (bold, same family, indented to title column)
        if title_cont is not None and (r['font'].startswith(('Arial', 'Tahoma')) and not r['font'].startswith('ArialNarrow-Bold')) \
                and not t.startswith(('[', '•', '@', '#')) and not any(rx.match(t) for _, rx in LABELS[lang]) \
                and r['x'] > title_cont['cx'] + 10 and not SUB_RX.match(t) and not CODE_RX.match(t):
            title_cont['title'] = join(title_cont['title'], t)
            continue
        title_cont = None
        # ---- subdivision templates
        if SUBDIV_START[lang].search(t):
            sub = {'text': t, 'entries': [], 'level': 5 if re.search('fifth|5', t) else 4}
            owner = code if code is not None else (blk if blk is not None else ch)
            owner.setdefault('subdivs', []).append(sub)
            note = None; sub_entry = None
            continue
        if sub is not None and not sub['entries'] and not SUB_RX.match(t) and r['size'] <= 9.5 and not r['bold']:
            sub['text'] += ' ' + t     # wrapped intro sentence
            continue
        ms = SUB_RX.match(t)
        if ms and r['bold']:
            if sub is None:
                owner = code if code is not None else (blk if blk is not None else ch)
                sub = {'text': '', 'entries': [], 'level': 5 if len(ms.group(1)) == 1 and code and '.' in code['c'] else 4}
                owner.setdefault('subdivs', []).append(sub)
            sub_entry = {'d': ms.group(1), 'da': ms.group(2), 'title': ms.group(3).strip(), 'notes': []}
            sub['entries'].append(sub_entry)
            target = sub_entry['notes']; note = None
            continue
        if sub_entry is not None and r['bold'] and not any(rx.match(t) for _, rx in LABELS[lang]) and not note:
            sub_entry['title'] = join(sub_entry['title'], t)
            continue
        # ---- labels
        matched = False
        for typ, rx in LABELS[lang]:
            ml = rx.match(t)
            if ml:
                if target is None:
                    break
                first = ml.group(1).strip() if ml.groups() else ''
                if typ in ('use_additional', 'code_first', 'see'):
                    start_note(typ, first, r['x'])
                else:
                    base = r['w'][1][0] if len(r['w']) > 1 else None
                    start_note(typ, first or None, base)
                matched = True
                break
        if matched:
            continue
        if target is None:
            continue
        add_item(r)

    return {'chapters': chapters, 'blocks': blocks, 'codes': codes}


if __name__ == '__main__':
    for lang in ('en', 'th'):
        res = parse(lang)
        for n in [x for x in res['codes']]:
            for nt in n['notes']:
                nt.pop('base', None); nt.pop('bx', None)
        json.dump(res, open(f'/home/claude/src/tm_{lang}.json', 'w', encoding='utf8'), ensure_ascii=False)
        print(lang, 'chapters', len(res['chapters']), 'blocks', len(res['blocks']), 'codes', len(res['codes']))
