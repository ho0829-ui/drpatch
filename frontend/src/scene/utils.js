import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch {
    return false;
  }
}

export function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
  }[c]));
}

const KEEP_CLEARCOAT = typeof location !== 'undefined' && new URLSearchParams(location.search).get('hq') === '1';

/** 굴절 유리는 장면을 한 번 더 그려서 무겁다 → 일반 반투명으로 전환.
 *  또한 clearcoat(이중 반사)는 Windows ANGLE(D3D11)에서 환경맵을 두 번 샘플링해 픽셀 부하가 크므로 ?hq=1이 아니면 끈다. */
export function prep(obj, cast = true) {
  obj.traverse((o) => {
    if (!o.isMesh) return;
    o.receiveShadow = true;
    const m = o.material;
    if (m) {
      if (m.transmission > 0) {
        m.opacity = m.transmission >= 0.9 ? 0.28 : 0.72;
        m.transmission = 0;
        m.transparent = true;
        m.depthWrite = false;
      }
      if (!KEEP_CLEARCOAT && m.clearcoat > 0) {
        m.clearcoat = 0;
      }
    }
    o.castShadow = cast && !(m && m.transparent);
  });
  return obj;
}

/** 움직이지 않는 메시는 재질별로 한 덩어리로 합친다 (draw call 감소). exclude 하위 트리는 유지. */
export function mergeStatic(parent, exclude = [], cast = true) {
  parent.updateMatrixWorld(true);
  const inv = parent.matrixWorld.clone().invert();
  const groups = new Map();
  const remove = [];
  parent.traverse((o) => {
    if (!o.isMesh) return;
    for (let a = o; a && a !== parent; a = a.parent) {
      if (exclude.includes(a)) return;
    }
    const g = o.geometry.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld));
    if (!groups.has(o.material.uuid)) {
      groups.set(o.material.uuid, { mat: o.material, geos: [] });
    }
    groups.get(o.material.uuid).geos.push(g);
    remove.push(o);
  });
  for (const o of remove) o.parent.remove(o);
  for (const { mat, geos } of groups.values()) {
    const names = ['position', 'normal', 'uv'].filter((n) => geos.every((g) => g.attributes[n]));
    let list = geos.map((g) => {
      const ng = new THREE.BufferGeometry();
      names.forEach((n) => ng.setAttribute(n, g.attributes[n]));
      if (g.index) ng.setIndex(g.index);
      return ng;
    });
    if (list.some((g) => !g.index)) {
      list = list.map((g) => (g.index ? g.toNonIndexed() : g));
    }
    const merged = mergeGeometries(list, false);
    if (!merged) continue;
    const mesh = new THREE.Mesh(merged, mat);
    mesh.receiveShadow = true;
    mesh.castShadow = cast && !mat.transparent;
    parent.add(mesh);
  }
}

export function textTexture(w, h, draw) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const g = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  tex.flipY = false; // glTF UV 기준
  const redraw = (...a) => {
    g.clearRect(0, 0, w, h);
    draw(g, w, h, ...a);
    tex.needsUpdate = true;
  };
  redraw();
  return { tex, redraw };
}

export const FONT = (wt, px, mono) =>
  `${wt} ${px}px ${mono ? '"JetBrains Mono", monospace' : '"IBM Plex Sans KR", sans-serif'}`;

export const ease = {
  inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  out: (t) => 1 - Math.pow(1 - t, 3),
  back: (t) => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  lin: (t) => t,
};

export function createTweener(isReduced) {
  const tweens = new Set();
  const tween = (dur, update, e = ease.inOut) =>
    new Promise((res) => {
      if (isReduced()) {
        update(1);
        res();
        return;
      }
      tweens.add({ t0: performance.now(), dur, update, e, res });
    });

  const stepTweens = (now) => {
    for (const tw of tweens) {
      const p = Math.min(1, (now - tw.t0) / tw.dur);
      tw.update(tw.e(p));
      if (p >= 1) {
        tweens.delete(tw);
        tw.res();
      }
    }
  };

  const sleep = (ms) => new Promise((r) => setTimeout(r, isReduced() ? Math.min(ms, 250) : ms));

  return { tween, stepTweens, sleep };
}

// 다시 만들 물체를 치울 때: mergeStatic가 만든 각자의 geometry와, 넘겨준 자기 몫의 재질·텍스처만 해제한다.
// (원본 모델과 공유하는 재질은 해제하지 않는다 — 다음 물체가 그대로 쓴다)
export function disposeOwned(root, own = []) {
  root.traverse((o) => o.isMesh && o.geometry?.dispose());
  for (const r of own) r?.dispose?.();
}
