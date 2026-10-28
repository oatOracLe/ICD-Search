/**
 * สร้าง Google Form "เสนอเพิ่ม/แก้ไขรหัสและคำย่อ" ของเว็บค้นรหัส ICD พร้อม Google Sheet เก็บคำตอบ
 * วิธีใช้: เปิด https://script.google.com > New project > วางโค้ดนี้ทั้งหมด > กด Run (ฟังก์ชัน createIcdSuggestionForm)
 * ครั้งแรก Google จะถามสิทธิ์ ให้กด Allow แล้วดูผลที่ Execution log คัดลอกทั้ง 3 บรรทัดที่ขึ้นต้นด้วย FORM / PREFILL / SHEET ส่งให้ Claude
 */
function createIcdSuggestionForm() {
  var TYPES = ['คำย่อใหม่', 'รหัสใหม่', 'แก้ชื่อหรือคำแปลของรหัส', 'แก้คำย่อที่มีอยู่', 'อื่น ๆ'];
  var SYSTEMS = ['ICD-10', 'ICD-9-CM'];
  var form = FormApp.create('ค้นรหัส ICD — เสนอเพิ่มหรือแก้ไขรหัสและคำย่อ');
  form.setDescription('ข้อเสนอจะส่งถึงผู้ดูแลเว็บ ผู้ดูแลตรวจกับบัญชีจำแนกก่อนเพิ่มในเว็บ กรุณาใส่แหล่งอ้างอิงถ้ามี');
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('ขอบคุณครับ ผู้ดูแลจะตรวจข้อเสนอก่อนเพิ่มในเว็บ');

  var items = {};
  items.type = form.addMultipleChoiceItem().setTitle('ประเภทข้อเสนอ').setChoiceValues(TYPES).setRequired(true);
  items.sys = form.addMultipleChoiceItem().setTitle('ระบบรหัส').setChoiceValues(SYSTEMS).setRequired(true);
  items.code = form.addTextItem().setTitle('รหัส').setHelpText('เช่น E11.9, 47.09 (ถ้าเกี่ยวกับรหัส)');
  items.abbr = form.addTextItem().setTitle('คำย่อ').setHelpText('เช่น DM, CKD (ถ้าเกี่ยวกับคำย่อ)');
  items.meaning = form.addParagraphTextItem().setTitle('ความหมาย / ชื่อที่เสนอ').setHelpText('คำเต็มของคำย่อ ชื่อรหัส หรือสิ่งที่ควรแก้').setRequired(true);
  items.ref = form.addTextItem().setTitle('แหล่งอ้างอิง').setHelpText('เช่น ICD-10-TM 2009 หน้า 120, แนวทางมาตรฐาน 2026 ข้อ 2');
  items.note = form.addParagraphTextItem().setTitle('หมายเหตุเพิ่มเติม');
  items.who = form.addTextItem().setTitle('ชื่อผู้เสนอ / หน่วยงาน').setHelpText('ไม่บังคับ');
  items.from = form.addTextItem().setTitle('ส่งจากหน้า').setHelpText('เว็บกรอกให้อัตโนมัติ');

  var ss = SpreadsheetApp.create('ค้นรหัส ICD — ข้อเสนอ (คำตอบจากฟอร์ม)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // a pre-filled link reveals the entry.NNNN field ids that the website posts to
  var r = form.createResponse();
  r.withItemResponse(items.type.createResponse(TYPES[0]));
  r.withItemResponse(items.sys.createResponse(SYSTEMS[0]));
  ['code', 'abbr', 'ref', 'who', 'from'].forEach(function (k) { r.withItemResponse(items[k].createResponse('X_' + k)); });
  ['meaning', 'note'].forEach(function (k) { r.withItemResponse(items[k].createResponse('X_' + k)); });
  Logger.log('FORM ' + form.getPublishedUrl());
  Logger.log('PREFILL ' + r.toPrefilledUrl());
  Logger.log('SHEET ' + ss.getUrl());
}
