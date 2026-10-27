# เว็บค้นรหัส ICD

ค้นรหัสโรค ICD-10 (WHO 2016 ชื่อไทยจาก ICD-10-TM 2009) และรหัสหัตถการ ICD-9-CM FY15 (ThaiDRG)
มีดัชนี ตารางยาและสารเคมี ตารางเนื้องอก ICD-O ตารางอุบัติเหตุการขนส่งทางบก ตารางการแท้ง แนวทางการให้รหัส เกณฑ์ สปสช. 2562 ค้นด้วยคำย่อได้ และมีหลังบ้านสำหรับเพิ่มข้อมูล

เว็บ (GitHub Pages, อ่านอย่างเดียว): https://oatoracle.github.io/ICD-Search/

เวอร์ชันบน claude.ai (มีหลังบ้านออนไลน์): https://claude.ai/artifact/CZg1bWePmJkguh8v419fhS (หลังบ้าน: ต่อท้ายลิงก์ด้วย `#admin`)

## เปิดใช้ในเครื่อง
หน้าเว็บโหลดข้อมูลจากโฟลเดอร์ `web/data` จึงต้องเปิดผ่านเว็บเซิร์ฟเวอร์ ดับเบิลคลิกไฟล์ HTML ตรง ๆ จะโหลดข้อมูลไม่ได้

- Windows: ดับเบิลคลิก `start-web.bat` (ต้องมี Python) แล้วเบราว์เซอร์จะเปิด http://localhost:8000
- หรือในเทอร์มินัล: `cd web` แล้ว `python -m http.server 8000`
- หลังบ้านในเครื่อง: http://localhost:8000/index.html#admin

## โครงสร้างโฟลเดอร์
```
web/                        เว็บที่ใช้งาน
  index.html                โครงหน้า
  assets/app.css            หน้าตาเว็บ
  assets/app.js             การทำงานของเว็บ (ค้นหา ดัชนี ตาราง รายละเอียด และการรวมชั้นข้อมูล)
  assets/admin.js, admin.css   หลังบ้านผู้พัฒนา (โหลดเฉพาะหน้า #admin)
  data/manifest.json        รายการไฟล์ข้อมูล แหล่งที่มา และสคริปต์ที่สร้าง
  data/icd10/               ข้อมูลหลัก ICD-10: codes, keywords, tables, morph (ICD-O), index/
  data/icd9/                ข้อมูลหลัก ICD-9-CM: codes, keywords, index/
  data/shared/              คำย่อ แนวทาง เกณฑ์ สปสช.
  data/overlay.json         ข้อมูลที่ผู้พัฒนาเพิ่ม/แก้ไข (แก้ผ่านหลังบ้าน)
scripts/who_icd10/          สร้างข้อมูล ICD-10 จาก WHO 2016 (S0052, Index.pdf) + TM 2009, ICD-O
scripts/tm_icd9_nhso/       ถอดข้อมูลจาก ICD-10-TM 2009, ICD-9-CM (OCR), คู่มือ สปสช., คำย่อ
docs/backend.md             คู่มือหลังบ้านและรูปแบบข้อมูลที่เพิ่ม
docs/data-sources.md        แหล่งข้อมูลและสิ่งที่แก้ไข
docs/icd_schema.dbml        ER diagram
```

## แยกข้อมูลเป็นชั้น
- **ข้อมูลหลัก** (`data/icd10`, `data/icd9`, `data/shared`) สร้างจากเอกสารด้วยสคริปต์ ห้ามแก้มือ
- **ข้อมูลเพิ่มเติม** แก้ผ่านหลังบ้านเท่านั้น เก็บใน `data/overlay.json` (ในเครื่อง) หรือฐานข้อมูลของเว็บ (ออนไลน์)
- ลบรายการเพิ่มเติมเมื่อไรก็กลับเป็นข้อมูลหลัก รายละเอียดใน `docs/backend.md`

## สร้างข้อมูลหลักใหม่
สคริปต์ใช้ Python 3 + PyMuPDF (`pip install pymupdf`) ส่วน OCR ใช้ tesseract
พาธในสคริปต์ยังเป็นพาธของเครื่องที่ใช้สร้าง (`/home/claude/...`, ผลลัพธ์ไปที่ `/home/claude/icd-site/data/...`) ต้องแก้ให้ชี้ไปที่ไฟล์ PDF และโฟลเดอร์ `web/data` ในเครื่องก่อนรัน

ลำดับ ICD-10: `extract_who.py tab` และ `extract_who.py idx` → `parse_who_tab.py`, `parse_who_index.py` → `build_merged.py` → `build_who_index.py` → `parse_morph.py`
(build_merged.py ใช้ข้อมูลที่ถอดจาก TM 2009 เป็นฐานชื่อไทย สร้างจาก scripts/tm_icd9_nhso: extract_tm.py → parse_tm.py → build_icd10.py)

คำย่อ: แก้ `scripts/tm_icd9_nhso/abbr.py` แล้วรัน `python abbr.py --check` (หรือเพิ่มผ่านหลังบ้านโดยไม่ต้องแก้สคริปต์)

## ข้อควรระวัง
- ชื่อภาษาไทย 244 รหัส (ติดหมายเหตุในหน้าเว็บ) แปลเพิ่ม ไม่ใช่คำแปลทางการ
- ไม่ได้รวมไฟล์ PDF ต้นฉบับไว้ในโฟลเดอร์นี้
- ใช้ประกอบการทำงาน ตรวจซ้ำกับบัญชีจำแนกฉบับที่หน่วยงานใช้ทุกครั้ง

## สกิลออกแบบหน้าเว็บ (ui-ux-pro-max)
โฟลเดอร์ `.claude/skills/ui-ux-pro-max` คือสกิล [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) v2.15.0 (MIT License, Next Level Builder) พร้อมคลังข้อมูลครบ
Claude Code จะโหลดสกิลนี้เองเมื่อทำงานในโฟลเดอร์โปรเจกต์นี้ ใช้ตรวจหรือออกแบบหน้าเว็บ เช่น สั่ง `/ui-ux-pro-max ตรวจสอบ`
ปรับจากต้นฉบับเพียงจุดเดียว: พาธสคริปต์ใน SKILL.md ใช้ `${CLAUDE_PLUGIN_ROOT:-.}` เพื่อให้รันจากรากโปรเจกต์ได้เมื่อไม่ได้ติดตั้งเป็นปลั๊กอิน
