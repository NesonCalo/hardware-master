# -*- coding: utf-8 -*-
"""LibreHardwareMonitor 封装：采集全部温度、风扇、功耗、负载与频率传感器。"""

import os
import sys
import threading
import time
import collections

_LOG_PATH = os.path.join(os.environ.get("APPDATA", ""), "HardwareMaster", "app.log")


def _log(msg):
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write("[%s] hwmon: %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


GROUP_LABEL = {
    "cpu": "CPU",
    "gpu": "显卡",
    "mb": "主板",
    "disk": "硬盘",
    "net": "网络",
    "bat": "电池",
    "psu": "电源",
    "ec": "控制器",
    "mem": "内存",
    "other": "其他",
}

_TEMP_ALIAS = {
    "core (tctl/tdie)": "CPU 封装 (Tctl/Tdie)",
    "cpu package": "CPU 封装",
    "package": "CPU 封装",
    "core average": "核心平均",
    "core max": "核心最高",
    "ccd1 (tdie)": "CCD1 温度",
    "ccd1 (tctl)": "CCD1 温度",
    "gpu core": "GPU 核心",
    "gpu hot spot": "GPU 热点",
    "gpu memory": "显存",
    "gpu memory junction": "显存热点",
    "gpu vrm": "GPU 供电",
    "system": "主板温度",
    "chipset": "芯片组",
    "vrm": "供电 VRM",
    "temperature": "温度",
    "temperature 2": "温度 2",
    "cpu": "主板 CPU 传感器",
}

_POWER_ALIAS = {
    "package": "CPU 封装功耗",
    "gpu package": "GPU 功耗",
    "gpu core": "GPU 核心功耗",
    "dram": "内存控制器",
    "system": "整机(主板)",
}

_LOAD_ALIAS = {
    "cpu total": "CPU 总占用",
    "cpu core max": "单核最高占用",
    "cpu core average": "核心平均占用",
    "gpu core": "GPU 占用",
    "memory": "内存占用",
    "d3d 3d": "GPU 3D 引擎",
}

_FAN_ALIAS = {
    "gpu fan": "GPU 风扇",
    "cpu fan": "CPU 风扇",
    "system fan": "机箱风扇",
}

# 英文标签：非中文界面使用，保证不出现中文（原始传感器名多为英文，按规则规范化）
_EN_TEMP = {
    "core (tctl/tdie)": "CPU Package (Tctl/Tdie)",
    "cpu package": "CPU Package",
    "package": "CPU Package",
    "core average": "Core Average",
    "core max": "Core Max",
    "ccd1 (tdie)": "CCD1 Temperature",
    "ccd1 (tctl)": "CCD1 Temperature",
    "gpu core": "GPU Core",
    "gpu hot spot": "GPU Hot Spot",
    "gpu memory": "VRAM",
    "gpu memory junction": "VRAM Hot Spot",
    "gpu vrm": "GPU VRM",
    "system": "Motherboard",
    "chipset": "Chipset",
    "vrm": "VRM",
    "temperature": "Temperature",
    "temperature 2": "Temperature 2",
    "cpu": "Motherboard CPU Sensor",
}

_EN_POWER = {
    "package": "CPU Package Power",
    "gpu package": "GPU Power",
    "gpu core": "GPU Core Power",
    "dram": "Memory Controller",
    "system": "System (Motherboard)",
}

_EN_LOAD = {
    "cpu total": "CPU Total",
    "cpu core max": "Core Max",
    "cpu core average": "Core Average",
    "gpu core": "GPU Utilization",
    "memory": "Memory Usage",
    "d3d 3d": "GPU 3D Engine",
}

_EN_FAN = {
    "gpu fan": "GPU Fan",
    "cpu fan": "CPU Fan",
    "system fan": "Case Fan",
}

_CJK = tuple(range(0x4E00, 0x9FFF + 1))


def _has_cjk(text):
    return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in text or "")


def _en_fallback(raw, zh):
    """原始传感器名多为英文，可直接作为英文标签；实在拿不到就用通用名。"""
    raw = (raw or "").strip()
    if raw and not _has_cjk(raw):
        return raw
    return "Sensor" if _has_cjk(zh) else (zh or "Sensor")

_HW_GROUP = {
    "Cpu": "cpu",
    "GpuNvidia": "gpu",
    "GpuAmd": "gpu",
    "GpuIntel": "gpu",
    "Motherboard": "mb",
    "SuperIO": "mb",
    "Storage": "disk",
    "Memory": "mem",
    "Network": "net",
    "Battery": "bat",
    "Psu": "psu",
    "Cooler": "other",
    "EmbeddedController": "ec",
}

KEEP_TYPES = ("Temperature", "Fan", "Control", "Power", "Load", "Clock")


