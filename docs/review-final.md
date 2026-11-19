# 제출 전 최종 대조 리뷰 (docs/spec.md v1.16 ↔ 코드·테스트)

- 작성일: 2026-11-19
- 기준: `docs/spec.md` (v1.16), `docs/design.md` (4-1~4-6), `main` (`ab13995`)
- 판정 기준: `보장됨` / `일부만` / `테스트 없음` / `확인 필요`

---

## 1. 완료 기준 (일상어) (`docs/spec.md:289-300`)

| 기준 | 보장하는 코드 (파일:줄) | 보장하는 테스트 (파일::테스트 이름) | 판정 | 메모 |
|---|---|---|---|---|
| freeze 파일을 올리고 "5개까지"라고 하면 위험한 것부터 회차로 나뉜 계획이 나오고, 항목마다 "현재 → 목표 버전"과 이유가 보인다 | `app/api/upload.py:1-42`, `app/agent/planner/items.py:79-145`, `app/agent/planner/priority.py:11-22`, `app/agent/planner/rounds.py:44-82`, `app/agent/render.py:10-44`, `frontend/src/components/PaperSheet.vue:70-101,121-127` | `tests/test_planner.py::test_spec_example_priority_and_rounds`, `tests/test_planner.py::test_overflow_goes_to_next_rounds_then_unassigned`, `tests/test_agent_graph.py::test_spec_example_through_graph`, `tests/test_api.py::test_chat_stream_then_confirm_saves_rounds` | 보장됨 | 백엔드·API는 테스트로 보장. 화면 표시는 `PaperSheet.vue`에서 확인 — 브라우저에서 파일 업로드 후 조건 입력 → 블리스터·알약 클릭해 `현재 → 목표`와 `이유` 확인. |
| 현재 Python에서 설치 안 되는 버전은 절대 목표 버전으로 나오지 않는다 | `app/agent/planner/versions.py:25-54` (`python_allows`, `pick_latest`), `app/agent/graph.py:184-188` | `tests/test_planner.py::test_python_allows`, `tests/test_planner.py::test_pick_latest_on_real_django`, `tests/test_planner.py::test_pick_latest_on_real_requests`, `tests/test_planner.py::test_pick_latest_none_when_nothing_installable`, `tests/test_agent_graph.py::test_review_4_no_installable_version_goes_to_replan`, `tests/test_agent_graph.py::test_review_12_lower_version_is_not_a_target` | 보장됨 | `requires_python` 불일치·설치 불가·다운그레이드 모두 재계획(위반)으로 분기. |
| 고칠 방법이 Python 업그레이드뿐이면, 업그레이드가 그 패키지보다 앞 회차에 들어간다 | `app/agent/planner/python_upgrade.py:98-174`, `app/agent/planner/rounds.py:44-82` (`split_rounds` 순서 제약), `app/agent/graph.py:213-235` | `tests/test_planner.py::test_upgrade_spec_example_two_replans`, `tests/test_planner.py::test_dependent_item_never_in_same_round_as_upgrade`, `tests/test_planner.py::test_dependent_item_unassigned_when_upgrade_in_last_round`, `tests/test_agent_graph.py::test_spec_example_through_graph` | 보장됨 | `split_rounds`에서 순서 제약을 우선순위보다 먼저 적용. |
| `-e`나 `>=` 줄은 조회 제외 목록에 보이고 오류가 나지 않는다 | `app/parsing/requirements.py:90-141`, `app/api/upload.py:1-42`, `frontend/src/App.vue:56-69` (미표시) | `tests/test_parse_requirements.py::test_spec_example`, `tests/test_parse_requirements.py::test_excluded_lines`, `tests/test_api.py::test_upload_parses_and_creates_session` | 일부만 | 백엔드 파싱·`/upload` 응답 `excluded`는 보장되나, **`frontend/src/App.vue:59-65`에서 `res.excluded`를 전혀 읽지 않아 화면 업로드 안내에 제외 목록이 보이지 않음**. 브라우저로 확인: `-e git+...`·`celery>=4.0` 포함 파일 업로드 후 말풍선·대화 기록 확인. |
| 파일 없이 "계획 짜줘"라고 하면 Tool을 부르지 않고 먼저 묻는다 | `app/agent/state.py:36-67` (`missing_inputs`, `tool_inputs_missing`, `ask_message`), `app/agent/graph.py:116-122,326-345` | `tests/test_agent_graph.py::test_missing_inputs_asks_only_missing_and_calls_no_tool`, `tests/test_api.py::test_missing_input_stream_has_no_tool_events` | 보장됨 | 코드가 빠진 입력을 판정하고 `ask` 노드로 직행, `tool_call` 이벤트 0건. |
| 한 Tool이 실패해도 나머지 항목은 결과가 나오고, 실패한 항목엔 "확인 못 함"이 보인다 | `app/agent/runner.py:56-62`, `app/agent/graph.py:170-198`, `app/agent/planner/items.py:79-145`, `frontend/src/scene/clinicController.js:317-327`, `frontend/src/components/PaperSheet.vue:157-161` | `tests/test_tools.py::test_one_tool_failure_does_not_affect_others`, `tests/test_planner.py::test_review_2_one_failed_lookup_does_not_block_others`, `tests/test_agent_graph.py::test_one_tool_failure_marks_only_that_package`, `tests/test_agent_graph.py::test_eol_failure_is_shown_as_unchecked_not_invented` | 보장됨 | 백엔드 보장. 화면은 약병 클릭 시 `PaperSheet.vue:157-161`과 약병 위 이름표(`확인 못 함`)로 표시 — 브라우저로 확인: 존재하지 않는 패키지 포함 파일로 진료 후 약병 클릭. |
| 같은 날 시간이 겹치는 계획을 저장하면 둘 다 저장되고 겹친다는 알림이 뜬다 | `app/api/overlap.py:6-20`, `app/api/plans.py:15-46`, `frontend/src/components/CalendarSheet.vue:199-201` | `tests/test_api.py::test_overlap_warning_but_both_saved`, `tests/test_api.py::test_plan_list_is_date_ordered_and_update_delete_reflected` | 보장됨 | 백엔드 보장. 화면은 `CalendarSheet.vue:199-201`에 `⚠ 같은 날 시간이 겹치는 일정 N건이 있어요.` 출력 — 브라우저로 확인: 진료 예약 달력에서 같은 날짜·시간대로 두 계획 수정/저장. |
| 로그 탭에서 왜 이 순서·이 버전으로 정했는지, 왜 재계획했는지 볼 수 있다 | `app/agent/graph.py:115,131,205-210,220,231-235,249-258`, `app/api/logs.py:13-31`, `app/db/repo.py:115-134`, `frontend/src/components/LogSheet.vue:15-51,118-137` | `tests/test_agent_graph.py::test_review_8_logs_explain_versions_and_order`, `tests/test_api.py::test_logs_list_detail_delete_and_no_update` | 일부만 | 백엔드 이벤트·`/logs` API는 보장. 단, **`LogSheet.vue:120`이 `s.events` 대신 없는 필드 `s.event_count`를 읽어 세션 건수가 비어 보이고**, `LogSheet.vue:15-51`이 `llm_decision` 이벤트(의도·Tool 계획·재계획 전략 이유)를 포맷하지 않고 `llm_decision` 문자열만 출력함. 브라우저로 확인: 차트 클릭 → 세션 목록 건수와 이벤트 문장 확인. |
| 로깅이 멈춰도 대화는 정상 응답한다 | `app/events/bus.py:64-79` (`put_nowait`, 예외 흡수), `app/events/logger.py:46-64`, `app/main.py:52-56` | `tests/test_events.py::test_full_queue_drops_without_blocking`, `tests/test_events.py::test_publish_never_raises`, `tests/test_events.py::test_chat_works_without_logger`, `tests/test_events.py::test_chat_works_when_logger_db_fails`, `tests/test_events.py::test_chat_works_when_logger_stuck_and_queue_full` | 보장됨 | 이벤트 버스·로깅 스레드 분리 및 4가지 장애 시나리오 모두 테스트 통과. |
| 패키지 20개짜리 파일도 60초 안에 응답이 나오고, 기다리는 동안 실행 단계가 실시간으로 보인다 | `app/api/chat.py:65-123` (ndjson 스트리밍), `app/agent/runner.py:56-62` (병렬 조회), `frontend/src/api.js:61-106`, `frontend/src/scene/clinicController.js:354-400` | 없음 (실측 근거: `docs/scenario-check.md:27-38`, 20개 실측 35.2초) | 확인 필요 | 네트워크·실제 GMS 응답 시간은 환경에 따라 달라지므로 제출 직전 `scripts/run_scenarios.py` 및 브라우저에서 20개 파일로 실시간 단계 칩·응답 시간 재실측 필요. |

