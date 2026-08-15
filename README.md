# handdrawn-architecture-video

把「技术图」变成「手绘动画 4K 视频」的可复用 AI Agent Skill：**SVG 手绘化 → 动画 HTML → 细节调整 → 4K MP4 导出**，四阶段流水线，纯本地运行（无需云端）。

- 面向：比赛 / 路演 / 产品演示视频素材制作（系统架构图、创新卡片、流程示意图）
- 产物：米色纸面手绘风格 SVG、自包含动画 HTML（纯 CSS + SMIL，双击即播）、3840×2160 H.264 MP4
- 兼容：Claude Code、Codex、AtomCode 等能读取 Skill Markdown 的 agent；支持中文内容

## 快速开始

1. 把本仓库 `handdrawn-architecture-video/` 目录放入 agent 的 skills 目录：

   | Agent | 路径 |
   |---|---|
   | Claude Code | `~/.claude/skills/handdrawn-architecture-video/` |
   | Codex | `~/.codex/skills/handdrawn-architecture-video/` |
   | AtomCode | `~/.atomcode/skills/handdrawn-architecture-video/` |

2. 向 agent 提出需求，例如：
   > 把 `架构图_深色版.svg` 重绘为手绘风格，生成动画 HTML（模块依次出现、箭头有动画），再导出 4K MP4。

3. agent 会按 `SKILL.md` 的四阶段工作流执行，产出 `架构图_4K.mp4`。

## 唤醒方式

skill 安装后会被 agent **自动加载**，无需任何命令；触发方式有两种：

### 1. 自动匹配（推荐）

agent 根据 `SKILL.md` 的 `description` 自动识别，以下类型请求会自动命中本 skill：

- 「把这张 SVG 重绘为**手绘风格** / 手绘留白版」
- 「生成**动画 HTML**，模块依次出现、箭头有描线/圆点流动动画」
- 「导出 **4K MP4** / 高帧率视频」
- 「架构图 / 创新卡片 / 比赛视频素材」
- 「从这段**描述 / MD 文档**生成手绘架构图视频」（阶段 0）

### 2. 显式点名

直接指定 skill 名称，确保被调用：

> 「用 **handdrawn-architecture-video** 处理这个 SVG」
> 「调用手绘动画 skill 走完整流程」

### 安装到其他机器

```bash
git clone https://gitee.com/xie-linfeng-666/handdrawn-architecture-video.git
# 将 handdrawn-architecture-video/ 目录放入目标 agent 的 skills 路径（见上表）
```

### 自检确认安装成功

```bash
cd handdrawn-architecture-video
python scripts/selfcheck.py .    # 一键自检：结构/frontmatter/脚本语法/HTML 坑检测
```

## 四阶段工作流

| 阶段 | 输入 → 输出 | 规范 |
|---|---|---|
| 1. SVG 手绘化 | 深色/科技风 SVG → 米色纸面手绘留白版 SVG | `references/handdrawn-style.md` |
| 2. 动画 HTML | 手绘 SVG → 自包含动画 HTML（模块串行 + 箭头描线/圆点流动） | `references/animation-html.md` |
| 3. 细节调整 | 用户反馈 → 局部修复（碰边框/文字溢出/层级遮挡/色彩） | `SKILL.md` 阶段 3 |
| 4. 4K 导出 | 动画 HTML → 3840×2160 MP4（bt709/tv 色彩） | `references/export-4k.md` |

## 一键导出

```powershell
# Windows（依赖：Node.js ≥18、ffmpeg、Chrome）
cd scripts
.\export_4k.ps1 -Html "..\架构图_动画.html" -Out "架构图_4K.mp4" -DurationMs 14000
```

```bash
# macOS / Linux（bash）
cd scripts
./export_4k.sh ../架构图_动画.html 架构图_4K.mp4 14000
```

脚本自动完成：搭建工作目录 → 安装 puppeteer-core → headless Chrome 逐帧 PNG 截图（真实时间驱动）→ ffmpeg 合成（色彩转换 + bt709 元数据）→ 验证 → 清理。

**环境变量**（均可覆盖默认值）：`MOSU_CHROME`（Chrome 路径）、`MOSU_NPM_PROXY`（npm 代理，默认 `http://127.0.0.1:7897`）、`MOSU_WIDTH` / `MOSU_HEIGHT`（分辨率，默认 3840×2160）、`MOSU_DURATION_MS`（截图时长）。

## 常用脚本速查

| 脚本 | 用途 |
|---|---|
| `scripts/embed_logo.py` | logo PNG → base64 data URI 内嵌进 SVG（自包含） |
| `scripts/compress_timeline.py` | 时间轴 ×scale 压缩（如 0.5 → 12s 版） |
| `scripts/verify_animation.py` | 动画 HTML 验收（标签配对/重复 class/keyframes/圆点时序/关键内容） |
| `scripts/verify_sync.py` | SVG ↔ 动画 HTML 细节同步校验 |
| `scripts/selfcheck.py` | 发布前一键自检（结构/frontmatter/全部脚本语法/样板存在性） |
| `scripts/capture.js` | headless Chrome 3840×2160 PNG 逐帧截图（真实时间驱动） |
| `scripts/make_concat.py` | 按真实时间戳生成 ffmpeg concat 列表 |
| `scripts/export_4k.ps1` / `.sh` | 一键导出 4K MP4（Windows / 跨平台） |

