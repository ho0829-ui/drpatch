import * as THREE from 'three';
import { LAYOUT, POPULAR } from '../../demo.js';
import { disposeOwned, ease, mergeStatic, prep } from '../utils.js';

const JAR_SCALE = 0.72;
export const MAX_JAR_PILLS = 24; // 약병 최대 24알 (6층 × 4알)
const TRAY_SPOTS = [
  [-0.9, -0.25],
  [0, -0.3],
  [0.9, -0.25],
  [-0.45, 0.35],
  [0.45, 0.35],
  [1.25, 0.3],
];
// 곡반 자리 수만큼만 알약을 올린다. 넘친 안전 패키지는 "+N" 이름표로만 (곡반 종이에는 전부)
export const MAX_TRAY_PILLS = TRAY_SPOTS.length;

export function setupJarAndTray(world, M, addPick, removePick, tween) {
  const [bx, by, bz] = LAYOUT.bottle;
  const jar = prep(M.bottle);
  jar.position.set(bx, by, bz);
  world.add(jar);
  const lid = jar.getObjectByName('Lid');
  const LID0 = lid.position.clone();
  addPick(jar, 'jar');

  const tray = prep(M.tray);
  tray.position.set(...LAYOUT.tray);
  world.add(tray);
  addPick(tray, 'tray');

  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  let pills = [];
  let trayUsed = 0;
  let jarTotal = 0;
  let trayExtra = 0;

  function clearPills() {
    for (const p of pills) {
      removePick?.(p.root);
      world.remove(p.root);
      disposeOwned(p.root);
    }
    pills = [];
    trayUsed = 0;
    jarTotal = 0;
    trayExtra = 0;
  }

  function removePill(p) {
    pills = pills.filter((q) => q !== p);
    removePick?.(p.root);
    world.remove(p.root);
    disposeOwned(p.root);
  }

  function placeInJar(p, i) {
    const capped = Math.min(i, MAX_JAR_PILLS - 1);
    const layer = Math.floor(capped / 4);
    const k = capped % 4;
    const a = (k * Math.PI) / 2 + layer * 0.78;
    p.root.position.set(bx + Math.cos(a) * 0.55, 0.32 + layer * 0.4, bz + Math.sin(a) * 0.55);
    p.root.rotation.set(0, -a + Math.PI / 2, (rnd() - 0.5) * 0.3);
    p.root.scale.setScalar(JAR_SCALE);
  }

  function createPill(pkg, i) {
    const name = pkg.name;
    const lower = name.toLowerCase();
    const root = new THREE.Group();
    world.add(root);
    const lift = new THREE.Group();
    root.add(lift);
    const inner = new THREE.Group();
    lift.add(inner);

    const special = POPULAR.has(lower) ? M.pills.getObjectByName(`Pill_${lower}`) : null;
    const model = prep((special || M.capsule).clone(true));
    model.position.set(0, 0, 0);
    inner.add(model);
    mergeStatic(model);

    const pill = {
      it: {
        name,
        cur: pkg.version || pkg.current_version || '미상',
        tgt: pkg.target_version || null,
        sev: 'unknown',
        round: null,
        status: 'pending',
        reason: '',
        flags: [],
        eol_date: null,
        kind: lower === 'python' ? 'runtime' : 'package',
      },
      root,
      lift,
      inner,
      special: !!special,
      inJar: true,
      slot: null,
      pack: null,
      liftY: 0,
      phase: rnd() * 6,
      hasTag: false,
      tagText: null,
      jarIndex: i,
    };
    placeInJar(pill, i);
    addPick(root, 'pill', { pill });
    return pill;
  }

  function setPackages(packages = []) {
    clearPills();
    seed = 7;
    jarTotal = packages.length;
    pills = packages.slice(0, MAX_JAR_PILLS).map((pkg, i) => createPill(pkg, i));
    return pills;
  }

  function pillByName(name) {
    if (!name) return null;
    const lower = String(name).toLowerCase();
    return pills.find((p) => p.it.name.toLowerCase() === lower) || null;
  }

  function ensurePill(pkg) {
    const existing = pillByName(pkg.name);
    if (existing) return existing;
    const pill = createPill(pkg, pills.length);
    pills.push(pill);
    return pill;
  }

  function resetToJar() {
    trayUsed = 0;
    trayExtra = 0;
    const extra = pills.splice(MAX_JAR_PILLS);
    for (const p of extra) {
      removePick?.(p.root);
      world.remove(p.root);
      disposeOwned(p.root);
    }
    pills.forEach((p, i) => {
      placeInJar(p, i);
      p.root.rotation.z = 0;
      p.lift.rotation.set(0, 0, 0);
      p.inner.position.set(0, 0, 0);
      p.inner.rotation.set(0, 0, 0);
      p.inner.scale.set(1, 1, 1);
      p.inJar = true;
      p.slot = null;
      p.pack = null;
      p.hasTag = false;
      p.tagText = null;
    });
  }

  function setJarTotal(n) {
    jarTotal = Math.max(0, n);
  }

  function getOverflowCount() {
    const visibleInJar = pills.filter((p) => p.inJar).length;
    return Math.max(0, jarTotal - visibleInJar);
  }

  const jarTop = new THREE.Vector3(bx, 3.0, bz);
  // 곡반 위 알약 이름표들과 겹치지 않게 오른쪽 가장자리에 둔다 (가운데 두면 위로 밀려 약병 이름표처럼 보임)
  const trayTop = new THREE.Vector3(tray.position.x + 1.7, tray.position.y + 0.35, tray.position.z + 0.4);
  const lidTo = (open) =>
    tween(
      520,
      (t) => {
        const q = open ? t : 1 - t;
        lid.position.set(LID0.x + q * 1.0, LID0.y + q * 1.2, LID0.z);
        lid.rotation.z = -q * 0.7;
      },
      ease.out,
    );

  function nextTrayPos() {
    const [sx, sz] = TRAY_SPOTS[trayUsed++ % TRAY_SPOTS.length];
    return new THREE.Vector3(tray.position.x + sx, tray.position.y + 0.33, tray.position.z + sz);
  }

  return {
    jar,
    tray,
    getPills: () => pills,
    setPackages,
    pillByName,
    ensurePill,
    resetToJar,
    setJarTotal,
    getOverflowCount,
    removePill,
    setTrayExtra: (n) => { trayExtra = Math.max(0, n); },
    getTrayExtra: () => trayExtra,
    jarTop,
    trayTop,
    lidTo,
    nextTrayPos,
  };
}
