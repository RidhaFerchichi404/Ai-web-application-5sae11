import { Suspense } from 'react';
import Sidebar from '@/components/sidebar/Sidebar';

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Suspense
        fallback={
          <aside
            style={{
              width: 240,
              minWidth: 240,
              background: 'var(--surface)',
              borderRight: '1px solid var(--border)',
            }}
          />
        }
      >
        <Sidebar />
      </Suspense>
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {children}
      </main>
    </div>
  );
}
