<!-- 
侧边栏
功能：
1. 切换对话
2. 新建对话
3. 导航到设置页面

 -->

<template>
  <aside class="app-sidebar" :class="{ 'collapsed': isCollapsed }">
    <!-- Logo 区域 -->
    <div class="sidebar-header">
      <img src="../assets/vue.svg" alt="Logo" class="logo" v-if="!isCollapsed" />
      <img src="../assets/vue.svg" alt="Logo" class="logo-small" v-else />
    </div>
    
    <!-- 新建对话按钮 -->
    <div class="new-chat-section">
      <a-button 
        type="primary" 
        class="new-chat-btn"
        @click="createNewChat"
      >
        <template #icon><PlusOutlined /></template>
        <span v-if="!isCollapsed">新建对话</span>
      </a-button>
    </div>

    <!-- 对话列表组件 -->
    <ChatList :is-collapsed="isCollapsed" />
    
    <!-- 底部导航链接 -->
    <div class="sidebar-footer">
      <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
        <MessageOutlined />
        <span v-if="!isCollapsed">对话</span>
      </router-link>
      <router-link to="/settings" class="nav-link" :class="{ active: $route.path === '/settings' }">
        <SettingOutlined />
        <span v-if="!isCollapsed">设置</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { PlusOutlined, MessageOutlined, SettingOutlined } from '@ant-design/icons-vue'
import { useChatStore } from '../../stores/ChatStore.js'
import ChatList from './ChatList.vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const chatStore = useChatStore()

// 创建新对话
const createNewChat = () => {
  chatStore.createNewChat()
}
</script>

<style scoped>
.app-sidebar {
  background-color: #001529;
  color: white;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  height: 32px;
  width: auto;
}

.logo-small {
  height: 32px;
  width: 32px;
}

.new-chat-section {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
}

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.active {
  color: white;
  background: #1677ff;
}

.nav-link span {
  margin-left: 8px;
}
</style>

