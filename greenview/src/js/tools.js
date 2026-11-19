/* =========================================================
 * tools.js — Toàn bộ công cụ vẽ, chia nhóm giống TradingView:
 *   Công cụ · Công cụ xu hướng · Gann và Fibonacci · Mô hình ·
 *   Dự đoán và đo lường · Các dạng hình học · Chú thích · Hình ảnh
 * Mỗi công cụ: n = số điểm cần bấm ('free' = vẽ tay, 'multi' = nhiều điểm),
 * draw(g, P, d, X): P là toạ độ điểm ảnh của các điểm, d là hình, X là bộ hỗ trợ vẽ.
 * ========================================================= */
(function (App) {
  'use strict';
  const DR = App.draw, reg = DR.reg;
  const FL = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.618, 2.618];
  const FC = ['#787b86', '#f23645', '#ff9800', '#4caf50', '#089981', '#00bcd4', '#787b86', '#2962ff', '#9c27b0'];
  const mid = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const pct = (a, b) => App.fmtPct((b / a - 1) * 100);

  /* ---- Biểu tượng SVG (28×28) ---- */
  const dot = (x, y) => `<circle cx="${x}" cy="${y}" r="2.2" class="h"/>`;
  const I = (d, extra = '') => `<svg viewBox="0 0 28 28"><path d="${d}"/>${extra}</svg>`;
  const IC = {
    trend: I('M6 22L22 6', dot(6, 22) + dot(22, 6)), ray: I('M6 22L25 3', dot(6, 22) + dot(13, 15)), info: I('M5 21L17 9', dot(5, 21) + dot(17, 9) + '<rect x="17" y="16" width="7" height="6" rx="1.5"/>'),
    ext: I('M3 25L25 3', dot(10, 18) + dot(18, 10)), angle: I('M5 22L21 8M5 22h16M12 22a7 7 0 0 0-2-5', dot(21, 8)), hline: I('M3 14h22', dot(14, 14)), hray: I('M7 14h19', dot(7, 14)),
    vline: I('M14 3v22', dot(14, 14)), cross: I('M3 14h22M14 3v22', dot(14, 14)), parallel: I('M4 18L18 6M10 24L24 12', dot(4, 18) + dot(18, 6) + dot(24, 12)),
    regr: I('M4 20L24 10M4 24l20-10M4 16L24 6'), flat: I('M4 22l18-10M4 8h20', dot(4, 22) + dot(22, 12) + dot(14, 8)), disjoint: I('M4 10l18-5M4 18l18 6', dot(4, 10) + dot(22, 5) + dot(22, 24)),
    pitch: I('M4 22l8-8M12 14l12-4M12 14l10 8M10 7l14 6', dot(4, 22) + dot(10, 7) + dot(17, 21)), schiff: I('M4 20h8M8 20l16-8M10 8l14 6M12 26l12-6', dot(4, 20) + dot(10, 8)), mschiff: I('M6 18l18-6M8 8l16 6M8 26l16-6M6 18l2-10', dot(6, 18)), inpitch: I('M5 24l7-6M12 18l12-6M12 18l12 4M8 9l16 5', dot(5, 24)),
    fibret: I('M4 5h20M4 10h20M4 15h20M4 20h20M4 24h20', dot(4, 24) + dot(24, 5)), fibext: I('M4 22l6-12l5 7M14 6h11M14 11h11M14 16h11', dot(4, 22) + dot(10, 10) + dot(15, 17)), fibchan: I('M3 16L19 5M6 21l16-11M9 26l16-11'),
    fibtz: I('M5 4v20M8 4v20M12 4v20M18 4v20M25 4v20'), fibfan: I('M4 24L24 4M4 24l20-8M4 24l20-14M4 24h20'), fibtime: I('M4 22l6-10M12 4v20M17 4v20M24 4v20', dot(4, 22) + dot(10, 12)),
    fibcirc: I('M14 14m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M14 14m-8 0a8 8 0 1 0 16 0a8 8 0 1 0-16 0M14 14m-11 0a11 11 0 1 0 22 0a11 11 0 1 0-22 0'), fibspiral: I('M14 14a2 2 0 0 1 4 0a4 4 0 0 1-8 0a7 7 0 0 1 14 0a10 10 0 0 1-17 7'),
    fibarc: I('M4 22a10 10 0 0 1 20 0M8 22a6 6 0 0 1 12 0M11 22a3 3 0 0 1 6 0', dot(14, 22)), fibwedge: I('M5 23L24 6M5 23h19M5 23m8 0a8 8 0 0 0-2-6M5 23m13 0a13 13 0 0 0-3-9', dot(5, 23)), pitchfan: I('M5 23L23 4M5 23l18-6M5 23l18 0M5 23l18-12', dot(5, 23)),
    gannbox: I('M4 4h20v20H4zM4 11h20M4 17h20M11 4v20M17 4v20'), gannsqf: I('M4 4h20v20H4zM4 24L24 4M4 4l20 20M14 4v20'), gannsq: I('M4 4h20v20H4zM4 24L24 4M4 24a20 20 0 0 1 20-20'), gannfan: I('M4 24L24 4M4 24l20-8M4 24l20-14M4 24l8-20M4 24l14-20', dot(4, 24)),
    xabcd: I('M3 22L8 6l6 12l5-9l6 13M3 22l11-4M8 6l11 3', dot(3, 22) + dot(8, 6) + dot(14, 18) + dot(19, 9) + dot(25, 22)), cypher: I('M3 22L8 6l6 12l5-9l6 13', dot(3, 22) + dot(8, 6) + dot(14, 18) + dot(19, 9) + dot(25, 22) + '<text x="11" y="27" font-size="7">C</text>'),
    hs: I('M2 20l4-8l4 6l4-12l4 12l4-6l4 8M6 18h16'), abcd: I('M4 22L9 6l10 12l5-13', dot(4, 22) + dot(9, 6) + dot(19, 18) + dot(24, 5)), tripat: I('M4 22L10 5l6 12l8-6l-20 11', dot(4, 22) + dot(10, 5) + dot(16, 17) + dot(24, 11)),
    drives: I('M2 24l4-8l3 4l4-9l3 4l4-9l3 4l3-8'), ew5: I('M3 22l5-6l3 3l6-9l3 4l5-8', '<text x="4" y="8" font-size="7">1 5</text>'), ewabc: I('M4 10l6 10l6-6l8 10', '<text x="6" y="7" font-size="7">A C</text>'),
    ewtri: I('M3 8l5 12l4-10l4 8l4-6l5 5', '<text x="6" y="6" font-size="7">A E</text>'), eww: I('M4 18l6-8l6 6l8-10', '<text x="5" y="7" font-size="7">W Y</text>'), ewwxz: I('M3 18l4-6l4 4l4-6l4 4l6-8', '<text x="5" y="7" font-size="7">W Z</text>'),
    cyc: I('M5 4v20M11 4v20M17 4v20M23 4v20', dot(5, 14) + dot(11, 14)), tcyc: I('M3 18a4 4 0 0 1 8 0a4 4 0 0 1 8 0a4 4 0 0 1 8 0'), sine: I('M3 14c3-10 6-10 8 0s5 10 8 0s5-10 7-4', dot(3, 14) + dot(11, 14)),
    long: I('M5 4h18v9H5zM5 13h18v11H5z', '<path d="M8 9h12" class="t"/>'), short: I('M5 4h18v11H5zM5 15h18v9H5z'), fcast: I('M4 6v16M4 6l3 0M4 22h3M20 10l4 4l-4 4M8 14h15', dot(4, 14)),
    barspat: I('M6 8v12M10 6v10M14 10v12M18 8v12M22 12v10'), ghost: I('M4 20l4-6l4 3l5-8l4 4l4-5', dot(4, 20) + dot(25, 8)), proj: I('M5 23L14 5l9 18M5 23a9 9 0 0 1 18 0'), avwap: I('M4 20c4-2 6-10 10-8s6 4 10-6M8 6v4M6 8h4', dot(4, 20)),
    fvp: I('M6 4v20M22 4v20M6 8h8M6 12h12M6 16h6M6 20h10'), avp: I('M6 4v20M6 8h10M6 12h14M6 16h8M6 20h11', dot(6, 24)), prange: I('M6 5h16M6 23h16M14 5v18M11 8l3-3l3 3'), drange: I('M5 6v16M23 6v16M5 14h18M20 11l3 3l-3 3'), dprange: I('M5 5h18v18H5zM14 8v12M8 14h12'),
    brush: I('M6 20c2 2 6 1 6-3c0-2 2-4 4-3l8-8'), hilite: I('M8 20l8-8l4 4l-8 8H6zM16 12l4-6l3 3l-5 7'), amark: I('M5 23L19 9l-3-3h8v8l-3-3L7 25z'), arrow: I('M5 23L22 6M15 6h7v7', dot(5, 23)),
    aup: I('M14 4l8 9h-5v11h-6V13H6z'), adn: I('M14 24l8-9h-5V4h-6v11H6z'), rect: I('M5 6h18v16H5z', dot(5, 6) + dot(23, 22)), rotrect: I('M8 4l16 8l-4 12L4 16z', dot(8, 4) + dot(24, 12)), path: I('M3 18l6-6l5 4l9-10M18 6h5v5'),
    circle: I('M14 14m-9 0a9 9 0 1 0 18 0a9 9 0 1 0-18 0', dot(14, 14)), ellipse: I('M14 14m-11 0a11 7 0 1 0 22 0a11 7 0 1 0-22 0'), polyline: I('M5 20l4-12h8l6 6l-5 9z', dot(5, 20) + dot(9, 8) + dot(17, 8) + dot(23, 14)),
    tri: I('M5 23L10 5l13 18z', dot(5, 23) + dot(10, 5) + dot(23, 23)), arc: I('M4 22a10 10 0 0 1 20 0z', dot(4, 22) + dot(24, 22)), curve: I('M5 23C5 10 12 6 23 5', dot(5, 23) + dot(23, 5)), dcurve: I('M5 23c0-8 9-6 9-10s9-2 9-9', dot(5, 23) + dot(23, 4)),
    text: I('M7 6h14M14 6v17M11 23h6'), note: I('M5 5h18v12H5zM14 17v6', '<path d="M10 9h8M14 9v6"/>'), pnote: I('M5 5h18v12H5zM14 17v6', '<text x="10" y="15" font-size="10">$</text>'), pin: I('M14 25s-8-8-8-13a8 8 0 0 1 16 0c0 5-8 13-8 13z', '<circle cx="14" cy="12" r="3"/>'),
    table: I('M4 6h20v16H4zM4 11h20M4 16h20M11 6v16'), callout: I('M4 5h20v13H12l-5 5v-5H4z'), comment: I('M5 7a5 5 0 0 1 5-3h8a5 5 0 0 1 5 5v2a5 5 0 0 1-5 5h-8a5 5 0 0 1-5-5z'), plabel: I('M6 5h17v12H10l-4 5z', dot(6, 22)),
    sign: I('M14 14v12M14 14a7 7 0 1 0 0-14a7 7 0 1 0 0 14', '<path d="M14 4l1.5 3h3l-2.5 2l1 3l-3-2l-3 2l1-3l-2.5-2h3z"/>'), flag: I('M7 25V4h14l-4 5l4 5H7'), image: I('M4 5h20v18H4zM4 19l6-6l5 5l3-3l6 6', '<circle cx="18" cy="10" r="2"/>'),
    measure: I('M4 20L20 4l4 4L8 24zM8 16l2 2M11 13l2 2M14 10l2 2'), eraser: I('M10 22l-6-6L16 4l8 8l-10 10zM4 22h20'), keep: I('M6 20l12-12l4 4l-12 12H6zM18 22h6v-4', '<rect x="17" y="17" width="6" height="5" rx="1"/>'), hide: I('M3 14s4-7 11-7s11 7 11 7s-4 7-11 7S3 14 3 14z', '<circle cx="14" cy="14" r="3"/>'),
    lock: I('M8 13V9a6 6 0 0 1 12 0M6 13h16v11H6z'), magnet: I('M7 4v10a7 7 0 0 0 14 0V4h-4v10a3 3 0 0 1-6 0V4z'), trash: I('M5 7h18M10 7V4h8v3M7 7l1 17h12l1-17'), zin: I('M12 12m-7 0a7 7 0 1 0 14 0a7 7 0 1 0-14 0M17 17l7 7M9 12h6M12 9v6'), zout: I('M12 12m-7 0a7 7 0 1 0 14 0a7 7 0 1 0-14 0M17 17l7 7M9 12h6'),
    cursor: I('M7 4l14 10l-6 1l4 8l-3 1l-4-8l-5 4z')
  };
  DR.ICONS = IC;

  DR.CATS = [
    ['fav', 'Yêu thích'], ['tools', 'Công cụ'], ['trend', 'Công cụ xu hướng'], ['fib', 'Gann và fibonacci'], ['pattern', 'Mô hình'],
    ['predict', 'Dự đoán và đo lường'], ['geo', 'Các dạng hình học'], ['note', 'Chú thích'], ['img', 'Hình ảnh']
  ];

  /* ============ CÔNG CỤ (thao tác, không phải hình) ============ */
  DR.ACTIONS = [
    ['measure', 'Công cụ đo lường', IC.measure], ['eraser', 'Tẩy', IC.eraser], ['keep', 'Tiếp tục vẽ', IC.keep, 'toggle'], ['hide', 'Ẩn hình vẽ', IC.hide, 'toggle'],
    ['lock', 'Khóa tất cả hình vẽ', IC.lock, 'toggle'], ['magnet', 'Nam châm', IC.magnet, 'cycle'], ['clear', 'Xóa tất cả đối tượng', IC.trash], ['zin', 'Phóng to', IC.zin], ['zout', 'Thu nhỏ', IC.zout]
  ];

  /* ============ CÔNG CỤ XU HƯỚNG ============ */
  const infoBox = (X, a, b, d, P) => {
    const pa = d.pts[0].p, pb = d.pts[1].p, bars = Math.round(DR.t2l(d.pts[1].t) - DR.t2l(d.pts[0].t));
    const ang = Math.atan2(-(b.y - a.y), b.x - a.x) * 180 / Math.PI;
    X.text(`${X.fmt(pb - pa)} (${pct(pa, pb)})\n${bars} nến, ${App.fmtSpan(bars * DR.step())}\n${ang.toFixed(1)}°`, b.x + 8, b.y, { bg: X.alpha(d.style.color, 0.9), color: '#fff', size: 11 });
  };
  reg('trend', 'trend', 'Đường xu hướng', { icon: IC.trend, draw(g, P, d, X) { X.line(P[0], P[1], { extL: d.style.extL, extR: d.style.extR }); if (d.style.info) infoBox(X, P[0], P[1], d); }, opts: ['extL', 'extR', 'info'] });
  reg('trend', 'ray', 'Tia', { icon: IC.ray, draw(g, P, d, X) { X.line(P[0], P[1], { extR: true }); } });
  reg('trend', 'infoline', 'Đường thông tin', { icon: IC.info, draw(g, P, d, X) { X.line(P[0], P[1]); infoBox(X, P[0], P[1], d); } });
  reg('trend', 'extended', 'Dòng mở rộng', { icon: IC.ext, draw(g, P, d, X) { X.line(P[0], P[1], { extL: true, extR: true }); } });
  reg('trend', 'trendangle', 'Góc xu hướng', { icon: IC.angle, draw(g, P, d, X) {
    const [a, b] = P; X.line(a, b); X.line(a, { x: a.x + 60, y: a.y }, { dash: 'dashed', width: 1 });
    const ang = Math.atan2(-(b.y - a.y), b.x - a.x); g.beginPath(); g.strokeStyle = d.style.color; g.lineWidth = 1; g.arc(a.x, a.y, 30, -ang, 0, ang < 0); g.stroke();
    X.text((ang * 180 / Math.PI).toFixed(1) + '°', a.x + 36, a.y - 10 * Math.sign(ang || 1), { size: 11 }); } });
  reg('trend', 'hline', 'Đường nằm ngang', { n: 1, icon: IC.hline, draw(g, P, d, X) { X.hl(P[0].y); X.label(X.fmt(d.pts[0].p), X.W - 2, P[0].y, d.style.color, 'right'); if (d.style.text) X.text(d.style.text, 8, P[0].y - 9, { size: 12 }); }, text: true, askText: false });
  reg('trend', 'hray', 'Tia ngang', { n: 1, icon: IC.hray, draw(g, P, d, X) { X.hl(P[0].y, P[0].x, X.W); X.label(X.fmt(d.pts[0].p), X.W - 2, P[0].y, d.style.color, 'right'); } });
  reg('trend', 'vline', 'Đường thẳng đứng', { n: 1, icon: IC.vline, draw(g, P, d, X) { X.vl(P[0].x); X.label(App.fmtTime(d.pts[0].t), P[0].x, X.H - 12, d.style.color, 'center'); } });
  reg('trend', 'crossline', 'Đường chữ thập', { n: 1, icon: IC.cross, draw(g, P, d, X) { X.hl(P[0].y); X.vl(P[0].x); X.label(X.fmt(d.pts[0].p), X.W - 2, P[0].y, d.style.color, 'right'); } });
  reg('trend', 'parallel', 'Kênh song song', { n: 3, icon: IC.parallel, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || b, off = (c.y - (a.y + (b.y - a.y) * ((c.x - a.x) / ((b.x - a.x) || 1)))) || 0;
    const a2 = { x: a.x, y: a.y + off }, b2 = { x: b.x, y: b.y + off };
    const f = new Path2D(); f.moveTo(a.x, a.y); f.lineTo(b.x, b.y); f.lineTo(b2.x, b2.y); f.lineTo(a2.x, a2.y); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.12));
    X.line(a, b, { extL: d.style.extL, extR: d.style.extR }); X.line(a2, b2, { extL: d.style.extL, extR: d.style.extR }); X.line(mid(a, a2), mid(b, b2), { dash: 'dashed', width: 1 }); }, opts: ['extL', 'extR'] });
  reg('trend', 'regression', 'Xu hướng hồi quy', { icon: IC.regr, draw(g, P, d, X) {
    const B = X.bars; let i1 = X.idx(d.pts[0].t), i2 = X.idx(d.pts[1].t); if (i1 > i2) [i1, i2] = [i2, i1]; i1 = Math.max(0, i1); i2 = Math.min(B.length - 1, i2); const n = i2 - i1 + 1; if (n < 2) return X.line(P[0], P[1]);
    let sx = 0, sy = 0, sxy = 0, sxx = 0; for (let j = 0; j < n; j++) { const y = B[i1 + j].close; sx += j; sy += y; sxy += j * y; sxx += j * j; }
    const m = (n * sxy - sx * sy) / (n * sxx - sx * sx), c0 = (sy - m * sx) / n; let v = 0; for (let j = 0; j < n; j++) v += (B[i1 + j].close - c0 - m * j) ** 2; const sd = Math.sqrt(v / n) * 2;
    const pt = (j, o) => ({ x: X.x(i1 + j), y: X.y(c0 + m * j + o) });
    const f = new Path2D(); f.moveTo(pt(0, sd).x, pt(0, sd).y); f.lineTo(pt(n - 1, sd).x, pt(n - 1, sd).y); f.lineTo(pt(n - 1, -sd).x, pt(n - 1, -sd).y); f.lineTo(pt(0, -sd).x, pt(0, -sd).y); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.1));
    X.line(pt(0, 0), pt(n - 1, 0), { dash: 'dashed' }); X.line(pt(0, sd), pt(n - 1, sd), { width: 1 }); X.line(pt(0, -sd), pt(n - 1, -sd), { width: 1 }); } });
  reg('trend', 'flattop', 'Mặt phẳng đỉnh/đáy', { n: 3, icon: IC.flat, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || b; const f = new Path2D(); f.moveTo(a.x, a.y); f.lineTo(b.x, b.y); f.lineTo(b.x, c.y); f.lineTo(a.x, c.y); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.12));
    X.line(a, b); X.line({ x: a.x, y: c.y }, { x: b.x, y: c.y }); } });
  reg('trend', 'disjoint', 'Kênh rời rạc', { n: 3, icon: IC.disjoint, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || b, c2 = { x: a.x, y: c.y + (c.y - b.y) * 0 }, e = { x: b.x, y: c.y - (b.y - a.y) };
    const f = new Path2D(); f.moveTo(a.x, a.y); f.lineTo(b.x, b.y); f.lineTo(e.x, e.y); f.lineTo(c2.x, c2.y); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.12)); X.line(a, b); X.line(c2, e); } });
  const fork = (origin, g, P, d, X) => {
    const [, b, c] = P, m = mid(b, c), o = origin;
    X.line(o, m, { extR: true, color: '#e91e63' });
    [b, c].forEach(q => X.line(q, { x: q.x + (m.x - o.x), y: q.y + (m.y - o.y) }, { extR: true }));
    X.line(b, c, { width: 1, dash: 'dashed' });
    const f = new Path2D(), k = 3; f.moveTo(b.x, b.y); f.lineTo(b.x + (m.x - o.x) * k, b.y + (m.y - o.y) * k); f.lineTo(c.x + (m.x - o.x) * k, c.y + (m.y - o.y) * k); f.lineTo(c.x, c.y); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.08), false);
  };
  reg('trend', 'pitchfork', 'Mô hình Pitchfork', { n: 3, icon: IC.pitch, draw(g, P, d, X) { if (P.length < 3) return X.line(P[0], P[1]); fork(P[0], g, P, d, X); } });
  reg('trend', 'schiff', 'Mô hình Schiff Pitchfork', { n: 3, icon: IC.schiff, draw(g, P, d, X) { if (P.length < 3) return X.line(P[0], P[1]); fork({ x: P[0].x, y: (P[0].y + P[1].y) / 2 }, g, P, d, X); } });
  reg('trend', 'mschiff', 'Mô hình Schiff Pitchfork Biến đổi', { n: 3, icon: IC.mschiff, draw(g, P, d, X) { if (P.length < 3) return X.line(P[0], P[1]); fork(mid(P[0], P[1]), g, P, d, X); } });
  reg('trend', 'inpitch', 'Mô hình Pitchfork Mặt trong', { n: 3, icon: IC.inpitch, draw(g, P, d, X) { if (P.length < 3) return X.line(P[0], P[1]); const o = mid(P[0], P[1]); fork({ x: o.x, y: P[0].y + (P[1].y - P[0].y) * 0.25 }, g, P, d, X); } });

  /* ============ GANN VÀ FIBONACCI ============ */
  const levels = d => d.style.levels || FL;
  const fibBands = (X, d, x1, x2, priceOf, labelX) => {
    let prevY = null;
    levels(d).forEach((lv, k) => {
      const pr = priceOf(lv), y = X.y(pr); if (y == null) return; const col = FC[k % FC.length];
      if (prevY != null) X.fill(new Path2D(`M${x1} ${prevY}H${x2}V${y}H${x1}Z`), X.alpha(col, 0.1));
      X.line({ x: x1, y }, { x: x2, y }, { color: col, width: 1 });
      X.text(`${lv} (${X.fmt(pr)})`, labelX != null ? labelX : x1 - 4, y - 1, { color: col, size: 11, align: labelX != null ? 'left' : 'right', base: 'bottom' });
      prevY = y;
    });
  };
  reg('fib', 'fibret', 'Hồi quy Fib', { icon: IC.fibret, draw(g, P, d, X) {
    const [a, b] = P, x1 = Math.min(a.x, b.x), x2 = d.style.extR ? X.W : Math.max(a.x, b.x, x1 + 40), p1 = d.pts[0].p, p2 = d.pts[1].p;
    X.line(a, b, { dash: 'dashed', width: 1, color: '#787b86' }); fibBands(X, d, x1, x2, lv => p2 + (p1 - p2) * lv, x1 > 120 ? null : x2 + 4); }, opts: ['extR'] });
  reg('fib', 'fibext', 'Phần mở rộng fib dựa trên xu hướng', { n: 3, icon: IC.fibext, draw(g, P, d, X) {
    X.poly(P, { dash: 'dashed', width: 1, color: '#787b86' }); if (P.length < 3) return;
    const dlt = d.pts[1].p - d.pts[0].p, x1 = P[2].x, x2 = Math.max(x1 + 80, P[1].x + 80); fibBands(X, d, x1, x2, lv => d.pts[2].p + dlt * lv, x2 + 4); } });
  reg('fib', 'fibchannel', 'Kênh Fib', { n: 3, icon: IC.fibchan, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || b, off = c.y - (a.y + (b.y - a.y) * ((c.x - a.x) / ((b.x - a.x) || 1)));
    levels(d).forEach((lv, k) => X.line({ x: a.x, y: a.y + off * lv }, { x: b.x, y: b.y + off * lv }, { color: FC[k % FC.length], width: 1, extR: true })); } });
  reg('fib', 'fibtz', 'Fib múi giờ', { icon: IC.fibtz, draw(g, P, d, X) {
    const dx = P[1].x - P[0].x; [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89].forEach((n, k) => { const x = P[0].x + dx * n; if (x > -10 && x < X.W + 10) { X.vl(x, { color: FC[k % FC.length], width: 1 }); X.text(String(n), x + 3, 12, { size: 10, color: FC[k % FC.length] }); } }); } });
  const fan = (X, o, b, lv, col) => X.line(o, { x: b.x, y: o.y + (b.y - o.y) * lv }, { extR: true, color: col, width: 1 });
  reg('fib', 'fibfan', 'Fib kháng cự dạng quạt', { icon: IC.fibfan, draw(g, P, d, X) {
    const [a, b] = P; [0.25, 0.382, 0.5, 0.618, 0.75, 1].forEach((lv, k) => { fan(X, a, b, lv, FC[k + 1]); X.line(a, { x: a.x + (b.x - a.x) * lv, y: b.y }, { extR: true, color: FC[k + 1], width: 1, dash: 'dotted' }); });
    X.rect(a, b, { fill: null, width: 1, color: '#787b86' }); } });
  reg('fib', 'fibtime', 'Thời gian dựa trên xu hướng', { n: 3, icon: IC.fibtime, draw(g, P, d, X) {
    X.poly(P, { dash: 'dashed', width: 1, color: '#787b86' }); if (P.length < 3) return; const dx = P[1].x - P[0].x;
    [0, 0.382, 0.5, 0.618, 1, 1.382, 1.618, 2, 2.382, 2.618].forEach((lv, k) => { const x = P[2].x + dx * lv; X.vl(x, { color: FC[k % FC.length], width: 1 }); X.text(String(lv), x + 3, 12, { size: 10, color: FC[k % FC.length] }); }); } });
  reg('fib', 'fibcircles', 'Chu kỳ Fib', { icon: IC.fibcirc, draw(g, P, d, X) {
    const c = mid(P[0], P[1]), r = dist(P[0], P[1]) / 2; X.line(P[0], P[1], { dash: 'dashed', width: 1 });
    [0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.618, 2.618].forEach((lv, k) => { const p = new Path2D(); p.arc(c.x, c.y, r * lv, 0, Math.PI * 2); X.stroke(p, FC[(k + 1) % FC.length], 1); }); } });
  reg('fib', 'fibspiral', 'Fib xoắn ốc', { icon: IC.fibspiral, draw(g, P, d, X) {
    const [a, b] = P, r0 = dist(a, b), ang0 = Math.atan2(b.y - a.y, b.x - a.x), phi = 1.618033988, p = new Path2D(); X.line(a, b, { dash: 'dashed', width: 1 });
    for (let k = -720; k <= 720; k += 5) { const th = k * Math.PI / 180, r = r0 * Math.pow(phi, th / (Math.PI / 2)); const x = a.x + r * Math.cos(ang0 + th), y = a.y + r * Math.sin(ang0 + th); k === -720 ? p.moveTo(x, y) : p.lineTo(x, y); }
    X.stroke(p); } });
  reg('fib', 'fibarcs', 'Fib kháng cự dạng cung', { icon: IC.fibarc, draw(g, P, d, X) {
    const [a, b] = P, r = dist(a, b), up = a.y > b.y; X.line(a, b, { dash: 'dashed', width: 1 });
    [0.236, 0.382, 0.5, 0.618, 0.786, 1].forEach((lv, k) => { const p = new Path2D(); p.arc(b.x, b.y, r * lv, up ? 0 : Math.PI, up ? Math.PI : 0); X.stroke(p, FC[(k + 1) % FC.length], 1); }); } });
  reg('fib', 'fibwedge', 'Fib hình nêm', { n: 3, icon: IC.fibwedge, draw(g, P, d, X) {
    const [o, b] = P, c = P[2] || b, r = dist(o, b), a1 = Math.atan2(b.y - o.y, b.x - o.x), a2 = Math.atan2(c.y - o.y, c.x - o.x);
    X.line(o, b); X.line(o, { x: o.x + r * Math.cos(a2), y: o.y + r * Math.sin(a2) });
    [0.236, 0.382, 0.5, 0.618, 0.786, 1].forEach((lv, k) => { const p = new Path2D(); p.arc(o.x, o.y, r * lv, a1, a2, a2 < a1); X.stroke(p, FC[(k + 1) % FC.length], 1); }); } });
  reg('fib', 'pitchfan', 'Mô hình Pitchfork dạng quạt', { n: 3, icon: IC.pitchfan, draw(g, P, d, X) {
    const [o, b] = P, c = P[2] || b; X.line(b, c, { dash: 'dashed', width: 1 });
    [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].forEach((lv, k) => X.line(o, { x: b.x + (c.x - b.x) * lv, y: b.y + (c.y - b.y) * lv }, { extR: true, width: 1, color: FC[k % FC.length] })); } });
  const gannGrid = (X, a, b, d, arcs) => {
    const R = [0, 0.25, 0.382, 0.5, 0.618, 0.75, 1], x1 = a.x, y1 = a.y, w = b.x - a.x, h = b.y - a.y;
    X.rect(a, b, { fill: X.alpha(d.style.color, 0.05), width: 1 });
    R.forEach((r, k) => { X.line({ x: x1 + w * r, y: y1 }, { x: x1 + w * r, y: y1 + h }, { width: 1, color: FC[k % FC.length] }); X.line({ x: x1, y: y1 + h * r }, { x: x1 + w, y: y1 + h * r }, { width: 1, color: FC[k % FC.length] }); });
    X.line(a, b, { width: 1 }); X.line({ x: a.x, y: b.y }, { x: b.x, y: a.y }, { width: 1 });
    if (arcs) [0.5, 1].forEach(r => { const p = new Path2D(); p.ellipse(a.x, b.y, Math.abs(w) * r, Math.abs(h) * r, 0, 0, Math.PI * 2); X.stroke(p, '#ff9800', 1); });
  };
  reg('fib', 'gannbox', 'Mô hình hộp Gann', { icon: IC.gannbox, draw(g, P, d, X) { gannGrid(X, P[0], P[1], d, false); } });
  reg('fib', 'gannsqfixed', 'Hình vuông Gann cố định', { icon: IC.gannsqf, draw(g, P, d, X) { const s = Math.abs(P[1].x - P[0].x), b = { x: P[1].x, y: P[0].y + Math.sign(P[1].y - P[0].y || -1) * s }; gannGrid(X, P[0], b, d, true); } });
  reg('fib', 'gannsquare', 'Hình vuông Gann', { icon: IC.gannsq, draw(g, P, d, X) { gannGrid(X, P[0], P[1], d, true); } });
  reg('fib', 'gannfan', 'Quạt Gann', { icon: IC.gannfan, draw(g, P, d, X) {
    const [o, b] = P, dx = b.x - o.x, dy = b.y - o.y;
    [[1, 8], [1, 4], [1, 3], [1, 2], [1, 1], [2, 1], [3, 1], [4, 1], [8, 1]].forEach(([tx, py], k) => { const e = { x: o.x + dx * tx / py * (py > tx ? 1 : 1), y: o.y + dy * py / tx }; const end = { x: o.x + dx * (tx / Math.max(tx, py)) * 4, y: o.y + dy * (py / Math.max(tx, py)) * 4 };
      X.line(o, end, { extR: true, width: 1, color: FC[k % FC.length] }); X.text(`${tx}x${py}`, o.x + (end.x - o.x) * 0.3, o.y + (end.y - o.y) * 0.3, { size: 10, color: FC[k % FC.length] }); void e; }); } });

  /* ============ MÔ HÌNH ============ */
  const pattern = (labels, ratios) => function (g, P, d, X) {
    const fillCol = X.alpha(d.style.color, 0.12);
    if (ratios && P.length >= 3) { // tô các tam giác XAB, BCD
      for (let k = 0; k + 2 < P.length; k += 2) { const f = new Path2D(); f.moveTo(P[k].x, P[k].y); f.lineTo(P[k + 1].x, P[k + 1].y); f.lineTo(P[k + 2].x, P[k + 2].y); f.closePath(); X.fill(f, fillCol); }
    }
    X.poly(P);
    P.forEach((p, k) => { const up = k > 0 ? p.y < P[k - 1].y : P[1] && p.y < P[1].y; X.text(labels[k] || '', p.x, p.y + (up ? -12 : 12), { align: 'center', size: 12, bold: true, color: d.style.color }); });
    if (ratios) {
      const pr = d.pts.map(q => q.p);
      for (let k = 2; k < P.length; k++) {
        const r = Math.abs((pr[k] - pr[k - 1]) / (pr[k - 1] - pr[k - 2] || 1));
        const m = mid(P[k - 2], P[k]); X.line(P[k - 2], P[k], { dash: 'dashed', width: 1 }); X.text(r.toFixed(3), m.x, m.y, { size: 10, align: 'center', bg: X.alpha(d.style.color, 0.85), color: '#fff' });
      }
    }
  };
  reg('pattern', 'xabcd', 'Mô hình XABCD', { n: 5, icon: IC.xabcd, draw: pattern(['X', 'A', 'B', 'C', 'D'], true) });
  reg('pattern', 'cypher', 'Mô hình Cypher', { n: 5, icon: IC.cypher, draw: pattern(['X', 'A', 'B', 'C', 'D'], true) });
  reg('pattern', 'headshoulders', 'Mô hình Biểu đồ Đầu Vai', { n: 7, icon: IC.hs, draw(g, P, d, X) {
    pattern(['', 'Vai trái', '', 'Đầu', '', 'Vai phải', ''])(g, P, d, X);
    if (P.length >= 5) X.line(P[2], P[4], { extL: true, extR: true, dash: 'dashed', color: '#f23645' }); } });
  reg('pattern', 'abcd', 'Mô hình ABCD', { n: 4, icon: IC.abcd, draw: pattern(['A', 'B', 'C', 'D'], true) });
  reg('pattern', 'tripattern', 'Mô hình tam giác', { n: 4, icon: IC.tripat, draw(g, P, d, X) {
    pattern(['A', 'B', 'C', 'D'])(g, P, d, X); if (P.length >= 4) { const f = new Path2D(); f.moveTo(P[0].x, P[0].y); P.forEach(p => f.lineTo(p.x, p.y)); f.closePath(); X.fill(f, X.alpha(d.style.color, 0.12)); X.line(P[0], P[2], { width: 1 }); X.line(P[1], P[3], { width: 1 }); } } });
  reg('pattern', 'threedrives', 'Mô hình Three Drives', { n: 7, icon: IC.drives, draw: pattern(['', '1', '', '2', '', '3', ''], true) });
  reg('pattern', 'ew_impulse', 'Sóng đẩy Elliott (1·2·3·4·5)', { n: 6, icon: IC.ew5, draw: pattern(['(0)', '(1)', '(2)', '(3)', '(4)', '(5)']) });
  reg('pattern', 'ew_corr', 'Sóng điều chỉnh Elliott (A·B·C)', { n: 4, icon: IC.ewabc, draw: pattern(['(0)', '(A)', '(B)', '(C)']) });
  reg('pattern', 'ew_tri', 'Sóng tam giác Elliott (A·B·C·D·E)', { n: 6, icon: IC.ewtri, draw: pattern(['(0)', '(A)', '(B)', '(C)', '(D)', '(E)']) });
  reg('pattern', 'ew_double', 'Sóng kết hợp kép Elliott (W·X·Y)', { n: 4, icon: IC.eww, draw: pattern(['(0)', '(W)', '(X)', '(Y)']) });
  reg('pattern', 'ew_triple', 'Sóng kết hợp ba Elliott (W·X·Y·X·Z)', { n: 6, icon: IC.ewwxz, draw: pattern(['(0)', '(W)', '(X)', '(Y)', '(X)', '(Z)']) });
  reg('pattern', 'cyclic', 'Các đường chu kỳ', { icon: IC.cyc, draw(g, P, d, X) {
    const dx = P[1].x - P[0].x; if (Math.abs(dx) < 3) return X.vl(P[0].x); for (let k = -40; k <= 80; k++) { const x = P[0].x + dx * k; if (x > -5 && x < X.W + 5) X.vl(x, { width: 1, dash: k ? 'solid' : 'dashed' }); } } });
  reg('pattern', 'timecycles', 'Vòng thời gian', { icon: IC.tcyc, draw(g, P, d, X) {
    const dx = Math.abs(P[1].x - P[0].x), y = P[0].y; if (dx < 3) return; for (let k = -40; k <= 80; k++) { const cx = Math.min(P[0].x, P[1].x) + dx * (k + 0.5); if (cx < -dx || cx > X.W + dx) continue; const p = new Path2D(); p.ellipse(cx, y, dx / 2, dx / 3, 0, Math.PI, 0); X.stroke(p, null, 1); } } });
  reg('pattern', 'sine', 'Đường hình sin', { icon: IC.sine, draw(g, P, d, X) {
    const [a, b] = P, half = b.x - a.x, amp = (b.y - a.y) / 2, cy = (a.y + b.y) / 2; if (Math.abs(half) < 2) return; const p = new Path2D();
    for (let x = 0; x <= X.W; x += 2) { const y = cy - amp * Math.cos(Math.PI * (x - a.x) / half); x ? p.lineTo(x, y) : p.moveTo(x, y); } X.stroke(p); } });

  /* ============ DỰ ĐOÁN VÀ ĐO LƯỜNG ============ */
  const position = side => ({
    n: 1, icon: side > 0 ? IC.long : IC.short,
    init(d) { const p = d.pts[0].p, t2 = d.pts[0].t + DR.step() * 25; d.pts = [d.pts[0], { t: t2, p: p * (1 + side * 0.03) }, { t: t2, p: p * (1 - side * 0.015) }]; },
    onHandle(d, k) { if (k === 1) d.pts[2].t = d.pts[1].t; if (k === 2) d.pts[1].t = d.pts[2].t; },
    draw(g, P, d, X) {
      const [e, tp, sl] = P, x1 = e.x, x2 = tp.x, ep = d.pts[0].p, tpp = d.pts[1].p, slp = d.pts[2].p;
      X.fill(new Path2D(`M${x1} ${e.y}H${x2}V${tp.y}H${x1}Z`), 'rgba(8,153,129,0.22)');
      X.fill(new Path2D(`M${x1} ${e.y}H${x2}V${sl.y}H${x1}Z`), 'rgba(242,54,69,0.22)');
      X.line({ x: x1, y: e.y }, { x: x2, y: e.y }, { color: '#787b86', width: 1 });
      // giá đã đi tới đâu kể từ điểm vào
      const B = X.bars, i0 = Math.max(0, X.idx(d.pts[0].t)), i1 = Math.min(B.length - 1, X.idx(d.pts[1].t)); let hit = null;
      for (let i = i0 + 1; i <= i1; i++) { if (side > 0 ? B[i].high >= tpp : B[i].low <= tpp) { hit = 'tp'; break; } if (side > 0 ? B[i].low <= slp : B[i].high >= slp) { hit = 'sl'; break; } }
      const rr = Math.abs(tpp - ep) / Math.abs(ep - slp || 1);
      X.text(`Mục tiêu: ${X.fmt(tpp)} (${pct(ep, tpp)})`, (x1 + x2) / 2, tp.y + (side > 0 ? -2 : 2), { align: 'center', base: side > 0 ? 'bottom' : 'top', bg: '#089981', color: '#fff', size: 11 });
      X.text(`Dừng lỗ: ${X.fmt(slp)} (${pct(ep, slp)})`, (x1 + x2) / 2, sl.y + (side > 0 ? 2 : -2), { align: 'center', base: side > 0 ? 'top' : 'bottom', bg: '#f23645', color: '#fff', size: 11 });
      X.text(`${side > 0 ? 'MUA' : 'BÁN'} ${X.fmt(ep)} · R/R ${rr.toFixed(2)}${hit ? (hit === 'tp' ? ' · ✓ Chạm mục tiêu' : ' · ✗ Chạm dừng lỗ') : ''}`, (x1 + x2) / 2, e.y, { align: 'center', bg: '#363a45', color: '#fff', size: 11 });
    }
  });
  reg('predict', 'long', 'Vị thế Mua', position(1));
  reg('predict', 'short', 'Vị thế Bán', position(-1));
  reg('predict', 'forecast', 'Dự báo vị thế', { icon: IC.fcast, draw(g, P, d, X) {
    const [a, b] = P, up = d.pts[1].p >= d.pts[0].p, col = up ? '#089981' : '#f23645'; X.line(a, b, { color: col }); X.arrowHead(a, b, 10, col);
    const bars = Math.round(DR.t2l(d.pts[1].t) - DR.t2l(d.pts[0].t)); X.text(`${pct(d.pts[0].p, d.pts[1].p)} · ${bars} nến`, b.x + 6, b.y, { bg: col, color: '#fff', size: 11 }); } });
  reg('predict', 'barspattern', 'Mô hình Thanh', { n: 3, icon: IC.barspat, draw(g, P, d, X) {
    const B = X.bars; let i1 = X.idx(d.pts[0].t), i2 = X.idx(d.pts[1].t); if (i1 > i2) [i1, i2] = [i2, i1]; i1 = Math.max(0, i1); i2 = Math.min(B.length - 1, i2);
    X.rect({ x: X.x(i1) - 3, y: P[0].y }, { x: X.x(i2) + 3, y: P[1].y }, { fill: X.alpha(d.style.color, 0.06), width: 1, dash: 'dashed' });
    if (P.length < 3 || i2 <= i1) return; const s = X.idx(d.pts[2].t), shift = d.pts[2].p - B[i1].open, bw = Math.max(1, (X.x(1) - X.x(0)) * 0.6);
    for (let i = i1; i <= i2; i++) { const b = B[i], x = X.x(s + i - i1), up = b.close >= b.open, col = X.alpha(up ? '#089981' : '#f23645', 0.55);
      const p = new Path2D(); p.moveTo(x, X.y(b.high + shift)); p.lineTo(x, X.y(b.low + shift)); X.stroke(p, col, 1, 'solid');
      const yo = X.y(b.open + shift), yc = X.y(b.close + shift); X.fill(new Path2D(`M${x - bw / 2} ${yo}H${x + bw / 2}V${yc}H${x - bw / 2}Z`), col); } } });
  reg('predict', 'ghostfeed', 'Mô hình Ghost Feed', { n: 'multi', icon: IC.ghost, draw(g, P, d, X) {
    X.poly(P, { dash: 'dotted', width: 1 }); const bw = Math.max(2, (X.x(1) - X.x(0)) * 0.6), seed = d.id.length;
    for (let k = 0; k + 1 < P.length; k++) { const a = d.pts[k], b = d.pts[k + 1], la = DR.t2l(a.t), lb = DR.t2l(b.t), n = Math.max(1, Math.round(lb - la));
      let prev = a.p; for (let j = 1; j <= n; j++) { const target = a.p + (b.p - a.p) * j / n, wig = Math.abs(b.p - a.p) / n * (0.6 + ((j * 7 + seed) % 5) / 6), c = target + (j < n ? (((j + seed) % 3) - 1) * wig * 0.4 : 0);
        const x = X.x(la + j), hi = Math.max(prev, c) + wig * 0.4, lo = Math.min(prev, c) - wig * 0.4, col = X.alpha(c >= prev ? '#089981' : '#f23645', 0.5);
        X.stroke(new Path2D(`M${x} ${X.y(hi)}V${X.y(lo)}`), col, 1, 'solid'); X.fill(new Path2D(`M${x - bw / 2} ${X.y(prev)}H${x + bw / 2}V${X.y(c)}H${x - bw / 2}Z`), col); prev = c; } } } });
  reg('predict', 'projection', 'Khu vực', { n: 3, icon: IC.proj, draw(g, P, d, X) {
    X.poly(P, { fill: X.alpha(d.style.color, 0.12) }); if (P.length < 3) return; const [a, b, c] = P, r = dist(b, a), a1 = Math.atan2(a.y - b.y, a.x - b.x), a2 = Math.atan2(c.y - b.y, c.x - b.x);
    const p = new Path2D(); p.arc(b.x, b.y, r * 0.3, a1, a2, a2 < a1); X.stroke(p, null, 1);
    const l1 = Math.abs(d.pts[1].p - d.pts[0].p), l2 = Math.abs(d.pts[2].p - d.pts[1].p); X.text(`${(l2 / (l1 || 1) * 100).toFixed(1)}%`, c.x + 6, c.y, { bg: d.style.color, color: '#fff', size: 11 }); } });
  reg('predict', 'avwap', 'VWAP được neo', { n: 1, icon: IC.avwap, style: { color: '#2962ff' }, draw(g, P, d, X) {
    const B = X.bars, s = Math.max(0, X.idx(d.pts[0].t)), p = new Path2D(); let pv = 0, vv = 0;
    for (let i = s; i < B.length; i++) { const tp = (B[i].high + B[i].low + B[i].close) / 3, v = B[i].volume || 1; pv += tp * v; vv += v; const x = X.x(i), y = X.y(pv / vv); i === s ? p.moveTo(x, y) : p.lineTo(x, y); }
    X.stroke(p); X.dot(P[0], 4); X.label('VWAP ' + X.fmt(pv / vv), X.x(B.length - 1) + 6, X.y(pv / vv), d.style.color); } });
  const vpTool = (g, X, d, i1, i2) => { const B = X.bars; i1 = Math.max(0, i1); i2 = Math.min(B.length - 1, i2); if (i2 <= i1) return; const D = App.ta.prep(B), vp = App.volumeProfile(D, i1, i2, 24); const x1 = X.x(i1), x2 = X.x(i2);
    X.rect({ x: x1, y: X.y(vp.lo + vp.step * 24) }, { x: x2, y: X.y(vp.lo) }, { fill: X.alpha(d.style.color, 0.04), width: 1, dash: 'dotted' }); App.drawProfile(g, { y: X.y, W: X.W, seg: (gg, a, b, c, e, col, ds, w) => X.line({ x: a, y: b }, { x: c, y: e }, { color: col, width: w || 1 }) }, vp, x1, (x2 - x1) * 0.7, false); };
  reg('predict', 'fixedvp', 'Khối lượng giao dịch phạm vi cố định', { icon: IC.fvp, draw(g, P, d, X) { let a = X.idx(d.pts[0].t), b = X.idx(d.pts[1].t); if (a > b) [a, b] = [b, a]; vpTool(g, X, d, a, b); } });
  reg('predict', 'anchoredvp', 'Khối lượng giao dịch được neo', { n: 1, icon: IC.avp, draw(g, P, d, X) { vpTool(g, X, d, X.idx(d.pts[0].t), X.bars.length - 1); X.vl(P[0].x, { width: 1, dash: 'dashed' }); } });
  const measure = (mode) => function (g, P, d, X) {
    const [a, b] = P, up = d.pts[1].p >= d.pts[0].p, col = mode === 'date' ? '#2962ff' : up ? '#2962ff' : '#f23645';
    X.rect(a, b, { fill: X.alpha(col, 0.15), stroke: false });
    const bars = Math.round(DR.t2l(d.pts[1].t) - DR.t2l(d.pts[0].t)), B = X.bars; let vol = 0; const i1 = Math.max(0, Math.min(X.idx(d.pts[0].t), X.idx(d.pts[1].t))), i2 = Math.min(B.length - 1, Math.max(X.idx(d.pts[0].t), X.idx(d.pts[1].t))); for (let i = i1; i <= i2; i++) vol += B[i].volume || 0;
    if (mode !== 'date') { X.line({ x: (a.x + b.x) / 2, y: a.y }, { x: (a.x + b.x) / 2, y: b.y }, { color: col }); X.arrowHead({ x: (a.x + b.x) / 2, y: a.y }, { x: (a.x + b.x) / 2, y: b.y }, 8, col); }
    if (mode !== 'price') { X.line({ x: a.x, y: (a.y + b.y) / 2 }, { x: b.x, y: (a.y + b.y) / 2 }, { color: col }); X.arrowHead({ x: a.x, y: (a.y + b.y) / 2 }, { x: b.x, y: (a.y + b.y) / 2 }, 8, col); }
    const lines = []; if (mode !== 'date') lines.push(`${X.fmt(d.pts[1].p - d.pts[0].p)} (${pct(d.pts[0].p, d.pts[1].p)})`);
    if (mode !== 'price') lines.push(`${bars} nến, ${App.fmtSpan(Math.abs(bars) * DR.step())}`, `KL ${App.fmtVol(vol)}`);
    X.text(lines.join('\n'), (a.x + b.x) / 2, Math.max(a.y, b.y) + 6, { align: 'center', base: 'top', bg: col, color: '#fff', size: 11 });
  };
  reg('predict', 'pricerange', 'Khoảng giá', { icon: IC.prange, draw: measure('price') });
  reg('predict', 'daterange', 'Phạm vi ngày', { icon: IC.drange, draw: measure('date') });
  reg('predict', 'dateprice', 'Phạm vi ngày và giá', { icon: IC.dprange, draw: measure('both') });
  reg('tools', 'measure', 'Công cụ đo lường', { icon: IC.measure, draw: measure('both'), hidden: true, temp: true });

  /* ============ CÁC DẠNG HÌNH HỌC ============ */
  reg('geo', 'brush', 'Cọ vẽ', { n: 'free', icon: IC.brush, draw(g, P, d, X) { const p = new Path2D(); P.forEach((q, k) => k ? p.lineTo(q.x, q.y) : p.moveTo(q.x, q.y)); g.lineJoin = g.lineCap = 'round'; X.stroke(p); } });
  reg('geo', 'highlighter', 'Công cụ đánh dấu', { n: 'free', icon: IC.hilite, style: { color: '#ffeb3b', width: 14 }, draw(g, P, d, X) { const p = new Path2D(); P.forEach((q, k) => k ? p.lineTo(q.x, q.y) : p.moveTo(q.x, q.y)); g.lineJoin = g.lineCap = 'round'; g.globalAlpha = 0.35; X.stroke(p); } });
  reg('geo', 'arrowmarker', 'Mũi tên đánh dấu', { icon: IC.amark, draw(g, P, d, X) {
    const [a, b] = P, ang = Math.atan2(b.y - a.y, b.x - a.x), L = dist(a, b), w = Math.max(4, L * 0.08), hw = w * 2.2, hl = Math.min(L * 0.4, hw * 1.6);
    const pt = (u, v) => ({ x: a.x + u * Math.cos(ang) - v * Math.sin(ang), y: a.y + u * Math.sin(ang) + v * Math.cos(ang) });
    const pts = [pt(0, -w / 2), pt(L - hl, -w / 2), pt(L - hl, -hw / 2), pt(L, 0), pt(L - hl, hw / 2), pt(L - hl, w / 2), pt(0, w / 2)];
    X.poly(pts, { close: true, fill: d.style.color, width: 1 }); if (d.style.text) X.text(d.style.text, a.x, a.y + 14, { align: 'center' }); }, text: true, askText: false });
  reg('geo', 'arrow', 'Mũi tên', { icon: IC.arrow, draw(g, P, d, X) { X.line(P[0], P[1]); X.arrowHead(P[0], P[1], 12); } });
  const bigArrow = up => ({ n: 1, icon: up ? IC.aup : IC.adn, style: { color: up ? '#089981' : '#f23645' }, text: true, askText: false, draw(g, P, d, X) {
    const { x, y } = P[0], s = up ? 1 : -1, w = 9;
    X.poly([{ x, y }, { x: x + w * 1.6, y: y + s * 16 }, { x: x + w * 0.6, y: y + s * 16 }, { x: x + w * 0.6, y: y + s * 34 }, { x: x - w * 0.6, y: y + s * 34 }, { x: x - w * 0.6, y: y + s * 16 }, { x: x - w * 1.6, y: y + s * 16 }], { close: true, fill: d.style.color, width: 1 });
    if (d.style.text) X.text(d.style.text, x, y + s * 46, { align: 'center', color: d.style.color }); } });
  reg('geo', 'arrowup', 'Mũi tên chỉ lên', bigArrow(true));
  reg('geo', 'arrowdown', 'Mũi tên chỉ xuống', bigArrow(false));
  reg('geo', 'rect', 'Hình chữ nhật', { icon: IC.rect, draw(g, P, d, X) { X.rect(P[0], P[1], { fill: d.style.nofill ? null : X.alpha(d.style.color, 0.15) }); if (d.style.text) X.text(d.style.text, (P[0].x + P[1].x) / 2, (P[0].y + P[1].y) / 2, { align: 'center' }); }, text: true, askText: false });
  reg('geo', 'rotrect', 'Hình chữ nhật xoay', { n: 3, icon: IC.rotrect, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || b, dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L, w = (c.x - a.x) * nx + (c.y - a.y) * ny;
    X.poly([a, b, { x: b.x + nx * w, y: b.y + ny * w }, { x: a.x + nx * w, y: a.y + ny * w }], { close: true, fill: X.alpha(d.style.color, 0.15) }); } });
  reg('geo', 'path', 'Đường dẫn', { n: 'multi', icon: IC.path, draw(g, P, d, X) { X.poly(P); if (P.length > 1) X.arrowHead(P[P.length - 2], P[P.length - 1], 11); } });
  reg('geo', 'circle', 'Đường tròn', { icon: IC.circle, draw(g, P, d, X) { const p = new Path2D(); p.arc(P[0].x, P[0].y, dist(P[0], P[1]), 0, Math.PI * 2); X.fill(p, X.alpha(d.style.color, 0.12)); X.stroke(p); } });
  reg('geo', 'ellipse', 'Hình elip', { icon: IC.ellipse, draw(g, P, d, X) { const [a, b] = P, p = new Path2D(); p.ellipse((a.x + b.x) / 2, (a.y + b.y) / 2, Math.abs(b.x - a.x) / 2 || 1, Math.abs(b.y - a.y) / 2 || 1, 0, 0, Math.PI * 2); X.fill(p, X.alpha(d.style.color, 0.12)); X.stroke(p); } });
  reg('geo', 'polyline', 'Hình Polyline', { n: 'multi', icon: IC.polyline, draw(g, P, d, X) { X.poly(P, { close: P.length > 2 && !DR.pending, fill: P.length > 2 ? X.alpha(d.style.color, 0.12) : null }); } });
  reg('geo', 'triangle', 'Hình tam giác', { n: 3, icon: IC.tri, draw(g, P, d, X) { X.poly(P, { close: true, fill: X.alpha(d.style.color, 0.15) }); } });
  reg('geo', 'arc', 'Hình vòng cung', { n: 3, icon: IC.arc, draw(g, P, d, X) {
    const [a, b] = P, c = P[2] || mid(a, b), p = new Path2D(); p.moveTo(a.x, a.y); p.quadraticCurveTo(2 * c.x - (a.x + b.x) / 2, 2 * c.y - (a.y + b.y) / 2, b.x, b.y); p.closePath(); X.fill(p, X.alpha(d.style.color, 0.15)); X.stroke(p); } });
  reg('geo', 'curve', 'Đường cong', { n: 3, icon: IC.curve, draw(g, P, d, X) { const [a, b] = P, c = P[2] || mid(a, b), p = new Path2D(); p.moveTo(a.x, a.y); p.quadraticCurveTo(2 * c.x - (a.x + b.x) / 2, 2 * c.y - (a.y + b.y) / 2, b.x, b.y); X.stroke(p); } });
  reg('geo', 'dcurve', 'Đường cong đôi', { n: 4, icon: IC.dcurve, draw(g, P, d, X) { const [a, b] = P, c = P[2] || a, e = P[3] || b, p = new Path2D(); p.moveTo(a.x, a.y); p.bezierCurveTo(c.x, c.y, e.x, e.y, b.x, b.y); X.stroke(p); } });

  /* ============ CHÚ THÍCH ============ */
  const T1 = { n: 1, text: true };
  reg('note', 'text', 'Văn bản', Object.assign({}, T1, { icon: IC.text, defText: 'Văn bản', style: { fontSize: 14 }, draw(g, P, d, X) { const r = X.text(d.style.text || 'Văn bản', P[0].x, P[0].y, { size: d.style.fontSize || 14, color: d.style.color, base: 'top' }); const w = g.measureText(d.style.text || 'Văn bản').width; X.hit(new Path2D(`M${P[0].x} ${P[0].y}h${w}v${(d.style.fontSize || 14) * 1.3 * String(d.style.text || '').split('\n').length}h${-w}z`), 'fill'); void r; }, multiline: true }));
  reg('note', 'anchorednote', 'Ghi chú', Object.assign({}, T1, { icon: IC.note, defText: 'Ghi chú', draw(g, P, d, X) { X.dot(P[0], 4); X.line(P[0], { x: P[0].x, y: P[0].y - 26 }, { width: 1 }); X.text(d.style.text || 'Ghi chú', P[0].x, P[0].y - 26, { align: 'center', base: 'bottom', bg: X.alpha(d.style.color, 0.9), color: '#fff' }); }, multiline: true }));
  reg('note', 'pricenote', 'Ghi chú giá', { icon: IC.pnote, draw(g, P, d, X) { X.dot(P[0], 4); X.line(P[0], P[1], { width: 1 }); X.text(X.fmt(d.pts[0].p), P[1].x, P[1].y, { align: 'center', bg: d.style.color, color: '#fff' }); } });
  reg('note', 'pin', 'Pin', Object.assign({}, T1, { icon: IC.pin, defText: '', draw(g, P, d, X) {
    const { x, y } = P[0], p = new Path2D(); p.moveTo(x, y); p.bezierCurveTo(x - 12, y - 14, x - 10, y - 28, x, y - 28); p.bezierCurveTo(x + 10, y - 28, x + 12, y - 14, x, y); X.fill(p, d.style.color);
    X.dot({ x, y: y - 19 }, 4, '#fff'); if (d.style.text && (DR.sel === d || DR.hover === d || d.style.showText)) X.text(d.style.text, x + 14, y - 22, { bg: App.theme.panel, border: d.style.color, color: App.theme.text, size: 12 }); } }));
  reg('note', 'table', 'Bảng', Object.assign({}, T1, { icon: IC.table, defText: 'Cột 1 | Cột 2\nA | 1\nB | 2', textLabel: 'Nội dung bảng (mỗi dòng một hàng, dùng | để chia cột)', multiline: true, draw(g, P, d, X) {
    const rows = String(d.style.text || '').split('\n').map(r => r.split('|').map(c => c.trim())), cols = Math.max(...rows.map(r => r.length));
    g.font = '12px -apple-system, Segoe UI, sans-serif'; const cw = []; for (let c = 0; c < cols; c++) cw[c] = Math.max(40, ...rows.map(r => g.measureText(r[c] || '').width + 14));
    const rh = 22, W = cw.reduce((s, x) => s + x, 0), Hh = rh * rows.length, { x, y } = P[0];
    X.fill(new Path2D(`M${x} ${y}h${W}v${Hh}h${-W}z`), App.theme.panel); X.fill(new Path2D(`M${x} ${y}h${W}v${rh}h${-W}z`), X.alpha(d.style.color, 0.85), false);
    const grid = new Path2D(); for (let r = 0; r <= rows.length; r++) { grid.moveTo(x, y + r * rh); grid.lineTo(x + W, y + r * rh); } let cx = x; for (let c = 0; c <= cols; c++) { grid.moveTo(cx, y); grid.lineTo(cx, y + Hh); cx += cw[c] || 0; }
    X.stroke(grid, App.theme.line, 1, 'solid');
    rows.forEach((r, ri) => { let xx = x; r.forEach((cell, ci) => { X.text(cell, xx + 7, y + ri * rh + rh / 2, { size: 12, color: ri ? App.theme.text : '#fff', bold: !ri }); xx += cw[ci]; }); }); } }));
  reg('note', 'callout', 'Chú thích', { icon: IC.callout, text: true, defText: 'Chú thích', multiline: true, draw(g, P, d, X) {
    const [a, b] = P; g.font = '12px sans-serif'; const r = X.text(d.style.text || 'Chú thích', b.x, b.y, { align: 'center', bg: X.alpha(d.style.color, 0.92), color: '#fff' });
    if (r) { const p = new Path2D(); p.moveTo(a.x, a.y); p.lineTo(r.x + r.w / 2 - 8, r.y + r.h / 2); p.lineTo(r.x + r.w / 2 + 8, r.y + r.h / 2); p.closePath(); X.fill(p, X.alpha(d.style.color, 0.92)); } } });
  reg('note', 'comment', 'Nhận xét', Object.assign({}, T1, { icon: IC.comment, defText: 'Nhận xét', multiline: true, draw(g, P, d, X) {
    const r = X.text(d.style.text || 'Nhận xét', P[0].x + 10, P[0].y - 26, { bg: App.theme.panel, border: d.style.color, color: App.theme.text, base: 'bottom' });
    if (r) { const p = new Path2D(); p.moveTo(P[0].x, P[0].y); p.lineTo(r.x + 10, r.y + r.h); p.lineTo(r.x + 22, r.y + r.h); p.closePath(); X.fill(p, d.style.color); } } }));
  reg('note', 'pricelabel', 'Nhãn giá', { n: 1, icon: IC.plabel, draw(g, P, d, X) {
    const { x, y } = P[0]; g.font = '12px sans-serif'; const s = X.fmt(d.pts[0].p), w = g.measureText(s).width + 14;
    const p = new Path2D(); p.moveTo(x, y); p.lineTo(x + 8, y - 22); p.lineTo(x + 8 + w, y - 22); p.lineTo(x + 8 + w, y - 44); p.lineTo(x, y - 44); p.closePath();
    const q = new Path2D(); DR.roundRect(q, x, y - 44, w + 8, 22, 4); X.fill(q, d.style.color); X.fill(new Path2D(`M${x} ${y}L${x + 6} ${y - 22}H${x + 14}Z`), d.style.color); X.text(s, x + 7, y - 33, { color: '#fff', size: 12 }); void p; } });
  reg('note', 'signpost', 'Biển chỉ dẫn', Object.assign({}, T1, { icon: IC.sign, defText: '★', draw(g, P, d, X) {
    const { x } = P[0], top = Math.max(18, P[0].y - 60); X.line({ x, y: P[0].y }, { x, y: top + 12 }, { width: 1.5 });
    const c = new Path2D(); c.arc(x, top, 12, 0, Math.PI * 2); X.fill(c, d.style.color); X.text(d.style.text || '★', x, top, { align: 'center', color: '#fff', size: 12 }); } }));
  reg('note', 'flagmark', 'Cờ đánh dấu', { n: 1, icon: IC.flag, style: { color: '#f23645' }, draw(g, P, d, X) {
    const { x, y } = P[0]; X.line({ x, y }, { x, y: y - 30 }, { width: 2 }); X.poly([{ x, y: y - 30 }, { x: x + 20, y: y - 30 }, { x: x + 14, y: y - 24 }, { x: x + 20, y: y - 18 }, { x, y: y - 18 }], { close: true, fill: d.style.color, width: 1 }); } });
  reg('note', 'image', 'Ảnh', { n: 2, icon: IC.image, draw(g, P, d, X) {
    const [a, b] = P; if (!d.style.img) { X.rect(a, b, { fill: X.alpha(d.style.color, 0.08), dash: 'dashed', width: 1 }); X.text('Bấm đúp để chọn ảnh', (a.x + b.x) / 2, (a.y + b.y) / 2, { align: 'center', size: 11 }); return; }
    let im = imgCache[d.id]; if (!im || im.src !== d.style.img) { im = imgCache[d.id] = new Image(); im.src = d.style.img; }
    if (im.complete) g.drawImage(im, Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y)); X.rect(a, b, { fill: 'rgba(0,0,0,0.001)', stroke: DR.sel === d, width: 1 }); },
    finalize(d) { setTimeout(() => App.ui.pickImage(d), 50); } });
  const imgCache = {};

  /* ============ HÌNH ẢNH (biểu tượng cảm xúc, ký hiệu) ============ */
  const EMOJI = ['🚀', '📈', '📉', '💰', '💎', '🔥', '⚠️', '✅', '❌', '⭐', '🎯', '🐂', '🐻', '🌙', '☀️', '⚡', '💡', '🔔', '📌', '🏁', '👍', '👎', '😀', '😱', '🤔', '💪', '🙏', '❤️', '🟢', '🔴', '🟡', '🔵', '⬆️', '⬇️', '➡️', '⬅️', '❗', '❓', '💲', '🪙'];
  DR.EMOJI = EMOJI;
  EMOJI.forEach((em, k) => reg('img', 'emo' + k, em, { n: 1, emoji: em, icon: `<span class="emo">${em}</span>`, style: { fontSize: 28 }, draw(g, P, d, X) {
    const s = d.style.fontSize || 28; g.font = `${s}px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(em, P[0].x, P[0].y);
    X.hit(new Path2D(`M${P[0].x - s / 2} ${P[0].y - s / 2}h${s}v${s}h${-s}z`), 'fill'); } }));
})(window.App);
