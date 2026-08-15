#!/usr/bin/env python3
"""selfcheck.py — skill 发布前一键自检

用法:
    python selfcheck.py [skill目录] [样板目录]

检查项:
    1. 目录结构完整（SKILL.md + references/ + scripts/ + examples/）
    2. SKILL.md frontmatter 合法（--- name / description ---）
    3. 所有 .py 脚本 py_compile 通过
    4. capture.js 通过 node --check
    5. export_4k.ps1 通过 PowerShell Parser（UTF-8 BOM 存在时中文可解析）
    6. examples/README.md 中引用的样板文件存在（按行内反引号路径解析）

退出码 0 = 全部通过；1 = 有失败。
"""
import os
import re
import subprocess
import sys
import tempfile

# CI（GitHub Actions windows-latest）上 Python 默认 stdout 是 cp1252，
# 打印中文会 UnicodeEncodeError 崩溃——强制 UTF-8（本地/CI 均兼容）。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

REQUIRED = [
    'SKILL.md',
    'README.md',
    'LICENSE',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'CODE_OF_CONDUCT.md',
    'references/handdrawn-style.md',
    'references/animation-html.md',
    'references/export-4k.md',
    'scripts/capture.js',
    'scripts/make_concat.py',
    'scripts/batch_export.py',
    'scripts/check_overlap.py',
    'scripts/export_4k.ps1',
    'scripts/export_4k.sh',
    'scripts/embed_logo.py',
    'scripts/compress_timeline.py',
    'scripts/verify_animation.py',
    'scripts/verify_sync.py',
    'scripts/selfcheck.py',
    'examples/README.md',
    'examples/minimal-demo.html',
]


