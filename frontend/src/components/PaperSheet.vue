<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { SEV, sevKey } from '../demo.js';
import CalendarSheet from './CalendarSheet.vue';
import LogSheet from './LogSheet.vue';

const props = defineProps({
  sheet: { type: Object, default: null },
});

const emit = defineEmits(['close', 'inspect-item', 'plan-done-change']);
const closeBtn = ref(null);

const sevLabel = (sev) => SEV[sevKey(sev)][1];
const shortDate = (iso) => {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${Number(m[2])}/${Number(m[3])}` : String(iso || '');
};

const roundInfo = computed(() => {
  if (props.sheet?.kind !== 'round') return null;
  return props.sheet.plan?.rounds?.find((r) => r.round_no === props.sheet.roundNo) || null;
});

const windowText = computed(() => {
  const w = props.sheet?.plan?.window;
  return w?.start && w?.end ? `${w.start}–${w.end}` : '';
});

const pythonUpgrade = computed(() => props.sheet?.plan?.python_upgrade || null);
const safeItems = computed(() => props.sheet?.plan?.safe || []);
const unassignedItems = computed(() => props.sheet?.plan?.unassigned || []);
const uncheckedItems = computed(() => props.sheet?.plan?.unchecked || []);
const heldItems = computed(() => props.sheet?.plan?.held || []);

// 열 때 초점을 닫기 버튼으로, 닫을 때 연 자리(누른 버튼 등)로 돌려준다
let returnFocus = null;
watch(
  () => props.sheet,
  async (val, old) => {
    if (val) {
      if (!old) returnFocus = document.activeElement;
      await nextTick();
      closeBtn.value?.focus({ preventScroll: true });
    } else if (returnFocus?.isConnected && returnFocus !== document.body) {
      returnFocus.focus({ preventScroll: true });
      returnFocus = null;
    }
  },
);

const onKeyDown = (e) => {
  if (e.key === 'Escape' && props.sheet) emit('close');
};
onMounted(() => addEventListener('keydown', onKeyDown));
onBeforeUnmount(() => removeEventListener('keydown', onKeyDown));
</script>

<template>
  <!-- 닫힌 종이는 안 보이므로 Tab 초점도 받지 않게 (inert) -->
  <div class="sheet" :class="{ open: !!sheet }" :inert="!sheet">
    <div class="paper" role="dialog" aria-labelledby="sheet-title">
      <div class="band" :style="{ background: sheet?.color || 'transparent' }"></div>
      <button ref="closeBtn" class="close" aria-label="닫기" @click="emit('close')">×</button>

      <template v-if="sheet?.kind === 'item'">
        <p class="eyebrow">
          처방전 ·
          {{
            sheet.item.round
              ? `${sheet.item.round}회차`
              : sheet.item.status === 'safe'
                ? '안전'
                : sheet.item.status === 'unchecked'
                  ? '확인 못 함'
                  : sheet.item.status === 'held'
                    ? '보류'
                    : '다음 진료'
          }}
        </p>
        <h2 id="sheet-title">{{ sheet.item.name }}</h2>
        <div class="ver">
          <span>{{ sheet.item.cur || '미상' }}</span>
          <template v-if="sheet.item.status !== 'safe' && sheet.item.tgt">
            <span class="arrow">→</span>
            <span class="tgt">{{ sheet.item.tgt }}</span>
          </template>
        </div>
        <div class="row">
          <span class="badge" :class="`sev-${sevKey(sheet.item.sev)}`">{{ sevLabel(sheet.item.sev) }}</span>
          <span v-for="f in sheet.item.flags || []" :key="f" class="chip">{{ f }}</span>
        </div>
        <dl>
          <dt>이유</dt>
          <dd>{{ sheet.item.reason || '확인 못 함' }}</dd>
          <dt>지원종료</dt>
          <dd>{{ sheet.item.eol_date || '미상' }}</dd>
          <template v-if="sheet.item.done_at">
            <dt>끝낸 날</dt>
            <dd>{{ String(sheet.item.done_at).slice(0, 10) }}</dd>
          </template>
          <dt>회차</dt>
          <dd>
            {{
              sheet.item.round
                ? `${sheet.item.round}회차`
                : sheet.item.status === 'safe'
                  ? '패치 필요 없음'
                  : sheet.item.status === 'unchecked'
                    ? '확인 못 함'
                    : sheet.item.status === 'held'
                      ? '보류'
                      : '다음 진료'
            }}
          </dd>
        </dl>
        <div v-if="pythonUpgrade?.attempts?.length" class="docnote">
          <b>Python 업그레이드 경로 ({{ pythonUpgrade.status }})</b>
          <ul class="log" style="max-height: 120px; margin-top: 4px;">
            <li v-for="(a, i) in pythonUpgrade.attempts" :key="i">
              Python {{ a.python }} ({{ a.is_eol ? 'EOL' : '지원' }}): {{ a.reason }}
            </li>
          </ul>
        </div>
      </template>

      <template v-else-if="sheet?.kind === 'round' && roundInfo">
        <p class="eyebrow">블리스터 · {{ sheet.roundNo }}회차</p>
        <h2 id="sheet-title">
          {{ roundInfo.date }}
          <small v-if="roundInfo.moved_from" style="font-size: 13px; color: #8A4600;">
            (↻ 원래 {{ shortDate(roundInfo.moved_from) }})
          </small>
        </h2>
        <p class="round-meta">{{ windowText }} · {{ roundInfo.items.length }}정</p>
        <p v-if="roundInfo.moved_from" class="cal-warn">
          내 일정과 겹쳐 {{ shortDate(roundInfo.moved_from) }} → {{ shortDate(roundInfo.date) }}로 옮겼어요.
        </p>
        <p v-if="roundInfo.calendar_conflicts?.length" class="cal-err">
          ⚠ 겹치는 일정: {{ roundInfo.calendar_conflicts.join(', ') }}
        </p>
        <p v-if="sheet.plan?.calendar_check === '확인 못 함'" class="cal-warn">
          캘린더를 확인하지 못했어요.
        </p>
        <ul class="list">
          <li v-for="it in roundInfo.items" :key="it.name">
            <span class="n">{{ it.name }}</span>
            <span class="v">{{ it.current_version }} → {{ it.target_version || '미상' }}</span>
            <span class="badge" :class="`sev-${sevKey(it.severity)}`">{{ sevLabel(it.severity) }}</span>
          </li>
        </ul>
        <div v-if="pythonUpgrade?.attempts?.length" class="docnote">
          <b>Python 업그레이드 경로</b>
          <div v-for="(a, i) in pythonUpgrade.attempts" :key="i" style="font-size: 12.5px;">
            Python {{ a.python }}: {{ a.reason }}
          </div>
        </div>
      </template>

      <template v-else-if="sheet?.kind === 'tray'">
        <p class="eyebrow">곡반 · 건강 확인</p>
        <h2 id="sheet-title">패치 필요 없음</h2>
        <ul v-if="safeItems.length" class="list">
          <li v-for="name in safeItems" :key="name">
            <span class="n">{{ name }}</span>
            <span class="badge sev-safe">안전</span>
          </li>
        </ul>
        <p v-else>해당하는 패키지가 없어요.</p>
      </template>

      <template v-else-if="sheet?.kind === 'jar'">
        <p class="eyebrow">약병 · 미배정 및 보류</p>
        <h2 id="sheet-title">약병에 남은 패키지</h2>
        <ul class="list">
          <li v-for="it in unassignedItems" :key="`u-${it.name}`">
            <span class="n">{{ it.name }} · 다음 진료</span>
            <span class="v">{{ it.current_version }} → {{ it.target_version || '미상' }}</span>
            <span class="badge" :class="`sev-${sevKey(it.severity)}`">{{ sevLabel(it.severity) }}</span>
          </li>
          <li v-for="u in uncheckedItems" :key="`c-${u.name}`">
            <span class="n">{{ u.name }} · 확인 못 함</span>
            <span class="v">{{ u.reason }}</span>
            <span class="badge sev-unchecked">확인 못 함</span>
          </li>
          <li v-for="h in heldItems" :key="`h-${h.name}`">
            <span class="n">{{ h.name }} · 보류</span>
            <span class="v">{{ h.reason }}</span>
            <span class="badge sev-held">보류</span>
          </li>
        </ul>
        <p v-if="!unassignedItems.length && !uncheckedItems.length && !heldItems.length">
          남은 패키지가 없어요.
        </p>
      </template>

      <template v-else-if="sheet?.kind === 'calendar'">
        <CalendarSheet
          @inspect-item="emit('inspect-item', $event)"
          @plan-done-change="emit('plan-done-change', $event)"
        />
      </template>

      <template v-else-if="sheet?.kind === 'log'">
        <LogSheet />
      </template>
    </div>
  </div>
</template>
