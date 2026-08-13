#!/usr/bin/env bash
# ============================================================
# export_4k.sh — 一键导出 4K MP4（bash/macOS/Linux 版）
#
# 用法:
#   ./export_4k.sh [html] [out.mp4] [duration_ms]
#   例: ./export_4k.sh ../架构图_动画.html 架构图_4K.mp4 14000
#
# 环境变量（均可覆盖）:
#   MOSU_CHROME       Chrome 可执行文件路径
#   MOSU_NPM_PROXY    npm 代理（外网不可达时）
#   MOSU_WIDTH/HEIGHT 导出分辨率（默认 3840x2160）
#   MOSU_DURATION_MS  截图时长（默认 14000）
#
# 依赖: node >= 18、python3、ffmpeg、Chrome
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="${1:-../架构图_动画.html}"
OUT="${2:-架构图_动画_4K.mp4}"
DURATION_MS="${3:-${MOSU_DURATION_MS:-14000}}"

WORK_DIR="$SCRIPT_DIR/_export"
NPM_PROXY="${MOSU_NPM_PROXY:-http://127.0.0.1:7897}"
CHROME="${MOSU_CHROME:-}"
WIDTH="${MOSU_WIDTH:-3840}"
HEIGHT="${MOSU_HEIGHT:-2160}"
export MOSU_WIDTH MOSU_HEIGHT
[ -n "$CHROME" ] && export MOSU_CHROME

# ---------- 1. 搭建工作目录 + 安装 puppeteer-core ----------
mkdir -p "$WORK_DIR"
if [ ! -d "$WORK_DIR/node_modules/puppeteer-core" ]; then
  echo "[1/4] 安装 puppeteer-core（代理 $NPM_PROXY）..."
  ( cd "$WORK_DIR" && npm init -y >/dev/null 2>&1 || true )
  ( cd "$WORK_DIR" && npm install puppeteer-core@24 \
      --proxy="$NPM_PROXY" --https-proxy="$NPM_PROXY" )
fi

# ---------- 2. 逐帧截图 ----------
echo "[2/4] 逐帧截图 $HTML（${DURATION_MS} ms, ${WIDTH}x${HEIGHT} PNG）..."
( cd "$WORK_DIR" && node "$SCRIPT_DIR/capture.js" "$HTML" "$DURATION_MS" frames )

# ---------- 3. 合成 4K MP4（bt709/tv 色彩） ----------
echo "[3/4] 合成 4K MP4..."
python3 "$SCRIPT_DIR/make_concat.py" "$WORK_DIR/frames" "$WORK_DIR/concat.txt"
ffmpeg -y -f concat -safe 0 -i "$WORK_DIR/concat.txt" \
    -vf "scale=in_range=full:out_range=tv" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
    "$SCRIPT_DIR/$OUT"

# ---------- 4. 验证 + 清理 ----------
echo "[4/4] 验证..."
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,color_range \
    -show_entries format=duration -of default=noprint_wrappers=1 "$SCRIPT_DIR/$OUT"
rm -rf "$WORK_DIR"
echo "完成: $OUT"
