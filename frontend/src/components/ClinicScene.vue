<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { createClinicController } from '../scene/clinicController.js';
import { hasWebGL } from '../scene/utils.js';

const props = defineProps({
  reduced: Boolean,
});

const emit = defineEmits([
  'fallback',
  'state-change',
  'status',
  'say',
  'log',
  'open-sheet',
  'close-sheet',
  'bubble-pos',
  'egg-count',
  'upload-request',
  'plan-update',
  'chat-turn',
  'retry-change',
]);

const canvasRef = ref(null);
const loading = ref(true);
const loadPct = ref(0);
const tip = ref({ show: false, text: '', x: 0, y: 0 });
const floatChips = ref([]);
const pillTags = ref([]);

let controller = null;
let disposed = false;

onMounted(async () => {
  if (!hasWebGL()) {
    loading.value = false;
    emit('fallback');
    return;
  }

  try {
    const ctrl = await createClinicController(canvasRef.value, {
      isReduced: () => props.reduced,
      onProgress: (pct) => {
        loadPct.value = pct;
      },
      onLoaded: () => {
        loadPct.value = 100;
        loading.value = false;
      },
      onStateChange: (s) => emit('state-change', s),
      onStatus: (text, stage) => emit('status', { text, stage }),
      onSay: (text) => emit('say', text),
      onLog: (line, logs) => emit('log', { line, logs }),
      onOpenSheet: (sheet) => emit('open-sheet', sheet),
      onCloseSheetRequest: () => emit('close-sheet'),
      onTip: (t) => {
        if (t.show && t.text) tip.value = t;
        else tip.value = { ...tip.value, show: false };
      },
      onFloatChip: (chip) => {
        floatChips.value = [...floatChips.value.slice(-4), chip];
        setTimeout(() => {
          floatChips.value = floatChips.value.filter((c) => c.id !== chip.id);
        }, props.reduced ? 400 : 1500);
      },
      onPillTagsUpdate: (tags) => {
        pillTags.value = tags;
      },
      onBubblePos: (pos) => emit('bubble-pos', pos),
      onEggCount: (found, total) => emit('egg-count', { found, total }),
      onUploadRequest: () => emit('upload-request'),
      onPlanUpdate: (plan, packages) => emit('plan-update', { plan, packages }),
      onChatTurn: (msg, finalEvent) => emit('chat-turn', { msg, finalEvent }),
      onRetryChange: (msg) => emit('retry-change', msg),
    });
    if (disposed) {
      ctrl.destroy();
      return;
    }
    controller = ctrl;
  } catch (err) {
    console.error(err);
    loading.value = false;
    emit('fallback', '진료실을 불러오지 못해 목록으로 보여드려요.');
  }
});

onBeforeUnmount(() => {
  disposed = true;
  controller?.destroy();
});

defineExpose({
  loadPackages: (pkgs) => controller?.loadPackages(pkgs),
  sendChatMessage: (msg) => controller?.sendChatMessage(msg),
  runVisit: () => controller?.runVisit(),
  confirmPlan: () => controller?.confirmPlan(),
  unpopPill: () => controller?.unpopPill(),
  markRoundDone: (roundNo, done) => controller?.markRoundDone(roundNo, done),
});
</script>

<template>
  <canvas ref="canvasRef" id="scene" aria-hidden="true"></canvas>

  <div v-if="loading" class="loading" role="status" aria-live="polite">
    <div>
      <img src="/brand/mascot.svg" width="96" height="96" alt="">
      <p>진료실 준비 중… {{ loadPct }}%</p>
      <div class="load-bar" aria-hidden="true"><i :style="{ width: `${loadPct}%` }"></i></div>
    </div>
  </div>

  <div
    class="tip"
    :class="{ show: tip.show && !!tip.text }"
    :style="{ left: `${tip.x}px`, top: `${tip.y}px` }"
  >
    {{ tip.text }}
  </div>

  <div id="tags" aria-hidden="true">
    <div
      v-for="chip in floatChips"
      :key="chip.id"
      class="chip-float"
      :class="`sev-${chip.sev}`"
      :style="{ left: `${chip.x}px`, top: `${chip.y}px` }"
    >
      <i :style="{ background: chip.color }"></i>{{ chip.name }} · {{ chip.sevLabel }}{{ chip.extra }}
    </div>
    <div
      v-for="tag in pillTags"
      :key="tag.name"
      class="tag"
      :style="{
        transform: `translate(${tag.x}px, ${tag.y}px) translate(-50%, -100%)`,
        opacity: tag.visible ? 1 : 0,
      }"
    >
      <i :style="{ background: tag.color }"></i>{{ tag.name }}
    </div>
  </div>
</template>
