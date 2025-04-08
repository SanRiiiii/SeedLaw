<template>
  <div class="chat-input">
    <a-textarea
      v-model:value="inputContent"
      placeholder="输入消息，Ctrl + Enter 发送"
      :disabled="disabled"
      :auto-size="{ minRows: 1, maxRows: 4 }"
      class="message-textarea"
      @keydown.ctrl.enter="handleSend"
    />
    <div class="input-actions">
      <!-- 这里可以添加附加功能按钮，如表情、图片上传等 -->
      <a-button 
        type="primary" 
        :disabled="!inputContent.trim() || disabled"
        @click="handleSend"
        class="send-button"
      >
        <template #icon><SendOutlined /></template>
        发送
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { SendOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['send']);

const inputContent = ref('');

const handleSend = () => {
  if (inputContent.value.trim() && !props.disabled) {
    emit('send', inputContent.value);
    inputContent.value = '';
  }
};
</script>

<style scoped>
.chat-input {
  display: flex;
  flex-direction: column;
}

.message-textarea {
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #d9d9d9;
  resize: none;
  transition: all 0.3s;
}

.message-textarea:focus {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.send-button {
  display: flex;
  align-items: center;
}
</style> 