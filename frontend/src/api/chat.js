import axios from 'axios';

// 模拟API调用的延迟
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 创建新对话
export async function createChat() {
  // 实际项目中会调用后端API
  // return axios.post('/api/chats');
  
  // 模拟API响应
  await delay(500);
  return {
    chatId: 'chat_' + Date.now(),
    chatSummary: '新对话'
  };
}

// 获取对话回复
export async function getChatReply(chatId, content) {
  // 实际项目中会调用后端API
  // return axios.post(`/api/chats/${chatId}/messages`, { content });
  
  // 模拟API响应
  await delay(1000);
  return {
    chatId: chatId.toString().startsWith('chat_') ? chatId : 'chat_' + Date.now(),
    chatSummary: content.length > 20 ? content.substring(0, 20) + '...' : content,
    reply: `这是对"${content}"的模拟回复。在实际项目中，这里会是来自AI的回答。`
  };
}
