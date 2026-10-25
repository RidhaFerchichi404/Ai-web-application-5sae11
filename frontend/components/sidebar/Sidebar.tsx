'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { PlusIcon, SearchIcon, Trash2Icon } from 'lucide-react';
import type { Conversation } from '@/lib/types';
import { listConversations, createConversation, deleteConversation } from '@/lib/api';

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [nowMs, setNowMs] = useState<number>(0);

  const activeId = pathname.startsWith('/chat/')
    ? parseInt(pathname.split('/chat/')[1], 10)
    : null;

  const load = useCallback(async (q?: string) => {
    try {
      const data = await listConversations(q);
      setConversations(data);
    } catch {}
  }, []);

  useEffect(() => {
    setNowMs(Date.now());
    load().finally(() => setLoading(false));
  }, [load, pathname]);

  useEffect(() => {
    const id = setTimeout(() => load(search || undefined), 200);
    return () => clearTimeout(id);
  }, [search, load]);

  async function handleNew() {
    try {
      const conv = await createConversation();
      router.push(`/chat/${conv.id}`);
    } catch {}
  }

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.preventDefault();
    e.stopPropagation();
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) router.push('/chat');
    } catch {}
  }

  const grouped = nowMs ? groupByDate(conversations, nowMs) : {};

  return (
    <aside
      style={{
        width: 240,
        minWidth: 240,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '14px 12px 8px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14, flex: 1, color: 'var(--text)' }}>
          AI Assistant
        </span>
        <button
          onClick={handleNew}
          title="New conversation"
          style={{
            background: 'var(--accent)',
            border: 'none',
            borderRadius: 6,
            padding: '4px 8px',
            cursor: 'pointer',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
          }}
        >
          <PlusIcon size={14} />
          New
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: '8px 12px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'var(--surface-2)',
            borderRadius: 6,
            padding: '5px 8px',
          }}
        >
          <SearchIcon size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text)',
              fontSize: 13,
              width: '100%',
            }}
          />
        </div>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 4px 8px' }}>
        {loading && (
          <p style={{ color: 'var(--text-muted)', fontSize: 12, padding: '8px 8px' }}>
            Loading…
          </p>
        )}
        {!loading && conversations.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: 12, padding: '8px 8px' }}>
            No conversations yet
          </p>
        )}
        {Object.entries(grouped).map(([label, items]) => (
          <div key={label}>
            <p
              style={{
                fontSize: 11,
                color: 'var(--text-muted)',
                padding: '8px 8px 2px',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {label}
            </p>
            {items.map((c) => (
              <ConvItem
                key={c.id}
                conv={c}
                active={c.id === activeId}
                onSelect={() => router.push(`/chat/${c.id}`)}
                onDelete={(e) => handleDelete(e, c.id)}
              />
            ))}
          </div>
        ))}
      </div>
    </aside>
  );
}

function ConvItem({
  conv,
  active,
  onSelect,
  onDelete,
}: {
  conv: Conversation;
  active: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '6px 8px',
        borderRadius: 6,
        cursor: 'pointer',
        background: active ? 'var(--surface-2)' : hovered ? 'rgba(255,255,255,0.04)' : 'transparent',
        gap: 6,
      }}
    >
      <span
        style={{
          flex: 1,
          fontSize: 13,
          color: active ? 'var(--text)' : 'var(--text-muted)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {conv.title}
      </span>
      {hovered && (
        <button
          onClick={onDelete}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: 2,
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            borderRadius: 4,
            flexShrink: 0,
          }}
        >
          <Trash2Icon size={13} />
        </button>
      )}
    </div>
  );
}

function groupByDate(conversations: Conversation[], nowMs: number): Record<string, Conversation[]> {
  const now = new Date(nowMs);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;
  const weekAgo = today - 7 * 86400000;

  const groups: Record<string, Conversation[]> = {};

  for (const c of conversations) {
    const t = new Date(c.updated_at).getTime();
    let label: string;
    if (t >= today) label = 'Today';
    else if (t >= yesterday) label = 'Yesterday';
    else if (t >= weekAgo) label = 'This week';
    else label = 'Earlier';

    if (!groups[label]) groups[label] = [];
    groups[label].push(c);
  }

  return groups;
}
