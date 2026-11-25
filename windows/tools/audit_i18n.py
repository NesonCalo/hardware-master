# -*- coding: utf-8 -*-
"""Audit UI strings: which Chinese literals are missing from locale dictionaries."""
import json
import os
import re
import sys

ROOT = r"C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师"
UI = os.path.join(ROOT, "app", "ui")
LOC = os.path.join(UI, "locales")

CJK = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")


def has_cjk(s):
    return bool(CJK.search(s))


def keys_from_html(text):
    out = []
    for attr in ("data-i18n", "data-i18n-html", "data-i18n-ph", "data-i18n-title"):
        for m in re.finditer(attr + r'="([^"]+)"', text):
            out.append(m.group(1))
    return out


def keys_from_js(text, name="app.js"):
    out = []
    # T("...") / I18N.t("...") / t("...") with single or double quotes, allow \n and template literals
    pat = re.compile(r"""(?:\bT|\bt)\s*\(\s*(?:\'([^\']*)\'|"([^"]*)"|`([^`]*)`)""")
    for m in pat.finditer(text):
        val = m.group(1) or m.group(2) or m.group(3)
        if val and has_cjk(val):
            out.append(val)
    # object literals like title: '中文' used with T? skip
    return out


def main():
    html = open(os.path.join(UI, "index.html"), encoding="utf-8").read()
    js = open(os.path.join(UI, "app.js"), encoding="utf-8").read()
    i18n_js = open(os.path.join(UI, "i18n.js"), encoding="utf-8").read()

    hk = keys_from_html(html)
    jk = keys_from_js(js)
    # any Chinese literal in html text nodes (outside i18n attributes) that could be displayed
    allkeys = sorted(set(hk + jk))
    print("html keys=%d js keys=%d unique=%d" % (len(hk), len(jk), len(allkeys)))

    en = json.load(open(os.path.join(LOC, "en.json"), encoding="utf-8"))
    print("en.json keys=%d" % len(en))
    miss_en = [k for k in allkeys if k not in en]
    print("missing in en: %d" % len(miss_en))
    for k in miss_en:
        print("   ", repr(k)[:120])

    # per-language missing counts
    print("\nper-language missing:")
    for fn in sorted(os.listdir(LOC)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        code = fn[:-5]
        d = json.load(open(os.path.join(LOC, fn), encoding="utf-8"))
        miss = [k for k in allkeys if k not in d]
        print("%-6s total=%4d missing=%4d" % (code, len(d), len(miss)))


if __name__ == "__main__":
    main()
