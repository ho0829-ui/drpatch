<script setup>
import { asset } from '../paths.js';
import { SEV, sevKey } from '../demo.js';

defineProps({
  message: {
    type: String,
    default: '이 브라우저에서는 3D 책상을 그릴 수 없어 목록으로 보여드려요.',
  },
  canReturn3d: Boolean,
  plan: { type: Object, default: null },
  packages: { type: Array, default: () => [] },
  state: { type: String, default: 'idle' },
});

const emit = defineEmits(['return-3d', 'upload', 'start', 'confirm', 'calendar', 'logs']);
const sevLabel = (sev) => SEV[sevKey(sev)][1];
</script>

<template>
  <section class="fallback" aria-label="패치 계획 목록 화면">
    <div>
      <div class="fallback-head">
        <h1><img :src="asset('brand/logo-lockup.svg')" height="56" alt="DR.PATCH"></h1>
        <button v-if="canReturn3d" type="button" class="btn btn-sm" @click="emit('return-3d')">
          3D 진료실로 보기
        </button>
      </div>
      <p>{{ message }}</p>

      <div class="fallback-actions">
        <button type="button" class="btn btn-sm" @click="emit('upload')">파일 올리기</button>
        <button type="button" class="btn primary btn-sm" :disabled="state !== 'ready'" @click="emit('start')">진료 시작</button>
        <button type="button" class="btn hot btn-sm" :disabled="state !== 'planned'" @click="emit('confirm')">처방 확정</button>
        <button type="button" class="btn btn-sm" @click="emit('calendar')">진료 예약</button>
        <button type="button" class="btn btn-sm" @click="emit('logs')">진료 기록</button>
      </div>

      <template v-if="plan">
        <template v-for="r in plan.rounds || []" :key="r.round_no">
          <h3>
            {{ r.round_no }}회차 ({{ r.date }})
            <small v-if="r.moved_from">↻ {{ r.moved_from }}</small>
          </h3>
          <ul class="list">
            <li v-for="it in r.items" :key="it.name">
              <span class="n">{{ it.name }}</span>
              <span class="v">{{ it.current_version }} → {{ it.target_version || '미상' }} · {{ it.reason }}</span>
              <span class="badge" :class="`sev-${sevKey(it.severity)}`">{{ sevLabel(it.severity) }}</span>
            </li>
          </ul>
        </template>

        <template v-if="(plan.unassigned || []).length">
          <h3>다음 진료 (미배정)</h3>
          <ul class="list">
            <li v-for="it in plan.unassigned" :key="it.name">
              <span class="n">{{ it.name }}</span>
              <span class="v">{{ it.current_version }} → {{ it.target_version || '미상' }}</span>
              <span class="badge" :class="`sev-${sevKey(it.severity)}`">{{ sevLabel(it.severity) }}</span>
            </li>
          </ul>
        </template>

        <template v-if="(plan.safe || []).length">
          <h3>안전 (패치 필요 없음)</h3>
          <ul class="list">
            <li v-for="name in plan.safe" :key="name">
              <span class="n">{{ name }}</span>
              <span class="badge sev-safe">안전</span>
            </li>
          </ul>
        </template>

        <template v-if="(plan.unchecked || []).length || (plan.held || []).length">
          <h3>확인 못 함 / 보류</h3>
          <ul class="list">
            <li v-for="u in plan.unchecked || []" :key="`u-${u.name}`">
              <span class="n">{{ u.name }}</span>
              <span class="v">{{ u.reason }}</span>
              <span class="badge sev-unchecked">확인 못 함</span>
            </li>
            <li v-for="h in plan.held || []" :key="`h-${h.name}`">
              <span class="n">{{ h.name }}</span>
              <span class="v">{{ h.reason }}</span>
              <span class="badge sev-held">보류</span>
            </li>
          </ul>
        </template>
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
