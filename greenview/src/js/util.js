/* =========================================================
 * util.js — Các hàm tiện ích dùng chung
 * Mọi module gắn vào đối tượng toàn cục window.App
 * ========================================================= */
window.App = window.App || {};

(function (App) {
  'use strict';

  // Độ lệch múi giờ của máy (giây). Thư viện biểu đồ hiển thị theo UTC,
  // nên ta cộng thêm độ lệch này để trục thời gian hiện đúng giờ địa phương.
  App.TZ = -new Date().getTimezoneOffset() * 60;

  /* ---------- Lưu trữ trong trình duyệt (localStorage) ---------- */
  App.store = {
    get(key, def) {
      try {
        const v = localStorage.getItem('gv:' + key);
        return v == null ? def : JSON.parse(v);
      } catch (e) { return def; }
    },
    set(key, val) {
      try { localStorage.setItem('gv:' + key, JSON.stringify(val)); } catch (e) { /* bộ nhớ đầy hoặc bị chặn */ }
    },
    del(key) { try { localStorage.removeItem('gv:' + key); } catch (e) {} }
  };

  /* ---------- Gọi API trả về JSON, có thời gian chờ ---------- */
  App.fetchJSON = async function (url, opts = {}) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), opts.timeout || 12000);
    try {
      const res = await fetch(url, { signal: ctrl.signal, headers: opts.headers });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } finally {
      clearTimeout(timer);
    }
  };

  // Gắn proxy CORS (nếu cô cấu hình trong Cài đặt) vào trước URL
  App.withProxy = function (url) {
    const p = (App.settings && App.settings.proxy || '').trim();
    if (!p) return url;
    return p.includes('{url}') ? p.replace('{url}', encodeURIComponent(url)) : p + encodeURIComponent(url);
  };

  /* ---------- Định dạng số ---------- */
  App.fmtPrice = function (v) {
    if (v == null || isNaN(v)) return '–';
    const a = Math.abs(v);
    let d = a >= 1000 ? 2 : a >= 1 ? 2 : a >= 0.01 ? 4 : 8;
    if (a >= 100000) d = 0;
    return v.toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d });
  };
  App.fmtVol = function (v) {
    if (v == null || isNaN(v)) return '–';
    const a = Math.abs(v);
    if (a >= 1e9) return (v / 1e9).toFixed(2) + ' tỷ';
    if (a >= 1e6) return (v / 1e6).toFixed(2) + ' tr';
    if (a >= 1e3) return (v / 1e3).toFixed(1) + ' N';
    return v.toFixed(a < 10 ? 3 : 0);
  };
  App.fmtPct = function (v) {
    if (v == null || isNaN(v)) return '–';
    return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
  };
  App.fmtTime = function (sec, withTime = true) {
    // sec là "giờ hiển thị" (đã cộng múi giờ) nên đọc theo UTC
    const d = new Date(sec * 1000);
    const p = n => String(n).padStart(2, '0');
    const s = p(d.getUTCDate()) + '/' + p(d.getUTCMonth() + 1) + '/' + d.getUTCFullYear();
    return withTime ? s + ' ' + p(d.getUTCHours()) + ':' + p(d.getUTCMinutes()) : s;
  };

  // Độ dài khoảng thời gian dạng chữ (VD: 3 ngày 4 giờ)
  App.fmtSpan = function (sec) {
    sec = Math.abs(sec);
    if (sec >= 86400 * 2) return Math.round(sec / 86400) + ' ngày';
    if (sec >= 3600) return Math.floor(sec / 3600) + ' giờ' + (sec % 3600 >= 60 ? ' ' + Math.round((sec % 3600) / 60) + ' phút' : '');
    return Math.round(sec / 60) + ' phút';
  };

  /* ---------- Thông báo nổi (toast) ---------- */
  App.toast = function (msg, type = 'info', ms = 4000) {
    const box = document.getElementById('toasts');
    if (!box) return;
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.textContent = msg;
    box.appendChild(el);
    while (box.children.length > 3) box.firstChild.remove();
    setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 300); }, ms);
  };

  /* ---------- Tiếng "bíp" khi có cảnh báo ---------- */
  let audioCtx = null;
  App.beep = function () {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.25].forEach(t => {
        const o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.frequency.value = 880; o.type = 'sine';
        g.gain.setValueAtTime(0.2, audioCtx.currentTime + t);
        g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + t + 0.2);
        o.connect(g); g.connect(audioCtx.destination);
        o.start(audioCtx.currentTime + t); o.stop(audioCtx.currentTime + t + 0.22);
      });
    } catch (e) {}
  };

  /* ---------- Hộp thoại (modal) tự làm, không dùng alert/prompt ---------- */
  App.openModal = function (id) { document.getElementById(id).classList.add('show'); };
  App.closeModal = function (id) { document.getElementById(id).classList.remove('show'); };

  App.$ = sel => document.querySelector(sel);
  App.$$ = sel => Array.from(document.querySelectorAll(sel));
  App.esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // Bộ sinh số ngẫu nhiên có "hạt giống" — để dữ liệu giả lập ổn định theo mã
  App.seededRandom = function (seedStr) {
    let h = 2166136261;
    for (const ch of seedStr) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
    return function () {
      h += 0x6D2B79F5;
      let t = h;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
})(window.App);
