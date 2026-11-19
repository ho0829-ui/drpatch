# 마지막 갱신: 2026-11-19 / 작성: Claude Code

## 지금 하던 것
- [Claude Code 2026-11-19] 합쳐진 agy 브랜치 3개 삭제(be-01-os·be-02-tone·fe-12-polish). spec v1.18 + agy 작업 문서 I10~I13. 코드는 안 고침
  - 재현(헤드리스 Chrome, 포트 8000에 이미 떠 있던 서버): 처방 완료 → 처음부터 → 재업로드 → 진료 시작 → 조건 되묻기인데 상태 칩 "접수"가 60초 넘게 그대로. 세션 엇갈림 1번(파일=세션 A, 대화=새 세션 B) — 다시 해서는 재현 안 됨
  - 진료 예약: 1280은 모든 세션 계획 14건이 섞임(화면이 session_id 안 넘김), 375는 "그 부탁은 처리하지 못했네요" + 0건 → I12에서 원인 확인
  - 테스트 세션 몇 개가 로컬 DB(data/sudo_patch.db)에 남음 (계획·일정 저장은 없음)
- [Claude Code 2026-11-19] I7·I8·I9 검증 → main 합침(I7·I8 ff, I9 merge — App.vue 업로드 안내 충돌은 I8 말투 + I9 sayBubble로 풂) + 검증에서 나온 것 고침, 261 통과·빌드 경고 0
  - I7 실제 GMS: 맥북 → macOS 버전만 되묻기 → "세쿼이아" → 계획("지원 중 (종료일 미발표)"), 윈도우 11 → 기능 업데이트 되묻기 → "24H2" → 11-24h2-w 조회
  - I8 실제 GMS: 되묻기·계획·잡담·사실 답 모두 박사님 말투, 백틱 없음
  - I9 헤드리스 Chrome(swiftshader): 130개 업로드 → 약병 24알 + "+106", 말풍선 클릭 → 닫힘·입력창 초점, 계획 46~49초(130개) → 약병엔 보류 1알, 곡반 6알 + "+119"
  - 고침: OS 항목을 보이는 이름으로(`app/agent/os_display.py`: macOS·"Windows 11 24H2 (Home/Pro 기준)"), 지원 종료 안내를 OS별로(LTS는 Ubuntu만), eol_checks.os에 보이는 이름·조회 기준 → 답에 Home/Pro 기준이 드러남 / 남은 평범한 문장(연결 끊김·서버 연결·빈 파일·1MB·메시지 실패)도 박사님 말투, 업로드 실패 때 서버 안내(detail)를 그대로 / 처음 보는 OS 되묻기 조사("fedora 쓰시는군요") / 곡반도 6알 상한 + 오른쪽 가장자리 "+N"(안전 패키지가 많으면 한 자리에 겹쳐 쌓였음) / I9가 지운 말풍선 주석 되살림 / 말풍선 아바타가 로고 오른쪽 아래를 덮어 TOP_SAFE 76→96
  - 못 본 것: 로고 "작게 검게 변함" — agy는 원인을 (0,0) 숨은 파일 입력 초점 테두리로 보고 막음, 재현은 이번에도 못 함 → 사용자 확인 필요. 실제 터치는 휴대폰에서
- [agy/be-02-tone] I8 완료: 고정 문구(state·graph·session·chat·프론트) 및 brain.py 프롬프트를 DR.PATCH 박사님 말투로 통일, 백틱 금지, `scripts/run_agent.py` 실측 확인, 260 통과·빌드 경고 0
- [agy/be-01-os] I7 완료: OS 입력(macOS·Windows 정규화·코드네임·버전만 되묻기), `get_eol` `isMaintained` 미발표 지원 처리, `eol_macos_15`/`eol_windows_11-24h2-w` fixture 및 테스트 5건 추가(260 통과)
- [agy/fe-12-polish] I9 완료: 약병 알약 24알(6층) 상한 + 넘친 수 `+N` 이름표, 말풍선 클릭/Esc/Enter/Space 닫기 및 입력창 초점 복귀, `.sr-only` 파일 입력 `(0,0)` 초점 테두리 차단 및 `.brand` 여백·자간·점 폭 조정 (빌드 경고 0, 255 통과)
- [Claude Code 2026-11-19] spec v1.17 — 직접 써 보며 나온 문제를 명세로: OS 입력(macOS·Windows, 버전만 되묻기), 고정 문구도 박사님 말투, 약병 알약 24알 상한, 말풍선 눌러 닫기, 왼쪽 위 로고. agy 작업 문서 `docs/agy-prompt-next.md`(I7 OS → I8 말투, I9 화면). 코드는 안 고침
  - 재현(임시 DB, 실제 GMS): 130개 freeze 업로드 → "Python 3.11…" → OS 물음 → "로컬 맥북" → os=macos·버전 없음 → 같은 문장 또 물음. endoflife: macos 15 → NO_EOL_DATE(eolFrom null·isMaintained true), windows 11 → PRODUCT_NOT_FOUND(실제 cycle `11-24h2-w` 꼴)
  - 로고 "작게 검게 변함"은 1024px 창에서 재현 못 함 → I9에서 재현부터. 따로 본 것: 계획 답에 "Ubuntu 20.04 → 미상으로 올립니다" 문장(명세에 안 넣음, 확인 필요)
