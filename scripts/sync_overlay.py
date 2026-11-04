"""Bring items added in the online back end (the artifact's database) into web/data/overlay.json.

Usage:
  python3 scripts/sync_overlay.py <source> [--dry-run]

<source> is either
  - an overlay.json exported from the #admin page (tab "นำเข้า / ส่งออก"), or
  - a folder of one-JSON-file-per-item documents (a dump of the database collection "overlay").

Items with the same id replace the file's item; {"deleted": true} removes it; account ids (by) are dropped.
The result is sorted by id so a commit shows only real changes. Prints what changed.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'web', 'data', 'overlay.json')


def load_source(path):
    if os.path.isdir(path):
        items = []
        for dirpath, _, files in os.walk(path):
            for f in sorted(files):
                if f.endswith('.json'):
                    items.append(json.load(open(os.path.join(dirpath, f), encoding='utf-8')))
        return items
    data = json.load(open(path, encoding='utf-8'))
    return data.get('items', data if isinstance(data, list) else [])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    cur = json.load(open(TARGET, encoding='utf-8'))
    by_id = {i['id']: i for i in cur.get('items', []) if i.get('id')}
    added, changed, removed = [], [], []
    for it in load_source(args[0]):
        if not isinstance(it, dict) or not it.get('id'):
            continue
        it = {k: v for k, v in it.items() if k not in ('by', '_src')}
        iid = it['id']
        if it.get('deleted'):
            if by_id.pop(iid, None) is not None:
                removed.append(iid)
            continue
        if not it.get('kind'):
            continue
        if iid not in by_id:
            added.append(iid)
        elif by_id[iid] != it:
            changed.append(iid)
        by_id[iid] = it
    out = {'version': 1, 'note': cur.get('note', 'ข้อมูลที่ผู้พัฒนาเพิ่ม/แก้ไข — แก้ผ่านหน้า #admin ไม่ต้องแก้มือ'),
           'items': [by_id[k] for k in sorted(by_id)]}
    print('added %d, changed %d, removed %d, total %d' % (len(added), len(changed), len(removed), len(out['items'])))
    for name, ids in (('+', added), ('~', changed), ('-', removed)):
        for i in ids:
            print(' ', name, i)
    if '--dry-run' not in sys.argv:
        with open(TARGET, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write('\n')


if __name__ == '__main__':
    main()
