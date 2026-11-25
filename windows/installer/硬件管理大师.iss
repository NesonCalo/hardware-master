; 硬件管理大师 —— Windows 标准安装程序（Inno Setup 6）
; 特性：per-machine 安装到 Program Files、许可页、开始菜单/桌面快捷方式、标准卸载；
;      安装阶段登记“仅手动启动、无触发器”的计划任务，实现安装版免 UAC 的管理员启动。
; 编译：ISCC.exe 硬件管理大师.iss

#define AppName "硬件管理大师"
#define AppVersion "1.1.0"
#define AppPublisher "NesonCalo"
#define AppURL "https://www.nesoncalo.com"
#define AppExe "HardwareMaster.exe"

[Setup]
AppId={{2C4E1F7A-9B3D-4C56-8E10-7A5D2F9C4B18}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} 安装程序
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=Copyright (C) 2026 {#AppPublisher}

DefaultDirName={autopf}\NesonCalo\Hardware Master
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

LicenseFile=license.txt
InfoBeforeFile=info-before.txt

PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

OutputDir=输出
OutputBaseFilename={#AppName}-安装程序-{#AppVersion}
SetupIconFile=..\app\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}

Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=auto
CloseApplications=yes
RestartApplications=no
SetupMutex=Global\NesonCaloHardwareMasterSetup

[Languages]
Name: "zhcn"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "installed.marker"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\服务条款.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "license.txt"; DestDir: "{app}\docs"; DestName: "服务条款.txt"; Flags: ignoreversion
Source: "info-before.txt"; DestDir: "{app}\docs"; DestName: "安装说明.txt"; Flags: ignoreversion
Source: "create_task.ps1"; DestDir: "{tmp}"; Flags: dontcopy

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\服务条款"; Filename: "{app}\docs\服务条款.md"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/delete /tn ""NesonCalo HardwareMaster"" /f"; Flags: runhidden; RunOnceId: "DelElevateTask"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\docs"

[Code]
function RegisterElevateTask(): Boolean;
var
  ResultCode: Integer;
  Params: String;
begin
  ExtractTemporaryFile('create_task.ps1');
  Params := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\create_task.ps1') +
            '" "' + ExpandConstant('{app}\{#AppExe}') + '"';
  Result := Exec('powershell.exe', Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Log('create_task.ps1 failed, exit code = ' + IntToStr(ResultCode));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if RegisterElevateTask() then
      Log('elevation task registered: NesonCalo HardwareMaster')
    else
      MsgBox('管理员启动任务创建失败，程序仍可使用，但每次启动不会有免 UAC 的管理员权限。' + #13#10 +
             '可手动以管理员身份运行本程序，或重新安装。', mbError, MB_OK);
  end;
end;

