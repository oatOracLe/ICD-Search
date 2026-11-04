"""Parse the CDC/NCHS ICD-9-CM Volume 3 index (Pindex12.rtf, FY2012) into index rows.

The RTF gives each index line its own paragraph; where its text starts (\\li + \\fi) gives the level:
0 twips = lead term (level 0), each further 360 twips = one level deeper.

    python3 parse_pindex12.py <Pindex12.rtf> <out.json>

Output: {"rows": [[level, text, code1, code2, 0], ...], "li": {indent: count}}
code1/code2 = the code(s) at the end of the line (None when the line has none).
"""
import json
import re
import sys

SKIP_DEST = {'fonttbl', 'colortbl', 'stylesheet', 'info', 'listtable', 'listoverridetable', 'rsidtbl', 'generator',
             'xmlnstbl', 'themedata', 'colorschememapping', 'latentstyles', 'datastore', 'mmathPr', 'pgdsctbl',
             'header', 'footer', 'headerl', 'headerr', 'footerl', 'footerr', 'pict', 'object', 'fldinst', 'bkmkstart',
             'bkmkend', 'filetbl', 'revtbl', 'listpicture', 'defchp', 'defpap', 'wgrffmtfilter', 'ftnsep', 'ftnsepc',
             'aftnsep', 'aftnsepc', 'xmlopen', 'xmlclose', 'mmathPr', 'protusertbl', 'docvar', 'shppict', 'nonshppict'}
SYMBOLS = {'emdash': '\u2014', 'endash': '\u2013', 'bullet': '\u2022', 'lquote': '\u2018', 'rquote': '\u2019',
           'ldblquote': '\u201c', 'rdblquote': '\u201d', 'tab': ' ', 'line': ' ', '~': ' ', '_': '-', '-': ''}
TOKEN = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([^\\{}\r\n]+)|[\r\n]+")


def paragraphs(src):
    stack = []          # (skipping,) per group
    skip = False
    li = fi = 0
    buf = []
    uc = 1
    pending_skip = 0
    for m in TOKEN.finditer(src):
        word, num, hexc, sym, brace, text = m.groups()
        if brace == '{':
            stack.append(skip)
            continue
        if brace == '}':
            skip = stack.pop() if stack else False
            continue
        if word is not None:
            if word in SKIP_DEST:
                skip = True
                continue
            if skip:
                continue
            if word == 'pard':
                li = 0
                fi = 0
            elif word == 'li' and num is not None:
                li = int(num)
            elif word == 'fi' and num is not None:
                fi = int(num)
            elif word == 'par':
                yield li + fi, ''.join(buf)
                buf = []
            elif word == 'uc' and num is not None:
                uc = int(num)
            elif word == 'u' and num is not None:
                n = int(num)
                buf.append(chr(n + 65536 if n < 0 else n))
                pending_skip = uc
            elif word in SYMBOLS:
                buf.append(SYMBOLS[word])
            continue
        if sym is not None:
            if sym == '*':
                skip = True
            elif not skip:
                buf.append({'~': ' ', '-': '', '_': '-'}.get(sym, sym))
            continue
        if skip:
            continue
        if hexc is not None:
            if pending_skip:
                pending_skip -= 1
                continue
            buf.append(bytes([int(hexc, 16)]).decode('cp1252', 'replace'))
            continue
        if text is not None:
            if pending_skip:
                cut = min(pending_skip, len(text))
                text = text[cut:]
                pending_skip -= cut
            buf.append(text)
    if buf:
        yield li + fi, ''.join(buf)


CODE_END = re.compile(r'\s(\d{2}(?:\.\d{1,2})?)(?:\s*\[(\d{2}(?:\.\d{1,2})?)\])?\s*$')


def main(src_path, out_path):
    src = open(src_path, encoding='latin-1').read()
    rows, lis = [], {}
    for li, text in paragraphs(src):
        t = re.sub(r'\s+', ' ', text).strip()
        if not t:
            continue
        lis[li] = lis.get(li, 0) + 1
        if li < 0 or li % 360:  # title lines and headings use other indents
            continue
        lvl = li // 360
        t = re.sub(r'\s*--\s*see\b', ' \u2013 see', t)
        c1 = c2 = None
        m = CODE_END.search(t)
        if m:
            c1, c2 = m.group(1), m.group(2)
            t = t[:m.start()].rstrip()
        rows.append([lvl, t, c1, c2, 0])
    json.dump({'rows': rows, 'li': lis}, open(out_path, 'w'), ensure_ascii=False)
    print(len(rows), 'rows; indents', sorted(lis.items()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
