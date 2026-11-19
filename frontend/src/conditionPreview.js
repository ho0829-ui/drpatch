/**
 * 입력창 글에서 조건을 미리 찾아 조건 칩에 "입력창에 있음(○)"으로 표시한다 (spec v1.20 J).
 * 서버 값을 대신하지 않으며, 보낸 뒤에는 서버 final.conditions 값으로 바뀐다.
 *
 * 정규식 패턴과 예문 표는 tests/test_condition_preview_table.py와 동일하게 유지한다.
 *
 * 예문 표 (입력 → 기대 칸):
 * - "Ubuntu 22.04, Python 3.10, 한 번에 2개, 첫 점검은 11/25부터 매주"
 *     → os, python_version, capacity, first_date, interval_days
 * - "우분투 20.04, 파이썬 3.8, 5개씩, 다음 화요일, 격주"
 *     → os, python_version, capacity, first_date, interval_days
 * - "맥북 15, py 3.11"
 *     → os, python_version
 * - "세쿼이아, Python 3.12, 한 번에 3개까지, 12월 1일, 14일마다"
 *     → os, python_version, capacity, first_date, interval_days
 * - "윈도우 11 24H2, 2026-12-01, 매달"
 *     → os, first_date, interval_days
 * - "안녕하세요"
 *     → (없음)
 */

export const PATTERNS = {
  os: '(?:Ubuntu|우분투)\\s+\\d{2}\\.\\d{2}|(?:macOS|OS\\s*X|맥OS|맥북|맥)\\s+\\d{2}(?:\\.\\d+)?|(?:Windows|윈도우)\\s+1[01]\\s+\\d{2}H[12]|(?:세쿼이아|타호|소노마|벤투라)',
  python_version: '(?:Python|파이썬|py)\\s*\\d+\\.\\d+',
  capacity: '(?:한\\s*번에\\s*\\d+\\s*개(?:\\s*까지)?|\\d+\\s*개씩|\\d+\\s*개\\s*까지)',
  first_date: '(?:\\d{4}-\\d{1,2}-\\d{1,2}|\\d{1,2}/\\d{1,2}|\\d{1,2}월\\s*\\d{1,2}일|다음\\s*[월화수목금토일]요일|내일|모레|오늘)',
  interval_days: '(?:매주|격주|매달|매월|\\d+\\s*일\\s*마다|\\d+\\s*주\\s*마다)',
};

const COMPILED = {
  os: new RegExp(PATTERNS.os, 'i'),
  python_version: new RegExp(PATTERNS.python_version, 'i'),
  capacity: new RegExp(PATTERNS.capacity, 'i'),
  first_date: new RegExp(PATTERNS.first_date, 'i'),
  interval_days: new RegExp(PATTERNS.interval_days, 'i'),
};

export function previewConditions(text) {
  const src = String(text || '');
  if (!src.trim()) return {};
  const found = {};
  for (const [key, re] of Object.entries(COMPILED)) {
    const m = src.match(re);
    if (m) found[key] = m[0].trim();
  }
  return found;
}
