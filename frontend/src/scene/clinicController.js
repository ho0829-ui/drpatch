import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import {
  COLOR, EGGS, ITEMS, MODELS, PATCH, PER_ROUND, QUIPS, ROUNDS, SEV, TOOL, roundOf,
} from '../demo.js';
import { BASE_DIST, createEngine } from './engine.js';
import { addGroundShadows } from './shadows.js';
import { createTweener, ease } from './utils.js';
import { setupRoom } from './props/room.js';
import { setupEggs } from './props/eggs.js';
import { setupBlisters, worldOfSlot } from './props/blister.js';
import { setupJarAndTray } from './props/jarAndTray.js';
import { setupIv } from './props/iv.js';
import { setupChart } from './props/chart.js';
import { setupStamp } from './props/stamp.js';
import { setupDoctor } from './props/doctor.js';

const TILT = 0.55;
const KONAMI = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

export async function createClinicController(canvas, callbacks) {
  const {
    isReduced,
    onLoaded,
    onStateChange,
    onStatus,
    onSay,
    onLog,
    onOpenSheet,
    onCloseSheetRequest,
    onTip,
    onFloatChip,
    onPillTagsUpdate,
    onBubblePos,
    onEggCount,
  } = callbacks;

  const loader = new GLTFLoader();
  const fontsReady = Promise.race([
    Promise.all([
      document.fonts.load('700 40px "IBM Plex Sans KR"'),
      document.fonts.load('700 40px "JetBrains Mono"'),
    ]),
    new Promise((r) => setTimeout(r, 1500)),
  ]).catch(() => {});

  const loaded = await Promise.all(
    MODELS.map((n) => loader.loadAsync(`/models/${n}.glb`).then((g) => [n, g.scene])),
  );
  await fontsReady;
  const M = Object.fromEntries(loaded);
  onLoaded();

  const { tween, stepTweens, sleep } = createTweener(isReduced);
  const engine = createEngine(canvas, tween, isReduced);
  const { scene, camera, controls, getDistScale, resetView, resize, toScreen, updateControlsAndRender } = engine;

  const world = new THREE.Group();
  scene.add(world);

  const pickRoots = [];
  const addPick = (obj, kind, data = {}) => {
    obj.userData = { ...obj.userData, kind, ...data };
    pickRoots.push(obj);
  };

  setupRoom(world, scene, M);
  addGroundShadows(world);
  const { eggNodes, tick: tickEggs } = setupEggs(world, M, addPick);
  const packs = setupBlisters(world, M, addPick);
  const { pills, pillByName, jarTop, lidTo, nextTrayPos } = setupJarAndTray(world, M, addPick, tween);
  const { drip } = setupIv(world, M, tween);

  const logs = [];
  const chartApi = setupChart(world, M, addPick, () => logs);
  const { stampPacks } = setupStamp(world, M, addPick, tween);
  const { docAct, tick: tickDoctor, getBubbleAnchor } = setupDoctor(world, M, addPick, tween, sleep);

  let state = 'idle';
  let popped = null;
  let hovered = null;
  let rafId = 0;

  const setState = (next) => {
    state = next;
    onStateChange(next);
  };

  function logEvent(type, detail) {
    const line = `#${String(logs.length + 1).padStart(2, '0')} ${type} ${detail}`;
    logs.push(line);
    chartApi.redraw();
    onLog(line, [...logs]);
  }

  // ── 이스터에그 ────────────────────────────────────────
  const found = new Set();
  try {
    JSON.parse(localStorage.getItem('drpatch-eggs') || '[]').forEach((k) => found.add(k));
  } catch { /* 저장 안 되는 환경 */ }
  onEggCount(found.size, Object.keys(EGGS).length);

  function runEgg(id) {
    const e = EGGS[id];
    if (!e) return;
    const first = !found.has(id);
    found.add(id);
    onEggCount(found.size, Object.keys(EGGS).length);
    try {
      localStorage.setItem('drpatch-eggs', JSON.stringify([...found]));
    } catch { /* 무시 */ }
    onSay((first ? '(숨은 것 발견!) ' : '') + e.say);
    logEvent('easter_egg', id);

    const node = eggNodes[id];
    if (e.act === 'no') docAct.no();
    else if (id === 'konami') docAct.dance();
    else if (id === 'sudo') docAct.tilt();
    else docAct.nod();

    if (node && e.act === 'squeak') {
      tween(
        380,
        (p) => {
          const q = Math.sin(p * Math.PI);
          node.scale.set(1 + q * 0.08, 1 - q * 0.18, 1 + q * 0.08);
        },
        ease.lin,
      ).then(() => node.scale.set(1, 1, 1));
    } else if (node) {
      tween(360, (p) => (node.position.y = Math.sin(p * Math.PI) * 0.15), ease.lin);
    }
  }

  // ── 진료 흐름 ─────────────────────────────────────────
  function emitFloatChip(it, extra = '') {
    const [x, y] = toScreen(jarTop);
    onFloatChip({
      id: `${Date.now()}-${Math.random()}`,
      name: it.name,
      sev: it.sev,
      sevLabel: SEV[it.sev][1],
      color: SEV[it.sev][0],
      extra,
      x,
      y,
    });
  }

  async function examine(p) {
    await tween(320, (t) => {
      p.inner.position.y = Math.sin(t * Math.PI) * 1.4;
    }, ease.lin);
    emitFloatChip(p.it);
  }

  async function shake(p) {
    emitFloatChip(p.it, ' · 처방 변경');
    await tween(
      700,
      (t) => {
        p.inner.rotation.y = Math.sin(t * Math.PI * 8) * 0.35 * (1 - t);
        p.inner.position.y = Math.sin(t * Math.PI) * 0.8;
      },
      ease.lin,
    );
  }

  async function flyTo(p, to, scale, rise = 3.2) {
    const from = p.root.position.clone();
    const rot0 = p.root.rotation.clone();
    const s0 = p.root.scale.x;
    p.inJar = false;
    await tween(900, (t) => {
      p.root.position.lerpVectors(from, to, t);
      p.root.position.y += Math.sin(t * Math.PI) * rise;
      p.root.rotation.set(rot0.x * (1 - t), rot0.y * (1 - t), rot0.z * (1 - t));
      p.root.scale.setScalar(s0 + (scale - s0) * t);
    });
    p.inner.rotation.set(0, 0, 0);
    await tween(
      260,
      (t) => {
        const q = Math.sin(t * Math.PI);
        p.inner.scale.set(1 + q * 0.12, 1 - q * 0.18, 1 + q * 0.12);
      },
      ease.lin,
    );
    p.inner.scale.set(1, 1, 1);
    await tween(240, (t) => (p.lift.rotation.x = TILT * t), ease.out);
  }

  async function packPill(p) {
    const bl = packs[p.it.round - 1];
    const slot = bl.slots[bl.used++];
    p.slot = slot;
    p.pack = bl;
    await flyTo(p, worldOfSlot(bl, slot), bl.group.scale.x * 1.1);
    slot.wellMat.color.set(SEV[p.it.sev][0]);
    p.hasTag = true;
  }

  async function trayPill(p) {
    await flyTo(p, nextTrayPos(), 0.95, 2.2);
    p.hasTag = true;
  }

  async function unpopPill() {
    if (popped) {
      const c = popped;
      popped = null;
      await tween(320, (p) => {
        c.inner.position.y = 1.1 * (1 - p);
      }, ease.out);
    }
  }

  async function runVisit() {
    if (state !== 'idle') return;
    setState('running');
    onCloseSheetRequest();
    await unpopPill();

    onStatus('접수', 0);
    logEvent('step_start', 'analyze');
    onSay(`흠, 어디 보자… requirements.txt ${ITEMS.length - 1}줄에 Python까지. 접수됐습니다.`);
    drip();
    docAct.nod();
    await sleep(1600);
    logEvent('step_end', 'analyze');

    onStatus('검사 중', 1);
    logEvent('step_start', 'call_tools');
    onSay('검사 들어갑니다. 따끔하지 않아요. 서버는요.');
    docAct.point();
    await lidTo(true);
    for (const [i, p] of pills.entries()) {
      logEvent('tool_call', `${TOOL(p.it)} ${p.it.name}`);
      await examine(p);
      drip();
      logEvent('tool_result', `${TOOL(p.it)} ${p.it.name}`);
      onStatus(`검사 ${i + 1}/${pills.length}`, 1);
    }
    logEvent('step_end', 'call_tools');
    onSay('허허, urllib3 1.24.1이라니… 꽤 오래 방치하셨군요.');
    docAct.nod();
    await sleep(1700);

    onStatus('판정', 2);
    logEvent('step_start', 'judge');
    for (const p of pills) {
      logEvent('judgment', `${p.it.name} ${SEV[p.it.sev][1]}`);
      await sleep(60);
    }
    logEvent('replan', 'Django 5.2 ✗ Python 3.8 → Python 3.11');
    onSay('Django 5.2는 Python 3.8로는 못 넘어가는군요. 처방 바꿉니다. Python부터 올리죠.');
    docAct.tilt();
    await shake(pillByName('Django'));
    await sleep(800);
    logEvent('step_end', 'judge');

    onStatus('처방', 3);
    logEvent('step_start', 'build');
    onSay(`급한 것부터 회차마다 ${PER_ROUND}정씩 담습니다. 건강한 녀석들은 곡반으로.`);
    const flights = [];
    for (const p of pills) {
      if (p.it.status === 'patch') flights.push(packPill(p));
      else if (p.it.status === 'safe') flights.push(trayPill(p));
      else continue;
      await sleep(150);
    }
    await Promise.all(flights);
    const left = pills.filter((p) => p.it.status === 'next');
    for (const p of left) {
      await tween(300, (t) => (p.inner.position.y = Math.sin(t * Math.PI) * 0.6), ease.lin);
    }
    await lidTo(false);
    logEvent('calendar_check', '겹치는 일정 없음');
    logEvent('plan_built', `${ROUNDS.length}회차 · ${PATCH.length}항목`);
    onStatus('처방 완료', 3);
    onSay(
      `처방 나왔습니다. ${ROUNDS.map((r) => r.date).join(', ')}. ${
        left.length ? `${left.map((p) => p.it.name).join(', ')}은 자리가 없어 다음 진료예요. ` : ''
      }궁금한 알약은 눌러 보세요.`,
    );
    docAct.hop();
    setState('planned');
  }

  async function confirmPlan() {
    if (state !== 'planned') return;
    setState('confirming');
    onCloseSheetRequest();
    await unpopPill();

    onSay('도장 찍습니다. 확정이에요.');
    await stampPacks(packs, (roundNo) => {
      logEvent('tool_result', `add_calendar_event ${roundNo}회차`);
    });
    onSay(`확정. ${ROUNDS[0].date} 밤 10시에 뵙죠. 늦으시면 서운합니다.`);
    docAct.wave();
    onStatus('처방 확정', 3);
    setState('done');
  }

  // ── 가리키기 · 누르기 · 키보드 ─────────────────────────
  const ray = new THREE.Raycaster();
  const ptr = new THREE.Vector2();
  const findRoot = (o) => {
    while (o && !o.userData.kind) o = o.parent;
    return o;
  };
  function pick(e) {
    ptr.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
    ray.setFromCamera(ptr, camera);
    const hit = ray.intersectObjects(pickRoots, true)[0];
    return hit ? findRoot(hit.object) : null;
  }
  function tipText(o) {
    const d = o.userData;
    if (d.kind === 'pill') {
      const it = d.pill.it;
      return state === 'idle' ? '검사 전' : `${it.name} ${it.cur}${it.status === 'next' ? ' · 다음 진료' : ''}`;
    }
    if (d.kind === 'blister') return `${d.round}회차 · ${roundOf(d.round).date}`;
    if (d.kind === 'egg') return EGGS[d.egg].tip;
    return {
      chart: '진료 기록',
      doctor: '닥터 패치',
      jar: '접수된 패키지',
      stamp: '확정 도장',
      tray: '곡반 · 패치 필요 없음',
    }[d.kind];
  }

  const onPointerMove = (e) => {
    const o = pick(e);
    hovered = o;
    canvas.style.cursor = o ? 'pointer' : 'default';
    if (o) onTip({ show: true, text: tipText(o), x: e.clientX, y: e.clientY });
    else onTip({ show: false, text: '', x: 0, y: 0 });
  };
  const onPointerLeave = () => {
    hovered = null;
    onTip({ show: false, text: '', x: 0, y: 0 });
  };

  let downAt = null;
  const onPointerDown = (e) => {
    downAt = [e.clientX, e.clientY];
  };
  const onClick = async (e) => {
    if (downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6) return;
    const o = pick(e);
    if (!o) {
      onCloseSheetRequest();
      await unpopPill();
      return;
    }
    const d = o.userData;
    if (d.kind === 'egg') {
      runEgg(d.egg);
      return;
    }
    if (d.kind === 'pill') {
      const p = d.pill;
      if (state === 'idle' || state === 'running') {
        onSay(state === 'idle' ? '아직 검사 전이에요. 진료 시작부터 누르시죠.' : '검사 중엔 잠깐만요. 금방 끝납니다.');
        return;
      }
      if (popped && popped !== p) {
        onCloseSheetRequest();
        await unpopPill();
      }
      popped = p;
      tween(
        480,
        (t) => {
          p.inner.position.y = 1.1 * t;
          p.inner.rotation.x = t * Math.PI * 2;
        },
        ease.back,
      ).then(() => (p.inner.rotation.x = 0));
      onOpenSheet({ kind: 'item', item: p.it, color: SEV[p.it.sev][0] });
    } else if (d.kind === 'blister') {
      if (state === 'idle' || state === 'running') {
        onSay('빈 포장지예요. 처방이 나오면 채워집니다.');
        return;
      }
      onOpenSheet({ kind: 'round', roundNo: d.round, color: COLOR.ink });
    } else if (d.kind === 'chart') {
      onOpenSheet({ kind: 'log', logs: [...logs], color: COLOR.teal });
    } else if (d.kind === 'tray') {
      if (state === 'idle' || state === 'running') onSay('곡반은 건강한 녀석들 자리입니다.');
      else onOpenSheet({ kind: 'tray', color: COLOR.teal });
    } else if (d.kind === 'doctor') {
      docAct.hop();
      onSay(QUIPS[Math.floor(Math.random() * QUIPS.length)]);
    } else if (d.kind === 'jar') {
      if (state === 'planned' || state === 'done') onOpenSheet({ kind: 'jar', color: COLOR.ink });
      else onSay(`접수된 패키지 ${ITEMS.length}개입니다. 진료 시작을 누르시죠.`);
    } else if (d.kind === 'stamp') {
      if (state === 'planned') confirmPlan();
      else onSay('도장은 처방이 나온 뒤에 찍습니다.');
    }
  };

  let konamiAt = 0;
  let typed = '';
  const onKeyDown = (e) => {
    const off = camera.position.clone().sub(controls.target);
    if (e.key === '+' || e.key === '=') camera.position.copy(controls.target).add(off.multiplyScalar(1 / 1.15));
    if (e.key === '-') camera.position.copy(controls.target).add(off.multiplyScalar(1.15));
    if (e.key === '0') resetView();

    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    konamiAt = k === KONAMI[konamiAt] ? konamiAt + 1 : k === KONAMI[0] ? 1 : 0;
    if (konamiAt === KONAMI.length) {
      konamiAt = 0;
      runEgg('konami');
    }
    if (k.length === 1) {
      typed = (typed + k).slice(-4);
      if (typed === 'sudo') {
        typed = '';
        runEgg('sudo');
      }
    }
  };

  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerleave', onPointerLeave);
  canvas.addEventListener('dblclick', resetView);
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('click', onClick);
  addEventListener('keydown', onKeyDown);
  addEventListener('resize', resize);

  // ── 매 프레임 ─────────────────────────────────────────
  const tmpV = new THREE.Vector3();
  onSay('어서 오세요. 오늘은 어디가 불편한 서버인가요?');

  function frame(now) {
    const t = now / 1000;
    const reduced = isReduced();
    stepTweens(now);
    updateControlsAndRender(now);

    tickDoctor(t, reduced, controls.getAzimuthalAngle());
    tickEggs(t);

    if (!reduced) {
      for (const p of pills) {
        if (p.inJar && state === 'idle') p.inner.rotation.z = Math.sin(t * 1.6 + p.phase) * 0.08;
      }
    }

    for (const p of pills) {
      const want = hovered === p.root && !p.inJar ? 0.18 : 0;
      p.liftY += (want - p.liftY) * 0.18;
      p.lift.position.y = p.liftY;
    }
    const chartWant = hovered === chartApi.chart ? 0.15 : 0;
    chartApi.chart.position.y += (chartWant - chartApi.chart.position.y) * 0.18;

    onBubblePos(getBubbleAnchor(camera));

    const showTags = camera.position.distanceTo(controls.target) < BASE_DIST * 1.3 * getDistScale();
    const tagList = [];
    for (const p of pills) {
      if (!p.hasTag) continue;
      tmpV.set(0, 0.45, 0);
      p.root.localToWorld(tmpV);
      const [x, y, front] = toScreen(tmpV);
      tagList.push({
        name: p.it.name,
        color: SEV[p.it.sev][0],
        x,
        y,
        visible: showTags && front && popped !== p,
      });
    }
    onPillTagsUpdate(tagList);

    rafId = requestAnimationFrame(frame);
  }
  rafId = requestAnimationFrame(frame);

  window.__dbg = {
    renderer: engine.renderer,
    scene,
    camera,
    ao: engine.getUseAO,
    freeze: (on) => (window.__freeze = on),
  };

  return {
    runVisit,
    confirmPlan,
    unpopPill,
    destroy() {
      cancelAnimationFrame(rafId);
      canvas.removeEventListener('pointermove', onPointerMove);
      canvas.removeEventListener('pointerleave', onPointerLeave);
      canvas.removeEventListener('dblclick', resetView);
      canvas.removeEventListener('pointerdown', onPointerDown);
      canvas.removeEventListener('click', onClick);
      removeEventListener('keydown', onKeyDown);
      removeEventListener('resize', resize);
      engine.dispose();
    },
  };
}
