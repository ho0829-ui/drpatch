import * as THREE from 'three';
import { COLOR, LAYOUT } from '../../demo.js';
import { FONT, prep, textTexture } from '../utils.js';

export function setupChart(world, M, addPick, getLogs) {
  const chart = prep(M.chart);
  chart.position.set(LAYOUT.chart[0], 0, LAYOUT.chart[2]);
  chart.rotation.y = LAYOUT.chart[3];
  world.add(chart);

  const paper = textTexture(440, 560, (c, w, h) => {
    const LOG = getLogs();
    c.fillStyle = '#FFFFFF';
    c.fillRect(0, 0, w, h);
    c.fillStyle = COLOR.teal;
    c.fillRect(0, 0, w, 14);
    c.fillStyle = COLOR.ink;
    c.font = FONT(700, 34);
    c.fillText('진료 기록', 26, 92);
    c.font = FONT(400, 21, true);
    LOG.slice(-14).forEach((line, i) => {
      c.fillStyle = i === Math.min(LOG.length, 14) - 1 ? '#1F6F6B' : '#4A5759';
      c.fillText(line.slice(0, 32), 26, 140 + i * 29);
    });
    if (!LOG.length) {
      c.fillStyle = '#8A9A9C';
      c.fillText('아직 기록이 없어요', 26, 140);
    }
  });
  chart.getObjectByName('Paper').material = new THREE.MeshStandardMaterial({
    map: paper.tex,
    roughness: 0.85,
  });
  addPick(chart, 'chart');

  return {
    chart,
    redraw: () => paper.redraw(),
  };
}
