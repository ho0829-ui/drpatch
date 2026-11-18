import * as THREE from 'three';
import { END_W, LAYOUT } from '../../demo.js';
import { ease, prep } from '../utils.js';

export function setupStamp(world, M, addPick, tween) {
  const STAMP_HOME = new THREE.Vector3(...LAYOUT.stamp);
  const stamp = prep(M.stamp);
  stamp.position.copy(STAMP_HOME);
  world.add(stamp);
  addPick(stamp, 'stamp');

  async function stampPacks(packs, onStamped) {
    for (const bl of packs) {
      const at = bl.group.localToWorld(new THREE.Vector3(END_W / 2, 0, 0));
      const from = stamp.position.clone();
      await tween(600, (t) => {
        stamp.position.lerpVectors(from, at, t);
        stamp.position.y = Math.sin(t * Math.PI) * 1.8 + t * 0.6;
      });
      await tween(160, (t) => (stamp.position.y = 0.6 - t * 0.45), ease.lin);
      bl.label.redraw(true);
      onStamped?.(bl.round.round_no ?? bl.round.no); // 실제 API 필드는 round_no
      await tween(220, (t) => (stamp.position.y = 0.15 + t * 0.6), ease.out);
    }
    const from = stamp.position.clone();
    await tween(700, (t) => {
      stamp.position.lerpVectors(from, STAMP_HOME, t);
      stamp.position.y += Math.sin(t * Math.PI) * 0.8 * (1 - t);
    });
    stamp.position.y = 0;
  }

  return { stamp, stampPacks };
}
