"""Medical abbreviations used in Thai charts -> search expansions.

Writes /home/claude/icd-site/data/shared/abbr.json:
  {"icd10": {"dm": [meaning, ...], ...}, "icd9": {...}, "spell": [[us, uk], ...]}
  meaning = {"en": str, "th": str, "m": [alt, ...], "top": [code, ...]}
  alt: plain text  -> substring of the code's searchable text (titles + index terms)
       "@E10-E14"  -> any code in that category range
       "@I21"      -> the code and all its subdivisions
  top: codes ranked first, in order (the usual choice for that abbreviation)
Run with --check to print how many codes each meaning finds.
"""
import json, sys

# keys | English | Thai | alternatives | top codes
D10 = [
    # ---- endocrine / metabolic
    ('DM', 'Diabetes mellitus', 'เบาหวาน', ['diabetes mellitus', '@E10-E14'], ['E11.9', 'E14.9', 'E10.9']),
    ('T2DM|NIDDM|DM2|DMT2', 'Type 2 diabetes (non-insulin-dependent)', 'เบาหวานชนิดที่ 2', ['@E11'], ['E11.9']),
    ('T1DM|IDDM|DM1|DMT1', 'Type 1 diabetes (insulin-dependent)', 'เบาหวานชนิดที่ 1', ['@E10'], ['E10.9']),
    ('GDM', 'Gestational diabetes', 'เบาหวานขณะตั้งครรภ์', ['@O24.4'], ['O24.4']),
    ('DKA', 'Diabetic ketoacidosis', 'ภาวะเลือดเป็นกรดจากคีโตน', ['ketoacidosis'], ['E11.1', 'E10.1']),
    ('HHS|HONK|HHNK', 'Hyperosmolar hyperglycaemic state', 'น้ำตาลในเลือดสูงร่วมกับภาวะออสโมลาร์สูง', ['hyperosmolar', '@E11.0', '@E14.0'], ['E11.0']),
    ('DLP|HLP|HL', 'Dyslipidaemia / hyperlipidaemia', 'ไขมันในเลือดผิดปกติ', ['@E78'], ['E78.5', 'E78.0']),
    ('DFU|DM FOOT|DIABETIC FOOT|DM FOOT ULCER', 'Diabetic foot ulcer', 'แผลเบาหวานที่เท้า', ['@E10.5', '@E11.5', '@E14.5', 'diabetic foot'], ['E11.5']),
    ('DR', 'Diabetic retinopathy', 'เบาหวานขึ้นจอตา', ['diabetic retinopathy', '@H36.0', '@E10.3'], ['H36.0', 'E11.3']),
    ('DN', 'Diabetic nephropathy', 'โรคไตจากเบาหวาน', ['diabetic nephropathy', '@N08.3'], ['E11.2', 'N08.3']),
    ('HYPOK|HYPO K', 'Hypokalaemia', 'โพแทสเซียมในเลือดต่ำ', ['@E87.6'], ['E87.6']),
    ('HYPERK', 'Hyperkalaemia', 'โพแทสเซียมในเลือดสูง', ['@E87.5'], ['E87.5']),
    ('HYPONA', 'Hyponatraemia', 'โซเดียมในเลือดต่ำ', ['@E87.1'], ['E87.1']),
    ('HYPERNA', 'Hypernatraemia', 'โซเดียมในเลือดสูง', ['@E87.0'], ['E87.0']),
    ('HYPOMG', 'Hypomagnesaemia', 'แมกนีเซียมในเลือดต่ำ', ['hypomagnes'], ['E83.4']),
    ('HYPOGLY|HYPOGLYCEMIA', 'Hypoglycaemia', 'น้ำตาลในเลือดต่ำ', ['hypoglycaemia'], ['E16.2', 'E16.0']),
    # ---- cardiovascular
    ('HT|HTN', 'Hypertension', 'ความดันโลหิตสูง', ['hypertensi', '@I10-I15'], ['I10']),
    ('HHD', 'Hypertensive heart disease', 'โรคหัวใจจากความดันโลหิตสูง', ['@I11'], ['I11.9', 'I11.0']),
    ('MI|AMI', 'Acute myocardial infarction', 'กล้ามเนื้อหัวใจตายเฉียบพลัน', ['myocardial infarction', '@I21-I22'], ['I21.9']),
    ('STEMI', 'ST elevation myocardial infarction', 'กล้ามเนื้อหัวใจตายเฉียบพลันชนิด ST ยก', ['@I21.0', '@I21.1', '@I21.2', '@I21.3'], ['I21.3', 'I21.0', 'I21.1']),
    ('NSTEMI', 'Non-ST elevation myocardial infarction', 'กล้ามเนื้อหัวใจตายเฉียบพลันชนิด ST ไม่ยก', ['@I21.4'], ['I21.4']),
    ('ACS', 'Acute coronary syndrome', 'กลุ่มอาการหลอดเลือดหัวใจเฉียบพลัน', ['@I20.0', '@I21', '@I24'], ['I24.9', 'I20.0', 'I21.9']),
    ('UA|USA', 'Unstable angina', 'เจ็บหน้าอกแบบไม่คงที่', ['unstable angina'], ['I20.0']),
    ('SA', 'Stable angina', 'เจ็บหน้าอกแบบคงที่', ['@I20.8', '@I20.9'], ['I20.9']),
    ('CAD|IHD', 'Coronary artery / ischaemic heart disease', 'โรคหลอดเลือดหัวใจ', ['@I20-I25', 'coronary'], ['I25.1', 'I25.9']),
    ('CHF|HF', 'Heart failure', 'หัวใจล้มเหลว', ['heart failure', '@I50'], ['I50.0', 'I50.9']),
    ('AF|AFIB', 'Atrial fibrillation', 'หัวใจห้องบนเต้นแผ่นระรัว', ['atrial fibrillation', '@I48'], ['I48.9', 'I48.0', 'I48.1', 'I48.2']),
    ('AFL', 'Atrial flutter', 'หัวใจห้องบนเต้นสั่นพลิ้ว', ['atrial flutter', '@I48.3', '@I48.4'], ['I48.3', 'I48.4']),
    ('SVT|PSVT', 'Supraventricular tachycardia', 'หัวใจเต้นเร็วผิดจังหวะเหนือหัวใจห้องล่าง', ['supraventricular tachycardia'], ['I47.1']),
    ('VT', 'Ventricular tachycardia', 'หัวใจห้องล่างเต้นเร็ว', ['ventricular tachycardia'], ['I47.2']),
    ('VF', 'Ventricular fibrillation', 'หัวใจห้องล่างเต้นแผ่นระรัว', ['ventricular fibrillation'], ['I49.0']),
    ('CHB', 'Complete heart block', 'หัวใจห้องบนล่างนำไฟฟ้าถูกปิดกั้นสมบูรณ์', ['@I44.2'], ['I44.2']),
    ('CHB', 'Chronic hepatitis B', 'ไวรัสตับอักเสบบีเรื้อรัง', ['@B18.0', '@B18.1'], ['B18.1']),
    ('SSS', 'Sick sinus syndrome', 'กลุ่มอาการไซนัสโหนดเสื่อม', ['sick sinus'], ['I49.5']),
    ('RHD', 'Rheumatic heart disease', 'โรคหัวใจรูมาติก', ['@I05-I09'], ['I09.9']),
    ('MS', 'Mitral stenosis', 'ลิ้นหัวใจไมทรัลตีบ', ['mitral stenosis'], ['I05.0', 'I34.2']),
    ('MS', 'Multiple sclerosis', 'โรคปลอกประสาทเสื่อมแข็ง', ['multiple sclerosis'], ['G35']),
    ('MR', 'Mitral regurgitation', 'ลิ้นหัวใจไมทรัลรั่ว', ['mitral (valve) insufficiency', 'mitral insufficiency', 'mitral regurgitation'], ['I34.0', 'I05.1']),
    ('AS', 'Aortic stenosis', 'ลิ้นหัวใจเอออร์ติกตีบ', ['aortic (valve) stenosis', 'aortic stenosis'], ['I35.0', 'I06.0']),
    ('AS', 'Ankylosing spondylitis', 'โรคข้อกระดูกสันหลังอักเสบติดยึด', ['ankylosing spondylitis'], ['M45']),
    ('AR', 'Aortic regurgitation', 'ลิ้นหัวใจเอออร์ติกรั่ว', ['aortic (valve) insufficiency', 'aortic insufficiency', 'aortic regurgitation'], ['I35.1', 'I06.1']),
    ('TR', 'Tricuspid regurgitation', 'ลิ้นหัวใจไตรคัสปิดรั่ว', ['tricuspid insufficiency', 'tricuspid regurgitation', 'tricuspid (valve) insufficiency'], ['I36.1', 'I07.1']),
    ('VSD', 'Ventricular septal defect', 'ผนังกั้นหัวใจห้องล่างรั่ว', ['ventricular septal defect'], ['Q21.0']),
    ('ASD', 'Atrial septal defect', 'ผนังกั้นหัวใจห้องบนรั่ว', ['atrial septal defect'], ['Q21.1']),
    ('PDA', 'Patent ductus arteriosus', 'หลอดเลือดดักตัส อาร์เทอริโอซัส ไม่ปิด', ['patent ductus arteriosus'], ['Q25.0']),
    ('TOF', 'Tetralogy of Fallot', 'เตตราโลจีออฟฟาลโล', ['fallot'], ['Q21.3']),
    ('DVT', 'Deep vein thrombosis', 'หลอดเลือดดำส่วนลึกอุดตัน', ['deep vein', 'deep vessels', '@I80.2'], ['I80.2']),
    ('PE', 'Pulmonary embolism', 'ลิ่มเลือดอุดตันในปอด', ['pulmonary embolism', '@I26'], ['I26.9']),
    ('PE', 'Pleural effusion', 'น้ำในเยื่อหุ้มปอด', ['pleural effusion', '@J90', '@J91'], ['J90', 'J91']),
    ('PAD|PAOD|PVD', 'Peripheral arterial / vascular disease', 'โรคหลอดเลือดแดงส่วนปลาย', ['peripheral vascular', '@I70.2'], ['I73.9', 'I70.2']),
    ('AAA', 'Abdominal aortic aneurysm', 'หลอดเลือดแดงใหญ่ในช่องท้องโป่งพอง', ['@I71.3', '@I71.4'], ['I71.4']),
    ('PIH', 'Pregnancy-induced hypertension', 'ความดันโลหิตสูงจากการตั้งครรภ์', ['@O13', '@O14', '@O16'], ['O13', 'O14.9']),
    # ---- neuro
    ('CVA|STROKE', 'Stroke / cerebrovascular accident', 'โรคหลอดเลือดสมอง', ['@I60-I64', 'stroke'], ['I64', 'I63.9', 'I61.9']),
    ('CVD', 'Cerebrovascular disease', 'โรคหลอดเลือดสมอง', ['@I60-I69', 'cerebrovascular'], ['I67.9', 'I64']),
    ('ISCHEMIC STROKE|ISCHAEMIC STROKE', 'Ischaemic stroke (cerebral infarction)', 'สมองขาดเลือด', ['@I63'], ['I63.9']),
    ('TIA', 'Transient ischaemic attack', 'สมองขาดเลือดชั่วคราว', ['@G45'], ['G45.9']),
    ('ICH', 'Intracerebral haemorrhage', 'เลือดออกในเนื้อสมอง', ['intracerebral haemorrhage', '@I61'], ['I61.9', 'S06.3']),
    ('SAH', 'Subarachnoid haemorrhage', 'เลือดออกใต้เยื่อหุ้มสมองชั้นกลาง', ['subarachnoid haemorrhage'], ['I60.9', 'S06.6']),
    ('SDH', 'Subdural haemorrhage', 'เลือดออกใต้เยื่อหุ้มสมองชั้นนอก', ['subdural haemorrhage'], ['S06.5', 'I62.0']),
    ('EDH', 'Extradural (epidural) haemorrhage', 'เลือดออกเหนือเยื่อหุ้มสมองชั้นนอก', ['extradural haemorrhage', 'epidural haemorrhage'], ['S06.4']),
    ('TBI|HI', 'Head / traumatic brain injury', 'บาดเจ็บที่ศีรษะ', ['@S06', 'head injury', '@S09.9'], ['S06.0', 'S09.9']),
    ('GBS', 'Guillain-Barré syndrome', 'กลุ่มอาการกิลแลง-บาร์เร', ['guillain'], ['G61.0']),
    ('MG', 'Myasthenia gravis', 'โรคกล้ามเนื้ออ่อนแรงเหตุประสาทและกล้ามเนื้อ', ['myasthenia gravis'], ['G70.0']),
    ('PD', 'Parkinson disease', 'โรคพาร์กินสัน', ['parkinson'], ['G20']),
    ('ALS|MND', 'Motor neuron disease (ALS)', 'โรคเซลล์ประสาทสั่งการเสื่อม', ['motor neuron disease', 'amyotrophic'], ['G12.2']),
    ('SE', 'Status epilepticus', 'ภาวะชักต่อเนื่อง', ['status epilepticus', '@G41'], ['G41.9']),
    ('SZ|SEIZURE', 'Seizure / convulsion', 'ชัก', ['convulsion', 'seizure', 'epilep'], ['R56.8', 'G40.9']),
    ('FS|FC', 'Febrile convulsion', 'ชักจากไข้สูง', ['febrile convulsion'], ['R56.0']),
    ('CP', 'Cerebral palsy', 'สมองพิการ', ['cerebral palsy'], ['G80.9']),
    ('HA', 'Headache', 'ปวดศีรษะ', ['headache'], ['R51']),
    ('BPPV', 'Benign paroxysmal vertigo', 'บ้านหมุนจากตะกอนหินปูนในหูชั้นใน', ['benign paroxysmal vertigo'], ['H81.1']),
    ('DEMENTIA|AD', "Alzheimer disease / dementia", 'สมองเสื่อม', ['alzheimer', 'dementia'], ['G30.9', 'F03']),
    # ---- psychiatric
    ('MDD', 'Major depressive disorder', 'โรคซึมเศร้า', ['depressive episode', 'recurrent depressive', '@F32', '@F33'], ['F32.9', 'F32.2']),
    ('GAD', 'Generalized anxiety disorder', 'โรควิตกกังวลทั่วไป', ['generalized anxiety'], ['F41.1']),
    ('BD|BPAD', 'Bipolar affective disorder', 'โรคอารมณ์สองขั้ว', ['bipolar'], ['F31.9']),
    ('OCD', 'Obsessive-compulsive disorder', 'โรคย้ำคิดย้ำทำ', ['obsessive-compulsive'], ['F42.9']),
    ('PTSD', 'Post-traumatic stress disorder', 'โรคเครียดหลังเหตุการณ์สะเทือนขวัญ', ['post-traumatic stress'], ['F43.1']),
    ('ADHD', 'Attention-deficit hyperactivity disorder', 'โรคสมาธิสั้น', ['@F90'], ['F90.0']),
    ('SCHIZO|SCZ', 'Schizophrenia', 'โรคจิตเภท', ['schizophrenia', '@F20'], ['F20.9']),
    ('AWS', 'Alcohol withdrawal', 'ภาวะถอนพิษสุรา', ['@F10.3', '@F10.4'], ['F10.3', 'F10.4']),
    ('ETOH|ALC', 'Alcohol use', 'การดื่มสุรา', ['@F10', 'alcohol'], ['F10.2', 'F10.0']),
    # ---- respiratory
    ('URI|URTI', 'Upper respiratory infection', 'การติดเชื้อทางเดินหายใจส่วนบน', ['upper respiratory infection', '@J00-J06'], ['J06.9']),
    ('LRI|LRTI', 'Lower respiratory infection', 'การติดเชื้อทางเดินหายใจส่วนล่าง', ['lower respiratory infection', '@J22'], ['J22']),
    ('CAP|HAP|VAP|PNEUMO', 'Pneumonia', 'ปอดอักเสบ', ['pneumonia', '@J12-J18'], ['J18.9', 'J15.9']),
    ('COPD|COLD', 'Chronic obstructive pulmonary disease', 'โรคปอดอุดกั้นเรื้อรัง', ['chronic obstructive pulmonary', '@J44'], ['J44.9', 'J44.1']),
    ('AECOPD', 'COPD with acute exacerbation', 'ปอดอุดกั้นเรื้อรังกำเริบ', ['@J44.0', '@J44.1'], ['J44.1', 'J44.0']),
    ('BA', 'Bronchial asthma', 'โรคหืด', ['asthma', '@J45', '@J46'], ['J45.9', 'J46']),
    ('BA', 'Birth asphyxia', 'ทารกขาดออกซิเจนแรกคลอด', ['birth asphyxia', '@P21'], ['P21.9']),
    ('TB', 'Tuberculosis', 'วัณโรค', ['tuberculosis', '@A15-A19'], ['A16.2', 'A15.0']),
    ('PTB', 'Pulmonary tuberculosis', 'วัณโรคปอด', ['tuberculosis of lung', '@A15.0', '@A15.1', '@A15.2', '@A15.3', '@A16.0', '@A16.1', '@A16.2'], ['A16.2', 'A15.0']),
    ('ARDS', 'Acute respiratory distress syndrome', 'กลุ่มอาการหายใจลำบากเฉียบพลัน', ['@J80'], ['J80']),
    ('RDS', 'Respiratory distress syndrome of newborn', 'กลุ่มอาการหายใจลำบากในทารกแรกเกิด', ['@P22.0'], ['P22.0']),
    ('ARF|RF', 'Respiratory failure', 'การหายใจล้มเหลว', ['respiratory failure', '@J96'], ['J96.0', 'J96.9']),
    ('ARF', 'Acute renal failure', 'ไตวายเฉียบพลัน', ['acute renal failure', '@N17'], ['N17.9']),
    ('OSA', 'Obstructive sleep apnoea', 'ภาวะหยุดหายใจขณะหลับจากการอุดกั้น', ['sleep apnoea'], ['G47.3']),
    ('ILD', 'Interstitial lung disease', 'โรคปอดเนื้อพังผืด', ['interstitial pulmonary', '@J84'], ['J84.9']),
    ('PTX', 'Pneumothorax', 'ลมรั่วในช่องเยื่อหุ้มปอด', ['pneumothorax'], ['J93.9', 'S27.0']),
    ('HTX', 'Haemothorax', 'เลือดออกในช่องเยื่อหุ้มปอด', ['haemothorax'], ['S27.1', 'J94.2']),
    ('AR|ALLERGIC RHINITIS', 'Allergic rhinitis', 'โรคจมูกอักเสบจากภูมิแพ้', ['allergic rhinitis', '@J30'], ['J30.4']),
    # ---- renal / urology
    ('CKD|CRF', 'Chronic kidney disease', 'โรคไตเรื้อรัง', ['@N18', 'chronic renal', 'chronic kidney'], ['N18.9', 'N18.5', 'N18.4', 'N18.3']),
    ('ESRD|ESKD', 'End-stage renal disease', 'โรคไตระยะสุดท้าย', ['@N18.5', 'end-stage renal'], ['N18.5']),
    ('AKI', 'Acute kidney injury', 'ไตบาดเจ็บเฉียบพลัน', ['acute renal failure', '@N17'], ['N17.9']),
    ('UTI', 'Urinary tract infection', 'การติดเชื้อในทางเดินปัสสาวะ', ['urinary tract infection', '@N39.0', '@N30', '@N10'], ['N39.0']),
    ('BPH', 'Benign prostatic hyperplasia', 'ต่อมลูกหมากโต', ['hyperplasia of prostate', '@N40'], ['N40']),
    ('NS', 'Nephrotic syndrome', 'กลุ่มอาการเนฟโฟรติก', ['nephrotic syndrome', '@N04'], ['N04.9']),
    ('AGN', 'Acute glomerulonephritis', 'ไตอักเสบเฉียบพลัน', ['acute nephritic', '@N00'], ['N00.9']),
    ('RC|KUB STONE|UROLITHIASIS', 'Urinary calculus', 'นิ่วในทางเดินปัสสาวะ', ['calculus of kidney', 'calculus of ureter', 'calculus', '@N20-N23'], ['N20.0', 'N20.1', 'N20.9']),
    ('ARU', 'Acute retention of urine', 'ปัสสาวะไม่ออกเฉียบพลัน', ['retention of urine'], ['R33']),
    # ---- GI / liver
    ('GERD|GORD', 'Gastro-oesophageal reflux disease', 'กรดไหลย้อน', ['@K21'], ['K21.9', 'K21.0']),
    ('UGIB|UGIH|GIB|LGIB|LGIH', 'Gastrointestinal bleeding', 'เลือดออกในทางเดินอาหาร', ['gastrointestinal haemorrhage', '@K92.0', '@K92.1', '@K92.2', 'with haemorrhage'], ['K92.2', 'K92.0', 'K92.1']),
    ('PUD', 'Peptic ulcer disease', 'แผลในกระเพาะอาหาร', ['@K25-K28'], ['K27.9', 'K25.9']),
    ('GU', 'Gastric ulcer', 'แผลในกระเพาะอาหาร', ['@K25'], ['K25.9']),
    ('DU', 'Duodenal ulcer', 'แผลในลำไส้เล็กส่วนต้น', ['@K26'], ['K26.9']),
    ('AGE', 'Acute gastroenteritis', 'ลำไส้อักเสบเฉียบพลัน', ['gastroenteritis', '@A09'], ['A09.9', 'A09.0']),
    ('AD|ADD', 'Acute diarrhoea', 'ท้องร่วงเฉียบพลัน', ['diarrhoea'], ['A09.9', 'K52.9']),
    ('IBS', 'Irritable bowel syndrome', 'ลำไส้แปรปรวน', ['irritable bowel'], ['K58.9']),
    ('IBD', 'Inflammatory bowel disease', 'ลำไส้อักเสบเรื้อรัง', ['@K50', '@K51'], ['K50.9', 'K51.9']),
    ('UC', 'Ulcerative colitis', 'ลำไส้ใหญ่อักเสบเป็นแผล', ['ulcerative colitis', '@K51'], ['K51.9']),
    ('AA|APPENDICITIS|ACUTE APPENDICITIS', 'Acute appendicitis', 'ไส้ติ่งอักเสบเฉียบพลัน', ['@K35'], ['K35.8', 'K35.3', 'K35.2']),
    ('RUPTURED APPENDIX', 'Ruptured appendicitis', 'ไส้ติ่งแตก', ['@K35.2', '@K35.3'], ['K35.2', 'K35.3']),
    ('SBO|IO|BOWEL OBSTRUCTION', 'Intestinal obstruction', 'ลำไส้อุดตัน', ['intestinal obstruction', '@K56'], ['K56.6', 'K56.7']),
    ('GS|CHOLELITHIASIS', 'Gallstones', 'นิ่วในถุงน้ำดี', ['cholelithiasis', '@K80'], ['K80.2', 'K80.0']),
    ('CBD STONE', 'Common bile duct stone', 'นิ่วในท่อน้ำดีร่วม', ['@K80.3', '@K80.4', '@K80.5'], ['K80.5']),
    ('AC', 'Acute cholecystitis / cholangitis', 'ถุงน้ำดีหรือท่อน้ำดีอักเสบเฉียบพลัน', ['acute cholecystitis', 'cholangitis', '@K81.0', '@K83.0'], ['K81.0', 'K83.0']),
    ('LC|CIRRHOSIS', 'Liver cirrhosis', 'ตับแข็ง', ['cirrhosis'], ['K74.6', 'K70.3']),
    ('ALD', 'Alcoholic liver disease', 'โรคตับจากสุรา', ['@K70'], ['K70.3', 'K70.9']),
    ('NAFLD|FATTY LIVER', 'Fatty liver', 'ไขมันพอกตับ', ['fatty (change of) liver', 'fatty liver', '@K76.0'], ['K76.0']),
    ('HE', 'Hepatic encephalopathy', 'ภาวะสมองผิดปกติจากโรคตับ', ['hepatic failure', '@K72'], ['K72.9', 'K72.1']),
    ('SBP', 'Spontaneous bacterial peritonitis', 'เยื่อบุช่องท้องอักเสบจากแบคทีเรีย', ['peritonitis'], ['K65.0', 'K65.9']),
    ('HBV|HEP B', 'Hepatitis B', 'ไวรัสตับอักเสบบี', ['hepatitis b', '@B16', '@B18.0', '@B18.1'], ['B18.1', 'B16.9']),
    ('HCV|HEP C', 'Hepatitis C', 'ไวรัสตับอักเสบซี', ['hepatitis c', '@B17.1', '@B18.2'], ['B18.2', 'B17.1']),
    ('HCC', 'Hepatocellular carcinoma', 'มะเร็งเซลล์ตับ', ['@C22.0'], ['C22.0']),
    ('CCA', 'Cholangiocarcinoma', 'มะเร็งท่อน้ำดี', ['@C22.1', '@C24.0'], ['C22.1', 'C24.0']),
    ('PANCREATITIS|AP', 'Acute pancreatitis', 'ตับอ่อนอักเสบเฉียบพลัน', ['acute pancreatitis', '@K85'], ['K85.9']),
    ('HEMORRHOID|HEMORRHOIDS|PILES', 'Haemorrhoids', 'ริดสีดวงทวาร', ['haemorrhoid', '@K64'], ['K64.9', 'K64.0', 'K64.1']),
    # ---- infection
    ('DHF', 'Dengue with warning signs / severe dengue', 'ไข้เลือดออกเด็งกี', ['@A97.1', '@A97.2'], ['A97.1', 'A97.2']),
    ('DF|DENGUE', 'Dengue', 'ไข้เด็งกี', ['@A97', 'dengue'], ['A97.0', 'A97.1', 'A97.2', 'A97.9']),
    ('DSS', 'Dengue shock syndrome', 'ไข้เลือดออกช็อก', ['dengue shock', '@A97.2'], ['A97.2']),
    ('HIV', 'HIV disease', 'โรคติดเชื้อเอชไอวี', ['human immunodeficiency virus', '@B20-B24', '@Z21'], ['B24', 'Z21']),
    ('AIDS', 'AIDS', 'โรคเอดส์', ['@B20-B24'], ['B24']),
    ('HFMD', 'Hand, foot and mouth disease', 'โรคมือเท้าปาก', ['vesicular stomatitis with exanthem', 'hand, foot and mouth'], ['B08.4']),
    ('FUO|PUO', 'Fever of unknown origin', 'ไข้ไม่ทราบสาเหตุ', ['@R50'], ['R50.9']),
    ('URTI', 'Upper respiratory infection', 'การติดเชื้อทางเดินหายใจส่วนบน', ['upper respiratory infection'], ['J06.9']),
    ('STI|STD', 'Sexually transmitted infection', 'โรคติดต่อทางเพศสัมพันธ์', ['@A50-A64'], ['A64']),
    ('MDR', 'Multidrug-resistant organism', 'เชื้อดื้อยาหลายขนาน', ['resistan', '@U82-U85'], ['U83.7', 'U84.7']),
    ('MRSA', 'Methicillin-resistant Staphylococcus aureus', 'เชื้อสแตฟิโลค็อกคัสดื้อเมทิซิลลิน', ['methicillin', '@U82.1', '@A49.0', '@B95.6'], ['U82.1', 'B95.6']),
    ('ESBL', 'ESBL-producing organism', 'เชื้อสร้างเอนไซม์ ESBL', ['@U82.2'], ['U82.2']),
    ('VRE', 'Vancomycin-resistant organism', 'เชื้อดื้อแวนโคมัยซิน', ['@U83.0'], ['U83.0']),
    ('COVID|COVID-19|COVID19|SARS-COV-2', 'COVID-19', 'โควิด-19', ['@U07.1', '@U07.2', 'covid'], ['U07.1', 'U07.2']),
    ('CELLULITIS', 'Cellulitis', 'เนื้อเยื่อใต้ผิวหนังอักเสบ', ['cellulitis', '@L03'], ['L03.9']),
    # ---- blood / oncology
    ('IDA', 'Iron deficiency anaemia', 'โลหิตจางจากการขาดธาตุเหล็ก', ['@D50'], ['D50.9']),
    ('ANEMIA', 'Anaemia', 'โลหิตจาง', ['anaemia'], ['D64.9']),
    ('THAL', 'Thalassaemia', 'ธาลัสซีเมีย', ['thalassaemia', '@D56'], ['D56.9']),
    ('G6PD', 'G6PD deficiency', 'ภาวะพร่องเอนไซม์ G6PD', ['glucose-6-phosphate', '@D55.0'], ['D55.0']),
    ('ITP', 'Idiopathic thrombocytopenic purpura', 'เกล็ดเลือดต่ำโดยไม่ทราบสาเหตุ', ['idiopathic thrombocytopenic', '@D69.3'], ['D69.3']),
    ('DIC', 'Disseminated intravascular coagulation', 'ภาวะเลือดแข็งตัวในหลอดเลือดแบบแพร่กระจาย', ['@D65'], ['D65']),
    ('FN|FEBRILE NEUTROPENIA', 'Febrile neutropenia', 'ไข้ร่วมกับเม็ดเลือดขาวต่ำ', ['agranulocytosis', 'neutropenia', '@D70'], ['D70']),
    ('AML', 'Acute myeloid leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดเฉียบพลันมัยอีลอยด์', ['@C92.0'], ['C92.0']),
    ('ALL', 'Acute lymphoblastic leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดเฉียบพลันลิมโฟบลาสติก', ['@C91.0'], ['C91.0']),
    ('CML', 'Chronic myeloid leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดเรื้อรังมัยอีลอยด์', ['@C92.1'], ['C92.1']),
    ('CLL', 'Chronic lymphocytic leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดเรื้อรังลิมโฟไซติก', ['@C91.1'], ['C91.1']),
    ('NHL', 'Non-Hodgkin lymphoma', 'มะเร็งต่อมน้ำเหลืองชนิดนอนฮอดจ์กิน', ['non-hodgkin', '@C82-C85'], ['C85.9']),
    ('HD|HL', 'Hodgkin lymphoma', 'มะเร็งต่อมน้ำเหลืองชนิดฮอดจ์กิน', ['@C81'], ['C81.9']),
    ('MM', 'Multiple myeloma', 'มะเร็งเซลล์พลาสมา', ['multiple myeloma', '@C90.0'], ['C90.0']),
    ('CA|CANCER|MALIGNANCY', 'Malignant neoplasm (cancer)', 'มะเร็ง', ['malignant neoplasm', 'carcinoma', '@C00-C97'], []),
    ('METS|METASTASIS|MET', 'Secondary (metastatic) malignant neoplasm', 'มะเร็งแพร่กระจาย', ['secondary malignant', '@C77-C79'], ['C79.9', 'C78.7', 'C79.3', 'C79.5']),
    ('CIS', 'Carcinoma in situ', 'มะเร็งระยะเริ่มแรก', ['in situ', '@D00-D09'], []),
    ('NPC', 'Nasopharyngeal carcinoma', 'มะเร็งโพรงหลังจมูก', ['@C11'], ['C11.9']),
    ('CRC', 'Colorectal cancer', 'มะเร็งลำไส้ใหญ่และทวารหนัก', ['@C18-C20'], ['C18.9', 'C20']),
    ('NSCLC|SCLC|LUNG CA', 'Lung cancer', 'มะเร็งปอด', ['@C34'], ['C34.9']),
    # ---- musculoskeletal / skin
    ('OA', 'Osteoarthritis', 'ข้อเสื่อม', ['arthrosis', '@M15-M19'], ['M17.9', 'M16.9']),
    ('OA KNEE', 'Osteoarthritis of knee', 'ข้อเข่าเสื่อม', ['@M17'], ['M17.9']),
    ('RA', 'Rheumatoid arthritis', 'โรคข้ออักเสบรูมาตอยด์', ['rheumatoid arthritis', '@M05', '@M06'], ['M06.9', 'M05.9']),
    ('SLE', 'Systemic lupus erythematosus', 'โรคเอสแอลอี', ['@M32'], ['M32.9', 'M32.1']),
    ('JIA|JRA', 'Juvenile arthritis', 'ข้ออักเสบในเด็ก', ['juvenile arthritis', '@M08'], ['M08.0']),
    ('LBP', 'Low back pain', 'ปวดหลังส่วนล่าง', ['@M54.5'], ['M54.5']),
    ('HNP', 'Herniated disc', 'หมอนรองกระดูกเคลื่อน', ['displacement of', 'disc disorder', '@M50.2', '@M51.2', '@M51.1'], ['M51.2', 'M51.1', 'M50.2']),
    ('FX|FRACTURE', 'Fracture', 'กระดูกหัก', ['fracture'], []),
    ('FX NECK OF FEMUR|FX NOF|HIP FX', 'Fracture of neck of femur', 'กระดูกคอสะโพกหัก', ['@S72.0', '@S72.1', '@S72.2'], ['S72.0']),
    ('DISLOCATION|DLC', 'Dislocation', 'ข้อเคลื่อน', ['dislocation'], []),
    ('SJS', 'Stevens-Johnson syndrome', 'กลุ่มอาการสตีเวนส์-จอห์นสัน', ['stevens-johnson', '@L51.1'], ['L51.1']),
    ('TEN', 'Toxic epidermal necrolysis', 'ผื่นผิวหนังตายเหตุพิษ', ['toxic epidermal necrolysis', '@L51.2'], ['L51.2']),
    ('DRESS|DRUG ALLERGY|ADR', 'Adverse drug reaction / drug allergy', 'แพ้ยา', ['@T88.7', 'drug eruption', '@L27.0'], ['T88.7', 'L27.0']),
    ('AD', 'Atopic dermatitis', 'ผื่นภูมิแพ้ผิวหนัง', ['atopic dermatitis', '@L20'], ['L20.9']),
    ('DM', 'Dermatomyositis', 'กล้ามเนื้อและผิวหนังอักเสบ', ['dermatomyositis'], []),
    # ---- eye / ENT
    ('POAG', 'Primary open-angle glaucoma', 'ต้อหินมุมเปิด', ['primary open-angle', '@H40.1'], ['H40.1']),
    ('PACG|ACG', 'Angle-closure glaucoma', 'ต้อหินมุมปิด', ['angle-closure', '@H40.2'], ['H40.2']),
    ('OM|AOM|OME', 'Otitis media', 'หูชั้นกลางอักเสบ', ['otitis media', '@H65', '@H66'], ['H66.9', 'H65.9']),
    ('OE', 'Otitis externa', 'หูชั้นนอกอักเสบ', ['otitis externa', '@H60'], ['H60.9']),
    ('DNS', 'Deviated nasal septum', 'ผนังกั้นช่องจมูกคด', ['deviated nasal septum', '@J34.2'], ['J34.2']),
    ('SNHL', 'Sensorineural hearing loss', 'ประสาทหูเสื่อม', ['sensorineural', '@H90.3', '@H90.4', '@H90.5'], ['H90.5']),
    # ---- pregnancy / newborn
    ('ANC', 'Antenatal care (supervision of pregnancy)', 'ฝากครรภ์', ['@Z34', '@Z35'], ['Z34.9', 'Z34.0']),
    ('NL|NSD|NVD|SVD|SPONTANEOUS DELIVERY|คลอดปกติ', 'Normal spontaneous delivery', 'คลอดปกติ', ['@O80'], ['O80.0', 'O80.9']),  # + คำไทย คลอดปกติ (8 พ.ย. 2569) ชื่อไทย TM ของ O80 คือ "การคลอดเอง" จึงหาไม่เจอ
    ('C/S|CS|LSCS|LTCS|CESAREAN|CAESAREAN|ผ่าคลอด|ผ่าตัดคลอด', 'Caesarean section delivery', 'ผ่าตัดคลอด', ['caesarean', '@O82'], ['O82.0', 'O82.1', 'O82.9']),  # + คำไทย ผ่าคลอด (8 พ.ย. 2569) ชื่อไทย TM ของ O82 คือ "...โดยการผ่าท้อง"
    ('V/E|VE|F/E|FE', 'Vacuum / forceps delivery', 'คลอดโดยใช้เครื่องสุญญากาศหรือคีม', ['@O81'], ['O81.4', 'O81.0']),
    ('PPH', 'Postpartum haemorrhage', 'ตกเลือดหลังคลอด', ['@O72'], ['O72.1', 'O72.0']),
    ('APH', 'Antepartum haemorrhage', 'เลือดออกก่อนคลอด', ['antepartum haemorrhage', '@O46'], ['O46.9']),
    ('PROM|PPROM', 'Premature rupture of membranes', 'ถุงน้ำคร่ำแตกก่อนเจ็บครรภ์', ['@O42'], ['O42.0', 'O42.9']),
    ('PTL|PRETERM LABOR|PRETERM LABOUR', 'Preterm labour', 'เจ็บครรภ์คลอดก่อนกำหนด', ['preterm labour', '@O60'], ['O60.1', 'O60.0']),
    ('CPD', 'Cephalopelvic disproportion', 'ศีรษะทารกไม่สัมพันธ์กับช่องเชิงกราน', ['disproportion', '@O33', '@O65'], ['O33.9', 'O65.4']),
    ('IUFD|FDIU|DFIU|STILLBIRTH', 'Intrauterine fetal death', 'ทารกตายในครรภ์', ['intrauterine death', '@O36.4', '@P95'], ['O36.4']),
    ('IUGR|FGR', 'Fetal growth restriction', 'ทารกเจริญเติบโตช้าในครรภ์', ['poor fetal growth', '@O36.5', '@P05'], ['O36.5', 'P05.9']),
    ('GHT', 'Gestational hypertension', 'ความดันโลหิตสูงขณะตั้งครรภ์', ['@O13'], ['O13']),
    ('PE|PREECLAMPSIA', 'Pre-eclampsia', 'ครรภ์เป็นพิษ', ['pre-eclampsia', '@O14'], ['O14.9', 'O14.1']),
    ('HELLP', 'HELLP syndrome', 'กลุ่มอาการ HELLP', ['hellp', '@O14.2'], ['O14.2']),
    ('HG', 'Hyperemesis gravidarum', 'แพ้ท้องรุนแรง', ['@O21'], ['O21.0', 'O21.1']),
    ('EP|ECTOPIC', 'Ectopic pregnancy', 'ตั้งครรภ์นอกมดลูก', ['ectopic pregnancy', '@O00'], ['O00.1', 'O00.9']),
    ('PP|PREVIA', 'Placenta praevia', 'รกเกาะต่ำ', ['placenta praevia', '@O44'], ['O44.1', 'O44.0']),
    ('AB|ABORTION', 'Abortion', 'แท้ง', ['abortion', '@O03-O08'], ['O03.9', 'O06.9']),
    ('PRETERM|PRETERM INFANT','Preterm infant', 'ทารกคลอดก่อนกำหนด', ['@P07.2', '@P07.3'], ['P07.3', 'P07.2']),
    ('LBW|VLBW|ELBW', 'Low birth weight', 'ทารกน้ำหนักแรกเกิดน้อย', ['low birth weight', '@P07.0', '@P07.1'], ['P07.1', 'P07.0']),
    ('NNJ|NJ', 'Neonatal jaundice', 'ทารกแรกเกิดตัวเหลือง', ['neonatal jaundice', '@P59'], ['P59.9']),
    ('MAS', 'Meconium aspiration syndrome', 'ทารกสำลักขี้เทา', ['meconium aspiration', '@P24.0'], ['P24.0']),
    ('TTNB|TTN', 'Transient tachypnoea of newborn', 'ทารกหายใจเร็วชั่วคราว', ['transient tachypnoea', '@P22.1'], ['P22.1']),
    ('NEC', 'Necrotizing enterocolitis', 'ลำไส้เน่าอักเสบในทารก', ['necrotizing enterocolitis', '@P77'], ['P77']),
    ('BBA', 'Born before arrival', 'คลอดก่อนถึงโรงพยาบาล', ['@Z38.1'], ['Z38.1']),
    ('NB|NEWBORN|LIVEBORN', 'Liveborn infant', 'ทารกเกิดมีชีพ', ['@Z38'], ['Z38.0']),
    ('PPV', 'Postpartum care', 'ตรวจหลังคลอด', ['@Z39'], ['Z39.2']),
    ('FP|IUD|DMPA|OCP', 'Contraceptive management', 'การคุมกำเนิด', ['contracepti', '@Z30'], ['Z30.0', 'Z30.4']),
    # ---- symptoms / general
    ('N/V|NV|VOMITING', 'Nausea and vomiting', 'คลื่นไส้อาเจียน', ['nausea', 'vomiting', '@R11'], ['R11']),
    ('ABD PAIN|AP', 'Abdominal pain', 'ปวดท้อง', ['abdominal', '@R10'], ['R10.4']),
    ('CP|CHEST PAIN', 'Chest pain', 'เจ็บหน้าอก', ['chest pain', '@R07'], ['R07.4']),
    ('SOB|DYSPNEA|DOE', 'Dyspnoea', 'หายใจเหนื่อยหอบ', ['dyspnoea', '@R06.0'], ['R06.0']),
    ('LOC|SYNCOPE', 'Syncope / loss of consciousness', 'หมดสติ', ['syncope', 'unconscious', '@R55', '@R40'], ['R55', 'R40.2']),
    ('AMS|ALTERED CONSCIOUSNESS', 'Altered mental status', 'ระดับความรู้สึกตัวเปลี่ยนแปลง', ['@R40', 'delirium'], ['R40.0', 'R41.0']),
    ('DIZZINESS', 'Dizziness', 'เวียนศีรษะ', ['dizziness', '@R42'], ['R42']),
    ('SHOCK', 'Shock', 'ภาวะช็อก', ['shock', '@R57'], ['R57.9', 'R57.1']),
    ('SEPSIS|SEPTICEMIA|SEPTICAEMIA', 'Sepsis', 'ภาวะติดเชื้อในกระแสเลือด', ['sepsis', 'septicaemia', '@A40', '@A41'], ['A41.9']),
    ('SEPTIC SHOCK', 'Septic shock', 'ช็อกจากการติดเชื้อ', ['septic shock', '@R57.2', '@A41'], ['R57.2', 'A41.9']),
    ('OD|OVERDOSE|POISONING', 'Poisoning / overdose', 'ได้รับยาเกินขนาดหรือสารพิษ', ['poisoning', '@T36-T65'], []),
    ('DOG BITE', 'Dog bite', 'สุนัขกัด', ['@W54'], ['W54']),
    ('SNAKE BITE', 'Snake bite', 'งูกัด', ['snake', '@X20', '@T63.0'], ['T63.0', 'X20']),
    ('MCA|MC ACCIDENT|MOTORCYCLE', 'Motorcycle accident', 'อุบัติเหตุรถจักรยานยนต์', ['motorcycle', '@V20-V29'], []),
    ('MVA|MVC|RTA|TA|TRAFFIC', 'Motor vehicle / transport accident', 'อุบัติเหตุจราจร', ['transport accident', 'traffic accident', 'motor vehicle', '@V01-V89'], []),
    ('FALL', 'Fall', 'พลัดตกหกล้ม', ['@W00-W19', 'fall'], []),
    ('ASSAULT', 'Assault', 'ถูกทำร้าย', ['@X85-Y09', 'assault'], []),
    ('SUICIDE|SELF HARM', 'Intentional self-harm', 'ทำร้ายตนเอง', ['@X60-X84', 'self-harm'], []),
    ('F/U|FU|FOLLOW UP|FOLLOW-UP', 'Follow-up examination', 'ตรวจติดตามการรักษา', ['follow-up', '@Z08', '@Z09'], ['Z09.8', 'Z09.9']),
    ('OPD|CHECK UP|CHECKUP', 'General examination', 'ตรวจสุขภาพทั่วไป', ['general examination', '@Z00'], ['Z00.0']),
    ('EPI|VACCINE|VACCINATION', 'Vaccination', 'ฉีดวัคซีน', ['vaccination', 'immunization', '@Z23-Z27'], ['Z27.8', 'Z23.5']),
    ('BMI|OBESITY', 'Obesity', 'โรคอ้วน', ['obesity', '@E66'], ['E66.9']),
    ('MALNUTRITION|PEM', 'Protein-energy malnutrition', 'ภาวะทุพโภชนาการ', ['malnutrition', '@E40-E46'], ['E46', 'E44.0']),
    ('DEHYDRATION', 'Dehydration / volume depletion', 'ภาวะขาดน้ำ', ['volume depletion', '@E86'], ['E86']),
    ('BEDSORE|PRESSURE ULCER', 'Pressure ulcer', 'แผลกดทับ', ['decubitus', '@L89'], ['L89.9']),
    ('PALLIATIVE|PC', 'Palliative care', 'การดูแลแบบประคับประคอง', ['palliative', '@Z51.5'], ['Z51.5']),
    ('CHEMO|CMT', 'Chemotherapy session', 'ให้ยาเคมีบำบัด', ['chemotherapy', '@Z51.1'], ['Z51.1']),
    ('RT|RADIOTHERAPY', 'Radiotherapy session', 'ฉายรังสีรักษา', ['radiotherapy', '@Z51.0'], ['Z51.0']),
    ('HD|DIALYSIS|ฟอกไต', 'Dialysis care', 'ฟอกไต', ['dialysis', '@Z49'], ['Z49.1', 'Z99.2']),
    # ---- added from the medical-terms glossary (cleaned.xlsx, 2026-11): abbreviations that map to codes
    ('AUB', 'Abnormal uterine bleeding', 'เลือดออกผิดปกติจากโพรงมดลูก', ['@N93', '@N92'], ['N93.9', 'N93.8']),
    ('DUB', 'Dysfunctional uterine bleeding', 'เลือดออกผิดปกติจากมดลูกเหตุฮอร์โมน', ['@N93.8'], ['N93.8']),
    ('ANLL', 'Acute non-lymphocytic (myeloid) leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดมัยอีลอยด์เฉียบพลัน', ['@C92.0'], ['C92.0']),
    ('ATN', 'Acute tubular necrosis', 'ท่อไตฝอยตายเฉียบพลัน', ['@N17.0'], ['N17.0']),
    ('AMD|ARMD', 'Age-related macular degeneration', 'จอประสาทตาเสื่อมตามอายุ', ['@H35.3'], ['H35.3']),
    ('AVM', 'Arteriovenous malformation', 'หลอดเลือดแดงและหลอดเลือดดำเชื่อมกันผิดปกติ', ['@Q28.2', '@Q27.3'], ['Q28.2', 'Q27.3']),
    ('AIHA', 'Autoimmune haemolytic anaemia', 'โลหิตจางจากเม็ดเลือดแดงแตกเหตุภูมิต้านตนเอง', ['@D59.1'], ['D59.1']),
    ('BE|SBE', 'Bacterial (subacute) endocarditis', 'เยื่อบุหัวใจอักเสบจากแบคทีเรีย', ['@I33.0'], ['I33.0']),
    ('CTS', 'Carpal tunnel syndrome', 'เส้นประสาทมีเดียนถูกกดทับที่ข้อมือ', ['@G56.0'], ['G56.0']),
    ('CIN', 'Cervical intraepithelial neoplasia', 'รอยโรคก่อนมะเร็งปากมดลูก', ['@N87', '@D06'], ['N87.9', 'D06.9']),
    ('CIN III|CIN 3|CIN3', 'Cervical intraepithelial neoplasia grade III', 'รอยโรคก่อนมะเร็งปากมดลูกระดับ 3', ['@D06'], ['D06.9']),
    ('CAH', 'Chronic active hepatitis', 'ตับอักเสบเรื้อรังชนิดแอคทีฟ', ['@K73.2'], ['K73.2']),
    ('CAH', 'Congenital adrenal hyperplasia', 'ต่อมหมวกไตโตแต่กำเนิด', ['@E25.0'], ['E25.0']),
    ('CGN', 'Chronic glomerulonephritis', 'ไตอักเสบเรื้อรัง', ['@N03'], ['N03.9']),
    ('CGL', 'Chronic granulocytic (myeloid) leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดมัยอีลอยด์เรื้อรัง', ['@C92.1'], ['C92.1']),
    ('COA', 'Coarctation of aorta', 'หลอดเลือดแดงใหญ่ตีบแคบแต่กำเนิด', ['@Q25.1'], ['Q25.1']),
    ('CHD', 'Coronary heart disease', 'โรคหลอดเลือดหัวใจ', ['@I20-I25'], ['I25.1', 'I25.9']),
    ('CHD', 'Congenital heart disease', 'โรคหัวใจพิการแต่กำเนิด', ['@Q20-Q24'], ['Q24.9']),
    ('CMV', 'Cytomegalovirus disease', 'โรคติดเชื้อไซโตเมกะโลไวรัส', ['@B25'], ['B25.9']),
    ('DTS', 'Delirium tremens', 'ภาวะสับสนเพ้อจากการถอนสุรา', ['@F10.4'], ['F10.4']),
    ('DI', 'Diabetes insipidus', 'เบาจืด', ['@E23.2', '@N25.1'], ['E23.2', 'N25.1']),
    ('DORV', 'Double outlet right ventricle', 'หัวใจห้องล่างขวามีทางออกสองทาง', ['@Q20.1'], ['Q20.1']),
    ('DCIS', 'Ductal carcinoma in situ', 'มะเร็งท่อน้ำนมระยะไม่ลุกลาม', ['@D05.1'], ['D05.1']),
    ('ED', 'Erectile dysfunction', 'ภาวะหย่อนสมรรถภาพทางเพศ', ['@N48.4', '@F52.2'], ['N48.4', 'F52.2']),
    ('EA', 'Oesophageal atresia', 'หลอดอาหารตีบตันแต่กำเนิด', ['@Q39.0', '@Q39.1'], ['Q39.1', 'Q39.0']),
    ('TEF|T-E FISTULA', 'Tracheo-oesophageal fistula (congenital)', 'รูเชื่อมหลอดลมคอกับหลอดอาหารแต่กำเนิด', ['@Q39.1', '@Q39.2'], ['Q39.2', 'Q39.1']),
    ('EKC', 'Epidemic keratoconjunctivitis', 'เยื่อบุตาและกระจกตาอักเสบชนิดระบาด', ['@B30.0'], ['B30.0']),
    ('FAS', 'Fetal alcohol syndrome', 'กลุ่มอาการทารกได้รับแอลกอฮอล์ในครรภ์', ['@Q86.0'], ['Q86.0']),
    ('FSGS', 'Focal segmental glomerulosclerosis', 'หน่วยไตแข็งเป็นหย่อม', ['focal and segmental'], ['N04.1', 'N03.1']),
    ('GER', 'Gastro-oesophageal reflux', 'กรดไหลย้อน', ['@K21'], ['K21.9']),
    ('G-6-PD', 'G6PD deficiency', 'ภาวะพร่องเอนไซม์ G6PD', ['glucose-6-phosphate', '@D55.0'], ['D55.0']),
    ('GC', 'Gonorrhoea', 'หนองใน', ['@A54'], ['A54.9']),
    ('GVHD|GVHR', 'Graft-versus-host disease', 'ภาวะเซลล์ปลูกถ่ายต่อต้านร่างกายผู้รับ', ['@T86.0'], ['T86.0']),
    ('HSV', 'Herpes simplex virus infection', 'การติดเชื้อเริม', ['@B00', '@A60'], ['B00.9', 'A60.0']),
    ('HPV', 'Human papillomavirus', 'การติดเชื้อไวรัสเอชพีวี', ['@B97.7', '@A63.0'], ['B97.7', 'A63.0']),
    ('HHNS|NKHHC', 'Hyperosmolar hyperglycaemic state', 'น้ำตาลในเลือดสูงร่วมกับภาวะออสโมลาร์สูง', ['hyperosmolar', '@E11.0', '@E14.0'], ['E11.0']),
    ('HPS', 'Hypertrophic pyloric stenosis', 'หูรูดกระเพาะอาหารส่วนปลายหนาตัวตีบแต่กำเนิด', ['@Q40.0'], ['Q40.0']),
    ('JOD', 'Juvenile-onset (type 1) diabetes', 'เบาหวานชนิดที่ 1', ['@E10'], ['E10.9']),
    ('KS', 'Kaposi sarcoma', 'มะเร็งคาโปซี', ['@C46'], ['C46.9']),
    ('LGA', 'Large for gestational age', 'ทารกตัวโตกว่าอายุครรภ์', ['@P08.1'], ['P08.1']),
    ('SGA|SFD', 'Small for gestational age', 'ทารกตัวเล็กกว่าอายุครรภ์', ['@P05'], ['P05.1', 'P05.0']),
    ('LGV', 'Lymphogranuloma venereum', 'กามโรคต่อมน้ำเหลือง', ['@A55'], ['A55']),
    ('MCNS', 'Minimal change nephrotic syndrome', 'กลุ่มอาการเนฟโฟรติกชนิดมินิมัลเชนจ์', ['@N04.0'], ['N04.0']),
    ('MD', 'Muscular dystrophy', 'กล้ามเนื้อเสื่อมแต่กำเนิด', ['@G71.0'], ['G71.0']),
    ('ME|CFS', 'Myalgic encephalomyelitis (chronic fatigue syndrome)', 'กลุ่มอาการอ่อนล้าเรื้อรัง', ['@G93.3'], ['G93.3']),
    ('NMS', 'Neuroleptic malignant syndrome', 'กลุ่มอาการรุนแรงจากยารักษาโรคจิต', ['@G21.0'], ['G21.0']),
    ('NSU|NGU', 'Non-specific (non-gonococcal) urethritis', 'ท่อปัสสาวะอักเสบที่ไม่ใช่หนองใน', ['@N34.1'], ['N34.1']),
    ('OCPD', 'Obsessive-compulsive personality disorder', 'บุคลิกภาพผิดปกติแบบย้ำคิดย้ำทำ', ['@F60.5'], ['F60.5']),
    ('PID', 'Pelvic inflammatory disease', 'อุ้งเชิงกรานอักเสบ', ['@N70-N73'], ['N73.9', 'N70.9']),
    ('PPHN', 'Persistent pulmonary hypertension of newborn', 'ความดันหลอดเลือดปอดสูงต่อเนื่องในทารกแรกเกิด', ['@P29.3'], ['P29.3']),
    ('PCP|PJP', 'Pneumocystis pneumonia', 'ปอดอักเสบจากเชื้อนิวโมซิสติส', ['@B59', '@B20.6'], ['B59']),
    ('PKD', 'Polycystic kidney disease', 'โรคถุงน้ำในไตหลายใบ', ['@Q61.1', '@Q61.2', '@Q61.3'], ['Q61.3', 'Q61.2']),
    ('PMS', 'Premenstrual syndrome', 'กลุ่มอาการก่อนมีประจำเดือน', ['@N94.3'], ['N94.3']),
    ('PS', 'Pulmonary (valve) stenosis', 'ลิ้นหัวใจพัลโมนารีตีบ', ['@Q22.1', '@I37.0'], ['Q22.1', 'I37.0']),
    ('RS', 'Raynaud syndrome', 'กลุ่มอาการเรย์โนด์', ['@I73.0'], ['I73.0']),
    ('ROP', 'Retinopathy of prematurity', 'จอประสาทตาผิดปกติในทารกคลอดก่อนกำหนด', ['@H35.1'], ['H35.1']),
    ('SOM', 'Serous otitis media', 'หูชั้นกลางอักเสบมีน้ำขัง', ['@H65.0', '@H65.2', '@H65.9'], ['H65.0', 'H65.9']),
    ('SIADH', 'Syndrome of inappropriate antidiuretic hormone', 'กลุ่มอาการหลั่งฮอร์โมนต้านการขับปัสสาวะผิดปกติ', ['@E22.2'], ['E22.2']),
    ('TEV|CTEV', 'Talipes equinovarus (clubfoot)', 'เท้าปุก', ['@Q66.0'], ['Q66.0']),
    ('TMJ|TMD', 'Temporomandibular joint disorder', 'ข้อต่อขากรรไกรผิดปกติ', ['@K07.6'], ['K07.6']),
    ('TOA', 'Thromboangiitis obliterans (Buerger disease)', 'หลอดเลือดอักเสบอุดตัน (โรคเบอร์เกอร์)', ['@I73.1'], ['I73.1']),
    ('TOA', 'Tubo-ovarian abscess', 'ฝีที่ท่อนำไข่และรังไข่', ['@N70.0', '@N70.1'], ['N70.0']),
    ('TSS', 'Toxic shock syndrome', 'กลุ่มอาการช็อกจากพิษ', ['@A48.3'], ['A48.3']),
    ('TGA|TGV', 'Transposition of great arteries', 'การสลับที่ของหลอดเลือดใหญ่', ['@Q20.3'], ['Q20.3']),
    ('TS', 'Tricuspid stenosis', 'ลิ้นหัวใจไตรคัสปิดตีบ', ['@I07.0', '@I36.0'], ['I07.0', 'I36.0']),
    ('VVC', 'Vulvovaginal candidiasis', 'เชื้อราแคนดิดาในช่องคลอด', ['@B37.3'], ['B37.3']),
    ('VZV', 'Varicella-zoster virus infection', 'การติดเชื้อไวรัสอีสุกอีใสหรืองูสวัด', ['@B01', '@B02'], ['B01.9', 'B02.9']),
    ('VVF|V-V FISTULA', 'Vesicovaginal fistula', 'รูทะลุระหว่างกระเพาะปัสสาวะกับช่องคลอด', ['@N82.0'], ['N82.0']),
    ('CCF|C-C FISTULA', 'Carotid-cavernous fistula', 'ทางเชื่อมผิดปกติระหว่างหลอดเลือดแดงคาโรติดกับโพรงคาเวอร์นัส', ['@I67.1', '@S09.0'], ['I67.1', 'S09.0']),
    ('CSR', 'Cheyne-Stokes respiration', 'การหายใจแบบเชย์น-สโตกส์', ['@R06.3'], ['R06.3']),
    ('IUCD', 'Contraceptive management', 'การคุมกำเนิด', ['contracepti', '@Z30'], ['Z30.0', 'Z30.4']),
    # ---- เพิ่มจากร่างรวม 7 แหล่ง (claude/abbr-handoff.md, 2026-11) รหัสผูกโดย Claude รอทีมแพทย์/coder ตรวจ ----
    ('HMD', 'Respiratory distress syndrome of newborn / Hyaline membrane disease', 'ภาวะหายใจลำบากของทารกแรกเกิด', ['@P22.0'], ['P22.0']),
    ('APL', 'Acute promyelocytic leukemia', 'มะเร็งเม็ดเลือดขาวโปรไมอีโลไซติกเฉียบพลัน', ['@C92.4'], ['C92.4']),
    ('DLBCL', 'Diffuse large B-cell lymphoma', 'มะเร็งต่อมน้ำเหลืองชนิดบีเซลล์ขนาดใหญ่', ['@C83.3'], ['C83.3']),
    ('MDS', 'Myelodysplastic syndrome', 'กลุ่มอาการเม็ดเลือดผิดปกติ (MDS)', ['@D46'], ['D46']),
    ('HUS', 'Hemolytic uremic syndrome', 'กลุ่มอาการเม็ดเลือดแดงแตกและยูรีเมีย', ['@D59.3'], ['D59.3']),
    ('PNH', 'Paroxysmal nocturnal hemoglobinuria', 'ฮีโมโกลบินในปัสสาวะเป็นพักๆ ตอนกลางคืน', ['@D59.5'], ['D59.5']),
    ('HSP', 'Henoch-Schönlein purpura', 'ผื่นเลือดออกเฮนอค-เชินไลน์', ['@D69.0'], ['D69.0']),
    ('DLD', 'Dyslipidemia / Hyperlipidemia', 'ไขมันในเลือดผิดปกติ/สูง', ['@E78'], ['E78']),
    ('PCOS', 'Polycystic ovary syndrome', 'กลุ่มอาการรังไข่มีถุงน้ำหลายใบ', ['@E28.2'], ['E28.2']),
    ('HZO', 'Herpes zoster ophthalmicus', 'งูสวัดที่ตา', ['@B02.3'], ['B02.3']),
    ('VD', 'Sexually transmitted disease / Venereal disease', 'โรคติดต่อทางเพศสัมพันธ์', ['@A64'], ['A64']),
    ('WC', 'Whooping cough (pertussis)', 'ไอกรน', ['@A37'], ['A37']),
    ('HW', 'Hookworm disease', 'โรคพยาธิปากขอ', ['@B76'], ['B76']),
    ('NF', 'Necrotizing fasciitis', 'พังผืดและเนื้อเยื่อใต้ผิวหนังเน่าตาย', ['@M72.6'], ['M72.6']),
    ('DT', 'Delirium tremens', 'ภาวะเพ้อสั่นจากถอนแอลกอฮอล์', ['@F10.4'], ['F10.4']),
    ('DCM', 'Dilated cardiomyopathy', 'กล้ามเนื้อหัวใจขยายตัว', ['@I42.0'], ['I42.0']),
    ('HCM|HOCM', 'Hypertrophic (obstructive) cardiomyopathy', 'กล้ามเนื้อหัวใจหนาตัว', ['@I42.1', '@I42.2'], ['I42.1', 'I42.2']),
    ('PAC', 'Premature atrial contraction', 'หัวใจห้องบนเต้นก่อนจังหวะ', ['@I49.1'], ['I49.1']),
    ('PVC', 'Premature ventricular contraction', 'หัวใจห้องล่างเต้นก่อนจังหวะ', ['@I49.3'], ['I49.3']),
    ('LBBB', 'Left bundle branch block', 'การนำไฟฟ้าหัวใจบล็อกมัดซ้าย', ['@I44.7'], ['I44.7']),
    ('RBBB', 'Right bundle branch block', 'การนำไฟฟ้าหัวใจบล็อกมัดขวา', ['@I45.1'], ['I45.1']),
    ('WPW', 'Wolff-Parkinson-White syndrome', 'กลุ่มอาการวูล์ฟ-พาร์กินสัน-ไวท์', ['@I45.6'], ['I45.6']),
    ('CRA|CPA', 'Cardiorespiratory / Cardiopulmonary arrest', 'หัวใจและการหายใจหยุด', ['@I46'], ['I46']),
    ('TAO', 'Thromboangiitis obliterans (Buerger)', 'หลอดเลือดอักเสบอุดตัน (บูร์เกอร์)', ['@I73.1'], ['I73.1']),
    ('VV', 'Varicose veins', 'เส้นเลือดขอด', ['@I83'], ['I83']),
    ('GIH', 'Upper/Gastrointestinal bleeding', 'เลือดออกในทางเดินอาหาร', ['@K92.0', '@K92.1', '@K92.2'], ['K92.0', 'K92.1', 'K92.2']),
    ('NUD', 'Non-ulcer dyspepsia', 'อาหารไม่ย่อยชนิดไม่มีแผล', ['@K30'], ['K30']),
    ('DJD', 'Degenerative joint disease', 'ข้อเสื่อม', ['@M15-M19'], []),
    ('CRAO', 'Central retinal artery occlusion', 'หลอดเลือดแดงจอประสาทตาส่วนกลางอุดตัน', ['@H34.1'], ['H34.1']),
    ('CRVO|BRVO', 'Central/Branch retinal vein occlusion', 'หลอดเลือดดำจอประสาทตาอุดตัน', ['@H34.8'], ['H34.8']),
    ('RD', 'Retinal detachment', 'จอประสาทตาลอก', ['@H33'], ['H33']),
    ('COM|CSOM', 'Chronic (suppurative) otitis media', 'หูชั้นกลางอักเสบเรื้อรัง', ['@H66.1', '@H66.2', '@H66.3'], ['H66.1', 'H66.2', 'H66.3']),
    ('ASD', 'Autism spectrum disorder', 'ออทิสติกสเปกตรัม', ['@F84.0'], []),  # เพิ่มความหมายที่ไม่มีในรายการเดิม
    ('CDH', 'Congenital dislocation of hip', 'ข้อสะโพกเคลื่อนแต่กำเนิด', ['@Q65'], ['Q65']),
    ('PET', 'Pre-eclampsia', 'ครรภ์เป็นพิษ', ['@O14'], ['O14']),
    ('HDP', 'Hypertensive disorders in pregnancy', 'ความดันโลหิตสูงในสตรีตั้งครรภ์', ['@O10-O16'], []),
    ('GTD', 'Gestational trophoblastic disease', 'โรคเนื้อเยื่อรกผิดปกติ (ครรภ์ไข่ปลาอุก)', ['@O01'], ['O01']),
    ('BPD', 'Bronchopulmonary dysplasia', 'ปอดเรื้อรังในทารกคลอดก่อนกำหนด', ['@P27.1'], ['P27.1']),  # BPD ยังหมายถึง biparietal diameter ได้
    ('FTT', 'Failure to thrive', 'เจริญเติบโตช้า', ['@R62.8'], ['R62.8']),
    ('SIDS', 'Sudden infant death syndrome', 'ทารกเสียชีวิตเฉียบพลันไม่ทราบสาเหตุ', ['@R95'], ['R95']),
    ('RTI', 'Road traffic injury / Motor vehicle accident', 'อุบัติเหตุจราจร', ['@V01-V89'], []),
    ('MI', 'Mitral insufficiency', 'ลิ้นหัวใจไมทรัลรั่ว', ['@I34.0'], []),  # เพิ่มความหมายที่ไม่มีในรายการเดิม
    ('CA', 'Cardiac arrest', 'หัวใจหยุดเต้น', ['@I46'], []),  # เพิ่มความหมายที่ไม่มีในรายการเดิม
    ('CP', 'Cleft palate', 'เพดานโหว่', ['@Q35'], []),  # เพิ่มความหมายที่ไม่มีในรายการเดิม
    ('NTG', 'Normal-tension glaucoma / Nitroglycerin', 'ต้อหินความดันตาปกติ / ไนโตรกลีเซอรีน', ['@H40.1', 'nitroglycerin'], []),  # หลายความหมาย
    ('OPP|DTA', 'Persistent occipitoposterior position / Deep transverse arrest', 'ศีรษะทารกหมุนไม่ครบ (ท่าท้ายทอยหลังค้าง)', ['@O64.0'], ['O64.0']),  # แหล่งเดิมให้ LOP = O32.4 ซึ่งไม่ตรง ICD-10 จึงไม่เพิ่ม LOP
    ('N/D', 'Normal (spontaneous) vaginal delivery', 'คลอดปกติทางช่องคลอด', ['@O80'], ['O80']),  # NVD ใน ASHA = nausea, vomiting, diarrhea
    ('AHP', 'Antepartum hemorrhage', 'เลือดออกก่อนคลอด', ['@O46'], ['O46']),
    ('ROM', 'Rupture of membranes', 'ถุงน้ำคร่ำแตก', ['@O42'], ['O42']),  # ROM ยังหมายถึง range of motion
    ('BOH', 'Bad obstetric history', 'ประวัติการตั้งครรภ์/คลอดที่ไม่ดี', ['@Z35.2', '@Z87.5'], ['Z35.2', 'Z87.5']),
    ('ASA', 'Aspirin (acetylsalicylic acid)', 'แอสไพริน', ['aspirin'], []),  # ผูกด้วยคำค้นชื่อยา ใช้ตารางยาเลือกรหัสพิษ/ผลไม่พึงประสงค์ | alt ที่ไม่พบรหัส: acetylsalicylic
    ('MO', 'Morphine', 'มอร์ฟีน', ['morphine'], []),  # ผูกด้วยคำค้นชื่อยา
    ('Hx|H/O', 'History of (personal or family)', 'ประวัติ (ส่วนตัวหรือครอบครัว) ของโรค', ['@Z80-Z87'], []),  # ต้องเลือกรหัสตามโรคที่เคยเป็น
    ('FH', 'Family history', 'ประวัติครอบครัว', ['@Z80-Z84'], []),
    ('PMH', 'Past medical history', 'ประวัติการเจ็บป่วยในอดีต', ['@Z86-Z87'], []),
    ('S/P', 'Status post (postprocedural state)', 'สถานะหลังการผ่าตัด/หัตถการ', ['@Z98'], ['Z98']),
    ('OMI|Old MI', 'Old myocardial infarction', 'กล้ามเนื้อหัวใจตายเก่า', ['@I25.2'], ['I25.2']),
    ('FB', 'Foreign body', 'สิ่งแปลกปลอม', ['@T15-T19'], []),  # เลือกรหัสตามตำแหน่ง
    ('GSW', 'Gunshot wound', 'บาดแผลถูกยิง', ['@W32-W34', '@X93-X95'], []),  # สาเหตุภายนอก เลือกตามเจตนา
    # ---- เพิ่ม 4 พ.ย. 2569 (รอบสอง) ----
    ('CCHD', 'Critical congenital heart disease', 'โรคหัวใจพิการแต่กำเนิดชนิดวิกฤต', ['@Q20.0', '@Q20.1', '@Q20.3', '@Q20.4', '@Q21.2', '@Q21.3', '@Q22.0', '@Q22.1', '@Q22.4', '@Q22.5', '@Q23.0', '@Q23.4', '@Q25.1', '@Q25.4', '@Q25.5', '@Q25.6', '@Q26.2'], []),  # รายการคัดกรอง pulse oximetry (ND HHS, KDHE) แปลงเป็นรหัส WHO 2016; interrupted aortic arch ใช้ Q25.4
    ('CCHD', 'Cyanotic congenital heart disease', 'โรคหัวใจพิการแต่กำเนิดชนิดเขียว', ['@Q24.9'], []),  # ตามรายการ รพ.ราชบุรี (Q24.9)
    # ---- เพิ่ม 4 พ.ย. 2569 จากแหล่งที่ผู้ใช้ให้ (รพ.ราชบุรี, รพ.ฟากท่า, MedlinePlus) รหัสตรวจกับ WHO 2016 แล้ว รอทีมตรวจ ----
    ('AACG', 'Acute angle-closure glaucoma', 'ต้อหินมุมปิดเฉียบพลัน', ['@H40.2'], ['H40.2']),  # รพ.ราชบุรี
    ('ABC', 'Aneurysmal bone cyst', 'ถุงน้ำกระดูกชนิดหลอดเลือดโป่ง', ['@M85.5'], ['M85.5']),  # รพ.ราชบุรี
    ('ACD', 'Allergic contact dermatitis', 'ผิวหนังอักเสบจากการสัมผัสสารก่อภูมิแพ้', ['@L23'], ['L23.9']),  # รพ.ราชบุรี
    ('ADPKD', 'Autosomal dominant polycystic kidney disease', 'โรคถุงน้ำในไตชนิดถ่ายทอดแบบยีนเด่น', ['@Q61.2'], ['Q61.2']),  # รพ.ราชบุรี (แหล่งให้ N28.9 ใช้ Q61.2 ตาม WHO)
    ('ADU', 'Acute duodenal ulcer', 'แผลลำไส้เล็กส่วนต้นเฉียบพลัน', ['@K26.0-K26.3'], ['K26.3']),  # รพ.ราชบุรี
    ('AFI', 'Acute febrile illness', 'ไข้เฉียบพลัน', ['@R50.9'], ['R50.9']),  # รพ.ราชบุรี
    ('AGNS', 'Acute glomerulonephritis syndrome', 'กลุ่มอาการไตอักเสบเฉียบพลัน', ['@N00'], ['N00.9']),  # รพ.ราชบุรี
    ('AHA', 'Acquired haemolytic anaemia', 'โลหิตจางจากเม็ดเลือดแดงแตกชนิดเกิดภายหลัง', ['@D59'], ['D59.9']),  # รพ.ราชบุรี
    ('AHC', 'Acute haemorrhagic conjunctivitis', 'เยื่อบุตาอักเสบชนิดมีเลือดออกเฉียบพลัน (ตาแดงจากเอนเทอโรไวรัส)', ['@B30.3'], ['B30.3']),  # รพ.ราชบุรี (แหล่งให้ H11.3 ใช้ B30.3)
    ('AHD', 'Arteriosclerotic heart disease', 'โรคหัวใจจากหลอดเลือดแข็ง', ['@I25.1'], ['I25.1']),  # รพ.ราชบุรี ความหมายแรก
    ('AHD', 'Aortic heart disease', 'โรคลิ้นหัวใจเอออร์ติก', ['@I35'], []),  # รพ.ราชบุรี ความหมายที่สอง
    ('AHF', 'Acute haemorrhagic fever (dengue)', 'ไข้เลือดออก', ['@A97.1', '@A97.2'], ['A97.1', 'A97.2']),  # รพ.ราชบุรี ใช้รหัสเดียวกับ DHF
    ('AI', 'Aortic insufficiency', 'ลิ้นหัวใจเอออร์ติกรั่ว', ['@I35.1', '@I06.1'], ['I35.1']),  # รพ.ราชบุรี
    ('AMC', 'Arthrogryposis multiplex congenita', 'ข้อติดแข็งหลายข้อแต่กำเนิด', ['@Q74.3'], ['Q74.3']),  # รพ.ราชบุรี
    ('AMM', 'Agnogenic myeloid metaplasia (primary myelofibrosis)', 'ไขกระดูกเป็นพังผืดชนิดปฐมภูมิ', ['@D47.4'], ['D47.4']),  # รพ.ราชบุรี (แหล่งให้ D73.1 ใช้ D47.4)
    ('AMML|AMMOL', 'Acute myelomonocytic leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดไมอีโลโมโนไซติกเฉียบพลัน', ['@C92.5'], ['C92.5']),  # รพ.ราชบุรี
    ('AMOL', 'Acute monocytic leukaemia', 'มะเร็งเม็ดเลือดขาวชนิดโมโนไซติกเฉียบพลัน', ['@C93.0'], ['C93.0']),  # รพ.ราชบุรี
    ('ANUG', 'Acute necrotizing ulcerative gingivitis', 'เหงือกอักเสบเป็นแผลเนื้อตายเฉียบพลัน', ['@A69.1'], ['A69.1']),  # รพ.ราชบุรี
    ('APC', 'Atrial premature contraction', 'หัวใจห้องบนเต้นก่อนจังหวะ', ['@I49.1'], ['I49.1']),  # รพ.ราชบุรี
    ('APCD', 'Acquired prothrombin complex deficiency', 'ภาวะขาดปัจจัยการแข็งตัวของเลือดชนิดเกิดภายหลัง', ['@D68.4'], ['D68.4']),  # รพ.ราชบุรี
    ('ARA', 'Acute rheumatoid arthritis', 'ข้ออักเสบรูมาตอยด์', ['@M06.9'], ['M06.9']),  # รพ.ราชบุรี
    ('ARC', 'AIDS-related complex', 'กลุ่มอาการที่สัมพันธ์กับเอดส์', ['@B20-B24'], ['B24']),  # รพ.ราชบุรี
    ('ARI', 'Acute respiratory infection', 'การติดเชื้อทางเดินหายใจเฉียบพลัน', ['@J22', '@J06.9'], ['J22', 'J06.9']),  # รพ.ราชบุรี, รพ.ฟากท่า
    ('ASHD', 'Arteriosclerotic heart disease', 'โรคหัวใจจากหลอดเลือดแข็ง', ['@I25.1'], ['I25.1']),  # รพ.ราชบุรี
    ('ASCVD', 'Arteriosclerotic cardiovascular disease', 'โรคหัวใจและหลอดเลือดจากหลอดเลือดแข็ง', ['@I25.0', '@I25.1'], ['I25.0']),  # รพ.ราชบุรี
    ('ASO', 'Arteriosclerosis obliterans', 'หลอดเลือดแดงแข็งอุดตันที่แขนขา', ['@I70.2', '@I70.9'], ['I70.2']),  # รพ.ราชบุรี
    ('ASVD', 'Arteriosclerotic vascular disease', 'โรคหลอดเลือดแข็ง', ['@I70'], ['I70.9']),  # รพ.ราชบุรี
    ('ATL', 'Adult T-cell leukaemia/lymphoma', 'มะเร็งเม็ดเลือดขาว/ต่อมน้ำเหลืองชนิดทีเซลล์ในผู้ใหญ่', ['@C91.5'], ['C91.5']),  # รพ.ราชบุรี (แหล่งให้ C91.8 ใช้ C91.5 ตาม WHO)
    ('AVF', 'Arteriovenous fistula (acquired)', 'ทางเชื่อมหลอดเลือดแดงกับดำ (เกิดภายหลัง)', ['@I77.0'], ['I77.0']),  # รพ.ราชบุรี
    ('AVH', 'Acute viral hepatitis', 'ตับอักเสบจากไวรัสเฉียบพลัน', ['@B15-B17', '@B19.9'], ['B17.9']),  # รพ.ราชบุรี
    ('AVN', 'Avascular necrosis of bone', 'กระดูกตายจากขาดเลือด', ['@M87'], ['M87.9']),  # รพ.ราชบุรี
    ('BDR', 'Background diabetic retinopathy', 'เบาหวานขึ้นจอตาระยะต้น', ['@E10.3', '@E11.3', '@E14.3', '@H36.0'], ['E14.3', 'H36.0']),  # รพ.ราชบุรี
    ('BIH', 'Benign intracranial hypertension', 'ความดันในกะโหลกศีรษะสูงชนิดไม่ร้าย', ['@G93.2'], ['G93.2']),  # รพ.ราชบุรี
    ('BPI', 'Brachial plexus injury', 'การบาดเจ็บของร่างแหประสาทแขน', ['@S14.3', '@G54.0'], ['S14.3']),  # รพ.ราชบุรี
    ('CAO', 'Carotid artery occlusion', 'หลอดเลือดแดงคาโรติดอุดตัน', ['@I65.2'], ['I65.2']),  # รพ.ราชบุรี
    ('CBN', 'Contracture of bladder neck', 'คอกระเพาะปัสสาวะตีบ', ['@N32.0'], ['N32.0']),  # รพ.ราชบุรี
    ('CCL', 'Complete cleft lip', 'ปากแหว่งชนิดสมบูรณ์', ['@Q36', '@Q37'], []),  # รพ.ราชบุรี
    ('CCP', 'Complete cleft palate', 'เพดานโหว่ชนิดสมบูรณ์', ['@Q35', '@Q37'], []),  # รพ.ราชบุรี
    ('CIDP', 'Chronic inflammatory demyelinating polyneuropathy', 'ปลายประสาทอักเสบเรื้อรังชนิดปลอกประสาทเสื่อม', ['@G61.8'], ['G61.8']),  # รพ.ราชบุรี
    ('CPH', 'Chronic persistent hepatitis', 'ตับอักเสบเรื้อรังชนิดคงที่', ['@K73.0'], ['K73.0']),  # รพ.ราชบุรี
    ('CPM', 'Central pontine myelinolysis', 'ปลอกประสาทสมองส่วนพอนส์สลาย', ['@G37.2'], ['G37.2']),  # รพ.ราชบุรี
    ('DLE', 'Discoid lupus erythematosus', 'ลูปัสชนิดผื่นวงกลมที่ผิวหนัง', ['@L93.0'], ['L93.0']),  # รพ.ราชบุรี
    ('EMF', 'Endomyocardial fibrosis', 'พังผืดที่เยื่อบุและกล้ามเนื้อหัวใจ', ['@I42.3'], ['I42.3']),  # รพ.ราชบุรี
    ('ET', 'Esotropia', 'ตาเหล่เข้าใน', ['@H50.0'], []),  # รพ.ราชบุรี
    ('ET', 'Essential tremor', 'อาการสั่นไม่ทราบสาเหตุ', ['@G25.0'], []),  # ความหมายที่ใช้ทั่วไป
    ('ET', 'Essential thrombocythaemia', 'เกล็ดเลือดสูงชนิดปฐมภูมิ', ['@D47.3'], []),  # ความหมายที่ใช้ทั่วไป
    ('FCD', 'Fibrocystic disease (cystic fibrosis)', 'โรคซิสติกไฟโบรซิส', ['@E84'], []),  # รพ.ราชบุรี
    ('FCD', 'Fibrocystic disease of breast', 'เต้านมเป็นถุงน้ำและพังผืด', ['@N60.1'], []),  # ความหมายที่สอง
    ('GPI', 'General paresis of the insane', 'ซิฟิลิสระบบประสาทชนิดอัมพาตทั่วไป', ['@A52.1'], ['A52.1']),  # รพ.ราชบุรี
    ('IIH', 'Indirect inguinal hernia', 'ไส้เลื่อนขาหนีบชนิดอินไดเรกต์', ['@K40'], ['K40.9']),  # รพ.ราชบุรี, รพ.ฟากท่า
    ('IIH', 'Idiopathic intracranial hypertension', 'ความดันในกะโหลกศีรษะสูงไม่ทราบสาเหตุ', ['@G93.2'], []),  # ความหมายที่ใช้ทั่วไป
    ('IOFB', 'Intraocular foreign body', 'สิ่งแปลกปลอมในลูกตา', ['@S05.5', '@H44.6', '@H44.7'], ['S05.5']),  # รพ.ราชบุรี
    ('LVH', 'Left ventricular hypertrophy', 'หัวใจห้องล่างซ้ายโต', ['@I51.7'], ['I51.7']),  # รพ.ราชบุรี
    ('MCTD', 'Mixed connective tissue disease', 'โรคเนื้อเยื่อเกี่ยวพันผสม', ['@M35.1'], ['M35.1']),  # รพ.ราชบุรี (แหล่งให้ M35.9 ใช้ M35.1)
    ('NVG', 'Neovascular glaucoma', 'ต้อหินจากหลอดเลือดงอกใหม่', ['@H40.5'], ['H40.5']),  # รพ.ราชบุรี
    ('PCM', 'Protein-calorie malnutrition', 'ภาวะขาดโปรตีนและพลังงาน', ['@E40-E46'], ['E46']),  # รพ.ราชบุรี
    ('PSS', 'Progressive systemic sclerosis', 'โรคหนังแข็งทั่วร่างกาย', ['@M34.0'], ['M34.0']),  # รพ.ราชบุรี
    ('RPGN', 'Rapidly progressive glomerulonephritis', 'ไตอักเสบชนิดลุกลามเร็ว', ['@N01'], ['N01.9']),  # รพ.ราชบุรี
    ('SI', 'Stress incontinence', 'ปัสสาวะเล็ดเมื่อมีแรงดันในช่องท้อง', ['@N39.3'], ['N39.3']),  # รพ.ราชบุรี
    ('SRD', 'Serous retinal detachment', 'จอประสาทตาลอกชนิดมีน้ำใต้จอตา', ['@H33.2'], ['H33.2']),  # รพ.ราชบุรี
    ('TI', 'Tricuspid insufficiency', 'ลิ้นหัวใจไตรคัสปิดรั่ว', ['@I07.1', '@I36.1'], ['I07.1', 'I36.1']),  # รพ.ราชบุรี
    ('TO abscess', 'Tubo-ovarian abscess', 'ฝีที่ท่อนำไข่และรังไข่', ['@N70.0', '@N70.9'], ['N70.0']),  # รพ.ราชบุรี
    ('AODM', 'Adult-onset diabetes mellitus', 'เบาหวานที่เริ่มเป็นในผู้ใหญ่', ['@E11'], ['E11.9']),  # MedlinePlus
    ('PAT', 'Paroxysmal atrial tachycardia', 'หัวใจห้องบนเต้นเร็วเป็นพักๆ', ['@I47.1'], ['I47.1']),  # MedlinePlus
    ('XRT', 'Radiotherapy', 'รังสีรักษา', ['@Z51.0'], ['Z51.0']),  # MedlinePlus
    ('BBB', 'Bundle branch block', 'การนำไฟฟ้าหัวใจบล็อกแขนงบันเดิล', ['@I44.4-I44.7', '@I45.0-I45.2'], []),  # รพ.ฟากท่า
    ('BBBB', 'Bilateral bundle branch block', 'การนำไฟฟ้าหัวใจบล็อกทั้งสองแขนง', ['@I45.2', '@I45.3'], ['I45.2']),  # รพ.ฟากท่า
    ('IFG', 'Impaired fasting glucose', 'ระดับน้ำตาลขณะอดอาหารผิดปกติ', ['@R73.0', '@R73.9'], ['R73.0']),  # รพ.ฟากท่า
    ('IICP', 'Increased intracranial pressure', 'ความดันในกะโหลกศีรษะสูง', ['@G93.2', '@G93.6'], ['G93.2']),  # รพ.ฟากท่า
    ('MDR-TB', 'Multidrug-resistant tuberculosis', 'วัณโรคดื้อยาหลายขนาน', ['@U84.3', '@A15-A19'], ['U84.3']),  # รพ.ฟากท่า
    ('OHCA', 'Out-of-hospital cardiac arrest', 'หัวใจหยุดเต้นนอกโรงพยาบาล', ['@I46'], ['I46.9']),  # รพ.ฟากท่า
    ('PEA', 'Pulseless electrical activity', 'คลื่นไฟฟ้าหัวใจมีแต่คลำชีพจรไม่ได้', ['@I46'], ['I46.9']),  # รพ.ฟากท่า
    ('PU', 'Peptic ulcer', 'แผลเปปติก', ['@K25-K27'], ['K27.9']),  # รพ.ฟากท่า
    ('PVT', 'Paroxysmal ventricular tachycardia', 'หัวใจห้องล่างเต้นเร็วเป็นพักๆ', ['@I47.2'], []),  # รพ.ฟากท่า
    ('PVT', 'Portal vein thrombosis', 'หลอดเลือดดำพอร์ทัลอุดตัน', ['@I81'], []),  # ความหมายที่ใช้ทั่วไป
    ('VC', 'Vesical calculus', 'นิ่วในกระเพาะปัสสาวะ', ['@N21.0'], ['N21.0']),  # รพ.ฟากท่า
    ('UC', 'Ureteric calculus', 'นิ่วในท่อไต', ['@N20.1'], []),  # รพ.ฟากท่า ความหมายที่สอง (ความหมายแรก ulcerative colitis)
    ('VHD', 'Valvular heart disease', 'โรคลิ้นหัวใจ', ['@I05-I09', '@I34-I38'], []),  # รพ.ฟากท่า
    ('VIA', 'Visual inspection with acetic acid (cervical screening)', 'การตรวจคัดกรองมะเร็งปากมดลูกด้วยน้ำส้มสายชู', ['@Z12.4'], ['Z12.4']),  # รพ.ฟากท่า
    ('FLU', 'Influenza', 'ไข้หวัดใหญ่', ['@J09-J11'], ['J11.1']),  # รพ.ฟากท่า
    # ---- เพิ่ม 8 พ.ย. 2569: ข้อเสนอจากชีตผู้ใช้ (อนุมัติแล้ว) และคำไทยที่ coder พิมพ์แต่เว็บยังหาไม่เจอ ----
    ('HFREF', 'Heart failure with reduced ejection fraction', 'หัวใจล้มเหลวชนิดค่าการบีบตัว (EF) ลดลง', ['@I50'], ['I50.9', 'I50.1', 'I50.0']),  # ชีตผู้ใช้; WHO ICD-10 ไม่มีรหัสแยกตาม EF ยังไม่มี coder ตรวจ
    ('HFPEF', 'Heart failure with preserved ejection fraction', 'หัวใจล้มเหลวชนิดค่าการบีบตัว (EF) ปกติ', ['@I50'], ['I50.9', 'I50.1', 'I50.0']),  # ชีตผู้ใช้; WHO ICD-10 ไม่มีรหัสแยกตาม EF ยังไม่มี coder ตรวจ
    ('ไข้เลือดออก', 'Dengue / dengue haemorrhagic fever', 'ไข้เลือดออก / ไข้เด็งกี', ['@A97'], ['A97.1', 'A97.2', 'A97.0', 'A97.9']),  # คำไทย; ชื่อไทย TM ของ A97 คือ "ไข้เด็งกี" เดิมจึงขึ้น A48.4 ก่อน ลำดับตาม DHF/AHF ยังไม่มี coder ตรวจ
    ('ปอดอักเสบ|ปอดบวม', 'Pneumonia', 'ปอดอักเสบ / ปอดบวม', ['ปอดบวม', 'ปอดอักเสบ', '@J12-J18'], ['J18.9', 'J18.0', 'J15.9', 'J12.9']),  # คำไทย; TM ใช้คำว่า "ปอดบวม" เดิมจึงขึ้น B25.0 ก่อน ยังไม่มี coder ตรวจ
]

