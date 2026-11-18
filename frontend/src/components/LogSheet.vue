<script setup>
import { computed, onMounted, ref } from 'vue';
import * as api from '../api.js';

const sessions = ref([]);
const selectedId = ref(null);
const events = ref([]);
const errorMsg = ref('');
const loading = ref(false);

const sortedEvents = computed(() =>
  [...events.value].sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0)),
);

function formatEvent(ev) {
  const p = ev.payload || ev;
  if (ev.type === 'judgment') {
    const pkgs = (p.packages || [])
      .map((x) => `${x.name} ${x.current || '미상'}(${x.severity || '미상'})`)
      .join(', ');
    const viol = (p.violations || []).join(', ') || '없음';
    return `판정 — ${pkgs || '항목 없음'} | Python 제약 위반: ${viol}`;
  }
  if (ev.type === 'replan') {
    if (p.python) {
      return `재계획 #${p.no ?? ''}: Python ${p.python} (${p.is_eol ? '지원 종료' : '지원 중'}) — ${p.reason || ''}`;
    }
    return `재계획 보류 — ${p.reason || ''}`;
  }
  if (ev.type === 'plan_built') {
    const rounds = (p.rounds || [])
      .map((r) => `${r.round_no}회차(${r.date}): ${(r.items || []).join(', ')}`)
      .join(' / ');
    const un = (p.unassigned || []).length ? ` | 미배정: ${p.unassigned.join(', ')}` : '';
    return `계획 수립 — ${rounds || '회차 없음'}${un}`;
  }
  if (ev.type === 'step_start' || ev.type === 'step_end') {
    return `${ev.type === 'step_start' ? '단계 시작' : '단계 완료'}: ${p.step || ''}`;
  }
  if (ev.type === 'tool_call' || ev.type === 'tool_result') {
    const target = p.args?.name || p.args?.product || '';
    return `${ev.type}: ${p.tool || ''} ${target} ${p.ok === false ? `(${p.error_code || '실패'})` : ''}`.trim();
  }
  if (ev.type === 'calendar_check') {
    return `캘린더 확인: ${p.status || ''}`;
  }
  if (ev.type === 'error') {
    return `오류: ${p.step || ''} ${p.kind || ''}`.trim();
  }
  return `${ev.type}`;
}

async function loadSessions() {
  loading.value = true;
  errorMsg.value = '';
  try {
    sessions.value = await api.logs.list();
    const cur = api.getSession();
    const pick =
      sessions.value.find((s) => s.session_id === selectedId.value)?.session_id ||
      sessions.value.find((s) => s.session_id === cur)?.session_id ||
      sessions.value[0]?.session_id ||
      null;
    if (pick) await selectSession(pick);
    else {
      selectedId.value = null;
      events.value = [];
    }
  } catch (err) {
    errorMsg.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function selectSession(sid) {
  selectedId.value = sid;
  errorMsg.value = '';
  try {
    const data = await api.logs.get(sid);
    events.value = data.events || [];
  } catch (err) {
    events.value = [];
    errorMsg.value = err.message;
  }
}

async function deleteSession(sid) {
  if (!confirm('이 세션의 진료 기록을 삭제할까요?')) return;
  errorMsg.value = '';
  try {
    await api.logs.remove(sid);
    if (selectedId.value === sid) selectedId.value = null;
    await loadSessions();
  } catch (err) {
    errorMsg.value = err.message;
  }
}

onMounted(loadSessions);
</script>

<template>
  <div class="log-sheet">
    <p class="eyebrow">진료 기록</p>
    <h2 id="sheet-title">실행 로그</h2>

    <p v-if="errorMsg" class="cal-err">{{ errorMsg }}</p>
    <p v-if="!sessions.length && !loading" class="cal-muted">저장된 세션 기록이 없어요.</p>

    <div v-if="sessions.length" class="log-sessions">
      <div
        v-for="s in sessions"
        :key="s.session_id"
        class="log-sess-row"
        :class="{ active: s.session_id === selectedId }"
      >
        <button type="button" class="log-sess-btn" @click="selectSession(s.session_id)">
          <b>{{ s.session_id.slice(0, 8) }}</b>
          <small>{{ s.event_count ?? '' }}건 · {{ s.last_at || '' }}</small>
        </button>
        <button
          type="button"
          class="cal-btn danger"
          aria-label="세션 기록 삭제"
          @click="deleteSession(s.session_id)"
        >
          삭제
        </button>
      </div>
    </div>

    <ol v-if="sortedEvents.length" class="log" style="margin-top: 10px;">
      <li v-for="ev in sortedEvents" :key="ev.seq ?? ev.id">
        <b>#{{ ev.seq }}</b> {{ formatEvent(ev) }}
      </li>
    </ol>
  </div>
</template>
