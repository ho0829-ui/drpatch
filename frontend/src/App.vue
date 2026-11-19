<script setup>
import { asset } from './paths.js';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as api from './api.js';
import { previewConditions } from './conditionPreview.js';
import ChatBar from './components/ChatBar.vue';
import ClinicScene from './components/ClinicScene.vue';
import ConditionChips from './components/ConditionChips.vue';
import Controls from './components/Controls.vue';
import FallbackList from './components/FallbackList.vue';
import PaperSheet from './components/PaperSheet.vue';
import SpeechBubble from './components/SpeechBubble.vue';
import StatusChip from './components/StatusChip.vue';
import TopTools from './components/TopTools.vue';

const sceneRef = ref(null);
const chatBarRef = ref(null);
const fileInputRef = ref(null);
const reduced = ref(matchMedia('(prefers-reduced-motion: reduce)').matches);
watch(
  reduced,
  (val) => {
    document.body.classList.toggle('reduced', val);
  },
  { immediate: true },
);

const fallback = ref(false);
const listView = ref(false);
const fallbackMsg = ref(undefined);
const state = ref('idle');
const status = ref({ text: '대기 중', stage: -1 });
const bubbleText = ref('');
const bubbleSeq = ref(0);
const bubbleAction = ref(null);
const bubblePos = ref({ right: 0, top: 0 });
const logs = ref([]);
const activeSheet = ref(null);
const eggCount = ref({ found: 0, total: 16 });
const nightState = ref({ unlocked: false, night: false });
const currentPlan = ref(null);
const currentPackages = ref([]);
const currentConditions = ref(null);
const chatMessages = ref([]);
const chatDraft = ref('');
const historyOpen = ref(false);
const dragging = ref(false);
const uploading = ref(false);
const retryMessage = ref(null);
const exampleCatalog = ref([]);
const activeExampleId = ref(null);

const DONE_EXAMPLES_KEY = 'drpatch.examples.done';

const isBusy = computed(() => uploading.value || state.value === 'running' || state.value === 'confirming');
const tickerLines = computed(() => logs.value.slice(-4).reverse());
const draftConditions = computed(() => previewConditions(chatDraft.value));
const thinkingText = computed(() => {
  if (state.value !== 'running' && state.value !== 'confirming') return '';
  const st = status.value?.text || '';
  if (['접수', '검사 중', '판정', '재계획', '처방'].includes(st)) {
    return `박사님이 차트를 보는 중… (${st})`;
  }
  return '박사님이 차트를 보는 중…';
});

