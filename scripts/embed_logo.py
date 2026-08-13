#!/usr/bin/env python3
"""embed_logo.py — 把 logo PNG 内嵌为 base64 data URI 到 SVG

用法:
    python embed_logo.py <svg路径> [png路径]

将 SVG 中引用 mosu_logo.png 的 <image> 的 href 替换为
data:image/png;base64,...，使 SVG 自包含（不依赖外部文件）。

注意: 若 SVG 为只读（Windows 上常见），先执行
    attrib -R <svg>  或  chmod +w <svg>
"""
import base64
import re
import sys


def main() -> int:
    svg_path = sys.argv[1] if len(sys.argv) > 1 else '架构图.svg'
    png_path = sys.argv[2] if len(sys.argv) > 2 else 'assets/branding/mosu_logo.png'

    with open(png_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    data_uri = f'data:image/png;base64,{b64}'
    print(f'PNG base64 长度: {len(b64)} chars')

    src = open(svg_path, encoding='utf-8').read()
    pattern = r'<image[^>]*href="[^"]*mosu_logo\.png"[^>]*/>'
    matches = re.findall(pattern, src)
    if not matches:
        print('ERROR: 未找到引用 mosu_logo.png 的 image 标签')
        return 1
    print(f'找到 image 标签 {len(matches)} 个')

    def replace_href(m):
        tag = m.group(0)
        old = re.search(r'href="[^"]*mosu_logo\.png"', tag).group(0)
        return tag.replace(old, f'href="{data_uri}"')

    open(svg_path, 'w', encoding='utf-8').write(re.sub(pattern, replace_href, src))
    print(f'OK 已内嵌 logo 到 {svg_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
