# 4K 导出规范（references/export-4k.md）

把动画 HTML 渲染为 **3840×2160 MP4**。脚本模板见 `scripts/`（capture.js / make_concat.py / batch_export.py / export_4k.ps1 / export_4k.sh）。

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
# 放置 capture.js / make_concat.py / batch_export.py（见 scripts/）
```

### 2. 采集（1080p CDP screencast，真实时间驱动，约 24fps）

`node scripts/capture.js <html> <duration_ms> <out_dir>`：
- **CDP `Page.startScreencast`**：浏览器原生按目标帧率输出 JPEG 帧流（quality 100，1920×1080 采集），配合 `Page.screencastFrameAck` 确认、按真实时间节流——SMIL `animateMotion` 依赖真实时间线，浏览器原生采集不受影响。
- 实测帧率对比（同一动画）：

| 方案 | 帧率 | 说明 |
|---|---|---|
| 逐帧 `page.screenshot` PNG-4K | **4.8fps** | 卡顿根源（每帧 ~210ms 串行瓶颈） |
| 逐帧 screenshot JPEG-4K | 6.5fps | 仍卡 |
| 4K 原生 screencast | 19.3fps | 尚可 |
| **1080p screencast + lanczos 放大 4K** | **~24fps** | **推荐**：清晰度 PSNR 46.9dB / 锐度比 1.01（与 4K 原生几乎无差异） |

- 时长取「动画最后延迟 + 0.5s 尾动画 + 1~2s 停留」。
- 输出 `frames/frame_XXXXX.jpg` + `frames/timestamps.json`。
- 环境变量：`MOSU_CHROME` / `MOSU_WIDTH` / `MOSU_HEIGHT`（默认 1920×1080）/ `MOSU_JPEG_QUALITY`（默认 100）。

### 3. 合成（按真实时间戳 concat + lanczos 放大 4K + 色彩转换）

```bash
py scripts/make_concat.py   # 读 timestamps.json → concat.txt（每帧 duration=帧间差，末帧 0.3s）
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -vf "scale=3840:2160:flags=lanczos,scale=in_range=full:out_range=tv" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  "输出_4K.mp4"
```

**关键点**：
- **lanczos 放大**：1080p 采集帧用 `scale=3840:2160:flags=lanczos` 高质量放大到 4K（实测 PSNR 46.9dB，视觉无差异）。
- **色彩转换**：JPEG 帧为 full-range（yuvj420p），必须 `scale=in_range=full:out_range=tv` + bt709 元数据 + `color_range=tv`，否则播放器按 full-range 解释导致整体发白（背景米色变白）。

### 4. 批量导出（多素材）

`py scripts/batch_export.py [start_idx] [end_idx]`：按 `ASSETS` 清单批量执行「采集 → concat → 合成」。默认导出全部；传下标可分批（如 `0 5`、`5 10`）。

### 5. 验证

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,color_range,color_space \
  -show_entries format=duration,size -of default=noprint_wrappers=1 输出_4K.mp4
# 期望：h264 / 3840×2160 / yuv420p / tv / bt709
```

- 帧率抽查：`ffprobe -count_frames -select_streams v -show_entries stream=nb_read_frames` → 帧数 ÷ 时长 ≈ 20–25fps（流畅）。
- 背景像素：抽一帧，四角 + 顶部中央 ≈ `#FBF7EF`(251,247,239) ±8（PIL 检查）。
- 可播放：`ffmpeg -vf "select='eq(n,5)+eq(n,20)+eq(n,40)'"` 抽 3 帧能解码。
- 清理：`rm -rf _diag _export`，MP4 复制到素材根目录。

## 可选变体

- **12s 内版本**：写脚本把所有 `--d:` 与 SMIL `begin` 值 ×0.5（22s→12s），生成 `_12s.html` 再走同一流程；如超出目标时长用 `ffmpeg -t 12` 裁剪。
- **更高帧率（30fps+）**：screencast 已接近浏览器节流上限；如需更高可降采集到 1080p 以下或接受少量 JPEG 压缩，通常 24fps 在手绘动画已流畅。
- **色彩二次确认**：导出后抽帧看米色背景是否发白（PASS 判据：偏差 ≤8）。
