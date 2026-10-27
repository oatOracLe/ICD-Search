(function () {
  'use strict';

  var SYS = {
    icd10: { name: 'ICD-10', long: 'ICD-10 (WHO 2016) · การวินิจฉัยโรค', label: 'ค้นหาโรคหรือรหัสวินิจฉัย', ph: 'พิมพ์รหัส ชื่อโรค หรือคำย่อ เช่น E11, เบาหวาน, DM, CKD', chips: ['เบาหวาน', 'DM', 'HT', 'CKD', 'ไข้เลือดออก', 'J18', 'sepsis'], idx: 'ดัชนีโรค ICD-10 (WHO 2016)', tag: 't10', rx: /\b([A-Z]\d\d(?:\.\d{1,3})?)([†*]?)/g },
    icd9: { name: 'ICD-9-CM', long: 'ICD-9-CM · หัตถการ', label: 'ค้นหาหัตถการหรือรหัสหัตถการ', ph: 'พิมพ์รหัส ชื่อหัตถการ หรือคำย่อ เช่น 47.0, appendectomy, ORIF, C/S', chips: ['appendectomy', 'C/S', 'ORIF', 'ETT', 'PRC', '99.04'], idx: 'ดัชนีหัตถการ ICD-9-CM', tag: 't9', rx: /\b(\d\d\.\d{1,2})\b/g }
  };
  var NOTE_ORDER = ['see', 'inclusion', 'includes', 'excludes', 'code_first', 'use_additional', 'code_also', 'omit', 'note'];
  var NOTE_LABEL = { see: 'การแบ่งย่อย', inclusion: 'คำที่รวมอยู่ในรหัสนี้', includes: 'รวม (Includes)', excludes: 'ไม่รวม (Excludes)', code_first: 'ให้รหัสโรคพื้นฐานก่อน (Code first)', use_additional: 'ใช้รหัสเพิ่ม (Use additional code)', code_also: 'ลงรหัสเพิ่ม (Code also)', omit: 'ไม่ต้องลงรหัส (Omit code)', note: 'หมายเหตุ' };
  var MAX_RESULTS = 200;
  var MAX_ROWS = 500;

  var S = { sys: 'icd10', view: 'search', q: 'เบาหวาน', sel: { icd10: 'E11.9', icd9: null }, imode: 'alpha', sec: { icd10: 'I', icd9: 'I' }, letter: {}, idxF: '', openCh: {}, openBl: {}, pane: 'list', ready: false, gq: '', gsec: '' };
  // where every data file lives (relative to index.html)
  var PATH = {
    icd10: 'data/icd10/codes.json', kw10: 'data/icd10/keywords.json', tables: 'data/icd10/tables.json', morph: 'data/icd10/morph.json', idx10: 'data/icd10/index/',
    icd9: 'data/icd9/codes.json', kw9: 'data/icd9/keywords.json', idx9: 'data/icd9/index/',
    abbr: 'data/shared/abbr.json', guide: 'data/shared/guidelines.json', nhso: 'data/shared/nhso2562.json',
    overlay: 'data/overlay.json'
  };
  var DB = {}, G = {}, NHSO = null, IDXM = {}, IDXL = {}, IDXRAW = {};
  var BASE = {};          // data exactly as built from the source books (never edited at run time)
  var NOTES = [];         // unit notes from the overlay

  function lsGet(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var favs = lsGet('icd.favs', []);
  var hist = lsGet('icd.hist', []);

  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function tokensOf(q) { var n = q.toLowerCase().trim(); return n ? n.split(/\s+/) : []; }
  function hl(text, toks) {
    var s = String(text || '');
    if (!toks.length) return esc(s);
    var low = s.toLowerCase();
    if (low.length !== s.length) return esc(s);
    var m = new Array(s.length);
    toks.forEach(function (t) { var i = low.indexOf(t); while (t && i !== -1) { for (var k = i; k < i + t.length; k++) m[k] = 1; i = low.indexOf(t, i + t.length); } });
    var out = '', open = false;
    for (var i = 0; i < s.length; i++) {
      if (m[i] && !open) { out += '<mark>'; open = true; }
      if (!m[i] && open) { out += '</mark>'; open = false; }
      out += esc(s[i]);
    }
    return open ? out + '</mark>' : out;
  }
  // turn code mentions inside note text into links to that code
  function linkify(text, sys) {
    var d = DB[sys];
    var src = String(text || '');
    var rx = new RegExp(SYS[sys].rx.source, 'g');
    var out = '', last = 0, m;
    while ((m = rx.exec(src))) {
      var c = m[1];
      out += esc(src.slice(last, m.index));
      if (d && d.byCode[c]) out += '<button type="button" class="cref" data-act="sel" data-sys="' + sys + '" data-code="' + esc(c) + '">' + esc(m[0]) + '</button>';
      else out += esc(m[0]);
      last = m.index + m[0].length;
    }
    return out + esc(src.slice(last));
  }
  var ICON = {
    check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>',
    copy: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/></svg>',
    star: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
    chev: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>',
    back: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg>',
    warn: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 8v5M12 16.5v.5"/><circle cx="12" cy="12" r="9"/></svg>'
  };

  // ---------- data ----------
  function cmpCode(a, b) { return a.c.localeCompare(b.c, 'en', { numeric: true }); }
  function prep(d) {
    var chapterMap = {}, blockMap = {}, byCode = {}, kids = {}, byBlock = {};
    (d.chapters || []).forEach(function (c) { chapterMap[c.id] = c; });
    (d.blocks || []).forEach(function (b) { blockMap[b.id] = b; byBlock[b.id] = []; });
    d.codes.forEach(function (x) {
      x.nodot = x.c.replace(/\./g, '');
      x.lowNodot = x.nodot.toLowerCase();
      x.hay = (x.c + ' ' + x.nodot + ' ' + (x.en || '') + ' ' + (x.th || '') + ' ' + (x.kw || '')).toLowerCase();
      x.tl = ((x.th || '') + ' ' + (x.en || '')).toLowerCase();
      byCode[x.c] = x;
    });
    d.codes.forEach(function (x) {
      if (x.p && byCode[x.p]) (kids[x.p] = kids[x.p] || []).push(x);
      (byBlock[x.b] = byBlock[x.b] || []).push(x);
    });
    Object.keys(kids).forEach(function (k) { kids[k].sort(cmpCode); });
    Object.keys(byBlock).forEach(function (k) { byBlock[k].sort(cmpCode); });
    d.codes.forEach(function (x) { var n = 0, p = x; while (p.p && byCode[p.p] && n < 8) { p = byCode[p.p]; n++; } x.depth = n; });
    d.chapterMap = chapterMap; d.blockMap = blockMap; d.byCode = byCode; d.kids = kids; d.byBlock = byBlock;
    d.sorted = d.codes.slice().sort(cmpCode);
    return d;
  }
  function addKeywords(sys, map) {
    var d = DB[sys];
    Object.keys(map).forEach(function (c) { var x = d.byCode[c]; if (x) { x.kw2 = map[c]; x.hay += ' ' + map[c]; } });
  }
  function ancestors(d, x) { var out = [], p = x; while (p.p && d.byCode[p.p] && out.length < 8) { p = d.byCode[p.p]; out.unshift(p); } return out; }
  function stripMark(c) { return String(c || '').replace(/[†*]/g, ''); }

  // ---------- query parsing: abbreviations + spelling variants ----------
  // ABBR[sys][key] = [{en, th, m:[alt], top:[code]}]; alt "@E10-E14" = code range, "@I21" = code and its subdivisions, else text
  var ABBR = { icd10: {}, icd9: {} }, SPELL = [];
  function reEsc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function spellVariants(t) {
    var out = [t];
    SPELL.forEach(function (p) {
      if (t.indexOf(p[0]) !== -1) out.push(t.split(p[0]).join(p[1]));
      if (t.indexOf(p[1]) !== -1) out.push(t.split(p[1]).join(p[0]));
    });
    return out.filter(function (v, i) { return out.indexOf(v) === i; });
  }
  function compileAlt(a) {
    if (a.charAt(0) !== '@') return { k: 's', v: a };
    var r = a.slice(1);
    if (r.indexOf('-') > 0) { var p = r.split('-'); return { k: 'r', lo: p[0], hi: p[1] }; }
    return { k: 'p', v: r, dot: r.indexOf('.') !== -1 };
  }
  function altHit(a, x) {
    if (a.k === 's') return x.hay.indexOf(a.v) !== -1;
    if (a.k === 'w') return a.rx.test(x.tl);
    if (a.k === 'r') { var c = x.c.slice(0, a.lo.length); return c >= a.lo && c <= a.hi; }
    return a.dot ? x.c.indexOf(a.v) === 0 : (x.c === a.v || x.c.indexOf(a.v + '.') === 0);
  }
  // does every query group match the code or its own title (not just index keywords)?
  function inTitle(groups, x, title) {
    return groups.every(function (g) {
      return g.alts.some(function (a) {
        if (a.k === 's') return title.indexOf(a.v) !== -1;
        if (a.k === 'w') return a.rx.test(title);
        return altHit(a, x);
      }) || (g.lit && x.lowNodot.indexOf(g.nodot) !== -1);
    });
  }
  // every abbreviation group that names code ranges is matched by one of them (stronger than a title word)
  function codeHit(groups, x) {
    return groups.every(function (g) {
      if (!g.abbr) return true;
      var codeAlts = g.alts.filter(function (a) { return a.k === 'r' || a.k === 'p'; });
      return !codeAlts.length || codeAlts.some(function (a) { return altHit(a, x); });
    });
  }
  // S.abbrPick[key] = index of the chosen meaning (unset = all meanings)
  function parseQuery(sys, q) {
    var raw = tokensOf(q), dict = ABBR[sys] || {}, groups = [], hlToks = [], abbrs = [];
    for (var i = 0; i < raw.length;) {
      var hit = null;
      for (var n = Math.min(3, raw.length - i); n >= 1 && !hit; n--) {
        var key = raw.slice(i, i + n).join(' ');
        if (Object.prototype.hasOwnProperty.call(dict, key)) hit = { key: key, n: n };
      }
      if (hit) {
        var ms = dict[hit.key], pick = S.abbrPick && S.abbrPick[hit.key];
        var use = pick != null && ms[pick] ? [ms[pick]] : ms;
        var alts = [{ k: 'w', rx: new RegExp('(^|[^a-z0-9])' + reEsc(hit.key) + '($|[^a-z0-9])') }], top = [];
        use.forEach(function (m) {
          m.m.forEach(function (a) {
            var ca = compileAlt(a);
            if (ca.k === 's') spellVariants(ca.v).forEach(function (v) { alts.push({ k: 's', v: v }); hlToks.push(v); });
            else alts.push(ca);
          });
          m.top.forEach(function (c) { if (top.indexOf(c) === -1) top.push(c); });
        });
        groups.push({ alts: alts, top: top, abbr: hit.key });
        abbrs.push({ key: hit.key, ms: ms, pick: pick });
        i += hit.n;
      } else {
        var t = raw[i], vs = spellVariants(t);
        groups.push({ alts: vs.map(function (v) { return { k: 's', v: v }; }), lit: t, nodot: t.replace(/\./g, '') });
        hlToks = hlToks.concat(vs);
        i++;
      }
    }
    return { groups: groups, hlToks: hlToks, abbrs: abbrs, raw: raw };
  }

  function search(d, q) {
    var P = parseQuery(d === DB.icd9 ? 'icd9' : 'icd10', q), toks = P.raw, GR = P.groups;
    if (!toks.length) return { toks: toks, list: [], total: 0, abbrs: [], empty: true };
    var qn = q.toLowerCase().replace(/[.\s]/g, '');
    var top = [];
    GR.forEach(function (g) { if (g.top) g.top.forEach(function (c) { if (top.indexOf(c) === -1) top.push(c); }); });
    var hasAbbr = P.abbrs.length > 0;
    function groupHit(g, x) {
      for (var k = 0; k < g.alts.length; k++) if (altHit(g.alts[k], x)) return true;
      return !!(g.lit && x.lowNodot.indexOf(g.nodot) !== -1);
    }
    function score(x, groups) {
      var sc = 5, ti = top.indexOf(x.c);
      if (x.lowNodot === qn) sc = 0;
      else if (ti !== -1) sc = -10 + ti * 0.01;
      else if (x.lowNodot.indexOf(qn) === 0) sc = 1;
      else if (!hasAbbr && groups[0].alts.some(function (a) { return (x.th || '').toLowerCase().indexOf(a.v) === 0 || (x.en || '').toLowerCase().indexOf(a.v) === 0; })) sc = 2;
      else if (hasAbbr && codeHit(groups, x) && inTitle(groups, x, x.tl)) sc = x.leaf ? 3 : 3.1;
      else if (inTitle(groups, x, x.tl)) sc = hasAbbr ? (x.leaf ? 3.3 : 3.4) : 3;
      else if (!hasAbbr && x.kw2 && toks.every(function (t) { return x.kw2.indexOf(t) !== -1; })) sc = 4;
      else if (hasAbbr) sc = 4.5;
      return x.bad || x.who_del ? sc + 3 : sc;
    }
    var out = [], i, x;
    for (i = 0; i < d.codes.length; i++) {
      x = d.codes[i];
      if (GR.every(function (g) { return groupHit(g, x); })) out.push({ x: x, sc: score(x, GR) });
    }
    // several abbreviations that never occur together ("TAH BSO", "DM HT DLP"): list the codes of each one
    var any = false;
    if (!out.length && P.abbrs.length > 1) {
      any = true;
      var AG = GR.filter(function (g) { return g.abbr; });
      for (i = 0; i < d.codes.length; i++) {
        x = d.codes[i];
        var hitG = AG.filter(function (g) { return groupHit(g, x); });
        if (hitG.length) out.push({ x: x, sc: score(x, hitG) });
      }
    }
    out.sort(function (a, b) { return a.sc - b.sc || a.x.c.localeCompare(b.x.c, 'en', { numeric: true }); });
    return { toks: P.hlToks, list: out.slice(0, MAX_RESULTS).map(function (o) { return o.x; }), total: out.length, abbrs: P.abbrs, any: any };
  }

  // ---------- rendering helpers ----------
  function codeTags(x, sys) {
    var t = '';
    if (x.who_del) t += '<span class="tag tag-bad">ไม่มีใน WHO</span>';
    else if (x.bad) t += '<span class="tag tag-bad">งดใช้</span>';
    else if (!x.leaf) t += '<span class="tag tag-cat">ยังไม่ครบหลัก</span>';
    if (x.tm && !x.who && !x.who_del) t += '<span class="tag tag-tm">TM</span>';
    if (x.ov === 'add') t += '<span class="tag tag-ov">เพิ่มโดยผู้ดูแล</span>';
    if (x.drg === 'or') t += '<span class="tag tag-or">OR</span>';
    if (x.drg === 'drg') t += '<span class="tag tag-drg">ThaiDRG</span>';
    return t ? '<span class="tags">' + t + '</span>' : '';
  }
  function resRow(x, sys, toks, opts) {
    opts = opts || {};
    var cur = S.sys === sys && S.sel[sys] === x.c;
    var main = x.th || x.en;
    return '<li><button type="button" class="res" data-act="sel" data-sys="' + sys + '" data-code="' + esc(x.c) + '" aria-current="' + cur + '">' +
      '<span class="code"' + (opts.sysColor ? ' style="color: var(--' + (sys === 'icd9' ? 'px' : 'dx') + ')"' : '') + '>' + esc(x.c) + esc(x.da || '') + '</span>' +
      '<span class="txt"><span class="th">' + hl(main, toks) + '</span>' + (x.th ? '<span class="en">' + hl(x.en, toks) + '</span>' : '') +
      (opts.sysColor ? '<span class="en">' + SYS[sys].name + '</span>' : '') + '</span>' + codeTags(x, sys) + '</button></li>';
  }

  function abbrBox(abbrs) {
    if (!abbrs || !abbrs.length) return '';
    return '<div class="abbr" role="note">' + abbrs.map(function (a) {
      var k = esc(a.key.toUpperCase());
      if (a.ms.length === 1) return '<p><b class="abbr-k">' + k + '</b> คำย่อของ ' + esc(a.ms[0].en) + ' <span class="abbr-th">' + esc(a.ms[0].th) + '</span></p>';
      var chips = '<button type="button" class="chip" data-act="abbr" data-k="' + esc(a.key) + '" data-i="" aria-pressed="' + (a.pick == null) + '">ทุกความหมาย</button>' +
        a.ms.map(function (m, i) { return '<button type="button" class="chip" data-act="abbr" data-k="' + esc(a.key) + '" data-i="' + i + '" aria-pressed="' + (a.pick === i) + '">' + esc(m.en) + ' · ' + esc(m.th) + '</button>'; }).join('');
      return '<p><b class="abbr-k">' + k + '</b> คำย่อนี้มี ' + a.ms.length + ' ความหมาย เลือกเพื่อกรองผล</p><div class="abbr-chips">' + chips + '</div>';
    }).join('') + '</div>';
  }
  // ICD-O morphology terms matching the search (ICD-10 only)
  function morphBox(q) {
    if (S.sys !== 'icd10' || !MORPH) return '';
    var t = String(q || '').trim();
    if (t.length < 3 || /^[a-ln-z]\d/i.test(t) || /[฀-๿]/.test(t)) return '';
    var list = MORPH.codes.filter(function (c) { return morphMatch(c, t); });
    if (!list.length) return '';
    var toks = /^m?\d/i.test(t) ? [] : t.toLowerCase().split(/\s+/);
    return '<div class="morphbox"><div class="sec-head"><h3>สัณฐานวิทยาเนื้องอก (ICD-O) · ' + list.length + ' รหัส</h3><button type="button" class="link" data-act="opentable" data-t="morph" data-f="' + esc(t) + '">ดูทั้งหมด</button></div>' +
      '<table class="itbl morph"><tbody>' + morphRows(list.slice(0, 5), toks) + '</tbody></table></div>';
  }
  function renderSearchList() {
    var d = DB[S.sys];
    var r = search(d, S.q);
    var h = '';
    if (r.empty) {
      var recent = hist.filter(function (e) { return e.sys === S.sys && DB[e.sys].byCode[e.c]; }).slice(0, 10);
      if (recent.length) h += '<div class="list-head"><h2>ดูล่าสุด</h2><span>' + recent.length + ' รหัส</span></div><ul class="results">' + recent.map(function (e) { return resRow(DB[e.sys].byCode[e.c], e.sys, []); }).join('') + '</ul><div style="height: 20px"></div>';
      h += '<div class="empty"><b>พิมพ์เพื่อค้นหาจาก ' + d.codes.length.toLocaleString('th-TH') + ' รหัส</b><p>ใช้รหัส ชื่อภาษาไทย ชื่อภาษาอังกฤษ หรือคำในดัชนี หรือเปิดเมนูดัชนีเพื่อไล่หาจากคำนำ</p></div>';
      return h;
    }
    h += '<div class="list-head"><h2>ผลการค้นหา</h2><span>พบ ' + r.total.toLocaleString('th-TH') + ' รหัส</span></div>';
    h += abbrBox(r.abbrs);
    if (r.any) h += '<p class="hint">ไม่มีรหัสเดียวที่ตรงกับทุกคำ จึงแสดงรหัสของแต่ละคำย่อรวมกัน</p>';
    h += morphBox(S.q);
    if (!r.total) {
      var other = S.sys === 'icd10' ? 'icd9' : 'icd10';
      var on = search(DB[other], S.q).total;
      return h + '<div class="empty"><b>ไม่พบรหัสที่ตรงกับ “' + esc(S.q) + '”</b><p>' + (S.sys === 'icd9' ? 'ชื่อหัตถการใน ICD-9-CM เป็นภาษาอังกฤษ ลองพิมพ์คำภาษาอังกฤษหรือรหัสบางส่วน' : 'ลองใช้คำที่สั้นลง พิมพ์รหัสบางส่วน (เช่น E11) หรือเปิดดัชนีเพื่อไล่หาจากคำนำ') + '</p>' +
        (on ? '<button type="button" class="btn" data-act="sys" data-sys="' + other + '">พบ ' + on + ' รหัสใน ' + SYS[other].name + '</button>' : '') + '</div>';
    }
    h += '<ul class="results" id="results">' + r.list.map(function (x) { return resRow(x, S.sys, r.toks); }).join('') + '</ul>';
    if (r.total > r.list.length) h += '<p class="more">แสดง ' + r.list.length + ' รายการแรก พิมพ์คำเพิ่มเพื่อให้แคบลง</p>';
    return h;
  }

  // ---------- index (lazy per-letter files) ----------
  function idxKey(sys, sec, L) { return sys + '/' + sec + '-' + L; }
  function idxDir(sys) { return sys === 'icd10' ? PATH.idx10 : PATH.idx9; }
  function loadManifest(sys) {
    if (IDXM[sys]) return Promise.resolve(IDXM[sys]);
    return fetch(idxDir(sys) + 'manifest.json').then(function (r) { return r.json(); }).then(function (m) { IDXM[sys] = m; return m; });
  }
  function loadLetter(sys, sec, L) {
    var k = idxKey(sys, sec, L);
    if (IDXL[k]) return Promise.resolve(IDXL[k]);
    var raw = IDXRAW[k] ? Promise.resolve(IDXRAW[k]) : fetch(idxDir(sys) + sec + '-' + L + '.json').then(function (r) { return r.ok ? r.json() : []; });
    return raw.then(function (rows0) {
      IDXRAW[k] = rows0;
      var rows = applyIdxItems(clone(rows0), sys, sec, L, OV.effective());
      var stack = [];
      rows.forEach(function (e) {
        stack = stack.slice(0, e[0]); stack[e[0]] = e[1] + (e[2] && e[2].indexOf('TABLE:') !== 0 ? ' ' + e[2] : '');
        e.low = stack.join(' ').toLowerCase(); e.letter = L;
      });
      IDXL[k] = rows; return rows;
    });
  }
  var idxPending = false;
  function renderAlpha() {
    var sys = S.sys, sec = S.sec[sys];
    var m = IDXM[sys];
    if (!m) {
      loadManifest(sys).then(function () { renderAll(); }).catch(function () { $('list').innerHTML = '<div class="empty"><b>โหลดดัชนีไม่สำเร็จ</b><p>ลองรีเฟรชหน้านี้</p></div>'; });
      return '<p class="hint">กำลังโหลดดัชนี…</p>';
    }
    var secs = Object.keys(m.sections);
    var tabs = sys === 'icd10' ? [['T:drugs', 'ตารางยาและสารเคมี'], ['T:neoplasm', 'ตารางเนื้องอก'], ['T:morph', 'สัณฐานวิทยาเนื้องอก (ICD-O)'], ['T:abortion', 'ตารางภาวะแทรกซ้อนของการแท้ง'], ['T:transport', 'ตารางอุบัติเหตุการขนส่งทางบก']] : [];
    var chips = secs.map(function (s) { return [s, m.sections[s]]; }).concat(tabs);
    $('secChips').innerHTML = chips.length > 1 ? '<span>หมวดดัชนี:</span>' + chips.map(function (s) { return '<button type="button" class="chip" data-act="isec" data-s="' + s[0] + '" aria-pressed="' + (s[0] === sec) + '">' + esc(s[1]) + '</button>'; }).join('') : '';
    if (sec === 'T:morph') return renderMorph();
    if (sec.indexOf('T:') === 0) return renderTable(sec.slice(2));
    var letters = m.letters[sec] || {};
    var avail = Object.keys(letters).sort();
    var L = S.letter[sys + sec];
    if (!L || !letters[L]) L = S.letter[sys + sec] = avail[0];
    var f = S.idxF.toLowerCase().trim();
    $('letters').innerHTML = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(function (ch) {
      return '<button type="button" data-act="letter" data-l="' + ch + '" aria-pressed="' + (!f && L === ch) + '"' + (letters[ch] ? '' : ' disabled') + '>' + ch + '</button>';
    }).join('');
    var want = f ? avail : [L];
    var missing = want.filter(function (x) { return !IDXL[idxKey(sys, sec, x)]; });
    if (missing.length) {
      if (!idxPending) {
        idxPending = true;
        Promise.all(missing.map(function (x) { return loadLetter(sys, sec, x); })).then(function () { idxPending = false; renderList(); }).catch(function () { idxPending = false; });
      }
      return '<p class="hint">' + (f ? 'กำลังโหลดดัชนีทั้งหมดเพื่อกรอง…' : 'กำลังโหลดดัชนีอักษร ' + esc(L) + '…') + '</p>';
    }
    var rows = [];
    want.forEach(function (x) { rows = rows.concat(IDXL[idxKey(sys, sec, x)]); });
    var toks = fToks(f), sel = treeSelect(rows, toks, function () { return true; });
    if (!sel.show.length) return '<div class="empty"><b>ไม่พบคำในดัชนีที่ตรงกับ “' + esc(S.idxF) + '”</b><p>ลองพิมพ์คำภาษาอังกฤษ เช่น fever หรือ appendectomy พิมพ์หลายคำได้ เช่น fever typhoid</p></div>';
    var d = DB[sys], lastL = '', cut = sel.show.length > MAX_ROWS;
    var h = '<div class="list-head"><h2>' + esc(m.sections[sec]) + (f ? '' : ' · อักษร ' + esc(L)) + '</h2><span>' + countLabel(sel) + '</span></div><div class="box">';
    sel.show.slice(0, MAX_ROWS).forEach(function (i) {
      var e = rows[i];
      if (f && e.letter !== lastL) { h += '<div class="ix-head">' + esc(e.letter) + '</div>'; lastL = e.letter; }
      var lvl = e[0], pad = 18 + Math.min(lvl, 6) * 22;
      var label = (lvl ? new Array(lvl + 1).join('– ') : '') + e[1];
      var cls = 'ix-row' + (lvl === 0 ? ' lead' : '') + (sel.hit[i] ? ' hit' : '');
      if (e[2] && e[2].indexOf('TABLE:') === 0) {
        h += '<button type="button" class="' + cls + '" style="padding-left: ' + pad + 'px" data-act="opentable" data-t="' + esc(e[2].slice(6)) + '"><span>' + hl(label, toks) + '</span><span class="code">ตาราง</span></button>';
        return;
      }
      var c1 = stripMark(e[2]), ok = c1 && d.byCode[c1];
      var codes = (e[2] ? esc(e[2]) : '') + (e[3] ? ' ' + esc(e[3]) : '');
      var tm = (e[4] ? '<span class="tmk" title="รหัสดัดแปลงของไทย">#</span>' : '') + (e.ov ? '<span class="tag tag-ov" title="เพิ่มโดยผู้ดูแลระบบ">เพิ่ม</span> ' : '');
      if (ok) h += '<button type="button" class="' + cls + '" style="padding-left: ' + pad + 'px" data-act="sel" data-sys="' + sys + '" data-code="' + esc(c1) + '" aria-current="' + (S.sel[sys] === c1) + '"><span>' + tm + hl(label, toks) + '</span><span class="code">' + codes + '</span></button>';
      else h += '<div class="' + cls + '" style="padding-left: ' + pad + 'px"><span>' + tm + seeLinks(label, toks) + '</span>' + (codes ? '<span class="code na">' + codes + '</span>' : '') + '</div>';
    });
    h += '</div>';
    if (cut) h += '<p class="more">แสดง ' + MAX_ROWS + ' บรรทัดแรก พิมพ์คำในช่องกรองให้เจาะจงขึ้น</p>';
    return h;
  }

  // ---------- shared by the alphabetical index and the index tables ----------
  // filter words: every word must appear in the entry or one of its parent terms
  function fToks(f) { return String(f || '').toLowerCase().split(/[\s,()]+/).filter(Boolean); }
  function tokHit(low, toks) { for (var i = 0; i < toks.length; i++) if (low.indexOf(toks[i]) === -1) return false; return true; }
  // rows: [level, text, ...] with .low = text of the row and its parents. Returns the rows to show
  // (matches plus their parent terms, or the rows passing `browse` when there is no filter) and which rows matched.
  function treeSelect(rows, toks, browse) {
    var show = [], hit = {}, seen = {}, anc = [], n = 0;
    rows.forEach(function (r, i) {
      anc = anc.slice(0, r[0]); anc[r[0]] = i;
      var on = toks.length ? tokHit(r.low, toks) : browse(r);
      if (!on) return;
      if (toks.length) { n++; var own = String(r[1]).toLowerCase(); if (toks.some(function (t) { return own.indexOf(t) !== -1; })) hit[i] = true; }
      anc.slice(0, r[0]).forEach(function (j) { if (j !== undefined && !seen[j]) { seen[j] = 1; show.push(j); } });
      if (!seen[i]) { seen[i] = 1; show.push(i); }
    });
    show.sort(function (a, b) { return a - b; });
    return { show: show, hit: hit, n: n, filtered: toks.length > 0 };
  }
  function countLabel(sel) { return sel.filtered ? 'ตรง ' + sel.n.toLocaleString('th-TH') + ' รายการ' : sel.show.length.toLocaleString('th-TH') + ' รายการ'; }
  // "– see Allergy, drug" / "(see also Dermatitis)" become links that filter the current index or table
  function seeLinks(label, toks) {
    var m = /^(.*?\bsee(?: also)? )([A-Z][^()]*?)(\)?)$/.exec(label);
    if (!m) return hl(label, toks);
    return hl(m[1], toks) + '<a href="#" class="seeref" data-act="seeref" data-f="' + esc(m[2]) + '">' + hl(m[2], toks) + '</a>' + esc(m[3]);
  }

  // ---------- ICD-O morphology of neoplasms ----------
  var MORPH = null, morphPending = null;
  function loadMorph() {
    if (MORPH) return Promise.resolve(MORPH);
    if (morphPending) return morphPending;
    morphPending = (BASE.morph ? Promise.resolve(BASE.morph) : fetch(PATH.morph).then(function (r) { return r.json(); })).then(function (m0) {
      BASE.morph = m0;
      var m = applyMorphItems(clone(m0), OV.effective());
      var gmap = {};
      m.groups.forEach(function (g) { gmap[g.id] = g; });
      m.beh = {};
      m.behaviour.forEach(function (b) { m.beh[b.d] = b; });
      m.codes.forEach(function (c) {
        c.nd = c.c.toLowerCase().replace(/[^0-9]/g, '');
        c.low = (c.c + ' ' + c.en + ' ' + (gmap[c.g] ? gmap[c.g].en : '')).toLowerCase();
      });
      m.gmap = gmap;
      MORPH = m; return m;
    });
    return morphPending;
  }
  function morphMatch(c, q) {
    var t = q.toLowerCase().trim();
    if (!t) return true;
    var digits = t.replace(/^m/, '').replace(/[^0-9]/g, '');
    if (/^m?\d{3,4}(\/\d)?$/.test(t)) return c.nd.indexOf(digits) === 0;
    return t.split(/\s+/).every(function (w) { return c.low.indexOf(w) !== -1; });
  }
  function morphSite(c) {
    if (c.site) {
      var code = cellCode(c.site);
      return cellHtml(c.site, code) + (c.old ? ' <span class="tag tag-bad" title="รหัสนี้ตามรายการ ICD-O ฉบับเก่า WHO 2016 เปลี่ยนหรือยกเลิกรหัสนี้แล้ว ให้ตรวจกับ ICD-O-3">ฉบับเก่า</span>' : '');
    }
    var b = MORPH.beh[c.beh];
    return '<span class="site-any" title="ใช้ตารางเนื้องอกตามตำแหน่งที่ระบุ">ตามตำแหน่ง · ' + esc(b ? b.chap : '') + '</span>';
  }
  function morphRows(list, toks) {
    return list.map(function (c) {
      var b = MORPH.beh[c.beh];
      return '<tr><td class="v"><span class="code">' + esc(c.c) + '</span></td><td class="term">' + (c.ov ? '<span class="tag tag-ov">เพิ่ม</span> ' : '') + hl(c.en, toks) + '</td><td><span class="beh beh' + c.beh + '">/' + c.beh + ' ' + esc(b ? b.th : '') + '</span></td><td class="v">' + morphSite(c) + '</td></tr>';
    }).join('');
  }
  function renderMorph() {
    $('letters').innerHTML = '';
    if (!MORPH) {
      loadMorph().then(function () { renderList(); }).catch(function () { $('list').innerHTML = '<div class="empty"><b>โหลดรหัสสัณฐานวิทยาไม่สำเร็จ</b><p>ลองรีเฟรชหน้านี้</p></div>'; });
      return '<p class="hint">กำลังโหลดรหัสสัณฐานวิทยา…</p>';
    }
    var f = S.idxF.trim(), toks = f && !/^m?\d/i.test(f) ? f.toLowerCase().split(/\s+/) : [];
    var intro = '<div class="tbl-intro"><p>' + esc(MORPH.note_th) + '</p><details><summary>รหัสพฤติกรรม (หลักหลังเส้นเฉียง)</summary><table class="itbl behtbl"><tbody>' +
      MORPH.behaviour.map(function (b) { return '<tr><td class="v">/' + b.d + '</td><td>' + esc(b.th) + '<small>' + esc(b.en) + '</small></td><td>' + esc(b.chap) + '</td></tr>'; }).join('') + '</tbody></table></details></div>';
    var list = MORPH.codes.filter(function (c) { return morphMatch(c, f); });
    if (!list.length) return intro + '<div class="empty"><b>ไม่พบรหัสที่ตรงกับ “' + esc(f) + '”</b><p>พิมพ์ชื่อชนิดเนื้องอกภาษาอังกฤษ เช่น adenocarcinoma หรือรหัส เช่น M8140</p></div>';
    var h = intro + '<div class="list-head"><h2>รหัสสัณฐานวิทยาของเนื้องอก</h2><span>' + list.length.toLocaleString('th-TH') + ' รหัส</span></div>';
    h += '<div class="tbl-wrap"><table class="itbl morph"><thead><tr><th scope="col">รหัส ICD-O</th><th scope="col">ชนิดเนื้องอก<small>Morphology</small></th><th scope="col">พฤติกรรม<small>Behaviour</small></th><th scope="col">รหัส ICD-10<small>เมื่อไม่ระบุตำแหน่ง</small></th></tr></thead><tbody>';
    var g = null;
    list.forEach(function (c) {
      if (c.g !== g) { g = c.g; var G = MORPH.gmap[g]; h += '<tr class="lead"><td class="v"><span class="code">' + esc(g) + '</span></td><td colspan="3">' + esc(G ? G.en : '') + '</td></tr>'; }
      h += morphRows([c], toks);
    });
    h += '</tbody></table></div><p class="gref" style="margin-top: 10px">ที่มา: ' + esc(MORPH.source) + '</p>';
    return h;
  }
  // morphology entries that point at a given ICD-10 code (exact, or its category with an open 4th character)
  function morphFor(x) {
    if (!MORPH || !/^[CD]/.test(x.c)) return [];
    var cat = x.c.slice(0, 3);
    return MORPH.codes.filter(function (c) { return c.site && (c.site === x.c || (c.site === cat + '.-' && x.c.indexOf(cat) === 0) || c.site === cat && x.c === cat); });
  }

  // ---------- index tables (drugs & chemicals, neoplasm, abortion) ----------
  var TABLES = null, tablesPending = null;
  function loadTables() {
    if (TABLES) return Promise.resolve(TABLES);
    if (tablesPending) return tablesPending;
    tablesPending = (BASE.tables ? Promise.resolve(BASE.tables) : fetch(PATH.tables).then(function (r) { return r.json(); })).then(function (t0) {
      BASE.tables = t0;
      var t = applyRowItems(clone(t0), OV.effective());
      Object.keys(t).forEach(function (name) {
        var stack = [];
        t[name].rows.forEach(function (r) {
          stack = stack.slice(0, r[0]); stack[r[0]] = r[1];
          r.path = stack.slice(0, r[0] + 1);
          r.low = r.path.join(' ').toLowerCase();
          var key = name === 'neoplasm' ? (r.path[1] || '') : (r.path[0] || '');
          r.letter = (key.replace(/^[^A-Za-z]+/, '')[0] || '').toUpperCase();
        });
      });
      // drug names become search words for their poisoning and adverse-effect codes
      var d = DB.icd10;
      t.drugs.rows.forEach(function (r) {
        [r[2], r[6]].forEach(function (v) { var c = cellCode(v); if (c && d.byCode[c]) d.byCode[c].hay += ' ' + r.low; });
      });
      TABLES = t; return t;
    });
    return tablesPending;
  }
  function cellCode(v) { return String(v || '').replace(/(\.-)+$/, '').replace(/[†*()]/g, ''); }
  function cellHtml(v, code) {
    if (!v) return '';
    var shown = String(v).replace(/(\.-)+$/, '.-');
    if (code && DB.icd10.byCode[code]) return '<button type="button" class="cref" data-act="sel" data-sys="icd10" data-code="' + esc(code) + '">' + esc(shown) + '</button>';
    return '<span class="na" title="ไม่พบรหัสนี้ในบัญชีจำแนกฉบับนี้">' + esc(shown) + '</span>';
  }
  function renderTable(name) {
    if (!TABLES) {
      loadTables().then(function () { renderList(); }).catch(function () { $('list').innerHTML = '<div class="empty"><b>โหลดตารางไม่สำเร็จ</b><p>ลองรีเฟรชหน้านี้</p></div>'; });
      return '<p class="hint">กำลังโหลดตาราง…</p>';
    }
    var T = TABLES[name], rows = T.rows, f = S.idxF.toLowerCase().trim();
    var lettersOn = name !== 'abortion' && name !== 'transport';
    var avail = {};
    rows.forEach(function (r) { if (r.letter) avail[r.letter] = true; });
    var L = S.letter['T:' + name];
    if (lettersOn && (!L || !avail[L])) L = S.letter['T:' + name] = Object.keys(avail).sort()[0];
    $('letters').innerHTML = lettersOn ? 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(function (ch) {
      return '<button type="button" data-act="letter" data-l="' + ch + '" aria-pressed="' + (!f && L === ch) + '"' + (avail[ch] ? '' : ' disabled') + '>' + ch + '</button>';
    }).join('') : '';
    // which rows to show: matches plus their parent terms, or one letter (same rules as the alphabetical index)
    var toks = fToks(f);
    var sel = treeSelect(rows, toks, function (r) { return !lettersOn || r.letter === L || (name === 'neoplasm' && r[0] === 0); });
    var show = sel.show;
    var intro = '';
    if (name === 'drugs') intro = '<div class="tbl-intro"><p><b>พิษจากยาหรือสารเคมี:</b> ลงรหัสพิษ (T36–T65) เป็นการวินิจฉัย คู่กับรหัสสาเหตุภายนอกตามเจตนา คือ อุบัติเหตุ (X40–X49) ทำร้ายตนเอง (X60–X69) หรือไม่ทราบเจตนา (Y10–Y19) และลงรหัสอาการที่เกิดขึ้นเพิ่ม</p><p><b>ผลไม่พึงประสงค์จากยาที่ใช้ถูกต้องตามขนาด:</b> ลงรหัสอาการหรือภาวะที่เกิด เช่น ผื่น คู่กับรหัสในคอลัมน์สุดท้าย (Y40–Y59) ไม่ใช้รหัส T</p><p>รหัส X40–X49 และ X60–X69 ต้องเติมหลักสถานที่เกิดเหตุ (.-)</p></div>';
    if (name === 'neoplasm') intro = '<div class="tbl-intro"><p>เลือกคอลัมน์ตามพฤติกรรมของเนื้องอกที่ระบุในผลชิ้นเนื้อหรือบันทึกแพทย์ ถ้าไม่ระบุ ให้ดูชนิดทางพยาธิวิทยาในดัชนีก่อนว่าให้ใช้คอลัมน์ใด</p><details><summary>หมายเหตุของตาราง (' + T.notes.length + ')</summary>' + T.notes.map(function (n) { return '<p>' + esc(n) + '</p>'; }).join('') + '</details></div>';
    if (name === 'transport') intro = '<div class="tbl-intro"><p>' + esc(T.note) + '</p><p>ตัวอย่าง: ผู้ขับขี่จักรยานยนต์ชนกับรถยนต์บนถนน ใช้แถว “ผู้ใช้รถจักรยานยนต์” คอลัมน์ “รถยนต์ รถกระบะ หรือรถตู้” ได้ V23 แล้วเติมหลักที่ 4 เป็น V23.4 (ผู้ขับขี่ในอุบัติเหตุจราจร)</p></div>';
    var abType = S.abType || 'O06';
    if (name === 'abortion') {
      intro = '<div class="tbl-intro"><p>' + esc(T.note) + ' เลือกชนิดของการแท้งก่อน แล้วรหัสในตารางจะเติมให้ครบ</p></div>' +
        '<div class="chips" style="margin-bottom: 12px"><span>ชนิดการแท้ง:</span>' + T.types.map(function (t) { return '<button type="button" class="chip" data-act="abtype" data-c="' + t.c + '" aria-pressed="' + (t.c === abType) + '">' + esc(t.c + ' ' + t.th) + '</button>'; }).join('') + '</div>';
    }
    if (!show.length) return intro + '<div class="empty"><b>ไม่พบรายการที่ตรงกับ “' + esc(S.idxF) + '”</b><p>ลองพิมพ์ชื่อสามัญทางยาหรือชื่อตำแหน่งภาษาอังกฤษ พิมพ์หลายคำได้ เช่น lung lower lobe</p></div>';
    var ncol = T.cols.length, cut = show.length > MAX_ROWS;
    var h = intro + '<div class="list-head"><h2>' + esc(T.title) + (f ? '' : lettersOn ? ' · อักษร ' + esc(L) : '') + '</h2><span>' + countLabel(sel) + '</span></div>';
    h += '<div class="tbl-wrap"><table class="itbl"><thead><tr><th scope="col">' + (name === 'drugs' ? 'สาร' : name === 'neoplasm' ? 'ตำแหน่ง' : name === 'transport' ? 'ผู้บาดเจ็บ / คู่กรณี →' : 'ภาวะแทรกซ้อน') + '</th>' +
      T.cols.map(function (c) { return '<th scope="col">' + esc(c.th) + '<small>' + esc(c.en) + (c.range ? ' · ' + esc(c.range) : '') + '</small></th>'; }).join('') + '</tr></thead><tbody>';
    show.slice(0, MAX_ROWS).forEach(function (i) {
      var r = rows[i];
      h += '<tr class="' + (r[0] === 0 ? 'lead' : '') + (sel.hit[i] ? ' hit' : '') + '"><td class="term" style="padding-left: ' + (10 + r[0] * 18) + 'px">' + (r[2 + ncol] ? '<span class="tmk" title="ดัดแปลงสำหรับไทย">#</span>' : '') + (r.ov ? '<span class="tag tag-ov">เพิ่ม</span> ' : '') + (r[0] ? '– ' : '') + seeLinks(r[1], toks) + '</td>';
      for (var k = 0; k < ncol; k++) {
        var v = r[2 + k], code;
        if (name === 'abortion') code = v ? (k === 2 ? 'O08' : abType) + v : '';
        else code = cellCode(v);
        h += '<td class="v">' + cellHtml(name === 'abortion' && v ? code : v, code) + '</td>';
      }
      h += '</tr>';
      if (r[3 + ncol]) h += '<tr class="rnote"><td colspan="' + (ncol + 1) + '">' + esc(r[3 + ncol]) + '</td></tr>';
    });
    h += '</tbody></table></div>';
    if (cut) h += '<p class="more">แสดง ' + MAX_ROWS + ' บรรทัดแรก พิมพ์คำในช่องกรองให้เจาะจงขึ้น</p>';
    return h;
  }
  // where a code appears in the tables (shown on the code's detail card)
  function tableRefs(x) {
    if (!TABLES || S.sys !== 'icd10') return null;
    var c = x.c, out = { drugs: [], neoplasm: [] };
    var col = /^T(3[6-9]|[45]\d|6[0-5])/.test(c) ? 2 : /^Y(4\d|5\d)/.test(c) ? 6 : null;
    if (col) TABLES.drugs.rows.forEach(function (r) { if (cellCode(r[col]) === c) out.drugs.push(r); });
    if (/^[CD]\d/.test(c)) TABLES.neoplasm.rows.forEach(function (r) { for (var k = 2; k < 7; k++) if (cellCode(r[k]) === c) { out.neoplasm.push(r); break; } });
    return out;
  }

  function renderTree() {
    $('secChips').innerHTML = '';
    var d = DB[S.sys];
    var counts = {};
    d.codes.forEach(function (x) { var b = d.blockMap[x.b]; if (b) counts[b.ch] = (counts[b.ch] || 0) + 1; });
    var h = '<div class="box">';
    (d.chapters || []).forEach(function (ch) {
      var open = !!S.openCh[S.sys + ch.id];
      var title = ch.th || ch.en;
      h += '<button type="button" class="tr-ch" data-act="tch" data-id="' + esc(ch.id) + '" aria-expanded="' + open + '">' + ICON.chev + '<span>' + (S.sys === 'icd10' ? 'บทที่ ' : 'บท ') + esc(ch.id) + ' · ' + esc(title) + ' <span style="font-weight: 400; color: var(--muted)">(' + esc(ch.range) + ')</span></span><span class="n">' + (counts[ch.id] || 0).toLocaleString('th-TH') + '</span></button>';
      if (!open) return;
      (d.blocks || []).filter(function (b) { return b.ch === ch.id; }).forEach(function (b) {
        var bo = !!S.openBl[S.sys + b.id];
        var list = d.byBlock[b.id] || [];
        h += '<button type="button" class="tr-bl" data-act="tbl" data-id="' + esc(b.id) + '" aria-expanded="' + bo + '">' + ICON.chev + '<span>' + esc(b.range) + ' · ' + esc(b.th || b.en) + '</span><span class="n">' + list.length + '</span></button>';
        if (!bo) return;
        list.forEach(function (x) {
          h += '<button type="button" class="tr-code" style="padding-left: ' + (64 + x.depth * 22) + 'px" data-act="sel" data-sys="' + S.sys + '" data-code="' + esc(x.c) + '" aria-current="' + (S.sel[S.sys] === x.c) + '"><span class="code">' + esc(x.c) + '</span><span>' + esc(x.th || x.en) + '</span></button>';
        });
      });
    });
    return h + '</div>';
  }

  function renderFavorites() {
    var h = '<div class="fav-sec"><div class="list-head"><h2>รายการโปรด</h2><span>' + favs.length + ' รหัส</span></div>';
    var fl = favs.filter(function (e) { return DB[e.sys] && DB[e.sys].byCode[e.c]; });
    h += fl.length ? '<ul class="results">' + fl.map(function (e) { return resRow(DB[e.sys].byCode[e.c], e.sys, [], { sysColor: true }); }).join('') + '</ul>'
      : '<div class="empty"><b>ยังไม่มีรายการโปรด</b><p>กดปุ่มดาวในหน้ารายละเอียดรหัสเพื่อเก็บรหัสที่ใช้บ่อยไว้ที่นี่ รายการนี้เก็บในเบราว์เซอร์เครื่องนี้เท่านั้น</p></div>';
    h += '</div>';
    var hl2 = hist.filter(function (e) { return DB[e.sys] && DB[e.sys].byCode[e.c]; }).slice(0, 30);
    if (hl2.length) h += '<div class="fav-sec"><div class="list-head"><h2>ประวัติการดูรหัส</h2><button type="button" class="link" data-act="clearhist">ล้างประวัติ</button></div><ul class="results">' + hl2.map(function (e) { return resRow(DB[e.sys].byCode[e.c], e.sys, [], { sysColor: true }); }).join('') + '</ul></div>';
    return h;
  }

  function renderList() {
    if (!S.ready) return;
    var el = $('list');
    if (S.view === 'search') el.innerHTML = renderSearchList();
    else if (S.view === 'index') el.innerHTML = S.imode === 'alpha' ? renderAlpha() : renderTree();
    else if (S.view === 'favorites') el.innerHTML = renderFavorites();
  }

  function isFav(sys, c) { return favs.some(function (e) { return e.sys === sys && e.c === c; }); }

  function noteBlock(t, items, sys) {
    if (!items || !items.length) return '';
    return '<ul' + (t === 'en' ? ' class="en-list" lang="en"' : '') + '>' + items.map(function (it) {
      var sub = /^•\s*/.test(it);
      return '<li' + (sub ? ' class="sub"' : '') + '>' + linkify(it.replace(/^•\s*/, ''), sys) + '</li>';
    }).join('') + '</ul>';
  }
  function renderNotes(groups, sys) {
    var h = '<div class="notes">';
    NOTE_ORDER.forEach(function (t) {
      var g = groups.filter(function (o) { return (o.n.t || 'note') === t; });
      if (!g.length) return;
      h += '<div class="note-g"><b>' + NOTE_LABEL[t] + '</b>';
      g.forEach(function (o) {
        if (o.src) h += '<div class="src">' + esc(o.src) + '</div>';
        if (o.n.ov) h += '<div class="src"><span class="tag tag-ov">เพิ่มโดยผู้ดูแลระบบ</span></div>';
        if (o.n.th && o.n.th.length) { h += noteBlock('th', o.n.th, sys) + noteBlock('en', o.n.en, sys); }
        else h += noteBlock('th', o.n.en, sys);
      });
      h += '</div>';
    });
    return h + '</div>';
  }

  // curated short guidance tied to code patterns
  function curated(x, sys, anc) {
    var keys = [], c = x.c, c3 = c.slice(0, 3);
    if (sys === 'icd10') {
      if (/^E1[0-4]/.test(c)) keys.push('dm4');
      if (x.da === '†' || x.da === '*' || anc.some(function (a) { return a.da; })) keys.push('dagger');
      if (c[0] === 'O') keys.push('preg');
      if (c[0] === 'R') keys.push('symptom');
      if (/^J1[2-8]/.test(c3)) keys.push('organism');
      if (c3 === 'I10') keys.push('htn');
      if (c3 === 'A90' || c3 === 'A91') keys.push('ver');
      if (/\.9$/.test(c) && /unspecified/i.test(x.en)) keys.push('unspec');
    } else {
      if (/^47\.0|^51\.2/.test(c)) keys.push('method');
      if (/^47\.0/.test(c)) keys.push('incidental');
      if (/^74\./.test(c)) keys.push('csAlso');
      if (/^13\.[1-6]/.test(c)) keys.push('iol');
      if (c === '96.04') keys.push('vent');
      if (x.drg === 'or') keys.push('mainProc');
    }
    var gs = keys.map(function (k) { return G[k]; }).filter(Boolean);
    if (!gs.length && G.verify) gs = [G.verify];
    return gs;
  }

  function nhsoMatch(pat, x, sys) {
    var c = x.c;
    if (sys === 'icd9') {
      var m9 = /^(\d\d\.\d{1,2})-(\d\d\.\d{1,2})$/.exec(pat);
      if (m9) return c.localeCompare(m9[1], 'en', { numeric: true }) >= 0 && c.localeCompare(m9[2], 'en', { numeric: true }) <= 0;
      return c === pat || (pat.length === 4 && c.indexOf(pat) === 0);
    }
    var m = /^([A-Z]\d\d)-([A-Z]\d\d)(?:\.(\d))?$/.exec(pat);
    if (m) {
      var c3 = c.slice(0, 3);
      if (!(c3[0] === m[1][0] && c3 >= m[1] && c3 <= m[2])) return false;
      return m[3] ? c.charAt(4) === m[3] : true;
    }
    if (pat.length === 3) return c.slice(0, 3) === pat;
    return c === pat || c.indexOf(pat) === 0;
  }
  function nhsoFor(x, sys) {
    if (!NHSO) return [];
    return NHSO.topics.filter(function (t) { return t.sys === sys && t.codes.some(function (p) { return nhsoMatch(p, x, sys); }); });
  }
  function nhsoItem(t, open) {
    return '<details class="nhso"' + (open ? ' open' : '') + '><summary>' + esc(t.title) + '<span class="meta">' + esc(t.sec) + ' · คู่มือ สปสช. 2562 หน้า ' + t.page + (t.codes.length ? ' · <b>' + esc(t.codes.join(', ')) + '</b>' : '') + '</span></summary><div class="body">' + linkify(t.text, t.sys) + '</div></details>';
  }

  function renderDetail() {
    var el = $('detail');
    if (!S.ready) return;
    var sys = S.sys, d = DB[sys];
    var x = S.sel[sys] && d.byCode[S.sel[sys]];
    if (!x) { el.innerHTML = '<div class="card" style="text-align: center; color: var(--muted)">เลือกรหัสจากรายการหรือดัชนีเพื่อดูรายละเอียด</div>'; return; }
    var anc = ancestors(d, x);
    var blk = d.blockMap[x.b];
    var ch = blk && d.chapterMap[blk.ch];
    var h = '<button type="button" class="btn back" data-act="back">' + ICON.back + 'กลับไปรายการ</button><article class="card">';
    h += '<div class="badges"><span class="badge b-sys">' + SYS[sys].long + '</span>';
    if (x.who_del) h += '<span class="badge b-bad">' + ICON.warn + 'ไม่มีใน ICD-10 WHO 2016</span>';
    else if (x.bad) h += '<span class="badge b-bad">' + ICON.warn + 'รหัสงดใช้ (@) ห้ามลงรหัสนี้</span>';
    else if (x.leaf) h += '<span class="badge b-ok">' + ICON.check + 'รหัสสมบูรณ์ · ใช้ลงรหัสได้</span>';
    else h += '<span class="badge b-warn">' + ICON.warn + 'ยังไม่ครบหลัก · เลือกรหัสย่อย</span>';
    if (x.ov === 'add') h += '<span class="badge b-ov">เพิ่มโดยผู้ดูแลระบบ</span>';
    else if (x.ov === 'edit') h += '<span class="badge b-ov">ปรับปรุงโดยผู้ดูแลระบบ</span>';
    if (sys === 'icd10' && x.tm && !x.who && !x.who_del) h += '<span class="badge b-info">รหัสเพิ่มเติมของ ICD-10-TM (ไม่มีใน WHO)</span>';
    if (x.da === '†') h += '<span class="badge b-warn">† รหัสสาเหตุ ต้องคู่กับรหัส *</span>';
    if (x.da === '*') h += '<span class="badge b-warn">* รหัสอาการแสดง ต้องคู่กับรหัส †</span>';
    if (x.drg === 'or') h += '<span class="badge b-or">OR procedure</span>';
    if (x.drg === 'drg') h += '<span class="badge b-drg">Non-OR · มีผลต่อ ThaiDRG</span>';
    h += '</div>';
    h += '<div class="big" id="bigCode">' + esc(x.c) + esc(x.da || '') + '</div>';
    h += '<h1 class="dtitle">' + esc(x.th || x.en) + '</h1>' + (x.th ? '<p class="dsub" lang="en">' + esc(x.en) + '</p>' : '');
    var fav = isFav(sys, x.c);
    h += '<div class="actions">' +
      '<button type="button" class="btn primary" data-act="copy" data-text="' + esc(x.c) + '">' + ICON.copy + 'คัดลอกรหัส</button>' +
      '<button type="button" class="btn" data-act="copy" data-text="' + esc(x.c + ' ' + x.en) + '">คัดลอกรหัส + ชื่อ</button>' +
      '<button type="button" class="btn icon" data-act="fav" aria-pressed="' + fav + '" aria-label="' + (fav ? 'เอาออกจากรายการโปรด' : 'เพิ่มในรายการโปรด') + '" title="' + (fav ? 'เอาออกจากรายการโปรด' : 'เพิ่มในรายการโปรด') + '">' + ICON.star + '</button></div>';
    if (x.who_del) {
      h += '<div class="whobox"><b>รหัสนี้อยู่ใน ICD-10-TM 2009 แต่ไม่มีใน ICD-10 WHO ฉบับ 2016</b>' +
        (x.rep && x.rep.length ? '<p>ใช้รหัสนี้แทน: ' + x.rep.map(function (c) { var y = d.byCode[c]; return '<button type="button" class="cref" data-act="sel" data-sys="' + sys + '" data-code="' + esc(c) + '">' + esc(c) + '</button>' + (y ? ' ' + esc(y.th || y.en) : ''); }).join(' · ') + '</p>'
          : '<p>WHO จัดหมวดนี้ใหม่ ให้ดูรหัสในหมวด ' + esc(x.c.slice(0, 3)) + ' หรือค้นจากดัชนี</p>') + '</div>';
    }
    if (x.tm_old) h += '<p class="ocr-note">ใน ICD-10-TM 2009 รหัสนี้ชื่อ “' + esc(x.tm_old.th || x.tm_old.en) + '” (' + esc(x.tm_old.en) + ') ความหมายใน WHO 2016 ต่างออกไป</p>';
    if (x.tm_bad) h += '<p class="ocr-note">ICD-10-TM 2009 กำหนดให้งดใช้รหัสนี้ (@) แต่ WHO 2016 ยังใช้ได้</p>';
    if (x.thx) h += '<p class="ocr-note">ชื่อภาษาไทยนี้แปลเพิ่มสำหรับเว็บนี้ ไม่ได้มาจากเล่ม ICD-10-TM</p>';
    if (x.gen) h += '<p class="ocr-note">รหัสนี้สร้างจากรายการแบ่งย่อยหลักที่ 4 ที่พิมพ์ไว้ครั้งเดียวต้นกลุ่มในเล่ม</p>';
    if (sys === 'icd10' && /^V[0-8]/.test(x.c)) h += '<p class="ocr-note"><button type="button" class="link" data-act="opentable" data-t="transport">เปิดตารางอุบัติเหตุการขนส่งทางบก</button> เพื่อเลือกรหัสตามผู้บาดเจ็บและคู่กรณี</p>';
    if (x.place && DB.icd10.place) {
      h += '<div class="placebox"><b>ต้องระบุสถานที่เกิดเหตุ</b> ใช้รหัสสถานที่เกิดเหตุร่วมกับรหัส W00–Y34<ol>' +
        DB.icd10.place.en.map(function (p, i) { return '<li><span>.' + i + '</span>' + esc(p) + '</li>'; }).join('') + '</ol></div>';
    }

    h += '<section class="sec"><h3>ลำดับชั้นในบัญชีจำแนก</h3><ol class="path">';
    if (ch) h += '<li><span>บท</span><span>' + esc(ch.id) + ' · ' + esc(ch.th || ch.en) + ' (' + esc(ch.range) + ')' + (ch.th ? '<span class="en" lang="en">' + esc(ch.en) + '</span>' : '') + '</span></li>';
    if (blk) h += '<li><span>กลุ่ม</span><span>' + esc(blk.range) + ' · ' + esc(blk.th || blk.en) + (blk.th ? '<span class="en" lang="en">' + esc(blk.en) + '</span>' : '') + '</span></li>';
    anc.forEach(function (a) { h += '<li><span>รหัส</span><span><button type="button" class="link code" data-act="sel" data-sys="' + sys + '" data-code="' + esc(a.c) + '">' + esc(a.c) + '</button> ' + esc(a.th || a.en) + '</span></li>'; });
    h += '</ol></section>';

    var kids = d.kids[x.c] || [];
    if (kids.length) {
      h += '<section class="sec"><h3>รหัสย่อย (' + kids.length + ')</h3><div class="minis">' + kids.slice(0, 40).map(function (k) { return '<button type="button" class="mini" data-act="sel" data-sys="' + sys + '" data-code="' + esc(k.c) + '"><span class="code">' + esc(k.c) + '</span>' + esc(k.th || k.en) + '</button>'; }).join('') + (kids.length > 40 ? '<span class="hint">และอีก ' + (kids.length - 40) + ' รหัส</span>' : '') + '</div></section>';
    }

    var notes = [];
    (x.notes || []).forEach(function (n) { notes.push({ n: n, src: '' }); });
    anc.slice().reverse().forEach(function (a) { (a.notes || []).forEach(function (n) { notes.push({ n: n, src: 'จากรหัส ' + a.c }); }); });
    if (blk && blk.notes) blk.notes.forEach(function (n) { notes.push({ n: n, src: 'จากกลุ่ม ' + blk.range }); });
    if (notes.length) h += '<section class="sec"><h3>หมายเหตุในบัญชีจำแนก</h3>' + renderNotes(notes, sys) + '</section>';
    if (ch && ch.notes && ch.notes.length) {
      h += '<details class="more-notes"><summary>หมายเหตุระดับบท ' + esc(ch.id) + ' (' + ch.notes.length + ')</summary>' + renderNotes(ch.notes.map(function (n) { return { n: n, src: '' }; }), sys) + '</details>';
    }

    var un = notesFor(x, sys);
    if (un.length) {
      h += '<section class="sec unit-notes"><h3>หมายเหตุของหน่วยงาน (' + un.length + ')</h3>' + un.map(function (n) {
        return '<div class="unote"><b>' + esc(n.title || 'หมายเหตุ') + '</b><p>' + linkify(n.body || '', sys).replace(/\n/g, '<br>') + '</p>' +
          '<span class="meta">ใช้กับ ' + esc((n.codes || []).join(', ')) + (n.updated ? ' · ปรับปรุง ' + esc(String(n.updated).slice(0, 10)) : '') + '</span></div>';
      }).join('') + '</section>';
    }
    if (x.ovMemo) h += '<p class="ocr-note">บันทึกของผู้ดูแล: ' + esc(x.ovMemo) + '</p>';
    var refs = tableRefs(x);
    if (refs) {
      [['drugs', 'พบในตารางยาและสารเคมี'], ['neoplasm', 'พบในตารางเนื้องอก']].forEach(function (p) {
        var list = refs[p[0]];
        if (!list.length) return;
        h += '<section class="sec"><div class="sec-head"><h3>' + p[1] + ' (' + list.length + ')</h3><button type="button" class="link" data-act="opentable" data-t="' + p[0] + '">เปิดตาราง</button></div><div class="subst">' +
          list.slice(0, 40).map(function (r) { var label = r.path.slice(p[0] === 'neoplasm' ? 1 : 0).join(', '); return '<button type="button" data-act="opentable" data-t="' + p[0] + '" data-f="' + esc(r[1]) + '">' + esc(label) + '</button>'; }).join('') +
          (list.length > 40 ? '<span class="hint">และอีก ' + (list.length - 40) + ' รายการ</span>' : '') + '</div></section>';
      });
    } else if (sys === 'icd10' && /^(T[3-6]|Y[45]|[CD]\d)/.test(x.c) && !TABLES) {
      loadTables().then(function () { renderDetail(); }).catch(function () {});
    }

    var mf = sys === 'icd10' ? morphFor(x) : [];
    if (mf.length) {
      h += '<section class="sec"><div class="sec-head"><h3>ชนิดเนื้องอก (ICD-O) ที่ให้ใช้รหัสนี้เมื่อไม่ระบุตำแหน่ง (' + mf.length + ')</h3><button type="button" class="link" data-act="opentable" data-t="morph">เปิดรายการ ICD-O</button></div>' +
        '<div class="tbl-wrap"><table class="itbl morph"><tbody>' + morphRows(mf.slice(0, 30), []) + '</tbody></table></div></section>';
    } else if (sys === 'icd10' && /^[CD]\d/.test(x.c) && !MORPH) {
      loadMorph().then(function () { renderDetail(); }).catch(function () {});
    }

    var topics = nhsoFor(x, sys);
    if (topics.length) {
      h += '<section class="sec"><div class="sec-head"><h3>เกณฑ์ตรวจสอบเวชระเบียน สปสช. 2562</h3><button type="button" class="link" data-act="view" data-view="guide">ดูทั้งหมด</button></div>' + topics.map(function (t, i) { return nhsoItem(t, i === 0 && topics.length === 1); }).join('') + '</section>';
    } else if (!NHSO) {
      h += '<p class="ocr-note">กำลังโหลดเกณฑ์ตรวจสอบเวชระเบียน…</p>';
    }

    var gs = curated(x, sys, anc);
    if (gs.length) h += '<section class="sec"><div class="sec-head"><h3>แนวทางที่เกี่ยวข้อง</h3><button type="button" class="link" data-act="view" data-view="guide">ดูแนวทางทั้งหมด</button></div><div class="guides">' + gs.map(function (g) { return '<div class="guide"><b>' + esc(g.t) + '</b><p>' + esc(g.d) + '</p></div>'; }).join('') + '</div></section>';

    var sib = (x.p ? (d.kids[x.p] || []) : (d.byBlock[x.b] || []).filter(function (y) { return !y.p; })).filter(function (y) { return y.c !== x.c; }).slice(0, 10);
    if (sib.length) h += '<section class="sec"><h3>รหัสข้างเคียง</h3><div class="minis">' + sib.map(function (y) { return '<button type="button" class="mini" data-act="sel" data-sys="' + sys + '" data-code="' + esc(y.c) + '"><span class="code">' + esc(y.c) + '</span>' + esc(y.th || y.en) + '</button>'; }).join('') + '</div></section>';
    if (d.ocr) h += '<p class="ocr-note">ข้อมูล ICD-9-CM แปลงจากเอกสารสแกนด้วย OCR และตรวจความครบถ้วนเทียบกับดัชนีหัตถการแล้ว ควรตรวจทานกับเล่มต้นฉบับเมื่อพบข้อความผิดปกติ</p>';
    h += '</article>';
    el.innerHTML = h;
  }

  function renderUnitNotes() {
    var el = $('unitNotes');
    if (!el) return;
    if (!NOTES.length) { el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = '<h2>หมายเหตุและข้อตกลงของหน่วยงาน</h2>' + NOTES.slice().sort(function (a, b) { return String(b.updated || '').localeCompare(String(a.updated || '')); }).map(function (n) {
      var sys = n.sys === 'icd9' ? 'icd9' : 'icd10';
      return '<div class="unote"><b>' + esc(n.title || 'หมายเหตุ') + '</b><p>' + linkify(n.body || '', sys).replace(/\n/g, '<br>') + '</p><span class="meta">' + (n.sys === 'icd9' ? 'ICD-9-CM' : n.sys === 'all' ? 'ทุกระบบ' : 'ICD-10') + ' · ใช้กับ ' + esc((n.codes || []).join(', ') || '—') + '</span></div>';
    }).join('');
  }
  function renderGuide() {
    renderUnitNotes();
    if (!NHSO) { $('nhsoList').innerHTML = '<p class="hint">กำลังโหลด…</p>'; return; }
    var secs = NHSO.sections;
    $('nhsoSecs').innerHTML = '<button type="button" class="chip" data-act="gsec" data-s="" aria-pressed="' + (!S.gsec) + '">ทั้งหมด</button>' + secs.map(function (s) { return '<button type="button" class="chip" data-act="gsec" data-s="' + esc(s) + '" aria-pressed="' + (S.gsec === s) + '">' + esc(s) + '</button>'; }).join('');
    var q = S.gq.toLowerCase().trim();
    var list = NHSO.topics.filter(function (t) {
      if (S.gsec && t.sec !== S.gsec) return false;
      if (!q) return true;
      return (t.title + ' ' + t.codes.join(' ') + ' ' + t.text).toLowerCase().indexOf(q) !== -1;
    });
    $('nhsoCount').textContent = list.length + ' หัวข้อ';
    $('nhsoList').innerHTML = list.length ? list.slice(0, 120).map(function (t) { return nhsoItem(t, false); }).join('') + (list.length > 120 ? '<p class="more">แสดง 120 หัวข้อแรก พิมพ์คำค้นเพื่อให้แคบลง</p>' : '')
      : '<div class="empty"><b>ไม่พบหัวข้อที่ตรงกับ “' + esc(S.gq) + '”</b><p>ลองค้นด้วยชื่อโรคภาษาอังกฤษหรือรหัส</p></div>';
  }

  function renderChrome() {
    document.body.setAttribute('data-sys', S.sys);
    var v = S.view;
    Array.prototype.forEach.call(document.querySelectorAll('.nav button'), function (b) { b.setAttribute('aria-current', b.getAttribute('data-view') === v ? 'page' : 'false'); });
    Array.prototype.forEach.call(document.querySelectorAll('#sysSeg button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-sys') === S.sys)); });
    Array.prototype.forEach.call(document.querySelectorAll('#modeSeg button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-m') === S.imode)); });
    $('tools').hidden = v === 'guide' || v === 'favorites' || v === 'admin';
    $('adminView').hidden = v !== 'admin';
    if (v === 'admin') openAdmin();
    $('tbSearch').hidden = v !== 'search';
    $('tbIndex').hidden = v !== 'index';
    $('alphaCtrl').hidden = S.imode !== 'alpha';
    $('layout').hidden = v === 'guide' || v === 'admin';
    $('guide').hidden = v !== 'guide';
    $('layout').classList.toggle('show-detail', S.pane === 'detail');
    $('layout').classList.toggle('tblmode', v === 'index' && S.imode === 'alpha' && S.sys === 'icd10' && String(S.sec.icd10).indexOf('T:') === 0);
    $('qLabel').textContent = SYS[S.sys].label;
    $('q').placeholder = SYS[S.sys].ph;
    if ($('q').value !== S.q) $('q').value = S.q;
    $('qClear').hidden = !S.q;
    $('idxTitle').textContent = SYS[S.sys].idx;
    $('chips').innerHTML = '<span>ลองค้น:</span>' + SYS[S.sys].chips.map(function (c) { return '<button type="button" class="chip" data-act="chip" data-q="' + esc(c) + '">' + esc(c) + '</button>'; }).join('');
    $('favCount').textContent = favs.length ? String(favs.length) : '';
  }

  function renderAll() { renderChrome(); renderList(); renderDetail(); if (S.view === 'guide') renderGuide(); }

  // ---------- routing ----------
  function codeHash(sys, c) { return 'c-' + sys + '-' + c.replace(/\./g, '-'); }
  function setHash(name) { try { history.replaceState(null, '', '#' + name); } catch (e) {} }
  function applyHash() {
    var hsh = (location.hash || '').replace(/^#/, '');
    if (!hsh) return;
    var m = /^c-(icd10|icd9)-([A-Za-z0-9-]+)$/.exec(hsh);
    if (m) {
      var c = m[2].replace('-', '.');
      if (DB[m[1]] && !DB[m[1]].byCode[c]) c = m[2];
      if (DB[m[1]] && DB[m[1]].byCode[c]) { S.sys = m[1]; S.sel[m[1]] = c; S.pane = 'detail'; if (S.view === 'guide' || S.view === 'favorites') S.view = 'search'; }
      return;
    }
    if (['search', 'index', 'guide', 'favorites', 'admin'].indexOf(hsh) !== -1) S.view = hsh;
  }

  function select(sys, c) {
    S.sys = sys; S.sel[sys] = c; S.pane = 'detail';
    if (S.view === 'guide') S.view = 'search';
    hist = hist.filter(function (e) { return !(e.sys === sys && e.c === c); });
    hist.unshift({ sys: sys, c: c, t: Date.now() });
    hist = hist.slice(0, 60); lsSet('icd.hist', hist);
    setHash(codeHash(sys, c));
    renderAll();
    var dp = $('detail'); if (dp.scrollTo) dp.scrollTo(0, 0);
    if (window.matchMedia && window.matchMedia('(max-width: 859px)').matches) { try { $('layout').scrollIntoView({ block: 'start' }); } catch (e) {} }
  }

  var toastT;
  function toast(msg) { var t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(function () { t.hidden = true; }, 1800); }
  function copyText(text) {
    var done = function () { toast('คัดลอก “' + text + '” แล้ว'); };
    var fail = function () {
      try { var r = document.createRange(); r.selectNodeContents($('bigCode')); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); } catch (e) {}
      toast('คัดลอกอัตโนมัติไม่ได้ เลือกรหัสไว้ให้แล้ว กด Ctrl+C หรือคัดลอกเอง');
    };
    try { if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fail); else fail(); } catch (e) { fail(); }
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-act]');
    if (!b) return;
    var act = b.getAttribute('data-act');
    if (act === 'view') {
      ev.preventDefault();
      S.view = b.getAttribute('data-view'); S.pane = 'list';
      setHash(S.view); renderAll(); window.scrollTo(0, 0);
      if (S.view === 'search') $('q').focus();
    } else if (act === 'sys') {
      var ns = b.getAttribute('data-sys');
      if (ns !== S.sys) { S.sys = ns; S.pane = 'list'; renderAll(); }
    } else if (act === 'sel') {
      ev.preventDefault();
      select(b.getAttribute('data-sys'), b.getAttribute('data-code'));
    } else if (act === 'chip') {
      S.q = b.getAttribute('data-q'); S.abbrPick = {}; S.pane = 'list'; renderAll();
    } else if (act === 'letter') {
      var sk = S.sec[S.sys].indexOf('T:') === 0 ? S.sec[S.sys] : S.sys + S.sec[S.sys];
      S.letter[sk] = b.getAttribute('data-l'); S.idxF = ''; $('idxf').value = ''; renderList();
    } else if (act === 'opentable') {
      S.sys = 'icd10'; S.view = 'index'; S.imode = 'alpha'; S.sec.icd10 = 'T:' + b.getAttribute('data-t'); S.pane = 'list';
      S.idxF = b.getAttribute('data-f') || ''; $('idxf').value = S.idxF;
      setHash('index'); renderAll(); window.scrollTo(0, 0);
    } else if (act === 'abbr') {
      var ak = b.getAttribute('data-k'), ai = b.getAttribute('data-i');
      S.abbrPick = S.abbrPick || {};
      if (ai === '') delete S.abbrPick[ak]; else S.abbrPick[ak] = +ai;
      renderList();
    } else if (act === 'seeref') {
      ev.preventDefault();
      S.idxF = b.getAttribute('data-f'); $('idxf').value = S.idxF; renderList(); window.scrollTo(0, 0);
    } else if (act === 'abtype') {
      S.abType = b.getAttribute('data-c'); renderList();
    } else if (act === 'isec') {
      S.sec[S.sys] = b.getAttribute('data-s'); renderAll();
    } else if (act === 'imode') {
      S.imode = b.getAttribute('data-m');
      if (S.imode === 'tree') { var d = DB[S.sys], x = S.sel[S.sys] && d.byCode[S.sel[S.sys]]; if (x && d.blockMap[x.b]) { S.openCh[S.sys + d.blockMap[x.b].ch] = true; S.openBl[S.sys + x.b] = true; } }
      renderAll();
    } else if (act === 'tch') {
      var id = S.sys + b.getAttribute('data-id'); S.openCh[id] = !S.openCh[id]; renderList();
    } else if (act === 'tbl') {
      var bid = S.sys + b.getAttribute('data-id'); S.openBl[bid] = !S.openBl[bid]; renderList();
    } else if (act === 'copy') {
      copyText(b.getAttribute('data-text'));
    } else if (act === 'fav') {
      var c = S.sel[S.sys];
      if (!c) return;
      if (isFav(S.sys, c)) { favs = favs.filter(function (e) { return !(e.sys === S.sys && e.c === c); }); toast('เอา ' + c + ' ออกจากรายการโปรดแล้ว'); }
      else { favs.unshift({ sys: S.sys, c: c }); toast('เพิ่ม ' + c + ' ในรายการโปรดแล้ว'); }
      lsSet('icd.favs', favs); renderChrome(); renderDetail(); if (S.view === 'favorites') renderList();
    } else if (act === 'clearhist') {
      hist = []; lsSet('icd.hist', hist); renderList();
    } else if (act === 'back') {
      S.pane = 'list'; renderChrome(); window.scrollTo(0, 0);
    } else if (act === 'gsec') {
      S.gsec = b.getAttribute('data-s'); renderGuide();
    }
  });

  var qT;
  $('q').addEventListener('input', function (e) {
    var v = e.target.value;
    $('qClear').hidden = !v;
    clearTimeout(qT);
    qT = setTimeout(function () { S.q = v; S.abbrPick = {}; S.pane = 'list'; renderChrome(); renderList(); }, 140);
  });
  $('q').addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { var f = document.querySelector('#list .res, #list .ix-row'); if (f) { e.preventDefault(); f.focus(); } }
    if (e.key === 'Enter') { clearTimeout(qT); S.q = e.target.value; renderList(); var first = document.querySelector('#list .res'); if (first) first.click(); }
  });
  $('qClear').addEventListener('click', function () { S.q = ''; $('q').value = ''; renderChrome(); renderList(); $('q').focus(); });
  var fT;
  $('idxf').addEventListener('input', function (e) { var v = e.target.value; clearTimeout(fT); fT = setTimeout(function () { S.idxF = v; renderList(); }, 200); });
  var gT;
  $('gq').addEventListener('input', function (e) { var v = e.target.value; clearTimeout(gT); gT = setTimeout(function () { S.gq = v; renderGuide(); }, 160); });
  $('list').addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    var items = Array.prototype.slice.call(document.querySelectorAll('#list button.res, #list button.ix-row, #list button.tr-code'));
    var i = items.indexOf(document.activeElement);
    if (i === -1) return;
    e.preventDefault();
    if (e.key === 'ArrowDown' && items[i + 1]) items[i + 1].focus();
    if (e.key === 'ArrowUp') { if (i > 0) items[i - 1].focus(); else if (S.view === 'search') $('q').focus(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target.tagName;
    if (t === 'INPUT' || t === 'TEXTAREA' || e.target.isContentEditable) return;
    e.preventDefault();
    if (S.view !== 'search') { S.view = 'search'; S.pane = 'list'; setHash('search'); renderAll(); }
    $('q').focus();
  });
  window.addEventListener('hashchange', function () { applyHash(); renderAll(); });

  // =====================================================================
  // OVERLAY: data added or changed by the developer/administrator.
  // Base files under data/ are built from the source books and never edited here.
  // Additions come from two layers, applied in this order:
  //   1. data/overlay.json      (local backend: the admin page in the project folder writes this file)
  //   2. db collection overlay  (online backend: the admin page on the published site)
  // Items with the same id: the online layer wins. An online item {deleted:true} hides a file item.
  // Item kinds: code | abbr | note | row | morph | idx  (see docs/backend.md)
  // =====================================================================
  var OV = {
    file: [], db: [], mode: 'loading', canEdit: false, dbns: null, user: null, dirty: false, fileHandle: null,
    effective: function () {
      var m = {};
      this.file.forEach(function (i) { if (i && i.id) m[i.id] = i; });
      this.db.forEach(function (i) { if (i && i.id) m[i.id] = i; });
      return Object.keys(m).map(function (k) { return m[k]; }).filter(function (i) { return !i.deleted; });
    }
  };
  function clone(o) { try { return structuredClone(o); } catch (e) { return JSON.parse(JSON.stringify(o)); } }
  function lc(s) { return String(s || '').toLowerCase().trim(); }

  // code patterns used by notes: "E11" (code and its subdivisions), "E10-E14" (category range), "J18.9" (exact), "*" (all)
  function patternHit(p, c) {
    p = String(p || '').trim().toUpperCase();
    if (!p) return false;
    if (p === '*') return true;
    if (p.indexOf('-') > 0) { var r = p.split('-'); var k = c.slice(0, r[0].length); return k >= r[0] && k <= r[1]; }
    return c === p || c.indexOf(p + '.') === 0 || (p.indexOf('.') !== -1 && c.indexOf(p) === 0);
  }
  function guessParent(c, by, sys) {
    if (sys === 'icd9') { var a = c.split('.'); if (a[1] && a[1].length === 2 && by[a[0] + '.' + a[1][0]]) return a[0] + '.' + a[1][0]; return null; }
    if (c.length === 6 && by[c.slice(0, 5)]) return c.slice(0, 5);
    if (c.length >= 5 && by[c.slice(0, 3)]) return c.slice(0, 3);
    return null;
  }
  function findBlock(d, c, sys) {
    if (sys === 'icd9') return c.split('.')[0];
    var cat = c.slice(0, 3), hit = null;
    (d.blocks || []).forEach(function (b) { var r = b.id.split('-'); if (r[0].length === 3 && cat >= r[0] && cat <= (r[1] || r[0])) hit = b.id; });
    return hit;
  }
  function applyCodeItems(d, sys, items) {
    var by = {};
    d.codes.forEach(function (x) { by[x.c] = x; });
    var hide = {};
    items.forEach(function (it) {
      if (it.kind !== 'code' || it.sys !== sys || !it.c) return;
      if (it.op === 'hide') { hide[it.c] = true; return; }
      var x = by[it.c];
      if (!x) {
        x = { c: it.c, en: '', th: '', leaf: true, ov: 'add' };
        var p = it.parent || guessParent(it.c, by, sys);
        if (p && by[p]) { x.p = p; by[p].leaf = false; x.b = by[p].b; }
        if (!x.b) x.b = it.block || findBlock(d, it.c, sys);
        d.codes.push(x); by[it.c] = x;
      } else if (!x.ov) x.ov = 'edit';
      ['en', 'th', 'da', 'drg'].forEach(function (f) { if (it[f] != null && it[f] !== '') x[f] = it[f]; });
      if (it.addNotes && it.addNotes.length) x.notes = (x.notes || []).concat(it.addNotes.map(function (n) { return { t: n.t || 'note', en: n.en || [], th: n.th || [], ov: 1 }; }));
      if (it.status === 'bad') x.bad = true;
      else if (it.status === 'ok') { delete x.bad; delete x.who_del; }
      if (it.memo) x.ovMemo = it.memo;
    });
    if (Object.keys(hide).length) d.codes = d.codes.filter(function (x) { return !hide[x.c]; });
    return d;
  }
  function applyAbbrItems(base, items) {
    var A = { icd10: Object.assign({}, base.icd10 || {}), icd9: Object.assign({}, base.icd9 || {}) };
    items.forEach(function (it) {
      if (it.kind !== 'abbr' || !A[it.sys]) return;
      String(it.keys || '').split('|').map(lc).filter(Boolean).forEach(function (k) {
        if (it.op === 'hide') { delete A[it.sys][k]; return; }
        A[it.sys][k] = [{ en: it.en || '', th: it.th || '', m: it.m || [], top: it.top || [], ov: 1 }].concat(A[it.sys][k] || []);
      });
    });
    return A;
  }
  // rows of drugs / neoplasm / abortion / transport tables: [level, term, cell1..cellN, tm, note?]
  function subtreeEnd(rows, i) { var l = rows[i][0], j = i + 1; while (j < rows.length && rows[j][0] > l) j++; return j; }
  function findRow(rows, lvl, term, from, to, loose) {
    var t = lc(term), i, end = to || rows.length;
    for (i = from || 0; i < end; i++) if (rows[i][0] === lvl && lc(rows[i][1]) === t) return i;
    if (loose) {   // index terms carry modifiers: "Diabetes, diabetic (mellitus)" matches "Diabetes"
      for (i = from || 0; i < end; i++) {
        var x = lc(rows[i][1]);
        if (rows[i][0] === lvl && (x.indexOf(t + ',') === 0 || x.indexOf(t + ' ') === 0)) return i;
      }
    }
    return -1;
  }
  function applyRowItems(t, items) {
    items.forEach(function (it) {
      if (it.kind !== 'row' || !t[it.table]) return;
      var T = t[it.table], rows = T.rows, ncol = T.cols.length;
      if (it.op === 'hide' || it.op === 'edit') {
        var i = findRow(rows, it.match ? it.match.lvl : 0, it.match ? it.match.term : '');
        if (i === -1) return;
        if (it.op === 'hide') { rows.splice(i, subtreeEnd(rows, i) - i); return; }
        var r = rows[i];
        (it.row || []).forEach(function (v, k) { if (k >= 1 && v != null && v !== '') r[k] = v; });
        r.ov = 1; return;
      }
      var nr = (it.row || []).slice(0, 2 + ncol);
      while (nr.length < 2 + ncol) nr.push('');
      nr[0] = +nr[0] || 0; nr.push(0);
      if (it.note) nr.push(it.note);
      nr.ov = 1;
      var pos = rows.length;
      if (nr[0] > 0 && it.parent) {
        var pi = findRow(rows, nr[0] - 1, it.parent);
        if (pi !== -1) pos = subtreeEnd(rows, pi);
      } else if (nr[0] === 0 && (it.table === 'drugs' || it.table === 'neoplasm')) {
        var key = lc(nr[1]);
        for (var k = it.table === 'neoplasm' ? 1 : 0; k < rows.length; k++) if (rows[k][0] === 0 && lc(rows[k][1]) > key) { pos = k; break; }
      }
      rows.splice(pos, 0, nr);
    });
    return t;
  }
  function applyMorphItems(m, items) {
    items.forEach(function (it) {
      if (it.kind !== 'morph' || !it.row || !it.row.c) return;
      var c = String(it.row.c).toUpperCase().trim();
      var i = -1;
      for (var k = 0; k < m.codes.length; k++) if (m.codes[k].c === c) { i = k; break; }
      if (it.op === 'hide') { if (i !== -1) m.codes.splice(i, 1); return; }
      var row = { c: c, g: it.row.g || c.slice(0, 4), en: it.row.en || '', beh: c.slice(-1), ov: 1 };
      if (it.row.site) row.site = it.row.site;
      if (!m.groups.some(function (g) { return g.id === row.g; })) m.groups.push({ id: row.g, en: it.row.gen || '' });
      if (i !== -1) { m.codes[i] = Object.assign({}, m.codes[i], row); return; }
      var pos = m.codes.length;
      for (var j = 0; j < m.codes.length; j++) if (m.codes[j].c > c) { pos = j; break; }
      m.codes.splice(pos, 0, row);
    });
    return m;
  }
  // alphabetical index rows: [level, text, code1, code2, tm]
  function applyIdxItems(rows, sys, sec, L, items) {
    items.forEach(function (it) {
      if (it.kind !== 'idx' || it.sys !== sys || it.sec !== sec) return;
      var lead = String(it.lead || '').trim();
      if (!lead || lead[0].toUpperCase() !== L) return;
      var path = [lead].concat((it.sub || []).map(function (x) { return String(x).trim(); }).filter(Boolean));
      var i = findRow(rows, 0, lead, 0, 0, true);
      if (i === -1) {
        var pos = rows.length;
        for (var k = 0; k < rows.length; k++) if (rows[k][0] === 0 && lc(rows[k][1]) > lc(lead)) { pos = k; break; }
        var nr = [0, lead, null, null, 0]; nr.ov = 1;
        rows.splice(pos, 0, nr); i = pos;
      }
      for (var lvl = 1; lvl < path.length; lvl++) {
        var end = subtreeEnd(rows, i), j = findRow(rows, lvl, path[lvl], i + 1, end, true);
        if (j === -1) { var r2 = [lvl, path[lvl], null, null, 0]; r2.ov = 1; rows.splice(end, 0, r2); j = end; }
        i = j;
      }
      if (it.c1) rows[i][2] = it.c1;
      if (it.c2) rows[i][3] = it.c2;
      rows[i].ov = 1;
    });
    return rows;
  }
  function notesFor(x, sys) {
    return NOTES.filter(function (n) { return (n.sys === sys || n.sys === 'all') && (n.codes || []).some(function (p) { return patternHit(p, x.c); }); });
  }
  function rebuild() {
    var items = OV.effective();
    DB.icd10 = prep(applyCodeItems(clone(BASE.icd10), 'icd10', items));
    DB.icd9 = prep(applyCodeItems(clone(BASE.icd9), 'icd9', items));
    if (BASE.kw10) addKeywords('icd10', BASE.kw10);
    if (BASE.kw9) addKeywords('icd9', BASE.kw9);
    var A = applyAbbrItems(BASE.abbr || {}, items);
    ABBR = { icd10: A.icd10, icd9: A.icd9 }; SPELL = (BASE.abbr && BASE.abbr.spell) || [];
    NOTES = items.filter(function (i) { return i.kind === 'note'; });
    TABLES = null; tablesPending = null; MORPH = null; morphPending = null; IDXL = {};
    if (BASE.tables) loadTables().then(function () { if (S.ready) { renderList(); renderDetail(); } });
    if (BASE.morph) loadMorph().then(function () { if (S.ready) { renderList(); renderDetail(); } });
    ['icd10', 'icd9'].forEach(function (k) { if (S.sel[k] && !DB[k].byCode[S.sel[k]]) S.sel[k] = null; });
  }
  var rbT;
  function scheduleRebuild() {
    clearTimeout(rbT);
    rbT = setTimeout(function () { rebuild(); footer(); renderAll(); if (window.ICDADMIN) window.ICDADMIN.refresh(); }, 200);
  }
  var DRAFT_KEY = 'icd.overlay.draft';
  function connectBackend() {
    var c = window.claude;
    if (!c || !c.use) {
      // a public static host (Netlify, GitHub Pages, ...): read-only, the backend stays hidden
      var h = location.hostname;
      if (!(h === 'localhost' || h === '127.0.0.1' || h === '' || /^192\.168\.|^10\./.test(h))) { OV.mode = 'static'; OV.canEdit = false; footer(); return; }
      // opened from the project folder (local web server): the local backend edits data/overlay.json
      OV.mode = 'local'; OV.canEdit = true;
      var draft = lsGet(DRAFT_KEY, null);
      if (draft && draft.items) { OV.file = draft.items; OV.dirty = true; scheduleRebuild(); }
      footer();
      return;
    }
    Promise.all([c.use('db'), c.use('user')]).then(function (r) {
      var db = r[0], user = r[1];
      OV.user = user;
      if (!db) { OV.mode = 'viewer'; footer(); return; }
      OV.mode = 'online'; OV.dbns = db;
      db.collection('overlay').onSnapshot(function (snap) {
        OV.db = snap.docs.map(function (d) { return Object.assign({}, d.data(), { id: d.id }); });
        scheduleRebuild();
      }, function () { OV.mode = 'viewer'; footer(); });
      if (user) user.canEdit().then(function (ok) { OV.canEdit = !!ok; footer(); if (window.ICDADMIN) window.ICDADMIN.refresh(); });
    }).catch(function () { OV.mode = 'viewer'; });
  }
  function newId(kind, key) {
    var k = key ? String(key).replace(/[^A-Za-z0-9_.~:@+-]+/g, '_').slice(0, 80) : (Date.now().toString(36) + Math.random().toString(36).slice(2, 7));
    return kind + '-' + k;
  }
  function stamp(it) {
    it.updated = new Date().toISOString();
    return OV.user && OV.mode === 'online' ? OV.user.id().then(function (uid) { if (uid) it.by = uid; return it; }) : Promise.resolve(it);
  }
  function persistLocal() { lsSet(DRAFT_KEY, { version: 1, items: OV.file }); OV.dirty = true; }
  function saveItem(it) {
    return stamp(it).then(function (it2) {
      if (OV.mode === 'online') return OV.dbns.collection('overlay').doc(it2.id).set(JSON.parse(JSON.stringify(it2)));
      var i = OV.file.findIndex(function (x) { return x.id === it2.id; });
      if (i === -1) OV.file.push(it2); else OV.file[i] = it2;
      persistLocal(); scheduleRebuild();
    });
  }
  function deleteItem(id) {
    if (OV.mode === 'online') {
      var inFile = OV.file.some(function (x) { return x.id === id; });
      var ref = OV.dbns.collection('overlay').doc(id);
      return inFile ? ref.set({ id: id, deleted: true, updated: new Date().toISOString() }) : ref.delete();
    }
    OV.file = OV.file.filter(function (x) { return x.id !== id; });
    persistLocal(); scheduleRebuild();
    return Promise.resolve();
  }
  var adminState = 0;
  function openAdmin() {
    if (adminState) { if (adminState === 2 && window.ICDADMIN) window.ICDADMIN.show(); return; }
    adminState = 1;
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'assets/admin.css'; document.head.appendChild(l);
    var sc = document.createElement('script'); sc.src = 'assets/admin.js';
    sc.onload = function () { adminState = 2; window.ICDADMIN.mount($('adminView')); };
    sc.onerror = function () { adminState = 0; $('adminView').innerHTML = '<div class="empty"><b>โหลดหน้าหลังบ้านไม่สำเร็จ</b></div>'; };
    document.body.appendChild(sc);
  }
  // the admin page (assets/admin.js) works through this object only
  window.ICDAPP = {
    PATH: PATH, SYS: SYS, OV: OV, S: S,
    db: function (sys) { return DB[sys]; }, base: function () { return BASE; },
    tables: function () { return loadTables(); }, morph: function () { return loadMorph(); },
    abbr: function () { return ABBR; }, notes: function () { return NOTES; },
    esc: esc, toast: toast, select: select, newId: newId, saveItem: saveItem, deleteItem: deleteItem,
    rebuild: scheduleRebuild, persistLocal: persistLocal, patternHit: patternHit, draftKey: DRAFT_KEY,
    goto: function (view) { S.view = view; setHash(view); renderAll(); }
  };

  // ---------- boot ----------
  function load(path) { return fetch(path).then(function (r) { if (!r.ok) throw new Error(path + ' ' + r.status); return r.json(); }); }
  function footer() {
    var o = OV.effective().length;
    $('footer').innerHTML = '<p>' + esc(DB.icd10.label) + ' ' + esc(DB.icd10.version) + ' · ' + DB.icd10.codes.length.toLocaleString('th-TH') + ' รหัส — ' + esc(DB.icd10.source || '') + '</p>' +
      '<p>' + esc(DB.icd9.label) + ' ' + esc(DB.icd9.version) + ' · ' + DB.icd9.codes.length.toLocaleString('th-TH') + ' รหัส — ' + esc(DB.icd9.source || '') + '</p>' +
      (o ? '<p>มีข้อมูลที่ผู้ดูแลเพิ่มหรือแก้ไข ' + o.toLocaleString('th-TH') + ' รายการ</p>' : '') +
      '<p>ใช้ประกอบการทำงาน ตรวจซ้ำกับบัญชีจำแนกฉบับที่หน่วยงานใช้ทุกครั้ง' +
      (OV.canEdit ? ' · <a href="#admin" data-act="view" data-view="admin">หลังบ้านผู้พัฒนา</a>' : '') + '</p>';
  }
  Promise.all([load(PATH.icd10), load(PATH.icd9), load(PATH.guide).catch(function () { return { items: {} }; }),
    load(PATH.abbr).catch(function () { return {}; }), load(PATH.overlay + '?v=' + Date.now()).catch(function () { return { items: [] }; })]).then(function (res) {
    BASE.icd10 = res[0]; BASE.icd9 = res[1]; G = res[2].items || {}; BASE.abbr = res[3]; OV.file = res[4].items || [];
    rebuild();
    if (DB.icd10.sample || DB.icd9.sample) {
      $('bannerText').innerHTML = '<b>ข้อมูลตัวอย่าง</b> ยังไม่ใช่บัญชีจำแนกฉบับเต็ม';
      $('banner').hidden = false;
    }
    footer();
    S.ready = true;
    applyHash();
    renderAll();
    // secondary data: index keywords for search, tables, NHSO audit topics
    load(PATH.kw10).then(function (m) { BASE.kw10 = m; addKeywords('icd10', m); if (S.view === 'search' && S.q) renderList(); }).catch(function () {});
    load(PATH.kw9).then(function (m) { BASE.kw9 = m; addKeywords('icd9', m); if (S.view === 'search' && S.q) renderList(); }).catch(function () {});
    loadTables().then(function () { if (S.view === 'search' && S.q) renderList(); renderDetail(); }).catch(function () {});
    loadMorph().then(function () { if (S.view === 'search' && S.q) renderList(); renderDetail(); }).catch(function () {});
    load(PATH.nhso).then(function (n) { NHSO = n; renderDetail(); if (S.view === 'guide') renderGuide(); }).catch(function () { NHSO = { topics: [], sections: [] }; renderDetail(); });
    connectBackend();
  }).catch(function (err) {
    $('list').innerHTML = '<div class="empty"><b>โหลดข้อมูลรหัสไม่สำเร็จ</b><p>ลองรีเฟรชหน้านี้ ถ้ายังไม่ได้ ให้แจ้งผู้ดูแลระบบว่าไฟล์ข้อมูลอาจหายไป (' + esc(err.message) + ')</p></div>';
  });
  renderChrome();
})();
