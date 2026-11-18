<script setup>
defineProps({
  state: { type: String, default: 'idle' },
  reduced: Boolean,
});

const emit = defineEmits(['start', 'confirm', 'reset', 'update:reduced']);
</script>

<template>
  <nav class="controls">
    <button class="btn primary" :disabled="state !== 'idle'" @click="emit('start')">진료 시작</button>
    <button class="btn hot" :disabled="state !== 'planned'" @click="emit('confirm')">처방 확정</button>
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
