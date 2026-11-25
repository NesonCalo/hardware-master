param(
  [Parameter(Mandatory = $true)][string]$ExePath
)

$ErrorActionPreference = "Stop"
$taskName = "NesonCalo HardwareMaster"
$exe = (Resolve-Path -LiteralPath $ExePath).Path
$dir = Split-Path -Parent $exe

$action = New-ScheduledTaskAction -Execute $exe -WorkingDirectory $dir
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$desc = "由「硬件管理大师」安装程序创建：仅手动启动、没有任何触发器、不会开机自启；卸载程序会删除此任务。"

Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings -Description $desc -Force | Out-Null

$info = Get-ScheduledTask -TaskName $taskName
if (-not $info) { throw "scheduled task not found after registration" }
Write-Output ("task ok: {0} / RunLevel={1} / Triggers={2}" -f $taskName, $info.Principal.RunLevel, ($info.Triggers | Measure-Object).Count)
