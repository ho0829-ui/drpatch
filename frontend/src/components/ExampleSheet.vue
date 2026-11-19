<script setup>
import { onMounted, ref } from 'vue';

const emit = defineEmits(['select']);

const examples = ref([]);
const loading = ref(false);
const error = ref('');

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const res = await fetch('/examples/index.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('예시 목록을 불러오지 못했어요.');
    const data = await res.json();
    examples.value = Array.isArray(data) ? data : [];
  } catch {
    error.value = '허허, 예시 차트 목록을 못 꺼냈네요. 다시 눌러 보시죠.';
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <p class="eyebrow">예시 차트 · 바로 체험</p>
  <h2 id="sheet-title">예시 시뮬레이션</h2>
  <p class="ex-lead">
    파일 없이도 바로 눌러 보실 수 있습니다. 실제 API로 조회하므로 날마다 결과가 달라질 수 있어요.
  </p>

  <div v-if="error" class="cal-err-box">
    <p class="cal-err">{{ error }}</p>
    <button type="button" class="btn btn-sm ghost" @click="load">다시 불러오기</button>
  </div>

  <p v-else-if="loading" class="ex-muted">예시 차트를 꺼내는 중…</p>

  <ul v-else class="ex-list">
    <li v-for="ex in examples" :key="ex.id">
      <button type="button" class="ex-card" @click="emit('select', ex)">
        <div class="ex-head">
          <strong class="ex-title">{{ ex.title }}</strong>
          <span class="ex-count">
            패키지 {{ ex.package_count }}개<template v-if="ex.excluded_count"> · 제외 {{ ex.excluded_count }}줄</template>
          </span>
        </div>
        <p class="ex-desc">{{ ex.description }}</p>
        <div class="ex-meta">
          <span class="ex-pill">{{ ex.os }}</span>
          <span class="ex-pill">{{ ex.python }}</span>
        </div>
      </button>
    </li>
  </ul>
</template>
