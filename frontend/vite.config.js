import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/',  // 生产环境静态资源路径
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    minify: true,
  },
  server: {
    host: '0.0.0.0',
    port: 10002,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
