# agy(하이드로젠)에게 넘기는 작업: DR.PATCH 화면 본 구현

> 역할: **계획·검증·디자인은 Claude Code(Opus), 구현은 agy 하이드로젠.**
> 작업은 아래 T1~T7을 **하나씩** 넘긴다. 하나 끝날 때마다 Claude Code에게 확인을 받고 main에 합친 뒤 다음 작업으로 간다.
> T1은 일부러 작게 잡은 시험 작업이다. 결과물 품질을 보고 다음 작업의 크기를 조절한다.

## 사람이 하는 순서 (매 작업마다)
1. 같은 폴더에서 터미널을 하나 더 열고 `agy` 실행 → 모델 **하이드로젠** 선택
2. 아래 **공통 머리말** + 해당 작업 프롬프트(T1, T2, …)를 이어 붙여 넣는다
3. agy가 끝나면 Claude Code에게: `agy/<브랜치> 확인해줘` → Claude Code가 diff 확인, `pytest -q`, `npm run build`, 브라우저 확인
4. 통과하면 Claude Code가 main에 합치고 HANDOFF를 갱신 → 다음 작업

---

## 공통 머리말 (모든 작업 앞에 붙인다)
```
너는 sudo-patch 저장소에서 화면(프론트엔드)을 구현한다. 시작 전에 꼭 읽어:
- AGENTS.md (이 프로젝트 규칙), docs/HANDOFF.md, git log -5
- docs/design.md (디자인 기준, 특히 2·3·4절과 4-1~4-5)
- prototype/drpatch-desk/index.html (동작 기준이 되는 시제품. 장면·연출·종이·이스터에그가 여기 다 있다)

지켜야 할 것:
1. 브랜치: 이 작업 전용 브랜치에서만 작업한다 (이름은 작업 안내에 있음). main에 직접 커밋하지 않는다. --yolo 금지.
2. 백엔드(app/)와 tests/는 작업 안내에 적힌 곳 말고는 건드리지 않는다. 기존 API 응답 형식을 바꾸지 않는다.
3. 프론트엔드는 우리 API만 부른다 (/upload, /chat, /plans, /logs, /calendar/events). endoflife.date·OSV·PyPI·LLM을 직접 부르지 않는다.
4. 화면에 숫자·버전·날짜·심각도를 지어내지 않는다. API 값이 없으면 "미상" / "확인 못 함"을 그대로 보여준다.
5. 오류는 짧은 안내만 보여준다 (상세 메시지·스택을 화면에 내지 않는다).
6. 3D 모델(prototype/drpatch-desk/models/*.glb)은 손으로 고치지 않는다. design/blender/*.py가 원본이다. 모델을 바꿔야 하면 멈추고 질문에 적는다.
7. 실제 회사·Python·Ubuntu 로고를 쓰지 않는다. 로고는 design/logo/*.svg만 쓴다.
8. docs/course/는 읽지도 인용하지도 않는다.
9. 새 라이브러리는 vue, vite, @vitejs/plugin-vue, three 네 가지만 쓴다. 다른 게 필요하면 설치하지 말고 질문에 적는다.
10. 성능: 시제품처럼 굴절 유리(transmission) 쓰지 않기, 움직이지 않는 메시는 재질별로 합치기(mergeStatic), 접지 그림자는 불투명 타원 5겹.
11. 움직임 줄이기(prefers-reduced-motion)와 WebGL이 없을 때의 목록 화면을 유지한다.

끝나면:
- 확인: `pytest -q`(백엔드 테스트 255개 이상 그대로 통과), `cd frontend && npm run build` 성공
- 커밋 메시지는 한국어, 작업 단위로 나눠서
- docs/HANDOFF.md "지금 하던 것"에 한 줄
- 마지막에 보고: 바꾼 파일, 확인한 방법, 못 한 것, 질문 (추측으로 채운 부분이 있으면 반드시 적기)
```

---

