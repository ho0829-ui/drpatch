# agy(제미나이)에게 넘기는 작업 묶음 — spec v1.17 (2026-11-19)

> 모델: **구현은 Hydrogen** (지난 I3~I6과 같음).
> 진행: **I7 → I8** (둘 다 `app/agent/state.py`를 고치므로 차례로). **I9**는 화면만 바꾸므로 I7·I8과 따로 해도 된다.
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
- docs/spec.md v1.17 — 특히 "OS 입력 (v1.17)", "화면 고칠 것 (v1.17)", "말투 맞추기 (v1.17)"
- docs/design.md (4-5 로고, 4-6 UI 배치, 5 말투)

지켜야 할 것:
1. 이 작업 전용 브랜치에서만 작업한다 (이름은 작업 안내에). main에 직접 커밋하지 않는다. --yolo 금지.
2. 작업 안내에 적힌 파일 말고는 건드리지 않는다. 기존 API 응답 형식을 바꾸지 않는다 (작업에 적힌 것만 예외).
3. 값을 지어내지 않는다. 확인 못 한 값은 "미상" / "확인 못 함". 화면 오류는 짧은 안내만.
4. 테스트는 네트워크를 쓰지 않는다. 외부 응답은 tests/fixtures/ 저장본으로.
5. 3D 모델(*.glb)은 손으로 고치지 않는다. 새 라이브러리를 설치하지 않는다. 필요하면 멈추고 질문에 적는다.
6. docs/course/는 읽지도 인용하지도 않는다. .env와 API 키 값은 열거나 출력하지 않는다.
7. 확실하지 않은 건 "확인 필요"라고 쓴다. 추측으로 채우지 않는다.

끝나면:
- 확인: `.venv/bin/python -m pytest -q` (255개 이상 통과), 화면을 바꿨으면 `cd frontend && npm run build` (경고 없이)
- 커밋 메시지는 한국어, 작업 단위로
- docs/HANDOFF.md "지금 하던 것"에 한 줄
- 마지막 보고: 바꾼 파일, 확인한 방법, 못 한 것, 질문
```

---

### I7 · OS 입력: macOS·Windows, 버전만 되묻기
브랜치 `agy/be-01-os` · 파일: `app/agent/state.py`, `app/agent/graph.py`, `app/agent/brain.py`(Analysis 설명만), `app/tools/eol.py`, `tests/`(fixtures 포함)
```
docs/spec.md "OS 입력 (v1.17)"을 구현해줘.

1. 재현부터 테스트로 만든다 (가짜 brain으로, 네트워크 없이):
   "Python 3.11이고 한 번에 5개까지, 11/25부터 매주" → OS를 묻는다
   "로컬 맥북을 백엔드 서버로 쓰고 있어요"(analyze 결과 os_name=macos, os_version=None) → 지금은 첫 번째와 똑같은 문장으로 또 묻는다.
   고친 뒤에는 두 번째 답이 macOS 버전만 묻는다. 같은 되묻기 문장이 연달아 나오지 않는다.
2. 되묻는 문장은 지금처럼 코드가 만든다(state.py). OS 이름이 있으면 그 OS에 맞는 버전 질문과 예시, 없으면 OS와 버전(예시에 Ubuntu·macOS·Windows).
   말투는 I8에서 바꾸므로 여기서는 내용(무엇을 묻는지)만 맞춘다.
3. 이름 정규화(코드): 맥·맥북·macOS·OS X → macos, 윈도우·Windows → windows. 코드네임은 세쿼이아→15, 타호→26처럼 아는 것만.
   Windows는 "11 24H2" → cycle "11-24h2-w". 주 버전만 있으면 기능 업데이트를 되묻는다. 에디션 말이 없으면 -w(Home/Pro).
4. get_eol(eol.py): eolFrom 없음 + isMaintained true → ok:true, eol_date null, is_eol false, note "지원 중 (종료일 미발표)". 둘 다 아니면 지금처럼 NO_EOL_DATE.
   endoflife.date 실제 응답(macos 15, windows 11-24h2-w 등)을 한 번 받아 tests/fixtures/에 저장하고, 테스트는 저장본으로.
