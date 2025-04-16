<!-- 
侧边栏
功能：
1. 切换对话
2. 新建对话
3. 导航到设置页面

 -->

<template>
  <aside class="h-full flex flex-col bg-[oklch(28.2%_0.091_267.935)] text-white transition-all duration-300 ease-in-out" :class="{ 'collapsed': isCollapsed }">
    <!-- Logo 区域和侧边栏切换按钮 -->
    <div class="p-4 flex items-center justify-between">
      <div class="flex items-center">
        <img src="../../assets/picsvg_download.svg" alt="Logo" class="h-8 w-auto" v-if="!isCollapsed" />
      </div>
      
      <a-button
        type="text"
        class="text-white/80 hover:text-white hover:bg-white/10"
        @click="toggleSidebar"
      >
        <template #icon>
          <MenuFoldOutlined v-if="!isCollapsed" />
          <MenuUnfoldOutlined v-else />
        </template>
      </a-button>
    </div>
    
    <!-- 新建对话按钮 -->
    <div class="p-2 w-full">
      <a-button 
        type="text" 
        class="w-full h-12 text-white flex items-center justify-start px-4 py-3 cursor-pointer bg-white/10 rounded-xl transition-all duration-200 hover:bg-white/20 border border-white/10"
        @click="createNewChat"
      >
        <PlusCircleOutlined class="text-xl mr-3 flex-shrink-0" />
        <span v-if="!isCollapsed" class="text-base font-medium">新建对话</span>
      </a-button>
    </div>

    <!-- 对话列表组件 -->
    <ChatList :is-collapsed="isCollapsed" />
    
    <!-- 底部导航链接 -->
    <div class="mt-auto border-t border-white/10 p-4 flex flex-col gap-2">
      <router-link to="/settings" 
                  class="flex items-center p-2 px-4 rounded-xl text-white/65 hover:text-white hover:bg-white/10 transition-all duration-300" 
                  :class="{ 'bg-[#1677ff] text-white': $route.path === '/settings' }">
        <SettingOutlined />
        <span v-if="!isCollapsed" class="ml-2">设置</span>
      </router-link>
      
      <!-- 登录/退出按钮 -->
      <div 
        class="flex items-center p-2 px-4 rounded-xl text-white/65 hover:text-white hover:bg-white/10 transition-all duration-300 cursor-pointer"
        @click="handleAuthAction"
      >
        <template v-if="authStore.isAuthenticated">
          <LogoutOutlined />
          <span v-if="!isCollapsed" class="ml-2">退出登录</span>
        </template>
        <template v-else>
          <LoginOutlined />
          <span v-if="!isCollapsed" class="ml-2">登录</span>
        </template>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch, defineExpose } from 'vue'
import { PlusCircleOutlined, SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined, LoginOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { useChatStore } from '../../stores/ChatStore.js'
import { useAuthStore } from '../../stores/AuthStore.js'
import ChatList from './ChatList.vue'
import { useRoute } from 'vue-router'

// 自己管理折叠状态
const isCollapsed = ref(false)

const route = useRoute()
const chatStore = useChatStore()
const authStore = useAuthStore()

// 切换侧边栏
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 创建新对话
const createNewChat = () => {
  chatStore.createNewChat()
}

// 处理登录/退出操作
const handleAuthAction = () => {
  if (authStore.isAuthenticated) {
    // 已登录，执行退出操作
    authStore.logout()
    chatStore.clearUserData()
  } else {
    // 未登录，打开登录模态框
    authStore.openLoginModal()
  }
}

// 向父组件暴露状态和方法
defineExpose({
  isCollapsed,
  toggleSidebar
})
</script>