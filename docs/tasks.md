# 할 일 (3일)

> 한 줄 = 작업 하나. 끝나면 체크. 담당: [C] Claude Code, [G] agy(Gemini), [나] 직접

## 0일차 (오늘, 수업 전 준비)
- [x] [나] Mac mini에서 `python check_apis.py` 실행 → spec v1.0 확정
- [x] [G·Flash] 세 API 이용 조건 조사 → docs/research/api-terms.md (agy-guide ①)
- [ ] [나] `packaging` 라이브러리 추가 가능한지 강사님께 확인
- [x] [C] 저장소 만들기: AGENTS.md, CLAUDE.md(`@AGENTS.md`), docs/spec.md, docs/tasks.md, docs/HANDOFF.md
- [x] [C] Claude Code 권한 설정: `rm -rf`, `git push --force` 차단

## 1일차 — 16시 게이트 통과가 최우선
- [ ] [나] 오전 FastAPI 실습 결과(app 폴더)를 저장소에 넣기
- [x] [C] LLM 한 번 호출 + Tool 명세를 넘겼을 때 Tool 호출을 고르는지 확인 (명세서 2.7 도구 연결 확인)
- [x] [C] 기획 검증 기록 작성: 대표 요청별 "LLM만 답하면 틀리는 점", API 출처·이용 조건 (docs/planning-check.md)
- [ ] **16:00 게이트: 세 API 호출 + LLM 호출 확인 완료**
- [x] [C] Tool 공통 응답 형식 + 레지스트리 (F3001)
- [ ] [C] get_eol / get_vulns / get_package_versions 구현 + fixture 테스트 (F3002~F3004)
- [ ] [C] requirements.txt 파싱 (조회 제외 줄 포함) + 테스트
- [ ] [C] 예시 한 건(spec 맨 아래)을 Tool로 직접 따라가 보고 spec 수정

## 2일차 — Agent
- [ ] [C] 목표 버전 고르기 + 우선순위 정렬 + 회차 나누기 (순수 함수 + 테스트)
- [ ] [C] LangGraph 흐름: 의도 분석 → 되묻기 → 계획 → Tool 호출 → 판단 → 재계획 → 응답 (F3005~F3009, F3011)
- [ ] [C] 호환 제약 위반 → Python 업그레이드 재계획 테스트 (상한 3회)
- [ ] [C] 대화 맥락(Memory): 패키지 목록·N·날짜·간격 유지 (F3010)
- [ ] [C] 이벤트 발행 + 로깅 Agent(큐 구독, SQLite 저장) + "로깅 꺼도 대화 정상" 테스트 (F3012~F3013)
- [ ] [G·Carbon] 2일차 끝: 교차 리뷰 (agy-guide ②) → 지적 사항은 [C]가 판단해서 반영

## 3일차 — 서비스·화면·제출
- [ ] [C] 계획 CRUD + 겹침 경고, 로그 조회·삭제 API (F3014~F3017)
- [ ] [C] 화면 탭 3개 + 실행 단계 표시 + 오류 안내 (F3018~F3019)
- [ ] [나] 대표 시나리오 5개를 화면에서 직접 돌려보기 (spec 완료 기준 체크)
- [ ] [나] 패키지 20개 파일로 응답 시간 재기 → 느리면 [C] 병렬 호출·캐시
- [ ] [G·Carbon] 제출 전: 전체 코드 vs spec 완료 기준 대조 (agy-guide ③, 백그라운드로 돌려두기)
- [ ] [나] 셀프 체크리스트로 점검 → 제출
- [ ] (시간 남으면) 심화 하나 선택
