import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { login as apiLogin, register as apiRegister, getCurrentUser, logout as apiLogout } from '../api/auth';
import { message } from 'ant-design-vue';
const { useChatStore } = await import('./ChatStore');

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null);
  const token = ref(localStorage.getItem('auth_token') || null);
  const loading = ref(false);
  const showLoginModal = ref(false);
  
  // 计算属性
  const isAuthenticated = computed(() => !!user.value);
  const userDisplayName = computed(() => user.value?.email || '');
  
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
        
        // 获取用户信息成功后，初始化聊天记录
        const chatStore = useChatStore();
        await chatStore.initUserChats();
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
  async function login(email, password) {
    loading.value = true;
    try {
      const response = await apiLogin(email, password);
      console.log('Login API response:', response);
      
      user.value = response.user;
      token.value = response.access_token;
      localStorage.setItem('auth_token', token.value);
      
      console.log('Auth state after login:', { 
        user: user.value, 
        token: token.value,
        isAuthenticated: isAuthenticated.value 
      });
      
      message.success('登录成功');
      closeLoginModal();
      
      // 登录成功后初始化聊天记录
      const chatStore = useChatStore();
      await chatStore.initUserChats();
      
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      const errorMsg = error.response?.data?.message || '登录失败，请检查邮箱和密码';
      message.error(errorMsg);
      throw error;
    } finally {
      loading.value = false;
    }
  }
  
  // 注册方法
  async function register(email, password) {
    loading.value = true;
    try {
      const response = await apiRegister(email, password);
      if (response.is_registered) {
        message.success('注册成功');
        closeLoginModal();}
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
    localStorage.removeItem('auth_token');
    apiLogout();
    
    // 清空聊天数据
    const chatStore = useChatStore();
    chatStore.clearUserData();
    
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