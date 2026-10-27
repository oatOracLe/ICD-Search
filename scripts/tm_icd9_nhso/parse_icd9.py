"""Parse OCR'd ICD-9-CM FY15 tabular list (pages 11–282) into chapters / categories / codes.

Each code also gets ThaiDRG flags from the box drawn around it in the book:
  grey filled box  -> 'or'   (OR procedure)
  outline box      -> 'drg'  (non-OR procedure but affects ThaiDRG)
Writes /home/claude/src/icd9_parsed.json and prints a QA report.
"""
import json, re
from collections import defaultdict, Counter
import cv2
import numpy as np
from ocrlines import lines

FIRST, LAST = 11, 282
CODE_RX = re.compile(r'^[|(\[]?(\d\d)[.,](\d{1,2})[\)\]\}|,.:;!]*$')
CAT_RX = re.compile(r'^(\d\d)$')
CHAPTER_RX = re.compile(r'^(\d{1,2}A?)[.,]?\s+([A-Z][A-Z ,\-–&/]{12,})')
LABELS = [('excludes', re.compile(r'^Excludes?\s*:?\s*(.*)$', re.I)),
          ('includes', re.compile(r'^Includes?\s*:?\s*(.*)$', re.I)),
          ('code_also', re.compile(r'^(Code also\b.*)$', re.I)),
          ('omit', re.compile(r'^(Omit code\b.*)$', re.I)),
          ('note', re.compile(r'^Note\s*:?\s*(.*)$', re.I)),
          ('use_additional', re.compile(r'^(Use additional .*)$', re.I))]
report = defaultdict(list)


