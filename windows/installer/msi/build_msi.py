# -*- coding: utf-8 -*-
"""Build per-language MSI packages for Hardware Master (WiX 3.14 portable)."""
import argparse
import base64
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MSI_DIR = os.path.join(ROOT, "installer", "msi")
LOCALES = os.path.join(ROOT, "app", "ui", "locales")
EXE = os.path.join(ROOT, "dist", "HardwareMaster.exe")
ICON = os.path.join(ROOT, "app", "assets", "icon.ico")
MARKER = os.path.join(ROOT, "installer", "installed.marker")
INDEX = os.path.join(ROOT, "app", "ui", "index.html")

WORKSPACE = os.environ.get(
    "WIX_WS",
    r"C:\Users\NesonCalo\AppData\Local\DoubaoWork\User Data\Default\.doubaowork\agent_mode\workspace\.sessions\38455657733985538\agents\m_0cwelB13usa",
)
WIX_TOOLS = os.path.join(WORKSPACE, "wix314", "tools")
WXL_SRC = os.path.join(WORKSPACE, "wix3src", "wix3-master", "src", "ext", "UIExtension", "wixlib")

VERSION = "1.1.0"
UPGRADE_CODE = "B7C4E2A1-5D6F-4B8E-9C3A-2F1D0E5B7A94"
TASK_NAME = "NesonCalo HardwareMaster"
INSTALL_DIR = r"C:\Program Files\NesonCalo\Hardware Master"

# code -> (culture, lcid, WixUI wxl or None)
LANGS = {
    "ar": ("ar-SA", 1025, "WixUI_ar-SA.wxl"),
    "bn": ("bn-BD", 0, "WixUI_bn.wxl"),  # MSI has no Bengali lang id, use language-neutral
    "de": ("de-DE", 1031, "WixUI_de-de.wxl"),
    "en": ("en-US", 1033, "WixUI_en-us.wxl"),
    "es": ("es-ES", 3082, "WixUI_es-es.wxl"),
    "fa": ("fa-IR", 1065, "WixUI_fa.wxl"),
    "fr": ("fr-FR", 1036, "WixUI_fr-fr.wxl"),
    "hi": ("hi-IN", 1081, "WixUI_hi-IN.wxl"),
    "id": ("id-ID", 1057, "WixUI_id.wxl"),
    "it": ("it-IT", 1040, "WixUI_it-it.wxl"),
    "ja": ("ja-JP", 1041, "WixUI_ja-jp.wxl"),
    "ko": ("ko-KR", 1042, "WixUI_ko-KR.wxl"),
    "ms": ("ms-MY", 1086, "WixUI_ms.wxl"),
    "nl": ("nl-NL", 1043, "WixUI_nl-NL.wxl"),
    "pl": ("pl-PL", 1045, "WixUI_pl-pl.wxl"),
    "pt-BR": ("pt-BR", 1046, "WixUI_pt-BR.wxl"),
    "ru": ("ru-RU", 1049, "WixUI_ru-ru.wxl"),
    "sv": ("sv-SE", 1053, "WixUI_sv-SE.wxl"),
    "th": ("th-TH", 1054, "WixUI_th-TH.wxl"),
    "tr": ("tr-TR", 1051, "WixUI_tr-TR.wxl"),
    "uk": ("uk-UA", 1058, "WixUI_uk-UA.wxl"),
    "vi": ("vi-VN", 1066, "WixUI_vi.wxl"),
    "zh-CN": ("zh-CN", 2052, "WixUI_zh-CN.wxl"),
    "zh-HK": ("zh-HK", 3076, "WixUI_zh-HK.wxl"),
    "zh-TW": ("zh-TW", 1028, "WixUI_zh-TW.wxl"),
}

RTL = {"ar", "fa"}

# Database code pages for the languages whose WixUI file we generate ourselves.
CODEPAGES = {"id": 1252, "ms": 1252, "vi": 65001, "fa": 65001, "bn": 65001, "hi": 65001}


def load_locale(code):
    with open(os.path.join(LOCALES, code + ".json"), "r", encoding="utf-8") as fp:
        return json.load(fp)


