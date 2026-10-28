"""Level-2 coding summaries, written from the book's own rules (เกณฑ์การให้รหัส). Each must be reviewed against the printed page.
Rows marked '⚠' differ from the printed text; the note says why."""
SUMS = {
 '2': {'ref': 'เกณฑ์การให้รหัส ข้อ 1–5', 'tables': [
   {'cap': 'เลือกวินิจฉัยหลักและวินิจฉัยร่วม', 'cols': ['สถานการณ์', 'วินิจฉัยหลัก', 'วินิจฉัยร่วม'], 'rows': [
     ['พบแหล่งติดเชื้อตามอวัยวะ เช่น acute pyelonephritis, acute cholecystitis', 'รหัสโรคตามอวัยวะ เช่น N10, K81.0', 'รหัส sepsis เช่น A41.9'],
     ['ไม่พบแหล่งติดเชื้อ แต่ hemoculture เพาะเชื้อขึ้น หรือเป็นการติดเชื้อไม่ระบุอวัยวะ เช่น scrub typhus', 'รหัสตามเชื้อ เช่น A40.-, A41.-', '—'],
     ['ไม่พบแหล่งติดเชื้อ และไม่พบเชื้อ แต่มีอาการของ sepsis', 'A49.9 bacterial infection หรือ B99 infectious disease หรือ R50.9 fever', 'A41.9'],
     ['ไม่พบแหล่งติดเชื้อ และไม่พบเชื้อ แต่มี sepsis with septic shock', 'R57.2', 'A41.9'],
     ['มี septic shock ร่วมด้วย (กรณีอื่น)', 'ตามแถวข้างบน', 'เพิ่ม R57.2']]}],
   'notes': ['sepsis เป็นวินิจฉัยร่วมเสมอเมื่อหาแหล่งติดเชื้อได้ ห้ามขึ้นเป็นวินิจฉัยหลักแทนโรคของอวัยวะ',
             'เกณฑ์ qSOFA: ต้นฉบับพิมพ์ "> 2 ข้อ" ร่วมกับมีภาวะติดเชื้อ (เกณฑ์ qSOFA สากลใช้ ≥ 2 ข้อ)']},
 '24': {'ref': 'เกณฑ์การให้รหัส', 'tables': [
   {'cap': 'ใช้เฉพาะเมื่อแพทย์เขียนว่า hypertensive heart / renal disease เท่านั้น', 'cols': ['แพทย์วินิจฉัย', 'รหัส'], 'rows': [
     ['Hypertensive heart disease with heart failure', 'I11.0'],
     ['Hypertensive heart disease without heart failure', 'I11.9'],
     ['Hypertensive renal disease with renal failure', 'I12.0'],
     ['Hypertensive renal disease without renal failure', 'I12.9']]}],
   'notes': ['ต้นฉบับยกตัวอย่างเฉพาะ I11.0 และ I12.9 ส่วน I11.9 กับ I12.0 เติมตามหลักเดียวกัน (เลือกตามที่แพทย์ระบุว่ามี heart failure / renal failure หรือไม่)',
             'ถ้าแพทย์ไม่ได้ระบุว่าโรคหัวใจหรือไตเกิดจากความดันโลหิตสูง ห้ามใช้ I11.- / I12.- เอง']},
 '32': {'ref': 'เกณฑ์การวินิจฉัย ย่อหน้าท้าย และเกณฑ์การให้รหัส', 'tables': [
   {'cap': 'ลำดับการวินิจฉัย', 'cols': ['สถานการณ์', 'วินิจฉัยหลัก', 'วินิจฉัยร่วม'], 'rows': [
     ['มาด้วย heart failure ครั้งแรก (de novo)', 'สาเหตุโรคหัวใจที่ตรวจพบ', 'heart failure'],
     ['มาด้วย congestive heart failure ในผู้ป่วยที่รู้แล้วว่าเป็นโรคหัวใจชนิดใด', 'heart failure', 'โรคหัวใจเดิม'],
     ['เป็นโรคหัวใจอยู่เดิม แต่รับไว้ด้วยโรคอื่น', 'โรคที่รับไว้', 'โรคหัวใจเดิมได้ แต่ไม่ให้ heart failure ถ้าไม่มีอาการแล้ว']]},
   {'cap': 'รหัส heart failure', 'cols': ['แพทย์วินิจฉัย', 'รหัส'], 'rows': [
     ['Heart failure (ไม่ระบุชนิด)', 'I50.9'],
     ['Left ventricular failure ไม่ระบุรายละเอียด', 'I50.1'],
     ['Congestive heart failure, right ventricular failure หรือ biventricular failure', 'I50.0']]}],
   'notes': ['echocardiogram EF < 50% อย่างเดียวยังไม่พอวินิจฉัย heart failure ต้องมีอาการและอาการแสดงร่วมด้วย']},
 '37': {'ref': 'เกณฑ์การให้รหัส', 'tables': [
   {'cap': 'แพทย์ระบุเชื้อ', 'cols': ['เชื้อ', 'รหัส'], 'rows': [
     ['Streptococcus pneumoniae', 'J13'], ['Haemophilus influenzae', 'J14'], ['Klebsiella pneumoniae', 'J15.0'],
     ['Pseudomonas aeruginosa', 'J15.1'], ['Staphylococcus', 'J15.2'], ['Beta-haemolytic streptococcus', 'J15.4'],
     ['Escherichia coli', '⚠ J15.5 (ต้นฉบับพิมพ์ J15.0)'], ['Mycoplasma pneumoniae', 'J15.7'], ['Chlamydophila pneumoniae', 'J16.0'],
     ['แบคทีเรียอื่นที่ระบุชื่อ', '⚠ J15.8 (ต้นฉบับพิมพ์ J15.58)'], ['ย้อมกรัมพบแบคทีเรีย แต่เพาะเชื้อไม่ขึ้น', 'J15.9']]},
   {'cap': 'ไม่พบเชื้อ เพาะไม่ขึ้น หรือไม่ได้ตรวจ', 'cols': ['แพทย์วินิจฉัย', 'รหัส'], 'rows': [
     ['Aspiration pneumonia', 'J69.- ตามสิ่งที่สำลัก เช่น J69.0 อาหารหรืออาเจียน'],
     ['Lobar pneumonia (ภาพรังสีพบ lobar consolidation)', 'J18.1'],
     ['Bronchopneumonia (infiltration แบบ patchy / กระจาย)', 'J18.0'],
     ['Pneumonia ไม่ระบุรายละเอียด', '⚠ J18.9 (ต้นฉบับพิมพ์ CA40.Z ซึ่งเป็นรหัส ICD-11)']]},
   {'cap': 'แหล่งที่ติดเชื้อ', 'cols': ['แพทย์วินิจฉัย', 'รหัสเพิ่ม'], 'rows': [
     ['Community-acquired / health care-associated pneumonia', 'ให้รหัสตามตารางข้างบน ไม่ต้องเพิ่ม'],
     ['Hospital-acquired หรือ ventilator associated pneumonia', 'ตามตารางข้างบน + Y95 nosocomial condition']]}],
   'notes': ['ช่องสีเหลืองคือรหัสที่ต้นฉบับพิมพ์ไม่ตรงกับ ICD-10 ของ WHO ในสรุปนี้ใช้รหัสตามบัญชีจำแนก ควรยืนยันกับทีมก่อนใช้จริง']},
}

