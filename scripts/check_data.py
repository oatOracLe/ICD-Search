#!/usr/bin/env python3
"""Checks the site data under web/data and guards against committing internal material.

Run from the repository root:
  python3 scripts/check_data.py               all checks (a-j)
  python3 scripts/check_data.py --guard-only  only the guard (j); scripts/hooks/pre-push runs this

Exit status 1 when any check reports an error. Warnings are printed but never fail the run.
Python 3.10+, standard library only.

  a  every JSON file under web/data parses (as a browser would: UTF-8, no NaN/Infinity)
  b  codes.json (ICD-10, ICD-9-CM): no duplicate codes, every parent "p" exists
  c  index/*.json: code references exist; manifest.json letter counts match the files
  d  tables.json: cells that look like ICD-10 codes exist
  e  abbr.json: every "@" alternative matches a code; every "top" code exists
  f  guide.json: every {"k": "cd", "key": CODE} exists in ICD-10 or ICD-9-CM
  g  nhso2562.json: every code pattern matches a code
  h  overlay.json: items have id and kind; references to unknown codes (warnings only)
  i  Thai text: no "ซ้ำย", no leaked running header of the NHSO 2562 manual
  j  guard: no tracked file named like internal material (SCG 2017 scans, PDFs, OneOCR/WinOCR
     files) and no tracked text file containing the hospital-only watermark

Code matching follows web/assets/app.js (compileAlt/altHit, nhsoMatch, patternHit, cellCode),
so an error means the reference is broken on the published site.
"""
import argparse
import bisect
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'web', 'data')
SYSTEMS = ('icd10', 'icd9')
LABEL = {'icd10': 'ICD-10', 'icd9': 'ICD-9-CM'}
SHOW = 5  # problems listed per check; the rest are only counted

# ------------------------------------------------------------------ guard (j)
# Tracked paths that must never be committed. Matched against the whole path, so folders count too.
FORBIDDEN_NAME = re.compile(
    r'(?i)scg[-_ ]?2017|guideline[-_ ]?2017|internal[-_](src|work)|oneocr|winocr|\.pdf$|\.dll$|\.onemodel$')
# Watermark printed on every page of the hospital-only SCG 2017 scans.
WATERMARK = 'ใช้ภายในโรงพยาบาลเท่านั้น'
# Tracked files that may *mention* the watermark because they explain the rule: path -> mentions allowed.
# More mentions than this, or any mention in another tracked text file, is treated as leaked text.
WATERMARK_ALLOWED = {
    'docs/data-sources.md': 1,  # says the SCG 2017 scans carry this watermark and were left out
    'docs/flow.md': 1,          # the "never push to GitHub" rule
}
# Not scanned for the watermark: they hold the guard's own patterns.
GUARD_SKIP = {'scripts/check_data.py', '.gitignore'}


def _watermark_regexes():
    # Also catches OCR/PDF-extraction variants: spaces or zero-width spaces between letters, า read
    # as ำ (the same fault that corrupts the NHSO manual text), and JSON written with \\uXXXX escapes.
    raw, esc = [], []
    for ch in WATERMARK:
        alts = 'าำ' if ch == 'า' else ch
        raw.append(b'(?:' + b'|'.join(re.escape(a.encode('utf-8')) for a in alts) + b')')
        esc.append(b'(?:' + b'|'.join(re.escape(('\\u%04x' % ord(a)).encode('ascii')) for a in alts) + b')')
    return (re.compile(rb'(?:[ \t\r\n]|\xc2\xa0|\xe2\x80\x8b)*'.join(raw)),
            re.compile(rb'(?:[ \t\r\n]|\\u00a0|\\u200b)*'.join(esc), re.IGNORECASE))


WATERMARK_RX = _watermark_regexes()


def watermark_count(data):
    """Occurrences of the watermark in raw file bytes."""
    return sum(len(rx.findall(data)) for rx in WATERMARK_RX)