def terms_items():
    """Return ordered (tag, key) items of the terms section in index.html."""
    with open(INDEX, "r", encoding="utf-8") as fp:
        html = fp.read()
    start = html.index('id="termsBox"')
    end = html.index("</div>", start)
    block = html[start:end]
    items = re.findall(r'<(h4|p)\b[^>]*data-i18n="([^"]+)"', block)
    return items


def rtf_text(text):
    out = []
    for ch in text:
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\par ")
        elif ord(ch) < 128:
            out.append(ch)
        else:
            cp = ord(ch)
            if cp > 32767:
                cp -= 65536
            out.append("\\u%d?" % cp)
    return "".join(out)


def build_license_rtf(code, path):
    loc = load_locale(code)
    items = terms_items()
    title = loc.get("服务条款", "Terms of Service")
    rtl = "\\rtlpar " if code in RTL else ""
    parts = [
        r"{\rtf1\ansi\ansicpg1252\deff0\nouicompat{\fonttbl{\f0\fnil\fcharset0 Segoe UI;}"
        r"{\f1\fnil\fcharset0 Segoe UI;}}",
        r"{\colortbl ;\red0\green0\blue0;}",
        r"\viewkind4\uc1 ",
        r"\pard%s\qc\sa240\f1\fs32\b %s\b0\f0\fs20\par " % (rtl, rtf_text(title)),
    ]
    for tag, key in items:
        val = loc.get(key, "")
        if not val:
            continue
        if tag == "h4":
            parts.append(
                r"\pard%s\sa120\sb200\keepn\f1\fs24\b %s\b0\f0\fs20\par " % (rtl, rtf_text(val))
            )
        else:
            italic = r"\i " if key.startswith("本条款提供多语言版本") else ""
            parts.append(
                r"\pard%s\sa160\sl-260\slmult0%s%s\i0\par " % (rtl, italic, rtf_text(val))
            )
    parts.append("}")
    data = "".join(parts).encode("ascii")
    with open(path, "wb") as fp:
        fp.write(data)


EXTRA_STRINGS = {
    "en": {
        "DowngradeError": "A newer version of Hardware Master is already installed. Uninstall it first if you want to install this version.",
        "TaskDescription": "Created by the Hardware Master installer: manual start only, no triggers, never starts at boot. The uninstaller removes this task.",
    },
    "id": {
        "DowngradeError": "Versi Hardware Master yang lebih baru sudah terpasang. Copot pemasangan versi tersebut terlebih dahulu jika ingin memasang versi ini.",
        "TaskDescription": "Dibuat oleh program pemasang Hardware Master: hanya peluncuran manual, tanpa pemicu, tidak pernah berjalan saat boot. Program pencopot akan menghapus tugas ini.",
    },
    "ms": {
        "DowngradeError": "Versi Hardware Master yang lebih baharu sudah dipasang. Nyahpasang versi tersebut terlebih dahulu jika anda mahu memasang versi ini.",
        "TaskDescription": "Dicipta oleh pemasang Hardware Master: pelancaran manual sahaja, tiada pencetus, tidak bermula semasa but. Penyahpasang akan mengalih keluar tugas ini.",
    },
    "vi": {
        "DowngradeError": "Đã cài đặt phiên bản Hardware Master mới hơn. Hãy gỡ phiên bản đó trước nếu bạn muốn cài phiên bản này.",
        "TaskDescription": "Được tạo bởi trình cài đặt Hardware Master: chỉ khởi chạy thủ công, không có kích hoạt, không bao giờ tự khởi động cùng hệ thống. Trình gỡ cài đặt sẽ xóa tác vụ này.",
    },
    "bn": {
        "DowngradeError": "হার্ডওয়্যার মাস্টারের একটি নতুন সংস্করণ ইতিমধ্যে ইনস্টল করা আছে। এই সংস্করণটি ইনস্টল করতে চাইলে প্রথমে সেটি আনইনস্টল করুন।",
        "TaskDescription": "হার্ডওয়্যার মাস্টার ইনস্টলার দ্বারা তৈরি: শুধুমাত্র ম্যানুয়াল স্টার্ট, কোনো ট্রিগার নেই, বুটে কখনো চলে না। আনইনস্টলার এই টাস্কটি মুছে ফেলবে।",
    },
    "fa": {
        "DowngradeError": "نسخه جدیدتری از Hardware Master نصب شده است. برای نصب این نسخه، ابتدا نسخه نصب‌شده را حذف کنید.",
        "TaskDescription": "توسط برنامه نصب Hardware Master ایجاد شده است: فقط اجرای دستی، بدون هیچ راه‌اندازی، هرگز هنگام بوت اجرا نمی‌شود. برنامه حذف این وظیفه را پاک می‌کند.",
    },
}

