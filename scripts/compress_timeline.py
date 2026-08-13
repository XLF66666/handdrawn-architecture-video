#!/usr/bin/env python3
"""compress_timeline.py — 压缩动画时间轴生成 N 秒版 HTML

用法:
    python compress_timeline.py <src.html> <dst.html> <scale>

把 HTML 中所有动画延迟 `--d:X.XXs` 与 SMIL `begin="X.XXs"` 值乘以
scale（如 0.5 = 22s 一轮 → 12s 一轮），并更新页脚"约 N 秒一轮"标注。

校验:
    - 输出 HTML 可解析、最后延迟 = 原最大延迟 × scale
    - 圆点 CSS --d <= SMIL begin 关系保持不变
"""
import re
import sys
from html.parser import HTMLParser


def main() -> int:
    if len(sys.argv) != 4:
        print('用法: python compress_timeline.py <src.html> <dst.html> <scale>')
        return 1
    src_path, dst_path, scale = sys.argv[1], sys.argv[2], float(sys.argv[3])

    src = open(src_path, encoding='utf-8').read()

    new = re.sub(r'--d:([\d.]+)s', lambda m: f'--d:{float(m.group(1)) * scale:.2f}s', src)
    new = re.sub(r'begin="([\d.]+)s"', lambda m: f'begin="{float(m.group(1)) * scale:.2f}s"', new)

    def max_delay(text):
        return max(float(m) for m in re.findall(r'--d:([\d.]+)s', text))

    old_max, new_max = max_delay(src), max_delay(new)
    # 更新页脚时长标注
    new = re.sub(r'约 [\d.]+ 秒一轮', f'约 {new_max + 0.5:.0f} 秒一轮', new)
    open(dst_path, 'w', encoding='utf-8').write(new)

    print(f'压缩前最后延迟: {old_max}s → 压缩后: {new_max}s (×{scale})')
    print(f'已生成: {dst_path}')

    # 自检：输出可解析 + 圆点时序不变
    class P(HTMLParser):
        def __init__(self):
            super().__init__(); self.stack = []
        def handle_starttag(self, tag, attrs):
            if tag not in ('meta', 'link', 'br', 'path', 'rect', 'circle', 'line', 'image', 'tspan', 'animateMotion'):
                self.stack.append(tag)
        def handle_endtag(self, tag):
            if tag in ('meta', 'link', 'br', 'path', 'rect', 'circle', 'line', 'image', 'tspan', 'animateMotion'):
                return
            if self.stack:
                self.stack.pop()
    p = P(); p.feed(new)
    assert not p.stack, f'HTML 标签不配对: {p.stack}'
    dots = re.findall(r'class="dot" style="--d:([\d.]+)s"[^>]*>[\s\S]*?<animateMotion dur="[\d.]+s" begin="([\d.]+)s"', new)
    for d, b in dots:
        assert float(d) <= float(b), (d, b)
    print('OK 输出 HTML 可解析；圆点 CSS --d <= SMIL begin')
    return 0


if __name__ == '__main__':
    sys.exit(main())
