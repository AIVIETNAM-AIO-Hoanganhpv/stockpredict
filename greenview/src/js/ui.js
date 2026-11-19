/* =========================================================
 * ui.js — Thành phần giao diện: bảng trượt, thanh công cụ, chú thích,
 *          hộp chọn chỉ báo, cài đặt chỉ báo, bảng "Bản vẽ", chọn mã…
 * ========================================================= */
(function (App) {
  'use strict';
  const $ = App.$, $$ = App.$$, esc = App.esc, ic = App.icon;
  const U = App.ui = {};
  U.mobile = () => window.innerWidth <= 860;

  /* =========================================================
   * BẢNG TRƯỢT / HỘP THOẠI dùng chung
   * ========================================================= */
  U.sheet = function ({ id, title, body, foot, cls = '', back, onClose, noHead }) {
    U.close(id);
    const bg = document.createElement('div');
    bg.className = 'sheet-bg'; bg.dataset.id = id;
    bg.innerHTML = `<div class="sheet ${cls}" role="dialog" aria-label="${esc(title || '')}">
      <div class="sh-grab"></div>
      ${noHead ? '' : `<div class="sh-head">${back ? `<button class="circ" data-back>${ic('back')}</button>` : '<span class="sp"></span>'}<h3>${title || ''}</h3><button class="circ" data-x aria-label="Đóng">${ic('x')}</button></div>`}
      <div class="sh-body"></div>${foot ? `<div class="sh-foot">${foot}</div>` : ''}</div>`;
    const b = bg.querySelector('.sh-body');
    if (typeof body === 'string') b.innerHTML = body; else if (body) b.appendChild(body);
    bg.addEventListener('mousedown', e => { if (e.target === bg) U.close(id); });
    bg.querySelectorAll('[data-x]').forEach(x => x.onclick = () => U.close(id));
    if (back) bg.querySelector('[data-back]').onclick = () => { U.close(id); back(); };
    bg._onClose = onClose;
    $('#sheets').appendChild(bg);
    return bg;
  };
  U.close = function (id) { $$('#sheets .sheet-bg').forEach(s => { if (!id || s.dataset.id === id) { s._onClose && s._onClose(); s.remove(); } }); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { const all = $$('#sheets .sheet-bg'); if (all.length) all[all.length - 1].remove(); $('#flyout').classList.add('hidden'); } });

  U.prompt = function (label, value, cb, multi) {
    const s = U.sheet({ id: 'prompt', title: label, cls: 'small', body: `${multi ? `<textarea class="inp" rows="4" id="pIn">${esc(value)}</textarea>` : `<input class="inp" id="pIn" value="${esc(value)}">`}`,
      foot: '<button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>OK</button>', onClose: () => { if (!done) cb(null); } });
    let done = false;
    const inp = s.querySelector('#pIn'); setTimeout(() => { inp.focus(); inp.select && inp.select(); }, 60);
    const ok = () => { done = true; cb(inp.value); U.close('prompt'); };
    s.querySelector('[data-ok]').onclick = ok; s.querySelector('[data-c]').onclick = () => U.close('prompt');
    inp.addEventListener('keydown', e => { if (e.key === 'Enter' && (!multi || e.ctrlKey || e.metaKey)) ok(); });
  };
  U.confirm = function (text, ok) {
    const s = U.sheet({ id: 'confirm', title: 'Xác nhận', cls: 'small', body: `<p>${esc(text)}</p>`, foot: '<button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>Đồng ý</button>' });
    s.querySelector('[data-c]').onclick = () => U.close('confirm');
    s.querySelector('[data-ok]').onclick = () => { U.close('confirm'); ok(); };
  };
  U.pickImage = function (d) {
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
    inp.onchange = () => {
      const f = inp.files[0]; if (!f) return;
      const r = new FileReader();
      r.onload = () => { const im = new Image(); im.onload = () => { const k = Math.min(1, 480 / Math.max(im.width, im.height)), c = document.createElement('canvas'); c.width = im.width * k; c.height = im.height * k; c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); d.style.img = c.toDataURL('image/jpeg', 0.85); App.draw.save(); }; im.src = r.result; };
      r.readAsDataURL(f);
    };
    inp.click();
  };

  /* =========================================================
   * THANH TRÊN
   * ========================================================= */
  U.initTop = function () {
    $$('[data-i]').forEach(el => { if (el.tagName === 'I') el.outerHTML = ic(el.dataset.i); else if (!el.querySelector('svg')) el.insertAdjacentHTML('afterbegin', ic(el.dataset.i)); });
    $('#brand').onclick = () => U.about();
    $('#btnSymbol').onclick = () => U.symbolSheet('open');
    $('#btnCompare').onclick = () => U.symbolSheet('compare');
    $('#btnType').onclick = U.typeSheet;
    $('#btnInd').onclick = () => U.indSheet();
    $('#btnTpl').onclick = () => App.panels.templates();
    $('#btnAlert').onclick = () => App.panels.alertSheet();
    $('#btnReplay').onclick = () => App.panels.replayStart();
    $('#btnTheme').onclick = () => App.setTheme(App.themeName === 'dark' ? 'light' : 'dark');
    $('#btnShot').onclick = App.panels.screenshot;
    $('#btnSettings').onclick = U.chartSettings;
    $('#btnHub').onclick = () => App.panels.hub();
    $('#btnDrawM').onclick = () => U.drawSheet();
    $('#btnTfM').onclick = () => U.tfSheet();
    $('#tfBar').addEventListener('click', e => { if (e.target.closest('[data-more]')) return U.tfSheet(); const b = e.target.closest('button[data-tf]'); if (b && !b.disabled) App.loadSymbol(App.state.src, App.state.sym, b.dataset.tf); });
  };
  U.renderTop = function () {
    const s = App.state, src = App.sources[s.src];
    $('#symName').textContent = s.sym;
    $('#symSrc').textContent = src.short;
    const b = App.badge(s.src, s.sym); $('#symIco').style.background = b.bg; $('#symIco').textContent = b.txt;
    $('#watermark').textContent = s.sym;
    document.title = s.sym + ' · GreenView';
    const quick = ['1m', '5m', '15m', '1h', '4h', '1D', '1W'];
    if (!quick.includes(s.tf)) quick.push(s.tf);
    $('#tfBar').innerHTML = Object.keys(App.TF).filter(tf => quick.includes(tf)).map(tf => `<button data-tf="${tf}" class="${tf === s.tf ? 'active' : ''}" ${src.tfs.includes(tf) ? '' : 'disabled title="Nguồn này không hỗ trợ"'} title="${App.TF_NAME[tf]}">${App.TF_LABEL[tf]}</button>`).join('')
      + `<button data-more="1" title="Tất cả khung thời gian">${ic('down')}</button>`;
    $('#btnType').innerHTML = ic('candle');
    $('#btnTfM').textContent = App.TF_LABEL[s.tf];
  };
  U.tfSheet = function () {
    const src = App.sources[App.state.src];
    const names = App.TF_NAME;
    const s = U.sheet({ id: 'tf', title: 'Khung thời gian', cls: 'small', body: `<div class="ilist">${Object.keys(App.TF).map(tf => `<div class="irow ${src.tfs.includes(tf) ? '' : 'dis'}" data-tf="${tf}"><span class="nm">${names[tf]}${src.tfs.includes(tf) ? (App.state.src === 'TCBS' && App.TF[tf] < 86400 || (App.state.src === 'VN' && App.mcp && App.TF[tf] < 86400) ? '<small>Tự ghép từ giá TCBS khi trang đang mở</small>' : '') : '<small>Nguồn này không hỗ trợ</small>'}</span>${tf === App.state.tf ? ic('check') : ''}</div>`).join('')}</div>` });
    s.addEventListener('click', e => { const r = e.target.closest('[data-tf]'); if (r && src.tfs.includes(r.dataset.tf)) { U.close('tf'); App.loadSymbol(App.state.src, App.state.sym, r.dataset.tf); } });
  };

  /* =========================================================
   * THANH VẼ BÊN TRÁI (máy tính) — nhóm công cụ xổ ra như TradingView
   * ========================================================= */
  const DR = App.draw;
  const lastOfCat = App.store.get('lastTool', { trend: 'trend', fib: 'fibret', pattern: 'xabcd', predict: 'long', geo: 'brush', note: 'text', img: 'emo0' });
  U.initTools = function () {
    const cats = ['trend', 'fib', 'pattern', 'predict', 'geo', 'note', 'img'];
    let h = `<button class="tl" data-tool="cursor" title="Con trỏ">${DR.ICONS.cursor}</button><div class="tl-sep"></div>`;
    cats.forEach(c => { const t = DR.TOOLS[lastOfCat[c]] || Object.values(DR.TOOLS).find(x => x.cat === c); h += `<button class="tl grp" data-cat="${c}" data-tool="${t.id}" title="${esc(t.name)}">${t.icon}</button>`; });
    h += `<div class="tl-sep"></div>
      <button class="tl" data-act="measure" title="Đo lường (Shift + kéo)">${DR.ICONS.measure}</button>
      <button class="tl" data-act="zin" title="Phóng to">${DR.ICONS.zin}</button>
      <div class="tl-sep"></div>
      <button class="tl" data-act="magnet" title="Nam châm">${DR.ICONS.magnet}</button>
      <button class="tl" data-act="keep" title="Tiếp tục vẽ">${DR.ICONS.keep}</button>
      <button class="tl" data-act="lock" title="Khóa tất cả hình vẽ">${DR.ICONS.lock}</button>
      <button class="tl" data-act="hide" title="Ẩn tất cả hình vẽ">${DR.ICONS.hide}</button>
      <button class="tl" data-act="clear" title="Xóa tất cả hình vẽ">${DR.ICONS.trash}</button>
      <div class="tl-sep"></div>
      <button class="tl" data-act="fav" title="Yêu thích / tất cả công cụ">${ic('star')}</button>`;
    $('#tools').innerHTML = h;
    $('#tools').addEventListener('click', e => {
      const b = e.target.closest('.tl'); if (!b) return;
      if (b.dataset.act) return U.action(b.dataset.act, b);
      if (b.dataset.cat) {
        const r = b.getBoundingClientRect();
        // bấm nửa phải (mũi tên) hoặc đang chọn → mở bảng xổ; còn lại → chọn công cụ
        if (e.clientX > r.right - 12 || DR.tool === b.dataset.tool) return U.flyout(b.dataset.cat, b);
      }
      DR.setTool(b.dataset.tool);
    });
    $('#tools').addEventListener('contextmenu', e => { const b = e.target.closest('.tl[data-cat]'); if (b) { e.preventDefault(); U.flyout(b.dataset.cat, b); } });
    let lp; $('#tools').addEventListener('pointerdown', e => { const b = e.target.closest('.tl[data-cat]'); if (b) lp = setTimeout(() => U.flyout(b.dataset.cat, b), 450); });
    $('#tools').addEventListener('pointerup', () => clearTimeout(lp));
    U.syncToolState();
  };
  U.flyout = function (cat, anchor) {
    const f = $('#flyout');
    const list = Object.values(DR.TOOLS).filter(t => t.cat === cat && !t.hidden);
    const name = (DR.CATS.find(c => c[0] === cat) || [])[1];
    if (cat === 'img') f.innerHTML = `<div class="fo-h">${name}</div><div class="emo-grid">${list.map(t => `<button data-tool="${t.id}" title="${esc(t.name)}">${t.emoji}</button>`).join('')}</div>`;
    else f.innerHTML = `<div class="fo-h">${name}</div>` + list.map(t => `<div class="fo-row ${DR.tool === t.id ? 'active' : ''}" data-tool="${t.id}"><span class="tsvg">${t.icon}</span><span class="nm">${esc(t.name)}</span><button class="fav ${DR.favs.includes(t.id) ? 'on' : ''}" data-fav="${t.id}">${ic('star')}</button></div>`).join('');
    const r = anchor.getBoundingClientRect();
    f.style.left = (r.right + 6) + 'px'; f.style.top = Math.max(8, Math.min(r.top - 8, window.innerHeight - 420)) + 'px';
    f.classList.remove('hidden');
    f.onclick = e => {
      const fv = e.target.closest('[data-fav]'); if (fv) { U.toggleFav(fv.dataset.fav); fv.classList.toggle('on'); e.stopPropagation(); return; }
      const t = e.target.closest('[data-tool]'); if (!t) return;
      lastOfCat[cat] = t.dataset.tool; App.store.set('lastTool', lastOfCat);
      anchor.dataset.tool = t.dataset.tool; anchor.innerHTML = DR.TOOLS[t.dataset.tool].icon; anchor.title = DR.TOOLS[t.dataset.tool].name;
      DR.setTool(t.dataset.tool); f.classList.add('hidden');
    };
    setTimeout(() => document.addEventListener('pointerdown', function h(ev) { if (!f.contains(ev.target)) { f.classList.add('hidden'); document.removeEventListener('pointerdown', h); } }), 0);
  };
  U.toggleFav = function (id) { const i = DR.favs.indexOf(id); if (i >= 0) DR.favs.splice(i, 1); else DR.favs.push(id); App.store.set('drawFavs', DR.favs); };
  U.action = function (a, btn) {
    const ts = App.chart.api.timeScale();
    switch (a) {
      case 'measure': DR.setTool('measure'); break;
      case 'eraser': DR.setTool('eraser'); App.toast('Bấm vào hình cần xoá'); break;
      case 'zin': case 'zout': { const r = ts.getVisibleLogicalRange(); if (!r) break; const c = (r.from + r.to) / 2, w = (r.to - r.from) * (a === 'zin' ? 0.35 : 0.8); ts.setVisibleLogicalRange({ from: c - w, to: c + w }); break; }
      case 'magnet': DR.magnet = { off: 'weak', weak: 'strong', strong: 'off' }[DR.magnet]; App.store.set('magnet', DR.magnet); App.toast('Nam châm: ' + { off: 'tắt', weak: 'yếu', strong: 'mạnh' }[DR.magnet]); break;
      case 'keep': DR.keep = !DR.keep; App.store.set('keepDraw', DR.keep); App.toast('Tiếp tục vẽ: ' + (DR.keep ? 'bật' : 'tắt')); break;
      case 'lock': DR.lockAll = !DR.lockAll; App.toast(DR.lockAll ? 'Đã khoá tất cả hình vẽ' : 'Đã mở khoá hình vẽ'); break;
      case 'hide': DR.hideAll = !DR.hideAll; DR.select(null); break;
      case 'clear': if (!DR.list.length) App.toast('Chưa có hình vẽ nào'); else U.confirm(`Xoá tất cả ${DR.list.length} hình vẽ của ${App.state.sym}?`, DR.clearAll); break;
      case 'fav': U.drawSheet('fav'); break;
    }
    U.syncToolState();
  };
  U.syncToolState = function () {
    $$('#tools .tl[data-tool]').forEach(b => b.classList.toggle('active', b.dataset.tool === DR.tool));
    const set = (a, on) => { const b = $(`#tools [data-act="${a}"]`); if (b) b.classList.toggle('active', !!on); };
    set('magnet', DR.magnet !== 'off'); set('keep', DR.keep); set('lock', DR.lockAll); set('hide', DR.hideAll); set('measure', DR.tool === 'measure');
    const m = $('#tools [data-act="magnet"]'); if (m) m.title = 'Nam châm: ' + { off: 'tắt', weak: 'yếu', strong: 'mạnh' }[DR.magnet];
  };
  U.onToolChange = function (t) {
    U.syncToolState();
    if (t !== 'cursor' && t !== 'eraser' && U.mobile()) App.toast(`${DR.TOOLS[t] ? DR.TOOLS[t].name : t}: chạm lên biểu đồ để đặt điểm`, 'info', 2500);
  };

  /* ---------- Bảng "Bản vẽ" (giống TradingView điện thoại) ---------- */
  U.drawSheet = function (cat) {
    let cur = cat || App.store.get('drawCat', 'trend'), q = '';
    const s = U.sheet({ id: 'draw', title: 'Bản vẽ', body: `<div class="search">${ic('search')}<input placeholder="Tìm kiếm" id="dsQ"></div><div class="chips" id="dsCats"></div><div id="dsGrid"></div>` });
    const render = () => {
      $('#dsCats').innerHTML = DR.CATS.map(([k, n]) => `<button class="chip ${k === cur && !q ? 'active' : ''}" data-c="${k}">${n}</button>`).join('');
      let items;
      if (q) items = Object.values(DR.TOOLS).filter(t => !t.hidden && t.cat !== 'img' && t.name.toLowerCase().includes(q)).map(t => tile(t));
      else if (cur === 'tools') items = DR.ACTIONS.map(([id, nm, icon, kind]) => {
        const on = (id === 'keep' && DR.keep) || (id === 'hide' && DR.hideAll) || (id === 'lock' && DR.lockAll) || (id === 'magnet' && DR.magnet !== 'off');
        const label = id === 'magnet' ? 'Nam châm ' + { off: '(tắt)', weak: 'yếu', strong: 'mạnh' }[DR.magnet] : nm;
        return `<button class="tile ${kind ? 'big-tile' : ''} ${on ? 'on' : ''}" data-act="${id}">${icon}<span>${label}</span></button>`; });
      else if (cur === 'fav') items = DR.favs.filter(id => DR.TOOLS[id]).map(id => tile(DR.TOOLS[id]));
      else items = Object.values(DR.TOOLS).filter(t => t.cat === cur && !t.hidden).map(t => tile(t));
      $('#dsGrid').innerHTML = items.length ? `<div class="grid3">${items.join('')}</div>` : '<div class="empty">Chưa có công cụ yêu thích — bấm ☆ trên ô công cụ để thêm</div>';
    };
    const tile = t => `<button class="tile ${DR.tool === t.id ? 'active' : ''}" data-tool="${t.id}">${t.icon}<span>${esc(t.cat === 'img' ? '' : t.name)}</span><span class="fav ${DR.favs.includes(t.id) ? 'on' : ''}" data-fav="${t.id}">${ic('star')}</span></button>`;
    render();
    $('#dsQ').oninput = e => { q = e.target.value.trim().toLowerCase(); render(); };
    s.addEventListener('click', e => {
      const c = e.target.closest('[data-c]'); if (c) { cur = c.dataset.c; App.store.set('drawCat', cur); q = ''; $('#dsQ').value = ''; render(); return; }
      const f = e.target.closest('[data-fav]'); if (f) { e.stopPropagation(); U.toggleFav(f.dataset.fav); render(); return; }
      const a = e.target.closest('[data-act]'); if (a) { U.action(a.dataset.act); if (['measure', 'eraser', 'zin', 'zout', 'clear'].includes(a.dataset.act)) U.close('draw'); else render(); return; }
      const t = e.target.closest('[data-tool]'); if (t) { DR.setTool(t.dataset.tool); U.close('draw'); }
    });
  };

  /* ---------- Thanh công cụ của hình đang chọn ---------- */
  const COLORS = ['#2962ff', '#14d1a0', '#089981', '#c6f432', '#ffeb3b', '#ff9800', '#f23645', '#e91e63', '#9c27b0', '#673ab7', '#00bcd4', '#795548', '#787b86', '#ffffff', '#000000', '#0f7a43'];
  U.drawToolbar = function (d) {
    const bar = $('#drawBar');
    if (!d) { bar.classList.add('hidden'); return; }
    const def = DR.TOOLS[d.tool] || {}, st = d.style;
    bar.innerHTML = `<span class="ot-ico tsvg" title="${esc(def.name)}">${def.icon || ''}</span>
      <button data-a="color" title="Màu"><span class="sw" style="background:${st.color}"></span></button>
      <select data-a="width" title="Độ dày">${[1, 2, 3, 4, 6, 10, 16].map(w => `<option ${+st.width === w ? 'selected' : ''} value="${w}">${w}px</option>`).join('')}</select>
      <select data-a="dash" title="Kiểu nét"><option value="solid">━━</option><option value="dashed" ${st.dash === 'dashed' ? 'selected' : ''}>╍╍</option><option value="dotted" ${st.dash === 'dotted' ? 'selected' : ''}>┈┈</option></select>
      ${def.text ? `<button data-a="text" title="Sửa chữ">${ic('text')}</button><select data-a="fs" title="Cỡ chữ">${[10, 12, 14, 18, 24, 32, 48].map(z => `<option ${+(st.fontSize || 12) === z ? 'selected' : ''}>${z}</option>`).join('')}</select>` : ''}
      ${(def.opts || []).includes('extL') ? `<button data-a="extL" class="${st.extL ? 'on' : ''}" title="Kéo dài sang trái">${ic('extL')}</button>` : ''}
      ${(def.opts || []).includes('extR') ? `<button data-a="extR" class="${st.extR ? 'on' : ''}" title="Kéo dài sang phải">${ic('extR')}</button>` : ''}
      ${(def.opts || []).includes('info') ? `<button data-a="info" class="${st.info ? 'on' : ''}" title="Hiện thông tin">${ic('info')}</button>` : ''}
      ${d.tool === 'image' ? `<button data-a="img" title="Chọn ảnh">${ic('folder')}</button>` : ''}
      <span class="dsep"></span>
      <button data-a="lock" class="${d.locked ? 'on' : ''}" title="${d.locked ? 'Mở khoá' : 'Khoá'}">${ic(d.locked ? 'lock' : 'unlock')}</button>
      <button data-a="clone" title="Nhân bản">${ic('copy')}</button>
      <button data-a="hide" title="Ẩn">${ic('eyeoff')}</button>
      <button data-a="del" title="Xoá (Delete)">${ic('trash')}</button>`;
    bar.classList.remove('hidden');
    bar.onchange = e => { const a = e.target.dataset.a; if (a === 'width') st.width = +e.target.value; if (a === 'dash') st.dash = e.target.value; if (a === 'fs') st.fontSize = +e.target.value; DR.save(); Object.assign(DR.style, { width: st.width, dash: st.dash }); App.store.set('drawStyle', DR.style); };
    bar.onclick = e => {
      const b = e.target.closest('button'); if (!b) return; const a = b.dataset.a;
      if (a === 'color') return U.colorPop(b, st.color, c => { st.color = c; DR.style.color = c; App.store.set('drawStyle', DR.style); DR.save(); U.drawToolbar(d); });
      if (a === 'text') return DR.editText(d);
      if (a === 'img') return U.pickImage(d);
      if (a === 'extL' || a === 'extR' || a === 'info') st[a] = !st[a];
      if (a === 'lock') d.locked = !d.locked;
      if (a === 'clone') return DR.clone(d);
      if (a === 'hide') { d.hidden = true; DR.select(null); DR.save(); App.toast('Đã ẩn — bật lại trong Cây đối tượng'); return; }
      if (a === 'del') return DR.remove(d);
      DR.save(); U.drawToolbar(d);
    };
  };
  U.colorPop = function (anchor, cur, cb) {
    const f = $('#flyout');
    f.innerHTML = `<div class="swatches">${COLORS.map(c => `<button style="background:${c}" class="${c === cur ? 'on' : ''}" data-c="${c}"></button>`).join('')}</div><div style="padding:4px 8px 8px"><input type="color" value="${cur && cur[0] === '#' ? cur.slice(0, 7) : '#2962ff'}" style="width:100%;height:30px;border:none;background:none"></div>`;
    const r = anchor.getBoundingClientRect();
    f.style.left = Math.min(r.left, window.innerWidth - 240) + 'px'; f.style.top = (r.bottom + 6 + 200 > window.innerHeight ? r.top - 210 : r.bottom + 6) + 'px';
    f.classList.remove('hidden');
    f.onclick = e => { const b = e.target.closest('[data-c]'); if (b) { cb(b.dataset.c); f.classList.add('hidden'); } };
    f.querySelector('input').oninput = e => cb(e.target.value);
    setTimeout(() => document.addEventListener('pointerdown', function h(ev) { if (!f.contains(ev.target)) { f.classList.add('hidden'); document.removeEventListener('pointerdown', h); } }), 0);
  };

  /* =========================================================
   * CHÚ THÍCH (legend) — dòng giá + từng chỉ báo có nút ẩn/cài đặt/xoá
   * ========================================================= */
  U.legendOpen = App.store.get('legendOpen', true);
  U.legend = function (param) {
    const C = App.chart, v = C.view; if (!v || !v.length) return;
    let i = v.length - 1;
    if (param && param.time != null) { const k = v.findIndex(b => b.time === param.time); if (k >= 0) i = k; }
    const b = v[i], p = v[i - 1] || b, ch = b.close - p.close, pc = p.close ? ch / p.close * 100 : 0, cls = ch >= 0 ? 'up' : 'down', f = App.fmtPrice;
    const s = App.state;
    let h = `<div class="lg-main"><span class="nm">${esc(s.sym)} · ${App.TF_LABEL[s.tf] || ''} · ${esc(App.sources[s.src].short)}</span>${C.replay ? '<span class="tag new">PHÁT LẠI</span>' : ''}</div>
      <div class="lg-ohlc"><span><b>M</b><span class="${cls}">${f(b.open)}</span></span><span><b>C</b><span class="${cls}">${f(b.high)}</span></span><span><b>T</b><span class="${cls}">${f(b.low)}</span></span><span><b>Đ</b><span class="${cls}">${f(b.close)}</span></span>
      <span class="${cls}">${ch >= 0 ? '+' : ''}${f(ch)} (${App.fmtPct(pc)})</span><span><b>KL</b>${App.fmtVol(b.volume)}</span></div>`;
    C.compares.forEach((c, k) => { h += `<div class="lg-row"><span class="t" style="color:${c.color}">● ${esc(c.sym)}</span><span class="acts" style="display:flex"><button data-cmp="${k}" title="Bỏ so sánh">${ic('x')}</button></span></div>`; });
    const paneRows = {};
    const rows = [];
    C.inds.forEach(inst => {
      const def = App.INDICATORS[inst.id]; if (!def) return;
      const I = C.inputs(inst), params = def.inputs.filter(x => x[3] === 'int' || x[3] === 'float' || x[3] === 'sel').slice(0, 4).map(x => I[x[0]]).join(', ');
      const res = C.results[inst.uid] || {};
      const vals = def.plots.map(([k]) => { const st = C.plotStyle(inst, k), a = res[k]; if (!a || !st.v) return ''; const val = a[i]; return App.ta.isN(val) ? `<span class="v" style="color:${st.c}">${Math.abs(val) < 1 && val !== 0 ? val.toFixed(4) : f(val)}</span>` : ''; }).join(' ');
      const html = `<div class="lg-row ${inst.hidden ? 'off' : ''}" data-uid="${inst.uid}"><span class="t">${esc(def.name)}${params ? ' <span class="muted">' + esc(params) + '</span>' : ''}</span>${vals}
        <span class="acts"><button data-a="eye" title="${inst.hidden ? 'Hiện' : 'Ẩn'}">${ic(inst.hidden ? 'eyeoff' : 'eye')}</button><button data-a="set" title="Cài đặt">${ic('gear')}</button><button data-a="del" title="Xoá">${ic('x')}</button></span></div>`;
      const pn = C.paneOf[inst.uid];
      if (pn) (paneRows[pn] = paneRows[pn] || []).push(html); else rows.push(html);
    });
    if (rows.length > 3 && !U.legendOpen) h += `<button class="lg-toggle" data-tog>▾ ${rows.length} chỉ báo</button>`;
    else { h += rows.join(''); if (rows.length > 3) h += `<button class="lg-toggle" data-tog>▴ Thu gọn</button>`; }
    $('#legend').innerHTML = h;
    // chú thích của từng khung chỉ báo bên dưới (giống TradingView)
    const box = $('#paneLegends'), wrapTop = $('#chartWrap').getBoundingClientRect().top, panes = C.api.panes();
    box.innerHTML = Object.entries(paneRows).map(([pn, list]) => {
      const el = panes[pn] && panes[pn].getHTMLElement && panes[pn].getHTMLElement(); if (!el) return '';
      return `<div class="pane-lg" style="top:${el.getBoundingClientRect().top - wrapTop + 4}px">${list.join('')}</div>`;
    }).join('');
  };
  U.initLegend = function () {
    const onClick = e => {
      if (e.target.closest('[data-tog]')) { U.legendOpen = !U.legendOpen; App.store.set('legendOpen', U.legendOpen); return U.legend(App.chart.hover); }
      const cm = e.target.closest('[data-cmp]'); if (cm) return App.chart.removeCompare(+cm.dataset.cmp);
      const b = e.target.closest('button[data-a]'), row = e.target.closest('.lg-row'); if (!row) return;
      const uid = +row.dataset.uid, inst = App.chart.inds.find(x => x.uid === uid); if (!inst) return;
      if (!b) { if (U.mobile()) row.classList.toggle('touch'); else U.indSettings(inst); return; }
      if (b.dataset.a === 'eye') { inst.hidden = !inst.hidden; App.chart.saveInds(); App.chart.renderIndicators(); }
      if (b.dataset.a === 'set') U.indSettings(inst);
      if (b.dataset.a === 'del') App.chart.removeIndicator(uid);
    };
    $('#legend').addEventListener('click', onClick); $('#paneLegends').addEventListener('click', onClick);
    $('#legend').addEventListener('dblclick', e => { const row = e.target.closest('.lg-row[data-uid]'); if (row) { const inst = App.chart.inds.find(x => x.uid === +row.dataset.uid); inst && U.indSettings(inst); } });
  };

  /* =========================================================
   * HỘP CHỈ BÁO (giống "Chỉ báo, chỉ số và chiến lược")
   * ========================================================= */
  const indFavs = () => App.store.get('indFavs', ['ma', 'ema', 'rsi', 'macd', 'bb', 'volume']);
  U.indSheet = function (tab) {
    let cur = tab || App.store.get('indTab', 'ind'), q = '';
    const tabs = [['fav', 'Yêu thích'], ['stockpredict', 'StockPredict'], ['ind', 'Các chỉ báo'], ['strategy', 'Chiến lược'], ['profile', 'Hồ sơ'], ['pattern', 'Mô hình'], ['options', 'Options'], ['tpl', 'Mẫu']];
    const s = U.sheet({ id: 'ind', title: 'Chỉ báo, chỉ số và chiến lược', cls: 'wide', body: `<div class="search">${ic('search')}<input placeholder="Tìm kiếm" id="iQ"></div><div class="chips" id="iTabs"></div><div class="ilist" id="iList"></div>` });
    const row = d => {
      const fav = indFavs().includes(d.id), cnt = App.chart.inds.filter(x => x.id === d.id).length;
      return `<div class="irow ${d.need ? 'dis' : ''}" data-id="${d.id}"><button class="star ${fav ? 'on' : ''}" data-star="${d.id}">${ic('star')}</button>
        <span class="nm">${esc(d.name)}${d.beta ? '<span class="tag">BETA</span>' : ''}${d.cat === 'options' ? '<span class="tag">BETA</span><span class="tag new">NEW</span>' : ''}${cnt ? `<span class="tag" style="color:var(--accent)">✓ ${cnt}</span>` : ''}
        ${d.need ? `<small>${esc(d.need)}</small>` : d.note ? `<small>${esc(d.note)}</small>` : ''}</span><button class="q" data-help="${d.id}" title="Giải thích">${ic('help')}</button></div>`;
    };
    const render = () => {
      $('#iTabs').innerHTML = tabs.map(([k, n]) => `<button class="chip ${k === cur && !q ? 'active' : ''}" data-t="${k}">${n}</button>`).join('');
      const all = Object.values(App.INDICATORS);
      let h = '';
      if (q) { const r = all.filter(d => d.name.toLowerCase().includes(q)); h = r.map(row).join('') || '<div class="empty">Không tìm thấy</div>'; }
      else if (cur === 'fav') h = indFavs().map(id => App.INDICATORS[id]).filter(Boolean).map(row).join('') || '<div class="empty">Bấm ☆ để thêm chỉ báo yêu thích</div>';
      else if (cur === 'pattern') {
        h = '<div class="isec">Mô hình biểu đồ</div>' + all.filter(d => d.cat === 'pattern' && d.sub === 'chart').map(row).join('')
          + '<div class="isec">Mô hình nến</div>' + all.filter(d => d.cat === 'pattern' && d.sub === 'candle').sort((a, b) => a.name.localeCompare(b.name)).map(row).join('');
      } else if (cur === 'stockpredict') h = ['sp_plan', 'sp_pha', 'sp_dong_pha', 'sp_dinh_day', 'st_daihan', 'st_fx_ls', 'st_dongpha', 'st_level1', 'st_macdsto', 'st_stockpredict'].map(id => App.INDICATORS[id]).filter(Boolean).map(row).join('');
      else if (cur === 'tpl') { U.close('ind'); return App.panels.templates(); }
      else h = all.filter(d => d.cat === cur).sort((a, b) => a.name.localeCompare(b.name)).map(row).join('');
      $('#iList').innerHTML = h;
    };
    render();
    $('#iQ').oninput = e => { q = e.target.value.trim().toLowerCase(); render(); };
    s.addEventListener('click', e => {
      const t = e.target.closest('[data-t]'); if (t) { cur = t.dataset.t; App.store.set('indTab', cur); q = ''; $('#iQ').value = ''; return render(); }
      const st = e.target.closest('[data-star]'); if (st) { const f = indFavs(), i = f.indexOf(st.dataset.star); if (i >= 0) f.splice(i, 1); else f.push(st.dataset.star); App.store.set('indFavs', f); return render(); }
      const hp = e.target.closest('[data-help]'); if (hp) { const d = App.INDICATORS[hp.dataset.help]; App.toast(d.name + ': ' + (App.IND_HELP[d.id] || d.need || (d.cat === 'strategy' ? 'Chiến lược có sẵn — xem kết quả ở bảng "Kiểm tra chiến lược" bên dưới biểu đồ.' : d.cat === 'pattern' ? 'Tự động nhận diện mô hình và đánh dấu trên biểu đồ.' : 'Chỉ báo tích hợp sẵn — bấm để thêm, bấm ⚙ trên chú thích để chỉnh.')), 'info', 7000); return; }
      const r = e.target.closest('.irow'); if (r) { const d = App.INDICATORS[r.dataset.id]; if (d.need) return App.toast(d.need, 'err'); App.chart.addIndicator(r.dataset.id); render(); }
    });
    setTimeout(() => !U.mobile() && $('#iQ').focus(), 80);
  };

  /* ---------- Cài đặt một chỉ báo ---------- */
  U.indSettings = function (inst) {
    const def = App.INDICATORS[inst.id], I = App.chart.inputs(inst);
    let tab = def.inputs.length ? 'in' : 'st';
    const s = U.sheet({ id: 'iset', title: def.name, body: `<div class="tabs2"><button data-tb="in">Đầu vào</button><button data-tb="st">Kiểu</button></div><div id="isBody"></div>`,
      foot: '<button class="btn" data-def>Mặc định</button><span class="grow"></span><button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>OK</button>' });
    const draft = { I: Object.assign({}, I), st: JSON.parse(JSON.stringify(inst.st || {})) };
    const render = () => {
      $$('.tabs2 button').forEach(b => b.classList.toggle('active', b.dataset.tb === tab));
      if (tab === 'in') $('#isBody').innerHTML = def.inputs.length ? def.inputs.map(([k, l, , type, opts]) => {
        const v = draft.I[k];
        if (type === 'sel') return `<div class="prow"><span>${esc(l)}</span><select data-k="${k}">${opts.map(o => `<option ${o === v ? 'selected' : ''}>${o}</option>`).join('')}</select></div>`;
        if (type === 'bool') return `<label class="chk"><input type="checkbox" data-k="${k}" ${v ? 'checked' : ''}> ${esc(l)}</label>`;
        return `<div class="prow"><span>${esc(l)}</span><input type="number" step="${type === 'float' ? 'any' : 1}" data-k="${k}" value="${v}"></div>`;
      }).join('') : '<p class="note">Chỉ báo này không có tham số.</p>';
      else $('#isBody').innerHTML = def.plots.length ? def.plots.map(([k, l]) => { const st = Object.assign(App.chart.plotStyle(inst, k), draft.st[k] || {});
        return `<div class="srow"><input type="checkbox" data-sv="${k}" ${st.v ? 'checked' : ''}><span class="nm">${esc(l)}</span><input type="color" data-sc="${k}" value="${st.c.slice(0, 7)}"><select data-sw="${k}">${[1, 1.5, 2, 3, 4].map(w => `<option ${+st.w === w ? 'selected' : ''} value="${w}">${w}px</option>`).join('')}</select></div>`; }).join('')
        : '<p class="note">Chỉ báo này vẽ bằng nhãn/hình — không có đường để chỉnh kiểu.</p>';
      if (def.cat === 'strategy') $('#isBody').insertAdjacentHTML('beforeend', `<label class="f">Vốn ban đầu</label><input type="number" id="btCap" value="${(App.settings.bt || {}).capital || 10000}"><label class="f">Phí giao dịch (%)</label><input type="number" step="any" id="btFee" value="${(App.settings.bt || {}).fee ?? 0.04}">`);
    };
    render();
    s.addEventListener('click', e => { const b = e.target.closest('[data-tb]'); if (b) { tab = b.dataset.tb; render(); } });
    s.addEventListener('input', e => {
      const t = e.target;
      if (t.dataset.k) { const d = def.inputs.find(x => x[0] === t.dataset.k); draft.I[t.dataset.k] = d[3] === 'bool' ? t.checked : d[3] === 'sel' ? t.value : (+t.value || d[2]); }
      const k = t.dataset.sv || t.dataset.sc || t.dataset.sw; if (k) { draft.st[k] = draft.st[k] || {}; if (t.dataset.sv) draft.st[k].v = t.checked; if (t.dataset.sc) draft.st[k].c = t.value; if (t.dataset.sw) draft.st[k].w = +t.value; }
    });
    s.querySelector('[data-c]').onclick = () => U.close('iset');
    s.querySelector('[data-def]').onclick = () => { draft.I = {}; def.inputs.forEach(([k, , v]) => draft.I[k] = v); draft.st = {}; render(); };
    s.querySelector('[data-ok]').onclick = () => {
      inst.I = draft.I; inst.st = draft.st;
      if (def.cat === 'strategy') { App.settings.bt = { capital: +$('#btCap').value || 10000, fee: +$('#btFee').value || 0 }; App.saveSettings(); }
      App.chart.saveInds(); App.chart.renderIndicators(); U.close('iset');
    };
  };

  /* =========================================================
   * LOẠI BIỂU ĐỒ
   * ========================================================= */
  const TYPE_ICON = { bar: 'M7 4v16M4 8h3M7 15h3M17 4v16M14 6h3M17 17h3', candle: 'M7 4v3M7 17v3M5 7h4v10H5zM17 3v5M17 15v5M15 8h4v7h-4z', hollow: 'M7 4v3M7 17v3M5 7h4v10H5zM17 3v5M17 15v5M15 8h4v7h-4z',
    line: 'M3 17l5-6l4 3l9-9', linemk: 'M3 17l5-6l4 3l9-9M8 11h.01M12 14h.01', step: 'M3 18h4v-5h5v3h4V8h5', area: 'M3 17l5-6l4 3l9-9v15H3z', hlcarea: 'M3 12l5-5l4 3l9-6M3 19l5-5l4 3l9-6', baseline: 'M3 12h18M3 15l5-7l4 8l9-9',
    columns: 'M5 20v-8M10 20V8M15 20v-5M20 20V5', highlow: 'M6 5v14M12 8v9M18 4v11', ha: 'M7 4v3M7 17v3M5 7h4v10H5zM17 3v5M17 15v5M15 8h4v7h-4z', renko: 'M3 16h5v4H3zM8 12h5v4H8zM13 8h5v4h-5z', linebreak: 'M4 14h4v6H4zM9 9h4v5H9zM14 5h4v4h-4z', kagi: 'M4 18V9h5v6h5V5h5v10', pnf: 'M5 6l3 3M8 6L5 9M5 11l3 3M8 11l-3 3M13 9a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0M13 14a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0' };
  U.typeSheet = function () {
    const s = U.sheet({ id: 'type', title: 'Loại biểu đồ', cls: 'small', body: `<div class="ilist typelist">${App.CHART_TYPES.map(([k, n]) => `<div class="irow ${App.chart.type === k ? 'on' : ''}" data-ty="${k}"><svg class="ico" viewBox="0 0 24 24"><path d="${TYPE_ICON[k]}"/></svg><span class="nm">${n}</span>${App.chart.type === k ? ic('check') : ''}</div>`).join('')}</div><p class="note">Renko, Line break, Kagi, Point &amp; figure dùng kích thước hộp tự động theo ATR (đổi trong Cài đặt biểu đồ).</p>` });
    s.addEventListener('click', e => { const r = e.target.closest('[data-ty]'); if (r) { App.chart.setType(r.dataset.ty); U.close('type'); } });
  };

  /* =========================================================
   * CÀI ĐẶT BIỂU ĐỒ
   * ========================================================= */
  U.chartSettings = function () {
    const cs = Object.assign({}, App.settings.chart || {});
    const s = U.sheet({ id: 'cset', title: 'Cài đặt biểu đồ', body: `
      <label class="f">Giao diện</label><div class="chips wrap">${Object.entries(App.THEMES).map(([k, t]) => `<button class="chip ${App.themeName === k ? 'active' : ''}" data-th="${k}">${t.name}</button>`).join('')}</div>
      <div class="row"><div><label class="f">Màu nến tăng</label><input type="color" id="csUp" value="${cs.up || App.theme.up}" class="inp" style="height:38px;padding:2px"></div><div><label class="f">Màu nến giảm</label><input type="color" id="csDn" value="${cs.dn || App.theme.down}" class="inp" style="height:38px;padding:2px"></div></div>
      <label class="f">Thang giá</label><select id="csScale"><option value="0">Thường</option><option value="1" ${cs.scale == 1 ? 'selected' : ''}>Logarit</option><option value="2" ${cs.scale == 2 ? 'selected' : ''}>Phần trăm</option><option value="3" ${cs.scale == 3 ? 'selected' : ''}>Chỉ số về 100</option></select>
      <label class="f">Kích thước hộp Renko / Kagi / P&amp;F (để trống = tự động theo ATR)</label><input type="number" step="any" id="csBox" value="${cs.box || ''}" placeholder="Tự động">
      <label class="chk"><input type="checkbox" id="csGrid" ${cs.grid !== false ? 'checked' : ''}> Hiện lưới</label>
      <label class="chk"><input type="checkbox" id="csMag" ${cs.magnetCross ? 'checked' : ''}> Con trỏ bám giá (magnet)</label>
      <label class="chk"><input type="checkbox" id="csWm" ${cs.watermark !== false ? 'checked' : ''}> Hiện tên mã mờ trên nền</label>
      <label class="chk"><input type="checkbox" id="csMk" ${App.settings.markerText !== false ? 'checked' : ''}> Hiện chữ trên nhãn mô hình / chiến lược</label>
      <button class="btn sm" id="csData" style="margin-top:8px">${ic('data')} Nguồn dữ liệu &amp; API key…</button>`,
      foot: '<button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>Lưu</button>' });
    s.addEventListener('click', e => { const t = e.target.closest('[data-th]'); if (t) { App.setTheme(t.dataset.th); $$('[data-th]').forEach(b => b.classList.toggle('active', b === t)); $('#csUp').value = App.theme.up; $('#csDn').value = App.theme.down; } });
    $('#csData').onclick = () => { U.close('cset'); U.dataSettings(); };
    s.querySelector('[data-c]').onclick = () => U.close('cset');
    s.querySelector('[data-ok]').onclick = () => {
      const up = $('#csUp').value, dn = $('#csDn').value;
      App.settings.chart = { up: up === App.theme.up ? null : up, dn: dn === App.theme.down ? null : dn, scale: +$('#csScale').value, box: +$('#csBox').value || null, grid: $('#csGrid').checked, magnetCross: $('#csMag').checked, watermark: $('#csWm').checked };
      App.settings.markerText = $('#csMk').checked;
      App.saveSettings(); $('#watermark').classList.toggle('hidden', !App.settings.chart.watermark);
      App.chart.applyTheme(); App.chart.refresh(true); U.close('cset');
    };
  };
  U.dataSettings = function () {
    const s = U.sheet({ id: 'dset', title: 'Nguồn dữ liệu', body: `
      <label class="f">API key Twelve Data (cổ phiếu Mỹ, Forex, Vàng)</label><input class="inp" id="dsKey" value="${esc(App.settings.tdKey || '')}" placeholder="Dán key vào đây" autocomplete="off">
      <p class="note">Đăng ký miễn phí tại <a href="https://twelvedata.com/register" target="_blank" rel="noopener">twelvedata.com/register</a> → mục <b>API Keys</b> → sao chép. Gói miễn phí: 800 lần gọi/ngày, 8 lần/phút. Key chỉ lưu trong trình duyệt của cô.</p>
      <label class="f">Proxy CORS (khi API cổ phiếu Việt Nam bị chặn)</label><input class="inp" id="dsProxy" value="${esc(App.settings.proxy || '')}" placeholder="VD: https://corsproxy.io/?url=" autocomplete="off">
      <p class="note">Để trống nếu dữ liệu VN tải bình thường. Có thể dùng <code>{url}</code> để chỉ chỗ chèn địa chỉ.</p>
      <button class="btn danger sm" id="dsReset">Xoá toàn bộ dữ liệu đã lưu</button>`,
      foot: '<button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>Lưu</button>' });
    s.querySelector('[data-c]').onclick = () => U.close('dset');
    $('#dsReset').onclick = () => U.confirm('Xoá danh sách theo dõi, cảnh báo, hình vẽ, bố cục, file CSV và cài đặt?', () => { try { Object.keys(localStorage).filter(k => k.startsWith('gv:')).forEach(k => localStorage.removeItem(k)); } catch (e) {} location.reload(); });
    s.querySelector('[data-ok]').onclick = () => { const had = !!App.settings.tdKey; App.settings.tdKey = $('#dsKey').value.trim(); App.settings.proxy = $('#dsProxy').value.trim(); App.saveSettings(); U.close('dset'); if (!had && App.settings.tdKey) App.panels.refreshQuotes(['TD']); App.toast('Đã lưu', 'ok'); };
  };

  /* =========================================================
   * CHỌN MÃ (mở / so sánh / thêm vào danh sách)
   * ========================================================= */
  const CHIPS = {
    SP: ['VNINDEX', 'VN30', 'FPT', 'HPG', 'VCB', 'MWG', 'SSI', 'VNM', 'TCB', 'VIX', 'PLC'],
    BINANCE: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'PAXGUSDT'],
    VN: ['VNINDEX', 'VN30', 'VNM', 'FPT', 'HPG', 'VCB', 'MWG', 'SSI', 'VIC', 'TCB', 'VIX'],
    TD: ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'NFLX', 'EUR/USD', 'USD/JPY', 'XAU/USD', 'SPX', 'DXY'],
    TCBS: ['VNINDEX', 'VN30', 'FPT', 'VCB', 'HPG', 'TCB', 'MWG', 'SSI', 'VNM', 'VIX'],
    DEMO: ['DEMO', 'ALPHA', 'BETA', 'GAMMA'], CSV: []
  };
  U.symbolSheet = function (mode, after) {
    let src = App.state.src;
    const title = { open: 'Tìm mã', compare: 'So sánh mã', watch: 'Thêm vào danh sách theo dõi' }[mode];
    const s = U.sheet({ id: 'sym', title, body: `<div class="search">${ic('search')}<input id="sQ" placeholder="Nhập mã, VD: BTCUSDT" autocomplete="off" autocapitalize="characters"></div>
      <div class="chips" id="sSrc"></div><p class="note" id="sHint"></p><div class="chips wrap" id="sChips"></div>
      <div id="sCsv" class="hidden"><label class="f">Nhập file CSV (cột: Ngày, Mở, Cao, Thấp, Đóng, Khối lượng)</label><div class="row"><input class="inp" id="csvName" placeholder="Tên hiển thị, VD: VANG_SJC"><label class="btn" style="flex:0">Chọn file…<input type="file" id="csvFile" accept=".csv,.txt,text/csv" hidden></label></div></div>
      <label class="f">Đã xem gần đây</label><div class="chips wrap" id="sRecent"></div>` });
    const render = () => {
      $('#sSrc').innerHTML = Object.entries(App.sources).map(([k, x]) => `<button class="chip ${k === src ? 'active' : ''}" data-src="${k}">${x.label}</button>`).join('');
      $('#sHint').textContent = App.sources[src].hint + (src === 'TD' && !App.settings.tdKey ? ' — chưa có API key, vào Cài đặt › Nguồn dữ liệu.' : '');
      const chips = src === 'CSV' ? App.store.get('csvNames', []) : CHIPS[src];
      $('#sChips').innerHTML = chips.map(c => { const n = App.symName(src, c); return `<button class="chip" data-sym="${esc(c)}">${esc(c)}${n ? ` <small>${esc(n)}</small>` : ''}</button>`; }).join('');
      $('#sCsv').classList.toggle('hidden', src !== 'CSV');
      $('#sRecent').innerHTML = App.store.get('recent', []).map(r => `<button class="chip" data-rs="${r.src}" data-sym="${esc(r.sym)}">${esc(r.sym)} <small>${App.sources[r.src] ? App.sources[r.src].short : ''}</small></button>`).join('') || '<span class="note">Chưa có</span>';
    };
    const choose = (sr, sym) => {
      if (!sym) return; U.close('sym'); sym = App.sources[sr].normalize(sym);
      if (mode === 'compare') App.chart.addCompare(sr, sym);
      else if (mode === 'watch') App.panels.addWatch(sr, sym, after);
      else App.loadSymbol(sr, sym, App.state.tf);
    };
    render();
    s.addEventListener('click', e => {
      const a = e.target.closest('[data-src]'); if (a) { src = a.dataset.src; render(); return; }
      const b = e.target.closest('[data-sym]'); if (b) choose(b.dataset.rs || src, b.dataset.sym);
    });
    $('#sQ').addEventListener('keydown', e => { if (e.key === 'Enter') choose(src, e.target.value.trim()); });
    $('#csvFile').onchange = async e => {
      const f = e.target.files[0]; if (!f) return;
      try {
        const bars = App.parseCSV(await f.text()), name = ($('#csvName').value.trim() || f.name.replace(/\.\w+$/, '')).toUpperCase().slice(0, 30);
        App.csvSets[name] = bars; App.store.set('csv:' + name, bars);
        const names = App.store.get('csvNames', []); if (!names.includes(name)) { names.push(name); App.store.set('csvNames', names); }
        App.toast(`Đã nhập ${bars.length} dòng`, 'ok'); choose('CSV', name);
      } catch (err) { App.toast('Lỗi đọc CSV: ' + err.message, 'err', 6000); }
    };
    setTimeout(() => !U.mobile() && $('#sQ').focus(), 80);
  };

  U.about = function () {
    U.sheet({ id: 'about', title: 'GreenView', cls: 'small', body: `<div style="text-align:center;padding:8px 0"><span class="logo">${App.logoSVG(App.theme, 64)}</span><h2 style="margin:8px 0 2px">Green<span style="color:var(--accent)">View</span></h2><p class="note">Công cụ biểu đồ giá cá nhân · ${Object.values(App.INDICATORS).filter(d => !d.need).length} chỉ báo &amp; mô hình · ${Object.values(App.draw.TOOLS).filter(t => !t.hidden).length} công cụ vẽ</p>
      <p class="note">Biểu đồ dùng thư viện mã nguồn mở Lightweight Charts™ của TradingView (giấy phép Apache 2.0).<br>Không phải lời khuyên đầu tư.</p></div>` });
  };
})(window.App);
