#!/usr/bin/env python3
"""check_overlap.py — 几何越界/重叠自动检查

用法:
    # 模式 A：检查 HTML 内 SVG 文字是否超出容器（rect）右缘
    python check_overlap.py <动画.html>

    # 模式 B：检查 div.card 容器（CSS transform 最终态）是否互不重叠
    python check_overlap.py <动画.html> --cards

说明:
    - 模式 A 遍历 <rect> 与 <text>：估算文字宽度（中文=字号px，ASCII≈0.55*字号），
      若 text 右缘 > 其所在 rect 右缘则报 FAIL（超框）。
    - 模式 B 解析 .card 容器 + @keyframes 的最终 transform（translate/scale），
      计算最终矩形，两两检查是否重叠。

退出码: 0 = 全部通过；1 = 有越界/重叠。
"""
import re
import sys
from html.parser import HTMLParser

WARN = True  # 容器内文字无法配对时打印 warning


def est_width(text: str, font_size: float) -> float:
    """估算文字渲染宽度（楷体）。中文≈字号，ASCII/空格≈0.55*字号。"""
    w = 0.0
    for ch in text:
        w += font_size if ord(ch) > 0x2E7F else font_size * 0.55
    return w


CLASS_FS = {}  # 可由 --class-fs "panelTitle:27,valueTitle:24" 覆盖


def parse_svg_geometry(src: str, class_fs=None):
    """提取 <rect> 与 <text>，坐标按 <g transform> 偏移栈累加为绝对坐标；
    记录 DOM 组路径（g 序号元组）用于精确匹配容器（同组/祖先组，排除兄弟组）。
    返回 (rects, texts)。"""
    rects, texts = [], []
    stack = [(0.0, 0.0, -1)]  # (ox, oy, gid)
    gid = 0

    pattern = re.compile(
        r'<g\b[^>]*transform="translate\(\s*(-?[\d.]+)\s+(-?[\d.]+)[^"]*"[^>]*>'
        r'|</g>'
        r'|<rect\b([^>]*?)/?>'
        r'|<text\b([^>]*)>([^<]*)</text>'
    )
    for m in pattern.finditer(src):
        if m.group(1) is not None:                       # <g transform>
            gid += 1
            stack.append((stack[-1][0] + float(m.group(1)),
                          stack[-1][1] + float(m.group(2)), gid))
        elif m.group(0) == '</g>':
            if len(stack) > 1:
                stack.pop()
        elif m.group(3) is not None:                     # <rect>
            attrs = m.group(3)
            def g(name, default=None):
                mm = re.search(name + r'="([\d.\-]+)"', attrs)
                return float(mm.group(1)) if mm else default
            x, y = g('x', 0.0) or 0.0, g('y', 0.0) or 0.0
            w, h = g('width'), g('height')
            if w is None or h is None:
                continue
            ax, ay = stack[-1][0] + x, stack[-1][1] + y
            rects.append({'x': ax, 'y': ay, 'w': w, 'h': h,
                          'right': ax + w, 'bottom': ay + h,
                          'path': tuple(s[2] for s in stack)})
        elif m.group(4) is not None:                     # <text>
            attrs, content = m.group(4), m.group(5).strip()
            xm = re.search(r'x="([\d.\-]+)"', attrs)
            ym = re.search(r'y="([\d.\-]+)"', attrs)
            fm = re.search(r'font-size="([\d.\-]+)"', attrs)
            middle = 'text-anchor="middle"' in attrs
            if not xm or not ym or not content:
                continue
            cls = (re.search(r'class="([^"]+)"', attrs) or [None, ''])[1].split()[0] if re.search(r'class="([^"]+)"', attrs) else ''
            fs = float(fm.group(1)) if fm else (class_fs or CLASS_FS).get(cls, 16.0)
            lx, ly = float(xm.group(1)), float(ym.group(1))
            ax, ay = stack[-1][0] + lx, stack[-1][1] + ly
            ew = est_width(content, fs)
            right = ax + (ew / 2 if middle else ew)
            texts.append({'x': ax, 'y': ay, 'content': content, 'fs': fs, 'right': right,
                          'path': tuple(s[2] for s in stack)})
    return rects, texts