D9 = [
    ('CABG', 'Coronary artery bypass graft', 'ผ่าตัดทำทางเบี่ยงหลอดเลือดหัวใจ', ['@36.1'], ['36.10', '36.12', '36.13']),
    ('PCI|PTCA|POBA', 'Percutaneous coronary intervention', 'ขยายหลอดเลือดหัวใจผ่านสายสวน', ['@00.66', 'coronary angioplasty', '@36.0'], ['00.66']),
    ('STENT|DES|BMS', 'Coronary stent insertion', 'ใส่ขดลวดค้ำยันหลอดเลือดหัวใจ', ['@36.06', '@36.07', '@00.40-00.48'], ['36.07', '36.06']),
    ('CAG', 'Coronary angiography', 'ฉีดสีดูหลอดเลือดหัวใจ', ['coronary arteriography', '@88.55', '@88.56', '@88.57'], ['88.56', '88.57', '88.55']),
    ('CATH|LHC|RHC', 'Cardiac catheterization', 'สวนหัวใจ', ['cardiac catheterization', '@37.21', '@37.22', '@37.23'], ['37.22', '37.23']),
    ('PPM|PACEMAKER|TPM', 'Pacemaker insertion', 'ใส่เครื่องกระตุ้นหัวใจ', ['pacemaker', '@37.7', '@37.8'], ['37.81', '37.83', '37.78']),
    ('AICD|ICD', 'Automatic implantable cardioverter-defibrillator', 'ฝังเครื่องกระตุกหัวใจอัตโนมัติ', ['defibrillator', '@37.94'], ['37.94']),
    ('ICD|ICD DRAIN|CHEST DRAIN|ICD INSERTION', 'Intercostal chest drainage', 'ใส่ท่อระบายทรวงอก', ['intercostal catheter', '@34.04'], ['34.04']),
    ('CPR', 'Cardiopulmonary resuscitation', 'ช่วยฟื้นคืนชีพ', ['@99.60', '@99.63'], ['99.60']),
    ('DC SHOCK|CARDIOVERSION|DEFIB', 'Electrical cardioversion / countershock', 'กระตุกหัวใจด้วยไฟฟ้า', ['countershock', 'cardioversion', '@99.61', '@99.62'], ['99.62', '99.61']),
    ('ETT|ET|ET TUBE|INTUBATION|INTUBATE|ใส่ท่อช่วยหายใจ', 'Endotracheal intubation', 'ใส่ท่อช่วยหายใจ', ['endotracheal tube', '@96.04'], ['96.04']),  # + คำไทย (8 พ.ย. 2569) เดิม 96.04 ขึ้นอันดับ 4 หลัง 96.01-96.03
    ('MV|VENT|RESPIRATOR', 'Invasive mechanical ventilation', 'ใช้เครื่องช่วยหายใจ', ['invasive mechanical ventilation', '@96.7'], ['96.71', '96.72']),
    ('NIV|NIPPV|BIPAP|CPAP|HFNC', 'Non-invasive ventilation', 'เครื่องช่วยหายใจแบบไม่ใส่ท่อ', ['non-invasive', '@93.90', '@93.96'], ['93.90']),
    ('TT|TRACH|TRACHEOSTOMY', 'Tracheostomy', 'เจาะคอ', ['tracheostomy', '@31.1', '@31.2'], ['31.1', '31.29']),
    ('ERCP', 'Endoscopic retrograde cholangiopancreatography', 'ส่องกล้องตรวจท่อน้ำดีและตับอ่อน', ['ercp', 'retrograde cholangio', '@51.10', '@51.11', '@51.8'], ['51.10', '51.85', '51.87', '51.88']),
    ('EST', 'Endoscopic sphincterotomy', 'ตัดหูรูดท่อน้ำดีผ่านกล้อง', ['@51.85'], ['51.85']),
    ('EGD|UGIE|GASTROSCOPY|OGD', 'Esophagogastroduodenoscopy', 'ส่องกล้องทางเดินอาหารส่วนบน', ['esophagogastroduodenoscopy', '@45.13', '@45.16'], ['45.13', '45.16']),
    ('COLONOSCOPY|COLONO', 'Colonoscopy', 'ส่องกล้องลำไส้ใหญ่', ['colonoscopy', '@45.23', '@45.25'], ['45.23', '45.25']),
    ('EVL|EBL', 'Endoscopic variceal ligation', 'ผูกเส้นเลือดขอดหลอดอาหารผ่านกล้อง', ['@42.33', '@44.43'], ['42.33']),
    ('LC|LAP CHOLE|LAPAROSCOPIC CHOLECYSTECTOMY', 'Laparoscopic cholecystectomy', 'ผ่าตัดถุงน้ำดีผ่านกล้อง', ['@51.23'], ['51.23']),
    ('OC|OPEN CHOLE|CHOLECYSTECTOMY', 'Open cholecystectomy', 'ผ่าตัดถุงน้ำดีแบบเปิด', ['@51.22'], ['51.22']),
    ('LA|LAP APPY|LAPAROSCOPIC APPENDECTOMY', 'Laparoscopic appendectomy', 'ผ่าตัดไส้ติ่งผ่านกล้อง', ['@47.01'], ['47.01']),
    ('APPY|APPENDECTOMY|OA', 'Appendectomy', 'ผ่าตัดไส้ติ่ง', ['appendectomy', '@47.0'], ['47.09', '47.01']),
    ('EX LAP|EXPLORE LAP|EXPLORATORY LAPAROTOMY', 'Exploratory laparotomy', 'ผ่าตัดเปิดช่องท้องสำรวจ', ['exploratory laparotomy', '@54.11'], ['54.11']),
    ('HERNIORRHAPHY|HERNIA REPAIR', 'Hernia repair', 'ผ่าตัดซ่อมไส้เลื่อน', ['repair of inguinal hernia', 'hernia', '@53'], ['53.00', '53.05']),
    ('TAH', 'Total abdominal hysterectomy', 'ตัดมดลูกทางหน้าท้อง', ['@68.4'], ['68.49', '68.41']),
    ('TLH', 'Total laparoscopic hysterectomy', 'ตัดมดลูกผ่านกล้อง', ['@68.41'], ['68.41']),
    ('LAVH', 'Laparoscopically assisted vaginal hysterectomy', 'ตัดมดลูกทางช่องคลอดโดยใช้กล้องช่วย', ['@68.51'], ['68.51']),
    ('TVH|VH|VAGINAL HYSTERECTOMY', 'Vaginal hysterectomy', 'ตัดมดลูกทางช่องคลอด', ['@68.5'], ['68.59', '68.51']),
    ('BSO', 'Bilateral salpingo-oophorectomy', 'ตัดรังไข่และท่อนำไข่ทั้งสองข้าง', ['@65.6'], ['65.61', '65.63']),
    ('USO|RSO|LSO', 'Unilateral salpingo-oophorectomy', 'ตัดรังไข่และท่อนำไข่ข้างเดียว', ['@65.4'], ['65.49', '65.41']),
    ('D&C|D/C|DC|D AND C', 'Dilation and curettage', 'ขูดมดลูก', ['dilation and curettage', '@69.0'], ['69.09', '69.02']),
    ('MVA|VACUUM ASPIRATION', 'Manual vacuum aspiration', 'ดูดโพรงมดลูก', ['aspiration curettage', '@69.5'], ['69.52', '69.51', '69.59']),
    ('C/S|CS|LSCS|LTCS|CESAREAN|CAESAREAN|ผ่าคลอด|ผ่าตัดคลอด', 'Cesarean section', 'ผ่าตัดคลอด', ['cesarean', '@74'], ['74.1', '74.0', '74.99']),  # + คำไทย ผ่าคลอด (8 พ.ย. 2569) ชื่อไทย TM ใช้ "ผ่าตัดคลอด"
    ('TR|TL|TUBAL|TUBAL RESECTION|TUBAL LIGATION|STERILIZATION', 'Tubal sterilization', 'ทำหมันหญิง', ['@66.2', '@66.3'], ['66.32', '66.39', '66.29']),
    ('VASECTOMY|MALE STERILIZATION', 'Vasectomy', 'ทำหมันชาย', ['vasectomy', '@63.73'], ['63.73']),
    ('NL|NSD|NVD|SVD|NORMAL LABOR|คลอดปกติ', 'Assisted spontaneous delivery', 'คลอดปกติ', ['@73.59', '@73.6'], ['73.59', '73.6']),  # + คำไทย คลอดปกติ (8 พ.ย. 2569) เดิมไม่พบรหัส
    ('EPISIOTOMY|EPIS', 'Episiotomy', 'ตัดฝีเย็บ', ['episiotomy', '@73.6'], ['73.6']),
    ('V/E|VE|VACUUM', 'Vacuum extraction', 'คลอดด้วยเครื่องดูดสุญญากาศ', ['vacuum extraction', '@72.7'], ['72.79', '72.71']),
    ('F/E|FE|FORCEPS', 'Forceps delivery', 'คลอดด้วยคีม', ['forceps', '@72.0-72.4'], ['72.0', '72.1']),
    ('I&D|I/D|ID|I AND D', 'Incision and drainage', 'ผ่าระบายหนอง', ['incision with drainage', '@86.04'], ['86.04']),
    ('ORIF', 'Open reduction with internal fixation', 'ผ่าตัดจัดกระดูกและยึดตรึงภายใน', ['@79.3'], ['79.35', '79.36', '79.32']),
    ('CRIF|CRPP', 'Closed reduction with internal fixation', 'จัดกระดูกแบบปิดและยึดตรึงภายใน', ['@79.1'], ['79.15', '79.12']),
    ('CR|CLOSED REDUCTION', 'Closed reduction of fracture', 'จัดกระดูกแบบปิด', ['@79.0', '@79.7'], ['79.02', '79.03']),
    ('ORIF DISLOCATION|OR DISLOCATION', 'Open reduction of dislocation', 'ผ่าตัดจัดข้อเคลื่อน', ['@79.8'], []),
    ('ExFix|EX FIX|EXTERNAL FIXATION', 'External fixation', 'ยึดตรึงกระดูกภายนอก', ['external fixator', '@78.1'], ['78.15', '78.17']),
    ('TKA|TKR', 'Total knee replacement', 'ผ่าตัดเปลี่ยนข้อเข่าเทียม', ['@81.54'], ['81.54']),
    ('THA|THR', 'Total hip replacement', 'ผ่าตัดเปลี่ยนข้อสะโพกเทียม', ['@81.51'], ['81.51']),
    ('BHA|HEMIARTHROPLASTY|HA', 'Partial hip replacement (hemiarthroplasty)', 'ผ่าตัดเปลี่ยนข้อสะโพกเทียมบางส่วน', ['@81.52'], ['81.52']),
    ('AKA|BKA|AMPUTATION|BK|AK', 'Amputation of lower limb', 'ตัดขา', ['amputation', '@84.1'], ['84.15', '84.17']),
    ('TURP', 'Transurethral resection of prostate', 'ผ่าตัดต่อมลูกหมากผ่านท่อปัสสาวะ', ['@60.2'], ['60.29']),
    ('TURBT', 'Transurethral resection of bladder tumour', 'ผ่าตัดเนื้องอกกระเพาะปัสสาวะผ่านท่อปัสสาวะ', ['@57.4'], ['57.49']),
    ('PCNL|PCNL STONE', 'Percutaneous nephrolithotomy', 'ผ่าตัดนิ่วในไตผ่านผิวหนัง', ['@55.04', '@55.03'], ['55.04']),
    ('PCN', 'Percutaneous nephrostomy', 'เจาะไตระบายปัสสาวะผ่านผิวหนัง', ['@55.03'], ['55.03']),
    ('URS|URSL|URETEROSCOPY', 'Ureteroscopy', 'ส่องกล้องท่อไต', ['@56.31', '@56.0'], ['56.31', '56.0']),
    ('ESWL', 'Extracorporeal shockwave lithotripsy', 'สลายนิ่วด้วยคลื่นกระแทก', ['@98.51', '@98.52', '@98.59'], ['98.51']),
    ('DJ|DJ STENT|URETERAL STENT', 'Ureteral stent (catheter)', 'ใส่สายระบายท่อไต', ['@59.8'], ['59.8']),
    ('FOLEY|RETAINED CATH|CATH URINE', 'Indwelling urinary catheter', 'ใส่สายสวนปัสสาวะ', ['@57.94'], ['57.94']),
    ('EVD|VENTRICULOSTOMY', 'External ventricular drain', 'ใส่สายระบายน้ำในโพรงสมอง', ['@02.21', '@02.2'], ['02.21']),
    ('VP SHUNT|VPS', 'Ventriculoperitoneal shunt', 'ใส่ท่อระบายน้ำจากโพรงสมองสู่ช่องท้อง', ['@02.34'], ['02.34']),
    ('CRANI|CRANIOTOMY|CRANIECTOMY', 'Craniotomy / craniectomy', 'ผ่าตัดเปิดกะโหลกศีรษะ', ['@01.2'], ['01.24', '01.25']),
    ('PHACO', 'Phacoemulsification', 'สลายต้อกระจกด้วยคลื่นเสียงความถี่สูง', ['@13.41'], ['13.41']),
    ('IOL', 'Intraocular lens insertion', 'ใส่เลนส์แก้วตาเทียม', ['@13.7'], ['13.71', '13.72']),
    ('ECCE|ICCE|MSICS', 'Extracapsular cataract extraction', 'ผ่าตัดต้อกระจกแบบนอกถุงเลนส์', ['@13.5', '@13.1'], ['13.59', '13.19']),
    ('HD|ฟอกเลือด|ฟอกไต', 'Hemodialysis', 'ฟอกเลือดด้วยเครื่องไตเทียม', ['@39.95'], ['39.95']),  # + คำไทย ฟอกเลือด (8 พ.ย. 2569) เดิม 39.95 ขึ้นอันดับ 5
    ('PD|CAPD|APD', 'Peritoneal dialysis', 'ล้างไตทางช่องท้อง', ['@54.98'], ['54.98']),
    ('TK|TENCKHOFF|CAPD CATHETER', 'Peritoneal dialysis catheter insertion', 'ใส่สายล้างไตทางช่องท้อง', ['@54.93'], ['54.93']),
    ('AVF|AVG', 'Arteriovenous fistula for dialysis', 'ผ่าตัดทำเส้นฟอกไต', ['@39.27', '@39.93'], ['39.27']),
    ('DLC|PERM CATH|HD CATH|QUINTON', 'Dialysis venous catheter', 'ใส่สายสวนหลอดเลือดดำเพื่อฟอกไต', ['@38.95', '@38.93'], ['38.95', '38.93']),
    ('CVC|CVP|CENTRAL LINE|PICC', 'Central venous catheter', 'ใส่สายสวนหลอดเลือดดำส่วนกลาง', ['@38.93', '@38.97'], ['38.93', '38.97']),
    ('A-LINE|A LINE|ART LINE', 'Arterial line', 'ใส่สายสวนหลอดเลือดแดง', ['@38.91'], ['38.91']),
    ('NG|NG TUBE|NGT|OG|OGT', 'Nasogastric tube insertion', 'ใส่สายให้อาหารทางจมูก', ['@96.07', '@96.6'], ['96.07', '96.6']),
    ('PEG|GASTROSTOMY', 'Percutaneous endoscopic gastrostomy', 'เจาะกระเพาะอาหารผ่านกล้อง', ['@43.11', '@43.19'], ['43.11']),
    ('PRC|LPRC|BT|BLOOD TRANSFUSION|PRBC', 'Transfusion of packed red cells', 'ให้เลือดชนิดเม็ดเลือดแดงอัดแน่น', ['@99.04'], ['99.04']),
    ('FFP|PLASMA', 'Transfusion of plasma', 'ให้พลาสมา', ['@99.07', 'plasma'], ['99.07']),
    ('PLT|PC|SDP|PLATELET', 'Transfusion of platelets', 'ให้เกล็ดเลือด', ['@99.05'], ['99.05']),
    ('CRYO', 'Transfusion of cryoprecipitate', 'ให้ไครโอ', ['@99.06', '@99.07'], ['99.07']),
    ('CT|CT SCAN', 'Computerized tomography', 'เอกซเรย์คอมพิวเตอร์', ['computerized axial tomography', 'computerized tomography', '@87.03', '@87.41', '@87.71', '@88.01', '@88.38'], ['87.03', '87.41', '88.01']),
    ('MRI', 'Magnetic resonance imaging', 'เอ็มอาร์ไอ', ['magnetic resonance imaging', '@88.9'], ['88.91', '88.93']),
    ('US|U/S|USG|ULTRASOUND', 'Diagnostic ultrasound', 'อัลตราซาวด์', ['diagnostic ultrasound', '@88.7'], ['88.76', '88.78']),
    ('ECHO|TTE|TEE', 'Echocardiography', 'อัลตราซาวด์หัวใจ', ['@88.72'], ['88.72']),
    ('EKG|ECG', 'Electrocardiogram', 'คลื่นไฟฟ้าหัวใจ', ['@89.52'], ['89.52']),
    ('EEG', 'Electroencephalogram', 'คลื่นไฟฟ้าสมอง', ['@89.14'], ['89.14']),
    ('CXR|FILM CHEST', 'Chest x-ray', 'เอกซเรย์ทรวงอก', ['@87.44', '@87.49'], ['87.44']),
    ('KUB', 'X-ray of kidney, ureter and bladder', 'เอกซเรย์ระบบทางเดินปัสสาวะ', ['@87.79', '@87.73'], ['87.79']),
    ('IVP', 'Intravenous pyelogram', 'ฉีดสีดูไต', ['@87.73'], ['87.73']),
    ('BMA|BM BX|BM', 'Bone marrow aspiration / biopsy', 'เจาะไขกระดูก', ['bone marrow', '@41.31'], ['41.31', '41.38']),
    ('LP|SPINAL TAP', 'Lumbar puncture', 'เจาะน้ำไขสันหลัง', ['@03.31'], ['03.31']),
    ('TAP|THORACENTESIS', 'Thoracentesis', 'เจาะระบายน้ำในช่องเยื่อหุ้มปอด', ['thoracentesis', '@34.91'], ['34.91']),
    ('PARACENTESIS|ABD TAP', 'Paracentesis', 'เจาะระบายน้ำในช่องท้อง', ['@54.91'], ['54.91']),
    ('MRM', 'Modified radical mastectomy', 'ผ่าตัดเต้านมแบบถอนรากถอนโคนดัดแปลง', ['@85.43', '@85.44'], ['85.43', '85.44']),
    ('WLE|LUMPECTOMY', 'Wide / local excision of breast lesion', 'ผ่าตัดเนื้องอกเต้านมออกเฉพาะที่', ['@85.21', '@85.2'], ['85.21']),
    ('FNA|FNAB', 'Fine needle aspiration / biopsy', 'เจาะดูดด้วยเข็มเล็ก', ['aspiration biopsy', 'needle'], []),
    ('BX|BIOPSY', 'Biopsy', 'ตัดชิ้นเนื้อตรวจ', ['biopsy'], []),
    ('STSG|FTSG|SKIN GRAFT', 'Skin graft', 'ปลูกถ่ายผิวหนัง', ['skin graft', '@86.6'], ['86.69', '86.63']),
    ('DEBRIDEMENT|DEBRIDE', 'Debridement', 'ตัดเนื้อตาย', ['debridement', '@86.22', '@86.28'], ['86.22', '86.28']),
    ('CIRCUM|CIRCUMCISION', 'Circumcision', 'ขลิบหนังหุ้มปลาย', ['@64.0'], ['64.0']),
    ('T&A|TA|TONSILLECTOMY', 'Tonsillectomy (with adenoidectomy)', 'ผ่าตัดต่อมทอนซิล', ['@28.2', '@28.3'], ['28.3', '28.2']),
    ('FESS|ESS', 'Functional endoscopic sinus surgery', 'ผ่าตัดไซนัสผ่านกล้อง', ['@22.6', '@22.5'], []),
    ('MYRINGOTOMY|VT|TYMPANOSTOMY', 'Myringotomy with tube insertion', 'เจาะแก้วหูใส่ท่อ', ['@20.01', '@20.0'], ['20.01']),
    ('SUTURE|STITCH|REPAIR WOUND', 'Suture of skin and subcutaneous tissue', 'เย็บแผล', ['suture of skin', '@86.59'], ['86.59']),
    ('NEBULIZER|NB|INHALATION', 'Inhalation therapy', 'พ่นยา', ['@93.94'], ['93.94']),
    ('O2|OXYGEN', 'Oxygen therapy', 'ให้ออกซิเจน', ['@93.96'], ['93.96']),
    ('TPN|PN', 'Parenteral nutrition', 'ให้อาหารทางหลอดเลือดดำ', ['@99.15'], ['99.15']),
    ('CHEMO|CMT', 'Chemotherapy injection', 'ให้ยาเคมีบำบัด', ['@99.25'], ['99.25']),
    ('RT|RADIOTHERAPY', 'Radiotherapy', 'ฉายรังสีรักษา', ['@92.2'], ['92.29', '92.24']),
    ('PT|PHYSIO', 'Physical therapy', 'กายภาพบำบัด', ['@93.3', '@93.1', '@93.0'], ['93.39']),
    ('ECT', 'Electroconvulsive therapy', 'รักษาด้วยไฟฟ้า', ['@94.27'], ['94.27']),
    ('IVIG', 'Immunoglobulin injection', 'ให้อิมมูโนโกลบูลิน', ['@99.14'], ['99.14']),
    ('THROMBOLYSIS|RTPA|SK|TPA', 'Thrombolytic infusion', 'ให้ยาละลายลิ่มเลือด', ['@99.10'], ['99.10']),
    ('HBOT|HYPERBARIC', 'Hyperbaric oxygenation', 'ออกซิเจนความดันสูง', ['@93.95'], ['93.95']),
    ('PRP|LASER RETINA', 'Retinal photocoagulation', 'ยิงเลเซอร์จอตา', ['@14.3', '@14.2'], ['14.34']),
    ('DENTAL|SCALING', 'Dental scaling', 'ขูดหินปูน', ['@96.54'], ['96.54']),
    # ---- added from the medical-terms glossary (cleaned.xlsx, 2026-11) and from website suggestions
    ('APR|A-P RESECTION', 'Abdominoperineal resection of rectum', 'ผ่าตัดไส้ตรงผ่านทางหน้าท้องและฝีเย็บ', ['@48.5'], ['48.52', '48.51']),
    ('A-P REPAIR|AP REPAIR', 'Anterior and posterior colporrhaphy', 'ซ่อมผนังช่องคลอดด้านหน้าและด้านหลัง', ['@70.50', '@70.53'], ['70.50']),
    ('A-V FISTULA|AV FISTULA|A.V.F.', 'Arteriovenous fistula for dialysis', 'ผ่าตัดทำเส้นฟอกไต', ['@39.27', '@39.93'], ['39.27']),
    ('A-V SHUNT|AV SHUNT', 'Arteriovenous shunt for dialysis', 'ใส่ท่อเชื่อมหลอดเลือดแดงกับหลอดเลือดดำเพื่อฟอกไต', ['@39.27', '@39.93'], ['39.93', '39.27']),
    ('AID|AIH|IUI', 'Artificial insemination', 'ผสมเทียม', ['@69.92'], ['69.92']),
    ('ALND', 'Axillary lymph node dissection', 'เลาะต่อมน้ำเหลืองรักแร้', ['@40.51', '@40.23'], ['40.51', '40.23']),
    ('BE|B.E', 'Barium enema', 'สวนแป้งแบเรียมเอกซเรย์ลำไส้ใหญ่', ['@87.64'], ['87.64']),
    ('BMT|HSCT', 'Bone marrow / haematopoietic stem cell transplant', 'ปลูกถ่ายไขกระดูกหรือเซลล์ต้นกำเนิดเม็ดเลือด', ['@41.0'], ['41.00', '41.04', '41.05']),
    ('CBI', 'Continuous bladder irrigation', 'ล้างกระเพาะปัสสาวะต่อเนื่อง', ['@96.48'], ['96.48']),
    ('CCPD|IPD', 'Peritoneal dialysis', 'ล้างไตทางช่องท้อง', ['@54.98'], ['54.98']),
    ('CRRT|CVVH|CVVHD|CVVHDF', 'Continuous renal replacement therapy', 'บำบัดทดแทนไตต่อเนื่อง', ['@39.95'], ['39.95']),
    ('CPPB', 'Continuous positive pressure breathing', 'ช่วยหายใจด้วยแรงดันบวกต่อเนื่อง', ['@93.90'], ['93.90']),
    ('CST|OCT', 'Contraction stress test (oxytocin challenge test)', 'ทดสอบหัวใจทารกขณะมดลูกหดรัดตัว', ['@75.34'], ['75.34']),
    ('OCT', 'Optical coherence tomography (intravascular)', 'ถ่ายภาพภายในหลอดเลือดด้วยแสง', ['@38.24', '@38.25'], ['38.24', '38.25']),
    ('NST', 'Non-stress test', 'ตรวจการตอบสนองของหัวใจทารก', ['@75.34'], ['75.34']),
    ('DCR', 'Dacryocystorhinostomy', 'ผ่าตัดเชื่อมถุงน้ำตากับโพรงจมูก', ['@09.81'], ['09.81']),
    ('D&E|D AND E', 'Dilation and evacuation', 'ขยายปากมดลูกและเอาชิ้นส่วนการตั้งครรภ์ออก', ['@69.01', '@69.51'], ['69.01', '69.51']),
    ('DTP|DPT', 'DTP vaccine', 'วัคซีนคอตีบ บาดทะยัก ไอกรน', ['@99.39'], ['99.39']),
    ('MMR', 'MMR vaccine', 'วัคซีนหัด คางทูม หัดเยอรมัน', ['@99.48'], ['99.48']),
    ('EMG', 'Electromyography', 'ตรวจคลื่นไฟฟ้ากล้ามเนื้อ', ['@93.08'], ['93.08']),
    ('NCV|NCS', 'Nerve conduction study', 'ตรวจการนำกระแสประสาท', ['@89.15'], ['89.15']),
    ('EUS', 'Endoscopic ultrasonography', 'ส่องกล้องตรวจคลื่นเสียงความถี่สูง', ['@88.74'], ['88.74']),
    ('EXPLOR LAP', 'Exploratory laparotomy', 'ผ่าตัดเปิดช่องท้องสำรวจ', ['exploratory laparotomy', '@54.11'], ['54.11']),
    ('LAP', 'Laparotomy', 'ผ่าตัดเปิดช่องท้อง', ['@54.1'], ['54.11', '54.19']),
    ('LAP', 'Laparoscopy', 'ส่องกล้องตรวจช่องท้อง', ['@54.21'], ['54.21']),
    ('FNAC', 'Fine needle aspiration cytology', 'เจาะดูดเซลล์ด้วยเข็มเล็ก', ['aspiration biopsy', 'needle'], []),
    ('IABP', 'Intra-aortic balloon pump', 'ใส่บอลลูนช่วยการบีบตัวของหัวใจ', ['@37.61'], ['37.61']),
    ('IVAD', 'Implanted vascular access device', 'ฝังอุปกรณ์เข้าถึงหลอดเลือด', ['@86.07'], ['86.07']),
    ('IVC', 'Intravenous cholangiography', 'เอกซเรย์ท่อน้ำดีโดยฉีดสีทางหลอดเลือดดำ', ['@87.52'], ['87.52']),
    ('IUD|IUCD', 'Intrauterine contraceptive device', 'ใส่หรือถอดห่วงอนามัย', ['@69.7', '@97.71'], ['69.7', '97.71']),
    ('LEEP|LLETZ', 'Loop electrosurgical excision of cervix', 'ตัดปากมดลูกด้วยห่วงลวดไฟฟ้า', ['@67.32'], ['67.32']),
    ('LASIK', 'Laser in situ keratomileusis', 'ผ่าตัดแก้ไขสายตาด้วยเลเซอร์ (เลสิก)', ['@11.71'], ['11.71']),
    ('MMS', 'Mohs micrographic surgery', 'ผ่าตัดมะเร็งผิวหนังแบบโมส์', ['@86.24'], ['86.24']),
    ('PEJ', 'Percutaneous endoscopic jejunostomy', 'ทำรูเปิดลำไส้เล็กส่วนกลางผ่านกล้อง', ['@46.32'], ['46.32']),
    ('PTC', 'Percutaneous transhepatic cholangiography', 'เอกซเรย์ท่อน้ำดีโดยแทงเข็มผ่านผิวหนังเข้าตับ', ['@87.51'], ['87.51']),
    ('PKP', 'Penetrating keratoplasty', 'ปลูกถ่ายกระจกตาทุกชั้น', ['@11.63', '@11.64'], ['11.64']),
    ('RK', 'Radial keratotomy', 'กรีดกระจกตาแนวรัศมี', ['@11.75'], ['11.75']),
    ('RND', 'Radical neck dissection', 'เลาะต่อมน้ำเหลืองที่คอแบบถอนรากถอนโคน', ['@40.4'], ['40.41', '40.42', '40.40']),
    ('RP', 'Retrograde pyelography', 'ฉีดสีย้อนเข้ากรวยไต', ['@87.74'], ['87.74']),
    ('SO', 'Salpingo-oophorectomy', 'ตัดรังไข่และท่อนำไข่', ['@65.4', '@65.6'], ['65.49', '65.61']),
    ('BILAT SO', 'Bilateral salpingo-oophorectomy', 'ตัดรังไข่และท่อนำไข่ทั้งสองข้าง', ['@65.6'], ['65.61', '65.63']),
    ('SLNB', 'Sentinel lymph node biopsy', 'ตัดต่อมน้ำเหลืองเซนทิเนลตรวจ', ['@40.23', '@40.11'], ['40.23', '40.11']),
    ('SMR', 'Submucous resection of nasal septum', 'ตัดผนังกั้นจมูกใต้เยื่อบุ', ['@21.5'], ['21.5']),
    ('SPP', 'Suprapubic prostatectomy', 'ผ่าตัดต่อมลูกหมากทางเหนือหัวหน่าว', ['@60.3'], ['60.3']),
    ('TAL', 'Tendo-Achilles lengthening', 'ยืดเอ็นร้อยหวาย', ['@83.85', '@83.11'], ['83.85']),
    ('TUR', 'Transurethral resection', 'ผ่าตัดผ่านทางท่อปัสสาวะ', ['@60.2', '@57.49'], ['60.29', '57.49']),
    ('VA SHUNT', 'Ventriculoatrial shunt', 'ใส่ท่อระบายน้ำจากโพรงสมองสู่หัวใจ', ['@02.32'], ['02.32']),
    ('V-P SHUNT', 'Ventriculoperitoneal shunt', 'ใส่ท่อระบายน้ำจากโพรงสมองสู่ช่องท้อง', ['@02.34'], ['02.34']),
    ('CBT', 'Cognitive behavioural therapy', 'การบำบัดความคิดและพฤติกรรม', ['@94.33'], ['94.33']),
    ('PFT', 'Pulmonary function test', 'ตรวจสมรรถภาพปอด', ['@89.37', '@89.38'], ['89.38', '89.37']),
    ('ABG', 'Arterial blood gas', 'ตรวจก๊าซในเลือดแดง', ['@89.65'], ['89.65']),
    ('WB', 'Whole blood transfusion', 'ให้เลือดครบส่วน', ['@99.03'], ['99.03']),
    ('USWA', 'Ultrasound of whole abdomen', 'อัลตราซาวด์ช่องท้องทั้งหมด', ['@88.76'], ['88.76']),
    ('REDUCE COLOSTOMY|CLOSE COLOSTOMY|CLOSURE COLOSTOMY', 'Closure of colostomy', 'ปิดทวารเทียม', ['@46.52'], ['46.52']),
    ('OAE', 'Otoacoustic emissions (hearing screening)', 'การตรวจการได้ยินด้วยเสียงสะท้อนจากหูชั้นใน (OAE)', ['@95.43', 'audiological evaluation'], ['95.43']),
    # ---- เพิ่มจากร่างรวม 7 แหล่ง (claude/abbr-handoff.md, 2026-11) รหัสผูกโดย Claude รอทีมแพทย์/coder ตรวจ ----
    ('TUR-P', 'Transurethral resection of prostate', 'ผ่าตัดต่อมลูกหมากทางท่อปัสสาวะ', ['@60.2'], ['60.2']),
    ('TUR-B|TUR-BT', 'Transurethral resection of bladder tumor', 'ผ่าตัดก้อนกระเพาะปัสสาวะทางท่อปัสสาวะ', ['@57.49'], ['57.49']),
    ('AVR|MVR|TVR', 'Heart valve replacement (aortic/mitral/tricuspid)', 'ผ่าตัดเปลี่ยนลิ้นหัวใจ', ['@35.2'], ['35.2']),
    ('STAH', 'Subtotal abdominal hysterectomy', 'ผ่าตัดมดลูกออกบางส่วนทางหน้าท้อง', ['@68.3'], ['68.3']),
    ('ARM', 'Artificial rupture of membranes', 'เจาะถุงน้ำคร่ำ', ['@73.0'], ['73.0']),
    ('MR', 'Menstrual regulation', 'ดูดประจำเดือน/ยุติการตั้งครรภ์ระยะแรก', ['@69.6'], ['69.6']),
    ('DHS', 'Dynamic hip screw', 'ยึดตรึงกระดูกสะโพกด้วยสกรูไดนามิก', ['@79.35'], ['79.35']),
    # ---- เพิ่ม 4 พ.ย. 2569 (รอบสอง) ----
    ('TAH-BSO|TAH/BSO|TAHBSO', 'Total abdominal hysterectomy with bilateral salpingo-oophorectomy', 'ผ่าตัดมดลูกออกทั้งหมดพร้อมท่อนำไข่และรังไข่สองข้าง', ['@68.4', '@65.6'], ['68.49', '65.61']),  # ลงสองรหัสคู่กัน
    ('TAS', 'Transabdominal sonography (pelvic ultrasound)', 'อัลตราซาวด์อุ้งเชิงกรานทางหน้าท้อง', ['@88.79', '@88.78', '@88.76'], ['88.79', '88.78']),  # ไม่ตั้งครรภ์ 88.79, ตั้งครรภ์ 88.78; ความหมายนี้พบแหล่งเดียว ให้ทีมยืนยัน
    ('BSO', 'Bilateral simple orchiectomy', 'ผ่าตัดอัณฑะออกทั้งสองข้าง', ['@62.41'], []),  # ความหมายที่สอง ตามรายการ รพ.ราชบุรี (62.41)
    # ---- เพิ่ม 4 พ.ย. 2569 จากแหล่งที่ผู้ใช้ให้ (รพ.ราชบุรี, รพ.ฟากท่า, MedlinePlus) รหัสตรวจกับ WHO 2016 แล้ว รอทีมตรวจ ----
    ('A/T', 'Autologous blood transfusion', 'การให้เลือดของตนเองที่เก็บไว้', ['@99.02'], ['99.02']),  # รพ.ราชบุรี
    ('AIP', 'Argon laser iridoplasty', 'การผ่าตัดตกแต่งม่านตาด้วยเลเซอร์อาร์กอน', ['@12.39'], ['12.39']),  # รพ.ราชบุรี
    ('ALI', 'Argon laser iridotomy / iridectomy', 'การเจาะม่านตาด้วยเลเซอร์อาร์กอน', ['@12.12', '@12.14'], ['12.12']),  # รพ.ราชบุรี (แหล่งให้ 12.41 ใช้ 12.12/12.14)
    ('PI|LPI', 'Peripheral iridotomy / iridectomy', 'การเจาะหรือตัดม่านตาส่วนริม', ['@12.12', '@12.14'], ['12.14', '12.12']),  # รพ.ราชบุรี
    ('ALP', 'Argon laser photocoagulation', 'การจี้จอตาด้วยเลเซอร์อาร์กอน', ['@14.24'], ['14.24']),  # รพ.ราชบุรี
    ('ALT', 'Argon laser trabeculoplasty', 'การยิงเลเซอร์อาร์กอนที่ทางระบายน้ำในลูกตา', ['@12.59'], ['12.59']),  # รพ.ราชบุรี
    ('APLD', 'Automated percutaneous lumbar discectomy', 'การตัดหมอนรองกระดูกเอวผ่านผิวหนังด้วยเครื่องอัตโนมัติ', ['@80.59'], ['80.59']),  # รพ.ราชบุรี (แหล่งให้ 77.69 ใช้ 80.59)
    ('LLC|SAC', 'Application of cast (long leg / short arm)', 'การใส่เฝือก', ['@93.53'], ['93.53']),  # รพ.ราชบุรี
    ('AROM', 'Artificial rupture of membranes', 'การเจาะถุงน้ำคร่ำ', ['@73.0'], ['73.09']),  # รพ.ฟากท่า
    ('XRT', 'Radiotherapy', 'รังสีรักษา', ['@92.2'], ['92.29']),  # MedlinePlus
    ('SSE', 'Soap suds enema', 'การสวนอุจจาระด้วยน้ำสบู่', ['@96.39'], ['96.39']),  # รพ.ฟากท่า
    # ---- เพิ่ม 8 พ.ย. 2569: ข้อเสนอจากชีตผู้ใช้ (อนุมัติแล้ว) ----
    ('USG OB|U/S OB|US OB|ULTRASOUND OB', 'Obstetric ultrasound (diagnostic ultrasound of gravid uterus)', 'อัลตราซาวด์ทางสูติกรรม (มดลูกขณะตั้งครรภ์)', ['@88.78'], ['88.78']),  # ชีตผู้ใช้; รูปคำย่อตามรายการ US|U/S|USG|ULTRASOUND
    ('UAC', 'Umbilical artery catheterization', 'ใส่สายสวนหลอดเลือดแดงสะดือ', ['@38.91'], ['38.91']),  # ชีตผู้ใช้; ดัชนี ICD-9-CM ไม่มี umbilical artery แยก ใช้ Catheterization, artery 38.91
    ('UVC', 'Umbilical vein catheterization', 'ใส่สายสวนหลอดเลือดดำสะดือ', ['@38.92'], ['38.92']),  # ชีตผู้ใช้
    ('SLS', 'Short leg splint (application of splint)', 'ใส่เฝือกอ่อนใต้เข่า', ['@93.54'], ['93.54']),  # ชีตผู้ใช้
    ('IOP|ความดันตา|วัดความดันตา', 'Tonometry (intraocular pressure measurement)', 'วัดความดันลูกตา', ['@89.11'], ['89.11']),  # ชีตผู้ใช้; ชื่อไทย TM คือ "การวัดความดันลูกตา" คำว่า ความดันตา จึงหาไม่เจอ
    ('PAP SMEAR|PAP|แปปสเมียร์', 'Papanicolaou (Pap) smear, female genital tract', 'ตรวจแปปสเมียร์ (เซลล์ปากมดลูก)', ['@91.46', 'papanicolaou smear'], ['91.46']),  # ชีตผู้ใช้; รหัส 9x.x6 ทุกตัวมีคำนี้ เดิม 90.06 จึงขึ้นก่อน
]

