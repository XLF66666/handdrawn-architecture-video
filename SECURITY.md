# Security Policy

## 报告安全问题

请**不要**在公开 Issue 中提交安全漏洞。请将问题私信仓库维护者
（Gitee 仓库：`https://gitee.com/xie-linfeng-666/handdrawn-architecture-video`），
或通过仓库主页提供的联系方式报告。

## 安全承诺

- 本 skill 为纯本地工具：截图与导出全部在本机完成，不上传任何作品内容。
- `scripts/capture.js` 仅连接本机 Chrome 并访问本地 `file://` 页面；
  除 npm 安装 puppeteer-core 外无任何网络调用。
- 不收集、不传输用户数据。

## 依赖与供应链

- npm 依赖仅 `puppeteer-core`（连接系统 Chrome，不下载浏览器）。
- 安装 puppeteer-core 时若外网直连不可达，可显式指定代理：
  `npm install puppeteer-core@24 --proxy=http://127.0.0.1:7897 --https-proxy=http://127.0.0.1:7897`
  或用环境变量 `MOSU_NPM_PROXY` 覆盖默认代理。
- 提交依赖锁文件前请审查新依赖的来源。

## 防护建议

- 只对可信的 SVG / HTML 源文件运行本流水线（导出会执行页面内 SMIL/CSS，
  恶意内容理论上可触发本地渲染异常）。
- 生产环境导出 4K 视频时建议在隔离环境或可信目录中进行。
