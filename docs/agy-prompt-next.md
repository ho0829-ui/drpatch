# agy(제미나이)에게 넘기는 작업 묶음 — spec v1.21 (2026-11-19)

> 모델: **구현은 Hydrogen**.
> 진행: I14~I17 끝남. 다음은 **I18(백엔드 요일 규칙) → I19(화면 칩·표시)** 차례로. I19는 I18이 main에 합쳐진 뒤 (final.conditions에 weekdays가 있어야 함). I16(예시 10개)은 I15의 새 알약을 쓰고, I14·I16은 둘 다 `App.vue`·`style.css`를 고치므로 한 번에 하나씩.
> **다음 작업은 앞 작업이 main에 합쳐진 뒤 main에서 브랜치를 딴다.**
> 각 작업이 끝나면 Claude Code가 diff·테스트·실제 화면을 확인하고 main에 합친다.
> (I10~I13은 끝나서 main에 있다.)

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
- docs/spec.md v1.21 — 특히 "v1.21 요일 규칙과 조건 표현 넓히기"(M·N), "판단 규칙 › 회차 나누기", "심화: 캘린더 연동", "v1.18 … D. 예시 시뮬레이션", "화면 (DR.PATCH 진료실)", "말투"
- docs/design.md (4-1 알약, 4-6 UI 배치, 5 말투, 7 꼭 지킬 것, 8 Blender)

지켜야 할 것:
1. main에서 이 작업 전용 브랜치를 새로 만들어 작업한다 (이름은 작업 안내에). main에 직접 커밋하지 않는다. --yolo 금지.
2. 작업 안내에 적힌 파일 말고는 건드리지 않는다. 기존 API 응답 형식은 필드를 더하는 것만 된다 (빼거나 이름 바꾸기 금지).
3. 값을 지어내지 않는다. 확인 못 한 값은 "미상" / "확인 못 함". 화면 오류는 짧은 안내만. 새 문장은 박사님 말투(spec "말투 맞추기").
4. 테스트는 네트워크를 쓰지 않는다. 외부 응답은 tests/fixtures/ 저장본으로.
5. 3D 모델(*.glb)은 손으로 고치지 않는다 — Blender 스크립트로 다시 만드는 것만 된다. 새 라이브러리를 설치하지 않는다. 필요하면 멈추고 질문에 적는다.
6. docs/course/는 읽지도 인용하지도 않는다. .env와 API 키 값은 열거나 출력하지 않는다.
7. 확실하지 않은 건 "확인 필요"라고 쓴다. 추측으로 채우지 않는다.
8. 포트 8000에 이미 서버가 떠 있으면 끄지 말고 다른 포트(예: 8001)로 띄워 확인한다. 화면을 바꿨으면 `cd frontend && npm run build` 뒤 그 서버로 본다 (dist가 옛 빌드면 바뀐 게 안 보인다).
9. 실제 로고(회사·Python·Ubuntu·패키지 로고)와 빨간 십자가는 쓰지 않는다.

끝나면:
- 확인: `.venv/bin/python -m pytest -q` (271개 이상 통과 — `pytest`만 치면 app 모듈을 못 찾으니 꼭 이 명령으로), 화면을 바꿨으면 `cd frontend && npm run build` (경고 없이)
- 커밋 메시지는 한국어, 작업 단위로
- docs/HANDOFF.md "지금 하던 것"에 한 줄
- 마지막 보고: 바꾼 파일, 확인한 방법(화면은 캡처 — 1280과 375 둘 다), 못 한 것, 질문
```

---

### I14 · 종이 점선·달 넘길 때 안내·끌어 놓기 화면
브랜치 `agy/fe-18-sheet-fixes` · 파일: `frontend/src/style.css`, `frontend/src/components/CalendarSheet.vue`, `frontend/src/App.vue`
```
docs/spec.md "v1.19 … E"를 고쳐줘. 세 가지 모두 작은 수정이다.

1. 종이 가운데 점선
   - 원인은 확정: style.css `.paper::after`(top: 50% 점선)가 스크롤되는 내용 위를 가로지른다.
   - 이 규칙을 지운다. 다른 종이(처방전·진료 기록·예시)에도 같은 선이 없어졌는지 375px에서 캡처.

