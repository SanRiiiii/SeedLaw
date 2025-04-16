import axios from 'axios';
import { API_BASE_URL } from './config';

// 创建axios实例
const authApi = axios.create({
  baseURL: API_BASE_URL
});

/**
 * 用户登录
 * @param {string} username 用户名
 * @param {string} password 密码
 * @returns {Promise<Object>} 用户信息和token
 */
export async function login(username, password) {
  const response = await authApi.post('/auth/login', {
    username,
    password
  });
  return response.data;
}

/**
 * 用户注册
 * @param {string} username 用户名
 * @param {string} password 密码
 * @returns {Promise<Object>} 用户信息和token
 */
export async function register(username, password) {
  const response = await authApi.post('/auth/register', {
    username,
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