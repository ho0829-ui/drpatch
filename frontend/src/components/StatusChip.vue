<script setup>
defineProps({
  text: { type: String, default: '대기 중' },
  stage: { type: Number, default: -1 },
});
</script>

<template>
  <div class="status" role="status">
    <span>{{ text }}</span>
    <span class="dots" aria-hidden="true">
      <i v-for="i in 4" :key="i" :class="{ on: i - 1 <= stage }"></i>
    </span>
  </div>
</template>
