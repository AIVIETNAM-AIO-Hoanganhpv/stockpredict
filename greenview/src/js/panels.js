/* =========================================================
 * panels.js — Danh sách theo dõi, cảnh báo, cây đối tượng, đánh giá kỹ thuật,
 *             thông tin mã, Trung tâm phân tích, bố cục, mẫu chỉ báo,
 *             phát lại thanh, kiểm tra chiến lược, chụp ảnh
 * ========================================================= */
(function (App) {
  'use strict';
  const $ = App.$, $$ = App.$$, esc = App.esc, ic = App.icon, U = App.ui;
  const P = App.panels = {};

  /* ---------- Tên & biểu tượng tròn cho từng mã ---------- */
  const NAMES = {
    BTCUSDT: 'Bitcoin / TetherUS', ETHUSDT: 'Ethereum / TetherUS', BNBUSDT: 'BNB / TetherUS', SOLUSDT: 'Solana / TetherUS', XRPUSDT: 'XRP / TetherUS', DOGEUSDT: 'Dogecoin / TetherUS', ADAUSDT: 'Cardano / TetherUS', PAXGUSDT: 'PAX Gold / TetherUS',
    VNINDEX: 'Chỉ số VN-Index', VN30: 'Chỉ số VN30', HNXINDEX: 'Chỉ số HNX', VNM: 'CTCP Sữa Việt Nam', FPT: 'CTCP FPT', HPG: 'CTCP Tập đoàn Hòa Phát', VCB: 'Ngân hàng Vietcombank', MWG: 'CTCP Thế Giới Di Động', SSI: 'CTCP Chứng khoán SSI', VIC: 'Tập đoàn Vingroup', TCB: 'Ngân hàng Techcombank', VIX: 'CTCP Chứng khoán VIX',
    AAPL: 'Apple Inc.', MSFT: 'Microsoft Corp.', NVDA: 'NVIDIA Corp.', TSLA: 'Tesla, Inc.', NFLX: 'Netflix, Inc.', 'EUR/USD': 'Euro / Đô la Mỹ', 'USD/JPY': 'Đô la Mỹ / Yên Nhật', 'GBP/USD': 'Bảng Anh / Đô la Mỹ', 'XAU/USD': 'Vàng / Đô la Mỹ', SPX: 'Chỉ số S&P 500', DXY: 'Chỉ số Đồng Đô la Mỹ',
    DEMO: 'Dữ liệu giả lập'
  };
  App.symName = (src, sym) => NAMES[sym] || (src === 'BINANCE' && /USDT$/.test(sym) ? sym.replace(/USDT$/, '') + ' / TetherUS' : '');
  const BADGE = { BTCUSDT: ['₿', '#f7931a'], ETHUSDT: ['Ξ', '#627eea'], BNBUSDT: ['B', '#f3ba2f'], SOLUSDT: ['S', '#9945ff'], XRPUSDT: ['X', '#23292f'], DOGEUSDT: ['Ð', '#c2a633'], ADAUSDT: ['A', '#0033ad'], PAXGUSDT: ['Au', '#d4a017'],
    'XAU/USD': ['Au', '#d4a017'], 'EUR/USD': ['€', '#1e5aa8'], 'USD/JPY': ['¥', '#bc002d'], 'GBP/USD': ['£', '#012169'], AAPL: ['', '#1c1c1e'], TSLA: ['T', '#e31937'], NFLX: ['N', '#e50914'], MSFT: ['M', '#00a4ef'], NVDA: ['N', '#76b900'],
    SPX: ['500', '#b22234'], DXY: ['$', '#2e7d5b'], VNINDEX: ['VN', '#da251d'], VN30: ['30', '#da251d'] };
  App.badge = function (src, sym) {
    if (BADGE[sym]) return { txt: BADGE[sym][0] || sym[0], bg: BADGE[sym][1] };
    let h = 0; for (const c of sym) h = (h * 31 + c.charCodeAt(0)) % 360;
    return { txt: sym.replace(/[^A-Z0-9]/g, '').slice(0, src === 'VN' ? 3 : 2), bg: `hsl(${h},55%,40%)` };
  };

  /* =========================================================
   * THANH BÊN & TRANG ĐIỆN THOẠI
   * ========================================================= */
  P.tab = App.store.get('sideTab', 'wl');
  P.show = function (tab) {
    P.tab = tab; App.store.set('sideTab', tab);
    $$('.st').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    ({ wl: P.renderWatch, al: P.renderAlerts, ot: P.renderTree, tr: P.renderRating, in: P.renderInfo }[tab] || P.renderWatch)();
  };
  P.initSide = function () {
    $$('.st').forEach(b => b.onclick = () => P.show(b.dataset.tab));
    $$('#bottomNav button').forEach(b => b.onclick = () => P.page(b.dataset.page));
    P.show(U.mobile() ? 'wl' : P.tab);
    if (U.mobile()) $('#side').classList.add('closed');
  };
  // Điều hướng trên điện thoại
  P.page = function (pg) {
    $$('#bottomNav button').forEach(b => b.classList.toggle('active', b.dataset.page === pg));
    if (pg === 'chart') { $('#side').classList.add('closed'); return; }
    if (pg === 'menu') { $('#side').classList.add('closed'); P.hub(); $$('#bottomNav button').forEach(b => b.classList.toggle('active', b.dataset.page === 'chart')); return; }
    $('#side').classList.remove('closed'); P.show(pg);
  };
  P.refreshSide = () => { if (!$('#side').classList.contains('closed')) P.show(P.tab); };

  /* =========================================================
   * DANH SÁCH THEO DÕI (có nhóm, như TradingView)
   * ========================================================= */
  let wl = App.store.get('wl2', [
    { sec: 'Crypto' }, { src: 'BINANCE', sym: 'BTCUSDT' }, { src: 'BINANCE', sym: 'ETHUSDT' }, { src: 'BINANCE', sym: 'SOLUSDT' }, { src: 'BINANCE', sym: 'PAXGUSDT' },
    { sec: 'Cổ phiếu Việt Nam' }, { src: 'VN', sym: 'VNINDEX' }, { src: 'VN', sym: 'FPT' }, { src: 'VN', sym: 'HPG' }, { src: 'VN', sym: 'VIX' },
    { sec: 'Mỹ · Forex · Vàng' }, { src: 'TD', sym: 'XAU/USD' }, { src: 'TD', sym: 'AAPL' }, { src: 'TD', sym: 'EUR/USD' },
    { sec: 'Giả lập' }, { src: 'DEMO', sym: 'DEMO' }
  ]);
  const quotes = {}; const qk = (s, y) => s + ':' + y;
  P.quotes = quotes;
  const saveWl = () => App.store.set('wl2', wl);
  P.addWatch = function (src, sym, afterSec) {
    if (wl.some(w => w.src === src && w.sym === sym)) return App.toast(sym + ' đã có trong danh sách');
    let at = wl.length;
    if (afterSec != null) { at = afterSec + 1; while (at < wl.length && !wl[at].sec) at++; }
    wl.splice(at, 0, { src, sym }); saveWl(); P.refreshQuotes([src]); P.refreshSide(); App.toast('Đã thêm ' + sym, 'ok');
  };
  P.renderWatch = function () {
    const s = App.state;
    let h = `<div class="sec-head"><span>Danh sách theo dõi</span><span style="display:flex;gap:2px"><button data-w="addsec" title="Thêm nhóm">${ic('folder')}</button><button data-w="add" title="Thêm mã">${ic('plus')}</button></span></div>`;
    wl.forEach((w, i) => {
      if (w.sec) { h += `<div class="wl-sec"><span>${esc(w.sec)}</span><span style="display:flex;gap:2px"><button class="mini" data-w="addto" data-i="${i}" title="Thêm mã vào nhóm">${ic('plus')}</button><button class="mini" data-w="delsec" data-i="${i}" title="Xoá nhóm">${ic('x')}</button></span></div>`; return; }
      const q = quotes[qk(w.src, w.sym)], b = App.badge(w.src, w.sym), cls = q ? (q.chg >= 0 ? 'up' : 'down') : 'muted', need = w.src === 'TD' && !App.settings.tdKey;
      const abs = q && q.prev ? q.price - q.prev : null;
      h += `<div class="wl-row ${w.src === s.src && w.sym === s.sym ? 'cur' : ''}" data-i="${i}">
        <span class="wl-ico" style="background:${b.bg}">${esc(b.txt)}</span>
        <span class="wl-nm"><b>${esc(w.sym)}</b><small>${esc(App.symName(w.src, w.sym) || App.sources[w.src].short)}</small></span>
        <span class="wl-px" data-q="${esc(qk(w.src, w.sym))}"><b>${q ? App.fmtPrice(q.price) : need ? '<small class="muted">cần key</small>' : '…'}</b><small class="${cls}">${q ? (abs != null ? (abs >= 0 ? '+' : '') + App.fmtPrice(abs) + ' ' : '') + App.fmtPct(q.chg) : ''}</small></span>
        <button class="del" data-w="del" data-i="${i}" title="Bỏ khỏi danh sách">${ic('x')}</button></div>`;
    });
    $('#sideBody').innerHTML = h;
  };
  $('#sideBody') && 0;
  document.addEventListener('click', e => {
    const body = e.target.closest('#sideBody'); if (!body || P.tab !== 'wl') return;
    const b = e.target.closest('[data-w]');
    if (b) {
      e.stopPropagation(); const i = +b.dataset.i;
      if (b.dataset.w === 'del') { wl.splice(i, 1); saveWl(); P.renderWatch(); }
      if (b.dataset.w === 'delsec') U.confirm(`Xoá nhóm "${wl[i].sec}" (các mã trong nhóm vẫn giữ)?`, () => { wl.splice(i, 1); saveWl(); P.renderWatch(); });
      if (b.dataset.w === 'add') U.symbolSheet('watch');
      if (b.dataset.w === 'addto') U.symbolSheet('watch', i);
      if (b.dataset.w === 'addsec') U.prompt('Tên nhóm mới', '', v => { if (v && v.trim()) { wl.push({ sec: v.trim() }); saveWl(); P.renderWatch(); } });
      return;
    }
    const r = e.target.closest('.wl-row');
    if (r) { const w = wl[+r.dataset.i]; App.loadSymbol(w.src, w.sym, App.state.tf); if (U.mobile()) P.page('chart'); }
  });

  const POLL = { BINANCE: 10, DEMO: 5, CSV: 3600, VN: 60, TD: 180 }, lastPoll = {};
  P.refreshQuotes = async function (only) {
    const groups = {};
    wl.forEach(w => { if (!w.sec) (groups[w.src] = groups[w.src] || []).push(w.sym); });
    await Promise.all(Object.entries(groups).map(async ([src, syms]) => {
      if (only && !only.includes(src)) return;
      lastPoll[src] = Date.now();
      try {
        const res = await App.sources[src].quotes(syms);
        Object.entries(res).forEach(([sym, q]) => {
          const k = qk(src, sym), old = quotes[k];
          q.prev = q.price / (1 + q.chg / 100);
          quotes[k] = q;
          if (!(src === App.state.src && sym === App.state.sym)) App.onPrice(src, sym, q.price, true);
          if (old && old.price !== q.price) { const el = document.querySelector(`[data-q="${CSS.escape(k)}"]`); if (el) { const row = el.parentElement; row.classList.remove('flash-up', 'flash-down'); void row.offsetWidth; row.classList.add(q.price > old.price ? 'flash-up' : 'flash-down'); } }
        });
      } catch (e) { /* thử lại lần sau */ }
    }));
    if (P.tab === 'wl') P.refreshSide();
  };
  setInterval(() => { const due = Object.keys(POLL).filter(s => !lastPoll[s] || Date.now() - lastPoll[s] >= POLL[s] * 1000); if (due.length) P.refreshQuotes(due); }, 5000);
  P.liveQuote = function (src, sym, price) {
    const q = quotes[qk(src, sym)]; if (!q || q.price === price) return;
    q.price = price; if (q.prev) q.chg = (price / q.prev - 1) * 100;
    const el = document.querySelector(`[data-q="${CSS.escape(qk(src, sym))}"] b`); if (el) el.textContent = App.fmtPrice(price);
  };

  /* =========================================================
   * CẢNH BÁO GIÁ
   * ========================================================= */
  let alerts = App.store.get('alerts', []), alog = App.store.get('alertLog', []);
  const saveAl = () => { App.store.set('alerts', alerts); App.store.set('alertLog', alog.slice(0, 50)); P.badge(); };
  P.badge = () => { const n = alerts.filter(a => a.on).length; $('#alBadge').textContent = n; $('#alBadge').classList.toggle('hidden', !n); };
  App.onPrice = function (src, sym, price, fromQuote) {
    if (!fromQuote) P.liveQuote(src, sym, price);
    alerts.forEach(a => {
      if (!a.on || a.src !== src || a.sym !== sym) return;
      const prev = a.last; a.last = price;
      const hit = a.op === '>=' ? price >= a.price : a.op === '<=' ? price <= a.price : prev != null && ((prev < a.price && price >= a.price) || (prev > a.price && price <= a.price));
      if (hit) {
        a.on = false; const msg = `🔔 ${a.sym} ${{ '>=': '≥', '<=': '≤', 'x': 'cắt' }[a.op]} ${App.fmtPrice(a.price)} — giá ${App.fmtPrice(price)}${a.note ? ' (' + a.note + ')' : ''}`;
        alog.unshift({ msg, at: Date.now() }); saveAl(); App.toast(msg, 'alert', 15000); App.beep();
        try { if ('Notification' in window && Notification.permission === 'granted') new Notification('GreenView — Cảnh báo giá', { body: msg }); } catch (e) {}
        if (P.tab === 'al') P.refreshSide();
      }
    });
  };
  P.renderAlerts = function () {
    $('#sideBody').innerHTML = `<div class="sec-head"><span>Cảnh báo</span><button data-a="new" title="Tạo cảnh báo">${ic('plus')}</button></div>` +
      (alerts.map((a, i) => `<div class="al-row ${a.on ? '' : 'off'}"><span class="wl-ico" style="background:${App.badge(a.src, a.sym).bg};width:28px;height:28px">${esc(App.badge(a.src, a.sym).txt)}</span>
        <div class="info"><b>${esc(a.sym)}</b> ${{ '>=': '≥', '<=': '≤', 'x': 'cắt' }[a.op]} ${App.fmtPrice(a.price)}<small>${esc(App.sources[a.src] ? App.sources[a.src].short : a.src)}${a.note ? ' · ' + esc(a.note) : ''}${a.on ? ' · đang chờ' : ' · đã kích hoạt / tắt'}</small></div>
        <button class="mini" data-a="tog" data-i="${i}" title="${a.on ? 'Tắt' : 'Bật lại'}">${ic(a.on ? 'pause' : 'play')}</button><button class="mini" data-a="del" data-i="${i}" title="Xoá">${ic('trash')}</button></div>`).join('') || '<div class="empty">Chưa có cảnh báo nào</div>') +
      `<div class="sec-head"><span>Nhật ký</span></div>` + (alog.slice(0, 20).map(l => `<div class="log-row">${esc(l.msg)}<br><small>${new Date(l.at).toLocaleString('vi-VN')}</small></div>`).join('') || '<div class="empty">—</div>') +
      '<p class="note">Cảnh báo chỉ hoạt động khi trang GreenView đang mở.</p>';
    $('#sideBody').onclick = e => {
      if (P.tab !== 'al') return; const b = e.target.closest('[data-a]'); if (!b) return;
      if (b.dataset.a === 'new') P.alertSheet();
      if (b.dataset.a === 'tog') { alerts[+b.dataset.i].on = !alerts[+b.dataset.i].on; saveAl(); P.renderAlerts(); }
      if (b.dataset.a === 'del') { alerts.splice(+b.dataset.i, 1); saveAl(); P.renderAlerts(); }
    };
  };
  P.alertSheet = function (price) {
    const s = App.state, last = s.bars[s.bars.length - 1];
    const sh = U.sheet({ id: 'alert', title: 'Tạo cảnh báo', cls: 'small', body: `<label class="f">Mã</label><div class="inp">${esc(s.sym)} · ${esc(App.sources[s.src].short)}</div>
      <label class="f">Điều kiện</label><select id="aOp"><option value="x">Giá cắt qua</option><option value=">=">Giá lên đến hoặc vượt (≥)</option><option value="<=">Giá xuống đến hoặc thấp hơn (≤)</option></select>
      <label class="f">Mức giá</label><input type="number" step="any" id="aPx" value="${price || (last ? +last.close.toPrecision(6) : '')}">
      <p class="note">Giá hiện tại: ${last ? App.fmtPrice(last.close) : '–'}</p><label class="f">Ghi chú</label><input type="text" id="aNote" maxlength="60" placeholder="VD: chốt lời">`,
      foot: '<button class="btn" data-c>Huỷ</button><button class="btn pri" data-ok>Tạo</button>' });
    sh.querySelector('[data-c]').onclick = () => U.close('alert');
    sh.querySelector('[data-ok]').onclick = () => {
      const px = parseFloat($('#aPx').value); if (!(px > 0)) return App.toast('Nhập mức giá', 'err');
      alerts.push({ id: Date.now(), src: s.src, sym: s.sym, op: $('#aOp').value, price: px, note: $('#aNote').value.trim(), on: true, last: last ? last.close : null });
      saveAl(); U.close('alert'); App.toast('Đã tạo cảnh báo cho ' + s.sym, 'ok');
      try { if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission().catch(() => {}); } catch (e) {}
      if (!wl.some(w => w.src === s.src && w.sym === s.sym)) P.addWatch(s.src, s.sym);
      P.refreshSide();
    };
  };

  /* =========================================================
   * CÂY ĐỐI TƯỢNG
   * ========================================================= */
  P.renderTree = function () {
    const C = App.chart, D = App.draw;
    let h = `<div class="sec-head"><span>Chỉ báo (${C.inds.length})</span><button data-t="addind" title="Thêm chỉ báo">${ic('plus')}</button></div>`;
    h += C.inds.map(x => { const d = App.INDICATORS[x.id]; return `<div class="ot-row"><span class="ot-ico">${ic('fx')}</span><div class="info">${esc(d ? d.name : x.id)}<small>${d && d.overlay ? 'Trên biểu đồ giá' : 'Khung riêng'}</small></div>
      <button class="mini" data-t="ieye" data-u="${x.uid}">${ic(x.hidden ? 'eyeoff' : 'eye')}</button><button class="mini" data-t="iset" data-u="${x.uid}">${ic('gear')}</button><button class="mini" data-t="idel" data-u="${x.uid}">${ic('trash')}</button></div>`; }).join('') || '<div class="empty">Chưa có</div>';
    h += `<div class="sec-head"><span>Hình vẽ (${D.list.length})</span>${D.list.length ? `<button data-t="dclear" title="Xoá tất cả">${ic('trash')}</button>` : ''}</div>`;
    h += D.list.map((d, i) => { const t = D.TOOLS[d.tool] || {}; return `<div class="ot-row"><span class="ot-ico tsvg">${t.icon || ''}</span><div class="info" data-t="dsel" data-k="${i}" style="cursor:pointer">${esc(t.name || d.tool)}${d.style.text ? ` <small>${esc(String(d.style.text).slice(0, 30))}</small>` : ''}</div>
      <button class="mini" data-t="deye" data-k="${i}">${ic(d.hidden ? 'eyeoff' : 'eye')}</button><button class="mini" data-t="dlock" data-k="${i}">${ic(d.locked ? 'lock' : 'unlock')}</button><button class="mini" data-t="ddel" data-k="${i}">${ic('trash')}</button></div>`; }).join('') || '<div class="empty">Chưa có hình vẽ cho mã này</div>';
    $('#sideBody').innerHTML = h;
    $('#sideBody').onclick = e => {
      if (P.tab !== 'ot') return; const b = e.target.closest('[data-t]'); if (!b) return;
      const t = b.dataset.t, inst = C.inds.find(x => x.uid === +b.dataset.u), d = D.list[+b.dataset.k];
      if (t === 'addind') U.indSheet();
      if (t === 'ieye') { inst.hidden = !inst.hidden; C.saveInds(); C.renderIndicators(); }
      if (t === 'iset') U.indSettings(inst);
      if (t === 'idel') C.removeIndicator(inst.uid);
      if (t === 'dclear') U.confirm('Xoá tất cả hình vẽ?', D.clearAll);
      if (t === 'dsel') D.select(d);
      if (t === 'deye') { d.hidden = !d.hidden; D.save(); }
      if (t === 'dlock') { d.locked = !d.locked; D.save(); }
      if (t === 'ddel') D.remove(d);
      P.renderTree();
    };
  };
  U.refreshTree = () => { if (P.tab === 'ot') P.refreshSide(); };

  /* =========================================================
   * ĐÁNH GIÁ KỸ THUẬT (đồng hồ)
   * ========================================================= */
  const gauge = (v, size = 200) => {
    const a = Math.PI * (1 - (v + 1) / 2), cx = size / 2, cy = size * 0.55, r = size * 0.4;
    const seg = (a1, a2, col) => `<path d="M${cx + r * Math.cos(a1)} ${cy - r * Math.sin(a1)} A${r} ${r} 0 0 1 ${cx + r * Math.cos(a2)} ${cy - r * Math.sin(a2)}" stroke="${col}" stroke-width="${size * 0.06}" fill="none"/>`;
    const cols = [App.theme.down, '#f0596b99', App.theme.muted, App.theme.up + '99', App.theme.up];
    let h = `<svg width="${size}" height="${size * 0.62}" viewBox="0 0 ${size} ${size * 0.62}">`;
    for (let k = 0; k < 5; k++) h += seg(Math.PI - k * Math.PI / 5 - 0.03, Math.PI - (k + 1) * Math.PI / 5 + 0.03, cols[k]);
    h += `<line x1="${cx}" y1="${cy}" x2="${cx + r * 0.85 * Math.cos(a)}" y2="${cy - r * 0.85 * Math.sin(a)}" stroke="${App.theme.text}" stroke-width="3" stroke-linecap="round"/><circle cx="${cx}" cy="${cy}" r="5" fill="${App.theme.text}"/></svg>`;
    return h;
  };
  P.ratingHTML = function () {
    const D = App.chart.D; if (!D || D.n < 60) return '<div class="empty">Cần ít nhất 60 nến</div>';
    const r = App.techRating(D), col = v => v > 0.1 ? 'up' : v < -0.1 ? 'down' : 'muted';
    const tot = { buy: r.maC.buy + r.oscC.buy, sell: r.maC.sell + r.oscC.sell, neu: r.maC.neu + r.oscC.neu };
    return `<div class="gauge-box"><h4>Tổng quan · ${App.TF_LABEL[App.state.tf]}</h4>${gauge(r.all)}<div class="lbl ${col(r.all)}">${App.ratingLabel(r.all)}</div>
      <div class="gauge-cnt"><span>Bán<b class="down">${tot.sell}</b></span><span>Trung lập<b>${tot.neu}</b></span><span>Mua<b class="up">${tot.buy}</b></span></div>
      <div class="gauges-sm"><div><h4>Dao động</h4>${gauge(r.osc, 130)}<div class="${col(r.osc)}" style="font-weight:600">${App.ratingLabel(r.osc)}</div></div><div><h4>Đường trung bình</h4>${gauge(r.ma, 130)}<div class="${col(r.ma)}" style="font-weight:600">${App.ratingLabel(r.ma)}</div></div></div>
      <p class="note">Tổng hợp tín hiệu từ 15 đường trung bình và 11 bộ dao động, theo cách tính "Technical Ratings" của TradingView. Không phải lời khuyên đầu tư.</p></div>`;
  };
  P.renderRating = () => { $('#sideBody').innerHTML = `<div class="sec-head"><span>Chỉ số kỹ thuật</span></div>` + P.ratingHTML(); };

  /* ---------- Thông tin mã ---------- */
  P.infoHTML = function () {
    const s = App.state, b = s.bars; if (!b.length) return '';
    const last = b[b.length - 1], first = b[0], hi = Math.max(...b.map(x => x.high)), lo = Math.min(...b.map(x => x.low));
    const vol = b.slice(-20).reduce((a, x) => a + x.volume, 0) / Math.min(20, b.length), D = App.ta.prep(b), atr = App.ta.atr(D, 14)[D.n - 1];
    const bd = App.badge(s.src, s.sym);
    return `<div style="display:flex;gap:12px;align-items:center;padding:12px 14px"><span class="wl-ico" style="background:${bd.bg};width:44px;height:44px;font-size:14px">${esc(bd.txt)}</span><div><b style="font-size:18px">${esc(s.sym)}</b><div class="muted">${esc(App.symName(s.src, s.sym) || '')} · ${esc(App.sources[s.src].label)}</div></div></div>
      <div style="padding:0 14px;font-size:26px;font-weight:700">${App.fmtPrice(last.close)} <span class="${last.close >= b[b.length - 2].close ? 'up' : 'down'}" style="font-size:15px">${App.fmtPct((last.close / b[b.length - 2].close - 1) * 100)}</span></div>
      <div class="info-grid"><div><small>Cao nhất (dữ liệu đã tải)</small><b>${App.fmtPrice(hi)}</b></div><div><small>Thấp nhất</small><b>${App.fmtPrice(lo)}</b></div>
      <div><small>Thay đổi từ đầu kỳ</small><b class="${last.close >= first.close ? 'up' : 'down'}">${App.fmtPct((last.close / first.close - 1) * 100)}</b></div><div><small>ATR(14)</small><b>${App.fmtPrice(atr)}</b></div>
      <div><small>KL trung bình 20 nến</small><b>${App.fmtVol(vol)}</b></div><div><small>Số nến đã tải</small><b>${b.length}</b></div>
      <div><small>Từ</small><b>${App.fmtTime(first.time, false)}</b></div><div><small>Đến</small><b>${App.fmtTime(last.time)}</b></div></div>
      ${App.mcp && ['VN', 'TCBS'].includes(s.src) ? '' : '<p class="note">Tài chính doanh nghiệp, khối ngoại, tin tức: có cho cổ phiếu Việt Nam khi mở trong Claude với connector TCBS.</p>'}`;
  };
  P.renderInfo = () => {
    $('#sideBody').innerHTML = `<div class="sec-head"><span>Thông tin mã</span></div>` + P.infoHTML() + '<div id="tcbsBox"></div>';
    P.tcbsInfo($('#tcbsBox'));
  };

  /* ---------- Dữ liệu doanh nghiệp từ connector TCBS ---------- */
  const pc = v => v == null || isNaN(v) ? '–' : (v * 100).toFixed(1) + '%';
  const nf = (v, d = 1) => v == null || isNaN(v) ? '–' : (+v).toLocaleString('vi-VN', { maximumFractionDigits: d });
  P.tcbsInfo = async function (box) {
    const s = App.state;
    if (!box) return;
    if (!(s.src === 'VN' || s.src === 'TCBS')) { box.innerHTML = '<p class="note">Thông tin doanh nghiệp, tài chính, khối ngoại và tin tức có cho cổ phiếu Việt Nam (nguồn TCBS).</p>'; return; }
    if (!App.mcp) { box.innerHTML = '<p class="note">Mở GreenView trong Claude (đã kết nối TCBS) để xem thêm thông tin doanh nghiệp, tài chính, khối ngoại và tin tức.</p>'; return; }
    const sym = s.sym, idx = App.isIndex(sym);
    box.innerHTML = `<div class="sec-head"><span>Dữ liệu TCBS</span><span class="muted" style="font-weight:400;font-size:11px">qua connector</span></div>
      ${idx ? '' : '<div id="tcO"><p class="note">Đang tải tổng quan…</p></div><div id="tcF"></div>'}<div id="tcG"></div>${idx ? '' : '<div id="tcK"></div><div id="tcN"></div>'}`;
    const sec = (id, fn) => fn().catch(e => { const el = $('#' + id); if (el) el.innerHTML = `<p class="note down">${esc(e.message)}</p>`; });
    const still = () => App.state.sym === sym && document.getElementById('tcbsBox');
    if (!idx) sec('tcO', async () => {
      const [o, v] = await Promise.all([App.tcbs('getTickerOverview', { ticker: sym }), App.tcbs('getPriceVolatility', { ticker: sym }).catch(() => null)]);
      if (!still()) return;
      $('#tcO').innerHTML = `<div style="padding:0 14px"><b>${esc(o.shortName || sym)}</b> <span class="muted">· ${esc(o.exchange || '')} · ${esc(o.industry || '')}</span></div>
        <div class="info-grid"><div><small>1 tuần</small><b class="${o.deltaInWeek >= 0 ? 'up' : 'down'}">${pc(o.deltaInWeek)}</b></div><div><small>1 tháng</small><b class="${o.deltaInMonth >= 0 ? 'up' : 'down'}">${pc(o.deltaInMonth)}</b></div>
        <div><small>1 năm</small><b class="${o.deltaInYear >= 0 ? 'up' : 'down'}">${pc(o.deltaInYear)}</b></div><div><small>Xếp hạng TCBS (1–5)</small><b>${nf(o.stockRating)}</b></div>
        ${v ? `<div><small>Cao nhất 52 tuần</small><b>${nf(v.highestPrice, 0)}</b></div><div><small>Thấp nhất 52 tuần</small><b>${nf(v.lowestPrice, 0)}</b></div>` : ''}
        <div><small>Sở hữu nước ngoài</small><b>${pc(o.foreignPercent)}</b></div><div><small>CP lưu hành (triệu)</small><b>${nf(o.outstandingShare)}</b></div>
        <div><small>Năm thành lập</small><b>${esc(o.establishedYear || '–')}</b></div><div><small>Số nhân viên</small><b>${nf(o.noEmployees, 0)}</b></div></div>
        ${o.website ? `<p class="note" style="padding:0 14px"><a href="${esc(o.website)}" target="_blank" rel="noopener">${esc(o.website)}</a></p>` : ''}`;
      P._companyType = o.companyType;
      sec('tcF', async () => {
        const bank = o.companyType === 'NH', r = await App.tcbs(bank ? 'getFinancialRatioForBank' : 'getFinancialRatioForNonBank', { ticker: sym, yearly: 1, fromYear: new Date().getFullYear() - 3 });
        const rows = (r.result || r || []).slice ? (r.result || r) : []; if (!still()) return;
        const last = rows.sort((a, b) => b.year - a.year).slice(0, 3);
        $('#tcF').innerHTML = `<div class="sec-head"><span>Chỉ số tài chính (năm)</span></div><div style="padding:0 14px"><table class="tt"><tr><th></th>${last.map(x => `<th>${x.year}</th>`).join('')}</tr>
          ${[['P/E', 'priceToEarning', nf], ['P/B', 'priceToBook', nf], ['EPS (đ)', 'earningPerShare', v => nf(v, 0)], ['ROE', 'roe', pc], ['ROA', 'roa', pc], ['Cổ tức', 'dividend', pc]].concat(bank ? [['NIM', 'interestMargin', pc], ['Nợ xấu', 'badDebtPercentage', pc]] : [['Biên LN gộp', 'grossProfitMargin', pc], ['Nợ/Vốn CSH', 'debtOnEquity', nf]])
            .map(([l, k, f]) => `<tr><td>${l}</td>${last.map(x => `<td>${f(x[k])}</td>`).join('')}</tr>`).join('')}</table></div>`;
      });
    });
    sec('tcG', async () => {
      if (idx) { $('#tcG').innerHTML = ''; return; }
      const tf = { '1D': 'D', '1W': 'W', '1h': '1h', '15m': '15m', '5m': '5m', '1m': '1m' }[s.tf] || 'D';
      const g = await App.tcbs('getGaugeChart', { ticker: sym, period: tf }); if (!still()) return;
      const lab = { 'Strong Buy': 'Mua mạnh', Buy: 'Mua', Neutral: 'Trung lập', Sell: 'Bán', 'Strong Sell': 'Bán mạnh' };
      const cls = x => /Buy/.test(x) ? 'up' : /Sell/.test(x) ? 'down' : 'muted';
      const sm = g.summary || {};
      $('#tcG').innerHTML = `<div class="sec-head"><span>Đánh giá kỹ thuật của TCBS</span></div><div class="info-grid">
        <div><small>Tổng hợp</small><b class="${cls(sm.signal)}">${lab[sm.signal] || sm.signal || '–'}</b></div><div><small>Mua / Trung lập / Bán</small><b>${sm.buy || 0} / ${sm.neutral || 0} / ${Math.abs(sm.sell || 0)}</b></div>
        <div><small>Dao động</small><b class="${cls(g.indicator && g.indicator.signal && g.indicator.signal.signal)}">${lab[g.indicator && g.indicator.signal && g.indicator.signal.signal] || '–'}</b></div><div><small>Đường trung bình</small><b class="${cls(g.average && g.average.signal)}">${lab[g.average && g.average.signal] || '–'}</b></div>
        <div><small>RSI</small><b>${nf(g.indicator && g.indicator.rsi && g.indicator.rsi.value)}</b></div><div><small>ADX</small><b>${nf(g.indicator && g.indicator.adx && g.indicator.adx.value)}</b></div></div>`;
    });
    if (!idx) sec('tcK', async () => {
      const f = await App.tcbs('getVolumeAndForeign', { ticker: sym }); if (!still()) return;
      const l = (f.listVolumeForeignInfoDto || []).slice(-7).reverse();
      $('#tcK').innerHTML = `<div class="sec-head"><span>Khối ngoại (7 phiên gần nhất)</span></div><div style="padding:0 14px"><table class="tt"><tr><th>Ngày</th><th>Mua</th><th>Bán</th><th>Ròng</th></tr>
        ${l.map(x => `<tr><td>${esc(x.dateReport)}</td><td>${App.fmtVol(x.foreignBuy)}</td><td>${App.fmtVol(Math.abs(x.foreignSell))}</td><td class="${x.netForeignVol >= 0 ? 'up' : 'down'}">${App.fmtVol(x.netForeignVol)}</td></tr>`).join('')}</table>
        ${l[0] ? `<p class="note">Ròng cộng dồn: <b class="${l[0].accNetFVol >= 0 ? 'up' : 'down'}">${App.fmtVol(l[0].accNetFVol)}</b> CP · Sức mạnh giá RS: ${nf(l[0].rsRank, 0)}/100</p>` : ''}</div>`;
    });
    if (!idx) sec('tcN', async () => {
      const n = await App.tcbs('getTickerActivityNews', { ticker: sym, size: 8 }); if (!still()) return;
      const l = n.listActivityNews || [];
      $('#tcN').innerHTML = `<div class="sec-head"><span>Tin tức</span></div>` + (l.map(x => `<div class="log-row"><b style="font-weight:500">${esc(x.title)}</b><br><small>${esc(x.source || '')} · ${esc(x.publishDate || '')} · giá ${nf(x.price, 0)} (<span class="${x.priceChangeRatio >= 0 ? 'up' : 'down'}">${pc(x.priceChangeRatio)}</span>)</small></div>`).join('') || '<div class="empty">Không có tin</div>');
    });
  };

  /* =========================================================
   * TRUNG TÂM PHÂN TÍCH (menu)
   * ========================================================= */
  P.hub = function () {
    const t = (id, icon, label, dis) => `<button class="tile ${dis ? 'dis' : ''}" data-h="${id}">${ic(icon)}<span>${label}</span></button>`;
    const s = U.sheet({ id: 'hub', title: 'Trung tâm phân tích', body: `
      <div class="grid3">${t('layout', 'layout', 'Quản lý bố cục')}${t('cset', 'gear', 'Cài đặt biểu đồ')}${t('theme', App.themeName === 'dark' ? 'sun' : 'moon', App.themeName === 'dark' ? 'Giao diện sáng' : 'Giao diện tối')}${t('new', 'newc', 'Mới')}${t('save', 'save', 'Lưu')}${t('open', 'folder', 'Mở')}</div>
      <div class="hub-sec">CÔNG CỤ</div>
      <div class="grid2">${t('ind', 'fx', 'Chỉ báo')}${t('cmp', 'plus', 'So sánh')}${t('alert', 'alarm', 'Cảnh báo')}${t('replay', 'replay', 'Chế độ phát lại thanh')}</div>
      <div class="grid3" style="margin-top:10px">${t('tpl', 'grid', 'Mẫu chỉ báo')}${t('type', 'candle', 'Loại biểu đồ')}${t('tree', 'layers', 'Cây đối tượng')}${t('draw', 'pen', 'Bản vẽ')}${t('shot', 'camera', 'Chụp ảnh')}${t('data', 'data', 'Nguồn dữ liệu')}</div>
      <div class="hub-sec">THÔNG TIN</div>
      <div class="grid2">${t('info', 'info', 'Thông tin chi tiết mã giao dịch')}${t('fin', 'bars', 'Tài chính', !App.mcp)}${t('fc', 'chart', 'Dự báo', 1)}${t('rate', 'gauge', 'Chỉ số kỹ thuật')}</div>
      <div class="hub-sec">GIỚI THIỆU</div><div class="grid2">${t('about', 'help', 'Về GreenView')}${t('strat', 'target', 'Kiểm tra chiến lược')}</div>` });
    s.addEventListener('click', e => {
      const b = e.target.closest('[data-h]'); if (!b) return; const h = b.dataset.h; U.close('hub');
      ({ layout: P.layouts, cset: U.chartSettings, theme: () => App.setTheme(App.themeName === 'dark' ? 'light' : 'dark'), new: P.newLayout, save: P.saveLayout, open: P.layouts,
        ind: () => U.indSheet(), cmp: () => U.symbolSheet('compare'), alert: P.alertSheet, replay: P.replayStart, tpl: P.templates, type: U.typeSheet, tree: () => P.mobilePanel('ot'),
        draw: () => U.drawSheet(), shot: P.screenshot, data: U.dataSettings, info: () => P.mobilePanel('in'), rate: () => P.mobilePanel('tr'), about: U.about,
        fin: () => { if (!App.mcp) return App.toast('Tài chính có khi mở GreenView trong Claude và đã kết nối TCBS', 'err'); if (!['VN', 'TCBS'].includes(App.state.src)) return App.toast('Chỉ có cho cổ phiếu Việt Nam', 'err'); P.mobilePanel('in'); }, fc: () => App.toast('Dự báo của chuyên gia cần nguồn trả phí — chưa hỗ trợ', 'err'),
        strat: () => { if (!App.chart.inds.some(x => App.INDICATORS[x.id] && App.INDICATORS[x.id].cat === 'strategy')) U.indSheet('strategy'); else { $('#bottomPanel').classList.remove('hidden'); P.strategyPanel(); } } }[h] || (() => {}))();
    });
  };
  P.mobilePanel = function (tab) { if (U.mobile()) { $('#side').classList.remove('closed'); P.show(tab); $$('#bottomNav button').forEach(b => b.classList.remove('active')); } else P.show(tab); };

  /* ---------- Bố cục (lưu nhiều cấu hình biểu đồ) ---------- */
  const curLayout = () => ({ src: App.state.src, sym: App.state.sym, tf: App.state.tf, type: App.chart.type, inds: App.chart.inds, at: Date.now() });
  P.saveLayout = function () {
    const name = App.store.get('layoutName', '');
    U.prompt('Tên bố cục', name || 'Bố cục ' + (Object.keys(App.store.get('layouts', {})).length + 1), v => {
      if (!v) return; const all = App.store.get('layouts', {}); all[v] = curLayout(); App.store.set('layouts', all); App.store.set('layoutName', v); App.toast('Đã lưu bố cục "' + v + '"', 'ok');
    });
  };
  P.newLayout = () => U.confirm('Tạo bố cục mới (bỏ hết chỉ báo, giữ mã đang xem)?', () => { App.chart.inds = [{ uid: Date.now(), id: 'volume', I: {}, st: {} }]; App.chart.saveInds(); App.chart.setType('candle'); App.store.set('layoutName', ''); });
  P.layouts = function () {
    const all = App.store.get('layouts', {});
    const s = U.sheet({ id: 'lay', title: 'Bố cục đã lưu', cls: 'small', body: `<div class="ilist">${Object.entries(all).sort((a, b) => b[1].at - a[1].at).map(([n, l]) => `<div class="irow" data-ln="${esc(n)}">${ic('layout')}<span class="nm">${esc(n)}<small>${esc(l.sym)} · ${App.TF_LABEL[l.tf]} · ${l.inds.length} chỉ báo</small></span><button class="mini" data-del="${esc(n)}">${ic('trash')}</button></div>`).join('') || '<div class="empty">Chưa có bố cục nào</div>'}</div>`,
      foot: '<button class="btn pri" data-sv>Lưu bố cục hiện tại</button>' });
    s.addEventListener('click', e => {
      const d = e.target.closest('[data-del]'); if (d) { delete all[d.dataset.del]; App.store.set('layouts', all); U.close('lay'); return P.layouts(); }
      const r = e.target.closest('[data-ln]'); if (r) { const l = all[r.dataset.ln]; App.chart.inds = l.inds; App.chart.saveInds(); App.chart.type = l.type; App.store.set('layoutName', r.dataset.ln); U.close('lay'); App.chart.setType(l.type, true); App.loadSymbol(l.src, l.sym, l.tf); }
    });
    s.querySelector('[data-sv]').onclick = () => { U.close('lay'); P.saveLayout(); };
  };

  /* ---------- Mẫu chỉ báo ---------- */
  const BUILTIN_TPL = {
    'Xu hướng cơ bản': ['ema', 'ma', 'volume', 'macd'], 'Dao động': ['rsi', 'stoch', 'volume'], 'Bollinger + RSI': ['bb', 'rsi', 'volume'],
    'Ichimoku': ['ichimoku', 'volume'], 'Khối lượng': ['volume', 'obv', 'vpvr', 'vwap'], 'Bill Williams': ['alligator', 'fractals', 'ao'], 'Supertrend + ADX': ['supertrend', 'adx', 'volume']
  };
  P.templates = function () {
    const mine = App.store.get('tpls', {});
    const s = U.sheet({ id: 'tpl', title: 'Mẫu chỉ báo', cls: 'small', body: `<div class="isec">Của tôi</div><div class="ilist">${Object.keys(mine).map(n => `<div class="irow" data-tm="${esc(n)}">${ic('grid')}<span class="nm">${esc(n)}<small>${mine[n].map(x => (App.INDICATORS[x.id] || {}).name).join(', ')}</small></span><button class="mini" data-del="${esc(n)}">${ic('trash')}</button></div>`).join('') || '<div class="empty">Chưa có — lưu bộ chỉ báo đang dùng thành mẫu</div>'}</div>
      <div class="isec">Mẫu có sẵn</div><div class="ilist">${Object.entries(BUILTIN_TPL).map(([n, ids]) => `<div class="irow" data-tb="${esc(n)}">${ic('grid')}<span class="nm">${esc(n)}<small>${ids.map(i => App.INDICATORS[i].name).join(', ')}</small></span></div>`).join('')}</div>`,
      foot: '<button class="btn pri" data-sv>Lưu bộ chỉ báo hiện tại thành mẫu</button>' });
    const apply = list => { App.chart.inds = list.map((x, k) => ({ uid: Date.now() + k, id: x.id || x, I: x.I || {}, st: x.st || {} })); App.chart.saveInds(); App.chart.renderIndicators(); U.close('tpl'); App.toast('Đã áp dụng mẫu', 'ok'); };
    s.addEventListener('click', e => {
      const d = e.target.closest('[data-del]'); if (d) { e.stopPropagation(); delete mine[d.dataset.del]; App.store.set('tpls', mine); U.close('tpl'); return P.templates(); }
      const m = e.target.closest('[data-tm]'); if (m) return apply(mine[m.dataset.tm]);
      const b = e.target.closest('[data-tb]'); if (b) return apply(BUILTIN_TPL[b.dataset.tb]);
    });
    s.querySelector('[data-sv]').onclick = () => U.prompt('Tên mẫu', '', v => { if (!v) return; mine[v] = App.chart.inds.map(x => ({ id: x.id, I: x.I, st: x.st })); App.store.set('tpls', mine); U.close('tpl'); App.toast('Đã lưu mẫu', 'ok'); });
  };

  /* =========================================================
   * PHÁT LẠI THANH (bar replay)
   * ========================================================= */
  let rpTimer = null;
  P.replayStart = function () {
    const C = App.chart;
    if (C.replay) return P.replayStop();
    C.replay = { picking: true, speed: 1 };
    App.toast('Bấm vào một nến trên biểu đồ để chọn điểm bắt đầu phát lại', 'info', 6000);
    P.replayBar();
  };
  U.replayPick = function (time) {
    const C = App.chart, b = App.state.bars, n = b.length;
    let k = 0; while (k < n - 1 && b[k + 1].time <= time) k++;
    const idx = Math.max(10, Math.min(n - 2, k));
    C.replay = { idx, speed: C.replay.speed || 1, playing: false };
    C.refresh(true); P.replayBar();
  };
  P.replayStep = function (k = 1) {
    const C = App.chart; if (!C.replay || C.replay.idx == null) return;
    if (C.replay.idx >= App.state.bars.length - 1) { P.replayPause(); return App.toast('Đã phát tới nến mới nhất'); }
    C.replay.idx += k;
    const bar = App.state.bars[C.replay.idx];
    if (['candle', 'bar', 'hollow', 'line', 'linemk', 'step', 'area', 'columns'].includes(C.type)) { C.view.push(bar); C.D = App.ta.prep(C.view); C.main.update(C.toMain(bar)); C.renderIndicators(true); U.legend(null); }
    else C.refresh(true);
    P.replayInfo();
  };
  P.replayPlay = function () { const C = App.chart; if (!C.replay || C.replay.idx == null) return; C.replay.playing = true; clearInterval(rpTimer); rpTimer = setInterval(() => P.replayStep(1), 1000 / C.replay.speed); P.replayBar(); };
  P.replayPause = function () { const C = App.chart; if (C.replay) C.replay.playing = false; clearInterval(rpTimer); P.replayBar(); };
  P.replayStop = function () { clearInterval(rpTimer); App.chart.replay = null; $('#replayBar').classList.add('hidden'); $('#btnReplay').classList.remove('on'); App.chart.refresh(true); };
  P.replayInfo = () => { const C = App.chart, el = $('#rpInfo'); if (el && C.replay && C.replay.idx != null) el.textContent = `${App.fmtTime(App.state.bars[C.replay.idx].time)} · còn ${App.state.bars.length - 1 - C.replay.idx} nến`; };
  P.replayBar = function () {
    const C = App.chart, r = C.replay, bar = $('#replayBar');
    $('#btnReplay').classList.toggle('on', !!r);
    if (!r) return bar.classList.add('hidden');
    bar.classList.remove('hidden');
    bar.innerHTML = r.idx == null ? `<span class="rp-info">${ic('target')} Chọn điểm bắt đầu trên biểu đồ</span><button data-r="stop" title="Thoát">${ic('x')}</button>`
      : `<button data-r="pick" title="Chọn lại điểm bắt đầu">${ic('target')}</button><button data-r="${r.playing ? 'pause' : 'play'}" title="${r.playing ? 'Tạm dừng' : 'Phát'}">${ic(r.playing ? 'pause' : 'play')}</button>
        <button data-r="step" title="Tiến 1 nến">${ic('step')}</button><select data-r="speed" title="Tốc độ">${[0.5, 1, 2, 3, 5, 10].map(x => `<option value="${x}" ${x === r.speed ? 'selected' : ''}>${x}×</option>`).join('')}</select>
        <span class="rp-info" id="rpInfo"></span><button data-r="stop" title="Thoát phát lại">${ic('stop')} Thoát</button>`;
    P.replayInfo();
    bar.onclick = e => { const b = e.target.closest('button[data-r]'); if (!b) return; ({ play: P.replayPlay, pause: P.replayPause, step: () => P.replayStep(1), stop: P.replayStop, pick: () => { P.replayPause(); C.replay = { picking: true, speed: r.speed }; C.refresh(true); P.replayBar(); } })[b.dataset.r](); };
    bar.onchange = e => { if (e.target.dataset.r === 'speed') { r.speed = +e.target.value; if (r.playing) P.replayPlay(); } };
  };

  /* =========================================================
   * KIỂM TRA CHIẾN LƯỢC (bảng dưới)
   * ========================================================= */
  let bpTab = 'sum';
  P.strategyPanel = U.strategyPanel = function () {
    const C = App.chart, list = C.inds.filter(x => App.INDICATORS[x.id] && App.INDICATORS[x.id].cat === 'strategy' && !x.hidden);
    const panel = $('#bottomPanel');
    if (!list.length) { panel.classList.add('hidden'); return; }
    if (panel.classList.contains('hidden') && panel.dataset.closed === '1') return;
    panel.classList.remove('hidden');
    let cur = list.find(x => x.uid === +panel.dataset.uid) || list[0]; panel.dataset.uid = cur.uid;
    const r = (C.results[cur.uid] || {}).backtest;
    const f2 = v => (v >= 0 ? '+' : '') + v.toLocaleString('vi-VN', { maximumFractionDigits: 2 });
    let body = '<div class="empty">Không có giao dịch</div>';
    if (r) {
      if (bpTab === 'sum') body = `<div class="kpis">
        <div class="kpi"><small>Lãi ròng</small><b class="${r.net >= 0 ? 'up' : 'down'}">${f2(r.net)} (${App.fmtPct(r.netPct)})</b></div>
        <div class="kpi"><small>Tổng số lệnh</small><b>${r.n}</b></div><div class="kpi"><small>Tỉ lệ thắng</small><b>${r.winRate.toFixed(1)}%</b></div>
        <div class="kpi"><small>Hệ số lợi nhuận</small><b>${isFinite(r.pf) ? r.pf.toFixed(2) : '∞'}</b></div><div class="kpi"><small>Sụt giảm tối đa</small><b class="down">${r.mdd.toFixed(2)}%</b></div>
        <div class="kpi"><small>TB mỗi lệnh</small><b>${f2(r.avg)}</b></div><div class="kpi"><small>Mua &amp; giữ</small><b class="${r.buyHold >= 0 ? 'up' : 'down'}">${App.fmtPct(r.buyHold)}</b></div></div>
        <canvas id="eqCv" style="width:100%;height:90px;margin-top:10px"></canvas><p class="note">${r.note ? esc(r.note) + ' ' : ''}Vốn ban đầu ${((App.settings.bt || {}).capital || 10000).toLocaleString('vi-VN')}, toàn bộ vốn mỗi lệnh, khớp giá mở cửa nến kế tiếp, phí ${(App.settings.bt || {}).fee ?? 0.04}%/chiều. Đổi trong ⚙ của chiến lược.</p>`;
      else body = `<table class="tt"><tr><th>#</th><th>Loại</th><th>Vào</th><th>Giá vào</th><th>Ra</th><th>Giá ra</th><th>Lãi/lỗ</th><th>%</th></tr>${r.trades.slice().reverse().map((t, k) => `<tr><td>${r.trades.length - k}</td><td class="${t.side === 'Mua' ? 'up' : 'down'}">${t.side}</td><td>${App.fmtTime(C.D.t[t.ei])}</td><td>${App.fmtPrice(t.ep)}</td><td>${App.fmtTime(C.D.t[t.xi])}${t.why === 'Đang mở' ? ' (mở)' : ''}</td><td>${App.fmtPrice(t.xp)}</td><td class="${t.pnl >= 0 ? 'up' : 'down'}">${f2(t.pnl)}</td><td class="${t.pct >= 0 ? 'up' : 'down'}">${App.fmtPct(t.pct)}</td></tr>`).join('')}</table>`;
    }
    panel.innerHTML = `<div class="bp-head">${ic('target')}<b>Kiểm tra chiến lược</b><select id="bpSel">${list.map(x => `<option value="${x.uid}" ${x.uid === cur.uid ? 'selected' : ''}>${esc(App.INDICATORS[x.id].name)}</option>`).join('')}</select>
      <span class="bp-tabs"><button data-bt="sum" class="${bpTab === 'sum' ? 'active' : ''}">Tổng quan</button><button data-bt="list" class="${bpTab === 'list' ? 'active' : ''}">Danh sách lệnh</button></span><span class="grow"></span>
      <button class="mini" data-bt="set" title="Cài đặt">${ic('gear')}</button><button class="mini" data-bt="close" title="Ẩn bảng">${ic('down')}</button></div><div class="bp-body">${body}</div>`;
    panel.onchange = e => { if (e.target.id === 'bpSel') { panel.dataset.uid = e.target.value; P.strategyPanel(); } };
    panel.onclick = e => { const b = e.target.closest('[data-bt]'); if (!b) return; if (b.dataset.bt === 'close') { panel.classList.add('hidden'); panel.dataset.closed = '1'; return; } if (b.dataset.bt === 'set') return U.indSettings(cur); bpTab = b.dataset.bt; P.strategyPanel(); };
    const cv = $('#eqCv'); if (cv && r) { const w = cv.clientWidth, h = 90, dpr = window.devicePixelRatio || 1; cv.width = w * dpr; cv.height = h * dpr; const g = cv.getContext('2d'); g.scale(dpr, dpr);
      const eq = r.equity, mn = Math.min(...eq), mx = Math.max(...eq), y = v => h - 4 - (v - mn) / (mx - mn || 1) * (h - 8);
      g.beginPath(); eq.forEach((v, i) => { const x = i / (eq.length - 1) * w; i ? g.lineTo(x, y(v)) : g.moveTo(x, y(v)); }); g.strokeStyle = App.theme.accent; g.lineWidth = 1.5; g.stroke();
      g.lineTo(w, h); g.lineTo(0, h); g.closePath(); g.fillStyle = App.theme.accentSoft; g.fill(); }
  };

  /* ---------- Chụp ảnh biểu đồ ---------- */
  P.screenshot = function () {
    let framed = true; try { framed = window.self !== window.top; } catch (e) {}
    if (framed) return App.toast('Chụp ảnh chỉ dùng được ở bản file HTML mở trên máy tính', 'err');
    try {
      const c = App.chart.api.takeScreenshot(), g = c.getContext('2d'), d = App.draw.cv, k = c.width / $('#chart').clientWidth / (window.devicePixelRatio || 1);
      g.drawImage(d, 0, 0, d.width * k, d.height * k);
      g.font = `600 ${14 * (c.width / $('#chart').clientWidth)}px sans-serif`; g.fillStyle = App.theme.accent; g.fillText('GreenView · ' + App.state.sym + ' · ' + App.TF_LABEL[App.state.tf], 12, c.height - 14);
      const a = document.createElement('a'); a.download = `GreenView_${App.state.sym.replace(/\W/g, '_')}_${App.state.tf}.png`; a.href = c.toDataURL('image/png');
      document.body.appendChild(a); a.click(); a.remove(); App.toast('Đã lưu ảnh', 'ok');
    } catch (e) { App.toast('Không chụp được ảnh ở chế độ này', 'err'); }
  };
})(window.App);
