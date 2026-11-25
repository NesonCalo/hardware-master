# -*- coding: utf-8 -*-
"""Apply hand-written translations onto the official English WixUI file."""
import html
import os
import re

from extra_locales import EXTRA_LOC

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.environ.get(
    "WIX_WS",
    r"C:\Users\NesonCalo\AppData\Local\DoubaoWork\User Data\Default\.doubaowork\agent_mode\workspace\.sessions\38455657733985538\agents\m_0cwelB13usa",
)
SRC = os.path.join(WS, "wix3src", "wix3-master", "src", "ext", "UIExtension", "wixlib", "WixUI_en-us.wxl")
OUT_DIR = os.path.join(HERE, "locales")


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    with open(SRC, "r", encoding="utf-8-sig") as fp:
        base = fp.read()
    os.makedirs(OUT_DIR, exist_ok=True)
    for code, items in EXTRA_LOC.items():
        missing = []
        text = base
        for sid, value in items.items():
            pattern = r'(<String Id="%s"[^>]*>)(.*?)(</String>)' % re.escape(sid)
            if not re.search(pattern, text, re.S):
                missing.append(sid)
                continue
            text = re.sub(pattern, lambda m, v=escape(value): m.group(1) + v + m.group(3),
                          text, count=1, flags=re.S)
        dst = os.path.join(OUT_DIR, "WixUI_%s.wxl" % code)
        with open(dst, "w", encoding="utf-8-sig") as fp:
            fp.write(text)
        print("%s: %d strings, %d missing -> %s" % (code, len(items), len(missing), os.path.basename(dst)))
        if missing:
            print("  missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()
