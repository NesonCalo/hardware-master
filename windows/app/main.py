# -*- coding: utf-8 -*-
"""硬件管理大师 —— 主程序入口（pywebview + 原生 Web UI）。"""

import base64
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse as urllib_parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "硬件管理大师"
APP_ID = "HardwareMaster"
VERSION = "1.1.0"
AUTHOR = "NesonCalo"
HOMEPAGE = "https://www.nesoncalo.com"
NET_COLORS = {"up": "#a78bfa", "down": "#22d3ee"}  # 与网络页上行/下行曲线同色
NET_LABELS = {"up": "上行", "down": "下行"}

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")
LIB_DIR = os.path.join(BASE_DIR, "lib")
ASSET_DIR = os.path.join(BASE_DIR, "assets")

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_ID)
SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.json")
LOG_PATH = os.path.join(APPDATA_DIR, "app.log")
PORT_PATH = os.path.join(APPDATA_DIR, "api.port")

DEFAULT_SETTINGS = {
    "temp_window": 15,
    "net_window": 5,
    "power_window": 15,
    "auto_elevate": True,
    "only_active_nics": True,
    "show_all_temp_series": True,
    "close_to_tray": True,
    "language": "auto",
    "theme": "auto",
    "autostart": False,
}

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "HardwareMaster"

# 支持的语言（与 app/ui/i18n.js 中的列表严格一致）
SUPPORTED_LANGS = (
    "zh-CN", "zh-TW", "zh-HK", "en", "ja", "ko", "es", "fr", "de", "it",
    "pt-BR", "ru", "ar", "hi", "bn", "vi", "th", "id", "tr", "nl",
    "pl", "uk", "fa", "ms", "sv",
)


def match_language(loc):
    """把 Windows 区域名（如 zh-TW、en-US）归一化成受支持的语言代码。"""
    loc = (loc or "").replace("_", "-").strip().lower()
    if not loc:
        return "zh-CN"
    if loc in ("zh", "zh-cn", "zh-hans", "zh-sg"):
        return "zh-CN"
    if loc in ("zh-tw", "zh-hant"):
        return "zh-TW"
    if loc in ("zh-hk", "zh-mo"):
        return "zh-HK"
    if loc in ("pt", "pt-br", "pt-pt"):
        return "pt-BR"
    for code in SUPPORTED_LANGS:
        if code.lower() == loc:
            return code
    base = loc.split("-")[0]
    for code in SUPPORTED_LANGS:
        if code.lower() == base:
            return code
    return "en"


def system_language():
    try:
        buf = ctypes.create_unicode_buffer(85)
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85):
            return match_language(buf.value)
    except Exception:
        pass
    return match_language(os.environ.get("LANG", ""))


LANG_TITLES = {
    "zh-CN": "硬件管理大师",
    "zh-TW": "硬體管理大師",
    "zh-HK": "硬體管理大師",
}


def ui_language():
    """当前界面语言：跟随设置，auto 时跟随系统。"""
    try:
        lang = (load_settings().get("language") or "auto")
    except Exception:
        lang = "auto"
    if lang == "auto":
        return system_language()
    return match_language(lang)


def window_title():
    return LANG_TITLES.get(ui_language(), "Hardware Master")


def tray_labels():
    if ui_language().startswith("zh"):
        return "打开主界面", "退出"
    return "Open Hardware Master", "Quit"

# 与前端 SENSOR_PALETTE 完全一致：同一传感器在曲线、卡片、悬浮温度条上同色
PALETTE = [
    "#22d3ee", "#fb923c", "#a78bfa", "#34d399", "#f472b6", "#facc15", "#60a5fa",
    "#f87171", "#c084fc", "#2dd4bf", "#fdba74", "#93c5fd", "#e879f9", "#a3e635",
    "#fb7185", "#818cf8", "#6ee7b7", "#94a3b8",
]


