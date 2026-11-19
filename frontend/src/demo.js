export const SEV = {
  critical: ['#E5484D', 'CRITICAL'],
  high: ['#F59E0B', 'HIGH'],
  moderate: ['#F5C518', 'MODERATE'],
  low: ['#3B82F6', 'LOW'],
  unknown: ['#A3AEB0', '미상'],
  safe: ['#3E9E98', '안전'],
  unchecked: ['#A3AEB0', '확인 못 함'],
  checked: ['#5E7F86', '조회 완료'],
  held: ['#7C5CD6', '보류'],
  next: ['#16313A', '다음 진료'],
};

export function sevKey(sev) {
  if (!sev) return 'unknown';
  const k = String(sev).toLowerCase();
  return SEV[k] ? k : 'unknown';
}

export const COLOR = {
  replan: '#7C5CD6',
  ink: '#16313A',
  teal: '#3E9E98',
  mint: '#B9E2D9',
  coral: '#F2734A',
  well: '#C9D3D4',
};

export const POPULAR = new Set([
  'python', 'requests', 'urllib3', 'django', 'flask',
  'numpy', 'pandas', 'pytest', 'pyyaml', 'jinja2',
  'fastapi', 'pydantic', 'starlette', 'uvicorn', 'scipy',
  'matplotlib', 'pillow', 'celery', 'cryptography', 'certifi',
]);

export const QUIPS = [
  '허허, 저 말입니까? 이 일만 삼십 년째입니다.',
  '알약은 눌러야 나옵니다. 세상 이치죠.',
  '미상은 미상입니다. 지어내진 않아요.',
  '안경 너머로 다 보입니다. 버전이 오래됐군요.',
  '휠을 굴려 보세요. 진료실이 더 넓답니다.',
];

// 야간 당직 진료실 (숨은 것 16/16을 다 찾으면 열림)
export const QUIPS_NIGHT = [
  '이 시간에 찾아오는 서버는 대개 사연이 있더군요.',
  '밤에는 급한 패치만 봅니다. 나머지는 아침에 하시죠.',
  '야간 배포는 다음 날 아침에 꼭 후회가 따라옵니다.',
  '모자는 못 본 척해 주세요. 당직 서는 사람의 특권입니다.',
  '로그도 이 시간엔 조용하군요. 좋은 징조입니다.',
];

export const NIGHT_LINES = {
  unlock: '허허, 숨은 걸 전부 찾아내셨군요. 이 정도 눈썰미면 야간 당직을 맡겨도 되겠습니다. 불 좀 낮추죠.',
  toNight: '슬슬 야간 진료로 넘어가죠. 불은 제가 낮추겠습니다.',
  toDay: '벌써 아침이군요. 낮 진료 시작합니다.',
  greeting: '어서 오세요, 야간 진료실입니다. 이 시간에 오신 걸 보니 급한 서버군요. requirements.txt부터 보여 주시죠.',
};

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
  'bottle', 'tray', 'iv', 'chart', 'stamp', 'doctor', 'night',
];

export const LAYOUT = {
  bottle: [-5.9, 0, -1.9],
  tray: [-5.4, 0.075, 2.7],
  chart: [7.1, 0, 0.1, -0.08],
  stamp: [8.2, 0, 3.0],
  iv: [-12.0, -8.05, -9.6, 0, 3.3],
  pad: { x: 0.6, z: 0.9, w: 10.0, d: 4.8 },
  doctor: { x: 0, z: -7.0, seat: -2.6, scale: 2.8 },
};

export const CELL = { w: 1.4, d: 1.24 };
export const END_W = 1.2;
