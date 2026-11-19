# 프론트엔드 코드 리뷰 (`frontend/src` 전체)

- 작성일: 2026-11-19
- 대상: `frontend/src/` 전체 및 `frontend/index.html` (`main` `d388e37` 기준)
- 코드는 수정하지 않고 문제와 근거(`파일:줄`, 코드 한 줄)만 정리함.

---

## 리뷰 표

| 심각도 | 파일:줄 | 문제 | 근거(코드 인용 한 줄) | 고칠 방향 |
|---|---|---|---|---|
| 높음 | `frontend/src/scene/clinicController.js:630,658` | 매 프레임(60fps)마다 `tagList` 배열을 새로 만들어 Vue `pillTags.value`를 통째로 교체하고, `bubblePos`도 매 프레임 갱신해 `SpeechBubble.vue:27-28`의 `offsetWidth`/`offsetHeight` 강제 리플로우를 유발함 | `onPillTagsUpdate(tagList);` / `onBubblePos(getBubbleAnchor(camera));` | 좌표가 0.5px 이상 변했을 때만 갱신하거나, 이름표·말풍선 DOM의 `style.transform`을 ref로 직접 갱신해 Vue 리렌더링·강제 리플로우 제거. |
| 높음 | `frontend/src/scene/engine.js:137-142` | `dispose()`가 `renderer`/`composer`/`pmrem`/`controls`만 해제하고 `scene` 내부의 `geometry`·`material`·`texture`(`scene.environment`, `CanvasTexture` 등)를 `dispose()`하지 않음 | `function dispose() { controls.dispose(); composer?.dispose(); pmrem.dispose(); renderer.dispose(); }` | `scene.traverse()`로 모든 메시의 `geometry`·`material`·`map` 및 `scene.environment` 텍스처를 해제. |
| 높음 | `frontend/src/scene/clinicController.js:409-433` | `api.chat` 호출만 `try/catch`로 감싸고 그 뒤 `applyPlan()`·`stampPacks()`는 `try/catch` 밖에 있어, 애니메이션/포장 중 예외가 나면 `state`가 `'running'`에 영구히 갇힘 | `if (finalEvent.plan) { await applyPlan(finalEvent.plan); }` | `sendChatMessage` 전체를 `try/catch/finally`로 감싸 예외 시 `state`를 안전하게 복구하고 짧은 오류 안내 표시. |
| 중간 | `frontend/src/components/ClinicScene.vue:41-79` | 비동기 GLB 로딩(`await createClinicController`) 도중 컴포넌트가 언마운트되면 `onBeforeUnmount` 시점에 `controller`가 `null`이라 해제되지 않고, 로딩 완료 후 `requestAnimationFrame`과 리스너가 영구 누수됨 | `controller = await createClinicController(canvasRef.value, {` | `let disposed = false` 플래그를 두고 `onBeforeUnmount`에서 `true` 설정, 완료 후 `disposed`면 즉시 `destroy()` 호출. |
| 중간 | `frontend/src/scene/props/blister.js:18-24`, `frontend/src/scene/props/jarAndTray.js:34-41` | `clearPacks()`·`clearPills()`가 `world.remove()`만 하고 복제된 `geometry`·`wellMat`·`label.tex`를 `dispose()`하지 않아 재업로드·재계획 시 GPU 메모리 누적 | `for (const p of packs) { removePick?.(p.group); world.remove(p.group); }` | 제거 전 하위 메시의 `geometry`·복제 `material`·`CanvasTexture`를 `dispose()` 처리. |
| 중간 | `frontend/src/scene/clinicController.js:84,99-103`, `frontend/src/App.vue:36,69,91` | `logs` 배열과 `chatMessages` 배열에 상한이 없어 세션이 길어지면 끝없이 커지며, `logEvent`마다 `[...logs]` 전체를 새로 복사함 | `logs.push(line); chartApi.redraw(); onLog(line, [...logs]);` | `logs`·`chatMessages`에 상한(예: 최근 200건)을 두고 초과 시 앞쪽을 잘라냄. |
| 중간 | `frontend/src/components/PaperSheet.vue:32-53` | 접근성: 종이가 닫혀 있을 때도 `.sheet`가 DOM에 남아 `role="dialog"`와 닫기 버튼이 Tab 초점을 받으며, 닫힐 때 원래 버튼으로 초점이 돌아가지 않고 `aria-modal="true"`도 없음 | `<div class="sheet" :class="{ open: !!sheet }">` | 닫힘 상태에 `:inert="!sheet"` 또는 `v-if` 적용, `aria-modal="true"` 추가, 열기 전 `document.activeElement`를 저장해 닫을 때 복원. |
| 중간 | `frontend/src/components/CalendarSheet.vue:170-173` | 접근성: 달력 날짜 칸에서 저장된 계획(청록 점)과 개인 일정(코랄 점)을 색 점으로만 구분함(`title`만 있어 키보드·스크린리더 접근 불가) | `<i v-if="cell.hasPlan" class="dot-plan" title="저장된 패치 계획"></i>` | 날짜 버튼에 `aria-label`로 날짜·계획/일정 유무를 읽히게 하고 `aria-pressed` 추가, 달력 상단에 색+글자 범례 표시. |
| 중간 | `frontend/src/api.js:41-58,95-115` | 오류 처리: 서버 413 응답 전용 문구(`파일이 너무 커요 (1MB까지)`)가 없고, `/chat` 스트림 중단 시 `[다시 시도]` 동작과 `final.intent === 'error'` 시 `"설정 필요"` 상태 칩 표시가 없음 | `throw new Error(typeof data.detail === 'string' ? data.detail : '파일을 올리지 못했어요.');` | `res.status === 413` 분기, `final.intent === 'error'` 상태 칩 처리, 마지막 메시지 재전송(`[다시 시도]`) 추가. |
| 낮음 | `frontend/src/components/SpeechBubble.vue:20-22,53` | 타이핑 `setTimeout` 타이머 배열을 `onBeforeUnmount`에서 정리하지 않음 | `timers.push(setTimeout(() => { if (id === typingId) shownText.value = next.slice(0, i + chunk); }, (i / chunk) * step));` | `onBeforeUnmount(clearTimers)` 추가. |
| 낮음 | `frontend/src/scene/utils.js:49-65` | `mergeStatic()`이 병합 전 임시로 생성한 `BufferGeometry`(`g`, `ng`)를 `dispose()`하지 않음 | `const merged = mergeGeometries(list, false); if (!merged) continue;` | 병합 후 `geos`와 `list`의 임시 지오메트리를 `dispose()`. |
| 낮음 | `frontend/src/components/ClinicScene.vue:55-60` | 병렬 `tool_result`가 한꺼번에 오면 `floatChips` DOM이 같은 위치에 제한 없이 겹쳐 쌓임 (1.5초 뒤 제거되어 영구 누수는 아님) | `floatChips.value.push(chip);` | 동시에 표시되는 `floatChips` 최대 개수(예: 5개) 제한. |
| 낮음 | `frontend/src/scene/clinicController.js:572-575,632-658` | `onKeyDown`·`frame()`의 `toScreen()`/`placed`에서 소규모 배열·벡터를 반복 생성함 (단 `tmpV`, `headPos`는 외부 재사용 중) | `const off = camera.position.clone().sub(controls.target);` | `toScreen`에 출력 객체 재사용, `tagList` 갱신 조건부 처리. |
| 확인 필요 | `frontend/index.html:16-18`, `frontend/src/components/RichText.vue:1-30` | 보안·명세 점검 결과: `v-html`/`innerHTML` 사용 0건(`RichText.vue`는 텍스트 노드만 렌더링), 외부 데이터 API/LLM 직접 호출 0건, 외부 링크 `target="_blank" rel="noopener"` 적용됨 | `// v-html을 쓰지 않는다 (글자는 모두 텍스트로만 들어간다).` | 현재 보안·명세 위반 없음. 외부 링크에 `rel="noopener noreferrer"`까지 보강할지 여부만 선택 확인. |