def guard_name_problems(paths):
    return [f'{p}: tracked file name looks like internal material' for p in paths if FORBIDDEN_NAME.search(p)]


def guard_content_problem(path, data):
    """Problem text when a tracked file's bytes contain the watermark beyond its allowance, else None."""
    if path in GUARD_SKIP or b'\0' in data[:8192]:  # skip the guard's own files and binaries
        return None
    n, allowed = watermark_count(data), WATERMARK_ALLOWED.get(path, 0)
    if n <= allowed:
        return None
    if allowed:
        return (f'{path}: hospital-only watermark text {n}x, {allowed} allowed '
                f'(if these only explain the rule, raise WATERMARK_ALLOWED in scripts/check_data.py)')
    return f'{path}: contains the hospital-only watermark text ({n}x)'


def tracked_files():
    """(paths tracked by git relative to ROOT, None) or (None, reason)."""
    try:
        r = subprocess.run(['git', '-C', ROOT, 'ls-files', '-z'], capture_output=True)
    except OSError as e:
        return None, f'cannot run git: {e}'
    if r.returncode:
        msg = r.stderr.decode('utf-8', 'replace').strip().splitlines()
        return None, 'git ls-files failed: ' + (msg[0] if msg else f'exit {r.returncode}')
    return [p for p in r.stdout.decode('utf-8', 'surrogateescape').split('\0') if p], None


def check_guard(c, d=None):
    paths, why = tracked_files()
    if paths is None:
        c.err(why + ' (the guard needs a git checkout)')
        return
    for msg in guard_name_problems(paths):
        c.err(msg)
    scanned = mentions = 0
    for p in paths:
        try:
            with open(os.path.join(ROOT, p), 'rb') as f:
                data = f.read()
        except OSError:  # tracked but deleted in the working tree, or not a regular file
            continue
        scanned += 1
        msg = guard_content_problem(p, data)
        if msg:
            c.err(msg)
        elif p in WATERMARK_ALLOWED:
            mentions += watermark_count(data)
    c.info = f'{len(paths)} tracked files, {scanned} scanned; watermark mentions in allowed docs: {mentions}'


# ------------------------------------------------------------------ data helpers
class Codes:
    """One system's code list with the lookups app.js uses."""

    def __init__(self, codes):
        self.set = set(codes)
        self.sorted = sorted(self.set)
        self._cut = {}

    def __contains__(self, code):
        return code in self.set

    def starts(self, prefix):
        """Some code starts with prefix (or equals it)."""
        i = bisect.bisect_left(self.sorted, prefix)
        return i < len(self.sorted) and self.sorted[i].startswith(prefix)

    def category(self, code):
        """The code itself or one of its subdivisions (code + '.')."""
        return code in self.set or self.starts(code + '.')

    def between(self, lo, hi):
        """Some code has lo <= code[:len(lo)] <= hi (app.js ranges)."""
        cut = self._cut.get(len(lo))
        if cut is None:
            cut = self._cut[len(lo)] = sorted({x[:len(lo)] for x in self.set})
        i = bisect.bisect_left(cut, lo)
        return i < len(cut) and cut[i] <= hi


def alt_hits(db, alt):
    """app.js compileAlt + altHit for an abbreviation alternative starting with '@'."""
    r = alt[1:]
    if r.find('-') > 0:
        lo, hi = r.split('-')[:2]
        return db.between(lo, hi)
    return db.starts(r) if '.' in r else db.category(r)


def pattern_hits(db, p):
    """app.js patternHit (code patterns of overlay notes)."""
    p = p.strip().upper()
    if not p:
        return False
    if p == '*':
        return True
    if p.find('-') > 0:
        lo, hi = p.split('-')[:2]
        return db.between(lo, hi)
    return db.category(p) or ('.' in p and db.starts(p))


