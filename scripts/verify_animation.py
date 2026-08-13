#!/usr/bin/env python3
"""verify_animation.py — 动画 HTML 验收自检

用法:
    python verify_animation.py <动画.html> [关键内容...]

检查项:
    1. HTMLParser 标签配对（自闭合标签不计）
    2. 无重复 class 属性（class="..." ... class="..."）
    3. keyframes 无 CSS transform:（会覆盖 SVG transform 定位）
    4. 圆点 CSS --d <= SMIL begin（先出现再流动）
    5. 关键内容完整（可选参数逐一断言）

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

    # 3) keyframes 无 CSS transform
    m = re.search(r'<style>(.*?)</style>', src, re.S)
    css = m.group(1) if m else ''
    for kf in re.finditer(r'@keyframes\s+(\w+)\s*\{([^}]*)\}', css):
        if 'transform:' in kf.group(2):
            errors.append(f'keyframes {kf.group(1)} 含 CSS transform:')

    # 4) 圆点时序
    dots = re.findall(r'class="dot" style="--d:([\d.]+)s"[^>]*>[\s\S]*?<animateMotion dur="[\d.]+s" begin="([\d.]+)s"', src)
    for d, b in dots:
        if float(d) > float(b):
            errors.append(f'圆点 CSS --d={d}s > SMIL begin={b}s')

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
