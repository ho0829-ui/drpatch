# agy(제미나이)에게 넘기는 작업 묶음 — spec v1.18 (2026-11-19)

> 모델: **구현은 Hydrogen**.
> 진행: **I10 → I11 → I12 → I13** 차례로. I10·I11·I13은 `App.vue`·`clinicController.js`·`ChatBar.vue`를 같이 고치고, I12도 처방전·도장을 건드리므로 한 번에 하나씩.
> **다음 작업은 앞 작업이 main에 합쳐진 뒤 main에서 브랜치를 딴다.** (지난번처럼 합치기 전에 시작하면 충돌이 난다.)
> 작업 전에 `agy/fe-13-brand-tip`(로고 툴팁)이 아직 main에 안 합쳐져 있다 → Claude Code 확인부터.
> 각 작업이 끝나면 Claude Code가 diff·테스트·실제 화면을 확인하고 main에 합친다.

## 사람이 하는 순서 (작업마다)
1. 같은 폴더에서 터미널을 하나 더 열고 `agy` 실행 → Hydrogen 선택
2. **공통 머리말** + 해당 작업 프롬프트를 이어 붙여 넣는다
3. 끝나면 Claude Code에게: `agy/<브랜치> 확인해줘`
4. Claude Code가 확인하고 main에 합친 뒤 HANDOFF를 갱신 → 다음 작업

---

## 공통 머리말 (모든 작업 앞에)
```
sudo-patch 저장소 작업이다. 시작 전에 꼭 읽어:
- AGENTS.md (프로젝트 규칙), docs/HANDOFF.md, git log -5
- docs/spec.md v1.18 — 특히 "v1.18 고칠 것·더할 것"(A~D), "화면 (DR.PATCH 진료실)", "말투"
- docs/design.md (4-6 UI 배치, 5 말투, 7 꼭 지킬 것)

지켜야 할 것:
1. main에서 이 작업 전용 브랜치를 새로 만들어 작업한다 (이름은 작업 안내에). main에 직접 커밋하지 않는다. --yolo 금지.
2. 작업 안내에 적힌 파일 말고는 건드리지 않는다. 기존 API 응답 형식은 필드를 더하는 것만 된다 (빼거나 이름 바꾸기 금지).
3. 값을 지어내지 않는다. 확인 못 한 값은 "미상" / "확인 못 함". 화면 오류는 짧은 안내만. 새 문장은 박사님 말투(spec "말투 맞추기").
4. 테스트는 네트워크를 쓰지 않는다. 외부 응답은 tests/fixtures/ 저장본으로.
5. 3D 모델(*.glb)은 손으로 고치지 않는다. 새 라이브러리를 설치하지 않는다. 필요하면 멈추고 질문에 적는다.
6. docs/course/는 읽지도 인용하지도 않는다. .env와 API 키 값은 열거나 출력하지 않는다.
7. 확실하지 않은 건 "확인 필요"라고 쓴다. 추측으로 채우지 않는다.
8. 포트 8000에 이미 서버가 떠 있으면 끄지 말고 다른 포트(예: 8001)로 띄워 확인한다.

끝나면:
- 확인: `.venv/bin/python -m pytest -q` (261개 이상 통과), 화면을 바꿨으면 `cd frontend && npm run build` (경고 없이)
- 커밋 메시지는 한국어, 작업 단위로
- docs/HANDOFF.md "지금 하던 것"에 한 줄
- 마지막 보고: 바꾼 파일, 확인한 방법(화면은 캡처), 못 한 것, 질문
```

---

### I10 · "처음부터" 뒤 재점검 버그
브랜치 `agy/fe-14-restart` · 파일: `frontend/src/scene/clinicController.js`, `frontend/src/App.vue`, `frontend/src/components/TopTools.vue`, `frontend/src/components/ChatBar.vue`, `frontend/src/api.js`
```
docs/spec.md "v1.18 … A"를 고쳐줘.

1. 재현부터: 업로드 → 조건 말하기 → 처방 완료 → "처음부터" → 같은 파일 업로드 → "진료 시작".
   지금은 박사님이 조건을 되묻는데 상단 상태 칩이 "접수"에 멈춰 진행 중처럼 보인다. 재현 결과를 보고에 적는다.
2. final을 받으면 진행 중 단계가 남지 않게 한다. missing이 있으면 상태 칩 "정보 필요"(진행 표시 없음).
3. "처음부터"는 확인을 받고(파일·조건·대화가 지워진다고 말함), 새로 시작한 뒤 박사님이 "새 차트입니다. 파일부터 올려 주시죠."라고 말한다.
4. 업로드 중에는 보내기·진료 시작을 막고 "접수 중…"을 보인다. 대화는 업로드가 준 세션으로만 보낸다.
   업로드 응답을 일부러 늦춘 상태(예: 개발자 도구 네트워크 느리게)에서 보내기를 눌러도 같은 세션으로 가는지 확인하고, 방법을 보고에 적는다.
5. 1을 다시 해서: 상태가 "정보 필요"로 바뀌고 → 조건을 다시 말하면 계획이 나오고 → 알약이 블리스터로 가는지 캡처.
```