NHSO9_RANGE = re.compile(r'([0-9][0-9]\.[0-9]{1,2})-([0-9][0-9]\.[0-9]{1,2})')
NHSO10_RANGE = re.compile(r'([A-Z][0-9][0-9])-([A-Z][0-9][0-9])(?:\.([0-9]))?')


def nhso_hits(db, pat, sys_):
    """app.js nhsoMatch: does the pattern select at least one code?"""
    if sys_ == 'icd9':
        m = NHSO9_RANGE.fullmatch(pat)
        if m:
            # code text cut to each end's length: 31.1-31.29 holds 31.2x but not 31.3
            lo, hi = m[1], m[2]
            return any(x[:len(lo)] >= lo and x[:len(hi)] <= hi for x in db.sorted)
        return pat in db or (len(pat) == 4 and db.starts(pat))
    m = NHSO10_RANGE.fullmatch(pat)
    if m:
        lo, hi, sub = m.groups()
        return any(lo <= x[:3] <= hi and (not sub or x[4:5] == sub) for x in db.sorted)  # may cross letters (C00-D48)
    return db.starts(pat)  # 3 characters: same category; otherwise the code or a code starting with it


def index_ref(tok):
    """('code' | 'cat', code) named by an index cell, or None for a TABLE: link or a range."""
    t = re.sub('[†*]', '', tok).strip()
    if not t or t.startswith('TABLE:'):
        return None
    if t.endswith('-'):  # category such as K35.-
        t = t.rstrip('-').rstrip('.')
        return None if '-' in t else ('cat', t)
    return None if '-' in t else ('code', t)


ICD10_CELL = re.compile(r'[A-Z][0-9][0-9](?:\.[0-9]{1,2})?')


def table_cell_code(cell):
    """app.js cellCode: drop a trailing '.-' and the marks † * ( )."""
    return re.sub(r'[†*()]', '', re.sub(r'(\.-)+$', '', cell.strip()))


def short(v, n=60):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n - 1] + '…'


def _item_label(v, i):
    if isinstance(v, dict):
        if isinstance(v.get('c'), str):
            return v['c']
        if v.get('id') is not None:
            return f'id={v["id"]}'
    return str(i)


def nodes(o, path=''):
    """Yield (path, node) for o and everything inside it; list items are labelled by code or id."""
    yield path, o
    if isinstance(o, dict):
        for k, v in o.items():
            yield from nodes(v, f'{path}.{k}' if path else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from nodes(v, f'{path}[{_item_label(v, i)}]')


def labelled_rows(rows):
    """Yield (i, row, 'Lead / sub / sub') for index or table rows [level, text, ...]."""
    stack = []
    for i, r in enumerate(rows):
        if isinstance(r, list) and len(r) > 1 and isinstance(r[0], int) and r[0] >= 0:
            del stack[r[0]:]
            stack.append(short(str(r[1]), 40))
            yield i, r, ' / '.join(stack)
        else:
            yield i, r, '?'


class Data:
    def __init__(self):
        self.json = {}    # path relative to web/data -> parsed JSON
        self.bad = set()  # paths that did not parse
        self.other = []   # non-JSON files under web/data
        self.codes = {}   # system -> Codes

    def need(self, c, rel, warn=False):
        """Parsed file, or None after noting why the check cannot use it."""
        if rel in self.json:
            return self.json[rel]
        (c.warn if warn else c.err)(f'{rel}: ' + ('did not parse, see a' if rel in self.bad else 'missing'))
        return None

    def db(self, c, sys_):
        if sys_ not in self.codes:
            c.err(f'{sys_}/codes.json unusable, {LABEL[sys_]} references not checked')
        return self.codes.get(sys_)


# ------------------------------------------------------------------ checks a-i
def _no_constant(name):
    raise ValueError(f'{name} is not valid JSON')


def check_json(c, d):
    for dirpath, dirnames, files in os.walk(DATA):
        dirnames.sort()
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(dirpath, f), DATA).replace(os.sep, '/')
            if not f.lower().endswith('.json'):
                d.other.append(rel)
                continue
            try:
                with open(os.path.join(dirpath, f), encoding='utf-8-sig') as fh:
                    d.json[rel] = json.load(fh, parse_constant=_no_constant)
            except (OSError, ValueError) as e:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
                d.bad.add(rel)
                c.err(f'{rel}: {e}')
    c.info = f'{len(d.json) + len(d.bad)} files'


