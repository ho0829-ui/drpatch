<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import * as api from '../api.js';
import PlanCard from './PlanCard.vue';

const emit = defineEmits(['inspect-item', 'plan-done-change']);

const today = new Date();
const viewYear = ref(today.getFullYear());
const viewMonth = ref(today.getMonth());
const pad = (n) => String(n).padStart(2, '0');
const todayIso = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
const selectedDate = ref(todayIso);

const events = ref([]);
const plans = ref([]);
const showAllSessions = ref(!api.getSession());
const eventFormOpen = ref(false);
const errorMsg = ref('');
const loading = ref(false);

const newTitle = ref('');
const newDate = ref(selectedDate.value);
const newStart = ref('');
const newEnd = ref('');

const ROUND_CIRCLES = ['①', '②', '③', '④', '⑤'];
const monthLabel = computed(() => `${viewYear.value}년 ${viewMonth.value + 1}월`);

const monthRange = computed(() => {
  const y = viewYear.value;
  const m = viewMonth.value;
  const from = new Date(y, m, 1);
  const to = new Date(y, m + 1, 0);
  return {
    from: `${y}-${pad(m + 1)}-01`,
    to: `${y}-${pad(m + 1)}-${pad(to.getDate())}`,
    firstDow: from.getDay(),
    daysInMonth: to.getDate(),
  };
});

const upcomingPlans = computed(() => plans.value.filter((p) => p.status !== 'done'));
const donePlans = computed(() => plans.value.filter((p) => p.status === 'done'));

