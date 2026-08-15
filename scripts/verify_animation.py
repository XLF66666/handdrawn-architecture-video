#!/usr/bin/env python3
"""verify_animation.py — 动画 HTML 验收自检

用法:
    python verify_animation.py <动画.html> [关键内容...]

检查项:
    1. HTMLParser 标签配对（自闭合标签不计）
    2. 无重复 class 属性（class="..." ... class="..."）
    3. keyframes 无 CSS transform:（会覆盖 SVG transform 定位）
    4. 圆点 CSS --d <= SMIL begin（先出现再流动）
    5. 圆点时序逻辑：SMIL begin ≥ 前一条箭头描线完成（draw/draw-sm --d+0.7s）
       且 ≥ 后一个目标元素出现完成（up --d+0.6s / fu --d+0.5s）
       —— 圆点须等箭头画完、目标出现后才流动（否则提前乱飞）
    6. 关键内容完整（可选参数逐一断言）

退出码 0 = 全部通过；1 = 有失败。
"""
import re
import sys
from html.parser import HTMLParser


def check(src: str) -> list[str]:
    errors = []

    # 1) 标签配对
    class P(HTMLParser):
        def __init__(self):
            super().__init__(); self.stack = []; self.errs = []
        def handle_starttag(self, tag, attrs):
            if tag not in ('meta', 'link', 'br', 'path', 'rect', 'circle', 'line', 'image', 'tspan', 'animateMotion'):
                self.stack.append(tag)
        def handle_endtag(self, tag):
            if tag in ('meta', 'link', 'br', 'path', 'rect', 'circle', 'line', 'image', 'tspan', 'animateMotion'):
                return
            if not self.stack:
                self.errs.append(f'extra </{tag}>'); return
            top = self.stack.pop()
            if top != tag:
                self.errs.append(f'mismatch </{tag}> vs <{top}>')
    p = P(); p.feed(src)
    if p.errs or p.stack:
        errors.append(f'HTML 标签不配对: {p.errs or p.stack}')

    # 2) 无重复 class
    dups = re.findall(r'class="[^"]*"[^>]*class="', src)
    if dups:
        errors.append(f'存在重复 class 属性: {dups[:3]}')

    # 3) 动画基元类的 keyframes 无 CSS transform（div 卡片动画 c1/c2/c3 等不受此限）
    m = re.search(r'<style>(.*?)</style>', src, re.S)
    css = m.group(1) if m else ''
    for kf in re.finditer(r'@keyframes\s+(\w+)\s*\{([^}]*)\}', css):
        name = kf.group(1)
        if name in ('draw', 'draw-sm', 'fillin', 'fu', 'up', 'fade', 'dot', 'barGrow', 'bar-grow') \
                and 'transform:' in kf.group(2):
            errors.append(f'动画基元 keyframes {name} 含 CSS transform:（会覆盖 SVG 定位）')

    # 4) 圆点 CSS --d <= SMIL begin（先出现再流动）
    dots = re.findall(r'class="dot" style="--d:([\d.]+)s"[^>]*>[\s\S]*?<animateMotion dur="[\d.]+s" begin="([\d.]+)s"', src)
    for d, b in dots:
        if float(d) > float(b):
            errors.append(f'圆点 CSS --d={d}s > SMIL begin={b}s')

    # 5) 圆点时序逻辑：出现 --d 与流动 begin 均 ≥ 前箭头描线完成，且 begin ≥ 后目标出现完成
    #    只统计 <path> 上的箭头描线（排除 rect 虚线框的 draw-sm），目标取最近的 up/fu/fade/fillin
    events = []
    for m in re.finditer(
            r'<path class="(draw-sm|draw)" style="--d:([\d.]+)s"|'
            r'class="(up|fu|fade|fillin|bar-grow)" style="--d:([\d.]+)s"', src):
        if m.group(1):
            kind, d = m.group(1), float(m.group(2))
            dur = 0.7
        else:
            kind, d = m.group(3), float(m.group(4))
            dur = 0.6 if kind in ('up', 'bar-grow') else 0.5
        events.append((m.start(), kind, d, dur))
    for m in re.finditer(
            r'<circle class="dot" style="--d:([\d.]+)s"[^>]*>[\s\S]*?<animateMotion dur="[\d.]+s" begin="([\d.]+)s"',
            src):
        d_css, b = float(m.group(1)), float(m.group(2))
        pos = m.start()
        # 前一条箭头描线（文档序中离圆点最近的一条 path draw/draw-sm）
        prev_arrows = [e for e in events if e[0] < pos and e[1] in ('draw', 'draw-sm')]
        # 后一个目标元素（文档序中离圆点最近的 up/fu/fade/fillin）
        next_targets = [e for e in events if e[0] > pos and e[1] in ('up', 'fu', 'fade', 'fillin')]
        arrow_ready = prev_arrows[-1][2] + prev_arrows[-1][3] if prev_arrows else 0.0
        target_ready = next_targets[0][2] + next_targets[0][3] if next_targets else 0.0
        if d_css < arrow_ready:
            errors.append(
                f'圆点出现 --d={d_css}s 早于前箭头描线完成 {arrow_ready:.1f}s'
                f'（应等箭头连线画完圆点才出现）')
        if b < arrow_ready:
            errors.append(
                f'圆点 begin={b}s 早于前箭头描线完成 {arrow_ready:.1f}s'
                f'（应先描线完成再流动，避免箭头未画完圆点先飞）')
        if next_targets and b < target_ready:
            errors.append(
                f'圆点 begin={b}s 早于目标元素出现完成 {target_ready:.1f}s'
                f'（应先出现目标再流动，避免圆点流向空白）')

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print('用法: python verify_animation.py <动画.html> [关键内容...]')
        return 1
    path = sys.argv[1]
    src = open(path, encoding='utf-8').read()

    errors = check(src)
    for k in sys.argv[2:]:
        if k not in src:
            errors.append(f'缺失关键内容: {k}')

    if errors:
        for e in errors:
            print(f'FAIL: {e}')
        return 1
    print(f'OK {path}: 标签配对/无重复class/keyframes无transform/圆点时序 全部通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
