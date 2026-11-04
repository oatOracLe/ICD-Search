"""Check and repair data/icd9/codes.json (OCR of the FY2015 book) against the official CMS v32 (FY2015)
procedure list, ref/CMS32_DESC_LONG_SG.txt.

- English titles of valid codes that OCR garbled or cut short are replaced by the CMS long title.
  Titles the book prints short on purpose ("Other" under a category) are kept: CMS spells them out
  differently, they are not errors (similarity < 0.5).
- Codes CMS has but the OCR missed are added (with a Thai name made the same way as their siblings).
- Codes the OCR made up (not in CMS, not a category of CMS codes) are removed.
- Stray OCR marks (@, }, ”, #4 ...) are cleaned from category titles.

    python3 icd9_cms_fix.py [data dir]
"""
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ICD_DATA', '/home/claude/icd-site/data')
KEEP_OURS = {'41.05'}   # CMS long title has a typo ("transpant")

# microscopic examination (90.0-91.9): fourth digit = kind of examination
MICRO = {'1': 'การย้อมดูเชื้อแบคทีเรีย', '2': 'การเพาะเชื้อ', '3': 'การเพาะเชื้อและทดสอบความไวต่อยา',
         '4': 'การตรวจหาปรสิต', '5': 'การตรวจหาสารพิษ', '6': 'การตรวจเซลล์บล็อกและแปปสเมียร์',
         '9': 'การตรวจด้วยกล้องจุลทรรศน์อื่น'}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def clean(t):
    t = re.sub(r'\s*@', '', t)
    t = re.sub(r'\s+[”#¥]+\s*\d*\s*$', '', t)
    t = re.sub(r'\(([^(){}]*)\}', r'(\1)', t)
    t = re.sub(r'\{([^(){}]*)\}', r'(\1)', t)
    t = re.sub(r'\{([^(){}]*)\)', r'(\1)', t)
    return re.sub(r'\s+', ' ', t).strip()


def main():
    cms = {}
    for line in open(os.path.join(HERE, 'ref', 'CMS32_DESC_LONG_SG.txt'), encoding='latin-1'):
        m = re.match(r'(\d+)\s+(.*)', line.strip())
        if m:
            c = m.group(1)
            cms[c[:2] + ('.' + c[2:] if len(c) > 2 else '')] = m.group(2).strip()
    path = os.path.join(DATA, 'icd9', 'codes.json')
    d = json.load(open(path, encoding='utf-8'))
    by = {x['c']: x for x in d['codes']}
    fixed, added, removed = [], [], []

    # 1. titles
    for c, x in by.items():
        if c in cms:
            if x['en'] != cms[c] and c not in KEEP_OURS:
                if difflib.SequenceMatcher(None, norm(x['en']), norm(cms[c])).ratio() >= 0.5:
                    fixed.append((c, x['en'], cms[c]))
                    x['en'] = cms[c]
        else:
            t = clean(x['en'])
            if t != x['en']:
                fixed.append((c, x['en'], t))
                x['en'] = t

    # 2. codes the OCR made up: not in CMS and no CMS code under them
    for c in list(by):
        if len(c) == 5 and c not in cms and not any(k.startswith(c) for k in cms):
            removed.append((c, by[c]['en']))
            del by[c]

    # 3. codes the OCR missed
    def site_th(digit, parent):
        # the Thai site name used by a sibling category for the same fourth digit, e.g. 77.34 for 78.34
        # site digits mean different bones in 77-78 and in 79, so only a category of the same two digits counts
        for k, y in sorted(by.items()):
            if len(k) == 5 and k.endswith(digit) and k[:2] == parent[:2] and k[:4] != parent and y.get('p') and by.get(y['p']) and y.get('th'):
                pth = by[y['p']].get('th', '')
                if y['th'].startswith(pth + ' '):
                    return y['th'][len(pth) + 1:]
        return None
    for c, en in sorted(cms.items()):
        if c in by or len(c) != 5:
            continue
        parent = c[:4]
        p = by.get(parent)
        if not p:
            continue
        x = {'c': c, 'b': p['b'], 'en': en, 'th': '', 'leaf': True, 'p': parent, 'thx': 1}
        if p.get('drg'):
            x['drg'] = p['drg']
        if c[:2] in ('90', '91') and c[-1] in MICRO:
            x['th'] = MICRO[c[-1]] + ' (' + p['th'] + ')'
        else:
            s = site_th(c[-1], parent)
            x['th'] = (p['th'] + ' ' + s) if s else p['th']
        p['leaf'] = False
        by[c] = x
        added.append((c, en, x['th']))

    d['codes'] = sorted(by.values(), key=lambda x: x['c'])   # the book's order is code order
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('titles fixed %d, codes added %d, removed %d, total %d' % (len(fixed), len(added), len(removed), len(d['codes'])))
    for r in removed:
        print('  - removed', *r)
    for a in added[:8]:
        print('  + added', *a)
    return fixed, added, removed


if __name__ == '__main__':
    main()