---

## 2. 화면 (DR.PATCH 진료실) (`docs/spec.md:263-277`)

| 기준 | 보장하는 코드 (파일:줄) | 보장하는 테스트 (파일::테스트 이름) | 판정 | 메모 |
|---|---|---|---|---|
| 보이는 이름은 DR.PATCH, 진료실 한 장면(Vue + Three.js) | `frontend/index.html:6`, `frontend/src/App.vue:145-148`, `frontend/src/components/ClinicScene.vue:1-120`, `app/main.py:26-28,90` | `tests/test_api.py::test_screen_is_served_from_same_server` | 일부만 | HTML에 `DR.PATCH`·`<div id="app">`·핵심 `.glb`/`.svg` 200 응답은 테스트됨. 3D 렌더링은 브라우저로 확인: `uvicorn app.main:app` 실행 후 `http://localhost:8000`에서 진료실 책상·박사님·소품 표시 및 콘솔 오류 0건 확인. |
| 대화: 하단 진료 도크 + 박사님 말풍선 + 접는 대화 기록 / 약병 속 알약 / 조회 제외 목록은 업로드 안내에 | `frontend/src/components/ChatBar.vue:41-96`, `frontend/src/components/Controls.vue:7-14`, `frontend/src/components/SpeechBubble.vue:63-75`, `frontend/src/scene/props/jarAndTray.js:76-81`, `frontend/src/App.vue:56-69` | 없음 | 일부만 | 도크·말풍선·접는 대화 기록·약병 알약은 구현됨. **조회 제외 목록(`res.excluded`)을 업로드 안내에 표시하는 코드가 `App.vue:56-69`에 누락**. 브라우저로 확인: 파일 첨부·드래그 앤 드롭, 메시지 입력(`Enter`/`Shift+Enter`), 대화 기록 열기/닫기 확인. |
| 실행 단계 표시: 상단 단계 칩(접수·검사·판정·처방), 수액 방울, 진료 기록 티커, 검사 결과 이름표 | `frontend/src/components/StatusChip.vue:1-16`, `frontend/src/scene/props/iv.js:18-33`, `frontend/src/App.vue:150-154`, `frontend/src/scene/clinicController.js:355-399` | 없음 | 일부만 | 단계 칩·수액·티커·떠오르는 이름표가 동작하나, **`clinicController.js:373-375`에서 `tool_result` 성공 시 실제 심각도와 무관하게 `safe`("안전") 칩을 띄움**(취약점이 있어도 잠깐 안전으로 표시). 브라우저로 확인: 진료 시작 후 상단 단계 칩·수액 방울·약병 위 칩·왼쪽 하단 티커 확인. |
| 계획 관리: 회차 = 블리스터 한 판(최대 3), 알약 클릭 → 처방전 종이, 진료 예약 종이(달력·수정·삭제·겹침 경고) | `frontend/src/scene/props/blister.js:23-112`, `frontend/src/scene/props/stamp.js:12-31`, `frontend/src/components/PaperSheet.vue:55-134`, `frontend/src/components/CalendarSheet.vue:1-225` | 없음 (백엔드 CRUD/겹침은 `tests/test_api.py`, `tests/test_calendar.py`) | 일부만 | 블리스터·처방전·달력 CRUD·겹침 경고는 구현. 단, **`stamp.js:21`의 `bl.label.redraw(true)`가 `state.stamped`를 바꾸지 않아 `calendar_event`가 없을 때 `Rx 확정` 도장이 라벨에 안 찍힘**(`clinicController.js:419-421`), `PaperSheet.vue:112-134`에 `calendar_conflicts`·`calendar_check: "확인 못 함"` 표시 누락. 브라우저로 확인: 알약·블리스터·대기 모니터/`진료 예약` 클릭. |
| 실행 로그: 차트(클립보드) → 진료 기록 종이(세션 목록 → 이벤트 순서, 재계획 이유) | `frontend/src/scene/props/chart.js:1-34`, `frontend/src/scene/clinicController.js:542-543`, `frontend/src/components/LogSheet.vue:1-139` | 없음 (백엔드 `/logs`는 `tests/test_api.py::test_logs_list_detail_delete_and_no_update`) | 일부만 | 차트 클릭·세션 목록·`#seq` 정렬·삭제 확인은 구현. `LogSheet.vue:120`의 `s.event_count` 불일치 및 `llm_decision` 미포맷 보완 필요. 브라우저로 확인: 책상 오른쪽 차트 또는 `[진료 기록]` 클릭. |
| 안전 → 곡반, 회차에 못 든 것 → 약병("다음 진료"), 확인 못 함·보류 → 약병 + 이름표 | `frontend/src/scene/clinicController.js:285-338`, `frontend/src/components/PaperSheet.vue:136-171` | 없음 | 테스트 없음 | 코드상 `safe`→곡반(`trayPill`), `unassigned`→약병(`다음 진료`), `unchecked`/`held`→약병(`확인 못 함`/`보류`) 및 이름표 표시 구현됨. 브라우저로 확인: 안전·초과·실패 패키지가 섞인 파일로 진료 후 곡반·약병·이름표 클릭 확인. |
| WebGL 없거나 "목록으로 보기" → 평평한 목록, 움직임 줄이기 지원 | `frontend/src/components/TopTools.vue:16-21`, `frontend/src/components/FallbackList.vue:1-106`, `frontend/src/App.vue:15-22,182-195`, `frontend/src/scene/utils.js:4-11` | 없음 | 테스트 없음 | `hasWebGL()` 감지, `목록으로 보기` ↔ `3D 진료실로 보기` 토글, `prefers-reduced-motion` 및 체크박스 연동 구현됨. 브라우저로 확인: `목록으로 보기` 토글, `움직임 줄이기` 체크, WebGL 비활성 환경에서 목록 렌더링 확인. |
| 화면 하단에 세 API 출처 표기 (`참고용 정보 · endoflife.date · OSV.dev CC-BY 4.0 · PyPI`) | `frontend/index.html:14-19` | `tests/test_api.py::test_screen_is_served_from_same_server` (`"참고용 정보"`, `"OSV.dev"` 검사) | 보장됨 | 정적 HTML 하단에 세 출처와 링크(`rel="noopener"`) 포함. 브라우저로 확인: 데스크톱·모바일(390px) 하단에서 도크와 겹치지 않는지 확인. |
| 화면에 값을 지어내지 않는다 (확인 못 한 값은 "미상" / "확인 못 함") | `frontend/src/demo.js:1-18`, `frontend/src/components/PaperSheet.vue:72,84,86,124,154,158`, `frontend/src/components/FallbackList.vue:46,56,77,94` | 없음 (백엔드 미상/확인 못 함은 `tests/test_tools.py`, `tests/test_agent_graph.py`) | 테스트 없음 | 화면 템플릿에서 누락 필드를 `'미상'`/`'확인 못 함'`으로 폴백. 브라우저로 확인: 심각도 없는 취약점·EOL 미확인·조회 실패 패키지에서 임의 값 없이 표시되는지 확인. |