---

## Hydrogen 작업(I3~I6)에 같이 넣으면 좋은 것

### I3 · 첫 화면 속도와 로딩 진행 표시 (`agy/fe-08-loading`)
- `ClinicScene.vue:41-79`의 비동기 GLB 로딩 중 언마운트 가드(`disposed` 플래그) 추가.
- `engine.js:137-142`·`blister.js:18-24`·`jarAndTray.js:34-41`·`utils.js:49-65`의 Three.js `geometry`/`material`/`texture` `dispose()` 보강.
- `clinicController.js:630,658`의 매 프레임 Vue `pillTags`/`bubblePos` 전체 교체 및 `SpeechBubble.vue` 강제 리플로우 최적화(초기 렌더·프레임 속도 개선과 직결).

### I4 · 오류 화면: API 키 없음 · 서버 끊김 · 업로드 실패 (`agy/fe-09-errors`)
- `clinicController.js:409-433`의 `applyPlan()`/`stampPacks()`를 `try/catch/finally`로 감싸 `'running'` 상태 고착 방지.
- `api.js:41-58`의 `413` 상태 코드 전용 문구(`파일이 너무 커요 (1MB까지)`) 및 `final.intent === 'error'` 시 상태 칩 `"설정 필요"`, 스트림 끊김 시 `[다시 시도]` 버튼.

### I5 · 캘린더 때문에 옮긴 회차 표시 (`agy/fe-10-moved`)
- `CalendarSheet.vue:170-173`의 달력 점 색 구분에 `aria-label`·`aria-pressed`·색+글자 범례 추가(접근성).

### I6 · 모바일 터치 (`agy/fe-11-touch`)
- `PaperSheet.vue:32-53`의 닫힘 상태 `:inert="!sheet"`·`aria-modal="true"`·닫기 시 초점 복원.
- `SpeechBubble.vue`의 `onBeforeUnmount(clearTimers)` 정리 및 `ClinicScene.vue:55-60`의 `floatChips` 동시 표시 상한(모바일 작은 화면 겹침 방지).

### I3~I6 범위 밖 (별도 소규모 수정 권장)
- `clinicController.js:84`·`App.vue:36`: `logs`·`chatMessages` 배열 상한 설정.
