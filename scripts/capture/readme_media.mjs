// README용 화면 캡처·GIF (docs/media/). 서버가 떠 있어야 한다 (기본 http://127.0.0.1:8010, 실제 GMS를 부름).
//   node scripts/capture/readme_media.mjs [주소]
// 필요: Chrome, ffmpeg. 새 라이브러리 없음.
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch } from './cdp.mjs';

const BASE = process.argv[2] || 'http://127.0.0.1:8010/';
const OUT = new URL('../../docs/media/', import.meta.url).pathname;
const TMP = '/tmp/drpatch-media';
mkdirSync(OUT, { recursive: true });
rmSync(TMP, { recursive: true, force: true });
mkdirSync(TMP, { recursive: true });

const W = 1280;
const H = 800;
const ff = (...args) => execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args]);
const jpg = (png, name) => ff('-i', png, '-q:v', '3', `${OUT}${name}`);

const b = await launch({ width: W, height: H });
await b.goto(BASE, 1500);
await b.js(`localStorage.clear(); sessionStorage.clear(); location.reload();`);
await sleep(8000);
await b.js(`document.querySelector('.bubble')?.click();`); // 첫 인사 말풍선 닫기
await sleep(600);
await b.shot(`${TMP}/01.png`);
jpg(`${TMP}/01.png`, '01-desk.jpg');

// ── 메인 GIF: 예시 → 보내기 → 처방(블리스터) → 확정 ──
const flow = async () => {
  await sleep(800);
  await b.click('.ex-open-btn');
  await sleep(1500);
  await b.js(`[...document.querySelectorAll('.ex-card')].find((c) => c.textContent.includes('웹 API 서버'))?.click();`);
  await sleep(3500);
  await b.click('보내기');
  for (let i = 0; i < 90; i++) { // 처방이 나올 때까지 (최대 90초)
    await sleep(1000);
    const done = await b.js(`return !![...document.querySelectorAll('button')].find((x) => x.textContent.trim() === '처방 확정' && !x.disabled);`);
    if (done) break;
  }
  await sleep(2500);
  await b.shot(`${TMP}/02.png`);
  await b.click('처방 확정');
  await sleep(7000);
};
await b.record(`${TMP}/main`, 1, 1); // 폴더 준비
const frames = `${TMP}/main`;
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames, { recursive: true });
let running = true;
const rec = (async () => {
  let i = 0;
  while (running) {
    const t0 = Date.now();
    await b.shot(`${frames}/f${String(++i).padStart(4, '0')}.png`);
    await sleep(Math.max(0, 200 - (Date.now() - t0))); // 5fps로 떠서
  }
})();
await flow();
running = false;
await rec;
jpg(`${TMP}/02.png`, '02-plan.jpg');
// 기다리는 구간이 길어 3배 빠르게, 폭 960, 팔레트로 GIF
ff('-framerate', '5', '-i', `${frames}/f%04d.png`, '-vf',
  'setpts=PTS/3,fps=12,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4',
  `${OUT}main.gif`);

// ── 진료 예약 ──
await b.js(`document.querySelector('.paper .close')?.click(); document.querySelector('.bubble')?.click();`);
await sleep(800);
await b.click('진료 예약');
await sleep(2500);
await b.shot(`${TMP}/03.png`);
jpg(`${TMP}/03.png`, '03-calendar.jpg');

// ── 야간 당직 (숨은 것 16/16) ──
await b.js(`localStorage.setItem('drpatch-eggs', JSON.stringify(['hotfix','rollback','lts','rmrf','duck','monkey','friday','clock','devnull','nodemods','eyechart','sudo','diploma','room200','xray','konami'])); localStorage.setItem('drpatch-night','1'); location.reload();`);
await sleep(8000);
await b.js(`document.querySelector('.bubble')?.click();`);
await sleep(600);
await b.shot(`${TMP}/04.png`);
jpg(`${TMP}/04.png`, '04-night.jpg');

await b.close();
console.log('done →', OUT);