---

## 3. 말투 (DR.PATCH) (`docs/spec.md:278-284`)

| 기준 | 보장하는 코드 (파일:줄) | 보장하는 테스트 (파일::테스트 이름) | 판정 | 메모 |
|---|---|---|---|---|
| Agent는 능청스러운 나이 든 박사님처럼 말한다 | `app/agent/brain.py:70-73,154-156` (`SYSTEM`, `write_response` 프롬프트) | 없음 (`tests/`는 `FakeBrain`만 사용) | 확인 필요 | 프롬프트 지시만 존재하며 자동 테스트 없음. `scripts/run_agent.py`로 실제 GMS 출력 확인 필요. |
| 능청은 표현에만, 숫자·버전·날짜·심각도는 코드 값 그대로(없으면 "미상"/"확인 못 함") | `app/agent/brain.py:68-73,132-134,154-160`, `app/agent/render.py:47-71` (`fallback_text`) | `tests/test_agent_graph.py::test_response_failure_falls_back_to_code_text`, `tests/test_agent_graph.py::test_review_3_fact_tool_result_is_computed_by_code` | 일부만 | LLM 실패 시 `fallback_text`와 사실 조회 코드 계산은 테스트됨. 실제 LLM 응답의 숫자/버전 변조 여부는 `scripts/run_agent.py` 수동 확인 필요. |
| 실제 의료 조언처럼 읽히는 말("치료", "복용 권장" 등) 금지 | `app/agent/brain.py:73` | 없음 | 확인 필요 | 프롬프트 문구로만 제한. 코드 레벨 금지어 검사나 자동 테스트는 없음. |
| 답은 짧게(회차별 핵심 한두 줄 + 경고), 꾸밈은 `**굵게**`와 `"- "` 목록만 | `app/agent/brain.py:73,155`, `frontend/src/components/RichText.vue:1-30` | 없음 | 확인 필요 | 프롬프트에 12줄 이내·`**굵게**`/`- ` 제한 명시, 화면은 `RichText.vue`가 `v-html` 없이 `**굵게**`·목록·제목만 렌더링. 실제 LLM 준수 여부는 수동 확인 필요. |
| 고정 문구(되묻기·오류 안내)는 코드가 작성 (말투 규칙 대상 외) | `app/agent/state.py:56-67` (`schedule_ask_message`, `ask_message`), `app/api/chat.py:26-27`, `app/agent/graph.py:113,163` | `tests/test_agent_graph.py::test_missing_inputs_asks_only_missing_and_calls_no_tool`, `tests/test_api.py::test_missing_api_key_shows_short_notice`, `tests/test_agent_graph.py::test_analyze_failure_ends_with_notice` | 보장됨 | 되묻기·API 키 누락·오류 안내는 모두 코드 고정 문자열로 테스트 통과. |

