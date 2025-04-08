<template>
  <div class="chat-view">
    <!-- 聊天消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <MessageList :messages="chatStore.currentMessages" :loading="chatStore.isLoading" />
    </div>
    
    <!-- 输入组件 -->
    <div class="input-container">
      <ChatInput 
        @send="sendMessage"
        :disabled="chatStore.isLoading" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { useChatStore } from '../stores/ChatStore';
import MessageList from '../components/Chat/MessageList.vue';
import ChatInput from '../components/Chat/ChatInput.vue';

const chatStore = useChatStore();
const messagesContainer = ref(null);  

// 发送消息
const sendMessage = (content) => {
  if (content && !chatStore.isLoading) {
    chatStore.sendMessage(content);
  }
};

// 当消息列表更新时，滚动到底部
watch(() => chatStore.currentMessages, async () => {
  await nextTick();
  scrollToBottom();
}, { deep: true });

// 当切换对话时，滚动到底部
watch(() => chatStore.currentChatId, async () => {
  await nextTick();
  scrollToBottom();
});

// 滚动到底部辅助函数
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};
</script>

<style scoped>
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.messages-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scroll-behavior: smooth;
}

.input-container {
  padding: 16px;
  background-color: white;
  border-top: 1px solid #e8e8e8;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}
</style>