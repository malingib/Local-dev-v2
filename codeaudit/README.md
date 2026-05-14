# CodeAudit

> AI-powered, hypothesis-driven code auditor with visual approval.  
> Finds bugs, security issues, performance problems, and UI quality issues.  
> Runs entirely on **free** LLM APIs (Gemini + Groq).

---

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/yourname/codeaudit
cd codeaudit

# 2. Run the startup script — it guides you through everything
python start.py
```

On first run, `start.py` creates your `.env` file and tells you where to get free API keys.

**Free API keys needed:**
- **Google AI Studio** (recommended): https://aistudio.google.com/app/apikey  
- **Groq** (fast fallback): https://console.groq.com/keys

Add them to `.env`, then run `python start.py` again.

The web console opens at **http://localhost:8000**. No terminal knowledge required after this.

---

## What it does

**Three modes:**

| Mode | Description |
|------|-------------|
| **Audit** | Full scan → findings report. No changes. |
| **Audit + Fix** | Full scan → hypothesis loop → staged visual approval → apply patches |
| **Goal** | Targeted task: "fix the React console errors", "audit the auth flow" |

**Five specialist agents run in parallel:**
- `Auditor` — bugs, anti-patterns, dead code, logic errors
- `UI` — accessibility, design quality, slop detection, WCAG checks
- `Security` — secrets, SQL injection, XSS, auth gaps
- `Performance` — N+1 queries, heavy deps, missing lazy loading, bundle analysis
- `Mobile` — responsive breakpoints, touch targets, fixed widths, viewport

**Hypothesis-driven debugging:**  
Each finding gets a ranked hypothesis tree. The agent runs experiments to maximize information gain, updates confidence scores, and only proposes a patch when confidence exceeds 85%.

**Staged visual approval (UI changes only):**  
1. Annotated sketch — approve the direction
2. Component preview — tweak in isolation
3. Full page render — final confirmation

Auto-applies: WCAG fixes, missing alt text, viewport tags, lazy loading (objectively correct, no judgment needed).

---

## Configuration

Everything lives in `config/config.yaml` and `.env`.

**Change the project:**
```yaml
# config/config.yaml
project:
  github_url: "https://github.com/yourname/yourrepo"
  # or
  local_path: "/path/to/your/project"
```

**Swap models:**
```yaml
models:
  hypothesis_agent: "groq/llama-3.3-70b"  # faster
  ui_agent: "gemini-flash"                  # needs vision
```

**Disable agents:**
```yaml
agents:
  disabled:
    - performance_runtime   # skip lighthouse (no running app)
    - mobile_responsiveness # skip mobile checks
```

**Move to another machine:**
```bash
# On new machine:
git clone ... && cd codeaudit
cp .env.example .env
# Fill in your API keys
python start.py
```

Sessions are stored in `sessions/` as JSON files. Copy them to the new machine to resume.

---

## Supported stacks

React, Next.js, Vue, Svelte, Angular, Flutter, Django, Flask, FastAPI, Laravel, Rails, Express, Go, plain HTML/CSS

---

## Project structure

```
codeaudit/
├── start.py              ← Run this to start
├── .env                  ← Your API keys (gitignored)
├── config/
│   └── config.yaml       ← All settings
├── backend/
│   ├── api.py            ← FastAPI server
│   ├── models.py         ← Pydantic data models
│   ├── llm_router.py     ← Multi-provider LLM routing (Gemini + Groq)
│   ├── session_store.py  ← Event-sourced session persistence
│   ├── config.py         ← Configuration management
│   └── preferences.py    ← Rejection memory & learning
├── agents/
│   ├── orchestrator.py   ← Session state machine
│   ├── hypothesis_engine.py ← Debug loop with experiments
│   ├── base_agent.py     ← Base class for all agents
│   ├── auditor.py        ← Code quality agent
│   ├── ui_agent.py       ← Visual quality agent
│   ├── security_agent.py ← Security agent
│   ├── performance_agent.py ← Performance agent
│   ├── mobile_agent.py   ← Mobile responsiveness agent
│   ├── meta_agent.py     ← Self-improvement agent
│   └── stack_detector.py ← Tech stack detection
├── frontend/             ← React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/   ← FindingCard, ActivityFeed, Badge
│   │   ├── pages/        ← Dashboard, SessionView
│   │   ├── lib/          ← API client, store (Zustand)
│   │   └── App.tsx       ← Main app
│   └── package.json
├── sessions/             ← Session data (auto-created)
└── preferences/          ← Learning data (auto-created)
```

---

## Self-improvement

The tool gets smarter over time:

- **Per-project**: rejected proposals are never re-suggested
- **Per-user**: patterns across projects update your preference profile  
- **Meta-loop**: after 5+ sessions, a meta-agent analyzes stuck loops and rejections, proposes prompt improvements — you approve before anything changes

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/config` | GET | Get configuration |
| `/api/sessions` | GET | List all sessions |
| `/api/sessions` | POST | Create new session |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/sessions/{id}/findings` | GET | Get findings |
| `/api/sessions/{id}/audit` | POST | Start audit |
| `/api/sessions/{id}/fix/{fid}` | POST | Fix single finding |
| `/api/sessions/{id}/fix-all` | POST | Fix all open findings |
| `/api/sessions/{id}/approve` | POST | Approve/reject fix |
| `/api/sessions/{id}/report` | GET | Get audit report |
| `/ws/{id}` | WS | WebSocket for real-time updates |

---

## License

Business Source License 1.1 (BSL-1.1)  
Free for personal and non-commercial use.  
Commercial use requires a license — contact [you@email.com].
