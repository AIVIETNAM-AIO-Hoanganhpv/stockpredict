/* =========================================================
 * extras.js — giống TradingView:
 *   • Đếm ngược thời gian còn lại của nến hiện tại, hiện ngay dưới nhãn giá trên trục giá
 *   • Menu chuột phải trên biểu đồ: đặt lại khung nhìn (Alt+R), sao chép giá, cảnh báo tại giá,
 *     vẽ vị thế Mua/Bán tại giá, đường dọc tại thời điểm, xem dạng bảng, cây đối tượng, mẫu,
 *     xoá chỉ báo, cài đặt
 * ========================================================= */
(function (App) {
  'use strict';
  const $ = App.$, esc = App.esc, ic = App.icon;
  const C = () => App.chart;

  /* ---------------- Đặt lại khung nhìn ---------------- */
  App.resetView = function () {
    const c = C(); if (!c || !c.api) return;
    try { c.api.priceScale('right').applyOptions({ autoScale: true }); } catch (e) {}
    try { c.main && c.main.priceScale().applyOptions({ autoScale: true }); } catch (e) {}
    try { c.api.timeScale().resetTimeScale(); } catch (e) {}
    try { const n = App.state.bars.length; if (n) c.api.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - 150), to: n + 8 }); } catch (e) {}
    App.toast('Đã đặt lại khung nhìn', 'ok', 1500);
  };

  /* ---------------- Đếm ngược thời gian nến ---------------- */
  const cd = document.createElement('div');
  cd.id = 'cdLabel';
  cd.style.cssText = 'position:fixed;z-index:6;pointer-events:none;font:600 11px/15px -apple-system,Segoe UI,Roboto,sans-serif;' +
    'color:#fff;text-align:center;border-radius:0 0 3px 3px;display:none;font-variant-numeric:tabular-nums';
  document.body.appendChild(cd);

  App.conLaiNen = function () {
    const s = App.state, n = s.bars.length; if (!n) return null;
    const last = s.bars[n - 1].time, now = Date.now() / 1000 + App.TZ;
    let end;
    // Cổ phiếu VN khung ngày: phiên đóng cửa lúc 14:45
    if (s.tf === '1D' && ['SP', 'VN', 'TCBS'].includes(s.src)) return last + 14.75 * 3600 - now;
    if (s.tf === '1M') { const d = new Date(last * 1000); end = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) / 1000; }
    else end = last + (App.TF[s.tf] || 86400);
    return end - now;
  };
  App.fmtConLai = function (r) {
    if (r == null || r <= 0) return '';
    const p = v => String(Math.floor(v)).padStart(2, '0');
    if (r >= 86400) { const d = Math.floor(r / 86400); return `${d} ngày ${p((r % 86400) / 3600)}g`; }
    return r >= 3600 ? `${p(r / 3600)}:${p((r % 3600) / 60)}:${p(r % 60)}` : `${p(r / 60)}:${p(r % 60)}`;
  };
  function veDemNguoc() {
    const c = C(), s = App.state, n = s.bars.length;
    const tat = (App.settings.chart || {}).countdown === false;
    if (tat || !c || !c.main || !n || App.chart.replay) { cd.style.display = 'none'; return; }
    const r = App.conLaiNen(), txt = App.fmtConLai(r);
    const b = s.bars[n - 1], y = c.main.priceToCoordinate(b.close);
    const box = $('#chart').getBoundingClientRect();
    let w = 0; try { w = c.api.priceScale('right').width(); } catch (e) {}
    if (!txt || y == null || !w || y < 0 || y > box.height - 30) { cd.style.display = 'none'; return; }
    cd.textContent = txt;
    cd.style.background = b.close >= b.open ? (App.theme.up || '#089981') : (App.theme.down || '#f23645');
    cd.style.left = (box.right - w) + 'px'; cd.style.width = w + 'px';
    cd.style.top = (box.top + y + 9) + 'px';
    cd.style.display = 'block';
  }
  setInterval(veDemNguoc, 1000);
  const hook = setInterval(() => {
    const c = C(); if (!c || !c.api) return;
    clearInterval(hook);
    c.api.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(veDemNguoc));
    window.addEventListener('resize', () => requestAnimationFrame(veDemNguoc));
    document.addEventListener('pointermove', e => { if (e.buttons) requestAnimationFrame(veDemNguoc); });
    document.addEventListener('wheel', () => requestAnimationFrame(veDemNguoc), { passive: true });
  }, 200);

  /* ---------------- Menu chuột phải ---------------- */
  function themHinh(tool, t, p) {
    const DR = App.draw, def = DR.TOOLS[tool]; if (!def) return;
    const d = { id: 'd' + Date.now() + Math.floor(Math.random() * 999), tool, pts: [{ t, p }], style: Object.assign({}, DR.style, def.style || {}), _hit: [] };
    if (def.init) def.init(d, DR);
    DR.list.push(d); DR.save(); DR.select && DR.select(d); DR.render && DR.render();
  }

  function bangGia() {
    const s = App.state, rows = s.bars.slice(-300).reverse();
    App.ui.sheet({ id: 'tbl', title: `Dạng bảng · ${esc(s.sym)} · ${App.TF_LABEL[s.tf] || s.tf}`, cls: 'wide',
      body: `<div style="max-height:65vh;overflow:auto"><table class="tt"><tr><th>Thời gian</th><th>Mở</th><th>Cao</th><th>Thấp</th><th>Đóng</th><th>%</th><th>KL</th></tr>${
        rows.map((b, k) => { const pr = rows[k + 1], ch = pr ? (b.close / pr.close - 1) * 100 : 0;
          return `<tr><td>${App.fmtTime(b.time)}</td><td>${App.fmtPrice(b.open)}</td><td>${App.fmtPrice(b.high)}</td><td>${App.fmtPrice(b.low)}</td><td>${App.fmtPrice(b.close)}</td><td class="${ch >= 0 ? 'up' : 'down'}">${App.fmtPct(ch)}</td><td>${(b.volume || 0).toLocaleString('vi-VN')}</td></tr>`; }).join('')}</table></div>` });
  }

  function moMenu(ev) {
    const c = C(); if (!c || !c.main || !App.state.bars.length) return;
    ev.preventDefault();
    const box = $('#chart').getBoundingClientRect(), y = ev.clientY - box.top, x = ev.clientX - box.left;
    let gia = c.main.coordinateToPrice(y);
    if (gia == null || !isFinite(gia)) gia = App.state.bars[App.state.bars.length - 1].close;
    let t = c.api.timeScale().coordinateToTime(x);
    if (t == null) t = App.state.bars[App.state.bars.length - 1].time;
    const g = App.fmtPrice(gia), sym = esc(App.state.sym), soInd = c.inds.length;
    const demNguoc = (App.settings.chart || {}).countdown !== false;
    const row = (a, icon, text, kb) => `<div class="fo-row" data-a="${a}">${icon ? ic(icon) : '<span style="width:26px"></span>'}<span class="nm">${text}</span>${kb ? `<small style="color:var(--muted)">${kb}</small>` : ''}</div>`;
    const hr = '<div style="border-top:1px solid var(--line);margin:4px 0"></div>';
    const f = $('#flyout');
    f.innerHTML = row('reset', 'refresh', 'Đặt lại khung nhìn biểu đồ', 'Alt + R') + hr
      + row('copy', null, `Sao chép giá ${g}`) + hr
      + row('alert', 'bell', `Thêm cảnh báo ${sym} tại ${g}…`, 'Alt + A')
      + row('long', null, `Vẽ vị thế MUA ${sym} tại ${g}`)
      + row('short', null, `Vẽ vị thế BÁN ${sym} tại ${g}`)
      + row('hline', null, `Vẽ đường ngang tại ${g}`) + hr
      + row('vline', null, `Khoá đường dọc tại ${App.fmtTime(t)}`)
      + row('cd', null, `${demNguoc ? '✓ ' : ''}Đếm ngược thời gian nến`) + hr
      + row('table', null, 'Xem dạng bảng') + row('tree', null, 'Cây đối tượng') + row('tpl', null, 'Mẫu biểu đồ ›') + hr
      + (soInd ? row('rmind', 'trash', `Xoá ${soInd} chỉ báo`) + hr : '')
      + row('set', 'gear', 'Cài đặt…');
    f.style.left = Math.min(ev.clientX, window.innerWidth - 300) + 'px';
    f.classList.remove('hidden');
    f.style.top = Math.max(6, Math.min(ev.clientY, window.innerHeight - f.offsetHeight - 6)) + 'px';
    f.onclick = e => {
      const b = e.target.closest('[data-a]'); if (!b) return;
      f.classList.add('hidden');
      ({
        reset: App.resetView,
        copy: () => { const v = String(+gia.toPrecision(8)); (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => App.toast('Đã chép ' + v, 'ok', 1500), () => App.toast(v, 'info')); },
        alert: () => App.panels.alertSheet(+gia.toPrecision(6)),
        long: () => themHinh('long', t, gia), short: () => themHinh('short', t, gia),
        hline: () => themHinh('hline', t, gia), vline: () => themHinh('vline', t, gia),
        cd: () => { App.settings.chart = Object.assign({}, App.settings.chart, { countdown: !demNguoc }); App.saveSettings(); veDemNguoc(); },
        table: bangGia, tree: () => App.panels.mobilePanel('ot'), tpl: App.panels.templates,
        rmind: () => App.ui.confirm(`Xoá ${soInd} chỉ báo?`, () => { c.inds = []; c.saveInds(); c.renderIndicators(); }),
        set: App.ui.chartSettings
      })[b.dataset.a]();
    };
    setTimeout(() => document.addEventListener('pointerdown', function h(e2) { if (!f.contains(e2.target)) { f.classList.add('hidden'); document.removeEventListener('pointerdown', h); } }), 0);
  }
  const gan = setInterval(() => { const w = $('#chartWrap'); if (!w) return; clearInterval(gan); w.addEventListener('contextmenu', moMenu); }, 200);

  // Phím tắt Alt+R: đặt lại khung nhìn
  document.addEventListener('keydown', e => {
    if (e.altKey && e.key.toLowerCase() === 'r' && !e.target.matches('input,textarea,select')) { e.preventDefault(); App.resetView(); }
  });
})(window.App);
