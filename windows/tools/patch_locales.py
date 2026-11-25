# -*- coding: utf-8 -*-
"""补齐新增 UI 文案（标题、驱动搜索占位符）到各语言词典。"""
import json, os

LOC = r"C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师\app\ui\locales"

NEW = {
    "en": {
        "硬件管理大师": "Hardware Master",
        "搜索设备名称 / 厂商 / INF / 硬件 ID": "Search device name / vendor / INF / hardware ID",
    },
    "zh-CN": {
        "硬件管理大师": "硬件管理大师",
        "搜索设备名称 / 厂商 / INF / 硬件 ID": "搜索设备名称 / 厂商 / INF / 硬件 ID",
    },
    "zh-TW": {
        "硬件管理大师": "硬體管理大師",
        "搜索设备名称 / 厂商 / INF / 硬件 ID": "搜尋裝置名稱 / 廠商 / INF / 硬體 ID",
    },
    "zh-HK": {
        "硬件管理大师": "硬體管理大師",
        "搜索设备名称 / 厂商 / INF / 硬件 ID": "搜尋裝置名稱 / 廠商 / INF / 硬體 ID",
    },
}

for code in ("en", "zh-CN", "zh-TW", "zh-HK"):
    path = os.path.join(LOC, code + ".json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for k, v in NEW[code].items():
        data[k] = v
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(code, "keys:", len(data))
