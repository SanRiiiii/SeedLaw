<template>
  <div class="message-list">
    <template v-if="messages.length > 0">
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        class="message-item"
        :class="message.role"
      >
        <div class="message-avatar">
          <UserOutlined v-if="message.role === 'user'" />
          <RobotOutlined v-else />
        </div>
        <div class="message-content">
          <div class="message-text">{{ message.content }}</div>
        </div>
      </div>
    </template>
    
    <div v-else class="empty-state">
      <div class="empty-icon">
        <MessageOutlined />
      </div>
      <div class="empty-text">开始一个新对话吧</div>
    </div>
    
    <!-- 加载指示器 -->
    <div v-if="loading" class="loading-indicator">
      <a-spin />
    </div>
  </div>
</template>

<script setup>
import { MessageOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons-vue';

defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.message-list {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.message-item {
  display: flex;
  margin-bottom: 24px;
  animation: fade-in 0.3s ease;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  font-size: 20px;
}

.user .message-avatar {
  background-color: #1890ff;
  color: white;
}

.assistant .message-avatar {
  background-color: #52c41a;
  color: white;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 60px);
}

.message-text {
  padding: 12px 16px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.user .message-text {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.assistant .message-text {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
}

.empty-state {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #aaa;
  padding: 40px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  margin: 16px 0;
}
</style> 