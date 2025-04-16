// ChatStore类型定义
import { Ref, ComputedRef } from 'vue'

interface Chat {
  id: string | number;
  title: string;
  isTemp?: boolean;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatStore {
  chatList: Ref<Chat[]>;
  currentChatId: Ref<string | number | null>;
  chatMessages: Ref<Record<string | number, Message[]>>;
  isLoading: Ref<boolean>;
  currentChat: ComputedRef<Chat | undefined>;
  currentMessages: ComputedRef<Message[]>;
  
  createNewChat: () => number;
  sendMessage: (content: string) => Promise<void>;
  switchChat: (chatId: string | number) => void;
  updateChatTitle: (chatId: string | number, newTitle: string) => void;
  deleteChat: (chatId: string | number) => void;
}

export declare function useChatStore(): ChatStore; 