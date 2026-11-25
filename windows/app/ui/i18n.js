/* 多语言支持：以中文原文为 key，缺译时自动回退中文 */
(function () {
  const LANGS = [
    { code: 'zh-CN', name: '简体中文', native: '简体中文' },
    { code: 'zh-TW', name: '繁體中文（台灣）', native: '繁體中文（台灣）' },
    { code: 'zh-HK', name: '繁體中文（香港）', native: '繁體中文（香港）' },
    { code: 'en', name: 'English', native: 'English' },
    { code: 'ja', name: '日本語', native: '日本語' },
    { code: 'ko', name: '한국어', native: '한국어' },
    { code: 'es', name: 'Español', native: 'Español' },
    { code: 'fr', name: 'Français', native: 'Français' },
    { code: 'de', name: 'Deutsch', native: 'Deutsch' },
    { code: 'it', name: 'Italiano', native: 'Italiano' },
    { code: 'pt-BR', name: 'Português (Brasil)', native: 'Português (Brasil)' },
    { code: 'ru', name: 'Русский', native: 'Русский' },
    { code: 'ar', name: 'العربية', native: 'العربية' },
    { code: 'hi', name: 'हिन्दी', native: 'हिन्दी' },
    { code: 'bn', name: 'বাংলা', native: 'বাংলা' },
    { code: 'vi', name: 'Tiếng Việt', native: 'Tiếng Việt' },
    { code: 'th', name: 'ไทย', native: 'ไทย' },
    { code: 'id', name: 'Bahasa Indonesia', native: 'Bahasa Indonesia' },
    { code: 'tr', name: 'Türkçe', native: 'Türkçe' },
    { code: 'nl', name: 'Nederlands', native: 'Nederlands' },
    { code: 'pl', name: 'Polski', native: 'Polski' },
    { code: 'uk', name: 'Українська', native: 'Українська' },
    { code: 'fa', name: 'فارسی', native: 'فارسی' },
    { code: 'ms', name: 'Bahasa Melayu', native: 'Bahasa Melayu' },
    { code: 'sv', name: 'Svenska', native: 'Svenska' },
  ];

  const RTL = { ar: 1, fa: 1 };
  const state = { lang: 'zh-CN', dict: null, enDict: null, cache: {} };

  function normalize(code) {
    if (!code) return 'zh-CN';
    const c = String(code).trim();
    const lower = c.toLowerCase().replace('_', '-');
    if (lower === 'zh' || lower === 'zh-cn' || lower === 'zh-hans' || lower === 'zh-sg') return 'zh-CN';
    if (lower === 'zh-tw' || lower === 'zh-hant') return 'zh-TW';
    if (lower === 'zh-hk' || lower === 'zh-mo') return 'zh-HK';
    if (lower === 'pt' || lower === 'pt-br' || lower === 'pt-pt') return 'pt-BR';
    const hit = LANGS.find((l) => l.code.toLowerCase() === lower);
    if (hit) return hit.code;
    const base = lower.split('-')[0];
    const baseHit = LANGS.find((l) => l.code.toLowerCase() === base);
    return baseHit ? baseHit.code : 'en';
  }

  function T(text) {
    if (text == null) return '';
    const s = String(text);
    const d = state.dict;
    if (!d || state.lang === 'zh-CN') return s;
    if (Object.prototype.hasOwnProperty.call(d, s)) return d[s];
    // 本语言缺译时回退英文，绝不把中文原文暴露出现在非中文界面
    const en = state.enDict;
    if (state.lang !== 'en' && en && Object.prototype.hasOwnProperty.call(en, s)) return en[s];
    return s;
  }

  async function loadDict(code) {
    if (state.cache[code]) return state.cache[code];
    if (code === 'zh-CN') return {};
    try {
      const resp = await fetch('locales/' + code + '.json', { cache: 'no-store' });
      if (!resp.ok) return {};
      const json = await resp.json();
      state.cache[code] = json;
      return json;
    } catch (e) {
      return {};
    }
  }

  function applyI18n(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      const val = T(key);
      if (el.tagName === 'OPTION') el.textContent = val;
      else el.textContent = val;
    });
    scope.querySelectorAll('[data-i18n-html]').forEach((el) => {
      el.innerHTML = T(el.getAttribute('data-i18n-html'));
    });
    scope.querySelectorAll('[data-i18n-ph]').forEach((el) => {
      el.setAttribute('placeholder', T(el.getAttribute('data-i18n-ph')));
    });
    scope.querySelectorAll('[data-i18n-title]').forEach((el) => {
      el.setAttribute('title', T(el.getAttribute('data-i18n-title')));
    });
  }

  async function setLanguage(code, opts) {
    const target = normalize(code);
    state.lang = target;
    const dict = await loadDict(target);
    if (target !== 'en') {
      state.enDict = await loadDict('en');
    } else {
      state.enDict = dict;
    }
    state.dict = dict;
    document.documentElement.lang = target;
    document.documentElement.dir = RTL[target.split('-')[0]] ? 'rtl' : 'ltr';
    document.body.classList.toggle('rtl', !!RTL[target.split('-')[0]]);
    document.body.classList.toggle('zh-ui', target.indexOf('zh') === 0);
    document.title = T('硬件管理大师');
    applyI18n(document);
    if (window.onLanguageChanged && !(opts && opts.silent)) window.onLanguageChanged(target);
    return target;
  }

  window.I18N = {
    LANGS,
    normalize,
    setLanguage,
    applyI18n,
    get lang() { return state.lang; },
    t: T,
  };
  window.T = T;
})();
