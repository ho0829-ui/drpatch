<script setup>
import { computed, ref, watch } from 'vue';
import * as api from './api.js';
import ClinicScene from './components/ClinicScene.vue';
import Controls from './components/Controls.vue';
import FallbackList from './components/FallbackList.vue';
import PaperSheet from './components/PaperSheet.vue';
import SpeechBubble from './components/SpeechBubble.vue';
import StatusChip from './components/StatusChip.vue';

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

async function onFileSelected(e) {
  const file = e.target.files?.[0];
  e.target.value = '';
  if (!file) return;
  try {
    const res = await api.upload(file);
    currentPackages.value = res.packages || [];
    sceneRef.value?.loadPackages(currentPackages.value);
  } catch (err) {
    bubbleText.value = err.message || '파일을 올리지 못했어요.';
  }
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

  <template v-if="!fallback">
    <ClinicScene
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
    />

    <header class="brand">
      <img src="/brand/logo-mark.svg" width="46" height="46" alt="">
      <div><b>DR<span class="dot">.</span>PATCH</b><small>진료 책상</small></div>
    </header>

    <StatusChip :text="status.text" :stage="status.stage" />

    <div class="ticker" aria-hidden="true">
      <div v-for="(line, i) in tickerLines" :key="i">{{ line }}</div>
    </div>

    <div class="note">
      드래그 회전 · 오른쪽 드래그 이동 · 휠 줌 · 더블클릭 처음으로 ·
      <span>숨은 것 {{ eggCount.found }}/{{ eggCount.total }}</span>
    </div>

    <SpeechBubble :text="bubbleText" :reduced="reduced" :pos="bubblePos" />

    <PaperSheet :sheet="activeSheet" @close="closeSheet" />

    <Controls
      :state="state"
      :reduced="reduced"
      @update:reduced="reduced = $event"
      @upload="triggerUpload"
      @start="sceneRef?.runVisit()"
      @confirm="sceneRef?.confirmPlan()"
      @reset="reloadPage"
    />
  </template>

  <FallbackList v-else :message="fallbackMsg" :plan="currentPlan" :packages="currentPackages" />
</template>
