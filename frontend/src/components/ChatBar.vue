<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import RichText from './RichText.vue';

const props = defineProps({
  messages: { type: Array, default: () => [] },
  busy: Boolean,
});

const emit = defineEmits(['send', 'upload']);

const text = ref('');
const historyOpen = ref(false);
const historyRef = ref(null);
const kbOffset = ref(0);

function updateViewport() {
  const vv = window.visualViewport;
  if (!vv) return;
  const gap = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
  kbOffset.value = gap > 40 ? Math.round(gap) : 0;
}

onMounted(() => {
  const vv = window.visualViewport;
  if (vv) {
    vv.addEventListener('resize', updateViewport);
    vv.addEventListener('scroll', updateViewport);
  }
});

onBeforeUnmount(() => {
  const vv = window.visualViewport;
  if (vv) {
    vv.removeEventListener('resize', updateViewport);
    vv.removeEventListener('scroll', updateViewport);
  }
});

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
  <div class="chat-dock" :style="kbOffset ? { bottom: `${kbOffset + 10}px` } : undefined">
    <slot />
    <div v-if="historyOpen" ref="historyRef" class="chat-history" aria-label="대화 기록">
      <div v-if="!messages.length" class="chat-empty">아직 대화 기록이 없어요.</div>
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="chat-msg"
        :class="m.role"
      >
        <b>{{ m.role === 'user' ? '나' : 'DR.PATCH' }}</b>
        <p><RichText :text="m.text" /></p>
      </div>
    </div>

    <div class="chat-input-row">
      <button
        type="button"
        class="btn btn-sm ghost"
        :aria-expanded="historyOpen"
        @click="historyOpen = !historyOpen"
      >
        <template v-if="historyOpen">닫기</template>
        <template v-else><span class="hist-label">대화 </span>{{ messages.length }}</template>
      </button>
      <button
        type="button"
        class="icon-btn"
        :disabled="busy"
        aria-label="requirements.txt 파일 올리기"
        title="requirements.txt 올리기"
        @click="emit('upload')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 11.5l-8.6 8.6a5.5 5.5 0 0 1-7.8-7.8l8.6-8.6a3.7 3.7 0 0 1 5.2 5.2l-8.6 8.6a1.8 1.8 0 0 1-2.6-2.6l7.9-7.9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <textarea
        v-model="text"
        class="chat-textarea"
        rows="1"
        placeholder="OS·Python 버전, 점검 일정"
        title="Enter 보내기 · Shift+Enter 줄바꿈"
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
