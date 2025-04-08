<template>
    <div class="app-layout" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <!-- 侧边栏切换按钮 -->
      <a-button
        class="sidebar-toggle"
        type="text"
        @click="toggleSidebar"
      >
        <template #icon>
          <MenuFoldOutlined v-if="!isSidebarCollapsed" />
          <MenuUnfoldOutlined v-else />
        </template>
      </a-button>
      
      <!-- 侧边栏组件，传入折叠状态 -->
      <AppSidebar 
        :is-collapsed="isSidebarCollapsed" 
        class="sidebar" 
      />
      
      <!-- 主内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </template>
  
  <script setup>
  import { ref, provide } from 'vue'
  import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
  import AppSidebar from '../components/Sidebar/appSidebar.vue'
  
  // 侧边栏折叠状态
  const isSidebarCollapsed = ref(false)
  
  // 切换侧边栏状态
  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }
  
  // 提供状态给后代组件
  provide('sidebarState', {
    isCollapsed: isSidebarCollapsed,
    toggle: toggleSidebar
  })
  </script>
  
  <style scoped>
  .app-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }
  
  .sidebar {
    width: 280px;
    transition: width 0.3s ease;
  }
  
  .sidebar-collapsed .sidebar {
    width: 60px;
  }
  
  .main-content {
    flex-grow: 1;
    height: 100vh;
    overflow: auto;
    transition: margin-left 0.3s ease;
    background-color: #f5f5f5;
  }
  
  .sidebar-toggle {
    position: absolute;
    z-index: 10;
    top: 16px;
    left: 290px;
    transition: left 0.3s ease;
  }
  
  .sidebar-collapsed .sidebar-toggle {
    left: 70px;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .sidebar {
      position: absolute;
      height: 100%;
      left: 0;
      transform: translateX(0);
      transition: transform 0.3s ease;
    }
    
    .sidebar-collapsed .sidebar {
      transform: translateX(-100%);
      width: 280px; /* 保持宽度不变，只是移出视图 */
    }
  }
  </style>