def check_codes(c, d):
    info = []
    for s in SYSTEMS:
        rel = f'{s}/codes.json'
        doc = d.need(c, rel)
        items = doc.get('codes') if isinstance(doc, dict) else None
        if not isinstance(items, list):
            if doc is not None:
                c.err(f'{rel}: no "codes" list')
            continue
        seen = set()
        for x in items:
            code = x.get('c') if isinstance(x, dict) else None
            if not isinstance(code, str) or not code:
                c.err(f'{rel}: entry without a code: {short(x)}')
            elif code in seen:
                c.err(f'{rel}: duplicate code {code}')
            else:
                seen.add(code)
        for x in items:
            p = x.get('p') if isinstance(x, dict) else None
            if p and p not in seen:
                c.err(f'{rel}: {x.get("c")} has parent {p!r}, which is not a code')
        d.codes[s] = Codes(seen)
        info.append(f'{LABEL[s]} {len(seen)}')
    c.info = ', '.join(info) + ' codes'


def check_index(c, d):
    refs = files_n = 0
    for s in SYSTEMS:
        folder = os.path.join(DATA, s, 'index')
        man = d.need(c, f'{s}/index/manifest.json')
        db = d.db(c, s)
        on_disk = sorted(f for f in os.listdir(folder) if f.endswith('.json') and f != 'manifest.json') \
            if os.path.isdir(folder) else []
        listed = {}
        letters = man.get('letters') if isinstance(man, dict) else None
        if man is not None and not isinstance(letters, dict):
            c.err(f'{s}/index/manifest.json: no "letters" table')
        for sec, per in (letters or {}).items():
            for letter, n in (per or {}).items():
                listed[f'{sec}-{letter}.json'] = n
        for f in sorted(set(on_disk) | set(listed)):
            rel = f'{s}/index/{f}'
            if f not in on_disk:
                c.err(f'{rel}: listed in manifest.json but missing')
                continue
            rows = d.json.get(rel)
            if rows is None:
                continue  # did not parse, reported by a
            files_n += 1
            if not isinstance(rows, list):
                c.err(f'{rel}: not a list of rows')
                continue
            if man is not None and f not in listed:
                c.err(f'{rel}: not listed in manifest.json')
            elif man is not None and listed[f] != len(rows):
                c.err(f'{rel}: manifest.json says {listed[f]} rows, file has {len(rows)}')
            if db is None:
                continue
            for i, r, where in labelled_rows(rows):
                if not (isinstance(r, list) and len(r) >= 4):
                    c.err(f'{rel} #{i}: malformed row {short(r)}')
                    continue
                for tok in r[2:4]:
                    if tok is None:
                        continue
                    ref = index_ref(tok) if isinstance(tok, str) else ('code', repr(tok))
                    if ref is None:
                        continue
                    refs += 1
                    if not (db.category(ref[1]) if ref[0] == 'cat' else ref[1] in db):
                        c.err(f'{rel} #{i} "{where}": {tok} not in {LABEL[s]}')
    c.info = f'{files_n} letter files, {refs} code references'


def check_tables(c, d):
    doc, db = d.need(c, 'icd10/tables.json'), d.db(c, 'icd10')
    if not isinstance(doc, dict) or db is None:
        return
    n = 0
    for name, t in doc.items():
        if not isinstance(t, dict):
            continue
        for ty in t.get('types') or []:
            code = ty.get('c') if isinstance(ty, dict) else None
            if code is not None:
                n += 1
                if code not in db:
                    c.err(f'tables.json {name} types: {code} not in ICD-10')
        for i, row, where in labelled_rows(t.get('rows') or []):
            for cell in row if isinstance(row, list) else ():
                if isinstance(cell, str) and ICD10_CELL.fullmatch(table_cell_code(cell)):
                    n += 1
                    if table_cell_code(cell) not in db:
                        c.err(f'tables.json {name} #{i} "{where}": {cell} not in ICD-10')
    c.info = f'{n} code cells'


