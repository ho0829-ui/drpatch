<script setup>
// 박사님 답(LLM)의 가벼운 마크다운만 그린다: **굵게**, 줄바꿈, "- " 목록, "# " 제목.
// v-html을 쓰지 않는다 (글자는 모두 텍스트로만 들어간다).
import { computed } from 'vue';

const props = defineProps({ text: { type: String, default: '' } });

const blocks = computed(() =>
  props.text.split('\n').map((raw) => {
    const line = raw.trimEnd();
    const bullet = /^\s*[-*•]\s+/.test(line);
    const heading = /^\s*#{1,4}\s+/.test(line);
    const body = line.replace(/^\s*[-*•]\s+/, '').replace(/^\s*#{1,4}\s+/, '');
    const segs = body.split(/(\*\*[^*]+\*\*)/g).filter(Boolean)
      .map((s) => (s.startsWith('**') && s.endsWith('**') ? { t: s.slice(2, -2), b: true } : { t: s.replace(/\*\*/g, ''), b: false }));
    return { bullet, heading, empty: !body.trim(), segs };
  }),
);
</script>

<template>
  <span class="rich">
    <template v-for="(bl, i) in blocks" :key="i">
      <span v-if="bl.empty" class="rich-gap"></span>
      <span v-else class="rich-line" :class="{ bullet: bl.bullet, heading: bl.heading }">
        <template v-for="(s, j) in bl.segs" :key="j"><strong v-if="s.b">{{ s.t }}</strong><template v-else>{{ s.t }}</template></template>
      </span>
    </template>
  </span>
</template>
