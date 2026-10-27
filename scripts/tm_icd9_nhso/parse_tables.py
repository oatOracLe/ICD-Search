"""Extract the three tables of the ICD-10-TM 2009 alphabetical index.

  drugs     Section III, Table of drugs and chemicals (pp. 1301–1462)
            columns: poisoning (Chapter XIX), accidental, intentional self-harm, undetermined intent, adverse effect
  neoplasm  'Neoplasm, neoplastic' table in Section I (pp. 1158–1180)
            columns: malignant primary, malignant secondary, in situ, benign, uncertain/unknown behaviour
  abortion  'Abortion' complication table in Section I (pp. 972–973), 4th characters for O03–O06 / O08

Row: [level, term, cell1, cell2, ..., tm]   (cell '' when empty)
Writes /home/claude/icd-site/data/icd10/tables.json and table_regions.json (y-ranges the plain index parser must skip).
"""
import json, re
import pymupdf
from extract_tm import fix_thai

SRC = '/mnt/user-data/uploads/-10-TM_2009_AllOK.pdf'
d = pymupdf.open(SRC)
CODE = re.compile(r'^[A-Z]\d\d(?:\.[\d-]{1,3})*(?:\.-)*[†*]?$|^\.\d$|^–$|^-$')
LEADER = re.compile(r'^\.+$')


def lines_of(pg, y0=0, y1=10 ** 6):
    """Group words into visual lines: [(y, [(x, text), ...])]."""
    rows = {}
    for w in d[pg - 1].get_text('words'):
        x, y, t = w[0], w[1], w[4]
        if not (y0 <= y < y1) or y < 60 or y > 790 or LEADER.match(t):
            continue
        key = round(y / 3)
        rows.setdefault(key, []).append((x, y, t))
    out = []
    for k in sorted(rows):
        ws = sorted(rows[k])
        out.append((min(w[1] for w in ws), [(w[0], w[2]) for w in ws]))
    return out


HEADER_WORDS = {'Malignant', 'Uncertain', 'In', 'situ', 'Benign', 'or', 'unknown', 'Primary', 'Secondary', 'behaviour',
                'Poisoning', 'Adverse', 'effect', 'in', 'Substance', 'Intentional', 'Undetermined', 'therapeutic', 'Chapter', 'XIX',
                'Accidental', 'self-harm', 'intent', 'use'}


def split_row(words, first_col_x):
    """Separate the term (left of the first value column) from the cell tokens."""
    term, cells = [], []
    words = [(x, t.lstrip('.') if re.match(r'^\.+[A-Z]\d', t) else t) for x, t in words]
    for x, t in words:
        if x >= first_col_x - 12 and (CODE.match(t) or t in ('–', '-')):
            cells.append((x, t))
        else:
            term.append(t)
    joined = ' '.join(term)
    tm0 = joined.startswith('#')
    joined = joined.lstrip('#').strip()
    m = re.match(r'^((?:[–-]\s*)+)', joined)
    lvl = len(re.findall('[–-]', m.group(1))) if m else 0
    term = joined[m.end():].split() if m else term
    tm = tm0
    if term and term[0] == '#':
        tm = True; term = term[1:]
    if '#' in term:
        tm = True; term = [t for t in term if t != '#']
    return lvl, ' '.join(term).strip(), cells, tm


def assign(cells, grid):
    out = [''] * len(grid)
    for x, t in cells:
        i = min(range(len(grid)), key=lambda k: abs(grid[k] - x))
        if abs(grid[i] - x) < 30:
            out[i] = t if t not in ('–', '-') else ''
    return out


