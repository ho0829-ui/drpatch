<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { ITEMS, PER_ROUND, ROUNDS, SEV, roundOf } from '../demo.js';

const props = defineProps({
  sheet: { type: Object, default: null },
});

const emit = defineEmits(['close']);
const closeBtn = ref(null);

const sevLabel = (sev) => (SEV[sev] ? SEV[sev][1] : '미상');

const roundItems = computed(() =>
  props.sheet?.kind === 'round' ? ITEMS.filter((it) => it.round === props.sheet.roundNo) : [],
);
const roundInfo = computed(() =>
  props.sheet?.kind === 'round' ? roundOf(props.sheet.roundNo) : null,
);
const safeItems = computed(() => ITEMS.filter((it) => it.status === 'safe'));
const nextItems = computed(() => ITEMS.filter((it) => it.status === 'next'));

watch(
  () => props.sheet,
  async (val) => {
    if (val) {
      await nextTick();
      closeBtn.value?.focus({ preventScroll: true });
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
  <div class="sheet" :class="{ open: !!sheet }">
    <div class="paper" role="dialog" aria-labelledby="sheet-title">
      <div class="band" :style="{ background: sheet?.color || 'transparent' }"></div>
      <button ref="closeBtn" class="close" aria-label="닫기" @click="emit('close')">×</button>

      <template v-if="sheet?.kind === 'item'">
        <p class="eyebrow">
          처방전 · {{ sheet.item.round ? `${sheet.item.round}회차` : sheet.item.status === 'safe' ? '안전' : '다음 진료' }}
        </p>
        <h2 id="sheet-title">{{ sheet.item.name }}</h2>
        <div class="ver">
          <span>{{ sheet.item.cur }}</span>
          <template v-if="sheet.item.status !== 'safe'">
            <span class="arrow">→</span>
            <span class="tgt">{{ sheet.item.tgt }}</span>
          </template>
        </div>
        <div class="row">
          <span class="badge" :class="`sev-${sheet.item.sev}`">{{ sevLabel(sheet.item.sev) }}</span>
          <span v-for="f in sheet.item.flags" :key="f" class="chip">{{ f }}</span>
        </div>
        <dl>
          <dt>이유</dt>
          <dd>{{ sheet.item.reason }}</dd>
          <dt>회차</dt>
          <dd>
            {{
              sheet.item.round
                ? `${sheet.item.round}회차 · ${roundOf(sheet.item.round).full} ${roundOf(sheet.item.round).win}`
                : sheet.item.status === 'safe'
                  ? '패치 필요 없음'
                  : '다음 진료'
            }}
          </dd>
        </dl>
        <p class="docnote"><b>DR.PATCH</b>{{ sheet.item.note }}</p>
      </template>

      <template v-else-if="sheet?.kind === 'round' && roundInfo">
        <p class="eyebrow">블리스터 · {{ sheet.roundNo }}회차</p>
        <h2 id="sheet-title">{{ roundInfo.full }}</h2>
        <p class="round-meta">{{ roundInfo.win }} · {{ roundItems.length }}/{{ PER_ROUND }}정</p>
        <ul class="list">
          <li v-for="it in roundItems" :key="it.name">
            <span class="n">{{ it.name }}</span>
            <span class="v">{{ it.cur }}<template v-if="it.status !== 'safe'"> → {{ it.tgt }}</template></span>
            <span class="badge" :class="`sev-${it.sev}`">{{ sevLabel(it.sev) }}</span>
          </li>
        </ul>
        <p class="docnote">
          <b>DR.PATCH</b>
          {{
            sheet.roundNo === 1
              ? '급한 것부터 담았습니다. Python이 먼저 올라가야 2회차가 편해요.'
              : sheet.roundNo === 2
                ? 'Python을 올린 다음 회차입니다. 순서 바꾸시면 곤란합니다.'
                : '나머지 중에 급한 순서대로 담았습니다.'
          }}
        </p>
      </template>

      <template v-else-if="sheet?.kind === 'tray'">
        <p class="eyebrow">곡반 · 건강 확인</p>
        <h2 id="sheet-title">패치 필요 없음</h2>
        <ul class="list">
          <li v-for="it in safeItems" :key="it.name">
            <span class="n">{{ it.name }}</span>
            <span class="v">{{ it.cur }}</span>
            <span class="badge" :class="`sev-${it.sev}`">{{ sevLabel(it.sev) }}</span>
          </li>
        </ul>
        <p class="docnote"><b>DR.PATCH</b>최신이고 알려진 취약점이 없는 녀석들입니다. 오늘은 돌려보내죠.</p>
      </template>

      <template v-else-if="sheet?.kind === 'jar'">
        <p class="eyebrow">약병 · 다음 진료</p>
        <h2 id="sheet-title">회차에 못 든 패키지</h2>
        <ul class="list">
          <li v-for="it in nextItems" :key="it.name">
            <span class="n">{{ it.name }}</span>
            <span class="v">{{ it.cur }} → {{ it.tgt }}</span>
            <span class="badge" :class="`sev-${it.sev}`">{{ sevLabel(it.sev) }}</span>
          </li>
        </ul>
        <p class="docnote">
          <b>DR.PATCH</b>회차는 최대 {{ ROUNDS.length }}번, 회차마다 {{ PER_ROUND }}정까지예요. 넘친 건 다음 진료 때 봅시다.
        </p>
      </template>

      <template v-else-if="sheet?.kind === 'log'">
        <p class="eyebrow">진료 기록</p>
        <h2 id="sheet-title">실행 로그</h2>
        <ol v-if="sheet.logs?.length" class="log">
          <li v-for="(l, idx) in sheet.logs" :key="idx">{{ l }}</li>
        </ol>
        <p v-else>아직 기록이 없어요. 진료를 시작해 보세요.</p>
      </template>
    </div>
  </div>
</template>
