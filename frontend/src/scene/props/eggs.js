import * as THREE from 'three';
import { COLOR } from '../../demo.js';
import { FONT, mergeStatic, prep, textTexture } from '../utils.js';

export function setupEggs(world, M, addPick) {
  world.add(prep(M.eggs));

  const signTex = textTexture(400, 400, (c, w) => {
    c.fillStyle = '#FFFFFF';
    c.fillRect(0, 0, w, 400);
    c.fillStyle = COLOR.ink;
    c.textAlign = 'center';
    c.font = FONT(700, 64, true);
    c.fillText('FRI', w / 2, 150);
    c.font = FONT(700, 40, true);
    c.fillText('DEPLOY', w / 2, 205);
    c.strokeStyle = '#E5484D';
    c.lineWidth = 26;
    c.beginPath();
    c.arc(w / 2, 165, 128, 0, Math.PI * 2);
    c.stroke();
    c.beginPath();
    c.moveTo(w / 2 - 90, 255);
    c.lineTo(w / 2 + 90, 75);
    c.stroke();
    c.fillStyle = COLOR.ink;
    c.font = FONT(700, 38);
    c.fillText('금요일 배포 금지', w / 2, 362);
  });
  M.eggs.getObjectByName('SignFace').material = new THREE.MeshStandardMaterial({
    map: signTex.tex,
    roughness: 0.6,
  });

  const secondPivot = M.eggs.getObjectByName('SecondPivot');
  const eggNodes = {};
  M.eggs.traverse((o) => {
    if (o.name.startsWith('Egg_')) eggNodes[o.name.slice(4)] = o;
  });
  for (const [id, node] of Object.entries(eggNodes)) {
    mergeStatic(node, [secondPivot]);
    addPick(node, 'egg', { egg: id });
  }

  const eyeHit = new THREE.Mesh(
    new THREE.BoxGeometry(3.2, 4.4, 0.3),
    new THREE.MeshBasicMaterial({ visible: false }),
  );
  eyeHit.position.set(-6.5, 5.6, -12.95);
  world.add(eyeHit);
  addPick(eyeHit, 'egg', { egg: 'eyechart' });

  function tick(t) {
    if (secondPivot) {
      secondPivot.rotation.z = t % 1 < 0.12 ? -0.1 : 0; // 멈춘 시계: 07초에서 넘어가려다 되돌아옴
    }
  }

  return { eggNodes, tick };
}
