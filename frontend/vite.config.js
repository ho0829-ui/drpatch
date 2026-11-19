import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  // GitHub Pages는 /sudo-patch/ 아래에 올라간다 (워크플로가 VITE_BASE를 준다). 로컬·Funnel 단독은 /
  base: process.env.VITE_BASE || '/',
  plugins: [vue()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // three 본체(three.module.js)는 한 덩어리 ES 모듈이라 더 못 나눈다: 523KB(gzip 133KB). 경고 기준만 그에 맞춘다
    chunkSizeWarningLimit: 550,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three/examples/')) return 'three-addons';
          if (id.includes('node_modules/three/')) return 'three';
          if (id.includes('node_modules/@vue/') || id.includes('node_modules/vue/')) return 'vue';
        },
      },
    },
  },
});
