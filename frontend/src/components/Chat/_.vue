<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { SuggestionItem } from '../../types';

const inputValue = ref('');
const activeTab = ref('问问题');

const suggestions = ref<SuggestionItem[]>([
  { id: '1', text: '建设工程价款优先受偿权的权利主体如何认定' },
  { id: '2', text: '好评返现是否属于不正当竞争行为' },
  { id: '3', text: '被单位无正当理由辞退，可以主张哪些赔偿' },
  { id: '4', text: '股东有权查阅公司文件材料的范围' }
]);

const sendMessage = () => {
  if (!inputValue.value.trim()) return;
  // Handle sending the message
  inputValue.value = '';
};

const useSuggestion = (text: string) => {
  inputValue.value = text;
};

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- Header -->
    <div class="p-8 text-center">
      <h1 class="text-2xl font-medium">你好，我是法智</h1>
    </div>
    
    <!-- Tab navigation -->
    <div class="flex justify-center mb-6">
      <div class="bg-white rounded-lg shadow-sm overflow-hidden flex">
        <button 
          class="px-6 py-2 text-sm font-medium"
          :class="activeTab === '问问题' ? 'bg-blue-900 text-white' : 'text-gray-700'"
          @click="activeTab = '问问题'"
        >
          问问题
        </button>
        <button 
          class="px-6 py-2 text-sm font-medium"
          :class="activeTab === '找类案' ? 'bg-blue-900 text-white' : 'text-gray-700'"
          @click="activeTab = '找类案'"
        >
          找类案
        </button>
        <button 
          class="px-6 py-2 text-sm font-medium"
          :class="activeTab === '查法规' ? 'bg-blue-900 text-white' : 'text-gray-700'"
          @click="activeTab = '查法规'"
        >
          查法规
        </button>
      </div>
    </div>
    
    <!-- Suggestions -->
    <div class="px-20 mb-4">
      <div class="text-sm text-gray-500 mb-2">试试这样问</div>
      <div class="grid grid-cols-2 gap-2">
        <div 
          v-for="suggestion in suggestions" 
          :key="suggestion.id"
          class="bg-white p-3 rounded-lg flex items-center cursor-pointer hover:bg-gray-50"
          @click="useSuggestion(suggestion.text)"
        >
          <el-icon class="mr-2 text-blue-500"><ChatLineRound /></el-icon>
          <span class="text-sm">{{ suggestion.text }}</span>
        </div>
      </div>
    </div>
    
    <!-- Input area -->
    <div class="px-20 mt-auto mb-10">
      <div class="relative bg-white rounded-lg shadow-sm">
        <textarea 
          v-model="inputValue"
          placeholder="请输入您的问题，支持 Shift + Enter 换行"
          class="w-full p-4 outline-none resize-none rounded-lg"
          rows="3"
          @keydown="handleKeyDown"
        ></textarea>
        <div class="absolute right-3 bottom-3 flex items-center">
          <el-icon class="text-gray-400 p-2 hover:text-blue-500 cursor-pointer"><UploadFilled /></el-icon>
          <el-button 
            type="primary" 
            :icon="inputValue.trim() ? 'el-icon-s-promotion' : ''" 
            circle
            @click="sendMessage"
            :disabled="!inputValue.trim()"
          >
            <el-icon><Position /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="text-xs text-gray-400 mt-1 text-center">
        内容由法大大机器生成，请仔细甄别
        <span class="text-gray-300 mx-2">·</span>
        <span>浙ICP备10056399号-35</span>
        <span class="text-gray-300 mx-2">·</span>
        <span>浙江网亿网络科技有限公司版权所有</span>
      </div>
    </div>
  </div>
</template> 