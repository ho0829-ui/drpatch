<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

const props = defineProps({
  packagesCount: { type: Number, default: 0 },
  conditions: { type: Object, default: null },
});

const emit = defineEmits(['fill', 'upload', 'examples']);

const fileMenuOpen = ref(false);
const fileMenuRef = ref(null);
const uploadOptRef = ref(null);

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];
const OS_NAMES = { ubuntu: 'Ubuntu', macos: 'macOS', windows: 'Windows' };

function fmtOs(c) {
  if (!c?.os_name) return null;
  const label = OS_NAMES[c.os_name] || c.os_name;
  if (!c.os_version) return `${label} (버전 필요)`;
  if (c.os_name === 'windows') {
    const m = String(c.os_version).match(/^(\d+)-(\d{2}h[12])-([we])$/i);
    if (m) return `Windows ${m[1]} ${m[2].toUpperCase()}`;
  }
  return `${label} ${c.os_version}`;
}

function fmtDate(iso) {
  if (!iso) return null;
  const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return String(iso);
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return `${Number(m[2])}/${Number(m[3])}(${WEEKDAYS[d.getDay()]})`;
}

function fmtInterval(days) {
  if (!days) return null;
  return { 7: '매주', 14: '격주', 30: '매월' }[days] || `${days}일마다`;
}

function fmtWindow(c) {
  if (!c?.window_start || !c?.window_end) return null;
  const s = c.window_start;
  const e = c.window_end;
  if (s.endsWith(':00') && e.endsWith(':00')) return `${Number(s.slice(0, 2))}–${Number(e.slice(0, 2))}시`;
  return `${s}–${e}`;
}

const chips = computed(() => {
  const c = props.conditions || {};
  const hasOs = Boolean(c.os_name && c.os_version);
  const osExample =
    c.os_name === 'macos' ? 'macOS 15' : c.os_name === 'windows' ? 'Windows 11 24H2' : 'Ubuntu 22.04';

  const list = [
    {
      key: 'packages',
      label: '파일',
      value: props.packagesCount > 0 ? `파일 ${props.packagesCount}개` : null,
      missing: props.packagesCount === 0,
      action: 'upload',
    },
    {
      key: 'os',
      label: 'OS',
      value: fmtOs(c),
      missing: !hasOs,
      snippet: osExample,
    },
    {
      key: 'python_version',
      label: 'Python',
      value: c.python_version ? `Python ${c.python_version}` : null,
      missing: !c.python_version,
      snippet: 'Python 3.11',
    },
    {
      key: 'capacity',
      label: '한 번에 N개',
      value: c.capacity ? `${c.capacity}개` : null,
      missing: !c.capacity,
      snippet: '한 번에 5개까지',
    },
    {
      key: 'first_date',
      label: '첫 날짜',
      value: fmtDate(c.first_date),
      missing: !c.first_date,
      snippet: '11/25부터',
    },
    {
      key: 'interval_days',
      label: '간격',
      value: fmtInterval(c.interval_days),
      missing: !c.interval_days,
      snippet: '매주',
    },
  ];

  const win = fmtWindow(c);
  if (win) {
    list.push({ key: 'window', label: '시각', value: win, missing: false });
  }
  return list;
});

function closeFileMenu() {
  fileMenuOpen.value = false;
}

function onClickChip(chip) {
  if (chip.action === 'upload') {
    if (chip.missing) {
      fileMenuOpen.value = !fileMenuOpen.value;
      if (fileMenuOpen.value) nextTick(() => uploadOptRef.value?.focus({ preventScroll: true }));
    } else {
      fileMenuOpen.value = false;
      emit('upload');
    }
  } else if (chip.missing && chip.snippet) {
    fileMenuOpen.value = false;
    emit('fill', chip.snippet);
  }
}

function pickUpload() {
  fileMenuOpen.value = false;
  emit('upload');
}

function pickExamples() {
  fileMenuOpen.value = false;
  emit('examples');
}

function onGlobalKeyDown(e) {
  if (e.key === 'Escape' && fileMenuOpen.value) {
    e.stopPropagation();
    closeFileMenu();
  }
}

function onGlobalPointerDown(e) {
  if (fileMenuOpen.value && fileMenuRef.value && !fileMenuRef.value.contains(e.target)) {
    closeFileMenu();
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeyDown);
  window.addEventListener('pointerdown', onGlobalPointerDown);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeyDown);
  window.removeEventListener('pointerdown', onGlobalPointerDown);
});
</script>

<template>
  <div class="cond-chips-wrap">
    <div v-if="fileMenuOpen && packagesCount === 0" ref="fileMenuRef" class="file-choice-pop" role="menu" aria-label="파일 입력 방법 선택">
      <button ref="uploadOptRef" type="button" class="btn btn-sm ghost" role="menuitem" @click="pickUpload">
        파일 올리기
      </button>
      <button type="button" class="btn btn-sm primary" role="menuitem" @click="pickExamples">
        예시 고르기
      </button>
    </div>
    <div class="cond-chips" role="group" aria-label="입력된 점검 조건">
      <button
        v-for="chip in chips"
        :key="chip.key"
        type="button"
        class="cond-chip"
        :class="{ missing: chip.missing, filled: !chip.missing }"
        :aria-expanded="chip.action === 'upload' && chip.missing ? fileMenuOpen : undefined"
        :title="chip.missing ? (chip.action === 'upload' ? '파일 올리기 또는 예시 고르기' : `누르면 '${chip.snippet}' 입력`) : chip.label"
        @click="onClickChip(chip)"
      >
        <template v-if="!chip.missing">{{ chip.value }}</template>
        <template v-else>{{ chip.value || chip.label }} <em>필요</em></template>
      </button>
    </div>
  </div>
</template>
