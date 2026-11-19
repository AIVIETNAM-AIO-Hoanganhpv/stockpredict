/* =========================================================
 * stockpredict.js — Kết nối GreenView với công cụ dự đoán StockPredict (thư mục co_phieu/)
 *
 *  • Nguồn giá "SP": giá cổ phiếu VN do Python lấy hộ (trình duyệt bị chặn khi gọi thẳng API Vietcap).
 *      - window.GV_DATA: dữ liệu nhúng sẵn (web app Streamlit) {ma, bars, ke_hoach, tin_hieu}
 *      - window.GV_API : địa chỉ máy chủ trên máy (co_phieu/chay_greenview.bat), "" = cùng địa chỉ trang
 *  • Chỉ báo "Khuyến nghị StockPredict": vùng mua, cắt lỗ, chốt lời, ngày chốt lời dự kiến,
 *    các lần báo Mua trong quá khứ và kết quả.
 *  • Chiến lược "StockPredict — Dự đoán xu hướng": cùng quy tắc đã kiểm định của công cụ
 *    (trọng số động lượng, ngưỡng 50, khung lớn tăng, cắt lỗ 0,5 ATR dưới đáy hồi, chốt lời 3R, giữ ≤ 60 nến).
 * ========================================================= */
(function (App) {
  'use strict';
  const T = App.ta, DEFS = App.INDICATORS, isN = T.isN, N = NaN;
  const hasData = () => !!(window.GV_DATA && window.GV_DATA.bars);
  const hasApi = () => window.GV_API != null;
  const api = (path) => (window.GV_API || '') + path;

  /* ---------------- Dữ liệu ---------------- */
  const SP = App.sp = { goi: {}, dang: {} };
  if (hasData()) SP.goi[window.GV_DATA.ma] = window.GV_DATA;

  async function daily(sym, fresh) {
    const g = SP.goi[sym];
    if (g && g.bars && !fresh) return g.bars;
    if (!hasApi()) throw new Error(`Chưa có dữ liệu ${sym}. Mở GreenView bằng co_phieu/chay_greenview.bat để xem mọi mã VN, hoặc chọn mã trong web app.`);
    const j = await App.fetchJSON(api('/api/gia?ma=' + encodeURIComponent(sym)), { timeout: 60000 });
    if (j.loi) throw new Error(j.loi);
    SP.goi[sym] = Object.assign(SP.goi[sym] || {}, { ma: sym, bars: j.bars });
    return j.bars;
  }

  // Kế hoạch + tín hiệu quá khứ: nhúng sẵn, hoặc hỏi máy chủ (chạy nền, vẽ lại khi có)
  SP.keHoach = function (sym) {
    const g = SP.goi[sym];
    if (g && g.ke_hoach) return g;
    if (hasApi() && !SP.dang[sym]) {
      SP.dang[sym] = true;
      App.fetchJSON(api('/api/khuyen_nghi?ma=' + encodeURIComponent(sym)), { timeout: 120000 })
        .then(j => { SP.goi[sym] = Object.assign(SP.goi[sym] || { ma: sym }, j); if (App.chart && App.chart.D) App.chart.renderIndicators(); })
        .catch(e => { SP.goi[sym] = Object.assign(SP.goi[sym] || { ma: sym }, { ke_hoach: { loi: e.message } }); });
    }
    return null;
  };

  const sp = {
    label: 'StockPredict (giá VN)',
    short: 'SP',
    tfs: ['1D', '1W', '1M'],
    canLoadMore: false,
    hint: 'Giá cổ phiếu VN do công cụ dự đoán lấy hộ (Vietcap). VD: FPT, HPG, VCB, VNINDEX — giá theo đồng',
    normalize: s => s.toUpperCase().replace(/[^A-Z0-9]/g, ''),
    async fetchBars(sym, tf, beforeTime, fresh) {
      if (beforeTime) return [];
      const d = (await daily(sym, fresh)).map(b => ({ ...b }));
      return tf === '1W' ? App.aggregate(d, 604800) : tf === '1M' ? App.aggregateMonth(d) : d;
    },
    live(sym, tf, onBar) {
      if (!hasApi()) { App.setStatus('idle', hasData() ? `Dữ liệu StockPredict lúc ${window.GV_DATA.luc || ''}` : 'Dữ liệu tĩnh'); return () => {}; }
      let stopped = false;
      const id = setInterval(async () => {
        if (stopped) return;
        try { (await sp.fetchBars(sym, tf, null, true)).slice(-2).forEach(onBar); App.setStatus('live', 'StockPredict — cập nhật mỗi phút'); }
        catch (e) { App.setStatus('warn', 'Không cập nhật được giá: ' + e.message); }
      }, 60000);
      App.setStatus('live', 'StockPredict — cập nhật mỗi phút');
      return () => { stopped = true; clearInterval(id); };
    },
    async quotes(syms) {
      const out = {};
      await Promise.all(syms.map(async s => {
        try {
          let d = SP.goi[s] && SP.goi[s].bars;
          if (!d && hasApi()) d = (await App.fetchJSON(api('/api/gia?ma=' + encodeURIComponent(s) + '&n=3'), { timeout: 60000 })).bars;
          if (!d || !d.length) return;
          const a = d[d.length - 1], b = d[d.length - 2] || a;
          out[s] = { price: a.close, chg: (a.close / b.close - 1) * 100 };
        } catch (e) { /* bỏ qua */ }
      }));
      return out;
    }
  };
  // Đặt nguồn StockPredict lên đầu danh sách
  App.sources = Object.assign({ SP: sp }, App.sources);
  // Có máy chủ trên máy: nguồn "Cổ phiếu Việt Nam" bị trình duyệt chặn thì lấy giá qua StockPredict
  if (hasApi()) {
    const vn = App.sources.VN, f0 = vn.fetchBars.bind(vn), q0 = vn.quotes.bind(vn);
    vn.fetchBars = async (sym, tf, before) => {
      try { return await f0(sym, tf, before); }
      catch (e) {
        if (before || !sp.tfs.includes(tf)) throw e;
        const k = App.isIndex(sym) ? 1 : 0.001;   // nguồn VN tính nghìn đồng
        return (await sp.fetchBars(sym, tf)).map(b => ({ ...b, open: b.open * k, high: b.high * k, low: b.low * k, close: b.close * k }));
      }
    };
    vn.quotes = async syms => {
      const out = await q0(syms).catch(() => ({})), thieu = syms.filter(s => !out[s]);
      if (thieu.length) { const r = await sp.quotes(thieu); thieu.forEach(s => { if (r[s]) out[s] = { price: App.isIndex(s) ? r[s].price : r[s].price / 1000, chg: r[s].chg }; }); }
      return out;
    };
  }

  /* ---------------- Tiện ích thời gian ---------------- */
  // Nến cuối cùng có thời gian <= t (t là đầu ngày, cộng gần 1 ngày để khớp cả nguồn có cộng múi giờ)
  function idx(D, t) {
    const x = t + 86399; let lo = 0, hi = D.n - 1, r = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (D.t[m] <= x) { r = m; lo = m + 1; } else hi = m - 1; }
    return r;
  }
  // Vị trí (có thể ở tương lai) của ngày t trên trục nến
  function idxFuture(D, t) {
    const last = D.t[D.n - 1];
    if (t <= last) return idx(D, t);
    const step = App.TF[App.state.tf] || 86400, days = (t - last) / 86400;
    return D.n - 1 + (step <= 86400 ? days * 5 / 7 * (86400 / step) : days * 86400 / step);
  }
  // Hệ số đổi đơn vị giá (nguồn VN tính nghìn đồng, SP/TCBS tính đồng)
  function heSo(D, g) {
    const a = D.c[D.n - 1], b = g.bars && g.bars.length ? g.bars[g.bars.length - 1].close : null;
    if (!b || !a) return 1;
    for (const k of [1, 0.001, 1000]) if (Math.abs(a / (b * k) - 1) < 0.2) return k;
    return null;
  }

  /* ---------------- Chỉ báo: Khuyến nghị StockPredict ---------------- */
  const MAU = { 'Mua': '#089981', 'Gần đủ điều kiện': '#2962ff', 'Theo dõi': '#ff9800', 'Không mua': '#787b86' };
  DEFS.sp_plan = {
    id: 'sp_plan', name: 'Khuyến nghị StockPredict', cat: 'stockpredict', overlay: true, plots: [], levels: [],
    inputs: [['kh', 'Hiện kế hoạch hiện tại', true, 'bool'], ['qk', 'Hiện các lần báo Mua trong quá khứ', true, 'bool'], ['tg', 'Hiện ngày chốt lời dự kiến', true, 'bool']],
    calc(D, I) {
      const sym = App.state.sym, g = SP.goi[sym] && SP.goi[sym].ke_hoach ? SP.goi[sym] : SP.keHoach(sym);
      if (!g) return { draw(gx, X) { X.label(gx, X.W / 2, 22, hasApi() ? `StockPredict: đang phân tích ${sym}…` : `StockPredict: chưa có khuyến nghị cho ${sym}`, '#787b86'); } };
      const k = heSo(D, g);
      if (k == null) return {};
      const kh = g.ke_hoach || {}, mk = [], tr = [];
      if (I.qk) (g.tin_hieu || []).forEach(s => {
        const i = idx(D, s.t_mua), j = idx(D, s.t_ra); if (i < 0) return;
        const ok = s.lai_pct > 0;
        mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: '#2962ff', text: 'Mua ' + (s.diem != null ? Math.round(s.diem) : '') });
        if (j >= 0 && s.ket_qua !== 'Đang giữ') mk.push({ i: j, pos: 'aboveBar', shape: 'circle', color: ok ? '#089981' : '#f23645', text: `${s.ket_qua} ${s.lai_pct > 0 ? '+' : ''}${s.lai_pct}%` });
        tr.push({ i, j: j < 0 ? D.n - 1 : j, sl: s.cat_lo * k, tp: s.chot_loi * k, ok });
      });
      return {
        markers: mk,
        draw(gx, X) {
          tr.forEach(t => {
            const x1 = X.x(t.i), x2 = X.x(t.j);
            X.seg(gx, x1, X.y(t.tp), x2, X.y(t.tp), 'rgba(8,153,129,0.8)', [3, 3]);
            X.seg(gx, x1, X.y(t.sl), x2, X.y(t.sl), 'rgba(242,54,69,0.8)', [3, 3]);
          });
          if (!I.kh) return;
          if (kh.loi) { X.label(gx, X.W / 2, 22, 'StockPredict: ' + kh.loi, '#f23645'); return; }
          if (!kh.muc) return;
          const n = D.n - 1, xa = X.x(Math.max(0, n - 25)), xb = X.W, col = MAU[kh.muc] || '#787b86';
          if (kh.vung && kh.vung[0] != null) X.box(gx, xa, X.y(kh.vung[1] * k), xb, X.y(kh.vung[0] * k), 'rgba(41,98,255,0.12)', 'rgba(41,98,255,0.5)');
          if (kh.gia_mua) X.hline(gx, xa, xb, X.y(kh.gia_mua * k), '#2962ff', 'Mua ' + App.fmtPrice(kh.gia_mua * k), 1.5);
          if (kh.cat_lo) X.hline(gx, xa, xb, X.y(kh.cat_lo * k), '#f23645', 'Cắt lỗ ' + App.fmtPrice(kh.cat_lo * k), 1.5);
          if (kh.chot_loi) X.hline(gx, xa, xb, X.y(kh.chot_loi * k), '#089981', 'Chốt lời ' + App.fmtPrice(kh.chot_loi * k) + (kh.rr ? ` (R:R ${kh.rr})` : ''), 1.5);
          if (I.tg && kh.du_kien) {
            const xd = X.x(idxFuture(D, kh.du_kien));
            if (xd != null) {
              X.seg(gx, xd, 30, xd, X.H - 30, '#089981', [6, 4], 1.5);
              const d = new Date(kh.du_kien * 1000), p = v => String(v).padStart(2, '0');
              X.label(gx, xd, 40, `Dự kiến chốt lời ${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)}`, '#089981');
            }
          }
          const dinh = kh.dinh && kh.dinh.muc && kh.dinh.muc !== 'Chưa có đỉnh' ? ` · Đỉnh: ${kh.dinh.muc}` : '';
          X.label(gx, Math.min(X.W - 150, Math.max(150, X.W / 2)), 18, `StockPredict: ${kh.muc} · điểm ${kh.diem}${dinh}`, col);
        }
      };
    }
  };

  /* ---------------- Chỉ báo: Đỉnh/đáy thật (để so với tín hiệu) ---------------- */
  // Đỉnh/đáy "thật" = điểm cao/thấp nhất trong ±N nến VÀ cách đáy/đỉnh trước ≥ X% (zigzag).
  // Chỉ dùng để NHÌN LẠI QUÁ KHỨ: điểm gần cuối biểu đồ chưa được xác nhận (cần N nến sau đó).
  DEFS.sp_dinh_day = {
    id: 'sp_dinh_day', name: 'Đỉnh/đáy thật (để so sánh)', cat: 'stockpredict', overlay: true, plots: [], levels: [],
    inputs: [['n', 'Số nến mỗi bên', 10, 'int'], ['pct', 'Biên độ tối thiểu (%)', 8, 'float'], ['nhan', 'Ghi giá & % trên nhãn', true, 'bool']],
    calc(D, I) {
      const n = Math.max(2, I.n | 0), mk = [], dd = [];
      for (let i = n; i < D.n - n; i++) {
        let hi = true, lo = true;
        for (let j = i - n; j <= i + n; j++) { if (j === i) continue; if (D.h[j] > D.h[i]) hi = false; if (D.l[j] < D.l[i]) lo = false; }
        if (hi) dd.push({ i, p: D.h[i], k: 'H' }); if (lo) dd.push({ i, p: D.l[i], k: 'L' });
      }
      // gộp thành zigzag xen kẽ, bỏ sóng nhỏ hơn X%
      const z = [];
      dd.forEach(x => {
        const t = z[z.length - 1];
        if (!t) return z.push(x);
        if (t.k === x.k) { if ((x.k === 'H' && x.p > t.p) || (x.k === 'L' && x.p < t.p)) z[z.length - 1] = x; return; }
        if (Math.abs(x.p / t.p - 1) * 100 >= I.pct) z.push(x);
      });
      z.forEach((x, k) => {
        const tr = z[k - 1], ch = tr ? (x.p / tr.p - 1) * 100 : null;
        mk.push({ i: x.i, pos: x.k === 'H' ? 'aboveBar' : 'belowBar', shape: 'square', color: x.k === 'H' ? '#f23645' : '#089981',
          text: (x.k === 'H' ? 'ĐỈNH' : 'ĐÁY') + (I.nhan ? ` ${App.fmtPrice(x.p)}${ch != null ? ` (${ch > 0 ? '+' : ''}${ch.toFixed(0)}%)` : ''}` : '') });
      });
      return { markers: mk, draw(g, X) { for (let k = 1; k < z.length; k++) X.seg(g, X.x(z[k - 1].i), X.y(z[k - 1].p), X.x(z[k].i), X.y(z[k].p), 'rgba(255,152,0,0.7)', [4, 3], 1.5); } };
    }
  };

  /* ---------------- Chiến lược: Dự đoán xu hướng (bản JS của quy tắc đã kiểm định) ---------------- */
  const sign = x => (x > 0 ? 1 : x < 0 ? -1 : 0), kep = x => Math.max(-1, Math.min(1, x));

  // Điểm động lượng một khung (giống Pine "Động lượng (đã kiểm định)") — chỉ dùng dữ liệu đến từng nến
  App.spScore = function (D, kp = 3) {
    const n = D.n, a = T.atr(D, 14);
    const m = T.sub(T.ema(D.c, 12), T.ema(D.c, 26)), sg = T.ema(m, 9), hist = T.sub(m, sg);
    const kS = T.sma(T.stoch(D.c, D.h, D.l, 14), 3), dS = T.sma(kS, 3);
    const mf = T.mfi(D, 14), dm = T.dmi(D, 14, 14), vol30 = T.sum(D.v, 30);
    const diem = T.arr(n), xh = T.arr(n, 0), h1Bar = T.arr(n, -1);
    let h1 = N, h2 = N, l1 = N, l2 = N, hb = -1, chuaH = N, chuaL = N, xu = 0, haO = N, haCp = N;
    const xanh = [], rd = [], rt = [], cross = [];
    for (let i = 0; i < n; i++) {
      // đỉnh/đáy xác nhận sau kp nến
      const p = i - kp;
      if (p >= kp) {
        let isH = true, isL = true;
        for (let j = p - kp; j <= p + kp; j++) {
          if (j === p) continue;
          if (j < p ? D.h[j] >= D.h[p] : D.h[j] > D.h[p]) isH = false;
          if (j < p ? D.l[j] <= D.l[p] : D.l[j] < D.l[p]) isL = false;
        }
        if (isH) { h2 = h1; h1 = D.h[p]; hb = p; chuaH = D.h[p]; }
        if (isL) { l2 = l1; l1 = D.l[p]; chuaL = D.l[p]; }
      }
      h1Bar[i] = hb;
      // LEVEL 1 – cấu trúc đỉnh/đáy
      const bangDinh = isN(h2) && Math.abs(h1 - h2) <= 0.01 * Math.max(h1, h2), bangDay = isN(l2) && Math.abs(l1 - l2) <= 0.01 * Math.max(l1, l2);
      const vSw = !isN(h2) || !isN(l2) ? 0 : bangDinh && bangDay ? 0 : h1 > h2 && l1 > l2 ? 1 : h1 < h2 && l1 < l2 ? -1 : 0;
      // MACD
      cross.push(i && isN(m[i - 1]) && isN(sg[i - 1]) && sign(m[i] - sg[i]) !== sign(m[i - 1] - sg[i - 1]) ? 1 : 0);
      let soCat = 0; for (let j = Math.max(0, i - 19); j <= i; j++) soCat += cross[j];
      const vMacd = !isN(hist[i]) ? 0 : soCat >= 4 ? 0 : sign(hist[i]) * (i && Math.abs(hist[i]) > Math.abs(hist[i - 1]) ? 1 : 0.5);
      // Heikin Ashi
      const haC = (D.o[i] + D.h[i] + D.l[i] + D.c[i]) / 4;
      haO = isN(haO) ? (haO + haCp) / 2 : (D.o[i] + D.c[i]) / 2; haCp = haC;
      const haH = Math.max(D.h[i], haO, haC), haL = Math.min(D.l[i], haO, haC), ai = isN(a[i]) ? a[i] : 0;
      xanh.push(haC > haO); rd.push(Math.min(haO, haC) - haL <= 0.05 * ai); rt.push(haH - Math.max(haO, haC) <= 0.05 * ai);
      let vHa = 0;
      if (i >= 2) {
        const x3 = xanh[i] && xanh[i - 1] && xanh[i - 2], d3 = !xanh[i] && !xanh[i - 1] && !xanh[i - 2];
        vHa = x3 && rd[i] && rd[i - 1] && rd[i - 2] ? 1 : d3 && rt[i] && rt[i - 1] && rt[i - 2] ? -1 : x3 ? 0.5 : d3 ? -0.5 : 0;
      }
      // Stochastic
      let vSt = 0;
      if (i && isN(kS[i]) && isN(dS[i]) && isN(kS[i - 1]) && isN(dS[i - 1]))
        vSt = kS[i - 1] <= dS[i - 1] && kS[i] > dS[i] && kS[i] < 50 ? 1 : kS[i - 1] >= dS[i - 1] && kS[i] < dS[i] && kS[i] > 50 ? -1 : kS[i] > 80 ? -0.3 : kS[i] < 20 ? 0.3 : 0.5 * sign(kS[i] - dS[i]);
      // MFI
      const coKL = vol30[i] > 0 && isN(mf[i]) && i >= 3 && isN(mf[i - 3]);
      const vMf = !coKL ? 0 : mf[i] > 80 ? -0.7 : mf[i] < 20 ? 0.7 : kep(kep((mf[i] - mf[i - 3]) / 15) * 0.6 + (mf[i] > 50 ? 0.4 : -0.4));
      // ADX
      const ad = dm.adx[i], vAdx = isN(ad) && ad >= 25 ? sign(dm.plus[i] - dm.minus[i]) : 0;
      // SMC – phá cấu trúc
      if (isN(chuaH) && D.c[i] > chuaH) { xu = 1; chuaH = N; }
      else if (isN(chuaL) && D.c[i] < chuaL) { xu = -1; chuaL = N; }
      xh[i] = xu;
      const w = 1 + 2.5 + 1 + 1.5 + (coKL ? 1.5 : 0) + 1.5 + (xu ? 1 : 0);
      let d = 100 * (vSw + vMacd * 2.5 + vHa + vSt * 1.5 + (coKL ? vMf * 1.5 : 0) + vAdx * 1.5 + xu) / w;
      if (isN(ad) && ad < 20) d *= 0.7;
      diem[i] = i < 35 ? N : d;
    }
    return { diem, xh, atr: a, h1Bar };
  };

  // Khung lớn: tự chọn theo khung đang xem; trả về điểm & xu hướng của nến khung lớn ĐÃ ĐÓNG
  function khungLon(D) {
    const tf = App.TF[App.state.tf] || 86400;
    const bars = []; for (let i = 0; i < D.n; i++) bars.push({ time: D.t[i], open: D.o[i], high: D.h[i], low: D.l[i], close: D.c[i], volume: D.v[i] });
    const big = tf <= 3600 ? App.aggregate(bars, 14400) : tf < 86400 ? App.aggregate(bars, 86400) : tf < 604800 ? App.aggregate(bars, 604800) : tf < 2592000 ? App.aggregateMonth(bars) : null;
    if (!big || big.length < 40) return null;
    const B = T.prep(big), s = App.spScore(B), d = T.arr(D.n), x = T.arr(D.n, 0);
    let w = 0;
    for (let i = 0; i < D.n; i++) {
      while (w + 1 < B.n && B.t[w + 1] <= D.t[i]) w++;
      if (w >= 1) { d[i] = s.diem[w - 1]; x[i] = s.xh[w - 1]; }
    }
    return { diem: d, xh: x };
  }

  App.spStrategy = function (D, I) {
    const s = App.spScore(D), L = khungLon(D), n = D.n;
    const tong = s.diem.map((d, i) => (L && isN(L.diem[i]) ? (2 * d + L.diem[i]) / 3 : d));
    const xh = tong.map((t, i) => (isN(t) && t >= I.ng && s.diem[i] > 0 && (!I.loc || (L ? L.xh[i] === 1 : true)) ? 1 : 0));
    const opt = App.settings.bt || {}, cap0 = opt.capital || 10000, fee = (I.phi != null ? I.phi : 0.15) / 100, thue = (I.thue || 0) / 100;
    let cash = cap0, peak = cap0, mdd = 0, pos = null;
    const trades = [], equity = [], mk = [];
    for (let i = 0; i < n; i++) {
      // vào lệnh ở giá mở cửa sau nến có tín hiệu
      if (!pos && i && xh[i - 1] === 1 && (i < 2 || xh[i - 2] !== 1)) {
        const j = i - 1, c = D.c[j], a = s.atr[j], hb = s.h1Bar[j];
        let low = N; if (hb >= 0) { low = Infinity; for (let q = hb; q <= j; q++) low = Math.min(low, D.l[q]); }
        const sl = isN(low) && low - 0.5 * a < c ? low - 0.5 * a : c - a, tp = c + I.r * (c - sl), ep = D.o[i];
        if (isN(a) && sl < ep && ep < tp) {
          pos = { ei: i, ep, sl, tp, qty: cash * (1 - fee) / ep };
          mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: '#2962ff', text: 'Mua ' + Math.round(tong[j]) });
        }
      }
      if (pos) {
        let xp = null, why = '';
        if (D.l[i] <= pos.sl) { xp = i > pos.ei ? Math.min(D.o[i], pos.sl) : pos.sl; why = 'Cắt lỗ'; }
        else if (D.h[i] >= pos.tp) { xp = i > pos.ei ? Math.max(D.o[i], pos.tp) : pos.tp; why = 'Chốt lời'; }
        else if (i - pos.ei + 1 >= I.giu) { xp = D.c[i]; why = 'Hết ' + I.giu + ' nến'; }
        if (xp != null) {
          const val = pos.qty * xp * (1 - fee - thue), pnl = val - cash;
          trades.push({ side: 'Mua', ei: pos.ei, xi: i, ep: pos.ep, xp, pnl, pct: (val / cash - 1) * 100, why });
          mk.push({ i, pos: 'aboveBar', shape: 'circle', color: pnl > 0 ? '#089981' : '#f23645', text: why });
          cash = val; pos = null;
        }
      }
      const eq = pos ? pos.qty * D.c[i] : cash;
      equity.push(eq); peak = Math.max(peak, eq); mdd = Math.max(mdd, (peak - eq) / peak * 100);
    }
    if (pos) { const xp = D.c[n - 1], val = pos.qty * xp * (1 - fee - thue); trades.push({ side: 'Mua', ei: pos.ei, xi: n - 1, ep: pos.ep, xp, pnl: val - cash, pct: (val / cash - 1) * 100, why: 'Đang mở' }); cash = val; }
    const wins = trades.filter(t => t.pnl > 0), loss = trades.filter(t => t.pnl <= 0);
    const gp = wins.reduce((a, t) => a + t.pnl, 0), gl = -loss.reduce((a, t) => a + t.pnl, 0);
    const bt = { trades, equity, net: cash - cap0, netPct: (cash / cap0 - 1) * 100, n: trades.length, winRate: trades.length ? wins.length / trades.length * 100 : 0,
      pf: gl ? gp / gl : gp ? Infinity : 0, mdd, avg: trades.length ? (cash - cap0) / trades.length : 0, buyHold: (D.c[n - 1] / D.c[0] - 1) * 100,
      note: `Quy tắc của công cụ dự đoán: vào lệnh giá mở cửa nến sau tín hiệu, thoát khi chạm cắt lỗ / chốt lời ${I.r}R / hết ${I.giu} nến. Phí ${I.phi}%/chiều, thuế bán ${I.thue}%. Kiểm định 2006–2026 trên ~900 mã: chưa chắc tốt hơn mua ngẫu nhiên.` };
    return { markers: mk, backtest: bt, tong };
  };

  DEFS.st_stockpredict = {
    id: 'st_stockpredict', name: 'StockPredict — Dự đoán xu hướng', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['ng', 'Ngưỡng điểm (đã kiểm định: 50)', 50, 'float'], ['loc', 'Chỉ mua khi khung lớn tăng', true, 'bool'], ['r', 'Chốt lời = k × rủi ro', 3, 'float'],
      ['giu', 'Giữ tối đa (nến)', 60, 'int'], ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) { const r = App.spStrategy(D, I); return { markers: r.markers, backtest: r.backtest }; }
  };
})(window.App);
