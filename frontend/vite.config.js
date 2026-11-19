import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
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