SPELL = [  # American -> British; ICD-10 is British, ICD-9-CM is American
    ('anemi', 'anaemi'), ('ischemi', 'ischaemi'), ('hemorrh', 'haemorrh'), ('hematoma', 'haematoma'), ('hemato', 'haemato'),
    ('hemoglobin', 'haemoglobin'), ('hemophil', 'haemophil'), ('hemolyt', 'haemolyt'), ('hemothorax', 'haemothorax'),
    ('hematuria', 'haematuria'), ('hemoptysis', 'haemoptysis'), ('hemangioma', 'haemangioma'),
    ('edema', 'oedema'), ('esophag', 'oesophag'), ('diarrhea', 'diarrhoea'), ('leukemi', 'leukaemi'),
    ('tumor', 'tumour'), ('pediatric', 'paediatric'), ('orthopedic', 'orthopaedic'), ('gynecolog', 'gynaecolog'),
    ('estrogen', 'oestrogen'), ('behavior', 'behaviour'), ('color', 'colour'), ('labor', 'labour'), ('apnea', 'apnoea'),
    ('dyspnea', 'dyspnoea'), ('tachypnea', 'tachypnoea'), ('celiac', 'coeliac'), ('cesarean', 'caesarean'),
    ('fetal', 'fetal'), ('septicemia', 'septicaemia'), ('glycemi', 'glycaemi'), ('kalemia', 'kalaemia'), ('natremia', 'natraemia'),
    ('calcemia', 'calcaemia'), ('lipidemia', 'lipidaemia'), ('cholesterolemia', 'cholesterolaemia'), ('uremi', 'uraemi'),
    ('thalassemia', 'thalassaemia'), ('toxemia', 'toxaemia'), ('bacteremia', 'bacteraemia'), ('viremia', 'viraemia'),
    ('anesthe', 'anaesthe'), ('hypoxemi', 'hypoxaemi'), ('cecum', 'caecum'), ('cecal', 'caecal'), ('ileus', 'ileus'),
    ('localiz', 'localis'), ('organiz', 'organis'), ('hospitaliz', 'hospitalis'), ('paralyz', 'paralys'),
    ('center', 'centre'), ('fiber', 'fibre'), ('sulfate', 'sulphate'), ('sulfur', 'sulphur'), ('aluminum', 'aluminium'),
    ('maneuver', 'manoeuvre'), ('ameba', 'amoeba'), ('amebi', 'amoebi'), ('feces', 'faeces'), ('fecal', 'faecal'),
    ('hemodialysis', 'haemodialysis'), ('hemo', 'haemo'), ('hema', 'haema'),
    # Thai spelling pairs are allowed too (substring, applied both ways like the rest); TM spells thalassaemia ทาลัสซีเมีย (8 พ.ย. 2569)
    ('ธาลัส', 'ทาลัส'),
]
SPELL = [p for p in SPELL if p[0] != p[1]]


