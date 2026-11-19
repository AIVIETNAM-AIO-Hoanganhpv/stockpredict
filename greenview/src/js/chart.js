/* =========================================================
 * chart.js — Bộ điều khiển biểu đồ GreenView
 *  - 17 loại biểu đồ (nến, Heikin Ashi, Renko, Kagi, P&F…)
 *  - Chỉ báo dạng "phiên bản" (thêm nhiều lần, mỗi cái tham số riêng)
 *  - So sánh mã, phát lại thanh (bar replay), thang giá log/%
 * ========================================================= */
(function (App) {
  'use strict';
  const LC = window.LightweightCharts, T = App.ta, isN = T.isN;

  App.CHART_TYPES = [
    ['bar', 'Thanh'], ['candle', 'Nến'], ['hollow', 'Nến rỗng'], ['line', 'Đường'], ['linemk', 'Đường có điểm'], ['step', 'Đường bậc thang'],
    ['area', 'Vùng'], ['hlcarea', 'Vùng HLC'], ['baseline', 'Đường cơ sở'], ['columns', 'Cột'], ['highlow', 'Cao-Thấp'],
    ['ha', 'Heikin Ashi'], ['renko', 'Renko'], ['linebreak', 'Line break'], ['kagi', 'Kagi'], ['pnf', 'Point & figure']
  ];
  const SYNTH = { renko: 1, linebreak: 1, kagi: 1, pnf: 1 };

  const C = App.chart = {
    api: null, main: null, extra: [], type: App.store.get('chartType', 'candle'),
    inds: App.store.get('inds', null) || [{ uid: 1, id: 'volume', I: {}, st: {} }],
    series: {},    // uid -> [series]
    results: {},   // uid -> kết quả tính
    compares: [],
    replay: null,
    view: [],

    init(el) {
      C.el = el;
      C.api = LC.createChart(el, { autoSize: true, crosshair: { mode: LC.CrosshairMode.Normal }, localization: { locale: 'vi-VN', priceFormatter: p => App.fmtPrice(p) },
        timeScale: { timeVisible: true, secondsVisible: false, rightOffset: 10 }, rightPriceScale: { scaleMargins: { top: 0.08, bottom: 0.08 } },
        layout: { panes: { enableResize: true } } });
      C.applyTheme();
      C.api.subscribeCrosshairMove(p => { C.hover = p && p.time != null ? p : null; App.ui.legend(C.hover); });
      C.api.timeScale().subscribeVisibleLogicalRangeChange(r => { if (r && r.from < 5 && !C.replay) App.loadMoreHistory && App.loadMoreHistory(); });
      C.api.subscribeClick(p => { if (C.replay && C.replay.picking && p && p.time != null) App.ui.replayPick(p.time); });
      C.setType(C.type, true);
    },

    applyTheme() {
      const th = App.theme, cs = App.settings.chart || {};
      C.api.applyOptions({
        layout: { background: { type: 'solid', color: th.chartBg }, textColor: th.muted, fontFamily: '-apple-system, "Segoe UI", Roboto, sans-serif', panes: { separatorColor: th.line, separatorHoverColor: th.accentSoft } },
        grid: { vertLines: { color: th.grid, visible: cs.grid !== false }, horzLines: { color: th.grid, visible: cs.grid !== false } },
        rightPriceScale: { borderColor: th.line, mode: cs.scale || 0 }, timeScale: { borderColor: th.line },
        crosshair: { mode: cs.magnetCross ? LC.CrosshairMode.Magnet : LC.CrosshairMode.Normal, vertLine: { color: th.muted, labelBackgroundColor: th.accentDark }, horzLine: { color: th.muted, labelBackgroundColor: th.accentDark } }
      });
      if (C.main) C.styleMain();
    },
    colors() { const cs = App.settings.chart || {}; return { up: cs.up || App.theme.up, dn: cs.dn || App.theme.down }; },

    /* ---------- Loại biểu đồ ---------- */
    setType(type, silent) {
      const prev = C.type;
      C.type = type; App.store.set('chartType', type);
      if (C.main) { try { C.markersApi && C.markersApi.detach && C.markersApi.detach(); } catch (e) {} C.markersApi = null; C.api.removeSeries(C.main); }
      C.extra.forEach(s => C.api.removeSeries(s)); C.extra = [];
      const S = { line: LC.LineSeries, linemk: LC.LineSeries, step: LC.LineSeries, kagi: LC.LineSeries, area: LC.AreaSeries, hlcarea: LC.AreaSeries, baseline: LC.BaselineSeries, columns: LC.HistogramSeries, bar: LC.BarSeries }[type] || LC.CandlestickSeries;
      C.main = C.api.addSeries(S, {}, 0);
      if (type === 'hlcarea') C.extra = [C.api.addSeries(LC.LineSeries, { lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }, 0), C.api.addSeries(LC.LineSeries, { lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }, 0)];
      C.styleMain();
      if (!silent) C.refresh(!(SYNTH[type] || SYNTH[prev]) || type === prev);
    },
    styleMain() {
      const { up, dn } = C.colors(), t = C.type, acc = App.theme.accent, o = { priceLineVisible: true, lastValueVisible: true };
      if (t === 'line' || t === 'linemk' || t === 'step' || t === 'kagi') Object.assign(o, { color: acc, lineWidth: 2, lineType: t === 'step' || t === 'kagi' ? 1 : 0, pointMarkersVisible: t === 'linemk' });
      else if (t === 'area' || t === 'hlcarea') Object.assign(o, { lineColor: acc, topColor: App.theme.accentSoft, bottomColor: 'rgba(0,0,0,0)', lineWidth: 2 });
      else if (t === 'baseline') Object.assign(o, { topLineColor: up, bottomLineColor: dn, topFillColor1: up + '55', topFillColor2: up + '08', bottomFillColor1: dn + '08', bottomFillColor2: dn + '55' });
      else if (t === 'columns') Object.assign(o, { color: acc });
      else if (t === 'bar') Object.assign(o, { upColor: up, downColor: dn, thinBars: false });
      else if (t === 'hollow') Object.assign(o, { upColor: 'rgba(0,0,0,0)', downColor: dn, borderUpColor: up, borderDownColor: dn, wickUpColor: up, wickDownColor: dn, borderVisible: true });
      else if (t === 'highlow') Object.assign(o, { upColor: acc, downColor: acc, borderVisible: false, wickVisible: false });
      else Object.assign(o, { upColor: up, downColor: dn, borderUpColor: up, borderDownColor: dn, wickUpColor: up, wickDownColor: dn, borderVisible: false });
      C.main.applyOptions(o);
      C.extra.forEach((s, k) => s.applyOptions({ color: k ? dn : up }));
    },

    /* ---------- Dữ liệu hiển thị (sau phát lại & biến đổi) ---------- */
    viewBars() { return C.view; },
    buildView() {
      let b = App.state.bars;
      if (C.replay && C.replay.idx != null) b = b.slice(0, C.replay.idx + 1);
      C.view = C.transform(b, C.type);
      C.D = T.prep(C.view);
      return C.view;
    },
    transform(b, type) {
      if (!b.length) return b;
      if (type === 'ha') {
        const out = []; let po = b[0].open, pc = b[0].close;
        b.forEach(x => { const c = (x.open + x.high + x.low + x.close) / 4, o = (po + pc) / 2; out.push({ time: x.time, open: o, high: Math.max(x.high, o, c), low: Math.min(x.low, o, c), close: c, volume: x.volume }); po = o; pc = c; });
        return out;
      }
      if (type === 'highlow') return b.map(x => ({ ...x, open: x.low, close: x.high }));
      if (!SYNTH[type]) return b;
      const D = T.prep(b), atr = T.atr(D, 14)[D.n - 1] || b[b.length - 1].close * 0.01, box = (App.settings.chart && App.settings.chart.box) || +(atr.toPrecision(2));
      const out = []; let lastT = -Infinity;
      const push = (t, o, h, l, c, v) => { t = Math.max(t, lastT + 1); lastT = t; out.push({ time: t, open: o, high: h, low: l, close: c, volume: v || 0 }); };
      if (type === 'renko') {
        let base = Math.floor(b[0].close / box) * box, dir = 0;
        b.forEach(x => {
          while (x.close >= base + box * (dir === -1 ? 2 : 1)) { const o = dir === -1 ? base + box : base; push(x.time, o, o + box, o, o + box, x.volume); base = o + box; dir = 1; }
          while (x.close <= base - box * (dir === 1 ? 2 : 1)) { const o = dir === 1 ? base - box : base; push(x.time, o, o, o - box, o - box, x.volume); base = o - box; dir = -1; }
        });
        if (!out.length) push(b[0].time, b[0].open, b[0].high, b[0].low, b[0].close);
        // gán lại "base" để nến sau cùng nối tiếp đúng
        return out;
      }
      if (type === 'linebreak') {
        const L = [{ o: b[0].open, c: b[0].close }]; push(b[0].time, b[0].open, Math.max(b[0].open, b[0].close), Math.min(b[0].open, b[0].close), b[0].close);
        b.slice(1).forEach(x => { const last3 = L.slice(-3), hi = Math.max(...last3.map(l => Math.max(l.o, l.c))), lo = Math.min(...last3.map(l => Math.min(l.o, l.c))), prev = L[L.length - 1];
          if (x.close > hi || x.close < lo) { const o = x.close > hi ? Math.max(prev.o, prev.c) : Math.min(prev.o, prev.c); L.push({ o, c: x.close }); push(x.time, o, Math.max(o, x.close), Math.min(o, x.close), x.close, x.volume); } });
        return out;
      }
      if (type === 'kagi') {
        const rev = box * 2; let dir = 0, ext = b[0].close; push(b[0].time, ext, ext, ext, ext);
        b.forEach(x => { const c = x.close;
          if (dir >= 0 && c > ext) { ext = c; dir = 1; out[out.length - 1].close = c; }
          else if (dir <= 0 && c < ext) { ext = c; dir = -1; out[out.length - 1].close = c; }
          else if ((dir >= 0 && ext - c >= rev) || (dir <= 0 && c - ext >= rev)) { dir = -dir || -1; ext = c; push(x.time, c, c, c, c, x.volume); } });
        return out.map(o => ({ ...o, open: o.close, high: o.close, low: o.close }));
      }
      if (type === 'pnf') {
        const rev = 3; let col = null;
        b.forEach(x => {
          if (!col) { col = { up: x.close >= x.open, top: Math.ceil(x.high / box) * box, bot: Math.floor(x.low / box) * box, t: x.time }; return; }
          if (col.up) { if (x.high >= col.top + box) col.top = Math.floor(x.high / box) * box; else if (x.low <= col.top - box * rev) { push(col.t, col.bot, col.top, col.bot, col.top); col = { up: false, top: col.top - box, bot: Math.ceil(x.low / box) * box, t: x.time }; } }
          else { if (x.low <= col.bot - box) col.bot = Math.ceil(x.low / box) * box; else if (x.high >= col.bot + box * rev) { push(col.t, col.top, col.top, col.bot, col.bot); col = { up: true, bot: col.bot + box, top: Math.floor(x.high / box) * box, t: x.time }; } }
        });
        if (col) col.up ? push(col.t, col.bot, col.top, col.bot, col.top) : push(col.t, col.top, col.top, col.bot, col.bot);
        return out;
      }
      return b;
    },
    toMain(x) {
      const t = C.type;
      if (t === 'line' || t === 'linemk' || t === 'step' || t === 'area' || t === 'baseline' || t === 'kagi' || t === 'hlcarea') return { time: x.time, value: x.close };
      if (t === 'columns') return { time: x.time, value: x.close, color: x.close >= x.open ? C.colors().up : C.colors().dn };
      return { time: x.time, open: x.open, high: x.high, low: x.low, close: x.close };
    },
    applyPrecision() {
      const v = C.view; if (!v.length) return;
      const a = Math.abs(v[v.length - 1].close), d = a >= 1000 ? 2 : a >= 10 ? 2 : a >= 1 ? 3 : a >= 0.1 ? 4 : a >= 0.001 ? 6 : 8;
      C.main.applyOptions({ priceFormat: { type: 'price', precision: d, minMove: Math.pow(10, -d) } });
    },

    /* ---------- Vẽ lại toàn bộ ---------- */
    refresh(keepView) {
      if (!App.state.bars.length) return;
      const range = keepView ? C.api.timeScale().getVisibleLogicalRange() : null;
      C.buildView();
      C.applyPrecision();
      C.main.setData(C.view.map(C.toMain));
      if (C.type === 'hlcarea') { C.extra[0].setData(C.view.map(x => ({ time: x.time, value: x.high }))); C.extra[1].setData(C.view.map(x => ({ time: x.time, value: x.low }))); }
      if (C.type === 'baseline') { const v = C.view; C.main.applyOptions({ baseValue: { type: 'price', price: v[Math.max(0, v.length - 100)].close } }); }
      C.renderIndicators();
      C.renderCompares();
      if (range) C.api.timeScale().setVisibleLogicalRange(range);
      else if (!keepView) { const n = C.view.length; C.api.timeScale().setVisibleLogicalRange({ from: Math.max(-5, n - 140), to: n + 10 }); }
      App.ui.legend(null);
    },
    // Thêm nến cũ vào đầu, giữ khung nhìn
    prepended(k) {
      const r = C.api.timeScale().getVisibleLogicalRange();
      C.refresh(false);
      if (r && !SYNTH[C.type]) C.api.timeScale().setVisibleLogicalRange({ from: r.from + k, to: r.to + k });
    },

    /* ---------- Cập nhật realtime ---------- */
    updateBar(bar) {
      const bars = App.state.bars; if (!bars.length) return;
      const last = bars[bars.length - 1];
      if (bar.time < last.time) { const i = bars.findIndex(b => b.time === bar.time); if (i >= 0) bars[i] = bar; return; }
      const isNew = bar.time > last.time;
      if (isNew) bars.push(bar); else bars[bars.length - 1] = bar;
      App.onPrice && App.onPrice(App.state.src, App.state.sym, bar.close);
      if (C.replay) return; // đang phát lại thì không vẽ giá mới
      if (SYNTH[C.type] || C.type === 'ha') { C.throttle(() => C.refresh(true), 1000); return; }
      C.view = bars; C.D = T.prep(bars);
      C.main.update(C.toMain(bar));
      if (C.type === 'hlcarea') { C.extra[0].update({ time: bar.time, value: bar.high }); C.extra[1].update({ time: bar.time, value: bar.low }); }
      C.throttle(() => { C.D = T.prep(C.view); C.renderIndicators(true); }, isNew ? 0 : 1200);
      if (!C.hover) App.ui.legend(null);
    },
    throttle(fn, ms) {
      if (C._thr) { C._pend = fn; return; }
      fn(); C._thr = setTimeout(() => { C._thr = null; if (C._pend) { const f = C._pend; C._pend = null; C.throttle(f, ms); } }, ms);
    },

    /* =========================================================
     * CHỈ BÁO
     * ========================================================= */
    saveInds() { App.store.set('inds', C.inds); App.ui.refreshTree && App.ui.refreshTree(); },
    addIndicator(id, I) {
      const def = App.INDICATORS[id]; if (!def) return;
      if (def.need) { App.toast(def.name + ': ' + def.need, 'err', 6000); return; }
      const uid = Date.now() + Math.floor(Math.random() * 1000);
      C.inds.push({ uid, id, I: I || {}, st: {} });
      C.saveInds(); C.renderIndicators();
      App.toast('Đã thêm ' + def.name, 'ok');
      return uid;
    },
    removeIndicator(uid) { C.inds = C.inds.filter(x => x.uid !== uid); C.saveInds(); C.renderIndicators(); },
    inputs(inst) { const def = App.INDICATORS[inst.id], I = {}; def.inputs.forEach(([k, , v]) => { I[k] = inst.I[k] != null ? inst.I[k] : v; }); return I; },
    plotStyle(inst, k) { const def = App.INDICATORS[inst.id], p = def.plots.find(x => x[0] === k) || []; return Object.assign({ c: p[2] || App.theme.accent, w: p[3] === 'hist' || p[3] === 'cols' ? 1 : 1.5, v: true }, (inst.st || {})[k] || {}); },
    paneOf: {},

    renderIndicators(soft) {
      const D = C.D; if (!D || !D.n) return;
      // Tính toán
      C.results = {};
      C.inds.forEach(inst => {
        const def = App.INDICATORS[inst.id]; if (!def || def.need) return;
        try { C.results[inst.uid] = def.calc(D, C.inputs(inst)) || {}; } catch (e) { console.warn(inst.id, e); C.results[inst.uid] = {}; }
      });
      // Cấu trúc khung (pane) có thay đổi không?
      const sig = C.inds.map(x => x.uid + ':' + x.id + ':' + (x.hidden ? 0 : 1) + ':' + JSON.stringify(x.st || {})).join('|') + '#' + C.type;
      if (soft && sig === C._sig) { C.updateIndicatorData(); C.updateMarkers(); return; }
      C._sig = sig;
      Object.values(C.series).flat().forEach(s => { try { C.api.removeSeries(s); } catch (e) {} });
      C.series = {}; C.paneOf = {};
      let pane = 1;
      C.inds.forEach(inst => {
        const def = App.INDICATORS[inst.id], res = C.results[inst.uid]; if (!def || !res || inst.hidden) return;
        const myPane = def.overlay ? 0 : pane;
        const list = [];
        def.plots.forEach(([k, , , type]) => {
          if (!res[k]) return;
          const st = C.plotStyle(inst, k); if (!st.v) return;
          const base = { priceLineVisible: false, lastValueVisible: def.overlay ? false : true, crosshairMarkerVisible: false, title: '' };
          if (def.scale === 'vol') Object.assign(base, { priceScaleId: 'vol' + inst.uid, lastValueVisible: false });
          let s;
          if (type === 'hist' || type === 'cols') s = C.api.addSeries(LC.HistogramSeries, Object.assign(base, { color: st.c, base: 0 }), myPane);
          else if (type === 'area') s = C.api.addSeries(LC.AreaSeries, Object.assign(base, { lineColor: st.c, topColor: st.c + '44', bottomColor: st.c + '05', lineWidth: st.w }), myPane);
          else s = C.api.addSeries(LC.LineSeries, Object.assign(base, { color: st.c, lineWidth: st.w, lineType: type === 'step' ? 1 : 0, lineVisible: !(type === 'dots' || type === 'cross'), pointMarkersVisible: type === 'dots' || type === 'cross', pointMarkersRadius: 2 }), myPane);
          s._plot = k; s._uid = inst.uid; list.push(s);
        });
        if (def.scale === 'vol' && list.length) C.api.priceScale('vol' + inst.uid, 0).applyOptions({ scaleMargins: { top: 0.8, bottom: 0 }, visible: false });
        // các mức ngang
        if (list[0] && def.levels && def.levels.length && !def.overlay) def.levels.forEach(v => list.find(s => s._plot) .createPriceLine({ price: v, color: App.theme.muted, lineWidth: 1, lineStyle: 2, axisLabelVisible: false }));
        C.series[inst.uid] = list;
        if (!def.overlay && (list.length || def.plots.length)) { C.paneOf[inst.uid] = pane; pane++; }
      });
      C.updateIndicatorData();
      // chiều cao khung chỉ báo
      const ps = C.api.panes(); ps.forEach((p, i) => p.setStretchFactor(i === 0 ? 3 : 1));
      C.updateMarkers();
      App.ui.legend(C.hover);
      requestAnimationFrame(() => requestAnimationFrame(() => App.ui.legend(C.hover)));
      App.ui.strategyPanel && App.ui.strategyPanel();
    },
    updateIndicatorData() {
      const D = C.D, step = D.n > 1 ? D.t[D.n - 1] - D.t[D.n - 2] : 86400;
      Object.entries(C.series).forEach(([uid, list]) => {
        const res = C.results[uid]; if (!res) return;
        list.forEach(s => {
          const arr = res[s._plot], cols = res.colors && res.colors[s._plot], out = [];
          for (let i = 0; i < D.n; i++) {
            const v = arr[i];
            if (!isN(v)) { out.push({ time: D.t[i] }); continue; }
            const p = { time: D.t[i], value: v }; if (cols && cols[i]) p.color = cols[i]; out.push(p);
          }
          const fut = res.future && res.future[s._plot];
          if (fut) fut.forEach((v, k) => out.push(isN(v) ? { time: D.t[D.n - 1] + step * (k + 1), value: v } : { time: D.t[D.n - 1] + step * (k + 1) }));
          // bỏ khoảng trắng ở đầu
          let f = 0; while (f < out.length && out[f].value == null) f++;
          try { s.setData(out.slice(f)); } catch (e) { console.warn(e); }
        });
      });
    },
    updateMarkers() {
      const D = C.D, mk = [];
      C.inds.forEach(inst => { const r = C.results[inst.uid]; if (inst.hidden || !r || !r.markers) return; r.markers.forEach(m => { if (m.i >= 0 && m.i < D.n) mk.push({ time: D.t[m.i], position: m.pos, shape: m.shape, color: m.color, text: App.settings.markerText === false ? '' : (m.text || ''), size: 0.8 }); }); });
      mk.sort((a, b) => a.time - b.time);
      if (!C.markersApi) C.markersApi = LC.createSeriesMarkers(C.main, mk); else C.markersApi.setMarkers(mk);
    },

    /* ---------- Phần vẽ thêm của chỉ báo (trên canvas) ---------- */
    drawOverlays(g) {
      const D = C.D; if (!D) return;
      const ts = C.api.timeScale(), W = ts.width(), H = App.draw.H;
      const X = {
        W, H, D,
        x: i => ts.logicalToCoordinate(i), y: p => C.main.priceToCoordinate(p),
        visible() { const r = ts.getVisibleLogicalRange() || { from: 0, to: D.n - 1 }; return [Math.max(0, Math.ceil(r.from)), Math.min(D.n - 1, Math.floor(r.to))]; },
        seg(g, x1, y1, x2, y2, col, dash, w) { if ([x1, y1, x2, y2].some(v => v == null)) return; g.beginPath(); g.strokeStyle = col; g.lineWidth = w || 1; g.setLineDash(dash || []); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); g.setLineDash([]); },
        hline(g, x1, x2, y, col, text, w, small) { if (y == null) return; X.seg(g, x1 == null ? 0 : x1, y, x2 == null ? W : x2, y, col, null, w || 1); if (text) { g.font = (small ? '10' : '11') + 'px sans-serif'; g.fillStyle = col; g.textAlign = 'right'; g.textBaseline = 'bottom'; g.fillText(text, Math.min(W - 4, x2 == null ? W - 4 : x2 - 2), y - 2); g.textAlign = 'left'; } },
        poly(g, pts, col, dash, w) { const ok = pts.filter(p => p[0] != null && p[1] != null); if (ok.length < 2) return; g.beginPath(); g.strokeStyle = col; g.lineWidth = w || 1; g.setLineDash(dash || []); ok.forEach((p, k) => k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); g.setLineDash([]); },
        box(g, x1, y1, x2, y2, fill, stroke) { if ([x1, y1, x2, y2].some(v => v == null)) return; g.fillStyle = fill; g.fillRect(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1)); if (stroke) { g.strokeStyle = stroke; g.lineWidth = 1; g.strokeRect(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1)); } },
        label(g, x, y, text, col) { if (x == null || y == null) return; g.font = '11px sans-serif'; const w = g.measureText(text).width + 8; g.fillStyle = col; g.fillRect(x - w / 2, y - 8, w, 16); g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, x, y); g.textAlign = 'left'; }
      };
      C.inds.forEach(inst => {
        const def = App.INDICATORS[inst.id], r = C.results[inst.uid]; if (!r || inst.hidden || !def || !def.overlay) return;
        // tô giữa hai đường (Bollinger, Ichimoku…)
        (r.fills || []).forEach(([k1, k2, col, col2]) => {
          const a = r[k1], b = r[k2]; if (!a || !b) return;
          const [i0, i1] = X.visible(), ext = r.future ? (r.future[k1] || []).length : 0;
          const get = (arr, k, i) => i < D.n ? arr[i] : (r.future && r.future[k] ? r.future[k][i - D.n] : NaN);
          let start = null;
          const flush = (end, up) => { if (start == null) return; g.beginPath(); for (let i = start; i <= end; i++) g.lineTo(X.x(i), X.y(get(a, k1, i))); for (let i = end; i >= start; i--) g.lineTo(X.x(i), X.y(get(b, k2, i))); g.closePath(); g.fillStyle = col2 && !up ? col2 : col; g.fill(); start = null; };
          let up = null;
          for (let i = Math.max(0, i0 - 2); i <= i1 + ext && i < D.n + ext; i++) {
            const va = get(a, k1, i), vb = get(b, k2, i);
            if (!isN(va) || !isN(vb)) { flush(i - 1, up); continue; }
            const u = va >= vb; if (col2 && up != null && u !== up) { flush(i, up); start = i; } if (start == null) start = i; up = u;
          }
          flush(Math.min(i1 + ext, D.n + ext - 1), up);
        });
        if (r.draw) { g.save(); try { r.draw(g, X); } catch (e) { console.warn(inst.id, e); } g.restore(); }
      });
    },

    /* =========================================================
     * SO SÁNH MÃ
     * ========================================================= */
    async addCompare(src, sym) {
      const s = App.sources[src]; sym = s.normalize(sym);
      try {
        const bars = await s.fetchBars(sym, App.state.tf);
        const color = ['#ff9800', '#e91e63', '#9c27b0', '#00bcd4', '#8bc34a'][C.compares.length % 5];
        C.compares.push({ src, sym, bars, color });
        C.renderCompares(); App.ui.legend(null);
        App.toast('Đang so sánh với ' + sym, 'ok');
      } catch (e) { App.toast('Không tải được ' + sym + ': ' + e.message, 'err'); }
    },
    removeCompare(k) { const c = C.compares[k]; if (c && c.series) C.api.removeSeries(c.series); C.compares.splice(k, 1); C.renderCompares(); App.ui.legend(null); },
    renderCompares() {
      C.compares.forEach(c => { if (!c.series) c.series = C.api.addSeries(LC.LineSeries, { color: c.color, lineWidth: 2, priceLineVisible: false, title: c.sym }, 0); const t0 = (C.view[0] || {}).time, t1 = (C.view[C.view.length - 1] || {}).time; c.series.setData(c.bars.filter(b => b.time >= t0 && b.time <= t1).map(b => ({ time: b.time, value: b.close }))); });
      const cs = App.settings.chart || {};
      C.api.priceScale('right', 0).applyOptions({ mode: C.compares.length ? LC.PriceScaleMode.Percentage : (cs.scale || 0) });
    }
  };
})(window.App);
