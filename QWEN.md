# Local dev v2 — Project Context

## Overview

This directory contains **two connected projects**:

1. **`app/`** — The React + TypeScript + Vite frontend for CodeAudit (serves as the web console)
2. **`codeaudit/`** — The Python FastAPI backend with AI-powered code audit agents

The `app/` frontend communicates with `codeaudit/`'s backend API via Vite dev proxy (development) or direct static file serving (production).

---

## How They Work Together

```
┌──────────────────┐         ┌──────────────────────────┐
│   app/ (React)   │  HTTP   │  codeaudit/ (FastAPI)    │
│   Port 5173      │ ◄─────► │  Port 8000               │
│   (dev only)     │  /ws    │  + WebSocket             │
└──────────────────┘         └──────────────────────────┘
                                      │
                              ┌───────▼────────┐
                              │  LLM Providers │
                              │  Gemini / Groq │
                              └────────────────┘
```

### Development Mode
```bash
cd codeaudit
python run.py --dev
```
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:5173` (Vite dev server with HMR)
- Vite proxies `/api` and `/ws` requests to the backend

### Production Mode
```bash
cd codeaudit
python run.py
```
- Frontend is built and copied to `codeaudit/frontend/dist`
- Backend serves everything on `http://localhost:8000`

### Key Integration Points
- **API Client** — `app/src/lib/api.ts` — all backend endpoints
- **State Management** — `app/src/lib/store.ts` — Zustand store with real-time WebSocket sync
- **Types** — `app/src/types/index.ts` — mirrors backend Pydantic models
- **Static Serving** — `codeaudit/backend/api.py` mounts `frontend/dist` in production
- **Vite Proxy** — `app/vite.config.ts` routes `/api` → `localhost:8000` in dev

---

## Project 1: `app/` — React Frontend Application

### Purpose
A minimal React application setup using Vite with Hot Module Replacement (HMR), TypeScript, Tailwind CSS v3.4.19, and 40+ shadcn/ui components. Currently serves as a blank template (default Vite counter app).

### Tech Stack
- **Framework:** React 19 with TypeScript
- **Build Tool:** Vite 7.2.4
- **Styling:** Tailwind CSS 3.4.19 + shadcn/ui
- **Linting:** ESLint 9 with React Hooks & Refresh plugins
- **Node Version:** 20

### Key Dependencies
- **UI Components:** Radix UI primitives, lucide-react icons, recharts, sonner (toasts)
- **Form Handling:** react-hook-form + Zod validation
- **State Management:** Zustand-style patterns (via shadcn)

### Available Scripts
```bash
npm run dev       # Start dev server with HMR
npm run build     # Type-check and build for production
npm run lint      # Run ESLint
npm run preview   # Preview production build locally
```

### Project Structure
```
app/
├── src/
│   ├── components/   # shadcn/ui components (Button, Card, etc.)
│   ├── hooks/        # Custom React hooks
│   ├── lib/          # Utility libraries
│   ├── sections/     # Page sections (if added)
│   ├── types/        # TypeScript type definitions
│   ├── App.tsx       # Root component
│   ├── App.css       # App-specific styles
│   ├── index.css     # Global styles
│   └── main.tsx      # Entry point
├── index.html        # HTML entry point
├── vite.config.ts    # Vite configuration
├── tailwind.config.js # Tailwind CSS configuration
├── tsconfig.json     # TypeScript configuration
└── package.json
```

### Component Usage
```tsx
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
```

---

## Project 2: `codeaudit/` — AI-Powered Code Audit System

### Purpose
A complete AI-powered code audit system that finds bugs, security issues, performance problems, and UI quality issues. It runs on free LLM APIs (Google Gemini + Groq) and features both a traditional audit mode and an experimental multi-agent swarm system.

### Tech Stack
- **Backend:** Python, FastAPI, Pydantic
- **LLM Providers:** Google Gemini, Groq
- **Frontend:** React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **State Management:** Zustand
- **Real-time:** WebSocket
- **Storage:** Event-sourced JSON files

### Two Operating Modes

| Mode | Description |
|------|-------------|
| **Original Audit System** | Hypothesis-driven code auditing with 5 specialized agents |
| **Agent Swarm System** | Multi-agent collaborative system with 10 specialized agents |

### Original Audit Agents
- **Auditor** — Bugs, anti-patterns, dead code, logic errors
- **UI** — Accessibility, design quality, WCAG checks
- **Security** — Secrets, SQL injection, XSS, auth gaps
- **Performance** — N+1 queries, bundle analysis, lazy loading
- **Mobile** — Responsive breakpoints, touch targets, viewport
- **Meta** — Self-improvement analysis

