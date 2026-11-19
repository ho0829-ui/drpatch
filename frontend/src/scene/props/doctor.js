import * as THREE from 'three';
import { LAYOUT } from '../../demo.js';
import { ease, mergeStatic, prep } from '../utils.js';

export function setupDoctor(world, M, addPick, tween, sleep) {
  const D = LAYOUT.doctor;
  const doctor = new THREE.Group();
  doctor.position.set(D.x, D.seat - 0.14 * D.scale, D.z);
  doctor.scale.setScalar(D.scale);
  world.add(doctor);
  doctor.add(prep(M.doctor));

  const docBody = M.doctor.getObjectByName('Body');
  const BODY_Y = docBody.position.y;
  const eyes = ['EyeL', 'EyeR'].map((n) => M.doctor.getObjectByName(n));
  const EYE_Y = eyes.map((e) => e.scale.y);
  const arms = ['ArmL', 'ArmR'].map((n) => M.doctor.getObjectByName(n));
  const ARM0 = arms.map((a) => a.rotation.clone());
  const REST = -1.0; // 팔을 앞으로 내밀어 손을 책상에
  arms.forEach((a, i) => (a.rotation.x = ARM0[i].x + REST));

  addPick(doctor, 'doctor');
  mergeStatic(docBody, [...eyes, ...arms]);

  const docAct = {
    nod: async () => {
      await tween(180, (p) => (docBody.rotation.x = 0.16 * p));
      await tween(260, (p) => (docBody.rotation.x = 0.16 * (1 - p)));
    },
    tilt: async () => {
      await tween(300, (p) => (docBody.rotation.z = 0.22 * p), ease.out);
      await sleep(1100);
      await tween(300, (p) => (docBody.rotation.z = 0.22 * (1 - p)));
    },
    hop: () => tween(420, (p) => (docBody.position.y = BODY_Y + Math.sin(p * Math.PI) * 0.18), ease.lin),
    wave: () =>
      tween(
        1200,
        (p) => {
          const s = Math.sin(p * Math.PI);
          arms[1].rotation.x = ARM0[1].x + REST - s * 1.6;
          arms[1].rotation.z = ARM0[1].z + Math.sin(p * Math.PI * 6) * 0.3 * s;
        },
        ease.lin,
      ),
    point: () =>
      tween(
        900,
        (p) => {
          const s = Math.sin(p * Math.PI);
          arms[0].rotation.x = ARM0[0].x + REST - s * 0.5;
        },
        ease.inOut,
      ),
    no: async () => {
      await tween(700, (p) => (docBody.rotation.y = Math.sin(p * Math.PI * 4) * 0.35 * (1 - p)), ease.lin);
      docBody.rotation.y = 0;
    },
    dance: async () => {
      await tween(
        2600,
        (p) => {
          const s = Math.sin(p * Math.PI);
          docBody.rotation.z = Math.sin(p * Math.PI * 8) * 0.22 * s;
          docBody.position.y = BODY_Y + Math.abs(Math.sin(p * Math.PI * 8)) * 0.25 * s;
          arms.forEach((a, i) => {
            a.rotation.x = ARM0[i].x + REST - s * (1.4 + 0.5 * Math.sin(p * Math.PI * 8 + i * Math.PI));
          });
        },
        ease.lin,
      );
      docBody.rotation.z = 0;
      docBody.position.y = BODY_Y;
      arms.forEach((a, i) => (a.rotation.x = ARM0[i].x + REST));
    },
  };

  let blinkAt = 2;
  let blinkUntil = 0;
  const headPos = new THREE.Vector3();

  function tick(t, reduced, azimuth) {
    if (!reduced) {
      const breathe = Math.sin(t * 1.8);
      docBody.scale.set(1 + breathe * 0.008, 1 + breathe * 0.014, 1 + breathe * 0.008);
      doctor.rotation.y += (azimuth * 0.35 - doctor.rotation.y) * 0.05;
      if (t > blinkAt) {
        blinkUntil = t + 0.13;
        blinkAt = t + 2.8 + Math.random() * 3;
      }
    }
    eyes.forEach((e, i) => (e.scale.y = t < blinkUntil ? EYE_Y[i] * 0.12 : EYE_Y[i]));
  }

  function getBubbleAnchor(camera) {
    headPos.set(-0.75, 2.25, 0);
    doctor.localToWorld(headPos);
    headPos.project(camera);
    return {
      right: innerWidth - ((headPos.x + 1) / 2) * innerWidth + 10,
      top: ((1 - headPos.y) / 2) * innerHeight,
    };
  }

  return { doctor, docBody, docAct, tick, getBubbleAnchor };
}
