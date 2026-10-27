"""Extract ICD-10-TM 2009 bilingual tabular pages into per-column line records.

Output: tm_lines.jsonl — one record per visual line:
  {pg, col: 'en'|'th', y, x, font, size, bold, text}
Thai text is repaired for the sara-am (ำ) extraction quirk, which differs by span:
  * spans that contain the 'ำ' glyph use a mapping where า→ำ and real ำ→' ำ'
  * other spans render real ำ as ' า' (consonant [+tone] + space + า)
"""
import json, re, sys
import pymupdf

SRC = '/mnt/user-data/uploads/-10-TM_2009_AllOK.pdf'
FIRST, LAST = 83, 931          # chapters I–XXII + morphology (1-based, inclusive)
SPLIT_X = 285                  # left column = English, right column = Thai

THAI = re.compile(r'[฀-๿]')
TONE_FIX = re.compile(r'([ก-ฮ][่-๋]?) า')
TONE_SPLIT_FIX = re.compile(r'([ก-ฮ]) ([่-๋])า')


def fix_thai(t):
    if not THAI.search(t):
        return t
    if 'ำ' in t:
        t = t.replace(' ำ', '\u0001').replace('ำ', 'า').replace('\u0001', 'ำ')
        # a real ำ can also appear glued to the consonant in this mapping after a tone mark
        return t
    t = TONE_SPLIT_FIX.sub(lambda m: m.group(1) + m.group(2) + 'ำ', t)
    t = t.replace('น่ำ', 'น้ำ')
    return TONE_FIX.sub(lambda m: m.group(1) + 'ำ', t)


# Post-pass: repairs that need corpus evidence (a candidate spelling must be common elsewhere)
SUSPECT = [
    (re.compile(r'([ก-ฮ])้า'), lambda m: m.group(1) + 'ำ'),                 # font that writes ำ as ้า
    (re.compile(r'([ก-ฮ]ื) (อ)'), lambda m: m.group(1) + '้' + m.group(2)),  # lost mai tho: เนื อ → เนื้อ
    (re.compile(r'([ก-ฮ]ื) (อ)'), lambda m: m.group(1) + '่' + m.group(2)),  # lost mai ek: เสื อม → เสื่อม
    (re.compile(r'([ก-ฮ]) ([ะาิีึืุู็่้๊๋์ั])'), lambda m: m.group(1) + m.group(2)),  # stray space before a vowel
]


def corpus_repair(texts):
    corpus = '\n'.join(texts)
    cache = {}

    def freq(w):
        if w not in cache:
            cache[w] = corpus.count(w)
        return cache[w]

    fixed = 0
    out = []
    for t in texts:
        for rx, rep in SUSPECT:
            def sub(m):
                nonlocal fixed
                a, b = m.start(), m.end()
                cand = rep(m)
                w0 = t[max(0, a - 2):min(len(t), b + 3)]
                w1 = t[max(0, a - 2):a] + cand + t[b:min(len(t), b + 3)]
                if freq(w1) >= 2 and freq(w1) > freq(w0):
                    fixed += 1
                    return cand
                return m.group(0)
            t = rx.sub(sub, t)
        # a space between ื and อ is never valid Thai: restore the lost tone mark unconditionally
        def tone(m):
            nonlocal fixed
            a, b = m.start(), m.end()
            c1 = m.group(1) + '้' + m.group(2); c2 = m.group(1) + '่' + m.group(2)
            ctx = lambda c: t[max(0, a - 2):a] + c + t[b:min(len(t), b + 3)]
            fixed += 1
            return c2 if freq(ctx(c2)) > freq(ctx(c1)) else c1
        t = re.sub(r'([ก-ฮ]ื) (อ)', tone, t)
        out.append(t)
    return out, fixed


def main():
    d = pymupdf.open(SRC)
    out = open('/home/claude/src/tm_lines.jsonl', 'w', encoding='utf8')
    n = 0
    allrecs = []
    for pg in range(FIRST, LAST + 1):
        page = d[pg - 1]
        recs = []
        raw = page.get_text('rawdict')['blocks']
        split = SPLIT_X
        for b in raw:
            for l in b.get('lines', []):
                for s_ in l['spans']:
                    if s_['chars'] and THAI.search(''.join(ch['c'] for ch in s_['chars'])) and 200 < s_['chars'][0]['bbox'][0] < split:
                        split = s_['chars'][0]['bbox'][0] - 1
        for b in raw:
            for l in b.get('lines', []):
                cols = {}
                for s in l['spans']:
                    chars = s['chars']
                    if not chars:
                        continue
                    col = 'en' if chars[0]['bbox'][0] < split else 'th'
                    c = cols.setdefault(col, {'font': s['font'], 'size': s['size'], 'chars': [], 'bold': False})
                    if any(ch['c'].strip() for ch in chars) and 'Bold' in s['font']:
                        c['bold'] = True
                    if not any(ch[0].strip() for ch in c['chars']) and any(ch['c'].strip() for ch in chars):
                        c['font'] = s['font']; c['size'] = s['size']
                    span_txt = fix_thai(''.join(ch['c'] for ch in chars))
                    # keep geometry: re-map fixed text onto char boxes conservatively (fix only changes Thai chars)
                    if len(span_txt) == len(chars):
                        c['chars'] += [(span_txt[i], chars[i]['bbox'][0]) for i in range(len(chars))]
                    else:
                        x0 = chars[0]['bbox'][0]
                        c['chars'] += [(ch, x0) for ch in span_txt]
                for col, c in cols.items():
                    words = []
                    cur = ''; cx = None
                    for ch, x in c['chars']:
                        ch = ch.replace('\uf0b7', '•').replace('\u00a0', ' ')
                        if ch.isspace():
                            if cur: words.append([round(cx, 1), cur]); cur = ''
                            continue
                        if not cur: cx = x
                        cur += ch
                    if cur: words.append([round(cx, 1), cur])
                    if not words:
                        continue
                    text = ' '.join(w for _, w in words)
                    recs.append({'pg': pg, 'col': col, 'y': round(l['bbox'][1], 1), 'x': words[0][0],
                                 'font': c['font'], 'size': round(c['size'], 1), 'bold': c['bold'], 'text': text, 'w': words})
        for r in recs:
            if r['col'] == 'en' and THAI.search(r['text']):
                r['col'] = 'th'      # Thai text that overflowed onto the left of the next page
        # drop running headers / footers
        recs = [r for r in recs if 60 < r['y'] < 800]
        recs.sort(key=lambda r: (r['col'], r['y'], r['x']))
        allrecs.extend(recs)
    idx = [i for i, r in enumerate(allrecs) if THAI.search(r['text'])]
    fixed_texts, nfix = corpus_repair([allrecs[i]['text'] for i in idx])
    for i, t in zip(idx, fixed_texts):
        if t != allrecs[i]['text']:
            allrecs[i]['text'] = t
            allrecs[i]['w'] = [[allrecs[i]['x'], t]]
    print('corpus repairs', nfix)
    for r in allrecs:
        out.write(json.dumps(r, ensure_ascii=False) + '\n')
        n += 1
    out.close()
    print('lines', n)


if __name__ == '__main__':
    main()
