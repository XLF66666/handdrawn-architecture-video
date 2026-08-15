# ============================================================
# export_4k.ps1 — 一键导出 4K MP4（含环境搭建 + 截图 + 合成 + 验证）
#
# 用法:
#   .\export_4k.ps1 -Html "..\架构图_动画.html" -Out "架构图_4K.mp4" [-DurationMs 14000]
#
# 依赖: Node.js、ffmpeg、Chrome（路径见 $Chrome 或环境变量 MOSU_CHROME）
# 外网不可达时 npm 走代理 7897（可改 $NpmProxy）
# ============================================================
param(
    [string]$Html = "..\架构图_动画.html",   # 动画 HTML（相对本脚本所在目录）
    [string]$Out = "架构图_动画_4K.mp4",     # 输出 MP4 文件名
    [int]$DurationMs = 0                      # 截图时长（0 = 用环境变量/默认）
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkDir = Join-Path $ScriptDir "_export"

# ---- 环境变量可覆盖（默认值；兼容 Windows PowerShell 5.1）----
if (-not $DurationMs) {
    $envDur = $env:MOSU_DURATION_MS
    if ($envDur) { $DurationMs = [int]$envDur } else { $DurationMs = 14000 }
}
$NpmProxy = $env:MOSU_NPM_PROXY;            if (-not $NpmProxy) { $NpmProxy = "http://127.0.0.1:7897" }
$Chrome = $env:MOSU_CHROME;                 if (-not $Chrome) { $Chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe" }
$Width = $env:MOSU_WIDTH;                   if (-not $Width) { $Width = 1920 }
$Height = $env:MOSU_HEIGHT;                 if (-not $Height) { $Height = 1080 }
# 透传给 capture.js（MOSU_WIDTH/HEIGHT/CHROME）
$env:MOSU_WIDTH = $Width; $env:MOSU_HEIGHT = $Height; $env:MOSU_CHROME = $Chrome

# ---------- 1. 搭建工作目录 + 安装 puppeteer-core ----------
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
Push-Location $WorkDir
if (-not (Test-Path "node_modules\puppeteer-core")) {
    Write-Host "[1/4] 安装 puppeteer-core（代理 $NpmProxy）..."
    if (-not (Test-Path "package.json")) { npm init -y | Out-Null }
    npm install puppeteer-core@24 --proxy=$NpmProxy --https-proxy=$NpmProxy
}
Pop-Location

# ---------- 2. 逐帧截图 ----------
Write-Host "[2/4] 逐帧截图 $Html（$DurationMs ms, ${Width}x${Height} PNG）..."
Push-Location $WorkDir
node (Join-Path $ScriptDir "capture.js") $Html $DurationMs frames
Pop-Location

# ---------- 3. 合成 4K MP4（1080p 采集 → lanczos 放大 4K，bt709/tv 色彩） ----------
Write-Host "[3/4] 合成 4K MP4（lanczos 放大）..."
python (Join-Path $ScriptDir "make_concat.py") (Join-Path $WorkDir "frames") (Join-Path $WorkDir "concat.txt")
ffmpeg -y -f concat -safe 0 -i (Join-Path $WorkDir "concat.txt") `
    -vf "scale=3840:2160:flags=lanczos,scale=in_range=full:out_range=tv" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart `
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv `
    (Join-Path $ScriptDir $Out)
if ($LASTEXITCODE -ne 0) { throw "ffmpeg 合成失败" }

# ---------- 4. 验证 + 清理 ----------
Write-Host "[4/4] 验证..."
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,color_range `
    -show_entries format=duration -of default=noprint_wrappers=1 (Join-Path $ScriptDir $Out)
Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue
Write-Host "完成: $Out"
