export interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  type: 'case' | 'law' | 'regulation';
}

export interface SuggestionItem {
  id: string;
  text: string;
  icon?: string;
} 