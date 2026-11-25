param(
  [string]$OutDir = "C:\Users\NesonCalo\DoubaoWork\chats\2026-11-23\new-chat\硬件管理大师\installer\msi\out",
  [string]$DtfDll = "C:\Users\NesonCalo\AppData\Local\DoubaoWork\User Data\Default\.doubaowork\agent_mode\workspace\.sessions\38455657733985538\agents\m_0cwelB13usa\wix314\tools\Microsoft.Deployment.WindowsInstaller.dll"
)
Add-Type -Path $DtfDll

$scriptRange = @{
  'ar' = '[\u0600-\u06FF]'; 'fa' = '[\u0600-\u06FF]'; 'bn' = '[\u0980-\u09FF]'; 'hi' = '[\u0900-\u097F]'
  'th' = '[\u0E00-\u0E7F]'; 'ja' = '[\u3040-\u30FF\u4E00-\u9FFF]'; 'ko' = '[\uAC00-\uD7AF]'
  'ru' = '[\u0400-\u04FF]'; 'uk' = '[\u0400-\u04FF]'
  'zh-CN' = '[\u4E00-\u9FFF]'; 'zh-HK' = '[\u4E00-\u9FFF]'; 'zh-TW' = '[\u4E00-\u9FFF]'
}

function Decode-Rtf([string]$rtf) {
  $sb = New-Object System.Text.StringBuilder
  $i = 0
  while ($i -lt $rtf.Length) {
    if ($rtf[$i] -eq '\') {
      $m = [regex]::Match($rtf.Substring($i), '^\\u(-?\d+)\s?\??')
      if ($m.Success) {
        $cp = [int]$m.Groups[1].Value
        if ($cp -lt 0) { $cp += 65536 }
        [void]$sb.Append([char]$cp)
        $i += $m.Length
        continue
      }
      $m2 = [regex]::Match($rtf.Substring($i), '^\\([a-zA-Z]+)(-?\d+)?\s?')
      if ($m2.Success) {
        if ($m2.Groups[1].Value -in @('par', 'pard', 'sa240', 'sb200', 'fs32', 'fs24', 'fs20', 'f0', 'f1', 'b', 'b0', 'i', 'i0', 'qc', 'keepn', 'sl', 'slmult0')) { }
        $i += $m2.Length
        continue
      }
      $i++
      continue
    }
    if ($rtf[$i] -eq '{' -or $rtf[$i] -eq '}') { $i++; continue }
    [void]$sb.Append($rtf[$i]); $i++
  }
  return $sb.ToString()
}

$rows = @()
foreach ($msi in Get-ChildItem $OutDir -Filter *.msi | Sort-Object Name) {
  $code = ($msi.BaseName -split '-', 3)[-1]
  $db = New-Object Microsoft.Deployment.WindowsInstaller.Database($msi.FullName, [Microsoft.Deployment.WindowsInstaller.DatabaseOpenMode]::ReadOnly)
  $name = ''; $lang = ''
  $v = $db.OpenView("SELECT Property, Value FROM ``Property`` WHERE Property='ProductName' OR Property='ProductLanguage'")
  $v.Execute()
  while ($r = $v.Fetch()) { if ($r.GetString(1) -eq 'ProductName') { $name = $r.GetString(2) } else { $lang = $r.GetString(2) } }
  $v.Close()

  $title = ''
  $v = $db.OpenView("SELECT Text FROM ``Control`` WHERE Dialog_='InstallDirDlg' AND Control='Title'")
  $v.Execute(); while ($r = $v.Fetch()) { $title = $r.GetString(1) }; $v.Close()

  $accept = ''
  $v = $db.OpenView("SELECT Text FROM ``Control`` WHERE Dialog_='LicenseAgreementDlg' AND Control='LicenseAcceptedCheckBox'")
  $v.Execute(); while ($r = $v.Fetch()) { $accept = $r.GetString(1) }; $v.Close()

  $licRaw = ''
  $v = $db.OpenView("SELECT Text FROM ``Control`` WHERE Dialog_='LicenseAgreementDlg' AND Control='LicenseText'")
  $v.Execute(); while ($r = $v.Fetch()) { $licRaw = $r.GetString(1) }; $v.Close()
  $db.Close()

  $plain = Decode-Rtf $licRaw
  $letters = ([regex]::Matches($plain, '[A-Za-z]')).Count
  $hits = 0
  if ($scriptRange.ContainsKey($code)) { $hits = ([regex]::Matches($plain, $scriptRange[$code])).Count }

  $ok = if ($scriptRange.ContainsKey($code)) { $hits -gt 100 } else { $letters -gt 300 }

  $rows += [pscustomobject]@{
    File = $msi.Name
    Code = $code
    ProductName = $name
    DirTitle = ($title -replace '^\{[^}]*\}', '')
    LicRTF = $licRaw.Length
    LicText = $plain.Length
    Letters = $letters
    Script = $hits
    Accept = $accept.Length
    Status = if ($ok) { 'OK' } else { 'CHECK' }
  }
}
$rows | Format-Table -AutoSize | Out-String -Width 320
$rows | Export-Csv -Path (Join-Path $OutDir 'verify-report.csv') -Encoding UTF8 -NoTypeInformation