## T1 · 시험 작업: Vue 뼈대 + 진료실 장면 옮기기 (API 없이)
브랜치 `agy/fe-01-scene`
```
목표: 시제품의 진료실 3D 장면을 Vite + Vue 프로젝트로 옮긴다. 이번 작업은 API를 부르지 않는다 (예시 데이터 그대로).

할 일:
1. frontend/ 에 Vite + Vue 3 프로젝트를 만든다 (JavaScript, 라우터·상태관리 라이브러리 없이).
   - 빌드 결과는 frontend/dist
   - 정적 파일: prototype/drpatch-desk/models/*.glb → frontend/public/models/, design/logo/*.svg → frontend/public/brand/ 로 복사
2. 장면 코드를 컴포넌트와 모듈로 나눈다. 예:
   - src/scene/ (렌더러·카메라·조명·접지 그림자·mergeStatic·tween), src/scene/props/ (블리스터 조립·알약·약병·차트·도장·박사님)
   - src/components/ ClinicScene.vue(캔버스), SpeechBubble.vue, PaperSheet.vue(누르면 펼쳐지는 종이), StatusChip.vue, Controls.vue, FallbackList.vue
   - src/demo.js 에 시제품의 ITEMS·ROUNDS 예시 데이터
3. 시제품과 똑같이 동작해야 한다: 진료 시작 → 검사 → 재계획 → 포장 → 알약 누르면 처방전 → 처방 확정 도장, 진료 기록, 이스터에그 16개, 자유 카메라(범위 제한), 움직임 줄이기, 목록 화면.
4. 백엔드는 app/main.py 한 곳만: frontend/dist 가 있으면 그걸, 없으면 지금처럼 web/ 을 내보낸다 (StaticFiles 경로만 바꾸는 최소 수정). tests는 건드리지 않는다.

완료 기준:
- npm run build 성공, pytest -q 통과
- uvicorn app.main:app 실행 후 http://localhost:8000 에서 시제품과 같은 장면·연출 (콘솔 오류 없음)
- prototype/ 폴더는 그대로 둔다 (지우지 않음)
```

## T2 · API 연결 모듈
브랜치 `agy/fe-02-api`
```
목표: 화면이 쓸 API 모듈을 만든다. 장면은 아직 예시 데이터를 쓴다.

src/api.js 에:
- upload(file) → POST /upload (본문 = 파일 그대로, 1MB 제한). 응답 {session_id, packages, excluded, saved}
- chat(sessionId, message, onEvent) → POST /chat, 응답은 ndjson 스트림(한 줄에 JSON 하나).
  줄 종류: {type:"session"} → 실행 이벤트들({type, seq, ...}) → 마지막 {type:"final", answer, plan, missing, conditions, confirmed, intent, saved}
  스트림을 줄 단위로 읽어 onEvent(event)를 부르고, final 객체를 반환한다. 중간에 끊기면 짧은 오류로.
- plans: list/get/update(PUT)/remove(DELETE) → /plans
- logs: list(/logs), get(/logs/{session_id})
- calendar: list(date_from, date_to), add({title,date,start,end}), remove(id) → /calendar/events
- 422 응답은 {detail, fields}. 화면에는 detail만.
기존 web/js/api.js 가 같은 일을 하니 참고한다 (형식은 그대로).

완료 기준: npm run build, pytest -q 통과. 서버를 켜고 브라우저 콘솔에서 upload·chat이 실제로 동작하는지 확인한 방법을 보고에 적는다.
```

## T3 · 진료 흐름을 실제 데이터로
브랜치 `agy/fe-03-live`
```
목표: 예시 데이터 대신 실제 업로드와 /chat 이벤트로 장면을 움직인다.

연결 규칙 (이벤트 이름은 app/agent/graph.py 그대로):
- 업로드 응답 packages → 약병 안 알약. 인기 패키지(design/blender/pills.py POPULAR: python, requests, urllib3, django, flask, numpy, pandas, pytest, pyyaml, jinja2)는 특별 알약, 나머지는 일반 캡슐. 이름 비교는 소문자.
- step_start/step_end → 상단 단계 칩(접수·검사·판정·처방)과 수액 한 방울
- tool_call/tool_result → 해당 패키지 알약이 폴짝 + 약병 위 검사 결과 이름표
- judgment → 진료 기록 한 줄 / replan → 박사님 갸웃 + 해당 알약 흔들림 + 이름표 "처방 변경"
- calendar_check → 회차 라벨 날짜 갱신, moved_from 이 있으면 "↻ 원래 날짜" 표시
- error → 짧은 안내만 (상세는 보이지 않음)
- final.plan →
  - rounds[] (최대 3) → 회차마다 블리스터 한 판. 칸 수 N = 그 계획에서 가장 많은 회차의 items 수. 알약은 round 순서대로.
  - safe[](이름 목록) → 곡반 / unassigned[] → 약병에 남음 "다음 진료" / unchecked[]·held[]({name, reason}) → 약병에 남고 이름표 "확인 못 함"·"보류"
  - 처방전 종이: name, current_version → target_version, severity(없으면 "미상"), reason, flags, eol_date
  - python_upgrade 가 있으면 처방전·회차 종이에 업그레이드 경로(attempts) 표시
- final.answer → 박사님 말풍선. final.missing 이 있으면 말풍선이 되묻기 (입력 칸은 T4).
- 업로드 전에는 약병이 비어 있고 "requirements.txt를 올려 주세요" 안내.

완료 기준: 서버 + 실제 GMS 키로 예시 파일(scripts/walk_example.py 참고)을 올려 끝까지 진행되는지. 키가 없으면 "서버 설정 확인" 안내가 나오는지. npm run build, pytest -q.
```