def check_texts(src: str, class_fs=None) -> list[str]:
    """模式 A：文字右缘是否超出其容器 rect 右缘（容差 6px）。
    容器 = 同 DOM 组或祖先组的 rect（排除兄弟组误配）。"""
    rects, texts = parse_svg_geometry(src, class_fs)
    errors = []
    for t in texts:
        # 容器候选：path 是 text 祖先（或同组）的 rect
        holders = [
            r for r in rects
            if r['path'] == t['path'][:len(r['path'])]
            and r['x'] - 2 <= t['x'] <= r['right'] + 2
            and r['y'] - 12 <= t['y'] <= r['bottom'] + 12
        ]
        if not holders:
            continue  # 无容器（如居中标题），跳过
        h = min(holders, key=lambda r: (r['w'], r['h']))
        if t['right'] > h['right'] + 6:
            errors.append(f'文字超框「{t["content"]}」x={t["x"]:.0f} 右缘{t["right"]:.0f} > 容器右缘{h["right"]:.0f}')
    return errors


def parse_card_final_rects(src: str):
    """模式 B：解析 .card div 的 @keyframes 最终 transform，返回最终矩形。"""
    # 提取 <div class="card" id="X"> 与对应 @keyframes X 的 100% transform
    cards = re.findall(r'<div class="card" id="(\w+)"', src)
    css = re.search(r'<style>(.*?)</style>', src, re.S)
    css = css.group(1) if css else ''
    rects = []
    for cid in cards:
        kf = re.search(r'@keyframes\s+' + re.escape(cid) + r'\s*\{([^}]*)\}', css)
        if not kf:
            kf = re.search(r'@keyframes\s+' + re.escape(cid) + r'\s*\{(.*?)\n\}', css, re.S)
        body = kf.group(1) if kf else ''
        # 取最后一个含 transform 的关键帧（通常 100%）
        frames = re.findall(r'([\d.]+%)\s*\{([^}]*)\}', body)
        final = None
        for pct, rule in frames:
            if 'transform:' in rule or 'translate(' in rule:
                final = rule
        if final is None and frames:
            # 兜底：取带 translate 的任意帧
            for pct, rule in frames:
                if 'translate' in rule:
                    final = rule
                    break
        if final is None:
            continue
        # translate(x,y) scale(s)
        tm = re.search(r'translate\((-?[\d.]+)px?,(-?[\d.]+)px?\)', final)
        sm = re.search(r'scale\(([\d.]+)\)', final)
        if not tm:
            continue
        tx, ty = float(tm.group(1)), float(tm.group(2))
        s = float(sm.group(1)) if sm else 1.0
        rects.append({'id': cid, 'x': tx, 'y': ty, 'w': 1920 * s, 'h': 1080 * s,
                      'right': tx + 1920 * s, 'bottom': ty + 1080 * s})
    return rects


def check_cards(src: str) -> list[str]:
    """模式 B：三卡/多卡容器最终位置是否互不重叠。"""
    rects = parse_card_final_rects(src)
    errors = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            overlap_x = a['x'] < b['right'] and b['x'] < a['right']
            overlap_y = a['y'] < b['bottom'] and b['y'] < a['bottom']
            if overlap_x and overlap_y:
                errors.append(f'容器重叠: {a["id"]}[{a["x"]:.0f},{a["right"]:.0f}] × {b["id"]}[{b["x"]:.0f},{b["right"]:.0f}]')
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print('用法: python check_overlap.py <html> [--cards]')
        return 2
    src = open(sys.argv[1], encoding='utf-8').read()
    class_fs = None
    if '--class-fs' in sys.argv:
        i = sys.argv.index('--class-fs')
        class_fs = {}
        for pair in sys.argv[i + 1].split(','):
            k, v = pair.split(':')
            class_fs[k] = float(v)

    # 先确认 HTML 可解析
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
    p = P(); p.feed(src)
    if p.stack:
        print(f'FAIL: HTML 标签不配对 {p.stack}')
        return 1

    errors = check_texts(src, class_fs) if '--cards' not in sys.argv else []
    if '--cards' in sys.argv:
        errors += check_cards(src)

    if errors:
        for e in errors:
            print(f'FAIL: {e}')
        print(f'共 {len(errors)} 项问题')
        return 1
    mode = '卡片容器' if '--cards' in sys.argv else 'SVG 文字'
    print(f'OK {mode}几何检查全部通过（{sys.argv[1]}）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
