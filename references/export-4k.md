# 4K 导出规范（references/export-4k.md）

把动画 HTML 渲染为 **3840×2160 MP4**。脚本模板见 `scripts/`（capture.js / make_concat.py / export_4k.ps1）。

## 环境要求

| 依赖 | 本机路径 / 说明 |
|---|---|
| Node.js | ≥ 18（本机 v24.12.0） |
| npm | 外网直连不可达时加代理：`--proxy=http://127.0.0.1:7897 --https-proxy=http://127.0.0.1:7897` |
| puppeteer-core | `npm install puppeteer-core@24`（连接系统 Chrome，不下载浏览器） |
| Chrome | `C:/Program Files/Google/Chrome/Application/chrome.exe` |
| ffmpeg | gyan 版（`ffmpeg -version` 可用） |

## 流程

### 1. 搭建 `_export/` 工作目录（每次从零）

```bash
mkdir -p _export && cd _export
npm init -y >/dev/null 2>&1
npm install puppeteer-core@24 --proxy=http://127.0.0.1:7897 --https-proxy=http://127.0.0.1:7897
# 放置 capture.js / make_concat.py（见 scripts/）
```

### 2. 逐帧截图（PNG 无损，真实时间驱动）

`node scripts/capture.js`：
- headless Chrome，viewport 3840×2160，`deviceScaleFactor:1`，`--force-device-scale-factor=1 --hide-scrollbars --disable-gpu`
- `page.goto(file://…, waitUntil:'load')` 后 `setTimeout(400)` 等首帧动画
- 循环 `page.screenshot({type:'png'})`，**记录每帧真实时间戳**（`times.push({idx, t})`）——SMIL `animateMotion` 依赖真实时间线，虚拟时钟/加速截图会跳过圆点动画
- 时长取「动画最后延迟 + 0.5s 尾动画 + 1~2s 停留」，INTERVAL=40ms 目标帧间隔
- 输出 `frames/frame_XXXXX.png` + `frames/timestamps.json`

### 3. 合成（按真实时间戳 concat + 色彩转换）

```bash
py scripts/make_concat.py   # 读 timestamps.json → concat.txt（每帧 duration=帧间差，末帧 0.3s）
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -vf "scale=in_range=full:out_range=tv" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  "输出_4K.mp4"
```

**色彩关键**：输入 PNG 为 full-range（RGB），必须显式 `scale=in_range=full:out_range=tv` + bt709 元数据 + `color_range=tv`，否则播放器按 full-range 解释导致整体发白（背景米色变白）。不要用 JPEG 帧（yuvj420p 污染）。

### 4. 验证

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,color_range,color_space \
  -show_entries format=duration,size -of default=noprint_wrappers=1 输出_4K.mp4
# 期望：h264 / 3840×2160 / yuv420p / tv / bt709
```

- 背景像素：抽一帧，四角 + 顶部中央 ≈ `#FBF7EF`(251,247,239) ±6（PIL 检查）。
- 可播放：`ffmpeg -vf "select='eq(n,5)+eq(n,20)+eq(n,40)'"` 抽 3 帧能解码。
- 清理：`rm -rf _diag _export`，MP4 复制到素材根目录。

## 可选变体

- **12s 内版本**：写脚本把所有 `--d:` 与 SMIL `begin` 值 ×0.5（22s→12s），生成 `_12s.html` 再走同一流程；如超出目标时长用 `ffmpeg -t 12` 裁剪。
- **色彩二次确认**：导出后抽帧看米色背景是否发白（PASS 判据：偏差 ≤6）。
