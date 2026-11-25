# -*- coding: utf-8 -*-
"""驱动与设备信息：枚举全部设备驱动、问题设备、驱动包，并支持备份导出。"""

import json
import os
import subprocess
import threading
import time

_NO_WINDOW = 0x08000000

CLASS_CN = {
    "NET": "网络适配器",
    "DISPLAY": "显示适配器",
    "MEDIA": "音频/视频",
    "AUDIO": "音频设备",
    "AUDIOPROCESSINGOBJECT": "音频处理对象",
    "HDC": "存储控制器",
    "SCSIADAPTER": "存储控制器",
    "VOLUME": "存储卷",
    "DISKDRIVE": "磁盘驱动器",
    "CDROM": "光盘驱动器",
    "USB": "USB 设备",
    "USBDEVICE": "USB 设备",
    "HIDCLASS": "人机接口",
    "KEYBOARD": "键盘",
    "MOUSE": "鼠标",
    "BLUETOOTH": "蓝牙",
    "PRINTER": "打印机",
    "PRINTQUEUE": "打印队列",
    "SYSTEM": "系统设备",
    "PROCESSOR": "处理器",
    "FIRMWARE": "固件",
    "SECURITYDEVICE": "安全设备",
    "SECURITYDEVICES": "安全设备",
    "SECURITYPROCESSOR": "安全处理器",
    "SMARTCARDREADER": "智能卡",
    "CAMERA": "摄像头",
    "IMAGE": "图像设备",
    "BATTERY": "电池",
    "BIOMETRIC": "生物识别",
    "COMPUTER": "计算机",
    "MONITOR": "显示器",
    "MODEM": "调制解调器",
    "PORTS": "端口",
    "SENSOR": "传感器",
    "AUDIOENDPOINT": "音频端点",
    "SOFTWAREDEVICE": "软件设备",
    "SOFTWARECOMPONENT": "软件组件",
    "SWCOMPONENT": "软件组件",
    "COMPOSITE": "复合设备",
    "LEGACY": "旧式设备",
    "MTD": "内存技术设备",
    "WCEUSBSH001": "WinCE USB",
    "WINDISPLAY": "显示组件",
    "EXTENSIONINF": "驱动扩展",
}

ERROR_CN = {
    1: "设备未正确配置",
    3: "驱动未安装或已损坏",
    10: "设备无法启动",
    12: "系统资源不足",
    14: "需要重启计算机",
    18: "请重新安装驱动",
    19: "注册表配置损坏",
    21: "系统正在移除设备",
    22: "设备已被禁用",
    24: "设备不存在/未连接",
    28: "驱动未安装",
    29: "固件未提供所需资源",
    31: "无法加载驱动",
    32: "驱动启动失败",
    33: "无法确定所需资源",
    37: "驱动初始化失败",
    39: "驱动损坏或缺失",
    43: "设备已被驱动程序停止",
    45: "设备当前未连接",
}

CLASS_EN = {
    "NET": "Network adapters",
    "DISPLAY": "Display adapters",
    "MEDIA": "Sound, video and game controllers",
    "AUDIO": "Audio devices",
    "AUDIOPROCESSINGOBJECT": "Audio processing objects",
    "HDC": "Storage controllers",
    "SCSIADAPTER": "Storage controllers",
    "VOLUME": "Storage volumes",
    "DISKDRIVE": "Disk drives",
    "CDROM": "DVD/CD-ROM drives",
    "USB": "USB devices",
    "USBDEVICE": "USB devices",
    "HIDCLASS": "Human interface devices",
    "KEYBOARD": "Keyboards",
    "MOUSE": "Mice and other pointing devices",
    "BLUETOOTH": "Bluetooth",
    "PRINTER": "Printers",
    "PRINTQUEUE": "Print queues",
    "SYSTEM": "System devices",
    "PROCESSOR": "Processors",
    "FIRMWARE": "Firmware",
    "SECURITYDEVICE": "Security devices",
    "SECURITYDEVICES": "Security devices",
    "SECURITYPROCESSOR": "Security processors",
    "SMARTCARDREADER": "Smart card readers",
    "CAMERA": "Cameras",
    "IMAGE": "Imaging devices",
    "BATTERY": "Batteries",
    "BIOMETRIC": "Biometric devices",
    "COMPUTER": "Computer",
    "MONITOR": "Monitors",
    "MODEM": "Modems",
    "PORTS": "Ports (COM & LPT)",
    "SENSOR": "Sensors",
    "AUDIOENDPOINT": "Audio endpoints",
    "SOFTWAREDEVICE": "Software devices",
    "SOFTWARECOMPONENT": "Software components",
    "SWCOMPONENT": "Software components",
    "COMPOSITE": "Composite devices",
    "LEGACY": "Legacy devices",
    "MTD": "Memory technology devices",
    "WCEUSBSH001": "WinCE USB",
    "WINDISPLAY": "Display components",
    "EXTENSIONINF": "Driver extensions",
}