# ------------------------------------------------------------------ 开机自启
def startup_command():
    """写入注册表的启动命令行。"""
    if getattr(sys, "frozen", False):
        return '"%s"' % os.path.abspath(sys.executable)
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    script = os.path.abspath(sys.argv[0])
    return '"%s" "%s"' % (exe, script)


def autostart_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, RUN_NAME)
            return bool(value)
    except Exception:
        return False


def set_autostart(enabled):
    """写入 / 删除 HKCU 启动项，返回 (是否成功, 说明)。"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, startup_command())
            else:
                try:
                    winreg.DeleteValue(key, RUN_NAME)
                except FileNotFoundError:
                    pass
        return True, startup_command() if enabled else ""
    except Exception as exc:
        log("开机自启设置失败: %s" % exc)
        return False, str(exc)


# ------------------------------------------------------------------ 工具
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def log(msg):
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def load_settings():
    data = dict(DEFAULT_SETTINGS)
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            # 迁移旧键名，并丢弃已经废弃的小组件配置
            if "close_to_tray" not in raw and raw.get("close_to_widget"):
                raw["close_to_tray"] = True
            for key in ("close_to_widget", "widget_items", "widget_sensors"):
                raw.pop(key, None)
            data.update(raw)
    except Exception:
        pass
    return data


# ------------------------------------------------------------------ 工具
def save_settings(data):
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def relaunch_elevated():
    """以管理员身份重新启动自身，返回是否成功发起。"""
    try:
        if getattr(sys, "frozen", False):
            exe, params = sys.executable, ""
        else:
            exe = sys.executable
            script = os.path.abspath(sys.argv[0])
            params = '"%s"' % script
        cwd = os.path.dirname(exe) if getattr(sys, "frozen", False) else os.path.dirname(script)
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, cwd, 1)
        return rc > 32
    except Exception as exc:
        log("提权失败: %s" % exc)
        return False


# ------------------------------------------------ 安装版：计划任务提权启动
INSTALL_TASK = "NesonCalo HardwareMaster"
INSTALL_MARKER = "installed.marker"


def installed_dir():
    """安装版程序目录（单文件打包时取 exe 所在目录），非安装版返回空串。"""
    if not getattr(sys, "frozen", False):
        return ""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    return exe_dir if os.path.exists(os.path.join(exe_dir, INSTALL_MARKER)) else ""


def _schtasks(args):
    """静默调用 schtasks（不弹黑框）。"""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        ["schtasks.exe"] + args,
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
        creationflags=flags,
    )


def installed_task_exists():
    try:
        return _schtasks(["/query", "/tn", INSTALL_TASK]).returncode == 0
    except Exception:
        return False


def run_installed_task():
    """通过安装时创建的计划任务以最高权限拉起自身，全程无 UAC 提示。"""
    try:
        rc = _schtasks(["/run", "/tn", INSTALL_TASK]).returncode
        if rc == 0:
            log("已通过安装版计划任务以管理员权限启动（无 UAC 提示）")
            return True
        log("计划任务启动失败 rc=%s" % rc)
    except Exception as exc:
        log("计划任务启动异常: %s" % exc)
    return False


def pawnio_installed():
    try:
        out = subprocess.run(["sc.exe", "query", "PawnIO"], capture_output=True,
                             creationflags=0x08000000, timeout=10)
        return b"RUNNING" in out.stdout or b"STOPPED" in out.stdout or b"1060" not in out.stdout
    except Exception:
        return False


def copy_to_clipboard(text):
    try:
        safe = (text or "").replace("\r", "")
        script = "Set-Clipboard -Value @'\n%s\n'@" % safe
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        subprocess.run([os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                     "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
                        "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
                        "-EncodedCommand", encoded],
                       capture_output=True, creationflags=0x08000000, timeout=20)
        return True
    except Exception:
        return False


class Api(object):
    def __init__(self):
        self.settings = load_settings()
        self.started = time.time()
        self.window = None
        self.tray = None
        self.boot_errors = []
        self._colors = {}
        self._used_colors = []

        from core.hwmon import HardwareMonitor, is_admin as _ia
        from core.netmon import NetMonitor
        from core.driverinfo import DriverInfo

        self.hw = HardwareMonitor(LIB_DIR, interval=1.0, history_seconds=7200)
        self.net = NetMonitor(history_seconds=3600, interval=1.0)
        self.drv = DriverInfo()
        self.admin = _ia()

        self.drv.refresh_async()

    def ping(self):
        """存活探针：供二次启动时判断已有实例是否还活着。"""
        return {"ok": True, "pid": os.getpid()}

        self._csv_cache = []
        self._pawnio_tried = False

    # -------------------------------------------------------------- 基础信息
    def ping(self):
        return {"ok": True}

    def color_for(self, key):
        """同一传感器固定同色，供曲线 / 卡片 / 悬浮温度条共用。"""
        if not key:
            return PALETTE[0]
        cached = self._colors.get(key)
        if cached:
            return cached
        color = next((c for c in PALETTE if c not in self._used_colors), None)
        if color is None:
            color = PALETTE[len(self._colors) % len(PALETTE)]
        self._used_colors.append(color)
        self._colors[key] = color
        return color

    def _paint(self, items):
        for item in items or []:
            try:
                item["c"] = self.color_for(item.get("k"))
            except Exception:
                pass
        return items

    def get_boot(self):
        try:
            import platform
            osname = ""
            try:
                osname = platform.platform(terse=True)
            except Exception:
                pass
            return {
                "app": APP_NAME,
                "version": VERSION,
                "author": AUTHOR,
                "homepage": HOMEPAGE,
                "admin": self.admin,
                "pid": os.getpid(),
                "settings": self.settings,
                "system_lang": system_language(),
                "autostart_actual": autostart_enabled(),
                "autostart_cmd": startup_command(),
                "pawnio": pawnio_installed(),
                "host": os.environ.get("COMPUTERNAME", ""),
                "user": os.environ.get("USERNAME", ""),
                "os": osname,
                "frozen": bool(getattr(sys, "frozen", False)),
            }
        except Exception as exc:
            return {"error": str(exc), "app": APP_NAME, "version": VERSION}

    def state(self):
        snap = self.hw.get_snapshot()
        snap["temps"] = self._paint(snap.get("temps"))
        snap["powers"] = self._paint(snap.get("powers"))
        return {"snap": snap, "net": self.net.get(), "admin": self.admin,
                "uptime": int(time.time() - self.started)}

    def open_site(self):
        """在系统浏览器中打开官网。"""
        try:
            if hasattr(os, "startfile"):
                os.startfile(HOMEPAGE)  # noqa: S606
            else:
                import webbrowser
                webbrowser.open(HOMEPAGE)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def restore_window(self):
        try:
            if self.window is not None:
                self.window.show()
                self.window.restore()
                bring_to_front()
                return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "窗口不可用"}

    def set_setting(self, key, value):
        try:
            if key == "language":
                code = str(value or "auto")
                if code != "auto" and code not in SUPPORTED_LANGS:
                    return {"ok": False, "error": "不支持的语言代码: %s" % code}
                self.settings["language"] = code
                try:
                    if self.window is not None:
                        lang = system_language() if code == "auto" else match_language(code)
                        self.window.title = LANG_TITLES.get(lang, "Hardware Master")
                except Exception:
                    pass
            elif key == "autostart":
                ok, info = set_autostart(bool(value))
                if not ok:
                    return {"ok": False, "error": info}
                self.settings["autostart"] = bool(value)
            elif key == "theme":
                mode = str(value or "auto")
                if mode not in ("auto", "light", "dark"):
                    return {"ok": False, "error": "不支持的主题: %s" % mode}
                self.settings["theme"] = mode
                try:
                    apply_dark_titlebar(self.window, tray_icon_path(), effective_dark(mode))
                except Exception:
                    pass
            elif key == "close_to_tray":
                self.settings["close_to_tray"] = bool(value)
                if value:
                    ensure_tray(self, tray_icon_path())
                else:
                    stop_tray(self)
            else:
                self.settings[key] = value
            save_settings(self.settings)
            return {"ok": True, "settings": self.settings, "autostart_actual": autostart_enabled()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -------------------------------------------------------------- 温度导出
    def export_csv(self, minutes=15):
        try:
            out_dir = os.path.join(os.path.expanduser("~"), "Documents", APP_NAME, "温度记录")
            os.makedirs(out_dir, exist_ok=True)
            name = "温度记录_%s.csv" % time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join(out_dir, name)
            header = "时间" if ui_language().startswith("zh") else "Time"
            self.hw.export_csv(float(minutes), path, header)
            return {"ok": True, "path": path, "dir": out_dir}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def open_target(self, target):
        try:
            mapping = {
                "windowsupdate": "ms-settings:windowsupdate",
                "devmgmt": "devmgmt.msc",
                "network": "ms-settings:network-status",
                "settings": "ms-settings:",
                "about": "ms-settings:about",
            }
            if target in mapping:
                os.startfile(mapping[target])
                return {"ok": True}
            if target == "backup":
                self.open_target_path(os.path.join(os.path.expanduser("~"), "Documents", APP_NAME, "驱动备份"))
                return {"ok": True}
            if target == "log":
                self.open_target_path(APPDATA_DIR)
                return {"ok": True}
            if target == "csv":
                self.open_target_path(os.path.join(os.path.expanduser("~"), "Documents", APP_NAME, "温度记录"))
                return {"ok": True}
            if target == "program":
                home = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) \
                    else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                os.startfile(home)
                return {"ok": True, "path": home}
            return {"ok": False, "error": "未知目标"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def open_target_path(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            os.startfile(path)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -------------------------------------------------------------- 驱动
    def drivers(self):
        data = self.drv.get()
        data["packages"] = self.drv.packages()
        data["admin"] = self.admin
        return data

    def refresh_drivers(self):
        return {"started": self.drv.refresh_async()}

    def backup_drivers(self):
        dest = os.path.join(os.path.expanduser("~"), "Documents", APP_NAME, "驱动备份")
        return {"started": self.drv.backup_async(dest), "path": dest}

    def backup_status(self):
        return self.drv.backup_status()

    # -------------------------------------------------------------- 驱动安装 / 提权
    def install_pawnio(self):
        if not self.admin:
            return {"ok": False, "error": "需要管理员权限"}
        path = os.path.join(ASSET_DIR, "PawnIO_setup.exe")
        if not os.path.exists(path):
            return {"ok": False, "error": "安装包缺失"}
        try:
            subprocess.Popen([path], creationflags=0x00000000)
            return {"ok": True, "hint": "请按安装程序提示完成安装，完成后重启本程序"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def elevate(self):
        if self.admin:
            return {"ok": True, "already": True}
        ok = relaunch_elevated()
        if ok:
            threading.Timer(1.0, lambda: os._exit(0)).start()
        else:
            self.settings["auto_elevate"] = False
            save_settings(self.settings)
        return {"ok": ok, "already": False}

    def copy_text(self, text):
        return {"ok": copy_to_clipboard(text)}

    def quit_app(self):
        try:
            if getattr(self, "tray", None) is not None:
                self.tray.stop()
        except Exception:
            pass
        try:
            if self.window is not None:
                self.window.destroy()
        except Exception:
            pass
        os._exit(0)


def bring_to_front():
    """把主窗口从托盘/最小化状态拉到前台（按本进程 PID 找，标题随语言变化也能找到）。"""
    try:
        hwnd = own_window_handle()
        if not hwnd:
            return
        u = ctypes.windll.user32
        u.ShowWindow(hwnd, 9)          # SW_RESTORE
        # 从托盘点击唤回时，系统会限制非前台进程抢焦点；先模拟一次 Alt 按键再设置前台
        u.keybd_event(0x12, 0, 0, 0)              # VK_MENU down
        u.SetForegroundWindow(hwnd)
        u.BringWindowToTop(hwnd)
        u.keybd_event(0x12, 0, 0x0002, 0)         # VK_MENU up
    except Exception:
        pass


def show_main_window(api):
    try:
        if api.window is not None:
            api.window.show()
            api.window.restore()
            bring_to_front()
    except Exception as exc:
        log("显示主窗口失败: %s" % exc)


def start_tray(api, icon_path):
    """托盘图标：关窗后仍能唤回主界面或彻底退出。"""
    try:
        import pystray
        from PIL import Image

        image = Image.open(icon_path)
    except Exception as exc:
        log("托盘依赖不可用: %s" % exc)
        return False
    try:
        def do_quit(icon=None, item=None):
            try:
                if api.tray is not None:
                    api.tray.stop()
            except Exception:
                pass
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem(tray_labels()[0], lambda: show_main_window(api), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(tray_labels()[1], do_quit),
        )
        api.tray = pystray.Icon("HardwareMaster", image, window_title(), menu)
        threading.Thread(target=api.tray.run, daemon=True).start()
        log("托盘图标已启动")
        threading.Thread(target=promote_tray_icon, daemon=True).start()
        return True
    except Exception as exc:
        log("托盘图标启动失败: %s" % exc)
        return False


def ensure_tray(api, icon_path):
    """托盘图标只在首次需要时创建；已存在则直接复用。"""
    if getattr(api, "tray", None) is not None:
        return True
    return start_tray(api, icon_path)


def stop_tray(api):
    """关闭托盘图标（用户关掉“关闭后最小化到托盘”时调用）。"""
    try:
        if getattr(api, "tray", None) is not None:
            api.tray.stop()
            api.tray = None
            log("托盘图标已移除")
    except Exception as exc:
        log("移除托盘图标失败: %s" % exc)


def tray_icon_path():
    return os.path.join(ASSET_DIR, "icon.ico")


def promote_tray_icon(attempts=5, delay=1.6):
    """Windows 11 默认把新的托盘图标收进折叠区（^）里。

    这里在 HKCU\\Control Panel\\NotifyIconSettings 下找到本程序对应的那条记录，
    把 IsPromoted 置 1，让图标直接常显在任务栏右下角；用户仍可自行改回。
    """
    try:
        import winreg
    except Exception:
        return
    if not getattr(sys, "frozen", False):
        return
    target = os.path.normcase(os.path.abspath(sys.executable))
    target_name = os.path.basename(target)
    for _ in range(max(1, attempts)):
        found = 0
        try:
            root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\NotifyIconSettings", 0,
                                  winreg.KEY_READ | winreg.KEY_WRITE)
        except OSError:
            return
        try:
            idx = 0
            while True:
                try:
                    name = winreg.EnumKey(root, idx)
                except OSError:
                    break
                idx += 1
                path = ""
                try:
                    sub = winreg.OpenKey(root, name, 0, winreg.KEY_READ | winreg.KEY_WRITE)
                except OSError:
                    continue
                try:
                    for value_name in ("ExecutablePath", "IconFile", "WindowName"):
                        try:
                            path = str(winreg.QueryValueEx(sub, value_name)[0] or "")
                            if path:
                                break
                        except OSError:
                            continue
                    norm = os.path.normcase(path.replace("/", "\\"))
                    if norm and (norm == target or norm.endswith("\\" + target_name)):
                        try:
                            winreg.SetValueEx(sub, "IsPromoted", 0, winreg.REG_DWORD, 1)
                            found += 1
                        except OSError:
                            pass
                finally:
                    sub.Close()
        finally:
            root.Close()
        if found:
            log("托盘图标已设为常显（任务栏右下角）")
            return
        time.sleep(delay)
    log("托盘图标未能自动常显，可在“隐藏图标 ^”里拖出")
def own_window_handle(title_only=None):
    """按进程 PID 找本程序的窗口；title_only 指定时按标题精确匹配（可不可见）。"""
    found = []
    pid = os.getpid()
    u = ctypes.windll.user32

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, lparam):
        wpid = ctypes.wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value != pid:
            return True
        if title_only is None and not u.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        u.GetWindowTextW(hwnd, buf, 256)
        if title_only is not None:
            if buf.value == title_only:
                found.append(hwnd)
        elif APP_NAME in buf.value:
            found.append(hwnd)
        return True

    u.EnumWindows(cb, 0)
    return found[0] if found else 0


def system_uses_dark():
    """读取 Windows「应用模式」设置：True=深色。"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        try:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        finally:
            key.Close()
        return int(value) == 0
    except Exception:
        return True


