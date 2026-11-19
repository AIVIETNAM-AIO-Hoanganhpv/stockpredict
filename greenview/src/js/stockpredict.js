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

  /* ---------------- Chỉ báo: Pha thị trường (chu kỳ) ---------------- */
  DEFS.sp_pha = {
    id: 'sp_pha', name: 'Pha thị trường VN (chu kỳ)', cat: 'stockpredict', overlay: true, plots: [], levels: [],
    inputs: [['op', 'Độ đậm nền (%)', 18, 'int']],
    calc(D, I) {
      const P = window.GV_PHA || [];
      if (!P.length) return { draw(g, X) { X.label(g, X.W / 2, 22, 'Chưa có dữ liệu pha – chạy quét toàn thị trường trong StockPredict', '#787b86'); } };
      const seg = [];
      P.forEach(([t, pha, mau]) => {
        const ts = Date.parse(t) / 1000, i = idx(D, ts); if (i < 0) return;
        const s = seg[seg.length - 1];
        if (s && s.pha === pha) s.j = i; else seg.push({ i, j: i, pha, mau });
      });
      const a = Math.max(0, Math.min(100, I.op)) / 100, hex = c => { const n = parseInt(c.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; };
      const cuoi = P[P.length - 1];
      return { draw(g, X) {
        const nua = Math.abs((X.x(1) || 0) - (X.x(0) || 0)) / 2;   // nửa độ rộng 1 nến (toạ độ số lẻ không dùng được)
        seg.forEach(s => { const a1 = X.x(s.i), a2 = X.x(s.j); if (a1 == null || a2 == null) return; X.box(g, a1 - nua, 0, a2 + nua, X.H, hex(s.mau)); });
        X.label(g, Math.min(X.W - 120, Math.max(120, X.W / 2)), 40, `Thị trường: pha ${cuoi[1]}`, cuoi[2]);
      } };
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


  /* ======================================================================
   * Chiến lược theo khoá học: "Công thức 2 đường MA (LEVEL 1)" và "MACD + Sto"
   * Lệnh vị thế 30% vốn + lệnh xác nhận 70% vốn (khi lệnh vị thế có lãi), mỗi lệnh có cắt lỗ riêng.
   * Tín hiệu ở giá đóng cửa nến, khớp giá mở cửa nến sau; cắt lỗ khớp min(giá mở, giá cắt lỗ).
   * ====================================================================== */
  function moPhongLo(D, R, I) {
    // R: { vt(i)->{stop} | null, xn(i, fillVT)->{stop} | null, banPhan(i)->bool, banHet(i)->bool, tenBan }
    const n = D.n, cap0 = (App.settings.bt || {}).capital || 10000, phi = (I.phi != null ? I.phi : 0.15) / 100, thue = (I.thue || 0) / 100;
    let cash = cap0, peak = cap0, mdd = 0, lo = [], cho = null, daBanPhan = false, fillVT = null, tpChung = null;
    const trades = [], equity = [], mk = [];
    const dong = (l, i, px, phan, why) => {
      const q = l.q * phan, val = q * px * (1 - phi - thue), von = q * l.ep * (1 + phi);
      cash += val; l.q -= q;
      trades.push({ side: 'Mua', ei: l.ei, xi: i, ep: l.ep, xp: px, pnl: val - von, pct: (val / von - 1) * 100, why });
    };
    for (let i = 0; i < n; i++) {
      // 1) thực hiện lệnh chờ ở giá mở cửa
      if (cho) {
        const o = D.o[i];
        if (cho.k === 'het' && lo.length) { lo.forEach(l => dong(l, i, o, 1, cho.why || R.tenBan || 'Bán hết')); lo = []; mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: '#f23645', text: cho.why ? 'Hết hạn giữ' : 'Bán hết' }); }
        else if (cho.k === 'phan' && lo.length) { lo.forEach(l => dong(l, i, o, I.phan / 100, `Bán ${I.phan}%`)); mk.push({ i, pos: 'aboveBar', shape: 'circle', color: '#ff9800', text: `Bán ${I.phan}%` }); }
        else if ((cho.k === 'vt' || cho.k === 'xn') && o > cho.stop && !(cho.tp && o >= cho.tp)) {
          const eq = cash + lo.reduce((a, l) => a + l.q * o, 0), tien = Math.min(cash, eq * (cho.k === 'vt' ? 0.3 : 0.7));
          if (tien > 0) {
            const q = tien / (o * (1 + phi)); cash -= q * o * (1 + phi);
            lo.push({ ei: i, ep: o, q, stop: cho.stop, k: cho.k, tp: R.tpChiVe ? null : (cho.k === 'vt' ? cho.tp : tpChung) });
            if (cho.k === 'vt') { fillVT = o; daBanPhan = false; tpChung = cho.tp || null; if (cho.tp && R.veTp) R.veTp.push({ i, tp: cho.tp, j: null }); }
            mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: cho.k === 'vt' ? '#2962ff' : '#089981', text: cho.k === 'vt' ? 'Vị thế 30%' : 'Xác nhận 70%' });
          }
        }
        lo = lo.filter(l => l.q > 1e-12); cho = null;
      }
      // 2) cắt lỗ trong phiên (mỗi lệnh 1 mức)
      lo.forEach(l => { if (D.l[i] < l.stop) { dong(l, i, Math.min(D.o[i], l.stop), 1, 'Cắt lỗ'); mk.push({ i, pos: 'belowBar', shape: 'square', color: '#f23645', text: 'Cắt lỗ' }); } });
      lo = lo.filter(l => l.q > 1e-12);
      // chốt lời tại mục tiêu (nếu có): giá cao trong phiên chạm mục tiêu
      const tpHit = lo.find(l => l.tp && D.h[i] >= l.tp);
      if (tpHit) { const px = Math.max(D.o[i], tpHit.tp); lo.forEach(l => dong(l, i, px, 1, 'Chốt lời Fibo')); lo = [];
        mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: '#089981', text: 'Chốt lời Fibo' });
        if (R.veTp && R.veTp.length) R.veTp[R.veTp.length - 1].j = i; }
      if (!lo.length) { if (fillVT != null && R.veTp && R.veTp.length && R.veTp[R.veTp.length - 1].j == null) R.veTp[R.veTp.length - 1].j = i; fillVT = null; }
      // 3) tín hiệu ở giá đóng cửa → lệnh chờ phiên sau
      if (i < n - 1) {
        if (lo.length) {
          if (R.banHet(i)) cho = { k: 'het' };
          else if (R.giuToiDa && D.t[i] - D.t[Math.min(...lo.map(l => l.ei))] >= R.giuToiDa) cho = { k: 'het', why: 'Hết thời gian giữ tối đa' };
          else if (!daBanPhan && R.banPhan && R.banPhan(i)) { cho = { k: 'phan' }; daBanPhan = true; }
          else if (!daBanPhan && fillVT != null && !lo.some(l => l.k === 'xn')) { const x = R.xn(i, fillVT); if (x) cho = { k: 'xn', stop: x.stop }; }
        } else { const v = R.vt(i); if (v) cho = { k: 'vt', stop: v.stop, tp: v.tp || null }; }
      }
      const eq = cash + lo.reduce((a, l) => a + l.q * D.c[i], 0);
      equity.push(eq); peak = Math.max(peak, eq); mdd = Math.max(mdd, (peak - eq) / peak * 100);
    }
    if (lo.length) lo.forEach(l => dong(l, n - 1, D.c[n - 1], 1, 'Đang mở'));
    const wins = trades.filter(t => t.pnl > 0), loss = trades.filter(t => t.pnl <= 0);
    const gp = wins.reduce((a, t) => a + t.pnl, 0), gl = -loss.reduce((a, t) => a + t.pnl, 0);
    return { markers: mk, backtest: { trades, equity, net: cash - cap0, netPct: (cash / cap0 - 1) * 100, n: trades.length,
      winRate: trades.length ? wins.length / trades.length * 100 : 0, pf: gl ? gp / gl : gp ? Infinity : 0, mdd,
      avg: trades.length ? (cash - cap0) / trades.length : 0, buyHold: (D.c[n - 1] / D.c[0] - 1) * 100, note: R.note } };
  }

  // đáy gần nhất đã xác nhận (pivot k nến mỗi bên) thấp hơn giá; không có → đáy thấp nhất 10 nến
  function dayGanNhat(D, j, k = 3, xa = 60) {
    for (let i = j - k; i > Math.max(k - 1, j - xa); i--) {
      let ok = true; for (let q = i - k; q <= i + k; q++) if (q !== i && D.l[q] < D.l[i]) { ok = false; break; }
      if (ok && D.l[i] < D.c[j]) return D.l[i];
    }
    let m = Infinity; for (let q = Math.max(0, j - 9); q <= j; q++) m = Math.min(m, D.l[q]); return m < D.c[j] ? m : null;
  }

  // --- Công thức 2 đường MA (LEVEL 1) ---
  DEFS.st_level1 = {
    id: 'st_level1', name: 'Khoá học — Công thức 2 đường MA (LEVEL 1)', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['cap', 'Cặp MA (tín hiệu/điều kiện)', 'Tự chọn', 'sel', ['Tự chọn', '6/10', '10/20', '5/10']],
      ['phan', 'Bán khi đóng cửa dưới MA điều kiện (%)', 70, 'int'], ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) {
      const c = D.c, ma = { 5: T.sma(c, 5), 6: T.sma(c, 6), 10: T.sma(c, 10), 20: T.sma(c, 20) }, atr = T.atr(D, 14);
      const hug = T.sma(c.map((x, i) => Math.abs(x - ma[10][i])), 20).map((x, i) => x / atr[i]);
      const capTai = i => I.cap === 'Tự chọn' ? (hug[i] <= 0.874 ? [10, 20] : [6, 10]) : I.cap.split('/').map(Number);
      let cap = capTai(D.n - 1);
      const tren = (i, cp) => ma[cp[0]][i] > ma[cp[1]][i];
      const R = {
        vt(j) {
          if (j < 25) return null;
          cap = capTai(j); const [a, b] = cap, sg = ma[a], cd = ma[b];
          let cat = false; for (let x = Math.max(1, j - 2); x <= j; x++) { let deu = true; for (let q = x; q <= j; q++) if (!tren(q, cap)) deu = false; if (deu && tren(x, cap) && !tren(x - 1, cap)) cat = true; }
          if (!(cat && c[j] > D.o[j] && c[j] > sg[j] && c[j] > cd[j])) return null;
          let k = j; while (k >= Math.max(0, j - 30) && !(D.l[k] < cd[k])) k--;
          if (k < Math.max(0, j - 30)) return null;
          let sl = D.l[k]; while (k - 1 >= Math.max(0, j - 30) && D.l[k - 1] < cd[k - 1]) { k--; sl = Math.min(sl, D.l[k]); }
          return sl < c[j] ? { stop: sl } : null;
        },
        xn(m, fill) {
          const cd = ma[cap[1]];
          if (!(c[m] > D.o[m] && c[m] > fill && c[m] > cd[m])) return null;
          for (let q = m; q > Math.max(-1, m - 20); q--) if (D.l[q] <= cd[q] - 0.25 * (atr[q] || 0)) return { stop: D.l[q] };
          let mn = Infinity; for (let q = m; q > Math.max(-1, m - 20); q--) if (D.l[q] < cd[q]) mn = Math.min(mn, D.l[q]);
          return isFinite(mn) && mn < c[m] ? { stop: mn } : null;
        },
        banPhan: i => c[i] < ma[cap[1]][i],
        banHet: i => ma[cap[0]][i] < ma[cap[1]][i],
        tenBan: 'MA tín hiệu cắt xuống',
        note: `Công thức 2 MA (slide LEVEL 1): vị thế 30% khi MA tín hiệu cắt lên MA điều kiện + nến tăng trên 2 MA; xác nhận 70% khi có lãi + nến tăng; bán ${I.phan}% khi đóng dưới MA điều kiện, bán nốt khi MA cắt xuống. Kiểm định chứng khoán VN 2020–2026: khung D +4%, W +2,6%, M +5,2%/năm – thấp hơn mua & giữ.`
      };
      return moPhongLo(D, R, I);
    }
  };

  // --- MACD + Sto (Sto ngắn 8-5-3, Sto dài 13-13-5 theo bản của thầy) ---
  App.macdSto = function (D, nguong = 2) {
    const sto = (n, k, d) => { const K = T.sma(T.stoch(D.c, D.h, D.l, n), k); return [K, T.sma(K, d)]; };
    const [sk, sd] = sto(8, 5, 3), [lk, ld] = sto(13, 13, 5);
    const m = T.sub(T.ema(D.c, 12), T.ema(D.c, 26)), sg = T.ema(m, 9), hi = T.sub(m, sg);
    const cu = (a, b, i) => i > 0 && a[i] > b[i] && a[i - 1] <= b[i - 1], cd = (a, b, i) => cu(b, a, i);
    const gan = (fn, a, b, i, k) => { for (let q = 0; q < k; q++) if (fn(a, b, i - q)) return true; return false; };
    const S = { Mua1: [], Mua2: [], XN1: [], XN2: [], XN3: [], Ban: [] };
    for (let i = 0; i < D.n; i++) {
      const bull = D.c[i] > D.o[i], bear = D.c[i] < D.o[i];
      const sXU = cu(sk, sd, i), sXD = cd(sk, sd, i), lXU = cu(lk, ld, i), lXD = cd(lk, ld, i);
      const somMua = i > 1 && hi[i] < 0 && hi[i] > hi[i - 1] && hi[i - 1] > hi[i - 2], somBan = i > 1 && hi[i] > 0 && hi[i] < hi[i - 1] && hi[i - 1] < hi[i - 2];
      const chamMua = Math.abs(lk[i] - ld[i]) <= nguong || gan(cu, lk, ld, i, 2), chamBan = Math.abs(lk[i] - ld[i]) <= nguong || gan(cd, lk, ld, i, 2);
      const haiLen = (sXU && (lXU || (i && cu(lk, ld, i - 1)))) || (lXU && i && cu(sk, sd, i - 1));
      const haiXuong = (sXD && (lXD || (i && cd(lk, ld, i - 1)))) || (lXD && i && cd(sk, sd, i - 1));
      const macdLen = m[i] > sg[i] && gan(cu, m, sg, i, 10), macdXuong = m[i] < sg[i] && gan(cd, m, sg, i, 10);
      S.Mua1.push(bull && sXU && somMua); S.Mua2.push(bull && haiLen);
      S.XN1.push(bull && haiLen && somMua); S.XN2.push(bull && sXU && somMua && chamMua); S.XN3.push(bull && sXU && chamMua && macdLen);
      S.Ban.push(bear && ((sXD && somBan) || haiXuong || (sXD && somBan && chamBan) || (sXD && chamBan && macdXuong)));
    }
    return S;
  };
  DEFS.st_macdsto = {
    id: 'st_macdsto', name: 'Khoá học — MACD + Sto (8-5-3 · 13-13-5)', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['thoat', 'Cách bán', 'Bán hết khi có tín hiệu bán', 'sel', ['Bán hết khi có tín hiệu bán', 'Bán 70% rồi bán nốt', 'Bán khi MA10 cắt xuống MA20']],
      ['phan', 'Phần bán lần đầu (%)', 70, 'int'], ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) {
      const S = App.macdSto(D), ma10 = T.sma(D.c, 10), ma20 = T.sma(D.c, 20), m = T.sub(T.ema(D.c, 12), T.ema(D.c, 26)), sg = T.ema(m, 9);
      let lanBan = 0;
      const R = {
        vt: j => { if (!(S.Mua1[j] || S.Mua2[j])) return null; lanBan = 0; const sl = dayGanNhat(D, j); return sl != null ? { stop: sl } : null; },
        xn: (j, fill) => (S.XN1[j] || S.XN2[j] || S.XN3[j]) && D.c[j] > fill ? (x => x != null ? { stop: x } : null)(dayGanNhat(D, j)) : null,
        banPhan: I.thoat === 'Bán 70% rồi bán nốt' ? (i => S.Ban[i] && ++lanBan === 1) : null,
        banHet: i => I.thoat === 'Bán khi MA10 cắt xuống MA20' ? (ma10[i] < ma20[i] && ma10[i - 1] >= ma20[i - 1])
          : I.thoat === 'Bán 70% rồi bán nốt' ? ((S.Ban[i] && lanBan >= 1) || (m[i] < sg[i] && m[i - 1] >= sg[i - 1]))
            : S.Ban[i],
        tenBan: 'Tín hiệu bán',
        note: 'MACD + Sto (slide khoá học): vị thế 30% ở Mua 1/Mua 2, xác nhận 70% ở Xác nhận 1/2/3 khi có lãi; lệnh mua là nến tăng, bán là nến giảm. Kiểm định chứng khoán VN 2020–2026: khung D +3,1%, W −3%/năm – thua vào lệnh ngẫu nhiên.'
      };
      const r = moPhongLo(D, R, I);
      // đánh dấu thêm loại tín hiệu (không phải lệnh) để nhìn
      for (let i = 0; i < D.n; i++) {
        const ten = S.XN1[i] ? 'XN1' : S.XN2[i] ? 'XN2' : S.XN3[i] ? 'XN3' : S.Mua2[i] ? 'M2' : S.Mua1[i] ? 'M1' : '';
        if (ten && !r.markers.some(x => x.i === i + 1)) r.markers.push({ i, pos: 'belowBar', shape: 'circle', color: '#9598a1', text: ten });
      }
      return r;
    }
  };


  /* ======================================================================
   * Khoá học — ĐỒNG PHA NGÀY/TUẦN/THÁNG: vào lệnh theo khung NGÀY khi ngày, tuần, tháng cùng TĂNG;
   * giữ & bán theo tín hiệu bán MACD + Sto của khung TUẦN (lệnh tuần) hoặc THÁNG (lệnh tháng).
   * Một khung "TĂNG" khi đủ ≥ 2 trong 3 điều kiện: đỉnh/đáy sau cao hơn đỉnh/đáy trước · MACD trên đường tín hiệu ·
   * Sto dài (13-13-5) %K trên %D. (MA 80% và Heikin Ashi chỉ để tham khảo.)
   * ====================================================================== */
  function xuHuongTang(D, k) {
    // mảng true/false: khung (D là nến của khung đó) đang TĂNG tại từng nến
    const n = D.n, m = T.sub(T.ema(D.c, 12), T.ema(D.c, 26)), sg = T.ema(m, 9);
    const K = T.sma(T.stoch(D.c, D.h, D.l, 13), 13), Dd = T.sma(K, 5), up = new Array(n).fill(false);
    let h1 = N, h2 = N, l1 = N, l2 = N;
    for (let i = 0; i < n; i++) {
      const p = i - k;                     // đỉnh/đáy chỉ được xác nhận sau k nến
      if (p >= k) {
        let isH = true, isL = true;
        for (let q = p - k; q <= p + k; q++) { if (q === p) continue; if (D.h[q] > D.h[p]) isH = false; if (D.l[q] < D.l[p]) isL = false; }
        if (isH) { h2 = h1; h1 = D.h[p]; }
        if (isL) { l2 = l1; l1 = D.l[p]; }
      }
      const caoDan = isN(h2) && isN(l2) && h1 > h2 && l1 > l2;
      up[i] = (caoDan ? 1 : 0) + (m[i] > sg[i] ? 1 : 0) + (K[i] > Dd[i] ? 1 : 0) >= 2;   // đủ 2/3 điều kiện
    }
    return up;
  }
  // nến tuần/tháng dựng từ nến ngày + chỉ số nến ngày cuối của mỗi nến lớn (nến lớn cuối cùng có thể chưa xong)
  function khungLonTuNgay(D, loai) {
    const bars = []; for (let i = 0; i < D.n; i++) bars.push({ time: D.t[i], open: D.o[i], high: D.h[i], low: D.l[i], close: D.c[i], volume: D.v[i] });
    const big = loai === 'W' ? App.aggregate(bars, 604800) : App.aggregateMonth(bars), B = T.prep(big);
    const cuoi = new Array(B.n).fill(-1); let w = 0;
    for (let i = 0; i < D.n; i++) { while (w + 1 < B.n && B.t[w + 1] <= D.t[i]) w++; cuoi[w] = i; }
    return { B, cuoi };
  }
  App.dongPha = function (D) {
    const upD = xuHuongTang(D, 3), W = khungLonTuNgay(D, 'W'), M = khungLonTuNgay(D, 'M');
    const upW = xuHuongTang(W.B, 2), upM = xuHuongTang(M.B, 2);
    // trạng thái tuần/tháng tại ngày i = nến tuần/tháng ĐÃ XONG gần nhất (nến cuối của dữ liệu coi như chưa xong)
    const theoNgay = (X, up) => { const out = new Array(D.n).fill(false); let j = -1;
      for (let i = 0; i < D.n; i++) { while (j + 1 < X.B.n - 1 && X.cuoi[j + 1] <= i) j++; out[i] = j >= 0 && X.cuoi[j] <= i ? up[j] : false; } return out; };
    const tW = theoNgay(W, upW), tM = theoNgay(M, upM);
    // tín hiệu bán MACD + Sto trên nến tuần/tháng, thực hiện sau khi nến đó đóng (ngày cuối của nến)
    const banTai = X => { const S = App.macdSto(X.B), out = new Array(D.n).fill(false);
      for (let j = 0; j < X.B.n - 1; j++) if (S.Ban[j] && X.cuoi[j] >= 0) out[X.cuoi[j]] = true; return out; };
    return { upD, tW, tM, dongPha: upD.map((x, i) => x && tW[i] && tM[i]), banW: banTai(W), banM: banTai(M),
      cuoi: { D: upD[D.n - 1], W: upW[W.B.n - 2] ?? false, M: upM[M.B.n - 2] ?? false } };
  };

  // Mục tiêu chốt lời Fibo trên sóng của khung lệnh (W/M), tại ngày j: A đáy trước B, B đỉnh gần nhất (k=2, đã xác nhận),
  // C thấp nhất từ sau B đến j; hồi = (B−C)/(B−A) → 1.618 (<0,441) · 1.272 (<0,691) · 1.0; nâng mức nếu ≤ giá vào +1%.
  App.fiboSong = function (D, X, j, giaVao, k = 2, tlCoDinh = null) {
    let w = -1; for (let q = 0; q < X.B.n - 1; q++) if (X.cuoi[q] >= 0 && X.cuoi[q] <= j) w = q;
    if (w < 2 * k + 2) return null;
    const B_ = X.B; let ib = -1, ia = -1;
    for (let p = w - k; p >= k; p--) { let ok = true; for (let q = p - k; q <= p + k; q++) if (B_.h[q] > B_.h[p]) ok = false; if (ok) { ib = p; break; } }
    if (ib < 0) return null;
    for (let p = ib - 1; p >= k; p--) { let ok = true; for (let q = p - k; q <= Math.min(p + k, w); q++) if (B_.l[q] < B_.l[p]) ok = false; if (ok) { ia = p; break; } }
    if (ia < 0) return null;
    const thu = (A, B, C, moi) => {
      if (!(B > A && C >= A)) return null;
      const sau = (B - C) / (B - A); const tl0 = sau < 0.441 ? 1.618 : sau < 0.691 ? 1.272 : 1.0;
      for (const x of (tlCoDinh ? [tlCoDinh] : [1.0, 1.272, 1.618, 2.0, 2.618])) { if (!tlCoDinh && x < tl0) continue; const tp = C + x * (B - A); if (tp > giaVao * 1.01) return { tp, tl: x, sau, A, B, C, moi }; }
      return null;
    };
    let C = Infinity, ic = X.cuoi[ib];
    for (let q = X.cuoi[ib] + 1; q <= j; q++) if (D.l[q] < C) { C = D.l[q]; ic = q; }
    if (!isFinite(C)) C = B_.l[ib];
    const cu = C > B_.l[ia] ? thu(B_.l[ia], B_.h[ib], C, false) : null;
    if (cu) return cu;
    // sóng cũ hỏng (phá đáy A) hoặc quá nhỏ so với giá → đo SÓNG MỚI: A = đáy thấp nhất sau đỉnh cũ, B = đỉnh cao nhất sau đó, C = đáy hồi sau B
    const A = Math.min(C, B_.l[ia]); let ibd = ic, B = -Infinity;
    for (let q = Math.max(0, ic); q <= j; q++) if (D.h[q] > B) { B = D.h[q]; ibd = q; }
    let C2 = D.l[j]; for (let q = ibd; q <= j; q++) C2 = Math.min(C2, D.l[q]);
    return thu(A, B, C2, true);
  };

  DEFS.sp_dong_pha = {
    id: 'sp_dong_pha', name: 'Đồng pha Ngày / Tuần / Tháng', cat: 'stockpredict', overlay: true, plots: [], levels: [],
    inputs: [['op', 'Độ đậm nền (%)', 14, 'int']],
    calc(D, I) {
      if ((App.TF[App.state.tf] || 86400) !== 86400) return { draw(g, X) { X.label(g, X.W / 2, 22, 'Đồng pha: mở biểu đồ khung NGÀY (1N)', '#787b86'); } };
      const P = App.dongPha(D), a = Math.max(0, Math.min(100, I.op)) / 100;
      const ky = x => x ? 'TĂNG' : 'chưa tăng', c = P.cuoi, du = P.dongPha[D.n - 1];
      return { draw(g, X) {
        let i = 0; while (i < D.n) { if (!P.dongPha[i]) { i++; continue; } let j = i; while (j + 1 < D.n && P.dongPha[j + 1]) j++;
          const nua = Math.abs((X.x(1) || 0) - (X.x(0) || 0)) / 2, a1 = X.x(i), a2 = X.x(j); if (a1 != null && a2 != null) X.box(g, a1 - nua, 0, a2 + nua, X.H, `rgba(8,153,129,${a})`); i = j + 1; }
        X.label(g, Math.min(X.W - 170, Math.max(170, X.W / 2)), 62, `Ngày ${ky(c.D)} · Tuần ${ky(c.W)} · Tháng ${ky(c.M)} → ${du ? 'ĐỒNG PHA' : 'chưa đồng pha'}`, du ? '#089981' : '#787b86');
      } };
    }
  };

  DEFS.st_dongpha = {
    id: 'st_dongpha', name: 'Khoá học — Đồng pha N/T/Th: vào khung ngày, giữ tuần/tháng', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['lenh', 'Loại lệnh', 'Lệnh tuần', 'sel', ['Lệnh tuần', 'Lệnh tháng']],
      ['vao', 'Tín hiệu vào (khung ngày)', '2MA hoặc MACD+Sto', 'sel', ['2MA hoặc MACD+Sto', '2MA', 'MACD+Sto']],
      ['chot', 'Chốt lời', 'Fibonacci theo sóng tuần/tháng', 'sel', ['Fibonacci theo sóng tuần/tháng', 'Không (chỉ tín hiệu bán)']],
      ['ban', 'Cách bán', 'Bán hết khi có tín hiệu bán', 'sel', ['Bán hết khi có tín hiệu bán', 'Bán 70% rồi bán nốt']],
      ['phan', 'Phần bán lần đầu (%)', 70, 'int'], ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) {
      if ((App.TF[App.state.tf] || 86400) !== 86400) return { draw(g, X) { X.label(g, X.W / 2, 22, 'Chiến lược đồng pha: mở biểu đồ khung NGÀY (1N) – vào lệnh theo khung ngày', '#787b86'); } };
      const P = App.dongPha(D), S = App.macdSto(D), c = D.c, ma = { 6: T.sma(c, 6), 10: T.sma(c, 10), 20: T.sma(c, 20) }, atr = T.atr(D, 14);
      const hug = T.sma(c.map((x, i) => Math.abs(x - ma[10][i])), 20).map((x, i) => x / atr[i]);
      const cap = i => hug[i] <= 0.874 ? [10, 20] : [6, 10];
      const tren = (i, cp) => ma[cp[0]][i] > ma[cp[1]][i];
      const maLen = j => {   // MA tín hiệu cắt lên MA điều kiện trong ≤ 3 nến gần nhất và vẫn nằm trên (giống LEVEL 1)
        const cp = cap(j); let cat = false;
        for (let x = Math.max(1, j - 2); x <= j; x++) { let deu = true; for (let q = x; q <= j; q++) if (!tren(q, cp)) deu = false; if (deu && !tren(x - 1, cp)) cat = true; }
        return cat && c[j] > ma[cp[0]][j] && c[j] > ma[cp[1]][j]; };
      const banTF = I.lenh === 'Lệnh tháng' ? P.banM : P.banW;
      const KW = khungLonTuNgay(D, 'W'), KM = khungLonTuNgay(D, 'M'), veTp = [];
      const mDay = T.sub(T.ema(c, 12), T.ema(c, 26)), sDay = T.ema(mDay, 9);
      let lan = 0;
      const R = {
        vt(j) {
          if (j < 30 || !P.dongPha[j] || !(c[j] > D.o[j])) return null;
          const ok = (I.vao !== 'MACD+Sto' && maLen(j)) || (I.vao !== '2MA' && (S.Mua1[j] || S.Mua2[j]));
          if (!ok) return null; lan = 0; const sl = dayGanNhat(D, j); if (sl == null) return null;
          const fb = I.chot.startsWith('Fibonacci') ? App.fiboSong(D, I.lenh === 'Lệnh tháng' ? KM : KW, j, c[j]) : null;
          return { stop: sl, tp: fb ? fb.tp : null };
        },
        xn(j, fill) {
          if (!P.dongPha[j] || !(c[j] > D.o[j] && c[j] > fill)) return null;
          const ok = (I.vao !== 'MACD+Sto' && c[j] > ma[cap(j)[1]][j]) || (I.vao !== '2MA' && (S.XN1[j] || S.XN2[j] || S.XN3[j]));
          if (!ok) return null; const sl = dayGanNhat(D, j); return sl != null ? { stop: sl } : null;
        },
        banPhan: I.ban === 'Bán 70% rồi bán nốt' ? (i => banTF[i] && ++lan === 1) : null,
        banHet: i => I.ban === 'Bán 70% rồi bán nốt' ? (lan >= 1 && (banTF[i] || (mDay[i] < sDay[i] && mDay[i - 1] >= sDay[i - 1]))) : banTF[i],
        tenBan: `Tín hiệu bán MACD+Sto ${I.lenh === 'Lệnh tháng' ? 'tháng' : 'tuần'}`, veTp,
        note: `Đồng pha: chỉ vào khi Ngày + Tuần + Tháng cùng TĂNG (≥ 2/3: đỉnh/đáy cao dần, MACD trên tín hiệu, Sto 13-13-5 %K>%D); vào lệnh theo tín hiệu khung ngày (${I.vao}); bán theo tín hiệu bán MACD+Sto khung ${I.lenh === 'Lệnh tháng' ? 'tháng' : 'tuần'} hoặc cắt lỗ đáy ngày gần nhất. Kiểm định chứng khoán VN 2020–2026 (vốn 1 tỷ): +16,9%/năm nhưng 97% lợi nhuận từ 1 lệnh HQC – bỏ HQC còn +3,9%/năm (mua & giữ +9,8%); vào ngẫu nhiên trong ngày đồng pha +6,6%. Chưa có lợi thế đáng tin.`
      };
      const r = moPhongLo(D, R, I);
      r.draw = (g, X) => veTp.forEach(v => { const x1 = X.x(v.i), x2 = X.x(v.j != null ? v.j : D.n - 1); if (x1 == null || x2 == null) return;
        X.seg(g, x1, X.y(v.tp), x2, X.y(v.tp), '#089981', [5, 4], 1.5); X.label(g, x1 + 50, X.y(v.tp) - 9, 'Fibo ' + App.fmtPrice(v.tp), '#089981'); });
      return r;
    }
  };

  // Khoá học — CỔ PHIẾU DÀI HẠN: đồng pha N/T/Th + tín hiệu mua khung ngày; chỉ vào khi lãi dự kiến tới Fibo 1,0 của sóng
  // THÁNG (không có thì sóng TUẦN) ≥ 10%; KHÔNG tự bán ở mức Fibo – giữ đến khi khung THÁNG có tín hiệu bán MACD+Sto;
  // cắt lỗ ở đáy sóng TUẦN gần nhất.
  DEFS.st_daihan = {
    id: 'st_daihan', name: 'Khoá học — Cổ phiếu trung/dài hạn: Fibo 1,0 ≥ 10%, ADX tuần, giữ đến tín hiệu bán tháng', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['giu', 'Thời gian giữ', 'Trung hạn (tối đa 9 tháng)', 'sel', ['Trung hạn (tối đa 9 tháng)', 'Dài hạn (tối đa 10 năm)']],
      ['lai', 'Lãi dự kiến tối thiểu (%)', 10, 'float'], ['catMax', 'Cắt lỗ tối đa (%)', 15, 'float'],
      ['adx', 'ADX tuần tối thiểu (0 = tắt)', 25, 'float'],
      ['vao', 'Tín hiệu vào (khung ngày)', '2MA hoặc MACD+Sto', 'sel', ['2MA hoặc MACD+Sto', '2MA', 'MACD+Sto']],
      ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) {
      if ((App.TF[App.state.tf] || 86400) !== 86400) return { draw(g, X) { X.label(g, X.W / 2, 22, 'Chiến lược dài hạn: mở biểu đồ khung NGÀY (1N) – vào lệnh theo khung ngày', '#787b86'); } };
      const P = App.dongPha(D), S = App.macdSto(D), c = D.c, ma = { 6: T.sma(c, 6), 10: T.sma(c, 10), 20: T.sma(c, 20) }, atr = T.atr(D, 14);
      const hug = T.sma(c.map((x, i) => Math.abs(x - ma[10][i])), 20).map((x, i) => x / atr[i]);
      const cap = i => hug[i] <= 0.874 ? [10, 20] : [6, 10];
      const tren = (i, cp) => ma[cp[0]][i] > ma[cp[1]][i];
      const maLen = j => { const cp = cap(j); let cat = false;
        for (let x = Math.max(1, j - 2); x <= j; x++) { let deu = true; for (let q = x; q <= j; q++) if (!tren(q, cp)) deu = false; if (deu && !tren(x - 1, cp)) cat = true; }
        return cat && c[j] > ma[cp[0]][j] && c[j] > ma[cp[1]][j]; };
      const KW = khungLonTuNgay(D, 'W'), KM = khungLonTuNgay(D, 'M'), veTp = [], boQua = [];
      const tuanXong = j => { let w = -1; for (let q = 0; q < KW.B.n - 1; q++) if (KW.cuoi[q] >= 0 && KW.cuoi[q] <= j) w = q; return w; };
      // cắt lỗ: đáy sóng tuần gần nhất, nhưng không xa quá `catMax`% dưới giá
      const dayTuan = j => { const w = tuanXong(j); if (w < 6) return null; const s = dayGanNhat(KW.B, w, 2, 52), san = c[j] * (1 - I.catMax / 100);
        return s != null && s < c[j] ? Math.max(s, san) : san; };
      const lai = I.lai / 100;
      // ADX(14) khung TUẦN của tuần đã xong gần nhất: xu hướng đủ mạnh (≥ ngưỡng) và DI+ > DI− (xu hướng tăng)
      const dmW = T.dmi(KW.B, 14, 14);
      const adxOk = j => { if (!(I.adx > 0)) return true; const w = tuanXong(j); return w >= 0 && dmW.adx[w] >= I.adx && dmW.plus[w] > dmW.minus[w]; };
      const muc = j => App.fiboSong(D, KM, j, c[j], 2, 1.0) || App.fiboSong(D, KW, j, c[j], 2, 1.0);
      const R = {
        vt(j) {
          if (j < 30 || !P.dongPha[j] || !(c[j] > D.o[j])) return null;
          const ok = (I.vao !== 'MACD+Sto' && maLen(j)) || (I.vao !== '2MA' && (S.Mua1[j] || S.Mua2[j]));
          if (!ok) return null;
          if (!adxOk(j)) return null;
          const fb = muc(j);
          if (!fb || fb.tp < c[j] * (1 + lai)) { boQua.push({ i: j, tp: fb ? fb.tp : null }); return null; }
          const sl = dayTuan(j); if (sl == null) return null;
          return { stop: sl, tp: fb.tp };
        },
        xn(j, fill) {
          if (!P.dongPha[j] || !(c[j] > D.o[j] && c[j] > fill)) return null;
          const ok = (I.vao !== 'MACD+Sto' && c[j] > ma[cap(j)[1]][j]) || (I.vao !== '2MA' && (S.XN1[j] || S.XN2[j] || S.XN3[j]));
          if (!ok) return null; const sl = dayTuan(j); return sl != null ? { stop: sl } : null;
        },
        banPhan: null, banHet: i => P.banM[i], tenBan: 'Tín hiệu bán MACD+Sto tháng', veTp, tpChiVe: true,
        giuToiDa: (I.giu.startsWith('Dài') ? 3653 : 274) * 86400,
        note: `Dài hạn: vào khi Ngày + Tuần + Tháng đồng pha và có tín hiệu mua khung ngày (${I.vao}), CHỈ khi ADX tuần ≥ ${I.adx} với DI+ > DI− và lãi dự kiến tới Fibo 1,0 của sóng tháng (không có thì sóng tuần) ≥ ${I.lai}%. Không tự bán ở Fibo: giữ đến tín hiệu bán MACD+Sto khung THÁNG, tối đa ${I.giu.startsWith('Dài') ? '10 năm' : '9 tháng'}; cắt lỗ ở đáy sóng tuần nhưng không quá ${I.catMax}%. Chấm xám = có tín hiệu mua nhưng lãi dự kiến < ${I.lai}% nên bỏ qua. Chưa kiểm định trên toàn thị trường.`
      };
      const r = moPhongLo(D, R, I);
      const bo = []; let truoc = -99;
      boQua.forEach(b => { if (b.i - truoc > 10) { bo.push(b); truoc = b.i; } });
      r.markers = r.markers.concat(bo.map(b => ({ i: b.i, pos: 'belowBar', shape: 'circle', color: '#9598a1', text: '<' + I.lai + '%' })));
      r.draw = (g, X) => veTp.forEach(v => { const x1 = X.x(v.i), x2 = X.x(v.j != null ? v.j : D.n - 1); if (x1 == null || x2 == null) return;
        X.seg(g, x1, X.y(v.tp), x2, X.y(v.tp), '#089981', [5, 4], 1.5); X.label(g, x1 + 60, X.y(v.tp) - 9, 'Fibo 1,0 ' + App.fmtPrice(v.tp), '#089981'); });
      return r;
    }
  };

  DEFS.st_stockpredict = {
    id: 'st_stockpredict', name: 'StockPredict — Dự đoán xu hướng', cat: 'strategy', overlay: true, plots: [], levels: [],
    inputs: [['ng', 'Ngưỡng điểm (đã kiểm định: 50)', 50, 'float'], ['loc', 'Chỉ mua khi khung lớn tăng', true, 'bool'], ['r', 'Chốt lời = k × rủi ro', 3, 'float'],
      ['giu', 'Giữ tối đa (nến)', 60, 'int'], ['phi', 'Phí mỗi chiều (%)', 0.15, 'float'], ['thue', 'Thuế khi bán (%)', 0.1, 'float']],
    calc(D, I) { const r = App.spStrategy(D, I); return { markers: r.markers, backtest: r.backtest }; }
  };
})(window.App);
