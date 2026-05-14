---
name: agents
description: "Use when: creating new agents, modifying agent logic, configuring agent behavior, or debugging agent communication. Enforces base_agent inheritance, async patterns, YAML configuration, and message bus architecture."
applyTo: "codeaudit/agents/**,codeaudit/backend/orchestrator.py"
---

# Agent Development Instructions

## Agent Architecture

### Base Class & Inheritance
All agents inherit from `agents/base_agent.py`:

```python
from agents.base_agent import BaseAgent
from models import Message, EventLog

class SecurityAgent(BaseAgent):
    """Finds security vulnerabilities and auth gaps."""
    
    def __init__(self, config: Dict):
        super().__init__(
            name="security",
            config=config,
            role="Security specialist agent",
        )
    
    async def analyze(self, code: str) -> List[Finding]:
        """Async main execution method."""
        hypotheses = await self._generate_hypotheses(code)
        findings = []
        for hypothesis in hypotheses:
            result = await self._test_hypothesis(hypothesis)
            if result.confidence > 0.85:
                findings.append(Finding(
                    type="security",
                    hypothesis=hypothesis,
                    confidence=result.confidence,
                    recommendation=result.fix,
                ))
        return findings
```

### Required Methods
- `analyze(self, code: str)` — Main async entry point; receives code, returns findings
- `_generate_hypotheses(self, code)` — Creates ranked hypothesis list
- `_test_hypothesis(self, hypothesis)` — Runs experiments, returns confidence + result
- `_format_finding(self, hypothesis, result)` — Structures Finding for frontend

### Async-First Pattern
```python
async def analyze(self, code: str) -> List[Finding]:
    # All I/O operations use await
    llm_response = await self._call_llm(code)
    test_result = await self._run_experiment(llm_response)
    return self._extract_findings(test_result)

async def _call_llm(self, prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(self.llm_endpoint, json={"prompt": prompt}) as resp:
            return await resp.json()
```

## Message Bus & Communication

### Event Flow
```
Agent 1                Agent 2                Orchestrator
  │                      │                        │
  ├─ publish event ─────────────────────────────>│
  │                      │          ┌─────────────┤
  │                      │          │ routes to   │
  │                      │<─────────┤ subscribers │
  │                      │          └─────────────┤
  │                      ├─ publish reply ───────>│
```

### Publishing Events
```python
# In your agent's analyze method:
await self.bus.publish(Message(
    type="hypothesis_generated",
    agent_id=self.name,
    payload={"hypothesis": hyp, "confidence": 0.75},
))

# Other agents can subscribe:
await self.bus.subscribe("hypothesis_generated", self.handle_hypothesis)
```

### Message Structure
```python
# models.py defines Message
from pydantic import BaseModel

class Message(BaseModel):
    type: str                          # e.g., "hypothesis_generated"
    agent_id: str                      # originating agent name
    timestamp: datetime
    payload: Dict[str, Any]            # event-specific data
    
class EventLog(BaseModel):
    session_id: str
    events: List[Message]              # immutable append-only log
```

## Configuration (YAML)

### Agent Enable/Disable
```yaml
# codeaudit/config/config.yaml
agents:
  enabled:
    - auditor
    - ui
    - security
    - performance
    - mobile
  disabled:
    - performance_runtime  # skip Lighthouse (no running app)
    - mobile_responsiveness # skip mobile checks
    
  security:
    max_scan_depth: 5
    severity_threshold: 0.7
    
  performance:
    budget_kb: 250
    lighthouse_threshold: 80
```

### Testing Locally
Before committing:
1. Disable slow agents in `config.yaml`
2. Swap LLM model to faster (Groq) version
3. Run agent in isolation
```python
# Test script
agent = SecurityAgent(config)
findings = await agent.analyze(sample_code)
print(findings)
```

## LLM Integration

### Multi-Provider Routing
Use `backend/llm_router.py` for resilient LLM calls:

```python
from backend.llm_router import LLMRouter

class SecurityAgent(BaseAgent):
    def __init__(self, config: Dict):
        super().__init__(name="security", config=config)
        self.llm = LLMRouter(
            primary="gemini",           # Google Gemini
            fallback="groq",            # Groq fallback
            config=config,
        )
    
    async def _call_llm(self, prompt: str) -> str:
        response = await self.llm.call(prompt, temperature=0.7)
        return response
```

### Configuration
```python
# models.py or config
class LLMConfig(BaseModel):
    primary_model: str = "gemini-pro"       # from config.yaml
    fallback_model: str = "llama-3.3-70b"
    temperature: float = 0.7
    max_tokens: int = 2000
```