def effective_dark(theme):
    if theme == "light":
        return False
    if theme == "dark":
        return True
    return system_uses_dark()


def apply_dark_titlebar(window, icon_path, dark=None):
    """标题栏跟随外观主题（深色/浅色）+ 窗口图标。"""
    import ctypes.wintypes as wt

    if dark is None:
        dark = True
    hwnd = 0
    for _ in range(20):
        hwnd = own_window_handle()
        if hwnd:
            break
        time.sleep(0.3)
    if not hwnd:
        log("未找到窗口句柄，跳过标题栏装饰")
        return

    try:
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes = [wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD]
        flag = ctypes.c_int(1 if dark else 0)
        codes = []
        for attr in (20, 19):
            codes.append(dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(flag), 4))
        log("标题栏 dark=%s hr=%s" % (dark, codes))
    except Exception as exc:
        log("标题栏设置失败: %s" % exc)

    try:
        u = ctypes.windll.user32
        u.LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT,
                                 ctypes.c_int, ctypes.c_int, wt.UINT]
        u.LoadImageW.restype = wt.HANDLE
        u.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        small = u.LoadImageW(None, icon_path, 1, 16, 16, 0x10)
        big = u.LoadImageW(None, icon_path, 1, 32, 32, 0x10)
        if small:
            u.SendMessageW(hwnd, 0x0080, 0, small)
        if big:
            u.SendMessageW(hwnd, 0x0080, 1, big)
    except Exception as exc:
        log("窗口图标设置失败: %s" % exc)