---

## 제출 전에 꼭 고칠 것 (심각도 순, 최대 5개)

1. **[높음] 업로드 시 조회 제외 목록(`excluded`) 화면 미표시** (`frontend/src/App.vue:56-69`)
   - 명세 완료 기준(`docs/spec.md:268,293`)인 "`-e`나 `>=` 줄은 조회 제외 목록에 보이고"를 백엔드만 충족하고 화면은 `res.excluded`를 버리고 있음. 업로드 완료 안내(말풍선·대화 기록)에 제외 줄 번호·내용·이유를 함께 표시해야 함.
2. **[높음] `calendar_event` 없을 때 확정 도장(`Rx 확정`) 미표시** (`frontend/src/scene/props/stamp.js:21`, `frontend/src/scene/clinicController.js:419-421`)
   - `bl.label.redraw(true)`가 `state.stamped`를 변경하지 않고, `clinicController.js:419`가 `conf?.calendar_event`가 있을 때만 `pack.redrawLabel({ stamped: true, reserved: true })`를 호출함. `CALENDAR_BACKEND=off`이거나 캘린더 등록 실패 시 도장 자국이 라벨에 남지 않으므로 `pack.redrawLabel({ stamped: true, reserved: !!conf?.calendar_event })`로 항상 갱신해야 함.
