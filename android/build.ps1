# 硬件管理大师 Android 版构建脚本
# 依赖：Android SDK（platforms/android-36、build-tools/36.0.0）与 SDK 自带 JDK 17
# 不使用 Gradle，直接走 aapt2 -> javac -> d8 -> zipalign -> apksigner，便于离线复现。

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$sdk  = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$bt   = "$sdk\build-tools\36.0.0"
$plat = "$sdk\platforms\android-36\android.jar"
$jdk  = Get-ChildItem "$sdk\jdk-17" -Directory | Select-Object -First 1
$java = "$($jdk.FullName)\bin\java.exe"
$javac = "$($jdk.FullName)\bin\javac.exe"
$keytool = "$($jdk.FullName)\bin\keytool.exe"

foreach ($p in @($bt, $plat, $java, $javac)) {
    if (-not (Test-Path $p)) { throw "缺少构建依赖：$p" }
}

# d8 / apksigner 通过 JAVA_HOME 找 java
$env:JAVA_HOME = $jdk.FullName
$env:PATH = "$($jdk.FullName)\bin;$env:PATH"

$out = "$root\build"
New-Item -ItemType Directory -Force "$out\gen", "$out\classes", "$out\dex" | Out-Null

$versionName = "1.2.0"
$versionCode = 13

Write-Host "[1/7] aapt2 compile"
& "$bt\aapt2.exe" compile --dir "$root\res" -o "$out\res.zip"
if ($LASTEXITCODE -ne 0) { throw "aapt2 compile 失败" }

Write-Host "[2/7] aapt2 link"
& "$bt\aapt2.exe" link -o "$out\unsigned.apk" -I $plat --manifest "$root\AndroidManifest.xml" `
    --java "$out\gen" -R "$out\res.zip" -A "$root\assets" --auto-add-overlay `
    --min-sdk-version 26 --target-sdk-version 34 `
    --version-code $versionCode --version-name $versionName
if ($LASTEXITCODE -ne 0) { throw "aapt2 link 失败" }

# aapt2 在 Windows 上会把 assets 子目录写成反斜杠，Android 读不到；这里重写为标准斜杠
Write-Host "[2.5/7] 规范 assets 路径"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$normTmp = "$out\norm.apk"
$zipIn = [System.IO.Compression.ZipFile]::OpenRead("$out\unsigned.apk")
$fsOut = [System.IO.File]::Create($normTmp)
$zipOut = New-Object System.IO.Compression.ZipArchive($fsOut, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($e in $zipIn.Entries) {
        $name = $e.FullName.Replace('\', '/')
        $level = if ($name -eq 'resources.arsc') {
            [System.IO.Compression.CompressionLevel]::NoCompression
        } else {
            [System.IO.Compression.CompressionLevel]::Optimal
        }
        $ne = $zipOut.CreateEntry($name, $level)
        $in = $e.Open()
        $os = $ne.Open()
        $in.CopyTo($os)
        $os.Dispose()
        $in.Dispose()
    }
} finally {
    $zipIn.Dispose()
    $zipOut.Dispose()
    $fsOut.Dispose()
}
Move-Item $normTmp "$out\unsigned.apk" -Force

Write-Host "[3/7] javac"
$sources = Get-ChildItem "$root\src" -Recurse -Filter *.java | ForEach-Object { $_.FullName }
$gen = Get-ChildItem "$out\gen" -Recurse -Filter *.java -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
& $javac -encoding UTF-8 --release 11 -classpath $plat -d "$out\classes" $sources $gen
if ($LASTEXITCODE -ne 0) { throw "javac 失败" }

Write-Host "[4/7] d8"
$classes = Get-ChildItem "$out\classes" -Recurse -Filter *.class | ForEach-Object { $_.FullName }
& "$bt\d8.bat" --min-api 26 --lib $plat --output "$out\dex" $classes
if ($LASTEXITCODE -ne 0) { throw "d8 失败" }

Write-Host "[5/7] 打包 dex"
Copy-Item "$out\unsigned.apk" "$out\unaligned.apk" -Force
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open("$out\unaligned.apk", "Update")
try {
    $entry = $zip.GetEntry("classes.dex")
    if ($entry) { $entry.Delete() }
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, "$out\dex\classes.dex", "classes.dex", [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
} finally {
    $zip.Dispose()
}

Write-Host "[6/7] zipalign"
& "$bt\zipalign.exe" -f 4 "$out\unaligned.apk" "$out\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "zipalign 失败" }

Write-Host "[7/7] 签名"
$ks = "$root\签名\hardwaremaster.keystore"
if (-not (Test-Path $ks)) {
    New-Item -ItemType Directory -Force "$root\签名" | Out-Null
    & $keytool -genkeypair -keystore $ks -alias hardwaremaster -keyalg RSA -keysize 2048 -validity 10000 `
        -storepass hm2026 -keypass hm2026 -dname "CN=NesonCalo, OU=Hardware Master, O=NesonCalo, L=Tianjin, ST=Tianjin, C=CN" `
        -storetype PKCS12 2>&1 | Out-Null
}
$apk = "$root\build\HardwareMaster-$versionName.apk"
& "$bt\apksigner.bat" sign --ks $ks --ks-pass pass:hm2026 --key-pass pass:hm2026 `
    --min-sdk-version 26 --out $apk "$out\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "apksigner 失败" }

& "$bt\apksigner.bat" verify --print-certs $apk | Select-Object -First 3
Get-Item $apk | Select-Object Name, Length, LastWriteTime

