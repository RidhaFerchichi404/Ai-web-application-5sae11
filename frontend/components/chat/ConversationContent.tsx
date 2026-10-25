'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import MessageBubble from '@/components/chat/MessageBubble';
import Composer from '@/components/chat/Composer';
import { listMessages, getConversation, getModels, streamChat } from '@/lib/api';
import type { Message, Conversation } from '@/lib/types';

interface StreamMessage extends Message {
  streaming?: boolean;
}

export default function ConversationContent() {
  const { id } = useParams<{ id: string }>();
  const conversationId = parseInt(id, 10);

  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (!conversationId) return;
    setError(null);
    setMessages([]);
    Promise.all([
      listMessages(conversationId).catch(() => [] as Message[]),
      getConversation(conversationId).catch(() => null),
      getModels().catch(() => null),
    ]).then(([msgs, conv, modelInfo]) => {
      setMessages(msgs);
      setConversation(conv);
      if (modelInfo) {
        setModels(modelInfo.models);
        setCurrentModel(conv?.chat_model ?? modelInfo.chat_model);
      }
      setTimeout(scrollToBottom, 50);
    });
  }, [conversationId, scrollToBottom]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  async function handleSend(text: string, model: string | null) {
    const userMsg: StreamMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    const assistantMsg: StreamMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      streaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);
    setError(null);
    if (model) setCurrentModel(model);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      for await (const chunk of streamChat(conversationId, text, model, controller.signal)) {
        if (chunk.error) {
          setError(chunk.error.message);
          break;
        }
        const delta = chunk.content ?? '';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: m.content + delta, streaming: !chunk.done }
              : m
          )
        );
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsg.id ? { ...m, streaming: false } : m))
      );
    }
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div
        style={{
          padding: '10px 20px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg)',
          flexShrink: 0,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--text)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {conversation?.title ?? 'Conversation'}
        </h1>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
        }}
      >
        {messages.length === 0 && !streaming && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              fontSize: 14,
            }}
          >
            Start the conversation below.
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {error && (
          <div
            style={{
              background: 'rgba(239,68,68,0.15)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              color: '#fca5a5',
            }}
          >
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <Composer
        onSend={handleSend}
        streaming={streaming}
        onStop={handleStop}
        models={models}
        currentModel={currentModel}
      />
    </div>
  );
}