TASK_DESC = {
    "zh-CN": "由「硬件管理大师」安装程序创建：仅手动启动、没有任何触发器、不会开机自启；卸载程序会删除此任务。",
    "zh-HK": "由「硬件管理大師」安裝程式建立：僅手動啟動、沒有任何觸發程序、不會開機自動啟動；解除安裝程式會刪除此工作。",
    "zh-TW": "由「硬體管理大師」安裝程式建立：僅手動啟動、沒有任何觸發程序、不會開機自動啟動；解除安裝程式會刪除此工作。",
}

DOWNGRADE = {
    "zh-CN": "已安装更新版本的「硬件管理大师」。如需安装此版本，请先卸载已安装的版本。",
    "zh-HK": "已安裝更新版本的「硬件管理大師」。如需安裝此版本，請先解除安裝已安裝的版本。",
    "zh-TW": "已安裝更新版本的「硬體管理大師」。如需安裝此版本，請先解除安裝已安裝的版本。",
}


def build_wxl(code, path):
    culture, lcid, src = LANGS[code]
    base = os.path.join(WXL_SRC, src)
    if not os.path.exists(base):
        base = os.path.join(MSI_DIR, "locales", src)
    with open(base, "r", encoding="utf-8-sig") as fp:
        text = fp.read()
    name = load_locale(code)["硬件管理大师"]
    extra = EXTRA_STRINGS.get(code, {})
    desc = TASK_DESC.get(code, extra.get("TaskDescription", EXTRA_STRINGS["en"]["TaskDescription"]))
    down = DOWNGRADE.get(code, extra.get("DowngradeError", EXTRA_STRINGS["en"]["DowngradeError"]))
    custom = (
        '    <String Id="ProductName" Overridable="yes">%s</String>\n'
        '    <String Id="DowngradeError" Overridable="yes">%s</String>\n'
        '    <String Id="TaskDescription" Overridable="yes">%s</String>\n'
        % (xml_escape(name), xml_escape(down), xml_escape(desc))
    )
    text = text.replace("</WixLocalization>", custom + "</WixLocalization>")
    # force culture/codepage from our table
    text = re.sub(r'Culture="[^"]*"', 'Culture="%s"' % culture, text, count=1)
    if code in CODEPAGES:
        text = re.sub(r'Codepage="\d+"', 'Codepage="%d"' % CODEPAGES[code], text, count=1)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


def xml_escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def ps_encoded(script):
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def write_task_script(code, path):
    desc = (TASK_DESC.get(code) or "Created by the Hardware Master installer: manual start only, no triggers, never starts at boot. The uninstaller removes this task.").replace("'", "''")
    script = """param([string]$Mode = 'install', [string]$User = '')
$ErrorActionPreference = 'Stop'
$task = '%s'
$dir = $PSScriptRoot
$exe = Join-Path $dir 'HardwareMaster.exe'
if (-not $User) { $User = ($env:USERDOMAIN + '\\' + $env:USERNAME) }

if ($Mode -eq 'remove') {
    Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
    exit 0
}

$action = New-ScheduledTaskAction -Execute $exe -WorkingDirectory $dir
$principal = New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $task -Action $action -Principal $principal -Settings $settings -Description '%s' -Force | Out-Null

if (-not (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue)) { exit 1 }
""" % (TASK_NAME, desc)
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as fp:
        fp.write(script)


