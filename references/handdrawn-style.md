# 手绘风格转换规范（references/handdrawn-style.md）

把深色科技风 SVG（渐变底 / 发光卡片 / 标准 marker 箭头 / 雅黑字体）转为**米色纸面手绘留白版**的统一视觉语言。样板见 `examples/`（墨塑创新一/创新二手绘留白版）。

## 设计令牌（Design Tokens）

| 类别 | 值 |
|---|---|
| 纸面底色 | `#FBF7EF`（米色纸） |
| 墨线主色 | `#3A3650`（卡片/大框描边，3~3.5px） |
| 内虚线装饰 | `#B9ACF2`/`#9BB9ED`/`#D5CCE8` 等浅色，1.5~1.8px，`stroke-dasharray="8 7"` 或 `10 7` |
| 正文墨色 | `#2E2A45` |
| 次要文字 | `#6E6784` |
| 语义色（提亮） | 紫 `#6D5CE0`/`#7C6BF2`、蓝 `#3E6BD8`、青 `#2E9E8B`、琥珀 `#C77D1E`/`#F2A65A` |
| 卡片底 | 白 `#FFF` 或浅色 `#F4F1FF`/`#EFF4FF`/`#FFF6E8`/`#E9F7F3` |
| 字体 | `"KaiTi","Kaiti SC","STKaiti","Microsoft YaHei",serif`；英文用 `"Segoe UI"` 等无衬线 |
| 投影 | `feDropShadow dx=0 dy=12 stdDeviation=14 flood-opacity=.12`（softShadow）；中枢用强投影 |

## 手绘质感要点

1. **卡片微旋转**：大卡 `rotate(-.38 454 410)` / `rotate(.42 1466 410)` 之类的 ±0.2~0.6° 小角度；内卡 `rotate(.25 148 31)`（绕自身中心）。
2. **双线描边**：外框墨线实线 + 内侧 6~8px 偏移的浅色虚线（模拟手绘两笔）。
3. **侧条装饰**：卡片左侧竖条 `M118 299v238`，对应语义色 8px 圆头。
4. **手绘箭头**：不用 marker，直接画歪头折线：
   `M438 432C459 423 472 423 493 432` + 箭头头 `M493 432l-13-10M493 432l-13 10`。
5. **纸面噪点**：若干 `#DCCFB8`/`#E7DDCB` 小圆点 r=1~1.6，opacity .45~.65；角落加波浪涂鸦 `M63 1008q17-13 34 0t35 0`。
6. **logo**：白圆底 + 内嵌 base64 PNG（`data:image/png;base64,...`），不再依赖外部路径。

## 结构骨架

```
纸面背景 + 噪点 + 角落涂鸦
Header（logo + 墨塑 MORPHEUS + 橙色下划线 + INNOVATION 0N 副标题 + 右上便签）
大标题（cap + headline + 下划线 + sub）
主体卡片区（左右大卡 / 中枢 / 步骤卡，按需）
连接箭头 / 反馈回路
价值声明 + 真实 APP 界面落地标签
底部标语（可留白）
```

## 转换步骤

1. 读入原 SVG，盘点所有分组与坐标。
2. 按令牌重写每个元素（保留坐标框架，只换样式：fill/stroke/font/rotate/dasharray）。
3. 字号体系：cap 16px / headline 50px / sub 19px / panelTitle 28px / stepTitle 22px / body 16px / mini 14px。
4. logo 用脚本内嵌 base64（PNG→data URI，替换 image href）。
5. 校验：`xml.dom.minidom.parse()` 合法；关键文本逐个 `in` 断言；无外部路径引用。

## 与动画版同步

手绘 SVG 是静态源，动画 HTML 是运行时版本。**改动画版细节（坐标/文案/删除元素）后必须同步回 SVG**，反之亦然——用同一套坐标值，逐项比对（脚本断言 token 同时存在于两个文件）。
