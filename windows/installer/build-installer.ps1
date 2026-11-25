# -*- coding: utf-8 -*-
<#
  一键构建安装包：先重新打包 exe，再编译 Inno Setup 安装程序。
  用法：
    powershell -ExecutionPolicy Bypass -File .\installer\build-installer.ps1 -Python "C:\path\to\python.exe"
    powershell -ExecutionPolicy Bypass -File .\installer\build-installer.ps1 -SkipApp   # 只重编安装包
#>
param(
  [string]$Python = "python",
  [switch]$SkipApp
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$iscc = @(
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "未找到 ISCC.exe，请先安装 Inno Setup 6（winget install JRSoftware.InnoSetup）" }

if (-not $SkipApp) {
  Write-Host "[1/2] 重新打包 app -> dist\HardwareMaster.exe" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\build.ps1" -Python $Python
  if ($LASTEXITCODE -ne 0) { throw "应用打包失败" }
} else {
  Write-Host "[1/2] 跳过应用打包，使用现有 dist\HardwareMaster.exe" -ForegroundColor Yellow
}

Write-Host "[2/2] 编译安装程序" -ForegroundColor Cyan
Push-Location "$root\installer"
try { & $iscc "硬件管理大师.iss" } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw "安装程序编译失败" }

Get-ChildItem "$root\installer\输出\*.exe" | Select-Object Name,
  @{n = '大小MB'; e = { [math]::Round($_.Length / 1MB, 1) } }, LastWriteTime

