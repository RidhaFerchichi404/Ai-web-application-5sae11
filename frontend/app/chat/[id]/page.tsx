import { Suspense } from 'react';
import ConversationContent from '@/components/chat/ConversationContent';

export default function ConversationPage() {
  return (
    <Suspense fallback={<div style={{ flex: 1, display: 'flex' }} />}>
      <ConversationContent />
    </Suspense>
  );
}
