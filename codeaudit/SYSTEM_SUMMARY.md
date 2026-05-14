# CodeAudit System Summary

## What Was Built

A **complete AI-powered code audit system** with two modes:

1. **Original Audit System** - Hypothesis-driven code auditing
2. **Agent Swarm System** - Multi-agent collaborative system (NEW)

---

## Architecture Overview

### Backend Stack
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Google Gemini + Groq** - LLM providers with fallback
- **WebSocket** - Real-time updates
- **JSON file storage** - Session persistence

### Frontend Stack
- **React + TypeScript** - UI framework
- **Vite** - Build tool
- **Tailwind CSS + shadcn/ui** - Styling
- **Zustand** - State management

---

## Original Audit System

### Components

| Component | Purpose |
|-----------|---------|
| `api.py` | FastAPI REST + WebSocket endpoints |
| `models.py` | Pydantic data models |
| `llm_router.py` | Multi-provider LLM (Gemini + Groq) |
| `session_store.py` | Event-sourced JSON persistence |
| `config.py` | YAML + .env configuration |
| `preferences.py` | Rejection memory & learning |

### Agents (Original)

| Agent | Purpose |
|-------|---------|
| **Auditor** | Bugs, anti-patterns, dead code |
| **UI** | Accessibility, design quality |
| **Security** | Secrets, XSS, SQL injection |
| **Performance** | N+1 queries, bundle analysis |
| **Mobile** | Responsive, touch targets |
| **Meta** | Self-improvement analysis |

### Key Features
- **Hypothesis-driven debugging** - Ranked hypotheses, experiments, confidence scoring
- **Auto-approval** - WCAG fixes applied automatically
- **Visual approval flow** - Staged approval for UI changes
- **Rejection memory** - Don't re-suggest rejected fixes
- **Stack detection** - Auto-detect React, Vue, Django, etc.

---

## Agent Swarm System (NEW)

### Components

| Component | Purpose |
|-----------|---------|
| `message_bus.py` | Central agent communication |
| `shared_context.py` | Collective swarm memory |
| `round_table.py` | Structured agent discussions |
| `consensus.py` | Voting and agreement |
| `coordinator.py` | Swarm orchestration |
| `base_agent.py` | Agent foundation class |
| `agents.py` | All specialized agents |

### Swarm Agents

| Agent | Role | Can Self-Modify |
|-------|------|-----------------|
| **Orchestrator** | Task coordination | ❌ |
| **Coder** | Code writing | ❌ |
| **Debugger** | Bug hunting | ❌ |
| **UI Designer** | Frontend/UX | ❌ |
| **Database** | Schema/queries | ❌ |
| **Backend** | APIs/services | ❌ |
| **Optimizer** | Performance | ❌ |
| **QA Reviewer** | Code review | ❌ |
| **Critic** | Challenge assumptions | ❌ |
| **Self-Modifier** | Improve the swarm | ✅ |

### Key Features

#### 1. Message-Based Communication
```python
# Agents talk via message bus
await agent.broadcast({
    "proposal": "Use async/await",
    "reasoning": "Better I/O performance"
})

# Direct questions
response = await agent.ask_agent(
    "database",
    "Best index for user lookup?"
)
```

#### 2. Shared Context (Collective Memory)
```python
# Store finding
await context.add_memory(Memory(
    content="SQL injection in auth.py:42",
    agent="security",
    memory_type="finding",
    tags=["critical", "security"]
))

# Query memories
memories = await context.query_memories(
    tags=["critical"],
    query="injection"
)
```

#### 3. Round Table Discussions
```python
# Complex decision? Call round table
decision = await coordinator.call_round_table(
    topic="Auth strategy",
    question="JWT vs Sessions?",
    agents=["backend", "security", "database"]
)
# Returns: consensus score, positions, reasoning
```

#### 4. Consensus Mechanisms
- **Simple majority** (>50%)
- **Supermajority** (>67%) - default
- **Unanimous** (100%)
- **Expertise-weighted** (DB agent has more say on DB topics)

#### 5. Model Switching
```python
# Switch one agent
coordinator.switch_agent_model("coder", "groq/llama-3.3-70b")

# Switch all
coordinator.switch_all_models("gemini-pro")

# Available:
# - gemini-flash (fast, cheap)
# - gemini-pro (capable)
# - groq/llama-3.3-70b (fast inference)
# - groq/llama-3.1-8b (very fast)
# - groq/mixtral-8x7b (balanced)
```

#### 6. Self-Improvement
- **Reflection** - Agents analyze their actions
- **Meta-analysis** - Self-Modifier analyzes swarm
- **System updates** - Can modify prompts, rules, thresholds

#### 7. Bias Prevention
- **Critic agent** challenges all proposals
- **Structured debate** before decisions
- **Multiple voting mechanisms**

---

## File Structure

