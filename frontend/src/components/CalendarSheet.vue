<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import * as api from '../api.js';

const today = new Date();
const viewYear = ref(today.getFullYear());
const viewMonth = ref(today.getMonth()); // 0-indexed
const selectedDate = ref(today.toISOString().slice(0, 10));

const events = ref([]);
const plans = ref([]);
const errorMsg = ref('');
const loading = ref(false);

const newTitle = ref('');
const newDate = ref(selectedDate.value);
const newStart = ref('');
const newEnd = ref('');

const editingPlanId = ref(null);
const editDate = ref('');
const editStart = ref('');
const editEnd = ref('');

const monthLabel = computed(() => `${viewYear.value}년 ${viewMonth.value + 1}월`);

const monthRange = computed(() => {
  const y = viewYear.value;
  const m = viewMonth.value;
  const from = new Date(y, m, 1);
  const to = new Date(y, m + 1, 0);
  const pad = (n) => String(n).padStart(2, '0');
  return {
    from: `${y}-${pad(m + 1)}-01`,
    to: `${y}-${pad(m + 1)}-${pad(to.getDate())}`,
    firstDow: from.getDay(),
    daysInMonth: to.getDate(),
  };
});

const calendarCells = computed(() => {
  const { firstDow, daysInMonth } = monthRange.value;
  const y = viewYear.value;
  const m = String(viewMonth.value + 1).padStart(2, '0');
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${y}-${m}-${String(d).padStart(2, '0')}`;
    const planCount = plans.value.filter((p) => p.date === iso).length;
    const eventCount = events.value.filter((e) => e.date === iso).length;
    const parts = [`${viewMonth.value + 1}월 ${d}일`];
    if (planCount) parts.push(`패치 계획 ${planCount}개`);
    if (eventCount) parts.push(`내 일정 ${eventCount}개`);
    cells.push({
      day: d,
      iso,
      hasPlan: planCount > 0,
      hasEvent: eventCount > 0,
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
    const [evRes, plRes] = await Promise.all([
      api.calendar.list(from, to).catch((err) => {
        errorMsg.value = err.message;
        return [];
      }),
      api.plans.list().catch((err) => {
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

function selectDay(iso) {
  selectedDate.value = iso;
  newDate.value = iso;
}

function startEditPlan(p) {
  editingPlanId.value = p.id;
  editDate.value = p.date;
  editStart.value = p.window_start || '';
  editEnd.value = p.window_end || '';
}

async function savePlan(id) {
  errorMsg.value = '';
  try {
    await api.plans.update(id, {
      date: editDate.value || undefined,
      window_start: editStart.value || null,
      window_end: editEnd.value || null,
    });
    editingPlanId.value = null;
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

watch([viewYear, viewMonth], loadAll);
onMounted(loadAll);
</script>

<template>
  <div class="cal-sheet">
    <p class="eyebrow">진료 예약 · 캘린더</p>
    <h2 id="sheet-title">월간 예약 달력</h2>

    <p v-if="errorMsg" class="cal-err">{{ errorMsg }}</p>

    <div class="cal-nav">
      <button type="button" class="cal-btn" aria-label="이전 달" @click="shiftMonth(-1)">◀</button>
      <b>{{ monthLabel }}</b>
      <button type="button" class="cal-btn" aria-label="다음 달" @click="shiftMonth(1)">▶</button>
    </div>

    <div class="cal-legend" aria-hidden="true">
      <span><i class="dot-plan"></i> 패치 계획</span>
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
          :class="{ selected: cell.iso === selectedDate }"
          :aria-label="cell.ariaLabel"
          :aria-pressed="cell.iso === selectedDate"
          @click="selectDay(cell.iso)"
        >
          <span>{{ cell.day }}</span>
          <span class="cal-dots" aria-hidden="true">
            <i v-if="cell.hasPlan" class="dot-plan" title="저장된 패치 계획"></i>
            <i v-if="cell.hasEvent" class="dot-event" title="내 일정"></i>
          </span>
        </button>
      </template>
    </div>

    <div class="cal-section">
      <h3>저장된 계획 ({{ plans.length }})</h3>
      <p v-if="!plans.length && !loading" class="cal-muted">저장된 계획이 없어요.</p>
      <ul class="cal-list">
        <li v-for="p in plans" :key="p.id">
          <template v-if="editingPlanId === p.id">
            <div class="cal-edit-row">
              <input v-model="editDate" type="date" aria-label="계획 날짜">
              <input v-model="editStart" type="time" aria-label="시작 시각">
              <input v-model="editEnd" type="time" aria-label="종료 시각">
              <button type="button" class="cal-btn" @click="savePlan(p.id)">저장</button>
              <button type="button" class="cal-btn" @click="editingPlanId = null">취소</button>
            </div>
          </template>
          <template v-else>
            <div class="cal-item-row">
              <span>
                <b>{{ p.round_no }}회차</b> · {{ p.date }}
                <template v-if="p.window_start"> {{ p.window_start }}–{{ p.window_end }}</template>
                ({{ (p.items || []).length }}건)
              </span>
              <span class="cal-actions">
                <button type="button" class="cal-btn" @click="startEditPlan(p)">수정</button>
                <button type="button" class="cal-btn danger" @click="deletePlan(p.id)">삭제</button>
              </span>
            </div>
            <p v-if="p.overlaps?.length" class="cal-warn">
              ⚠ 같은 날 시간이 겹치는 일정 {{ p.overlaps.length }}건이 있어요.
            </p>
          </template>
        </li>
      </ul>
    </div>

    <div class="cal-section">
      <h3>내 일정 ({{ events.length }})</h3>
      <form class="cal-form" @submit.prevent="addEvent">
        <input v-model="newTitle" type="text" placeholder="일정 제목" required aria-label="일정 제목">
        <input v-model="newDate" type="date" required aria-label="일정 날짜">
        <input v-model="newStart" type="time" aria-label="시작 시각">
        <input v-model="newEnd" type="time" aria-label="종료 시각">
        <button type="submit" class="cal-btn primary">추가</button>
      </form>
      <ul class="cal-list">
        <li v-for="ev in events" :key="ev.id" class="cal-item-row">
          <span>{{ ev.date }} <template v-if="ev.start">{{ ev.start }}–{{ ev.end }} </template>· {{ ev.title }}</span>
          <button type="button" class="cal-btn danger" @click="removeEvent(ev.id)">삭제</button>
        </li>
      </ul>
    </div>
  </div>
</template>
