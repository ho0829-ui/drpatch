import * as THREE from 'three';
import { ITEMS, LAYOUT } from '../../demo.js';
import { ease, mergeStatic, prep } from '../utils.js';

const JAR_SCALE = 0.72;
const TRAY_SPOTS = [
  [-0.9, -0.25],
  [0, -0.3],
  [0.9, -0.25],
  [-0.45, 0.35],
  [0.45, 0.35],
  [1.25, 0.3],
];

export function setupJarAndTray(world, M, addPick, tween) {
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
  const pills = ITEMS.map((it, i) => {
    const root = new THREE.Group();
    world.add(root);
    const lift = new THREE.Group();
    root.add(lift);
    const inner = new THREE.Group();
    lift.add(inner);

    const special = M.pills.getObjectByName(`Pill_${it.name.toLowerCase()}`);
    const model = prep((special || M.capsule).clone(true));
    model.position.set(0, 0, 0);
    inner.add(model);
    mergeStatic(model);

    // 약병 안: 층마다 4알을 원 둘레 방향으로 눕혀 겹치지 않게
    const layer = Math.floor(i / 4);
    const k = i % 4;
    const a = (k * Math.PI) / 2 + layer * 0.78;
    root.position.set(bx + Math.cos(a) * 0.55, 0.32 + layer * 0.4, bz + Math.sin(a) * 0.55);
    root.rotation.set(0, -a + Math.PI / 2, (rnd() - 0.5) * 0.3);
    root.scale.setScalar(JAR_SCALE);

    const pill = {
      it,
      root,
      lift,
      inner,
      special: !!special,
      inJar: true,
      slot: null,
      pack: null,
      liftY: 0,
      phase: rnd() * 6,
      tag: null,
    };
    addPick(root, 'pill', { pill });
    return pill;
  });

  const pillByName = (n) => pills.find((p) => p.it.name === n);
  const jarTop = new THREE.Vector3(bx, 3.0, bz);
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

  let trayUsed = 0;
  function nextTrayPos() {
    const [sx, sz] = TRAY_SPOTS[trayUsed++ % TRAY_SPOTS.length];
    return new THREE.Vector3(tray.position.x + sx, tray.position.y + 0.33, tray.position.z + sz);
  }

  return { jar, tray, pills, pillByName, jarTop, lidTo, nextTrayPos };
}
