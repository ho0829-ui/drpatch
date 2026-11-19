// 야간 당직 진료실 — 숨은 것 16/16을 다 찾으면 열린다 (spec v1.23).
// 기능은 그대로, 장면만 바꾼다: 조명·배경·창밖 밤하늘(달·별)·대기 모니터 글자·수면 모자·야간 근무표.
// 종이·말풍선·도크(HTML)는 읽기 좋게 밝은 그대로 둔다.
import * as THREE from 'three';
import { FONT, prep, textTexture } from './utils.js';

const DAY = {
  bg: '#CBEAE2', hemiSky: '#ffffff', hemiGround: '#9fcfc4', hemi: 0.6,
  keyColor: '#fff8ef', key: 2.1, winColor: '#e3f6ff', win: 0.7, lamp: 6, env: 0.42,
};
const NIGHT = {
  bg: '#0B2029', hemiSky: '#5a78b0', hemiGround: '#0b1f22', hemi: 0.14,
  keyColor: '#9fb4ff', key: 0.38, winColor: '#8fb0ff', win: 0.8, lamp: 22, env: 0.07,
};

function drawNightSky(c, w, h) {
  const g = c.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, '#0B1A3A');
  g.addColorStop(1, '#1D3B5C');
  c.fillStyle = g;
  c.fillRect(0, 0, w, h);
  // 별: 같은 자리에 늘 같게 (씨앗 고정)
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 90; i++) {
    const x = rnd() * w;
    const y = rnd() * h * 0.9;
    const r = rnd() * 1.6 + 0.4;
    c.fillStyle = `rgba(255,255,240,${0.35 + rnd() * 0.6})`;
    c.beginPath();
    c.arc(x, y, r, 0, Math.PI * 2);
    c.fill();
  }
  // 초승달 (블라인드가 위쪽 절반을 가리므로 아래쪽 왼편에)
  const mx = w * 0.24;
  const my = h * 0.72;
  const R = h * 0.11;
  const glow = c.createRadialGradient(mx, my, R * 0.6, mx, my, R * 2.6);
  glow.addColorStop(0, 'rgba(255,244,200,0.35)');
  glow.addColorStop(1, 'rgba(255,244,200,0)');
  c.fillStyle = glow;
  c.fillRect(mx - R * 3, my - R * 3, R * 6, R * 6);
  c.fillStyle = '#FFF3C4';
  c.beginPath();
  c.arc(mx, my, R, 0, Math.PI * 2);
  c.fill();
  c.globalCompositeOperation = 'destination-out';
  c.beginPath();
  c.arc(mx + R * 0.45, my - R * 0.25, R * 0.92, 0, Math.PI * 2);
  c.fill();
  c.globalCompositeOperation = 'source-over';
  // 지운 자리에 다시 하늘색을 채워 투명하지 않게
  c.globalCompositeOperation = 'destination-over';
  c.fillStyle = '#16304F';
  c.fillRect(0, 0, w, h);
  c.globalCompositeOperation = 'source-over';
}

function drawNightTv(c, w, h) {
  c.fillStyle = '#071A22';
  c.fillRect(0, 0, w, h);
  c.fillStyle = '#24406B';
  c.fillRect(0, 0, w, 70);
  c.fillStyle = '#FFFFFF';
  c.font = FONT(700, 34, true);
  c.fillText('DR.PATCH  야간 당직', 28, 48);
  c.fillStyle = '#9FB7E8';
  c.font = FONT(500, 30);
  c.fillText('지금 진료 중', 40, 140);
  c.fillStyle = '#FFF3C4';
  c.font = FONT(700, 170, true);
  c.fillText('03:14', 36, 320);
  c.fillStyle = '#F2734A';
  c.font = FONT(700, 36);
  c.fillText('응급 패치만 받습니다', 470, 160);
  c.fillStyle = '#9FB7E8';
  c.font = FONT(500, 28);
  c.fillText('다음 환자', 470, 222);
  c.fillStyle = '#FFFFFF';
  c.font = FONT(700, 40, true);
  c.fillText('prod-01', 470, 276);
  c.fillStyle = '#24406B';
  c.fillRect(0, h - 64, w, 64);
  c.fillStyle = '#C9D6F2';
  c.font = FONT(500, 24);
  c.fillText('조용히 · 롤백 준비 · 커피는 한 잔만', 28, h - 22);
}

function drawRoster(c, w, h) {
  c.fillStyle = '#FFFFFF';
  c.fillRect(0, 0, w, h);
  c.fillStyle = '#24406B';
  c.font = FONT(700, 54);
  c.fillText('야간 근무표', 40, 90);
  c.fillRect(40, 112, w - 80, 4);
  const rows = [
    ['당직', 'DR.PATCH'],
    ['00:00', '로그 회진'],
    ['03:14', '시계 점검'],
    ['04:00', '백업 확인'],
    ['06:00', '인수인계'],
  ];
  c.font = FONT(600, 36);
  rows.forEach(([a, b], i) => {
    const y = 190 + i * 76;
    c.fillStyle = '#5B7375';
    c.fillText(a, 40, y);
    c.fillStyle = '#16313A';
    c.fillText(b, 190, y);
    c.fillStyle = '#E3EFEC';
    c.fillRect(40, y + 22, w - 80, 2);
  });
  c.fillStyle = '#F2734A';
  c.font = FONT(700, 30);
  c.fillText('금요일 밤 배포 금지', 40, h - 48);
}

