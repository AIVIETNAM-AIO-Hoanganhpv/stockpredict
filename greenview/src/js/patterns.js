/* =========================================================
 * patterns.js — Mô hình nến Nhật (44 mẫu) và mô hình biểu đồ tự động
 * Mỗi mô hình được đăng ký như một chỉ báo (nhóm "Mô hình"), vẽ bằng nhãn/hình.
 * ========================================================= */
(function (App) {
  'use strict';
  const T = App.ta, DEFS = App.INDICATORS, isN = T.isN;
  const UP = '#089981', DN = '#f23645', NEU = '#787b86';

  /* ---------- Thông số nến dùng chung ---------- */
  function feats(D) {
    const body = D.c.map((c, i) => Math.abs(c - D.o[i]));
    const bodyAvg = T.ema(body, 14), sma50 = T.sma(D.c, 50);
    const F = i => {
      const o = D.o[i], c = D.c[i], h = D.h[i], l = D.l[i], b = body[i], r = h - l || 1e-12;
      const top = Math.max(o, c), bot = Math.min(o, c);
      return { o, c, h, l, b, r, top, bot, up: h - top, dn: bot - l, white: c > o, black: c < o,
        small: b < (bodyAvg[i] || b), long: b > (bodyAvg[i] || b), doji: b <= r * 0.05, mid: (o + c) / 2,
        upTrend: c > sma50[i], downTrend: c < sma50[i] };
    };
    return F;
  }

  // Định nghĩa từng mô hình: [id, tên, hướng, số nến, hàm(F, i) -> true/false]
  const CANDLES = [
    ['abandonedbear', 'Abandoned baby (bearish)', -1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.upTrend && a.white && a.long && b.doji && b.l > a.h && c.black && c.h < b.l; }],
    ['abandonedbull', 'Abandoned baby (bullish)', 1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.downTrend && a.black && a.long && b.doji && b.h < a.l && c.white && c.l > b.h; }],
    ['darkcloud', 'Dark cloud cover (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && a.long && b.black && b.o >= a.h && b.c < a.mid && b.c > a.o; }],
    ['doji', 'Doji (neutral)', 0, 1, (F, i) => { const a = F(i); return a.doji && !(a.dn > a.r * 0.7) && !(a.up > a.r * 0.7); }],
    ['dojistarbear', 'Doji star (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && a.long && b.doji && b.bot > a.top; }],
    ['dojistarbull', 'Doji star (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.long && b.doji && b.top < a.bot; }],
    ['tasukidown', 'Downside Tasuki gap (bearish)', -1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.downTrend && a.black && a.long && b.black && b.top < a.bot && c.white && c.o < b.top && c.o > b.bot && c.c > b.top && c.c < a.bot; }],
    ['dragonfly', 'Dragonfly Doji (bullish)', 1, 1, (F, i) => { const a = F(i); return a.doji && a.downTrend && a.dn > a.r * 0.7 && a.up <= a.r * 0.05; }],
    ['engulfbear', 'Engulfing (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && a.small && b.black && b.long && b.top >= a.top && b.bot <= a.bot && (b.top > a.top || b.bot < a.bot); }],
    ['engulfbull', 'Engulfing (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.small && b.white && b.long && b.top >= a.top && b.bot <= a.bot && (b.top > a.top || b.bot < a.bot); }],
    ['eveningdoji', 'Evening Doji star (bearish)', -1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.upTrend && a.white && a.long && b.doji && b.bot > a.top && c.black && c.c < a.mid; }],
    ['eveningstar', 'Evening star (bearish)', -1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.upTrend && a.white && a.long && b.small && !b.doji && b.bot > a.top && c.black && c.long && c.c < a.mid; }],
    ['fall3', 'Falling three methods (bearish)', -1, 5, (F, i) => { const a = F(i - 4), x = [F(i - 3), F(i - 2), F(i - 1)], e = F(i); return a.downTrend && a.black && a.long && x.every(k => k.small && k.h < a.h && k.l > a.l) && x[0].white && x[2].white && e.black && e.long && e.c < a.c; }],
    ['fallwindow', 'Falling window (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && b.h < a.l && a.r > 0 && b.r > 0; }],
    ['gravestone', 'Gravestone Doji (bearish)', -1, 1, (F, i) => { const a = F(i); return a.doji && a.upTrend && a.up > a.r * 0.7 && a.dn <= a.r * 0.05; }],
    ['hammer', 'Hammer (bullish)', 1, 1, (F, i) => { const a = F(i); return a.downTrend && a.small && a.b > 0 && a.dn >= 2 * a.b && a.up <= a.b * 0.3; }],
    ['hangingman', 'Hanging man (bearish)', -1, 1, (F, i) => { const a = F(i); return a.upTrend && a.small && a.b > 0 && a.dn >= 2 * a.b && a.up <= a.b * 0.3; }],
    ['haramibear', 'Harami (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && a.long && b.black && b.small && b.top <= a.top && b.bot >= a.bot && !b.doji; }],
    ['haramibull', 'Harami (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.long && b.white && b.small && b.top <= a.top && b.bot >= a.bot && !b.doji; }],
    ['haramicrossbear', 'Harami cross (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && a.long && b.doji && b.h <= a.top && b.l >= a.bot; }],
    ['haramicrossbull', 'Harami cross (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.long && b.doji && b.h <= a.top && b.l >= a.bot; }],
    ['invhammer', 'Inverted hammer (bullish)', 1, 1, (F, i) => { const a = F(i); return a.downTrend && a.small && a.b > 0 && a.up >= 2 * a.b && a.dn <= a.b * 0.3; }],
    ['kickbear', 'Kicking (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.white && a.long && a.up < a.r * 0.05 && a.dn < a.r * 0.05 && b.black && b.long && b.up < b.r * 0.05 && b.dn < b.r * 0.05 && b.h < a.l; }],
    ['kickbull', 'Kicking (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.black && a.long && a.up < a.r * 0.05 && a.dn < a.r * 0.05 && b.white && b.long && b.up < b.r * 0.05 && b.dn < b.r * 0.05 && b.l > a.h; }],
    ['longlower', 'Long lower shadow (bullish)', 1, 1, (F, i) => { const a = F(i); return a.dn > a.r * 0.75; }],
    ['longupper', 'Long upper shadow (bearish)', -1, 1, (F, i) => { const a = F(i); return a.up > a.r * 0.75; }],
    ['marublack', 'Marubozu black (bearish)', -1, 1, (F, i) => { const a = F(i); return a.black && a.long && a.up < a.b * 0.05 && a.dn < a.b * 0.05; }],
    ['maruwhite', 'Marubozu white (bullish)', 1, 1, (F, i) => { const a = F(i); return a.white && a.long && a.up < a.b * 0.05 && a.dn < a.b * 0.05; }],
    ['morningdoji', 'Morning Doji star (bullish)', 1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.downTrend && a.black && a.long && b.doji && b.top < a.bot && c.white && c.c > a.mid; }],
    ['morningstar', 'Morning star (bullish)', 1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.downTrend && a.black && a.long && b.small && !b.doji && b.top < a.bot && c.white && c.long && c.c > a.mid; }],
    ['onneck', 'On-neck (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.long && b.white && b.o < a.c && b.small && Math.abs(b.c - a.l) <= a.r * 0.05; }],
    ['piercing', 'Piercing (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && a.long && b.white && b.o <= a.l && b.c > a.mid && b.c < a.o; }],
    ['rise3', 'Rising three methods (bullish)', 1, 5, (F, i) => { const a = F(i - 4), x = [F(i - 3), F(i - 2), F(i - 1)], e = F(i); return a.upTrend && a.white && a.long && x.every(k => k.small && k.h < a.h && k.l > a.l) && x[0].black && x[2].black && e.white && e.long && e.c > a.c; }],
    ['risewindow', 'Rising window (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && b.l > a.h && a.r > 0 && b.r > 0; }],
    ['shootingstar', 'Shooting star (bearish)', -1, 1, (F, i) => { const a = F(i); return a.upTrend && a.small && a.b > 0 && a.up >= 2 * a.b && a.dn <= a.b * 0.3; }],
    ['spinblack', 'Spinning top black (neutral)', 0, 1, (F, i) => { const a = F(i); return a.black && a.up >= a.b && a.dn >= a.b && a.b > a.r * 0.05; }],
    ['spinwhite', 'Spinning top white (neutral)', 0, 1, (F, i) => { const a = F(i); return a.white && a.up >= a.b && a.dn >= a.b && a.b > a.r * 0.05; }],
    ['3crows', 'Three black crows (bearish)', -1, 3, (F, i) => { const x = [F(i - 2), F(i - 1), F(i)]; return x.every(k => k.black && k.long && k.dn < k.r * 0.15) && x[1].o < x[0].o && x[1].o > x[0].c && x[2].o < x[1].o && x[2].o > x[1].c && x[2].c < x[1].c; }],
    ['3soldiers', 'Three white soldiers (bullish)', 1, 3, (F, i) => { const x = [F(i - 2), F(i - 1), F(i)]; return x.every(k => k.white && k.long && k.up < k.r * 0.15) && x[1].o > x[0].o && x[1].o < x[0].c && x[2].o > x[1].o && x[2].o < x[1].c && x[2].c > x[1].c; }],
    ['tristarbear', 'Tri-star (bearish)', -1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.upTrend && a.doji && b.doji && c.doji && b.bot > a.top && c.top < b.bot; }],
    ['tristarbull', 'Tri-star (bullish)', 1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.downTrend && a.doji && b.doji && c.doji && b.top < a.bot && c.bot > b.top; }],
    ['tweezerbot', 'Tweezer bottom (bullish)', 1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.downTrend && a.black && b.white && Math.abs(a.l - b.l) <= Math.max(a.b, b.b) * 0.05 && !a.doji && !b.doji; }],
    ['tweezertop', 'Tweezer top (bearish)', -1, 2, (F, i) => { const a = F(i - 1), b = F(i); return a.upTrend && a.white && b.black && Math.abs(a.h - b.h) <= Math.max(a.b, b.b) * 0.05 && !a.doji && !b.doji; }],
    ['tasukiup', 'Upside Tasuki gap (bullish)', 1, 3, (F, i) => { const a = F(i - 2), b = F(i - 1), c = F(i); return a.upTrend && a.white && a.long && b.white && b.bot > a.top && c.black && c.o > b.bot && c.o < b.top && c.c < b.bot && c.c > a.top; }]
  ];
  App.CANDLE_LIST = CANDLES;

  // Rút gọn tên để làm nhãn trên biểu đồ
  const short = name => name.replace(/\s*\((bearish|bullish|neutral)\)/, '').replace(/Doji star/, 'Doji★').slice(0, 14);
  function scan(D, list) {
    const F = feats(D), mk = [];
    for (let i = 5; i < D.n; i++) {
      for (const [, name, dir, k, fn] of list) {
        if (i - k + 1 < 0) continue;
        let hit = false; try { hit = fn(F, i); } catch (e) {}
        if (hit) { mk.push({ i, pos: dir < 0 ? 'aboveBar' : dir > 0 ? 'belowBar' : 'aboveBar', shape: dir < 0 ? 'arrowDown' : dir > 0 ? 'arrowUp' : 'circle', color: dir < 0 ? DN : dir > 0 ? UP : NEU, text: short(name) }); break; }
      }
    }
    return mk;
  }
  DEFS.allcandles = { id: 'allcandles', name: 'All candlestick patterns', cat: 'pattern', sub: 'candle', overlay: true, inputs: [], plots: [], levels: [], calc(D) { return { markers: scan(D, CANDLES) }; } };
  CANDLES.forEach(c => {
    DEFS['cp_' + c[0]] = { id: 'cp_' + c[0], name: c[1], cat: 'pattern', sub: 'candle', overlay: true, inputs: [], plots: [], levels: [], calc(D) { return { markers: scan(D, [c]) }; } };
  });

  /* =========================================================
   * Mô hình biểu đồ — dò trên các đỉnh/đáy ZigZag
   * ========================================================= */
  function pivots(D, I) { return T.zigzag(D, I && I.dev > 0 ? I.dev : T.autoDev(D), 5); }
  const near = (a, b, tol) => Math.abs(a - b) <= tol;
  const slope = (p, q) => (q.p - p.p) / (q.i - p.i || 1);

  const FINDERS = {
    doubletop(P, tol) { const r = []; for (let k = 2; k < P.length; k++) { const [a, b, c] = P.slice(k - 2, k + 1); if (a.hi && c.hi && near(a.p, c.p, tol) && a.p - b.p > 2 * tol) r.push({ pts: [a, b, c], name: 'Hai đỉnh', col: DN, neck: b.p }); } return r; },
    doublebottom(P, tol) { const r = []; for (let k = 2; k < P.length; k++) { const [a, b, c] = P.slice(k - 2, k + 1); if (!a.hi && !c.hi && near(a.p, c.p, tol) && b.p - a.p > 2 * tol) r.push({ pts: [a, b, c], name: 'Hai đáy', col: UP, neck: b.p }); } return r; },
    tripletop(P, tol) { const r = []; for (let k = 4; k < P.length; k++) { const s = P.slice(k - 4, k + 1); if (s[0].hi && near(s[0].p, s[2].p, tol) && near(s[2].p, s[4].p, tol) && s[0].p - Math.max(s[1].p, s[3].p) > 2 * tol) r.push({ pts: s, name: 'Ba đỉnh', col: DN, neck: Math.min(s[1].p, s[3].p) }); } return r; },
    triplebottom(P, tol) { const r = []; for (let k = 4; k < P.length; k++) { const s = P.slice(k - 4, k + 1); if (!s[0].hi && near(s[0].p, s[2].p, tol) && near(s[2].p, s[4].p, tol) && Math.min(s[1].p, s[3].p) - s[0].p > 2 * tol) r.push({ pts: s, name: 'Ba đáy', col: UP, neck: Math.max(s[1].p, s[3].p) }); } return r; },
    hs(P, tol) { const r = []; for (let k = 4; k < P.length; k++) { const s = P.slice(k - 4, k + 1); if (s[0].hi && s[2].p > s[0].p + tol && s[2].p > s[4].p + tol && near(s[0].p, s[4].p, 2 * tol)) r.push({ pts: s, name: 'Vai-Đầu-Vai', col: DN, neckLine: [s[1], s[3]] }); } return r; },
    ihs(P, tol) { const r = []; for (let k = 4; k < P.length; k++) { const s = P.slice(k - 4, k + 1); if (!s[0].hi && s[2].p < s[0].p - tol && s[2].p < s[4].p - tol && near(s[0].p, s[4].p, 2 * tol)) r.push({ pts: s, name: 'VĐV ngược', col: UP, neckLine: [s[1], s[3]] }); } return r; },
    _shape(P, tol, kind) {
      const r = [];
      for (let k = 5; k < P.length; k++) {
        const s = P.slice(k - 5, k + 1), H = s.filter(p => p.hi), L = s.filter(p => !p.hi);
        if (H.length < 2 || L.length < 2) continue;
        const sh = slope(H[0], H[H.length - 1]), sl = slope(L[0], L[L.length - 1]), span = s[5].i - s[0].i, eps = tol / span;
        const flatH = Math.abs(sh) < eps, flatL = Math.abs(sl) < eps;
        let name = null, col = NEU;
        if (kind === 'rect' && flatH && flatL) name = 'Chữ nhật';
        if (kind === 'tri' && ((sh < -eps && sl > eps) || (flatH && sl > eps) || (sh < -eps && flatL))) { name = flatH ? 'Tam giác tăng' : flatL ? 'Tam giác giảm' : 'Tam giác cân'; col = flatH ? UP : flatL ? DN : NEU; }
        if (kind === 'rwedge' && sh > eps && sl > eps && sl > sh) { name = 'Nêm tăng'; col = DN; }
        if (kind === 'fwedge' && sh < -eps && sl < -eps && sh < sl) { name = 'Nêm giảm'; col = UP; }
        if (name) r.push({ pts: s, name, col, lines: [[H[0], H[H.length - 1]], [L[0], L[L.length - 1]]] });
      }
      return r;
    },
    flag(P, tol, D, bull, pennant) {
      const r = [], atr = T.atr(D, 14);
      for (let k = 4; k < P.length; k++) {
        const pole0 = P[k - 4], pole1 = P[k - 3], s = P.slice(k - 3, k + 1);
        const move = pole1.p - pole0.p, a = atr[pole1.i] || tol;
        if (bull ? move < 4 * a : move > -4 * a) continue;
        if (pole1.i - pole0.i > 25) continue;
        const rng = Math.max(...s.map(p => p.p)) - Math.min(...s.map(p => p.p));
        if (rng > Math.abs(move) * 0.5) continue;
        const H = s.filter(p => p.hi), L = s.filter(p => !p.hi); if (H.length < 2 || L.length < 2) continue;
        const conv = Math.abs(H[1].p - L[1].p) < Math.abs(H[0].p - L[0].p) * 0.7;
        if (!!pennant !== conv) continue;
        r.push({ pts: [pole0, pole1], name: (pennant ? 'Cờ đuôi nheo ' : 'Cờ ') + (bull ? 'tăng' : 'giảm'), col: bull ? UP : DN, lines: [[H[0], H[1]], [L[0], L[1]]] });
      }
      return r;
    },
    cup(P, tol, D, inv) {
      const r = [];
      for (let k = 3; k < P.length; k++) {
        const [a, b, c, d] = P.slice(k - 3, k + 1);
        if (inv ? (a.hi || !b.hi || c.hi || !d.hi) : (!a.hi || b.hi || !c.hi || d.hi)) continue;
        const depth = Math.abs(a.p - b.p), w = c.i - a.i;
        if (!near(a.p, c.p, 2 * tol) || w < 15 || depth < 3 * tol) continue;
        if (Math.abs(c.p - d.p) > depth * 0.5 || d.i - c.i > w * 0.5) continue;
        if (Math.abs((b.i - a.i) / w - 0.5) > 0.25) continue;
        r.push({ pts: [a, b, c, d], name: inv ? 'Cốc tay cầm ngược' : 'Cốc tay cầm', col: inv ? DN : UP, curve: true });
      }
      return r;
    },
    elliott(P) {
      const r = [];
      for (let k = 5; k < P.length; k++) {
        const s = P.slice(k - 5, k + 1), up = !s[0].hi, p = s.map(x => up ? x.p : -x.p);
        const w1 = p[1] - p[0], w3 = p[3] - p[2], w5 = p[5] - p[4];
        if (p[2] > p[0] && p[3] > p[1] && p[4] > p[1] && p[5] > p[3] && !(w3 < w1 && w3 < w5))
          r.push({ pts: s, name: 'Sóng Elliott', col: '#2962ff', nums: true });
      }
      return r;
    }
  };

  function drawFound(g, X, list) {
    list.forEach(f => {
      const pts = f.pts.map(q => [X.x(q.i), X.y(q.p)]);
      if (f.curve) {
        g.strokeStyle = f.col; g.lineWidth = 2; g.beginPath(); g.moveTo(...pts[0]); g.quadraticCurveTo(pts[1][0], pts[1][1] + (pts[1][1] - pts[0][1]) * 0.4, ...pts[2]); g.lineTo(...pts[3]); g.stroke();
      } else X.poly(g, pts, f.col, null, 2);
      g.globalAlpha = 0.08; g.fillStyle = f.col; g.beginPath(); pts.forEach((p, k) => k ? g.lineTo(...p) : g.moveTo(...p)); g.fill(); g.globalAlpha = 1;
      if (f.neck != null) X.seg(g, pts[0][0], X.y(f.neck), pts[pts.length - 1][0] + 30, X.y(f.neck), f.col, [5, 4]);
      if (f.neckLine) { const [a, b] = f.neckLine; const s = slope(a, b), i2 = f.pts[f.pts.length - 1].i + 10; X.seg(g, X.x(a.i), X.y(a.p), X.x(i2), X.y(a.p + s * (i2 - a.i)), f.col, [5, 4]); }
      if (f.lines) f.lines.forEach(([a, b]) => X.seg(g, X.x(a.i), X.y(a.p), X.x(b.i), X.y(b.p), f.col, [3, 3], 1.5));
      if (f.nums) f.pts.forEach((q, k) => X.label(g, X.x(q.i), X.y(q.p) + (q.hi ? -12 : 12), String(k), f.col));
      const top = Math.min(...pts.map(p => p[1]));
      X.label(g, pts[Math.floor(pts.length / 2)][0], top - 16, f.name, f.col);
    });
  }

  const CHART = [
    ['bearflag', 'Bearish flag chart pattern', (P, t, D) => FINDERS.flag(P, t, D, false, false)],
    ['bullflag', 'Bullish flag chart pattern', (P, t, D) => FINDERS.flag(P, t, D, true, false)],
    ['cuphandle', 'Cup and handle chart pattern', (P, t, D) => FINDERS.cup(P, t, D, false)],
    ['invcup', 'Inverted cup and handle chart pattern', (P, t, D) => FINDERS.cup(P, t, D, true)],
    ['doublebottom', 'Double bottom chart pattern', (P, t) => FINDERS.doublebottom(P, t)],
    ['doubletop', 'Double top chart pattern', (P, t) => FINDERS.doubletop(P, t)],
    ['elliott', 'Elliott wave chart pattern', P => FINDERS.elliott(P)],
    ['hs', 'Head and shoulders chart pattern', (P, t) => FINDERS.hs(P, t)],
    ['ihs', 'Inverted head and shoulders chart pattern', (P, t) => FINDERS.ihs(P, t)],
    ['bearpennant', 'Bearish pennant chart pattern', (P, t, D) => FINDERS.flag(P, t, D, false, true)],
    ['bullpennant', 'Bullish pennant chart pattern', (P, t, D) => FINDERS.flag(P, t, D, true, true)],
    ['rect', 'Rectangle chart pattern', (P, t) => FINDERS._shape(P, t, 'rect')],
    ['triangle', 'Triangle chart pattern', (P, t) => FINDERS._shape(P, t, 'tri')],
    ['triplebottom', 'Triple bottom chart pattern', (P, t) => FINDERS.triplebottom(P, t)],
    ['tripletop', 'Triple top chart pattern', (P, t) => FINDERS.tripletop(P, t)],
    ['fwedge', 'Falling wedge chart pattern', (P, t) => FINDERS._shape(P, t, 'fwedge')],
    ['rwedge', 'Rising wedge chart pattern', (P, t) => FINDERS._shape(P, t, 'rwedge')]
  ];
  // Loại bỏ mô hình trùng lặp (giữ cái mới nhất, không chồng lấn)
  function dedupe(list, max) {
    const out = [];
    list.sort((a, b) => b.pts[b.pts.length - 1].i - a.pts[a.pts.length - 1].i).forEach(f => {
      const a = f.pts[0].i, b = f.pts[f.pts.length - 1].i;
      if (!out.some(o => !(b < o.pts[0].i || a > o.pts[o.pts.length - 1].i))) out.push(f);
    });
    return out.slice(0, max);
  }
  const chartInputs = [['dev', 'Độ lệch % (0 = tự động)', 0, 'float'], ['max', 'Số mô hình tối đa', 6, 'int']];
  function runChart(D, I, finders) {
    const P = pivots(D, I), tol = T.atr(D, 14)[D.n - 1] * 0.8 || D.c[D.n - 1] * 0.01;
    let found = []; finders.forEach(f => { found = found.concat(f[2](P, tol, D)); });
    const show = dedupe(found, I.max);
    return { draw(g, X) { drawFound(g, X, show); }, found: show };
  }
  DEFS.allchart = { id: 'allchart', name: 'All chart patterns', cat: 'pattern', sub: 'chart', overlay: true, inputs: chartInputs, plots: [], levels: [], calc(D, I) { return runChart(D, I, CHART); } };
  CHART.forEach(c => { DEFS['ch_' + c[0]] = { id: 'ch_' + c[0], name: c[1], cat: 'pattern', sub: 'chart', overlay: true, inputs: chartInputs, plots: [], levels: [], calc(D, I) { return runChart(D, I, [c]); } }; });
  DEFS.autotrenddet = { id: 'autotrenddet', name: 'Auto trend detector', beta: true, cat: 'pattern', sub: 'chart', overlay: true, inputs: [['len', 'Độ dài', 50, 'int']], plots: [], levels: [],
    calc(D, I) {
      const lr = T.linreg(D.c, I.len), adx = T.dmi(D, 14, 14).adx, segs = []; let cur = null;
      for (let i = I.len; i < D.n; i++) {
        const sl = lr[i] - lr[i - 1], tr = adx[i] < 20 ? 0 : sl > 0 ? 1 : -1;
        if (!cur || cur.tr !== tr) { cur = { a: i, b: i, tr, hi: D.h[i], lo: D.l[i] }; segs.push(cur); } else { cur.b = i; cur.hi = Math.max(cur.hi, D.h[i]); cur.lo = Math.min(cur.lo, D.l[i]); }
      }
      const show = segs.filter(s => s.b - s.a > 8).slice(-8);
      return { draw(g, X) { show.forEach(s => { const col = s.tr > 0 ? 'rgba(8,153,129,0.10)' : s.tr < 0 ? 'rgba(242,54,69,0.10)' : 'rgba(120,123,134,0.10)'; X.box(g, X.x(s.a), X.y(s.hi), X.x(s.b), X.y(s.lo), col, col.replace('0.10', '0.6'));
        X.label(g, (X.x(s.a) + X.x(s.b)) / 2, X.y(s.hi) - 10, s.tr > 0 ? 'Tăng' : s.tr < 0 ? 'Giảm' : 'Đi ngang', s.tr > 0 ? UP : s.tr < 0 ? DN : NEU); }); } };
    } };

  /* ---------- Tab "Options" (cần dữ liệu quyền chọn) ---------- */
  DEFS.opt_move = { id: 'opt_move', name: 'Options expected move', cat: 'options', need: 'Cần dữ liệu quyền chọn (options) — các nguồn miễn phí không có', inputs: [], plots: [], levels: [] };
  DEFS.opt_vp = { id: 'opt_vp', name: 'Options volume profile', cat: 'options', need: 'Cần dữ liệu quyền chọn (options) — các nguồn miễn phí không có', inputs: [], plots: [], levels: [] };
})(window.App);
