import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createChat, getChatReply } from '../api/chat'

// 记得去App那里注册一下

export const useChatStore = defineStore('chat', () => {
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
  
  // 动作
  function createNewChat() {
    // 创建临时对话
    const tempId = Date.now() //改成uuid
    const newChat = {
      id: tempId,
      title: 'Untitled',
      isTemp: true
    }
    
    chatList.value.unshift(newChat)  // 使用 unshift 替代 push，将新对话添加到数组开头
    currentChatId.value = tempId
    chatMessages.value[tempId] = []
    
    return tempId
  }

  async function sendMessage(content) {
    isLoading.value = true
    
    try {
      // 将用户消息添加到当前对话
      chatMessages.value[currentChatId.value].push({
        role: 'user',
        content
      })
      
      // 调用API发送消息
      const response = await getChatReply(currentChatId.value, content)
      
      // 处理API响应
      if (chatList.value.find(c => c.id === currentChatId.value)?.isTemp) {
        // 如果是临时对话，更新对话信息
        const index = chatList.value.findIndex(c => c.id === currentChatId.value)
        chatList.value[index] = {
          id: response.chatId,
          title: response.chatSummary,
          isTemp: false
        }
        
        // 更新消息列表的键
        chatMessages.value[response.chatId] = chatMessages.value[currentChatId.value]
        delete chatMessages.value[currentChatId.value]
        currentChatId.value = response.chatId
      }
      
      // 添加AI回复到消息列表
      chatMessages.value[currentChatId.value].push({
        role: 'assistant',
        content: response.reply
      })
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      isLoading.value = false
    }
  }

  function switchChat(chatId) {
    currentChatId.value = chatId
  }


  function updateChatTitle(chatId, newTitle) {
    const index = chatList.value.findIndex(chat => chat.id === chatId)
    if (index !== -1) {
      chatList.value[index].title = newTitle
      
      // 实际项目中这里会调用API
      // await updateChat(chatId, { title: newTitle })
    }
  }
  
  function deleteChat(chatId) {
    const index = chatList.value.findIndex(chat => chat.id === chatId)
    
    if (index !== -1) {
      chatList.value.splice(index, 1)
      
      // 删除聊天记录
      delete chatMessages.value[chatId]
      
      // 如果删除的是当前聊天，切换到其他聊天
      if (currentChatId.value === chatId) {
        currentChatId.value = chatList.value.length > 0 ? chatList.value[0].id : null
      }
      
      // 实际项目中这里会调用API
      // await deleteChat(chatId)
    }
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
    deleteChat
  }
})
