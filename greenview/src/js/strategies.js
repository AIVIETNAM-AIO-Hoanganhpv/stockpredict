/* =========================================================
 * strategies.js — 23 chiến lược có sẵn của TradingView + bộ kiểm tra (backtest)
 * Mỗi chiến lược trả về tín hiệu: +1 = vào lệnh Mua, -1 = vào lệnh Bán (đảo chiều),
 * 2 = đóng lệnh Mua, -2 = đóng lệnh Bán. Lệnh khớp ở giá mở cửa nến kế tiếp.
 * ========================================================= */
(function (App) {
  'use strict';
  const T = App.ta, DEFS = App.INDICATORS, isN = T.isN, N = NaN;
  const len = (d, k = 'len', l = 'Độ dài') => [k, l, d, 'int'];

  const S = {
    barupdn: ['Bar up/down strategy', [], (D) => D.c.map((c, i) => i && c > D.o[i] && D.o[i] > D.c[i - 1] ? 1 : i && c < D.o[i] && D.o[i] < D.c[i - 1] ? -1 : 0)],
    bbs: ['Bollinger Bands strategy', [len(20), ['k', 'Hệ số', 2, 'float']], (D, I) => { const m = T.sma(D.c, I.len), sd = T.stdev(D.c, I.len), u = m.map((x, i) => x + I.k * sd[i]), l = m.map((x, i) => x - I.k * sd[i]); return D.c.map((_, i) => T.crossover(D.c, l, i) ? 1 : T.crossunder(D.c, u, i) ? -1 : 0); }],
    bbsd: ['Bollinger Bands strategy directed', [len(20), ['k', 'Hệ số', 2, 'float'], ['dir', 'Hướng', 'Mua', 'sel', ['Mua', 'Bán']]], (D, I) => { const m = T.sma(D.c, I.len), sd = T.stdev(D.c, I.len), u = m.map((x, i) => x + I.k * sd[i]), l = m.map((x, i) => x - I.k * sd[i]);
      return D.c.map((_, i) => I.dir === 'Mua' ? (T.crossover(D.c, l, i) ? 1 : T.crossunder(D.c, u, i) ? 2 : 0) : (T.crossunder(D.c, u, i) ? -1 : T.crossover(D.c, l, i) ? -2 : 0)); }],
    chbreak: ['Channel breakout strategy', [len(5)], (D, I) => { const hh = T.highest(D.h, I.len), ll = T.lowest(D.l, I.len); return D.c.map((_, i) => i && D.h[i] > hh[i - 1] ? 1 : i && D.l[i] < ll[i - 1] ? -1 : 0); }],
    consec: ['Consecutive up/down strategy', [len(3, 'u', 'Số nến tăng liên tiếp'), len(3, 'd', 'Số nến giảm liên tiếp')], (D, I) => { let u = 0, d = 0; return D.c.map((c, i) => { if (!i) return 0; u = c > D.c[i - 1] ? u + 1 : 0; d = c < D.c[i - 1] ? d + 1 : 0; return u >= I.u ? 1 : d >= I.d ? -1 : 0; }); }],
    greedy: ['Greedy strategy', [], (D) => D.c.map((_, i) => i && D.o[i] > D.h[i - 1] ? 1 : i && D.o[i] < D.l[i - 1] ? -1 : 0)],
    insidebar: ['Inside bar strategy', [], (D) => D.c.map((c, i) => i && D.h[i] < D.h[i - 1] && D.l[i] > D.l[i - 1] ? (c > D.o[i] ? 1 : -1) : 0)],
    kcs: ['Keltner channels strategy', [len(20), ['k', 'Hệ số', 1, 'float']], (D, I) => { const m = T.ema(D.c, I.len), r = T.ema(T.sub(D.h, D.l), I.len), u = m.map((x, i) => x + I.k * r[i]), l = m.map((x, i) => x - I.k * r[i]); return D.c.map((_, i) => T.crossover(D.c, u, i) ? 1 : T.crossunder(D.c, l, i) ? -1 : 0); }],
    macds: ['MACD strategy', [len(12, 'f', 'Nhanh'), len(26, 's', 'Chậm'), len(9, 'sig', 'Tín hiệu')], (D, I) => { const m = T.sub(T.ema(D.c, I.f), T.ema(D.c, I.s)), h = T.sub(m, T.ema(m, I.sig)); return D.c.map((_, i) => T.crossover(h, 0, i) ? 1 : T.crossunder(h, 0, i) ? -1 : 0); }],
    moms: ['Momentum strategy', [len(12)], (D, I) => { const m0 = T.mom(D.c, I.len), m1 = T.mom(m0, 1); return D.c.map((_, i) => m0[i] > 0 && m1[i] > 0 ? 1 : m0[i] < 0 && m1[i] < 0 ? -1 : 0); }],
    macross: ['Moving average crossover', [len(9)], (D, I) => { const m = T.sma(D.c, I.len); return D.c.map((_, i) => T.crossover(D.c, m, i) ? 1 : T.crossunder(D.c, m, i) ? -1 : 0); }],
    outsidebar: ['Outside bar strategy', [], (D) => D.c.map((c, i) => i && D.h[i] > D.h[i - 1] && D.l[i] < D.l[i - 1] ? (c > D.o[i] ? 1 : -1) : 0)],
    sars: ['Parabolic SAR strategy', [['s', 'Bắt đầu', 0.02, 'float'], ['inc', 'Bước', 0.02, 'float'], ['max', 'Tối đa', 0.2, 'float']], (D, I) => { const s = T.sar(D, I.s, I.inc, I.max); return D.c.map((c, i) => T.crossover(D.c, s, i) ? 1 : T.crossunder(D.c, s, i) ? -1 : 0); }],
    pivext: ['Pivot extension strategy', [len(4, 'l', 'Nến trái'), len(2, 'r', 'Nến phải')], (D, I) => { const H = T.pivothigh(D.h, I.l, I.r), L = T.pivotlow(D.l, I.l, I.r), s = T.arr(D.n, 0); for (let i = 0; i < D.n; i++) { if (isN(L[i]) && i + I.r < D.n) s[i + I.r] = 1; if (isN(H[i]) && i + I.r < D.n) s[i + I.r] = -1; } return s; }],
    pivrev: ['Pivot reversal strategy', [len(4, 'l', 'Nến trái'), len(2, 'r', 'Nến phải')], (D, I) => { const H = T.pivothigh(D.h, I.l, I.r), L = T.pivotlow(D.l, I.l, I.r); let hp = N, lp = N; return D.c.map((c, i) => { const k = i - I.r; if (k >= 0) { if (isN(H[k])) hp = H[k]; if (isN(L[k])) lp = L[k]; } return isN(hp) && D.h[i] > hp ? (hp = N, 1) : isN(lp) && D.l[i] < lp ? (lp = N, -1) : 0; }); }],
    pchans: ['Price channel strategy', [len(20)], (D, I) => { const hh = T.highest(D.h, I.len), ll = T.lowest(D.l, I.len); return D.c.map((_, i) => i && D.h[i] > hh[i - 1] ? 1 : i && D.l[i] < ll[i - 1] ? -1 : 0); }],
    rbadx: ['Rob Booker — ADX breakout', [len(14, 'adx', 'Độ dài ADX'), ['th', 'Ngưỡng ADX', 18, 'float'], len(20, 'box', 'Hộp nến')], (D, I) => { const a = T.dmi(D, I.adx, I.adx).adx, hh = T.highest(D.h, I.box), ll = T.lowest(D.l, I.box); return D.c.map((c, i) => i && a[i - 1] < I.th ? (c > hh[i - 1] ? 1 : c < ll[i - 1] ? -1 : 0) : 0); }],
    rsis: ['RSI strategy', [len(14), ['ob', 'Quá mua', 70, 'float'], ['os', 'Quá bán', 30, 'float']], (D, I) => { const r = T.rsi(D.c, I.len); return D.c.map((_, i) => T.crossover(r, I.os, i) ? 1 : T.crossunder(r, I.ob, i) ? -1 : 0); }],
    stochs: ['Stochastic slow strategy', [len(14), ['ob', 'Quá mua', 80, 'float'], ['os', 'Quá bán', 20, 'float']], (D, I) => { const k = T.sma(T.stoch(D.c, D.h, D.l, I.len), 3), d = T.sma(k, 3); return D.c.map((_, i) => T.crossover(k, d, i) && k[i] < I.os ? 1 : T.crossunder(k, d, i) && k[i] > I.ob ? -1 : 0); }],
    sts: ['Supertrend strategy', [len(10), ['f', 'Hệ số', 3, 'float']], (D, I) => { const { dir } = T.supertrend(D, I.f, I.len); return dir.map((d, i) => i && isN(dir[i - 1]) && d !== dir[i - 1] ? d : 0); }],
    techs: ['Technical ratings strategy', [], (D) => { const r = DEFS.techrating.calc(D).r; return r.map((v, i) => T.crossover(r, 0.1, i) ? 1 : T.crossunder(r, -0.1, i) ? -1 : 0); }],
    twoma: ['Two moving averages crossover', [len(9, 'f', 'MA nhanh'), len(21, 's', 'MA chậm')], (D, I) => { const a = T.sma(D.c, I.f), b = T.sma(D.c, I.s); return D.c.map((_, i) => T.crossover(a, b, i) ? 1 : T.crossunder(a, b, i) ? -1 : 0); }],
    volexp: ['Volatility expansion-close strategy', [len(5), ['k', 'Hệ số ATR', 0.75, 'float']], (D, I) => { const a = T.atr(D, I.len); return D.c.map((_, i) => i && D.h[i] > D.c[i - 1] + I.k * a[i - 1] ? 1 : i && D.l[i] < D.c[i - 1] - I.k * a[i - 1] ? -1 : 0); }]
  };

  /* ---------- Bộ kiểm tra chiến lược ---------- */
  App.backtest = function (D, sig, opt = {}) {
    const cap0 = opt.capital || 10000, fee = (opt.fee || 0.04) / 100;
    let pos = 0, qty = 0, entry = 0, eIdx = 0, cash = cap0, peak = cap0, mdd = 0;
    const trades = [], equity = [];
    const close = (i, px, why) => {
      const pnl = pos * qty * (px - entry) - fee * qty * (px + entry);
      cash += pnl; trades.push({ side: pos > 0 ? 'Mua' : 'Bán', ei: eIdx, xi: i, ep: entry, xp: px, pnl, pct: pos * (px / entry - 1) * 100, why });
      pos = 0; qty = 0;
    };
    for (let i = 0; i < D.n; i++) {
      // thực hiện tín hiệu của nến trước tại giá mở cửa nến này
      const s = i ? sig[i - 1] : 0, px = D.o[i];
      if (s === 2 && pos > 0) close(i, px, 'Đóng');
      if (s === -2 && pos < 0) close(i, px, 'Đóng');
      if ((s === 1 && pos <= 0) || (s === -1 && pos >= 0)) {
        if (pos) close(i, px, 'Đảo chiều');
        pos = s; entry = px; eIdx = i; qty = cash / px;
      }
      const eq = cash + (pos ? pos * qty * (D.c[i] - entry) : 0);
      equity.push(eq); peak = Math.max(peak, eq); mdd = Math.max(mdd, (peak - eq) / peak * 100);
    }
    if (pos) close(D.n - 1, D.c[D.n - 1], 'Đang mở');
    const wins = trades.filter(t => t.pnl > 0), loss = trades.filter(t => t.pnl <= 0);
    const gp = wins.reduce((s, t) => s + t.pnl, 0), gl = -loss.reduce((s, t) => s + t.pnl, 0);
    return { trades, equity, net: cash - cap0, netPct: (cash / cap0 - 1) * 100, n: trades.length, winRate: trades.length ? wins.length / trades.length * 100 : 0,
      pf: gl ? gp / gl : gp ? Infinity : 0, mdd, avg: trades.length ? (cash - cap0) / trades.length : 0, buyHold: (D.c[D.n - 1] / D.c[0] - 1) * 100 };
  };

  Object.entries(S).forEach(([id, [name, inputs, fn]]) => {
    DEFS['st_' + id] = {
      id: 'st_' + id, name, cat: 'strategy', overlay: true, inputs, plots: [], levels: [],
      calc(D, I) {
        const sig = fn(D, I), bt = App.backtest(D, sig, App.settings.bt || {}), mk = [];
        bt.trades.forEach(t => {
          mk.push({ i: t.ei, pos: t.side === 'Mua' ? 'belowBar' : 'aboveBar', shape: t.side === 'Mua' ? 'arrowUp' : 'arrowDown', color: t.side === 'Mua' ? '#2962ff' : '#e91e63', text: t.side });
          if (t.why === 'Đóng') mk.push({ i: t.xi, pos: t.side === 'Mua' ? 'aboveBar' : 'belowBar', shape: 'circle', color: '#787b86', text: 'Đóng' });
        });
        return { markers: mk, backtest: bt };
      }
    };
  });
})(window.App);
