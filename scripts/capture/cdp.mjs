// 헤드리스 Chrome을 DevTools Protocol로 움직여 화면 캡처·GIF용 프레임을 만든다 (README용, 테스트 아님).
// 새 라이브러리 없이: Node 22+ 내장 WebSocket + 설치된 Chrome + ffmpeg.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

export async function launch({ width = 1280, height = 800, port = 9333, profile = '/tmp/drpatch-cdp-profile' } = {}) {
  const proc = spawn(CHROME, [
    '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    `--window-size=${width},${height}`, '--hide-scrollbars', '--use-angle=metal', '--enable-gpu',
    '--force-device-scale-factor=1', 'about:blank',
  ], { stdio: 'ignore' });
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200);
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      target = list.find((t) => t.type === 'page');
    } catch { /* 아직 안 뜸 */ }
  }
  if (!target) throw new Error('Chrome DevTools에 붙지 못함');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id;
    pending.set(n, { resolve, reject });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 768 });

  const api = {
    send,
    async goto(url, waitMs = 6000) {
      await send('Page.navigate', { url });
      await sleep(waitMs);
    },
    async js(expr) {
      const r = await send('Runtime.evaluate', { expression: `(async () => { ${expr} })()`, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || 'js 오류');
      return r.result.value;
    },
    async shot(path, clip) {
      const r = await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 1 } } : {}) });
      writeFileSync(path, Buffer.from(r.data, 'base64'));
    },
    /** ms 동안 fps로 프레임을 떠서 dir/f0001.png… 로 저장 */
    async record(dir, ms, fps = 12, during) {
      mkdirSync(dir, { recursive: true });
      const n = Math.round((ms / 1000) * fps);
      const run = during ? during() : Promise.resolve();
      for (let i = 1; i <= n; i++) {
        const t0 = Date.now();
        await api.shot(`${dir}/f${String(i).padStart(4, '0')}.png`);
        await sleep(Math.max(0, 1000 / fps - (Date.now() - t0)));
      }
      await run;
    },
    async click(selectorOrText) {
      return api.js(`
        const q = ${JSON.stringify(selectorOrText)};
        const el = document.querySelector(q) || [...document.querySelectorAll('button')].find((b) => b.textContent.trim() === q || b.textContent.includes(q));
        if (!el) return false; el.click(); return true;`);
    },
    async close() {
      try { await send('Browser.close'); } catch { /* 무시 */ }
      proc.kill();
    },
  };
  return api;
}
