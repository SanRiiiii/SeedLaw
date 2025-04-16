<template>
  <div class="flex flex-col">
    <Sender
      v-model:value="inputContent"
      :loading="disabled"
      :auto-size="{ minRows: 1, maxRows: 4 }"
      placeholder="输入消息，按Enter发送，Shift+Enter换行"
      @submit="handleSend"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Sender } from 'ant-design-x-vue';

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