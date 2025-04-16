<template>
  <div class="settings-page">
    <h1 class="title">设置</h1>
    
    <div class="settings-section">
      <h2 class="section-title">系统设置</h2>
      
      <div class="setting-item">
        <span class="setting-label">主题</span>
        <a-select v-model:value="theme" style="width: 200px">
          <a-select-option value="light">浅色</a-select-option>
          <a-select-option value="dark">深色</a-select-option>
          <a-select-option value="system">跟随系统</a-select-option>
        </a-select>
      </div>
      
      <div class="setting-item">
        <span class="setting-label">语言</span>
        <a-select v-model:value="language" style="width: 200px">
          <a-select-option value="zh">中文</a-select-option>
          <a-select-option value="en">English</a-select-option>
        </a-select>
      </div>
    </div>
    
    <div class="settings-section">
      <h2 class="section-title">用户信息</h2>
      <p>此部分功能尚未实现</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const theme = ref('light');
const language = ref('zh');
</script>

<style scoped>
.settings-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 24px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.settings-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  margin-bottom: 15px;
}

.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.setting-label {
  width: 100px;
  font-weight: 500;
}
</style>
