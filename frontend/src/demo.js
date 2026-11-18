// 예시 데이터 (실제 조회 아님) — T1 시제품 기준
export const PER_ROUND = 4;

export const SEV = {
  critical: ['#E5484D', 'CRITICAL'],
  high: ['#F59E0B', 'HIGH'],
  moderate: ['#F5C518', 'MODERATE'],
  low: ['#3B82F6', 'LOW'],
  unknown: ['#A3AEB0', '미상'],
  safe: ['#3E9E98', '안전'],
};

export const COLOR = {
  replan: '#7C5CD6',
  ink: '#16313A',
  teal: '#3E9E98',
  mint: '#B9E2D9',
  coral: '#F2734A',
  well: '#C9D3D4',
};

export const ROUNDS = [
  { no: 1, date: '11/21', full: '2026-11-21', win: '22:00–24:00' },
  { no: 2, date: '12/05', full: '2026-12-05', win: '22:00–24:00' },
  { no: 3, date: '12/19', full: '2026-12-19', win: '22:00–24:00' },
];

const P = (name, cur, tgt, sev, round, reason, note, flags = [], extra = {}) => ({
  name,
  cur,
  tgt,
  sev,
  round,
  reason,
  note,
  flags,
  ...extra,
});

export const ITEMS = [
  P('Python', '3.8', '3.11', 'high', 1, '지원 종료일이 지났어요.', '오늘의 주인공이죠. 이걸 먼저 올려야 나머지가 따라옵니다.', ['큰 변경'], { kind: 'runtime' }),
  P('urllib3', '1.24.1', '2.2.x', 'critical', 1, '알려진 취약점이 있어요.', '1.24.1이라니… 꽤 오래 방치하셨군요.', ['큰 변경']),
  P('requests', '2.19.0', '2.32.x', 'critical', 1, '알려진 취약점이 있어요.', '자주 쓰는 녀석일수록 먼저 챙겨야 합니다.'),
  P('PyYAML', '5.1', '6.0.x', 'critical', 1, '알려진 취약점이 있어요.', 'YAML은 늘 조심해서 다뤄야죠.', ['큰 변경']),
  P('Django', '2.2.0', '4.2.x', 'high', 2, 'Python 업그레이드 뒤에 올릴 수 있어요.', '처음엔 5.2를 드리려 했는데 Python 3.8로는 못 넘어가더군요. 그래서 2회차입니다.', ['큰 변경', '처방 변경']),
  P('Jinja2', '2.10', '3.1.x', 'moderate', 2, '알려진 취약점이 있어요.', '급하진 않지만 미루면 서운해합니다.', ['큰 변경']),
  P('Flask', '1.0.2', '3.0.x', 'low', 2, '알려진 취약점이 있어요.', '가벼운 증상입니다. 그래도 처방은 처방이죠.', ['큰 변경']),
  P('numpy', '1.16.0', '1.24.x', 'unknown', 2, '취약점은 있지만 심각도 정보가 없어요.', '등급을 못 찾았어요. 모르는 건 모른다고 적습니다.'),
  P('pandas', '0.24.2', '2.0.x', 'moderate', 3, '알려진 취약점이 있어요.', 'numpy랑 같이 다니는 녀석이라 3회차로 모셨습니다.', ['큰 변경']),
  P('pytest', '4.6.0', '8.3.x', 'low', 3, '알려진 취약점이 있어요.', '테스트 도구도 아프면 서럽습니다.', ['큰 변경']),
  P('gunicorn', '19.9.0', '23.0.x', 'moderate', 3, '알려진 취약점이 있어요.', '서버 문지기죠. 미루지 마세요.', ['큰 변경']),
  P('celery', '4.3.0', '5.4.x', 'low', 3, '알려진 취약점이 있어요.', '일꾼도 건강검진은 받아야죠.', ['큰 변경']),
  P('click', '8.1.7', '8.1.7', 'safe', null, '최신이고 알려진 취약점이 없어요.', '아주 건강합니다. 돌려보내죠.', [], { status: 'safe' }),
  P('idna', '3.7', '3.7', 'safe', null, '최신이고 알려진 취약점이 없어요.', '깨끗합니다.', [], { status: 'safe' }),
  P('six', '1.16.0', '1.16.0', 'safe', null, '최신이고 알려진 취약점이 없어요.', '오래됐지만 멀쩡한 친구예요.', [], { status: 'safe' }),
  P('itsdangerous', '2.2.0', '2.2.0', 'safe', null, '최신이고 알려진 취약점이 없어요.', '이름은 무섭지만 괜찮습니다.', [], { status: 'safe' }),
  P('lxml', '4.3.0', '5.3.x', 'low', null, '회차 3개가 꽉 차서 다음 진료로 미뤘어요.', '오늘은 자리가 없네요. 다음에 꼭 오세요.', [], { status: 'next' }),
].map((it) => ({ status: 'patch', kind: 'package', ...it }));

