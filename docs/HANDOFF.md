# 마지막 갱신: 2026-11-18 16:30 / 작성: Claude Code

## 지금 하던 것
- 2일차 [C] 작업 모두 끝. 마지막: Memory (F3010) — 전체 테스트 191개 통과, 실제 GMS 두 턴 확인(N 2→3만 바뀜)
  - app/agent/session.py: chat_turn(session_id|None, message, brain, bus=, db_path=) → run_agent 결과 + session_id·last_plan·saved
    save_upload(session_id, packages, excluded), load_session(session_id) → conditions·last_turn·last_plan
  - sessions 표에 last_message·last_answer·last_plan_json 추가 (init_db가 예전 DB 파일에도 칸을 붙임)
  - analyze에 직전 대화(last_turn) 전달. 새 계획을 만들 때만 last_plan 교체 (사실 질문 뒤 "확정해줘"도 직전 계획 유지)
  - scripts/run_session.py: 실제 GMS 두 턴 확인

## 다음에 할 것
- [G·Carbon] 2일차 교차 리뷰 (docs/agy-guide.md ②) → 결과 docs/review-day2.md → [C]가 맞는 지적만 골라 반영
- 3일차 [C] 계획 CRUD + 겹침 경고, 로그 조회·삭제 API (F3014~F3017) — /chat(ndjson)·/upload도 여기서 chat_turn·save_upload로 연결
- 3일차 [C] 화면 탭 3개 + 실행 단계 표시 + 오류 안내 (F3018~F3019)

## 주의
- spec v1.10: Memory = 조건 + 직전 메시지·답·제안 계획
- 응답 시간: 예시 한 건 25~28초. 대부분 LLM 4번(analyze·plan·replan·respond). judge의 목표 버전 재조회는 패키지마다 순서대로 → 3일차 측정 때 병렬화 후보
- 재계획 방식은 LLM이 고름(upgrade_python/hold), 실패하면 upgrade_python. 되묻기 문장은 코드 (spec v1.9)
- 사실 조회 경로도 조건(os 등)을 Memory에 남김
- 구조는 docs/architecture.md (v1). /chat ndjson 스트리밍은 아직 없음
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖)
- .venv는 Python 3.14.7
