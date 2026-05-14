# CodeAudit Agent Swarm Architecture

> Inspired by Kimi's multi-agent system and Andrej Karpathy's LLM OS concepts.

## Overview

The CodeAudit Swarm is a multi-agent system where specialized AI agents collaborate to audit, improve, and evolve codebases. The swarm can also improve itself through reflection and self-modification.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SWARM COORDINATOR                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Message   │  │   Shared    │  │      Round Table        │  │
│  │    Bus      │  │   Context   │  │    (Consensus)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │  AGENTS │          │  AGENTS │          │  AGENTS │
   └─────────┘          └─────────┘          └─────────┘
```

## The Agent Swarm

### 1. **Orchestrator** 👑
- **Role**: Central coordinator
- **Responsibilities**:
  - Break down complex tasks
  - Assign tasks to appropriate agents
  - Monitor progress
  - Facilitate discussions
  - Resolve conflicts
  - Make final decisions

### 2. **Coder** 💻
- **Role**: Software engineer
- **Responsibilities**:
  - Write clean, maintainable code
  - Implement features
  - Fix bugs
  - Refactor code
  - Write tests

### 3. **Debugger** 🐛
- **Role**: Bug hunter
- **Responsibilities**:
  - Analyze error reports
  - Trace code execution
  - Identify root causes
  - Propose targeted fixes
  - Verify fixes

### 4. **UI Designer** 🎨
- **Role**: Frontend & UX expert
- **Responsibilities**:
  - Design UI components
  - Ensure accessibility (WCAG)
  - Maintain visual consistency
  - Handle responsive design
  - Review frontend code

### 5. **Database** 🗄️
- **Role**: Data architect
- **Responsibilities**:
  - Schema design
  - Query optimization
  - Migration planning
  - Data modeling

### 6. **Backend** ⚙️
- **Role**: API & service architect
- **Responsibilities**:
  - API design
  - Service architecture
  - Authentication
  - Caching strategies

### 7. **Optimizer** 🚀
- **Role**: Performance expert
- **Responsibilities**:
  - Find bottlenecks
  - Algorithm optimization
  - Memory optimization
  - Profiling

### 8. **QA Reviewer** ✅
- **Role**: Quality assurance
- **Responsibilities**:
  - Code review
  - Bug detection
  - Best practice enforcement
  - Security review
  - Test coverage

### 9. **Critic** 🎭
- **Role**: Devil's advocate
- **Responsibilities**:
  - Challenge assumptions
  - Identify blind spots
  - Suggest alternatives
  - Prevent groupthink
  - Ask probing questions

### 10. **Self-Modifier** 🔧
- **Role**: Meta-improver
- **Responsibilities**:
  - Analyze swarm performance
  - Propose system improvements
  - Modify agent prompts
  - Update coordination logic
  - Learn from past decisions

## Communication System

### Message Bus

All agents communicate through a central message bus:

```python
# Agent sends a message
await agent.broadcast({
    "proposal": "Use async/await pattern",
    "reasoning": "Better performance for I/O"
})

# Agent asks another agent
response = await agent.ask_agent(
    "database",
    "What's the best index for this query?",
    context="User authentication table"
)
```

### Message Types

- `TASK_ASSIGNED` - Work assignment
- `AGENT_MESSAGE` - General communication
- `AGENT_QUESTION` / `AGENT_ANSWER` - Q&A
- `AGENT_DEBATE` - Discussion
- `AGENT_CHALLENGE` - Critique
- `CODE_PROPOSAL` / `CODE_REVIEW` - Code workflow
- `CONSENSUS_REQUEST` / `CONSENSUS_REACHED` - Decision making
- `SYSTEM_PROPOSAL` - Self-modification

## Shared Context

The shared context is like the swarm's collective memory:

### Memory Types
- **Code Artifacts** - Files being worked on
- **Analysis Results** - Findings and insights
- **Decisions** - Swarm decisions with reasoning
- **Lessons** - Learned improvements
- **Agent Workspaces** - Private agent memory

### Example
```python
# Store a finding
await context.add_memory(Memory(
    content="Found SQL injection vulnerability",
    agent="security",
    memory_type="finding",
    tags=["security", "critical"]
))

# Query relevant memories
memories = await context.query_memories(
    agent="security",
    tags=["critical"],
    query="injection"
)
```

## Round Table Discussions

For complex decisions, agents participate in structured discussions:

```python
# Call a round table
decision = await coordinator.call_round_table(
    topic="Authentication approach",
    question="Should we use JWT or session-based auth?",
    agents=["backend", "security", "database"]
)

