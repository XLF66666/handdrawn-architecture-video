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

## 四阶段工作流

| 阶段 | 输入 → 输出 | 规范 |
|---|---|---|
| 1. SVG 手绘化 | 深色/科技风 SVG → 米色纸面手绘留白版 SVG | `references/handdrawn-style.md` |
| 2. 动画 HTML | 手绘 SVG → 自包含动画 HTML（模块串行 + 箭头描线/圆点流动） | `references/animation-html.md` |
| 3. 细节调整 | 用户反馈 → 局部修复（碰边框/文字溢出/层级遮挡/色彩） | `SKILL.md` 阶段 3 |
| 4. 4K 导出 | 动画 HTML → 3840×2160 MP4（bt709/tv 色彩） | `references/export-4k.md` |

## 一键导出

```powershell
# 依赖：Node.js ≥18、ffmpeg、Chrome
cd scripts
.\export_4k.ps1 -Html "..\架构图_动画.html" -Out "架构图_4K.mp4" -DurationMs 14000
```

脚本自动完成：搭建工作目录 → 安装 puppeteer-core → headless Chrome 逐帧 PNG 截图（真实时间驱动）→ ffmpeg 合成（色彩转换 + bt709 元数据）→ 验证 → 清理。

## 目录结构

```
handdrawn-architecture-video/
├── SKILL.md                 # Skill 入口：四阶段工作流 + 验收清单
├── references/
│   ├── handdrawn-style.md   # 手绘风格设计令牌与转换规范
│   ├── animation-html.md    # 动画 HTML 基元、串行时序、箭头动画、踩坑清单
│   └── export-4k.md         # 4K 导出环境、ffmpeg 命令、验证标准
├── scripts/
│   ├── capture.js           # headless Chrome 3840×2160 PNG 逐帧截图（参数化）
│   ├── make_concat.py       # 按真实时间戳生成 ffmpeg concat 列表
│   └── export_4k.ps1        # 一键导出（装依赖+截图+合成+验证+清理）
└── examples/README.md       # 项目样板清单（手绘 SVG / 动画 HTML / 4K MP4）
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

## License

[MIT](LICENSE)
