<!-- 
聊天管理
功能：
1. 标记对话
2. 删除对话
3. 重命名对话 -->

<template>
  <div class="flex-grow overflow-y-auto p-2 scrollbar-thin">
    <TransitionGroup 
      name="chat-list" 
      tag="div"
      class="flex flex-col"
    >
      <div
        v-for="chat in chatStore.chatList"
        :key="chat.id"
        class="flex items-center justify-between px-4 py-2.5 mb-2 rounded-xl cursor-pointer transition-all duration-200 hover:bg-white/10 group"
        :class="{ 'bg-[#1677ff] hover:bg-[#1677ff]/60': chatStore.currentChatId === chat.id && $route.path === '/' }"
      >
        <div class="flex items-center flex-grow min-w-0" @click="chatStore.switchChat(chat.id); $router.push('/')">
          <MessageOutlined class="text-base mr-3 flex-shrink-0" />
          <span 
            v-if="!isCollapsed && editingChatId !== chat.id" 
            class="text-sm whitespace-nowrap overflow-hidden text-ellipsis"
          >
            {{ chat.title }}
          </span>
          <a-input
            v-if="!isCollapsed && editingChatId === chat.id"
            v-model:value="editTitle"
            size="small"
            class="w-full max-w-[160px]"
            ref="titleInputRef"
            @pressEnter="updateChatTitle(chat.id)"
            @blur="updateChatTitle(chat.id)"
          />
        </div>
        
        <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-200 ml-2" v-if="!isCollapsed">
          <a-dropdown trigger="click" placement="bottomRight">
            <a-button 
              type="text" 
              size="small"
              class="text-white/80 hover:text-white w-7 h-7 p-0 flex items-center justify-center hover:bg-white/10 hover:rounded"
            >
              <template #icon><MoreOutlined class="text-lg" rotate="90" /></template>
            </a-button>
            <template #overlay>
              <a-menu class="bg-[oklch(80.9%_0.105_251.813)]">
                <a-menu-item key="edit" @click="startEditing(chat.id, chat.title)">
                  <template #icon><EditOutlined /></template>
                  <span>编辑标题</span>
                </a-menu-item>
                <a-menu-item key="delete" @click="confirmDelete(chat.id)">
                  <template #icon><DeleteOutlined /></template>
                  <span>删除对话</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
    </TransitionGroup>
  </div>
  
  <a-modal
    v-model:visible="deleteModalVisible"
    title="删除对话？"
    ok-text="删除"
    cancel-text="取消"
    @ok="deleteConfirmed"
  >
    <p>确定要删除这个对话吗？</p>
  </a-modal>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  MessageOutlined, 
  EditOutlined, 
  DeleteOutlined,
  MoreOutlined
} from '@ant-design/icons-vue';
import { Menu, Dropdown, Button, Modal } from 'ant-design-vue';
import { useChatStore } from '../../stores/ChatStore.js';
import { TransitionGroup } from 'vue';

const router = useRouter();
const route = useRoute();
const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
});

const chatStore = useChatStore();
const editingChatId = ref(null);
const editTitle = ref('');
const titleInputRef = ref(null);
const deleteModalVisible = ref(false);
const chatToDelete = ref(null);

// 开始编辑聊天标题
const startEditing = async (chatId, title) => {
  editingChatId.value = chatId;
  editTitle.value = title;
  
  // 等待DOM更新后聚焦输入框
  await nextTick();
  titleInputRef.value?.focus();
};

// 更新聊天标题
const updateChatTitle = (chatId) => {
  if (editTitle.value.trim()) {
    chatStore.updateChatTitle(chatId, editTitle.value.trim());
  }
  editingChatId.value = null;
};

// 显示删除确认框
const confirmDelete = (chatId) => {
  chatToDelete.value = chatId;
  deleteModalVisible.value = true;
};

// 确认删除
const deleteConfirmed = () => {
  if (chatToDelete.value) {
    // 获取当前对话在列表中的索引
    const currentIndex = chatStore.chatList.findIndex(chat => chat.id === chatToDelete.value);
    const isCurrentChat = chatToDelete.value === chatStore.currentChatId;
    
    // 删除对话
    chatStore.deleteChat(chatToDelete.value);
    
    // 如果删除的是当前对话，并且路由在聊天页面
    if (isCurrentChat && route.path === '/') {
      // 如果对话列表还有对话，确保 route 显示前一个对话
      if (chatStore.chatList.length > 0) {
        // 导航不需要特殊处理，因为 ChatStore.deleteChat 已经会自动切换到其他对话
        // 但确保当前在聊天页面
        router.push('/');
      } else {
        //应该是一个欢迎页
        // 如果没有更多对话，可能需要导航到其他页面
        router.push('/settings');
      }
    }
    
    chatToDelete.value = null;
  }
  deleteModalVisible.value = false;
};
</script>

<style>
/* 一些复杂的动画和深度选择器样式仍然需要保留 */
@keyframes expand {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    max-height: 60px;
    transform: translateY(0);
  }
}

.chat-list-enter-active,
.chat-list-leave-active {
  transition: all 0.3s ease-out;
}

.chat-list-enter-from,
.chat-list-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.chat-list-move {
  transition: transform 0.3s ease-out;
}

:deep(.ant-dropdown-menu) {
  @apply min-w-[120px] p-1 bg-neutral-800 border border-white/10 rounded-lg;
}

:deep(.ant-dropdown-menu-item) {
  @apply px-3 py-2 text-white/85 rounded;
}

:deep(.ant-dropdown-menu-item:hover) {
  @apply bg-white/10 text-white;
}

:deep(.ant-dropdown-menu-item .anticon) {
  @apply text-base;
}

:deep(.ant-btn-text) {
  @apply text-white/80;
}

:deep(.ant-btn-text:hover) {
  @apply text-white bg-white/10;
}

:deep(.ant-menu-item .anticon) {
  @apply text-white/85;
}

:deep(.ant-menu-item:hover .anticon) {
  @apply text-white;
}
</style>
