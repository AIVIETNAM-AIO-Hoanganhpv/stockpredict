/* =========================================================
 * ta.js — Thư viện hàm tính toán kỹ thuật (giống các hàm ta.* của Pine Script)
 * Mọi hàm nhận mảng số (có thể có NaN) và trả về mảng cùng độ dài.
 * ========================================================= */
(function (App) {
  'use strict';
  const N = NaN;
  const isN = v => v === v && v != null; // không phải NaN

  const T = App.ta = {};

  T.nz = (v, d = 0) => (isN(v) ? v : d);
  T.arr = (n, v = N) => new Array(n).fill(v);

  // Lấy nguồn giá theo tên
  T.src = function (D, name) {
    switch (name) {
      case 'open': return D.o; case 'high': return D.h; case 'low': return D.l;
      case 'hl2': return D.hl2; case 'hlc3': return D.hlc3; case 'ohlc4': return D.ohlc4;
      case 'volume': return D.v;
      default: return D.c;
    }
  };

  // Chuẩn bị dữ liệu dạng cột từ mảng nến
  T.prep = function (bars) {
    const n = bars.length, o = new Array(n), h = new Array(n), l = new Array(n), c = new Array(n), v = new Array(n), t = new Array(n);
    const hl2 = new Array(n), hlc3 = new Array(n), ohlc4 = new Array(n);
    for (let i = 0; i < n; i++) {
      const b = bars[i];
      o[i] = b.open; h[i] = b.high; l[i] = b.low; c[i] = b.close; v[i] = b.volume || 0; t[i] = b.time;
      hl2[i] = (b.high + b.low) / 2; hlc3[i] = (b.high + b.low + b.close) / 3; ohlc4[i] = (b.open + b.high + b.low + b.close) / 4;
    }
    return { n, o, h, l, c, v, t, hl2, hlc3, ohlc4, bars };
  };

  /* ---------- Trung bình động ---------- */
  T.sma = function (s, n) {
    const out = T.arr(s.length); let sum = 0, cnt = 0;
    for (let i = 0; i < s.length; i++) {
      const x = s[i];
      if (isN(x)) { sum += x; cnt++; }
      if (i >= n) { const y = s[i - n]; if (isN(y)) { sum -= y; cnt--; } }
      if (i >= n - 1 && cnt === n) out[i] = sum / n;
    }
    return out;
  };
  T.ema = function (s, n, alpha) {
    const a = alpha || 2 / (n + 1), out = T.arr(s.length);
    let prev = N, seed = 0, cnt = 0;
    for (let i = 0; i < s.length; i++) {
      const x = s[i];
      if (!isN(x)) { out[i] = prev; continue; }
      if (isN(prev)) { prev = a * x + (1 - a) * prev; out[i] = prev; continue; }
      seed += x; cnt++;
      if (cnt === n) { prev = seed / n; out[i] = prev; }
    }
    return out;
  };
  T.rma = (s, n) => T.ema(s, n, 1 / n);           // trung bình Wilder
  T.wma = function (s, n) {
    const out = T.arr(s.length), den = n * (n + 1) / 2;
    for (let i = n - 1; i < s.length; i++) {
      let sum = 0, ok = true;
      for (let j = 0; j < n; j++) { const x = s[i - j]; if (!isN(x)) { ok = false; break; } sum += x * (n - j); }
      if (ok) out[i] = sum / den;
    }
    return out;
  };
  T.hma = (s, n) => T.wma(T.sub(T.mul(T.wma(s, Math.floor(n / 2)), 2), T.wma(s, n)), Math.round(Math.sqrt(n)));
  T.dema = (s, n) => { const e = T.ema(s, n); return T.sub(T.mul(e, 2), T.ema(e, n)); };
  T.tema = (s, n) => { const e1 = T.ema(s, n), e2 = T.ema(e1, n), e3 = T.ema(e2, n); return e1.map((v, i) => 3 * v - 3 * e2[i] + e3[i]); };
  T.vwma = (s, v, n) => T.div(T.sma(T.mul(s, v), n), T.sma(v, n));
  T.alma = function (s, n, offset = 0.85, sigma = 6) {
    const out = T.arr(s.length), m = offset * (n - 1), sd = n / sigma, w = [];
    let norm = 0;
    for (let j = 0; j < n; j++) { w[j] = Math.exp(-((j - m) ** 2) / (2 * sd * sd)); norm += w[j]; }
    for (let i = n - 1; i < s.length; i++) {
      let sum = 0;
      for (let j = 0; j < n; j++) sum += w[j] * s[i - (n - 1 - j)];
      out[i] = sum / norm;
    }
    return out;
  };
  T.linreg = function (s, n, offset = 0) {
    const out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) {
      let sx = 0, sy = 0, sxy = 0, sxx = 0, ok = true;
      for (let j = 0; j < n; j++) {
        const y = s[i - n + 1 + j]; if (!isN(y)) { ok = false; break; }
        sx += j; sy += y; sxy += j * y; sxx += j * j;
      }
      if (!ok) continue;
      const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx), icpt = (sy - slope * sx) / n;
      out[i] = icpt + slope * (n - 1 - offset);
    }
    return out;
  };
  T.mcginley = function (s, n) {
    const out = T.arr(s.length), e = T.ema(s, n);
    let prev = N;
    for (let i = 0; i < s.length; i++) {
      if (!isN(prev)) { prev = e[i]; out[i] = prev; continue; }
      prev = prev + (s[i] - prev) / (n * Math.pow(s[i] / prev, 4));
      out[i] = prev;
    }
    return out;
  };
  // Chọn kiểu trung bình theo tên
  T.ma = function (type, s, n, v) {
    switch (type) {
      case 'EMA': return T.ema(s, n); case 'WMA': return T.wma(s, n); case 'RMA': case 'SMMA': return T.rma(s, n);
      case 'HMA': return T.hma(s, n); case 'VWMA': return T.vwma(s, v, n); case 'DEMA': return T.dema(s, n); case 'TEMA': return T.tema(s, n);
      default: return T.sma(s, n);
    }
  };
  T.MA_TYPES = ['SMA', 'EMA', 'WMA', 'RMA', 'HMA', 'VWMA', 'DEMA', 'TEMA'];

  /* ---------- Phép toán mảng ---------- */
  const bin = f => (a, b) => (Array.isArray(a) ? a : null)
    ? a.map((x, i) => f(x, Array.isArray(b) ? b[i] : b))
    : b.map(y => f(a, y));
  T.add = bin((x, y) => x + y); T.sub = bin((x, y) => x - y); T.mul = bin((x, y) => x * y);
  T.div = bin((x, y) => (y === 0 ? N : x / y));
  T.shift = (s, k) => s.map((_, i) => (i - k >= 0 && i - k < s.length ? s[i - k] : N));
  T.change = (s, k = 1) => s.map((x, i) => (i >= k ? x - s[i - k] : N));
  T.sum = function (s, n) {
    const out = T.arr(s.length); let sum = 0;
    for (let i = 0; i < s.length; i++) { sum += T.nz(s[i]); if (i >= n) sum -= T.nz(s[i - n]); if (i >= n - 1) out[i] = sum; }
    return out;
  };
  T.cum = s => { let a = 0; return s.map(x => (a += T.nz(x))); };
  T.highest = function (s, n) {
    const out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) { let m = -Infinity; for (let j = i - n + 1; j <= i; j++) if (s[j] > m) m = s[j]; out[i] = m; }
    return out;
  };
  T.lowest = function (s, n) {
    const out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) { let m = Infinity; for (let j = i - n + 1; j <= i; j++) if (s[j] < m) m = s[j]; out[i] = m; }
    return out;
  };
  T.highestbars = function (s, n) {
    const out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) { let m = -Infinity, k = 0; for (let j = i - n + 1; j <= i; j++) if (s[j] >= m) { m = s[j]; k = j; } out[i] = k - i; }
    return out;
  };
  T.lowestbars = function (s, n) {
    const out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) { let m = Infinity, k = 0; for (let j = i - n + 1; j <= i; j++) if (s[j] <= m) { m = s[j]; k = j; } out[i] = k - i; }
    return out;
  };
  T.stdev = function (s, n) {
    const m = T.sma(s, n), out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) {
      if (!isN(m[i])) continue;
      let v = 0; for (let j = i - n + 1; j <= i; j++) v += (s[j] - m[i]) ** 2;
      out[i] = Math.sqrt(v / n);
    }
    return out;
  };
  T.dev = function (s, n) { // độ lệch tuyệt đối trung bình
    const m = T.sma(s, n), out = T.arr(s.length);
    for (let i = n - 1; i < s.length; i++) { let v = 0; for (let j = i - n + 1; j <= i; j++) v += Math.abs(s[j] - m[i]); out[i] = v / n; }
    return out;
  };
  T.correlation = function (a, b, n) {
    const out = T.arr(a.length);
    for (let i = n - 1; i < a.length; i++) {
      let sa = 0, sb = 0, saa = 0, sbb = 0, sab = 0;
      for (let j = i - n + 1; j <= i; j++) { sa += a[j]; sb += b[j]; saa += a[j] * a[j]; sbb += b[j] * b[j]; sab += a[j] * b[j]; }
      const cov = sab / n - (sa / n) * (sb / n), va = saa / n - (sa / n) ** 2, vb = sbb / n - (sb / n) ** 2;
      out[i] = va > 0 && vb > 0 ? cov / Math.sqrt(va * vb) : N;
    }
    return out;
  };
  T.percentrank = function (s, n) {
    const out = T.arr(s.length);
    for (let i = n; i < s.length; i++) { let c = 0; for (let j = i - n; j < i; j++) if (s[j] <= s[i]) c++; out[i] = c / n * 100; }
    return out;
  };

  /* ---------- Biến động ---------- */
  T.tr = function (D) {
    return D.c.map((_, i) => i === 0 ? D.h[i] - D.l[i] : Math.max(D.h[i] - D.l[i], Math.abs(D.h[i] - D.c[i - 1]), Math.abs(D.l[i] - D.c[i - 1])));
  };
  T.atr = (D, n) => T.rma(T.tr(D), n);

  /* ---------- Dao động phổ biến ---------- */
  T.rsi = function (s, n) {
    const up = T.rma(s.map((x, i) => (i ? Math.max(x - s[i - 1], 0) : N)), n);
    const dn = T.rma(s.map((x, i) => (i ? Math.max(s[i - 1] - x, 0) : N)), n);
    return up.map((u, i) => (dn[i] === 0 ? 100 : u === 0 ? 0 : 100 - 100 / (1 + u / dn[i])));
  };
  T.stoch = function (s, h, l, n) {
    const hh = T.highest(h, n), ll = T.lowest(l, n);
    return s.map((x, i) => (hh[i] - ll[i] === 0 ? N : 100 * (x - ll[i]) / (hh[i] - ll[i])));
  };
  T.cci = (s, n) => { const m = T.sma(s, n), d = T.dev(s, n); return s.map((x, i) => (x - m[i]) / (0.015 * d[i])); };
  T.roc = (s, n) => s.map((x, i) => (i >= n ? 100 * (x - s[i - n]) / s[i - n] : N));
  T.mom = (s, n) => T.change(s, n);
  T.dmi = function (D, n, smooth) {
    const pdm = [], mdm = [];
    for (let i = 0; i < D.n; i++) {
      if (!i) { pdm.push(N); mdm.push(N); continue; }
      const up = D.h[i] - D.h[i - 1], dn = D.l[i - 1] - D.l[i];
      pdm.push(up > dn && up > 0 ? up : 0); mdm.push(dn > up && dn > 0 ? dn : 0);
    }
    const tr = T.rma(T.tr(D).map((x, i) => (i ? x : N)), n);
    const plus = T.rma(pdm, n).map((x, i) => 100 * x / tr[i]);
    const minus = T.rma(mdm, n).map((x, i) => 100 * x / tr[i]);
    const dx = plus.map((p, i) => { const s = p + minus[i]; return s === 0 ? 0 : 100 * Math.abs(p - minus[i]) / s; });
    return { plus, minus, adx: T.rma(dx, smooth || n) };
  };
  T.obv = D => { let a = 0; return D.c.map((x, i) => (i ? (a += x > D.c[i - 1] ? D.v[i] : x < D.c[i - 1] ? -D.v[i] : 0) : (a = 0))); };
  T.mfi = function (D, n) {
    const tp = D.hlc3, pos = [], neg = [];
    for (let i = 0; i < D.n; i++) {
      const mf = tp[i] * D.v[i];
      pos.push(i && tp[i] > tp[i - 1] ? mf : 0); neg.push(i && tp[i] < tp[i - 1] ? mf : 0);
    }
    const sp = T.sum(pos, n), sn = T.sum(neg, n);
    return sp.map((p, i) => (sn[i] === 0 ? 100 : 100 - 100 / (1 + p / sn[i])));
  };
  T.sar = function (D, start = 0.02, inc = 0.02, max = 0.2) {
    const out = T.arr(D.n); if (D.n < 2) return out;
    let up = D.c[1] >= D.c[0], af = start, ep = up ? D.h[0] : D.l[0], sar = up ? D.l[0] : D.h[0];
    for (let i = 1; i < D.n; i++) {
      sar = sar + af * (ep - sar);
      if (up) {
        sar = Math.min(sar, D.l[i - 1], i > 1 ? D.l[i - 2] : D.l[i - 1]);
        if (D.l[i] < sar) { up = false; sar = ep; ep = D.l[i]; af = start; }
        else if (D.h[i] > ep) { ep = D.h[i]; af = Math.min(af + inc, max); }
      } else {
        sar = Math.max(sar, D.h[i - 1], i > 1 ? D.h[i - 2] : D.h[i - 1]);
        if (D.h[i] > sar) { up = true; sar = ep; ep = D.h[i]; af = start; }
        else if (D.l[i] < ep) { ep = D.l[i]; af = Math.min(af + inc, max); }
      }
      out[i] = sar;
    }
    return out;
  };
  T.supertrend = function (D, factor, n) {
    const atr = T.atr(D, n), st = T.arr(D.n), dir = T.arr(D.n);
    let ub = N, lb = N, d = 1;
    for (let i = 0; i < D.n; i++) {
      if (!isN(atr[i])) continue;
      const up = D.hl2[i] + factor * atr[i], dn = D.hl2[i] - factor * atr[i];
      const pub = ub, plb = lb;
      lb = isN(plb) && (dn < plb && D.c[i - 1] > plb) ? plb : dn;
      ub = isN(pub) && (up > pub && D.c[i - 1] < pub) ? pub : up;
      if (isN(pub)) d = d === -1 ? (D.c[i] > ub ? 1 : -1) : (D.c[i] < lb ? -1 : 1);
      st[i] = d === 1 ? lb : ub; dir[i] = d;
    }
    return { st, dir };
  };
  T.vwap = function (D, anchor = 'D') {
    const out = T.arr(D.n), up = T.arr(D.n), lo = T.arr(D.n);
    let pv = 0, vv = 0, pv2 = 0, key = null;
    for (let i = 0; i < D.n; i++) {
      const k = T.periodKey(D.t[i], anchor);
      if (k !== key) { pv = vv = pv2 = 0; key = k; }
      const p = D.hlc3[i], v = D.v[i] || 1;
      pv += p * v; vv += v; pv2 += p * p * v;
      out[i] = pv / vv;
      const sd = Math.sqrt(Math.max(0, pv2 / vv - out[i] ** 2));
      up[i] = out[i] + sd; lo[i] = out[i] - sd;
    }
    return { vwap: out, sd: up.map((u, i) => u - out[i]) };
  };
  // Khoá theo kỳ (ngày/tuần/tháng/quý/năm) để reset VWAP, pivot…
  T.periodKey = function (t, p) {
    const d = new Date(t * 1000);
    const y = d.getUTCFullYear(), m = d.getUTCMonth();
    switch (p) {
      case 'W': return Math.floor((t / 86400 + 3) / 7);
      case 'M': return y * 12 + m;
      case 'Q': return y * 4 + Math.floor(m / 3);
      case 'Y': return y;
      case '4H': return Math.floor(t / 14400);
      case '1H': return Math.floor(t / 3600);
      default: return Math.floor(t / 86400);
    }
  };

  /* ---------- Đỉnh / đáy (pivot) ---------- */
  T.pivothigh = function (s, L, R) {
    const out = T.arr(s.length);
    for (let i = L; i < s.length - R; i++) {
      let ok = true;
      for (let j = i - L; j <= i + R && ok; j++) if (j !== i && (s[j] > s[i] || (j > i && s[j] === s[i]))) ok = false;
      if (ok) out[i] = s[i];
    }
    return out;
  };
  T.pivotlow = function (s, L, R) {
    const out = T.arr(s.length);
    for (let i = L; i < s.length - R; i++) {
      let ok = true;
      for (let j = i - L; j <= i + R && ok; j++) if (j !== i && (s[j] < s[i] || (j > i && s[j] === s[i]))) ok = false;
      if (ok) out[i] = s[i];
    }
    return out;
  };
  // ZigZag: danh sách đỉnh/đáy xen kẽ, đổi chiều khi giá đi ngược >= dev%
  T.zigzag = function (D, devPct = 5, depth = 10) {
    const pts = [];
    if (D.n < 2) return pts;
    let dir = 0, ext = { i: 0, p: D.c[0] };
    for (let i = 1; i < D.n; i++) {
      const h = D.h[i], l = D.l[i];
      if (dir >= 0) {
        if (h >= ext.p || dir === 0 && h > ext.p) { ext = { i, p: h }; if (dir === 0) dir = 1; }
        if (dir === 1 && (ext.p - l) / ext.p * 100 >= devPct && i - ext.i >= 0) {
          pts.push({ i: ext.i, p: ext.p, hi: true }); dir = -1; ext = { i, p: l }; continue;
        }
      }
      if (dir <= 0) {
        if (l <= ext.p) { ext = { i, p: l }; if (dir === 0) dir = -1; }
        if (dir === -1 && (h - ext.p) / ext.p * 100 >= devPct) {
          pts.push({ i: ext.i, p: ext.p, hi: false }); dir = 1; ext = { i, p: h };
        }
      }
    }
    pts.push({ i: ext.i, p: ext.p, hi: dir === 1, last: true });
    // bỏ các điểm quá gần nhau (độ sâu)
    return pts.filter((p, k) => k === 0 || p.last || p.i - pts[k - 1].i >= Math.min(depth, 2));
  };
  // Tự chọn độ lệch zigzag hợp với biến động của mã
  T.autoDev = function (D) {
    const a = T.atr(D, 14), last = a[a.length - 1], c = D.c[D.n - 1];
    return Math.max(0.3, Math.min(15, (last / c) * 100 * 3));
  };

  T.crossover = (a, b, i) => i > 0 && a[i] > (Array.isArray(b) ? b[i] : b) && a[i - 1] <= (Array.isArray(b) ? b[i - 1] : b);
  T.crossunder = (a, b, i) => i > 0 && a[i] < (Array.isArray(b) ? b[i] : b) && a[i - 1] >= (Array.isArray(b) ? b[i - 1] : b);
  T.isN = isN;
})(window.App);