D2 = ['แพทย์วินิจฉัย', 'รหัส']
D3 = ['สถานการณ์', 'วินิจฉัยหลัก', 'วินิจฉัยร่วม']
def T(cap, cols, rows): return {'cap': cap, 'cols': cols, 'rows': rows}
SUMS.update({
 '3': {'ref': 'ย่อหน้าการเลือกวินิจฉัย', 'tables': [T('ลำดับการวินิจฉัย (ICD-10)', D3, [
     ['รับไว้ด้วยภาวะติดเชื้อ มะเร็ง หรือภาวะอื่นในผู้ป่วย HIV', 'รหัส HIV ที่ associate กับภาวะนั้น (B20–B23)', 'รหัสภาวะติดเชื้อ มะเร็ง หรือภาวะอื่น'],
     ['ระยะต้น: acute HIV infection syndrome', 'B23.0', '—'],
     ['Asymptomatic HIV / HIV disease ไม่ระบุ', 'B24', '—'],
     ['HIV resulting in generalized lymphadenopathy', 'B23.1', '—']])],
   'notes': ['แพทย์ยังวินิจฉัยแบบเดิม (ภาวะที่นำเข้าโรงพยาบาลเป็นหลัก) แต่ตอนลงรหัส ICD-10 ให้รหัส HIV ที่ associate กับภาวะนั้นขึ้นก่อน',
             'ใน ICD-11 กลับกัน: ภาวะติดเชื้อ/มะเร็งเป็นหลัก ตามด้วย HIV stage เป็นวินิจฉัยร่วม']},
 '4': {'ref': 'คำถาม-คำตอบ', 'tables': [T('Cirrhosis / hepatoma จาก viral hepatitis', D3, [
     ['Cirrhosis หรือ hepatoma ที่เกิดจาก viral hepatitis และยังรักษา viral hepatitis', 'cirrhosis / hepatoma', 'viral hepatitis (B15–B19) ให้ได้']])],
   'notes': ['ไม่มีเกณฑ์ของ WHO ที่ว่า "ไม่ได้รักษาแล้วห้ามลงรหัส" viral hepatitis เข้าเกณฑ์โรคร่วม']},
 '5': {'ref': 'หลักเกณฑ์ข้อ 1–8', 'tables': [T('มะเร็งปฐมภูมิ / ทุติยภูมิ', D3, [
     ['รับไว้รักษามะเร็งปฐมภูมิ', 'มะเร็งปฐมภูมิ', 'มะเร็งทุติยภูมิ'],
     ['รับไว้รักษามะเร็งทุติยภูมิ (เช่น brain, liver, bone metastasis)', 'มะเร็งทุติยภูมิ C77–C79', 'มะเร็งปฐมภูมิ หรือถ้าไม่ทราบ primary site unknown'],
     ['มีมะเร็งปฐมภูมิหลายแห่ง', 'ตัวที่นำเข้าโรงพยาบาล หรือรุนแรงกว่า (แพทย์ตัดสิน)', 'มะเร็งที่เหลือ'],
     ['ผ่าตัดมะเร็งปฐมภูมิออกแล้ว ไม่แพร่กระจาย แต่ยังให้เคมีบำบัด / ฉายแสงต่อ', 'มะเร็งปฐมภูมินั้น จนกว่าจะรักษาครบ', '—'],
     ['มีทั้งปฐมภูมิและทุติยภูมิตั้งแต่แรก รับไว้ให้เคมีบำบัดต่อเนื่อง', 'มะเร็งปฐมภูมิ (แม้ตัดออกไปแล้ว)', 'มะเร็งทุติยภูมิ'],
     ['ตรวจติดตามหลังรักษาหาย ไม่พบการกลับเป็น', 'Follow-up examination (Z08.-)', 'Personal history of malignant neoplasm (Z85.-)'],
     ['รักษามะเร็งปฐมภูมิหายแล้ว ครั้งนี้มาด้วยมะเร็งทุติยภูมิใหม่', 'มะเร็งทุติยภูมิ', 'Personal history ของมะเร็งปฐมภูมิ (Z85.-)']])],
   'notes': ['มะเร็งทุติยภูมิที่ตัดออกหมดแล้วและไม่กลับเป็น ไม่ต้องวินิจฉัยตำแหน่งนั้นอีก', 'รหัส Z08.- และ Z85.- เติมจากบัญชีจำแนก ต้นฉบับเขียนเป็นชื่อภาษาอังกฤษ']},
 '6-7': {'ref': 'ภาพรวม', 'tables': [T('ก้อนในตับ', ['หลักฐาน', 'รหัส'], [
     ['ภาพรังสีเข้าได้กับ HCC (arterial enhancement + rapid washout) และมี cirrhosis เดิม หรือผลชิ้นเนื้อยืนยัน', 'C22.0'],
     ['Intrahepatic cholangiocarcinoma ที่มีผลพยาธิวิทยายืนยัน', 'C22.1'],
     ['ไม่มีลักษณะเฉพาะทางรังสี ไม่ได้ biopsy แต่มีหลักฐานอื่นว่าเป็นมะเร็ง (เช่น metastasis, invasion)', 'C22.9'],
     ['ไม่มีหลักฐานว่าเป็นมะเร็ง แต่แพทย์แน่ใจว่าเป็นเนื้องอก', 'D37.6'],
     ['แพทย์ยังไม่แน่ใจว่าเป็นเนื้องอก (อาจเป็น granuloma, fibrosis, infection)', 'R93.2']])],
   'notes': ['ไม่ใช้ alpha fetoprotein เป็นเกณฑ์วินิจฉัยแล้ว', 'cholangiocarcinoma วินิจฉัยจากภาพรังสีอย่างเดียวไม่ได้']},
 '10': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('เสียเลือดเฉียบพลัน', D3, [
     ['เสียเลือดเฉียบพลัน เลือดจางจนมีอาการและต้องให้เลือด', 'โรคที่ทำให้เลือดออก เช่น acute haemorrhagic gastritis', 'D62']])],
   'notes': ['ถ้าไม่ได้ซีดมากจนต้องให้เลือด ไม่ต้องวินิจฉัย D62']},
 '11': {'ref': 'เกณฑ์การพิจารณาเป็นโรคร่วม', 'tables': [T('ซีดในโรคเรื้อรัง ให้เป็นโรคร่วมเมื่อ', ['ภาวะ', 'เงื่อนไข'], [
     ['Anaemia in neoplastic disease (D63.0*)', 'หาสาเหตุอื่นไม่พบ และซีดรุนแรงจนต้องให้เลือดหรือตรวจเพิ่มเพื่อแยกโรค'],
     ['Anaemia in chronic infectious disease', 'ซีดรุนแรงจนต้องให้เลือด หรือตรวจทางห้องปฏิบัติการเพิ่ม'],
     ['Anaemia in chronic kidney disease (D63.8*)', 'CKD stage 3 ขึ้นไป และผู้ป่วยในต้องให้เลือดหรือ erythropoietin'],
     ['ซีดในโรคเรื้อรังอื่น (ตับแข็ง, hypothyroidism ฯลฯ)', 'ต้องให้เลือด หรือตรวจเพิ่มเพื่อแยกโรค']])], 'notes': []},
 '12': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('ซีดจากโรคเฉียบพลัน', D2, [
     ['Anaemia due to acute disease (critical illness, ติดเชื้อเฉียบพลัน, trauma) หลังตัด hemolysis / bleeding / ขาดเหล็กแล้ว', 'D64.8']])],
   'notes': ['วินิจฉัยเมื่อซีดมากจนต้องให้เลือด หรือมีการตรวจทางห้องปฏิบัติการเพื่อวินิจฉัยเท่านั้น']},
 '13': {'ref': 'เกณฑ์การสรุปและให้รหัส', 'tables': [T('Pancytopenia ให้ 3 รหัส', ['ส่วนประกอบ', 'รหัส'], [
     ['Anaemia (Hb < 12 กรัม% หญิง, < 13 กรัม% ชาย)', 'D64.9'], ['Agranulocytosis (ANC < 1000)', 'D70'], ['Thrombocytopenia (เกล็ดเลือด < 100,000)', 'D69.6']])],
   'notes': ['ถ้า pancytopenia เกิดจาก aplastic anaemia หรือ myelodysplastic syndrome ไม่ต้องให้รหัส pancytopenia เพิ่ม',
             'แม้รักษาแค่ให้เลือด ก็ให้ D70 และ D69.6 ได้ เพราะเพิ่มความเสี่ยงติดเชื้อและเลือดออก']},
 '14': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('DIC', ['หลักฐาน', 'รหัส'], [
     ['ISTH score > 5 (overt DIC)', 'DIC (D65)'],
     ['ไม่ถึงเกณฑ์ overt DIC หรือไม่ได้ตรวจ D-dimer / fibrinogen', 'D69.5 + D68.4']])],
   'notes': ['รหัส D65 เติมจากบัญชีจำแนก ต้นฉบับไม่ได้พิมพ์รหัสของ overt DIC']},
 '15': {'ref': 'ภาพรวม', 'tables': [
   T('แผลที่เท้าในเบาหวานชนิดที่ 2', ['สาเหตุ', 'รหัสหลัก', 'รหัสร่วม'], [
     ['Diabetic neuropathy', 'E11.4†', 'G63.2*'], ['Peripheral vascular disease / diabetic gangrene', 'E11.5†', 'I79.2*'],
     ['ทั้ง neuropathy และ PVD', 'E11.7†', 'G63.2* + I79.2*'], ['Charcot joint (neuropathic arthropathy)', 'E11.6†', 'M14.6*']]),
   T('ลำดับการวินิจฉัย', D3, [
     ['มาด้วยการติดเชื้อ เช่น cellulitis, abscess, osteomyelitis, necrotizing fasciitis', 'การติดเชื้อ', 'เบาหวานที่มีภาวะแทรกซ้อน'],
     ['มีแผล (ulcer) เฉย ๆ มา admit ทำแผล', 'เบาหวาน + ภาวะแทรกซ้อน neuropathy / PVD', '—'],
     ['Acute complication ร่วมกับ chronic เช่น hyperglycaemic coma ในผู้ป่วยที่มี nephropathy', 'acute complication เช่น E11.0', 'chronic complication เช่น E11.2† N08.3*']])], 'notes': []},
 '16': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('ระดับทุพโภชนาการตาม BMI', ['BMI', 'ระดับ'], [
     ['17–18.49', 'ระดับ 1 mild'], ['16.00–16.99', 'ระดับ 2 moderate'], ['< 16.00', 'ระดับ 3 severe']])],
   'notes': ['ผู้ป่วยใน: ให้เป็นโรคร่วมตั้งแต่ moderate ขึ้นไป (รวม marasmus, kwashiorkor) และต้องมีการรักษา เช่น อาหารโปรตีนสูง enteral หรือ parenteral nutrition']},
 '19': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('Obesity ในผู้ป่วยใน', D2, [
     ['Obesity class III', 'E66.8'], ['Obesity class II ที่มีโรคร่วมจากอ้วน (เบาหวาน, sleep apnea, HT, fatty liver ฯลฯ)', 'E66.9'],
     ['Extreme obesity with alveolar hypoventilation', 'E66.2']])], 'notes': ['class I หรือ class II ที่ไม่มีโรคร่วมจากอ้วน ไม่ต้องวินิจฉัยในผู้ป่วยใน']},
 '20': {'ref': 'ภาพรวม', 'tables': [T('เมื่อไรต้องวินิจฉัย electrolyte imbalance', ['สถานการณ์', 'ให้รหัสเมื่อ'], [
     ['Acute diarrhoea', 'severe เท่านั้น: Na < 120, K < 2.5 mEq/L, Mg < 0.5 mmol/L'],
     ['Hyperkalaemia ใน CKD stage 4–5 หรือ AKI', 'ต้องรักษาเร่งด่วน เช่น ECG เปลี่ยน ให้ calcium, insulin หรือล้างไตฉุกเฉิน'],
     ['Volume overload ใน CKD stage 5', 'เป็นเหตุให้ admit หรือเกิดในโรงพยาบาลจนต้อง dialysis เพิ่ม / ให้ยาขับปัสสาวะทางหลอดเลือด']])], 'notes': []},
 '21': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('TIA', D2, [
     ['Vertebro-basilar artery syndrome / posterior circulation', 'G45.0'], ['Carotid artery syndrome / anterior circulation', 'G45.1'],
     ['Multiple or bilateral precerebral artery syndrome', 'G45.2'], ['Amaurosis fugax', 'G45.3'], ['Transient global amnesia', 'G45.4'],
     ['TIA ไม่ระบุรายละเอียด', 'G45.9'], ['เคยเป็น stroke มีอาการใหม่ชั่วคราว หายใน 24 ชม. CT/MRI ไม่เปลี่ยน', 'G45.9']])], 'notes': []},
 '22': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('ตำแหน่ง cerebral infarction (ใช้คู่กับ I63.-)', ['กลุ่มอาการ', 'รหัส'], [
     ['Middle cerebral artery syndrome', 'G46.0'], ['Anterior cerebral artery syndrome', 'G46.1'], ['Posterior cerebral artery syndrome', 'G46.2'],
     ['Brain stem stroke syndrome', 'G46.3'], ['Cerebellar stroke syndrome', 'G46.4'], ['Pure motor lacunar', 'G46.5'], ['Pure sensory lacunar', 'G46.6'],
     ['Ataxic hemiparesis, dysarthria-clumsy hand, lacunar อื่น', 'G46.7']])], 'notes': ['ไม่ต้องทำ cerebral angiogram ใช้อาการร่วมกับ CT / MRI ได้ ถ้า CT ยังปกติในระยะแรกวินิจฉัยจากอาการได้']},
 '25': {'ref': 'เกณฑ์การให้รหัส (ทุกหัวข้อย่อย)', 'tables': [T('Acute coronary syndrome', D2, [
     ['Unstable angina', 'I20.0'], ['Stable angina', 'I20.8'], ['Angina pectoris ไม่ระบุ', 'I20.9'],
     ['STEMI', 'I21.0–I21.3 ตามตำแหน่ง'], ['NSTEMI', 'I21.4'], ['Acute MI ไม่ระบุ', 'I21.9'],
     ['Subsequent MI (เกิดใหม่ภายใน 28 วัน)', 'I22.-'], ['Coronary thrombosis not resulting in MI', 'I24.0'], ['Acute ischaemic heart disease ไม่ระบุ', 'I24.9']])],
   'notes': ['วินิจฉัย acute MI ได้ถึง 4 สัปดาห์ (28 วัน) นับจากวันเริ่มเกิด']},
 '26': {'ref': 'ภาพรวม', 'tables': [T('Chronic ischaemic heart disease', D2, [
     ['Atherosclerotic heart disease (stenosis > 70% หรือ left main > 50%)', 'I25.1'], ['Old MI ปัจจุบันไม่มีอาการ', 'I25.2'],
     ['Ischaemic cardiomyopathy (LVEF < 40% + เกณฑ์เพิ่ม 1 ข้อ)', 'I25.5']])], 'notes': ['ischaemic cardiomyopathy ที่มีอาการ CHF ให้ heart failure เป็นโรคร่วมได้']},
 '27': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Pulmonary thromboembolism', D2, [['Acute pulmonary thromboembolism', 'I26.0'], ['Chronic pulmonary thromboembolism', 'I26.9']])],
   'notes': ['ใน ICD-10 I26.0 / I26.9 แยกตามมี acute cor pulmonale หรือไม่ ไม่ได้แยก acute / chronic ต้นฉบับจับคู่ไว้แบบนี้ ควรยืนยันกับทีม']},
 '28': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Pulmonary hypertension', D2, [
     ['Pulmonary arterial / primary / idiopathic PAH', 'I27.0'], ['PH due to left heart disease', 'I27.2'], ['PH due to lung disease or hypoxia', 'I27.9'],
     ['Chronic thromboembolic PH', 'I27.8'], ['⚠ PH with multifactorial mechanism', '⚠ ต้นฉบับให้เฉพาะ BB01.4 (ICD-11) ไม่มีรหัส ICD-10'], ['Cor pulmonale', 'I27.9']])], 'notes': []},
 '29': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Cardiomyopathy', D2, [
     ['Dilated cardiomyopathy', 'I42.0'], ['Obstructive hypertrophic', 'I42.1'], ['Non-obstructive hypertrophic', 'I42.2'], ['Endocardial fibroelastosis', 'I42.4'],
     ['Restrictive ไม่ระบุ', 'I42.5'], ['⚠ Non-familial restrictive', '⚠ ต้นฉบับให้เฉพาะ BC43.20 (ICD-11)'], ['จากยาหรือสารภายนอก', 'I42.7'],
     ['Stress-induced (takotsubo), arrhythmogenic, non-compaction', 'I42.8']])], 'notes': []},
 '30': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Cardiac arrest', D3, [
     ['ทราบสาเหตุ และ resuscitation สำเร็จ', 'สาเหตุ เช่น I49.0 VF, I44.2 complete AV block, I21.- MI, I47–I49', 'I46.0'],
     ['ไม่ทราบสาเหตุ รับไว้ดูแลหลัง arrest', 'I46.0', 'โรคแทรกหลัง arrest เช่น G93.1 anoxic brain damage'],
     ['Sudden cardiac death', 'I46.1', '—'], ['เกิด arrest ในโรงพยาบาลและ resuscitation ไม่สำเร็จ', 'ไม่ต้องลงรหัส cardiac arrest', '—']])], 'notes': []},
 '31': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('AF / flutter', D2, [
     ['Paroxysmal AF', 'I48.0'], ['Persistent AF', 'I48.1'], ['Permanent AF', 'I48.2'], ['Typical atrial flutter', 'I48.3'], ['Atypical atrial flutter', 'I48.4']])], 'notes': []},
 '33': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Stroke', D2, [
     ['Subarachnoid haemorrhage', 'I60.-'], ['Intracerebral haemorrhage', 'I61.-'], ['Nontraumatic intracranial haemorrhage อื่น', 'I62.-'],
     ['Cerebral infarction (ระบุ embolism/thrombosis, cerebral/precerebral)', 'I63.- ละเอียด + G46.-* ระบุหลอดเลือด'], ['Acute ischaemic stroke', 'I63.9'],
     ['Stroke ไม่ระบุว่า haemorrhage หรือ infarction', 'I64 (หลีกเลี่ยง สืบหาคำวินิจฉัยก่อน)']])],
   'notes': ['I63 ครอบคลุมราว 10 วันแรก', 'infarction เกิน 10 วันแต่ไม่ถึง 1 เดือน ยังมี neurodeficit และ admit ด้วยเหตุใดก็ตาม ยังวินิจฉัยเป็น acute infarction (ยังไม่ถึงเกณฑ์ sequelae)']},
 '34': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Old CVA (1 เดือนขึ้นไป)', D3, [
     ['ยังมีความผิดปกติทางระบบประสาทหลงเหลือ เช่น hemiparesis, aphasia', 'รหัสของความผิดปกติที่เหลือ', 'I69.-'],
     ['หายสนิท ไม่มีความผิดปกติเหลือ', 'Z86.7', '—']])], 'notes': []},
 '35': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Venous thrombosis', D3, [
     ['DVT ที่ขา', 'I80.2', '—'], ['เกิดจากมะเร็ง', 'มะเร็ง', 'I80.2'],
     ['จาก hypercoagulable state (protein C / S deficiency)', 'I80.2', 'D68.5'], ['จาก antiphospholipid / anticardiolipin syndrome', 'I80.2', 'D68.6'],
     ['Phlebitis จากให้น้ำเกลือ (บวม เจ็บ ต้องประคบ)', 'T80.1', 'Y62.1'], ['Phlebitis ที่มีการติดเชื้อ ต้องให้ยาปฏิชีวนะ', 'T80.2', 'ต้นฉบับไม่ได้ระบุ']])], 'notes': []},
 '36': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('Influenza', D2, [
     ['Avian / zoonotic influenza', 'J09'], ['Seasonal influenza ยืนยันเชื้อ + pneumonia', 'J10.0'], ['Seasonal ยืนยันเชื้อ อาการทางเดินหายใจส่วนบน', 'J10.1'],
     ['Seasonal ยืนยันเชื้อ อาการอื่น (สมองอักเสบ, ท้องเดิน, หัวใจอักเสบ)', 'J10.8'], ['Influenza ไม่ได้ยืนยันเชื้อ ไม่พบสาเหตุอื่น', 'J11.-']])], 'notes': []},
 '38': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('COPD', D2, [
     ['COPD with acute exacerbation', 'J44.1'], ['COPD with acute lower respiratory infection', 'J44.0 + รหัสการติดเชื้อ เช่น pneumonia'], ['COPD อย่างเดียว', 'J44.9']])],
   'notes': ['ต้องมี pulmonary function test จึงวินิจฉัย COPD ได้', 'ถ้าวินิจฉัยแค่ COPD ในผู้ป่วยใน ควรมีข้อบ่งชี้การ admit เช่น chronic respiratory failure หรือรับไว้ตรวจวินิจฉัย']},
 '39': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Asthma', D2, [
     ['Allergic asthma', 'J45.0'], ['Non-allergic asthma', 'J45.1'], ['Acute asthmatic attack', 'J45.9'], ['Asthmatic bronchitis / late onset asthma', 'J45.9'],
     ['Status asthmaticus', 'J46'], ['Bronchial hyperresponsiveness (ไม่ได้ทำ spirometry)', 'J45.2']])],
   'notes': ['ต้องตรวจ spirometry ยืนยัน ถ้าไม่ได้ทำ วินิจฉัยได้แค่ bronchial hyperresponsiveness', 'ต้นฉบับระบุว่า J45.2 ไม่มีใน ICD-10 WHO 2016 (เป็นรหัสที่เพิ่มในฉบับไทย)']},
 '40': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Pulmonary oedema', D2, [['Non-cardiogenic pulmonary oedema', 'J81'], ['Cardiogenic pulmonary oedema', 'I50.1']])], 'notes': []},
 '41': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Pleural effusion', D3, [
     ['ไม่ระบุสาเหตุ', 'J90', '—'], ['ระบุสาเหตุ เช่น CHF, cirrhosis, SLE', 'รหัสสาเหตุ', 'J91*'],
     ['จาก metastatic carcinoma', 'C78.2 (ไม่ต้องใช้ J91)', '—'], ['จากวัณโรค ยืนยันเชื้อ / ไม่ยืนยัน', 'A15.6 / A16.5', '—'],
     ['Minimal effusion ไม่ทราบสาเหตุ ไม่ได้ตรวจต่อ', 'ไม่ต้องลงรหัส', '—']])], 'notes': []},
 '42': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Respiratory failure', ['แพทย์วินิจฉัย', 'รหัสในต้นฉบับ', 'ICD-10 WHO'], [
     ['Acute type I / acute hypoxaemic', '⚠ J96.00', 'J96.0'], ['Acute type II / acute hypercapnic', '⚠ J96.01', 'J96.0'],
     ['Acute type III, IV หรือไม่ระบุ', '⚠ J96.09', 'J96.0'], ['Chronic type I / chronic hypoxaemic', '⚠ J96.10', 'J96.1'],
     ['Chronic type II / chronic hypercapnic', '⚠ J96.11', 'J96.1'], ['Chronic ไม่ระบุ', '⚠ J96.19', 'J96.1']])],
   'notes': ['รหัส 5 หลัก J96.00–J96.19 ไม่มีในบัญชี ICD-10 WHO ของเว็บนี้ (น่าจะเป็นรหัสขยายของ ICD-10-TM) ตรวจกับโปรแกรมที่โรงพยาบาลใช้',
             'แถว "acute type III/IV" ต้นฉบับพิมพ์ชื่อรหัสว่า Chronic respiratory failure, unspecified ซึ่งไม่ตรงกับแถว',
             'ตัดสินใจใส่ท่อช่วยหายใจตามอาการ วินิจฉัยได้แม้ O2 saturation ยังปกติ']},
 '43': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Gastritis', D2, [
     ['Acute haemorrhagic gastritis / acute gastritis with haemorrhage', 'K29.0'], ['Acute gastritis', 'K29.1'],
     ['Gastritis จาก H. pylori', 'รหัส gastritis + B98.0'], ['Portal hypertensive gastropathy', 'K29.6 + สาเหตุ เช่น K74.6, K76.6']])],
   'notes': ['ต้องทำ endoscopy จึงวินิจฉัย gastritis ได้ ถ้าไม่ได้ทำให้วินิจฉัย dyspepsia หรือ haematemesis / melaena',
             'สรุปทั้ง acute และ chronic ร่วมกันได้เมื่อมีผลพยาธิวิทยายืนยัน chronic และมีอาการ acute เช่น bleeding']},
 '45': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Appendicitis', D2, [
     ['Acute appendicitis with generalized peritonitis', 'K35.2'], ['Acute appendicitis with localized peritonitis', 'K35.3'],
     ['Acute appendicitis without peritonitis', 'K35.8'], ['Chronic appendicitis', 'K36']])], 'notes': []},
 '48': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('GI bleeding (ไม่ได้ส่องกล้อง)', D2, [
     ['Haematemesis (หรือมีทั้ง haematemesis และ melaena)', 'K92.0'], ['Melaena', 'K92.1'], ['Gastrointestinal bleeding ไม่ระบุ', 'K92.2'],
     ['Upper GI bleeding', 'K92.2'], ['Lower GI bleeding', '⚠ K92.2 (ต้นฉบับพิมพ์ K92.3 ซึ่งไม่มีใน ICD-10 WHO)'],
     ['เลือดออกหลายวัน ไม่ได้ส่องกล้อง มีภาวะซีด', 'รหัสภาวะซีดที่ตรวจพบ เช่น iron deficiency anaemia'], ['Stool occult blood บวก', 'R19.5']])],
   'notes': ['ถ้าส่องกล้อง ให้วินิจฉัยหลักตามผลส่องกล้อง เช่น acute haemorrhagic gastritis, gastric ulcer with haemorrhage, oesophageal varices with bleeding']},
 '49': {'ref': 'ภาพรวม', 'tables': [T('Cellulitis หรือแผลติดเชื้อ', D2, [
     ['Cellulitis เกิดเอง ไม่มีแผลนำมาก่อน', 'L03.-'], ['แผลจากการบาดเจ็บแล้วติดเชื้อ', 'T79.3 + สาเหตุภายนอก เช่น W54.- สุนัขกัด, W60.- หนามตำ, X98.- ถูกทำร้ายด้วยของมีคม']])], 'notes': []},
 '51': {'ref': 'เกณฑ์การให้รหัส', 'tables': [T('Acute kidney injury', D2, [
     ['AKI ตามชนิดที่แพทย์วินิจฉัย', 'N17.-'], ['Prerenal azotemia / prerenal failure / ARF (prerenal)', 'R39.2'], ['Postrenal failure', 'N17.8 + N13.- ตามการอุดกั้น'],
     ['ไม่มี Cr baseline แต่ Cr ลดลงชัดใน 1–3 วันหลังให้สารน้ำ', 'R39.2'],
     ['Congenital / drug-induced / HUS / hepatorenal / หลังแท้งหรือคลอด / postprocedural', 'ใช้รหัสของภาวะนั้น P96.0, N14.-, D59.3, K76.7, O08.4 หรือ O90.4, N99.0 (ไม่ใช้ N17)']])], 'notes': []},
 '52': {'ref': 'เกณฑ์การวินิจฉัย', 'tables': [T('CKD', ['Stage', 'การวินิจฉัย'], [
     ['Stage 1–3', 'วินิจฉัยเฉพาะชื่อโรคไต ไม่ต้องระบุ stage ถ้าไม่พบสาเหตุไม่ต้องวินิจฉัย'], ['Stage 4 (GFR 15–29)', 'ระบุ stage ทุกครั้งในผู้ป่วยใน: N18.4'], ['Stage 5 (GFR < 15)', 'ระบุ stage ทุกครั้งในผู้ป่วยใน: N18.5']])],
   'notes': ['รหัส N18.4 / N18.5 เติมจากบัญชีจำแนก ต้นฉบับระบุแค่ให้บอก stage']},
 '53': {'ref': 'ภาพรวม', 'tables': [T('Kidney failure ไม่ระบุ', D2, [['แยก acute กับ chronic ไม่ได้จริง ๆ เท่านั้น', 'N19']])], 'notes': ['ส่วนใหญ่แยกได้จาก urine flow, ซีด, BUN/Cr ratio, ขนาดไต']},
})
