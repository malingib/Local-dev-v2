---
name: frontend
description: "Use when: working on React components, styling, state management, or the TypeScript frontend. Enforces shadcn/ui patterns, Zustand store architecture, Tailwind conventions, and component organization."
applyTo: "app/src/**"
---

# Frontend Development Instructions

## Component Architecture

### File Organization
```
app/src/
├── components/
│   ├── ui/              # shadcn/ui primitives (extends Radix UI)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── ActivityFeed.tsx # Feature components (high-level features)
│   ├── FindingCard.tsx
│   └── SessionControls.tsx
├── pages/               # Page-level components
│   ├── Dashboard.tsx
│   ├── SessionView.tsx
│   └── Settings.tsx
├── lib/
│   ├── api.ts          # All backend endpoints
│   ├── store.ts        # Zustand store (global state + WebSocket sync)
│   └── utils.ts        # Helper functions
├── types/
│   └── index.ts        # TypeScript interfaces (mirror backend Pydantic)
└── hooks/
    └── use-mobile.ts   # Custom React hooks
```

### Component Patterns

**UI Primitives (in `components/ui/`):**
- Extend shadcn/ui Radix components
- Use `cn()` from `lib/utils.ts` for Tailwind class merging
- Never modify file after scaffolding; re-scaffold from shadcn/ui instead
- Always export the root component and subcomponents (e.g., `Button`, `ButtonGroup`)

**Feature Components (in `components/`):**
- Self-contained, reusable UI features
- Receive data via props, emit events via callbacks
- Connect to Zustand store for global state
- Use shadcn/ui components from local `./ui/` folder
- Example: `<ActivityFeed sessions={sessions} onSessionClick={handleClick} />`

**Page Components (in `pages/`):**
- Map 1:1 to routes (see `react-router-dom` setup)
- Compose feature components + layouts
- Manage page-level state via Zustand
- Connected by routing in `App.tsx`

## State Management (Zustand)

### Store Architecture
```typescript
// app/src/lib/store.ts
export const useStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSession: null,
  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session }),
  
  // WebSocket sync methods (called by WebSocket handler)
  handleSessionUpdate: (event) => { /* update state */ },
}));
```

### Patterns
- **Mirrors backend Pydantic models** — types in `app/src/types/index.ts` match `codeaudit/backend/models.py`
- **Async thunks**: Use `async` action methods for API calls
  ```typescript
  fetchSessions: async () => {
    const data = await api.getSessions();
    set({ sessions: data });
  }
  ```
- **WebSocket sync**: Store exposes methods called by WebSocket message handler in `useEffect`
  ```typescript
  useEffect(() => {
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      useStore.getState().handleSessionUpdate(data);
    };
  }, []);
  ```

## Forms & Validation

### Patterns
- Use `react-hook-form` + `zod` for validated forms
- Define schemas in the component file or shared `validation.ts`
- Always validate on submit, not on input (unless UX requires real-time feedback)

```typescript
const schema = z.object({
  email: z.string().email(),
  settings: z.object({
    autoApprove: z.boolean(),
  }),
});

type FormData = z.infer<typeof schema>;

export function SettingsForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });
  
  return (
    <form onSubmit={handleSubmit(async (data) => {
      await api.updateSettings(data);
    })}>
      {/* form fields */}
    </form>
  );
}
```

## Styling

### Tailwind + shadcn/ui
- **Base styles**: `app/src/index.css` (global resets, typography)
- **Component styles**: Use Tailwind classes directly in JSX (`className="")
- **Theme variables**: CSS variables in `globals.css` for colors, spacing, etc.
- **Dark mode**: Configured in `tailwind.config.js`; use `dark:` prefix for dark mode classes

### Class Merging
Always use `cn()` from `lib/utils.ts` to merge conditional classes:
```typescript
import { cn } from "@/lib/utils";

<button className={cn(
  "px-4 py-2 rounded",
  variant === "primary" && "bg-blue-600",
  isDisabled && "opacity-50"
)}>
```

## Type Safety

### Path Alias
All imports use `@/*` mapping to `src/`:
```typescript
// ✅ Correct
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import type { Session } from "@/types";

// ❌ Avoid
import { useStore } from "../lib/store";
import { Button } from "../../ui/button";
```

### Type Definitions
- Keep all types in `app/src/types/index.ts`
- Import, never duplicate
- Mirror backend Pydantic models exactly

```typescript
// app/src/types/index.ts
export interface Session {
  id: string;
  status: "pending" | "running" | "complete";
  findings: Finding[];
}

export interface Finding {
  id: string;
  type: "bug" | "performance" | "security" | "ui" | "mobile";
  confidence: number;
}
```

## WebSocket Integration

### Real-Time Updates
- WebSocket connection established in `useEffect` (e.g., `SessionView.tsx`)
- Messages routed to Zustand store handlers
- Store updates trigger React re-renders automatically

```typescript
useEffect(() => {
  const ws = new WebSocket("ws://localhost:8000/ws");
  
  ws.onmessage = (event) => {
    const { type, data } = JSON.parse(event.data);
    switch (type) {
      case "session_update":
        useStore.getState().handleSessionUpdate(data);
        break;
      case "finding":
        useStore.getState().addFinding(data);
        break;
    }
  };
  
  return () => ws.close();
}, []);
```

## API Integration

See `app/src/lib/api.ts` — all backend endpoints defined as async functions:
```typescript
export const api = {
  getSessions: async () => fetch("/api/sessions").then(r => r.json()),
  createSession: async (config) => fetch("/api/sessions", {
    method: "POST",
    body: JSON.stringify(config),
  }).then(r => r.json()),
};
```

## Build & Dev

### Development
```bash
cd app
npm run dev      # Vite dev server with HMR, proxies /api to backend
npm run lint     # ESLint check
npm run build    # TypeScript type check + Vite build → app/dist/
```

### Common Issues
- **Port 5173 taken**: Kill the process or use `PORT=3000 npm run dev`
- **API not responding**: Ensure backend is running on `localhost:8000`
- **Hot reload not working**: Check Vite config for `server.middleware` proxy settings
- **TypeScript errors on import**: Check path alias `@/*` in `tsconfig.json`

## Component Testing Checklist

When adding a new component:
- [ ] Uses shadcn/ui or feature component patterns
- [ ] All imports use `@/*` path alias
- [ ] Types imported from `@/types`
- [ ] Connected to Zustand store (if needs global state)
- [ ] Accessible markup (ARIA labels, semantic HTML)
- [ ] Responsive (mobile-first Tailwind breakpoints)
- [ ] Build passes: `npm run build` in `app/`
