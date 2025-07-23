<template>
  <div class="chat-view">
    <!-- 聊天消息列表 -->
    <div 
      class="messages-container" 
      ref="messagesContainer"
      :class="{ 'centered-state': chatStore.currentMessages.length === 0 }"
    >
      <MessageList :messages="chatStore.currentMessages" :loading="chatStore.isLoading" />
    </div>
    
    <!-- 当没有消息时显示的中央内容 -->
    <div v-if="chatStore.currentMessages.length === 0" class="centered-content">
      <div class="logo-container">
        <img src="../assets/picsvg_download.svg" alt="Logo" class="app-logo" />
      </div>
      <div class="input-centered">
        <ChatInput 
          @send="sendMessage"
          :disabled="chatStore.isLoading" 
        />
      </div>
    </div>
    
    <!-- 有消息时底部显示的输入框 -->
    <div v-else class="input-bottom">
      <ChatInput 
        @send="sendMessage"
        :disabled="chatStore.isLoading" 
      />
    </div>
    
    <!-- 登录/注册模态框 -->
    <AuthModal 
      v-model:visible="authStore.showLoginModal"
      @success="onAuthSuccess"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import { useChatStore } from '../stores/ChatStore';
import { useAuthStore } from '../stores/AuthStore';
import MessageList from '../components/Chat/MessageList.vue';
import ChatInput from '../components/Chat/ChatInput.vue';
import AuthModal from '../components/Auth/AuthModal.vue';
import { message } from 'ant-design-vue';

const chatStore = useChatStore();
const authStore = useAuthStore();
const messagesContainer = ref(null);

// 初始化
onMounted(async () => {
  // 尝试加载用户数据
  await authStore.init();
  
  // 如果用户已登录，确保加载聊天数据
  if (authStore.isAuthenticated) {
    await chatStore.initUserChats();
    
    // 如果有当前聊天，确保加载消息
    if (chatStore.currentChatId) {
      await chatStore.loadChatMessages(chatStore.currentChatId);
    }
  }
  
  // 初始滚动到底部
  await nextTick();
  scrollToBottom();
});

// 发送消息
const sendMessage = async (content) => {
  if (!content || chatStore.isLoading) return;
  
  try {
    // 检查用户是否已登录
    if (!authStore.isAuthenticated) {
      message.warning('请先登录');
      authStore.openLoginModal();
      return;
    }
    
    // 如果没有当前对话，创建一个新对话
    if (!chatStore.currentChatId) {
      await chatStore.createNewChat();
    }
    
    // 发送消息并获取响应
    const response = await chatStore.sendMessage(content);
    console.log('消息发送成功，响应:', response);
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error('发送消息失败:', error);
    if (error.message === '请先登录') {
      message.warning('请先登录');
      authStore.openLoginModal();
    } else {
      message.error('发送消息失败: ' + (error.message || '未知错误'));
    }
  }
};

// 当消息列表更新时，滚动到底部
watch(() => chatStore.currentMessages, async (newMessages) => {
  // 确保DOM更新后滚动
  await nextTick();
  scrollToBottom();
  
  // 调试消息列表
  console.log('当前消息列表:', newMessages);
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

// 登录成功回调
const onAuthSuccess = async () => {
  await chatStore.initUserChats();
};

// 退出登录
const logout = () => {
  authStore.logout();
  chatStore.clearUserData();
};
</script>

<style scoped>
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fafafa;
  position: relative;
}

.messages-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scroll-behavior: smooth;
}

/* 当没有消息时的样式 */
.centered-state {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 中央内容容器 */
.centered-content {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 90%;
  max-width: 700px;
  z-index: 10;
}

/* Logo样式 */
.logo-container {
  margin-bottom: 50px;
  text-align: center;
  width: 50%;
  max-width: 900px;
  display: flex;
  justify-content: center;
}

.app-logo {
  width: 100%;
  height: auto;
  border-radius: 0;
}

/* 底部输入框容器 */
.input-bottom {
  padding: 12px;
  width: 100%;
  max-width: 90%;
  margin: 0 auto;
}

/* 中央输入框容器 */
.input-centered {
  width: 100%;
}
</style>