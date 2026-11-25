# 从 Java 源码提取 L.t(中文, English) 文案，生成 25 语言资源
# 使用 Google 翻译公共端点，一次请求翻译整批（以换行分隔），结果写入 assets/i18n/<tag>.json
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = "$root\src"
$outDir = "$root\assets\i18n"

$pairs = [ordered]@{}
Get-ChildItem $src -Recurse -Filter *.java | ForEach-Object {
    $raw = Get-Content $_.FullName -Raw
    [regex]::Matches($raw, 'L\.t\("(?<zh>[^"]*)",\s*"(?<en>[^"]*)"\)') | ForEach-Object {
        $zh = $_.Groups['zh'].Value
        if (-not $pairs.Contains($zh)) { $pairs[$zh] = $_.Groups['en'].Value }
    }
}
$pairs | ConvertTo-Json -Depth 3 | Set-Content "$root\tools\strings-zh-en.json" -Encoding utf8

$langs = @("ar","bn","de","es","fa","fr","hi","id","it","ja","ko","ms","nl","pl","pt-BR","ru","sv","th","tr","uk","vi","zh-HK","zh-TW")
$keys = @($pairs.Keys)

function Translate-Batch([string]$text, [string]$tl) {
    $u = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=' + $tl + '&dt=t&q=' + [uri]::EscapeDataString($text)
    $resp = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 60
    $j = $resp.Content | ConvertFrom-Json
    $sb = New-Object System.Text.StringBuilder
    foreach ($seg in $j[0]) { [void]$sb.Append($seg[0]) }
    return $sb.ToString()
}

foreach ($lang in $langs) {
    $joined = ($keys | ForEach-Object { $pairs[$_].Trim() }) -join "`n"
    $translated = $null
    for ($try = 1; $try -le 3; $try++) {
        try { $translated = Translate-Batch $joined $lang; break } catch { Start-Sleep -Seconds 3 }
    }
    if (-not $translated) { Write-Host "[$lang] failed"; continue }
    $lines = $translated -split "`n"
    if ($lines.Count -ne $keys.Count) {
        Write-Host "[$lang] line mismatch $($lines.Count)/$($keys.Count), fallback per-string"
        $map = [ordered]@{}
        for ($i = 0; $i -lt $keys.Count; $i++) {
            $t = $null
            try { $t = Translate-Batch $keys[$i] $lang } catch {}
            $map[$keys[$i]] = if ($t) { $t.Trim() } else { $pairs[$keys[$i]] }
        }
        $map | ConvertTo-Json -Depth 3 | Set-Content "$outDir\$lang.json" -Encoding utf8
        continue
    }
    $obj = [ordered]@{}
    for ($i = 0; $i -lt $keys.Count; $i++) {
        $obj[$keys[$i]] = $lines[$i]
        if ($keys[$i].StartsWith(' ')) { $obj[$keys[$i]] = ' ' + $obj[$keys[$i]].TrimStart() }
        if ($keys[$i].EndsWith(' ')) { $obj[$keys[$i]] = $obj[$keys[$i]].TrimEnd() + ' ' }
    }
    $obj | ConvertTo-Json -Depth 3 | Set-Content "$outDir\$lang.json" -Encoding utf8
    Write-Host "[$lang] ok $($keys.Count)"
}

