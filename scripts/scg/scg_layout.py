import pymupdf, re, sys, json, collections
PDF = '<path to Final_SCG-2017_Modify_2026_1.pdf>'  # only used when this file is run directly
TH = 'ก-ฮ'
LABEL = re.compile(r'(การวินิจฉัย|Principal|Comorbid|Complication|Other|External|โรค|หัตถการ|Procedure|สัณฐาน|Morpholog|Main|Secondary|Operation|การผ่าตัด|รหัส)')
def fix_am(t):
    return re.sub(r'([' + TH + r'])\s([่-๋]?)า', lambda m: m.group(1) + m.group(2) + 'ำ', t)
def norm(t): return fix_am(re.sub(r'\s+', ' ', t).strip())
def rows_of(pg):
    pieces = []  # (x0, x1, ymid, text, [char x0s])
    for b in pg.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                cs = s['chars']
                if not ''.join(c['c'] for c in cs).strip(): continue
                bb = s['bbox']; pieces.append({'x0': bb[0], 'x1': bb[2], 'y': (bb[1] + bb[3]) / 2, 'h': bb[3] - bb[1], 'cs': cs})
    rows = []
    for p in sorted(pieces, key=lambda p: p['y']):
        if rows and abs(rows[-1]['y'] - p['y']) < 5: rows[-1]['ps'].append(p)
        else: rows.append({'y': p['y'], 'ps': [p]})
    for r in rows: r['ps'].sort(key=lambda p: p['x0'])
    return rows
def join(ps):
    out = ''; last = None
    for p in ps:
        t = ''.join(c['c'] for c in p['cs'])
        if last is not None and p['x0'] - last > 2 and not out.endswith(' ') and not t.startswith(' '): out += ' '
        out += t; last = p['x1']
    return norm(out)
def row_text(r): return join(r['ps'])
def split_row(r, xs):
    cols = [''] * len(xs); lastx = [None] * len(xs)
    for p in r['ps']:
        for c in p['cs']:
            x = c['bbox'][0]; k = 0
            for i, b in enumerate(xs):
                if x >= b - 6: k = i
            if c['c'] == ' ' and not cols[k]: continue
            cols[k] += c['c']
    return [norm(c) for c in cols]
def page_blocks(pg):
    """paragraph lines and reconstructed example tables, in reading order"""
    out = []; xs = None; tbl = None
    for r in rows_of(pg):
        t = row_text(r)
        if re.fullmatch(r'~\s*\d+\s*~', t) or re.fullmatch(r'[o°]', t): continue
        if 'แพทย์วินิจฉัย' in t and 'Coder' in t:
            allc = [c for p in r['ps'] for c in p['cs']]
            s = ''.join(c['c'] for c in allc)
            x1 = allc[s.index('แพทย์')]['bbox'][0]; x2 = allc[s.index('Coder')]['bbox'][0]
            xs = [0, x1, x2]; tbl = {'type': 'table', 'rows': []}; out.append(tbl); continue
        if xs:
            first = first_x(r)
            cells = split_row(r, xs)
            if first >= xs[1] - 6 or LABEL.match(cells[0]):
                tbl['rows'].append(cells); continue
            xs = None; tbl = None
        out.append({'type': 'line', 'x': round(first_x(r)), 'x1': round(max(p['x1'] for p in r['ps'])), 't': t, 'cells': gap_cells(r)})
    return out
def first_x(r):
    for p in r['ps']:
        for c in p['cs']:
            if c['c'].strip(): return c['bbox'][0]
    return r['ps'][0]['x0']
def gap_cells(r, gap=16):
    """split a row where the horizontal gap between characters is wide (columns of a printed table)"""
    cells, cur, last = [], '', None
    for p in r['ps']:
        for c in p['cs']:
            if not c['c'].strip():
                cur += c['c']; continue
            x0 = c['bbox'][0]
            if last is not None and x0 - last > gap:
                cells.append(cur); cur = ''
            cur += c['c']; last = max(last or 0, c['bbox'][2])
    cells.append(cur)
    return [norm(c) for c in cells if norm(c)]
if __name__ == '__main__':
    d = pymupdf.open(PDF)
    for n in map(int, sys.argv[1:]):
        print(f'=== page {n}')
        for b in page_blocks(d[n - 1]):
            if b['type'] == 'table':
                for c in b['rows']: print('   T|', ' | '.join(c))
            else: print(b['x'], b['t'])
