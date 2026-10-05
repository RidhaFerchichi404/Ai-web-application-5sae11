# Frontend

Status: Planned. The `frontend/` directory is an empty placeholder. Next.js is not initialized. No components exist.

## Stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

The UI will be an original dark workspace: quiet surfaces, readable type, and a conversation as the main panel. It takes its cue from a minimal, developer-oriented chat product and will not copy that product’s code, name, logo, or exact layout.

## Layout

```text
┌─────────────────────────────────────────────────────────────┐
│                     AI ASSISTANT                            │
├───────────────┬─────────────────────────────────────────────┤
│               │                                             │
│  + New Chat   │                                             │
│               │                                             │
│  Search       │              Conversation                   │
│               │                                             │
│  Conversations│                                             │
│               │                                             │
│  ───────────  │                                             │
│               │                                             │
│  Today        │                                             │
│  Chat 1       │                                             │
│  Chat 2       │                                             │
│               │                                             │
│  Documents    │                                             │
│               │                                             │
│  Settings     ├─────────────────────────────────────────────┤
│               │ 📎 Attach file     Ask anything...      ➤  │
└───────────────┴─────────────────────────────────────────────┘
```

### Sidebar

Planned contents:

- New conversation
- Conversation search
- Conversation history, grouped simply (for example, today and earlier)
- Documents
- Settings
- The active model name

### Conversation

Planned behavior:

- Render assistant output as Markdown
- Render fenced code with syntax highlighting
- Copy a response
- Copy a code block
- Regenerate a response
- Stop generation while a stream is open

### Composer

Planned behavior:

- Multiline text input
- File attachment
- Send
- Stop, shown while a response is streaming
- Selected model indicator

### Documents

The document view will show filename, file type, size, processing status, upload date, and delete. It will read `GET /api/documents`.

## Component architecture

Phase 7 will keep the tree shallow:

- App shell: sidebar plus main panel
- Conversation list
- Message thread
- Composer
- Document list
- Model selector

Shared visual pieces (buttons, inputs, dialogs, scroll areas) will come from shadcn/ui rather than a second design system. Feature components will live next to the routes that use them. A component will not call Ollama or MySQL itself.

## State management

Server data (conversations, messages, documents, models) will be loaded from the API and refreshed after mutations. Local state will cover the draft, the attachment picker, and whether a stream is open.

A global state library is not required. Phase 7 can use React state and the Next.js data functions. If that becomes awkward, the choice of a small cache library will be written in the decision log before it is added.

## API communication

The browser will call the Next.js app. Server-side or route handlers in Next.js may proxy to FastAPI, or the client may call FastAPI directly if Phase 7 chooses one of those and documents it. Only one of those paths will be implemented, and it will be the only path.

Requests and responses follow [api.md](api.md). The client will treat network and HTTP failures as error states, not as empty conversations.

## Streaming UI

While `POST /api/chat` is streaming, the thread will append tokens to the open assistant message. Send will be replaced by Stop. When the stream ends, the message list will match what the server stored. A failed stream will leave an error on that turn and will not pretend the answer was saved if the server reports that it was not.

The framing of the stream will match whatever Phase 3 records in the API document.

## Responsive design

The desktop layout is the sidebar beside the thread. Narrow viewports will collapse the sidebar into a drawer and keep the composer pinned. Phase 8 will check both widths. Phase 7 should already be usable on a laptop-width window.

## Theme

Tailwind will carry the palette: near-black background, restrained borders, and one accent for the send action and focus rings. Motion will be short and will not block reading. Empty, loading, and error states are Phase 8 requirements, and Phase 7 should leave obvious places for them instead of a blank panel.

## Accessibility

Planned for Phase 8, and not optional in the final UI:

- Keyboard access to new chat, the composer, and send
- Visible focus
- Text alternatives for icon-only buttons
- Contrast that holds on the dark background
- A way to stop generation from the keyboard

## Related documents

- [Architecture](architecture.md)
- [API](api.md)
- [Development phases](development.md)
