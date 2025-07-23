import axios from 'axios';
import { API_BASE_URL } from './config';

// 创建axios实例
const authApi = axios.create({
  baseURL: API_BASE_URL
});

/**
 * 用户登录
 * @param {string} email 邮箱
 * @param {string} password 密码
 * @returns {Promise<Object>} 用户信息和token
 */
export async function login(email, password) {
      // 创建一个表单数据对象
  const formData = new URLSearchParams();
  formData.append('username', email);  // OAuth2 表单期望的是 username 字段
  formData.append('password', password);
  try {
    const response = await authApi.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  } catch (error) {
    console.error('完整错误:', error);
    console.error('错误详情:', error.response?.data);
    throw error;
  }
}

/**
 * 用户注册
 * @param {string} email 邮箱
 * @param {string} password 密码
 * @returns {Promise<Object>} 用户信息和token
 */
export async function register(email, password) {
  const response = await authApi.post('/auth/register', {
    email,
    password
  });
  return response.data;
}

/**
 * 获取当前用户信息
 * @returns {Promise<Object>} 用户信息
 */
export async function getCurrentUser() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    return null;
  }
  
  try {
    const response = await authApi.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    localStorage.removeItem('auth_token');
    return null;
  }
}

/**
 * 退出登录
 */
export async function logout() {
  localStorage.removeItem('auth_token');
} 