```
codeaudit/
├── start.py                    # Main entry point
├── demo_swarm.py              # Swarm demo script
├── README.md                   # User documentation
├── SWARM_ARCHITECTURE.md      # Swarm technical docs
├── SYSTEM_SUMMARY.md          # This file
│
├── backend/                    # Original system
│   ├── api.py                 # FastAPI endpoints
│   ├── models.py              # Pydantic models
│   ├── llm_router.py          # LLM routing (Gemini + Groq)
│   ├── session_store.py       # JSON persistence
│   ├── config.py              # Configuration
│   ├── preferences.py         # Rejection memory
│   └── swarm_api.py           # NEW: Swarm endpoints
│
├── agents/                     # Original audit agents
│   ├── base_agent.py          # Base class
│   ├── orchestrator.py        # Session coordinator
│   ├── hypothesis_engine.py   # Debug loop
│   ├── auditor.py             # Code quality
│   ├── ui_agent.py            # Accessibility
│   ├── security_agent.py      # Security
│   ├── performance_agent.py   # Performance
│   ├── mobile_agent.py        # Mobile
│   ├── meta_agent.py          # Self-improvement
│   └── stack_detector.py      # Tech detection
│
├── swarm/                      # NEW: Agent swarm
│   ├── __init__.py
│   ├── message_bus.py         # Communication system
│   ├── shared_context.py      # Collective memory
│   ├── round_table.py         # Facilitated discussions
│   ├── consensus.py           # Voting mechanisms
│   ├── coordinator.py         # Swarm controller
│   ├── base_agent.py          # Agent foundation
│   └── agents.py              # All 10 agents
│
├── frontend/                   # React web console
│   ├── src/
│   │   ├── components/        # FindingCard, ActivityFeed, Badge
│   │   ├── pages/             # Dashboard, SessionView
│   │   ├── lib/               # API client, store
│   │   └── App.tsx            # Main app
│   └── package.json
│
├── config/
│   └── config.example.yaml    # Configuration template
│
├── requirements.txt            # Python dependencies
└── .env.example               # API keys template
```

---

## API Endpoints

### Original System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/sessions` | GET/POST | List/create sessions |
| `/api/sessions/{id}` | GET | Get session |
| `/api/sessions/{id}/audit` | POST | Start audit |
| `/api/sessions/{id}/fix/{fid}` | POST | Fix finding |
| `/api/sessions/{id}/approve` | POST | Approve/reject |
| `/ws/{id}` | WS | Real-time updates |

### Swarm System (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/swarm/status` | GET | Swarm status |
| `/api/swarm/agents` | GET | List agents |
| `/api/swarm/agents/{id}` | GET | Agent status |
| `/api/swarm/models` | GET | List models |
| `/api/swarm/models/switch` | POST | Switch models |
| `/api/swarm/tasks` | GET/POST | List/submit tasks |
| `/api/swarm/round-table` | POST | Call round table |
| `/ws/swarm` | WS | Real-time updates |

---

## Usage

### Quick Start
```bash
cd /mnt/okcomputer/output/codeaudit

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Run the system
python start.py
```

### Demo the Swarm
```bash
python demo_swarm.py
```

### Use the Swarm in Code
```python
from swarm import SwarmCoordinator, SwarmConfig

# Initialize
coordinator = SwarmCoordinator(SwarmConfig())
await coordinator.start()

# Submit task
task_id = await coordinator.submit_task(
    "Add user authentication",
    task_type="feature_implementation",
    requirements=["JWT", "Password hashing"],
    priority="high"
)

# Call round table
decision = await coordinator.call_round_table(
    topic="Auth strategy",
    question="JWT vs Sessions?"
)

# Switch models
coordinator.switch_agent_model("coder", "groq/llama-3.3-70b")

# Stop
await coordinator.stop()
```

---

## Key Innovations

### Compared to Original System

| Feature | Original | Swarm |
|---------|----------|-------|
| Agents | 5 | 10 |
| Communication | Direct calls | Message bus |
| Decision Making | Single agent | Consensus |
| Debate | None | Round-table |
| Self-Improvement | Analysis | Full modification |
| Model Switching | Global | Per-agent |
| Bias Prevention | None | Critic agent |
| Shared Memory | Session-only | Persistent context |

### Inspired By
- **Kimi** - Multi-agent architecture
- **Andrej Karpathy's LLM OS** - Message passing, shared memory
- **Auto-Research Tool** - Self-improvement loops

---

## Next Steps / Future Work

1. **Frontend Swarm Visualization**
   - Real-time agent activity graph
   - Message flow visualization
   - Consensus building animation

2. **Enhanced Self-Modification**
   - Agent prompt evolution
   - Dynamic agent creation
   - Performance-based agent hiring/firing

3. **Human-in-the-Loop**
   - Critical decision approval
   - Override agent decisions
   - Teach swarm new patterns

4. **Cross-Project Learning**
   - Transfer lessons between projects
   - Build institutional knowledge
   - Pattern recognition across codebases

5. **Advanced Consensus**
   - Fuzzy voting
   - Confidence-weighted decisions
   - Temporal consensus (decisions over time)

---

## Configuration

### Environment Variables (.env)
```bash
# Required - at least one
GOOGLE_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Optional
GITHUB_TOKEN=for_private_repos
FIGMA_TOKEN=for_design_comparison
```

### Config File (config/config.yaml)
```yaml
project:
  name: "My Project"
  github_url: "..."
  local_path: "..."

agents:
  enabled:
    - auditor
    - ui
    - security
    - performance_static
    - mobile_responsiveness

approval:
  auto_approve:
    missing_alt_text: true
    missing_meta_viewport: true

hypothesis:
  max_steps: 20
  confidence_threshold: 0.85
```

---

## Summary

This is a **production-ready, extensible code audit system** with:

✅ **Hypothesis-driven debugging** (original)  
✅ **Multi-agent swarm** (new)  
✅ **Message-based communication**  
✅ **Shared collective memory**  
✅ **Structured debate/consensus**  
✅ **Self-improvement capability**  
✅ **Model switching**  
✅ **Bias prevention**  
✅ **Real-time WebSocket updates**  
✅ **Modern React frontend**  

The system can audit codebases, propose fixes, learn from rejections, and even improve its own coordination and prompts over time.
