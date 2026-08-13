#!/usr/bin/env python3
"""verify_sync.py — SVG 与动画 HTML 细节同步校验

用法:
    python verify_sync.py <svg> <html> <token>... [--absent <token>...]

用于阶段 3 后确保静态手绘 SVG 与动画 HTML 的元素细节一致：
    - 每个 <token> 必须同时存在于 SVG 与 HTML
    - --absent 后跟的 token 必须同时不存在（如已删除的标语/引导线）
    - 可选 --xml 对 SVG 做 XML 合法性解析

退出码 0 = 全部通过；1 = 有差异。
"""
import sys
import xml.dom.minidom


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print('用法: python verify_sync.py <svg> <html> <token>... [--absent <token>...] [--xml]')
        return 1

    svg_path, html_path = args[0], args[1]
    rest = args[2:]
    absent_tokens: list[str] = []
    check_xml = False
    if '--absent' in rest:
        i = rest.index('--absent')
        absent_tokens = rest[i + 1:]
        rest = rest[:i]
    if '--xml' in rest:
        check_xml = True
        rest.remove('--xml')
    want_tokens = rest

    svg = open(svg_path, encoding='utf-8').read()
    html = open(html_path, encoding='utf-8').read()

    errors = []
    if check_xml:
        try:
            xml.dom.minidom.parse(svg_path)
        except Exception as e:
            errors.append(f'SVG XML 非法: {e}')

    for t in want_tokens:
        if t not in svg or t not in html:
            errors.append(f'token 不同步「{t}」: svg={t in svg} html={t in html}')
    for t in absent_tokens:
        if t in svg or t in html:
            errors.append(f'token 应已删除「{t}」: svg={t in svg} html={t in html}')

    if errors:
        for e in errors:
            print(f'FAIL: {e}')
        return 1
    print(f'OK {svg_path} ↔ {html_path} 同步（{len(want_tokens)} 项存在 + {len(absent_tokens)} 项缺席）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
