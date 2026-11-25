# -*- coding: utf-8 -*-
"""Generate WiX UI localization files for languages that WiX does not ship.

Strings are machine translated from the official en-us file via MyMemory and
cached under installer/msi/cache so the build is reproducible.
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.environ.get(
    "WIX_WS",
    r"C:\Users\NesonCalo\AppData\Local\DoubaoWork\User Data\Default\.doubaowork\agent_mode\workspace\.sessions\38455657733985538\agents\m_0cwelB13usa",
)
SRC = os.path.join(WS, "wix3src", "wix3-master", "src", "ext", "UIExtension", "wixlib", "WixUI_en-us.wxl")
OUT_DIR = os.path.join(HERE, "locales")
CACHE_DIR = os.path.join(HERE, "cache")

# Language code -> MyMemory target code (source is English).
TARGET = {"bn": "bn-BD", "fa": "fa-IR", "id": "id-ID", "ms": "ms-MY", "vi": "vi-VN"}

SKIP = re.compile(r"^(Error|MsiRMFilesInUse|FilesInUse)")

PLACEHOLDER = re.compile(r"\[[A-Za-z0-9_]+\]|%\d|%s|%d|&[A-Za-z0-9]")


def strings_of(path):
    with open(path, "r", encoding="utf-8-sig") as fp:
        text = fp.read()
    items = re.findall(r'<String Id="([^"]+)"([^>]*)>(.*?)</String>', text, re.S)
    return text, items


def unescape(s):
    return html.unescape(s)


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def translate_batch(lines, target, attempts=3):
    q = "\n".join(lines)
    url = "https://api.mymemory.translated.net/get?q=%s&langpair=en|%s" % (
        urllib.parse.quote(q, safe=""), target)
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HardwareMasterSetup/1.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            out = data.get("responseData", {}).get("translatedText") or ""
            if out:
                return unescape(out)
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(2 + i * 2)
    raise RuntimeError("translation failed: %s" % last)


def phokens(s):
    return sorted(PLACEHOLDER.findall(s))


def looks_ok(src, dst, rtl):
    if not dst or not dst.strip():
        return False
    if phokens(src) != phokens(dst):
        return False
    src_letters = sum(ch.isalpha() for ch in src)
    dst_letters = sum(ch.isalpha() for ch in dst)
    if src_letters > 3 and dst_letters < src_letters * 0.35:
        return False
    if not rtl and src.isascii() and not dst.isascii() and len(dst) > len(src) * 4:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    codes = list(TARGET) if args.all else (args.lang or list(TARGET))

    base_text, items = strings_of(SRC)
    wanted = [(sid, unescape(val)) for sid, _attrs, val in items if not SKIP.match(sid) and val.strip()]
    print("strings to translate: %d" % len(wanted))
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    for code in codes:
        if code not in TARGET:
            raise SystemExit("unsupported language: " + code)
        target = TARGET[code]
        rtl = code == "fa"
        cpath = os.path.join(CACHE_DIR, code + ".json")
        cache = {}
        if os.path.exists(cpath):
            with open(cpath, "r", encoding="utf-8") as fp:
                cache = json.load(fp)

        todo = [sid for sid, val in wanted if sid not in cache]
        print("%s: %d cached, %d to translate" % (code, len(cache), len(todo)))
        pos = 0
        while pos < len(todo):
            batch, size = [], 0
            while pos + len(batch) < len(todo):
                sid = todo[pos + len(batch)]
                val = dict(wanted)[sid]
                if batch and size + len(val) > 420:
                    break
                batch.append(sid)
                size += len(val) + 1
            lines = [dict(wanted)[sid] for sid in batch]
            try:
                out = translate_batch(lines, target)
                parts = [p.strip() for p in out.split("\n")]
                if len(parts) != len(batch):
                    raise ValueError("line mismatch %d/%d" % (len(parts), len(batch)))
                good = True
                for sid, part in zip(batch, parts):
                    if not looks_ok(dict(wanted)[sid], part, rtl):
                        good = False
                        break
                if not good:
                    raise ValueError("validation failed")
                for sid, part in zip(batch, parts):
                    cache[sid] = part
                pos += len(batch)
            except Exception as exc:  # noqa: BLE001
                # fall back to one-by-one for this batch
                print("  batch retry (%s): %s" % (code, exc))
                for sid in batch:
                    src = dict(wanted)[sid]
                    try:
                        one = translate_batch([src], target, attempts=2)
                        one = one.strip()
                        if looks_ok(src, one, rtl):
                            cache[sid] = one
                        else:
                            cache[sid] = src
                    except Exception as exc2:  # noqa: BLE001
                        print("  single failed (%s): %s" % (sid, exc2))
                        cache[sid] = src
                pos += len(batch)
            with open(cpath, "w", encoding="utf-8") as fp:
                json.dump(cache, fp, ensure_ascii=False, indent=1)
            time.sleep(0.6)

        # write the localized wxl by substituting the text of each <String>
        out_text = base_text
        for sid, val in wanted:
            new = escape(cache.get(sid, val))
            out_text = re.sub(
                r'(<String Id="%s"[^>]*>)(.*?)(</String>)' % re.escape(sid),
                lambda m, new=new: m.group(1) + new + m.group(3),
                out_text, count=1, flags=re.S)
        dst = os.path.join(OUT_DIR, "WixUI_%s.wxl" % code)
        with open(dst, "w", encoding="utf-8-sig") as fp:
            fp.write(out_text)
        fallback = [sid for sid in dict(wanted) if cache.get(sid) == dict(wanted)[sid]]
        print("%s -> %s (%d bytes, %d untranslated)" % (code, os.path.basename(dst), os.path.getsize(dst), len(fallback)))


if __name__ == "__main__":
    main()
