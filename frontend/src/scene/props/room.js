import * as THREE from 'three';
import { FONT, mergeStatic, prep, textTexture } from '../utils.js';

export function setupRoom(world, scene, M) {
  world.add(prep(M.room, false));
  world.add(prep(M.desk));

  const bulb = M.desk.getObjectByName('LampBulb');
  if (bulb) {
    const lamp = new THREE.PointLight(0xffe7b8, 6, 14, 1.6);
    bulb.getWorldPosition(lamp.position);
    scene.add(lamp);
  }

  world.add(prep(M.ward));

  const tvTex = textTexture(850, 470, (c, w, h) => {
    c.fillStyle = '#0F3A3A';
    c.fillRect(0, 0, w, h);
    c.fillStyle = '#3E9E98';
    c.fillRect(0, 0, w, 70);
    c.fillStyle = '#FFFFFF';
    c.font = FONT(700, 34, true);
    c.fillText('DR.PATCH  진료실 200', 28, 48);
    c.fillStyle = '#B9E2D9';
    c.font = FONT(500, 30);
    c.fillText('지금 진료 중', 40, 140);
    c.fillStyle = '#FFFFFF';
    c.font = FONT(700, 170, true);
    c.fillText('042', 36, 320);
    c.fillStyle = '#B9E2D9';
    c.font = FONT(500, 28);
    c.fillText('다음 환자', 470, 140);
    c.fillStyle = '#FFFFFF';
    c.font = FONT(700, 40, true);
    c.fillText('localhost', 470, 200);
    c.fillText('127.0.0.1', 470, 252);
    c.fillStyle = '#F2734A';
    c.font = FONT(600, 26);
    c.fillText('예상 대기 0ms', 470, 320);
    c.fillStyle = '#1F6F6B';
    c.fillRect(0, h - 64, w, 64);
    c.fillStyle = '#B9E2D9';
    c.font = FONT(500, 24);
    c.fillText('손 씻기 · 금요일 배포 금지 · 백업 필수', 28, h - 22);
  });
  const tvFace = M.ward.getObjectByName('TVFace');
  if (tvFace) {
    tvFace.material = new THREE.MeshBasicMaterial({ map: tvTex.tex, toneMapped: false });
  }

  mergeStatic(M.room, [], false);
  mergeStatic(M.ward);
  mergeStatic(M.desk);
}
