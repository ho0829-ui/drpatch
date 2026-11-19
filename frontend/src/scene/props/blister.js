import * as THREE from 'three';
import { CELL, COLOR, END_W, LAYOUT } from '../../demo.js';
import { disposeOwned, FONT, mergeStatic, prep, textTexture } from '../utils.js';

function shortDate(iso) {
  if (!iso) return '미정';
  const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[2]}/${m[3]}` : String(iso);
}

function formatWin(win) {
  if (!win || !win.start || !win.end) return '';
  return `${win.start.slice(0, 5)}–${win.end.slice(0, 5)}`;
}

export function setupBlisters(world, M, addPick, removePick) {
  let packs = [];

  function clearPacks() {
    for (const p of packs) {
      removePick?.(p.group);
      world.remove(p.group);
      disposeOwned(p.group, [p.label.tex, p.labelMat, ...p.slots.map((s) => s.wellMat)]);
    }
    packs = [];
  }

  function rebuild(rounds = [], windowObj = null) {
    clearPacks();
    if (!rounds.length) return packs;

    const perRound = Math.max(1, ...rounds.map((r) => (r.items ? r.items.length : 0)));
    const cols = Math.ceil(perRound / 2);
    const packW = END_W + cols * CELL.w;
    const packD = CELL.d * 2;
    const winText = formatWin(windowObj);

    packs = rounds.slice(0, 3).map((r) => {
      const g = new THREE.Group();
      world.add(g);
      const end = prep(M.blister_end.clone(true));
      end.position.x = END_W / 2;
      g.add(end);

      const state = {
        no: r.round_no,
        date: r.date,
        movedFrom: r.moved_from || null,
        winText,
        stamped: false,
        reserved: false,
      };

      const labelMesh = end.getObjectByName('Label');
      const label = textTexture(220, 520, (c, w, h) => {
        c.fillStyle = COLOR.ink;
        c.beginPath();
        c.roundRect(0, 0, w, h, 30);
        c.fill();
        c.fillStyle = '#fff';
        c.textAlign = 'center';
        c.font = FONT(700, 110, true);
        c.fillText(String(state.no), w / 2, 150);
        c.font = FONT(600, 38);
        c.fillText('회차', w / 2, 208);
        c.font = FONT(700, 42, true);
        c.fillText(shortDate(state.date), w / 2, 295);

        if (state.movedFrom) {
          c.font = FONT(600, 24, true);
          c.fillStyle = '#F5C518';
          c.fillText(`↻ ${shortDate(state.movedFrom)}`, w / 2, 336);
        }

        if (state.winText) {
          c.font = FONT(400, 26, true);
          c.fillStyle = COLOR.mint;
          c.fillText(state.winText, w / 2, state.movedFrom ? 378 : 350);
        }

        if (state.stamped) {
          c.save();
          c.translate(w / 2, 452);
          c.rotate(-0.25);
          c.strokeStyle = COLOR.coral;
          c.lineWidth = 8;
          c.beginPath();
          c.roundRect(-88, -36, 176, 72, 18);
          c.stroke();
          c.fillStyle = COLOR.coral;
          c.font = FONT(700, 34, true);
          c.fillText(state.reserved ? '예약됨' : 'Rx 확정', 0, 12);
          c.restore();
        }
      });
      const labelMat = (labelMesh.material = new THREE.MeshStandardMaterial({ map: label.tex, roughness: 0.6 }));
      mergeStatic(end);

      const slots = [];
      for (let k = 0; k < perRound; k++) {
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

      addPick(g, 'blister', { round: state.no });
      return {
        group: g,
        round: r,
        state,
        label,
        labelMat,
        slots,
        used: 0,
        redrawLabel(opts = {}) {
          Object.assign(state, opts);
          label.redraw();
        },
      };
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

  function updateCalendarCheck(rounds = []) {
    for (const r of rounds) {
      const pack = packs.find((p) => p.round.round_no === r.round_no);
      if (pack) {
        pack.round.date = r.date;
        pack.round.moved_from = r.moved_from || null;
        pack.redrawLabel({ date: r.date, movedFrom: r.moved_from || null });
      }
    }
  }

  return {
    getPacks: () => packs,
    rebuild,
    clearPacks,
    updateCalendarCheck,
  };
}

export function worldOfSlot(bl, slot) {
  return bl.group.localToWorld(new THREE.Vector3(slot.x, 0.27, slot.z));
}
