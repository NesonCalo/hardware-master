# -*- coding: utf-8 -*-
"""Extract every Chinese string literal from app.js / index.html and diff vs locales."""
import json, os, re, sys

ROOT = r"C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师"
UI = os.path.join(ROOT, "app", "ui")
LOC = os.path.join(UI, "locales")
CJK = re.compile(r"[\u4e00-\u9fff]")

def js_strings(src):
    """Very small JS string scanner: single, double and backtick literals with escapes."""
    res = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            q = c
            i += 1
            buf = []
            while i < n:
                if src[i] == "\\":
                    buf.append(src[i:i+2]); i += 2; continue
                if src[i] == q:
                    i += 1; break
                if src[i] == "\n" and q != "`":
                    break
                buf.append(src[i]); i += 1
            s = "".join(buf)
            if CJK.search(s):
                res.append(s)
            continue
        i += 1
    return res

def html_text_nodes(src):
    out = []
    # strip comments and scripts/styles
    src2 = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    # attributes values
    for m in re.finditer(r'(?:placeholder|title|aria-label|alt)="([^"]*)"', src2):
        if CJK.search(m.group(1)):
            out.append(m.group(1))
    # text nodes
    for m in re.finditer(r">([^<>]+)<", src2):
        t = m.group(1).strip()
        if t and CJK.search(t):
            out.append(t)
    return out

def main():
    js = open(os.path.join(UI, "app.js"), encoding="utf-8").read()
    html = open(os.path.join(UI, "index.html"), encoding="utf-8").read()
    jss = js_strings(js)
    hts = html_text_nodes(html)
    # unescape common sequences
    def un(s):
        return (s.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
                 .replace("\\t", "\t").replace("\\\\", "\\"))
    keys = set(un(x) for x in jss)
    htmlkeys = set(hts)
    en = json.load(open(os.path.join(LOC, "en.json"), encoding="utf-8"))
    allk = sorted(keys | htmlkeys)
    miss = [k for k in allk if k not in en]
    print("js chinese literals=%d html text=%d unique=%d, missing in en=%d" % (len(jss), len(hts), len(allk), len(miss)))
    print("-" * 60)
    for k in miss:
        print(repr(k))
    # also which files each missing key came from
    print("\nfile attribution:")
    for k in miss:
        where = []
        if k in htmlkeys: where.append("index.html")
        if k in keys: where.append("app.js")
        print(k[:50], "->", ",".join(where))

if __name__ == "__main__":
    main()
