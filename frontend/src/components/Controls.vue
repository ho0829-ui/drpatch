<script setup>
// 진료 도크 윗줄: 주요 동작만. (파일 올리기는 입력줄의 첨부 버튼 하나, 보조 동작은 TopTools)
defineProps({
  state: { type: String, default: 'idle' },
  canRetry: Boolean,
});
const emit = defineEmits(['start', 'confirm', 'retry', 'calendar', 'logs']);
</script>

<template>
  <nav class="dock-actions" aria-label="진료 제어">
    <button class="btn btn-sm primary" :disabled="state !== 'ready'" @click="emit('start')">진료 시작</button>
    <button class="btn btn-sm hot" :disabled="state !== 'planned'" @click="emit('confirm')">처방 확정</button>
    <button v-if="canRetry" class="btn btn-sm hot" :disabled="state === 'running' || state === 'confirming'" @click="emit('retry')">다시 시도</button>
    <span class="dock-sep" aria-hidden="true"></span>
    <button class="btn btn-sm ghost" @click="emit('calendar')">진료 예약</button>
    <button class="btn btn-sm ghost" @click="emit('logs')">진료 기록</button>
  </nav>
</template>
