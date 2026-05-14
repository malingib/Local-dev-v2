---
name: debug-session
description: Inspect and replay a CodeAudit session for troubleshooting. Loads event history from JSON, analyzes agent outputs, and suggests fixes for failed operations.
---

# Debug Session

## What This Does
Troubleshoots a CodeAudit session by replaying its event log:
- **Loads session JSON**: From `codeaudit/sessions/<id>.json`
- **Traces agent execution**: Shows what each agent did, confidence scores, LLM calls
- **Identifies errors**: Failed hypotheses, low-confidence findings, LLM rate limits
- **Suggests fixes**: Re-run with different config, change models, disable slow agents

## Usage
Run this prompt when:
- An audit stalled or produced no findings
- An agent produced low-confidence findings
- You want to understand why a finding was proposed
- You need to reproduce an issue on another machine

## Process

### 1. Load Session
```
Enter session ID: 3302a3ae
Loading: codeaudit/sessions/3302a3ae.json (142 events)
```

### 2. Display Timeline
```
[00:00] Session created
  • Config: hypothesis_depth=3, confidence_threshold=0.85
  • Project: local_path=/home/user/myapp
  • Agents: auditor, ui, security, performance, mobile

[00:02] Auditor agent started
  • Generated 8 hypotheses
  • Testing: "null pointer in reducer"
  • Confidence: 0.76 (below threshold, not proposed)

[00:05] UI agent started
  • Found: Missing alt text (accessibility)
  • Confidence: 0.98 ✅ PROPOSED

[00:08] Performance agent started
  • LLM call failed: rate_limit_exceeded
  • Retry with Groq fallback...
  • Success (0.2s)
  • Generated 5 findings

[00:15] Session complete
  • Total findings: 23
  • Proposed: 18
  • Low-confidence: 5 (logged)
```

### 3. Analyze Issues
```
⚠️  ISSUES DETECTED:

1. Performance agent: Rate limit hit
   Suggestion: Run again with `models.performance: "groq/..."` to skip rate limit

2. Auditor agent: 5/8 hypotheses below 85% threshold
   Suggestion: Lower confidence_threshold to 0.75 to surface more findings

3. Mobile agent: Only 1 finding (expected 3-5)
   Suggestion: Check if mobile agent is enabled in config.yaml
```

### 4. Debug Options

**Replay with Different Config**
```bash
# Current config led to rate limit; try Groq instead:
python run.py --dev --config-override models.primary=groq/llama-3.3-70b
```

**Re-run Session**
```bash
# Copy session to new machine, resume where it left off:
cp codeaudit/sessions/3302a3ae.json /other/machine/codeaudit/sessions/
cd /other/machine/codeaudit
python run.py  # Picks up from last event
```

**Export Event Log**
```bash
# View all agent events for debugging:
cat codeaudit/sessions/3302a3ae.json | jq '.events[] | 
  select(.type=="hypothesis_generated" or .type=="finding") | 
  {timestamp, agent_id, confidence: .payload.confidence}'
```

## Event Types in Session Log
- `session_created` — Audit initialized
- `hypothesis_generated` — Agent proposed ranked hypotheses
- `experiment_run` — Agent tested hypothesis (result + confidence)
- `finding` — Proposed finding (passed 85% threshold)
- `low_confidence_finding` — Finding below threshold (for learning)
- `llm_call` — LLM request/response + latency
- `error` — Agent or system error + exception
- `session_complete` — Audit finished

## Example: Inspect All Findings
```bash
jq '.events[] | select(.type=="finding") | {
  agent: .agent_id,
  confidence: .payload.confidence,
  issue: .payload.recommendation
}' codeaudit/sessions/3302a3ae.json
```

## Next Steps
- Use `/audit-frontend` to re-run audit with fixed config
- Disable slow/failing agents in `config.yaml` before next run
- Report LLM issues (rate limits, timeouts) for resilience improvements