def table(pages, header_words, ncols, region_end=None, region_start=None):
    rows = []
    regions = {}
    for pg in pages:
        L = lines_of(pg)
        # header: column anchor x's from the header words on this page
        hdr = {}
        hy = None
        hmin = None
        for y, ws in L:
            for x, t in ws:
                for i, hw in enumerate(header_words):
                    if t == hw and i not in hdr:
                        hdr[i] = x; hy = max(hy or 0, y); hmin = min(hmin or 10 ** 6, y)
        if len(hdr) < ncols:
            continue
        grid = [hdr[i] for i in range(ncols)]
        start = (region_start or {}).get(pg, 60)
        end = 10 ** 6
        for y, ws in L:
            if y <= start:
                continue
            if region_end and region_end(ws):
                end = y; break
        regions[pg] = [start, end]
        for y, ws in L:
            if not (start < y < end) or hmin - 2 <= y <= hy + 2:
                continue
            text = ' '.join(t for _, t in ws)
            if re.search(r'continued\s*$', text) or text.isdigit() or all(t in HEADER_WORDS for _, t in ws):
                continue
            lvl, term, cells, tm = split_row(ws, min(grid))
            vals = assign(cells, grid)
            if not term and not any(vals):
                continue
            # wrapped term line (no dashes, indented, no values) continues the previous row
            if rows and lvl == 0 and not any(vals) and rows[-1][-1] is not None and ws[0][0] > rows[-1][-1] + 3 \
                    and not term[:1].isupper():
                rows[-1][1] = (rows[-1][1] + ' ' + term).strip(); continue
            if rows and lvl == 0 and not term and any(vals):
                # values printed on the line below a wrapped term
                rows[-1][2:2 + ncols] = [a or b for a, b in zip(rows[-1][2:2 + ncols], vals)]; continue
            rows.append([lvl, fix_thai(term)] + vals + [tm, ws[0][0]])
    for r in rows:
        r.pop()               # drop x used for continuation detection
    return rows, regions


def three_col_resumes(ws):
    # the normal three-column index starts again: a dash or term at the 2nd/3rd column positions
    return any((240 <= x <= 262 or 395 <= x <= 412) and t in ('–',) for x, t in ws)


out = {}
# ---- drugs
rows, reg_d = table(range(1301, 1463), ['Chapter', 'Accidental', 'Intentional', 'Undetermined', 'Adverse'], 5)
out['drugs'] = {
    'title': 'ตารางยาและสารเคมี', 'en': 'Table of drugs and chemicals',
    'cols': [{'en': 'Poisoning (Chapter XIX)', 'th': 'พิษ', 'range': 'T36–T65'},
             {'en': 'Accidental', 'th': 'อุบัติเหตุ', 'range': 'X40–X49'},
             {'en': 'Intentional self-harm', 'th': 'ทำร้ายตนเอง', 'range': 'X60–X69'},
             {'en': 'Undetermined intent', 'th': 'ไม่ทราบเจตนา', 'range': 'Y10–Y19'},
             {'en': 'Adverse effect in therapeutic use', 'th': 'ผลไม่พึงประสงค์จากการใช้ยารักษา', 'range': 'Y40–Y59'}],
    'rows': rows}
out['drugs']['rows'] = [r for r in rows if not (r[0] == 0 and re.fullmatch(r'[A-Z]', r[1]) and not any(r[2:7]))]
print('drugs rows', len(out['drugs']['rows']))

# ---- neoplasm
neo_pages = range(1158, 1181)
rows, reg_n = table(neo_pages, ['Primary', 'Secondary', 'situ', 'Benign', 'behaviour'], 5, region_end=three_col_resumes,
                    region_start={1158: 345})
first_sub = next(i for i, r in enumerate(rows) if r[0] >= 1)
neo_notes = [r[1] for r in rows[1:first_sub] if r[1] and r[1] != 'Notes']
rows = rows[:1] + rows[first_sub:]
# inline 'Note –' paragraphs inside the table (e.g. under bone) become notes on the preceding row
clean, inline = [], []
for r in rows:
    if r[0] == 0 and clean and (r[1].startswith('Note') or inline and not any(r[2:7]) or inline and r[1][:1].islower() and len(r[1]) > 40):
        inline.append(r[1]); continue
    if inline:
        clean[-1].append(' '.join(inline)); inline = []
    clean.append(r)
