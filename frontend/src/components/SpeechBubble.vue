<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  text: { type: String, default: '' },
  reduced: Boolean,
  pos: { type: Object, default: () => ({ right: 0, top: 0 }) },
});

const shownText = ref('');
const visible = ref(false);
let typingId = 0;
const timers = [];

function clearTimers() {
  while (timers.length) clearTimeout(timers.pop());
}

watch(
  () => props.text,
  (next) => {
    if (!next) return;
    clearTimers();
    const id = ++typingId;
    visible.value = true;
    if (props.reduced) {
      shownText.value = next;
      return;
    }
    shownText.value = '';
    [...next].forEach((ch, i) => {
      timers.push(
        setTimeout(() => {
          if (id === typingId) shownText.value += ch;
        }, i * 22),
      );
    });
  },
);
</script>

<template>
  <div
    class="bubble"
    :class="{ show: visible }"
    :style="{ right: `${pos.right}px`, top: `${pos.top}px` }"
    aria-hidden="true"
  >
    <img class="avatar" src="/brand/mascot.svg" alt="">
    <b>DR.PATCH</b>
    <span>{{ shownText }}</span>
  </div>
  <div class="sr-only" aria-live="polite">{{ text ? `닥터 패치: ${text}` : '' }}</div>
</template>