def check_abbr(c, d):
    doc = d.need(c, 'shared/abbr.json')
    if not isinstance(doc, dict):
        return
    n = 0
    for s in SYSTEMS:
        db = d.db(c, s)
        table = doc.get(s)
        if not isinstance(table, dict):
            c.err(f'abbr.json: no "{s}" table')
            continue
        for key, entries in table.items():
            for e in entries if isinstance(entries, list) else [entries]:
                if not (isinstance(e, dict) and isinstance(e.get('m'), list) and isinstance(e.get('top'), list)):
                    c.err(f'abbr.json {s} "{key}": entry needs lists "m" and "top" (app.js reads both): {short(e)}')
                    continue
                if db is None:
                    continue
                for alt in e['m']:
                    if isinstance(alt, str) and alt.startswith('@'):
                        n += 1
                        if not alt_hits(db, alt):
                            c.err(f'abbr.json {s} "{key}": {alt} matches no code')
                for code in e['top']:
                    n += 1
                    if code not in db:
                        c.err(f'abbr.json {s} "{key}": top code {code} not in {LABEL[s]}')
    c.info = f'{n} code references'


def check_guide(c, d):
    doc = d.need(c, 'shared/guide.json')
    dbs = [d.db(c, s) for s in SYSTEMS]
    if doc is None or None in dbs:
        return
    n = 0
    for path, o in nodes(doc):
        if isinstance(o, dict) and o.get('k') == 'cd':
            n += 1
            key = o.get('key')
            if not (isinstance(key, str) and any(key in db for db in dbs)):
                c.err(f'guide.json {path}: {key!r} not in ICD-10 or ICD-9-CM (text {o.get("s")!r})')
    c.info = f'{n} code references'


def check_nhso(c, d):
    doc = d.need(c, 'shared/nhso2562.json')
    topics = doc.get('topics') if isinstance(doc, dict) else None
    if not isinstance(topics, list):
        if doc is not None:
            c.err('nhso2562.json: no "topics" list')
        return
    n = 0
    for t in topics:
        s = t.get('sys')
        if s not in SYSTEMS:
            c.err(f'nhso2562.json topic {t.get("id")}: unknown sys {s!r}')
            continue
        db = d.db(c, s)
        if db is None:
            continue
        for p in t.get('codes') or []:
            n += 1
            if not (isinstance(p, str) and nhso_hits(db, p, s)):
                c.err(f'nhso2562.json topic {t.get("id")} ({LABEL[s]}): {p!r} matches no code')
    c.info = f'{len(topics)} topics, {n} patterns'


OVERLAY_KINDS = {'code', 'abbr', 'note', 'row', 'morph', 'idx'}