- [agy/docs-cleanup] 완료·폐기된 agy 프롬프트 문서 3개 삭제(`agy-guide.md`, `agy-prompt-drpatch.md`, `agy-prompt-next.md`) 및 `docs/tasks.md`·`docs/HANDOFF.md` 정리
- [Claude Code 2026-11-19] I3~I6 검증 → main 합침(ff, 319478c). 범위 OK(frontend만, 새 라이브러리 없음), 빌드 경고 없음, 255 통과
  - 브라우저 확인: 로딩 진행률, I5(11/21 일정 → 1회차 11/22, "원래 11/21"·옮김 안내, 확인 후 일정 삭제), I4(413 문구, API 키 없는 서버 → "설정 필요", 계획 중 서버 끔 → "연결 끊김"+[다시 시도] → 다시 켜고 누르니 계획 완료), 모바일 375 배치
  - 고침: 답이 대화 기록에 두 번 들어가던 것(onChatTurn 한 곳에서만 넣음)
  - 판단: three 본체 523KB(gzip 133KB)는 한 덩어리라 못 나눔 → chunkSizeWarningLimit 550 유지(설정에 이유 주석)
  - 못 본 것: 숨긴 탭 첫 로딩(이 창에서는 재현 안 됨, visibilitychange 대응은 들어감), 실제 터치(롱프레스·두 손가락)는 휴대폰에서 직접
  - S7(Google Calendar 조사) 폐기 — 사용자 결정. 캘린더는 SQLite 구현체로 마무리
- [agy/fe-08-loading ~ agy/fe-11-touch] I3~I6 완료: I3(청크 분리·로딩 진행률·visibilitychange·GPU 해제·언마운트 가드), I4(API 키 누락·연결 끊김 재시도·413·try/finally), I5(이동/충돌/미확인 경고·달력 aria-label·범례), I6(모바일 터치·0.5초 롱프레스·visualViewport·floatChips 5개 상한)
- [Claude Code 2026-11-19] R2(review-frontend) 검증 → 14건 판정(맞음 9·일부 2·틀림 1·문제없음 1·낮음 1). 고침: 매 프레임 이름표·말풍선 갱신 줄임(정지 시 DOM 변경 0), 말풍선 ResizeObserver, 블리스터·알약 치울 때 GPU 해제(공유 재질 제외), 닫힌 종이 inert·초점 복원. I3·I4·I5·I6 프롬프트에 덧붙임. 다음: I3~I6(Hydrogen), S7(Flash)
- [agy/review-frontend] R2 완료: `docs/review-frontend.md` 작성 (`frontend/src` 자원 정리·매 프레임 낭비·오류·누수·접근성·명세·보안 리뷰 및 I3~I6 반영 항목 정리)
- [Claude Code 2026-11-19] R1(review-final) 검증 → 5건 모두 맞음. 1·2·3·5 직접 고침(제외 목록 표시, 캘린더 없을 때도 도장, 로그 건수·LLM 판단 표시, 조회 칩 중립), 4는 I5에, 숨긴 탭 첫 로딩 문제는 I3에 덧붙임. 실제 GMS로 업로드→계획→확정 확인, 255 통과. 다음: R2(Neon)·S7(Flash)
- [agy/review-final] R1 완료: `docs/review-final.md` 작성 (명세 v1.16 완료 기준·화면·말투 ↔ 코드·테스트 대조 및 제출 전 필수 수정 5건 정리)
- [Claude Code 2026-11-19] agy T1~T7 검증 → main 합침(ff, 1e8a378). 범위 OK(app/main.py만), 빌드 OK, 실제 GMS로 업로드→대화→회차 3판→처방전→확정→캘린더→기록→목록 보기 확인
  - 고침: 출처 표기 누락(명세), 확정 회차 round_no(undefined), 말풍선 넘침·마크다운, 하단 두 줄 겹침→한 도크, 이름표 겹침, 종이 여백, 모바일 상단·입력창, 화면 테스트(dist/web 공통 기준) → 255 통과
  - spec v1.16: 보이는 이름 DR.PATCH, 화면 = 진료실(예전 탭 기능 대응표), 말투 절. brain.py 말투 반영, run_agent.py 실제 확인
  - 남은 것: push 안 함, agy/fe-* 브랜치(합쳐짐) 정리, web/ 옛 화면 삭제 여부, 번들 766KB(three 분리 후보)
  - 다음 agy 작업: docs/agy-prompt-next.md — 리뷰 Neon(R1 제출 전 대조, R2 프론트 리뷰) → 구현 Hydrogen(I3 로딩·청크, I4 오류 화면, I5 옮긴 회차 표시, I6 터치) · 조사 Flash(S7 Google Calendar)