def build(rows):
    out = {}
    for keys, en, th, alts, top in rows:
        for k in keys.split('|'):
            out.setdefault(k.lower(), []).append({'en': en, 'th': th, 'm': alts, 'top': top})
    return out


OUT = {'icd10': build(D10), 'icd9': build(D9), 'spell': SPELL}

if __name__ == '__main__':
    json.dump(OUT, open('/home/claude/icd-site/data/shared/abbr.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('icd10 keys', len(OUT['icd10']), 'icd9 keys', len(OUT['icd9']))
    if '--check' in sys.argv:
        import re
        for sysk in ('icd10', 'icd9'):
            d = json.load(open('/home/claude/icd-site/data/%s/codes.json' % sysk, encoding='utf8'))
            kw = json.load(open('/home/claude/icd-site/data/%s/keywords.json' % sysk, encoding='utf8'))
            codes = d['codes']
            allc = {c['c'] for c in codes}
            hay = {c['c']: (c['c'] + ' ' + c['en'] + ' ' + c.get('th', '') + ' ' + kw.get(c['c'], '')).lower() for c in codes}

            def num(c):
                return c

            def alt_ok(a, x):
                if a.startswith('@'):
                    r = a[1:]
                    if '-' in r:
                        lo, hi = r.split('-')
                        return lo <= x[:len(lo)] <= hi
                    return x.startswith(r) if '.' in r else (x == r or x.startswith(r + '.'))
                return a in hay[x]
            seen = set()
            for k, ms in OUT[sysk].items():
                for m in ms:
                    key = (m['en'], tuple(m['m']))
                    if key in seen:
                        continue
                    seen.add(key)
                    hits = [x for x in hay if any(alt_ok(a, x) for a in m['m'])]
                    missing_top = [t for t in m['top'] if t not in allc]
                    dead = [a for a in m['m'] if not any(alt_ok(a, x) for x in hay)]
                    flag = '!!' if (not hits or missing_top or dead) else '  '
                    if flag == '!!' or '-v' in sys.argv:
                        print(flag, sysk, k, '|', m['en'], '| hits', len(hits), '| missing top', missing_top, '| dead alts', dead)