def check_overlay(c, d):
    """Warnings only: the overlay is edited through the admin page and may add codes of its own."""
    doc = d.need(c, 'overlay.json', warn=True)
    items = doc.get('items') if isinstance(doc, dict) else None
    if not isinstance(items, list):
        if doc is not None:
            c.warn('overlay.json: no "items" list')
        return
    if any(s not in d.codes for s in SYSTEMS):
        c.warn('codes.json unusable, overlay code references not checked')
        return
    added = {s: set() for s in SYSTEMS}
    for it in items:
        if isinstance(it, dict) and it.get('kind') == 'code' and it.get('op') != 'hide' and it.get('sys') in added:
            added[it['sys']].add(it.get('c'))
    db = {s: Codes(d.codes[s].set | added[s]) if added[s] else d.codes[s] for s in SYSTEMS}
    seen = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            c.warn(f'overlay.json item #{i}: not an object')
            continue
        where = f'overlay.json item {it.get("id") or "#" + str(i)}'
        if not it.get('id'):
            c.warn(f'{where}: no id (the site ignores items without one)')
        elif it['id'] in seen:
            c.warn(f'{where}: duplicate id (the later item wins)')
        seen.add(it.get('id'))
        kind, s = it.get('kind'), it.get('sys')
        if not kind:
            c.warn(f'{where}: no kind')
            continue
        if kind not in OVERLAY_KINDS:
            c.warn(f'{where}: unknown kind {kind!r}')
            continue
        dbs = [db[x] for x in SYSTEMS] if kind == 'note' and s == 'all' else [db[s]] if s in db else []
        if kind == 'row':
            for cell in it.get('row') or []:
                if isinstance(cell, str) and ICD10_CELL.fullmatch(table_cell_code(cell)) \
                        and table_cell_code(cell) not in db['icd10']:
                    c.warn(f'{where}: table cell {cell} not in ICD-10')
            continue
        if kind == 'morph':
            continue
        if not dbs:
            c.warn(f'{where}: unknown sys {s!r}')
            continue
        if kind == 'code':
            if it.get('op') in ('edit', 'hide') and it.get('c') not in d.codes[s]:
                c.warn(f'{where}: {it.get("op")} of {it.get("c")!r}, which is not in {LABEL[s]}')
        elif kind == 'note':
            for p in it.get('codes') or []:
                if not (isinstance(p, str) and any(pattern_hits(x, p) for x in dbs)):
                    c.warn(f'{where}: code pattern {p!r} matches no code')
        elif kind == 'abbr':
            for alt in it.get('m') or []:
                if isinstance(alt, str) and alt.startswith('@') and not alt_hits(dbs[0], alt):
                    c.warn(f'{where}: {alt} matches no code')
            for code in it.get('top') or []:
                if code not in dbs[0]:
                    c.warn(f'{where}: top code {code} not in {LABEL[s]}')
        elif kind == 'idx':
            for tok in (it.get('c1'), it.get('c2')):
                ref = index_ref(tok) if isinstance(tok, str) else None
                if ref and not (dbs[0].category(ref[1]) if ref[0] == 'cat' else ref[1] in dbs[0]):
                    c.warn(f'{where}: index code {tok} not in {LABEL[s]}')
    c.info = f'{len(items)} items'


THAI_BAD = (
    ('"ซ้ำย" (ซ้าย with า read as ำ)', re.compile('ซ้ำย')),
    # header printed on every page of the NHSO 2562 manual; its text extraction reads า as ำ
    ('NHSO 2562 manual running header',
     re.compile('แนวทำงปฏิบัติ|บริกำร|ค่ำใช้จ่ำย|คณะกรรมกำรตรวจสอบเวชระเบียน|หลักประกันสุขภำพ|กำรสรุปและให้รหัส')),
)


def check_thai(c, d):
    strings = 0
    for rel in sorted(d.json) + d.other:
        if rel in d.json:
            found = []
            for p, o in nodes(d.json[rel]):
                if isinstance(o, str):
                    found.append((p, o))
                elif isinstance(o, dict):
                    found.extend((f'{p} (key)', k) for k in o)
        else:
            with open(os.path.join(DATA, rel), encoding='utf-8', errors='replace') as f:
                found = [('', f.read())]
        strings += len(found)
        for label, rx in THAI_BAD:
            where = [p for p, text in found if rx.search(text)]
            if where:
                more = f' … +{len(where) - 6}' if len(where) > 6 else ''
                c.err(f'{rel}: {label} in {len(where)} string(s): {", ".join(where[:6])}{more}')
    c.info = f'{strings} strings'


