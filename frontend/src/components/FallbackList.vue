<script setup>
import { SEV, sevKey } from '../demo.js';

defineProps({
  message: {
    type: String,
    default: '이 브라우저에서는 3D 책상을 그릴 수 없어 목록으로 보여드려요.',
  },
  plan: { type: Object, default: null },
  packages: { type: Array, default: () => [] },
});

const sevLabel = (sev) => SEV[sevKey(sev)][1];
</script>

<template>
  <section class="fallback">
    <div>
      <h1><img src="/brand/logo-lockup.svg" height="64" alt="DR.PATCH"></h1>
      <p>{{ message }}</p>

      <template v-if="plan">
        <template v-for="r in plan.rounds || []" :key="r.round_no">
          <h3>{{ r.round_no }}회차 ({{ r.date }})</h3>
          <ul class="list">
            <li v-for="it in r.items" :key="it.name">
              <span class="n">{{ it.name }}</span>
              <span class="v">{{ it.current_version }} → {{ it.target_version || '미상' }}</span>
              <span class="badge" :class="`sev-${sevKey(it.severity)}`">{{ sevLabel(it.severity) }}</span>
            </li>
          </ul>
        </template>
        <ul v-if="(plan.safe || []).length" class="list">
          <li v-for="name in plan.safe" :key="name">
            <span class="n">{{ name }} · 안전</span>
            <span class="badge sev-safe">안전</span>
          </li>
        </ul>
      </template>

      <ul v-else-if="packages.length" class="list">
        <li v-for="pkg in packages" :key="pkg.name">
          <span class="n">{{ pkg.name }}</span>
          <span class="v">{{ pkg.version || '미상' }}</span>
          <span class="badge sev-unknown">검사 전</span>
        </li>
      </ul>

      <p v-else>requirements.txt를 올려 주세요.</p>
    </div>
  </section>
</template>
