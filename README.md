# 硬件管理大师 · Hardware Master

Windows、macOS 与 Android 三端的本地硬件监控工具：CPU、内存、GPU、网络、磁盘、温度、功耗、风扇、驱动，手机上则聚焦电池、充电与温度，全部在本机采集，无遥测、无联网上报。

- Windows：Python + PySide6，单文件 exe，可选带托盘与小组件
- macOS：原生 SwiftUI（arm64，macOS 14+），含可选的温度/功耗特权助手
- Android：原生 Java（API 26+，无第三方依赖），电池损耗、充电速度、温度与功耗助手
- 界面语言：25 种（English、简体中文、繁體中文（台灣/香港）、日本語、한국어、Deutsch、Français、Español、Italiano、Português (Brasil)、Русский、Українська、Polski、Nederlands、Svenska、Türkçe、العربية、فارسی、हिन्दी、বাংলা、ไทย、Tiếng Việt、Bahasa Indonesia、Bahasa Melayu）

官网：https://www.nesoncalo.com

## 目录

```
windows/   Windows 版源码（app/ 主程序、tools/ 采集与打包脚本、installer/ 安装程序与 MSI 构建、docs/ 截图与服务条款）
macos/     macOS 版源码（Sources/ SwiftUI 与传感器助手、Resources/ 图标·launchd 模板·25 种语言词条）
android/   Android 版源码（src/ Java 界面与采集、assets/ 25 种语言资源、tools/ 翻译脚本、build.ps1 手工构建）
```

两个平台各自的详细说明在 `windows/README.md` 与 `macos/README.md`。

## 下载安装

到 [Releases](../../releases) 下载：

### Windows / macOS · v1.1.0

| 文件 | 平台 | 说明 |
| --- | --- | --- |
| `HardwareMaster-Setup-1.1.0.exe` | Windows 10/11 x64 | 安装到 `Program Files\NesonCalo\Hardware Master`，带开始菜单与桌面快捷方式；只有安装这一步需要一次管理员授权 |
| `hardware-master-1.1.0.dmg` | Apple Silicon Mac，macOS 14+ | 拖到「应用程序」即可；本地 ad-hoc 签名，首次打开需右键 → 打开 |
| `hardware-master-1.1.0-source.zip` | 全部 | 两个平台的源码快照 |

SHA-256：

```
6c9a8d1c06c977df03ce0efd42932465483cd0051dba642d3c96ec3c922720da  HardwareMaster-Setup-1.1.0.exe
3d0234b5f6ef924fd35f5a32aabc9f3b9d877a25283a517d33ed5f117e51a788  hardware-master-1.1.0.dmg
47d53d35766eae2635825445f9b4b401db4390b3afbcd6c1c3257094ce0f600d  hardware-master-1.1.0-source.zip
```

### Android · v1.2.0

| 文件 | 平台 | 说明 |
| --- | --- | --- |
| `HardwareMaster-1.2.0.apk` | Android 8.0+ | 已签名的安装包，约 150 KB；允许“未知来源安装”后直接装 |
| `HardwareMaster-Android-1.2.0-source.zip` | 全部 | Android 源码快照（含 25 语言资源与构建脚本） |

SHA-256：

```
9DD183E6B13492D470BA2CAA705A16942C6B424A00AA2A402F2C54907F6D675A  HardwareMaster-1.2.0.apk
FC227B84DDDB7DDD6934057DCC0CE78281E265D279AF2632FF418FF3416E2A5B  HardwareMaster-Android-1.2.0-source.zip
```

## 功能概览

- **概览**：CPU / 内存 / GPU 实时读数，网络、磁盘、温度与功耗速览，综合负载曲线，硬件清单
- **处理器**：总占用曲线、逐核负载（macOS 区分 P 核 / E 核）、进程与线程
- **内存**：已用 / 应用 / 联动 / 压缩 / 文件缓存、交换空间、内存压力、占用趋势
- **温度与功耗**：CPU / GPU 温度、整机与 CPU/GPU/ANE 功耗、风扇转速、逐传感器明细、趋势曲线、CSV 导出（Windows）
- **网络**：各网卡实时上下行、会话与累计流量、峰值、吞吐曲线、链路速率 / IPv4 / MAC
- **磁盘**：读写吞吐、累计读写、卷容量
- **驱动**（Windows）：180+ 设备清单、异常设备高亮、按 INF 归并的驱动包、一键备份
- **设置**：采样间隔、暂停、外观主题（Windows）、25 种界面语言、开机自启（Windows）、辅助功能状态
- **关于**：版本、机型、开源组件与许可证、内置服务条款（25 种语言，以简体中文为准）

### Android 版

- **概览**：电量环、实时功率、预计充满时间、电池温度、循环次数、设备信息与充电建议
- **充电**：功率 / 电流 / 电压 / 温度、充电速度（%/h）、充满剩余时间、本次充入电量、峰值功率与 90 秒曲线
- **电池**：损耗百分比、健康状态、循环次数、设计容量与满充容量、数据来源与算法说明
- **温度**：电池温度、系统热状态、实时功率、90 秒温度趋势与建议
- **记录**：每次插线的电量区间、时长、充入 Wh、峰值与平均功率（最多 60 条）
- **设置**：25 种语言、设计容量手填、80% / 高温 / 慢充提醒、后台监控通知

Android 不允许普通应用限制充电、也不开放 CPU/GPU 温度，因此应用只做读数、估算与提醒，温度页用电池温度与系统热状态判断整机发热。

## 温度 / 功耗 / 风扇需要额外授权

两个平台都不允许普通进程读取底层传感器：

- **Windows**：依赖 LibreHardwareMonitor 的内核驱动，首次运行需一次管理员授权；安装版通过计划任务免去后续 UAC 弹窗。
- **macOS**：SoC 温度只能读 IOKit AppleSMC、功耗只能跑 `powermetrics`，两者都要 root。应用内点「启用传感器助手」会弹出一次系统密码框，安装一个小助手（约 78 KB）到 `/Library/PrivilegedHelperTools`，通过 launchd 常驻，每秒写一个 JSON 到 `/var/run/hardwaremaster/`；不联网、不上传数据，可随时在应用内卸载。

## 从源码构建

Windows（需 Python 3.10+ 与 Inno Setup 6 打安装包）：

```powershell
cd windows
pip install -r requirements.txt
powershell -File build.ps1
```

macOS（需 Xcode Command Line Tools）：

```bash
cd macos
swiftc -parse-as-library -O -target arm64-apple-macosx14.0 \
  Sources/App.swift Sources/Theme.swift Sources/Metrics.swift Sources/Model.swift \
  Sources/Views.swift Sources/HelperInstall.swift Sources/Localization.swift \
  -o build/HardwareMaster

cd Sources/Helper
clang -fobjc-arc -O2 -framework Foundation -framework IOKit smc.c helper.m \
  -o ../../build/hardwaremaster-helper
```

Android（需 Android SDK：`platforms/android-36`、`build-tools/36.0.0` 与 SDK 自带 JDK 17，不需要 Gradle）：

```powershell
cd android
pwsh -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

输出 `android/build/HardwareMaster-1.2.0.apk`；签名密钥首次运行自动生成到 `android/签名/`。

## 隐私

所有指标在内存中计算，写盘的只有用户自己的设置与日志；没有账号、没有云端、没有第三方统计。唯一的外部访问是用户主动点击官网链接。

## 许可

源码与安装包版权归 NesonCalo 所有。内置第三方组件的许可证清单见各平台「关于」页与 `windows/docs/服务条款.md`。