2. 달 넘길 때 엉뚱한 안내
   - 먼저 재현: 진료 예약 → ▶ 여러 번 → ◀ 여러 번. 계획이 있는 세션·없는 세션, "모든 계획 보기" 켬/끔 모두.
     재현되면 정확한 문장, 어디에 떴는지(말풍선/종이), 어떤 요청이 실패했는지(네트워크 탭)를 보고에 적는다. 안 되면 "재현 못 함"과 해 본 방법.
   - 재현 여부와 상관없이 고친다:
     a. 달을 바꾸면 그 달의 내 일정(`api.calendar.list`)만 다시 부른다. 계획 목록(`api.plans.list`)은 종이를 열 때, "모든 계획 보기"를 바꿀 때, 끝냄·수정·삭제 뒤에만.
     b. 달력/계획 불러오기 실패는 서버 안내를 그대로 쓰지 말고 "허허, 달력을 불러오지 못했네요." / "허허, 점검 목록을 불러오지 못했네요." + [다시 불러오기]. 어떤 것이 실패했는지 구분된다.
     c. 지금 `api.calendar.list(...).catch(() => [])`가 실패를 숨겨 "내 일정 (0)"으로 보이는 것도 b처럼 안내한다.
   - 빠르게 ▶를 연달아 누르면 늦게 온 옛 달 응답이 새 달을 덮지 않게 한다 (요청 번호로 마지막 것만 반영).

3. 끌어 놓기 화면("여기에 requirements.txt를 놓아 주세요")
   - 지금: `dragover`면 무엇이든 켜고, `dragleave.self`·drop에서만 끈다 → 3D 위에서 창 밖으로 나가거나 Esc로 끌기를 취소하면 화면 전체가 덮인 채 남는다. 먼저 이렇게 재현해서 보고에 적는다.
   - 기능은 남기고 고친다:
     a. `dataTransfer.types`에 'Files'가 있을 때만 켠다 (글자·그림 끌기는 무시).
     b. dragenter/dragleave를 세어(카운터) 0이 되면 끈다. window의 dragleave(창 밖으로 나감: relatedTarget null), dragend, drop, blur에서도 끈다.
     c. Esc, 안내 화면 클릭, 오른쪽 위 닫기(×, aria-label "닫기")로 닫힌다. 안내 화면은 `role="dialog"` 대신 시각 안내라 aria-live로 "파일을 놓으면 접수합니다" 한 번만.
     d. 놓은 게 파일이 아니면 아무 일도 하지 않는다.
   - 확인: 파일 끌어 놓기 업로드가 그대로 되는지, 위 재현 방법으로 더는 남지 않는지.
```

### I15 · 새 특별 알약 10종 (Blender)
브랜치 `agy/fe-19-pills` (I14 합친 뒤) · 파일: `design/blender/pills.py`, `design/blender/common.py`(도형 함수가 필요할 때만, 기존 함수 동작은 바꾸지 않음), `frontend/public/models/pills.glb`(스크립트 출력), `design/blender/previews/`(미리보기), `frontend/src/demo.js`
```
docs/spec.md "v1.19 … G"를 구현해줘.

1. design/blender/pills.py를 먼저 읽고 기존 10종(POPULAR)과 모양 함수(capsule·caplet·tablet·softgel)를 그대로 둔다.
2. 10종을 더한다: fastapi, pydantic, starlette, uvicorn, scipy, matplotlib, pillow, celery, cryptography, certifi.
   - 모양과 기호는 spec G 표대로. 각인은 이니셜 두 글자(FA, PD처럼 — 기존 PD(pandas)와 겹치면 다른 두 글자로, 보고에 적기).
   - 기호는 기본 도형(C.rbox·원기둥·원뿔·토러스 등)으로 알약 윗면에 1~5mm 띄워(z-fighting 방지, design.md 4-2) 새긴다. 실제 로고 모양·배치를 따라 그리지 않는다 (예: fastapi는 "원 안의 번개" 로고 구도 금지, 그냥 번개 하나).
   - 기호 함수는 pills.py 안에 `symbol_<이름>(key, color, at)`처럼 작게. 이니셜과 기호가 겹치지 않게 자리 나눔.
   - 색: 두 색. 기존 10종·위험도 고리 색(SEV)과 헷갈리지 않게. 고른 색을 표로 보고.
   - 크기·축·원점·노드 이름 규칙은 기존과 같다 (`Pill_<소문자>`, 길이 약 1, X축으로 눕힘). 배치 간격(i*1.6)이 20개로 늘어 미리보기 카메라가 다 담도록 조정.
