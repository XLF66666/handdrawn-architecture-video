#!/usr/bin/env node
/* ============================================================
 * capture.js — headless Chrome 逐帧截图（3840x2160 PNG 无损）
 *
 * 用法（在含 node_modules 的 _export 目录下）:
 *   node capture.js <动画HTML相对路径> [时长ms] [输出目录]
 *   例: node capture.js ../架构图_动画.html 14000 frames
 *
 * 关键点:
 *   - 真实时间驱动: SMIL animateMotion 依赖真实时间线,
 *     虚拟时钟/加速截图会跳过圆点流动动画。
 *   - PNG 无损: 避免 JPEG 的 full-range(yuvj420p) 色彩污染,
 *     后续 ffmpeg 需 in_range=full:out_range=tv 转换。
 *   - 记录每帧真实时间戳 → timestamps.json 供 concat 合成。
 * ============================================================ */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME = process.env.MOSU_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const HTML_REL = process.argv[2] || '../架构图_动画.html';
const DURATION = parseInt(process.argv[3] || '14000', 10);
const OUT_DIR = process.argv[4] || 'frames';
const HTML = path.resolve(process.cwd(), HTML_REL);
const OUT = path.resolve(process.cwd(), OUT_DIR);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--window-size=3840,2160', '--hide-scrollbars', '--force-device-scale-factor=1', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 3840, height: 2160, deviceScaleFactor: 1 });

  const fileUrl = 'file:///' + HTML.replace(/\\/g, '/');
  await page.goto(fileUrl, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 400)); // 等首帧动画启动

  const t0 = Date.now();
  const INTERVAL = 40; // 目标帧间隔 ~25fps
  let idx = 0;
  const times = [];

  while (Date.now() - t0 < DURATION) {
    const f0 = Date.now();
    const buf = await page.screenshot({ type: 'png' });
    const f1 = Date.now();
    fs.writeFileSync(path.join(OUT, `frame_${String(idx).padStart(5, '0')}.png`), buf);
    times.push({ idx, t: f1 - t0 });
    idx++;
    const target = t0 + idx * INTERVAL;
    const wait = target - Date.now();
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    if (idx % 10 === 0) console.log(`  frame ${idx} t=${(f1 - t0) / 1000}s`);
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, 'timestamps.json'), JSON.stringify(times));
  const span = (times[times.length - 1].t - times[0].t) / 1000;
  console.log(`DONE frames=${idx} span=${span.toFixed(2)}s`);
})().catch(e => { console.error(e); process.exit(1); });
