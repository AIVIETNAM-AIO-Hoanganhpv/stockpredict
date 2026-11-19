/* =========================================================
 * app.js — Khởi động GreenView: trạng thái, tải mã, realtime, phím tắt
 * ========================================================= */
(function (App) {
  'use strict';
  const $ = App.$;

  App.state = { src: 'BINANCE', sym: 'BTCUSDT', tf: '1h', bars: [], loading: false, noMore: false, token: 0 };
  App.settings = Object.assign({ tdKey: '', proxy: '', chart: {}, bt: { capital: 10000, fee: 0.04 } }, App.store.get('settings', {}));
  App.saveSettings = () => App.store.set('settings', App.settings);
  // Key Twelve Data do StockPredict đưa vào (file khoa_twelvedata.txt trên máy) – chỉ điền khi chưa có
  if (window.GV_TD_KEY && !App.settings.tdKey) { App.settings.tdKey = window.GV_TD_KEY; App.saveSettings(); }

  App.setStatus = function (kind, text) { $('#stDot').className = 'dot ' + kind; $('#stText').textContent = text; };
  setInterval(() => { const d = new Date(), p = n => String(n).padStart(2, '0'); $('#clock').textContent = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())} (UTC${App.TZ >= 0 ? '+' : ''}${App.TZ / 3600})`; }, 1000);

  /* ---------- Tải một mã ---------- */
  let stopLive = null;
  App.loadSymbol = async function (src, sym, tf, opts = {}) {
    const source = App.sources[src];
    sym = source.normalize(sym);
    if (!source.tfs.includes(tf)) tf = source.tfs.includes('1D') ? '1D' : source.tfs[0];
    const token = ++App.state.token;
    if (stopLive) { stopLive(); stopLive = null; }
    if (App.chart.replay) App.panels.replayStop();
    $('#loading').classList.remove('hidden');
    App.setStatus('load', 'Đang tải ' + sym + '…');
    try {
      const bars = await source.fetchBars(sym, tf);
      if (token !== App.state.token) return;
      if (!bars.length) throw new Error('Không có dữ liệu');
      const changed = src !== App.state.src || sym !== App.state.sym;
      Object.assign(App.state, { src, sym, tf, bars, noMore: !source.canLoadMore });
      if (changed) App.chart.compares.forEach(c => c.series && App.chart.api.removeSeries(c.series)), App.chart.compares = [];
      App.draw.load();
      App.chart.refresh(false);
      App.ui.renderTop();
      $('#stInfo').textContent = `${bars.length} nến`;
      App.setStatus('idle', 'Đã tải ' + sym);
      stopLive = source.live(sym, tf, bar => { if (token === App.state.token) App.chart.updateBar(bar); });
      if (!opts.fallback) App.store.set('last', { src, sym, tf });
      const r = App.store.get('recent', []).filter(x => !(x.src === src && x.sym === sym)); r.unshift({ src, sym }); App.store.set('recent', r.slice(0, 14));
      App.panels.refreshSide();
      return true;
    } catch (e) {
      if (token !== App.state.token) return;
      const msg = e && e.name === 'AbortError' ? 'Hết thời gian chờ' : (e && e.message) || 'Lỗi không rõ';
      App.setStatus('err', 'Lỗi: ' + msg);
      if (!opts.quiet) App.toast(`Không tải được ${sym}: ${msg}${src === 'VN' || src === 'TCBS' ? ' — trình duyệt bị chặn: mở GreenView bằng co_phieu/chay_greenview.bat rồi chọn nguồn "StockPredict (giá VN)"' : ''}`, 'err', 6500);
      if (App.state.bars.length) { const cur = App.sources[App.state.src], t2 = App.state.token; stopLive = cur.live(App.state.sym, App.state.tf, bar => { if (t2 === App.state.token) App.chart.updateBar(bar); }); }
      return false;
    } finally { if (token === App.state.token) $('#loading').classList.add('hidden'); }
  };

  App.loadMoreHistory = async function () {
    const s = App.state;
    if (s.loading || s.noMore || !s.bars.length) return;
    s.loading = true; const token = s.token;
    try {
      const first = s.bars[0].time, older = (await App.sources[s.src].fetchBars(s.sym, s.tf, first)).filter(b => b.time < first);
      if (token !== s.token) return;
      if (!older.length) { s.noMore = true; return; }
      s.bars = older.concat(s.bars); App.chart.prepended(older.length);
      $('#stInfo').textContent = `${s.bars.length} nến`;
    } catch (e) { s.noMore = true; } finally { s.loading = false; }
  };

  /* ---------- Phím tắt (giống TradingView) ---------- */
  document.addEventListener('keydown', e => {
    if (e.target.matches('input,textarea,select') || document.querySelector('.sheet-bg')) return;
    const k = e.key.toLowerCase();
    if (e.altKey) {
      const map = { t: 'trend', h: 'hline', v: 'vline', c: 'crossline', f: 'fibret', j: 'hray', p: 'parallel' };   // Alt+R: đặt lại khung nhìn (extras.js)
      if (map[k]) { e.preventDefault(); App.draw.setTool(map[k]); }
      if (k === 'a') { e.preventDefault(); App.panels.alertSheet(); }
      if (k === 'i') { e.preventDefault(); App.ui.indSheet(); }
      return;
    }
    if (e.key === '/' ) { e.preventDefault(); App.ui.indSheet(); return; }
    if (/^[a-z0-9]$/i.test(e.key) && !e.ctrlKey && !e.metaKey) { App.ui.symbolSheet('open'); setTimeout(() => { const q = $('#sQ'); if (q) { q.value = e.key.toUpperCase(); } }, 30); }
  });

  /* ---------- Khởi động ---------- */
  async function boot() {
    App.setTheme(App.store.get('theme', 'dark'));
    App.ui.initTop();
    App.chart.init($('#chart'));
    App.draw.init($('#chartWrap'));
    App.ui.initTools();
    App.ui.initLegend();
    App.panels.initSide();
    App.panels.badge();
    if ((App.settings.chart || {}).watermark === false) $('#watermark').classList.add('hidden');
    App.store.get('csvNames', []).forEach(n => { const d = App.store.get('csv:' + n); if (d) App.csvSets[n] = d; });
    window.addEventListener('resize', () => requestAnimationFrame(() => App.ui.legend(App.chart.hover)));

    // Connector của Claude (chỉ có khi mở trong Claude) — chờ tối đa ~10 giây
    App.mcpReady = (async () => { try { if (window.claude && window.claude.use) App.mcp = await window.claude.use('mcp'); } catch (e) { App.mcp = null; } return App.mcp; })();
    // Mở từ StockPredict: dữ liệu nhúng sẵn (web app) hoặc máy chủ giá trên máy (chay_greenview.bat)
    const spAuto = () => { if (!App.chart.inds.some(x => x.id === 'sp_plan')) App.chart.addIndicator('sp_plan'); };
    if (window.GV_DATA && window.GV_DATA.bars) {
      if (await App.loadSymbol('SP', window.GV_DATA.ma, '1D', { quiet: true, fallback: true })) { spAuto(); App.panels.refreshQuotes(); return; }
    }
    const last = App.store.get('last', window.GV_API != null ? { src: 'SP', sym: 'VNINDEX', tf: '1D' } : { src: 'BINANCE', sym: 'BTCUSDT', tf: '1h' });
    if (window.GV_API != null && (last.src === 'VN' || last.src === 'TCBS')) { last.src = 'SP'; if (!['1D', '1W', '1M'].includes(last.tf)) last.tf = '1D'; }
    if (window.GV_API != null && last.src === 'SP') spAuto();
    if (last.src === 'SP' && window.GV_API == null) { last.src = 'BINANCE'; last.sym = 'BTCUSDT'; last.tf = '1h'; }
    if (last.src === 'TCBS') await App.mcpReady;
    let ok = await App.loadSymbol(last.src, last.sym, last.tf, { quiet: true });
    if (!ok && last.src !== 'BINANCE') ok = await App.loadSymbol('BINANCE', 'BTCUSDT', '1h', { quiet: true });
    if (!ok) {
      await App.mcpReady;
      if (App.mcp) ok = await App.loadSymbol('TCBS', last.src === 'TCBS' || last.src === 'VN' ? last.sym : 'VNINDEX', '1D', { quiet: true });
      const b = $('#banner');
      b.innerHTML = ok ? `${App.icon('info')}<span>Đang dùng <b>connector TCBS</b> cho cổ phiếu Việt Nam. Khung nhỏ (1p–4g) được tự ghép từ giá TCBS trong giờ giao dịch, khi trang đang mở. Crypto, Mỹ, Forex cần mở file HTML trên máy tính.</span><button class="x">${App.icon('x')}</button>`
        : `${App.icon('info')}<span>Không kết nối được API dữ liệu nên đang chạy <b>dữ liệu giả lập</b>. Trong Claude: kết nối TCBS (Cài đặt › Connectors) để xem cổ phiếu VN, hoặc tải file HTML về máy để có đủ nguồn.</span><button class="x">${App.icon('x')}</button>`;
      b.classList.remove('hidden'); b.querySelector('.x').onclick = () => b.classList.add('hidden');
      if (!ok) await App.loadSymbol('DEMO', 'DEMO', last.tf || '1h', { fallback: true });
    }
    // Khi connector TCBS sẵn sàng mà đang xem dữ liệu giả lập -> tự chuyển sang giá thật
    App.mcpReady.then(async m => {
      if (!m) return;
      App.panels.refreshQuotes(['VN', 'TCBS']);
      if (App.state.src === 'DEMO' || !App.state.bars.length) {
        const ok2 = await App.loadSymbol('TCBS', 'VNINDEX', '1D', { quiet: true });
        const b = $('#banner');
        b.innerHTML = ok2 ? `${App.icon('info')}<span>Đang dùng <b>connector TCBS</b> cho cổ phiếu Việt Nam. Khung nhỏ (1p–4g) được tự ghép từ giá TCBS trong giờ giao dịch, khi trang đang mở. Crypto, Mỹ, Forex cần mở file HTML trên máy tính.</span><button class="x">${App.icon('x')}</button>`
          : `${App.icon('info')}<span>Đã thấy connector TCBS nhưng chưa lấy được dữ liệu: <b>${App.esc($('#stText').textContent)}</b>. Hãy cho phép GreenView dùng TCBS khi Claude hỏi, rồi tải lại trang.</span><button class="x">${App.icon('x')}</button>`;
        b.classList.remove('hidden'); b.querySelector('.x').onclick = () => b.classList.add('hidden');
      }
    });
    App.panels.refreshQuotes();
  }
  boot();
})(window.App);
