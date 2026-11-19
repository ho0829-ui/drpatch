<script setup>
// 오른쪽 위 보조 묶음: 목록 보기 · 처음부터 · 움직임 줄이기 · 조작 도움말 · 숨은 것 개수
import { ref } from 'vue';

defineProps({
  reduced: Boolean,
  eggs: { type: Object, default: () => ({ found: 0, total: 16 }) },
  nightState: { type: Object, default: () => ({ unlocked: false, night: false }) },
});
const emit = defineEmits(['toggle-list', 'reset', 'update:reduced', 'toggle-night']);
const helpOpen = ref(false);
</script>

<template>
  <div class="top-tools">
    <div class="tool-row">
      <button class="chip-btn" @click="emit('toggle-list')">목록으로 보기</button>
      <button class="chip-btn reset" @click="emit('reset')">처음부터</button>
      <label class="chip-btn toggle">
        <input type="checkbox" :checked="reduced" @change="emit('update:reduced', $event.target.checked)">
        움직임 줄이기
      </label>
      <button class="chip-btn icon" :aria-expanded="helpOpen" aria-label="조작 도움말" @click="helpOpen = !helpOpen">?</button>
    </div>
    <div v-if="helpOpen" class="help-card">
      <p><b>드래그</b> 돌려 보기 · <b>오른쪽 드래그</b>(Shift) 이동 · <b>휠</b> 줌 · <b>더블클릭</b> 처음 시점</p>
      <p>알약·블리스터·차트·약병을 누르면 종이가 펼쳐져요.</p>
    </div>
    <!-- 16/16을 다 찾으면 숨은 것 칩이 낮/밤 전환 버튼이 된다 (야간 당직 진료실) -->
    <button
      v-if="nightState.unlocked"
      type="button"
      class="egg-chip night-toggle"
      :aria-pressed="nightState.night"
      :title="nightState.night ? '낮 진료실로' : '야간 당직 진료실로'"
      @click="emit('toggle-night')"
    >
      <span aria-hidden="true">{{ nightState.night ? '☀' : '🌙' }}</span>
      {{ nightState.night ? '낮으로' : '야간 당직' }} · {{ eggs.found }}/{{ eggs.total }}
    </button>
    <div v-else class="egg-chip" :title="'진료실 곳곳의 숨은 것'">숨은 것 {{ eggs.found }}/{{ eggs.total }}</div>
  </div>
</template>