const calendarCells = computed(() => {
  const { firstDow, daysInMonth } = monthRange.value;
  const y = viewYear.value;
  const m = pad(viewMonth.value + 1);
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${y}-${m}-${pad(d)}`;
    const dayPlans = plans.value.filter((p) => p.date === iso);
    const dayEvents = events.value.filter((e) => e.date === iso);
    const parts = [`${viewMonth.value + 1}월 ${d}일`];
    if (dayPlans.length) parts.push(`패치 계획 ${dayPlans.length}개`);
    if (dayEvents.length) parts.push(`내 일정 ${dayEvents.length}개`);
    cells.push({
      day: d,
      iso,
      plans: dayPlans,
      hasEvent: dayEvents.length > 0,
      isPast: iso < todayIso,
      ariaLabel: parts.join(', '),
    });
  }
  return cells;
});

async function loadAll() {
  loading.value = true;
  errorMsg.value = '';
  try {
    const { from, to } = monthRange.value;
    const sid = showAllSessions.value ? null : api.getSession();
    const [evRes, plRes] = await Promise.all([
      api.calendar.list(from, to).catch(() => []),
      api.plans.list(sid).catch((err) => {
        errorMsg.value = err.message;
        return [];
      }),
    ]);
    events.value = evRes || [];
    plans.value = plRes || [];
  } finally {
    loading.value = false;
  }
}

function shiftMonth(delta) {
  const d = new Date(viewYear.value, viewMonth.value + delta, 1);
  viewYear.value = d.getFullYear();
  viewMonth.value = d.getMonth();
}

async function selectDay(iso) {
  selectedDate.value = iso;
  newDate.value = iso;
  const target = plans.value.find((p) => p.date === iso);
  if (target) {
    await nextTick();
    document.getElementById(`plan-card-${target.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

async function toggleDone(plan) {
  errorMsg.value = '';
  const nextStatus = plan.status === 'done' ? 'planned' : 'done';
  try {
    const updated = await api.plans.update(plan.id, { status: nextStatus });
    emit('plan-done-change', { roundNo: updated.round_no, done: updated.status === 'done' });
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

async function toggleItem({ plan, index, checked }) {
  errorMsg.value = '';
  const nowIso = new Date().toISOString().slice(0, 19) + 'Z';
  const nextItems = (plan.items || []).map((it, i) =>
    i === index ? { ...it, done_at: checked ? nowIso : null } : it,
  );
  try {
    const updated = await api.plans.update(plan.id, { items: nextItems });
    emit('plan-done-change', { roundNo: updated.round_no, done: updated.status === 'done' });
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

async function saveEdit({ id, date, window_start, window_end }) {
  errorMsg.value = '';
  try {
    await api.plans.update(id, { date, window_start, window_end });
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

async function deletePlan(id) {
  errorMsg.value = '';
  try {
    await api.plans.remove(id);
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

async function addEvent() {
  if (!newTitle.value.trim() || !newDate.value) return;
  errorMsg.value = '';
  try {
    await api.calendar.add({
      title: newTitle.value.trim(),
      date: newDate.value,
      start: newStart.value || null,
      end: newEnd.value || null,
    });
    newTitle.value = '';
    newStart.value = '';
    newEnd.value = '';
    eventFormOpen.value = false;
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

async function removeEvent(id) {
  errorMsg.value = '';
  try {
    await api.calendar.remove(id);
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

watch([viewYear, viewMonth, showAllSessions], loadAll);
onMounted(loadAll);
</script>

<template>
  <div class="cal-sheet">
    <p class="eyebrow">진료 예약 · 점검 일정</p>
    <div class="cal-head-row">
      <h2 id="sheet-title">다가오는 점검</h2>
      <label class="cal-scope-toggle">
        <input v-model="showAllSessions" type="checkbox">
        모든 계획 보기
      </label>
    </div>

    <div v-if="errorMsg" class="cal-err">
      <span>{{ errorMsg }}</span>
      <button type="button" class="cal-btn nowrap" @click="loadAll">다시 불러오기</button>
    </div>

    <div class="cal-section">
      <p v-if="!upcomingPlans.length && !loading" class="cal-muted">예정된 점검이 없어요.</p>
      <div class="plan-cards">
        <PlanCard
          v-for="p in upcomingPlans"
          :key="p.id"
          :plan="p"
          :highlighted="p.date === selectedDate"
          @toggle-done="toggleDone"
          @toggle-item="toggleItem"
          @save-edit="saveEdit"
          @delete="deletePlan"
          @inspect-item="emit('inspect-item', $event)"
        />
      </div>

      <details v-if="donePlans.length" class="done-group">
        <summary>끝난 점검 ({{ donePlans.length }})</summary>
        <div class="plan-cards">
          <PlanCard
            v-for="p in donePlans"
            :key="p.id"
            :plan="p"
            :highlighted="p.date === selectedDate"
            @toggle-done="toggleDone"
            @toggle-item="toggleItem"
            @save-edit="saveEdit"
            @delete="deletePlan"
            @inspect-item="emit('inspect-item', $event)"
          />
        </div>
      </details>
    </div>

    <div class="cal-section">
      <div class="cal-nav">
        <button type="button" class="cal-btn" aria-label="이전 달" @click="shiftMonth(-1)">◀</button>
        <b>{{ monthLabel }}</b>
        <button type="button" class="cal-btn" aria-label="다음 달" @click="shiftMonth(1)">▶</button>
      </div>

      <div class="cal-legend" aria-hidden="true">
        <span><b class="round-pill">①</b> 패치 회차</span>
        <span><i class="dot-event"></i> 내 일정</span>
      </div>

      <div class="cal-grid">
        <span v-for="d in ['일', '월', '화', '수', '목', '금', '토']" :key="d" class="cal-dow">{{ d }}</span>
        <template v-for="(cell, idx) in calendarCells" :key="idx">
          <span v-if="!cell" class="cal-blank"></span>
          <button
            v-else
            type="button"
            class="cal-day"
            :class="{ selected: cell.iso === selectedDate, muted: cell.isPast }"
            :aria-label="cell.ariaLabel"
            :aria-pressed="cell.iso === selectedDate"
            @click="selectDay(cell.iso)"
          >
            <span>{{ cell.day }}</span>
            <span class="cal-badges" aria-hidden="true">
              <span
                v-for="p in cell.plans.slice(0, 2)"
                :key="p.id"
                class="round-pill"
                :class="{ done: p.status === 'done' }"
              >{{ ROUND_CIRCLES[(p.round_no || 1) - 1] || p.round_no }}</span>
              <i v-if="cell.hasEvent" class="dot-event"></i>
            </span>
          </button>
        </template>
      </div>
    </div>

    <div class="cal-section">
      <div class="cal-head-row">
        <h3>내 일정 ({{ events.length }})</h3>
        <button type="button" class="cal-btn nowrap" @click="eventFormOpen = !eventFormOpen">
          {{ eventFormOpen ? '접기' : '일정 추가' }}
        </button>
      </div>
      <form v-if="eventFormOpen" class="cal-form" @submit.prevent="addEvent">
        <input v-model="newTitle" type="text" placeholder="일정 제목" required aria-label="일정 제목">
        <input v-model="newDate" type="date" required aria-label="일정 날짜">
        <input v-model="newStart" type="time" aria-label="시작 시각">
        <input v-model="newEnd" type="time" aria-label="종료 시각">
        <button type="submit" class="cal-btn primary nowrap">저장</button>
      </form>
      <ul v-if="events.length" class="cal-list">
        <li v-for="ev in events" :key="ev.id" class="cal-item-row">
          <span>{{ ev.date }} <template v-if="ev.start">{{ ev.start }}–{{ ev.end }} </template>· {{ ev.title }}</span>
          <button type="button" class="cal-btn danger nowrap" @click="removeEvent(ev.id)">삭제</button>
        </li>
      </ul>
    </div>
  </div>
</template>