rows = clean
merged = []
for r in rows:
    if merged and r[0] == 0 and (r[1][:1].islower() or r[1][:1] in ')('):
        p = merged[-1]; p[1] = p[1] + ' ' + r[1]; p[2:7] = [a or b for a, b in zip(p[2:7], r[2:7])]; continue
    merged.append(r)
rows = merged
# join wrapped note lines into numbered paragraphs
paras = []
for t in neo_notes:
    if re.match(r'^\d\.\s', t) or not paras:
        paras.append(t)
    else:
        paras[-1] += ' ' + t
neo_notes = [p.replace('\uf0b8', '◊') for p in paras]
for r in rows:
    r[1] = r[1].replace('\uf0b8', '◊').strip()
out['neoplasm_notes'] = neo_notes
out['neoplasm'] = {
    'title': 'ตารางเนื้องอก', 'en': 'Neoplasm, neoplastic',
    'cols': [{'en': 'Malignant primary', 'th': 'มะเร็งปฐมภูมิ'}, {'en': 'Malignant secondary', 'th': 'มะเร็งทุติยภูมิ'},
             {'en': 'In situ', 'th': 'มะเร็งระยะเริ่มแรก (in situ)'}, {'en': 'Benign', 'th': 'เนื้องอกไม่ร้าย'},
             {'en': 'Uncertain or unknown behaviour', 'th': 'ไม่แน่ชัดหรือไม่ทราบพฤติกรรม'}],
    'rows': rows, 'notes': neo_notes}
out.pop('neoplasm_notes')
print('neoplasm rows', len(rows), 'notes', len(neo_notes))

# ---- abortion (4th characters)
ab_rows = []
reg_a = {}
for pg, y0, y1 in ((972, 195, 790), (973, 60, 100)):
    L = lines_of(pg, y0, y1)
    reg_a[pg] = [60 if pg == 973 else 100, y1]
    for y, ws in L:
        text = ' '.join(t for _, t in ws)
        if re.search(r'continued\s*$', text):
            continue
        vals = [t for x, t in ws if re.match(r'^\.\d$', t)]
        term = [t for x, t in ws if not re.match(r'^\.\d$', t)]
        lvl = 0
        while term and term[0] in ('–', '-'):
            lvl += 1; term = term[1:]
        ab_rows.append([lvl, ' '.join(term)] + (vals + ['', '', ''])[:3] + [False])
out['abortion'] = {
    'title': 'ตารางภาวะแทรกซ้อนของการแท้ง', 'en': 'Abortion, complicated (by)',
    'note': 'หลักที่ 4 สำหรับ O03–O06 (การแท้งครั้งนี้) และ O08 (ภาวะแทรกซ้อนที่มารักษาภายหลัง)',
    'types': [{'c': 'O03', 'th': 'แท้งเอง (spontaneous)'}, {'c': 'O04', 'th': 'แท้งด้วยเหตุทางการแพทย์ (medical)'},
              {'c': 'O05', 'th': 'แท้งแบบอื่น (other)'}, {'c': 'O06', 'th': 'แท้ง ไม่ระบุ (unspecified)'}],
    'cols': [{'en': 'Current episode, complete or unspecified', 'th': 'ครั้งนี้ แท้งครบหรือไม่ระบุ'},
             {'en': 'Current episode, incomplete', 'th': 'ครั้งนี้ แท้งไม่ครบ'},
             {'en': 'Subsequent episode (O08)', 'th': 'มารักษาภาวะแทรกซ้อนภายหลัง (O08)'}],
    'rows': ab_rows}
print('abortion rows', len(ab_rows))

json.dump(out, open('/home/claude/icd-site/data/icd10/tables.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
regions = {}
for pg, r in list(reg_n.items()) + list(reg_a.items()):
    regions[str(pg)] = r
json.dump(regions, open('/home/claude/src/table_regions.json', 'w'), indent=0)
print('regions', regions)
