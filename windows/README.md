# 硬件管理大师（可视化电脑硬件管理）

一个 Windows 桌面工具，把网络、温度、功耗、驱动四类信息和趋势曲线放在同一个玻璃拟态界面里（深色 / 浅色皮肤，默认跟随系统），自带 25 种界面语言，单文件 exe，无需安装 Python。

官网：https://www.nesoncalo.com

界面预览：`docs/preview-*.png`（概览 / 网络 / 温度 / 功耗 / 驱动 / 设置 / 关于）。

## 功能

- **网络管理**：枚举全部网卡（有线 / 无线 / 蓝牙 / 虚拟），实时上下行速率、本次会话流量、开机以来累计流量、峰值；1/5/15/60 分钟吞吐曲线，可按网卡筛选；明细表含链路速率、IPv4、MAC，点行只画该网卡的曲线。
- **温度检测**：把电脑上所有温度传感器画在同一张曲线上，录像窗口可设为 5/15/30/60/120 分钟或自定义 1–180 分钟；图例带实时温度；**每个传感器固定一种颜色，曲线、图例、实时卡片上的色点与数字同色**，多条曲线一眼对应；传感器卡片可点击隐藏/显示对应曲线；支持暂停记录、导出 CSV（UTF-8 BOM，Excel 直接打开）；统计含记录时长、数据点、最高/平均温度及来源；另有风扇转速区域。
- **功耗显示**：CPU 封装功耗、GPU 功耗、合计、累计能耗（Wh）；功耗曲线含合计虚线；统计含窗口平均、峰值与按 0.55 元/度估算的电费。
- **驱动管理**：设备清单（180+ 设备，含异常设备高亮与原因）、按类别筛选、搜索、行展开查看硬件 ID / INF / 服务名 / 签名者 / 状态；按 INF 归并的驱动包列表；一键备份全部驱动（`Export-WindowsDriver`）、打开设备管理器、跳转系统更新。
- **概览**：CPU/GPU 温度环形仪表、实时功耗、网络速率、温度与网络趋势、硬件清单。
- **设置**：界面语言（25 种，含简体/繁体中文、英语、日语等，切换后立即生效）；外观主题（跟随系统 / 深色 / 浅色，默认跟随 Windows）。“关闭窗口后最小化”：开启后点 × 会把主窗口最小化到任务栏并保留右下角托盘图标，可从托盘菜单唤回主界面或退出，后台继续采集；一键“开机自动启动”（写入当前用户 `Run` 启动项，可随时关闭）。
- **关于**：版本、作者 NesonCalo、官网 https://www.nesoncalo.com、运行环境、全部开源组件及其许可证清单（含 LGPL-3.0 的 pystray、MPL-2.0 的 LibreHardwareMonitorLib 等），以及内置服务条款（25 种语言，以简体中文为准；可一键复制，另存 `docs/服务条款.md`）。

## 安装版（推荐）

双击 `installer\输出\硬件管理大师-安装程序-1.1.0.exe`：安装到 `Program Files\NesonCalo\Hardware Master`，带许可页、开始菜单与桌面快捷方式、标准卸载项。

- **只有安装这一步需要一次管理员授权**（写入 Program Files 并登记下面的计划任务）；以后双击快捷方式直接以管理员模式打开，**不再弹 UAC 允许框**。
- 免 UAC 靠安装时登记的计划任务 `NesonCalo HardwareMaster`：无任何触发器（不会开机自启）、`RunLevel=Highest`、仅手动启动；卸载时自动删除。
- 非流氓行为：不写开机自启、不捆绑、不装服务、不联网上报；卸载删除任务与安装目录，只保留你自己的 `%APPDATA%\HardwareMaster` 设置与日志（可手动删）。
- 计划任务缺失或被删时，程序进入受限模式运行，**也不会弹 UAC**；可从“设置”里以管理员身份重启并重装。
- 安装包未做代码签名，首次运行时 SmartScreen 会提示“未知发布者”，选择“更多信息 → 仍要运行”即可。

## 运行

直接双击 `dist\HardwareMaster.exe`（便携版）。

- 首次启动会弹一次 UAC（需要管理员权限才能读取 CPU 温度、CPU 功耗、主板/硬盘传感器）。拒绝也不影响使用，界面会进入“受限模式”并显示黄色横幅和“以管理员身份重启”按钮，此时只能读到 GPU 温度/功耗等公开传感器。
- 如果 CPU 温度/功耗一直是“—”，说明缺少 LibreHardwareMonitor 0.9.6 使用的 signed 内核驱动 **PawnIO**。点横幅里的“安装驱动”，会启动随程序打包的官方安装器 `PawnIO_setup.exe`（不会静默安装），装完重启本程序即可。

## 数据与文件位置

- 设置：`%APPDATA%\HardwareMaster\settings.json`
- 日志：`%APPDATA%\HardwareMaster\app.log`
- 开机启动项：`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 下的 `HardwareMaster` 值（仅在你开启“开机自动启动”后存在）
- 温度导出：`%USERPROFILE%\Documents\硬件管理大师\温度记录\温度记录_YYYYmmdd_HHMMSS.csv`
- 驱动备份：`%USERPROFILE%\Documents\硬件管理大师\驱动备份\`

## 从源码构建

```powershell
# 依赖：Python 3.10+，Windows 11 / WebView2 运行时；安装包需 WiX 3.14
powershell -ExecutionPolicy Bypass -File build.ps1                 # 仅 exe
powershell -ExecutionPolicy Bypass -File installer\build-installer.ps1   # exe + 旧版 Inno 安装程序
python installer\msi\build_msi.py --all                            # 25 种语言的 MSI
```

产物：`dist\HardwareMaster.exe`（单文件，内嵌 UI 与 LibreHardwareMonitor 运行库）、`installer\msi\out\HardwareMaster-1.1.0-<语言>.msi`（25 个语言专用 MSI 安装包）。

安装程序源码在 `installer\msi\`：`build_msi.py`（生成 WiX 工程并调用 candle/light）、`extra_locales.py`（WiX 未内置语言的向导文案）、`setup-task.ps1` 模板（登记免 UAC 计划任务）。旧版 Inno 脚本保留在 `installer\` 作为参考。

## 实现说明

- 采集：`pythonnet` 加载 LibreHardwareMonitorLib.dll 读传感器，`psutil` 读网卡/内存，PowerShell CIM 查询枚举驱动。
- 界面：本地 HTML/CSS/JS（ECharts 5.6.0 画曲线），WebView2 承载；前端通过 `127.0.0.1` 上的轻量 HTTP 接口取数（`/api/state` 等），比 JS 桥接在打包环境下更稳。
- 多语言：`app/ui/locales/<code>.json`，以中文原文为字典 key，缺失回退中文；`app/ui/i18n.js` 负责加载、切换与 RTL（阿拉伯语/波斯语）。
- 主题：`html[data-theme]` 变量切换，默认 `auto`（读 `AppsUseLightTheme` 跟随系统），标题栏颜色同步。
- 代码结构：
  - `app/main.py` 入口、窗口、提权、本地 HTTP 接口
  - `app/core/hwmon.py` 传感器采集与历史
  - `app/core/netmon.py` 网卡流量
  - `app/core/driverinfo.py` 驱动枚举与备份
  - `app/ui/` 前端页面