### I11 · 조건 칩 줄과 알아들은 조건 한 줄
브랜치 `agy/fs-15-conditions` (I10 합친 뒤) · 파일: `frontend/src/components/ChatBar.vue`, 새 `frontend/src/components/ConditionChips.vue`, `frontend/src/App.vue`, `frontend/src/style.css`, `app/agent/graph.py`(respond), `app/agent/render.py`, `tests/`
```
docs/spec.md "v1.18 … B"를 구현해줘.

1. 입력창 바로 위에 조건 칩 줄: 파일 · OS · Python · 한 번에 N개 · 첫 날짜 · 간격 · (시각).
   값은 업로드 응답과 /chat final의 conditions에서만 채운다. 빠진 것은 "필요"로 강조. 모바일은 가로 스크롤.
2. 빠진 칩을 누르면 입력창에 예시 조각을 넣는다(보내지 않음). 칩 이름은 되묻기 문장의 이름과 같게.
3. 계획 답 맨 앞에 코드가 만든 한 줄: "차트: Ubuntu 22.04 · Python 3.11 · 한 번에 5개 · 11/25(화)부터 매주 (22–24시)".
   OS 이름은 app/agent/os_display.py를 쓴다. LLM이 쓰지 않는다. 테스트로 문장 모양을 고정한다.
4. "처음부터"·새로고침 뒤에도 칩이 지금 세션 값과 맞는지 확인한다 (세션을 다시 불러오는 API가 없으면 빈 칩으로 시작하고, 그 사실을 보고에 적는다).
```

### I12 · 진료 예약(캘린더) 손보기 + 끝냄 처리
브랜치 `agy/fs-16-calendar` (I11 합친 뒤) · 파일: `app/db/repo.py`(+ 스키마), `app/api/plans.py`, `app/api/schemas.py`, `app/api/deps.py`, `frontend/src/components/CalendarSheet.vue`(나눠도 됨: 새 `PlanCard.vue` 등), `frontend/src/components/PaperSheet.vue`, `frontend/src/api.js`, `frontend/src/scene/props/blister.js`·`stamp.js`(끝 도장), `frontend/src/style.css`, `tests/`
```
docs/spec.md "v1.18 … C"를 구현해줘.

백엔드 먼저(테스트와 함께):
1. plans에 status(planned/done)·done_at. 옛 DB 파일은 열을 자동으로 더한다(sessions가 하는 방식 그대로).
2. items_json 항목에 done_at. PUT /plans/{id}가 status와 항목 done_at을 받는다. 항목을 모두 체크하면 status=done, 하나라도 풀면 planned.
3. 날짜 전에 끝내도 된다(미리 끝냄). 끝난 계획은 겹침 판단에서 뺀다. GET /plans?session_id=는 이미 있으니 그대로.
4. 테스트: 끝냄·되돌리기, 항목 전부 체크 → 끝남, 미리 끝냄, 겹침에서 빠짐, 옛 DB 열 추가.

화면:
5. 주 화면은 "다가오는 점검" 카드(날짜순, 카드 하나 = 회차 하나): 머리에 날짜(요일)·시각·회차·D-day·상태 배지(예정/오늘/지남/끝남),
   몸에 항목 이름과 현재 → 목표(위험도 점, 5개까지 + 외 n개). 카드 안 항목 체크, 회차 "끝냄", 수정, 삭제(확인 받음).
6. 달력 칸은 점 대신 회차 배지 + 내 일정 점. 날짜를 누르면 그 날 카드로. 지난·끝난 것은 흐리게. 끝난 회차는 "끝난 점검"으로 접힘.
7. 버튼 글자가 꺾이지 않게(white-space: nowrap, 최소 폭). 좁은 폭(375)에서는 ⋯ 메뉴로 접는다.
8. 기본은 지금 세션 계획만, "모든 계획 보기" 토글. 내 일정 입력은 "일정 추가"를 눌렀을 때 펼친다.
9. 375px에서 진료 예약을 열면 "그 부탁은 처리하지 못했네요"가 뜨고 계획 0건이 보인 적이 있다(같은 서버 1280px은 14건) → 원인을 찾아 보고에 적고 고친다.
10. 3D 블리스터 라벨에 "끝" 도장(확정 도장과 다른 모양·색). 처방전 종이에도 끝낸 날.
캡처: 1280·375 각각 — 카드 목록, 달력, 끝냄 전후, 좁은 폭 버튼.
```

### I13 · 예시 시뮬레이션
브랜치 `agy/fe-17-examples` (I12 합친 뒤) · 파일: 새 `frontend/public/examples/`(index.json + 예시 파일), 새 `frontend/src/components/ExampleSheet.vue`, `frontend/src/components/ChatBar.vue`, `frontend/src/App.vue`, `frontend/src/components/PaperSheet.vue`(종이 종류 추가가 필요하면), `tests/`
```
docs/spec.md "v1.18 … D"를 구현해줘.

1. 하단 도크의 파일 첨부(📎) 옆에 "예시" 버튼 하나(위치는 나중에 옮길 수 있게 버튼 하나로). 모바일도 같은 자리.
2. 누르면 종이에 예시 목록: 제목, 한 줄 설명, 패키지 수, OS·Python.
3. 고르면 ① 예시 파일을 업로드와 같은 길로 올리고 ② 입력창에 조건 문장을 자동으로 채운다(보내지 않음) ③ 박사님 한마디.
   첫 날짜는 고른 날 기준으로 계산(예: 다음 화요일). 결과는 실제 API로 조회 — 값을 저장해 두거나 지어내지 않는다.
4. 예시 4개는 spec 표대로. "큰 freeze 파일"은 /Users/jaeho/Developer/sudo-quest/requirements.txt(130줄)를 복사해 쓴다.
   설명에 "오래 걸림(50초 안팎)"을 적는다.
5. 테스트(네트워크 없이, pytest): index.json의 예시 파일이 모두 있고 파싱되는지(오래된 우분투 예시는 제외 줄 1개),
   조건 문장에 OS·Python·N·간격이 다 들어 있는지(정규식 수준).
6. 예시 4개를 실제로 하나씩 돌려 계획이 나오는지 확인하고, 걸린 시간과 캡처를 보고에 붙인다.
```
