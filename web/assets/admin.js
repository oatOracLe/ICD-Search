/* Developer backend (หลังบ้านผู้พัฒนา) — opened at index.html#admin.
 *
 * Everything here writes OVERLAY ITEMS, never the base data files.
 *   online mode : items go to the site's database (collection "overlay"); only the owner/editors may write
 *   local mode  : items go to data/overlay.json in the project folder (saved through the browser)
 * Item kinds and fields are documented in docs/backend.md.
 */
(function () {
  'use strict';
  var A = window.ICDAPP, esc = A.esc, OV = A.OV;
  var root = null, tab = 'code', edit = {};   // edit[kind] = item being edited

  var TABS = [
    ['code', 'รหัส ICD'], ['abbr', 'คำย่อ'], ['note', 'หมายเหตุหน่วยงาน'], ['row', 'ตาราง'],
    ['morph', 'ICD-O'], ['idx', 'ดัชนี'], ['io', 'นำเข้า / ส่งออก']
  ];
  var NOTE_TYPES = [['note', 'หมายเหตุ'], ['includes', 'รวม (Includes)'], ['excludes', 'ไม่รวม (Excludes)'], ['inclusion', 'คำที่รวมอยู่ในรหัสนี้'],
    ['use_additional', 'ใช้รหัสเพิ่ม'], ['code_first', 'ให้รหัสโรคพื้นฐานก่อน']];
  var TABLE_NAMES = [['drugs', 'ตารางยาและสารเคมี'], ['neoplasm', 'ตารางเนื้องอก'], ['transport', 'ตารางอุบัติเหตุการขนส่งทางบก'], ['abortion', 'ตารางภาวะแทรกซ้อนของการแท้ง']];

  function $(id) { return document.getElementById(id); }
  function val(id) { var e = $(id); return e ? String(e.value || '').trim() : ''; }
  function lines(id) { return val(id).split(/\n/).map(function (s) { return s.trim(); }).filter(Boolean); }
  function list(id) { return val(id).split(/[\s,;]+/).map(function (s) { return s.trim(); }).filter(Boolean); }
  function opt(v, label, cur) { return '<option value="' + esc(v) + '"' + (String(cur) === String(v) ? ' selected' : '') + '>' + esc(label) + '</option>'; }
  function field(label, html, hint) { return '<label class="af"><span>' + label + '</span>' + html + (hint ? '<small>' + hint + '</small>' : '') + '</label>'; }
  function inp(id, v, ph) { return '<input id="' + id + '" value="' + esc(v || '') + '"' + (ph ? ' placeholder="' + esc(ph) + '"' : '') + '>'; }
  function area(id, v, ph, rows) { return '<textarea id="' + id + '" rows="' + (rows || 3) + '"' + (ph ? ' placeholder="' + esc(ph) + '"' : '') + '>' + esc(v || '') + '</textarea>'; }
  function sysSel(id, cur, withAll) {
    return '<select id="' + id + '">' + opt('icd10', 'ICD-10', cur) + opt('icd9', 'ICD-9-CM', cur) + (withAll ? opt('all', 'ทุกระบบ', cur) : '') + '</select>';
  }
  function writable() { return OV.mode === 'local' || (OV.mode === 'online' && OV.canEdit); }
  function items(kind) {
    var fileIds = {};
    OV.file.forEach(function (i) { fileIds[i.id] = 1; });
    return OV.effective().filter(function (i) { return i.kind === kind; }).map(function (i) {
      var onDb = OV.db.some(function (d) { return d.id === i.id; });
      return Object.assign({}, i, { _src: onDb ? 'ออนไลน์' : 'ไฟล์ overlay.json' });
    }).sort(function (a, b) { return String(b.updated || '').localeCompare(String(a.updated || '')); });
  }
  function findItem(id) { return OV.effective().filter(function (i) { return i.id === id; })[0]; }
  function save(it, msg) {
    if (!writable()) { A.toast('บัญชีนี้ไม่มีสิทธิ์แก้ไข'); return; }
    A.saveItem(it).then(function () { A.toast(msg || 'บันทึกแล้ว'); edit[it.kind] = null; render(); })
      .catch(function (e) { A.toast('บันทึกไม่สำเร็จ: ' + (e && (e.code || e.message) || '')); });
  }

  // ------------------------------------------------------------------ header
  function head() {
    var mode = OV.mode === 'local' ? '<span class="pill pill-local">โหมดในเครื่อง</span> บันทึกลงไฟล์ <code>data/overlay.json</code> ในโฟลเดอร์โปรเจกต์'
      : OV.mode === 'online' ? '<span class="pill pill-online">โหมดออนไลน์</span> บันทึกลงฐานข้อมูลของเว็บ ผู้ใช้ทุกคนเห็นทันที'
        : OV.mode === 'static' ? '<span class="pill">อ่านอย่างเดียว</span> เว็บนี้อยู่บนโฮสต์สาธารณะ แก้ข้อมูลได้จากโฟลเดอร์โปรเจกต์ในเครื่อง (localhost) แล้วอัปโหลดใหม่'
        : '<span class="pill">อ่านอย่างเดียว</span> หน้านี้เชื่อมฐานข้อมูลไม่ได้';
    var warn = '';
    if (OV.mode === 'online' && !OV.canEdit) warn = '<p class="awarn">บัญชีนี้ดูได้อย่างเดียว ต้องเป็นเจ้าของหรือผู้แก้ไข (Editor) ของเว็บนี้จึงจะเพิ่มหรือแก้ข้อมูลได้</p>';
    if (OV.mode === 'local' && OV.dirty) warn = '<p class="awarn">มีการแก้ไขที่ยังไม่ได้บันทึกลงไฟล์ (เก็บไว้ชั่วคราวในเบราว์เซอร์) <button type="button" class="btn primary" data-a="savefile">บันทึกลงไฟล์ overlay.json</button> <button type="button" class="btn" data-a="dropdraft">ทิ้งการแก้ไขที่ยังไม่บันทึก</button></p>';
    var n = OV.effective().length;
    return '<div class="ahead"><div><h1>หลังบ้านผู้พัฒนา</h1><p class="amode">' + mode + '</p></div>' +
      '<div class="astat"><b>' + n.toLocaleString('th-TH') + '</b> รายการที่เพิ่ม/แก้ไข<button type="button" class="btn" data-a="back">กลับไปหน้าค้นหา</button></div></div>' + warn +
      '<p class="ahint">ข้อมูลหลักที่ถอดจากเล่ม (โฟลเดอร์ data/icd10, data/icd9, data/shared) ไม่ถูกแก้ไข ทุกอย่างที่เพิ่มในหน้านี้เก็บเป็นชั้นข้อมูลแยก ลบรายการเมื่อไรก็กลับเป็นค่าเดิม</p>' +
      '<nav class="atabs" role="tablist">' + TABS.map(function (t) {
        var c = t[0] === 'io' ? '' : ' <span class="cnt">' + items(t[0]).length + '</span>';
        return '<button type="button" role="tab" data-a="tab" data-t="' + t[0] + '" aria-selected="' + (tab === t[0]) + '">' + t[1] + c + '</button>';
      }).join('') + '</nav>';
  }
  function itemList(kind, rowFn) {
    var xs = items(kind);
    if (!xs.length) return '<div class="alist"><p class="hint">ยังไม่มีรายการ</p></div>';
    return '<div class="alist"><h3>รายการที่เพิ่ม/แก้ไขแล้ว (' + xs.length + ')</h3><ul>' + xs.map(function (i) {
      return '<li><div>' + rowFn(i) + '<small>' + esc(i._src) + (i.updated ? ' · ' + esc(String(i.updated).slice(0, 16).replace('T', ' ')) : '') + '</small></div>' +
        (writable() ? '<span class="abtns"><button type="button" class="btn" data-a="edit" data-k="' + kind + '" data-id="' + esc(i.id) + '">แก้ไข</button>' +
          '<button type="button" class="btn danger" data-a="del" data-id="' + esc(i.id) + '">ลบ</button></span>' : '') + '</li>';
    }).join('') + '</ul></div>';
  }

  // ------------------------------------------------------------------ codes
  function codeForm() {
    var it = edit.code || {}, sys = it.sys || 'icd10';
    var d = A.db(sys), x = it.c && d.byCode[it.c];
    var base = A.base()[sys].codes.filter(function (b) { return b.c === it.c; })[0];
    var info = it.c ? (base ? '<p class="ainfo">รหัสนี้มีในข้อมูลหลัก: <b>' + esc(base.c) + '</b> ' + esc(base.th || base.en) + ' — ช่องที่เว้นว่างจะใช้ค่าเดิม</p>'
      : '<p class="ainfo new">รหัสใหม่ ยังไม่มีในข้อมูลหลัก ต้องใส่ชื่ออย่างน้อยหนึ่งภาษา</p>') : '';
    var n0 = (it.addNotes || [])[0] || {};
    return '<div class="aform"><h2>เพิ่มหรือแก้ไขรหัส</h2>' +
      '<div class="agrid">' + field('ระบบ', sysSel('f_sys', sys)) +
      field('รหัส', inp('f_c', it.c, sys === 'icd9' ? 'เช่น 47.09' : 'เช่น E11.9') + '<button type="button" class="btn" data-a="loadcode">ดึงข้อมูลเดิม</button>') + '</div>' + info +
      field('ชื่อภาษาอังกฤษ', inp('f_en', it.en, x ? x.en : '')) +
      field('ชื่อภาษาไทย', inp('f_th', it.th, x ? x.th : '')) +
      '<div class="agrid">' +
      (sys === 'icd10' ? field('เครื่องหมาย', '<select id="f_da">' + opt('', 'ไม่เปลี่ยน', it.da) + opt('†', '† รหัสสาเหตุ', it.da) + opt('*', '* รหัสอาการแสดง', it.da) + '</select>')
        : field('ThaiDRG', '<select id="f_drg">' + opt('', 'ไม่เปลี่ยน', it.drg) + opt('or', 'OR procedure', it.drg) + opt('drg', 'Non-OR มีผลต่อ ThaiDRG', it.drg) + '</select>')) +
      field('สถานะการใช้', '<select id="f_status">' + opt('', 'ไม่เปลี่ยน', it.status) + opt('ok', 'ใช้ลงรหัสได้', it.status) + opt('bad', 'งดใช้', it.status) + '</select>') +
      field('รหัสแม่ (รหัสใหม่)', inp('f_parent', it.parent, 'เว้นว่างให้ระบบหาเอง')) + '</div>' +
      '<fieldset><legend>หมายเหตุเพิ่มเติมของรหัสนี้</legend>' +
      field('ชนิด', '<select id="f_nt">' + NOTE_TYPES.map(function (t) { return opt(t[0], t[1], n0.t || 'note'); }).join('') + '</select>') +
      field('ภาษาอังกฤษ (บรรทัดละข้อ)', area('f_nen', (n0.en || []).join('\n'))) +
      field('ภาษาไทย (บรรทัดละข้อ)', area('f_nth', (n0.th || []).join('\n'))) + '</fieldset>' +
      field('บันทึกสำหรับผู้ดูแล', inp('f_memo', it.memo, 'เช่น แหล่งที่มา เหตุผลที่แก้'), 'แสดงในหน้ารายละเอียดของรหัส') +
      '<div class="aact"><button type="button" class="btn primary" data-a="savecode">บันทึก</button>' +
      '<button type="button" class="btn danger" data-a="hidecode">ซ่อนรหัสนี้จากเว็บ</button>' +
      '<button type="button" class="btn" data-a="clear" data-k="code">ล้างฟอร์ม</button></div></div>';
  }
  function saveCode(hide) {
    var sys = val('f_sys'), c = val('f_c').toUpperCase();
    if (sys === 'icd9') c = c.replace(/[^0-9.]/g, '');
    var ok = sys === 'icd10' ? /^[A-Z]\d\d(\.\d{1,3})?$/.test(c) : /^\d\d(\.\d{1,2})?$/.test(c);
    if (!ok) { A.toast('รูปแบบรหัสไม่ถูกต้อง'); return; }
    var inBase = A.base()[sys].codes.some(function (b) { return b.c === c; });
    var it = { id: A.newId('code', sys + '-' + c), kind: 'code', sys: sys, c: c, op: hide ? 'hide' : (inBase ? 'edit' : 'add') };
    if (!hide) {
      it.en = val('f_en'); it.th = val('f_th'); it.status = val('f_status'); it.memo = val('f_memo'); it.parent = val('f_parent').toUpperCase();
      if ($('f_da')) it.da = val('f_da');
      if ($('f_drg')) it.drg = val('f_drg');
      var nen = lines('f_nen'), nth = lines('f_nth');
      if (nen.length || nth.length) it.addNotes = [{ t: val('f_nt'), en: nen, th: nth }];
      if (!inBase && !it.en && !it.th) { A.toast('รหัสใหม่ต้องมีชื่อ'); return; }
      Object.keys(it).forEach(function (k) { if (it[k] === '') delete it[k]; });
    }
    save(it, hide ? 'ซ่อน ' + c + ' แล้ว' : 'บันทึก ' + c + ' แล้ว');
  }

  // ------------------------------------------------------------------ abbreviations
  function abbrForm() {
    var it = edit.abbr || {};
    return '<div class="aform"><h2>เพิ่มคำย่อ</h2>' +
      '<div class="agrid">' + field('ระบบ', sysSel('a_sys', it.sys || 'icd10')) + field('คำย่อ', inp('a_keys', it.keys, 'เช่น DM|T2DM'), 'หลายคำคั่นด้วย |') + '</div>' +
      field('ความหมาย (อังกฤษ)', inp('a_en', it.en)) + field('ความหมาย (ไทย)', inp('a_th', it.th)) +
      field('คำค้นหรือช่วงรหัส (บรรทัดละรายการ)', area('a_m', (it.m || []).join('\n'), 'diabetes mellitus\n@E10-E14\n@E11', 4),
        'คำ = ค้นในชื่อรหัส · @E10-E14 = ช่วงรหัส · @E11 = รหัสและรหัสย่อย') +
      field('รหัสที่ให้ขึ้นก่อน', inp('a_top', (it.top || []).join(', '), 'E11.9, E14.9')) +
      '<label class="acheck"><input type="checkbox" id="a_hide"' + (it.op === 'hide' ? ' checked' : '') + '> ลบคำย่อนี้ออกจากพจนานุกรม (ใช้กับคำย่อเดิมที่ไม่ต้องการ)</label>' +
      '<div class="aact"><button type="button" class="btn primary" data-a="saveabbr">บันทึก</button><button type="button" class="btn" data-a="clear" data-k="abbr">ล้างฟอร์ม</button></div></div>';
  }
  function saveAbbr() {
    var keys = val('a_keys').split('|').map(function (s) { return s.trim(); }).filter(Boolean);
    if (!keys.length) { A.toast('ใส่คำย่อ'); return; }
    var sys = val('a_sys'), hide = $('a_hide').checked;
    var it = { id: (edit.abbr && edit.abbr.id) || A.newId('abbr', sys + '-' + keys[0].toLowerCase()), kind: 'abbr', sys: sys, keys: keys.join('|'), op: hide ? 'hide' : 'add' };
    if (!hide) {
      it.en = val('a_en'); it.th = val('a_th'); it.m = lines('a_m'); it.top = list('a_top').map(function (c) { return c.toUpperCase(); });
      if (!it.m.length && !it.top.length) { A.toast('ใส่คำค้นหรือรหัสอย่างน้อยหนึ่งรายการ'); return; }
      it.top.forEach(function (c) { if (!A.db(sys).byCode[c]) A.toast('คำเตือน: ไม่พบรหัส ' + c); });
    }
    save(it);
  }

  // ------------------------------------------------------------------ unit notes
  function noteForm() {
    var it = edit.note || {};
    return '<div class="aform"><h2>หมายเหตุและแนวทางของหน่วยงาน</h2>' +
      '<div class="agrid">' + field('ระบบ', sysSel('n_sys', it.sys || 'icd10', true)) + field('ใช้กับรหัส', inp('n_codes', (it.codes || []).join(', '), 'E11, E10-E14, J18.9 หรือ * ทุกรหัส')) + '</div>' +
      field('หัวข้อ', inp('n_title', it.title)) + field('เนื้อหา', area('n_body', it.body, 'รหัสที่พิมพ์ในเนื้อหาจะกลายเป็นลิงก์', 6)) +
      '<p class="ahint">หมายเหตุจะแสดงในหน้ารายละเอียดของรหัสที่ตรงเงื่อนไข และในหน้าแนวทาง</p>' +
      '<div class="aact"><button type="button" class="btn primary" data-a="savenote">บันทึก</button><button type="button" class="btn" data-a="clear" data-k="note">ล้างฟอร์ม</button></div></div>';
  }
  function saveNote() {
    var it = { id: (edit.note && edit.note.id) || A.newId('note'), kind: 'note', sys: val('n_sys'), title: val('n_title'), body: val('n_body'), codes: list('n_codes').map(function (c) { return c.toUpperCase(); }) };
    if (!it.title || !it.body) { A.toast('ใส่หัวข้อและเนื้อหา'); return; }
    save(it);
  }

  // ------------------------------------------------------------------ table rows
  var TBL = null;
  function rowForm() {
    if (!TBL) { A.tables().then(function (t) { TBL = t; render(); }); return '<p class="hint">กำลังโหลดตาราง…</p>'; }
    var it = edit.row || {}, name = it.table || $('r_table') && val('r_table') || 'drugs', T = TBL[name], cols = T.cols;
    var row = it.row || [], op = it.op || 'add';
    return '<div class="aform"><h2>เพิ่มหรือแก้ไขแถวในตาราง</h2>' +
      '<div class="agrid">' + field('ตาราง', '<select id="r_table" data-a="rtable">' + TABLE_NAMES.map(function (t) { return opt(t[0], t[1], name); }).join('') + '</select>') +
      field('การทำงาน', '<select id="r_op">' + opt('add', 'เพิ่มแถวใหม่', op) + opt('edit', 'แก้แถวเดิม', op) + opt('hide', 'ซ่อนแถวเดิม', op) + '</select>') + '</div>' +
      '<fieldset><legend>แถวเดิมที่จะแก้หรือซ่อน (เฉพาะแก้/ซ่อน)</legend><div class="agrid">' +
      field('ชื่อในแถวเดิม', inp('r_mterm', it.match && it.match.term)) + field('ระดับ', inp('r_mlvl', it.match ? it.match.lvl : 0)) + '</div></fieldset>' +
      '<div class="agrid">' + field('ระดับ (0 = คำนำ)', inp('r_lvl', row[0] != null ? row[0] : 0)) +
      field('อยู่ใต้คำ (ระดับก่อนหน้า)', inp('r_parent', it.parent, 'เช่น Paracetamol')) + '</div>' +
      field('ชื่อ / คำ', inp('r_term', row[1])) +
      '<div class="agrid cols">' + cols.map(function (c, k) { return field(esc(c.th), inp('r_c' + k, row[2 + k], c.range || '')); }).join('') + '</div>' +
      field('หมายเหตุใต้แถว', inp('r_note', it.note)) +
      '<div class="aact"><button type="button" class="btn primary" data-a="saverow">บันทึก</button><button type="button" class="btn" data-a="clear" data-k="row">ล้างฟอร์ม</button></div></div>';
  }
  function saveRow() {
    var name = val('r_table'), T = TBL[name], op = val('r_op');
    var row = [+val('r_lvl') || 0, val('r_term')];
    T.cols.forEach(function (c, k) { row.push(val('r_c' + k).toUpperCase()); });
    var it = { id: (edit.row && edit.row.id) || A.newId('row'), kind: 'row', table: name, op: op, row: row, parent: val('r_parent'), note: val('r_note') };
    if (op !== 'add') it.match = { term: val('r_mterm'), lvl: +val('r_mlvl') || 0 };
    if (op === 'add' && !row[1]) { A.toast('ใส่ชื่อในแถว'); return; }
    if (op !== 'add' && !it.match.term) { A.toast('ใส่ชื่อของแถวเดิม'); return; }
    save(it);
  }

  // ------------------------------------------------------------------ ICD-O
  function morphForm() {
    var it = edit.morph || {}, r = it.row || {};
    return '<div class="aform"><h2>เพิ่มหรือแก้ไขรหัสสัณฐานวิทยา (ICD-O)</h2>' +
      '<div class="agrid">' + field('รหัส', inp('m_c', r.c, 'M8140/3')) + field('กลุ่ม', inp('m_g', r.g, 'เว้นว่าง = 4 หลักแรก')) + '</div>' +
      field('ชื่อชนิดเนื้องอก', inp('m_en', r.en)) + field('รหัส ICD-10 เมื่อไม่ระบุตำแหน่ง', inp('m_site', r.site, 'เช่น C22.0 หรือ C44.-')) +
      '<label class="acheck"><input type="checkbox" id="m_hide"' + (it.op === 'hide' ? ' checked' : '') + '> ซ่อนรหัสนี้</label>' +
      '<div class="aact"><button type="button" class="btn primary" data-a="savemorph">บันทึก</button><button type="button" class="btn" data-a="clear" data-k="morph">ล้างฟอร์ม</button></div></div>';
  }
  function saveMorph() {
    var c = val('m_c').toUpperCase().replace(/\s/g, '');
    if (!/^M\d{4}\/\d$/.test(c)) { A.toast('รูปแบบรหัสต้องเป็น M0000/0'); return; }
    var it = { id: A.newId('morph', c.replace('/', '_')), kind: 'morph', op: $('m_hide').checked ? 'hide' : 'add', row: { c: c, g: val('m_g'), en: val('m_en'), site: val('m_site').toUpperCase() } };
    if (it.op === 'add' && !it.row.en) { A.toast('ใส่ชื่อชนิดเนื้องอก'); return; }
    save(it);
  }

  // ------------------------------------------------------------------ alphabetical index
  function idxForm() {
    var it = edit.idx || {}, sys = it.sys || 'icd10';
    return '<div class="aform"><h2>เพิ่มคำในดัชนี</h2>' +
      '<div class="agrid">' + field('ระบบ', sysSel('i_sys', sys)) +
      field('หมวดดัชนี', '<select id="i_sec">' + opt('I', 'โรค / หัตถการ (Section I)', it.sec) + opt('II', 'สาเหตุภายนอก (Section II, ICD-10)', it.sec) + '</select>') + '</div>' +
      field('คำนำ (lead term)', inp('i_lead', it.lead, 'เช่น Diabetes')) +
      field('คำขยาย ไล่ตามลำดับชั้น (บรรทัดละระดับ)', area('i_sub', (it.sub || []).join('\n'), 'type 2\nwith foot ulcer', 3), 'ถ้าคำขยายมีอยู่แล้วจะต่อจากของเดิม') +
      '<div class="agrid">' + field('รหัส 1', inp('i_c1', it.c1, 'E11.5')) + field('รหัส 2 (ถ้ามี)', inp('i_c2', it.c2, 'เช่น รหัส *')) + '</div>' +
      '<div class="aact"><button type="button" class="btn primary" data-a="saveidx">บันทึก</button><button type="button" class="btn" data-a="clear" data-k="idx">ล้างฟอร์ม</button></div></div>';
  }
  function saveIdx() {
    var it = { id: (edit.idx && edit.idx.id) || A.newId('idx'), kind: 'idx', sys: val('i_sys'), sec: val('i_sec'), lead: val('i_lead'), sub: lines('i_sub'), c1: val('i_c1').toUpperCase(), c2: val('i_c2').toUpperCase() };
    if (!it.lead || !/^[A-Za-z]/.test(it.lead)) { A.toast('คำนำต้องขึ้นต้นด้วยตัวอักษรภาษาอังกฤษ'); return; }
    if (it.sys === 'icd9') it.sec = 'I';
    if (it.c1 && !A.db(it.sys).byCode[it.c1.replace(/[†*]/g, '')]) A.toast('คำเตือน: ไม่พบรหัส ' + it.c1);
    save(it);
  }

  // ------------------------------------------------------------------ import / export
  function ioPane() {
    var all = OV.effective();
    return '<div class="aform"><h2>นำเข้าและส่งออก</h2>' +
      '<p>ไฟล์ <code>overlay.json</code> คือชั้นข้อมูลที่เพิ่มทั้งหมด วางไว้ที่ <code>web/data/overlay.json</code> ของโฟลเดอร์โปรเจกต์ แล้วเว็บจะโหลดเอง</p>' +
      '<div class="aact"><button type="button" class="btn primary" data-a="export">ส่งออกเป็น overlay.json (' + all.length + ' รายการ)</button>' +
      (OV.mode === 'local' ? '<button type="button" class="btn" data-a="savefile">บันทึกทับไฟล์ overlay.json ในโฟลเดอร์</button>' : '') + '</div>' +
      '<h3>นำเข้า</h3><p>เลือกไฟล์ overlay.json เพื่อรวมรายการเข้ากับข้อมูลปัจจุบัน (รายการที่ id ซ้ำจะถูกแทนที่)' + (OV.mode === 'online' ? ' ระบบจะบันทึกลงฐานข้อมูลออนไลน์' : '') + '</p>' +
      '<input type="file" id="io_file" accept=".json,application/json"> <button type="button" class="btn" data-a="import">นำเข้า</button>' +
      '<h3>ข้อมูลดิบ</h3><textarea class="araw" readonly rows="10">' + esc(JSON.stringify({ version: 1, items: all }, null, 2)) + '</textarea></div>';
  }
  function exportJson() {
    var data = JSON.stringify({ version: 1, note: 'ข้อมูลที่ผู้พัฒนาเพิ่ม/แก้ไข — แก้ผ่านหน้า #admin', exported: new Date().toISOString(), items: OV.effective() }, null, 2);
    var c = window.claude;
    var fallback = function () {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
      a.download = 'overlay.json'; document.body.appendChild(a); a.click(); a.remove();
    };
    if (c && c.use) c.use('downloads').then(function (dl) { if (!dl) return fallback(); dl.save({ filename: 'overlay.json', data: data }).catch(function () {}); });
    else fallback();
  }
  function saveFile() {
    var data = JSON.stringify({ version: 1, note: 'ข้อมูลที่ผู้พัฒนาเพิ่ม/แก้ไข — แก้ผ่านหน้า #admin ไม่ต้องแก้มือ', items: OV.file }, null, 2);
    var done = function () { try { localStorage.removeItem(A.draftKey); } catch (e) {} OV.dirty = false; A.toast('บันทึกลงไฟล์แล้ว'); render(); };
    if (window.showSaveFilePicker) {
      var get = OV.fileHandle ? Promise.resolve(OV.fileHandle) : window.showSaveFilePicker({ suggestedName: 'overlay.json', types: [{ description: 'JSON', accept: { 'application/json': ['.json'] } }] });
      get.then(function (h) { OV.fileHandle = h; return h.createWritable(); }).then(function (w) { return w.write(data).then(function () { return w.close(); }); }).then(done)
        .catch(function (e) { if (e && e.name !== 'AbortError') A.toast('บันทึกไม่สำเร็จ'); });
    } else {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
      a.download = 'overlay.json'; document.body.appendChild(a); a.click(); a.remove();
      A.toast('ดาวน์โหลดแล้ว ให้นำไฟล์ไปวางทับ web/data/overlay.json');
      done();
    }
  }
  function importJson() {
    var f = $('io_file').files[0];
    if (!f) { A.toast('เลือกไฟล์ก่อน'); return; }
    f.text().then(function (txt) {
      var j = JSON.parse(txt), xs = (j.items || []).filter(function (i) { return i && i.id && i.kind; });
      if (!xs.length) { A.toast('ไม่พบรายการในไฟล์'); return; }
      if (OV.mode === 'local') {
        xs.forEach(function (it) { var i = OV.file.findIndex(function (x) { return x.id === it.id; }); if (i === -1) OV.file.push(it); else OV.file[i] = it; });
        A.persistLocal(); A.rebuild(); A.toast('นำเข้า ' + xs.length + ' รายการ'); render();
        return;
      }
      var chain = Promise.resolve();
      xs.forEach(function (it) { chain = chain.then(function () { return A.saveItem(it); }); });
      chain.then(function () { A.toast('นำเข้า ' + xs.length + ' รายการ'); render(); }).catch(function () { A.toast('นำเข้าไม่ครบ'); });
    }).catch(function () { A.toast('อ่านไฟล์ไม่ได้'); });
  }

  // ------------------------------------------------------------------ render & events
  var FORMS = { code: codeForm, abbr: abbrForm, note: noteForm, row: rowForm, morph: morphForm, idx: idxForm };
  var LABELS = {
    code: function (i) { return '<b class="code">' + esc(i.c) + '</b> ' + esc(i.sys === 'icd9' ? 'ICD-9-CM' : 'ICD-10') + ' · ' + esc({ add: 'เพิ่ม', edit: 'แก้ไข', hide: 'ซ่อน' }[i.op] || i.op) + ' ' + esc(i.th || i.en || ''); },
    abbr: function (i) { return '<b class="code">' + esc(i.keys) + '</b> ' + (i.op === 'hide' ? 'ลบออก' : esc(i.en || '') + ' ' + esc(i.th || '')); },
    note: function (i) { return '<b>' + esc(i.title) + '</b> ' + esc((i.codes || []).join(', ')); },
    row: function (i) { return esc((TABLE_NAMES.filter(function (t) { return t[0] === i.table; })[0] || [0, i.table])[1]) + ' · ' + esc({ add: 'เพิ่ม', edit: 'แก้ไข', hide: 'ซ่อน' }[i.op]) + ' <b>' + esc(i.op === 'add' ? i.row[1] : i.match && i.match.term) + '</b>'; },
    morph: function (i) { return '<b class="code">' + esc(i.row.c) + '</b> ' + (i.op === 'hide' ? 'ซ่อน' : esc(i.row.en)); },
    idx: function (i) { return esc(i.sys === 'icd9' ? 'ICD-9-CM' : 'ICD-10 ' + i.sec) + ' · <b>' + esc([i.lead].concat(i.sub || []).join(' › ')) + '</b> ' + esc([i.c1, i.c2].filter(Boolean).join(' ')); }
  };
  function render() {
    if (!root) return;
    var body = tab === 'io' ? ioPane() : '<div class="acols">' + (writable() ? FORMS[tab]() : '<div class="aform"><p class="hint">ดูรายการได้อย่างเดียว</p></div>') + itemList(tab, LABELS[tab]) + '</div>';
    root.innerHTML = head() + body;
  }
  function onClick(ev) {
    var b = ev.target.closest('[data-a]');
    if (!b || !root.contains(b)) return;
    var a = b.getAttribute('data-a');
    if (a === 'tab') { tab = b.getAttribute('data-t'); render(); }
    else if (a === 'back') A.goto('search');
    else if (a === 'clear') { edit[b.getAttribute('data-k')] = null; render(); }
    else if (a === 'edit') { var it = findItem(b.getAttribute('data-id')); if (it) { edit[b.getAttribute('data-k')] = it; render(); root.scrollIntoView({ block: 'start' }); } }
    else if (a === 'del') {
      if (!window.confirm || window.confirm('ลบรายการนี้? ข้อมูลจะกลับเป็นค่าเดิม')) A.deleteItem(b.getAttribute('data-id')).then(function () { A.toast('ลบแล้ว'); render(); });
    }
    else if (a === 'loadcode') {
      var sys = val('f_sys'), c = val('f_c').toUpperCase();
      var ex = findItem(A.newId('code', sys + '-' + c));
      edit.code = ex || { sys: sys, c: c };
      render();
    }
    else if (a === 'savecode') saveCode(false);
    else if (a === 'hidecode') saveCode(true);
    else if (a === 'saveabbr') saveAbbr();
    else if (a === 'savenote') saveNote();
    else if (a === 'saverow') saveRow();
    else if (a === 'savemorph') saveMorph();
    else if (a === 'saveidx') saveIdx();
    else if (a === 'export') exportJson();
    else if (a === 'savefile') saveFile();
    else if (a === 'dropdraft') { try { localStorage.removeItem(A.draftKey); } catch (e) {} location.reload(); }
    else if (a === 'import') importJson();
  }
  function onChange(ev) {
    var t = ev.target;
    if (t.id === 'r_table') { edit.row = { table: t.value }; render(); }
    if (t.id === 'f_sys') { edit.code = { sys: t.value }; render(); }
  }
  window.ICDADMIN = {
    mount: function (el) {
      root = el;
      el.addEventListener('click', onClick);
      el.addEventListener('change', onChange);
      render();
    },
    show: function () { render(); },
    refresh: function () { TBL = null; render(); }
  };
})();