## T4 · 대화 입력과 파일 올리기
브랜치 `agy/fe-04-chat`
```
목표: 사용자가 박사님과 대화한다.
- 화면 아래 입력창(여러 줄 가능, Enter 보내기 / Shift+Enter 줄바꿈) + 파일 올리기(약병을 누르거나 끌어다 놓기)
- 보낸 메시지와 박사님 답을 대화 기록(접었다 펴는 패널)에 쌓는다. 말풍선에는 마지막 답.
- OS·Python 버전·회차 조건을 물으면(final.missing) 박사님 질문만 보여준다. 예시 값을 미리 채운 빠른 답 버튼은 만들지 않는다 (값을 지어내지 않기).
- 진행 중에는 보내기 버튼을 막고 단계 칩으로 진행을 보여준다.
완료 기준: 대화로 조건을 채워 계획이 나오는 흐름을 실제로 확인. npm run build, pytest -q.
```

## T5 · 처방 확정과 진료 예약
브랜치 `agy/fe-05-confirm`
```
목표: 확정은 대화로 한다 (/chat 에 "확정해줘" 같은 메시지 → final.confirmed).
- [처방 확정] 버튼 = /chat 에 확정 메시지 보내기. final.confirmed[] 의 회차마다 도장 연출, calendar_event 가 있으면 라벨에 "예약됨".
- 진료 예약 종이(벽시계 또는 대기 모니터를 누르면): /calendar/events 와 /plans 를 월 달력으로. 내 일정 추가·삭제, 저장한 계획 날짜·시간 수정(PUT /plans/{id}), 겹침(overlaps) 경고.
완료 기준: 확정 → 캘린더에 등록되는 것까지 실제 확인. npm run build, pytest -q.
```

## T6 · 진료 기록(실행 로그)
브랜치 `agy/fe-06-logs`
```
목표: 차트(클립보드)를 누르면 진료 기록 종이. /logs 세션 목록 → /logs/{session_id} 이벤트를 #seq 순서로.
- 판단 근거: judgment·replan·plan_built 이벤트는 사람이 읽는 문장으로 (값은 이벤트 그대로, 지어내지 않기)
- 세션 삭제(DELETE /logs/{id})는 확인을 한 번 받고
완료 기준: 실제 세션 기록이 보이는지. npm run build, pytest -q.
```

## T7 · 마무리: 접근성·모바일·옛 화면 정리
브랜치 `agy/fe-07-polish`
```
- 키보드만으로: Tab으로 버튼·입력, 종이 닫기 Esc, 3D 물체 대신 "목록으로 보기" 토글(FallbackList)로 같은 정보
- 모바일(390px): 카메라 거리·말풍선·종이 위치
- web/ 폴더 삭제는 하지 말고, 삭제해도 되는지 질문에 적는다 (Claude Code가 판단)
완료 기준: npm run build, pytest -q, 모바일 크기 스크린샷을 보고에 첨부.
```

---

## Claude Code가 확인할 것 (작업마다)
- diff가 브랜치 범위 안인지 (app/·tests/·models 손댐 여부), 새 라이브러리 여부
- `pytest -q`, `npm run build`, 브라우저에서 시제품과 같은 연출·콘솔 오류
- 화면에 지어낸 값이 없는지 ("미상"/"확인 못 함" 처리)
- 보고의 "질문"에 답하고 다음 작업 프롬프트를 필요하면 고친다
