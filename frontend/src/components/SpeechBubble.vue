<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import RichText from './RichText.vue';

const props = defineProps({
  text: { type: String, default: '' },
  seq: { type: Number, default: 0 },
  reduced: Boolean,
  pos: { type: Object, default: () => ({ right: 0, top: 0 }) },
});

const emit = defineEmits(['closed']);

const shownText = ref('');
const visible = ref(false);
const el = ref(null);
const place = ref({ right: 0, top: 0 });
let typingId = 0;
const timers = [];
const EDGE = 16;
const TOP_SAFE = 76; // 상태 칩·로고 아래
let size = { w: 300, h: 80 };
let ro = null;
let downAt = null;

function clearTimers() {
  while (timers.length) clearTimeout(timers.pop());
}

function closeBubble() {
  if (!visible.value) return;
  clearTimers();
  visible.value = false;
  emit('closed');
}

function onPointerDown(e) {
  downAt = [e.clientX, e.clientY];
}

function onClick(e) {
  if (downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6) return;
  const sel = window.getSelection?.();
  if (sel && String(sel).trim()) return;
  closeBubble();
}

function onGlobalKeyDown(e) {
  if (e.key === 'Escape' && visible.value) {
    closeBubble();
  }
}

// 박사님 머리 옆에 두되, 화면 밖(왼쪽·위)으로 나가지 않게 붙잡는다
function clamp() {
  const { w, h } = size;
  const maxRight = Math.max(EDGE, innerWidth - w - EDGE - 24);
  place.value = {
    right: Math.min(Math.max(EDGE, props.pos.right), maxRight),
    top: Math.max(TOP_SAFE + h, Math.min(props.pos.top, innerHeight - 160)),
  };
}

watch(() => [props.pos.right, props.pos.top], clamp);
onMounted(() => {
  ro = new ResizeObserver(() => {
    if (!el.value) return;
    size = { w: el.value.offsetWidth, h: el.value.offsetHeight };
    clamp();
  });
  if (el.value) ro.observe(el.value);
  addEventListener('keydown', onGlobalKeyDown);
});
onBeforeUnmount(() => {
  clearTimers();
  ro?.disconnect();
  removeEventListener('keydown', onGlobalKeyDown);
});

watch(
  () => [props.text, props.seq],
  async ([next]) => {
    if (!next) return;
    clearTimers();
    const id = ++typingId;
    visible.value = true;
    if (props.reduced) {
      shownText.value = next;
    } else {
      const step = Math.max(4, Math.min(22, 1600 / next.length));
      const chunk = Math.max(1, Math.round(4 / step));
      shownText.value = '';
      for (let i = 0; i < next.length; i += chunk) {
        timers.push(setTimeout(() => { if (id === typingId) shownText.value = next.slice(0, i + chunk); }, (i / chunk) * step));
      }
    }
    await nextTick();
    clamp();
    if (el.value) el.value.scrollTop = 0;
  },
);
</script>

<template>
  <div
    ref="el"
    class="bubble"
    :class="{ show: visible }"
    :style="{ right: `${place.right}px`, top: `${place.top}px` }"
    :tabindex="visible ? 0 : -1"
    :inert="!visible"
    role="button"
    aria-label="박사님 말풍선 — 누르면 닫기"
    title="누르면 닫기 (Esc)"
    @pointerdown="onPointerDown"
    @click="onClick"
    @keydown.enter.prevent="closeBubble"
    @keydown.space.prevent="closeBubble"
  >
    <img class="avatar" src="/brand/mascot.svg" alt="" draggable="false">
    <b>DR.PATCH</b>
    <div class="bubble-body"><RichText :text="shownText" /></div>
  </div>
  <div class="sr-only" aria-live="polite">{{ text ? `닥터 패치: ${text}` : '' }}</div>
</template>
