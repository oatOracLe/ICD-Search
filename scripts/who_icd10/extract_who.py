"""Extract text lines from WHO ICD-10 2016 PDFs (S0052 tabular, Index) with glyph repair.

Some embedded Arial/Times subsets have broken ToUnicode maps: the text layer shows U+FFFD
or the glyph id instead of the letter. Those subsets keep the standard Arial/Times glyph
order, so a broken ASCII character is chr(gid + 29); a few accented/typographic glyphs are
mapped by hand (HIGH). Spaces are rebuilt from character gaps because some lines have none.

Output: <name>_lines.jsonl, one visual line per row:
  {"p": page, "y": top, "x": left, "t": text, "b": first span bold,
   "spans": [[x, text, bold, x_end], ...]}
"""
import json, sys
import pymupdf

HIGH = {112: 'é', 113: 'é', 108: 'ä', 111: 'ç', 115: 'ë', 124: 'ö', 129: 'ü', 135: '•', 177: '–', 181: '“',
        182: '’', 237: '–', 149: '≥'}


def decode_chars(s):
    """[(x0, x1, ch)] for one texttrace span."""
    chars = s['chars']
    real = [c for c in chars if c[1] != -1]
    std = all(c[0] in (c[1], c[1] + 29, 0xFFFD) or c[1] in (191, 192) or c[0] > 0x2000 for c in real)
    out = []
    prev_g = None
    for c in chars:
        u, g, bbox = c[0], c[1], c[3]
        x0, x1 = bbox[0], bbox[2]
        if g == -1:                      # second letter of an fi/fl ligature
            ch = chr(u) if 32 <= u < 0xFFFD else ('l' if prev_g == 192 else 'i')
            out.append((x0, x1, ch)); continue
        prev_g = g
        broken = u == 0xFFFD or (std and u == g)
        if not broken:
            ch = chr(u)
        elif g in (191, 192):
            ch = 'f'
        elif 3 <= g <= 97:
            ch = chr(g + 29)
        else:
            ch = HIGH.get(g, '†')
        if ch == '':               # symbol-font asterisk
            ch = '*'
        out.append((x0, x1, ch))
    return out


def run(src, name):
    doc = pymupdf.open(src)
    with open(f'/home/claude/who/{name}_lines.jsonl', 'w', encoding='utf8') as fo:
        for pn in range(doc.page_count):
            spans = []
            for s in doc[pn].get_texttrace():
                cs = decode_chars(s)
                if not ''.join(c[2] for c in cs).strip():
                    continue
                # split a run that crosses a column gap into separate pieces
                pieces, curp, last = [], [], None
                for c in cs:
                    if last is not None and c[0] - last > max(8, s['size'] * 0.9) and c[2] != ' ':
                        pieces.append(curp); curp = []
                    curp.append(c)
                    if c[2] != ' ':
                        last = c[1]
                pieces.append(curp)
                for pc in pieces:
                    if not ''.join(c[2] for c in pc).strip():
                        continue
                    xs = [c[0] for c in pc if c[2] != ' ']
                    spans.append({'y': round(s['bbox'][1], 1), 'x': min(xs), 'x1': max(c[1] for c in pc), 'cs': pc,
                                  'b': 'Bold' in s['font'], 'size': s['size']})
            spans.sort(key=lambda r: (r['y'], r['x']))
            lines = []
            for sp in spans:
                if lines and abs(lines[-1][0]['y'] - sp['y']) < 2.5:
                    lines[-1].append(sp)
                else:
                    lines.append([sp])
            for L in lines:
                L.sort(key=lambda r: r['x'])
                text, out_spans, prev = '', [], None
                for sp in L:
                    st = ''
                    for x0, x1, ch in sp['cs']:
                        if prev is not None and ch != ' ' and not (text + st).endswith(' ') and x0 - prev > sp['size'] * 0.2:
                            st += ' '
                        st += ch
                        prev = x1 if prev is None else max(prev, x1)
                    text += st
                    out_spans.append([round(sp['x'], 1), ' '.join(st.split()), sp['b'], round(sp['x1'], 1)])
                text = ' '.join(text.split())
                fo.write(json.dumps({'p': pn + 1, 'y': L[0]['y'], 'x': round(L[0]['x'], 1), 't': text, 'b': L[0]['b'],
                                     'spans': out_spans}, ensure_ascii=False) + '\n')
    print(name, 'pages', doc.page_count)


if __name__ == '__main__':
    if sys.argv[1] == 'tab':
        run('/home/claude/who/S0052.pdf', 'tab')
    else:
        run('/home/claude/who/Index.pdf', 'idx')
