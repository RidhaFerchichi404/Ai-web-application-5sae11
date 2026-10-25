'use client';

import { useState, useRef, useEffect } from 'react';
import { SendIcon, SquareIcon, ChevronDownIcon } from 'lucide-react';

interface ComposerProps {
  onSend: (message: string, model: string | null) => void;
  streaming: boolean;
  onStop: () => void;
  models: string[];
  currentModel: string | null;
}

export default function Composer({ onSend, streaming, onStop, models, currentModel }: ComposerProps) {
  const [text, setText] = useState('');
  const [model, setModel] = useState<string | null>(currentModel);
  const [showModels, setShowModels] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!streaming) textareaRef.current?.focus();
  }, [streaming]);

  useEffect(() => {
    setModel(currentModel);
  }, [currentModel]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const msg = text.trim();
    if (!msg || streaming) return;
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    onSend(msg, model);
  }

  const displayModel = model ?? (models[0] || null);

  return (
    <div
      style={{
        borderTop: '1px solid var(--border)',
        padding: '12px 16px',
        background: 'var(--bg)',
      }}
    >
      {/* Model selector row */}
      {models.length > 0 && (
        <div style={{ marginBottom: 8, position: 'relative', display: 'inline-block' }}>
          <button
            onClick={() => setShowModels(!showModels)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '3px 8px',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              fontSize: 12,
            }}
          >
            {displayModel ?? 'No model'}
            <ChevronDownIcon size={12} />
          </button>
          {showModels && (
            <div
              style={{
                position: 'absolute',
                bottom: '110%',
                left: 0,
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: 4,
                minWidth: 200,
                zIndex: 10,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              }}
            >
              {models.map((m) => (
                <button
                  key={m}
                  onClick={() => { setModel(m); setShowModels(false); }}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    background: m === displayModel ? 'var(--surface-2)' : 'transparent',
                    border: 'none',
                    borderRadius: 6,
                    padding: '6px 10px',
                    cursor: 'pointer',
                    color: 'var(--text)',
                    fontSize: 13,
                  }}
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Input row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 10,
          background: 'var(--surface)',
          borderRadius: 12,
          padding: '8px 12px',
          border: '1px solid var(--border)',
        }}
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => { setText(e.target.value); autoResize(); }}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything…"
          disabled={streaming}
          rows={1}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--text)',
            fontSize: 14,
            resize: 'none',
            lineHeight: 1.6,
            fontFamily: 'inherit',
            overflowY: 'auto',
          }}
        />
        {streaming ? (
          <button
            onClick={onStop}
            title="Stop generation"
            style={{
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '6px 10px',
              cursor: 'pointer',
              color: 'var(--text)',
              display: 'flex',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <SquareIcon size={15} />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!text.trim()}
            title="Send"
            style={{
              background: text.trim() ? 'var(--accent)' : 'var(--surface-2)',
              border: 'none',
              borderRadius: 8,
              padding: '6px 10px',
              cursor: text.trim() ? 'pointer' : 'default',
              color: text.trim() ? '#fff' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              flexShrink: 0,
              transition: 'background 0.15s',
            }}
          >
            <SendIcon size={15} />
          </button>
        )}
      </div>
    </div>
  );
}
