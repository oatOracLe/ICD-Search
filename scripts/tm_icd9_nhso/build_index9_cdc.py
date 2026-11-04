"""Build the ICD-9-CM procedure index (data/icd9/index/, data/icd9/keywords.json) from the official
CDC/NCHS file ref/Pindex12.rtf (FY2012) instead of the OCR of the scanned FY2015 book.

The OCR index (parse_index9.py) lost many indent levels and misread words; the RTF keeps both exactly.
FY2013-FY2015 added only a few procedure codes; their index lines from the FY2015 book are added below
(ADDED), and four codes the FY2012 file prints wrongly are corrected (FIX, checked against the book and CMS v32).

    python3 build_index9_cdc.py [data dir]
"""
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ICD_DATA', '/home/claude/icd-site/data')
OUT = os.path.join(DATA, 'icd9', 'index')

FIX = {  # (start of the line, code in Pindex12) -> code
    ('Anastomosis', 'abdominal artery to coronary artery', '37.17'): '36.17',
    ('Ball operation', 'undercutting', '40.92'): '49.02',
    ('Balanoplasty', None, '64.69'): '64.49',
    ('Bisection', 'stapes foot plate', '19.79'): '19.19',
}
# path from the lead term (each level must already exist except the last, which is added) -> code
ADDED = [
    (['Implant, implantation', 'epiretinal visual prosthesis'], '14.81'),
    (['Implant, implantation', 'prosthesis, prosthetic device', 'epiretinal visual'], '14.81'),
    (['Infusion (intra-arterial) (intravenous)', '4-Factor Prothrombin Complex Concentrate'], '00.96'),
    (['Infusion (intra-arterial) (intravenous)', 'glucarpidase'], '00.95'),
    (['Infusion (intra-arterial) (intravenous)', 'Kcentra™'], '00.96'),
    (['Infusion (intra-arterial) (intravenous)', 'Voraxaze®'], '00.95'),
    (['Injection (into) (hypodermically) (intramuscularly) (intravenously) (acting locally or systemically)', 'glucarpidase'], '00.95'),
    (['Injection (into) (hypodermically) (intramuscularly) (intravenously) (acting locally or systemically)', 'Voraxaze®'], '00.95'),
    (['Removal', 'epiretinal visual prosthesis'], '14.82'),
    (['Replacement', 'prosthesis', 'epiretinal visual'], '14.83'),
    (['Revision', 'prosthesis', 'epiretinal visual'], '14.83'),
]


def sort_key(t):
    return re.sub(r'[^a-z0-9 ]', '', t.lower())


def subtree_end(rows, i):
    j = i + 1
    while j < len(rows) and rows[j][0] > rows[i][0]:
        j += 1
    return j


def find_child(rows, i, text):
    """index of the direct child of rows[i] whose text starts with `text` (or None)"""
    lvl, j, end = rows[i][0] + 1, i + 1, subtree_end(rows, i)
    while j < end:
        if rows[j][0] == lvl and rows[j][1].lower().startswith(text.lower()):
            return j
        j += 1
    return None


def main():
    spec = importlib.util.spec_from_file_location('p12', os.path.join(HERE, 'parse_pindex12.py'))
    p12 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p12)
    tmp = os.path.join(OUT, '_pindex12.json')
    os.makedirs(OUT, exist_ok=True)
    p12.main(os.path.join(HERE, 'ref', 'Pindex12.rtf'), tmp)
    rows = json.load(open(tmp))['rows']
    os.remove(tmp)
    rows = [r for r in rows if not (r[0] == 0 and (len(r[1]) == 1 or r[1] == 'Index to Procedures'))]
    codes = {x['c'] for x in json.load(open(os.path.join(DATA, 'icd9', 'codes.json'), encoding='utf-8'))['codes']}
    # "Note: ..." paragraphs sit at the left margin in the RTF; they belong to the line above them
    for k in range(1, len(rows)):
        if rows[k][1].startswith('Note:'):
            rows[k][0] = rows[k - 1][0] + 1 if not rows[k - 1][1].startswith('Note:') else rows[k - 1][0]

    # corrections
    stack, fixed = [], 0
    for r in rows:
        stack = stack[:r[0]] + [r[1]]
        for (lead, sub, bad), good in FIX.items():
            if r[2] == bad and stack[0].startswith(lead) and (sub is None or r[1].startswith(sub)):
                r[2] = good
                fixed += 1
    # FY2013-FY2015 additions
    added = 0
    for path, code in ADDED:
        i = next(k for k, r in enumerate(rows) if r[0] == 0 and r[1].lower().startswith(path[0].lower()))
        for part in path[1:-1]:
            j = find_child(rows, i, part)
            if j is None:
                raise SystemExit('index path not found: %r' % path)
            i = j
        lvl, end, pos = rows[i][0] + 1, subtree_end(rows, i), None
        for k in range(i + 1, end):
            # subterms are alphabetical after the "with" / "without" block that opens each list
            # (a bare "with" line is followed by the line it governs, printed at the same indent)
            after_bare_with = rows[k - 1][0] == lvl and rows[k - 1][1] in ('with', 'without')
            if rows[k][0] == lvl and not after_bare_with and not re.match(r'(with|without)\b', rows[k][1]) and sort_key(rows[k][1]) > sort_key(path[-1]):
                pos = k
                break
        rows.insert(pos if pos is not None else end, [lvl, path[-1], code, None, 0])
        added += 1

    bad = sorted({c for r in rows for c in r[2:4] if c and c not in codes})
    by, kw, letter, stack = defaultdict(list), defaultdict(list), 'A', []
    for r in rows:
        if r[0] == 0 and r[1][:1].isalpha() and not r[1].startswith('Note:'):
            letter = r[1][0].upper()
        by[letter].append(r)
        stack = stack[:r[0]] + [r[1]]
        for c in r[2:4]:
            if c and c in codes:
                kw[c].append(' '.join(stack))
    for f in os.listdir(OUT):
        if f.startswith('I-') and f.endswith('.json'):
            os.remove(os.path.join(OUT, f))
    manifest = {'sections': {'I': 'ดัชนีหัตถการ'}, 'letters': {'I': {}},
                'source': 'CDC/NCHS ICD-9-CM Index to Procedures FY2012 (Pindex12.rtf) + FY2013-2015 additions'}
    for L, rs in sorted(by.items()):
        json.dump(rs, open(os.path.join(OUT, 'I-%s.json' % L), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        manifest['letters']['I'][L] = len(rs)
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    stop = {'see', 'also', 'code', 'with', 'without', 'and', 'the', 'for', 'other', 'nec', 'nos', 'by', 'of', 'or'}
    kwout = {}
    for c, paths in kw.items():
        seen, words = set(), []
        for p in paths:
            for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p.lower()):
                if w not in seen and len(w) > 2 and w not in stop:
                    seen.add(w)
                    words.append(w)
        kwout[c] = ' '.join(words)[:400]
    json.dump(kwout, open(os.path.join(DATA, 'icd9', 'keywords.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    leaf = {x['c'] for x in json.load(open(os.path.join(DATA, 'icd9', 'codes.json'), encoding='utf-8'))['codes'] if x.get('leaf')}
    print('rows %d, leads %d, fixed %d, added %d, codes not in codes.json %s, leaf codes never in index %d'
          % (len(rows), sum(1 for r in rows if r[0] == 0), fixed, added, bad, len(leaf - set(kw))))


if __name__ == '__main__':
    main()
