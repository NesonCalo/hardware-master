# -*- coding: utf-8 -*-
"""检查 UI 中所有中文文案是否都能在 en.json 里找到英文译文。"""
import json, os, re

ROOT = r"C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师"
UI = os.path.join(ROOT, "app", "ui")
LOC = os.path.join(UI, "locales")
CJK = re.compile(r"[\u4e00-\u9fff]")


def literals(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            q = c
            i += 1
            buf = []
            while i < n:
                if src[i] == "\\":
                    buf.append(src[i:i + 2]); i += 2; continue
                if src[i] == q:
                    i += 1; break
                buf.append(src[i]); i += 1
            s = "".join(buf)
            if CJK.search(s) and "${" not in s:
                out.append(s)
            continue
        i += 1
    return out


js = open(os.path.join(UI, "app.js"), encoding="utf-8").read()
html = open(os.path.join(UI, "index.html"), encoding="utf-8").read()
keys = set(literals(js))
for m in re.finditer(r'data-i18n(?:-html|-ph|-title)?="([^"]+)"', html):
    keys.add(m.group(1))
for m in re.finditer(r'(?:placeholder|title)="([^"]*)"', html):
    if CJK.search(m.group(1)):
        keys.add(m.group(1))

en = json.load(open(os.path.join(LOC, "en.json"), encoding="utf-8"))
miss = sorted(k for k in keys if k not in en)
print("keys=%d  missing=%d" % (len(keys), len(miss)))
for k in miss:
    print("MISS:", repr(k))