WXS_TEMPLATE = r"""<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"
     xmlns:util="http://schemas.microsoft.com/wix/UtilExtension">
  <Product Id="*"
           Name="!(loc.ProductName)"
           Language="__LCID__"
           Version="__VERSION__"
           Manufacturer="NesonCalo"
           UpgradeCode="__UPGRADE__"__CPATTR__>
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" Platform="x64"
             Description="!(loc.ProductName) __VERSION__"
             Comments="Hardware Master by NesonCalo" />
    <MajorUpgrade AllowSameVersionUpgrades="yes" DowngradeErrorMessage="!(loc.DowngradeError)" />
    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />

    <Icon Id="AppIcon" SourceFile="__ICON__" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon" />
    <Property Id="ARPHELPLINK" Value="https://www.nesoncalo.com" />
    <Property Id="ARPURLINFOABOUT" Value="https://www.nesoncalo.com" />

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="DesktopFolder" />
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="NesonCaloDir" Name="NesonCalo">
          <Directory Id="INSTALLFOLDER" Name="Hardware Master">
            <Component Id="MainExe" Guid="*" Win64="yes">
              <File Id="HardwareMasterExe" Source="__EXE__" Name="HardwareMaster.exe" KeyPath="yes">
                <Shortcut Id="DesktopShortcut" Directory="DesktopFolder" Name="!(loc.ProductName)"
                          WorkingDirectory="INSTALLFOLDER" Icon="AppIcon" Advertise="no" />
              </File>
              <RemoveFolder Id="RemoveInstallFolder" Directory="INSTALLFOLDER" On="uninstall" />
            </Component>
            <Component Id="MarkerFile" Guid="*" Win64="yes">
              <File Id="InstalledMarker" Source="__MARKER__" Name="installed.marker" KeyPath="yes" />
            </Component>
            <Component Id="HelperScript" Guid="*" Win64="yes">
              <File Id="SetupTaskScript" Source="__TASKSCRIPT__" Name="setup-task.ps1" KeyPath="yes" />
            </Component>
            <Component Id="RegistryEntries" Guid="*" Win64="yes">
              <RegistryValue Root="HKLM" Key="Software\NesonCalo\HardwareMaster" Name="InstallDir"
                             Type="string" Value="[INSTALLFOLDER]" KeyPath="yes" />
              <RemoveFolder Id="RemoveNesonCaloDir" Directory="NesonCaloDir" On="uninstall" />
            </Component>
          </Directory>
        </Directory>
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="AppMenuFolder" Name="Hardware Master">
          <Component Id="StartMenuShortcut" Guid="*" Win64="yes">
            <Shortcut Id="StartMenuShortcut" Directory="AppMenuFolder" Name="!(loc.ProductName)"
                      Target="[INSTALLFOLDER]HardwareMaster.exe" WorkingDirectory="INSTALLFOLDER"
                      Icon="AppIcon" Advertise="no" />
            <RemoveFolder Id="RemoveAppMenuFolder" Directory="AppMenuFolder" On="uninstall" />
            <RegistryValue Root="HKLM" Key="Software\NesonCalo\HardwareMaster" Name="MenuEntry"
                           Type="integer" Value="1" KeyPath="yes" />
          </Component>
        </Directory>
      </Directory>
    </Directory>

    <Feature Id="MainFeature" Title="!(loc.ProductName)" Level="1">
      <ComponentRef Id="MainExe" />
      <ComponentRef Id="MarkerFile" />
      <ComponentRef Id="HelperScript" />
      <ComponentRef Id="RegistryEntries" />
      <ComponentRef Id="StartMenuShortcut" />
    </Feature>

    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
    <WixVariable Id="WixUILicenseRtf" Value="__LICENSE__" />
    <UIRef Id="WixUI_InstallDir" />

    <CustomAction Id="SetCreateTaskCmd" Property="CreateElevateTask"
                  Value="&quot;[SystemFolder]WindowsPowerShell\v1.0\powershell.exe&quot; -NoProfile -ExecutionPolicy Bypass -File &quot;[INSTALLFOLDER]setup-task.ps1&quot; install &quot;[%USERDOMAIN]\[%USERNAME]&quot;"
                  Execute="immediate" />
    <CustomAction Id="CreateElevateTask" BinaryKey="WixCA" DllEntry="WixQuietExec"
                  Execute="deferred" Return="ignore" Impersonate="no" />
    <CustomAction Id="SetDeleteTaskCmd" Property="DeleteElevateTask"
                  Value="&quot;[SystemFolder]schtasks.exe&quot; /delete /tn &quot;NesonCalo HardwareMaster&quot; /f"
                  Execute="immediate" />
    <CustomAction Id="DeleteElevateTask" BinaryKey="WixCA" DllEntry="WixQuietExec"
                  Execute="deferred" Return="ignore" Impersonate="no" />

    <InstallExecuteSequence>
      <Custom Action="SetCreateTaskCmd" Sequence="4001">NOT Installed</Custom>
      <Custom Action="CreateElevateTask" Sequence="4002">NOT Installed</Custom>
      <Custom Action="SetDeleteTaskCmd" Sequence="3399">REMOVE~="ALL"</Custom>
      <Custom Action="DeleteElevateTask" Sequence="3400">REMOVE~="ALL"</Custom>
    </InstallExecuteSequence>
  </Product>
</Wix>
"""


