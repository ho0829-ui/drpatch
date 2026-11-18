import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as api from '../api.js';
import { COLOR, EGGS, MODELS, QUIPS, SEV, sevKey } from '../demo.js';
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
const STEP_STAGE = { analyze: [0, '접수'], call_tools: [1, '검사 중'], judge: [2, '판정'], replan: [2, '재계획'], build: [3, '처방'] };

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
    onUploadRequest,
    onPlanUpdate,
    onChatTurn,
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
  const removePick = (obj) => {
    const idx = pickRoots.indexOf(obj);
    if (idx >= 0) pickRoots.splice(idx, 1);
  };

  setupRoom(world, scene, M, addPick);
  addGroundShadows(world);
  const { eggNodes, tick: tickEggs } = setupEggs(world, M, addPick);
  const blisterApi = setupBlisters(world, M, addPick, removePick);
  const jarApi = setupJarAndTray(world, M, addPick, removePick, tween);
  const { drip } = setupIv(world, M, tween);

  const logs = [];
  const chartApi = setupChart(world, M, addPick, () => logs);
  const { stampPacks } = setupStamp(world, M, addPick, tween);
  const { docAct, tick: tickDoctor, getBubbleAnchor } = setupDoctor(world, M, addPick, tween, sleep);

  let state = 'idle'; // 'idle' (업로드 전) | 'ready' (업로드됨) | 'running' | 'planned' | 'confirming' | 'done'
  let popped = null;
  let hovered = null;
  let rafId = 0;
  let currentPlan = null;
  let currentPackages = [];
  let violatedNames = [];

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
  } catch { /* 무시 */ }
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

  // ── 알약 애니메이션 helpers ────────────────────────────
  function emitFloatChip(name, sev, extra = '') {
    const k = sevKey(sev);
    const [x, y] = toScreen(jarApi.jarTop);
    onFloatChip({
      id: `${Date.now()}-${Math.random()}`,
      name,
      sev: k,
      sevLabel: SEV[k][1],
      color: SEV[k][0],
      extra,
      x,
      y,
    });
  }

  async function examinePill(p) {
    if (!p) return;
    await tween(300, (t) => {
      p.inner.position.y = Math.sin(t * Math.PI) * 1.4;
    }, ease.lin);
  }

  async function shakePill(p) {
    if (!p) return;
    emitFloatChip(p.it.name, p.it.sev, ' · 처방 변경');
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

  async function packPill(p, bl) {
    const slot = bl.slots[bl.used++];
    if (!slot) return;
    p.slot = slot;
    p.pack = bl;
    await flyTo(p, worldOfSlot(bl, slot), bl.group.scale.x * 1.1);
    slot.wellMat.color.set(SEV[sevKey(p.it.sev)][0]);
    p.hasTag = true;
    p.tagText = p.it.name;
  }

  async function trayPill(p) {
    await flyTo(p, jarApi.nextTrayPos(), 0.95, 2.2);
    p.hasTag = true;
    p.tagText = p.it.name;
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

  // ── 업로드 · 실데이터 반영 ─────────────────────────────
  function loadPackages(packages) {
    currentPackages = packages || [];
    currentPlan = null;
    violatedNames = [];
    blisterApi.clearPacks();
    jarApi.setPackages(currentPackages);
    onPlanUpdate?.(null, currentPackages);
    if (currentPackages.length) {
      setState('ready');
      onStatus('접수 완료', 0);
      onSay(`requirements.txt ${currentPackages.length}개 패키지 접수됐습니다. 진료를 시작하거나 조건을 말씀해 주세요.`);
    } else {
      setState('idle');
      onStatus('대기 중', -1);
      onSay('어서 오세요. requirements.txt를 올려 주세요.');
    }
  }

  async function applyPlan(plan) {
    currentPlan = plan;
    onPlanUpdate?.(plan, currentPackages);
    jarApi.resetToJar();

    const rounds = plan.rounds || [];
    const packs = blisterApi.rebuild(rounds, plan.window);

    await jarApi.lidTo(true);
    const flights = [];

    for (const r of rounds) {
      const bl = packs.find((pk) => pk.round.round_no === r.round_no);
      for (const item of r.items || []) {
        const p = jarApi.ensurePill({ name: item.name, version: item.current_version });
        Object.assign(p.it, {
          cur: item.current_version || '미상',
          tgt: item.target_version || '미상',
          sev: sevKey(item.severity),
          round: r.round_no,
          status: 'patch',
          reason: item.reason || '',
          flags: item.flags || [],
          eol_date: item.eol_date || null,
          kind: item.kind || p.it.kind,
        });
        if (bl) {
          flights.push(packPill(p, bl));
          await sleep(100);
        }
      }
    }

    for (const safeName of plan.safe || []) {
      const p = jarApi.ensurePill({ name: safeName });
      Object.assign(p.it, {
        tgt: p.it.cur,
        sev: 'safe',
        round: null,
        status: 'safe',
        reason: '알려진 취약점이 없어요.',
        flags: [],
      });
      flights.push(trayPill(p));
      await sleep(80);
    }

    for (const item of plan.unassigned || []) {
      const p = jarApi.ensurePill({ name: item.name, version: item.current_version });
      Object.assign(p.it, {
        cur: item.current_version || '미상',
        tgt: item.target_version || '미상',
        sev: sevKey(item.severity),
        round: null,
        status: 'next',
        reason: item.reason || '회차가 꽉 차서 다음 진료로 미뤘어요.',
        flags: item.flags || [],
        eol_date: item.eol_date || null,
      });
      p.hasTag = true;
      p.tagText = `${p.it.name} · 다음 진료`;
    }

    for (const u of plan.unchecked || []) {
      const p = jarApi.ensurePill({ name: u.name });
      Object.assign(p.it, {
        sev: 'unchecked',
        round: null,
        status: 'unchecked',
        reason: u.reason || '확인 못 함',
        flags: [],
      });
      p.hasTag = true;
      p.tagText = `${p.it.name} · 확인 못 함`;
    }

    for (const h of plan.held || []) {
      const p = jarApi.ensurePill({ name: h.name });
      Object.assign(p.it, {
        sev: 'held',
        round: null,
        status: 'held',
        reason: h.reason || '보류',
        flags: [],
      });
      p.hasTag = true;
      p.tagText = `${p.it.name} · 보류`;
    }

    await Promise.all(flights);
    await jarApi.lidTo(false);
  }

  // ── /chat 실데이터 스트림 실행 ─────────────────────────
  async function sendChatMessage(message) {
    if (state === 'running' || state === 'confirming') return null;
    const prevState = state;
    setState('running');
    onCloseSheetRequest();
    await unpopPill();

    let finalEvent = null;
    try {
      finalEvent = await api.chat(api.getSession(), message, (ev) => {
        if (ev.type === 'step_start') {
          const st = STEP_STAGE[ev.step];
          if (st) onStatus(st[1], st[0]);
          logEvent('step_start', ev.step || '');
          drip();
          if (ev.step === 'call_tools') docAct.point();
          else if (ev.step === 'analyze') docAct.nod();
        } else if (ev.type === 'step_end') {
          logEvent('step_end', ev.step || '');
        } else if (ev.type === 'tool_call') {
          const pkgName = ev.args?.name || ev.args?.product || '';
          logEvent('tool_call', `${ev.tool || ''} ${pkgName}`.trim());
          const p = jarApi.pillByName(pkgName);
          if (p) examinePill(p);
          drip();
        } else if (ev.type === 'tool_result') {
          const pkgName = ev.args?.name || ev.args?.product || '';
          logEvent('tool_result', `${ev.tool || ''} ${pkgName} ${ev.ok ? 'ok' : ev.error_code || 'err'}`.trim());
          if (pkgName) {
            emitFloatChip(pkgName, ev.ok ? 'safe' : 'unchecked', ev.ok ? '' : ' · 확인 못 함');
          }
        } else if (ev.type === 'judgment') {
          const pkgs = ev.packages || [];
          violatedNames = ev.violations || [];
          for (const item of pkgs) {
            const p = jarApi.pillByName(item.name);
            if (p) p.it.sev = sevKey(item.severity);
          }
          logEvent('judgment', `${pkgs.length}개 판정 (위반 ${violatedNames.length})`);
          docAct.nod();
        } else if (ev.type === 'replan') {
          logEvent('replan', ev.python ? `Python ${ev.python}` : ev.result || 'hold');
          docAct.tilt();
          for (const vn of violatedNames) {
            shakePill(jarApi.pillByName(vn));
          }
        } else if (ev.type === 'plan_built') {
          logEvent('plan_built', `${(ev.rounds || []).length}회차`);
        } else if (ev.type === 'calendar_check') {
          blisterApi.updateCalendarCheck(ev.rounds || []);
          logEvent('calendar_check', ev.status || '');
        } else if (ev.type === 'error') {
          logEvent('error', `${ev.step || ''} ${ev.kind || ''}`.trim());
          onSay('처리 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.');
        }
      });
    } catch (err) {
      onSay(err.message || '요청을 처리하지 못했어요.');
      setState(prevState);
      return null;
    }

    onChatTurn?.(message, finalEvent);

    if (finalEvent.plan) {
      await applyPlan(finalEvent.plan);
    }

    if (finalEvent.confirmed?.length) {
      const confirmedNos = new Set(finalEvent.confirmed.map((c) => c.round_no));
      const confirmedPacks = blisterApi.getPacks().filter((pk) => confirmedNos.has(pk.round.round_no));
      await stampPacks(confirmedPacks, (roundNo) => {
        const conf = finalEvent.confirmed.find((c) => c.round_no === roundNo);
        const pack = confirmedPacks.find((pk) => pk.round.round_no === roundNo);
        if (pack && conf?.calendar_event) {
          pack.redrawLabel({ stamped: true, reserved: true });
        }
        logEvent('tool_result', `confirm ${roundNo}회차`);
      });
      docAct.wave();
      onStatus('처방 확정', 3);
      setState('done');
    } else if (finalEvent.plan?.rounds?.length) {
      docAct.hop();
      onStatus('처방 완료', 3);
      setState('planned');
    } else {
      setState(currentPackages.length ? 'ready' : 'idle');
    }

    if (finalEvent.answer) {
      onSay(finalEvent.answer);
    }
    return finalEvent;
  }

  async function runVisit() {
    if (!currentPackages.length) {
      onSay('먼저 requirements.txt를 올려 주세요.');
      onUploadRequest?.();
      return;
    }
    await sendChatMessage('패치 계획 짜줘');
  }

  async function confirmPlan() {
    if (state !== 'planned') return;
    await sendChatMessage('확정해줘');
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
      if (it.status === 'pending') return `${it.name} ${it.cur}`;
      if (it.status === 'next') return `${it.name} · 다음 진료`;
      if (it.status === 'unchecked') return `${it.name} · 확인 못 함`;
      if (it.status === 'held') return `${it.name} · 보류`;
      return `${it.name} ${it.cur}`;
    }
    if (d.kind === 'blister') {
      const r = currentPlan?.rounds?.find((x) => x.round_no === d.round);
      return r ? `${d.round}회차 · ${r.date}` : `${d.round}회차`;
    }
    if (d.kind === 'egg') return EGGS[d.egg].tip;
    return {
      chart: '진료 기록',
      doctor: '닥터 패치',
      jar: currentPackages.length ? '접수된 패키지' : 'requirements.txt 올리기',
      stamp: '확정 도장',
      tray: '곡반 · 패치 필요 없음',
      calendar: '진료 예약 · 달력',
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
      if (state === 'running' || state === 'confirming') {
        onSay('진료 중엔 잠깐만요. 금방 끝납니다.');
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
      onOpenSheet({ kind: 'item', item: p.it, plan: currentPlan, color: SEV[sevKey(p.it.sev)][0] });
    } else if (d.kind === 'blister') {
      onOpenSheet({ kind: 'round', roundNo: d.round, plan: currentPlan, color: COLOR.ink });
    } else if (d.kind === 'chart') {
      onOpenSheet({ kind: 'log', logs: [...logs], color: COLOR.teal });
    } else if (d.kind === 'tray') {
      if (!currentPlan) onSay('곡반은 건강한 녀석들 자리입니다.');
      else onOpenSheet({ kind: 'tray', plan: currentPlan, color: COLOR.teal });
    } else if (d.kind === 'doctor') {
      docAct.hop();
      onSay(QUIPS[Math.floor(Math.random() * QUIPS.length)]);
    } else if (d.kind === 'jar') {
      if (!currentPackages.length) {
        onUploadRequest?.();
      } else if (currentPlan) {
        onOpenSheet({ kind: 'jar', plan: currentPlan, color: COLOR.ink });
      } else {
        onSay(`접수된 패키지 ${currentPackages.length}개입니다. 진료를 시작해 보세요.`);
      }
    } else if (d.kind === 'stamp') {
      if (state === 'planned') confirmPlan();
      else onSay('도장은 처방이 나온 뒤에 찍습니다.');
    } else if (d.kind === 'calendar') {
      onOpenSheet({ kind: 'calendar', color: COLOR.teal });
    }
  };

  let konamiAt = 0;
  let typed = '';
  const onKeyDown = (e) => {
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

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
  onSay('어서 오세요. requirements.txt를 올려 주세요.');

  function frame(now) {
    const t = now / 1000;
    const reduced = isReduced();
    stepTweens(now);
    updateControlsAndRender(now);

    tickDoctor(t, reduced, controls.getAzimuthalAngle());
    tickEggs(t);

    const pills = jarApi.getPills();
    if (!reduced) {
      for (const p of pills) {
        if (p.inJar && (state === 'idle' || state === 'ready')) {
          p.inner.rotation.z = Math.sin(t * 1.6 + p.phase) * 0.08;
        }
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
        name: p.tagText || p.it.name,
        color: SEV[sevKey(p.it.sev)][0],
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
    loadPackages,
    sendChatMessage,
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