ERROR_EN = {
    1: "This device is not configured correctly",
    3: "The driver is not installed or is corrupted",
    10: "This device cannot start",
    12: "Not enough system resources",
    14: "A reboot is required",
    18: "Reinstall the driver",
    19: "Registry configuration is corrupted",
    21: "Windows is removing this device",
    22: "This device is disabled",
    24: "This device is not present / not connected",
    28: "The driver is not installed",
    29: "Firmware did not provide the required resources",
    31: "The driver could not be loaded",
    32: "The driver failed to start",
    33: "Unable to determine required resources",
    37: "The driver failed to initialize",
    39: "The driver is corrupted or missing",
    43: "The device was stopped by its driver",
    45: "This device is not connected",
}

# Windows 自带的中文设备名 -> 英文等价写法（仅覆盖系统通用设备）
NAME_EN = {
    "（标准系统设备）": "(Standard system devices)",
    "(标准系统设备)": "(Standard system devices)",
    "(标准 USB 主控制器)": "(Standard USB Host Controller)",
    "(标准 USB 集线器)": "(Standard USB Hub)",
    "(标准鼠标类型)": "(Standard mouse types)",
    "(标准键盘类型)": "(Standard keyboards)",
    "(标准显示器类型)": "(Standard monitor types)",
    "(标准磁盘驱动器)": "(Standard disk drives)",
    "(标准卷)": "(Standard volumes)",
    "(标准网络适配器)": "(Standard network adapters)",
    "WSD 扫描设备": "WSD Scan Device",
    "通用串行总线控制器": "Universal Serial Bus controllers",
    "通用即插即用设备": "Generic PnP Device",
    "符合 HID 标准的用户控制设备": "HID-compliant user control device",
    "符合 HID 标准的鼠标": "HID-compliant mouse",
    "符合 HID 标准的键盘": "HID-compliant keyboard",
    "符合 HID 标准的系统控制器": "HID-compliant system controller",
    "符合 HID 标准的供应商定义的设备": "HID-compliant vendor-defined device",
    "复合设备": "Composite device",
    "Microsoft 基本显示适配器": "Microsoft Basic Display Adapter",
    "Microsoft 基本呈现驱动程序": "Microsoft Basic Render Driver",
    "Microsoft 输入设备": "Microsoft Input Device",
    "Microsoft 内核驱动程序": "Microsoft Kernel Driver",
    "系统固件": "System Firmware",
    "系统计时器": "System Timer",
    "系统扬声器": "System Speaker",
    "系统 CMOS 电池": "System CMOS Battery",
    "ACPI 固定功能按钮": "ACPI Fixed Feature Button",
    "ACPI 电源按钮": "ACPI Power Button",
    "ACPI 睡眠按钮": "ACPI Sleep Button",
    "ACPI 热区域": "ACPI Thermal Zone",
    "可编程中断控制器": "Programmable interrupt controller",
    "高精度事件计时器": "High precision event timer",
    "直接内存访问控制器": "Direct memory access controller",
    "PCI 标准主机 CPU 桥": "PCI standard host CPU bridge",
    "PCI 标准 ISA 桥": "PCI standard ISA bridge",
    "PCI 标准 PCI-to-PCI 桥": "PCI standard PCI-to-PCI bridge",
    "受信任的平台模块 2.0": "Trusted Platform Module 2.0",
    "卷影副本": "Volume Shadow Copy",
    "麦克风（高清晰度音频）": "Microphone (High Definition Audio)",
    "扬声器（高清晰度音频）": "Speakers (High Definition Audio)",
}

