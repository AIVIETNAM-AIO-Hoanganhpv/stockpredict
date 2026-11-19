/* =========================================================
 * sources.js — Các nguồn dữ liệu giá
 *
 * Mỗi nguồn có cùng "giao diện":
 *   label            : tên hiển thị
 *   tfs              : các khung thời gian hỗ trợ
 *   fetchBars(sym, tf, beforeTime?) -> Promise<[{time,open,high,low,close,volume}]>
 *   live(sym, tf, onBar)            -> hàm dừng (cập nhật nến realtime)
 *   quotes([sym])                   -> Promise<{sym:{price, chg}}> (cho danh sách theo dõi)
 *
 * "time" là số giây ĐÃ CỘNG múi giờ địa phương (xem App.TZ trong util.js).
 * ========================================================= */
(function (App) {
  'use strict';

  // Khung thời gian chung: mã -> số giây
  App.TF = { '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '12h': 43200, '1D': 86400, '3D': 259200, '1W': 604800, '1M': 2592000 };
  App.TF_LABEL = { '1m': '1p', '3m': '3p', '5m': '5p', '15m': '15p', '30m': '30p', '1h': '1g', '2h': '2g', '4h': '4g', '6h': '6g', '12h': '12g', '1D': '1N', '3D': '3N', '1W': '1T', '1M': '1Th' };
  App.TF_NAME = { '1m': '1 phút', '3m': '3 phút', '5m': '5 phút', '15m': '15 phút', '30m': '30 phút', '1h': '1 giờ', '2h': '2 giờ', '4h': '4 giờ', '6h': '6 giờ', '12h': '12 giờ', '1D': '1 ngày', '3D': '3 ngày', '1W': '1 tuần', '1M': '1 tháng' };

  const now = () => Math.floor(Date.now() / 1000);

  /* =======================================================
   * 1) BINANCE — tiền mã hoá, miễn phí, không cần key
   * ======================================================= */
  const BN_REST = ['https://api.binance.com', 'https://data-api.binance.vision'];
  const BN_WS = ['wss://stream.binance.com:9443/ws/', 'wss://data-stream.binance.vision/ws/'];
  const BN_TF = { '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '12h': '12h', '1D': '1d', '3D': '3d', '1W': '1w', '1M': '1M' };
  let bnBase = 0; // máy chủ đang dùng được

  async function bnGet(path) {
    let lastErr;
    for (let i = 0; i < BN_REST.length; i++) {
      const idx = (bnBase + i) % BN_REST.length;
      try {
        const j = await App.fetchJSON(BN_REST[idx] + path);
        bnBase = idx;
        return j;
      } catch (e) { lastErr = e; }
    }
    throw lastErr;
  }

  const binance = {
    label: 'Binance (Crypto)',
    short: 'Binance',
    tfs: Object.keys(BN_TF),
    canLoadMore: true,
    hint: 'VD: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT',
    normalize: s => s.toUpperCase().replace(/[^A-Z0-9]/g, ''),

    async fetchBars(sym, tf, beforeTime) {
      let q = `/api/v3/klines?symbol=${sym}&interval=${BN_TF[tf]}&limit=1000`;
      if (beforeTime) q += `&endTime=${(beforeTime - App.TZ) * 1000 - 1}`;
      const rows = await bnGet(q);
      if (!Array.isArray(rows)) throw new Error('Mã không hợp lệ');
      return rows.map(r => ({
        time: r[0] / 1000 + App.TZ,
        open: +r[1], high: +r[2], low: +r[3], close: +r[4], volume: +r[5]
      }));
    },

    live(sym, tf, onBar) {
      let ws, stopped = false, tries = 0, wsIdx = 0;
      const open = () => {
        if (stopped) return;
        ws = new WebSocket(BN_WS[wsIdx % BN_WS.length] + sym.toLowerCase() + '@kline_' + BN_TF[tf]);
        ws.onopen = () => { tries = 0; App.setStatus('live', 'Realtime (WebSocket)'); };
        ws.onmessage = ev => {
          const k = JSON.parse(ev.data).k;
          if (!k) return;
          onBar({ time: k.t / 1000 + App.TZ, open: +k.o, high: +k.h, low: +k.l, close: +k.c, volume: +k.v });
        };
        ws.onclose = () => {
          if (stopped) return;
          App.setStatus('warn', 'Mất kết nối, đang nối lại…');
          tries++; wsIdx++;
          setTimeout(open, Math.min(30000, 1000 * 2 ** tries));
        };
        ws.onerror = () => { try { ws.close(); } catch (e) {} };
      };
      open();
      return () => { stopped = true; try { ws && ws.close(); } catch (e) {} };
    },

    async quotes(syms) {
      if (!syms.length) return {};
      const rows = await bnGet('/api/v3/ticker/24hr?symbols=' + encodeURIComponent(JSON.stringify(syms)));
      const out = {};
      rows.forEach(r => { out[r.symbol] = { price: +r.lastPrice, chg: +r.priceChangePercent }; });
      return out;
    }
  };

  /* =======================================================
   * 2) CỔ PHIẾU VIỆT NAM — API công khai VNDirect, dự phòng TCBS
   *    (không chính thức; giá tính theo NGHÌN ĐỒNG)
   * ======================================================= */
  const VND_TF = { '1m': '1', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '1D': 'D', '1W': 'W' };
  // Khung VN không có sẵn -> gộp từ khung nhỏ hơn
  const VN_AGG = { '3m': '1m', '2h': '1h', '4h': '1h', '1M': '1D' };

  async function vnTry(urls) {
    // Thử lần lượt: gọi thẳng, rồi qua proxy (nếu có cấu hình)
    let lastErr;
    const list = [...urls];
    if (App.settings.proxy) urls.forEach(u => list.push(App.withProxy(u)));
    for (const u of list) {
      try { return await App.fetchJSON(u); } catch (e) { lastErr = e; }
    }
    throw lastErr || new Error('Không lấy được dữ liệu');
  }

  async function vnDirect(sym, tf, from, to) {
    const url = `https://dchart-api.vndirect.com.vn/dchart/history?resolution=${VND_TF[tf]}&symbol=${sym}&from=${from}&to=${to}`;
    const j = await vnTry([url]);
    if (!j || !j.t || !j.t.length) throw new Error('Không có dữ liệu cho mã ' + sym);
    return j.t.map((t, i) => ({
      time: t + App.TZ, open: +j.o[i], high: +j.h[i], low: +j.l[i], close: +j.c[i], volume: +j.v[i]
    }));
  }

  async function vnTcbs(sym, count) {
    const isIndex = /INDEX|^VN30$|^HNX/.test(sym);
    const url = `https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term?ticker=${sym}&type=${isIndex ? 'index' : 'stock'}&resolution=D&to=${now()}&countBack=${count}`;
    const j = await vnTry([url]);
    if (!j || !j.data || !j.data.length) throw new Error('Không có dữ liệu cho mã ' + sym);
    const k = isIndex ? 1 : 1000; // TCBS trả giá cổ phiếu theo đồng -> đổi sang nghìn đồng
    return j.data.map(d => ({
      time: Math.floor(Date.parse(d.tradingDate) / 1000),
      open: d.open / k, high: d.high / k, low: d.low / k, close: d.close / k, volume: +d.volume
    }));
  }

  // Nến trong phiên từ API công khai của TCBS (dự phòng cho VNDirect)
  async function vnTcbsIntraday(sym, tf, to) {
    const res = { '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60 }[tf];
    const isIndex = App.isIndex(sym);
    const url = `https://apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars?ticker=${sym}&type=${isIndex ? 'index' : 'stock'}&resolution=${res}&to=${Math.floor(to)}&countBack=600`;
    const j = await vnTry([url]);
    if (!j || !j.data || !j.data.length) throw new Error('Không có dữ liệu trong phiên cho ' + sym);
    const k = isIndex ? 1 : 1000;
    return j.data.map(d => ({ time: Math.floor(Date.parse(d.tradingDate) / 1000) + (/Z$/.test(d.tradingDate) ? App.TZ : 0), open: d.open / k, high: d.high / k, low: d.low / k, close: d.close / k, volume: +d.volume })).sort((a, b) => a.time - b.time);
  }

  const vn = {
    label: 'Cổ phiếu Việt Nam',
    short: 'VN',
    tfs: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1D', '1W', '1M'],
    canLoadMore: true,
    hint: 'VD: VNM, FPT, HPG, VCB, VNINDEX, VN30 — giá theo nghìn đồng',
    normalize: s => s.toUpperCase().replace(/[^A-Z0-9]/g, ''),

    async fetchBars(sym, tf, beforeTime) {
      try { return await vn._fetch(sym, tf, beforeTime); }
      catch (e) {
        // Không gọi được API công khai -> dùng connector TCBS (nếu đang mở trong Claude)
        if (App.mcp && tcbs.tfs.includes(tf)) return (await tcbs.fetchBars(sym, tf, beforeTime)).map(b => App.isIndex(sym) ? b : { ...b, open: b.open / 1000, high: b.high / 1000, low: b.low / 1000, close: b.close / 1000 });
        throw e;
      }
    },
    async _fetch(sym, tf, beforeTime) {
      if (VN_AGG[tf]) {
        const base = await vn._fetch(sym, VN_AGG[tf], beforeTime);
        return tf === '1M' ? App.aggregateMonth(base) : App.aggregate(base, App.TF[tf]);
      }
      const tfs = App.TF[tf];
      const intraday = tfs < 86400;
      const to = beforeTime ? beforeTime - App.TZ - 1 : now();
      // Lấy khoảng thời gian đủ ~600 nến (tính cả ngày nghỉ, giờ không giao dịch)
      const span = intraday ? tfs * 600 * 5 : tfs * 600 * 1.5;
      try {
        return await vnDirect(sym, tf, Math.floor(to - span), to);
      } catch (e) {
        if (intraday) return await vnTcbsIntraday(sym, tf, to);
        if (!beforeTime && (tf === '1D' || tf === '1W')) {
          const d = await vnTcbs(sym, 600);
          return tf === '1W' ? App.aggregate(d, 604800) : d;
        }
        throw e;
      }
    },

    live(sym, tf, onBar) {
      // VN không có WebSocket công khai -> hỏi lại mỗi 20 giây
      let stopped = false;
      const tick = async () => {
        if (stopped) return;
        try {
          const t = now();
          const bars = VN_AGG[tf] ? (await vn._fetch(sym, tf)).slice(-2) : await vnDirect(sym, tf, t - App.TF[tf] * 3 - 86400 * 4, t);
          bars.slice(-2).forEach(onBar);
          App.setStatus('live', 'Cập nhật mỗi 20 giây');
        } catch (e) {
          if (App.mcp && tcbs.tfs.includes(tf)) {
            try { (await tcbs.liveBars(sym, tf)).forEach(b => onBar(App.isIndex(sym) ? b : { ...b, open: b.open / 1000, high: b.high / 1000, low: b.low / 1000, close: b.close / 1000 })); App.setStatus('live', 'Qua TCBS (connector)'); return; } catch (e2) {}
          }
          App.setStatus('warn', 'Không cập nhật được giá VN');
        }
      };
      const id = setInterval(tick, App.mcp ? 30000 : 20000);
      return () => { stopped = true; clearInterval(id); };
    },

    async quotes(syms) {
      const out = {};
      await Promise.all(syms.map(async s => {
        try {
          let d;
          try { d = await vnDirect(s, '1D', now() - 86400 * 15, now()); }
          catch (e) { try { d = await vnTcbs(s, 5); } catch (e2) { if (!App.mcp) throw e2; d = (await tcbs.fetchBars(s, '1D', null, 3)).map(b => App.isIndex(s) ? b : { ...b, close: b.close / 1000 }); } }
          const a = d[d.length - 1], b = d[d.length - 2] || a;
          out[s] = { price: a.close, chg: (a.close / b.close - 1) * 100 };
        } catch (e) { /* bỏ qua mã lỗi */ }
      }));
      return out;
    }
  };

  /* =======================================================
   * 3) TWELVE DATA — Cổ phiếu Mỹ, Forex, Vàng (cần API key miễn phí)
   * ======================================================= */
  const TD_TF = { '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '1h', '2h': '2h', '4h': '4h', '1D': '1day', '1W': '1week', '1M': '1month' };
  const tdTZ = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { return 'UTC'; } })();

  function tdKey() {
    const k = (App.settings.tdKey || '').trim();
    if (!k) throw new Error('Cần API key Twelve Data — vào ⚙ Cài đặt để nhập');
    return k;
  }
  function tdParse(dt) {
    // "2024-01-02" hoặc "2024-01-02 09:30:00" (đã theo giờ máy) -> đọc như UTC
    return Math.floor(Date.parse(dt.replace(' ', 'T') + (dt.length <= 10 ? 'T00:00:00Z' : 'Z')) / 1000);
  }
  async function tdSeries(sym, tf, size, endDate) {
    let url = `https://api.twelvedata.com/time_series?symbol=${encodeURIComponent(sym)}&interval=${TD_TF[tf]}&outputsize=${size}&timezone=${encodeURIComponent(tdTZ)}&apikey=${tdKey()}`;
    if (endDate) url += '&end_date=' + encodeURIComponent(endDate);
    const j = await App.fetchJSON(url);
    if (j.status === 'error') throw new Error('Twelve Data: ' + j.message);
    return (j.values || []).map(v => ({
      time: tdParse(v.datetime),
      open: +v.open, high: +v.high, low: +v.low, close: +v.close, volume: v.volume ? +v.volume : 0
    })).reverse();
  }

  const td = {
    label: 'Mỹ / Forex / Vàng (Twelve Data)',
    short: 'TwelveData',
    tfs: Object.keys(TD_TF),
    canLoadMore: true,
    hint: 'VD: AAPL, TSLA, EUR/USD, USD/JPY, XAU/USD (vàng), BTC/USD',
    normalize: s => s.toUpperCase().replace(/\s/g, ''),

    async fetchBars(sym, tf, beforeTime) {
      let end;
      if (beforeTime) {
        const d = new Date((beforeTime - 1) * 1000);
        end = d.toISOString().slice(0, 19).replace('T', ' ');
      }
      return tdSeries(sym, tf, 1000, end);
    },

    live(sym, tf, onBar) {
      // Gói miễn phí giới hạn 8 lần gọi/phút -> hỏi lại mỗi 60 giây
      const tick = async () => {
        try {
          (await tdSeries(sym, tf, 2)).forEach(onBar);
          App.setStatus('live', 'Cập nhật mỗi 60 giây');
        } catch (e) { App.setStatus('warn', e.message); }
      };
      const id = setInterval(tick, 60000);
      return () => clearInterval(id);
    },

    async quotes(syms) {
      if (!syms.length || !App.settings.tdKey) return {};
      const j = await App.fetchJSON(`https://api.twelvedata.com/quote?symbol=${encodeURIComponent(syms.join(','))}&apikey=${tdKey()}`);
      const out = {};
      const one = q => { if (q && q.symbol && q.close) out[q.symbol.toUpperCase()] = { price: +q.close, chg: +q.percent_change }; };
      if (j.symbol) one(j); else Object.values(j).forEach(one);
      return out;
    }
  };

  /* =======================================================
   * 3b) TCBS — qua connector TCBS của cô trên Claude
   *     (chỉ chạy khi mở GreenView trong Claude; giá theo ĐỒNG)
   * ======================================================= */
  App.isIndex = sym => /INDEX$|^VN30$|^HNX30$|^UPCOM$|^VN100$|^VNMID$|^VNSML$|^VNALL$/.test(sym);
  App.mcp = null;
  App.tcbsErr = function (e) {
    const m = { needs_reauth: 'Kết nối TCBS đã hết hạn — vào Cài đặt › Connectors trên claude.ai để kết nối lại',
      server_not_connected: 'Chưa kết nối TCBS — thêm trong Cài đặt › Connectors trên claude.ai',
      not_in_manifest: 'Cô chưa cho phép GreenView dùng TCBS', approval_required: 'Cần cô cho phép GreenView dùng TCBS',
      selection_required: 'Có nhiều connector tên TCBS — hãy chọn một', blocked_by_policy: 'TCBS bị chặn bởi chính sách tài khoản',
      server_unavailable: 'Máy chủ TCBS tạm thời không phản hồi', tool_error: 'TCBS báo lỗi: ' + (e && e.message) };
    return new Error(m[e && e.code] || (e && e.message) || 'Lỗi TCBS');
  };
  App.tcbs = async function (tool, input, fresh) {
    if (!App.mcp) throw new Error('TCBS chỉ dùng được khi mở GreenView trong Claude (đã kết nối connector TCBS)');
    try {
      const r = await App.mcp.callTool('Tcbs', 'tcinvest-' + tool, input, fresh ? { cache: false } : { cache: { staleTime: 60000, gcTime: 600000 } });
      return r.payload;
    } catch (e) {
      if (e && e.retryable) { await new Promise(r => setTimeout(r, Math.min(e.retryAfterMs || 1500, 8000) + Math.random() * 500)); try { return (await App.mcp.callTool('Tcbs', 'tcinvest-' + tool, input, { cache: false })).payload; } catch (e2) { throw App.tcbsErr(e2); } }
      throw App.tcbsErr(e);
    }
  };
  const TC_TF = { '1D': 'D', '1W': 'W', '1M': 'M' };
  const TC_INTRA = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h'];
  // Giờ giao dịch HOSE/HNX (giờ Việt Nam): 9:00–11:30, 13:00–15:00, thứ 2–6
  App.vnMarketOpen = function (t) {
    const d = new Date(((t || now()) + 7 * 3600) * 1000), m = d.getUTCHours() * 60 + d.getUTCMinutes(), wd = d.getUTCDay();
    return wd >= 1 && wd <= 5 && ((m >= 540 && m <= 690) || (m >= 780 && m <= 905));
  };
  /* Tự ghép nến trong phiên: mỗi lần hỏi TCBS lấy nến NGÀY hiện tại (giá khớp + KL cộng dồn),
     lưu lại thành "điểm giá" theo thời gian, rồi gộp thành nến 1p, 5p… */
  const tickKey = sym => 'tick:' + sym;
  const loadTicks = sym => App.store.get(tickKey(sym), []);
  function addTick(sym, day) {
    const t = now(), ticks = loadTicks(sym), last = ticks[ticks.length - 1];
    if (!App.vnMarketOpen(t)) return ticks;
    if (last && t <= last.t) return ticks;
    if (last && last.p === day.close && last.v === day.volume && t - last.t < 600) return ticks;
    ticks.push({ t, p: day.close, v: day.volume, d: day.time });
    const cut = t - 6 * 86400; while (ticks.length && (ticks[0].t < cut || ticks.length > 4000)) ticks.shift();
    App.store.set(tickKey(sym), ticks);
    return ticks;
  }
  function buildBars(ticks, tf) {
    const step = App.TF[tf], out = [];
    let prevV = null, prevD = null;
    ticks.slice().sort((a, b) => a.t - b.t).forEach(k => {
      const time = Math.floor((k.t + App.TZ) / step) * step;
      if (k.d !== prevD) { prevV = null; prevD = k.d; }
      const dv = prevV == null ? 0 : Math.max(0, k.v - prevV); prevV = k.v;
      const b = out[out.length - 1];
      if (b && b.time === time) { b.high = Math.max(b.high, k.p); b.low = Math.min(b.low, k.p); b.close = k.p; b.volume += dv; }
      else out.push({ time, open: b ? b.close : k.p, high: Math.max(k.p, b ? b.close : k.p), low: Math.min(k.p, b ? b.close : k.p), close: k.p, volume: dv });
    });
    return out;
  }
  async function dailyNow(sym) {
    const d = await tcbs.fetchBars(sym, '1D', null, 1, true);
    return d[d.length - 1];
  }
  const tcbs = {
    label: 'TCBS (connector)',
    short: 'TCBS',
    tfs: TC_INTRA.concat(['1D', '1W', '1M']),
    canLoadMore: true,
    hint: 'Cổ phiếu & chỉ số VN qua connector TCBS. VD: FPT, VCB, HPG, VNINDEX, VN30 — giá theo đồng. Khung nhỏ được tự ghép từ lúc mở trang, trong giờ giao dịch',
    normalize: s => s.toUpperCase().replace(/[^A-Z0-9]/g, ''),
    async fetchBars(sym, tf, beforeTime, count, fresh) {
      if (TC_INTRA.includes(tf)) {
        if (beforeTime) return [];
        let ticks = loadTicks(sym);
        try { ticks = addTick(sym, await dailyNow(sym)); } catch (e) { if (!ticks.length) throw e; }
        let bars = buildBars(ticks, tf);
        if (!bars.length) {
          // chưa có điểm nào (ngoài giờ giao dịch): hiện 1 nến từ giá đóng cửa gần nhất
          const d = await dailyNow(sym), step = App.TF[tf];
          bars = [{ time: Math.floor((now() + App.TZ) / step) * step, open: d.close, high: d.close, low: d.close, close: d.close, volume: 0 }];
          App.toast(App.vnMarketOpen() ? 'Đang bắt đầu ghép nến — cứ 30 giây có thêm điểm giá mới' : 'Ngoài giờ giao dịch (9:00–11:30, 13:00–15:00). Nến khung nhỏ chỉ được ghép trong giờ giao dịch, khi trang đang mở.', 'info', 7000);
        } else App.toast(`Nến ${App.TF_NAME[tf]} tự ghép từ ${ticks.length} điểm giá đã thu (TCBS không có sẵn nến trong phiên)`, 'info', 5000);
        return bars;
      }
      const day = 86400, to = beforeTime ? Math.floor((beforeTime - 1) / day) * day : Math.floor(now() / day) * day;
      const j = await App.tcbs('getLongTermCandleChart', { type: App.isIndex(sym) ? 'index' : 'stock', ticker: sym, resolution: TC_TF[tf] || 'D', to, countBack: count || 250 }, fresh);
      if (!j || !j.data || !j.data.length) throw new Error('TCBS không có dữ liệu cho ' + sym);
      const out = j.data.map(d => ({ time: Math.floor(Date.parse(d.tradingDate) / 1000), open: +d.open, high: +d.high, low: +d.low, close: +d.close, volume: +d.volume || 0 }));
      out.sort((a, b) => a.time - b.time);
      return out.filter((b, i) => !i || b.time !== out[i - 1].time);
    },
    // Lấy nến mới nhất (dùng cho cập nhật realtime)
    async liveBars(sym, tf) {
      if (TC_INTRA.includes(tf)) { const ticks = addTick(sym, await dailyNow(sym)), b = buildBars(ticks, tf); return b.slice(-2); }
      return tcbs.fetchBars(sym, tf, null, 2, true);
    },
    live(sym, tf, onBar) {
      const intra = TC_INTRA.includes(tf), ms = intra ? 30000 : 60000;
      const msg = intra ? 'TCBS · tự ghép nến, 30 giây/lần' + (App.vnMarketOpen() ? '' : ' (ngoài giờ giao dịch)') : 'TCBS · cập nhật mỗi 60 giây';
      const id = setInterval(async () => {
        try { (await tcbs.liveBars(sym, tf)).forEach(onBar); App.setStatus('live', msg); }
        catch (e) { App.setStatus('warn', e.message); }
      }, ms);
      App.setStatus('live', msg);
      return () => clearInterval(id);
    },
    async quotes(syms) {
      const out = {};
      await Promise.all(syms.map(async s => { try { const d = await tcbs.fetchBars(s, '1D', null, 3); const a = d[d.length - 1], b = d[d.length - 2] || a; out[s] = { price: a.close, chg: (a.close / b.close - 1) * 100 }; } catch (e) {} }));
      return out;
    }
  };

  /* =======================================================
   * 4) DỮ LIỆU GIẢ LẬP — chạy mọi nơi, không cần mạng
   * ======================================================= */
  const demoState = {}; // lưu chuỗi nến theo mã+khung

  function demoGen(sym, tf) {
    const key = sym + '|' + tf;
    if (demoState[key]) return demoState[key];
    const rnd = App.seededRandom(key);
    const step = App.TF[tf];
    const n = 800;
    const end = Math.floor((now() + App.TZ) / step) * step;
    let price = 50 + rnd() * 950;
    const vol = 0.004 * Math.sqrt(step / 3600) + 0.002;
    const bars = [];
    let trend = 0;
    for (let i = n - 1; i >= 0; i--) {
      if (i % 60 === 0) trend = (rnd() - 0.5) * vol * 0.6;
      const o = price;
      const c = o * (1 + trend + (rnd() - 0.5) * 2 * vol);
      const h = Math.max(o, c) * (1 + rnd() * vol * 0.8);
      const l = Math.min(o, c) * (1 - rnd() * vol * 0.8);
      bars.push({ time: end - i * step, open: o, high: h, low: l, close: c, volume: Math.round(1000 + rnd() * 9000 * (1 + Math.abs(c - o) / o * 50)) });
      price = c;
    }
    return (demoState[key] = bars);
  }

  const demo = {
    label: 'Dữ liệu giả lập',
    short: 'Giả lập',
    tfs: Object.keys(App.TF),
    canLoadMore: false,
    hint: 'Gõ tên bất kỳ, VD: DEMO, ABC, TEST1',
    normalize: s => s.toUpperCase().replace(/[^A-Z0-9]/g, '') || 'DEMO',
    async fetchBars(sym, tf) { return demoGen(sym, tf).map(b => ({ ...b })); },
    live(sym, tf, onBar) {
      const bars = demoGen(sym, tf), step = App.TF[tf];
      const id = setInterval(() => {
        const last = bars[bars.length - 1];
        const t = Math.floor((now() + App.TZ) / step) * step;
        if (t > last.time) {
          bars.push({ time: t, open: last.close, high: last.close, low: last.close, close: last.close, volume: 0 });
        }
        const b = bars[bars.length - 1];
        b.close = b.close * (1 + (Math.random() - 0.5) * 0.0016);
        b.high = Math.max(b.high, b.close); b.low = Math.min(b.low, b.close);
        b.volume += Math.round(Math.random() * 60);
        onBar({ ...b });
      }, 1000);
      App.setStatus('live', 'Giả lập — nhảy giá mỗi giây');
      return () => clearInterval(id);
    },
    async quotes(syms) {
      const out = {};
      syms.forEach(s => {
        const d = demoGen(s, '1D'), a = d[d.length - 1], b = d[d.length - 2];
        out[s] = { price: a.close, chg: (a.close / b.close - 1) * 100 };
      });
      return out;
    }
  };

  /* =======================================================
   * 5) FILE CSV — cô tải file giá lên
   *    Cột: thời gian, mở, cao, thấp, đóng, [khối lượng]
   * ======================================================= */
  App.csvSets = {};
  const csv = {
    label: 'File CSV đã nhập',
    short: 'CSV',
    tfs: ['1D'],
    canLoadMore: false,
    hint: 'Dùng nút "Nhập file CSV" bên dưới',
    normalize: s => s,
    async fetchBars(sym) {
      const d = App.csvSets[sym] || App.store.get('csv:' + sym);
      if (!d) throw new Error('Chưa có file CSV tên ' + sym);
      App.csvSets[sym] = d;
      return d.map(b => ({ ...b }));
    },
    live() { App.setStatus('idle', 'Dữ liệu tĩnh từ file'); return () => {}; },
    async quotes(syms) {
      const out = {};
      for (const s of syms) {
        try {
          const d = await csv.fetchBars(s);
          const a = d[d.length - 1], b = d[d.length - 2] || a;
          out[s] = { price: a.close, chg: (a.close / b.close - 1) * 100 };
        } catch (e) {}
      }
      return out;
    }
  };

  // Đọc nội dung CSV -> mảng nến
  App.parseCSV = function (text) {
    const lines = text.replace(/\r/g, '').split('\n').map(l => l.trim()).filter(Boolean);
    if (lines.length < 2) throw new Error('File quá ít dòng');
    const sep = [';', '\t', ','].find(s => lines[0].split(s).length >= 5) || ',';
    const split = l => l.split(sep).map(x => x.trim().replace(/^"|"$/g, ''));
    let head = split(lines[0]).map(h => h.toLowerCase());
    let start = 1;
    const isNum = v => v !== '' && !isNaN(v.replace(',', '.'));
    if (isNum(split(lines[0])[1] || '')) { head = []; start = 0; } // không có dòng tiêu đề
    const find = (names, def) => {
      const i = head.findIndex(h => names.some(n => h.includes(n)));
      return i >= 0 ? i : def;
    };
    const iT = find(['date', 'time', 'ngày', 'ngay', 'thời', 'thoi'], 0);
    const iO = find(['open', 'mở', 'mo cua', 'mở cửa'], 1);
    const iH = find(['high', 'cao'], 2);
    const iL = find(['low', 'thấp', 'thap'], 3);
    const iC = find(['close', 'đóng', 'dong', 'price', 'giá'], 4);
    const iV = find(['vol', 'khối', 'khoi', 'kl'], 5);
    const num = v => parseFloat(String(v).replace(/\s/g, '').replace(/,(?=\d{3}\b)/g, '').replace(',', '.'));
    const parseT = v => {
      if (/^\d{10}$/.test(v)) return +v;
      if (/^\d{13}$/.test(v)) return Math.floor(+v / 1000);
      let m = v.match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})(?:[ T](\d{1,2}):(\d{2}))?/); // dd/mm/yyyy
      if (m) return Date.UTC(+m[3], +m[2] - 1, +m[1], +(m[4] || 0), +(m[5] || 0)) / 1000;
      m = v.match(/^(\d{4})[\/\-.](\d{1,2})[\/\-.](\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?/); // yyyy-mm-dd
      if (m) return Date.UTC(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0)) / 1000;
      return NaN;
    };
    const bars = [];
    for (let i = start; i < lines.length; i++) {
      const c = split(lines[i]);
      const b = { time: parseT(c[iT]), open: num(c[iO]), high: num(c[iH]), low: num(c[iL]), close: num(c[iC]), volume: c[iV] != null ? num(c[iV]) || 0 : 0 };
      if (!isNaN(b.time) && !isNaN(b.close)) {
        if (isNaN(b.open)) b.open = b.close;
        if (isNaN(b.high)) b.high = Math.max(b.open, b.close);
        if (isNaN(b.low)) b.low = Math.min(b.open, b.close);
        bars.push(b);
      }
    }
    if (bars.length < 2) throw new Error('Không đọc được dữ liệu — cần cột ngày, mở, cao, thấp, đóng');
    bars.sort((a, b) => a.time - b.time);
    return bars.filter((b, i) => i === 0 || b.time !== bars[i - 1].time);
  };

  // Gộp nến nhỏ thành nến lớn hơn (VD: ngày -> tuần)
  App.aggregate = function (bars, step) {
    const out = [];
    const offset = step === 604800 ? 4 * 86400 : 0; // tuần bắt đầu thứ Hai
    bars.forEach(b => {
      const t = Math.floor((b.time - offset) / step) * step + offset;
      const last = out[out.length - 1];
      if (last && last.time === t) {
        last.high = Math.max(last.high, b.high); last.low = Math.min(last.low, b.low);
        last.close = b.close; last.volume += b.volume;
      } else out.push({ ...b, time: t });
    });
    return out;
  };

  App.aggregateMonth = function (bars) {
    const out = [];
    bars.forEach(b => { const d = new Date(b.time * 1000), t = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000, l = out[out.length - 1];
      if (l && l.time === t) { l.high = Math.max(l.high, b.high); l.low = Math.min(l.low, b.low); l.close = b.close; l.volume += b.volume; } else out.push({ ...b, time: t }); });
    return out;
  };
  App.sources = { BINANCE: binance, VN: vn, TCBS: tcbs, TD: td, DEMO: demo, CSV: csv };
})(window.App);
