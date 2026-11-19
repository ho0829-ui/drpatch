# 할 일 (3일)

> 한 줄 = 작업 하나. 끝나면 체크. 담당: [C] Claude Code, [G] agy(Gemini), [나] 직접

## 0일차 (오늘, 수업 전 준비)
- [x] [나] Mac mini에서 `python check_apis.py` 실행 → spec v1.0 확정
- [x] [G·Flash] 세 API 이용 조건 조사 → docs/research/api-terms.md (agy-guide ①)
- [x] [나] `packaging` 라이브러리 추가 가능한지 강사님께 확인 → 문의 없이 추가하기로 결정 (packaging==26.3)
- [x] [C] 저장소 만들기: AGENTS.md, CLAUDE.md(`@AGENTS.md`), docs/spec.md, docs/tasks.md, docs/HANDOFF.md
- [x] [C] Claude Code 권한 설정: `rm -rf`, `git push --force` 차단

## 1일차 — 16시 게이트 통과가 최우선
- [x] [나] 오전 FastAPI 실습 결과(app 폴더)를 저장소에 넣기 → docs/course/1일차_FastAPI/(참고용, 커밋 안 함) + 구조를 따라 app/main.py 뼈대
- [x] [C] LLM 한 번 호출 + Tool 명세를 넘겼을 때 Tool 호출을 고르는지 확인 (명세서 2.7 도구 연결 확인)
- [x] [C] 기획 검증 기록 작성: 대표 요청별 "LLM만 답하면 틀리는 점", API 출처·이용 조건 (docs/planning-check.md)
- [x] **16:00 게이트: 세 API 호출 + LLM 호출 확인 완료**
- [x] [C] Tool 공통 응답 형식 + 레지스트리 (F3001)
- [x] [C] get_eol / get_vulns / get_package_versions 구현 + fixture 테스트 (F3002~F3004)
- [x] [C] requirements.txt 파싱 (조회 제외 줄 포함) + 테스트
- [x] [C] 예시 한 건(spec 맨 아래)을 Tool로 직접 따라가 보고 spec 수정

## 2일차 — Agent
- [x] [C] 목표 버전 고르기 + 우선순위 정렬 + 회차 나누기 (순수 함수 + 테스트)
- [x] [C] LangGraph 흐름: 의도 분석 → 되묻기 → 계획 → Tool 호출 → 판단 → 재계획 → 응답 (F3005~F3009, F3011)
- [x] [C] 호환 제약 위반 → Python 업그레이드 재계획 테스트 (상한 3회)
- [x] [C] 대화 맥락(Memory): 패키지 목록·N·날짜·간격 유지 (F3010)
- [x] [C] 이벤트 발행 + 로깅 Agent(큐 구독, SQLite 저장) + "로깅 꺼도 대화 정상" 테스트 (F3012~F3013)
- [x] [G·Carbon] 2일차 끝: 교차 리뷰 (agy-guide ②) → 지적 사항은 [C]가 판단해서 반영 → 13건 반영 (docs/review-day2.md)

## 3일차 — 서비스·화면·제출
- [x] [C] 계획 CRUD + 겹침 경고, 로그 조회·삭제 API (F3014~F3017) + /upload·/chat(ndjson)
- [x] [C] 화면 탭 3개 + 실행 단계 표시 + 오류 안내 (F3018~F3019)
- [x] [나] 대표 시나리오 5개를 화면에서 직접 돌려보기 (spec 완료 기준 체크) → docs/scenario-check.md (Claude Code가 실제 서버로 대신 실행)
- [x] [나] 패키지 20개 파일로 응답 시간 재기 → 느리면 [C] 병렬 호출·캐시 → docs/scenario-check.md (Claude Code가 실제 서버로 대신 실행)
- [x] [G·Neon] 제출 전: 전체 코드 vs spec 완료 기준 대조 및 프론트엔드 리뷰 → docs/review-final.md, docs/review-frontend.md (반영 완료)
- [ ] [나] 셀프 체크리스트로 점검 → 제출
- [x] (시간 남으면) 심화 하나 선택 → F3023 캘린더 연동 (로컬 구현체, 충돌 회차 이동, 확정 시 등록)

## 4일차~ — 확장 (사용자 결정 2026-11-18)
- [x] ~~ [C] Figma "보안 관제(SOC) 대시보드" 디자인 → docs/design.md (화면 4개·컴포넌트 7개·토큰)~~ (폐기)
- [x] [C] 디자인 인터뷰 → DR.PATCH 진료 책상 방향 (docs/design.md) + 시제품 prototype/drpatch-desk/
- [x] [C·G] Vite + Vue로 화면 다시 만들기 (캘린더 화면 포함) — agy T1~T7, Claude Code 검증·수정 (2026-11-19)
- [x] [C·G] 화면 마무리 I3~I6 (청크 분리·로딩, 오류 화면·재시도, 캘린더 이동 경고, 모바일 터치) (2026-11-19)
- [x] ~~ [C] (선택) Google Calendar 구현체 — OAuth 준비 후~~ (폐기 — SQLite 로컬 캘린더로 마무리)
- [ ] [C] (선택) 심화 F3020 이상 징후 / F3021 Planner·Worker / F3022 RAG — 하려면 spec 먼저
- [ ] [나] 명세 밖 나만의 기능 정하기
- [ ] [나] 모든 기능 끝난 뒤 README

## 사용 중 발견 (spec v1.17, 2026-11-19) — agy가 하고 Claude Code가 확인 (docs/agy-prompt-next.md)
- [x] [G] I7 OS 입력: macOS·Windows 받기, OS 이름만 있으면 버전만 되묻기, macOS "지원 중 (종료일 미발표)"
- [x] [G] I8 말투: 고정 문구도 박사님 말투, LLM 프롬프트에 기준 대사 (I7 합친 뒤)
- [x] [G] I9 화면: 약병 알약 24알 상한, 말풍선 눌러 닫기, 왼쪽 위 로고 (I7·I8과 따로 해도 됨)
- [x] [C] 실제 freeze 파일(130개) 응답 시간 재기 → 46~49초 (2026-11-19, 헤드리스 Chrome)
