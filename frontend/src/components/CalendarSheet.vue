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
const plansError = ref('');
const eventsError = ref('');
const actionError = ref('');
const plansLoading = ref(false);
const eventsLoading = ref(false);

let plansReqId = 0;
let eventsReqId = 0;

const newTitle = ref('');
const newDate = ref(selectedDate.value);
const newStart = ref('');
const newEnd = ref('');

const monthLabel = computed(() => `${viewYear.value}년 ${viewMonth.value + 1}월`);

// 점검(= 세션, 파일을 올린 한 번)마다 색 하나. 위험도 색(빨강·주황·노랑·초록)과 헷갈리지 않는 색만 쓴다.
const SESSION_COLORS = ['#2F80A8', '#7A5CC2', '#00897B', '#5C6BC0', '#8D6E63', '#AD5A9E'];
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

const sessionTags = computed(() => {
  const first = new Map(); // session_id → 가장 먼저 만든 계획 시각
  for (const p of plans.value) {
    const t = p.created_at || p.date || '';
    if (!first.has(p.session_id) || t < first.get(p.session_id)) first.set(p.session_id, t);
  }
  const current = api.getSession();
  const ordered = [...first.entries()].sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  const tags = new Map();
  ordered.forEach(([sid], i) => {
    const letter = LETTERS[i % LETTERS.length];
    tags.set(sid, {
      letter,
      color: SESSION_COLORS[i % SESSION_COLORS.length],
      label: sid === current ? `점검 ${letter} · 지금 차트` : `점검 ${letter}`,
    });
  });
  return tags;
});

const tagOf = (p) => sessionTags.value.get(p.session_id) || { letter: '?', color: SESSION_COLORS[0], label: '점검' };

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

// 달력은 늘 6주(42칸)로 그린다 — 달마다 줄 수가 달라 종이 높이가 바뀌지 않게. 앞뒤 달 날짜는 흐리게만.
const calendarCells = computed(() => {
  const { firstDow } = monthRange.value;
  const start = new Date(viewYear.value, viewMonth.value, 1 - firstDow);
  const cells = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    const iso = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    const inMonth = d.getMonth() === viewMonth.value;
    if (!inMonth) {
      cells.push({ day: d.getDate(), iso, outside: true });
      continue;
    }
    const dayPlans = plans.value.filter((p) => p.date === iso);
    const dayEvents = events.value.filter((e) => e.date === iso);
    const parts = [`${d.getMonth() + 1}월 ${d.getDate()}일`];
    for (const p of dayPlans) parts.push(`${tagOf(p).label} ${p.round_no}회차${p.status === 'done' ? ' 끝남' : ''}`);
    if (dayEvents.length) parts.push(`내 일정 ${dayEvents.length}개`);
    cells.push({
      day: d.getDate(),
      iso,
      outside: false,
      plans: dayPlans,
      hasEvent: dayEvents.length > 0,
      isPast: iso < todayIso,
      isToday: iso === todayIso,
      ariaLabel: parts.join(', '),
    });
  }
  return cells;
});

// 범례: 지금 보이는 계획에 나온 점검만
const legendTags = computed(() => {
  const seen = new Map();
  for (const p of plans.value) {
    const t = tagOf(p);
    if (!seen.has(t.letter)) seen.set(t.letter, t);
  }
  return [...seen.values()].sort((a, b) => a.letter.localeCompare(b.letter));
});

async function loadPlans() {
  const reqId = ++plansReqId;
  plansLoading.value = true;
  plansError.value = '';
  try {
    const sid = showAllSessions.value ? null : api.getSession();
    const plRes = await api.plans.list(sid);
    if (reqId !== plansReqId) return;
    plans.value = plRes || [];
  } catch {
    if (reqId !== plansReqId) return;
    plansError.value = '허허, 점검 목록을 불러오지 못했네요.';
  } finally {
    if (reqId === plansReqId) plansLoading.value = false;
  }
}

