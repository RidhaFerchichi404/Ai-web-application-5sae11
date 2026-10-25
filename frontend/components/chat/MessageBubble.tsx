'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CopyIcon, CheckIcon } from 'lucide-react';
import { useState } from 'react';
import type { Message } from '@/lib/types';

export default function MessageBubble({ message }: { message: Message & { streaming?: boolean } }) {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        padding: '4px 0',
      }}
    >
      <div
        style={{
          maxWidth: '80%',
          background: isUser ? 'var(--accent)' : 'var(--surface)',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          padding: '10px 14px',
          color: 'var(--text)',
          position: 'relative',
        }}
      >
        {isUser ? (
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {message.content}
          </p>
        ) : (
          <div className="prose" style={{ fontSize: 14 }}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const code = String(children).replace(/\n$/, '');
                  if (match) {
                    return (
                      <CodeBlock lang={match[1]} code={code} />
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
            {message.streaming && (
              <span
                style={{
                  display: 'inline-block',
                  width: 7,
                  height: 14,
                  background: 'var(--text-muted)',
                  borderRadius: 1,
                  animation: 'blink 0.9s step-start infinite',
                  verticalAlign: 'text-bottom',
                  marginLeft: 1,
                }}
              />
            )}
          </div>
        )}
        {!isUser && !message.streaming && message.content && (
          <CopyButton text={message.content} />
        )}
      </div>
    </div>
  );
}

function CodeBlock({ lang, code }: { lang: string; code: string }) {
  return (
    <div style={{ position: 'relative' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#1e1e2e',
          borderRadius: '8px 8px 0 0',
          padding: '4px 12px',
          fontSize: 11,
          color: 'var(--text-muted)',
        }}
      >
        <span>{lang}</span>
        <CopyButton text={code} small />
      </div>
      <SyntaxHighlighter
        language={lang}
        style={oneDark}
        customStyle={{ margin: 0, borderRadius: '0 0 8px 8px', fontSize: 13 }}
        PreTag="div"
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

function CopyButton({ text, small }: { text: string; small?: boolean }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={copy}
      title="Copy"
      style={{
        background: 'transparent',
        border: 'none',
        cursor: 'pointer',
        color: 'var(--text-muted)',
        padding: small ? 2 : '4px 8px',
        borderRadius: 4,
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        fontSize: 12,
        position: small ? 'static' : 'absolute',
        top: small ? undefined : 6,
        right: small ? undefined : 8,
      }}
    >
      {copied ? <CheckIcon size={13} /> : <CopyIcon size={13} />}
      {!small && (copied ? 'Copied' : 'Copy')}
    </button>
  );
}
