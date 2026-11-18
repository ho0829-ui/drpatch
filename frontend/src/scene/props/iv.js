import * as THREE from 'three';
import { LAYOUT } from '../../demo.js';
import { ease, prep } from '../utils.js';

export function setupIv(world, M, tween) {
  const iv = prep(M.iv);
  const [ix, iy, iz, irot, iscale] = LAYOUT.iv;
  iv.position.set(ix, iy, iz);
  iv.rotation.y = irot;
  iv.scale.setScalar(iscale);
  world.add(iv);

  const liquid = iv.getObjectByName('Liquid');
  const LIQ_Y = liquid.scale.y;
  const drop = iv.getObjectByName('Drop');
  const DROP0 = drop.position.clone();
  const DROP_S = drop.scale.clone();
  let level = 1;

  async function drip() {
    level = Math.max(0.2, level - 0.03);
    const from = liquid.scale.y / LIQ_Y;
    tween(500, (p) => {
      liquid.scale.y = LIQ_Y * THREE.MathUtils.lerp(from, level, p);
    });
    await tween(
      420,
      (p) => {
        drop.position.y = DROP0.y - p * 0.3;
        drop.scale.copy(DROP_S).multiplyScalar(1 - p * 0.5);
      },
      ease.lin,
    );
    drop.position.copy(DROP0);
    drop.scale.copy(DROP_S);
  }

  return { drip };
}
