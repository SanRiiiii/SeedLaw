import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5174,
    strictPort: false,
    cors: true,
    hmr: {
      overlay: true,
    },
    headers: {
      'Cache-Control': 'no-store',
      'Pragma': 'no-cache'
    }
  }
}) 