3. 다시 만들기: `blender -b --factory-startup -P design/blender/pills.py` → pills.glb와 미리보기 png.
4. frontend/src/demo.js POPULAR에 10개 이름 추가.
5. 확인:
   - 미리보기 png를 보고에 첨부 (20종 모두 보임).
   - 화면: 새 패키지가 든 requirements(예: fastapi==0.65.1, pydantic==1.8.1, pillow==8.2.0, certifi==2020.12.5)를 올려 약병·이름표·블리스터·곡반에서 기존 알약과 크기·바닥 높이가 맞는지 1280 캡처.
   - pills.glb 크기 전후, 빌드 경고 없음.
```

### I16 · 예시 시뮬레이션 10개 + 예시 입구
브랜치 `agy/fe-20-examples` (I15 합친 뒤) · 파일: `frontend/public/examples/`(새 파일 6개 + `index.json`), `frontend/src/components/ExampleSheet.vue`, `frontend/src/components/ConditionChips.vue`, `frontend/src/components/SpeechBubble.vue`(누를 수 있는 링크가 필요할 때만), `frontend/src/App.vue`, `frontend/src/scene/clinicController.js`(첫 인사·다음 환자 한 줄), `frontend/src/api.js`(calendar.add는 이미 있음 — 바꿀 필요 없으면 안 건드림), `frontend/src/style.css`, `tests/test_examples.py`
```
docs/spec.md "v1.19 … F"와 "H"를 구현해줘.

1. 예시 파일 6개 새로 (spec F 표 1·5·6·7·8·9번). 기존 4개 파일은 그대로.
   - 버전은 직접 고르되, 실제 서버(8001)로 각 예시를 한 번 끝까지 돌려서 표의 "보여 주는 것"이 실제로 나오는지 확인한 뒤 확정한다.
     나오지 않으면 버전을 바꿔 다시. 끝내 안 되면 그 예시는 "확인 필요"로 보고 (지어내서 설명을 맞추지 않는다).
   - 1번 건강검진: 작성하는 날 실제 조회로 취약점 0건인 버전. 설명에 "날마다 달라질 수 있어요".
   - 7번 지저분한 requirements: spec "requirements.txt 파싱 규칙" 표의 줄을 골고루 (조회 3~4줄, 제외 6줄 이상, 빈 줄·주석 줄). 각 줄의 기대 결과(조회/제외 이유)를 테스트에 적는다.
   - 결과 보고에 예시마다: 패키지 수, 제외 줄 수, 회차 수, 재계획 여부, 걸린 시간(초)을 표로. (이 숫자는 보고용 — index.json·화면 설명에 쓰지 않는다.)
