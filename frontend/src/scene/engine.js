import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export const BASE = new THREE.Vector3(0, 13.2, 18.6);
export const TARGET = new THREE.Vector3(0, 0.6, -1.4);
export const BASE_DIST = BASE.distanceTo(TARGET);

const ROOM = { x: 23.5, y: 16.5, z: 40 }; // 카메라가 진료실 밖으로 나가지 않는 한계
const TARGET_BOX = new THREE.Box3(new THREE.Vector3(-14, -3, -10), new THREE.Vector3(14, 6, 6));
const CAMERA_BOX = new THREE.Box3(new THREE.Vector3(-ROOM.x, -6.5, -11), new THREE.Vector3(ROOM.x, ROOM.y, ROOM.z));

export function createEngine(canvas, tween, isReduced) {
  const params = new URLSearchParams(location.search);
  const forceHigh = params.get('hq') === '1';
  const forceLow = params.get('lq') === '1';
  const isMobile = innerWidth < 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
  const isWindows = /\bWin/i.test(navigator.platform || navigator.userAgent);
  let lowTier = forceLow || isMobile || (isWindows && !forceHigh);

  const getTargetPixelRatio = () => {
    if (lowTier) return Math.min(devicePixelRatio, forceLow ? 1.0 : 1.2);
    if (innerWidth * innerHeight > 2200000) return Math.min(devicePixelRatio, 1.25);
    return Math.min(devicePixelRatio, 1.5);
  };

  // 낮은 품질(Windows·모바일 기본, ?lq=1)은 MSAA를 끈다 — 고해상도 Windows 화면에서 픽셀 부하가 크다
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !lowTier, powerPreference: 'high-performance' });
  renderer.setPixelRatio(getTargetPixelRatio());
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = lowTier ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#CBEAE2');
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.42;

  const camera = new THREE.PerspectiveCamera(36, 1, 0.5, 150);
  let distScale = 1;

  const hemi = new THREE.HemisphereLight(0xffffff, 0x9fcfc4, 0.6);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff8ef, 2.1);
  key.position.set(-7, 20, 12);
  key.castShadow = true;
  const initShadowSize = lowTier ? 1024 : 2048;
  key.shadow.mapSize.set(initShadowSize, initShadowSize);
  Object.assign(key.shadow.camera, { left: -20, right: 24, top: 18, bottom: -18, near: 1, far: 70 });
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 0.025;
  scene.add(key);

  const windowLight = new THREE.DirectionalLight(0xe3f6ff, 0.7);
  windowLight.position.set(14, 8, -16);
  scene.add(windowLight);

  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(TARGET);
  Object.assign(controls, {
    enableDamping: !isReduced(),
    dampingFactor: 0.08,
    rotateSpeed: 0.55,
    zoomSpeed: 0.8,
    panSpeed: 0.7,
    screenSpacePanning: true,
    minDistance: BASE_DIST * 0.4,
    maxDistance: BASE_DIST * 1.7,
    minPolarAngle: 0.28,
    maxPolarAngle: 1.36,
    minAzimuthAngle: -0.95,
    maxAzimuthAngle: 0.95,
    touches: { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN },
  });

  const homeView = () => ({
    pos: TARGET.clone().add(BASE.clone().sub(TARGET).multiplyScalar(distScale)),
    at: TARGET.clone(),
  });

  function resetView() {
    const from = { pos: camera.position.clone(), at: controls.target.clone() };
    const to = homeView();
    tween(700, (t) => {
      camera.position.lerpVectors(from.pos, to.pos, t);
      controls.target.lerpVectors(from.at, to.at, t);
    });
  }

  let composer = null;
  let useAO = forceHigh && !forceLow;
  if (useAO) {
    try {
      composer = new EffectComposer(renderer);
      composer.addPass(new RenderPass(scene, camera));
      const ao = new GTAOPass(scene, camera, innerWidth, innerHeight);
      ao.updateGtaoMaterial({ radius: 0.9, distanceExponent: 1.2, thickness: 1.2, scale: 1.1 });
      ao.blendIntensity = 0.85;
      composer.addPass(ao);
      composer.addPass(new OutputPass());
    } catch (err) {
      console.warn('AO 없이 그립니다', err);
      composer = null;
      useAO = false;
    }
  }

  function downgradeQuality() {
    if (useAO) {
      useAO = false;
      return;
    }
    if (!lowTier) {
      lowTier = true;
      renderer.setPixelRatio(1.0);
      renderer.setSize(innerWidth, innerHeight, false);
      renderer.shadowMap.type = THREE.PCFShadowMap;
      renderer.shadowMap.needsUpdate = true;
      key.shadow.mapSize.set(1024, 1024);
      key.shadow.map?.dispose();
      key.shadow.map = null;
    }
  }

  function resize() {
    const w = innerWidth;
    const h = innerHeight;
    renderer.setPixelRatio(getTargetPixelRatio());
    renderer.setSize(w, h, false);
    if (useAO) composer?.setSize(w, h);
    camera.aspect = w / h;
    distScale = Math.min(2.2, Math.max(1, 1.55 / camera.aspect));
    controls.maxDistance = BASE_DIST * 1.7 * distScale;
    camera.updateProjectionMatrix();
  }
  resize();
  camera.position.copy(homeView().pos);

  const tmpV = new THREE.Vector3();
  function toScreen(v) {
    tmpV.copy(v).project(camera);
    return [(tmpV.x + 1) / 2 * innerWidth, (1 - tmpV.y) / 2 * innerHeight, tmpV.z < 1];
  }

  const perf = { n: 0, sum: 0, last: performance.now(), downgraded: false, frame: 0 };
  // ?debug=1: 왼쪽 아래에 프레임 시간·draw call·삼각형 수 (Windows에서 원인 찾기용)
  const debugEl = params.get('debug') === '1' ? document.createElement('div') : null;
  if (debugEl) {
    Object.assign(debugEl.style, { position: 'fixed', left: '8px', bottom: '8px', zIndex: 99, padding: '4px 8px',
      font: '11px monospace', background: 'rgba(0,0,0,.7)', color: '#0f0', borderRadius: '6px', pointerEvents: 'none' });
    document.body.appendChild(debugEl);
  }
  let debugAcc = 0;
  let debugN = 0;
  function updateControlsAndRender(now) {
    if (window.__freeze) {
      camera.position.copy(window.__freeze.pos);
      camera.lookAt(window.__freeze.at);
    } else {
      controls.enableDamping = !isReduced();
      controls.update();
      TARGET_BOX.clampPoint(controls.target, controls.target);
      CAMERA_BOX.clampPoint(camera.position, camera.position);
      camera.lookAt(controls.target);
    }

    const dt = now - perf.last;
    perf.last = now;
    if (!perf.downgraded && dt > 0 && dt < 200) {
      perf.sum += dt;
      perf.n++;
      if (perf.n === 90) {
        const avg = perf.sum / 90;
        perf.sum = 0;
        perf.n = 0;
        if (avg > 24) {
          downgradeQuality();
          if (lowTier && !useAO) perf.downgraded = true;
        }
      }
    }
    // 낮은 품질: 그림자는 3프레임마다 다시 그린다 (그림자 패스가 장면을 한 번 더 그림)
    perf.frame++;
    if (lowTier) {
      renderer.shadowMap.autoUpdate = false;
      if (perf.frame % 3 === 0) renderer.shadowMap.needsUpdate = true;
    } else {
      renderer.shadowMap.autoUpdate = true;
    }
    if (useAO && composer) composer.render();
    else renderer.render(scene, camera);
    if (debugEl && dt > 0 && dt < 500) {
      debugAcc += dt;
      debugN++;
      if (debugN >= 30) {
        const i = renderer.info.render;
        debugEl.textContent = `${(debugAcc / debugN).toFixed(1)}ms (${Math.round(1000 / (debugAcc / debugN))}fps) · `
          + `calls ${i.calls} · tris ${(i.triangles / 1000).toFixed(0)}k · px ${renderer.getPixelRatio().toFixed(2)} · `
          + `${lowTier ? 'low' : 'high'}${useAO ? '+AO' : ''}`;
        debugAcc = 0;
        debugN = 0;
      }
    }
  }

  function dispose() {
    const geos = new Set();
    const mats = new Set();
    const texs = new Set();
    if (scene.environment) texs.add(scene.environment);
    scene.traverse((o) => {
      if (o.geometry) geos.add(o.geometry);
      if (o.material) {
        const list = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of list) {
          mats.add(m);
          for (const v of Object.values(m)) {
            if (v && v.isTexture) texs.add(v);
          }
        }
      }
    });
    geos.forEach((g) => g.dispose());
    texs.forEach((t) => t.dispose());
    mats.forEach((m) => m.dispose());
    controls.dispose();
    composer?.dispose();
    pmrem.dispose();
    renderer.dispose();
  }

  return {
    renderer,
    scene,
    camera,
    lights: { hemi, key, windowLight }, // 야간 모드가 낮↔밤으로 바꾼다 (night.js)
    controls,
    getDistScale: () => distScale,
    getUseAO: () => useAO,
    resetView,
    resize,
    toScreen,
    updateControlsAndRender,
    dispose,
  };
}