3. **[중간] 진료 기록(실행 로그) 세션 건수 필드 불일치 및 `llm_decision` 미표시** (`frontend/src/components/LogSheet.vue:15-51,120` vs `app/db/repo.py:118`)
   - `/logs` 응답 필드는 `events`인데 `LogSheet.vue:120`이 `s.event_count`를 읽어 `"건 · ..."`로 숫자가 비어 보임. 또한 `llm_decision` 이벤트를 포맷하지 않아 "왜 재계획 전략을 골랐는지"가 화면 로그에 드러나지 않음.
4. **[중간] 캘린더 충돌 미이동(`calendar_conflicts`)·확인 실패(`calendar_check`) 화면 미표시** (`frontend/src/components/PaperSheet.vue:112-134`)
   - 7일 안에 빈 날이 없어 못 옮긴 경우의 `calendar_conflicts` 경고와 `calendar_check === "확인 못 함"` 안내가 회차 종이에 표시되지 않음(I5 작업 범위).
5. **[낮음] 검사 중 `tool_result` 이름표가 취약 패키지도 잠깐 `"안전"`으로 표시됨** (`frontend/src/scene/clinicController.js:373-375`)
   - `ev.ok`가 `true`이기만 하면 `emitFloatChip(pkgName, 'safe', ...)`를 호출해, 취약점이 있는 패키지도 검사 단계에서 초록색 `"안전"` 칩이 뜸. `tool_result` 단계에서는 중립 상태(`조회 완료`)로 띄우고 실제 등급은 `judgment` 이후에 표시하는 것이 정확함.

