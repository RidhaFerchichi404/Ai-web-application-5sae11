export interface Conversation {
  id: number;
  title: string;
  chat_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface ModelInfo {
  models: string[];
  chat_model: string;
  embedding_model: string;
  chat_model_installed: boolean;
  embedding_model_installed: boolean;
}

export interface ChatChunk {
  content?: string;
  done?: boolean;
  error?: { code: string; message: string };
}
