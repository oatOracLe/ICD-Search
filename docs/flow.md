# Flow ของงานทั้งหมด

หน้านี้แสดงว่าแต่ละงานเริ่มจากไหน ผ่านไฟล์หรือสคริปต์อะไร และไปจบที่ไหน แผนภาพทุกรูป GitHub วาดให้เอง ถ้าต้องการรายละเอียดของแต่ละขั้น ให้ดูไฟล์ที่ลิงก์ไว้

| # | งาน | ใช้เมื่อ |
|---|---|---|
| 1 | [ภาพรวม](#1-ภาพรวม) | อยากเห็นทั้งระบบในรูปเดียว |
| 2 | [ข้อมูล ICD-10](#2-ข้อมูล-icd-10) | สร้างรหัส ดัชนี ตาราง ICD-10 ใหม่ |
| 3 | [ข้อมูล ICD-9-CM](#3-ข้อมูล-icd-9-cm) | สร้างรหัส ชื่อไทย ดัชนีหัตถการใหม่ |
| 4 | [คำย่อ](#4-คำย่อ) | เพิ่มหรือแก้คำย่อ |
| 5 | [หน้าแนวทาง](#5-หน้าแนวทาง) | แก้แนวทางการให้รหัส เกณฑ์ สปสช. หรือกล่องสรุป |
| 6 | [ข้อเสนอจากผู้ใช้](#6-ข้อเสนอจากผู้ใช้) | ตรวจข้อเสนอที่ส่งมาทางฟอร์ม |
| 7 | [หลังบ้าน](#7-หลังบ้าน-admin) | เพิ่มหมายเหตุ แก้ชื่อรหัส โดยไม่แตะข้อมูลหลัก |
| 8 | [เผยแพร่](#8-เผยแพร่) | เอาสิ่งที่แก้ขึ้นเว็บ |

สีในแผนภาพ: 🟦 ไฟล์ต้นฉบับ 🟨 สคริปต์หรือคนทำ 🟩 ไฟล์ข้อมูลที่เว็บใช้

---

## 1. ภาพรวม

ข้อมูลมี 2 ชั้น **ข้อมูลหลัก** สร้างจากเอกสารด้วยสคริปต์ ห้ามแก้มือ ส่วน **ข้อมูลเพิ่มเติม** (overlay) แก้ผ่านหลังบ้าน และทับข้อมูลหลักตอนแสดงผล

```mermaid
flowchart TD
  src["เอกสารต้นฉบับ<br>PDF · RTF · TXT"]:::src --> scripts["สคริปต์<br>scripts/"]:::work
  scripts --> base["ข้อมูลหลัก<br>web/data/icd10 · icd9 · shared"]:::data
  admin["หลังบ้าน #admin"]:::work --> ov["ข้อมูลเพิ่มเติม<br>web/data/overlay.json"]:::data
  base --> push["push เข้า main"]:::work
  ov --> push
  push --> pages["เว็บบน GitHub Pages"]:::data
  pages -- "ผู้ใช้กดเสนอแก้ไข" --> sheet["Google Form → Sheet"]:::src
  sheet --> review["ผู้ดูแลตรวจ"]:::work
  review --> scripts
  review --> admin

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

---

## 2. ข้อมูล ICD-10

รหัสและชื่ออังกฤษยึด WHO 2016 ชื่อไทยและหมายเหตุสองภาษามาจาก ICD-10-TM 2009 สคริปต์อยู่ใน `scripts/who_icd10/` และ `scripts/tm_icd9_nhso/`

```mermaid
flowchart TD
  tm["ICD-10-TM 2009 PDF"]:::src --> tm1["extract_tm.py → parse_tm.py → build_icd10.py"]:::work
  who1["WHO 2016 เล่ม 1<br>บัญชีจำแนก"]:::src --> e1["extract_who.py tab → parse_who_tab.py"]:::work
  who3["WHO 2016 เล่ม 3<br>ดัชนี"]:::src --> e3["extract_who.py idx → parse_who_index.py"]:::work
  tm1 --> merged["build_merged.py<br>รวม WHO + ชื่อไทย TM<br>(th_new.py · thfix.py)"]:::work
  e1 --> merged
  e3 --> merged
  merged --> codes["icd10/codes.json"]:::data
  codes --> idx["build_who_index.py"]:::work
  e3 --> idx
  idx --> index["icd10/index/<br>icd10/keywords.json<br>icd10/tables.json"]:::data
  codes --> morph["parse_morph.py<br>(ICD-O จากเล่ม TM)"]:::work
  morph --> mj["icd10/morph.json"]:::data

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

ลำดับรัน: `build_merged.py` ก่อน แล้วจึง `build_who_index.py` และ `parse_morph.py` (สองตัวหลังอ่าน `codes.json`)

---

## 3. ข้อมูล ICD-9-CM

รายการรหัสมาจาก OCR ของเล่ม FY15 แล้วตรวจกับรายการทางการของ CMS ส่วนดัชนีสร้างจากไฟล์ทางการของ CDC ไม่ใช้ OCR สคริปต์อยู่ใน `scripts/tm_icd9_nhso/`

```mermaid
flowchart TD
  book["เล่ม ICD-9-CM FY15<br>ภาพสแกน S0034.pdf"]:::src --> ocr["ocr9.sh · ocr9b.sh<br>→ parse_icd9.py"]:::work
  ocr --> b9["build_icd9.py"]:::work
  b9 --> th["icd9_th.py<br>ใส่ชื่อไทยจาก icd9_th.tsv"]:::work
  th --> cms["icd9_cms_fix.py<br>ตรวจกับ CMS v32<br>แก้ชื่อ เพิ่ม/ลบรหัส"]:::work
  cmsref["ref/CMS32_DESC_LONG_SG.txt"]:::src --> cms
  cms --> codes["icd9/codes.json"]:::data

  pidx["ref/Pindex12.rtf<br>ดัชนีหัตถการ CDC"]:::src --> p12["parse_pindex12.py"]:::work
  p12 --> bidx["build_index9_cdc.py<br>แก้รหัสพิมพ์ผิด 4 จุด<br>เพิ่มรายการ FY2013–2015"]:::work
  codes --> bidx
  bidx --> index["icd9/index/<br>icd9/keywords.json"]:::data

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

- `build_icd9.py` เรียก `icd9_th.py` และ `icd9_cms_fix.py` ให้เอง รันคำสั่งเดียวพอ
- **แก้ชื่อไทย:** แก้ `icd9_th.tsv` แล้วรัน `build_icd9.py` ใหม่
- `build_index9_cdc.py` ต้องรันหลัง `codes.json` เสร็จ เพราะใช้ตรวจว่ารหัสในดัชนีมีจริง

---

## 4. คำย่อ

```mermaid
flowchart LR
  need["คำย่อใหม่<br>(ข้อเสนอ / แหล่งอ้างอิง)"]:::src --> edit["แก้ abbr.py<br>(คำย่อ, อังกฤษ, ไทย, รหัส, รหัสที่ขึ้นก่อน)"]:::work
  edit --> check["python3 abbr.py --check"]:::work
  check -- "มีคำเตือนใหม่" --> edit
  check -- "ผ่าน" --> run["python3 abbr.py"]:::work
  run --> out["shared/abbr.json"]:::data
  need -. "ทางลัด: ไม่ต้องแก้สคริปต์" .-> admin["หลังบ้าน #admin<br>ชนิด คำย่อ"]:::work
  admin -.-> ov["overlay.json"]:::data

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

- รหัสในคำย่อเขียนได้ 3 แบบ: `@E11` (รหัสนั้นและรหัสย่อย), `@A-B` (ช่วงรหัส), หรือข้อความที่ต้องตรงกับชื่อรหัส
- `--check` แจ้งรูปแบบที่ไม่เจอรหัสเลย คำเตือนเดิม 14 ข้อเป็นเรื่องปกติ ให้ดูเฉพาะข้อที่เพิ่มขึ้น
- คำย่อเดียวมีหลายความหมายได้ (เช่น BSO, ET) ใส่เป็นคนละแถว

---

## 5. หน้าแนวทาง

```mermaid
flowchart TD
  scg["แนวทางมาตรฐานการให้รหัสโรค<br>ฉบับปรับปรุง 2026 (PDF)"]:::src --> bs["scripts/scg/build_scg2026.py"]:::work
  bs --> sj["shared/scg2026.json"]:::data
  nhso["คู่มือเกณฑ์ตรวจสอบเวชระเบียน<br>สปสช. 2562"]:::src --> nt["nhso_topics.py"]:::work
  nt --> nj["shared/nhso2562.json"]:::data
  summ["scripts/guide/summ.py<br>กล่องสรุปการให้รหัส"]:::work --> bg["scripts/guide/build_guide.py"]:::work
  sj --> bg
  nj --> bg
  bg --> gj["shared/guide.json"]:::data

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

**แก้กล่องสรุป:** แก้ `summ.py` แล้วรัน `ICD_DATA=web/data python3 scripts/guide/build_guide.py`

---

## 6. ข้อเสนอจากผู้ใช้

```mermaid
flowchart TD
  btn["ผู้ใช้กดเสนอแก้ไขในเว็บ<br>ระบบ · รหัส · คำย่อ · ความหมาย"]:::src --> sheet["Google Form → Google Sheet"]:::src
  sheet --> rv{"คัดกรอง<br>มีแล้วไหม · รหัสถูกไหม"}:::work
  rv -- "มีอยู่แล้ว / ไม่ถูก" --> close["ปิดในชีต"]:::work
  rv -- "ข้อมูลไม่พอ" --> ask["ถามผู้เสนอหรือ coder"]:::work
  ask --> rv
  rv -- "คำย่อ / คำค้น" --> abbr["แก้ abbr.py<br>(ดูข้อ 4)"]:::work
  rv -- "หมายเหตุ / แก้ชื่อรหัส" --> admin["หลังบ้าน #admin<br>(ดูข้อ 7)"]:::work
  rv -- "ข้อมูลหลักผิด" --> fix["แก้สคริปต์ที่สร้างข้อมูล<br>(ดูข้อ 2–3)"]:::work
  abbr --> pub["เผยแพร่ (ดูข้อ 8)"]:::data
  admin --> pub
  fix --> pub
  pub --> close

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

ปุ่มเสนอแก้ไขอยู่ที่หน้ารายละเอียดรหัส ("เสนอแก้ไขรหัสนี้"), ตอนค้นไม่เจอ ("เสนอเพิ่มคำย่อ") และท้ายหน้า ที่อยู่ฟอร์มตั้งใน `web/data/shared/feedback.json` สร้างฟอร์มใหม่ได้ด้วย `scripts/feedback/create-form.gs`

---

## 7. หลังบ้าน (#admin)

หลังบ้านมี 2 โหมด ขึ้นกับว่าเปิดจากที่ไหน ทั้งสองโหมดจบที่ไฟล์ `web/data/overlay.json` ใน repo

```mermaid
flowchart TD
  subgraph local["โหมดในเครื่อง"]
    l1["เปิด localhost:8000/#admin"]:::work --> l2["เพิ่ม / แก้ / ลบ แล้วกดบันทึก"]:::work
    l2 --> l3["เขียนลง web/data/overlay.json ทันที"]:::data
  end
  subgraph online["โหมดออนไลน์ (claude.ai artifact)"]
    o1["เปิด artifact แล้วไป #admin<br>(ต้องเป็นเจ้าของหรือ Editor)"]:::work --> o2["เพิ่ม / แก้ / ลบ"]:::work
    o2 --> o3["ฐานข้อมูลของ artifact<br>collection overlay<br>เห็นผลใน artifact ทันที"]:::data
    o3 --> o4["แท็บ นำเข้า / ส่งออก → ส่งออก"]:::work
    o4 --> o5a["อัปโหลดทับใน GitHub<br>(ลิงก์อยู่ในหน้า)"]:::work
    o4 --> o5b["หรือ python3 scripts/sync_overlay.py ไฟล์"]:::work
  end
  l3 --> commit["commit + push"]:::work
  o5a --> ovf["web/data/overlay.json"]:::data
  o5b --> ovf
  ovf --> commit
  commit --> pub["เผยแพร่ (ดูข้อ 8)"]:::data

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

ตอนแสดงผล หน้าเว็บรวมข้อมูลตามลำดับนี้ ชั้นหลังทับชั้นหน้าเมื่อ id ตรงกัน:

```mermaid
flowchart LR
  a["ข้อมูลหลัก"]:::data --> b["overlay.json"]:::data --> c["ฐานข้อมูล artifact<br>(เฉพาะโหมดออนไลน์)"]:::data --> d["สิ่งที่ผู้ใช้เห็น"]:::src

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

- ลบรายการใน overlay เมื่อไร ก็กลับไปเป็นข้อมูลหลัก
- ปุ่มลบต้องกด 2 ครั้งภายใน 4 วินาที
- รูปแบบข้อมูลแต่ละชนิดดูใน [`backend.md`](backend.md)

---

## 8. เผยแพร่

```mermaid
flowchart TD
  change["แก้เสร็จ<br>ผลจากสคริปต์อยู่ใน web/data"]:::work --> test["เปิดในเครื่องลองค้น<br>python -m http.server ใน web/"]:::work
  test --> guard{"python3 scripts/check_data.py<br>ข้อมูลถูกต้อง และไม่มีไฟล์ที่ห้ามเผยแพร่"}:::work
  guard -- "ผ่าน" --> push["commit + push เข้า main<br>(hook pre-push ตรวจไฟล์ต้องห้ามซ้ำ)"]:::work
  guard -- "ไม่ผ่าน" --> change
  push --> act["GitHub Actions<br>ตรวจข้อมูลอีกรอบ แล้วจึง deploy<br>(.github/workflows/pages.yml)"]:::work
  act -- "ตรวจไม่ผ่าน: เว็บไม่เปลี่ยน" --> change
  act --> pages["GitHub Pages อัปเดต<br>ราว 1 นาที"]:::data
  push --> art["อัปเดต artifact หลังบ้านออนไลน์<br>ให้ตรงกับ web/"]:::work

  classDef src fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
  classDef work fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
```

- ถ้าแก้แค่ `scripts/` หรือ `docs/` เว็บจะไม่ deploy ใหม่ เพราะหน้าเว็บไม่เปลี่ยน แต่ `check.yml` ยังตรวจข้อมูลทุกครั้งที่ push
- เปิด hook ตรวจก่อน push ครั้งเดียวต่อเครื่อง: `git config core.hooksPath scripts/hooks`
- **ห้ามขึ้น GitHub:** ไฟล์ PDF ต้นฉบับ และเอกสารที่ใช้ภายในโรงพยาบาลเท่านั้น
- วิธีเผยแพร่แบบอื่น (Netlify, Cloudflare Pages) ดูใน [`deploy.md`](deploy.md)
