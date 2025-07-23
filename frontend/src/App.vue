<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useAuthStore } from './stores/AuthStore';
import { useChatStore } from './stores/ChatStore';

const authStore = useAuthStore();
const chatStore = useChatStore();

// 在应用启动时初始化认证状态
onMounted(() => {
  // 初始化认证状态
  authStore.init();
});

// 监听认证状态变化
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (!isAuthenticated) {
    // 如果用户退出登录，清除聊天数据
    chatStore.clearUserData();
  }
}, { immediate: true });
</script>

<template>
  <router-view />
</template>

<style>
/* Global styles */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

body{
  margin: 0;
  padding: 0;
}

#app {
  height: 100%;
  width: 100%;
}
</style>