5. 지원 중인 OS는 계획 항목이 아니다. 종료일 null이 우선순위 계산(남은 일수)에서 오류를 내지 않게.
6. Analysis의 os_name·os_version 설명에 macOS·Windows 예를 넣는다.
```

### I8 · 말투: 고정 문구도 박사님
브랜치 `agy/be-02-tone` (I7이 main에 합쳐진 뒤 시작) · 파일: `app/agent/state.py`, `app/agent/brain.py`(SYSTEM·프롬프트), `app/agent/graph.py`·`app/agent/session.py`·`app/api/chat.py`(고정 문구만), `frontend/src/scene/clinicController.js`·`frontend/src/App.vue`(onSay·안내 문장만), `tests/`
```
docs/spec.md "말투 맞추기 (v1.17)"를 구현해줘. 기준은 prototype/drpatch-desk/index.html의 대사다.

1. 코드가 쓰는 문장(맞이·접수·되묻기·오류·진행 중·확정 안내)을 기준 대사 결로 바꾼다.
   되묻는 항목은 여전히 빠진 것만, 코드가 만든다. 값·항목 이름·예시는 그대로.
   오류 안내는 짧게, 원인 상세는 화면에 내지 않는다.
2. brain.py SYSTEM과 write_response 프롬프트에 기준 대사를 예시로 넣고, 회차 줄마다 박사님 말로 짧게 쓰게 한다.
   백틱 등 화면이 그리지 않는 꾸밈은 쓰지 않게 한다 (**굵게**와 "- " 목록만).
3. 문장을 확인하는 기존 테스트가 깨지면 새 문장에 맞춰 고친다. 테스트를 지우지 않는다.
4. scripts/run_agent.py로 계획·되묻기·잡담 답을 하나씩 실제로 받아 보고, 받은 답 원문을 보고에 붙인다 (키 값은 출력하지 않는다).
```

### I9 · 화면: 알약 상한, 말풍선 닫기, 로고
브랜치 `agy/fe-12-polish` · 파일: `frontend/src/scene/props/jarAndTray.js`, `frontend/src/scene/clinicController.js`, `frontend/src/components/SpeechBubble.vue`, `frontend/src/App.vue`, `frontend/src/style.css`
```
docs/spec.md "화면 고칠 것 (v1.17)"을 구현해줘.

1. 약병 알약 상한 24알(6층). 넘친 수는 약병 이름표에 "+N". 조회·포장에 필요한 알약은 그때 만든다(ensurePill).
   약병을 눌러 나오는 목록과 "목록으로 보기"에는 패키지가 전부 보여야 한다. 치운 알약은 GPU 자원을 지금처럼 해제한다.
   확인: 패키지 130줄짜리 freeze 파일(직접 `pip freeze`로 만들어도 됨)과 20줄짜리 파일로 각각 올려 본다.
2. 말풍선: 움직임 없는 클릭·Esc·Enter/Space로 닫힘, 다음 말에 다시 열림, 스크롤·글자 고르기로 끌 때는 안 닫힘,
   닫힐 때 초점은 입력창으로. 대화 기록은 그대로.
3. 왼쪽 위 로고:
   - 먼저 "상호작용하면 로고 왼쪽 위가 작게 검게 변하는" 현상을 재현해서 방법과 원인을 보고에 적는다.
     후보: 화면 (0,0)의 1×1 숨은 파일 입력(.sr-only)이 파일 선택 뒤 초점 테두리를 그림, 로고 그림 끌기·선택. 재현 못 하면 못 했다고 적는다.
   - "DR.PATCH" 글자가 바탕에서 바깥으로 빠져 보이는 것: 여백·자간·점 폭을 맞춘다. 데스크톱과 모바일(375px) 화면을 각각 캡처해 보고에 붙인다.
4. 움직임 줄이기·키보드 접근성은 지금 수준을 유지한다.
```
