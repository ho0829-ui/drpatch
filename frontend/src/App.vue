<script setup>
import { computed, ref, watch } from 'vue';
import * as api from './api.js';
import ChatBar from './components/ChatBar.vue';
import ClinicScene from './components/ClinicScene.vue';
import Controls from './components/Controls.vue';
import FallbackList from './components/FallbackList.vue';
import PaperSheet from './components/PaperSheet.vue';
import SpeechBubble from './components/SpeechBubble.vue';
import StatusChip from './components/StatusChip.vue';
import TopTools from './components/TopTools.vue';

const sceneRef = ref(null);
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
const bubblePos = ref({ right: 0, top: 0 });
const logs = ref([]);
const activeSheet = ref(null);
const eggCount = ref({ found: 0, total: 16 });
const currentPlan = ref(null);
const currentPackages = ref([]);
const chatMessages = ref([]);
const dragging = ref(false);
const retryMessage = ref(null);

const isBusy = computed(() => state.value === 'running' || state.value === 'confirming');
const tickerLines = computed(() => logs.value.slice(-4).reverse());

function onFallback(msg) {
  fallback.value = true;
  if (msg) fallbackMsg.value = msg;
}

function closeSheet() {
  activeSheet.value = null;
  sceneRef.value?.unpopPill();
}

function triggerUpload() {
  fileInputRef.value?.click();
}

async function handleUploadFile(file) {
  if (!file) return;
  try {
    const res = await api.upload(file);
    currentPackages.value = res.packages || [];
    sceneRef.value?.loadPackages(currentPackages.value);
    const excluded = res.excluded || [];
    const lines = [`${file.name} (${currentPackages.value.length}개 패키지) 접수됐습니다.`];
    if (excluded.length) {
      lines.push(`**접수하지 않은 줄 ${excluded.length}개**`);
      for (const ex of excluded.slice(0, 8)) lines.push(`- ${ex.line_no}번째 줄 ${ex.text} — ${ex.reason}`);
      if (excluded.length > 8) lines.push(`- 그 밖 ${excluded.length - 8}개`);
    }
    chatMessages.value.push({ role: 'assistant', text: lines.join('\n') });
    if (excluded.length && currentPackages.value.length) {
      bubbleText.value = `${currentPackages.value.length}개 패키지 접수했어요. **${excluded.length}줄은 접수하지 않았어요** — 대화 기록에 이유를 적어 뒀습니다.`;
    }
  } catch (err) {
    bubbleText.value = err.message || '파일을 올리지 못했어요.';
  }
}

async function onFileSelected(e) {
  const file = e.target.files?.[0];
  e.target.value = '';
  await handleUploadFile(file);
}

async function onDropFile(e) {
  dragging.value = false;
  const file = e.dataTransfer?.files?.[0];
  await handleUploadFile(file);
}

// 대화 기록에 답을 넣는 곳은 onChatTurn 한 곳뿐 (보내기·다시 시도·진료 시작 모두 거기로 온다)
async function onSendChat(message) {
  chatMessages.value.push({ role: 'user', text: message });
  await sceneRef.value?.sendChatMessage(message);
}

async function onRetryChat() {
  if (retryMessage.value) await sceneRef.value?.sendChatMessage(retryMessage.value);
}

function onChatTurn({ msg, finalEvent }) {
  // 진료 시작 버튼처럼 입력창을 거치지 않은 말은 여기서 넣는다 (다시 시도는 이미 들어 있음)
  const lastUser = [...chatMessages.value].reverse().find((m) => m.role === 'user');
  if (lastUser?.text !== msg) chatMessages.value.push({ role: 'user', text: msg });
  if (finalEvent?.answer) chatMessages.value.push({ role: 'assistant', text: finalEvent.answer });
}

function reloadPage() {
  api.setSession(null);
  location.reload();
}
</script>

<template>
  <input
    ref="fileInputRef"
    type="file"
    accept=".txt,text/plain"
    class="sr-only"
    aria-label="requirements.txt 파일 선택"
    @change="onFileSelected"
  >

  <div
    v-show="!fallback && !listView"
    class="drop-zone"
    @dragover.prevent="dragging = true"
    @dragleave.self="dragging = false"
    @drop.prevent="onDropFile"
  >
    <ClinicScene
      v-if="!fallback"
      ref="sceneRef"
      :reduced="reduced"
      @fallback="onFallback"
      @state-change="state = $event"
      @status="status = $event"
      @say="bubbleText = $event"
      @log="logs = $event.logs"
      @open-sheet="activeSheet = $event"
      @close-sheet="activeSheet = null"
      @bubble-pos="bubblePos = $event"
      @egg-count="eggCount = $event"
      @upload-request="triggerUpload"
      @plan-update="currentPlan = $event.plan; currentPackages = $event.packages"
      @chat-turn="onChatTurn"
      @retry-change="retryMessage = $event"
    />

    <div v-if="dragging" class="drop-overlay">
      <p>여기에 requirements.txt를 놓아 주세요</p>
    </div>

    <header class="brand">
      <img src="/brand/logo-mark.svg" width="46" height="46" alt="">
      <div><b>DR<span class="dot">.</span>PATCH</b><small>진료 책상</small></div>
    </header>

    <StatusChip :text="status.text" :stage="status.stage" />

    <div class="ticker" aria-hidden="true">
      <div v-for="(line, i) in tickerLines" :key="i">{{ line }}</div>
    </div>

    <TopTools
      :reduced="reduced"
      :eggs="eggCount"
      @update:reduced="reduced = $event"
      @toggle-list="listView = true"
      @reset="reloadPage"
    />

    <SpeechBubble :text="bubbleText" :reduced="reduced" :pos="bubblePos" />

    <ChatBar
      :messages="chatMessages"
      :busy="isBusy"
      @send="onSendChat"
      @upload="triggerUpload"
    >
      <Controls
        :state="state"
        :can-retry="!!retryMessage"
        @start="sceneRef?.runVisit()"
        @confirm="sceneRef?.confirmPlan()"
        @retry="onRetryChat"
        @calendar="activeSheet = { kind: 'calendar', color: '#3E9E98' }"
        @logs="activeSheet = { kind: 'log', color: '#3E9E98' }"
      />
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

  <PaperSheet :sheet="activeSheet" @close="closeSheet" />
</template>
