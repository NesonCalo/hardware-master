<#
  构建脚本：把 app/ 打包成单文件 exe（dist\HardwareMaster.exe）
  用法：powershell -ExecutionPolicy Bypass -File build.ps1
  可选：-Python "C:\path\to\python.exe"
#>
param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/3] 安装依赖 ..." -ForegroundColor Cyan
& $Python -m pip install --upgrade -r "$root\requirements.txt"

Write-Host "[2/3] 打包 (PyInstaller onefile) ..." -ForegroundColor Cyan
Set-Location "$root\app"
& $Python -m PyInstaller `
  --noconfirm --clean --onefile --windowed `
  --name "HardwareMaster" `
  --icon "$root\app\assets\icon.ico" `
  --add-data "$root\app\ui;ui" `
  --add-data "$root\app\lib;lib" `
  --add-data "$root\app\assets;assets" `
  --collect-all webview `
  --collect-all pystray `
  --hidden-import clr `
  --distpath "$root\dist" `
  --workpath "$root\build" `
  --specpath "$root\build" `
  main.py

Set-Location $root
Write-Host "[3/3] 完成：$root\dist\HardwareMaster.exe" -ForegroundColor Green
Get-ChildItem "$root\dist" | Select-Object Name, @{n='大小MB';e={[math]::Round($_.Length/1MB,1)}}

