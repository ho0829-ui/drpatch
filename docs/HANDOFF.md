# 마지막 갱신: 2026-11-18 15:23 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] 작업 모두 끝. 마지막: spec 예시를 실제 Tool로 따라가기 → spec v1.6
  - 결과: django·requests 둘 다 Python 3.8 최신(4.2.30·2.32.4)에서도 취약점 남음 → Python 3.10 필요 → 3.10은 종료(2026-10-01) → 3.11 확정 (재계획 2회)
  - 기록: docs/planning-check.md "설계 시험", 스크립트 scripts/walk_example.py

## 다음에 할 것
- [나] 오전 FastAPI 실습 결과(app 폴더) 넣기 — 폴더 위치 확인 필요
- [나] packaging 허용 여부 확인 — 근거는 spec "남은 확인"
- 2일차 [C] 목표 버전 고르기 + 우선순위 정렬 + 회차 나누기 (순수 함수 + 테스트)
  - spec v1.6 규칙: 정식 버전만, 필요한 가장 낮은 Python 구하기, 재계획 1회 = Python 줄기 하나 get_eol 확인, Python 항목 합치기, 순서 제약이 우선순위보다 먼저
  - packaging 답에 따라 버전 비교 구현 방식이 갈림 (허용 → packaging / 불가 → PEP 440 일부 직접 구현)

## 주의
- scripts/walk_example.py의 버전 계산은 임시(>=3.N 위주). 실제 판정 코드로 쓰지 말 것
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- 세션 캐시·동시 호출 수 제한은 아직 없음 (2~3일차 실행 흐름에서)
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- 되묻기 프롬프트는 2일차에 (spec 밖 정보까지 묻는 경향)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정
- .venv는 Python 3.14.7
