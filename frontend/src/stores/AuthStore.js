import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { login as apiLogin, register as apiRegister, getCurrentUser, logout as apiLogout } from '../api/auth';
import { message } from 'ant-design-vue';

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null);
  const token = ref(localStorage.getItem('auth_token') || null);
  const loading = ref(false);
  const showLoginModal = ref(false);
  
  // 计算属性
  const isAuthenticated = computed(() => !!user.value);
  const userDisplayName = computed(() => user.value?.username || '');
  
  // 登录模态框控制
  function openLoginModal() {
    showLoginModal.value = true;
  }
  
  function closeLoginModal() {
    showLoginModal.value = false;
  }
  
  // 初始化方法 - 在应用启动时调用
  async function init() {
    if (token.value) {
      loading.value = true;
      try {
        user.value = await getCurrentUser();
      } catch (error) {
        console.error('Failed to get user info:', error);
        user.value = null;
        token.value = null;
        localStorage.removeItem('auth_token');
      } finally {
        loading.value = false;
      }
    }
  }
  
  // 登录方法
  async function login(username, password) {
    loading.value = true;
    try {
      const response = await apiLogin(username, password);
      user.value = response.user;
      token.value = response.token;
      localStorage.setItem('auth_token', response.token);
      message.success('登录成功');
      closeLoginModal();
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      const errorMsg = error.response?.data?.message || '登录失败，请检查用户名和密码';
      message.error(errorMsg);
      throw error;
    } finally {
      loading.value = false;
    }
  }
  
  // 注册方法
  async function register(username, password) {
    loading.value = true;
    try {
      const response = await apiRegister(username, password);
      user.value = response.user;
      token.value = response.token;
      localStorage.setItem('auth_token', response.token);
      message.success('注册成功');
      closeLoginModal();
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      const errorMsg = error.response?.data?.message || '注册失败，请稍后再试';
      message.error(errorMsg);
      throw error;
    } finally {
      loading.value = false;
    }
  }
  
  // 退出登录方法
  async function logout() {
    user.value = null;
    token.value = null;
    apiLogout();
    message.success('已退出登录');
  }
  
  return {
    user,
    token,
    loading,
    isAuthenticated,
    userDisplayName,
    showLoginModal,
    openLoginModal,
    closeLoginModal,
    init,
    login,
    register,
    logout
  };
}); 