def check_py(path: str) -> list[str]:
    r = subprocess.run([sys.executable, '-m', 'py_compile', path],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return [] if r.returncode == 0 else [f'py_compile 失败 {path}: {r.stderr.strip()}']


def check_node(path: str) -> list[str]:
    r = subprocess.run(['node', '--check', path],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return [] if r.returncode == 0 else [f'node --check 失败 {path}: {r.stderr.strip()}']


def check_ps1(path: str) -> list[str]:
    with open(path, 'rb') as f:
        raw = f.read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    if not has_bom:
        return [f'{path} 缺少 UTF-8 BOM（Windows PowerShell 5.1 中文会解析错乱）']
    # 用临时检查脚本调用 PowerShell Parser，避免转义问题
    tmp = tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False, encoding='utf-8')
    tmp.write(f"$e = $null\n[System.Management.Automation.Language.Parser]::ParseFile('{path}', [ref]$null, [ref]$e) | Out-Null\nif ($e.Count -gt 0) {{ $e | ForEach-Object {{ Write-Host ('PSERR: ' + $_.Message) }}; exit 1 }}\n")
    tmp.close()
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', tmp.name],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            msg = (r.stdout or '').strip() or (r.stderr or '').strip() or f'exit={r.returncode}'
            return [f'PowerShell 解析失败 {path}: {msg}']
        return []
    finally:
        os.unlink(tmp.name)


def check_frontmatter(skill_dir: str) -> list[str]:
    head = open(os.path.join(skill_dir, 'SKILL.md'), encoding='utf-8').read()
    errs = []
    if not head.startswith('---'):
        errs.append('SKILL.md 缺少 YAML frontmatter 起始 ---')
    m = re.match(r'^---\nname:\s*(.+)\ndescription:\s*(.+)\n---', head, re.S)
    if not m:
        errs.append('SKILL.md frontmatter 格式非法（需 name/description 字段）')
    elif not m.group(1).strip() or not m.group(2).strip():
        errs.append('SKILL.md name/description 为空')
    return errs


def check_examples(skill_dir: str, sample_dir: str | None) -> list[str]:
    """examples/README.md 里反引号引用的相对样板文件需存在。"""
    path = os.path.join(skill_dir, 'examples', 'README.md')
    if not os.path.exists(path):
        return ['examples/README.md 缺失']
    if not sample_dir or not os.path.isdir(sample_dir):
        return []  # 未提供样板目录则不检查存在性
    text = open(path, encoding='utf-8').read()
    errs = []
    for tok in re.findall(r'`([^`]+)`', text):
        # 只检查看起来像文件名的 token（含 .svg/.html/.mp4/.png/.md）
        if not re.search(r'\.(svg|html|mp4|png|md)$', tok, re.I):
            continue
        # 跳过 skill 内部文件、examples 自身文件、简写 token（如 _12s.html）
        if tok.startswith(('references/', 'scripts/', 'examples/')) or tok.startswith('_'):
            continue
        if os.path.exists(os.path.join(skill_dir, tok)):
            continue
        if os.path.exists(os.path.join(skill_dir, 'examples', tok)):
            continue
        candidate = os.path.join(sample_dir, tok)
        if not os.path.exists(candidate):
            errs.append(f'examples 引用样板不存在: {tok}')
    return errs


ANIM_CLASSES = ('fade', 'fu', 'fillin', 'draw', 'draw-sm', 'dot')


def check_html_pitfalls(path: str) -> list[str]:
    """动画 HTML 常见坑检测：
    1) 动画类元素（fade/fu/fillin/draw/draw-sm/dot）上不应有 opacity=".XX"
       —— CSS opacity 动画会覆盖该属性，导致底色变不透明遮挡文字，应改 fill-opacity。
    2) 一个元素只能有一个 class 属性。
    """
    src = open(path, encoding='utf-8').read()
    errs = []
    for m in re.finditer(r'<[^>]*class="(?:fade|fu|fillin|draw|draw-sm|dot)[^"]*"[^>]*\sopacity="\.', src):
        errs.append(f'动画类元素含 opacity 属性（应改 fill-opacity）: …{m.group(0)[-60:]}')
    for m in re.finditer(r'class="[^"]*"[^>]*class="', src):
        errs.append(f'重复 class 属性: …{m.group(0)[-60:]}')
    return errs


def check_capture_regex(path: str) -> list[str]:
    """capture.js 的 file:// 反斜杠替换正则必须完整（/\\\\/g 两个反斜杠）。
    heredoc/shell 写入时 \\\\ 常被吃掉一个变成 /\\/g，导致 SyntaxError。"""
    src = open(path, encoding='utf-8').read()
    errs = []
    m = re.search(r'HTML\.replace\((/[^/]+/g),\s*\'/\'\)', src)
    if m:
        pattern = m.group(1)
        if pattern.count('\\') < 2:
            errs.append(f'capture.js 的 fileUrl 反斜杠替换正则不完整: {pattern}（应为 /\\\\/g）')
    return errs


def main() -> int:
    skill_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    sample_dir = sys.argv[2] if len(sys.argv) > 2 else None
    errors: list[str] = []

    # 1) 结构完整
    for rel in REQUIRED:
        if not os.path.exists(os.path.join(skill_dir, rel)):
            errors.append(f'缺少文件: {rel}')

    # 2) frontmatter
    errors += check_frontmatter(skill_dir)

    # 3) 脚本语法
    for rel in ['scripts/capture.js']:
        p = os.path.join(skill_dir, rel)
        if os.path.exists(p):
            errors += check_node(p)
    for rel in ['scripts/make_concat.py', 'scripts/embed_logo.py',
                'scripts/compress_timeline.py', 'scripts/verify_animation.py',
                'scripts/verify_sync.py', 'scripts/batch_export.py',
                'scripts/check_overlap.py', 'scripts/selfcheck.py']:
        p = os.path.join(skill_dir, rel)
        if os.path.exists(p):
            errors += check_py(p)
    ps1 = os.path.join(skill_dir, 'scripts/export_4k.ps1')
    if os.path.exists(ps1):
        errors += check_ps1(ps1)

    # 3.5) HTML 坑检测（minimal-demo.html 样板）+ capture.js 正则完整性
    demo = os.path.join(skill_dir, 'examples', 'minimal-demo.html')
    if os.path.exists(demo):
        errors += check_html_pitfalls(demo)
    cap = os.path.join(skill_dir, 'scripts', 'capture.js')
    if os.path.exists(cap):
        errors += check_capture_regex(cap)

    # 4) 样板存在性
    errors += check_examples(skill_dir, sample_dir)

    if errors:
        for e in errors:
            print(f'FAIL: {e}')
        print(f'共 {len(errors)} 项失败')
        return 1
    print(f'OK selfcheck 全部通过（{skill_dir}）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