class ApiHandler(BaseHTTPRequestHandler):
    """本地 HTTP 接口：/api/<方法名> + 静态文件。仅监听 127.0.0.1。"""

    api_obj = None

    def log_message(self, *args):
        pass

    MIME = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".ico": "image/x-icon",
        ".woff2": "font/woff2",
    }

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def do_GET(self):
        rel = urllib_parse.unquote(self.path.split("?")[0]).lstrip("/") or "index.html"
        full = os.path.normpath(os.path.join(UI_DIR, rel))
        root = os.path.normpath(UI_DIR)
        if not full.startswith(root) or not os.path.isfile(full):
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        with open(full, "rb") as fh:
            data = fh.read()
        self._send(200, data, self.MIME.get(os.path.splitext(full)[1].lower(),
                                            "application/octet-stream"))

    def do_POST(self):
        if not self.path.startswith("/api/"):
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        name = self.path[5:].split("?")[0]
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"[]"
            args = json.loads(raw.decode("utf-8") or "[]")
            if not isinstance(args, list):
                args = [args]
        except Exception:
            args = []
        fn = getattr(self.api_obj, name, None)
        if not callable(fn) or name.startswith("_"):
            self._send(404, b'{"error":"unknown"}')
            return
        try:
            out = fn(*args)
        except Exception as exc:
            log("接口异常 %s: %r" % (name, exc))
            out = {"error": str(exc)}
        self._send(200, json.dumps(out, ensure_ascii=False, default=str).encode("utf-8"))


