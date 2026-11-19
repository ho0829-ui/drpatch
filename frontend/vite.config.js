import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
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
