<script setup>
defineProps({
  state: { type: String, default: 'idle' },
  reduced: Boolean,
});

const emit = defineEmits(['upload', 'start', 'confirm', 'calendar', 'reset', 'update:reduced']);
</script>

<template>
  <nav class="controls">
    <button
      class="btn"
      :disabled="state === 'running' || state === 'confirming'"
      @click="emit('upload')"
    >
      파일 올리기
    </button>
    <button class="btn primary" :disabled="state !== 'ready'" @click="emit('start')">진료 시작</button>
    <button class="btn hot" :disabled="state !== 'planned'" @click="emit('confirm')">처방 확정</button>
    <button class="btn" @click="emit('calendar')">진료 예약</button>
    <button class="btn" @click="emit('reset')">처음부터</button>
    <label class="motion">
      <input
        type="checkbox"
        :checked="reduced"
        @change="emit('update:reduced', $event.target.checked)"
      >
      움직임 줄이기
    </label>
  </nav>
</template>
