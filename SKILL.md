---
name: handdrawn-architecture-video
description: 将深色/科技风 SVG 架构图重绘为米色纸面手绘风格，生成带模块串行出场与箭头描线/圆点流动动画的自包含 HTML，按用户反馈调整元素细节（碰边框、文字溢出、层级遮挡），最后用 headless Chrome 逐帧 PNG + ffmpeg 导出 4K MP4（bt709/tv 色彩）。适用于比赛/路演视频素材制作：架构图、创新卡片（蓝图+记忆、VibeWorking、多角色配音闭环等）的手绘动画版与 4K 成片。包含可复用环境脚本与四份项目样板（墨塑 video_materials）。
---

# Handdrawn Architecture Video

把一张"技术图"变成"手绘动画 4K 视频"的四阶段流水线：**SVG 手绘化 → 动画 HTML → 细节调整 → 4K 导出**。每个阶段产出可独立交付的素材，样板见 `examples/`。

## 工作原则

- 每个阶段先读入当前文件确认坐标/结构，再做局部替换（页面和 SVG 文件普遍很大，勿顺手重写）。
- 手绘风格统一：米色纸底 `#FBF7EF`、楷体（`KaiTi/Kaiti SC`）、墨线 `#3A3650`、卡片微旋转 ±0.6°、内侧虚线装饰、手绘折线箭头。
- 内容 100% 保留，只换视觉；删改元素前先与用户确认。

## 阶段 1：SVG 手绘化

把深色科技风 SVG（渐变底/发光卡片/标准 marker 箭头）转为手绘留白版。详细规范见 `references/handdrawn-style.md`。

1. 读入 SVG 全部元素，列出可动画化分组（Header/大标题/各卡片/箭头/标语）。
2. 按手绘规范重写：纸面背景 + 噪点颗粒、白卡 + 墨描边 + 内虚线、楷体文字、手绘箭头（`M.. L.. M.. l-12-9M.. l-12 9` 歪头）、配色沿用语义色但提亮。
3. logo 需内嵌 base64 data URI（`mobile_app/assets/branding/mosu_logo.png` → `data:image/png;base64,...`），SVG 自包含。
4. 用 `python` 校验 XML 合法 + 关键文本完整。

## 阶段 2：动画 HTML

把手绘 SVG 转为自包含 HTML（纯 CSS + SMIL，零依赖，双击即播，刷新重播）。详细规范见 `references/animation-html.md`。

1. 结构：`<!DOCTYPE html>` + `<style>`（动画基元）+ `<svg>` 内联全部元素 + 页脚 legend。
2. 动画基元：`.draw/.draw-sm`（描线）、`.fillin`（填充淡入）、`.fu`（淡入上浮 12px）、`.up`（大卡下浮上入 40px）、`.fade`（纯淡入）、`.dot`（圆点+SMIL `animateMotion`）。
3. 出场逻辑：**模块串行**——前一个模块完全出现后，有箭头先出箭头（描线+圆点流动），再出下一个；无箭头按逻辑衔接。用 `--d:X.XXs` 控制延迟。
4. 箭头动画：主线箭头 4 条 + 反馈回路 1 条，全部「描线 + 圆点沿路径流动」（`<circle class="dot">` + `<animateMotion dur begin repeatCount="1">`）。
5. 关键坑（务必遵守，否则元素错位/遮挡/颜色丢失）：
   - **CSS `transform` 会覆盖 SVG `transform="translate(...)"` 定位**：动画类 keyframes 只用独立属性 `translate`/`opacity`/`stroke-dashoffset`，禁止 `transform:`。
   - **`stroke-dasharray` 必须 ≥ 最大框周长**（外舞台主框 5240/虚线框 5176 → 用 5400），否则动画前框线提前露出。
   - **动画类元素（fade/fu/fillin/draw）上的 `opacity=".12"` 会被 CSS 覆盖成不透明**：改用 `fill-opacity=".12"`。
   - **一个元素只能有一个 `class` 属性**：`class="fu" ... class="sub"` 后者失效，需合并为 `class="fu sub"`。
   - **`<g transform="translate(...)">` 内不要放绝对坐标文字**：文字用相对坐标或把 `<g>` 去掉直接绝对定位，否则双重偏移跑出画面。
   - 文字超出边框：加宽容器或缩小字号（如 15→13）。
6. 校验：HTML 标签配对、无重复 class、keyframes 无 `transform:`、圆点 CSS `--d <= SMIL begin`、模块时序单调。

## 阶段 3：细节调整（用户反馈循环）

用户反馈的典型问题与修法（全部为局部单步修改）：

| 症状 | 根因 | 修法 |
|---|---|---|
| 元素碰到边框 | 坐标超出内虚线底 | 整体上移（如 `translate(132 540)`→`(132 520)`，按钮底 < 虚线底） |
| 文字超出框 | 容器太窄/字号太大 | 加宽 rect 或缩字号，右缘 < 框宽 |
| 元素被遮挡/层级错误 | SVG 按文档序绘制，后绘者在上 | 被挡元素移到文档末尾；或修绝对坐标双重偏移 |
| 黑底黑字看不见 | CSS 类优先级高于内联 `fill` | 新增白字类或改用深底浅字 |
| 背景发白 | JPEG 帧 full-range 标记 | 导出用 PNG 帧 + ffmpeg `in_range=full:out_range=tv` + bt709 元数据 |

改完跑验证脚本确认几何（`右缘 < 框右缘`、`底 < 虚线底`、`层级顺序`）。

## 阶段 4：4K 导出

把动画 HTML 渲染为 3840×2160 MP4。脚本见 `scripts/`，规范见 `references/export-4k.md`。

1. 环境：本机 node ≥ 18、ffmpeg（gyan 版）、Chrome `C:/Program Files/Google/Chrome/Application/chrome.exe`；npm 走代理 `--proxy=http://127.0.0.1:7897`（外网直连不可达时）。
2. 重装依赖：`cd _export && npm init -y && npm install puppeteer-core@24 --proxy=... --https-proxy=...`（每次从零搭建，装完即用）。
3. 逐帧截图：`node scripts/capture.js`——headless Chrome 3840×2160、`page.screenshot({type:'png'})` 无损、真实时间驱动（SMIL 圆点动画必须真实时间，虚拟时钟会跳过）、记录每帧时间戳。
4. 合成：`py scripts/make_concat.py`（按真实时间戳生成 concat 列表）+ ffmpeg：
   ```bash
   ffmpeg -y -f concat -safe 0 -i concat.txt -vf "scale=in_range=full:out_range=tv" \
     -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart \
     -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv out_4K.mp4
   ```
5. 验证：`ffprobe` 确认 3840×2160 / yuv420p / color_range=tv / bt709；抽帧查背景像素 ≈ `#FBF7EF`（251,247,239）±6；抽 3 帧解码可播放。
6. 清理：`rm -rf _diag _export`，MP4 复制到素材根目录。

## 验收清单

- [ ] 手绘 SVG：XML 合法、logo 内嵌、无外部路径依赖
- [ ] 动画 HTML：标签配对、无重复 class、keyframes 无 transform、时序单调、箭头圆点 SMIL 同步
- [ ] 细节调整：无碰边框、无文字溢出、无层级遮挡、背景色正确
- [ ] 4K MP4：3840×2160 / h264 / yuv420p / tv / bt709 / 背景像素 PASS / 可播放
