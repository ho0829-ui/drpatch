<script setup>
import { asset } from '../paths.js';
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import RichText from './RichText.vue';

const props = defineProps({
  text: { type: String, default: '' },
  seq: { type: Number, default: 0 },
  reduced: Boolean,
  pos: { type: Object, default: () => ({ right: 0, top: 0 }) },
  action: { type: Object, default: null },
});

const emit = defineEmits(['closed', 'action']);

const shownText = ref('');
const visible = ref(false);
const el = ref(null);
const place = ref({ right: 0, top: 0, maxH: null });
let typingId = 0;
const timers = [];
const EDGE = 16;
const TOP_SAFE = 96; // 상태 칩·로고 아래. 아바타가 말풍선 위로 20px 나오므로 그만큼 더 내려야 로고와 안 겹친다
let size = { w: 300, h: 80 }; // 크기가 바뀔 때만 잰다 (위치가 바뀔 때마다 재면 매 프레임 레이아웃 계산)
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

// 끌어서 스크롤하거나 글자를 고른 클릭은 닫지 않는다 (spec v1.17: 움직임 없는 클릭만)
function onClick(e) {
  if (e.target?.closest?.('.bubble-link')) return;
  if (downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6) return;
  const sel = window.getSelection?.();
  if (sel && String(sel).trim()) return;
  closeBubble();
}

function onClickAction() {
  if (props.action) emit('action', props.action);
}

function onGlobalKeyDown(e) {
  if (e.key === 'Escape' && visible.value) {
    closeBubble();
  }
}

// 박사님 머리 옆에 두되, 화면 밖(왼쪽·위)과 블리스터 판 위로 내려오지 않게 붙잡는다 (spec v1.20 I)
function clamp() {
  const { w, h } = size;
  const maxRight = Math.max(EDGE, innerWidth - w - EDGE - 24); // 왼쪽 아바타 여유
  const mobile = innerWidth < 768;
  const bTop = typeof props.pos.blisterTop === 'number' ? props.pos.blisterTop : null;

  if (mobile) {
    const mobileTop = 112;
    const baseMaxH = Math.round(innerHeight * 0.22);
    const maxH = bTop !== null ? Math.max(68, Math.min(baseMaxH, Math.floor(bTop - mobileTop - 10))) : baseMaxH;
    place.value = {
      right: Math.min(Math.max(EDGE, props.pos.right), maxRight),
      top: mobileTop,
      maxH,
    };
    return;
  }

  const baseMaxH = Math.round(innerHeight * 0.30);
  const maxBottom = bTop !== null ? Math.min(innerHeight - 160, Math.floor(bTop - 12)) : innerHeight - 160;
  let top = Math.min(props.pos.top, maxBottom);
  let maxH = baseMaxH;
  if (top - h < TOP_SAFE) {
    if (maxBottom - TOP_SAFE < h) {
      top = Math.max(TOP_SAFE + 68, maxBottom);
      maxH = Math.max(68, Math.min(baseMaxH, top - TOP_SAFE));
    } else {
      top = TOP_SAFE + h;
    }
  }
  place.value = {
    right: Math.min(Math.max(EDGE, props.pos.right), maxRight),
    top,
    maxH,
  };
}

watch(() => [props.pos.right, props.pos.top, props.pos.blisterTop], clamp);
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
    :style="{ right: `${place.right}px`, top: `${place.top}px`, maxHeight: place.maxH ? `${place.maxH}px` : undefined }"
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
    <img class="avatar" :src="asset('brand/mascot.svg')" alt="" draggable="false">
    <b>DR.PATCH</b>
    <div class="bubble-body"><RichText :text="shownText" /></div>
    <p v-if="action" class="bubble-action">
      {{ action.prefix || '' }}<button
        type="button"
        class="bubble-link"
        @click.stop="onClickAction"
        @keydown.enter.stop.prevent="onClickAction"
        @keydown.space.stop.prevent="onClickAction"
      >{{ action.label }}</button>{{ action.suffix || '' }}
    </p>
  </div>
  <div class="sr-only" aria-live="polite">{{ text ? `닥터 패치: ${text}` : '' }}</div>
</template>
