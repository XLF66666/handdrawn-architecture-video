# 动画 HTML 规范（references/animation-html.md）

把手绘 SVG 转成**自包含动画 HTML**（纯 CSS + SMIL，零依赖，双击即播，刷新重播）。样板见 `examples/`（墨塑架构图 / 创新一 / 创新二动画 HTML）。

## 文件骨架

```html
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>…</title><style>…动画基元…</style></head>
<body><div class="stage">
<svg viewBox="0 0 1920 1080" xmlns="…">
  …纸面背景（常显）…
  …各分组元素（带 class + style="--d:X.XXs"）…
</svg>
<div class="legend">…约 N 秒一轮…</div><div class="loop-note">刷新页面重新播放</div>
</div></body></html>
```

## 动画基元（CSS 模板）

```css
.draw   { stroke-dasharray:5400; stroke-dashoffset:5400; animation:draw .8s ease-in-out var(--d,0s) forwards; }
.draw-sm{ stroke-dasharray:5400; stroke-dashoffset:5400; animation:draw .7s ease-in-out var(--d,0s) forwards; }
@keyframes draw { to { stroke-dashoffset:0; } }
.fillin { opacity:0; animation:fillin .5s ease-out var(--d,0s) forwards; }
@keyframes fillin { to { opacity:1; } }
.fu     { opacity:0; animation:fu .5s ease-out var(--d,0s) forwards; }
@keyframes fu { from { opacity:0; translate:0 12px; } to { opacity:1; translate:0 0; } }  /* 独立 translate */
.up     { opacity:0; animation:up .6s ease-out var(--d,0s) forwards; }
@keyframes up { from { opacity:0; translate:0 40px; } to { opacity:1; translate:0 0; } }  /* 大卡下浮上入 */
.fade   { opacity:0; animation:fade .5s ease-out var(--d,0s) forwards; }
@keyframes fade { to { opacity:1; } }
.dot    { opacity:0; animation:dotIn .3s linear var(--d,0s) forwards; }
@keyframes dotIn { to { opacity:1; } }
```

## 出场逻辑（用户核心要求）

- **模块串行**：前一个模块完全出现后，再出下一个；模块间有箭头 → 先出箭头（描线 + 圆点流动），再出下一个模块；无箭头 → 直接按逻辑衔接。
- 时间轴示例（约 12s 一轮）：Header 0.3 → 大标题 1.4 → 卡1 2.4 → 箭头 3.8 → 中枢 4.3 → 卡2 5.0 → 箭头 → 卡3 … → 反馈回路 9.5 → 价值声明 10.2 → 落地 10.4 → 标语 11.2。
- 用 `--d:X.XXs` 精确控延迟；同组元素用相同延迟实现"同时出现"（如左右两卡都是 3.8s）。

## 箭头动画（描线 + 圆点流动）

```html
<path class="draw-sm" style="--d:3.8s" d="M438 432C459 423 472 423 493 432" fill="none" stroke="#6D5CE0" stroke-width="4" stroke-linecap="round"/>
<path class="fade" style="--d:4.1s" d="M493 432l-13-10M493 432l-13 10" fill="none" stroke="#6D5CE0" stroke-width="4" stroke-linecap="round"/>
<circle class="dot" style="--d:3.85s" cx="440" cy="431" r="7" fill="#6D5CE0">
  <animateMotion dur="0.7s" begin="3.9s" repeatCount="1" path="M0 0 C21 -9 34 -9 55 0"/>
</circle>
```
约束：圆点 CSS `--d` ≤ SMIL `begin`（先出现再流动）；`animateMotion` 的 `path` 与箭头路径方向一致；`repeatCount="1"` 单次（刷新重播）。

## 不可违背的坑（踩过全部修复）

1. **CSS `transform` 覆盖 SVG `transform` 定位** → keyframes 禁用 `transform:`，只用独立 `translate` 属性（`translate:0 12px → 0 0`）。否则所有带 `transform="translate(x y)"` 的 `<g>` 堆到左上角。
2. **`stroke-dasharray` 必须 ≥ 最大框周长**：外舞台主框 2×(1760+860)=5240、虚线框 2×(1744+844)=5176 → 统一 5400。太小则动画前框线提前露出。
3. **动画类元素上的 `opacity=".12"` 被 CSS 覆盖** → 胶囊/图标底用 `fill-opacity=".12"`（独立于元素 opacity 动画），否则背景变不透明挡住文字。
4. **一个元素只能一个 `class` 属性** → `class="fu" style="…" class="sub"` 后一个失效，合并 `class="fu sub"`。
5. **`<g transform="translate(x y)">` 内禁止绝对坐标文字**：`<text x="960" y="534">` 在 translate 容器内会双重偏移跑出画面 → 去掉 `<g>` 的 translate，rect/text 都用绝对坐标（或文字用相对坐标）。
6. 文字超出边框：加宽容器或缩字号（15→13），断言 `文字右缘 < 框右缘`。

## 验证脚本要点

- HTMLParser 标签配对（自闭合标签不计闭合）。
- 无重复 class：`re.findall(r'class="[^"]*"[^>]*class="')` 为空。
- keyframes 无 `transform:`。
- 圆点 `--d ≤ begin`；模块开始时间单调递增。
- 关键文本全部 `in` 断言。
