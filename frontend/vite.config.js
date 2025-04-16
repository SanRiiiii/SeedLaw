import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

import components from 'unplugin-vue-components/vite'
import { AntDesignXVueResolver } from 'ant-design-x-vue/resolver';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    components({
      resolvers: [AntDesignXVueResolver()],
    }),
    vue(),
  ],
})