### Swarm Agents (Extended)
- Orchestrator, Coder, Debugger, UI Designer, Database, Backend, Optimizer, QA Reviewer, Critic, Self-Modifier

### Key Features
- **Hypothesis-driven debugging** — Ranked hypotheses, experiments, confidence scoring (85% threshold)
- **Staged visual approval** — Annotated sketch → Component preview → Full page render
- **Auto-approval** — WCAG fixes, missing alt text, viewport tags applied automatically
- **Rejection memory** — Rejected proposals are never re-suggested
- **Round-table discussions** — Structured agent debates for complex decisions
- **Consensus mechanisms** — Simple majority, supermajority, expertise-weighted voting
- **Self-improvement** — Reflection, meta-analysis, system updates
- **Model switching** — Per-agent or global model switching (Gemini-flash/pro, Groq/llama-3.3-70b, etc.)

### Quick Start
```bash
cd codeaudit

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your Google AI Studio and/or Groq API keys

# Run the system
python start.py
```

### Demo the Swarm
```bash
python demo_swarm.py
```

### Web Console
Opens at **http://localhost:8000**

### API Endpoints

#### Original System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/sessions` | GET/POST | List/create sessions |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/sessions/{id}/audit` | POST | Start audit |
| `/api/sessions/{id}/fix/{fid}` | POST | Fix single finding |
| `/api/sessions/{id}/approve` | POST | Approve/reject fix |
| `/ws/{id}` | WS | Real-time updates |

#### Swarm System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/swarm/status` | GET | Swarm status |
| `/api/swarm/agents` | GET | List agents |
| `/api/swarm/models` | GET | List available models |
| `/api/swarm/models/switch` | POST | Switch models |
| `/api/swarm/tasks` | GET/POST | List/submit tasks |
| `/api/swarm/round-table` | POST | Call round table discussion |
| `/ws/swarm` | WS | Real-time swarm updates |

### Project Structure
```
codeaudit/
├── start.py                    # Main entry point
├── demo_swarm.py              # Swarm demo script
├── .env.example               # API keys template
├── config/
│   └── config.yaml            # All settings
├── backend/
│   ├── api.py                 # FastAPI endpoints
│   ├── models.py              # Pydantic data models
│   ├── llm_router.py          # Multi-provider LLM routing
│   ├── session_store.py       # Event-sourced session persistence
│   ├── config.py              # Configuration management
│   ├── preferences.py         # Rejection memory & learning
│   └── swarm_api.py           # Swarm-specific endpoints
├── agents/                     # Original audit agents
│   ├── orchestrator.py
│   ├── hypothesis_engine.py
│   ├── base_agent.py
│   ├── auditor.py, ui_agent.py, security_agent.py, ...
├── swarm/                      # Multi-agent swarm system
│   ├── message_bus.py         # Communication system
│   ├── shared_context.py      # Collective memory
│   ├── round_table.py         # Facilitated discussions
│   ├── consensus.py           # Voting mechanisms
│   ├── coordinator.py         # Swarm controller
│   ├── base_agent.py
│   └── agents.py              # All 10 specialized agents
├── frontend/                   # React web console
│   └── src/
├── sessions/                   # Session data (auto-created)
└── preferences/                # Learning data (auto-created)
```

### Configuration

#### Environment Variables (`.env`)
```bash
GOOGLE_API_KEY=     # Google AI Studio (recommended)
GROQ_API_KEY=       # Groq (fast fallback)
GITHUB_TOKEN=       # Optional — for private repos
FIGMA_TOKEN=        # Optional — for design comparison
```

#### Config File (`config/config.yaml`)
Controls project target, enabled agents, auto-approval rules, hypothesis thresholds, and model assignments.

### Supported Tech Stacks
React, Next.js, Vue, Svelte, Angular, Flutter, Django, Flask, FastAPI, Laravel, Rails, Express, Go, plain HTML/CSS

### License
Business Source License 1.1 (BSL-1.1) — Free for personal/non-commercial use.

---

## Development Conventions

### `app/` Project
- Uses TypeScript with strict mode
- ESLint configured with React-specific rules
- Path aliasing: `@/` maps to `src/`
- Component imports use absolute paths from `@/components/ui/`

### `codeaudit/` Project
- Backend uses FastAPI with Pydantic models for validation
- Session persistence via event-sourced JSON files
- WebSocket for real-time communication
- Agents follow a base class pattern for extensibility
- Hypothesis engine uses information gain for experiment selection

---

## Important Notes
- The `app/` project is currently a blank template — ready for development
- The `codeaudit/` project requires at least one API key (Google or Groq) to function
- Both projects use React + Vite + TypeScript + Tailwind + shadcn/ui for their frontends
- API keys in `.env.example` appear to contain placeholder/example values — replace with real keys for actual use
