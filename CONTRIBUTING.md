# Contributing

感谢你愿意为 `handdrawn-architecture-video` 贡献！本 skill 的目标是把
「手绘架构图 → 动画 HTML → 4K 视频」的流水线做得越来越省心。

## 工作流

1. Fork 本仓库，新建分支：`git checkout -b feat/xxx`。
2. 改动前先读 `SKILL.md` 与 `references/`，保持四阶段工作流的一致性。
3. 新增能力时遵循现有结构：
   - 规范/说明 → `references/*.md`
   - 可执行脚本 → `scripts/*.py|js|ps1|sh`（**参数化**：支持环境变量 + 命令行参数，默认值合理）
   - 样例 → `examples/`
4. 提交前跑自检：`python scripts/selfcheck.py .`（需 Node.js、ffmpeg、Chrome 可选）。
5. 提交信息用中文，遵循 Conventional Commits（`feat:` / `fix:` / `docs:` / `refactor:`）。
6. 推送后开 Pull Request。

## 新增脚本的约定

- Python 脚本：`python scripts/xxx.py` 可直接运行，`if __name__ == '__main__'` 返回 0/1。
- JS 脚本：`node --check` 通过；参数从 `process.argv` + `process.env.MOSU_*` 读取。
- PowerShell 脚本：**必须带 UTF-8 BOM**（Windows PowerShell 5.1 无 BOM 中文会解析失败）；
  只用 5.1 兼容语法（不要用 `??` 等 PS7 运算符）。
- 所有脚本在 `selfcheck.py` 中有语法检查项，新增脚本记得补进 `REQUIRED` 或检查列表。

## 踩坑记录

实战中修过的坑已固化为规范（见 `SKILL.md` 阶段 2/3、`references/animation-html.md`）：
CSS transform 覆盖 SVG 定位、dasharray 过小提前露线、opacity 被 CSS 覆盖、
重复 class、g translate 内绝对坐标文字、PNG 帧色彩转换、PS 无 BOM 解析。
遇到新坑时，请把它补进规范与 `examples/README.md` 的对照表。
