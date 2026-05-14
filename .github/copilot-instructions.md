# CodeAudit Workspace Guidelines

CodeAudit is an AI-powered, hypothesis-driven code auditor. This workspace contains a full-stack application: a React/TypeScript frontend (`app/`) and a FastAPI backend (`codeaudit/`) with multi-agent AI orchestration.

## Code Style

### Frontend (React/TypeScript)
- **File structure**: Components in `src/components/`, UI primitives in `src/components/ui/` (shadcn/ui)
- **State management**: Zustand (see `src/lib/store.ts`); mirrors Pydantic backend models
- **Styling**: Tailwind CSS 3.4+ with shadcn/ui Radix components
- **Forms**: `react-hook-form` + `zod` for validation
- **Routing**: `react-router-dom`; main pages in `src/pages/`
- **Type safety**: All imports use path alias `@/*` → `src/`; interfaces in `src/types/index.ts`

### Backend (Python/FastAPI)
- **Async-first**: FastAPI + `aiohttp`; all handlers use `async def`
- **Validation**: Pydantic 2.0+ models; no raw dicts
- **Agents**: Event message flow through base agent class; see `agents/base_agent.py`
- **Configuration**: YAML-based (`config/config.yaml`) + `.env` for secrets
- **Error handling**: FastAPI exceptions with descriptive messages for frontend error UI

## Architecture

**Full-stack monorepo**: Frontend and backend strongly coupled but independently deployable.

```
app/                    → React Vite SPA (requests via /api → backend)
codeaudit/
  backend/api.py        → FastAPI REST + WebSocket server
  agents/               → Specialist agent implementations
  sessions/             → JSON event logs (immutable session persistence)
  config/config.yaml    → Project & LLM model configuration
```

**Key design decisions**:
- **Hypothesis-driven debugging**: Agents rank hypotheses, run experiments, propose fixes only >85% confidence
- **Multi-provider LLM**: Google Gemini primary → Groq fallback (resilience on free tier)
- **Event-sourced sessions**: JSON files in `codeaudit/sessions/` allow reproducible audits across machines
- **Vite proxy architecture** (dev only): Frontend port 5173 proxies `/api` and `/ws` to backend port 8000
- **Staged visual approval**: UI-only findings flow through sketch → component preview → full page render

See [SYSTEM_SUMMARY.md](../codeaudit/SYSTEM_SUMMARY.md) and [SWARM_ARCHITECTURE.md](../codeaudit/SWARM_ARCHITECTURE.md) for agent roles and message bus design.

## Build and Test

### Development (Auto-reload everything)
```bash
cd codeaudit
python run.py --dev
```
- Backend: `http://localhost:8000` (FastAPI with auto-reload on Python changes)
- Frontend: `http://localhost:5173` (Vite with HMR on TypeScript/CSS changes)
- WebSocket at `ws://localhost:8000/ws`

### Production (Static-served both parts)
```bash
cd codeaudit
python run.py
```
- Rebuilds frontend → `app/dist/` → copies to `codeaudit/frontend/dist/`
- Serves both on `http://localhost:8000`

### Frontend-only
```bash
cd app
npm run dev       # Vite dev server (port 5173)
npm run build     # TypeScript type check + Vite build
npm run lint      # ESLint check
```

### Manual frontend build (without running backend)
```bash
python build_frontend.py  # → codeaudit/frontend/dist/
```

## Conventions

### API Integration
- All backend endpoints and WebSocket defined in `app/src/lib/api.ts`
- Frontend state mirrors backend Pydantic models (see `app/src/types/index.ts`)
- WebSocket events for real-time session updates captured in store

### Component Extension
1. For new UI primitives, add to `src/components/ui/` (extends shadcn/ui Radix)
2. For feature components, add to `src/components/` (e.g., `ActivityFeed.tsx`, `FindingCard.tsx`)
3. Always import UI components from local `./ui` folder, not node_modules

### Agent Development
- All agents inherit from `agents/base_agent.py`
- Message routing through `backend/orchestrator.py`
- Configuration for enabling/disabling agents in `codeaudit/config/config.yaml` under `agents.disabled`
- Test agents locally by modifying config before committing

### Session Debugging
- Sessions stored as JSON event logs in `codeaudit/sessions/<id>.json`
- Reproducible: copy session files to new machine and resume
- Event structure defined in Pydantic models (see `backend/models.py`)

## Critical Setup Quirks

### API Keys Required
**No fallback to UI without keys**—set `.env` on first run:
```bash
cd codeaudit
# Copy example
cp config/config.example.yaml config/config.yaml
# Create .env and add:
GOOGLE_API_KEY=... # from https://aistudio.google.com/app/apikey
GROQ_API_KEY=...   # from https://console.groq.com/keys
```

### Port Conflicts
- Frontend dev needs `5173`, backend needs `8000`
- Both must be available on first run; dev mode fails silently if ports taken
- Workaround: `python run.py --dev --port 9000` (experimental)

### Python Environment
- Backend requires activated venv before running
- `run.py` does **not** auto-activate; use full path in terminal:
  ```bash
  source /path/to/.venv/bin/activate
  # Then: python run.py --dev
  ```
- Last seen issue: exit code 1 on activation—check `.venv` path exists

### Node Version
- Requires Node 20+ (modern ESM modules)
- Vite builds break silently on Node 16—check `node --version`

### Build Order (Production)
- Always rebuilds frontend first via `build_frontend.py`
- Avoid editing `codeaudit/frontend/dist/` directly—changes disappear on next `npm run build`

### TypeScript Path Alias
- All imports use `@/*` which maps to `src/`
- Keep consistent; don't mix `./src/` with `@/` in same file

### Session Persistence
- Sessions are JSON event logs (not binary)
- Safe to copy, inspect, or ship to another machine
- Resumes from last recorded event on reload

## Related Documentation
- [codeaudit/README.md](../codeaudit/README.md) — Quick start, modes, configuration
- [codeaudit/SYSTEM_SUMMARY.md](../codeaudit/SYSTEM_SUMMARY.md) — Agent roles, architecture
- [codeaudit/SWARM_ARCHITECTURE.md](../codeaudit/SWARM_ARCHITECTURE.md) — Message bus, consensus voting
- [app/info.md](../app/info.md) — Frontend component inventory
