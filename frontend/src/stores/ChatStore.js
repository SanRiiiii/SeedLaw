import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createChat, getChatReply, getChatList, getChatHistory, deleteChat, updateChatTitle as apiUpdateChatTitle } from '../api/chat'
import { useAuthStore } from './AuthStore'

// 记得去App那里注册一下

export const useChatStore = defineStore('chat', () => {
  // 引入认证Store
  const authStore = useAuthStore();
  
  // 状态
  const chatList = ref([])
  const currentChatId = ref(null)
  const chatMessages = ref({}) // 每个对话的消息 { chatId: [messages] }
  const isLoading = ref(false)

  // 计算属性
  const currentChat = computed(() => 
    chatList.value.find(chat => chat.id === currentChatId.value)
  )
  
  const currentMessages = computed(() => 
    chatMessages.value[currentChatId.value] || []
  )
  
  // 初始化方法 - 在用户登录后调用
  async function initUserChats() {
    if (!authStore.isAuthenticated) return;
    
    isLoading.value = true;
    try {
      const conversations = await getChatList();
      chatList.value = conversations || [];
      
      // 如果有对话，自动选择第一个
      if (chatList.value.length > 0) {
        currentChatId.value = chatList.value[0].id;
        // 加载第一个对话的消息
        await loadChatMessages(currentChatId.value);
      }
    } catch (error) {
      console.error('Failed to init user chats:', error);
    } finally {
      isLoading.value = false;
    }
  }
  
  // 加载特定对话的消息历史
  async function loadChatMessages(chatId) {
    if (!authStore.isAuthenticated) return;
    
    // 如果已有消息，不重复加载
    if (chatMessages.value[chatId] && chatMessages.value[chatId].length > 0) {
      return;
    }
    
    isLoading.value = true;
    try {
      const conversation = await getChatHistory(chatId);
      // 确保保存的消息格式与MessageList组件兼容
      if (conversation.messages && Array.isArray(conversation.messages)) {
        chatMessages.value[chatId] = conversation.messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));
      } else {
        chatMessages.value[chatId] = [];
      }
    } catch (error) {
      console.error(`Failed to load messages for chat ${chatId}:`, error);
    } finally {
      isLoading.value = false;
    }
  }
  
  // 动作
  async function createNewChat() {
    // 检查用户是否已登录
    if (!authStore.isAuthenticated) {
      throw new Error('请先登录');
    }
    
    // 创建临时对话
    const tempId = 'temp_' + Date.now().toString();
    const newChat = {
      id: tempId,
      title: 'Untitled',
      isTemp: true
    }
    
    chatList.value.unshift(newChat)
    currentChatId.value = tempId
    chatMessages.value[tempId] = []
    
    return tempId
  }

  async function sendMessage(content) {
    // 检查用户是否已登录
    if (!authStore.isAuthenticated) {
      throw new Error('请先登录');
    }
    
    isLoading.value = true
    
    try {
      // 使用当前对话ID
      const sendChatId = currentChatId.value;
      
      // 将用户消息添加到当前对话
      if (!chatMessages.value[currentChatId.value]) {
        chatMessages.value[currentChatId.value] = [];
      }
      
      chatMessages.value[currentChatId.value].push({
        role: 'user',
        content
      });
      
      // 调用API发送消息
      const response = await getChatReply(sendChatId, content);
      
      // 处理API响应
      if (chatList.value.find(c => c.id === currentChatId.value)?.isTemp) {
        // 如果是临时对话，更新对话信息
        const index = chatList.value.findIndex(c => c.id === currentChatId.value);
        const newChatId = response.conversation_id;
        
        // 更新对话信息
        chatList.value[index] = {
          id: newChatId,
          title: content.length > 20 ? content.substring(0, 20) + '...' : content,
          isTemp: false
        };
        
        // 更新消息列表的键
        chatMessages.value[newChatId] = chatMessages.value[currentChatId.value];
        delete chatMessages.value[currentChatId.value];
        currentChatId.value = newChatId;
        
        console.log('对话已从临时ID转换为永久ID:', {
          oldId: currentChatId.value,
          newId: newChatId
        });
      }
      
      // 添加AI回复到消息列表
      chatMessages.value[currentChatId.value].push({
        role: 'assistant',
        content: response.reply
      });
      
      return response;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  function switchChat(chatId) {
    currentChatId.value = chatId
    // 加载该对话的消息历史
    loadChatMessages(chatId);
  }

  async function updateChatTitle(chatId, newTitle) {
    // 检查用户是否已登录
    if (!authStore.isAuthenticated) return;
    
    try {
      await apiUpdateChatTitle(chatId, newTitle);
      
      const index = chatList.value.findIndex(chat => chat.id === chatId)
      if (index !== -1) {
        chatList.value[index].title = newTitle
      }
    } catch (error) {
      console.error('Failed to update chat title:', error);
    }
  }
  
  async function deleteUserChat(chatId) {
    // 检查用户是否已登录
    if (!authStore.isAuthenticated) return;
    
    try {
      await deleteChat(chatId);
      
      const index = chatList.value.findIndex(chat => chat.id === chatId)
      if (index !== -1) {
        chatList.value.splice(index, 1)
        
        // 删除聊天记录
        delete chatMessages.value[chatId]
        
        // 如果删除的是当前聊天，切换到其他聊天
        if (currentChatId.value === chatId) {
          currentChatId.value = chatList.value.length > 0 ? chatList.value[0].id : null
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  }

  // 在用户登出时清空聊天数据
  function clearUserData() {
    chatList.value = [];
    currentChatId.value = null;
    chatMessages.value = {};
  }

  return {
    chatList,
    currentChatId,
    chatMessages,
    isLoading,
    currentChat,
    currentMessages,
    createNewChat,
    sendMessage,
    switchChat,
    updateChatTitle,
    deleteChat: deleteUserChat,
    initUserChats,
    loadChatMessages,
    clearUserData
  }
})
