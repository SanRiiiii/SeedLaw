import axios from 'axios';
import { API_BASE_URL } from './config';

// 创建axios实例
const chatApi = axios.create({
  baseURL: API_BASE_URL
});

// 请求拦截器，添加认证token
chatApi.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 模拟API调用的延迟（开发阶段使用）
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 创建新对话
export async function createChat() {
  // 使用实际的API调用
  try {
    const response = await chatApi.post('/chats');
    return response.data;
  } catch (error) {
    console.error('Failed to create chat:', error);
    throw error;
  }
  
  // 开发阶段可以使用模拟数据
  // await delay(500);
  // return {
  //   chatId: 'chat_' + Date.now(),
  //   chatSummary: '新对话'
  // };
}

// 获取对话回复
export async function getChatReply(chatId, content) {
  // 使用实际的API调用
  try {
    const response = await chatApi.post(`/chats/${chatId}/messages`, { content });
    return response.data;
  } catch (error) {
    console.error('Failed to get chat reply:', error);
    throw error;
  }
  
  // 开发阶段可以使用模拟数据
  // await delay(1000);
  // return {
  //   chatId: chatId.toString().startsWith('chat_') ? chatId : 'chat_' + Date.now(),
  //   chatSummary: content.length > 20 ? content.substring(0, 20) + '...' : content,
  //   reply: `这是对"${content}"的模拟回复。在实际项目中，这里会是来自AI的回答。`
  // };
}

// 获取用户的对话列表
export async function getChatList() {
  try {
    const response = await chatApi.get('/chats');
    return response.data;
  } catch (error) {
    console.error('Failed to get chat list:', error);
    throw error;
  }
}

// 获取特定对话的消息历史
export async function getChatHistory(chatId) {
  try {
    const response = await chatApi.get(`/chats/${chatId}/messages`);
    return response.data;
  } catch (error) {
    console.error('Failed to get chat history:', error);
    throw error;
  }
}

// 删除对话
export async function deleteChat(chatId) {
  try {
    const response = await chatApi.delete(`/chats/${chatId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete chat:', error);
    throw error;
  }
}
