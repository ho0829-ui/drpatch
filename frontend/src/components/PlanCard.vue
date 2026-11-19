<script setup>
import { computed, ref } from 'vue';
import { SEV, sevKey } from '../demo.js';

const props = defineProps({
  plan: { type: Object, required: true },
  highlighted: Boolean,
  tag: { type: Object, default: null }, // { letter, color, label } — 점검(세션)마다 색
});

const emit = defineEmits(['toggle-done', 'toggle-item', 'save-edit', 'delete', 'inspect-item']);

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];
const editing = ref(false);
const editDate = ref('');
const editStart = ref('');
const editEnd = ref('');
const expanded = ref(false);

const todayIso = computed(() => {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
});

const isDone = computed(() => props.plan.status === 'done');

const dateLabel = computed(() => {
  const m = String(props.plan.date || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return props.plan.date || '';
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return `${Number(m[2])}/${Number(m[3])}(${WEEKDAYS[d.getDay()]})`;
});

const winLabel = computed(() => {
  const s = props.plan.window_start;
  const e = props.plan.window_end;
  if (!s || !e) return '';
  if (s.endsWith(':00') && e.endsWith(':00')) return `${Number(s.slice(0, 2))}–${Number(e.slice(0, 2))}시`;
  return `${s}–${e}`;
});

const dDay = computed(() => {
  if (!props.plan.date) return '';
  const t0 = new Date(`${todayIso.value}T00:00:00`).getTime();
  const t1 = new Date(`${props.plan.date}T00:00:00`).getTime();
  const diff = Math.round((t1 - t0) / 86400000);
  if (diff === 0) return 'D-Day';
  return diff > 0 ? `D-${diff}` : `D+${Math.abs(diff)}`;
});

const doneDateShort = computed(() => {
  const m = String(props.plan.done_at || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${Number(m[2])}/${Number(m[3])}` : '';
});

const isEarlyDone = computed(() => {
  if (!isDone.value || !props.plan.done_at || !props.plan.date) return false;
  return String(props.plan.done_at).slice(0, 10) < props.plan.date;
});

const statusBadge = computed(() => {
  if (isDone.value) {
    return isEarlyDone.value
      ? { text: `미리 끝냄 (${doneDateShort.value})`, cls: 'st-done' }
      : { text: doneDateShort.value ? `끝남 (${doneDateShort.value})` : '끝남', cls: 'st-done' };
  }
  if (props.plan.date === todayIso.value) return { text: '오늘', cls: 'st-today' };
  if (props.plan.date < todayIso.value) return { text: '지남', cls: 'st-past' };
  return { text: '예정', cls: 'st-planned' };
});

const items = computed(() => props.plan.items || []);
const visibleItems = computed(() => (expanded.value ? items.value : items.value.slice(0, 5)));
const extraCount = computed(() => Math.max(0, items.value.length - 5));

function startEdit() {
  editDate.value = props.plan.date;
  editStart.value = props.plan.window_start || '';
  editEnd.value = props.plan.window_end || '';
  editing.value = true;
}

function submitEdit() {
  emit('save-edit', {
    id: props.plan.id,
    date: editDate.value || undefined,
    window_start: editStart.value || null,
    window_end: editEnd.value || null,
  });
  editing.value = false;
}

function confirmDelete() {
  if (!confirm(`${props.plan.round_no}회차 (${props.plan.date}) 계획을 지울까요?`)) return;
  emit('delete', props.plan.id);
}

const sevColor = (sev) => SEV[sevKey(sev)][0];
</script>

<template>
  <article
    :id="`plan-card-${plan.id}`"
    class="plan-card"
    :class="{ done: isDone, highlighted }"
    :style="tag ? { '--tag': tag.color } : undefined"
  >
    <p v-if="tag" class="plan-tag"><i aria-hidden="true"></i>{{ tag.label }}</p>
    <header class="plan-card-head">
      <div class="plan-card-title">
        <b>{{ dateLabel }}</b>
        <span v-if="winLabel" class="plan-win">{{ winLabel }}</span>
        <span class="plan-round">{{ plan.round_no }}회차</span>
        <span v-if="!isDone && dDay" class="plan-dday">{{ dDay }}</span>
      </div>
      <span class="st-badge" :class="statusBadge.cls">{{ statusBadge.text }}</span>
    </header>

    <div v-if="editing" class="cal-edit-row">
      <input v-model="editDate" type="date" aria-label="계획 날짜">
      <input v-model="editStart" type="time" aria-label="시작 시각">
      <input v-model="editEnd" type="time" aria-label="종료 시각">
      <button type="button" class="cal-btn primary nowrap" @click="submitEdit">저장</button>
      <button type="button" class="cal-btn nowrap" @click="editing = false">취소</button>
    </div>

    <template v-else>
      <ul v-if="items.length" class="plan-items">
        <li v-for="(it, idx) in visibleItems" :key="`${it.name}-${idx}`" :class="{ checked: !!it.done_at }">
          <label class="plan-chk">
            <input
              type="checkbox"
              :checked="!!it.done_at"
              :aria-label="`${it.name} 끝냄 표시`"
              @change="emit('toggle-item', { plan, index: idx, checked: $event.target.checked })"
            >
          </label>
          <button type="button" class="plan-item-btn" @click="emit('inspect-item', { item: it, plan })">
            <i class="sev-dot" :style="{ background: sevColor(it.severity) }" aria-hidden="true"></i>
            <span class="plan-item-name">{{ it.name }}</span>
            <span class="plan-item-ver">
              {{ it.current_version || '미상' }}
              <template v-if="it.target_version"> → {{ it.target_version }}</template>
            </span>
          </button>
        </li>
      </ul>
      <button
        v-if="extraCount > 0 && !expanded"
        type="button"
        class="plan-more"
        @click="expanded = true"
      >
        외 {{ extraCount }}개 더 보기
      </button>

      <p v-if="plan.overlaps?.length" class="cal-warn">
        ⚠ 같은 날 시간이 겹치는 일정 {{ plan.overlaps.length }}건이 있어요.
      </p>

      <footer class="plan-card-actions">
        <div class="plan-actions-wide">
          <button type="button" class="cal-btn nowrap" :class="{ primary: !isDone }" @click="emit('toggle-done', plan)">
            {{ isDone ? '되돌리기' : '끝냄' }}
          </button>
          <button type="button" class="cal-btn nowrap" @click="startEdit">수정</button>
          <button type="button" class="cal-btn danger nowrap" @click="confirmDelete">삭제</button>
        </div>

        <details class="plan-actions-narrow">
          <summary class="cal-btn nowrap" aria-label="계획 메뉴">⋯</summary>
          <div class="plan-menu-pop">
            <button type="button" class="cal-btn nowrap" @click="emit('toggle-done', plan)">
              {{ isDone ? '되돌리기' : '끝냄' }}
            </button>
            <button type="button" class="cal-btn nowrap" @click="startEdit">수정</button>
            <button type="button" class="cal-btn danger nowrap" @click="confirmDelete">삭제</button>
          </div>
        </details>
      </footer>
    </template>
  </article>
</template>
