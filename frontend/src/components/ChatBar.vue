<script setup>
import { nextTick, ref, watch } from 'vue';

const props = defineProps({
  messages: { type: Array, default: () => [] },
  busy: Boolean,
});

const emit = defineEmits(['send', 'upload']);

const text = ref('');
const historyOpen = ref(false);
const historyRef = ref(null);

function submit() {
  const msg = text.value.trim();
  if (!msg || props.busy) return;
  text.value = '';
  emit('send', msg);
}

function onKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    submit();
  }
}

watch(
  () => props.messages.length,
  async () => {
    if (historyOpen.value) {
      await nextTick();
      if (historyRef.value) historyRef.value.scrollTop = historyRef.value.scrollHeight;
    }
  },
);
</script>

<template>
  <div class="chat-dock">
    <div v-if="historyOpen" ref="historyRef" class="chat-history" aria-label="대화 기록">
      <div v-if="!messages.length" class="chat-empty">아직 대화 기록이 없어요.</div>
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="chat-msg"
        :class="m.role"
      >
        <b>{{ m.role === 'user' ? '나' : 'DR.PATCH' }}</b>
        <p>{{ m.text }}</p>
      </div>
    </div>

    <div class="chat-input-row">
      <button
        type="button"
        class="btn btn-sm"
        :aria-expanded="historyOpen"
        @click="historyOpen = !historyOpen"
      >
        {{ historyOpen ? '대화 닫기' : `대화 (${messages.length})` }}
      </button>
      <button
        type="button"
        class="btn btn-sm"
        :disabled="busy"
        @click="emit('upload')"
      >
        파일 올리기
      </button>
      <textarea
        v-model="text"
        class="chat-textarea"
        rows="1"
        placeholder="OS·Python 버전, 회차 조건을 입력해 주세요 (Enter 보내기 / Shift+Enter 줄바꿈)"
        aria-label="박사님에게 보낼 메시지"
        :disabled="busy"
        @keydown="onKeyDown"
      ></textarea>
      <button
        type="button"
        class="btn primary btn-sm"
        :disabled="busy || !text.trim()"
        @click="submit"
      >
        보내기
      </button>
    </div>
  </div>
</template>