- [agy/fe-07-polish] T7 완료: 키보드 접근성(`목록으로 보기` 토글, `진료 기록` 버튼, Tab/Esc), 모바일(390px) 말풍선·종이·컨트롤 배치 개선 (`web/` 유지)
- [agy/fe-06-logs] T6 완료: 차트 클릭 시 `/logs` 세션 목록·`#seq` 순 실행 로그·판단 근거 문장·확인 후 삭제(`LogSheet.vue`)
- [agy/fe-05-confirm] T5 완료: 처방 확정 도장/`예약됨` 라벨, 월간 예약 달력(`CalendarSheet.vue`)·일정 추가/삭제·계획 수정(`PUT /plans/{id}`)·겹침 경고
- [agy/fe-04-chat] T4 완료: 하단 대화 입력창(`ChatBar.vue`, Enter 전송/Shift+Enter 줄바꿈), 접고 펴는 대화 기록, 드래그 앤 드롭 업로드
- [agy/fe-03-live] T3 완료: 실데이터(`/upload`, `/chat` ndjson 이벤트)와 3D 장면·블리스터·처방전 종이 연동
- [agy/fe-02-api] T2 완료: `frontend/src/api.js` 구현 (`upload`, `chat` ndjson 스트림, `plans`, `logs`, `calendar`), 실제 서버(127.0.0.1:8000)로 동작 확인
- [agy/fe-01-scene] T1 완료: `frontend/` Vite + Vue 3 + Three.js 진료실 장면 이식 (`app/main.py` dist 우선 서빙, `tests/test_api.py::test_screen_is_served_from_same_server`는 구 web/ 탭 문자열 검사로 1건 실패 — Claude Code 확인 필요)
- 심화 F3023 캘린더 연동 끝 (테스트 255개, 실제 서버+GMS: 11/21 23시 일정 → 1회차 11/22로 이동, 확정 시 캘린더 등록)
  - app/calendar/backend.py: CalendarBackend 인터페이스 + LocalCalendar(SQLite calendar_events), make_calendar(.env CALENDAR_BACKEND=local|google|off)
  - app/tools/calendar_tools.py: list_calendar_events(date_from, date_to), add_calendar_event(plan_id) — kind local, build_registry(calendar, db_path)일 때만 등록
  - app/agent/planner/calendar_fit.py: find_free_date (7일 안, 내가 등록한 일정 무시) / graph build의 fit_to_calendar → rounds의 moved_from·calendar_conflicts, plan.calendar_check, calendar_check 이벤트
  - /chat 확정 → register_on_calendar (Tool 경유), /calendar/events GET·POST·DELETE
  - app/timewindow.py: 시각 구간 계산 공용 (planner가 app.api를 부르지 않게)
  - 기준선 태그 v1-submit은 캘린더 전 상태

## 다음에 할 것
- agy/fe-13-brand-tip 확인 → I10 → I11 → I12 → I13 (앞 작업 합친 뒤 main에서 브랜치)
- agy I7(`agy/be-01-os`) → I8(`agy/be-02-tone`), I9(`agy/fe-12-polish`) — 끝나면 Claude Code가 확인·합침
- 저장소 정리: 구 화면 `web/` 삭제 여부 결정, `main`에 합쳐진 `agy/*` 로컬 브랜치 정리, `git push`
- 최종 제출 마무리: 셀프 체크리스트 점검, `README.md` 최종 작성
- (선택) R2 잔여 소규모 항목: `logs`·`chatMessages` 배열 상한 설정 (`clinicController.js`, `App.vue`)

## 주의
- spec v1.16 (DR.PATCH 진료실 화면·말투·캘린더 반영). 이벤트 종류에 plan_built·calendar_check 포함
- 가짜 LLM 테스트는 GmsBrain 자체를 검사하지 않음 → brain.py를 고치면 scripts/run_agent.py로 실제 확인할 것
- 응답 시간: 예시 한 건 25~28초. 대부분 LLM 4번(analyze·plan·replan·respond). judge의 목표 버전 재조회는 패키지마다 순서대로 → 3일차 측정 때 병렬화 후보
- 재계획 방식은 LLM이 고름(upgrade_python/hold), 실패하면 upgrade_python. 되묻기 문장은 코드 (spec v1.9)
- 사실 조회 경로도 조건(os 등)을 Memory에 남김
- 구조는 docs/architecture.md (v1). /chat ndjson 스트리밍은 아직 없음
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖)
- .venv는 Python 3.14.7
