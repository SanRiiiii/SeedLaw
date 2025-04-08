<!-- 
聊天管理
功能：
1. 标记对话
2. 删除对话
3. 重命名对话 -->

<template>
  <div class="chat-list">
    <div
      v-for="chat in chatStore.chatList"
      :key="chat.id"
      class="chat-item"
      :class="{ 'active': chatStore.currentChatId === chat.id }"
    >
      <div class="chat-content" @click="chatStore.switchChat(chat.id)">
        <MessageOutlined class="chat-icon" />
        <span 
          v-if="!isCollapsed && editingChatId !== chat.id" 
          class="chat-title"
        >
          {{ chat.title }}
        </span>
        <a-input
          v-if="!isCollapsed && editingChatId === chat.id"
          v-model:value="editTitle"
          size="small"
          class="title-input"
          ref="titleInputRef"
          @pressEnter="updateChatTitle(chat.id)"
          @blur="updateChatTitle(chat.id)"
        />
      </div>
      
      <div class="chat-actions" v-if="!isCollapsed">
        <a-dropdown :trigger="['click']" @click.stop>
          <a-button 
            type="text" 
            size="small"
            class="more-btn"
            @click.stop
          >
            <template #icon><EllipsisOutlined /></template>
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item @click.stop="startEditing(chat.id, chat.title)">
                <template #icon><EditOutlined /></template>
                编辑标题
              </a-menu-item>
              <a-menu-item @click.stop="confirmDelete(chat.id)">
                <template #icon><DeleteOutlined /></template>
                删除对话
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
  </div>
  
  <!-- 删除确认对话框 -->
  <a-modal
    v-model:visible="deleteModalVisible"
    title="删除确认"
    ok-text="删除"
    cancel-text="取消"
    @ok="deleteConfirmed"
  >
    <p>确定要删除这个对话吗？</p>
  </a-modal>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { 
  MessageOutlined, 
  EditOutlined, 
  DeleteOutlined,
  EllipsisOutlined
} from '@ant-design/icons-vue';
import { useChatStore } from '../../stores/ChatStore.js';

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
    chatStore.deleteChat(chatToDelete.value);
    chatToDelete.value = null;
  }
  deleteModalVisible.value = false;
};
</script>

<style scoped>
.chat-list {
  flex-grow: 1;
  overflow-y: auto;
  padding: 8px;
  scrollbar-width: thin;
}

.chat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.chat-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.chat-item.active {
  background-color: #1890ff;
}

.chat-content {
  display: flex;
  align-items: center;
  flex-grow: 1;
  min-width: 0;
}

.chat-icon {
  font-size: 16px;
  margin-right: 12px;
  flex-shrink: 0;
}

.chat-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.title-input {
  width: 100%;
  max-width: 160px;
}

.chat-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.chat-item:hover .chat-actions {
  opacity: 1;
}

:deep(.ant-btn-text) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.ant-btn-text:hover) {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
}

.more-btn {
  padding: 4px;
  height: auto;
}
</style>
