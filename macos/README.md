# 硬件管理大师 · macOS 版 1.1.0

原生 SwiftUI 的 Apple Silicon 硬件监控工具。全部指标在本机采集，无遥测、无广告、无网络请求。

## 功能

- 概览：CPU / 内存 / GPU 三环，网络、磁盘、温度与功耗速览，综合负载曲线，系统信息
- 处理器：总占用曲线、负载均值、逐核柱状图（P 核 / E 核区分）、进程与线程
- 内存：已用 / 应用 / 联动 / 压缩 / 文件缓存、交换空间、内存压力、占用趋势
- 温度与功耗（需可选助手）：CPU / GPU 温度、整机与 CPU/GPU 功耗、风扇转速、逐传感器明细、温度与功耗曲线
- 网络：各接口实时上下行、累计流量、吞吐曲线
- 磁盘：读写吞吐、累计读写、卷容量
- 设置：采样间隔、暂停、界面语言（25 种）、助手状态与卸载、数据来源说明
- 关于：版本、机型、隐私说明

## 25 种界面语言

English / 简体中文 / 繁體中文（台灣）/ 繁體中文（香港）/ 日本語 / 한국어 / Deutsch / Français /
Español / Italiano / Português (Brasil) / Русский / Українська / Polski / Nederlands / Svenska /
Türkçe / العربية / فارسی / हिन्दी / বাংলা / ไทย / Tiếng Việt / Bahasa Indonesia / Bahasa Melayu

文案 key 采用中文原文，`Resources/locales/<code>.json` 为从 Windows 版继承的 332 条词条；
macOS 新增词条在 `Resources/locales/macos-extra.json` 中按语言分节。查找顺序：当前语言 → 英文 → 中文原文。
macOS 新增词条目前提供 12 种语言（en、zh-TW、zh-HK、ja、ko、de、fr、es、it、pt-BR、ru），
其余语言对新增词条回落英文；zh-CN 直接使用中文原文。

## 温度 / 功耗 / 风扇助手

macOS 不允许普通应用读取 SoC 传感器。`Sources/Helper/` 是一个约 78 KB 的 Objective-C 助手：

- `smc.c`：IOKit AppleSMC 读取 `Tp*/Te*/Tg*/Tm*` 温度与 `F0Ac` 风扇转速（flt / sp78 / fpe2 / ui16 等类型解码）
- `helper.m`：每秒写一次 JSON，后台持续跑 `powermetrics --samplers cpu_power,gpu_power,ane_power,thermal`
- 输出 `/var/run/hardwaremaster/metrics.json`（0644），日志 `/var/log/hardwaremaster-helper.log`
- 安装位置 `/Library/PrivilegedHelperTools/com.nesoncalo.hardwaremaster.helper` + `/Library/LaunchDaemons/com.nesoncalo.hardwaremaster.helper.plist`

App 内点「启用传感器助手」会通过 `osascript ... with administrator privileges` 弹出一次系统密码框完成安装；
「卸载」会 bootout 服务并删除上述文件。助手不联网、不上传任何数据。

## 构建

```bash
cd HardwareMaster-macOS
swiftc -parse-as-library -O -target arm64-apple-macosx14.0 \
  Sources/App.swift Sources/Theme.swift Sources/Metrics.swift Sources/Model.swift \
  Sources/Views.swift Sources/HelperInstall.swift Sources/Localization.swift \
  -o build/HardwareMaster

cd Sources/Helper
clang -fobjc-arc -O2 -framework Foundation -framework IOKit smc.c helper.m \
  -o ../../build/hardwaremaster-helper
```

App 包需要把 `Resources/locales/*.json`、`Resources/helper.plist`、`build/hardwaremaster-helper`、
`build/AppIcon.icns` 放进 `Contents/Resources/`，再 `codesign --force --deep -s -`。

离屏预览（无需真机窗口）：

```bash
swiftc -DSNAPSHOT -O -target arm64-apple-macosx14.0 Sources/*.swift -o build/snapshot
HM_LANG=en ./build/snapshot   # 输出 /tmp/snap_<页名>.png
```

调试可用 `HM_METRICS_PATH` 指向伪造的 metrics JSON；`HM_LANG` 强制界面语言；助手支持 `HM_RUN_DIR`、`HM_LOG_PATH`。

## 系统要求

Apple Silicon Mac（arm64），macOS 14+。本版为本地 ad-hoc 签名，未做 Apple 公证，首次打开需右键 → 打开。