## Session Persistence

### Event Sourcing
All agent activity is recorded in immutable JSON event logs:

```python
# backend/session_store.py
class SessionStore:
    async def log_event(self, session_id: str, event: Message):
        """Append-only: never overwrites, enables replay."""
        session = await self.get_session(session_id)
        session.events.append(event)
        await self.save(session_id, session)
    
    async def get_session(self, session_id: str) -> EventLog:
        # Load from codeaudit/sessions/<id>.json
        with open(f"sessions/{session_id}.json") as f:
            return EventLog(**json.load(f))
```

### Debugging Sessions
```bash
# List all sessions
ls codeaudit/sessions/

# Inspect a session (JSON)
cat codeaudit/sessions/3302a3ae.json | jq '.events[] | select(.type=="finding")'

# Copy to new machine and replay
cp codeaudit/sessions/3302a3ae.json /other/machine/codeaudit/sessions/
# Resume on other machine — picks up from last event
```

## Hypothesis-Driven Debugging

### Confidence Scoring (>85% to propose fix)

```python
async def analyze(self, code: str) -> List[Finding]:
    hypotheses = await self._generate_hypotheses(code)  # ranked by likelihood
    findings = []
    
    for hypothesis in hypotheses:
        # Run multiple experiments to refine confidence
        results = []
        for experiment in hypothesis.experiments:
            result = await self._run_experiment(experiment)
            results.append(result)
        
        # Score based on convergence
        confidence = self._calculate_confidence(results)
        
        if confidence > 0.85:  # ✅ Only propose if high confidence
            findings.append(self._format_finding(hypothesis, confidence))
        else:
            # Log low-confidence for future learning
            await self.bus.publish(Message(
                type="low_confidence_finding",
                agent_id=self.name,
                payload={"hypothesis": hypothesis, "confidence": confidence},
            ))
    
    return findings
```

### Ranking & Prioritization
```python
def _generate_hypotheses(self, code: str) -> List[Hypothesis]:
    """Generate ranked by likelihood (NLP similarity, pattern frequency, etc.)"""
    hypotheses = [
        Hypothesis(
            title="SQL injection in query builder",
            likelihood=0.95,  # Very common pattern
            fix_complexity="medium",
        ),
        Hypothesis(
            title="Unvalidated user input",
            likelihood=0.88,
            fix_complexity="low",
        ),
    ]
    return sorted(hypotheses, key=lambda h: h.likelihood, reverse=True)
```

## Error Handling

### FastAPI Exception Patterns
Always raise descriptive exceptions for frontend UI:

```python
from fastapi import HTTPException

async def analyze(self, code: str) -> List[Finding]:
    if not code.strip():
        raise HTTPException(
            status_code=400,
            detail="Code cannot be empty",
        )
    
    try:
        findings = await self._run_analysis(code)
    except LLMRateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded; try fallback model",
        )
    except Exception as e:
        # Log for debugging
        logger.error(f"Agent {self.name} error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal agent error; check logs",
        )
    
    return findings
```

## Testing Checklist

When adding a new agent:
- [ ] Inherits from `BaseAgent`
- [ ] All methods are `async def`
- [ ] `analyze(code: str) -> List[Finding]` implemented
- [ ] Hypothesis generation + confidence scoring
- [ ] Publishes events to message bus
- [ ] Pydantic models for all data structures
- [ ] LLM calls via `LLMRouter` (multi-provider)
- [ ] Fails gracefully with descriptive exceptions
- [ ] Tested locally with `config.yaml` agent disabled
- [ ] Session logs show expected events

## Common Patterns

### Pattern: Parallel Hypothesis Testing
```python
async def analyze(self, code: str) -> List[Finding]:
    hypotheses = await self._generate_hypotheses(code)
    # Test all in parallel
    results = await asyncio.gather(*[
        self._test_hypothesis(h) for h in hypotheses
    ])
    return [self._format_finding(h, r) 
            for h, r in zip(hypotheses, results) 
            if r.confidence > 0.85]
```

### Pattern: Rejection Memory
```python
# In agent __init__:
self.rejected_findings = await preferences.load_rejected(self.name)

# Before proposing:
if finding.id not in self.rejected_findings:
    findings.append(finding)  # Only if not previously rejected
```

### Pattern: Stack Detection
```python
# Auto-detect project framework
from backend.stack_detector import StackDetector

detector = StackDetector(code, file_paths)
stack = await detector.detect()  # returns {"framework": "react", "version": "19"}

# Tailor agent behavior per stack
if stack.framework == "react":
    hypotheses.extend(await self._react_specific_checks(code))
```
