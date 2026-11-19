/**
 * 입력창 글에서 조건을 미리 찾아 조건 칩에 "입력창에 있음(○)"으로 표시하고,
 * 서버에서 받은 간격·요일 조건을 표시 문자열로 바꾼다 (spec v1.20 J · v1.21 M·N).
 *
 * 정규식 패턴·예문 표·fmtSchedule 표는 tests/test_condition_preview_table.py 및
 * app/agent/schedule_text.py와 동일하게 유지한다.
 *
 * fmtSchedule 예문 표 (입력 → 기대 문자열):
 * - { interval_days: 1 } → "매일"
 * - { interval_days: 2 } → "격일"
 * - { interval_days: 7 } → "매주"
 * - { interval_days: 14 } → "격주"
 * - { interval_days: 21 } → "3주마다"
 * - { interval_days: 30 } → "매월"
 * - { interval_days: 90 } → "분기마다"
 * - { interval_days: 5 } → "5일마다"
 * - { weekdays: [1, 3], week_interval: 1 } → "매주 화·목"
 * - { weekdays: [0, 1, 2, 3, 4], week_interval: 1 } → "평일"
 * - { weekdays: [5, 6], week_interval: 1 } → "주말"
 * - { weekdays: [1, 4], week_interval: 2 } → "격주 화·금"
 * - { weekly_count: 2 } → "주 2회 (요일 필요)"
 */

const WEEKDAYS_KO = '월화수목금토일';
const INTERVAL_LABELS = {
  1: '매일',
  2: '격일',
  7: '매주',
  14: '격주',
  21: '3주마다',
  30: '매월',
  90: '분기마다',
};

export function fmtSchedule(c) {
  if (!c) return '';
  const rawDays = Array.isArray(c.weekdays) ? c.weekdays : [];
  const weekdays = [...new Set(rawDays.filter((d) => Number.isInteger(d) && d >= 0 && d <= 6))].sort((a, b) => a - b);
  const weekInterval = c.week_interval || 1;

  if (weekdays.length) {
    if (weekdays.length === 5 && weekdays.every((d, i) => d === i) && weekInterval === 1) return '평일';
    if (weekdays.length === 2 && weekdays[0] === 5 && weekdays[1] === 6 && weekInterval === 1) return '주말';
    const prefix = weekInterval === 2 ? '격주' : '매주';
    return `${prefix} ${weekdays.map((d) => WEEKDAYS_KO[d]).join('·')}`;
  }
  if (c.interval_days && c.interval_days > 0) {
    return INTERVAL_LABELS[c.interval_days] || `${c.interval_days}일마다`;
  }
  if (c.weekly_count && c.weekly_count > 0) {
    return `주 ${c.weekly_count}회 (요일 필요)`;
  }
  return '';
}

export const PATTERNS = {
  os: '(?:Ubuntu|우분투)\\s+\\d{2}(?:\\.\\d{2})?|(?:jammy|noble|focal|bionic)|(?:macOS|OS\\s*X|맥OS|맥북|맥)\\s+\\d{2}(?:\\.\\d+)?|(?:Windows|윈도우)\\s+1[01]\\s+\\d{2}H[12]|(?:세쿼이아|타호|소노마|벤투라)',
  python_version: '(?:Python|파이썬|py)\\s*\\d+(?:\\.\\d+|\\d{2})',
  capacity: '(?:한\\s*번에\\s*(?:\\d+|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\\s*개(?:\\s*까지)?|(?:\\d+|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\\s*개씩|(?:최대\\s*)?\\d+\\s*개(?:\\s*(?:까지|이하))?|(?:다섯|여섯|일곱|여덟|아홉|열)\\s*개)',
  first_date: '(?:\\d{4}-\\d{1,2}-\\d{1,2}|\\d{1,2}/\\d{1,2}|(?:다음\\s*달|\\d{1,2}월)\\s*\\d{1,2}일|(?:다음\\s*주|이번\\s*주|다음)\\s*[월화수목금토일]요일|(?<!\\d)\\d{1,2}일(?!\\s*마다)|내일|모레|오늘)',
  interval_days: '(?:매일|격일|이틀에\\s*한\\s*번|사흘\\s*마다|매주|격주|매달|매월|한\\s*달에\\s*한\\s*번|분기\\s*마다|주\\s*\\d+\\s*회|일주일에\\s*(?:\\d+|한|두|세|네|다섯)\\s*번|\\d+\\s*일\\s*마다|\\d+\\s*주\\s*(?:마다|간격|에\\s*한\\s*번)|평일|주말|[월화수목금토일](?:·[월화수목금토일])+|[월화수목금토일]{2,7}(?=\\s|$|으로|마다)|[월화수목금토일]요일(?:\\s*[,·]?\\s*[월화수목금토일]요일)+)',
};

// "매달 첫째 주 화요일"·"12월 첫째 주"처럼 서버가 못 정하는 표현은 ○를 띄우지 않는다
export const UNSUPPORTED_WEEK_ORDINAL = '(?:매달|매월|\\d{1,2}월)\\s*(?:첫|둘|셋|넷|마지막|\\d+)째?\\s*주';

const COMPILED = {
  os: new RegExp(PATTERNS.os, 'i'),
  python_version: new RegExp(PATTERNS.python_version, 'i'),
  capacity: new RegExp(PATTERNS.capacity, 'i'),
  first_date: new RegExp(PATTERNS.first_date, 'i'),
  interval_days: new RegExp(PATTERNS.interval_days, 'i'),
};
const UNSUPPORTED_RE = new RegExp(UNSUPPORTED_WEEK_ORDINAL, 'i');

export function previewConditions(text) {
  const src = String(text || '');
  if (!src.trim()) return {};
  const unsupported = UNSUPPORTED_RE.test(src);
  const found = {};
  for (const [key, re] of Object.entries(COMPILED)) {
    if (unsupported && key === 'interval_days') continue;
    const m = src.match(re);
    if (m) found[key] = m[0].trim();
  }
  return found;
}