2. index.json: 10개, 코스 순서(spec F의 #)대로. 필드 더하기: group, tags(2~3개), 9번만 seed_event {title: "[예시] 정기 배포", offset_days: 0, start: "21:00", end: "23:00"}.
   - 조건 문장의 {date}는 지금처럼 다음 화요일. seed_event 날짜도 같은 날(offset_days 기준).
3. ExampleSheet.vue
   - 묶음 제목(처음이라면 / 흔한 증상 / 까다로운 경우) 아래 카드. 카드: 제목, 설명, tags 칩, 패키지 n개 · 제외 n줄, OS·Python.
   - 해 본 예시에 "진료함" 표시 (localStorage `drpatch.examples.done`, try/catch — 없어도 동작).
   - 9번 카드를 고르면 바로 올리지 않고 카드 안에 확인란 "내 일정에 '[예시] 정기 배포'(m/d 21~23시)도 넣기"(기본 켬) + [이 예시로 시작]. 켜져 있으면 api.calendar.add로 넣는다. 같은 날짜·같은 제목 일정이 이미 있으면 다시 넣지 않는다.
   - 열 때 특정 예시 id를 받으면 그 카드로 스크롤·초점 (다음 환자에서 씀).
4. 예시 입구 (spec H)
   - 하단 도크 "예시" 버튼은 그대로.
   - 첫 인사(파일이 없을 때만) 끝에 "파일이 없으시면 예시 차트부터 보시죠." — "예시 차트"를 누르거나 Enter로 예시 종이가 열린다. 말풍선 닫기 동작(누르면 닫힘)과 충돌하지 않게: 링크를 누르면 종이만 열리고, 링크 밖을 누르면 지금처럼 닫힘. RichText에 v-html을 쓰지 않는다.
   - 조건 칩 "파일 필요"를 누르면 작은 선택 [파일 올리기] [예시 고르기] (Esc로 닫힘, 키보드로 고를 수 있음). 파일이 있으면 지금 동작 그대로.
5. 다음 환자
   - 예시로 올린 세션에서 처방(계획)이 나오면 박사님이 코스의 다음 예시를 한 줄로 권한다: "다음 환자도 보시겠어요? — <다음 예시 제목>". 대화 기록에도 남고, 누르면 예시 종이가 그 카드에 초점을 두고 열린다. 자동으로 올리지 않는다. 마지막(10번) 뒤에는 권하지 않는다.
   - 예시가 아닌 사용자 파일이면 권하지 않는다.
6. 테스트 tests/test_examples.py
   - 10개, id 목록, 각 파일 파싱 결과가 package_count·excluded_count와 같음, 7번은 줄마다 기대 제외 이유, group·tags 필드, seed_event 모양(9번만), 조건 문장 정규식(지금 것 + Ubuntu 18.04·24.04, macOS 14 통과).
7. 확인 (1280·375 캡처)
   - 예시 종이 묶음·카드·진료함 표시
   - 첫 인사 링크 → 예시 종이, "파일 필요" 칩 선택
   - 9번: 일정 넣기 → 계획에서 1회차가 옮겨지고 "↻ 원래 m/d" → 확인 뒤 [예시] 일정 삭제
   - 다음 환자 한 줄 → 다음 카드 초점
   - 모바일에서 도크 버튼이 꺾이지 않는지
```

### I17 · 보내면 대화 보이기·긴 답은 기록으로·조건 칩 "입력창에 있음"·모바일 칩 정렬
브랜치 `agy/fe-21-chat-flow` (I16 합친 뒤) · 파일: `frontend/src/components/ChatBar.vue`, `frontend/src/components/ConditionChips.vue`, `frontend/src/components/SpeechBubble.vue`, `frontend/src/App.vue`, `frontend/src/scene/clinicController.js`(블리스터 화면 위치 전달만), `frontend/src/style.css`, 새 `frontend/src/conditionPreview.js`, `tests/`(정규식 예문 표)
```
docs/spec.md "v1.20 … I·J·K"를 구현해줘. (L은 Claude Code가 한다 — design/blender·pills.glb는 건드리지 않는다.)

1. I · 보내면 대화 기록 열기
   - 보내기·진료 시작·다시 시도 모두: 대화 기록을 열고, 보낸 말을 바로 맨 아래에, "박사님이 차트를 보는 중…"(step_start 단계 이름 따라: 접수·검사·판정·처방) 한 줄. final이 오면 그 줄을 답으로 바꾼다.
   - 대화 기록에 답을 넣는 곳은 지금처럼 App.vue onChatTurn 한 곳뿐 (두 번 들어가던 버그가 있었다 — 주석 참고). "보는 중" 줄은 대화 기록 배열이 아니라 ChatBar의 표시 상태로.
   - 사용자가 닫아도 다음 보낼 때 다시 연다.
2. I · 긴 답은 기록으로, 말풍선은 짧게
   - 대화 기록이 열려 있고 답이 길면(줄 3개 넘음 또는 200자 넘음) 말풍선은 첫 문장(조건 한 줄 `차트:`로 시작하면 그 다음 문장) + "자세한 처방은 대화 기록에 적었습니다."만.
   - 말풍선 높이 상한: 모바일(<768) 22vh, 그 밖 30vh.
   - 블리스터 판이 화면에 있으면 말풍선 아래 끝이 판 윗선보다 위에 있게 (판 화면 위치를 clinicController가 0.5px 문턱으로만 알려 줌, 지금 onBubblePos 방식 그대로). 자리가 없으면 말풍선을 화면 위쪽에 붙이고 더 짧게(스크롤).
   - 재현 방법(보고에 전후 캡처): 375에서 패키지 5개 업로드 → "Ubuntu 22.04, Python 3.10, 한 번에 2개, 첫 점검은 다음 화요일부터 매주" → 처방 완료. 지금은 말풍선이 블리스터 3판을 덮는다.
3. J · 조건 칩 세 상태
   - 새 frontend/src/conditionPreview.js: previewConditions(text) → {os, python_version, capacity, first_date, interval} 중 찾은 것만 (표시용 문자열). 정규식은 tests/test_examples.py 조건 정규식과 같은 범위 + "우분투/맥/윈도우" 한글 이름.
   - ChatBar의 입력 글을 App으로 올려(v-model 또는 emit) ConditionChips에 draft로 넘긴다. 받음(서버) > 입력창에 있음(draft) > 필요 순.
   - "입력창에 있음" 모양: 청록 점선 테두리 + `라벨 ○` 만 (예: `OS ○`, `한 번에 N개 ○`). 긴 문구를 칩에 쓰지 않는다 — 찾은 값과 "보내면 확인"은 title·aria-label로 ("OS: 입력창에 Ubuntu 22.04 — 보내면 확인"). ○는 글자색 청록, 받음 칩과 폭이 크게 달라지지 않게. 누르면 입력창 초점.
   - 서버가 준 값이 생기면 그 칩은 "받음". 보냈는데 서버가 못 알아들은 칸은 draft가 비었으니 다시 "필요".
   - 칩 줄 앞 "받은 조건" 작은 글씨(768 미만 숨김, 줄 aria-label은 "받은 조건").
   - 테스트: 화면 JS 테스트 도구가 없으므로 새 라이브러리 없이 — tests/test_condition_preview_table.py에 예문 표(입력 → 기대 칸)를 두고 파이썬 정규식이 같은 결과인지 확인하고, 같은 표를 conditionPreview.js 주석에 적는다. (JS 정규식과 파이썬 정규식이 같은 패턴 문자열이 되게.)
4. K · 모바일 칩 줄 가운데
   - style.css 768 미만 `.cond-chips { justify-content: flex-start }` → 다 들어가면 가운데, 넘치면 왼쪽부터 스크롤 (`justify-content: safe center`가 안 먹는 브라우저 대비 첫/끝 칩 margin-inline:auto).
   - 확인: 칩이 짧을 때(값 다 받은 뒤)와 길 때(전부 필요) 둘 다 375 캡처. 버튼 줄과 가운데 축이 같은지.
5. 확인 (1280·375 캡처, 실제 GMS 한 번)
   - 보내기 → 기록 열림·보낸 말·보는 중 → 답, 말풍선 짧음, 블리스터 안 가림
   - 입력창에 "Ubuntu 22.04, Python 3.10" 입력만 → 두 칩 `OS ○`·`Python ○` → 보내기 → 값 칩("Ubuntu 22.04"·"Python 3.10")
   - Esc로 기록 닫기, 다시 보내면 열림
```

### I18 · 요일 규칙 (백엔드) + 조건 표현 표
브랜치 `agy/be-03-weekdays` · 파일: `app/agent/state.py`, `app/agent/brain.py`(Analysis 스키마·설명만), `app/agent/graph.py`(merge_conditions·회차·캘린더 맞추기 호출), `app/agent/planner/rounds.py`, `app/agent/planner/calendar_fit.py`, `app/agent/render.py`, `app/db/schema.sql`, `app/db/repo.py`, 새 `app/agent/schedule_text.py`(표시 함수), `tests/`(새 `test_weekdays.py`, `test_condition_phrases.py`), 새 `scripts/probe_conditions.py`
```
docs/spec.md "v1.21 … M·N"을 구현해줘. 화면(frontend/)은 건드리지 않는다 (I19).

1. Conditions에 weekdays: list[int] | None (0=월…6=일), weekly_count: int | None, week_interval: int | None(1·2) 추가.
   Analysis에 weekdays, weekly_count, interval_unsupported(bool, 기본 False) 추가. 필드 설명에 예:
   "매주 화·목"→[1,3], "평일"→[0,1,2,3,4], "주말"→[5,6], "월수금"→[0,2,4], "주 2회"→weekly_count 2(weekdays null),
   "매달 첫째 주 화요일"처럼 몇째 주 규칙은 interval_days에 넣지 말고 interval_unsupported=true.
2. merge_conditions: spec M의 우선순위 규칙 그대로 (이번 메시지의 것이 이김, 요일과 같이 온 7·14는 week_interval 1·2로).
   missing_inputs: interval_days 칸은 interval_days 또는 weekdays가 있으면 채워진 것.
   weekly_count만 있고 weekdays가 없으면 되묻기 문장(코드)이 "주 N회라면 무슨 요일로 할까요? (예: 화·금)".
   interval_unsupported면 "몇째 주 규칙은 아직 못 합니다. 매주·격주·요일로 말씀해 주시죠." (박사님 말투, 코드 문장).
3. rounds.split_rounds: weekdays가 있으면 spec M 규칙으로 날짜 (첫 날짜가 그 요일 아니면 다음 맞는 요일부터, week_interval 2면 다음 주 건너뜀). 없으면 지금 그대로.
4. calendar_fit.find_free_date(…, allowed_weekdays=None): 있으면 그 요일만 후보. 옮긴 결과 두 회차가 같은 날이면 뒤 회차를 다음 맞는 요일로.
5. 표시 함수 app/agent/schedule_text.py: fmt_schedule(conditions) → spec M 표대로 (매일·격일·매주·격주·3주마다·매월·분기마다·N일마다·매주 화·목·평일·주말·격주 화·금·주 2회(요일 필요)). render.py conditions_header가 이걸 쓴다.
6. DB: sessions에 weekdays TEXT("1,3"), weekly_count INTEGER, week_interval INTEGER. 옛 DB 자동 열 추가(지금 repo.py 방식). 읽을 때 "1,3" → [1,3].
7. 테스트 (네트워크 없음)
   - test_condition_phrases.py: spec N의 표현 표 — (입력 문장, 가짜 Analysis 값) → merge 결과·missing·표시 문자열. 실측 35개 + 요일 10개 이상(화·목, 화요일 목요일, 월수금, 평일, 주말, 격주 화·금, 매주 금요일, 주 2회, 주 3회 월수금, 매달 첫째 주 화요일).
   - test_weekdays.py: 회차 날짜(첫 날짜가 맞는 요일/아닌 요일, 주 간격 2, 3회차 넘김), 캘린더 겹침 시 맞는 요일로 이동·없으면 그대로+conflicts·두 회차 같은 날 방지, 옛 DB 열 추가, 우선순위(요일 뒤 "3일마다" → weekdays 지움 등).
8. scripts/probe_conditions.py (수동, 테스트 아님): test_condition_phrases.py의 표를 import해서 실제 GmsBrain.analyze에 넣고 기대와 다른 줄만 출력 (병렬 6개, 오늘 날짜 고정 인자). 결과를 보고에 붙인다 — 다른 줄이 있으면 brain.py 설명을 고쳐 다시 돌린다.
9. scripts/run_agent.py로 실제 한 번: "Ubuntu 22.04, Python 3.11, 한 번에 2개, 다음 주 화요일부터 매주 화·목" → 회차 날짜가 화·목·화인지, 조건 한 줄이 "매주 화·목"인지. 그리고 "주 2회"만 → 요일 되묻기.
```

### I19 · 화면: 요일 표시·칩 미리보기 넓히기
브랜치 `agy/fe-22-weekdays` (I18 합친 뒤) · 파일: `frontend/src/components/ConditionChips.vue`, `frontend/src/conditionPreview.js`, `tests/test_condition_preview_table.py`, (필요하면) `frontend/src/components/PlanCard.vue`·`CalendarSheet.vue`의 간격 표시
```
docs/spec.md "v1.21 … M(표시)·N(미리보기)"를 구현해줘. 백엔드는 건드리지 않는다.

1. 간격 칩 표시: final.conditions의 interval_days·weekdays·week_interval·weekly_count로 spec M 표대로.
   서버의 app/agent/schedule_text.py와 같은 결과가 나와야 한다 — 같은 예 표를 tests에 두고 (파이썬 함수 결과) == (JS 함수 결과를 주석 표로) 맞춘다. JS 테스트 도구는 없으니 지금 conditionPreview 방식(패턴 문자열 비교·예문 표)처럼.
   weekly_count만 있고 요일이 없으면 간격 칩은 "필요" 상태 + 글자 "주 2회 · 요일 필요".
2. 칩 미리보기(conditionPreview.js): spec N 목록의 표현 모두. 예문 표(입력 → 기대 칸)를 tests/test_condition_preview_table.py에 더하고 JS 패턴 문자열 일치 검사 유지.
   특히: 매일, 격일, 이틀에 한 번, 사흘마다, 3주 간격, 2주에 한 번, 한 달에 한 번, 분기마다, 주 2회, 평일, 주말, 매주 화·목, 화요일 목요일, 월수금 / 다음 주 월요일, 이번 주 금요일, 25일, 다음 달 3일 / 다섯 개, 최대 4개, 10개 이하 / jammy, noble, 우분투 22 / py311, 파이썬3.11.
   "12월 첫째 주", "매달 첫째 주 화요일"은 ○를 띄우지 않는다 (서버가 못 정하는 표현).
3. 확인 (375·1280 캡처, 실제 GMS 한 번): 입력창에 "매주 화·목" → 간격 ○ → 보내기 → 칩 "매주 화·목", 계획 회차 날짜가 화·목. "주 2회" → 칩 "주 2회 · 요일 필요" + 박사님 요일 되묻기.
```
