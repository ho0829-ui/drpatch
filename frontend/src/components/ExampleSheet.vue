<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';

const props = defineProps({
  focusId: { type: String, default: '' },
});

const emit = defineEmits(['select']);

const GROUPS = ['처음이라면', '흔한 증상', '까다로운 경우'];
const DONE_KEY = 'drpatch.examples.done';

const examples = ref([]);
const loading = ref(false);
const error = ref('');
const doneIds = ref(new Set());
const expandedSeedId = ref('');
const seedChecked = ref(true);

function loadDoneSet() {
  try {
    const raw = JSON.parse(localStorage.getItem(DONE_KEY) || '[]');
    if (Array.isArray(raw)) doneIds.value = new Set(raw);
  } catch { /* localStorage 없어도 동작 */ }
}

function nextTuesdayDate(offsetDays = 0) {
  const d = new Date();
  const diff = (2 - d.getDay() + 7) % 7 || 7;
  d.setDate(d.getDate() + diff + offsetDays);
  return d;
}

function fmtSeedWhen(se) {
  if (!se) return '';
  const d = nextTuesdayDate(se.offset_days || 0);
  const s = se.start ? se.start.replace(/:00$/, '') : '';
  const e = se.end ? se.end.replace(/:00$/, '') : '';
  const win = s && e ? ` ${s}~${e}시` : '';
  return `${d.getMonth() + 1}/${d.getDate()}${win}`;
}

const grouped = computed(() => {
  const buckets = new Map(GROUPS.map((g) => [g, []]));
  for (const ex of examples.value) {
    const g = ex.group && buckets.has(ex.group) ? ex.group : GROUPS[0];
    buckets.get(g).push(ex);
  }
  return GROUPS.map((name) => ({ name, items: buckets.get(name) })).filter((g) => g.items.length);
});

async function focusTargetCard() {
  if (!props.focusId) return;
  await nextTick();
  const el = document.getElementById(`ex-card-${props.focusId}`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.focus({ preventScroll: true });
  }
}

async function load() {
  loading.value = true;
  error.value = '';
  loadDoneSet();
  try {
    const res = await fetch('/examples/index.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('예시 목록을 불러오지 못했어요.');
    const data = await res.json();
    examples.value = Array.isArray(data) ? data : [];
    await focusTargetCard();
  } catch {
    error.value = '허허, 예시 차트 목록을 못 꺼냈네요. 다시 눌러 보시죠.';
  } finally {
    loading.value = false;
  }
}

function onClickCard(ex) {
  if (ex.seed_event) {
    if (expandedSeedId.value === ex.id) {
      expandedSeedId.value = '';
    } else {
      expandedSeedId.value = ex.id;
      seedChecked.value = true;
    }
    return;
  }
  emit('select', { ...ex, addSeedEvent: false });
}

function startWithSeed(ex) {
  emit('select', { ...ex, addSeedEvent: seedChecked.value });
}

watch(() => props.focusId, focusTargetCard);
onMounted(load);
</script>

<template>
  <p class="eyebrow">예시 차트 · 진료 코스</p>
  <h2 id="sheet-title">예시 시뮬레이션</h2>
  <p class="ex-lead">
    파일 없이도 바로 눌러 보실 수 있습니다. 실제 API로 조회하므로 날마다 결과가 달라질 수 있어요.
  </p>

  <div v-if="error" class="cal-err-box">
    <p class="cal-err">{{ error }}</p>
    <button type="button" class="btn btn-sm ghost" @click="load">다시 불러오기</button>
  </div>

  <p v-else-if="loading" class="ex-muted">예시 차트를 꺼내는 중…</p>

  <div v-else class="ex-groups">
    <section v-for="grp in grouped" :key="grp.name" class="ex-group">
      <h3 class="ex-group-title">{{ grp.name }}</h3>
      <ul class="ex-list">
        <li v-for="ex in grp.items" :key="ex.id" class="ex-item">
          <button
            :id="`ex-card-${ex.id}`"
            type="button"
            class="ex-card"
            :class="{ focused: focusId === ex.id }"
            :aria-expanded="ex.seed_event ? expandedSeedId === ex.id : undefined"
            @click="onClickCard(ex)"
          >
            <div class="ex-head">
              <strong class="ex-title">
                {{ ex.title }}
                <span v-if="doneIds.has(ex.id)" class="ex-done-badge">진료함</span>
              </strong>
              <span class="ex-count">
                패키지 {{ ex.package_count }}개<template v-if="ex.excluded_count"> · 제외 {{ ex.excluded_count }}줄</template>
              </span>
            </div>
            <p class="ex-desc">{{ ex.description }}</p>
            <div v-if="ex.tags?.length" class="ex-tags">
              <span v-for="tag in ex.tags" :key="tag" class="ex-tag">{{ tag }}</span>
            </div>
            <div class="ex-meta">
              <span class="ex-pill">{{ ex.os }}</span>
              <span class="ex-pill">{{ ex.python }}</span>
            </div>
          </button>

          <div v-if="ex.seed_event && expandedSeedId === ex.id" class="ex-seed-box">
            <label class="ex-seed-check">
              <input v-model="seedChecked" type="checkbox">
              <span>내 일정에 '{{ ex.seed_event.title }}'({{ fmtSeedWhen(ex.seed_event) }})도 넣기</span>
            </label>
            <button type="button" class="btn primary btn-sm" @click="startWithSeed(ex)">
              이 예시로 시작
            </button>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
