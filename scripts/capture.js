#!/usr/bin/env node
/* ============================================================
 * capture.js — CDP Page.startScreencast 逐帧采集（高帧率方案）
 *
 * 用法（在含 node_modules 的 _export 目录下）:
 *   node capture.js <html> <duration_ms> <out_dir>
 *
 * 方案要点（实测数据）:
 *   - 1080p screencast + ffmpeg lanczos 放大 4K：~24fps，
 *     PSNR 46.9dB / 锐度比 1.01（与 4K 原生几乎无差异）
 *   - 对比：逐帧 page.screenshot PNG-4K 仅 4.8fps（卡顿根源）
 *   - 真实时间驱动：SMIL animateMotion 依赖真实时间线，
 *     浏览器原生 screencast 按真实时间节流，动画自然。
 *
 * 环境变量: MOSU_CHROME / MOSU_WIDTH / MOSU_HEIGHT（默认 1920x1080 采集）
 * 输出: out_dir/frame_XXXXX.jpg + timestamps.json
 * ============================================================ */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME = process.env.MOSU_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const WIDTH = parseInt(process.env.MOSU_WIDTH || '1920', 10);   // 采集分辨率（默认 1080p）
const HEIGHT = parseInt(process.env.MOSU_HEIGHT || '1080', 10);
const QUALITY = parseInt(process.env.MOSU_JPEG_QUALITY || '100', 10);
const HTML_REL = process.argv[2];
const DURATION = parseInt(process.argv[3] || '13000', 10);
const OUT_DIR = process.argv[4] || 'frames';
const HTML = path.resolve(process.cwd(), HTML_REL);
const OUT = path.resolve(process.cwd(), OUT_DIR);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: [`--window-size=${WIDTH},${HEIGHT}`, '--force-device-scale-factor=1', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });
  const client = await page.createCDPSession();
  await client.send('Page.enable');

  let idx = 0;
  const times = [];
  const t0 = Date.now();

  client.on('Page.screencastFrame', async (e) => {
    const t = Date.now() - t0;
    fs.writeFileSync(path.join(OUT, `frame_${String(idx).padStart(5, '0')}.jpg`), Buffer.from(e.data, 'base64'));
    times.push({ idx, t });
    idx++;
    if (idx % 100 === 0) console.log(`  frame ${idx} t=${(t / 1000).toFixed(1)}s`);
    await client.send('Page.screencastFrameAck', { sessionId: e.sessionId });
  });

  await client.send('Page.startScreencast', {
    format: 'jpeg', quality: QUALITY, maxWidth: WIDTH, maxHeight: HEIGHT, everyNthFrame: 1,
  });
  const fileUrl = 'file:///' + HTML.replace(/\\/g, '/');
  await page.goto(fileUrl, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 400));

  // 等待 DURATION 毫秒（真实时间推进，SMIL 动画正常）
  while (Date.now() - t0 < DURATION) {
    await new Promise(r => setTimeout(r, 200));
  }
  await client.send('Page.stopScreencast');
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'timestamps.json'), JSON.stringify(times));
  const span = times.length > 1 ? (times[times.length - 1].t - times[0].t) / 1000 : 0;
  const fps = span > 0 ? (times.length - 1) / span : 0;
  console.log(`DONE ${OUT_DIR} frames=${idx} span=${span.toFixed(2)}s fps=${fps.toFixed(1)}`);
})().catch(e => { console.error(e); process.exit(1); });
