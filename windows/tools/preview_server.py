# -*- coding: utf-8 -*-
"""预览服务器：用源码里的新后端 + 新界面起一个本地 HTTP 服务，供逐页检查多语言。"""
import os
import sys
import threading
import time

ROOT = r"C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师"
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import main as app_main  # noqa: E402

PORT = int(os.environ.get("PREVIEW_PORT", "8123"))


def run():
    api = app_main.Api()
    app_main.ApiHandler.api_obj = api
    srv = app_main.ThreadingHTTPServer(("127.0.0.1", PORT), app_main.ApiHandler)
    srv.daemon_threads = True
    print("preview on http://127.0.0.1:%d  admin=%s" % (PORT, api.admin), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    run()