function shortenForBubble(text) {
  const src = String(text || '');
  if (!historyOpen.value && window.innerWidth >= 768) return src;
  const lines = src.split('\n');
  if (lines.length <= 3 && src.length <= 200) return src;
  const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
  let pick = nonEmpty[0] || '';
  if (pick.startsWith('차트:') && nonEmpty.length > 1) {
    pick = nonEmpty[1];
  }
  const clean = pick.replace(/^\s*[-*•#]+\s*/, '').replace(/\*\*/g, '');
  const m = clean.match(/^(.+?[.?!])(?:\s|$)/);
  const firstSentence = m ? m[1] : clean.slice(0, 100);
  return `${firstSentence}\n자세한 처방은 대화 기록에 적었습니다.`;
}

function sayBubble(text, action = null) {
  bubbleText.value = text;
  bubbleAction.value = action;
  bubbleSeq.value++;
}

// 다음 환자 링크: onChatTurn이 먼저 오고 답 말풍선(say)이 뒤에 오므로, 여기 담아 뒀다가 그 말풍선에 붙인다
let pendingBubbleAction = null;

function onSceneSay(text) {
  const isGreeting =
    currentPackages.value.length === 0 &&
    (String(text).startsWith('어서 오세요') || String(text).startsWith('새 차트입니다'));
  let action = null;
  if (isGreeting) {
    action = { prefix: '파일이 없으시면 ', label: '예시 차트', suffix: '부터 보시죠.', kind: 'examples', focusId: '' };
  } else if (pendingBubbleAction) {
    action = pendingBubbleAction;
  }
  pendingBubbleAction = null;
  sayBubble(shortenForBubble(text), action);
}

function openExamples(focusId = '') {
  activeSheet.value = { kind: 'examples', color: '#3E9E98', focusId };
}

function onBubbleAction(action) {
  if (action?.kind === 'examples') {
    openExamples(action.focusId || '');
  }
}

function markExampleDone(id) {
  if (!id) return;
  try {
    const cur = JSON.parse(localStorage.getItem(DONE_EXAMPLES_KEY) || '[]');
    const set = new Set(Array.isArray(cur) ? cur : []);
    set.add(id);
    localStorage.setItem(DONE_EXAMPLES_KEY, JSON.stringify([...set]));
  } catch { /* 무시 */ }
}

function focusChatInput() {
  document.querySelector('.chat-textarea')?.focus({ preventScroll: true });
}

function onFallback(msg) {
  fallback.value = true;
  if (msg) fallbackMsg.value = msg;
}

function closeSheet() {
  activeSheet.value = null;
  sceneRef.value?.unpopPill();
}

function onInspectPlanItem({ item, plan }) {
  activeSheet.value = {
    kind: 'item',
    item: {
      name: item.name,
      cur: item.current_version || '미상',
      tgt: item.target_version || null,
      sev: item.severity || 'unknown',
      round: plan?.round_no || null,
      status: 'patch',
      reason: item.reason || '',
      flags: item.flags || [],
      eol_date: item.eol_date || null,
      done_at: item.done_at || plan?.done_at || null,
    },
    plan: currentPlan.value,
    color: '#3E9E98',
  };
}

function triggerUpload() {
  fileInputRef.value?.click();
}

async function handleUploadFile(file, opts = {}) {
  if (!file || uploading.value) return false;
  uploading.value = true;
  status.value = { text: '접수 중…', stage: 0 };
  try {
    const res = await api.upload(file);
    currentPackages.value = res.packages || [];
    activeExampleId.value = opts.exampleId || null;
    sceneRef.value?.loadPackages(currentPackages.value);
    const excluded = res.excluded || [];
    const lines = [`흠, 어디 보자… ${file.name} ${currentPackages.value.length}줄. 접수됐습니다.`];
    if (excluded.length) {
      lines.push(`**차트에서 뺀 줄 ${excluded.length}개**`);
      for (const ex of excluded.slice(0, 8)) lines.push(`- ${ex.line_no}번째 줄 ${ex.text} — ${ex.reason}`);
      if (excluded.length > 8) lines.push(`- 그 밖 ${excluded.length - 8}개`);
    }
    chatMessages.value.push({ role: 'assistant', text: lines.join('\n') });
    if (excluded.length && currentPackages.value.length) {
      sayBubble(`흠, ${currentPackages.value.length}줄 접수됐습니다. **${excluded.length}줄은 차트에서 뺐어요** — 대화 기록에 적어 뒀습니다.`);
    }
    return true;
  } catch (err) {
    status.value = { text: currentPackages.value.length ? '접수 완료' : '대기 중', stage: currentPackages.value.length ? 0 : -1 };
    sayBubble(err.message || '허허, 파일을 받지 못했네요. 다시 올려 보시죠.');
    return false;
  } finally {
    uploading.value = false;
  }
}

function nextTuesdayDate(offsetDays = 0) {
  const d = new Date();
  // 다음 화요일 (0=일, 2=화). 오늘이 화요일이면 7일 뒤.
  const diff = (2 - d.getDay() + 7) % 7 || 7;
  d.setDate(d.getDate() + diff + offsetDays);
  return d;
}

function nextTuesdayLabel() {
  const d = nextTuesdayDate(0);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function toIsoDate(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

async function ensureSeedEvent(se) {
  if (!se?.title) return;
  const iso = toIsoDate(nextTuesdayDate(se.offset_days || 0));
  try {
    const existing = await api.calendar.list(iso, iso);
    const dup = (existing || []).some((ev) => ev.date === iso && ev.title === se.title);
    if (!dup) {
      await api.calendar.add({
        title: se.title,
        date: iso,
        start: se.start || null,
        end: se.end || null,
      });
    }
  } catch { /* 캘린더 추가 실패해도 예시 진행 */ }
}

// 예시 시작은 한 번에 하나만 (일정 넣기 → 업로드 사이에 두 번 눌리면 예시 일정이 두 개 생길 수 있음)
let selectingExample = false;

async function onSelectExample(ex) {
  if (!ex?.file || isBusy.value || selectingExample) return;
  selectingExample = true;
  closeSheet();
  try {
    if (ex.addSeedEvent && ex.seed_event) {
      await ensureSeedEvent(ex.seed_event);
    }
    const res = await fetch(asset(`examples/${ex.file}`), { cache: 'no-store' });
    if (!res.ok) throw new Error('예시 파일을 불러오지 못했어요.');
    const text = await res.text();
    const file = new File([text], ex.file, { type: 'text/plain' });
    const ok = await handleUploadFile(file, { exampleId: ex.id });
    if (!ok) return;
    const condText = String(ex.condition_template || '').replace('{date}', nextTuesdayLabel());
    chatBarRef.value?.setText(condText);
    sayBubble('예시 차트를 꺼냈습니다. 조건은 입력창에 적어 뒀으니 보내기만 누르시죠.');
  } catch {
    sayBubble('허허, 예시 파일을 못 꺼냈네요. 다시 골라 보시죠.');
  } finally {
    selectingExample = false;
  }
}

async function onFileSelected(e) {
  const file = e.target.files?.[0];
  e.target.value = '';
  await handleUploadFile(file);
}

let dragDepth = 0;

function hasDraggedFiles(e) {
  const types = e.dataTransfer?.types;
  return Boolean(types && Array.from(types).includes('Files'));
}

function clearDrag() {
  dragDepth = 0;
  dragging.value = false;
}

function onDragEnter(e) {
  if (!hasDraggedFiles(e)) return;
  e.preventDefault();
  dragDepth += 1;
  dragging.value = true;
}

function onDragOver(e) {
  if (!hasDraggedFiles(e)) return;
  e.preventDefault();
  dragging.value = true;
}

function onDragLeave() {
  if (!dragging.value) return;
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) dragging.value = false;
}

async function onDropFile(e) {
  e.preventDefault();
  clearDrag();
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  await handleUploadFile(file);
}

// 창 밖으로 나갔는지는 좌표로 본다 (Safari 등은 relatedTarget을 늘 비워서 안에서 옮겨도 꺼질 수 있음)
function onWindowDragLeave(e) {
  const out = e.clientX <= 0 || e.clientY <= 0 || e.clientX >= innerWidth || e.clientY >= innerHeight;
  if (out) clearDrag();
}

function onWindowKeyDown(e) {
  if (e.key === 'Escape' && dragging.value) clearDrag();
}

onMounted(() => {
  window.addEventListener('dragleave', onWindowDragLeave);
  window.addEventListener('dragend', clearDrag);
  window.addEventListener('drop', clearDrag);
  window.addEventListener('blur', clearDrag);
  window.addEventListener('keydown', onWindowKeyDown);
  fetch(asset('examples/index.json'))
    .then((r) => (r.ok ? r.json() : []))
    .then((list) => {
      if (Array.isArray(list)) exampleCatalog.value = list;
    })
    .catch(() => {});
});

onBeforeUnmount(() => {
  window.removeEventListener('dragleave', onWindowDragLeave);
  window.removeEventListener('dragend', clearDrag);
  window.removeEventListener('drop', clearDrag);
  window.removeEventListener('blur', clearDrag);
  window.removeEventListener('keydown', onWindowKeyDown);
});

// 대화 기록에 답을 넣는 곳은 onChatTurn 한 곳뿐 (보내기·다시 시도·진료 시작 모두 거기로 온다)
async function onSendChat(message) {
  chatBarRef.value?.openHistory();
  chatMessages.value.push({ role: 'user', text: message });
  await sceneRef.value?.sendChatMessage(message);
}

async function onStartVisit() {
  if (currentPackages.value.length > 0) {
    chatBarRef.value?.openHistory();
    const lastUser = [...chatMessages.value].reverse().find((m) => m.role === 'user');
    if (lastUser?.text !== '패치 계획 짜줘') {
      chatMessages.value.push({ role: 'user', text: '패치 계획 짜줘' });
    }
  }
  await sceneRef.value?.runVisit();
}

async function onRetryChat() {
  if (!retryMessage.value) return;
  chatBarRef.value?.openHistory();
  await sceneRef.value?.sendChatMessage(retryMessage.value);
}

function onChatTurn({ msg, finalEvent }) {
  if (finalEvent?.conditions) {
    currentConditions.value = finalEvent.conditions;
  }
  // 진료 시작 버튼처럼 입력창을 거치지 않은 말은 여기서 넣는다 (다시 시도는 이미 들어 있음)
  const lastUser = [...chatMessages.value].reverse().find((m) => m.role === 'user');
  if (lastUser?.text !== msg) chatMessages.value.push({ role: 'user', text: msg });
  if (finalEvent?.answer) chatMessages.value.push({ role: 'assistant', text: finalEvent.answer });

  // 모바일(<768)에서 처방(블리스터)이 나오면 열린 대화 기록이 블리스터를 가리지 않게 접는다
  if (finalEvent?.plan?.rounds?.length && window.innerWidth < 768) {
    chatBarRef.value?.closeHistory();
  }

  // 예시로 올린 세션에서 처방(계획)이 나오면 진료함 기록 + 다음 환자 권유
  if (finalEvent?.plan && !(finalEvent.missing?.length) && activeExampleId.value) {
    markExampleDone(activeExampleId.value);
    const idx = exampleCatalog.value.findIndex((e) => e.id === activeExampleId.value);
    const nextEx = idx >= 0 && idx < exampleCatalog.value.length - 1 ? exampleCatalog.value[idx + 1] : null;
    if (nextEx) {
      const nextLine = `다음 환자도 보시겠어요? — ${nextEx.title}`;
      chatMessages.value.push({ role: 'assistant', text: nextLine });
      const nextAction = { prefix: '', label: nextLine, suffix: '', kind: 'examples', focusId: nextEx.id };
      pendingBubbleAction = nextAction;
      bubbleAction.value = nextAction; // 답 말풍선이 오지 않는 경우에도 지금 말풍선에 남게
    }
  }
  if (!finalEvent?.answer) pendingBubbleAction = null;
}

function reloadPage() {
  if (!confirm('파일과 조건, 대화를 모두 지우고 처음부터 할까요?')) return;
  api.setSession(null);
  try {
    sessionStorage.setItem('drpatch.restarted', '1');
  } catch { /* 무시 */ }
  location.reload();
}
</script>

<template>
  <input
    ref="fileInputRef"
    type="file"
    accept=".txt,text/plain"
    class="sr-only"
    tabindex="-1"
    aria-hidden="true"
    @change="onFileSelected"
  >

  <div
    v-show="!fallback && !listView"
    class="drop-zone"
    @dragenter="onDragEnter"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDropFile"
  >
    <div class="sr-only" aria-live="polite">{{ dragging ? '파일을 놓으면 접수합니다' : '' }}</div>
    <ClinicScene
      v-if="!fallback"
      ref="sceneRef"
      :reduced="reduced"
      @fallback="onFallback"
      @state-change="state = $event"
      @status="status = $event"
      @say="onSceneSay($event)"
      @log="logs = $event.logs"
      @open-sheet="activeSheet = $event"
      @close-sheet="activeSheet = null"
      @bubble-pos="bubblePos = $event"
      @egg-count="eggCount = $event"
      @upload-request="triggerUpload"
      @plan-update="currentPlan = $event.plan; currentPackages = $event.packages"
      @chat-turn="onChatTurn"
      @retry-change="retryMessage = $event"
      @night-change="nightState = $event"
    />

    <div v-if="dragging" class="drop-overlay" @click="clearDrag">
      <button type="button" class="drop-close" aria-label="닫기" @click.stop="clearDrag">×</button>
      <p>여기에 requirements.txt를 놓아 주세요</p>
    </div>

    <header class="brand">
      <img :src="asset('brand/logo-mark.svg')" width="46" height="46" alt="" draggable="false">
      <div><b>DR<span class="dot">.</span>PATCH</b><small>진료 책상</small></div>
    </header>

    <StatusChip :text="status.text" :stage="status.stage" />

    <div class="ticker" aria-hidden="true">
      <div v-for="(line, i) in tickerLines" :key="i">{{ line }}</div>
    </div>

    <TopTools
      :reduced="reduced"
      :eggs="eggCount"
      :night-state="nightState"
      @toggle-night="sceneRef?.setNight(!nightState.night)"
      @update:reduced="reduced = $event"
      @toggle-list="listView = true"
      @reset="reloadPage"
    />

    <SpeechBubble
      :text="bubbleText"
      :seq="bubbleSeq"
      :reduced="reduced"
      :pos="bubblePos"
      :action="bubbleAction"
      @closed="focusChatInput"
      @action="onBubbleAction"
    />

    <ChatBar
      ref="chatBarRef"
      :messages="chatMessages"
      :busy="isBusy"
      :thinking-text="thinkingText"
      @send="onSendChat"
      @upload="triggerUpload"
      @examples="openExamples()"
      @update:draft="chatDraft = $event"
      @history-change="historyOpen = $event"
    >
      <Controls
        :state="uploading ? 'running' : state"
        :can-retry="!!retryMessage"
        @start="onStartVisit"
        @confirm="sceneRef?.confirmPlan()"
        @retry="onRetryChat"
        @calendar="activeSheet = { kind: 'calendar', color: '#3E9E98' }"
        @logs="activeSheet = { kind: 'log', color: '#3E9E98' }"
      />
      <template #chips>
        <ConditionChips
          :packages-count="currentPackages.length"
          :conditions="currentConditions"
          :draft="draftConditions"
          @upload="triggerUpload"
          @examples="openExamples()"
          @fill="chatBarRef?.appendSnippet($event)"
          @focus-input="chatBarRef?.focusInput()"
        />
      </template>
    </ChatBar>
  </div>

  <FallbackList
    v-if="fallback || listView"
    :message="fallback ? fallbackMsg : '키보드·목록 보기로 전체 처방 내용을 확인합니다.'"
    :can-return-3d="!fallback"
    :plan="currentPlan"
    :packages="currentPackages"
    :state="state"
    @return-3d="listView = false"
    @upload="triggerUpload"
    @start="sceneRef?.runVisit()"
    @confirm="sceneRef?.confirmPlan()"
    @calendar="activeSheet = { kind: 'calendar', color: '#3E9E98' }"
    @logs="activeSheet = { kind: 'log', color: '#3E9E98' }"
  />

  <PaperSheet
    :sheet="activeSheet"
    @close="closeSheet"
    @inspect-item="onInspectPlanItem"
    @plan-done-change="sceneRef?.markRoundDone($event.roundNo, $event.done)"
    @select-example="onSelectExample"
  />
</template>
