<script setup>
import { ITEMS, SEV } from '../demo.js';

defineProps({
  message: {
    type: String,
    default: '이 브라우저에서는 3D 책상을 그릴 수 없어 목록으로 보여드려요.',
  },
});

const sevLabel = (sev) => (SEV[sev] ? SEV[sev][1] : '미상');
</script>

<template>
  <section class="fallback">
    <div>
      <h1><img src="/brand/logo-lockup.svg" height="64" alt="DR.PATCH"></h1>
      <p>{{ message }}</p>
      <ul class="list">
        <li v-for="it in ITEMS" :key="it.name">
          <span class="n">
            {{ it.name }} · {{ it.round ? `${it.round}회차` : it.status === 'safe' ? '안전' : '다음 진료' }}
          </span>
          <span class="v">{{ it.cur }} → {{ it.tgt }}</span>
          <span class="badge" :class="`sev-${it.sev}`">{{ sevLabel(it.sev) }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>
