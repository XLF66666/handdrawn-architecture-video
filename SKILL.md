---
name: handdrawn-architecture-video
description: 将深色/科技风 SVG 架构图重绘为米色纸面手绘风格，生成带模块串行出场与箭头描线/圆点流动动画的自包含 HTML，按用户反馈调整元素细节（碰边框、文字溢出、层级遮挡），最后用 headless Chrome 逐帧 PNG + ffmpeg 导出 4K MP4（bt709/tv 色彩）。适用于比赛/路演视频素材制作：架构图、创新卡片（蓝图+记忆、VibeWorking、多角色配音闭环等）的手绘动画版与 4K 成片。包含可复用环境脚本与四份项目样板（墨塑 video_materials）。
---

# Handdrawn Architecture Video

把"技术图"或"文字描述"变成"手绘动画 4K 视频"的流水线：**（阶段 0：描述/MD → 手绘 SVG）→ SVG 手绘化 → 动画 HTML → 细节调整 → 4K 导出**。每个阶段产出可独立交付的素材，样板见 `examples/`。

## 工作原则

- 每个阶段先读入当前文件确认坐标/结构，再做局部替换（页面和 SVG 文件普遍很大，勿顺手重写）。
- 手绘风格统一：米色纸底 `#FBF7EF`、楷体（`KaiTi/Kaiti SC`）、墨线 `#3A3650`、卡片微旋转 ±0.6°、内侧虚线装饰、手绘折线箭头。
- 内容 100% 保留，只换视觉；删改元素前先与用户确认。

## 阶段 0：从描述 / Markdown 生成手绘 SVG

当输入是文字描述或 MD 文档（产品说明、视频脚本、创意草稿）而非 SVG 时执行。
详细规范见 `references/from-description.md`。

1. 识别输入类型：一句话描述 / Markdown 文档 / 已有 SVG + 补充描述。
2. 内容结构化：提取 Header 信息、大标题、模块卡片（≤6 卡、每卡 ≤5 行）、箭头关系（`→`/列表顺序/循环词）、收尾（价值徽章/落地/标语），输出《元素分组清单》供用户确认。
3. 选布局模板（三列并列 / 横向流水线 / 四步流水线+闭环 / 单列纵向），把内容填入坐标骨架。
4. 按 `handdrawn-style.md` 令牌生成手绘 SVG，logo 用 `scripts/embed_logo.py` 内嵌。
5. 校验：`python scripts/verify_sync.py <svg> <html> <token>... --xml`。

## 阶段 1：SVG 手绘化

把深色科技风 SVG（渐变底/发光卡片/标准 marker 箭头）转为手绘留白版。详细规范见 `references/handdrawn-style.md`。

1. 读入 SVG 全部元素，列出可动画化分组（Header/大标题/各卡片/箭头/标语）。
2. 按手绘规范重写：纸面背景 + 噪点颗粒、白卡 + 墨描边 + 内虚线、楷体文字、手绘箭头（`M.. L.. M.. l-12-9M.. l-12 9` 歪头）、配色沿用语义色但提亮。
3. logo 需内嵌 base64 data URI（`mobile_app/assets/branding/mosu_logo.png` → `data:image/png;base64,...`），SVG 自包含。
   用固化脚本一键完成：`python scripts/embed_logo.py <svg> <png>`（文件只读时先 `attrib -R` 或 `chmod +w`）。
4. 用 `python scripts/verify_sync.py <svg> <html> <token>... --xml` 校验 XML 合法 + 关键文本完整。

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
6. 校验：`python scripts/verify_animation.py <动画.html> [关键内容...]` ——自动检查 HTML 标签配对、
   无重复 class、keyframes 无 `transform:`、圆点 CSS `--d <= SMIL begin`、关键内容完整。

## 阶段 3：细节调整（用户反馈循环）

用户反馈的典型问题与修法（全部为局部单步修改）：

| 症状 | 根因 | 修法 |
|---|---|---|
| 元素碰到边框 | 坐标超出内虚线底 | 整体上移（如 `translate(132 540)`→`(132 520)`，按钮底 < 虚线底） |
| 文字超出框 | 容器太窄/字号太大 | 加宽 rect 或缩字号，右缘 < 框宽 |
| 元素被遮挡/层级错误 | SVG 按文档序绘制，后绘者在上 | 被挡元素移到文档末尾；或修绝对坐标双重偏移 |
| 黑底黑字看不见 | CSS 类优先级高于内联 `fill` | 新增白字类或改用深底浅字 |
| 背景发白 | JPEG 帧 full-range 标记 | 导出用 PNG 帧 + ffmpeg `in_range=full:out_range=tv` + bt709 元数据 |