## 目录结构

```
handdrawn-architecture-video/
├── SKILL.md                 # Skill 入口：四阶段工作流 + 验收清单
├── references/
│   ├── handdrawn-style.md   # 手绘风格设计令牌与转换规范
│   ├── animation-html.md    # 动画 HTML 基元、串行时序、箭头动画、踩坑清单
│   └── export-4k.md         # 4K 导出环境、ffmpeg 命令、验证标准
├── scripts/
│   ├── embed_logo.py        # logo 内嵌 base64（SVG 自包含）
│   ├── compress_timeline.py # 时间轴压缩（12s 版）
│   ├── verify_animation.py  # 动画 HTML 验收自检
│   ├── verify_sync.py       # SVG↔HTML 同步校验
│   ├── selfcheck.py         # 发布前一键自检
│   ├── capture.js           # headless Chrome 逐帧 PNG 截图（参数化）
│   ├── make_concat.py       # 按真实时间戳生成 ffmpeg concat 列表
│   ├── export_4k.ps1        # 一键导出（Windows）
│   └── export_4k.sh         # 一键导出（bash/macOS/Linux）
└── examples/
    ├── README.md            # 生产样板清单（墨塑项目）+ 踩坑对照表
    └── minimal-demo.html    # 最小自包含动画样板（克隆即可打开）
```

## 关键经验（已固化为规范）

- **CSS `transform` 会覆盖 SVG `transform` 定位**：动画 keyframes 禁用 `transform:`，只用独立 `translate` 属性，否则带定位的 `<g>` 全部堆到左上角。
- **`stroke-dasharray` 必须 ≥ 最大框周长**（如 5400），否则描线动画开始前框线提前露出。
- **动画类元素上的 `opacity` 会被 CSS 覆盖成不透明**：胶囊/图标底色用 `fill-opacity`。
- **一个元素只能有一个 `class` 属性**；`<g translate>` 内禁止放绝对坐标文字（双重偏移）。
- **MP4 背景发白**：用 PNG 帧 + ffmpeg `scale=in_range=full:out_range=tv` + bt709 元数据，不要用 JPEG 帧。
- **PowerShell 脚本需 UTF-8 BOM**，否则 Windows PowerShell 5.1 中文解析报错。

## 验证标准

- 手绘 SVG：XML 合法、logo 内嵌 base64、无外部路径依赖
- 动画 HTML：标签配对、无重复 class、keyframes 无 `transform:`、圆点 CSS `--d ≤ SMIL begin`、模块时序单调
- 4K MP4：`ffprobe` 显示 h264 / 3840×2160 / yuv420p / color_range=tv / bt709；背景像素 ≈ `#FBF7EF` ±6；抽帧可播放

## FAQ

### 导出的视频为什么一卡一卡？

逐帧 `page.screenshot()` 是串行瓶颈：4K PNG 每帧约 210ms，实际仅 ~4.8fps。
改用 **1080p CDP `Page.startScreencast` + lanczos 放大 4K**（`scripts/capture.js`）：~24fps，
清晰度 PSNR 46.9dB（与 4K 原生几乎无差异）。逐帧截图方案已弃用。

### MP4 背景发白/颜色不对？

JPEG 帧是 full-range（yuvj420p），播放器按 tv 解释会整体发白。
合成时**必须**加 `-vf "scale=in_range=full:out_range=tv"` + `-colorspace bt709
-color_primaries bt709 -color_trc bt709 -color_range tv`（`export_4k.ps1/.sh` 已内置）。

### 动画里元素堆到左上角/错位？

CSS `transform` 会覆盖 SVG 的 `transform="translate(...)"` 定位。
动画 keyframes 禁止写 `transform:`，只用独立属性 `translate`（如 `translate:0 12px → 0 0`）。

### 卡片/文字被不透明色块遮挡？

动画类元素（fade/fu/fillin/draw）上的 `opacity=".12"` 会被 CSS opacity 动画覆盖成不透明。
半透明底色请用 `fill-opacity=".12"`（`selfcheck.py` 会自动检测这类坑）。

### 文字超出卡片/按钮边框？

估算文字宽度（中文=字号px，ASCII≈0.55×字号）是否超过容器右缘；
或加宽容器、缩小字号。可用 `python scripts/check_overlap.py <动画.html>` 自动检查（含 `--cards` 三卡重叠模式）。

### Windows 上 PowerShell 脚本解析报错？

`export_4k.ps1` 必须带 **UTF-8 BOM**（否则 PowerShell 5.1 按 GBK 读中文乱码报语法错）；
且只用 5.1 兼容语法（不要用 `??` 等 PS7 运算符）。

### 脚本里 heredoc 写入后 node 报 SyntaxError？

heredoc/shell 写入会吃掉 `\\` 反斜杠。`capture.js` 的 `HTML.replace(/\\/g, '/')`
若变成 `/\/g` 会报 `missing ) after argument list`——用 `edit_file` 写入或用 `selfcheck.py` 检测。

## License

[MIT](LICENSE)