_PS_SCRIPT = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'SilentlyContinue'
$devs = @(Get-CimInstance Win32_PnPSignedDriver | ForEach-Object {
    [PSCustomObject]@{
        name   = [string]$_.DeviceName
        cls    = [string]$_.DeviceClass
        mfr    = [string]$_.Manufacturer
        ver    = [string]$_.DriverVersion
        date   = $(if ($_.DriverDate) { (Get-Date $_.DriverDate).ToString('yyyy-MM-dd') } else { '' })
        inf    = [string]$_.InfName
        id     = [string]$_.DeviceID
        svc    = [string]$_.Service
        signer = [string]$_.Signer
    }
})
$prob = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | ForEach-Object {
    [PSCustomObject]@{
        name  = [string]$_.Name
        code  = [int]$_.ConfigManagerErrorCode
        id    = [string]$_.DeviceID
        cls   = [string]$_.PNPClass
        status = [string]$_.Status
    }
})
$os = [PSCustomObject]@{
    caption = [string](Get-CimInstance Win32_OperatingSystem).Caption
    version = [string](Get-CimInstance Win32_OperatingSystem).Version
    build   = [string](Get-CimInstance Win32_OperatingSystem).BuildNumber
    model   = [string](Get-CimInstance Win32_ComputerSystem).Model
    vendor  = [string](Get-CimInstance Win32_ComputerSystem).Manufacturer
    host    = [string](Get-CimInstance Win32_ComputerSystem).Name
    board   = [string](Get-CimInstance Win32_BaseBoard).Product
}
[PSCustomObject]@{ devices = $devs; problems = $prob; os = $os } | ConvertTo-Json -Depth 6 -Compress
"""


def _powershell():
    root = os.environ.get("SystemRoot", r"C:\Windows")
    return os.path.join(root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")


def _run_ps(script, timeout=120):
    cp = subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-WindowStyle", "Hidden", "-Command", script],
        capture_output=True, creationflags=_NO_WINDOW, timeout=timeout,
    )
    out = cp.stdout.decode("utf-8", "replace").strip()
    if not out:
        raise RuntimeError((cp.stderr or b"").decode("utf-8", "replace").strip() or "PowerShell 无输出")
    return out


def _en_device_name(name):
    """Windows 返回的中文通用设备名给出英文写法；专有型号名保持原样。"""
    name = (name or "").strip()
    if not name:
        return name
    hit = NAME_EN.get(name)
    if hit:
        return hit
    for cn, en in NAME_EN.items():
        if cn in name:
            return name.replace(cn, en)
    return name


_EDITION_EN = (
    ("工作站", "Pro for Workstations"),
    ("企业", "Enterprise"),
    ("教育", "Education"),
    ("家庭单语言", "Home Single Language"),
    ("家庭", "Home"),
    ("专业", "Pro"),
    ("服务器", "Server"),
)


def _os_en(caption, version=""):
    """把本机语言版本的 Windows 名称换成英文规范写法。"""
    cap = (caption or "").strip()
    if not cap:
        return ""
    if not any(0x4E00 <= ord(ch) <= 0x9FFF for ch in cap):
        return cap.replace("Microsoft ", "").strip()
    ver = "Windows 11" if "11" in (version or "") else "Windows 10"
    if "Windows 10" in cap:
        ver = "Windows 10"
    elif "Windows 11" in cap:
        ver = "Windows 11"
    elif "Server" in cap:
        ver = "Windows Server"
    for cn, en in _EDITION_EN:
        if cn in cap:
            return ("%s %s" % (ver, en)) if ver != "Windows Server" else "Windows Server"
    return ver


def _as_list(obj):
    if obj is None:
        return []
    return obj if isinstance(obj, list) else [obj]


class DriverInfo(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.devices = []
        self.problems = []
        self.system = {}
        self.timestamp = 0.0
        self.loading = False
        self.error = None
        self.backup_state = {"running": False, "done": False, "count": 0, "path": "", "error": None,
                             "started": 0.0, "finished": 0.0}
        self._thread = None

    # ------------------------------------------------------------------
    def refresh_async(self):
        with self.lock:
            if self.loading:
                return False
            self.loading = True
        self._thread = threading.Thread(target=self._load, name="drivers", daemon=True)
        self._thread.start()
        return True

    def _load(self):
        try:
            raw = _run_ps(_PS_SCRIPT)
            data = json.loads(raw)
            devs = _as_list(data.get("devices"))
            probs = _as_list(data.get("problems"))
            problem_index = {}
            for p in probs:
                problem_index[(p.get("id") or "").upper()] = p

            items = []
            for d in devs:
                name = (d.get("name") or "").strip()
                if not name:
                    continue
                code = 0
                p = problem_index.get((d.get("id") or "").upper())
                if p:
                    code = int(p.get("code") or 0)
                items.append({
                    "name": name,
                    "name_en": _en_device_name(name),
                    "cls": (d.get("cls") or "").strip(),
                    "cls_cn": CLASS_CN.get((d.get("cls") or "").strip().upper(), (d.get("cls") or "其他")),
                    "cls_en": CLASS_EN.get((d.get("cls") or "").strip().upper(), (d.get("cls") or "Other")),
                    "mfr": (d.get("mfr") or "").strip(),
                    "mfr_en": _en_device_name((d.get("mfr") or "").strip()),
                    "ver": (d.get("ver") or "").strip(),
                    "date": (d.get("date") or "").strip(),
                    "inf": (d.get("inf") or "").strip(),
                    "id": (d.get("id") or "").strip(),
                    "svc": (d.get("svc") or "").strip(),
                    "signer": (d.get("signer") or "").strip(),
                    "code": code,
                    "msg": ERROR_CN.get(code, ("正常" if code == 0 else "错误码 %s" % code)),
                    "msg_en": ERROR_EN.get(code, ("OK" if code == 0 else "Error code %s" % code)),
                })
            items.sort(key=lambda x: (x["code"] == 0, x["cls_cn"], x["name"].lower()))

            with self.lock:
                self.devices = items
                self.problems = [d for d in items if d["code"]]
                self.system = data.get("os") or {}
                sysinfo = self.system
                sysinfo["caption_en"] = _os_en(sysinfo.get("caption"), sysinfo.get("version"))
                self.timestamp = time.time()
                self.error = None
        except Exception as exc:
            with self.lock:
                self.error = "驱动信息读取失败：%s" % exc
        finally:
            with self.lock:
                self.loading = False

    def get(self):
        with self.lock:
            return {
                "loading": self.loading,
                "error": self.error,
                "devices": self.devices,
                "problems": self.problems,
                "system": self.system,
                "timestamp": self.timestamp,
            }

    def packages(self):
        """按 INF 归并成驱动包视图。"""
        with self.lock:
            groups = {}
            for d in self.devices:
                inf = d["inf"].upper() or "(无 INF)"
                g = groups.get(inf)
                if g is None:
                    g = groups[inf] = {
                        "inf": inf, "mfr": d["mfr"], "mfr_en": d.get("mfr_en") or d["mfr"],
                        "ver": d["ver"], "date": d["date"],
                        "count": 0, "devices": [], "devices_en": [], "signed": bool(d["signer"]),
                    }
                g["count"] += 1
                if len(g["devices"]) < 6:
                    g["devices"].append(d["name"])
                    g["devices_en"].append(d.get("name_en") or d["name"])
                if d["date"] and d["date"] > g["date"]:
                    g["date"] = d["date"]
            return sorted(groups.values(), key=lambda x: (-x["count"], x["inf"]))

    # ------------------------------------------------------------------ 备份
    def backup_async(self, dest):
        with self.lock:
            if self.backup_state["running"]:
                return False
            self.backup_state = {"running": True, "done": False, "count": 0, "path": dest,
                                 "error": None, "started": time.time(), "finished": 0.0}
        threading.Thread(target=self._backup, args=(dest,), name="drv-backup", daemon=True).start()
        return True

    def _backup(self, dest):
        try:
            os.makedirs(dest, exist_ok=True)
            script = (
                "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8\n"
                "Export-WindowsDriver -Online -Destination '%s' | "
                "Select-Object -ExpandProperty Driver\n" % dest.replace("'", "''")
            )
            out = _run_ps(script, timeout=900)
            lines = [l.strip() for l in out.splitlines() if l.strip().startswith(("oem", "OEM"))]
            with self.lock:
                self.backup_state.update({
                    "running": False, "done": True, "count": len(lines),
                    "finished": time.time(), "error": None,
                })
        except Exception as exc:
            with self.lock:
                self.backup_state.update({
                    "running": False, "done": True, "error": str(exc),
                    "finished": time.time(),
                })

    def backup_status(self):
        with self.lock:
            return dict(self.backup_state)