def box_kind(img, w):
    """Classify the box around a code token: 'or' (grey fill), 'drg' (outline) or ''."""
    x, y, ww, hh = w[0], w[1], w[2], w[3]
    H, W = img.shape
    pad = 14
    x0, x1 = max(0, x - pad), min(W, x + ww + pad)
    y0, y1 = max(0, y - pad), min(H, y + hh + pad)
    reg = img[y0:y1, x0:x1].astype(np.int32)
    if reg.size == 0:
        return ''
    # background tone just around the glyphs (exclude dark text pixels)
    ring = np.concatenate([img[y0:y0 + 6, x0:x1].ravel(), img[y1 - 6:y1, x0:x1].ravel()]).astype(np.int32)
    inner = reg[pad // 2: -pad // 2 or None, :]
    bg = inner[inner > 150]
    med = np.median(bg) if bg.size else 255
    if 150 < med < 232:
        return 'or'
    # outline: a dark vertical stroke left of the digits spanning most of the height
    left = img[y:y + hh, max(0, x - 10):max(1, x - 1)]
    if left.size:
        col_line = (left < 230).mean(axis=0)
        if col_line.max() > 0.7:
            return 'drg'
    return ''


def parse(src='ocr9'):
    chapters, cats, codes = [], [], []
    ch = cat = code = None
    target = None
    note = None
    chapter_buf = None
    last_x3 = {}
    tmpl = None          # fourth-digit subclassification being read
    templates = []
    for pg in range(FIRST, LAST + 1):
        img = cv2.imread(f'/home/claude/src/ocr9/p{pg:03d}.png', 0)
        L = [l for l in lines(f'/home/claude/src/{src}/p{pg:03d}.tsv') if 190 < l['y'] < 2280]
        L = [l for l in L if not re.search(r'OR procedure|TABULAR LIST OF PROCEDURES', l['text'])]
        # a code printed alone beside a wrapped title: pull the title lines next to it into the code line
        used = set()
        for i, l in enumerate(L):
            if len(l['words']) == 1 and CODE_RX.match(l['words'][0][4]):
                cx, cy = l['x'], l['y']
                near = [j for j, m in enumerate(L) if j != i and j not in used and abs(m['y'] - cy) < 48
                        and cx + 70 < m['x'] < cx + 140 and not re.match(r'^(Excludes|Includes|Code also|Note|Omit)', m['text'])
                        and (m['y'] <= cy + 5 or m['text'][:1].islower())]
                near.sort(key=lambda j: L[j]['y'])
                if near:
                    tw = []
                    for j in near:
                        tw += L[j]['words']; used.add(j)
                    l['words'] = l['words'] + tw
                    l['text'] = ' '.join(w[4] for w in l['words'])
                    l['y'] = min([cy] + [L[j]['y'] for j in near])
        L = [l for j, l in enumerate(L) if j not in used]
        L.sort(key=lambda r: (r['y'], r['x']))
        # per-page code columns
        xs3 = [l['x'] for l in L if CODE_RX.match(l['words'][0][4]) and len(CODE_RX.match(l['words'][0][4]).group(2)) == 1]
        x3 = min(xs3) if xs3 else last_x3.get(pg % 2)
        if xs3:
            last_x3[pg % 2] = x3
        if tmpl is not None and tmpl['open']:
            tmpl['x'] = None         # list may continue on the next page with a different margin
        for l in L:
            w = l['words']; t = l['text']; first = w[0][4]
            # ---- fourth-digit subclassification templates
            if re.search(r'fourth[-—–\s]*digit subclassifications? (?:is|to)|Requires the use of one of the following', t, re.I):
                tmpl = {'intro': t, 'entries': {}, 'pg': pg, 'owner': (code or cat or {}).get('c') or (cat or {}).get('id'), 'x': None, 'open': True}
                templates.append(tmpl); note = None
                continue
            if tmpl is not None and tmpl['open']:
                me = re.match(r'^(\d)[.,s]?\s+([a-z].*)$', t)
                if me and (tmpl['x'] is None or abs(l['x'] - tmpl['x']) < 25) and me.group(1) not in tmpl['entries']:
                    tmpl['x'] = l['x']; tmpl['entries'][me.group(1)] = me.group(2); tmpl['last'] = me.group(1)
                    continue
                if not tmpl['entries'] and not CODE_RX.match(first):
                    tmpl['intro'] += ' ' + t
                    continue
                if tmpl['entries'] and not CODE_RX.match(first) and not CAT_RX.match(first):
                    continue   # inclusion terms under a site entry (or its continuation on the next page)
                tmpl['open'] = False
            mb = re.match(r'^[\[(|{]([\dQOo,\s\-–—]+)[\])}|]', first)
            if mb and code is not None and code['lvl'] == 3:
                code['valid'] = mb.group(1).replace('Q', '0').replace('O', '0').replace('o', '0')
                w = w[1:]
                if not w:
                    continue
                l = dict(l, words=w, text=' '.join(x[4] for x in w), x=w[0][0]); t = l['text']; first = w[0][4]
            # chapter heading (may wrap)
            if chapter_buf is not None:
                chapter_buf += ' ' + t
                m = re.search(r'\((\d\d)(?:\s*[-–]\s*(\d\d))?\)', chapter_buf)
                if m or len(chapter_buf) > 200:
                    ch['title'] = re.sub(r'\s*\(.*$', '', chapter_buf).strip(' ,')
                    ch['range'] = (m.group(1) + ('–' + m.group(2) if m and m.group(2) else '')) if m else ''
                    chapter_buf = None
                continue
            mch = CHAPTER_RX.match(t)
            if mch and sum(c.isupper() for c in t) > 0.6 * sum(c.isalpha() for c in t):
                ch = {'id': mch.group(1), 'title': '', 'range': '', 'notes': []}
                chapters.append(ch); cat = code = None; target = ch['notes']; note = None
                rest = t[mch.end(1):].lstrip('.,').strip()
                m = re.search(r'\((\d\d)(?:\s*[-–]\s*(\d\d))?\)', rest)
                if '(' not in rest:
                    ch['title'] = rest.strip(' ,')
                elif m:
                    ch['title'] = re.sub(r'\s*\(.*$', '', rest).strip(' ,'); ch['range'] = m.group(1) + ('–' + m.group(2) if m.group(2) else '')
                else:
                    chapter_buf = rest
                continue
            # two-digit category
            if CAT_RX.match(first) and len(w) > 1 and w[1][4][:1].isupper() and (x3 is None or l['x'] < x3 + 40):
                cat = {'id': first, 'title': ' '.join(x[4] for x in w[1:]), 'ch': ch['id'] if ch else None, 'notes': [], 'pg': pg, 'tx': w[1][0]}
                cats.append(cat); code = None; target = cat['notes']; note = None
                continue
            if len(w) > 1 and CODE_RX.match(first) and re.match(r'^[(|\[{]+[A-Za-z]', w[1][4]):
                w = [w[0], (w[1][0], w[1][1], w[1][2], w[1][3], re.sub(r'^[(|\[{]+', '', w[1][4]))] + w[2:]
                l = dict(l, words=w, text=' '.join(x[4] for x in w))
            mc = CODE_RX.match(first)
            if mc and len(w) > 1 and w[1][4][:1].isalpha() and not re.search(r'\d\d\.\d', w[1][4]) \
                    and (x3 is None or l['x'] <= x3 + 150):
                lvl3 = x3 is not None and l['x'] < x3 + 45
                d = mc.group(2)
                if lvl3 and len(d) == 2:
                    report['3-char code read with extra digit'].append(f'{first} p{pg}'); d = d[0]
                if not lvl3 and len(d) == 1:
                    report['4-char code read short'].append(f'{first} p{pg}')
                c = f'{mc.group(1)}.{d}'
                code = {'c': c, 'title': ' '.join(x[4] for x in w[1:]), 'cat': cat['id'] if cat else None,
                        'notes': [], 'pg': pg, 'tx': w[1][0], 'box': box_kind(img, w[0]), 'lvl': 3 if lvl3 else 4}
                codes.append(code); target = code['notes']; note = None
                continue
            owner = code or cat
            # wrapped title: same x as title, starts lowercase / bracket, before any note
            if owner is not None and note is None and target is owner['notes'] and not owner['notes'] \
                    and abs(l['x'] - owner['tx']) <= 10 and (first[:1].islower() or first[:1] in '([{&'):
                owner['title'] += ' ' + t
                continue
            if target is None:
                continue
            lab = None
            for typ, rx in LABELS:
                m = rx.match(t)
                if m:
                    lab = (typ, m.group(1).strip()); break
            if lab:
                typ, rest = lab
                base = w[1][0] if typ in ('excludes', 'includes', 'note') and len(w) > 1 else None
                note = {'t': typ, 'items': [rest] if rest else [], 'base': base, 'lx': l['x']}
                target.append(note)
                continue
            if note is None:
                note = {'t': 'inclusion', 'items': [], 'base': l['x'], 'lx': l['x']}
                target.append(note)
            if note['base'] is None:
                note['base'] = l['x']
            items = note['items']
            if note['t'] in ('code_also', 'omit', 'use_additional') and items and l['x'] > note['lx'] + 5 and not items[-1].endswith(':'):
                items[-1] += ' ' + t; continue
            if items and l['x'] > note['base'] + 12:
                if items[-1].rstrip().endswith(':') or items[-1].startswith('• ') and l['x'] < note.get('subx', 9999) + 8:
                    note['subx'] = l['x']
                    items.append('• ' + t)
                else:
                    items[-1] += ' ' + t
                continue
            if items and l['x'] < note['base'] - 12 and note['t'] != 'inclusion':
                # dedent: a new inclusion block after a note
                note = {'t': 'inclusion', 'items': [t], 'base': l['x'], 'lx': l['x']}
                target.append(note); continue
            items.append(t)
    return chapters, cats, codes, templates


CONFUSE = {'0': '689', '1': '74', '2': '7', '3': '85', '4': '19', '5': '63', '6': '0858', '7': '12', '8': '360', '9': '40'}


def fix_sequence(codes, cat_start):
    # 1) code printed under a category must share its two-digit prefix,
    #    unless that category's header was simply missed by OCR on this pass
    for c in codes:
        pre = c['c'][:2]
        if c['cat'] and pre != c['cat'] and pre in cat_start and cat_start[pre] <= c['pg'] and int(pre) > int(c['cat']):
            c['cat'] = pre
            continue
        if c['cat'] and c['c'][:2] != c['cat']:
            new = c['cat'] + c['c'][2:]
            report['prefix corrected'].append(f"{c['c']}→{new} p{c['pg']}")
            c['c'] = new
    # 2) out-of-order codes within a category: try one-digit OCR confusions that restore order
    def k(x):
        a, b = x.split('.')
        return (int(a), b.ljust(2, ' '))
    existing = Counter(c['c'] for c in codes)
    for i, c in enumerate(codes):
        prev = codes[i - 1]['c'] if i else None
        nxt = codes[i + 1]['c'] if i + 1 < len(codes) else None
        bad = (prev and k(c['c']) <= k(prev) and prev[:2] == c['c'][:2]) and not (nxt and k(nxt) <= k(c['c']))
        bad = bad or existing[c['c']] > 1 and prev and k(c['c']) <= k(prev)
        if not bad:
            continue
        a, b = c['c'].split('.')
        cands = []
        for pos in range(len(b)):
            for alt in CONFUSE.get(b[pos], ''):
                nb = b[:pos] + alt + b[pos + 1:]
                cand = f'{a}.{nb}'
                if len(nb) != len(b) or existing[cand]:
                    continue
                if prev and k(cand) <= k(prev):
                    continue
                if nxt and nxt[:2] == a and k(cand) >= k(nxt):
                    continue
                cands.append(cand)
        if len(cands) >= 1:
            report['sequence corrected'].append(f"{c['c']}→{cands[0]} p{c['pg']} (options {cands})")
            existing[c['c']] -= 1; existing[cands[0]] += 1
            c['c'] = cands[0]
        else:
            report['sequence unresolved'].append(f"{prev}→{c['c']}→{nxt} p{c['pg']}")


def digits_of(spec):
    out = []
    for part in re.split(r'[,\s]+', spec.replace('—', '-').replace('–', '-')):
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-')[:2]
            if a.isdigit() and b.isdigit():
                out += [str(i) for i in range(int(a), int(b) + 1)]
        elif part.isdigit():
            out.append(part)
    return out


import glob as _glob
INDEX_CODES = set()
for _f in _glob.glob('/home/claude/icd-site/data/icd9/index/I-*.json'):
    INDEX_CODES.update(r[2] for r in json.load(open(_f)) if r[2])


def generate_from_templates(codes, templates):
    scope = {}
    for t in templates:
        if not t['entries']:
            continue
        ms = re.search(r'section\s+([\d.,\sand]+)', t['intro'])
        if ms:
            for s in re.findall(r'\d\d(?:\.\d)?', ms.group(1)):
                scope[s] = t
        elif t['owner']:
            scope[t['owner']] = t
    have = {c['c'] for c in codes}
    out = []
    gen = 0
    for c in codes:
        out.append(c)
        if c['lvl'] != 3:
            continue
        t = scope.get(c['c']) or scope.get(c['c'][:2])
        if not t:
            continue
        valid = digits_of(c.get('valid') or '') or (sorted(t['entries']) if scope.get(c['c']) is t else [])
        from_index = [d for d in t['entries'] if c['c'] + d in INDEX_CODES and d not in valid]
        if from_index:
            report['site digits added from index evidence'].append(c['c'] + ':' + ''.join(from_index))
            valid = sorted(set(valid) | set(from_index))
        c['title'] = re.sub(r'\s+[0O9©]$', '', c['title'])
        for dgt in valid:
            cc = c['c'] + dgt
            if cc in have or dgt not in t['entries']:
                continue
            out.append({'c': cc, 'title': f"{c['title']}, {t['entries'][dgt]}", 'cat': c['cat'], 'notes': [], 'pg': c['pg'],
                        'tx': c['tx'], 'box': c['box'], 'lvl': 4, 'gen': True})
            have.add(cc); gen += 1
    report['generated from site subclassifications'] = [str(gen)]
    def sk(x):
        a, b = x['c'].split('.')
        return (int(a), b)
    return sorted(out, key=sk)


def clean(s):
    s = re.sub(r'\s*[®©%]\s*', ' ', s)
    s = s.replace(' ,', ',').replace('( ', '(').replace(' )', ')')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def main():
    ch_a, cats_a, codes_a, tmpl_a = parse('ocr9')
    ch_b, cats_b, codes_b, tmpl_b = parse('ocr9b')
    cat_start = {}
    for c in cats_a + cats_b:
        cat_start[c['id']] = min(cat_start.get(c['id'], 9999), c['pg'])
    fix_sequence(codes_a, cat_start)
    fix_sequence(codes_b, cat_start)
    merged = {}
    for c in codes_a:
        merged.setdefault(c['c'], c)
    added = []
    for c in codes_b:
        if c['c'] not in merged:
            merged[c['c']] = c; added.append(c['c'])
        elif not merged[c['c']]['box'] and c['box']:
            merged[c['c']]['box'] = c['box']
    report['recovered from second OCR pass'] = added
    def sk(x):
        a, b = x['c'].split('.')
        return (int(a), b)
    codes = sorted(merged.values(), key=sk)
    cats = {}
    for c in cats_a + cats_b:
        cats.setdefault(c['id'], c)
    cats = [cats[k] for k in sorted(cats)]
    chapters = {}
    for c in ch_a + ch_b:
        chapters.setdefault(c['id'], c)
    chapters = list(chapters.values())
    # carry bracket digits from pass b where pass a missed them
    vb = {c['c']: c.get('valid') for c in codes_b if c.get('valid')}
    for c in codes:
        if not c.get('valid') and c['c'] in vb:
            c['valid'] = vb[c['c']]
    codes = generate_from_templates(codes, tmpl_a)
    # codes recovered by targeted re-OCR of gaps (see recovered9.json)
    try:
        rec = json.load(open('/home/claude/src/recovered9.json'))
    except FileNotFoundError:
        rec = {}
    have = {c['c'] for c in codes}
    for cc, (pg, title) in rec.items():
        if cc not in have:
            codes.append({'c': cc, 'title': title, 'cat': cc[:2], 'notes': [], 'pg': pg, 'tx': 0, 'box': '', 'lvl': 4 if len(cc.split('.')[1]) == 2 else 3})
            report['recovered by gap re-OCR'].append(cc)
    codes.sort(key=lambda x: (int(x['c'].split('.')[0]), x['c'].split('.')[1]))
    # QA: ordering and duplicates
    seen = Counter(c['c'] for c in codes)
    report['duplicate codes'] = [k for k, v in seen.items() if v > 1]
    prev = None
    for c in codes:
        if prev and c['c'] < prev['c'] and c['c'][:2] == prev['c'][:2]:
            report['out of order'].append(f"{prev['c']}→{c['c']} p{c['pg']}")
        if c['cat'] and c['c'][:2] != c['cat']:
            report['code not under its category'].append(f"{c['c']} under {c['cat']} p{c['pg']}")
        prev = c
    for c in codes:
        c['title'] = clean(c['title'])
        for n in c['notes']:
            n['items'] = [clean(i) for i in n['items'] if clean(i)]
            for k in ('base', 'lx', 'subx'):
                n.pop(k, None)
        c['notes'] = [n for n in c['notes'] if n['items']]
    for o in cats + chapters:
        o['title'] = clean(o['title'])
        for n in o['notes']:
            n['items'] = [clean(i) for i in n['items'] if clean(i)]
            for k in ('base', 'lx', 'subx'):
                n.pop(k, None)
        o['notes'] = [n for n in o['notes'] if n['items']]
    json.dump({'chapters': chapters, 'cats': cats, 'codes': codes}, open('/home/claude/src/icd9_parsed.json', 'w'), ensure_ascii=False)
    print('chapters', len(chapters), [c['id'] + ' ' + c['range'] for c in chapters])
    print('categories', len(cats), 'codes', len(codes), 'boxes', Counter(c['box'] for c in codes))
    for k, v in report.items():
        print(f'{k}: {len(v)}', v[:15])


if __name__ == '__main__':
    main()