class HardwareMonitor(object):
    def __init__(self, lib_dir, interval=1.0, history_seconds=7200):
        self.lib_dir = lib_dir
        self.interval = interval
        self.history_seconds = history_seconds
        self.lock = threading.RLock()
        self.ready = False
        self.error = None
        self.started_at = time.time()
        self.energy_wh = 0.0
        self._last_energy_ts = None

        self.snapshot = self._empty_snapshot()
        self.temp_hist = collections.OrderedDict()
        self._labels = {}
        self._computer = None
        self._thread = None
        self._stop = threading.Event()
        self._last_power_sum = 0.0
        self.peak_energy_w = 0.0
        self._engine_ready = False
        self._engine_lock = threading.Lock()

    # ------------------------------------------------------------------ 基础
    def _empty_snapshot(self):
        return {
            "ts": time.time(),
            "ready": False,
            "admin": False,
            "temps": [],
            "fans": [],
            "powers": [],
            "loads": [],
            "clocks": [],
            "hardware": [],
            "summary": {
                "cpu_temp": None,
                "gpu_temp": None,
                "cpu_load": 0.0,
                "cpu_clock": 0.0,
                "gpu_load": 0.0,
                "ram_load": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0,
                "cpu_power": None,
                "gpu_power": None,
                "hot": None,
                "sensor_count": 0,
            },
            "meta": {"cpu": "", "gpu": "", "mb": "", "ram_gb": 0.0, "disk": []},
            "energy_wh": 0.0,
            "uptime": 0,
        }

    def start(self):
        self._thread = threading.Thread(target=self._run, name="hwmon", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    # ------------------------------------------------------------------ 初始化
    def init_now(self):
        """在主线程同步完成 LHM 初始化，避免界面加载时与 .NET 初始化争用。"""
        with self._engine_lock:
            if self._engine_ready:
                return True
            t0 = time.time()
            self._init_lhm()
            self._engine_ready = True
            _log("LHM 已就绪 %.2fs" % (time.time() - t0))
            return True

    def _init_lhm(self):
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(self.lib_dir)
            except Exception:
                pass
        if self.lib_dir not in sys.path:
            sys.path.insert(0, self.lib_dir)

        import clr  # pythonnet

        dll = os.path.join(self.lib_dir, "LibreHardwareMonitorLib.dll")
        try:
            clr.AddReference(dll)
        except Exception:
            clr.AddReference("LibreHardwareMonitorLib")

        from LibreHardwareMonitor.Hardware import Computer

        c = Computer()
        c.IsCpuEnabled = True
        c.IsGpuEnabled = True
        c.IsMemoryEnabled = True
        c.IsMotherboardEnabled = True
        c.IsStorageEnabled = True
        c.IsNetworkEnabled = True
        c.IsBatteryEnabled = True
        c.IsControllerEnabled = True
        c.IsPsuEnabled = True
        c.Open()
        self._computer = c

    # ------------------------------------------------------------------ 采集循环
    def _run(self):
        if not self._engine_ready:
            t0 = time.time()
            try:
                self.init_now()
            except Exception as exc:  # pragma: no cover
                _log("LHM 初始化失败 %.1fs: %s" % (time.time() - t0, exc))
                self.error = "底层传感器库初始化失败：%s" % exc
                with self.lock:
                    self.snapshot["error"] = self.error
                return

        self.ready = True
        while not self._stop.is_set():
            t0 = time.time()
            try:
                self._poll_once()
            except Exception as exc:
                self.error = "采集异常：%s" % exc
            dt = max(0.2, self.interval - (time.time() - t0))
            self._stop.wait(dt)

    def _poll_once(self):
        now = time.time()
        temps, fans, powers, loads, clocks, hardware = [], [], [], [], [], []

        for hw in self._computer.Hardware:
            group = _HW_GROUP.get(hw.HardwareType.ToString(), "other")
            hardware.append({"g": group, "name": hw.Name})
            self._walk(hw, group, temps, fans, powers, loads, clocks)

        snap = self._build_snapshot(now, temps, fans, powers, loads, clocks, hardware)

        with self.lock:
            self.snapshot = snap
            self._record_history(now, temps)

    def _walk(self, hw, group, temps, fans, powers, loads, clocks, depth=0):
        try:
            hw.Update()
        except Exception:
            return
        name = hw.Name or ""
        for s in hw.Sensors:
            st = s.SensorType.ToString()
            if st not in KEEP_TYPES:
                continue
            try:
                val = s.Value
                if val is None:
                    continue
                value = float(val)
            except Exception:
                continue

            key = "%s|%s" % (hw.Identifier.ToString(), s.Identifier.ToString())
            label, label_en = self._label(hw, group, name, s.Name or "", st, len(temps))
            item = {"k": key, "g": group, "l": label, "le": label_en, "v": round(value, 2), "raw": s.Name or ""}

            if st == "Temperature":
                if value <= 0.0 or value > 130.0:
                    continue
                temps.append(item)
            elif st == "Fan":
                if value < 0:
                    continue
                item["p"] = None
                fans.append(item)
            elif st == "Power":
                powers.append(item)
            elif st == "Load":
                item["v"] = round(value, 1)
                loads.append(item)
            elif st == "Clock":
                clocks.append(item)

        for sub in hw.SubHardware:
            self._walk(sub, group, temps, fans, powers, loads, clocks, depth + 1)

    def _label(self, hw, group, hw_name, sname, stype, idx):
        """返回 (中文标签, 英文标签)。英文标签用于非中文界面，避免出现中文传感器名。"""
        key = "%s|%s|%s" % (hw.Identifier.ToString(), sname, stype)
        if key in self._labels:
            return self._labels[key]

        low = sname.strip().lower()
        label = sname
        label_en = _en_fallback(sname, sname)

        if stype == "Temperature":
            label = _TEMP_ALIAS.get(low, sname)
            label_en = _EN_TEMP.get(low, _en_fallback(sname, label))
            if group == "disk":
                model = hw_name.replace(" ", "")[:16]
                label = "%s %s" % (model, label)
                label_en = "%s %s" % (hw_name[:24], label_en)
        elif stype == "Power":
            label = _POWER_ALIAS.get(low, sname)
            label_en = _EN_POWER.get(low, _en_fallback(sname, label))
            if group == "cpu" and low.startswith("core") and "(smu)" in low:
                parts = sname.split()
                core = parts[1] if len(parts) > 1 else sname
                label = "核心 %s" % core
                label_en = "Core %s" % core
        elif stype == "Load":
            label = _LOAD_ALIAS.get(low, sname)
            label_en = _EN_LOAD.get(low, _en_fallback(sname, label))
        elif stype == "Clock":
            if group == "cpu":
                label = "CPU 平均频率" if "average" in low else sname
                label_en = "CPU Average Clock" if "average" in low else _en_fallback(sname, label)
            elif group == "gpu":
                label = {"gpu core": "GPU 核心频率", "gpu memory": "显存频率"}.get(low, sname)
                label_en = {"gpu core": "GPU Core Clock", "gpu memory": "VRAM Clock"}.get(
                    low, _en_fallback(sname, label))
        elif stype == "Fan":
            label = _FAN_ALIAS.get(low, sname)
            label_en = _EN_FAN.get(low, _en_fallback(sname, label))
            if group == "gpu" and low == "gpu fan":
                label, label_en = "GPU 风扇", "GPU Fan"
            elif group == "mb" and low in ("fan", "fan #1"):
                label, label_en = "机箱风扇", "Case Fan"

        base = label
        base_en = label_en
        n = 2
        while label in self._labels.values() or (label, label_en) in self._labels.values():
            label = "%s (%d)" % (base, n)
            label_en = "%s (%d)" % (base_en, n)
            n += 1

        self._labels[key] = (label, label_en)
        return label, label_en

    # ------------------------------------------------------------------ 组装
    def _build_snapshot(self, now, temps, fans, powers, loads, clocks, hardware):
        cpu_load = _pick(loads, "cpu", ("cpu total",), ("CPU 总占用",), "max")
        gpu_load = _pick(loads, "gpu", ("gpu core", "d3d 3d"), ("GPU 占用",), "max")
        ram_load = _pick(loads, "mem", ("memory",), ("内存占用",), "max")

        cpu_temp = _pick_temp(temps, "cpu", ("tctl", "tdie", "cpu 封装", "package", "core max", "core average"))
        gpu_temp = _pick_temp(temps, "gpu", ("gpu 核心", "gpu core", "gpu hot spot"))
        cpu_power = _pick(powers, "cpu", ("package", "cpu 封装"), ("CPU 封装功耗",), "max")
        gpu_power = _pick(powers, "gpu", ("gpu package", "gpu 功耗", "gpu core"), ("GPU 功耗",), "max")

        # CPU 频率取平均
        clock_val = 0.0
        for c in clocks:
            if c["g"] == "cpu" and ("平均" in c["l"] or "average" in c["l"].lower()):
                clock_val = c["v"]
                break
        if not clock_val:
            cpu_clocks = [c["v"] for c in clocks if c["g"] == "cpu" and c["v"] > 0]
            clock_val = round(sum(cpu_clocks) / len(cpu_clocks), 1) if cpu_clocks else 0.0

        ram_used, ram_total = 0.0, 0.0
        for h in hardware:
            if h["g"] == "mem" and "Total Memory" in h["name"]:
                break

        # 内存由 psutil 兜底
        try:
            import psutil
            vm = psutil.virtual_memory()
            ram_used = round(vm.used / (1024 ** 3), 1)
            ram_total = round(vm.total / (1024 ** 3), 1)
            if not ram_load:
                ram_load = vm.percent
        except Exception:
            pass

        hot = None
        if temps:
            top = max(temps, key=lambda x: x["v"])
            hot = {"l": top["l"], "le": top.get("le") or top["l"], "v": top["v"], "g": top["g"]}

        # 风扇百分比（若有控制传感器）
        ctrl = {}
        for f in fans:
            pass

        # 能耗累计（CPU + GPU 功耗积分）
        total_w = (cpu_power or 0.0) + (gpu_power or 0.0)
        if self._last_energy_ts is not None:
            dt = max(0.0, now - self._last_energy_ts)
            if total_w > 0:
                self.energy_wh += total_w * dt / 3600.0
        self._last_energy_ts = now
        self.peak_energy_w = max(self.peak_energy_w, total_w)

        meta = self._meta_info(hardware)

        return {
            "ts": now,
            "ready": True,
            "error": self.error,
            "temps": temps,
            "fans": fans,
            "powers": powers,
            "loads": loads,
            "clocks": clocks,
            "hardware": hardware,
            "summary": {
                "cpu_temp": cpu_temp,
                "gpu_temp": gpu_temp,
                "cpu_load": round(cpu_load, 1),
                "cpu_clock": clock_val,
                "gpu_load": round(gpu_load, 1),
                "ram_load": round(ram_load, 1),
                "ram_used_gb": ram_used,
                "ram_total_gb": ram_total,
                "cpu_power": None if cpu_power is None or cpu_power <= 0 else cpu_power,
                "gpu_power": None if gpu_power is None or gpu_power <= 0 else gpu_power,
                "hot": hot,
                "sensor_count": len(temps) + len(fans) + len(powers),
            },
            "meta": meta,
            "energy_wh": round(self.energy_wh, 2),
            "uptime": int(now - self.started_at),
        }

    def _meta_info(self, hardware):
        cpu = gpu = mb = ""
        disks = []
        for h in hardware:
            if h["g"] == "cpu" and not cpu:
                cpu = h["name"]
            elif h["g"] == "gpu" and not gpu:
                gpu = h["name"]
            elif h["g"] == "mb" and not mb:
                mb = h["name"]
            elif h["g"] == "disk":
                disks.append(h["name"])
        return {"cpu": cpu, "gpu": gpu, "mb": mb, "disk": disks}

    def _record_history(self, now, temps):
        for t in temps:
            dq = self.temp_hist.get(t["k"])
            if dq is None:
                dq = collections.deque(maxlen=self.history_seconds)
                self.temp_hist[t["k"]] = dq
            dq.append((now, t["v"], t["l"], t["g"]))

    # ------------------------------------------------------------------ 对外
    def get_snapshot(self):
        with self.lock:
            snap = dict(self.snapshot)
            snap["admin"] = is_admin()
            return snap

    def export_csv(self, minutes, path, header="时间"):
        cutoff = time.time() - minutes * 60
        keys = []
        with self.lock:
            for k, dq in self.temp_hist.items():
                if dq and dq[-1][0] >= cutoff:
                    keys.append(k)
            series = {k: [(t, v)] for k, (t, v) in
                      ((k, (self.temp_hist[k][-1][0], 0)) for k in keys)}

        # 重新采样对齐
        rows = []
        with self.lock:
            for k in keys:
                dq = list(self.temp_hist[k])
                label = dq[-1][2] if dq else k
                rows.append((label, [(t, v) for (t, v, _l, _g) in dq if t >= cutoff]))

        stamps = sorted({t for _, pts in rows for t, _ in pts})
        stamp_index = {t: i for i, t in enumerate(stamps)}
        table = {}
        for label, pts in rows:
            col = [None] * len(stamps)
            for t, v in pts:
                col[stamp_index[t]] = v
            table[label] = col

        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            fh.write(header + "," + ",".join(table.keys()) + "\n")
            for i, t in enumerate(stamps):
                line = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))]
                for label in table:
                    v = table[label][i]
                    line.append("" if v is None else "%.1f" % v)
                fh.write(",".join(line) + "\n")
        return path


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _pick(items, group, raw_names, label_names, mode="first"):
    for it in items:
        if it["g"] != group:
            continue
        low = (it.get("raw") or "").lower()
        if low in raw_names or it["l"] in label_names:
            return it["v"]
    vals = [it["v"] for it in items if it["g"] == group]
    if not vals:
        return 0.0
    return max(vals) if mode == "max" else vals[0]


def _pick_temp(temps, group, keys):
    for t in temps:
        if t["g"] != group:
            continue
        low = (t.get("raw") or "").lower()
        label = t["l"]
        for k in keys:
            if k in low or k in label.lower():
                return t["v"]
    return None
