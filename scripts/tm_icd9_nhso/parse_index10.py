"""Parse the ICD-10-TM 2009 alphabetical index (Sections I and II) into entries.

Each entry: [level, text, code1, code2, section, tm]
  level 0 = lead term, 1.. = subterm depth (count of leading dashes)
Pages are three-column; columns are read top-to-bottom, left-to-right.
Writes /home/claude/src/index10.json
"""
import json, re
import pymupdf
from extract_tm import fix_thai

SRC = '/mnt/user-data/uploads/-10-TM_2009_AllOK.pdf'
SECTIONS = [(970, 1267, 'I'), (1269, 1299, 'II')]
CODE_TAIL = re.compile(r'\s+((?:[A-Z]\d\d(?:\.\d{1,3})?(?:\.-|-)?[†*]?\s*){1,2})$')
DASHES = re.compile(r'^((?:–\s*)+)')


REGIONS = {int(k): v for k, v in json.load(open('/home/claude/src/table_regions.json')).items()}


def page_lines(page):
    out = []
    skip = REGIONS.get(page.number + 1)
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            chars = [(c['c'], c['bbox'][0]) for s in l['spans'] for c in s['chars']]
            txt = ''.join(c for c, _ in chars)
            if not txt.strip():
                continue
            x = next((x for c, x in chars if c.strip() and c != '#'), chars[0][1])
            bold = any('Bold' in s['font'] for s in l['spans'] if ''.join(c['c'] for c in s['chars']).strip())
            out.append({'x': x, 'y': l['bbox'][1], 'text': re.sub(r'\s+', ' ', txt).strip(), 'bold': bold})
    out = [o for o in out if 60 < o['y'] < 800]
    if skip:
        out = [o for o in out if not (skip[0] <= o['y'] < skip[1])]
    return out


def split_columns(lines):
    xs = sorted({round(o['x']) for o in lines})
    # column starts: the leftmost x, then any x that jumps > 100 from the previous column start
    starts = []
    for x in xs:
        if not starts or x - starts[-1] > 110:
            starts.append(x)
    cols = [[] for _ in starts]
    for o in lines:
        i = max(i for i, s in enumerate(starts) if o['x'] >= s - 5)
        o['cx'] = o['x'] - starts[i]
        cols[i].append(o)
    for c in cols:
        c.sort(key=lambda o: o['y'])
    return cols


def main():
    d = pymupdf.open(SRC)
    entries = []
    stack = []            # current path of terms by level (for "continued" lines)
    for a, b, sec in SECTIONS:
        for pg in range(a, b + 1):
            for col in split_columns(page_lines(d[pg - 1])):
                for o in col:
                    t = o['text']
                    if re.search(r'continued\s*$', t) or t in ('ICD-10-TM', ) or re.fullmatch(r'[A-Z]', t) or re.fullmatch(r'\d+', t):
                        continue
                    tm = t.startswith('#')
                    t = t.lstrip('#').strip()
                    m = DASHES.match(t)
                    level = len(re.findall('–', m.group(1))) if m else 0
                    body = t[m.end():].strip() if m else t
                    # continuation of the previous entry: no dash, not a lead term, indented
                    if not m and entries and (o['cx'] > 4 or t.startswith('-')):
                        prev = entries[-1]
                        joined = (prev[1] + ' ' + (prev[2] or '') + ' ' + body).replace('  ', ' ').strip() if prev[2] else (prev[1] + ' ' + body).strip()
                        mm = CODE_TAIL.search(' ' + joined)
                        if mm:
                            codes = mm.group(1).split()
                            prev[1] = joined[:len(joined) - len(mm.group(1))].strip()
                            prev[2] = codes[0]; prev[3] = codes[1] if len(codes) > 1 else None
                        else:
                            prev[1] = joined
                        continue
                    mm = CODE_TAIL.search(' ' + body)
                    c1 = c2 = None
                    if mm:
                        codes = mm.group(1).split()
                        c1 = codes[0]; c2 = codes[1] if len(codes) > 1 else None
                        body = body[:len(body) - len(mm.group(1))].strip()
                    entries.append([level, fix_thai(body), c1, c2, sec, tm])
    # normalise codes: drop trailing dash forms to a category reference, keep †/*
    for e in entries:
        for i in (2, 3):
            if e[i]:
                e[i] = e[i].replace('.-', '').rstrip('-')
    json.dump(entries, open('/home/claude/src/index10.json', 'w', encoding='utf8'), ensure_ascii=False)
    leads = sum(1 for e in entries if e[0] == 0)
    print('entries', len(entries), 'lead terms', leads, 'with code', sum(1 for e in entries if e[2]))


if __name__ == '__main__':
    main()
