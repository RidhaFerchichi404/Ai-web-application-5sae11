'use client';

import { useRouter } from 'next/navigation';
import { PlusIcon } from 'lucide-react';
import { createConversation } from '@/lib/api';

export default function ChatIndex() {
  const router = useRouter();

  async function handleNew() {
    try {
      const conv = await createConversation();
      router.push(`/chat/${conv.id}`);
    } catch {}
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        color: 'var(--text-muted)',
      }}
    >
      <p style={{ fontSize: 15 }}>Select a conversation or start a new one.</p>
      <button
        onClick={handleNew}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--accent)',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          padding: '9px 18px',
          fontSize: 14,
          cursor: 'pointer',
          fontWeight: 500,
        }}
      >
        <PlusIcon size={16} />
        New conversation
      </button>
    </div>
  );
}
