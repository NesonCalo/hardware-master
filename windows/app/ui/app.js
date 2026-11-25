/* ============================================================
   硬件管理大师 — 前端逻辑
   ============================================================ */
(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  const MAX_KEEP_MIN = 180;

  const GROUP_NAME = { cpu: 'CPU', gpu: '显卡', mb: '主板', disk: '硬盘', mem: '内存', other: '其他', ec: '控制器', bat: '电池', net: '网络', psu: '电源' };
  const GROUP_COLORS = {
    cpu: ['#fb923c', '#f97316', '#fbbf24', '#fdba74', '#f59e0b', '#fb7185'],
    gpu: ['#22d3ee', '#38bdf8', '#0ea5e9', '#67e8f9', '#818cf8'],
    mb: ['#a78bfa', '#8b5cf6', '#c084fc', '#7c3aed'],
    disk: ['#34d399', '#10b981', '#6ee7b7', '#2dd4bf'],
    mem: ['#f472b6', '#ec4899'],
    bat: ['#eab308'],
    net: ['#94a3b8'],
    psu: ['#fbbf24'],
    ec: ['#94a3b8'],
    other: ['#94a3b8', '#64748b', '#475569', '#cbd5e1'],
  };

  const S = {
    boot: null,
    admin: false,
    ready: false,
    page: 'overview',
    paused: false,
    win: { temp: 15, net: 5, power: 15 },
    ovWin: 10,
    lastTs: 0,
    ticks: 0,
    charts: {},
    data: {
      tempSeries: new Map(),
      powerSeries: new Map(),
      powerTotal: [],
      netAll: [],
      netNic: new Map(),
      legendValues: new Map(),
      nicRows: new Map(),
      colorByKey: new Map(),
      usedColors: new Set(),
      pickSig: null,
    },
    drv: { data: null, loading: false, filter: 'all', q: '', open: new Set(), backupTimer: null, pollTimer: null },
    lastSnap: null,
    lastNet: null,
    pawnioDismissed: false,
    settings: {},
  };

  // ------------------------------------------------------------ 工具
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const num = (v, d = 1) => (v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(d));

  // 时间格式化：显式跟随界面语言，避免跟随系统区域设置冒出「上午 / 下午」等中文
  const LANG_TAG = { en: 'en-GB', 'zh-CN': 'zh-CN', 'zh-TW': 'zh-TW', 'zh-HK': 'zh-HK' };
  function fmtTime(value) {
    const d = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(d.getTime())) return '—';
    const lang = (typeof I18N !== 'undefined' && I18N.lang) || 'en';
    try {
      return d.toLocaleTimeString(LANG_TAG[lang] || lang, { hour12: false });
    } catch (e) {
      const p = (n) => String(n).padStart(2, '0');
      return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
    }
  }

  function fmtRate(bps) {
    if (bps == null || bps <= 0) return '0 B/s';
    const u = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    let i = 0, v = bps;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v >= 100 ? v.toFixed(0) : v.toFixed(1)} ${u[i]}`;
  }

  function fmtBytes(n) {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0, v = n;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v >= 100 ? v.toFixed(0) : v.toFixed(1)} ${u[i]}`;
  }

  function fmtUptime(sec) {
    if (!sec && sec !== 0) return '—';
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60);
    if (h > 24) return `${Math.floor(h / 24)} ${T('天')} ${h % 24} ${T('小时')}`;
    if (h > 0) return `${h} ${T('小时')} ${m} ${T('分')}`;
    return `${m} ${T('分')} ${String(Math.floor(sec % 60)).padStart(2, '0')} ${T('秒')}`;
  }

  function tempColor(v) {
    if (v == null) return '#76839a';
    if (v < 45) return '#38bdf8';
    if (v < 60) return '#34d399';
    if (v < 72) return '#fbbf24';
    if (v < 85) return '#fb923c';
    return '#f87171';
  }

  function tempState(v) {
    if (v == null) return { text: T('无数据'), cls: 'mute' };
    if (v < 60) return { text: T('正常'), cls: 'ok' };
    if (v < 75) return { text: T('偏温'), cls: 'warn' };
    if (v < 88) return { text: T('高温'), cls: 'warn' };
    return { text: T('过热'), cls: 'err' };
  }

  // 每个传感器固定一种颜色：曲线、图例、传感器卡片共用同一个色值。
  // 调色板按“相邻色相差异最大”的顺序排列，同组传感器依次取色也容易区分。
  const SENSOR_PALETTE = [
    '#22d3ee', '#fb923c', '#a78bfa', '#34d399', '#f472b6', '#facc15', '#60a5fa',
    '#f87171', '#c084fc', '#2dd4bf', '#fdba74', '#93c5fd', '#e879f9', '#a3e635',
    '#fb7185', '#818cf8', '#6ee7b7', '#94a3b8',
  ];

  function seriesColor(key, serverColor) {
    const cached = S.data.colorByKey.get(key);
    if (cached) return cached;
    let color = serverColor;
    if (!color || S.data.usedColors.has(color)) {
      color = SENSOR_PALETTE.find((c) => !S.data.usedColors.has(c))
        || SENSOR_PALETTE[S.data.colorByKey.size % SENSOR_PALETTE.length];
    }
    S.data.usedColors.add(color);
    S.data.colorByKey.set(key, color);
    return color;
  }

  function toast(msg, kind = '') {
    const wrap = $('#toastWrap');
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    el.innerHTML = `<i class="t-dot"></i><div>${T(msg)}</div>`;
    wrap.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateY(6px)'; el.style.transition = 'all .25s'; }, 3200);
    setTimeout(() => el.remove(), 3600);
  }

  // 传感器 / 设备名称：中文界面用中文名，其它语言优先用词典译文，
  // 没有译文就用后端给的英文名，绝不在非中文界面显示中文。
  function DN(obj) {
    if (!obj) return '';
    const zh = (I18N.lang || '').indexOf('zh') === 0;
    const cn = obj.l != null ? obj.l : (typeof obj === 'string' ? obj : '');
    if (zh) return T(cn);
    if (cn && T(cn) !== cn) return T(cn);
    const en = obj.le || obj.name_en || obj.cls_en || obj.msg_en || '';
    if (en) return T(en) !== en ? T(en) : en;
    return cn;
  }

  // 列表分隔符：中文用顿号，其它语言用逗号
  function SEP() { return (I18N.lang || '').indexOf('zh') === 0 ? '、' : ', '; }

  // 后端返回的错误文案：能命中词典就翻，形如「前缀: 值」的只翻前缀
  function errText(msg, fallback) {
    if (!msg) return fallback || '';
    const s = String(msg);
    const idx = s.search(/[:：]/);
    if (idx > 0) {
      const head = s.slice(0, idx);
      const rest = s.slice(idx + 1).trim();
      if (T(head) !== head) return T(head) + (s[idx] === '：' ? '：' : ': ') + rest;
    }
    return T(s);
  }

  function modal(title, bodyHtml, actions) {
    $('#modalTitle').textContent = T(title);
    $('#modalBody').innerHTML = T(bodyHtml);
    const box = $('#modalActions');
    box.innerHTML = '';
    (actions || [{ label: '知道了', primary: true }]).forEach((a) => {
      const b = document.createElement('button');
      b.className = `btn ${a.primary ? 'primary' : 'ghost'}`;
      b.textContent = T(a.label);
      b.onclick = () => { $('#overlay').classList.add('hidden'); a.onClick && a.onClick(); };
      box.appendChild(b);
    });
    $('#overlay').classList.remove('hidden');
  }

  // 本地采集服务：通过 127.0.0.1 上的轻量 HTTP 接口取数（比 JS 桥接更稳）
  let bridgeReady = false;
  const bridge = () => bridgeReady;
  async function call(method, ...args) {
    if (!bridgeReady) throw new Error('bridge-not-ready');
    const res = await fetch('/api/' + method, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args),
      cache: 'no-store',
    });
    if (!res.ok) throw new Error('http-' + res.status);
    return res.json();
  }

  // 带超时的调用：本地桥偶尔阻塞时不让主循环卡死
  function callTimed(method, ms, ...args) {
    return Promise.race([
      call(method, ...args),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
    ]);
  }

  // ------------------------------------------------------------ 画布
  function fitCanvas(cv) {
    const rect = cv.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(1, Math.round(rect.width * dpr));
    const h = Math.max(1, Math.round(rect.height * dpr));
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    const ctx = cv.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w: rect.width, h: rect.height };
  }

  function drawRing(cv, value, opts) {
    if (!cv) return;
    const { ctx, w, h } = fitCanvas(cv);
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 9, lw = 9;
    const start = -Math.PI * 0.78, end = Math.PI * 0.78;

    ctx.beginPath();
    ctx.arc(cx, cy, r, start, end);
    ctx.strokeStyle = 'rgba(255,255,255,0.075)';
    ctx.lineWidth = lw;
    ctx.stroke();

    if (value == null) return;
    const p = clamp(value / (opts.max || 100), 0, 1);
    const ang = start + (end - start) * p;
    const grad = ctx.createLinearGradient(0, h, w, 0);
    grad.addColorStop(0, opts.c1 || '#22d3ee');
    grad.addColorStop(1, opts.c2 || '#a78bfa');

    ctx.save();
    ctx.shadowColor = opts.c2 || '#a78bfa';
    ctx.shadowBlur = 14;
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, ang);
    ctx.strokeStyle = grad;
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.restore();

    const ex = cx + r * Math.cos(ang), ey = cy + r * Math.sin(ang);
    ctx.beginPath();
    ctx.arc(ex, ey, 2.6, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.globalAlpha = 0.85;
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  function drawSpark(cv, values, color, color2) {
    if (!cv) return;
    const { ctx, w, h } = fitCanvas(cv);
    ctx.clearRect(0, 0, w, h);
    if (!values.length) return;
    const pad = 6;
    const max = Math.max(1e-6, ...values);
    const min = Math.min(...values);
    const span = Math.max(max - min, max * 0.15, 1e-6);
    const n = values.length;
    const X = (i) => pad + (w - pad * 2) * (n === 1 ? 0.5 : i / (n - 1));
    const Y = (v) => h - pad - (h - pad * 2) * ((v - min) / span);

    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, color);
    grad.addColorStop(1, color2 || color);

    ctx.beginPath();
    values.forEach((v, i) => { const x = X(i), y = Y(v); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.8;
    ctx.stroke();

    const fill = ctx.createLinearGradient(0, 0, 0, h);
    fill.addColorStop(0, color2 ? color2 + '33' : color + '33');
    fill.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.beginPath();
    values.forEach((v, i) => { const x = X(i), y = Y(v); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.lineTo(X(n - 1), h - pad);
    ctx.lineTo(X(0), h - pad);
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
  }

  // ------------------------------------------------------------ 数据摄取
  function trimPairs(arr, cutoff) {
    let i = 0;
    while (i < arr.length && arr[i] < cutoff) i++;
    if (i > 0) arr.splice(0, i);
  }

  function isMainPower(item) {
    if (item.g === 'cpu') return /封装|package/i.test(item.l);
    if (item.g === 'gpu') return /功耗/.test(item.l);
    return false;
  }

  function trimSeries(map, keepSec) {
    const cutoff = (S.dataEnd || S.lastTs) - keepSec;
    map.forEach((ser) => {
      let i = 0;
      while (i < ser.t.length && ser.t[i] < cutoff) i++;
      if (i > 0) { ser.t.splice(0, i); ser.v.splice(0, i); }
    });
  }

  function ingest(st) {
    const snap = st.snap || {};
    const net = st.net || {};
    S.lastSnap = snap;
    S.lastNet = net;
    S.lastTs = snap.ts || Date.now() / 1000;
    S.ticks++;
    if (snap.ready) S.ready = true;

    if (!S.paused) {
      const t = S.lastTs;
      const seen = new Set();
      (snap.temps || []).forEach((item) => {
        let ser = S.data.tempSeries.get(item.k);
        if (!ser) {
          ser = { l: item.l, le: item.le || '', g: item.g, t: [], v: [], color: seriesColor(item.k, item.c), hidden: false };
          S.data.tempSeries.set(item.k, ser);
        }
        ser.l = item.l; ser.le = item.le || ''; ser.g = item.g;
        ser.t.push(t); ser.v.push(item.v);
        seen.add(item.k);
      });
      // 本次未出现的传感器也补 null 以保持图线中断
      S.data.tempSeries.forEach((ser, k) => {
        if (!seen.has(k)) { ser.t.push(t); ser.v.push(null); }
      });
      trimSeries(S.data.tempSeries, MAX_KEEP_MIN * 60);

      const pseen = new Set();
      (snap.powers || []).forEach((item) => {
        let ser = S.data.powerSeries.get(item.k);
        if (!ser) {
          ser = { l: item.l, le: item.le || '', g: item.g, t: [], v: [], color: seriesColor(item.k, item.c), hidden: false, main: isMainPower(item) };
          S.data.powerSeries.set(item.k, ser);
        }
        ser.l = item.l; ser.le = item.le || ''; ser.g = item.g; ser.main = isMainPower(item);
        ser.t.push(t); ser.v.push(item.v);
        pseen.add(item.k);
      });
      S.data.powerSeries.forEach((ser, k) => {
        if (!pseen.has(k)) { ser.t.push(t); ser.v.push(null); }
      });
      trimSeries(S.data.powerSeries, MAX_KEEP_MIN * 60);

      const sum = snap.summary || {};
      S.data.powerTotal.push([t, (sum.cpu_power || 0) + (sum.gpu_power || 0)]);
      if (S.data.powerTotal.length > MAX_KEEP_MIN * 60) S.data.powerTotal.splice(0, S.data.powerTotal.length - MAX_KEEP_MIN * 60);

      if (net.rows) {
        S.data.netAll.push({ t: S.lastTs, d: net.down || 0, u: net.up || 0 });
        if (S.data.netAll.length > 3600) S.data.netAll.splice(0, S.data.netAll.length - 3600);
        net.rows.forEach((r) => {
          let ns = S.data.netNic.get(r.n);
          if (!ns) { ns = { d: [], u: [] }; S.data.netNic.set(r.n, ns); }
          ns.d.push([S.lastTs, r.down]);
          ns.u.push([S.lastTs, r.up]);
          if (ns.d.length > 3600) { ns.d.splice(0, ns.d.length - 3600); ns.u.splice(0, ns.u.length - 3600); }
        });
      }
      S.dataEnd = t;
    } else {
      S.lastTs = snap.ts || S.lastTs;
    }
  }

  function pairsSince(ser, minutes, maxPts = 1200) {
    const cur = S.dataEnd || S.lastTs;
    const cut = cur - minutes * 60;
    let start = 0;
    const tArr = ser.t;
    while (start < tArr.length && tArr[start] < cut) start++;
    const n = tArr.length - start;
    if (n <= 0) return [];
    const step = Math.max(1, Math.ceil(n / maxPts));
    const out = [];
    for (let i = start; i < tArr.length; i += step) {
      const v = ser.v[i];
      out.push([tArr[i] * 1000, v == null ? null : v]);
    }
    const lastIdx = tArr.length - 1;
    if (out.length && out[out.length - 1][0] !== tArr[lastIdx] * 1000) {
      out.push([tArr[lastIdx] * 1000, ser.v[lastIdx] == null ? null : ser.v[lastIdx]]);
    }
    return out;
  }

  function netPairs(nic, minutes, maxPts = 900) {
    const cur = S.dataEnd || S.lastTs;
    const src = nic ? (S.data.netNic.get(nic) || { d: [], u: [] }) : null;
    const build = (arr) => {
      const cut = cur - minutes * 60;
      let start = 0;
      while (start < arr.length && arr[start][0] < cut) start++;
      const n = arr.length - start;
      if (n <= 0) return [];
      const step = Math.max(1, Math.ceil(n / maxPts));
      const out = [];
      for (let i = start; i < arr.length; i += step) out.push([arr[i][0] * 1000, arr[i][1]]);
      if (arr.length && out.length && out[out.length - 1][0] !== arr[arr.length - 1][0] * 1000) {
        out.push([arr[arr.length - 1][0] * 1000, arr[arr.length - 1][1]]);
      }
      return out;
    };
    if (src) return { down: build(src.d), up: build(src.u) };
    const cut = cur - minutes * 60;
    let start = 0;
    while (start < S.data.netAll.length && S.data.netAll[start].t < cut) start++;
    const n = S.data.netAll.length - start;
    if (n <= 0) return { down: [], up: [] };
    const step = Math.max(1, Math.ceil(n / maxPts));
    const down = [], up = [];
    for (let i = start; i < S.data.netAll.length; i += step) {
      down.push([S.data.netAll[i].t * 1000, S.data.netAll[i].d]);
      up.push([S.data.netAll[i].t * 1000, S.data.netAll[i].u]);
    }
    if (S.data.netAll.length && down.length && down[down.length - 1][0] !== S.data.netAll[S.data.netAll.length - 1].t * 1000) {
      const last = S.data.netAll[S.data.netAll.length - 1];
      down.push([last.t * 1000, last.d]);
      up.push([last.t * 1000, last.u]);
    }
    return { down, up };
  }

  // ------------------------------------------------------------ ECharts 公共配置
  const AXIS_LABEL = { color: '#76839a', fontSize: 10.5, fontFamily: 'Segoe UI' };
  const SPLIT_LINE = { lineStyle: { color: 'rgba(255,255,255,0.055)', width: 1 } };
  const TOOLTIP = {
    backgroundColor: 'rgba(13,17,24,0.94)',
    borderColor: 'rgba(255,255,255,0.12)',
    borderWidth: 1,
    padding: [9, 12],
    textStyle: { color: '#e8eef8', fontSize: 12, fontFamily: 'Segoe UI, Microsoft YaHei UI' },
    axisPointer: { lineStyle: { color: 'rgba(255,255,255,0.16)', width: 1 }, crossStyle: { color: 'rgba(255,255,255,0.16)' }, label: { backgroundColor: '#1b2431', borderColor: 'rgba(255,255,255,0.1)', color: '#cbd5e1', fontSize: 10.5 } },
  };

  function ensureChart(id) {
    if (!S.charts[id]) {
      const el = document.getElementById(id);
      if (!el) return null;
      S.charts[id] = echarts.init(el, null, { renderer: 'canvas' });
    }
    return S.charts[id];
  }

  function resizeCharts() {
    Object.values(S.charts).forEach((c) => { try { c.resize(); } catch (e) { } });
  }

  function tempSeriesOption(minutes, opts = {}) {
    const values = new Map();
    const series = [];
    let keyCount = 0;
    S.data.tempSeries.forEach((ser, k) => {
      if (ser.hidden) return;
      if (opts.onlyMain && !(ser.g === 'cpu' || ser.g === 'gpu')) return;
      const data = pairsSince(ser, minutes);
      if (!data.length) return;
      values.set(DN(ser), ser.v[ser.v.length - 1]);
      series.push({
        name: DN(ser),
        type: 'line',
        showSymbol: false,
        smooth: 0.32,
        sampling: 'lttb',
        lineStyle: { width: ser.g === 'cpu' || ser.g === 'gpu' ? 1.8 : 1.2, color: ser.color, opacity: 0.92 },
        itemStyle: { color: ser.color },
        emphasis: { focus: 'series', lineStyle: { width: 2.4 } },
        data,
        z: ser.g === 'cpu' || ser.g === 'gpu' ? 3 : 2,
      });
      keyCount++;
    });
    S.data.legendValues = values;

    return {
      animation: false,
      grid: { left: 46, right: 18, top: series.length > 8 ? 62 : 34, bottom: 34 },
      tooltip: Object.assign({}, TOOLTIP, {
        trigger: 'axis',
        valueFormatter: (v) => (v == null ? '—' : `${Number(v).toFixed(1)} °C`),
      }),
      legend: {
        type: 'scroll',
        top: 4, left: 0, right: 26,
        itemWidth: 10, itemHeight: 10, itemGap: 13,
        textStyle: { color: '#a7b2c4', fontSize: 10.5, fontFamily: 'Segoe UI, Microsoft YaHei UI' },
        pageIconColor: '#67e8f9', pageIconInactiveColor: '#475569',
        pageIconSize: 9, pageTextStyle: { color: '#76839a', fontSize: 10 },
        formatter: (name) => {
          const v = S.data.legendValues.get(name);
          return v == null ? name : `${name}  ${Number(v).toFixed(1)}°`;
        },
      },
      xAxis: {
        type: 'time',
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
        axisLabel: Object.assign({}, AXIS_LABEL, { hideOverlap: true, formatter: (v) => { const d = new Date(v); return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`; } }),
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 20,
        max: 100,
        axisLabel: Object.assign({}, AXIS_LABEL, { formatter: '{value}°' }),
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: SPLIT_LINE,
        splitNumber: 4,
      },
      dataZoom: [{ type: 'inside', filterMode: 'none' }],
      series,
    };
  }

  function netSeriesOption(minutes, nic) {
    const d = netPairs(nic, minutes);
    return {
      animation: false,
      grid: { left: 62, right: 18, top: 30, bottom: 32 },
      tooltip: Object.assign({}, TOOLTIP, {
        trigger: 'axis',
        valueFormatter: (v) => fmtRate(v),
      }),
      legend: {
        top: 2, left: 0, itemWidth: 10, itemHeight: 10, itemGap: 16,
        textStyle: { color: '#a7b2c4', fontSize: 11, fontFamily: 'Segoe UI, Microsoft YaHei UI' },
      },
      xAxis: {
        type: 'time',
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
        axisLabel: Object.assign({}, AXIS_LABEL, { hideOverlap: true, formatter: (v) => { const dt = new Date(v); return `${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}:${String(dt.getSeconds()).padStart(2, '0')}`; } }),
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: Object.assign({}, AXIS_LABEL, { formatter: (v) => fmtRate(v) }),
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: SPLIT_LINE,
      },
      series: [
        {
          name: T('下行'), type: 'line', showSymbol: false, smooth: 0.3, sampling: 'lttb',
          lineStyle: { width: 1.9, color: '#22d3ee' }, itemStyle: { color: '#22d3ee' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(34,211,238,0.34)' }, { offset: 1, color: 'rgba(34,211,238,0.02)' }]) },
          data: d.down,
        },
        {
          name: T('上行'), type: 'line', showSymbol: false, smooth: 0.3, sampling: 'lttb',
          lineStyle: { width: 1.6, color: '#a78bfa' }, itemStyle: { color: '#a78bfa' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(167,139,250,0.26)' }, { offset: 1, color: 'rgba(167,139,250,0.02)' }]) },
          data: d.up,
        },
      ],
    };
  }

  function powerSeriesOption(minutes) {
    const series = [];
    const values = new Map();
    S.data.powerSeries.forEach((ser) => {
      if (ser.hidden || !ser.main) return;
      const data = pairsSince(ser, minutes);
      if (!data.length) return;
      values.set(DN(ser), ser.v[ser.v.length - 1]);
      const color = ser.g === 'cpu'
        ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(251,191,36,0.35)' }, { offset: 1, color: 'rgba(251,191,36,0.02)' }])
        : new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(244,114,182,0.30)' }, { offset: 1, color: 'rgba(244,114,182,0.02)' }]);
      series.push({
        name: DN(ser), type: 'line', showSymbol: false, smooth: 0.3, sampling: 'lttb',
        lineStyle: { width: 1.9, color: ser.g === 'cpu' ? '#fbbf24' : '#f472b6' },
        itemStyle: { color: ser.g === 'cpu' ? '#fbbf24' : '#f472b6' },
        areaStyle: { color },
        data,
      });
    });
    // 合计曲线
    const total = [];
    const cur = S.dataEnd || S.lastTs;
    const cut = cur - minutes * 60;
    const src = S.data.powerTotal;
    let i0 = 0;
    while (i0 < src.length && src[i0][0] < cut) i0++;
    const step = Math.max(1, Math.ceil((src.length - i0) / 1200));
    for (let i = i0; i < src.length; i += step) total.push([src[i][0] * 1000, src[i][1]]);
    if (total.length) {
      series.push({
        name: T('合计'), type: 'line', showSymbol: false, smooth: 0.3, sampling: 'lttb',
        lineStyle: { width: 1.3, color: '#22d3ee', type: 'dashed', opacity: 0.75 },
        itemStyle: { color: '#22d3ee' },
        data: total,
      });
    }
    return {
      animation: false,
      grid: { left: 52, right: 18, top: 32, bottom: 32 },
      tooltip: Object.assign({}, TOOLTIP, { trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : `${Number(v).toFixed(1)} W`) }),
      legend: {
        top: 2, left: 0, itemWidth: 10, itemHeight: 10, itemGap: 16,
        textStyle: { color: '#a7b2c4', fontSize: 11, fontFamily: 'Segoe UI, Microsoft YaHei UI' },
      },
      xAxis: {
        type: 'time',
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
        axisLabel: Object.assign({}, AXIS_LABEL, { hideOverlap: true, formatter: (v) => { const d = new Date(v); return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`; } }),
        axisTick: { show: false }, splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: Object.assign({}, AXIS_LABEL, { formatter: '{value} W' }),
        axisLine: { show: false }, axisTick: { show: false }, splitLine: SPLIT_LINE,
      },
      series,
    };
  }

  // ------------------------------------------------------------ 概览渲染
  function renderOverview() {
    const snap = S.lastSnap || {};
    const net = S.lastNet || {};
    const sum = snap.summary || {};
    const meta = snap.meta || {};

    $('#ovCpuTemp').textContent = num(sum.cpu_temp);
    $('#ovGpuTemp').textContent = num(sum.gpu_temp);
    $('#ovCpuLoad').textContent = sum.cpu_load != null ? `${num(sum.cpu_load)}%` : '—';
    $('#ovCpuClock').textContent = sum.cpu_clock ? `${(sum.cpu_clock / 1000).toFixed(2)} GHz` : '—';
    $('#ovGpuLoad').textContent = sum.gpu_load != null ? `${num(sum.gpu_load)}%` : '—';

    const hot = sum.hot;
    $('#ovGpuHot').textContent = hot && hot.g === 'gpu' ? `${num(hot.v)}°C` : (sum.gpu_temp ? `${num(sum.gpu_temp)}°C` : '—');

    const ct = tempState(sum.cpu_temp);
    const cpuTag = $('#cpuTag');
    if (sum.cpu_temp == null) {
      cpuTag.textContent = S.admin ? T('未检测到') : T('需管理员');
      cpuTag.className = 'kpi-tag warn';
    } else {
      cpuTag.textContent = ct.text;
      cpuTag.className = `kpi-tag ${ct.cls === 'ok' ? '' : ct.cls}`;
    }
    const gt = tempState(sum.gpu_temp);
    const gpuTag = $('#gpuTag');
    gpuTag.textContent = gt.text;
    gpuTag.className = `kpi-tag ${gt.cls === 'ok' ? '' : gt.cls}`;

    drawRing($('#ringCpu'), sum.cpu_temp, { max: 100, c1: '#38bdf8', c2: tempColor(sum.cpu_temp) });
    drawRing($('#ringGpu'), sum.gpu_temp, { max: 100, c1: '#22d3ee', c2: tempColor(sum.gpu_temp) });

    const totalW = (sum.cpu_power || 0) + (sum.gpu_power || 0);
    $('#ovPower').textContent = (sum.cpu_power == null && sum.gpu_power == null) ? '—' : num(totalW, 0);
    $('#ovPowerSub').textContent = `CPU ${sum.cpu_power == null ? '—' : num(sum.cpu_power, 0)} W · GPU ${sum.gpu_power == null ? '—' : num(sum.gpu_power, 0)} W`;
    drawSpark($('#sparkPower'), S.data.powerTotal.slice(-160).map((p) => p[1]), '#fbbf24', '#fb923c');

    $('#ovDown').textContent = fmtRate(net.down || 0);
    $('#ovUp').textContent = fmtRate(net.up || 0);
    $('#ovNetSub').textContent = `${T('本次')} ↓ ${fmtBytes(net.sess_down)} · ↑ ${fmtBytes(net.sess_up)}`;
    drawSpark($('#sparkNet'), S.data.netAll.slice(-160).map((x) => x.d), '#22d3ee', '#38bdf8');

    // 硬件清单
    if (meta.cpu || meta.gpu) {
      const rows = [
        [T('处理器'), meta.cpu || '—'],
        [T('显卡'), meta.gpu || '—'],
        [T('主板'), meta.mb || '—'],
        [T('内存'), `${num(sum.ram_used_gb, 1)} / ${num(sum.ram_total_gb, 0)} GB`],
        [T('硬盘'), (meta.disk || []).join(SEP()) || '—'],
        [T('系统'), (S.boot && S.boot.os) || '—'],
        [T('采集权限'), S.admin ? T('管理员（完整传感器）') : T('普通用户（部分传感器）')],
        [T('运行时长'), fmtUptime(snap.uptime)],
      ];
      if (S.boot && S.boot.host) rows.push([T('计算机名'), S.boot.host]);
      $('#hwList').innerHTML = rows.map(([k, v]) => `<div class="hw-item"><div class="hw-k">${k}</div><div class="hw-v">${escapeHtml(String(v))}</div></div>`).join('');
    } else {
      $('#hwList').innerHTML = `<div class="hw-item"><div class="hw-k">${T('状态')}</div><div class="hw-v">${T('正在识别硬件…')}</div></div>`;
    }

    if (S.ticks % 2 === 0) {
      const c = ensureChart('chartOvTemp');
      if (c && S.data.tempSeries.size) c.setOption(tempSeriesOption(S.ovWin, { onlyMain: true }), { notMerge: true, lazyUpdate: true });
      const n2 = ensureChart('chartOvNet');
      if (n2) n2.setOption(netSeriesOption(S.ovWin === 10 ? 5 : S.ovWin, ''), { notMerge: true, lazyUpdate: true });
      $('#ovNetHint').textContent = T('最近 5 分钟');
    }
  }

  // ------------------------------------------------------------ 网络渲染
  function renderNetwork() {
    const net = S.lastNet || {};
    $('#netDown').textContent = fmtRate(net.down || 0);
    $('#netUp').textContent = fmtRate(net.up || 0);
    $('#netDownSub').textContent = `${T('峰值')} ${fmtRate(net.peak_down || 0)}`;
    $('#netUpSub').textContent = `${T('峰值')} ${fmtRate(net.peak_up || 0)}`;
    $('#netSess').textContent = `↓ ${fmtBytes(net.sess_down)} / ↑ ${fmtBytes(net.sess_up)}`;
    $('#netSessSub').textContent = `${net.nic_count || 0} ${T('张网卡参与统计')}`;
    $('#netBoot').textContent = `↓ ${fmtBytes(net.boot_down)} / ↑ ${fmtBytes(net.boot_up)}`;
    $('#netBootSub').textContent = T('系统开机以来的累计流量');

    renderNicTable(net.rows || []);
    syncNicSelect(net.rows || []);

    if (S.ticks % 1 === 0) {
      const c = ensureChart('chartNet');
      if (c) c.setOption(netSeriesOption(S.win.net, S.data.nicSel), { notMerge: true, lazyUpdate: true });
    }
  }

  function syncNicSelect(rows) {
    const sel = $('#netNicSel');
    const names = rows.map((r) => r.n);
    const current = S.data.nicSel || '';
    if (!S.data.nicNames || S.data.nicNames.join('|') !== names.join('|')) {
      S.data.nicNames = names;
      sel.innerHTML = `<option value="">${T('全部网卡')}</option>` + names.map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(NICNAME(n))}</option>`).join('');
      sel.value = current;
    }
  }

  function renderNicTable(rows) {
    const body = $('#nicBody');
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="9" class="empty">${T('未检测到网络适配器')}</td></tr>`;
      S.data.nicRows.clear();
      return;
    }
    // 若网卡数量变化，整体重建
    const names = rows.map((r) => r.n).join('|');
    if (!S.data.nicSig || S.data.nicSig !== names) {
      S.data.nicSig = names;
      body.innerHTML = rows.map((r) => `
        <tr class="nic-row" data-nic="${escapeHtml(r.n)}">
          <td><span class="pill ${r.kind === 'wifi' ? 'cyan' : r.kind === 'virtual' ? 'mute' : 'violet'}">${r.kind === 'wifi' ? T('无线') : r.kind === 'virtual' ? T('虚拟') : r.kind === 'bt' ? T('蓝牙') : T('有线')}</span> ${escapeHtml(shortNic(NICNAME(r.n), r.kind))}</td>
          <td class="c-state"></td>
          <td class="c-speed"></td>
          <td class="num c-down"></td>
          <td class="num c-up"></td>
          <td class="num c-sess"></td>
          <td class="num c-total"></td>
          <td class="mono c-ip"></td>
          <td class="mono c-mac"></td>
        </tr>`).join('');
      S.data.nicRows.clear();
      $$('#nicBody .nic-row').forEach((tr) => {
        const name = tr.dataset.nic;
        S.data.nicRows.set(name, {
          tr,
          state: tr.querySelector('.c-state'),
          speed: tr.querySelector('.c-speed'),
          down: tr.querySelector('.c-down'),
          up: tr.querySelector('.c-up'),
          sess: tr.querySelector('.c-sess'),
          total: tr.querySelector('.c-total'),
          ip: tr.querySelector('.c-ip'),
          mac: tr.querySelector('.c-mac'),
        });
        tr.addEventListener('click', () => selectNic(name));
      });
    }
    rows.forEach((r) => {
      const refs = S.data.nicRows.get(r.n);
      if (!refs) return;
      refs.state.innerHTML = r.isup ? `<span class="pill ok">${T('已连接')}</span>` : `<span class="pill mute">${T('断开')}</span>`;
      refs.speed.textContent = r.speed ? (r.speed >= 1000 ? `${(r.speed / 1000).toFixed(r.speed % 1000 === 0 ? 0 : 1)} Gbps` : `${r.speed} Mbps`) : '—';
      refs.down.textContent = fmtRate(r.down);
      refs.down.style.color = r.down > 0 ? '#67e8f9' : '';
      refs.up.textContent = fmtRate(r.up);
      refs.up.style.color = r.up > 0 ? '#c4b5fd' : '';
      refs.sess.textContent = `${fmtBytes(r.s_recv)} / ${fmtBytes(r.s_sent)}`;
      refs.total.textContent = `${fmtBytes(r.recv)} / ${fmtBytes(r.sent)}`;
      refs.ip.textContent = r.ip || '—';
      refs.mac.textContent = r.mac || '—';
      refs.tr.classList.toggle('sel', S.data.nicSel === r.n);
    });
  }

  function selectNic(name) {
    S.data.nicSel = S.data.nicSel === name ? '' : name;
    $('#netNicSel').value = S.data.nicSel;
    $$('#nicBody .nic-row').forEach((tr) => tr.classList.toggle('sel', tr.dataset.nic === S.data.nicSel));
    const c = ensureChart('chartNet');
    if (c) c.setOption(netSeriesOption(S.win.net, S.data.nicSel), { notMerge: true });
  }

  // ------------------------------------------------------------ 温度页渲染
  function renderThermalPage() {
    const snap = S.lastSnap || {};
    const temps = (snap.temps || []).slice().sort((a, b) => b.v - a.v);
    $('#tempCount').textContent = `${temps.length} ${T('个温度点')}`;

    const groups = {};
    temps.forEach((t) => { (groups[t.g] = groups[t.g] || []).push(t); });
    const order = ['cpu', 'gpu', 'mb', 'disk', 'mem', 'bat', 'other', 'ec', 'net', 'psu'];
    const wrap = $('#tempGroups');
    const sig = order.map((g) => `${g}:${(groups[g] || []).length}`).join('|') + '#' + temps.map((t) => t.k).join('|');
    if (!S.data.tempSig || S.data.tempSig !== sig) {
      S.data.tempSig = sig;
      wrap.innerHTML = '';
      S.data.sensorEls = new Map();
      order.forEach((g) => {
        const arr = groups[g];
        if (!arr || !arr.length) return;
        const sec = document.createElement('div');
        sec.className = 'sensor-group';
        const headColor = seriesColor(arr[0].k, arr[0].c);
        sec.innerHTML = `<div class="sg-title"><i style="background:${headColor}"></i>${T(GROUP_NAME[g] || g)}<span class="cnt">${arr.length} ${T('项')}</span></div>`;
        const grid = document.createElement('div');
        grid.className = 'sensor-grid';
        arr.forEach((t) => {
          const ser = S.data.tempSeries.get(t.k);
          const color = seriesColor(t.k, t.c);
          const el = document.createElement('div');
          el.className = `sensor-item${ser && ser.hidden ? ' off' : ''}`;
          el.innerHTML = `
            <div class="sensor-top">
              <i class="sensor-dot" style="background:${color}"></i>
              <span class="sensor-name">${escapeHtml(DN(t))}</span>
              <span class="sensor-val">—<i>°C</i></span>
            </div>
            <div class="sensor-bar"><span style="background:${color}"></span></div>`;
          el.addEventListener('click', () => toggleSeries(t.k));
          S.data.sensorEls.set(t.k, { el, val: el.querySelector('.sensor-val'), bar: el.querySelector('.sensor-bar span') });
          grid.appendChild(el);
        });
        sec.appendChild(grid);
        wrap.appendChild(sec);
      });
    }
    // 更新数值
    const maxV = Math.max(60, ...temps.map((t) => t.v));
    temps.forEach((t) => {
      const refs = S.data.sensorEls && S.data.sensorEls.get(t.k);
      if (!refs) return;
      const color = seriesColor(t.k, t.c);
      refs.val.innerHTML = `${num(t.v)}<i>°C</i>`;
      refs.val.style.color = color;
      refs.bar.style.width = `${clamp((t.v / (maxV + 6)) * 100, 2, 100)}%`;
      refs.bar.style.background = color;
    });

    renderFans(snap.fans || []);
    renderTempStats(snap);

    if (S.ticks % 2 === 0) {
      const c = ensureChart('chartTemp');
      if (c) c.setOption(tempSeriesOption(S.win.temp, { onlyMain: !$('#tempAllSeries').checked }), { notMerge: true, lazyUpdate: true });
    }
  }

  function renderTempStats(snap) {
    const win = S.win.temp;
    let maxItem = null, sum = 0, cnt = 0;
    S.data.tempSeries.forEach((ser) => {
      const n = Math.min(ser.t.length, Math.round(win * 60));
      for (let i = ser.t.length - n; i < ser.t.length; i++) {
        const v = ser.v[i];
        if (v == null) continue;
        sum += v; cnt++;
        if (!maxItem || v > maxItem.v) maxItem = { l: ser.l, le: ser.le, v };
      }
    });
    $('#tempStatHint').textContent = `${T('窗口')} ${win} ${T('分钟')} · ${T('采样 1 秒')}`;
    const cells = [
      [T('记录时长'), `${win} ${T('分钟')}`],
      [T('数据点'), cnt ? `${cnt.toLocaleString()} ${T('项')}` : '—'],
      [T('最高温度'), maxItem ? `${num(maxItem.v)}°C` : '—'],
      [T('平均温度'), cnt ? `${num(sum / cnt)}°C` : '—'],
    ];
    $('#tempStats').innerHTML = cells.map(([k, v]) => `<div class="stat-cell"><span>${k}</span><b>${v}</b></div>`).join('')
      + `<div class="stat-cell"><span>${T('最高温度来源')}</span><b class="sm">${escapeHtml(maxItem ? DN(maxItem) : '—')}</b></div>`;
  }

  function renderFans(fans) {
    $('#fanCount').textContent = fans.length ? `${fans.length} ${T('组')}` : T('未检测到');
    const wrap = $('#fanList');
    const sig = fans.map((f) => f.k).join('|');
    if (!S.data.fanSig || S.data.fanSig !== sig) {
      S.data.fanSig = sig;
      wrap.innerHTML = '';
      S.data.fanEls = new Map();
      if (!fans.length) { wrap.innerHTML = `<div class="hint">${T('主板与显卡未上报风扇转速传感器。')}</div>`; return; }
      fans.forEach((f) => {
        const el = document.createElement('div');
        el.className = 'fan-item';
        el.innerHTML = `<div class="fan-row"><span class="fan-label">${escapeHtml(DN(f))}</span><span class="fan-rpm">—<i>RPM</i></span></div><div class="fan-track"><span></span></div>`;
        S.data.fanEls.set(f.k, { val: el.querySelector('.fan-rpm'), bar: el.querySelector('.fan-track span') });
        wrap.appendChild(el);
      });
    }
    const maxRpm = Math.max(1000, ...fans.map((f) => f.v));
    fans.forEach((f) => {
      const refs = S.data.fanEls && S.data.fanEls.get(f.k);
      if (!refs) return;
      refs.val.innerHTML = `${Math.round(f.v)}<i>RPM</i>`;
      refs.bar.style.width = `${clamp((f.v / maxRpm) * 100, 2, 100)}%`;
    });
  }

  function toggleSeries(key) {
    const ser = S.data.tempSeries.get(key);
    if (!ser) return;
    ser.hidden = !ser.hidden;
    const refs = S.data.sensorEls && S.data.sensorEls.get(key);
    if (refs) refs.el.classList.toggle('off', ser.hidden);
    const c = ensureChart('chartTemp');
    if (c) c.setOption(tempSeriesOption(S.win.temp, { onlyMain: !$('#tempAllSeries').checked }), { notMerge: true });
  }

  // ------------------------------------------------------------ 功耗页渲染
  function renderPowerPage() {
    const snap = S.lastSnap || {};
    const sum = snap.summary || {};
    $('#powCpu').textContent = sum.cpu_power == null ? '—' : num(sum.cpu_power, 1);
    $('#powGpu').textContent = sum.gpu_power == null ? '—' : num(sum.gpu_power, 1);
    const total = (sum.cpu_power || 0) + (sum.gpu_power || 0);
    $('#powTotal').textContent = (sum.cpu_power == null && sum.gpu_power == null) ? '—' : num(total, 1);
    $('#powEnergy').textContent = num(snap.energy_wh, 2);
    $('#powCpuSub').textContent = sum.cpu_power == null ? T('需管理员权限或 PawnIO 驱动') : T('CPU 封装（Package）实测');
    $('#powGpuSub').textContent = sum.gpu_power == null ? T('需管理员权限或 PawnIO 驱动') : T('显卡功耗实测');
    const peak = Math.max(0, ...S.data.powerTotal.slice(-Math.max(60, S.win.power * 60)).map((p) => p[1]));
    $('#powTotalSub').textContent = `${T('峰值')} ${num(peak, 0)} W`;
    $('#powEnergySub').textContent = `${T('运行')} ${fmtUptime(snap.uptime)}`;

    // 传感器列表
    const powers = (snap.powers || []).filter((p) => p.v > 0);
    const wrap = $('#powerList');
    if (!powers.length) {
      if (!S.data.powSig) { wrap.innerHTML = `<div class="hint">${T('当前没有可用的功耗传感器（需要管理员权限或 PawnIO 驱动）。')}</div>`; }
      S.data.powSig = 'none';
    } else {
      const sig = powers.map((p) => p.k).join('|');
      if (!S.data.powSig || S.data.powSig !== sig) {
        S.data.powSig = sig;
        wrap.innerHTML = '';
        S.data.powEls = new Map();
        powers.forEach((p) => {
          const el = document.createElement('div');
          const color = seriesColor(p.k, p.c);
          el.className = 'bar-item';
          el.innerHTML = `<div class="bar-row"><span class="bar-name"><i class="sensor-dot" style="background:${color}"></i>${escapeHtml(DN(p))}</span><span class="bar-val">—<i>W</i></span></div><div class="bar-track"><span style="background:${color}"></span></div>`;
          S.data.powEls.set(p.k, { val: el.querySelector('.bar-val'), bar: el.querySelector('.bar-track span') });
          wrap.appendChild(el);
        });
      }
      const maxW = Math.max(20, ...powers.map((p) => p.v));
      powers.forEach((p) => {
        const refs = S.data.powEls && S.data.powEls.get(p.k);
        if (!refs) return;
        refs.val.innerHTML = `${num(p.v, 1)}<i>W</i>`;
        refs.bar.style.width = `${clamp((p.v / maxW) * 100, 2, 100)}%`;
      });
    }

    const win = S.data.powerTotal.slice(-(S.win.power * 60)).map((p) => p[1]);
    const avg = win.length ? win.reduce((a, b) => a + b, 0) / win.length : 0;
    $('#powNote1').textContent = `${num(total, 1)} W`;
    $('#powNote2').textContent = `${num(avg, 1)} W`;
    $('#powNote3').textContent = `${num(Math.max(0, ...win), 1)} W`;
    const cost = ((snap.energy_wh || 0) / 1000) * 0.55;
    $('#powNote4').textContent = `¥ ${cost.toFixed(3)}`;
    $('#powHint').textContent = `${T('窗口')} ${S.win.power} ${T('分钟')} · ${T('采样 1 秒')}`;

    if (S.ticks % 2 === 0) {
      const c = ensureChart('chartPower');
      if (c) c.setOption(powerSeriesOption(S.win.power), { notMerge: true, lazyUpdate: true });
    }
  }

  // ------------------------------------------------------------ 驱动页
  async function loadDrivers(force) {
    if (force) {
      await call('refresh_drivers');
    }
    const data = await call('drivers');
    S.drv.data = data;
    S.drv.loading = data.loading;
    renderDrivers();
    if (data.loading) {
      clearTimeout(S.drv.pollTimer);
      S.drv.pollTimer = setTimeout(() => loadDrivers(false), 2000);
    }
  }

  // 设备类名 / 设备名 / 状态文案：中文界面用中文，其它语言用词典译文或英文
  function CLS(d) {
    if (!d) return '';
    const zh = (I18N.lang || '').indexOf('zh') === 0;
    const cn = d.cls_cn || '';
    if (zh) return T(cn);
    if (cn && T(cn) !== cn) return T(cn);
    return d.cls_en || cn;
  }

  function MSG(d) {
    if (!d) return '';
    const zh = (I18N.lang || '').indexOf('zh') === 0;
    const cn = d.msg || '';
    if (zh) return T(cn);
    if (cn && T(cn) !== cn) return T(cn);
    return d.msg_en || cn;
  }

  function DEVM(d) {
    if (!d) return '';
    const zh = (I18N.lang || '').indexOf('zh') === 0;
    return zh ? (d.name || '') : (d.name_en || d.name || '');
  }

  function driverMatches(d, q, filter) {
    if (filter === 'err' && !d.code) return false;
    if (filter && filter !== 'err' && filter !== 'all') {
      if ((d.cls || d.cls_cn) !== filter) return false;
    }
    if (!q) return true;
    const hay = `${d.name} ${d.name_en || ''} ${d.mfr} ${d.mfr_en || ''} ${d.inf} ${d.id} ${d.cls_cn} ${d.cls_en || ''} ${d.ver}`.toLowerCase();
    return hay.includes(q.toLowerCase());
  }

  function renderDrivers() {
    const data = S.drv.data;
    if (!data) return;
    const devs = data.devices || [];
    const probs = data.problems || [];
    const sys = data.system || {};
    const pkgs = data.packages || [];

    $('#drvCount').textContent = devs.length || '—';
    $('#drvCountSub').textContent = data.loading ? T('正在读取…') : `${T('上次读取')} ${data.timestamp ? fmtTime(data.timestamp * 1000) : '—'}`;
    $('#drvProblem').textContent = probs.length;
    $('#drvProblemSub').textContent = probs.length ? T('存在异常/禁用设备') : T('所有设备状态正常');
    $('#drvPkg').textContent = pkgs.length || '—';
    $('#drvOs').textContent = sys.caption
      ? ((I18N.lang || '').indexOf('zh') === 0 ? sys.caption : (sys.caption_en || sys.caption)).replace('Microsoft ', '')
      : '—';
    $('#drvHost').textContent = `${sys.vendor || ''} ${sys.model || ''}`.trim() || '—';

    const navBadge = $('#navDrvBadge');
    navBadge.classList.toggle('hidden', !probs.length);

    // chips
    const chipBox = $('#drvChips');
    if (!S.drv.chipSig || S.drv.chipSig !== devs.length) {
      S.drv.chipSig = devs.length;
      const byClass = {};
      devs.forEach((d) => {
        const key = d.cls || d.cls_cn || 'other';
        if (!byClass[key]) byClass[key] = { n: 0, d };
        byClass[key].n += 1;
      });
      const top = Object.entries(byClass).sort((a, b) => b[1].n - a[1].n).slice(0, 8);
      chipBox.innerHTML =
        `<div class="chip ${S.drv.filter === 'all' ? 'active' : ''}" data-f="all">${T('全部')}<span class="c">${devs.length}</span></div>` +
        `<div class="chip err ${S.drv.filter === 'err' ? 'active' : ''}" data-f="err">${T('异常')}<span class="c">${probs.length}</span></div>` +
        top.map(([cls, o]) => `<div class="chip ${S.drv.filter === cls ? 'active' : ''}" data-f="${escapeHtml(cls)}">${escapeHtml(CLS(o.d))}<span class="c">${o.n}</span></div>`).join('');
      $$('#drvChips .chip').forEach((chip) => {
        chip.addEventListener('click', () => {
          S.drv.filter = chip.dataset.f;
          $$('#drvChips .chip').forEach((c) => c.classList.toggle('active', c.dataset.f === S.drv.filter));
          renderDrivers();
        });
      });
    }

    const rows = devs.filter((d) => driverMatches(d, S.drv.q, S.drv.filter));
    const body = $('#drvBody');
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="7" class="empty">${data.loading ? T('正在读取驱动信息…') : T('没有匹配的设备')}</td></tr>`;
      return;
    }
    body.innerHTML = rows.map((d) => {
      const opened = S.drv.open.has(d.id);
      const tr = `
        <tr class="drv-row ${d.code ? 'has-err' : ''}" data-id="${escapeHtml(d.id)}">
          <td><span class="drv-icon"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg></span></td>
          <td><div class="drv-name">${escapeHtml(DEVM(d))}</div>${d.code ? `<div class="hint" style="color:#fca5a5">${escapeHtml(MSG(d))}</div>` : ''}</td>
          <td>${escapeHtml(CLS(d) || '—')}</td>
          <td>${escapeHtml((((I18N.lang || '').indexOf('zh') === 0 ? d.mfr : (d.mfr_en || d.mfr)) || '') || '—')}</td>
          <td class="mono ver-cell"><b>${escapeHtml(d.ver || '—')}</b><span class="dim">${escapeHtml(d.date || '—')}</span></td>
          <td>${d.signer ? `<span class="pill ok">${escapeHtml(shortSigner(d.signer))}</span>` : `<span class="pill warn">${T('未签名')}</span>`}</td>
          <td><div class="drv-ops"><button class="mini-btn" data-copy="${escapeHtml(d.id)}">${T('复制ID')}</button></div></td>
        </tr>`;
      const detail = opened ? `
        <tr class="drv-detail-row"><td colspan="7">
          <div class="drv-detail">
            <div class="d">${T('硬件 ID')}<b>${escapeHtml(d.id)}</b></div>
            <div class="d">${T('驱动 INF')}<b>${escapeHtml(d.inf || '—')}</b></div>
            <div class="d">${T('服务名')}<b>${escapeHtml(d.svc || '—')}</b></div>
            <div class="d">${T('签名者')}<b>${escapeHtml(d.signer || T('未签名'))}</b></div>
            <div class="d">${T('状态')}<b>${escapeHtml(MSG(d))}</b></div>
            <div class="d">${T('版本')}<b>${escapeHtml(d.ver || '—')} / ${escapeHtml(d.date || '—')}</b></div>
          </div>
        </td></tr>` : '';
      return tr + detail;
    }).join('');

    $$('#drvBody .drv-row').forEach((tr) => {
      tr.addEventListener('click', (ev) => {
        if (ev.target.closest('[data-copy]')) return;
        const id = tr.dataset.id;
        if (S.drv.open.has(id)) S.drv.open.delete(id); else S.drv.open.add(id);
        renderDrivers();
      });
    });
    $$('#drvBody [data-copy]').forEach((b) => {
      b.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        await copyText(b.dataset.copy);
      });
    });

    // 驱动包表
    $('#pkgHint').textContent = `${pkgs.length} ${T('个 INF 驱动包')}`;
    $('#pkgBody').innerHTML = pkgs.slice(0, 200).map((p) => `
      <tr>
        <td class="mono">${escapeHtml(p.inf)}</td>
        <td>${escapeHtml(((I18N.lang || '').indexOf('zh') === 0 ? p.mfr : (p.mfr_en || p.mfr)) || '—')}</td>
        <td class="mono">${escapeHtml(p.ver || '—')}</td>
        <td class="mono">${escapeHtml(p.date || '—')}</td>
        <td class="num">${p.count}</td>
        <td class="hint">${escapeHtml((((I18N.lang || '').indexOf('zh') === 0 ? p.devices : (p.devices_en || p.devices)) || []).join(SEP()))}${p.count > p.devices.length ? ' …' : ''}</td>
      </tr>`).join('') || `<tr><td colspan="6" class="empty">—</td></tr>`;
  }

  // ------------------------------------------------------------ 设置页
  function renderSettings() {
    $('#setCloseToTray').checked = !!S.settings.close_to_tray;
    $('#setAutostart').checked = !!S.settings.autostart;
    const autoEl = $('#setAutostartHint');
    if (autoEl) {
      const live = !!S.boot && S.boot.autostart_actual;
      autoEl.innerHTML = live
        ? T('当前启动项已生效，登录 Windows 后会自动启动。') + ' <code>HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run</code>'
        : T('开启后写入') + ' <code>HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run</code>' + T('，登录 Windows 后自动启动。');
    }
  }

  function fillLanguageSelect(current) {
    const sel = $('#setLanguage');
    if (!sel) return;
    sel.innerHTML = I18N.LANGS.map((l) => `<option value="${l.code}">${l.native}</option>`).join('');
    sel.value = I18N.normalize(current || I18N.lang);
  }

  window.onLanguageChanged = function () {
    fillLanguageSelect(I18N.lang);
    if (S.page) setPage(S.page);
    if (S.admin !== undefined) {
      $('#sideMode').textContent = S.admin ? T('管理员模式 · 全部传感器') : T('受限模式 · 部分传感器');
    }
    renderActive(true);
  };

  function renderAbout() {
    const b = S.boot || {};
    $('#aboutVer').textContent = 'v' + (b.version || '1.1.0');
    const env = [b.os, b.host && `${T('主机')} ${b.host}`, b.admin ? T('管理员权限') : T('受限模式')].filter(Boolean).join(' · ');
    $('#aboutEnv').textContent = env || '—';
  }

  // Windows 默认网络连接名（中文系统）在非中文界面换成英文
  const NIC_CN_EN = [
    [/^蓝牙网络连接/, 'Bluetooth Network Connection'],
    [/^无线网络连接/, 'Wireless Network Connection'],
    [/^网络连接/, 'Network connection'],
    [/^本地连接/, 'Local Area Connection'],
    [/^以太网/, 'Ethernet'],
    [/^虚拟网卡/, 'Virtual adapter'],
  ];

  function NICNAME(name) {
    const s = String(name || '').trim();
    if ((I18N.lang || '').indexOf('zh') === 0) return s;
    for (const [re, en] of NIC_CN_EN) if (re.test(s)) return s.replace(re, en);
    return s;
  }

  function shortNic(name, kind) {
    let n = String(name || '').trim();
    const words = { bt: ['蓝牙', 'Bluetooth'], wifi: ['无线', 'Wi-Fi', 'WLAN'], virtual: ['虚拟'] }[kind] || [];
    for (const w of words) {
      if (n.toLowerCase().startsWith(w.toLowerCase()) && n.length > w.length + 1) {
        n = n.slice(w.length).trim();
      }
    }
    return n || String(name || '');
  }

  function shortSigner(s) {
    if (!s) return '';
    if (s.includes('Microsoft')) return 'Microsoft';
    const parts = s.split(',');
    return parts[0].replace('CN=', '').slice(0, 22);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('已复制到剪贴板', 'ok');
      return;
    } catch (e) { }
    try {
      const r = await call('copy_text', text);
      toast(r.ok ? '已复制到剪贴板' : '复制失败', r.ok ? 'ok' : 'err');
    } catch (e) {
      toast('复制失败', 'err');
    }
  }

  // ------------------------------------------------------------ 页面切换
  const PAGE_META = {
    overview: ['系统概览', '实时掌握温度、功耗、网络与驱动状态'],
    network: ['网络管理', '所有网卡的上下行速率、累计流量与链路状态'],
    thermal: ['温度检测', '全部温度传感器统一曲线记录，可自定义记录时长'],
    power: ['功耗监控', 'CPU / GPU 功耗与累计能耗实时曲线'],
    drivers: ['驱动管理', '全部设备驱动、异常诊断、驱动包与备份'],
    settings: ['设置', '界面语言、窗口行为、开机自启与文件位置'],
    about: ['关于', '版本信息、作者、开源许可与服务条款'],
  };

  function pageMeta(page) {
    const meta = PAGE_META[page] || ['', ''];
    return [T(meta[0]), T(meta[1])];
  }

  function setPage(page) {
    S.page = page;
    $$('.nav-item').forEach((n) => n.classList.toggle('active', n.dataset.page === page));
    $$('.page').forEach((p) => p.classList.toggle('active', p.id === `page-${page}`));
    const meta = pageMeta(page);
    $('#pageTitle').textContent = meta[0];
    $('#pageSub').textContent = meta[1];
    if (page === 'about') renderAbout();
    setTimeout(() => { resizeCharts(); renderActive(true); }, 30);
  }

  function renderActive(force) {
    if (!S.lastSnap) return;
    if (S.page === 'overview') renderOverview();
    else if (S.page === 'network') renderNetwork();
    else if (S.page === 'thermal') renderThermalPage();
    else if (S.page === 'power') renderPowerPage();
    else if (S.page === 'drivers') renderDrivers();
    else if (S.page === 'settings') renderSettings();
  }

  // ------------------------------------------------------------ 顶部/侧栏
  function updateChrome(st) {
    const snap = st.snap || {};
    $('#uptime').textContent = fmtUptime(snap.uptime || 0);
    const stateEl = $('#sensorState');
    if (snap.error) { stateEl.textContent = T('采集中断'); stateEl.className = 'state-wait'; }
    else if (!snap.ready) { stateEl.textContent = T('初始化…'); stateEl.className = 'state-wait'; }
    else { stateEl.textContent = `${(snap.temps || []).length} ${T('个温度点')}`; stateEl.className = 'state-ok'; }

    $('#liveText').textContent = S.paused ? T('已暂停记录') : T('实时采集中');
    $('.live .dot').classList.toggle('stale', S.paused);

    const net = S.lastNet || {};
    const badge = $('#navNetBadge');
    if (badge) badge.classList.toggle('hidden', (net.up || 0) + (net.down || 0) < 1024);

    // 权限与 PawnIO 提示
    const elev = $('#elevBanner');
    elev.classList.toggle('hidden', S.admin);
    const pawn = $('#pawnioBanner');
    const needPawn = S.admin && !S.pawnioDismissed && snap.ready && (snap.summary && snap.summary.cpu_temp == null) && S.ticks > 6;
    pawn.classList.toggle('hidden', !needPawn);
  }

  // ------------------------------------------------------------ 交互绑定
  function bindEvents() {
    $$('.nav-item').forEach((n) => n.addEventListener('click', () => setPage(n.dataset.page)));

    setInterval(() => {
      $('#clock').textContent = fmtTime(new Date());
    }, 1000);

    // ------------------------------------------------ 设置页
    $('#setLanguage').addEventListener('change', async (e) => {
      const code = e.target.value;
      const cur = await I18N.setLanguage(code);
      fillLanguageSelect(cur);
      const r = await call('set_setting', 'language', cur);
      if (r && !r.ok) toast(errText(r.error, '保存失败'), 'err');
    });

    $('#setCloseToTray').addEventListener('change', async (e) => {
      const on = e.target.checked;
      const r = await call('set_setting', 'close_to_tray', on);
      if (!r.ok) { e.target.checked = !on; toast(errText(r.error, '保存失败'), 'err'); return; }
      S.settings.close_to_tray = on;
      toast(on ? '已开启：点 × 只最小化，托盘图标可随时唤回' : '已关闭：点 × 直接退出程序', on ? 'ok' : '');
    });

    const themeBox = $('#setTheme');
    if (themeBox) {
      themeBox.addEventListener('click', async (e) => {
        const btn = e.target.closest('button[data-theme]');
        if (!btn) return;
        const mode = btn.dataset.theme;
        applyTheme(mode);
        if (S.settings) S.settings.theme = mode;
        const r = await call('set_setting', 'theme', mode);
        if (r && r.ok === false) toast(errText(r.error, '保存失败'), 'err');
      });
    }

    $('#setAutostart').addEventListener('change', async (e) => {
      const on = e.target.checked;
      const r = await call('set_setting', 'autostart', on);
      if (!r.ok) {
        e.target.checked = !on;
        toast(errText(r.error, '写入启动项失败'), 'err');
        return;
      }
      S.settings.autostart = on;
      if (S.boot) S.boot.autostart_actual = on;
      renderSettings();
      toast(on ? '已加入开机自启（当前用户启动项）' : '已取消开机自启', 'ok');
    });

    $('#btnOpenCfg').addEventListener('click', () => call('open_target', 'log'));
    $('#btnOpenCsv2').addEventListener('click', () => call('open_target', 'csv'));
    $('#btnOpenBackup2').addEventListener('click', () => call('open_target', 'backup'));
    $('#btnOpenDocs').addEventListener('click', () => call('open_target', 'program'));
    if ($('#aboutSite')) $('#aboutSite').addEventListener('click', () => call('open_site'));
    $('#btnQuit').addEventListener('click', () => {
      modal('退出程序', '退出后温度曲线记录与后台采集都会停止，确定退出吗？', [
        { label: '取消' },
        { label: '退出', primary: true, onClick: () => call('quit_app') },
      ]);
    });

    $('#btnCopyTerms').addEventListener('click', () => {
      const box = $('#termsBox');
      if (box) copyText(box.innerText.replace(/\n{3,}/g, '\n\n'));
    });

    $('#btnElevate').addEventListener('click', async () => {      const r = await call('elevate');
      if (!r.ok) toast('已取消提权，继续以受限模式运行', 'err');
    });

    $('#btnPawnio').addEventListener('click', async () => {
      const r = await call('install_pawnio');
      if (!r.ok) { toast(errText(r.error, '安装失败'), 'err'); return; }
      modal('安装 PawnIO 底层驱动', '将运行 LibreHardwareMonitor 官方附带的 PawnIO 签名驱动安装程序，用于读取 CPU 温度与封装功耗。<br><br>安装完成后请重启本程序。', [{ label: '知道了', primary: true }]);
      S.pawnioDismissed = true;
    });

    $('#btnTempPause').addEventListener('click', () => {
      S.paused = !S.paused;
      $('#btnTempPause').textContent = S.paused ? T('继续记录') : T('暂停记录');
      toast(S.paused ? '已暂停记录（曲线停止更新）' : '已恢复记录', '');
    });

    $('#btnTempExport').addEventListener('click', async () => {
      const r = await call('export_csv', S.win.temp);
      if (r.ok) {
        toast(T('已导出 N 分钟温度数据').replace('N', S.win.temp), 'ok');
        modal('导出完成', T('文件已保存到：') + `<br><b style="color:#67e8f9">${escapeHtml(r.path)}</b><br><br>` + T('是否打开所在文件夹？'), [
          { label: '关闭' },
          { label: '打开文件夹', primary: true, onClick: () => call('open_target', 'csv') },
        ]);
      } else toast(errText(r.error, '导出失败'), 'err');
    });

    $$('#tempSeg button').forEach((b) => b.addEventListener('click', () => {
      $$('#tempSeg button').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      S.win.temp = Number(b.dataset.min);
      $('#tempCustom').value = S.win.temp;
      call('set_setting', 'temp_window', S.win.temp);
      const c = ensureChart('chartTemp');
      if (c) c.setOption(tempSeriesOption(S.win.temp, { onlyMain: !$('#tempAllSeries').checked }), { notMerge: true });
    }));

    $('#tempCustom').addEventListener('change', (e) => {
      let v = Number(e.target.value);
      if (!Number.isFinite(v) || v < 1) v = 1;
      if (v > 180) v = 180;
      e.target.value = v;
      S.win.temp = v;
      $$('#tempSeg button').forEach((x) => x.classList.toggle('active', Number(x.dataset.min) === v));
      call('set_setting', 'temp_window', v);
      const c = ensureChart('chartTemp');
      if (c) c.setOption(tempSeriesOption(S.win.temp, { onlyMain: !$('#tempAllSeries').checked }), { notMerge: true });
    });

    $('#tempAllSeries').addEventListener('change', () => {
      const c = ensureChart('chartTemp');
      if (c) c.setOption(tempSeriesOption(S.win.temp, { onlyMain: !$('#tempAllSeries').checked }), { notMerge: true });
    });

    $$('#netSeg button').forEach((b) => b.addEventListener('click', () => {
      $$('#netSeg button').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      S.win.net = Number(b.dataset.min);
      call('set_setting', 'net_window', S.win.net);
      const c = ensureChart('chartNet');
      if (c) c.setOption(netSeriesOption(S.win.net, S.data.nicSel), { notMerge: true });
    }));

    $('#netNicSel').addEventListener('change', (e) => {
      S.data.nicSel = e.target.value;
      $$('#nicBody .nic-row').forEach((tr) => tr.classList.toggle('sel', tr.dataset.nic === S.data.nicSel));
      const c = ensureChart('chartNet');
      if (c) c.setOption(netSeriesOption(S.win.net, S.data.nicSel), { notMerge: true });
    });

    $$('#powSeg button').forEach((b) => b.addEventListener('click', () => {
      $$('#powSeg button').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      S.win.power = Number(b.dataset.min);
      call('set_setting', 'power_window', S.win.power);
      const c = ensureChart('chartPower');
      if (c) c.setOption(powerSeriesOption(S.win.power), { notMerge: true });
    }));

    $('#drvSearch').addEventListener('input', (e) => { S.drv.q = e.target.value.trim(); renderDrivers(); });
    $('#btnDrvRefresh').addEventListener('click', () => { toast('正在重新读取驱动信息…', ''); loadDrivers(true); });
    $('#btnDevmgmt').addEventListener('click', () => call('open_target', 'devmgmt'));
    $('#btnWinUpdate').addEventListener('click', () => call('open_target', 'windowsupdate'));
    $('#btnDrvBackup').addEventListener('click', async () => {
      if (!S.admin) { toast('备份驱动需要管理员权限', 'err'); return; }
      const r = await call('backup_drivers');
      if (!r.started) { toast('已有备份任务在进行', 'err'); return; }
      toast('已开始备份驱动到文档目录，请稍候…', '');
      pollBackup();
    });

    window.addEventListener('resize', () => { setTimeout(resizeCharts, 60); });
  }

  async function pollBackup() {
    clearTimeout(S.drv.backupTimer);
    const st = await call('backup_status');
    if (st.running) {
      S.drv.backupTimer = setTimeout(pollBackup, 1500);
      return;
    }
    if (st.error) toast(T('备份失败：') + st.error, 'err');
    else {
      toast(T('驱动备份完成，共 N 个驱动包').replace('N', st.count), 'ok');
      modal('驱动备份完成', T('已备份 N 个驱动包到：').replace('N', `<b style="color:#6ee7b7">${st.count}</b>`) + `<br><b style="color:#67e8f9">${escapeHtml(st.path)}</b>`, [
        { label: '关闭' },
        { label: '打开文件夹', primary: true, onClick: () => call('open_target_path', st.path) },
      ]);
    }
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // ------------------------------------------------------------ 主循环
  let busy = false;
  async function loop() {
    if (busy) { setTimeout(loop, 300); return; }
    busy = true;
    try {
      const st = await callTimed('state', 5000);
      ingest(st);
      S.pausedState = false;
      updateChrome(st);
      renderActive(false);
    } catch (e) {
      $('#liveText').textContent = T('连接中断，重试中…');
      $('.live .dot').classList.add('stale');
    } finally {
      busy = false;
    }
    setTimeout(loop, 1000);
  }

  // ------------------------------------------------------------ 外观主题（深色 / 浅色 / 跟随系统）
  const darkMedia = window.matchMedia('(prefers-color-scheme: dark)');
  function resolveTheme(mode) {
    if (mode === 'light' || mode === 'dark') return mode;
    return darkMedia.matches ? 'dark' : 'light';
  }
  function applyTheme(mode) {
    const m = (mode === 'light' || mode === 'dark') ? mode : 'auto';
    const actual = resolveTheme(m);
    document.documentElement.dataset.theme = actual;
    document.documentElement.style.colorScheme = actual;
    $$('#setTheme button').forEach((b) => b.classList.toggle('active', b.dataset.theme === m));
    try { localStorage.setItem('hm.theme', m); } catch (e) { }
    themeMqHook();
  }
  function themeMqHook() { /* 占位，保持调用顺序清晰 */ }
  try {
    const cachedTheme = localStorage.getItem('hm.theme');
    if (cachedTheme) applyTheme(cachedTheme);
  } catch (e) { }
  darkMedia.addEventListener('change', () => {
    const cur = (S.settings && S.settings.theme) || 'auto';
    if (cur === 'auto') applyTheme('auto');
  });

  let booted = false;
  async function boot() {
    if (booted) return;
    if (!bridgeReady) {
      $('#liveText').textContent = T('正在连接采集服务…');
      try {
        const probe = await fetch('/api/ping', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '[]',
          cache: 'no-store',
        });
        if (probe.ok) bridgeReady = true;
      } catch (e) { /* 稍后重试 */ }
      if (!bridgeReady) {
        setTimeout(boot, 300);
        return;
      }
    }
    booted = true;
    init();
  }

  async function init() {
    bindEvents();
    const pages = ['overview', 'network', 'thermal', 'power', 'drivers', 'settings', 'about'];
    const hash = (location.hash || '').replace('#', '');
    setPage(pages.includes(hash) ? hash : 'overview');
    try {
      S.boot = await callTimed('get_boot', 8000);
      S.admin = !!S.boot.admin;
      const s = S.boot.settings || {};
      S.settings = s;
      if (s.temp_window) S.win.temp = Number(s.temp_window);
      if (s.net_window) S.win.net = Number(s.net_window);
      if (s.power_window) S.win.power = Number(s.power_window);
      $('#tempCustom').value = S.win.temp;
      $$('#tempSeg button').forEach((b) => b.classList.toggle('active', Number(b.dataset.min) === S.win.temp));
      $$('#netSeg button').forEach((b) => b.classList.toggle('active', Number(b.dataset.min) === S.win.net));
      $$('#powSeg button').forEach((b) => b.classList.toggle('active', Number(b.dataset.min) === S.win.power));
      $('#sideMode').textContent = S.admin ? T('管理员模式 · 全部传感器') : T('受限模式 · 部分传感器');
      $('#elevBanner').classList.toggle('hidden', S.admin);
      $('#setCloseToTray').checked = !!s.close_to_tray;
      applyTheme(s.theme || 'auto');
      $('#setAutostart').checked = !!(S.boot.autostart_actual != null ? S.boot.autostart_actual : s.autostart);
      const wantLang = (s.language && s.language !== 'auto')
        ? s.language
        : (S.boot.system_lang || 'zh-CN');
      const cur = await I18N.setLanguage(wantLang);
      fillLanguageSelect(cur);
      renderAbout();
      toast('硬件管理大师已启动，正在读取传感器…', '');
      loadDrivers(false);
    } catch (e) {
      toast('采集服务响应较慢，正在重试…', '');
    } finally {
      loop();
    }
  }

  window.addEventListener('pywebviewready', boot);
  boot();

  // 运行诊断（供排障使用，不影响界面）
  window.__errors = [];
  window.addEventListener('error', (e) => { window.__errors.push(String(e.message)); });
  window.__diag = () => {
    const first = S.data.tempSeries.values().next().value;
    return {
      page: S.page,
      ticks: S.ticks,
      paused: S.paused,
      ready: S.ready,
      tempSeries: S.data.tempSeries.size,
      sample: first ? { l: first.l, n: first.t.length, head: first.v.slice(-3) } : null,
      netPoints: S.data.netAll.length,
      netDown: S.data.netAll.length ? S.data.netAll[S.data.netAll.length - 1].d : null,
      charts: Object.keys(S.charts),
      chartSeries: (() => { try { return S.charts.chartOvTemp ? S.charts.chartOvTemp.getOption().series.map((x) => [x.name, x.data.length]) : []; } catch (e) { return String(e); } })(),
      errors: window.__errors.slice(0, 5),
      summary: S.lastSnap ? S.lastSnap.summary : null,
    };
  };
  // 浏览器预览兜底
  setTimeout(() => { if (!bridge()) { $('#liveText').textContent = T('等待本地服务…'); } }, 1200);
})();