export const PATCH = ITEMS.filter((i) => i.status === 'patch');
export const TOOL = (it) => (it.kind === 'runtime' ? 'get_eol' : 'get_vulns');

export const QUIPS = [
  '허허, 저 말입니까? 이 일만 삼십 년째입니다.',
  '알약은 눌러야 나옵니다. 세상 이치죠.',
  '미상은 미상입니다. 지어내진 않아요.',
  '안경 너머로 다 보입니다. 버전이 오래됐군요.',
  '휠을 굴려 보세요. 진료실이 더 넓답니다.',
];

export const EGGS = {
  hotfix: { tip: '해열제 HOTFIX', say: '열 날 때 한 알. 핫픽스는 원래 급할 때 먹는 겁니다. 부작용으로 또 다른 핫픽스가 생길 수 있어요.' },
  rollback: { tip: '되돌림 시럽 ROLLBACK', say: '어제 배포가 체했으면 이걸로 되돌립니다. 백업이 있을 때만 효과가 있어요.' },
  lts: { tip: 'LTS 장기 복용약 · EXP 2038-01-19', say: '장기 지원이라 오래 드셔도 됩니다. 유통기한이 2038년 1월 19일이네요… 32비트 시계가 멈추는 날이죠.' },
  rmrf: { tip: '⚠ rm -rf /', say: '그건 처방할 수 없습니다. 절대로요. 복구 불가 부작용이 있습니다.', act: 'no' },
  duck: { tip: '고무 오리', say: '꽥. …그래서, 문제가 뭐였죠? 오리한테 설명하다 보면 답이 보일 겁니다.', act: 'squeak' },
  monkey: { tip: 'MONKEY PATCH 반창고', say: '실행 중에 급히 덧대는 반창고입니다. 언젠가는 제대로 꿰매셔야 해요.' },
  friday: { tip: '금요일 배포 금지', say: '병원 규칙입니다. 금요일 오후 배포는 주말 응급실행이에요.' },
  clock: { tip: '03:14:07에 멈춘 시계', say: '2038년 1월 19일 03:14:07 UTC. 32비트 유닉스 시간은 여기서 넘칩니다. 그래서 고장 난 채로 두었죠.' },
  devnull: { tip: '/dev/null', say: '여기 버린 건 다시 못 찾습니다. 로그도요.' },
  nodemods: { tip: 'node_modules', say: '진료실에서 제일 무거운 화분입니다. 물은 npm install로 줍니다.' },
  eyechart: { tip: '시력표', say: '맨 아래 줄까지 읽으셨다면 시력이 아주 좋으신 겁니다. D… R… P… A… T… C… H… S… U… D… O.' },
  konami: { say: '↑↑↓↓←→←→BA! 무적 모드입니다. 오늘은 버그가 없을 겁니다. 아마도요.' },
  sudo: { say: '사용자는 sudoers 파일에 없습니다. 이 일은 보고될 겁니다.' },
  diploma: { tip: '학위증 · Doctor of Patchology', say: '/dev/null 대학교 패치학 박사입니다. 졸업 논문도 /dev/null에 잘 보관돼 있죠.' },
  room200: { tip: '진료실 200호 · OK', say: '여기는 200호, 들어오시면 OK입니다. 404호는… 아직 아무도 못 찾았어요.' },
  xray: { tip: '흉부 X-ray · PROD-01', say: '갈비뼈 사이에 버그가 보이네요. 꽤 오래 산 녀석입니다. 재현이 안 돼서 아무도 못 잡았죠.' },
};

export const MODELS = [
  'room', 'ward', 'desk', 'eggs',
  'blister_cell', 'blister_end', 'capsule', 'pills',
  'bottle', 'tray', 'iv', 'chart', 'stamp', 'doctor',
];

// 배치 (three 좌표: x 오른쪽, y 위, z 사용자 쪽). design/blender/scene_preview.py와 같게.
export const LAYOUT = {
  bottle: [-5.9, 0, -1.9],
  tray: [-5.4, 0.075, 2.7], // 곡반은 패드보다 살짝 높여 겹치지 않게
  chart: [7.1, 0, 0.1, -0.08],
  stamp: [8.2, 0, 3.0],
  iv: [-12.0, -8.05, -9.6, 0, 3.3], // 높이 ≈1.3m: 책상 옆에서 튀지 않게
  pad: { x: 0.6, z: 0.9, w: 10.0, d: 4.8 },
  doctor: { x: 0, z: -7.0, seat: -2.6, scale: 2.8 },
};

export const CELL = { w: 1.4, d: 1.24 };
export const END_W = 1.2;

export const roundOf = (no) => ROUNDS.find((r) => r.no === no);