---

## Claude Code 판정 (2026-11-19)

지적마다 해당 줄을 열어 확인했다. 5건 모두 **맞음**.

| # | 판정 | 처리 |
|---|---|---|
| 1 | 맞음 — `handleUploadFile`이 `res.packages`만 씀 | 고침: 대화 기록에 "접수하지 않은 줄 n개" + `n번째 줄 내용 — 이유`(최대 8개, 나머지 개수), 말풍선에 한 줄 요약 |
| 2 | 맞음 — `label.redraw(true)`는 `state`를 안 바꾸고, `calendar_event` 없으면 도장 갱신 안 함 | 고침: stamp.js의 `redraw(true)` 제거, 항상 `redrawLabel({stamped:true, reserved:!!conf?.calendar_event})`. 실제 확정으로 라벨 도장 확인 |
| 3 | 맞음 — 필드는 `events`, `llm_decision`은 타입 이름만 나옴 | 고침: `s.events`, `LLM 판단 — 의도/도구 순서/재계획 방법: 값 (코드가 추가: …) · 이유` |
| 4 | 맞음 — I5 범위 | I5 프롬프트에 덧붙임 (`calendar_conflicts`, `calendar_check` "확인 못 함") |
| 5 | 맞음 — 조회 성공(`ok`)은 안전하다는 뜻이 아님 | 고침: `SEV.checked` "조회 완료"(중립 회청색) 추가, `tool_result` 칩은 `checked`/`unchecked` |

검증 중 새로 본 것 (I3에 덧붙임): 탭이 숨겨진 상태에서 페이지를 처음 열면 3D 장면이 그려지지 않은 채 남는 경우가 있었다(새로고침하면 정상). 콘솔 오류·WebGL 컨텍스트 손실은 없었다. 재현 조건 확인 필요.

"확인 필요" 항목(말투는 프롬프트로만 보장, 20개 60초 실측)은 그대로 둔다 — 실측은 제출 전 사람이 한 번 더.
