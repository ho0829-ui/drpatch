<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import RichText from './RichText.vue';

const props = defineProps({
  text: { type: String, default: '' },
  reduced: Boolean,
  pos: { type: Object, default: () => ({ right: 0, top: 0 }) },
});

const shownText = ref('');
const visible = ref(false);
const el = ref(null);
const place = ref({ right: 0, top: 0 });
let typingId = 0;
const timers = [];
const EDGE = 16;
const TOP_SAFE = 76; // 상태 칩·로고 아래
let size = { w: 300, h: 80 }; // 크기가 바뀔 때만 잰다 (위치가 바뀔 때마다 재면 매 프레임 레이아웃 계산)
let ro = null;

function clearTimers() {
  while (timers.length) clearTimeout(timers.pop());
}

// 박사님 머리 옆에 두되, 화면 밖(왼쪽·위)으로 나가지 않게 붙잡는다
function clamp() {
  const { w, h } = size;
  const maxRight = Math.max(EDGE, innerWidth - w - EDGE - 24); // 왼쪽 아바타 여유
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
});
onBeforeUnmount(() => {
  clearTimers();
  ro?.disconnect();
});

watch(
  () => props.text,
  async (next) => {
    if (!next) return;
    clearTimers();
    const id = ++typingId;
    visible.value = true;
    if (props.reduced) {
      shownText.value = next;
    } else {
      // 긴 답도 1.6초 안에 다 나오게 (한 글자 최대 22ms)
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
    aria-hidden="true"
  >
    <img class="avatar" src="/brand/mascot.svg" alt="">
    <b>DR.PATCH</b>
    <div class="bubble-body"><RichText :text="shownText" /></div>
  </div>
  <div class="sr-only" aria-live="polite">{{ text ? `닥터 패치: ${text}` : '' }}</div>
</template>
