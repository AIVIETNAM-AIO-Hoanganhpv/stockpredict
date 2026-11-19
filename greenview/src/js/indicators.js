/* =========================================================
 * indicators.js — Danh mục chỉ báo tích hợp sẵn (theo danh sách của TradingView)
 *
 * Mỗi chỉ báo khai báo:
 *   name     tên hiển thị        overlay  true = vẽ chồng lên giá
 *   inputs   [khoá, nhãn, mặc định, kiểu, lựa chọn]
 *   plots    [khoá, tên, màu, kiểu]   (kiểu: line | hist | step | dots | area | cross | cols)
 *   levels   các mức ngang (VD: 70/30 của RSI)
 *   calc(D, I) -> { khoáPlot: mảng giá trị, colors?, markers?, fills?, draw? }
 *   need     lý do không hỗ trợ (cần dữ liệu ngoài)
 * ========================================================= */
(function (App) {
  'use strict';
  const T = App.ta, N = NaN, isN = T.isN;
  const DEFS = App.INDICATORS = {};
  const R = (id, name, o) => { DEFS[id] = Object.assign({ id, name, cat: 'ind', inputs: [], plots: [], levels: [] }, o); };

  const SRC = ['close', 'open', 'high', 'low', 'hl2', 'hlc3', 'ohlc4'];
  const src = (k = 'src', d = 'close') => [k, 'Nguồn', d, 'sel', SRC];
  const len = (d, k = 'len', l = 'Độ dài') => [k, l, d, 'int'];
  const UP = '#089981', DN = '#f23645', BLUE = '#2962ff', ORG = '#ff6d00', PUR = '#7e57c2', GRAY = '#787b86', TEAL = '#00897b', YEL = '#fbc02d';
  const histCol = arr => arr.map((v, i) => v >= 0 ? (i && v < arr[i - 1] ? '#b2dfdb' : '#26a69a') : (i && v > arr[i - 1] ? '#ffcdd2' : '#ff5252'));
  const signCol = (arr, u = UP, d = DN) => arr.map(v => v >= 0 ? u : d);

  /* ===================== A ===================== */
  R('vol24', '24-hour volume', { inputs: [], plots: [['v', 'KL 24 giờ', BLUE, 'cols']],
    calc(D) { const out = T.arr(D.n); let s = 0, j = 0; for (let i = 0; i < D.n; i++) { s += D.v[i]; while (D.t[j] <= D.t[i] - 86400) s -= D.v[j++]; out[i] = s; } return { v: out }; } });
  R('ad', 'Accumulation/distribution', { plots: [['ad', 'A/D', '#999915']],
    calc(D) { return { ad: T.cum(D.c.map((c, i) => { const r = D.h[i] - D.l[i]; return r ? ((c - D.l[i]) - (D.h[i] - c)) / r * D.v[i] : 0; })) }; } });
  R('adl', 'Advance-decline line', { need: 'Cần dữ liệu số mã tăng/giảm của toàn sàn' });
  R('adr', 'Advance-decline ratio', { need: 'Cần dữ liệu số mã tăng/giảm của toàn sàn' });
  R('adrbars', 'Advance-decline ratio (bars)', { inputs: [len(9)], plots: [['r', 'Tỉ lệ', BLUE]], levels: [1],
    calc(D, I) { const up = T.sum(D.c.map((c, i) => c > D.o[i] ? 1 : 0), I.len), dn = T.sum(D.c.map((c, i) => c < D.o[i] ? 1 : 0), I.len); return { r: up.map((u, i) => dn[i] ? u / dn[i] : u) }; } });
  R('alma', 'Arnaud Legoux moving average', { overlay: true, inputs: [len(9), ['off', 'Offset', 0.85, 'float'], ['sig', 'Sigma', 6, 'float'], src()], plots: [['m', 'ALMA', BLUE]],
    calc(D, I) { return { m: T.alma(T.src(D, I.src), I.len, I.off, I.sig) }; } });
  R('aroon', 'Aroon', { inputs: [len(14)], plots: [['up', 'Aroon lên', ORG], ['dn', 'Aroon xuống', BLUE]],
    calc(D, I) { const hb = T.highestbars(D.h, I.len + 1), lb = T.lowestbars(D.l, I.len + 1); return { up: hb.map(x => 100 * (x + I.len) / I.len), dn: lb.map(x => 100 * (x + I.len) / I.len) }; } });
  R('aroonosc', 'Aroon oscillator', { inputs: [len(14)], plots: [['o', 'Dao động Aroon', PUR]], levels: [0, 90, -90],
    calc(D, I) { const hb = T.highestbars(D.h, I.len + 1), lb = T.lowestbars(D.l, I.len + 1); return { o: hb.map((x, i) => 100 * (x - lb[i]) / I.len) }; } });

  // Các chỉ báo "Auto" vẽ bằng lớp phủ dựa trên ZigZag
  const zz = (D, I) => T.zigzag(D, I.dev > 0 ? I.dev : T.autoDev(D), I.depth || 10);
  const FIBL = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.272, 1.618, 2.618];
  const FIBC = ['#787b86', '#f23645', '#ff9800', '#4caf50', '#089981', '#00bcd4', '#787b86', '#2962ff', '#9c27b0', '#e91e63'];
  R('autofibret', 'Auto fib retracement', { overlay: true, inputs: [['dev', 'Độ lệch % (0 = tự động)', 0, 'float'], ['depth', 'Độ sâu', 10, 'int']],
    calc(D, I) { const p = zz(D, I); if (p.length < 2) return {}; const a = p[p.length - 2], b = p[p.length - 1];
      return { draw(g, X) { const x1 = X.x(a.i), x2 = X.W; FIBL.slice(0, 7).forEach((lv, k) => { const pr = b.p + (a.p - b.p) * lv, y = X.y(pr); X.hline(g, x1, x2, y, FIBC[k], `${lv} (${App.fmtPrice(pr)})`); }); X.seg(g, X.x(a.i), X.y(a.p), X.x(b.i), X.y(b.p), GRAY, [4, 4]); } }; } });
  R('autofibext', 'Auto fib extension', { overlay: true, inputs: [['dev', 'Độ lệch % (0 = tự động)', 0, 'float'], ['depth', 'Độ sâu', 10, 'int']],
    calc(D, I) { const p = zz(D, I); if (p.length < 3) return {}; const [a, b, c] = p.slice(-3);
      return { draw(g, X) { const d = b.p - a.p; [0, 0.382, 0.618, 1, 1.272, 1.618, 2.618].forEach((lv, k) => { const pr = c.p + d * lv; X.hline(g, X.x(c.i), X.W, X.y(pr), FIBC[k + 1], `${lv} (${App.fmtPrice(pr)})`); });
        X.poly(g, [a, b, c].map(q => [X.x(q.i), X.y(q.p)]), GRAY, [4, 4]); } }; } });
  R('autokeylevels', 'Auto key levels', { overlay: true, inputs: [len(10, 'lb', 'Số nến hai bên'), ['max', 'Số mức tối đa', 6, 'int']],
    calc(D, I) { const ph = T.pivothigh(D.h, I.lb, I.lb), pl = T.pivotlow(D.l, I.lb, I.lb), lv = [];
      for (let i = 0; i < D.n; i++) { if (isN(ph[i])) lv.push(ph[i]); if (isN(pl[i])) lv.push(pl[i]); }
      const tol = T.atr(D, 14)[D.n - 1] * 0.5, cl = [];
      lv.forEach(p => { const c = cl.find(c => Math.abs(c.p - p) < tol); if (c) { c.p = (c.p * c.n + p) / (c.n + 1); c.n++; } else cl.push({ p, n: 1 }); });
      const top = cl.sort((a, b) => b.n - a.n).slice(0, I.max);
      return { draw(g, X) { top.forEach(c => X.hline(g, 0, X.W, X.y(c.p), c.p > D.c[D.n - 1] ? DN : UP, `${App.fmtPrice(c.p)} ×${c.n}`, c.n > 2 ? 2 : 1)); } }; } });
  R('autopitchfork', 'Auto pitchfork', { overlay: true, inputs: [['dev', 'Độ lệch % (0 = tự động)', 0, 'float'], ['depth', 'Độ sâu', 10, 'int']],
    calc(D, I) { const p = zz(D, I); if (p.length < 4) return {}; const [a, b, c] = p.slice(-4, -1);
      return { draw(g, X) { const A = [X.x(a.i), X.y(a.p)], B = [X.x(b.i), X.y(b.p)], C = [X.x(c.i), X.y(c.p)], M = [(B[0] + C[0]) / 2, (B[1] + C[1]) / 2];
        const dx = M[0] - A[0], dy = M[1] - A[1], k = dx ? (X.W - A[0]) / dx : 0;
        X.seg(g, A[0], A[1], A[0] + dx * k, A[1] + dy * k, '#e91e63'); [B, C].forEach(P => X.seg(g, P[0], P[1], P[0] + dx * k, P[1] + dy * k, BLUE)); X.seg(g, B[0], B[1], C[0], C[1], GRAY); } }; } });
  R('autotrend', 'Auto trendlines', { overlay: true, inputs: [len(10, 'lb', 'Số nến hai bên')],
    calc(D, I) { const ph = [], pl = []; const H = T.pivothigh(D.h, I.lb, I.lb), L = T.pivotlow(D.l, I.lb, I.lb);
      for (let i = 0; i < D.n; i++) { if (isN(H[i])) ph.push([i, H[i]]); if (isN(L[i])) pl.push([i, L[i]]); }
      return { draw(g, X) { [[ph, DN], [pl, UP]].forEach(([arr, col]) => { if (arr.length < 2) return; const [p1, p2] = arr.slice(-2); const s = (p2[1] - p1[1]) / (p2[0] - p1[0]), iEnd = D.n + 10;
        X.seg(g, X.x(p1[0]), X.y(p1[1]), X.x(iEnd), X.y(p1[1] + s * (iEnd - p1[0])), col, null, 2); }); } }; } });
  R('adx', 'Average directional index', { inputs: [len(14, 'smooth', 'Làm mượt ADX'), len(14, 'len', 'Độ dài DI')], plots: [['adx', 'ADX', '#ff5252']],
    calc(D, I) { return { adx: T.dmi(D, I.len, I.smooth).adx }; } });
  R('ao', 'Awesome oscillator', { plots: [['ao', 'AO', TEAL, 'hist']],
    calc(D) { const ao = T.sub(T.sma(D.hl2, 5), T.sma(D.hl2, 34)); return { ao, colors: { ao: ao.map((v, i) => i && v >= ao[i - 1] ? UP : DN) } }; } });
  R('adrange', 'Average day range', { inputs: [len(14)], plots: [['a', 'ADR', '#2196f3']], calc(D, I) { return { a: T.sma(T.sub(D.h, D.l), I.len) }; } });
  R('atr', 'Average true range', { inputs: [len(14), ['ma', 'Làm mượt', 'RMA', 'sel', ['RMA', 'SMA', 'EMA', 'WMA']]], plots: [['a', 'ATR', '#b71c1c']],
    calc(D, I) { return { a: T.ma(I.ma, T.tr(D), I.len) }; } });

  /* ===================== B ===================== */
  R('bop', 'Balance of power', { plots: [['b', 'BOP', '#ff5252']], levels: [0],
    calc(D) { return { b: D.c.map((c, i) => D.h[i] - D.l[i] ? (c - D.o[i]) / (D.h[i] - D.l[i]) : 0) }; } });
  R('bbtrend', 'BBTrend', { inputs: [len(20, 'sl', 'Dải ngắn'), len(50, 'll', 'Dải dài'), ['k', 'Độ lệch chuẩn', 2, 'float']], plots: [['b', 'BBTrend', TEAL, 'hist']], levels: [0],
    calc(D, I) { const m1 = T.sma(D.c, I.sl), s1 = T.stdev(D.c, I.sl), m2 = T.sma(D.c, I.ll), s2 = T.stdev(D.c, I.ll);
      const b = m1.map((m, i) => (Math.abs((m - I.k * s1[i]) - (m2[i] - I.k * s2[i])) - Math.abs((m + I.k * s1[i]) - (m2[i] + I.k * s2[i]))) / m * 100); return { b, colors: { b: histCol(b) } }; } });
  const bb = (D, I) => { const s = T.src(D, I.src), m = T.ma(I.ma || 'SMA', s, I.len, D.v), sd = T.stdev(s, I.len); return { m, u: m.map((x, i) => x + I.k * sd[i]), l: m.map((x, i) => x - I.k * sd[i]), s }; };
  R('bb', 'Bollinger bands', { overlay: true, inputs: [len(20), src(), ['k', 'Độ lệch chuẩn', 2, 'float'], ['ma', 'Kiểu MA', 'SMA', 'sel', T.MA_TYPES]],
    plots: [['m', 'Cơ sở', '#2962ff'], ['u', 'Trên', '#f23645'], ['l', 'Dưới', '#089981']],
    calc(D, I) { const r = bb(D, I); return { m: r.m, u: r.u, l: r.l, fills: [['u', 'l', 'rgba(33,150,243,0.06)']] }; } });
  R('bbb', 'Bollinger bands %b', { inputs: [len(20), src(), ['k', 'Độ lệch chuẩn', 2, 'float']], plots: [['b', '%b', TEAL]], levels: [1, 0.5, 0],
    calc(D, I) { const r = bb(D, I); return { b: r.s.map((x, i) => (x - r.l[i]) / (r.u[i] - r.l[i])) }; } });
  R('bbw', 'Bollinger bandwidth', { inputs: [len(20), src(), ['k', 'Độ lệch chuẩn', 2, 'float']], plots: [['w', 'Độ rộng', '#2962ff']],
    calc(D, I) { const r = bb(D, I); return { w: r.m.map((m, i) => (r.u[i] - r.l[i]) / m * 100) }; } });
  R('bbars', 'Bollinger bars', { overlay: true, inputs: [len(20), src(), ['k', 'Độ lệch chuẩn', 2, 'float']],
    calc(D, I) { const r = bb(D, I), mk = []; for (let i = 1; i < D.n; i++) { if (D.c[i] > r.u[i] && D.c[i - 1] <= r.u[i - 1]) mk.push({ i, pos: 'aboveBar', shape: 'circle', color: DN, text: 'Trên' }); if (D.c[i] < r.l[i] && D.c[i - 1] >= r.l[i - 1]) mk.push({ i, pos: 'belowBar', shape: 'circle', color: UP, text: 'Dưới' }); } return { markers: mk }; } });
  R('bbp', 'Bull bear power', { inputs: [len(13)], plots: [['p', 'BBPower', TEAL, 'hist']], levels: [0],
    calc(D, I) { const e = T.ema(D.c, I.len), p = D.h.map((h, i) => h + D.l[i] - 2 * e[i]); return { p, colors: { p: histCol(p) } }; } });

  /* ===================== C ===================== */
  R('cmf', 'Chaikin money flow', { inputs: [len(20)], plots: [['m', 'CMF', '#43a047']], levels: [0],
    calc(D, I) { const mfv = D.c.map((c, i) => { const r = D.h[i] - D.l[i]; return r ? ((c - D.l[i]) - (D.h[i] - c)) / r * D.v[i] : 0; }); return { m: T.div(T.sum(mfv, I.len), T.sum(D.v, I.len)) }; } });
  R('chaikinosc', 'Chaikin oscillator', { inputs: [len(3, 'f', 'Nhanh'), len(10, 's', 'Chậm')], plots: [['o', 'Chaikin Osc', '#ec407a']], levels: [0],
    calc(D, I) { const ad = DEFS.ad.calc(D).ad; return { o: T.sub(T.ema(ad, I.f), T.ema(ad, I.s)) }; } });
  R('cks', 'Chande kroll stop', { overlay: true, inputs: [len(10, 'p', 'Chu kỳ ATR'), ['x', 'Hệ số', 1, 'float'], len(9, 'q', 'Chu kỳ dừng')], plots: [['s', 'Dừng ngắn', DN], ['l', 'Dừng dài', UP]],
    calc(D, I) { const a = T.atr(D, I.p), fh = T.highest(D.h, I.p).map((h, i) => h - I.x * a[i]), fl = T.lowest(D.l, I.p).map((l, i) => l + I.x * a[i]); return { s: T.highest(fh, I.q), l: T.lowest(fl, I.q) }; } });
  R('cmo', 'Chande momentum oscillator', { inputs: [len(9), src()], plots: [['m', 'CMO', BLUE]], levels: [50, 0, -50],
    calc(D, I) { const s = T.src(D, I.src), ch = T.change(s), u = T.sum(ch.map(x => x > 0 ? x : 0), I.len), d = T.sum(ch.map(x => x < 0 ? -x : 0), I.len); return { m: u.map((x, i) => 100 * (x - d[i]) / (x + d[i])) }; } });
  R('chopzone', 'Chop zone', { plots: [['z', 'Chop Zone', TEAL, 'cols']],
    calc(D) { const e = T.ema(D.c, 34), hh = T.highest(D.h, 30), ll = T.lowest(D.l, 30), cols = [], z = [];
      for (let i = 0; i < D.n; i++) { const span = 25 / (hh[i] - ll[i]) * ll[i], y2 = i ? (e[i - 1] - e[i]) / D.hlc3[i] * span : 0, c = Math.sqrt(1 + y2 * y2), ang = Math.round(180 * Math.acos(1 / c) / Math.PI) * (y2 > 0 ? -1 : 1);
        z.push(1); cols.push(ang >= 5 ? '#26C6DA' : ang >= 3.57 ? '#43A047' : ang >= 2.14 ? '#A5D6A7' : ang >= 0.71 ? '#009688' : ang <= -5 ? '#D50000' : ang <= -3.57 ? '#E91E63' : ang <= -2.14 ? '#FF6D00' : ang <= -0.71 ? '#FFB74D' : '#FDD835'); }
      return { z, colors: { z: cols } }; } });
  R('chop', 'Choppiness index', { inputs: [len(14)], plots: [['c', 'CHOP', BLUE]], levels: [61.8, 38.2],
    calc(D, I) { const s = T.sum(T.atr(D, 1), I.len), hh = T.highest(D.h, I.len), ll = T.lowest(D.l, I.len); return { c: s.map((x, i) => 100 * Math.log10(x / (hh[i] - ll[i])) / Math.log10(I.len)) }; } });
  R('cci', 'Commodity channel index', { inputs: [len(20), src('src', 'hlc3')], plots: [['c', 'CCI', BLUE]], levels: [100, 0, -100],
    calc(D, I) { return { c: T.cci(T.src(D, I.src), I.len) }; } });
  R('crsi', 'Connors RSI', { inputs: [len(3, 'r', 'Độ dài RSI'), len(2, 's', 'Độ dài chuỗi'), len(100, 'p', 'Độ dài xếp hạng')], plots: [['c', 'CRSI', BLUE]], levels: [70, 30],
    calc(D, I) { const streak = []; let s = 0; D.c.forEach((c, i) => { s = !i ? 0 : c > D.c[i - 1] ? (s > 0 ? s + 1 : 1) : c < D.c[i - 1] ? (s < 0 ? s - 1 : -1) : 0; streak.push(s); });
      const a = T.rsi(D.c, I.r), b = T.rsi(streak, I.s), r = T.percentrank(T.roc(D.c, 1), I.p); return { c: a.map((x, i) => (x + b[i] + r[i]) / 3) }; } });
  R('coppock', 'Coppock curve', { inputs: [len(10, 'w', 'Độ dài WMA'), len(14, 'l', 'ROC dài'), len(11, 's', 'ROC ngắn')], plots: [['c', 'Coppock', BLUE]], levels: [0],
    calc(D, I) { return { c: T.wma(T.add(T.roc(D.c, I.l), T.roc(D.c, I.s)), I.w) }; } });
  R('corr', 'Correlation coefficient', { need: 'Cần mã thứ hai để so sánh — dùng "So sánh" trong Trung tâm phân tích' });
  R('cvd', 'Cumulative volume delta', { plots: [['d', 'CVD', TEAL, 'hist']],
    calc(D) { const d = T.cum(D.c.map((c, i) => c >= D.o[i] ? D.v[i] : -D.v[i])); return { d, colors: { d: signCol(d) } }; }, note: 'Ước lượng theo nến tăng/giảm (không có dữ liệu khớp lệnh từng giao dịch)' });
  R('cvi', 'Cumulative volume index', { need: 'Cần khối lượng tăng/giảm của toàn sàn' });

  /* ===================== D–E ===================== */
  R('dema', 'Double EMA', { overlay: true, inputs: [len(9), src()], plots: [['d', 'DEMA', '#43a047']], calc(D, I) { return { d: T.dema(T.src(D, I.src), I.len) }; } });
  R('dpo', 'Detrended price oscillator', { inputs: [len(21)], plots: [['d', 'DPO', '#43a047']], levels: [0],
    calc(D, I) { const b = Math.floor(I.len / 2 + 1), m = T.sma(D.c, I.len); return { d: D.c.map((c, i) => c - (i >= b ? m[i - b] : N)) }; } });
  R('dmi', 'Directional movement index', { inputs: [len(14, 'smooth', 'Làm mượt ADX'), len(14, 'len', 'Độ dài DI')], plots: [['adx', 'ADX', '#f50057'], ['p', '+DI', BLUE], ['m', '-DI', ORG]],
    calc(D, I) { const r = T.dmi(D, I.len, I.smooth); return { adx: r.adx, p: r.plus, m: r.minus }; } });
  R('donchian', 'Donchian channels', { overlay: true, inputs: [len(20)], plots: [['u', 'Trên', BLUE], ['b', 'Cơ sở', ORG], ['l', 'Dưới', BLUE]],
    calc(D, I) { const u = T.highest(D.h, I.len), l = T.lowest(D.l, I.len); return { u, l, b: u.map((x, i) => (x + l[i]) / 2), fills: [['u', 'l', 'rgba(33,150,243,0.06)']] }; } });
  R('eom', 'Ease of movement', { inputs: [len(14), ['div', 'Hệ số chia', 10000, 'int']], plots: [['e', 'EOM', '#43a047']], levels: [0],
    calc(D, I) { return { e: T.sma(D.hl2.map((x, i) => i ? I.div * (x - D.hl2[i - 1]) * (D.h[i] - D.l[i]) / (D.v[i] || 1) : N), I.len) }; } });
  R('efi', 'Elder force index', { inputs: [len(13)], plots: [['f', 'EFI', '#f44336']], levels: [0], calc(D, I) { return { f: T.ema(T.change(D.c).map((x, i) => x * D.v[i]), I.len) }; } });
  R('ema', 'Moving average exponential', { overlay: true, inputs: [len(9), src(), ['off', 'Dịch chuyển', 0, 'int']], plots: [['e', 'EMA', BLUE]],
    calc(D, I) { return { e: T.shift(T.ema(T.src(D, I.src), I.len), I.off) }; } });
  R('emacross', 'EMA cross', { overlay: true, inputs: [len(9, 'a', 'EMA ngắn'), len(26, 'b', 'EMA dài')], plots: [['a', 'Ngắn', ORG], ['b', 'Dài', BLUE]],
    calc(D, I) { const a = T.ema(D.c, I.a), b = T.ema(D.c, I.b), mk = []; for (let i = 1; i < D.n; i++) { if (T.crossover(a, b, i)) mk.push({ i, pos: 'belowBar', shape: 'circle', color: UP }); if (T.crossunder(a, b, i)) mk.push({ i, pos: 'aboveBar', shape: 'circle', color: DN }); } return { a, b, markers: mk }; } });
  R('env', 'Envelope', { overlay: true, inputs: [len(20), ['pct', 'Phần trăm', 10, 'float'], ['exp', 'Dùng EMA', false, 'bool']], plots: [['u', 'Trên', BLUE], ['b', 'Cơ sở', ORG], ['l', 'Dưới', BLUE]],
    calc(D, I) { const b = I.exp ? T.ema(D.c, I.len) : T.sma(D.c, I.len); return { b, u: b.map(x => x * (1 + I.pct / 100)), l: b.map(x => x * (1 - I.pct / 100)), fills: [['u', 'l', 'rgba(33,150,243,0.05)']] }; } });

  /* ===================== F–H ===================== */
  R('fisher', 'Fisher transform', { inputs: [len(9)], plots: [['f', 'Fisher', BLUE], ['t', 'Kích hoạt', ORG]], levels: [1.5, 0.75, 0, -0.75, -1.5],
    calc(D, I) { const hh = T.highest(D.hl2, I.len), ll = T.lowest(D.hl2, I.len), f = T.arr(D.n); let v = 0, fi = 0;
      for (let i = 0; i < D.n; i++) { if (!isN(hh[i])) continue; const r = hh[i] - ll[i]; v = 0.66 * ((r ? (D.hl2[i] - ll[i]) / r : 0.5) - 0.5) + 0.67 * v; v = Math.max(-0.999, Math.min(0.999, v)); fi = 0.5 * Math.log((1 + v) / (1 - v)) + 0.5 * fi; f[i] = fi; }
      return { f, t: T.shift(f, 1) }; } });
  R('gaps', 'Gaps', { overlay: true, inputs: [['max', 'Số khoảng trống tối đa', 15, 'int']],
    calc(D, I) { const gaps = []; for (let i = 1; i < D.n; i++) { if (D.l[i] > D.h[i - 1]) gaps.push({ i, top: D.l[i], bot: D.h[i - 1], up: true }); else if (D.h[i] < D.l[i - 1]) gaps.push({ i, top: D.l[i - 1], bot: D.h[i], up: false }); }
      gaps.forEach(g => { for (let j = g.i + 1; j < D.n; j++) { if (g.up ? D.l[j] <= g.bot : D.h[j] >= g.top) { g.end = j; break; } } });
      const show = gaps.filter(g => !g.end).slice(-I.max);
      return { draw(g, X) { show.forEach(s => X.box(g, X.x(s.i - 1), X.y(s.top), X.W, X.y(s.bot), s.up ? 'rgba(8,153,129,0.15)' : 'rgba(242,54,69,0.15)')); } }; } });
  R('hv', 'Historical volatility', { inputs: [len(10)], plots: [['h', 'HV', BLUE]],
    calc(D, I) { const lr = D.c.map((c, i) => i ? Math.log(c / D.c[i - 1]) : N), per = (App.TF[App.state && App.state.tf] || 86400) >= 86400 ? 365 : 365 * 24 * 3600 / (App.TF[App.state.tf] || 3600); return { h: T.stdev(lr, I.len).map(x => 100 * x * Math.sqrt(per)) }; } });
  R('hma', 'Hull moving average', { overlay: true, inputs: [len(9), src()], plots: [['h', 'HMA', '#ff9800']], calc(D, I) { return { h: T.hma(T.src(D, I.src), I.len) }; } });

  /* ===================== I–L ===================== */
  R('ichimoku', 'Ichimoku cloud', { overlay: true, inputs: [len(9, 'a', 'Tenkan'), len(26, 'b', 'Kijun'), len(52, 'c', 'Senkou B'), len(26, 'd', 'Dịch chuyển')],
    plots: [['ten', 'Tenkan', '#2962ff'], ['kij', 'Kijun', '#b71c1c'], ['lag', 'Chikou', '#43a047'], ['sa', 'Senkou A', '#a5d6a7'], ['sb', 'Senkou B', '#ef9a9a']],
    calc(D, I) { const dc = n => T.highest(D.h, n).map((h, i) => (h + T.lowest(D.l, n)[i]) / 2);
      const ten = dc(I.a), kij = dc(I.b), sa0 = ten.map((x, i) => (x + kij[i]) / 2), sb0 = dc(I.c), off = I.d - 1;
      // Mây vẽ lệch về tương lai: mở rộng trục thời gian bằng "future"
      return { ten, kij, lag: T.shift(D.c, -off), sa: T.shift(sa0, off), sb: T.shift(sb0, off), future: { sa: sa0.slice(-off), sb: sb0.slice(-off) },
        fills: [['sa', 'sb', 'rgba(67,160,71,0.12)', 'rgba(244,67,54,0.12)']] }; } });
  R('kc', 'Keltner channels', { overlay: true, inputs: [len(20), ['k', 'Hệ số', 2, 'float'], ['exp', 'Dùng EMA', true, 'bool'], ['band', 'Kiểu dải', 'ATR', 'sel', ['ATR', 'True range', 'Range']], len(10, 'al', 'Độ dài ATR')],
    plots: [['u', 'Trên', BLUE], ['b', 'Cơ sở', BLUE], ['l', 'Dưới', BLUE]],
    calc(D, I) { const b = I.exp ? T.ema(D.c, I.len) : T.sma(D.c, I.len), r = I.band === 'ATR' ? T.atr(D, I.al) : I.band === 'True range' ? T.tr(D) : T.ema(T.sub(D.h, D.l), I.len);
      return { b, u: b.map((x, i) => x + I.k * r[i]), l: b.map((x, i) => x - I.k * r[i]), fills: [['u', 'l', 'rgba(33,150,243,0.05)']] }; } });
  R('klinger', 'Klinger oscillator', { plots: [['k', 'Klinger', BLUE], ['s', 'Tín hiệu', '#43a047']],
    calc(D) { const sv = D.hlc3.map((x, i) => (i && x - D.hlc3[i - 1] >= 0 ? 1 : -1) * D.v[i]); const k = T.sub(T.ema(sv, 34), T.ema(sv, 55)); return { k, s: T.ema(k, 13) }; } });
  R('kst', 'Know sure thing', { plots: [['k', 'KST', '#089981'], ['s', 'Tín hiệu', DN]], levels: [0],
    calc(D) { const r = (a, b) => T.sma(T.roc(D.c, a), b); const k = r(10, 10).map((x, i) => x + 2 * r(15, 10)[i] + 3 * r(20, 10)[i] + 4 * r(30, 15)[i]); return { k, s: T.sma(k, 9) }; } });
  R('lsma', 'Least squares moving average', { overlay: true, inputs: [len(25), ['off', 'Offset', 0, 'int'], src()], plots: [['l', 'LSMA', BLUE]], calc(D, I) { return { l: T.linreg(T.src(D, I.src), I.len, I.off) }; } });
  R('lrc', 'Linear regression channel', { overlay: true, inputs: [len(100), ['k', 'Độ lệch', 2, 'float']],
    calc(D, I) { const n = Math.min(I.len, D.n), s = D.n - n; let sx = 0, sy = 0, sxy = 0, sxx = 0;
      for (let j = 0; j < n; j++) { const y = D.c[s + j]; sx += j; sy += y; sxy += j * y; sxx += j * j; }
      const m = (n * sxy - sx * sy) / (n * sxx - sx * sx), b = (sy - m * sx) / n; let dv = 0; for (let j = 0; j < n; j++) dv += (D.c[s + j] - (b + m * j)) ** 2; const sd = Math.sqrt(dv / n);
      return { draw(g, X) { [[0, BLUE], [I.k * sd, DN], [-I.k * sd, UP]].forEach(([o, c]) => X.seg(g, X.x(s), X.y(b + o), X.x(D.n - 1), X.y(b + m * (n - 1) + o), c, o ? null : [6, 4], o ? 1.5 : 1));
        g.fillStyle = 'rgba(41,98,255,0.06)'; g.beginPath(); g.moveTo(X.x(s), X.y(b + I.k * sd)); g.lineTo(X.x(D.n - 1), X.y(b + m * (n - 1) + I.k * sd)); g.lineTo(X.x(D.n - 1), X.y(b + m * (n - 1) - I.k * sd)); g.lineTo(X.x(s), X.y(b - I.k * sd)); g.fill(); } }; } });

  /* ===================== M ===================== */
  R('macross', 'MA cross', { overlay: true, inputs: [len(9, 'a', 'MA ngắn'), len(21, 'b', 'MA dài')], plots: [['a', 'Ngắn', '#43a047'], ['b', 'Dài', DN]],
    calc(D, I) { const a = T.sma(D.c, I.a), b = T.sma(D.c, I.b), mk = []; for (let i = 1; i < D.n; i++) { if (T.crossover(a, b, i) || T.crossunder(a, b, i)) mk.push({ i, pos: 'inBar', shape: 'circle', color: '#2962ff' }); } return { a, b, markers: mk }; } });
  R('macd', 'MACD', { inputs: [len(12, 'f', 'Nhanh'), len(26, 's', 'Chậm'), src(), len(9, 'sig', 'Tín hiệu'), ['osc', 'MA dao động', 'EMA', 'sel', ['EMA', 'SMA']], ['sm', 'MA tín hiệu', 'EMA', 'sel', ['EMA', 'SMA']]],
    plots: [['h', 'Histogram', TEAL, 'hist'], ['m', 'MACD', BLUE], ['s', 'Tín hiệu', ORG]], levels: [0],
    calc(D, I) { const s = T.src(D, I.src), m = T.sub(T.ma(I.osc, s, I.f), T.ma(I.osc, s, I.s)), sg = T.ma(I.sm, m, I.sig), h = T.sub(m, sg); return { h, m, s: sg, colors: { h: histCol(h) } }; } });
  R('mass', 'Mass index', { inputs: [len(10)], plots: [['m', 'Mass', '#2196f3']],
    calc(D, I) { const r = T.sub(D.h, D.l), e1 = T.ema(r, 9), e2 = T.ema(e1, 9); return { m: T.sum(T.div(e1, e2), I.len) }; } });
  R('mcginley', 'McGinley dynamic', { overlay: true, inputs: [len(14)], plots: [['m', 'McGinley', '#00bcd4']], calc(D, I) { return { m: T.mcginley(D.c, I.len) }; } });
  R('median', 'Median', { overlay: true, inputs: [len(3), src('src', 'hl2'), len(14, 'al', 'Độ dài ATR'), ['k', 'Hệ số ATR', 2, 'float']], plots: [['m', 'Trung vị', '#ff1744'], ['u', 'Trên', '#2196f3'], ['l', 'Dưới', '#2196f3']],
    calc(D, I) { const s = T.src(D, I.src), m = s.map((_, i) => { if (i < I.len - 1) return N; const w = s.slice(i - I.len + 1, i + 1).sort((a, b) => a - b); return I.len % 2 ? w[(I.len - 1) / 2] : (w[I.len / 2 - 1] + w[I.len / 2]) / 2; }); const a = T.atr(D, I.al);
      return { m, u: m.map((x, i) => x + I.k * a[i]), l: m.map((x, i) => x - I.k * a[i]), fills: [['u', 'l', 'rgba(33,150,243,0.05)']] }; } });
  R('mom', 'Momentum', { inputs: [len(10), src()], plots: [['m', 'Động lượng', BLUE]], levels: [0], calc(D, I) { return { m: T.mom(T.src(D, I.src), I.len) }; } });
  R('mfi', 'Money flow index', { inputs: [len(14)], plots: [['m', 'MFI', PUR]], levels: [80, 20], calc(D, I) { return { m: T.mfi(D, I.len) }; } });
  R('moon', 'Moon phases', { overlay: true,
    calc(D) { const mk = [], syn = 29.530588853 * 86400, ref = 947182440; let prev = null;
      for (let i = 0; i < D.n; i++) { const ph = (((D.t[i] - App.TZ - ref) % syn) + syn) % syn / syn, cur = ph < 0.5 ? 'w' : 'n';
        if (prev && cur !== prev) mk.push(cur === 'w' ? { i, pos: 'belowBar', shape: 'circle', color: '#787b86', text: 'Trăng non' } : { i, pos: 'aboveBar', shape: 'circle', color: '#fbc02d', text: 'Trăng tròn' }); prev = cur; }
      return { markers: mk }; } });
  R('ma', 'Moving average simple', { overlay: true, inputs: [len(9), src(), ['off', 'Dịch chuyển', 0, 'int']], plots: [['m', 'MA', BLUE]],
    calc(D, I) { return { m: T.shift(T.sma(T.src(D, I.src), I.len), I.off) }; } });
  R('wma', 'Moving average weighted', { overlay: true, inputs: [len(9), src()], plots: [['m', 'WMA', BLUE]], calc(D, I) { return { m: T.wma(T.src(D, I.src), I.len) }; } });
  R('maribbon', 'Moving average ribbon', { overlay: true, inputs: [['ma', 'Kiểu MA', 'SMA', 'sel', T.MA_TYPES], len(20, 'a', 'MA 1'), len(50, 'b', 'MA 2'), len(100, 'c', 'MA 3'), len(200, 'd', 'MA 4')],
    plots: [['a', 'MA 1', '#f6c309'], ['b', 'MA 2', '#fb9800'], ['c', 'MA 3', '#fb6500'], ['d', 'MA 4', '#f60c0c']],
    calc(D, I) { const f = n => T.ma(I.ma, D.c, n, D.v); return { a: f(I.a), b: f(I.b), c: f(I.c), d: f(I.d) }; } });
  R('mtp', 'Multi-time period charts', { need: 'Cần dữ liệu khung thời gian khác cùng lúc' });

  /* ===================== N–P ===================== */
  R('netvol', 'Net volume', { plots: [['n', 'KL ròng', BLUE]], levels: [0], calc(D) { return { n: D.c.map((c, i) => i ? (c > D.c[i - 1] ? D.v[i] : c < D.c[i - 1] ? -D.v[i] : 0) : 0) }; } });
  R('obv', 'On balance volume', { plots: [['o', 'OBV', BLUE]], calc(D) { return { o: T.obv(D) }; } });
  R('oi', 'Open interest', { need: 'Cần dữ liệu hợp đồng mở (phái sinh)' });
  R('sar', 'Parabolic SAR', { overlay: true, inputs: [['s', 'Bắt đầu', 0.02, 'float'], ['inc', 'Bước tăng', 0.02, 'float'], ['max', 'Tối đa', 0.2, 'float']], plots: [['p', 'SAR', BLUE, 'cross']],
    calc(D, I) { return { p: T.sar(D, I.s, I.inc, I.max) }; } });
  R('perf', 'Performance', { need: 'Cần dữ liệu hiệu suất nhiều kỳ từ sàn' });
  R('pphl', 'Pivot points high low', { overlay: true, inputs: [len(10, 'l', 'Nến trái'), len(10, 'r', 'Nến phải')],
    calc(D, I) { const H = T.pivothigh(D.h, I.l, I.r), L = T.pivotlow(D.l, I.l, I.r), mk = [];
      for (let i = 0; i < D.n; i++) { if (isN(H[i])) mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: DN, text: App.fmtPrice(H[i]) }); if (isN(L[i])) mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: UP, text: App.fmtPrice(L[i]) }); }
      return { markers: mk }; } });
  R('pps', 'Pivot points standard', { overlay: true, inputs: [['type', 'Kiểu', 'Traditional', 'sel', ['Traditional', 'Fibonacci', 'Woodie', 'Classic', 'DM', 'Camarilla']], ['tf', 'Khung pivot', 'Auto', 'sel', ['Auto', 'D', 'W', 'M', 'Q', 'Y']], ['num', 'Số kỳ hiển thị', 10, 'int']],
    calc(D, I) { const tfs = App.TF[App.state.tf] || 86400, p = I.tf !== 'Auto' ? I.tf : tfs <= 900 ? 'D' : tfs <= 14400 ? 'W' : tfs <= 86400 ? 'M' : 'Y';
      const per = []; let k = null;
      for (let i = 0; i < D.n; i++) { const key = T.periodKey(D.t[i], p); if (key !== k) { per.push({ s: i, h: D.h[i], l: D.l[i], o: D.o[i], c: D.c[i] }); k = key; } else { const c = per[per.length - 1]; c.h = Math.max(c.h, D.h[i]); c.l = Math.min(c.l, D.l[i]); c.c = D.c[i]; } }
      const lv = [];
      for (let j = 1; j < per.length; j++) { const { h, l, c, o } = per[j - 1], cur = per[j], r = h - l, e = j + 1 < per.length ? per[j + 1].s : D.n + 5; let L = {};
        if (I.type === 'Fibonacci') { const P = (h + l + c) / 3; L = { P, R1: P + .382 * r, S1: P - .382 * r, R2: P + .618 * r, S2: P - .618 * r, R3: P + r, S3: P - r }; }
        else if (I.type === 'Woodie') { const P = (h + l + 2 * cur.o) / 4; L = { P, R1: 2 * P - l, S1: 2 * P - h, R2: P + r, S2: P - r, R3: h + 2 * (P - l), S3: l - 2 * (h - P) }; }
        else if (I.type === 'Classic') { const P = (h + l + c) / 3; L = { P, R1: 2 * P - l, S1: 2 * P - h, R2: P + r, S2: P - r, R3: P + 2 * r, S3: P - 2 * r }; }
        else if (I.type === 'DM') { const x = c < o ? h + 2 * l + c : c > o ? 2 * h + l + c : h + l + 2 * c; L = { P: x / 4, R1: x / 2 - l, S1: x / 2 - h }; }
        else if (I.type === 'Camarilla') { L = { P: (h + l + c) / 3, R1: c + r * 1.1 / 12, S1: c - r * 1.1 / 12, R2: c + r * 1.1 / 6, S2: c - r * 1.1 / 6, R3: c + r * 1.1 / 4, S3: c - r * 1.1 / 4, R4: c + r * 1.1 / 2, S4: c - r * 1.1 / 2 }; }
        else { const P = (h + l + c) / 3; L = { P, R1: 2 * P - l, S1: 2 * P - h, R2: P + r, S2: P - r, R3: h + 2 * (P - l), S3: l - 2 * (h - P), R4: P * 3 + (h - 3 * l), S4: P * 3 - (3 * h - l) }; }
        lv.push({ s: cur.s, e, L }); }
      const show = lv.slice(-I.num);
      return { draw(g, X) { show.forEach(q => Object.entries(q.L).forEach(([nm, v]) => X.hline(g, X.x(q.s), X.x(q.e), X.y(v), nm === 'P' ? '#ff9800' : nm[0] === 'R' ? DN : UP, nm, 1, true))); } }; } });
  R('ppo', 'Price oscillator', { inputs: [len(10, 'f', 'Nhanh'), len(21, 's', 'Chậm'), src()], plots: [['p', 'PPO', TEAL]], levels: [0],
    calc(D, I) { const s = T.src(D, I.src), a = T.sma(s, I.f), b = T.sma(s, I.s); return { p: a.map((x, i) => (x - b[i]) / b[i] * 100) }; } });
  R('ptarget', 'Price target', { need: 'Cần dữ liệu giá mục tiêu của nhà phân tích' });
  R('pvt', 'Price volume trend', { plots: [['p', 'PVT', BLUE]], calc(D) { return { p: T.cum(D.c.map((c, i) => i ? (c - D.c[i - 1]) / D.c[i - 1] * D.v[i] : 0)) }; } });
  R('pchan', 'Price channel', { overlay: true, inputs: [len(20), ['off', 'Dịch chuyển', 0, 'int']], plots: [['h', 'Cao', DN], ['l', 'Thấp', UP], ['m', 'Giữa', BLUE]],
    calc(D, I) { const h = T.shift(T.highest(D.h, I.len), I.off), l = T.shift(T.lowest(D.l, I.len), I.off); return { h, l, m: h.map((x, i) => (x + l[i]) / 2) }; } });

  /* ===================== R ===================== */
  R('rci', 'Rank correlation index', { inputs: [len(10)], plots: [['r', 'RCI', BLUE]], levels: [80, 0, -80],
    calc(D, I) { const n = I.len; return { r: D.c.map((_, i) => { if (i < n - 1) return N; const w = D.c.slice(i - n + 1, i + 1), idx = w.map((v, k) => [v, k]).sort((a, b) => b[0] - a[0]); let d = 0; idx.forEach(([, k], r) => { d += ((n - k) - (r + 1)) ** 2; }); return (1 - 6 * d / (n * (n * n - 1))) * 100; }) }; } });
  R('roc', 'Rate of change', { inputs: [len(9), src()], plots: [['r', 'ROC', BLUE]], levels: [0], calc(D, I) { return { r: T.roc(T.src(D, I.src), I.len) }; } });
  R('ratio', 'Ratio', { need: 'Cần mã thứ hai — dùng "So sánh"' });
  R('rvgi', 'Relative vigor index', { inputs: [len(10)], plots: [['r', 'RVGI', '#008000'], ['s', 'Tín hiệu', DN]], levels: [0],
    calc(D, I) { const sw = s => s.map((x, i) => i < 3 ? N : (x + 2 * s[i - 1] + 2 * s[i - 2] + s[i - 3]) / 6); const r = T.div(T.sum(sw(T.sub(D.c, D.o)), I.len), T.sum(sw(T.sub(D.h, D.l)), I.len)); return { r, s: sw(r) }; } });
  R('rvi', 'Relative volatility index', { inputs: [len(10), len(14, 'm', 'Làm mượt')], plots: [['r', 'RVI', PUR]], levels: [80, 50, 20],
    calc(D, I) { const sd = T.stdev(D.c, I.len), ch = T.change(D.c), u = T.ema(sd.map((s, i) => ch[i] <= 0 ? 0 : s), I.m), d = T.ema(sd.map((s, i) => ch[i] > 0 ? 0 : s), I.m); return { r: u.map((x, i) => 100 * x / (x + d[i])) }; } });
  R('rsi', 'Relative strength index', { inputs: [len(14), src(), ['ma', 'MA làm mượt', 'SMA', 'sel', ['None', 'SMA', 'EMA', 'WMA']], len(14, 'ml', 'Độ dài MA')],
    plots: [['r', 'RSI', PUR], ['m', 'MA của RSI', YEL]], levels: [70, 50, 30],
    calc(D, I) { const r = T.rsi(T.src(D, I.src), I.len); return { r, m: I.ma === 'None' ? T.arr(D.n) : T.ma(I.ma, r, I.ml) }; } });
  R('rb_pivot', 'Rob Booker — Intraday pivot points', { overlay: true, inputs: [['tf', 'Khung', 'D', 'sel', ['D', 'W']]],
    calc(D, I) { return DEFS.pps.calc(D, { type: 'Traditional', tf: I.tf, num: 5 }); } });
  R('rb_knox', 'Rob Booker — Knoxville divergence', { overlay: true, inputs: [len(150, 'lb', 'Số nến nhìn lại'), len(21, 'r', 'Độ dài RSI'), len(20, 'm', 'Độ dài động lượng')],
    calc(D, I) { const rsi = T.rsi(D.c, I.r), mom = T.mom(D.c, I.m), mk = [];
      for (let i = 20; i < D.n; i++) for (let j = i - 5; j > Math.max(0, i - I.lb); j--) {
        if (D.h[i] > D.h[j] && mom[i] < mom[j] && rsi[j] > 70) { mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: DN, text: 'KD' }); break; }
        if (D.l[i] < D.l[j] && mom[i] > mom[j] && rsi[j] < 30) { mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: UP, text: 'KD' }); break; } }
      return { markers: mk.filter((m, k) => !k || m.i - mk[k - 1].i > 3) }; } });
  R('rb_missed', 'Rob Booker — Missed pivot points', { overlay: true, inputs: [len(5, 'l', 'Nến hai bên')],
    calc(D, I) { const H = T.pivothigh(D.h, I.l, I.l), L = T.pivotlow(D.l, I.l, I.l), mk = []; let last = 0;
      for (let i = 0; i < D.n; i++) { const t = isN(H[i]) ? 1 : isN(L[i]) ? -1 : 0; if (t && t === last) mk.push({ i, pos: t > 0 ? 'aboveBar' : 'belowBar', shape: 'circle', color: GRAY, text: 'Bỏ lỡ' }); if (t) last = t; }
      return { markers: mk }; } });
  R('rb_rev', 'Rob Booker — Reversal', { overlay: true, inputs: [len(12, 'f', 'MACD nhanh'), len(26, 's', 'MACD chậm'), len(70, 'ob', 'Stoch quá mua'), len(30, 'os', 'Stoch quá bán')],
    calc(D, I) { const m = T.sub(T.ema(D.c, I.f), T.ema(D.c, I.s)), k = T.sma(T.stoch(D.c, D.h, D.l, 70), 10), mk = [];
      for (let i = 1; i < D.n; i++) { if (T.crossunder(m, 0, i) && k[i] > I.ob) mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: DN, text: 'Đảo chiều' }); if (T.crossover(m, 0, i) && k[i] < I.os) mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: UP, text: 'Đảo chiều' }); }
      return { markers: mk }; } });
  R('rvwap', 'Rolling VWAP', { overlay: true, inputs: [len(30, 'len', 'Số nến cuộn')], plots: [['v', 'VWAP cuộn', '#2962ff']],
    calc(D, I) { return { v: T.div(T.sum(T.mul(D.hlc3, D.v), I.len), T.sum(D.v, I.len)) }; } });

  /* ===================== S ===================== */
  R('season', 'Seasonality', { need: 'Cần nhiều năm dữ liệu lịch sử theo mùa' });
  R('smiei', 'SMI ergodic indicator', { inputs: [len(5, 'l', 'Dài'), len(20, 's', 'Ngắn'), len(5, 'sig', 'Tín hiệu')], plots: [['i', 'SMI', BLUE], ['s', 'Tín hiệu', ORG]], levels: [0],
    calc(D, I) { const tsi = DEFS.tsi.calc(D, { l: I.s, s: I.l, sig: I.sig }).t.map(x => x / 100); return { i: tsi, s: T.ema(tsi, I.sig) }; } });
  R('smieo', 'SMI ergodic oscillator', { inputs: [len(5, 'l', 'Dài'), len(20, 's', 'Ngắn'), len(5, 'sig', 'Tín hiệu')], plots: [['o', 'Dao động', '#ff5252', 'hist']],
    calc(D, I) { const r = DEFS.smiei.calc(D, I); return { o: T.sub(r.i, r.s) }; } });
  R('smma', 'Smoothed moving average', { overlay: true, inputs: [len(7), src()], plots: [['m', 'SMMA', '#673ab7']], calc(D, I) { return { m: T.rma(T.src(D, I.src), I.len) }; } });
  R('spread', 'Spread', { need: 'Cần mã thứ hai — dùng "So sánh"' });
  R('stdev', 'Standard deviation', { inputs: [len(20), src()], plots: [['s', 'Độ lệch chuẩn', BLUE]], calc(D, I) { return { s: T.stdev(T.src(D, I.src), I.len) }; } });
  R('stderr', 'Standard error', { inputs: [len(21)], plots: [['s', 'Sai số chuẩn', BLUE]],
    calc(D, I) { const lr = T.linreg(D.c, I.len); return { s: D.c.map((_, i) => { if (i < I.len - 1) return N; let s = 0; for (let j = 0; j < I.len; j++) s += (D.c[i - j] - T.linreg(D.c.slice(i - I.len + 1, i + 1), I.len, j)[I.len - 1]) ** 2; return Math.sqrt(s / (I.len - 2)); }), _lr: lr }; } });
  R('stderrb', 'Standard error bands', { overlay: true, inputs: [len(21), ['k', 'Hệ số', 2, 'float'], len(3, 'sm', 'Làm mượt')], plots: [['u', 'Trên', BLUE], ['m', 'Giữa', DN], ['l', 'Dưới', BLUE]],
    calc(D, I) { const m = T.sma(T.linreg(D.c, I.len), I.sm), se = DEFS.stderr.calc(D, I).s, s2 = T.sma(se, I.sm); return { m, u: m.map((x, i) => x + I.k * s2[i]), l: m.map((x, i) => x - I.k * s2[i]), fills: [['u', 'l', 'rgba(33,150,243,0.05)']] }; } });
  R('stoch', 'Stochastic', { inputs: [len(14, 'k', '%K'), len(1, 'sk', 'Làm mượt %K'), len(3, 'd', '%D')], plots: [['k', '%K', BLUE], ['d', '%D', ORG]], levels: [80, 50, 20],
    calc(D, I) { const k = T.sma(T.stoch(D.c, D.h, D.l, I.k), I.sk); return { k, d: T.sma(k, I.d) }; } });
  R('smi', 'Stochastic momentum index', { inputs: [len(10, 'k', '%K'), len(3, 'd', '%D'), len(3, 'e', 'EMA')], plots: [['s', 'SMI', BLUE], ['e', 'EMA', ORG]], levels: [40, -40],
    calc(D, I) { const hh = T.highest(D.h, I.k), ll = T.lowest(D.l, I.k), rel = D.c.map((c, i) => c - (hh[i] + ll[i]) / 2), rng = hh.map((h, i) => h - ll[i]);
      const e2 = x => T.ema(T.ema(x, I.d), I.d), a = e2(rel), b = e2(rng), s = a.map((x, i) => 200 * x / b[i]); return { s, e: T.ema(s, I.e) }; } });
  R('stochrsi', 'Stochastic RSI', { inputs: [len(3, 'k', '%K'), len(3, 'd', '%D'), len(14, 'r', 'Độ dài RSI'), len(14, 's', 'Độ dài Stoch'), src()], plots: [['k', '%K', BLUE], ['d', '%D', ORG]], levels: [80, 50, 20],
    calc(D, I) { const r = T.rsi(T.src(D, I.src), I.r), k = T.sma(T.stoch(r, r, r, I.s), I.k); return { k, d: T.sma(k, I.d) }; } });
  R('supertrend', 'Supertrend', { overlay: true, inputs: [len(10, 'len', 'Độ dài ATR'), ['f', 'Hệ số', 3, 'float']], plots: [['up', 'Xu hướng tăng', UP, 'step'], ['dn', 'Xu hướng giảm', DN, 'step']],
    calc(D, I) { const { st, dir } = T.supertrend(D, I.f, I.len), mk = []; for (let i = 1; i < D.n; i++) if (dir[i] !== dir[i - 1] && isN(dir[i - 1])) mk.push(dir[i] > 0 ? { i, pos: 'belowBar', shape: 'arrowUp', color: UP, text: 'Mua' } : { i, pos: 'aboveBar', shape: 'arrowDown', color: DN, text: 'Bán' });
      return { up: st.map((v, i) => dir[i] > 0 ? v : N), dn: st.map((v, i) => dir[i] < 0 ? v : N), markers: mk }; } });

  /* ===================== T ===================== */
  // Đánh giá kỹ thuật (theo cách của TradingView: nhóm MA + nhóm dao động)
  App.techRatingSeries = function (D) {
    const c = D.c, n = D.n, ma = new Array(n).fill(0), maN = new Array(n).fill(0), osc = new Array(n).fill(0), oscN = new Array(n).fill(0);
    const cnt = { ma: { buy: 0, sell: 0, neu: 0 }, osc: { buy: 0, sell: 0, neu: 0 } };
    const addMA = (i, v) => { if (!isN(v)) return; const s = v > 0 ? 1 : v < 0 ? -1 : 0; ma[i] += s; maN[i]++; if (i === n - 1) cnt.ma[s > 0 ? 'buy' : s < 0 ? 'sell' : 'neu']++; };
    const addO = (i, s) => { if (!isN(s)) return; osc[i] += s; oscN[i]++; if (i === n - 1) cnt.osc[s > 0 ? 'buy' : s < 0 ? 'sell' : 'neu']++; };
    const mas = []; [10, 20, 30, 50, 100, 200].forEach(l => { mas.push(T.sma(c, l), T.ema(c, l)); });
    mas.push(T.vwma(c, D.v, 20), T.hma(c, 9));
    const ich = DEFS.ichimoku.calc(D, { a: 9, b: 26, c: 52, d: 26 }), rsi = T.rsi(c, 14), st = DEFS.stoch.calc(D, { k: 14, sk: 3, d: 3 }), cci = T.cci(D.hlc3, 20), dm = T.dmi(D, 14, 14),
      ao = DEFS.ao.calc(D).ao, mo = T.mom(c, 10), mc = DEFS.macd.calc(D, { f: 12, s: 26, src: 'close', sig: 9, osc: 'EMA', sm: 'EMA' }), sr = DEFS.stochrsi.calc(D, { k: 3, d: 3, r: 14, s: 14, src: 'close' }),
      wr = DEFS.wpr.calc(D, { len: 14 }).w, uo = DEFS.uo.calc(D, { a: 7, b: 14, c: 28 }).u;
    for (let i = 1; i < n; i++) {
      mas.forEach(m => addMA(i, isN(m[i]) ? c[i] - m[i] : N));
      if (isN(ich.kij[i])) addMA(i, c[i] > ich.kij[i] && ich.ten[i] > ich.kij[i] ? 1 : c[i] < ich.kij[i] && ich.ten[i] < ich.kij[i] ? -1 : 0);
      addO(i, isN(rsi[i]) ? (rsi[i] < 30 && rsi[i] > rsi[i - 1] ? 1 : rsi[i] > 70 && rsi[i] < rsi[i - 1] ? -1 : 0) : N);
      addO(i, isN(st.d[i]) ? (st.k[i] < 20 && st.k[i] > st.d[i] ? 1 : st.k[i] > 80 && st.k[i] < st.d[i] ? -1 : 0) : N);
      addO(i, isN(cci[i]) ? (cci[i] < -100 && cci[i] > cci[i - 1] ? 1 : cci[i] > 100 && cci[i] < cci[i - 1] ? -1 : 0) : N);
      addO(i, isN(dm.adx[i]) ? (dm.adx[i] > 20 && dm.plus[i] > dm.minus[i] ? 1 : dm.adx[i] > 20 && dm.plus[i] < dm.minus[i] ? -1 : 0) : N);
      addO(i, isN(ao[i]) ? (ao[i] > 0 && ao[i] > ao[i - 1] ? 1 : ao[i] < 0 && ao[i] < ao[i - 1] ? -1 : 0) : N);
      addO(i, isN(mo[i]) ? Math.sign(mo[i] - mo[i - 1]) : N);
      addO(i, isN(mc.s[i]) ? Math.sign(mc.m[i] - mc.s[i]) : N);
      addO(i, isN(sr.d[i]) ? (sr.k[i] < 20 && sr.k[i] > sr.d[i] ? 1 : sr.k[i] > 80 && sr.k[i] < sr.d[i] ? -1 : 0) : N);
      addO(i, isN(wr[i]) ? (wr[i] < -80 && wr[i] > wr[i - 1] ? 1 : wr[i] > -20 && wr[i] < wr[i - 1] ? -1 : 0) : N);
      addO(i, isN(uo[i]) ? (uo[i] > 70 ? 1 : uo[i] < 30 ? -1 : 0) : N);
    }
    const mA = ma.map((v, i) => maN[i] ? v / maN[i] : N), oA = osc.map((v, i) => oscN[i] ? v / oscN[i] : N);
    return { ma: mA, osc: oA, all: mA.map((v, i) => (v + oA[i]) / 2), cnt };
  };
  App.techRating = function (D) {
    const s = App.techRatingSeries(D), n = D.n - 1;
    return { ma: s.ma[n], osc: s.osc[n], all: s.all[n], maC: s.cnt.ma, oscC: s.cnt.osc };
  };
  App.ratingLabel = v => v > 0.5 ? 'Mua mạnh' : v > 0.1 ? 'Mua' : v < -0.5 ? 'Bán mạnh' : v < -0.1 ? 'Bán' : 'Trung lập';
  R('techrating', 'Technical ratings', { plots: [['r', 'Đánh giá', BLUE, 'hist']], levels: [0.5, 0.1, -0.1, -0.5],
    calc(D) { const out = App.techRatingSeries(D).all; return { r: out, colors: { r: out.map(v => v > 0.1 ? UP : v < -0.1 ? DN : GRAY) } }; } });
  R('twap', 'Time weighted average price', { overlay: true, inputs: [['a', 'Neo theo', 'D', 'sel', ['D', 'W', 'M']]], plots: [['t', 'TWAP', '#ff9800']],
    calc(D, I) { const out = T.arr(D.n); let s = 0, k = 0, key = null; for (let i = 0; i < D.n; i++) { const kk = T.periodKey(D.t[i], I.a); if (kk !== key) { s = 0; k = 0; key = kk; } s += D.ohlc4[i]; k++; out[i] = s / k; } return { t: out }; } });
  R('sessions', 'Trading sessions', { overlay: true, inputs: [],
    calc(D) { const tfs = App.TF[App.state.tf] || 86400; if (tfs >= 86400) return {};
      const S = [['Tokyo', 0, 9, 'rgba(255,152,0,0.07)'], ['London', 8, 16.5, 'rgba(33,150,243,0.07)'], ['New York', 13.5, 20, 'rgba(76,175,80,0.07)']];
      return { draw(g, X) { S.forEach(([nm, a, b, col]) => { let st = null; for (let i = 0; i <= D.n; i++) { const h = i < D.n ? ((D.t[i] - App.TZ) % 86400) / 3600 : -1, inS = h >= a && h < b;
        if (inS && st == null) st = i; if (!inS && st != null) { X.box(g, X.x(st), 0, X.x(i - 1), X.H, col); g.fillStyle = col.replace('0.07', '0.8'); g.font = '10px sans-serif'; g.fillText(nm, X.x(st) + 2, 12); st = null; } } }); } }; } });
  R('tsi_str', 'Trend strength index', { inputs: [len(14)], plots: [['t', 'TSI', BLUE]], levels: [0],
    calc(D, I) { const idx = D.c.map((_, i) => i); return { t: T.correlation(D.c, idx, I.len) }; } });
  R('tema', 'Triple EMA', { overlay: true, inputs: [len(9), src()], plots: [['t', 'TEMA', '#f44336']], calc(D, I) { return { t: T.tema(T.src(D, I.src), I.len) }; } });
  R('trix', 'TRIX', { inputs: [len(18)], plots: [['t', 'TRIX', DN]], levels: [0],
    calc(D, I) { const l = D.c.map(Math.log), e = T.ema(T.ema(T.ema(l, I.len), I.len), I.len); return { t: T.change(e).map(x => x * 10000) }; } });
  R('tsi', 'True strength index', { inputs: [len(25, 'l', 'Dài'), len(13, 's', 'Ngắn'), len(13, 'sig', 'Tín hiệu')], plots: [['t', 'TSI', BLUE], ['s', 'Tín hiệu', DN]], levels: [0],
    calc(D, I) { const pc = T.change(D.c), ds = x => T.ema(T.ema(x, I.l), I.s), t = T.div(ds(pc), ds(pc.map(Math.abs))).map(x => 100 * x); return { t, s: T.ema(t, I.sig) }; } });

  /* ===================== U–Z ===================== */
  R('uo', 'Ultimate oscillator', { inputs: [len(7, 'a', 'Nhanh'), len(14, 'b', 'Vừa'), len(28, 'c', 'Chậm')], plots: [['u', 'UO', '#f44336']], levels: [70, 50, 30],
    calc(D, I) { const bp = D.c.map((c, i) => c - Math.min(D.l[i], i ? D.c[i - 1] : D.l[i])), tr = D.c.map((c, i) => Math.max(D.h[i], i ? D.c[i - 1] : D.h[i]) - Math.min(D.l[i], i ? D.c[i - 1] : D.l[i]));
      const av = n => T.div(T.sum(bp, n), T.sum(tr, n)), a = av(I.a), b = av(I.b), c = av(I.c); return { u: a.map((x, i) => 100 * (4 * x + 2 * b[i] + c[i]) / 7) }; } });
  R('updownvol', 'Up/down volume', { plots: [['u', 'KL tăng', UP, 'cols'], ['d', 'KL giảm', DN, 'cols'], ['dl', 'Chênh lệch', BLUE]],
    calc(D) { const u = D.v.map((v, i) => D.c[i] >= D.o[i] ? v : 0), d = D.v.map((v, i) => D.c[i] < D.o[i] ? -v : 0); return { u, d, dl: T.add(u, d) }; }, note: 'Ước lượng theo màu nến' });
  R('vap', 'Visible average price', { overlay: true,
    calc(D) { return { draw(g, X) { const [a, b] = X.visible(); let s = 0, k = 0; for (let i = a; i <= b; i++) { s += D.c[i]; k++; } if (k) X.hline(g, 0, X.W, X.y(s / k), '#ff9800', 'TB hiển thị ' + App.fmtPrice(s / k), 1.5); } }; } });
  R('volstop', 'Volatility stop', { overlay: true, inputs: [len(20), ['k', 'Hệ số', 2, 'float']], plots: [['v', 'Dừng biến động', TEAL, 'cross']],
    calc(D, I) { const a = T.atr(D, I.len), out = T.arr(D.n), col = []; let up = true, mx = D.c[0], mn = D.c[0], st = N;
      for (let i = 0; i < D.n; i++) { if (!isN(a[i])) { col.push(GRAY); continue; } mx = Math.max(mx, D.c[i]); mn = Math.min(mn, D.c[i]);
        let s = up ? mx - I.k * a[i] : mn + I.k * a[i]; s = !isN(st) ? s : up ? Math.max(st, s) : Math.min(st, s);
        if (up && D.c[i] < s) { up = false; mx = mn = D.c[i]; s = mn + I.k * a[i]; } else if (!up && D.c[i] > s) { up = true; mx = mn = D.c[i]; s = mx - I.k * a[i]; }
        st = s; out[i] = s; col.push(up ? UP : DN); }
      return { v: out, colors: { v: col } }; } });
  R('volume', 'Volume', { overlay: true, scale: 'vol', inputs: [len(20, 'ml', 'Độ dài MA'), ['showma', 'Hiện MA', false, 'bool']], plots: [['v', 'Khối lượng', '#26a69a', 'cols'], ['m', 'MA khối lượng', BLUE]],
    calc(D, I) { return { v: D.v, m: I.showma ? T.sma(D.v, I.ml) : T.arr(D.n), colors: { v: D.c.map((c, i) => c >= D.o[i] ? 'rgba(8,153,129,0.5)' : 'rgba(242,54,69,0.5)') } }; } });
  R('voldelta', 'Volume delta', { plots: [['d', 'Delta', TEAL, 'hist']], calc(D) { const d = D.v.map((v, i) => { const r = D.h[i] - D.l[i]; return r ? v * (2 * D.c[i] - D.h[i] - D.l[i]) / r : 0; }); return { d, colors: { d: signCol(d) } }; }, note: 'Ước lượng từ vị trí giá đóng cửa trong nến' });
  R('volosc', 'Volume oscillator', { inputs: [len(5, 's', 'Ngắn'), len(10, 'l', 'Dài')], plots: [['o', 'Dao động KL', BLUE]], levels: [0],
    calc(D, I) { const a = T.ema(D.v, I.s), b = T.ema(D.v, I.l); return { o: a.map((x, i) => 100 * (x - b[i]) / b[i]) }; } });
  R('vwap', 'Volume weighted average price', { overlay: true, inputs: [['a', 'Neo theo', 'D', 'sel', ['D', 'W', 'M', 'Q', 'Y']], ['k', 'Hệ số dải', 1, 'float'], ['bands', 'Hiện dải', true, 'bool']], plots: [['v', 'VWAP', '#2962ff'], ['u', 'Dải trên', '#4caf50'], ['l', 'Dải dưới', '#4caf50']],
    calc(D, I) { const r = T.vwap(D, I.a); return { v: r.vwap, u: I.bands ? r.vwap.map((x, i) => x + I.k * r.sd[i]) : T.arr(D.n), l: I.bands ? r.vwap.map((x, i) => x - I.k * r.sd[i]) : T.arr(D.n), fills: I.bands ? [['u', 'l', 'rgba(76,175,80,0.06)']] : [] }; } });
  R('vwma', 'Volume weighted moving average', { overlay: true, inputs: [len(20), src()], plots: [['v', 'VWMA', BLUE]], calc(D, I) { return { v: T.vwma(T.src(D, I.src), D.v, I.len) }; } });
  R('vortex', 'Vortex indicator', { inputs: [len(14)], plots: [['p', 'VI+', BLUE], ['m', 'VI-', DN]],
    calc(D, I) { const vp = D.h.map((h, i) => i ? Math.abs(h - D.l[i - 1]) : N), vm = D.l.map((l, i) => i ? Math.abs(l - D.h[i - 1]) : N), s = T.sum(T.atr(D, 1), I.len);
      return { p: T.div(T.sum(vp, I.len), s), m: T.div(T.sum(vm, I.len), s) }; } });
  R('wpr', 'Williams %R', { inputs: [len(14)], plots: [['w', '%R', PUR]], levels: [-20, -50, -80],
    calc(D, I) { const hh = T.highest(D.h, I.len), ll = T.lowest(D.l, I.len); return { w: D.c.map((c, i) => -100 * (hh[i] - c) / (hh[i] - ll[i])) }; } });
  R('alligator', 'Williams alligator', { overlay: true, inputs: [len(13, 'j', 'Hàm'), len(8, 't', 'Răng'), len(5, 'l', 'Môi')], plots: [['j', 'Hàm', BLUE], ['t', 'Răng', '#e91e63'], ['l', 'Môi', '#66bb6a']],
    calc(D, I) { return { j: T.shift(T.rma(D.hl2, I.j), 8), t: T.shift(T.rma(D.hl2, I.t), 5), l: T.shift(T.rma(D.hl2, I.l), 3) }; } });
  R('fractals', 'Williams fractals', { overlay: true, inputs: [len(2, 'n', 'Chu kỳ')],
    calc(D, I) { const H = T.pivothigh(D.h, I.n, I.n), L = T.pivotlow(D.l, I.n, I.n), mk = []; for (let i = 0; i < D.n; i++) { if (isN(H[i])) mk.push({ i, pos: 'aboveBar', shape: 'arrowDown', color: DN }); if (isN(L[i])) mk.push({ i, pos: 'belowBar', shape: 'arrowUp', color: UP }); } return { markers: mk }; } });
  R('woodies', 'Woodies CCI', { inputs: [len(6, 't', 'CCI Turbo'), len(14, 'c', 'CCI 14')], plots: [['h', 'Histogram', GRAY, 'hist'], ['t', 'CCI Turbo', '#ffeb3b'], ['c', 'CCI 14', '#009688']], levels: [100, 0, -100],
    calc(D, I) { const c = T.cci(D.hlc3, I.c); return { h: c, t: T.cci(D.hlc3, I.t), c, colors: { h: c.map(v => v >= 0 ? 'rgba(8,153,129,0.5)' : 'rgba(242,54,69,0.5)') } }; } });
  R('zigzag', 'Zig zag', { overlay: true, inputs: [['dev', 'Độ lệch % (0 = tự động)', 5, 'float'], ['depth', 'Độ sâu', 10, 'int'], ['labels', 'Hiện giá', true, 'bool']],
    calc(D, I) { const p = zz(D, I); return { draw(g, X) { X.poly(g, p.map(q => [X.x(q.i), X.y(q.p)]), '#2962ff', null, 2);
      if (I.labels) p.forEach((q, k) => { if (!k) return; const ch = (q.p / p[k - 1].p - 1) * 100; X.label(g, X.x(q.i), X.y(q.p) + (q.hi ? -10 : 10), `${App.fmtPrice(q.p)} (${App.fmtPct(ch)})`, q.hi ? DN : UP); }); } }; } });

  /* ===================== Hồ sơ khối lượng (tab "Hồ sơ") ===================== */
  App.volumeProfile = function (D, a, b, rows) {
    let hi = -Infinity, lo = Infinity;
    for (let i = a; i <= b; i++) { hi = Math.max(hi, D.h[i]); lo = Math.min(lo, D.l[i]); }
    if (!(hi > lo)) return null;
    const step = (hi - lo) / rows, up = new Array(rows).fill(0), dn = new Array(rows).fill(0);
    for (let i = a; i <= b; i++) {
      const r0 = Math.max(0, Math.floor((D.l[i] - lo) / step)), r1 = Math.min(rows - 1, Math.floor((D.h[i] - lo) / step)), share = D.v[i] / (r1 - r0 + 1);
      for (let r = r0; r <= r1; r++) (D.c[i] >= D.o[i] ? up : dn)[r] += share;
    }
    const tot = up.map((u, i) => u + dn[i]), poc = tot.indexOf(Math.max(...tot)), sum = tot.reduce((s, x) => s + x, 0);
    let va = tot[poc], lo2 = poc, hi2 = poc;
    while (va < sum * 0.7 && (lo2 > 0 || hi2 < rows - 1)) { const nx = hi2 < rows - 1 ? tot[hi2 + 1] : -1, pv = lo2 > 0 ? tot[lo2 - 1] : -1; if (nx >= pv) va += tot[++hi2]; else va += tot[--lo2]; }
    return { lo, step, up, dn, tot, poc, vah: hi2, val: lo2, max: tot[poc] };
  };
  App.drawProfile = function (g, X, vp, xLeft, width, fromRight) {
    if (!vp) return;
    vp.tot.forEach((t, r) => {
      const y1 = X.y(vp.lo + (r + 1) * vp.step), y2 = X.y(vp.lo + r * vp.step), h = Math.max(1, y2 - y1 - 1), inVA = r >= vp.val && r <= vp.vah;
      const wu = width * vp.up[r] / vp.max, wd = width * vp.dn[r] / vp.max;
      const x0 = fromRight ? xLeft + width - wu - wd : xLeft;
      g.fillStyle = inVA ? 'rgba(8,153,129,0.55)' : 'rgba(8,153,129,0.25)'; g.fillRect(x0, y1, wu, h);
      g.fillStyle = inVA ? 'rgba(242,54,69,0.55)' : 'rgba(242,54,69,0.25)'; g.fillRect(x0 + wu, y1, wd, h);
    });
    const yp = X.y(vp.lo + (vp.poc + 0.5) * vp.step);
    X.seg(g, fromRight ? 0 : xLeft, yp, fromRight ? X.W : xLeft + width * 1.2, yp, '#ff5252', null, 1.5);
  };
  const VPcat = 'profile';
  R('vpvr', 'Visible range volume profile', { cat: VPcat, overlay: true, inputs: [['rows', 'Số hàng', 24, 'int'], ['w', 'Độ rộng (%)', 30, 'int']],
    calc(D, I) { return { draw(g, X) { const [a, b] = X.visible(); App.drawProfile(g, X, App.volumeProfile(D, a, b, I.rows), X.W * (1 - I.w / 100), X.W * I.w / 100, true); } }; } });
  R('vpfixed', 'Fixed range volume profile (N nến cuối)', { cat: VPcat, overlay: true, inputs: [len(150, 'len', 'Số nến'), ['rows', 'Số hàng', 24, 'int']],
    calc(D, I) { const a = Math.max(0, D.n - I.len), vp = App.volumeProfile(D, a, D.n - 1, I.rows); return { draw(g, X) { const x1 = X.x(a), x2 = X.x(D.n - 1); App.drawProfile(g, X, vp, x1, Math.max(20, (x2 - x1) * 0.5), false); } }; } });
  R('vpsession', 'Session volume profile', { cat: VPcat, overlay: true, inputs: [['rows', 'Số hàng', 16, 'int']],
    calc(D, I) { const per = []; let key = null; for (let i = 0; i < D.n; i++) { const k = T.periodKey(D.t[i], 'D'); if (k !== key) { per.push([i, i]); key = k; } else per[per.length - 1][1] = i; }
      const vps = per.slice(-30).map(([a, b]) => ({ a, b, vp: App.volumeProfile(D, a, b, I.rows) }));
      return { draw(g, X) { vps.forEach(p => { const x1 = X.x(p.a), x2 = X.x(p.b); App.drawProfile(g, X, p.vp, x1, Math.max(6, (x2 - x1) * 0.7), false); }); } }; } });
  R('vpperiodic', 'Periodic volume profile', { cat: VPcat, overlay: true, inputs: [['p', 'Chu kỳ', 'W', 'sel', ['D', 'W', 'M', 'Q']], ['rows', 'Số hàng', 20, 'int']],
    calc(D, I) { const per = []; let key = null; for (let i = 0; i < D.n; i++) { const k = T.periodKey(D.t[i], I.p); if (k !== key) { per.push([i, i]); key = k; } else per[per.length - 1][1] = i; }
      const vps = per.slice(-20).map(([a, b]) => ({ a, b, vp: App.volumeProfile(D, a, b, I.rows) }));
      return { draw(g, X) { vps.forEach(p => { const x1 = X.x(p.a), x2 = X.x(p.b); App.drawProfile(g, X, p.vp, x1, Math.max(6, (x2 - x1) * 0.8), false); }); } }; } });
  R('vpauto', 'Auto anchored volume profile', { cat: VPcat, overlay: true, inputs: [['rows', 'Số hàng', 24, 'int']],
    calc(D, I) { const p = T.zigzag(D, T.autoDev(D), 10), a = p.length > 1 ? p[p.length - 2].i : 0, vp = App.volumeProfile(D, a, D.n - 1, I.rows);
      return { draw(g, X) { const x1 = X.x(a), x2 = X.x(D.n - 1); App.drawProfile(g, X, vp, x1, Math.max(20, (x2 - x1) * 0.6), false); } }; } });

  // Mô tả ngắn tiếng Việt cho một số chỉ báo phổ biến (hiện khi bấm "?")
  App.IND_HELP = {
    ma: 'Giá trung bình cộng của N nến gần nhất — làm mượt giá, xem xu hướng.',
    ema: 'Trung bình hàm mũ — giống MA nhưng ưu tiên nến gần đây, phản ứng nhanh hơn.',
    rsi: 'Đo tốc độ tăng/giảm, 0–100. Trên 70: quá mua, dưới 30: quá bán.',
    macd: 'Hiệu hai đường EMA (12, 26) và đường tín hiệu EMA 9 — bắt đổi xu hướng.',
    bb: 'Dải Bollinger: MA ± k lần độ lệch chuẩn — đo độ biến động.',
    stoch: 'So sánh giá đóng cửa với vùng cao–thấp N nến. Trên 80 quá mua, dưới 20 quá bán.',
    ichimoku: 'Hệ thống mây Ichimoku: xu hướng, hỗ trợ/kháng cự và động lượng.',
    vwap: 'Giá trung bình theo khối lượng trong ngày — mức giá "công bằng".',
    supertrend: 'Đường dừng theo ATR, đổi màu khi xu hướng đảo chiều.',
    atr: 'Biên độ dao động thực trung bình — đo độ biến động.',
    adx: 'Đo sức mạnh xu hướng (không phân biệt hướng). Trên 25: xu hướng mạnh.',
    obv: 'Cộng dồn khối lượng theo hướng giá — xác nhận dòng tiền.',
    volume: 'Khối lượng giao dịch mỗi nến.',
    sar: 'Các điểm dừng lỗ dạng parabol bám theo xu hướng.',
    vpvr: 'Phân bố khối lượng theo mức giá trong vùng đang nhìn. Đường đỏ = POC (giá giao dịch nhiều nhất).'
  };
})(window.App);