export function setupNight({ world, scene, renderer, lights, room, docBody, M, tween }) {
  const C = (hex) => new THREE.Color(hex);
  const day = { bg: C(DAY.bg), hemiSky: C(DAY.hemiSky), hemiGround: C(DAY.hemiGround), key: C(DAY.keyColor), win: C(DAY.winColor) };
  const night = { bg: C(NIGHT.bg), hemiSky: C(NIGHT.hemiSky), hemiGround: C(NIGHT.hemiGround), key: C(NIGHT.keyColor), win: C(NIGHT.winColor) };
  if (!(scene.background instanceof THREE.Color)) scene.background = C(DAY.bg);

  // 창 하늘: 낮 재질은 그대로 두고 밤 재질을 따로
  const daySkyMat = room.sky?.material || null;
  const skyTex = textTexture(760, 600, drawNightSky);
  const nightSkyMat = new THREE.MeshBasicMaterial({ map: skyTex.tex, toneMapped: false });

  // 대기 모니터
  const dayTvMat = room.tvFace?.material || null;
  const tvTex = textTexture(850, 470, drawNightTv);
  const nightTvMat = new THREE.MeshBasicMaterial({ map: tvTex.tex, toneMapped: false });

  // 수면 모자: 박사님 머리 꼭대기에서 조금 내려 얹는다 (머리 캡슐 반지름 0.72, 모자 띠 0.5)
  let cap = null;
  const capSrc = M.night?.getObjectByName('NightCap');
  if (capSrc && docBody) {
    cap = prep(capSrc.clone(true));
    docBody.updateWorldMatrix(true, true); // 부모(박사님 묶음·크기 2.8)까지 반영해야 머리 위치가 맞는다
    const box = new THREE.Box3().setFromObject(docBody);
    const top = new THREE.Vector3((box.min.x + box.max.x) / 2, box.max.y, (box.min.z + box.max.z) / 2);
    docBody.worldToLocal(top);
    cap.position.set(top.x - 0.06, top.y - 0.24, top.z - 0.08);
    cap.rotation.set(-0.12, 0, -0.18);
    cap.visible = false;
    docBody.add(cap);
  }

  // 야간 근무표 (뒷벽, 진료실 좌표에 바로 놓인 모델)
  let roster = null;
  const rosterSrc = M.night?.getObjectByName('Roster');
  if (rosterSrc) {
    roster = prep(rosterSrc.clone(true));
    const paper = roster.getObjectByName('RosterPaper');
    if (paper) {
      const tex = textTexture(512, 660, drawRoster);
      paper.material = new THREE.MeshBasicMaterial({ map: tex.tex, toneMapped: false });
    }
    roster.visible = false;
    world.add(roster);
  }

  let isNight = false;

  function apply(t) {
    // t: 0 = 낮, 1 = 밤
    const { hemi, key, windowLight } = lights;
    scene.background.lerpColors(day.bg, night.bg, t);
    hemi.color.lerpColors(day.hemiSky, night.hemiSky, t);
    hemi.groundColor.lerpColors(day.hemiGround, night.hemiGround, t);
    hemi.intensity = THREE.MathUtils.lerp(DAY.hemi, NIGHT.hemi, t);
    key.color.lerpColors(day.key, night.key, t);
    key.intensity = THREE.MathUtils.lerp(DAY.key, NIGHT.key, t);
    windowLight.color.lerpColors(day.win, night.win, t);
    windowLight.intensity = THREE.MathUtils.lerp(DAY.win, NIGHT.win, t);
    if (room.lamp) room.lamp.intensity = THREE.MathUtils.lerp(DAY.lamp, NIGHT.lamp, t);
    scene.environmentIntensity = THREE.MathUtils.lerp(DAY.env, NIGHT.env, t);
    const showNight = t >= 0.5;
    if (room.sky && daySkyMat) room.sky.material = showNight ? nightSkyMat : daySkyMat;
    if (room.tvFace && dayTvMat) room.tvFace.material = showNight ? nightTvMat : dayTvMat;
    if (cap) cap.visible = showNight;
    if (roster) roster.visible = showNight;
  }

  async function set(on, { animate = true } = {}) {
    if (on === isNight) return;
    isNight = on;
    if (!animate) {
      apply(on ? 1 : 0);
      return;
    }
    await tween(1500, (p) => apply(on ? p : 1 - p));
  }

  function dispose() {
    skyTex.tex.dispose();
    tvTex.tex.dispose();
    nightSkyMat.dispose();
    nightTvMat.dispose();
  }

  void renderer;
  return { set, isNight: () => isNight, dispose };
}
