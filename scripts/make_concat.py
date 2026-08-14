#!/usr/bin/env python3
"""make_concat.py — 按真实时间戳生成 ffmpeg concat 列表

用法（在含 frames/timestamps.json 的目录下）:
    python make_concat.py [frames目录] [输出concat路径]

读取 frames/timestamps.json（每帧 {idx, t}），生成:
    ffconcat version 1.0
    file 'frames/frame_00000.png'
    duration 0.1234
    ...

最后一帧 duration=0.3s（尾部停留）；concat demuxer 需末帧重复。
"""
import json
import os
import sys

base = os.path.dirname(os.path.abspath(__file__))
frames_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, 'frames')
out_concat = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base, 'concat.txt')

times = json.load(open(os.path.join(frames_dir, 'timestamps.json'), encoding='utf-8'))

# 自动检测帧扩展名（png=逐帧截图版 / jpg=CDP screencast 版）
ext = 'png'
for fn in os.listdir(frames_dir):
    if fn.startswith('frame_') and fn.endswith(('.png', '.jpg')):
        ext = fn.rsplit('.', 1)[-1]
        break

lines = ['ffconcat version 1.0', '']
for i, fr in enumerate(times):
    lines.append(f"file '{frames_dir}/frame_{fr['idx']:05d}.{ext}'")
    if i + 1 < len(times):
        dur = (times[i + 1]['t'] - fr['t']) / 1000.0
    else:
        dur = 0.3
    if dur <= 0:
        dur = 0.04
    lines.append(f"duration {dur:.4f}")
lines.append(f"file '{frames_dir}/frame_{times[-1]['idx']:05d}.{ext}'")

with open(out_concat, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

total = sum((times[i + 1]['t'] - times[i]['t']) / 1000.0 for i in range(len(times) - 1)) + 0.3
print(f'concat.txt 已生成: {len(times)} 帧, 总时长约 {total:.2f}s')
