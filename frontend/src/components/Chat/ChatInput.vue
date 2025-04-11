<template>
  <div class="flex flex-col">
    <div class="flex gap-2 items-end">
      <a-textarea
        v-model:value="inputContent"
        placeholder="输入消息，按Enter发送，Shift+Enter换行"
        :disabled="disabled"
        :auto-size="{ minRows: 1, maxRows: 4 }"
        class="flex-1 max-w-[calc(100%-80px)] rounded-lg px-3 py-2 text-sm border border-gray-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-200 transition-all duration-300 resize-none"
        @keydown.enter="handleKeyDown"
      />
      <a-button 
        type="primary" 
        :disabled="!inputContent.trim() || disabled"
        @click="handleSend"
        class="h-8 flex items-center"
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

// 处理键盘事件
const handleKeyDown = (e) => {
  // 如果按下Shift+Enter，允许换行
  if (e.shiftKey) {
    return;
  }
  // 如果只按下Enter，阻止默认行为并发送消息
  e.preventDefault();
  handleSend();
};
</script> 