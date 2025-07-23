<template>
  <a-modal
    :visible="visible"
    :title="isLogin ? '登录' : '注册'"
    @cancel="handleCancel"
    :footer="null"
    width="400px"
  >
    <div class="auth-container">
      <a-form
        :model="formData"
        @finish="handleSubmit"
        layout="vertical"
      >
        <a-form-item
          label="邮箱"
          name="email"
          :rules="[{ required: true, message: '请输入邮箱' }]"
        >
          <a-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </a-form-item>
        
        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model:value="formData.password" placeholder="请输入密码" />
        </a-form-item>
        
        <a-form-item v-if="!isLogin" label="确认密码" name="confirmPassword" :rules="[
          { required: true, message: '请确认密码' },
          { validator: validateConfirmPassword }
        ]">
          <a-input-password v-model:value="formData.confirmPassword" placeholder="请再次输入密码" />
        </a-form-item>
        
        <div class="form-actions">
          <a-button type="primary" html-type="submit" :loading="loading" block>
            {{ isLogin ? '登录' : '注册' }}
          </a-button>
        </div>
        
        <div class="form-footer">
          <a @click="toggleAuthMode">{{ isLogin ? '没有账号？去注册' : '已有账号？去登录' }}</a>
        </div>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useAuthStore } from '../../stores/AuthStore';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:visible', 'success']);

const authStore = useAuthStore();
const isLogin = ref(true);
const loading = ref(false);

const formData = ref({
  email: '',
  password: '',
  confirmPassword: ''
});

// 监听visible变化，当关闭时重置表单
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetForm();
  }
});

// 重置表单
const resetForm = () => {
  formData.value = {
    email: '',
    password: '',
    confirmPassword: ''
  };
  isLogin.value = true;
};

// 验证确认密码
const validateConfirmPassword = async (rule, value) => {
  if (value !== formData.value.password) {
    return Promise.reject('两次密码输入不一致');
  }
  return Promise.resolve();
};

// 切换登录/注册模式
const toggleAuthMode = () => {
  isLogin.value = !isLogin.value;
  formData.value = {
    email: '',
    password: '',
    confirmPassword: ''
  };
};

// 处理表单提交
const handleSubmit = async () => {
  loading.value = true;
  try {
    if (isLogin.value) {
      await authStore.login(formData.value.email, formData.value.password);
    } else {
      await authStore.register(formData.value.email, formData.value.password);
    }
    // 这里不需要手动关闭模态框，登录/注册成功后AuthStore会自动关闭
    emit('success');
  } catch (error) {
    console.error('Auth error:', error);
  } finally {
    loading.value = false;
  }
};

// 取消按钮处理
const handleCancel = () => {
  emit('update:visible', false);
  authStore.closeLoginModal(); // 同步更新AuthStore中的状态
};
</script>

<style scoped>
.auth-container {
  padding: 10px;
}

.form-actions {
  margin-top: 24px;
}

.form-footer {
  margin-top: 16px;
  text-align: center;
}
</style> 