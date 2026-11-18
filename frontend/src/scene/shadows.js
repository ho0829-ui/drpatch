import * as THREE from 'three';

const FLOOR_Y = -8.05 + 0.035;

// [x, z, 폭, 깊이, 회전(y), 진하기] — three 좌표 (z = Blender -y)
const BLOBS = [
  [13.8, 15.9, 8.0, 6.6, 2.3, 0.85],   // 휠체어 몸통
  [11.2, 16.6, 3.6, 1.8, 2.3, 1.0],
  [14.8, 13.4, 3.6, 1.8, 2.3, 1.0],    // 큰 바퀴 접점
  [14.2, 19.3, 1.8, 1.8, 0, 1.0],
  [17.1, 16.7, 1.8, 1.8, 0, 1.0],      // 앞바퀴 접점
  [11.6, 3.4, 3.8, 3.8, 0, 0.9],       // /dev/null 휴지통
  [22.4, 13.0, 5.4, 5.4, 0, 0.8],      // 큰 화분
  [-13.6, -1.0, 6.6, 4.6, 0, 0.8],     // 처치 카트
  [20.6, -1.6, 8.8, 20.6, 0, 0.6],     // 진료 침대
  [-22.2, 24.0, 5.2, 16.4, 0, 0.7],    // 대기 의자
  [-12.0, -9.6, 6.4, 6.4, 0, 0.7],     // 수액 거치대
  [-22.0, -10.0, 5.6, 5.6, 0, 0.7],    // 키 체중계
  [-23.4, 1.6, 1.9, 1.9, 0, 0.8],      // 소화기
  [0, 0, 19.5, 10.4, 0, 0.45],         // 책상
];

const FLOOR_COLOR = new THREE.Color('#A9D8CD');
const SHADE = new THREE.Color('#2E5A5C');
const RINGS = [
  [1.0, 0.16],
  [0.8, 0.3],
  [0.6, 0.44],
  [0.42, 0.58],
  [0.26, 0.72],
];

/** 바닥과 같은 재질의 조금씩 어두운 불투명 타원 5겹 (접지 그림자) */
export function addGroundShadows(world) {
  const blobGeo = new THREE.CircleGeometry(0.5, 48);
  const ringMats = new Map();
  const ringMat = (t) => {
    const key = t.toFixed(3);
    if (!ringMats.has(key)) {
      ringMats.set(
        key,
        new THREE.MeshStandardMaterial({
          color: FLOOR_COLOR.clone().lerp(SHADE, t),
          roughness: 0.6,
          polygonOffset: true,
          polygonOffsetFactor: -1,
          polygonOffsetUnits: -1,
        }),
      );
    }
    return ringMats.get(key);
  };

  for (const [x, z, w, d, ry, k] of BLOBS) {
    RINGS.forEach(([f, t], i) => {
      const disc = new THREE.Mesh(blobGeo, ringMat(t * k));
      disc.rotation.set(-Math.PI / 2, 0, ry);
      disc.scale.set(w * f, d * f, 1);
      disc.position.set(x, FLOOR_Y + i * 0.004, z);
      disc.receiveShadow = true;
      disc.raycast = () => {};
      world.add(disc);
    });
  }
}