def build_one(code, keep_build=False):
    culture, lcid, _ = LANGS[code]
    bdir = os.path.join(MSI_DIR, "build", code)
    os.makedirs(bdir, exist_ok=True)
    lic = os.path.join(bdir, "license.rtf")
    build_license_rtf(code, lic)
    wxl = os.path.join(bdir, "loc.wxl")
    build_wxl(code, wxl)
    taskscript = os.path.join(bdir, "setup-task.ps1")
    write_task_script(code, taskscript)
    wxs = os.path.join(bdir, "product.wxs")
    body = (
        WXS_TEMPLATE.replace("__LCID__", str(lcid))
        .replace("__VERSION__", VERSION)
        .replace("__UPGRADE__", UPGRADE_CODE)
        .replace("__EXE__", EXE).replace("__ICON__", ICON)
        .replace("__MARKER__", MARKER)
        .replace("__TASKSCRIPT__", taskscript)
        .replace("__CPATTR__", (' Codepage="%d"' % CODEPAGES[code]) if code in CODEPAGES else "")
        .replace("__LICENSE__", lic)
    )
    with open(wxs, "w", encoding="utf-8") as fp:
        fp.write(body)

    obj = os.path.join(bdir, "product.wixobj")
    out = os.path.join(MSI_DIR, "out", "HardwareMaster-%s-%s.msi" % (VERSION, code))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ext = ["-ext", "WixUIExtension", "-ext", "WixUtilExtension"]
    r1 = subprocess.run(
        [os.path.join(WIX_TOOLS, "candle.exe"), "-nologo"] + ext + [wxs, "-out", obj],
        cwd=bdir, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r1.returncode != 0:
        print(r1.stdout)
        print(r1.stderr)
        raise SystemExit("candle failed for %s" % code)
    r2 = subprocess.run(
        [os.path.join(WIX_TOOLS, "light.exe"), "-nologo"] + ext +
        ["-loc", wxl, "-b", bdir, "-sice:ICE38", "-sice:ICE43", "-sice:ICE57",
         "-sice:ICE61", "-sice:ICE64", "-sice:ICE80", obj, "-out", out],
        cwd=bdir, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r2.returncode != 0 or not os.path.exists(out):
        print(r2.stdout)
        print(r2.stderr)
        raise SystemExit("light failed for %s" % code)
    warn = [ln for ln in (r2.stdout + r2.stderr).splitlines() if "warning" in ln.lower()]
    print("%s -> %s (%d bytes)%s" % (code, os.path.basename(out), os.path.getsize(out),
                                     ("; %d warnings" % len(warn)) if warn else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    codes = list(LANGS) if args.all else (args.lang or ["zh-CN"])
    for c in codes:
        if c not in LANGS:
            raise SystemExit("unknown language: " + c)
        build_one(c)


if __name__ == "__main__":
    main()






