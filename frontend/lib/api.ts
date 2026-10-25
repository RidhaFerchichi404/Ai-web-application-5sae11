import type { Conversation, Message, ModelInfo, ChatChunk } from './types';

const API_URL =
  (typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_API_URL : process.env.API_URL) ||
  'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.error?.message ?? msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function getModels(): Promise<ModelInfo> {
  return request('/api/models');
}

export async function listConversations(q?: string): Promise<Conversation[]> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : '';
  return request(`/api/conversations${qs}`);
}

export async function createConversation(
  title?: string,
  chat_model?: string
): Promise<Conversation> {
  return request('/api/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || undefined, chat_model: chat_model || undefined }),
  });
}

export async function getConversation(id: number): Promise<Conversation> {
  return request(`/api/conversations/${id}`);
}

export async function updateConversation(
  id: number,
  patch: { title?: string; chat_model?: string }
): Promise<Conversation> {
  return request(`/api/conversations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
}

export async function deleteConversation(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/conversations/${id}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`);
}

export async function listMessages(conversationId: number): Promise<Message[]> {
  return request(`/api/conversations/${conversationId}/messages`);
}

export async function* streamChat(
  conversationId: number,
  message: string,
  model: string | null,
  signal: AbortSignal
): AsyncGenerator<ChatChunk> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      model: model || undefined,
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.error?.message ?? msg;
    } catch {}
    throw new Error(msg);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop() ?? '';
      for (const line of lines) {
        if (line.trim()) yield JSON.parse(line) as ChatChunk;
      }
    }
    if (buf.trim()) yield JSON.parse(buf) as ChatChunk;
  } finally {
    reader.releaseLock();
  }
}