# ------------------------------------------------------------------ runner
class Check:
    def __init__(self, key, title):
        self.key, self.title, self.info = key, title, ''
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def check_app(c, d=None):
    """The installable app (PWA): every file sw.js precaches and every manifest icon must exist,
    or the service worker fails to install (CORE) or the app has no icon."""
    web = os.path.join(ROOT, 'web')
    sw = os.path.join(web, 'sw.js')
    if not os.path.exists(sw):
        c.err('web/sw.js missing')
        return
    src = open(sw, encoding='utf-8').read()
    n = 0
    for name in ('CORE', 'REST'):
        m = re.search(r'var ' + name + r' = \[(.*?)\];', src, re.S)
        if not m:
            c.err(f'sw.js: no {name} list')
            continue
        for path in re.findall(r"'([^']+)'", m.group(1)):
            n += 1
            if path != './' and not os.path.isfile(os.path.join(web, path)):
                c.err(f'sw.js {name}: {path} does not exist under web/')
    try:
        man = json.load(open(os.path.join(web, 'manifest.webmanifest'), encoding='utf-8'))
    except (OSError, ValueError) as e:
        c.err(f'manifest.webmanifest: {e}')
        return
    for ic in man.get('icons') or []:
        n += 1
        if not os.path.isfile(os.path.join(web, ic.get('src', ''))):
            c.err(f'manifest.webmanifest: icon {ic.get("src")!r} does not exist')
    if not any('maskable' in (ic.get('purpose') or '') for ic in man.get('icons') or []):
        c.warn('manifest.webmanifest: no maskable icon (Android crops the icon)')
    c.info = f'{n} files listed'


DATA_CHECKS = (
    ('a', 'JSON parses', check_json),
    ('b', 'codes', check_codes),
    ('c', 'index', check_index),
    ('d', 'tables.json', check_tables),
    ('e', 'abbr.json', check_abbr),
    ('f', 'guide.json', check_guide),
    ('g', 'nhso2562.json', check_nhso),
    ('h', 'overlay.json', check_overlay),
    ('i', 'Thai text', check_thai),
    ('k', 'app (PWA)', check_app),
)


def run(key, title, fn, d):
    c = Check(key, title)
    try:
        fn(c, d)
    except Exception as e:  # a crash in one check must not hide the others
        c.err(f'check crashed: {type(e).__name__}: {e}')
    return c


def main(argv=None):
    ap = argparse.ArgumentParser(description='Checks web/data and guards against committing internal material.')
    ap.add_argument('--guard-only', action='store_true', help='run only the guard (j); used by scripts/hooks/pre-push')
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors='backslashreplace')  # Thai text on a non-UTF-8 console
        except (AttributeError, ValueError):
            pass
    t0, d = time.time(), Data()
    checks = [] if args.guard_only else [run(k, t, fn, d) for k, t, fn in DATA_CHECKS]
    checks.append(run('j', 'guard', check_guard, d))
    for c in checks:
        state = 'FAIL' if c.errors else 'warn' if c.warnings else 'ok'
        counts = ', '.join(f'{len(x)} {w}{"s" if len(x) > 1 else ""}'
                           for x, w in ((c.errors, 'error'), (c.warnings, 'warning')) if x)
        print(f'{state:<4}  {c.key}  {c.title:<14} {c.info}' + (f'  [{counts}]' if counts else ''))
        for msgs, tag in ((c.errors, ''), (c.warnings, 'warning: ')):
            for m in msgs[:SHOW]:
                print(f'          {tag}{m}')
            if len(msgs) > SHOW:
                print(f'          … {len(msgs) - SHOW} more')
    failed = [c.key for c in checks if c.errors]
    n_err, n_warn = (sum(len(getattr(c, a)) for c in checks) for a in ('errors', 'warnings'))
    tail = f'{n_err} error(s), {n_warn} warning(s) in {time.time() - t0:.1f} s'
    print(f'FAILED checks {", ".join(failed)}: {tail}' if failed else f'OK: {len(checks)} check(s), {tail}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
