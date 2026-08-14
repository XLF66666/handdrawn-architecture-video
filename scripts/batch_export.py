#!/usr/bin/env python3
"""batch_export.py — 多素材批量导出 4K MP4（1080p screencast + lanczos 放大）

用法:
    python batch_export.py [start_idx] [end_idx]

按 ASSETS 清单批量执行「capture.js 采集 → concat → ffmpeg 合成 4K」。
默认导出全部；传下标可分批（如 `0 5`、`5 10`）。

依赖: Node.js、puppeteer-core（scripts/capture.js 使用）、ffmpeg。
前置: 在 _export 工作目录放置本脚本 + capture.js + make_concat.py，
      并已 `npm install puppeteer-core@24`。
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))  # 工作目录（_export）

# (动画 HTML 相对路径, 输出 MP4 文件名, 截图时长 ms)
ASSETS = [
    ('../架构图_动画.html', '架构图_动画_4K.mp4', 23000),
]


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        print('ERR:', (r.stdout or '')[-500:] or (r.stderr or '')[-500:])
        return False
    return True


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else len(ASSETS)
    for html, mp4, dur in ASSETS[lo:hi]:
        name = os.path.splitext(os.path.basename(html))[0]
        print(f'--- {name} ---')
        # 1) 1080p CDP screencast 采集（~24fps）
        if not run(f'cd "{BASE}" && node capture.js {html} {dur} frames_{name}'):
            continue
        # 2) 按真实时间戳生成 concat（JPEG 帧）
        with open(f'{BASE}/frames_{name}/timestamps.json', encoding='utf-8') as f:
            times = json.load(f)
        lines = ['ffconcat version 1.0', '']
        for i, fr in enumerate(times):
            lines.append(f"file 'frames_{name}/frame_{fr['idx']:05d}.jpg'")
            durf = (times[i + 1]['t'] - fr['t']) / 1000 if i + 1 < len(times) else 0.2
            if durf <= 0:
                durf = 0.03
            lines.append(f'duration {durf:.4f}')
        lines.append(f"file 'frames_{name}/frame_{times[-1]['idx']:05d}.jpg'")
        open(f'{BASE}/concat_{name}.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        # 3) lanczos 放大 4K + full→tv 色彩转换 + bt709 元数据
        out = os.path.join(BASE, '..', mp4)
        ok = run(f'cd "{BASE}" && ffmpeg -y -f concat -safe 0 -i concat_{name}.txt '
                 f'-vf "scale=3840:2160:flags=lanczos,scale=in_range=full:out_range=tv" '
                 f'-c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart '
                 f'-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv "{out}"')
        if ok:
            print(f'OK {mp4}')


if __name__ == '__main__':
    main()
