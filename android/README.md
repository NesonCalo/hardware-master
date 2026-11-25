# 硬件管理大师 · Android 版

深色原生的电池与充电管理工具，全部读数在本机完成，无账号、无联网上报、无广告。

## 功能

- **概览**：电量环、实时功率、预计充满时间、电池温度、循环次数、设备信息与充电建议。
- **充电**：实时功率 / 电流 / 电压 / 温度、充电速度（%/h）、充满剩余时间、本次充入电量与峰值功率，附 90 秒功率曲线。
- **电池**：电池损耗百分比、健康状态、循环次数、设计容量与满充容量、数据来源，以及损耗算法说明。
- **温度**：电池温度、系统热状态、实时功率、90 秒温度趋势，并按温度/功率给出建议。
- **充电记录**：自动累计每次插线的电量区间、时长、充入 Wh、峰值与平均功率，最多保留 60 条。
- **设置**：25 种界面语言、设计容量手填、80% / 高温 / 慢充提醒、后台监控常驻通知。

## 安装

1. 传输 `HardwareMaster-1.2.0.apk` 到手机。
2. 允许“安装未知来源应用”后点击安装。
3. 首次打开按提示授予通知权限（仅后台监控与提醒需要）。
4. 若系统隐藏了标称容量，在“设置 → 电池设计容量”填入官网参数，损耗估算即可显示。

系统要求：Android 8.0（API 26）及以上。

## 多语言

简体中文、繁體中文（台灣 / 香港）、English、日本語、한국어、Deutsch、Français、Español、Português (Brasil)、Русский、Italiano、Nederlands、Polski、Svenska、Türkçe、Українська、العربية、فارسی、हिन्दी、বাংলা、ไทย、Tiếng Việt、Bahasa Indonesia、Bahasa Melayu，共 25 种；默认跟随系统，也可在设置中固定。

语言资源位于 `assets/i18n/<tag>.json`，key 为中文原文；新增文案后运行 `tools/translate.ps1` 可重新生成。

## 说明与边界

- Android 不允许普通应用直接限制充电，本应用只做读数、估算与提醒。
- CPU / GPU 温度不对普通应用开放，温度页使用电池温度与系统热状态判断整机发热。
- 循环次数自 Android 14 起由部分机型提供，读不到时显示“未知”，不代表电池异常。
- 满充容量优先读 `charge_full`，读不到时用「剩余电荷 ÷ 当前电量」反推；设计容量读不到时使用设置中的手填值。

## 从源码构建

不使用 Gradle，直接调用 Android SDK 工具链，离线可复现：

```
pwsh -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

依赖：Android SDK（`platforms/android-36`、`build-tools/36.0.0`）与 SDK 自带 JDK 17。脚本依次执行 aapt2 compile → aapt2 link → javac → d8 → 打包 dex → 规范 assets 路径 → zipalign → apksigner，签名密钥首次运行自动生成于 `签名/hardwaremaster.keystore`。

输出：`build/HardwareMaster-1.2.0.apk`。

## 目录

```
src/com/nesoncalo/hardwaremaster/   页面、采集与图表源码
res/                                strings / styles / 图标
assets/i18n/                        25 种语言资源
tools/translate.ps1                 文案提取与翻译脚本
build.ps1                           手工构建脚本
```
