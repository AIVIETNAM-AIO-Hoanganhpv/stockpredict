/* =========================================================
 * drawcore.js — Khung xử lý công cụ vẽ
 *  - Lưu hình theo (thời gian, giá) để bám biểu đồ khi kéo/zoom
 *  - Vẽ trên một <canvas> phủ lên khung giá
 *  - Chọn, kéo điểm, kéo cả hình, khoá, ẩn, nhân bản, xoá
 *  - Nam châm (yếu/mạnh), giữ chế độ vẽ, đo nhanh
 * ========================================================= */
(function (App) {
  'use strict';
  const DR = App.draw = {
    TOOLS: {},          // id -> định nghĩa công cụ (xem tools.js)
    CATS: [],           // danh sách nhóm
    list: [],           // hình đã vẽ của mã hiện tại
    tool: 'cursor',
    pending: null,      // hình đang vẽ dở
    sel: null,          // hình đang chọn
    hover: null,
    magnet: App.store.get('magnet', 'off'), // off | weak | strong
    keep: App.store.get('keepDraw', false),
    hideAll: false, lockAll: false,
    favs: App.store.get('drawFavs', ['trend', 'hline', 'fibret', 'rect', 'long', 'text']),
    style: Object.assign({ color: '#2962ff', width: 2, dash: 'solid' }, App.store.get('drawStyle', {}))
  };
  let uid = Date.now();

  DR.reg = (cat, id, name, def) => { DR.TOOLS[id] = Object.assign({ id, name, cat, n: 2 }, def); };

  /* ---------- Lưu trữ theo mã ---------- */
  DR.key = () => 'drw:' + App.state.src + ':' + App.state.sym;
  DR.load = () => { DR.list = App.store.get(DR.key(), []); DR.pending = null; DR.sel = null; DR.toolbar(); };
  DR.save = () => { App.store.set(DR.key(), DR.list.map(d => { const c = Object.assign({}, d); delete c._hit; return c; })); App.ui && App.ui.refreshTree && App.ui.refreshTree(); };

  /* ---------- Quy đổi toạ độ ---------- */
  const bars = () => App.chart.viewBars();
  DR.step = () => { const b = bars(); return b.length > 1 ? b[b.length - 1].time - b[b.length - 2].time : (App.TF[App.state.tf] || 86400); };
  DR.t2l = function (t) {
    const b = bars(), n = b.length; if (!n) return null;
    if (t >= b[n - 1].time) return n - 1 + (t - b[n - 1].time) / DR.step();
    if (t <= b[0].time) return (t - b[0].time) / DR.step();
    let lo = 0, hi = n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (b[m].time <= t) lo = m; else hi = m; }
    return lo + (t - b[lo].time) / (b[hi].time - b[lo].time);
  };
  DR.l2t = function (l) {
    const b = bars(), n = b.length;
    if (l >= n - 1) return b[n - 1].time + (l - (n - 1)) * DR.step();
    if (l <= 0) return b[0].time + l * DR.step();
    const i = Math.floor(l); return b[i].time + (l - i) * (b[i + 1].time - b[i].time);
  };
  const ts = () => App.chart.api.timeScale();
  DR.toPx = pt => { const l = DR.t2l(pt.t), x = l == null ? null : ts().logicalToCoordinate(l), y = App.chart.main.priceToCoordinate(pt.p); return x == null || y == null ? null : { x, y }; };
  DR.fromPx = function (x, y, snap) {
    let l = ts().coordinateToLogical(x), p = App.chart.main.coordinateToPrice(y);
    if (l == null || p == null) return null;
    if (snap !== false && DR.magnet !== 'off') {
      const b = bars()[Math.round(l)];
      if (b) {
        let best = null, bd = DR.magnet === 'strong' ? 1e9 : 14;
        [b.open, b.high, b.low, b.close].forEach(v => { const yy = App.chart.main.priceToCoordinate(v); if (yy != null && Math.abs(yy - y) < bd) { bd = Math.abs(yy - y); best = v; } });
        if (best != null) { p = best; l = Math.round(l); }
      }
    }
    return { t: DR.l2t(l), p };
  };

  /* ---------- Bộ hỗ trợ vẽ cho từng công cụ ---------- */
  function makeX(g, d) {
    const W = DR.W, H = DR.H;
    const X = {
      W, H, g, d,
      y: p => App.chart.main.priceToCoordinate(p),
      x: l => ts().logicalToCoordinate(l),
      price: y => App.chart.main.coordinateToPrice(y),
      xt: t => { const l = DR.t2l(t); return l == null ? null : ts().logicalToCoordinate(l); },
      idx: t => Math.round(DR.t2l(t)),
      bars: bars(),
      hit(path, mode) { d._hit.push([path, mode || 'stroke']); },
      dash(st) { g.setLineDash(st === 'dashed' ? [6, 4] : st === 'dotted' ? [2, 3] : []); },
      stroke(path, col, w, dash) { g.strokeStyle = col || d.style.color; g.lineWidth = w || d.style.width; X.dash(dash || d.style.dash); g.stroke(path); g.setLineDash([]); X.hit(path); },
      fill(path, col, hit = true) { g.fillStyle = col; g.fill(path); if (hit) X.hit(path, 'fill'); },
      line(a, b, o = {}) { const p = new Path2D(); let A = a, B = b; if (o.extL || o.extR) [A, B] = X.extend(a, b, o.extL, o.extR); p.moveTo(A.x, A.y); p.lineTo(B.x, B.y); X.stroke(p, o.color, o.width, o.dash); return p; },
      extend(a, b, L, R) {
        const dx = b.x - a.x, dy = b.y - a.y, big = 1e5;
        if (!dx && !dy) return [a, b];
        const k = big / Math.max(1e-9, Math.hypot(dx, dy));
        return [L ? { x: a.x - dx * k, y: a.y - dy * k } : a, R ? { x: b.x + dx * k, y: b.y + dy * k } : b];
      },
      poly(pts, o = {}) { const p = new Path2D(); pts.forEach((q, k) => k ? p.lineTo(q.x, q.y) : p.moveTo(q.x, q.y)); if (o.close) p.closePath(); if (o.fill) X.fill(p, o.fill); X.stroke(p, o.color, o.width, o.dash); return p; },
      rect(a, b, o = {}) { const p = new Path2D(); p.rect(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y)); if (o.fill !== null) X.fill(p, o.fill || X.alpha(o.color || d.style.color, 0.15)); if (o.stroke !== false) X.stroke(p, o.color, o.width, o.dash); return p; },
      hl(y, x1 = 0, x2 = W, o = {}) { return X.line({ x: x1, y }, { x: x2, y }, o); },
      vl(x, o = {}) { return X.line({ x, y: 0 }, { x, y: H }, o); },
      text(s, x, y, o = {}) {
        g.font = `${o.bold ? '600 ' : ''}${o.size || d.style.fontSize || 12}px -apple-system, Segoe UI, Roboto, sans-serif`;
        g.textAlign = o.align || 'left'; g.textBaseline = o.base || 'middle';
        const lines = String(s).split('\n'), lh = (o.size || d.style.fontSize || 12) * 1.3;
        if (o.bg) {
          const w = Math.max(...lines.map(l => g.measureText(l).width)) + 10, h = lh * lines.length + 6;
          const bx = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x - 5, by = o.base === 'bottom' ? y - h : o.base === 'top' ? y : y - h / 2;
          const p = new Path2D(); roundRect(p, bx, by, w, h, 4); g.fillStyle = o.bg; g.fill(p); if (o.border) { g.strokeStyle = o.border; g.lineWidth = 1; g.stroke(p); } X.hit(p, 'fill');
          g.fillStyle = o.color || '#fff'; g.textBaseline = 'middle';
          lines.forEach((l, k) => g.fillText(l, o.align === 'center' ? x : o.align === 'right' ? x - 5 : x, by + 3 + lh * (k + 0.5)));
          return { x: bx, y: by, w, h };
        }
        g.fillStyle = o.color || d.style.color;
        lines.forEach((l, k) => g.fillText(l, x, y + k * lh));
        return null;
      },
      label(s, x, y, col, align = 'left') { return X.text(s, x, y, { bg: col || d.style.color, color: '#fff', align, size: 11 }); },
      dot(p, r = 3, col) { const q = new Path2D(); q.arc(p.x, p.y, r, 0, Math.PI * 2); g.fillStyle = col || d.style.color; g.fill(q); },
      arrowHead(a, b, size = 10, col) { const ang = Math.atan2(b.y - a.y, b.x - a.x), p = new Path2D(); p.moveTo(b.x, b.y); p.lineTo(b.x - size * Math.cos(ang - 0.45), b.y - size * Math.sin(ang - 0.45)); p.lineTo(b.x - size * Math.cos(ang + 0.45), b.y - size * Math.sin(ang + 0.45)); p.closePath(); g.fillStyle = col || d.style.color; g.fill(p); X.hit(p, 'fill'); },
      alpha(hex, a) { if (!hex || hex[0] !== '#') return hex; const n = parseInt(hex.slice(1, 7), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; },
      fmt: App.fmtPrice
    };
    return X;
  }
  function roundRect(p, x, y, w, h, r) { p.moveTo(x + r, y); p.arcTo(x + w, y, x + w, y + h, r); p.arcTo(x + w, y + h, x, y + h, r); p.arcTo(x, y + h, x, y, r); p.arcTo(x, y, x + w, y, r); p.closePath(); }
  DR.roundRect = roundRect;

  /* ---------- Khởi tạo lớp vẽ & sự kiện ---------- */
  DR.init = function (wrap) {
    DR.wrap = wrap;
    const cv = DR.cv = document.createElement('canvas');
    cv.className = 'draw-layer'; wrap.appendChild(cv);
    DR.g = cv.getContext('2d');
    // Lớp phủ chỉ báo (vẽ dưới hình vẽ) dùng chung canvas này
    wrap.addEventListener('pointerdown', onDown, true);
    wrap.addEventListener('pointermove', onMove, true);
    window.addEventListener('pointerup', onUp, true);
    wrap.addEventListener('dblclick', e => { if (DR.pending && DR.TOOLS[DR.pending.tool].n === 'multi') { finishMulti(); e.stopPropagation(); } else if (DR.sel && DR.TOOLS[DR.sel.tool].text) DR.editText(DR.sel); }, true);
    window.addEventListener('keydown', e => {
      if (e.target.matches('input,textarea,select')) return;
      if (e.key === 'Escape') { if (DR.pending && DR.TOOLS[DR.pending.tool].n === 'multi' && DR.pending.pts.length > 2) finishMulti(); else { DR.pending = null; DR.setTool('cursor'); } DR.select(null); }
      if ((e.key === 'Delete' || e.key === 'Backspace') && DR.sel) { DR.remove(DR.sel); e.preventDefault(); }
      if (e.key === 'Enter' && DR.pending) finishMulti();
    });
    const loop = () => { DR.render(); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  };

  DR.setTool = function (t) {
    if (t === 'eraser' || DR.TOOLS[t] || t === 'cursor') DR.tool = t;
    DR.pending = null;
    DR.wrap.classList.toggle('drawing', t !== 'cursor');
    App.ui && App.ui.onToolChange && App.ui.onToolChange(t);
  };

  const pos = e => { const r = DR.cv.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
  let drag = null;

  function onDown(e) {
    if (e.button === 2) return;
    if (!App.state.bars.length) return;
    let { x, y } = pos(e);
    if (DR.pending && DR.tool !== 'cursor') { x = Math.min(x, DR.W - 1); y = Math.min(y, DR.H - 1); } // điểm sau được kẹp vào khung giá
    if (y > DR.H || x > DR.W) return;        // ngoài khung giá (trục giá / khung chỉ báo)
    const tool = DR.tool;

    if (tool === 'eraser') { const h = DR.hitTest(x, y); if (h) DR.remove(h.d); stop(e); return; }
    if (tool !== 'cursor') {
      stop(e);
      const def = DR.TOOLS[tool], pt = DR.fromPx(x, y);
      if (!pt) return;
      if (def.n === 'free') { DR.pending = mk(tool, [pt]); drag = { free: true }; return; }
      if (!DR.pending) {
        DR.pending = mk(tool, [pt]);
        if (def.init) def.init(DR.pending, DR);
        if (def.n === 1 || DR.pending.pts.length >= def.n) return commit();
        DR.pending.pts.push(Object.assign({}, pt));
        drag = { placing: true, sx: x, sy: y };
        return;
      }
      const P = DR.pending.pts;
      if (def.n === 'multi') {
        const last = DR.toPx(P[P.length - 2]);
        if (last && Math.hypot(last.x - x, last.y - y) < 8 && P.length > 2) return finishMulti();
        P[P.length - 1] = pt; P.push(Object.assign({}, pt)); return;
      }
      P[P.length - 1] = pt;
      if (P.length >= def.n) return commit();
      P.push(Object.assign({}, pt));
      return;
    }
    // Chế độ con trỏ: chọn / kéo hình
    const h = DR.hitTest(x, y);
    if (h) {
      stop(e);
      DR.select(h.d);
      if (h.d.locked || DR.lockAll) return;
      drag = { d: h.d, handle: h.handle, start: DR.fromPx(x, y, false), orig: h.d.pts.map(p => Object.assign({}, p)), moved: false };
    } else if (DR.sel) DR.select(null);
  }
  function onMove(e) {
    const { x, y } = pos(e);
    if (DR.pending) {
      const def = DR.TOOLS[DR.pending.tool], pt = DR.fromPx(x, y);
      if (!pt) return;
      if (def.n === 'free') { if (drag && drag.free) DR.pending.pts.push(DR.fromPx(x, y, false)); stop(e); return; }
      DR.pending.pts[DR.pending.pts.length - 1] = pt;
      return;
    }
    if (drag && drag.d) {
      stop(e);
      const cur = DR.fromPx(x, y, drag.handle != null);
      if (!cur) return;
      const d = drag.d, def = DR.TOOLS[d.tool];
      drag.moved = true;
      if (drag.handle != null) {
        d.pts[drag.handle] = cur;
        if (def.onHandle) def.onHandle(d, drag.handle, drag.orig);
      } else {
        const dl = DR.t2l(cur.t) - DR.t2l(drag.start.t), dp = cur.p - drag.start.p;
        d.pts = drag.orig.map(p => ({ t: DR.l2t(DR.t2l(p.t) + dl), p: p.p + dp }));
      }
      return;
    }
    if (DR.tool === 'cursor') {
      const h = DR.hitTest(x, y);
      DR.hover = h ? h.d : null;
      DR.wrap.classList.toggle('over-draw', !!h);
      DR.wrap.dataset.handle = h && h.handle != null ? '1' : '';
    }
  }
  function onUp() {
    if (drag && drag.free && DR.pending) { commit(); }
    else if (drag && drag.placing && DR.pending) {
      // Kéo-thả để vẽ 2 điểm (thao tác trên điện thoại)
      const def = DR.TOOLS[DR.pending.tool], P = DR.pending.pts, a = DR.toPx(P[0]), b = DR.toPx(P[1]);
      if (def.n === 2 && a && b && Math.hypot(a.x - b.x, a.y - b.y) > 12) commit();
    }
    else if (drag && drag.d && drag.moved) DR.save();
    drag = null;
  }
  function stop(e) { e.preventDefault(); e.stopPropagation(); }
  function mk(tool, pts) { const def = DR.TOOLS[tool]; return { id: 'd' + (uid++), tool, pts, style: Object.assign({}, DR.style, def.style || {}), _hit: [] }; }
  function finishMulti() { if (!DR.pending) return; const P = DR.pending.pts; if (P.length > 2) P.pop(); if (P.length >= 2) commit(); else DR.pending = null; }
  function commit() {
    const d = DR.pending, def = DR.TOOLS[d.tool];
    DR.pending = null; drag = null;
    if (def.finalize) def.finalize(d, DR);
    DR.list.push(d); DR.save(); DR.select(d);
    if (def.text && def.askText !== false) DR.editText(d, true);
    if (!DR.keep) DR.setTool('cursor');
  }

  /* ---------- Chọn & thao tác trên hình ---------- */
  DR.select = function (d) { DR.sel = d; DR.toolbar(); };
  DR.remove = function (d) { DR.list = DR.list.filter(x => x !== d); if (DR.sel === d) DR.select(null); DR.save(); };
  DR.clone = function (d) {
    const c = JSON.parse(JSON.stringify(Object.assign({}, d, { _hit: [] })));
    c.id = 'd' + (uid++); const st = DR.step() * 5;
    c.pts = c.pts.map(p => ({ t: p.t + st, p: p.p })); DR.list.push(c); DR.save(); DR.select(c);
  };
  DR.clearAll = () => { DR.list = []; DR.select(null); DR.save(); };
  DR.editText = function (d, isNew) {
    App.ui.prompt(DR.TOOLS[d.tool].textLabel || 'Nội dung', d.style.text || DR.TOOLS[d.tool].defText || '', v => {
      if (v == null) { if (isNew && !d.style.text && !DR.TOOLS[d.tool].defText) DR.remove(d); return; }
      d.style.text = v; DR.save();
    }, DR.TOOLS[d.tool].multiline);
  };
  DR.toolbar = () => App.ui && App.ui.drawToolbar && App.ui.drawToolbar(DR.sel);

  // Tìm hình dưới con trỏ (ưu tiên tay nắm của hình đang chọn)
  DR.hitTest = function (x, y) {
    if (DR.hideAll) return null;
    const g = DR.g, dpr = window.devicePixelRatio || 1;
    g.save(); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.lineWidth = 12;
    try {
      const order = DR.sel ? [DR.sel].concat(DR.list.slice().reverse()) : DR.list.slice().reverse();
      for (const d of order) {
        if (d.hidden) continue;
        const hs = handles(d);
        for (let k = 0; k < hs.length; k++) if (hs[k] && Math.hypot(hs[k].x - x, hs[k].y - y) < 9) return { d, handle: k };
        for (const [p, mode] of d._hit || []) {
          if (mode === 'fill' ? g.isPointInPath(p, x * dpr, y * dpr) : g.isPointInStroke(p, x * dpr, y * dpr)) return { d, handle: null };
        }
      }
    } finally { g.restore(); }
    return null;
  };
  function handles(d) {
    const def = DR.TOOLS[d.tool];
    if (def.n === 'free') return [];
    return d.pts.map(DR.toPx);
  }

  /* ---------- Vẽ mỗi khung hình ---------- */
  DR.render = function () {
    if (!App.chart.api || !App.state.bars.length) return;
    const cv = DR.cv, dpr = window.devicePixelRatio || 1;
    const panes = App.chart.api.panes();
    DR.W = ts().width();
    DR.H = panes.length ? panes[0].getHeight() : cv.clientHeight;
    const fullW = cv.parentElement.clientWidth;
    if (cv.width !== Math.round(fullW * dpr) || cv.height !== Math.round(DR.H * dpr)) {
      cv.width = Math.round(fullW * dpr); cv.height = Math.round(DR.H * dpr);
      cv.style.width = fullW + 'px'; cv.style.height = DR.H + 'px';
    }
    const g = DR.g;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, fullW, DR.H);
    g.save(); g.beginPath(); g.rect(0, 0, DR.W, DR.H); g.clip();
    // 1) phần vẽ thêm của chỉ báo (mây, hồ sơ khối lượng, pivot…)
    try { App.chart.drawOverlays(g); } catch (e) { console.warn(e); }
    // 2) hình vẽ của người dùng
    if (!DR.hideAll) {
      const all = DR.pending ? DR.list.concat([DR.pending]) : DR.list;
      all.forEach(d => {
        if (d.hidden) return;
        d._hit = [];
        const def = DR.TOOLS[d.tool]; if (!def) return;
        const P = d.pts.map(DR.toPx);
        if (P.some(p => !p)) return;
        g.save();
        try { def.draw(g, P, d, makeX(g, d)); } catch (e) { console.warn('draw', d.tool, e); }
        g.restore();
      });
      // tay nắm của hình đang chọn / đang vẽ
      [DR.sel, DR.pending].forEach(d => {
        if (!d || d.hidden) return;
        handles(d).forEach(p => { if (!p) return; g.beginPath(); g.arc(p.x, p.y, 5, 0, 7); g.fillStyle = App.theme.bg; g.fill(); g.lineWidth = 2; g.strokeStyle = App.theme.accent; g.stroke(); });
      });
    }
    g.restore();
  };
})(window.App);
