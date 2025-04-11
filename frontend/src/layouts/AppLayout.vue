<template>
    <div class="flex h-screen w-screen overflow-hidden">
      
      <!-- 侧边栏组件 -->
      <AppSidebar 
        ref="sidebarRef"
        class="transition-all duration-300 ease-in-out sidebar"
        :class="[sidebarWidth]" 
      />
      
      <!-- 主内容区 -->
      <main class="flex-grow h-screen overflow-auto bg-gray-100 transition-all duration-300">
        <router-view />
      </main>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from 'vue'
  import AppSidebar from '../components/Sidebar/AppSidebar.vue'
  
  const sidebarRef = ref(null)
  
  // 根据侧边栏组件内部状态计算宽度
  const sidebarWidth = computed(() => {
    if (!sidebarRef.value) return 'w-[280px]'
    return sidebarRef.value.isCollapsed ? 'w-[60px]' : 'w-[280px]'
  })
  </script>
  
  <style scoped>
  /* 响应式设计 */
  @media (max-width: 768px) {
    .sidebar {
      @apply absolute h-full left-0 transform translate-x-0 transition-transform duration-300 ease-in-out;
    }
    
    .sidebar.w-\[60px\] {
      @apply -translate-x-full; /* 小屏幕上折叠时完全隐藏 */
    }
  }
  </style>