# Result includes:
# - Consensus score
# - Each agent's position
# - Key points
# - Areas of disagreement
```

### Discussion Flow
1. **Round 1**: All agents share initial opinions
2. **Round 2**: Agents respond to each other's points
3. **Round 3**: Final positions and consensus check
4. **Decision**: Form final decision or note disagreement

## Consensus Mechanisms

### Simple Majority
```python
engine = ConsensusEngine("simple")
result = engine.check_consensus(votes)
# Approved if > 50% agree
```

### Supermajority (Default)
```python
engine = ConsensusEngine("supermajority")
result = engine.check_consensus(votes)
# Approved if > 67% agree
```

### Expertise-Weighted
```python
engine = ExpertiseWeightedConsensus({
    "database": {"database": 2.0, "api": 0.5},
    "backend": {"api": 2.0, "database": 0.8}
})
result = engine.check_consensus(votes, topic="api")
```

## Self-Improvement

The swarm can improve itself through:

### 1. Reflection
Each agent periodically reflects on its actions:
```python
async def _reflect(self):
    # Analyze recent memories
    # Identify patterns
    # Generate lessons
    # Store for future use
```

### 2. Meta-Analysis
The Self-Modifier agent analyzes swarm performance:
- Which agents are effective?
- What decisions worked?
- What patterns cause failures?

### 3. System Updates
The swarm can modify:
- Agent system prompts
- Coordination rules
- Decision thresholds
- Communication patterns

## Model Switching

Agents can switch models dynamically:

```python
# Switch one agent
coordinator.switch_agent_model("coder", "groq/llama-3.3-70b")

# Switch all agents
coordinator.switch_all_models("gemini-pro")

# Available models:
# - gemini-flash (fast, cheap)
# - gemini-pro (capable)
# - groq/llama-3.3-70b (fast inference)
# - groq/llama-3.1-8b (very fast)
# - groq/mixtral-8x7b (good balance)
```

## Usage Example

```python
from swarm import SwarmCoordinator, SwarmConfig

# Initialize swarm
config = SwarmConfig(
    persist_dir="./swarm_data",
    enable_self_modification=True,
    default_model="gemini-flash"
)
coordinator = SwarmCoordinator(config)

# Start swarm
await coordinator.start()

# Submit a task
task_id = await coordinator.submit_task(
    description="Add user authentication",
    task_type="feature_implementation",
    requirements=["JWT tokens", "Password hashing", "Refresh tokens"],
    priority="high"
)

# Call round table for complex decision
decision = await coordinator.call_round_table(
    topic="Auth strategy",
    question="JWT vs Sessions?",
    agents=["backend", "security", "database"]
)

# Check status
status = coordinator.get_status()
print(f"Active agents: {len(status['agents'])}")
print(f"Pending tasks: {status['pending_tasks']}")

# Stop swarm
await coordinator.stop()
```

## API Endpoints

### Swarm Management
- `GET /api/swarm/status` - Swarm status
- `GET /api/swarm/agents` - List agents
- `GET /api/swarm/agents/{id}` - Agent status
- `GET /api/swarm/activity` - Recent activity

### Model Management
- `GET /api/swarm/models` - List available models
- `POST /api/swarm/models/switch` - Switch models

### Tasks
- `POST /api/swarm/tasks` - Submit task
- `GET /api/swarm/tasks` - List tasks

### Consensus
- `POST /api/swarm/round-table` - Call round table

### WebSocket
- `WS /ws/swarm` - Real-time updates

## Key Innovations

1. **True Multi-Agent**: Each agent has specialized role and expertise
2. **Message Passing**: Clean communication via message bus
3. **Shared Memory**: Collective context all agents can access
4. **Structured Debate**: Round-table discussions for complex decisions
5. **Consensus Building**: Multiple voting mechanisms
6. **Self-Improvement**: Swarm can modify itself
7. **Model Flexibility**: Switch models per-agent or globally
8. **Bias Prevention**: Critic agent challenges groupthink

## Comparison to Original

| Feature | Original | Swarm |
|---------|----------|-------|
| Agents | 5 (auditor, ui, security, performance, mobile) | 10+ specialized |
| Communication | Direct function calls | Message bus |
| Decision Making | Single agent | Consensus |
| Self-Improvement | Meta-agent analysis | Full self-modification |
| Model Switching | Global only | Per-agent |
| Debate | None | Round-table |
| Bias Prevention | None | Critic agent |

## Future Enhancements

- [ ] Visual agent interaction graph
- [ ] Agent specialization learning
- [ ] Cross-project knowledge transfer
- [ ] Human-in-the-loop for critical decisions
- [ ] Agent hiring/firing based on performance
- [ ] Dynamic agent creation for new domains
