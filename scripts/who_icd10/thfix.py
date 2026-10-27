"""Repair Thai text where the PDF extraction turned sara am (ำ) into mai tho + sara aa (้า)."""
import re

WORDS = [
    ('น้้า', 'น้ำ'), ('ช้้า', 'ช้ำ'), ('ซ้้า', 'ซ้ำ'), ('ต้้า', 'ต่ำ'),
    ('ต้าแหน่ง', 'ตำแหน่ง'), ('ล้าไส้', 'ลำไส้'), ('ก้าเนิด', 'กำเนิด'), ('บ้าบัด', 'บำบัด'),
    ('จ้ากัด', 'จำกัด'), ('จ้านวน', 'จำนวน'), ('ก้าลัง', 'กำลัง'), ('ส้าเร็จ', 'สำเร็จ'), ('ส้าหรับ', 'สำหรับ'),
    ('อ้านาจ', 'อำนาจ'), ('บ้ารุง', 'บำรุง'), ('ด้าเนิน', 'ดำเนิน'), ('ก้าหนด', 'กำหนด'), ('ค้าว่า', 'คำว่า'),
    ('ค้าอธิบาย', 'คำอธิบาย'), ('ก้าจัด', 'กำจัด'), ('ส้าคัญ', 'สำคัญ'), ('ท้าลาย', 'ทำลาย'), ('ซ้าซ้อน', 'ซ้ำซ้อน'),
    ('ต้่า', 'ต่ำ'), ('ซ้า', 'ซ้ำ'),
]
RX = [
    (re.compile(r'(?<!เ)ท้า(?!ย|ทาย|ว)'), 'ทำ'),            # ทำร้าย ทำให้ ทำงาน … (not เท้า ท้าย ท้าทาย)
    (re.compile(r'(?<=เลือด)ด้า(?!น)'), 'ดำ'),              # หลอดเลือดดำ
    (re.compile(r'(?<=สี)ด้า(?!น)'), 'ดำ'),
    (re.compile(r'(?<![หขผ])น้า'), 'น้ำ'),                   # น้ำ (not หน้า)
]


def fix(s):
    if not isinstance(s, str) or '้' not in s:
        return s
    for a, b in WORDS:
        s = s.replace(a, b)
    for rx, b in RX:
        s = rx.sub(b, s)
    return s


def fix_all(o):
    """Apply to every Thai string ('th' fields) in a nested structure."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'th':
                o[k] = [fix(x) for x in v] if isinstance(v, list) else fix(v)
            else:
                fix_all(v)
    elif isinstance(o, list):
        for v in o:
            fix_all(v)
    return o