改完跑验证脚本确认几何（`右缘 < 框右缘`、`底 < 虚线底`、`层级顺序`），
并用 `python scripts/verify_sync.py <svg> <html> <token>... [--absent <token>...]` 确认 SVG 与 HTML 同步。

## 阶段 4：4K 导出

把动画 HTML 渲染为 3840×2160 MP4。脚本见 `scripts/`，规范见 `references/export-4k.md`。

1. 环境：本机 node ≥ 18、ffmpeg（gyan 版）、Chrome `C:/Program Files/Google/Chrome/Application/chrome.exe`；npm 走代理 `--proxy=http://127.0.0.1:7897`（外网直连不可达时），可用环境变量 `MOSU_NPM_PROXY` / `MOSU_CHROME` / `MOSU_WIDTH` / `MOSU_HEIGHT` 覆盖。
2. 一键导出（Windows）：`.\scripts\export_4k.ps1 -Html "..\架构图_动画.html" -Out "架构图_4K.mp4" -DurationMs 14000`；
   跨平台（bash/macOS/Linux）：`./scripts/export_4k.sh <html> <out.mp4> <duration_ms>`；多素材：`python scripts/batch_export.py [start] [end]`。
   脚本自动完成：搭建 `_export/` → 安装 puppeteer-core → 采集 → 合成 → 验证 → 清理。
3. 采集：`node scripts/capture.js <html> <duration_ms> <out_dir>`——**1080p CDP `Page.startScreencast`**（浏览器原生帧流，quality 100，约 24fps；对比逐帧 `page.screenshot` PNG-4K 仅 4.8fps 是卡顿根源），真实时间驱动（SMIL 圆点动画正常）、记录每帧时间戳。
4. 合成：`py scripts/make_concat.py`（按真实时间戳生成 concat 列表）+ ffmpeg（**lanczos 放大 4K** + full→tv 色彩，实测 PSNR 46.9dB 与 4K 原生几乎无差异）：
   ```bash
   ffmpeg -y -f concat -safe 0 -i concat.txt -vf "scale=3840:2160:flags=lanczos,scale=in_range=full:out_range=tv" \
     -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart \
     -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv out_4K.mp4
   ```
5. 验证：`ffprobe` 确认 3840×2160 / yuv420p / color_range=tv / bt709；帧率抽查（帧数÷时长）≈ 20–25fps 流畅；抽帧查背景像素 ≈ `#FBF7EF`（251,247,239）±8；抽 3 帧解码可播放。
6. 12s 内版本：`python scripts/compress_timeline.py <src.html> <dst.html> 0.5`（时间轴 ×0.5），再走同一导出流程。
7. 清理：`rm -rf _diag _export`，MP4 复制到素材根目录。

## 发布前自检

`python scripts/selfcheck.py . [样板目录]` ——一键检查：目录结构完整、SKILL.md frontmatter 合法、
全部 .py/.js/.ps1 脚本语法（含 PowerShell UTF-8 BOM）、examples 引用样板存在性。任何 skill 改动提交前先跑它。

## 验收清单

- [ ] 阶段 0（描述/MD 输入）：元素分组清单与描述一致，布局模板匹配，输出自包含手绘 SVG
- [ ] 手绘 SVG：XML 合法、logo 内嵌、无外部路径依赖
- [ ] 动画 HTML：标签配对、无重复 class、keyframes 无 transform、时序单调、箭头圆点 SMIL 同步
- [ ] 细节调整：无碰边框、无文字溢出、无层级遮挡、背景色正确
- [ ] 4K MP4：3840×2160 / h264 / yuv420p / tv / bt709 / 背景像素 PASS / 可播放

## FAQ（常见问题速查）

详细版见 `README.md`「FAQ」。实战高频问题：

| 问题 | 一句话解法 |
|---|---|
| 导出视频一卡一卡 | 逐帧 screenshot 仅 ~4.8fps，改 1080p CDP screencast + lanczos 放大（~24fps） |
| MP4 背景发白 | JPEG 帧需 `scale=in_range=full:out_range=tv` + bt709/tv 元数据 |
| 元素堆左上角/错位 | keyframes 禁用 `transform:`，只用独立 `translate` 属性 |
| 文字被不透明色块遮挡 | 半透明底色用 `fill-opacity`，不要 `opacity`（selfcheck 自动检测） |
| 文字超框/三卡重叠 | `python scripts/check_overlap.py <html> [--cards]` 自动检查 |
| PowerShell 解析报错 | ps1 需 UTF-8 BOM，勿用 PS7 `??` 运算符 |
| heredoc 后 node SyntaxError | `HTML.replace(/\\/g,'/')` 反斜杠被吃掉，用 edit_file 写入（selfcheck 检测） |
