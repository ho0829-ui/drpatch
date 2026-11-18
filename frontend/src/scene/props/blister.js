import * as THREE from 'three';
import { CELL, COLOR, END_W, LAYOUT, PER_ROUND, ROUNDS } from '../../demo.js';
import { FONT, mergeStatic, prep, textTexture } from '../utils.js';

export function setupBlisters(world, M, addPick) {
  const cols = Math.ceil(PER_ROUND / 2);
  const packW = END_W + cols * CELL.w;
  const packD = CELL.d * 2;

  const packs = ROUNDS.map((r) => {
    const g = new THREE.Group();
    world.add(g);
    const end = prep(M.blister_end.clone(true));
    end.position.x = END_W / 2;
    g.add(end);

    const labelMesh = end.getObjectByName('Label');
    const label = textTexture(220, 520, (c, w, h, stamped) => {
      c.fillStyle = COLOR.ink;
      c.beginPath();
      c.roundRect(0, 0, w, h, 30);
      c.fill();
      c.fillStyle = '#fff';
      c.textAlign = 'center';
      c.font = FONT(700, 120, true);
      c.fillText(String(r.no), w / 2, 170);
      c.font = FONT(600, 40);
      c.fillText('회차', w / 2, 230);
      c.font = FONT(700, 44, true);
      c.fillText(r.date, w / 2, 330);
      c.font = FONT(400, 28, true);
      c.fillStyle = COLOR.mint;
      c.fillText('22–24시', w / 2, 380);
      if (stamped) {
        c.save();
        c.translate(w / 2, 450);
        c.rotate(-0.25);
        c.strokeStyle = COLOR.coral;
        c.lineWidth = 8;
        c.beginPath();
        c.roundRect(-88, -38, 176, 76, 18);
        c.stroke();
        c.fillStyle = COLOR.coral;
        c.font = FONT(700, 40, true);
        c.fillText('Rx 확정', 0, 14);
        c.restore();
      }
    });
    labelMesh.material = new THREE.MeshStandardMaterial({ map: label.tex, roughness: 0.6 });
    mergeStatic(end);

    const slots = [];
    for (let k = 0; k < PER_ROUND; k++) {
      const cell = prep(M.blister_cell.clone(true));
      const x = END_W + CELL.w / 2 + Math.floor(k / 2) * CELL.w;
      const z = ((k % 2 === 0 ? -1 : 1) * CELL.d) / 2;
      cell.position.set(x, 0, z);
      g.add(cell);
      const well = cell.getObjectByName('Well');
      const wellMat = (well.material = well.material.clone());
      mergeStatic(cell);
      slots.push({ x, z, wellMat });
    }
    addPick(g, 'blister', { round: r.no });
    return { group: g, round: r, label, slots, used: 0 };
  });

  // 패드 안에 줄 바꿔 놓고, 넘치면 줄인다
  const { x: px, z: pz, w: pw, d: pd } = LAYOUT.pad;
  const gap = 0.45;
  const perRow = Math.max(1, Math.floor((pw + gap) / (packW + gap)));
  const rows = Math.ceil(packs.length / perRow);
  const s = Math.min(
    1,
    pd / (rows * packD + (rows - 1) * gap),
    pw / (Math.min(perRow, packs.length) * packW + (Math.min(perRow, packs.length) - 1) * gap),
  );
  packs.forEach((p, i) => {
    const row = Math.floor(i / perRow);
    const n = Math.min(perRow, packs.length - row * perRow);
    const col = i % perRow;
    const rowW = n * packW + (n - 1) * gap;
    p.group.scale.setScalar(s);
    p.group.position.set(
      px + (-rowW / 2 + col * (packW + gap)) * s,
      0,
      pz + (-(rows * packD + (rows - 1) * gap) / 2 + packD / 2 + row * (packD + gap)) * s,
    );
  });

  return packs;
}

export function worldOfSlot(bl, slot) {
  return bl.group.localToWorld(new THREE.Vector3(slot.x, 0.27, slot.z));
}