def start_api_server(api):
    ApiHandler.api_obj = api
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
    srv.daemon_threads = True
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, name="api-http", daemon=True).start()
    return srv, port


def existing_instance_port():
    """已有实例还活着就返回它的端口（用于二次双击 exe 唤回窗口）。"""
    try:
        with open(PORT_PATH, "r", encoding="utf-8") as fh:
            port = int(fh.read().strip())
    except Exception:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://127.0.0.1:%d/api/ping" % port, data=b"[]", method="POST")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return port
    except Exception:
        return None
    return None


def main():
    os.makedirs(APPDATA_DIR, exist_ok=True)
    sys.path.insert(0, BASE_DIR)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # 先看有没有实例在跑：有就直接唤回它的窗口，省掉一次不必要的提权
    port0 = existing_instance_port()
    if port0:
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:%d/api/restore_window" % port0, method="POST", data=b"[]"),
                timeout=3)
        except Exception:
            pass
        log("已有实例在运行，唤回主窗口后退出")
        return

    if not is_admin():
        if installed_dir():
            # 安装版：只走计划任务，永不弹 UAC；任务缺失时降级为受限模式
            if installed_task_exists() and run_installed_task():
                return
            log("安装版未取得管理员权限，本次以受限模式运行")
        else:
            settings = load_settings()
            if settings.get("auto_elevate", True):
                if relaunch_elevated():
                    return

    import webview

    api = Api()
    log("启动：admin=%s pid=%s" % (api.admin, os.getpid()))

    try:
        api.hw.init_now()
    except Exception as exc:
        log("传感器初始化失败: %s" % exc)
    api.hw.start()

    srv, port = start_api_server(api)
    log("本地接口已启动 127.0.0.1:%d" % port)
    try:
        with open(PORT_PATH, "w", encoding="utf-8") as fh:
            fh.write(str(port))
    except Exception:
        pass

    icon = os.path.join(ASSET_DIR, "icon.ico")
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    win_w, win_h = 1400, 900
    pos_x = max(0, (sw - win_w) // 2)
    pos_y = max(0, (sh - win_h) // 2 - 24)
    window = webview.create_window(
        window_title(),
        url="http://127.0.0.1:%d/index.html" % port,
        width=win_w,
        height=win_h,
        x=pos_x,
        y=pos_y,
        min_size=(1120, 720),
        background_color=("#07090e" if effective_dark(api.settings.get("theme")) else "#eef1f7"),
        text_select=False,
    )
    api.window = window

    def on_main_closing():
        # pywebview：处理函数返回 False 表示取消关闭
        if not api.settings.get("close_to_tray"):
            return True
        try:
            # 托盘图标在启动时就已经建好；这里只把窗口最小化，任务栏按钮与托盘图标都还在，
            # 绝不会出现“窗口没了又点不开”的情况。
            ok = ensure_tray(api, icon)
            window.minimize()
            if ok:
                log("关闭主窗口 → 已最小化到任务栏，托盘图标可随时唤回")
            else:
                log("关闭主窗口 → 已最小化到任务栏（托盘不可用，可从任务栏唤回）")
            return False
        except Exception as exc:
            log("最小化失败: %s" % exc)
            return False

    window.events.closing += on_main_closing

    def after_start():
        try:
            apply_dark_titlebar(window, icon, effective_dark(api.settings.get("theme")))
            if api.settings.get("close_to_tray"):
                ensure_tray(api, icon)
        except Exception as exc:
            log("窗口装饰失败: %s" % exc)

    webview.start(after_start, debug=False)
    try:
        srv.shutdown()
    except Exception:
        pass
    api.hw.stop()
    api.net.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("致命错误:\n" + traceback.format_exc())
        raise
