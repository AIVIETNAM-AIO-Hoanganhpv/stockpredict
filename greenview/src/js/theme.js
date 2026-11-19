/* =========================================================
 * theme.js — Hai giao diện GreenView + logo + bộ biểu tượng
 *   B "Sáng xanh đậm"  : nền trắng xanh nhạt, nhấn xanh rừng
 *   C "Ngọc lục bảo"   : nền xanh đen sâu, nhấn ngọc + vàng chanh
 * ========================================================= */
(function (App) {
  'use strict';
  App.THEMES = {
    dark: { name: 'Ngọc lục bảo (tối)', bg: '#071612', panel: '#0b201b', panel2: '#10291f', hover: '#143329', line: '#17362d', text: '#dcefe8', muted: '#7a9a90',
      accent: '#14d1a0', accentDark: '#0e8f6e', accentSoft: 'rgba(20,209,160,0.18)', lime: '#c6f432', onAccent: '#04130e',
      up: '#14d1a0', down: '#f0596b', chartBg: '#071612', grid: '#0e251f', leaf: '#c6f432', vein: '#071612' },
    light: { name: 'Sáng xanh đậm', bg: '#f6faf7', panel: '#ffffff', panel2: '#eef5f0', hover: '#e3efe7', line: '#dbe8df', text: '#163a26', muted: '#6b8576',
      accent: '#0f7a43', accentDark: '#0f7a43', accentSoft: 'rgba(15,122,67,0.14)', lime: '#0f7a43', onAccent: '#ffffff',
      up: '#0f9d58', down: '#d93f4c', chartBg: '#ffffff', grid: '#eef3ef', leaf: '#0f7a43', vein: '#ffffff' }
  };

  App.logoSVG = (th, size = 26) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5C3.5 10.5 10 3.5 20.5 3.5c0 10.5-6.5 17-17 17z" fill="${th.leaf}"/><path d="M6 17.5l4-4.2 3 2.1 5.2-6.4" stroke="${th.vein}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="18.2" cy="9" r="1.4" fill="${th.vein}"/></svg>`;

  App.setTheme = function (name) {
    const th = App.THEMES[name] || App.THEMES.dark;
    App.themeName = name in App.THEMES ? name : 'dark';
    App.theme = th;
    App.store.set('theme', App.themeName);
    const r = document.documentElement;
    r.dataset.theme = App.themeName;
    Object.entries({ bg: th.bg, panel: th.panel, panel2: th.panel2, hover: th.hover, line: th.line, text: th.text, muted: th.muted, accent: th.accent, 'accent-soft': th.accentSoft, lime: th.lime, 'on-accent': th.onAccent, up: th.up, down: th.down })
      .forEach(([k, v]) => r.style.setProperty('--' + k, v));
    const meta = document.querySelector('meta[name=theme-color]') || Object.assign(document.head.appendChild(document.createElement('meta')), { name: 'theme-color' });
    meta.content = th.bg;
    document.querySelectorAll('.logo').forEach(el => { el.innerHTML = App.logoSVG(th); });
    const fav = document.querySelector('link[rel=icon]') || Object.assign(document.head.appendChild(document.createElement('link')), { rel: 'icon' });
    fav.href = 'data:image/svg+xml,' + encodeURIComponent(App.logoSVG(th, 64).replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"'));
    if (App.chart && App.chart.api) { App.chart.applyTheme(); App.chart.refresh(true); }
    const tb = document.getElementById('btnTheme'); if (tb) tb.innerHTML = App.icon(App.themeName === 'dark' ? 'sun' : 'moon');
  };
  App.theme = App.THEMES[App.store.get('theme', 'dark')] || App.THEMES.dark;

  /* ---------- Biểu tượng giao diện (SVG nét) ---------- */
  const P = {
    plus: 'M12 5v14M5 12h14', fx: 'M14 4c-3 0-3 3-3.5 6S9 17 6 17M8 10h7M14 12l5 6M19 12l-5 6', grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    alarm: 'M12 21a8 8 0 1 0 0-16a8 8 0 1 0 0 16zM12 9v4l2.5 2M4 4l3-2M20 4l-3-2', replay: 'M11 18l-7-6l7-6zM20 18l-7-6l7-6z', camera: 'M4 8h4l2-3h4l2 3h4v11H4zM12 17a3.5 3.5 0 1 0 0-7a3.5 3.5 0 1 0 0 7',
    gear: 'M12 15a3 3 0 1 0 0-6a3 3 0 1 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3a1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5a1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8a1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1a1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5a1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
    dots: 'M5 12h.01M12 12h.01M19 12h.01', menu: 'M4 7h16M4 12h16M4 17h16', list: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01', chart: 'M4 20V4M4 20h16M8 16l4-5l3 3l5-7',
    layers: 'M12 3l9 5l-9 5l-9-5zM3 13l9 5l9-5', gauge: 'M4 18a8 8 0 1 1 16 0M12 18l4-6', info: 'M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 11v6M12 7.5v.01', pen: 'M4 20l4-1l11-11l-3-3L5 16zM14 6l3 3',
    sun: 'M12 16a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4', moon: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z',
    search: 'M11 18a7 7 0 1 0 0-14a7 7 0 1 0 0 14zM20 20l-4-4', star: 'M12 3l2.8 5.7l6.2.9l-4.5 4.4l1 6.2L12 17.3L6.5 20.2l1-6.2L3 9.6l6.2-.9z', x: 'M6 6l12 12M18 6L6 18', chev: 'M9 6l6 6l-6 6', back: 'M15 6l-6 6l6 6', down: 'M6 9l6 6l6-6',
    eye: 'M2 12s4-7 10-7s10 7 10 7s-4 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6a3 3 0 1 0 0 6z', eyeoff: 'M3 3l18 18M10.6 6.1A10 10 0 0 1 12 6c6 0 10 6 10 6a17 17 0 0 1-3 3.5M6.5 7.6C3.8 9.3 2 12 2 12s4 7 10 7a9.7 9.7 0 0 0 4.4-1',
    lock: 'M7 11V8a5 5 0 0 1 10 0v3M5 11h14v10H5z', unlock: 'M7 11V8a5 5 0 0 1 9.6-2M5 11h14v10H5z', trash: 'M4 7h16M10 7V4h4v3M6 7l1 14h10l1-14', copy: 'M8 8h12v12H8zM4 16V4h12', settings2: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0M14 4v4M8 10v4M16 16v4',
    candle: 'M7 4v3M7 17v3M5 7h4v10H5zM17 3v5M17 15v5M15 8h4v7h-4z', save: 'M5 4h11l3 3v13H5zM8 4v5h7V4M8 20v-6h8v6', folder: 'M3 6h6l2 2h10v11H3z', newc: 'M5 4h9l5 5v11H5zM14 4v5h5M12 11v6M9 14h6',
    layout: 'M4 4h16v16H4zM4 10h16M10 10v10', play: 'M7 4l13 8L7 20z', pause: 'M7 4h4v16H7zM14 4h4v16h-4z', step: 'M5 4l10 8l-10 8zM17 4h2v16h-2z', stop: 'M6 6h12v12H6z', target: 'M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 16a4 4 0 1 0 0-8a4 4 0 1 0 0 8z',
    bars: 'M5 20V10M10 20V4M15 20v-7M20 20v-4', bell: 'M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 21h4', data: 'M12 3c5 0 8 1.5 8 3v12c0 1.5-3 3-8 3s-8-1.5-8-3V6c0-1.5 3-3 8-3zM4 6c0 1.5 3 3 8 3s8-1.5 8-3M4 12c0 1.5 3 3 8 3s8-1.5 8-3',
    help: 'M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17v.01', check: 'M5 12l5 5l9-10', edit: 'M4 20h4l11-11l-4-4L4 16zM13 7l4 4', text: 'M6 5h12M12 5v14M9 19h6',
    extL: 'M20 12H4M8 8l-4 4l4 4', extR: 'M4 12h16M16 8l4 4l-4 4', ruler: 'M4 16L16 4l4 4L8 20zM8 12l2 2M11 9l2 2M14 6l2 2'
  };
  App.icon = (name, cls = '') => `<svg class="ico ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${P[name] || P.dots}"/></svg>`;
})(window.App);