async function loadEvents() {
  const reqId = ++eventsReqId;
  eventsLoading.value = true;
  eventsError.value = '';
  try {
    const { from, to } = monthRange.value;
    const evRes = await api.calendar.list(from, to);
    if (reqId !== eventsReqId) return;
    events.value = evRes || [];
  } catch {
    if (reqId !== eventsReqId) return;
    eventsError.value = '허허, 달력을 불러오지 못했네요.';
  } finally {
    if (reqId === eventsReqId) eventsLoading.value = false;
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
  actionError.value = '';
  const nextStatus = plan.status === 'done' ? 'planned' : 'done';
  try {
    const updated = await api.plans.update(plan.id, { status: nextStatus });
    emit('plan-done-change', { roundNo: updated.round_no, done: updated.status === 'done' });
    await loadPlans();
  } catch (err) {
    actionError.value = err.message || '허허, 상태를 바꾸지 못했네요.';
  }
}

async function toggleItem({ plan, index, checked }) {
  actionError.value = '';
  const nowIso = new Date().toISOString().slice(0, 19) + 'Z';
  const nextItems = (plan.items || []).map((it, i) =>
    i === index ? { ...it, done_at: checked ? nowIso : null } : it,
  );
  try {
    const updated = await api.plans.update(plan.id, { items: nextItems });
    emit('plan-done-change', { roundNo: updated.round_no, done: updated.status === 'done' });
    await loadPlans();
  } catch (err) {
    actionError.value = err.message || '허허, 항목을 바꾸지 못했네요.';
  }
}

async function saveEdit({ id, date, window_start, window_end }) {
  actionError.value = '';
  try {
    await api.plans.update(id, { date, window_start, window_end });
    await loadPlans();
  } catch (err) {
    actionError.value = err.message || '허허, 계획을 고치지 못했네요.';
  }
}

async function deletePlan(id) {
  actionError.value = '';
  try {
    await api.plans.remove(id);
    await loadPlans();
  } catch (err) {
    actionError.value = err.message || '허허, 계획을 지우지 못했네요.';
  }
}

async function addEvent() {
  if (!newTitle.value.trim() || !newDate.value) return;
  actionError.value = '';
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
    await loadEvents();
  } catch (err) {
    actionError.value = err.message || '허허, 일정을 넣지 못했네요.';
  }
}

async function removeEvent(id) {
  actionError.value = '';
  try {
    await api.calendar.remove(id);
    await loadEvents();
  } catch (err) {
    actionError.value = err.message || '허허, 일정을 지우지 못했네요.';
  }
}

watch([viewYear, viewMonth], loadEvents);
watch(showAllSessions, loadPlans);
onMounted(() => {
  loadPlans();
  loadEvents();
});
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

    <div v-if="actionError" class="cal-err" role="alert">
      <span class="cal-err-text">{{ actionError }}</span>
      <button type="button" class="cal-btn nowrap" @click="actionError = ''">닫기</button>
    </div>

    <div v-if="plansError" class="cal-err" role="alert">
      <span class="cal-err-text">{{ plansError }}</span>
      <button type="button" class="cal-btn nowrap" @click="loadPlans">다시 불러오기</button>
    </div>

    <div class="cal-section">
      <p v-if="!upcomingPlans.length && !plansLoading && !plansError" class="cal-muted">예정된 점검이 없어요.</p>
      <div class="plan-cards">
        <PlanCard
          v-for="p in upcomingPlans"
          :key="p.id"
          :plan="p"
          :tag="tagOf(p)"
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
            :tag="tagOf(p)"
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
        <span v-for="t in legendTags" :key="t.letter"><i class="legend-swatch" :style="{ background: t.color }"></i>{{ t.label }}</span>
        <span><i class="dot-event"></i>내 일정</span>
      </div>

      <div class="cal-grid">
        <span v-for="d in ['일', '월', '화', '수', '목', '금', '토']" :key="d" class="cal-dow">{{ d }}</span>
        <template v-for="cell in calendarCells" :key="cell.iso">
          <span v-if="cell.outside" class="cal-day outside" aria-hidden="true">{{ cell.day }}</span>
          <button
            v-else
            type="button"
            class="cal-day"
            :class="{ selected: cell.iso === selectedDate, muted: cell.isPast, today: cell.isToday }"
            :aria-label="cell.ariaLabel"
            :aria-pressed="cell.iso === selectedDate"
            @click="selectDay(cell.iso)"
          >
            <span class="cal-num">{{ cell.day }}</span>
            <span class="cal-badges" aria-hidden="true">
              <span
                v-for="p in cell.plans.slice(0, 2)"
                :key="p.id"
                class="round-pill"
                :class="{ done: p.status === 'done' }"
                :style="{ '--tag': tagOf(p).color }"
              >{{ p.round_no }}</span>
              <span v-if="cell.plans.length > 2" class="round-more">+{{ cell.plans.length - 2 }}</span>
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
      <div v-if="eventsError" class="cal-err" role="alert">
        <span class="cal-err-text">{{ eventsError }}</span>
        <button type="button" class="cal-btn nowrap" @click="loadEvents">다시 불러오기</button>
      </div>
      <p v-else-if="eventsLoading && !events.length" class="cal-muted">달력을 불러오는 중…</p>
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
