# VS Code Copilot Customizations for CodeAudit

This directory contains workspace-wide customizations that guide Copilot agent behavior across the CodeAudit full-stack project.

## Files Overview

### `copilot-instructions.md`
**Scope**: Entire workspace  
**Auto-loaded**: ✅ Yes (on every chat request)

The primary workspace guidelines document. Covers:
- Code style expectations (frontend React/TypeScript, backend Python/FastAPI)
- Architecture principles and design decisions
- Build/test commands
- Project conventions and quirks
- API keys setup and environment issues

**When to update**: Major architecture changes, new patterns, significant quirks discovered

---

## Subdirectories

### `instructions/`
File-level guidance that auto-loads when you're working in specific areas.

#### `frontend.instructions.md`
**Auto-loads for**: `app/src/**` files  
**Use when**: Building React components, styling, state management

Covers:
- Component architecture (UI primitives `components/ui/`, feature components `components/`)
- Zustand store patterns and WebSocket integration
- Forms with `react-hook-form` + `zod`
- Tailwind + shadcn/ui styling
- Type safety with path aliases (`@/*`)
- API integration with `lib/api.ts`
- Development tasks and troubleshooting

**Example**: Edit `app/src/components/ActivityFeed.tsx` → agent loads this instruction automatically.

#### `agents.instructions.md`
**Auto-loads for**: `codeaudit/agents/**` and `codeaudit/backend/orchestrator.py` files  
**Use when**: Building new agents, modifying agent logic

Covers:
- Agent base class inheritance and async patterns
- Message bus communication and event publishing
- YAML configuration for enabling/disabling agents
- LLM integration via `LLMRouter` (multi-provider fallback)
- Session persistence (event-sourced JSON logs)
- Hypothesis-driven debugging with confidence scoring
- Error handling and testing checklist

**Example**: Create `codeaudit/agents/new_agent.py` → agent loads this instruction.

---

### `prompts/`
Focused prompts invoked via `/command` syntax in Copilot chat (e.g., `/audit-frontend`).

#### `/audit-frontend`
Complete frontend audit without modifications. Generates findings report for:
- UI Issues (accessibility, design quality)
- Performance (re-renders, bundle size, images)
- Mobile responsiveness
- Runtime errors

**Usage**: Type `/audit-frontend` in chat to kick off comprehensive analysis

#### `/fix-performance`
Targets performance bottlenecks. Auto-applies safe optimizations (lazy loading, memoization) and stages complex changes for visual approval.

**Usage**: Type `/fix-performance` when frontend is slow

#### `/debug-session`
Inspects and replays CodeAudit session event logs (JSON files in `codeaudit/sessions/`). Traces agent execution, identifies errors, suggests fixes.

**Usage**: Type `/debug-session` to troubleshoot a failed or stalled audit

---

### `hooks/`
Deterministic validation rules executed at agent lifecycle points (before/after tool use).

#### `pre-commit.json`
Validates code before modifications:

| Validation | Triggers On | Severity | Purpose |
|-----------|-----------|----------|---------|
| TypeScript build | `app/src/**` React files | **Fail** | Enforces type safety (strict mode) |
| ESLint | React components | Warn | Catches linting violations |
| Python syntax | `codeaudit/` Python files | **Fail** | Validates Python on changes |
| Pydantic models | `models.py` | **Fail** | Critical validation model file |
| Import paths | All TypeScript | Warn | Ensures `@/*` path aliases |
| Session JSON | `codeaudit/sessions/*.json` | **Fail** | Blocks corrupted session files |
| Config YAML | `config/config.yaml` | **Fail** | Validates YAML syntax |

**Behavior**:
- **Fail**: Agent blocks the edit and reports the error
- **Warn**: Agent shows warning but allows the edit

---

## Discovery & Auto-Loading

Copilot discovers and auto-loads customizations based on:

1. **File being edited**: Matches `applyTo` glob patterns
   - Editing `app/src/components/Button.tsx` → loads `instructions/frontend.instructions.md`
   - Editing `codeaudit/agents/security.py` → loads `instructions/agents.instructions.md`

2. **Chat context**: Descriptions in frontmatter
   - Type `/audit-frontend` → loads `prompts/audit-frontend.prompt.md`
   - Ask "debug my session" → agent recognizes request, offers `/debug-session`

3. **Lifecycle hooks**: Triggered on tool use
   - Before editing `app/src/App.tsx` → runs TypeScript validation hook
   - After creating `models.py` change → validates Pydantic syntax

---

## Maintenance & Updates

### Adding a New Instruction
1. Create file in `instructions/`
2. Add frontmatter with `name`, `description`, `applyTo` (glob pattern)
3. Follow template: problem statement → patterns → examples → checklist

### Adding a New Prompt
1. Create file in `prompts/`
2. Add frontmatter with `name`, `description`
3. Structure: What it Does → Usage → Process → Output Example → Next Steps

### Modifying Hooks
1. Edit `hooks/pre-commit.json`
2. Each task has `condition` (file glob) and `command` (shell validation)
3. Test locally before committing

---

## Quick Reference

| Need | Location | Type |
|------|----------|------|
| Full workspace guidelines | `copilot-instructions.md` | Instructions |
| React component help | `instructions/frontend.instructions.md` | Instructions |
| Agent development | `instructions/agents.instructions.md` | Instructions |
| Run full frontend audit | `prompts/audit-frontend.prompt.md` | Prompt |
| Fix performance issues | `prompts/fix-performance.prompt.md` | Prompt |
| Debug a session | `prompts/debug-session.prompt.md` | Prompt |
| Enforce code quality | `hooks/pre-commit.json` | Hooks |

---

## Testing Customizations

### Test an Instruction
```bash
# Edit a file in the matching scope, e.g., app/src/components/Test.tsx
# Copilot should auto-load the frontend.instructions.md

# Or ask explicitly:
# "Based on the frontend instructions, help me..."
```

### Test a Prompt
```
# In Copilot chat, type:
/audit-frontend

# Or:
/debug-session
```

### Test a Hook
```bash
# Modify codeaudit/backend/models.py with a syntax error
# Try to save/commit → should fail with validation error
```

---

## Conventions

- **Frontmatter**: YAML between `---` markers; always include `name`, `description`
- **File paths**: Use relative paths (e.g., `backend/models.py`); not absolute
- **Code examples**: Include before/after, with comments explaining pattern
- **Links**: Reference related docs (e.g., `SYSTEM_SUMMARY.md`, `README.md`)
- **Plain language**: Write for humans first; make intent clear

---

## Related Documentation

- [.github/copilot-instructions.md](.github/copilot-instructions.md) — Working version of root instructions
- [codeaudit/README.md](../codeaudit/README.md) — Backend quick start, configuration
- [codeaudit/SYSTEM_SUMMARY.md](../codeaudit/SYSTEM_SUMMARY.md) — Architecture, agent roles
- [codeaudit/SWARM_ARCHITECTURE.md](../codeaudit/SWARM_ARCHITECTURE.md) — Agent message bus design
- [app/info.md](../app/info.md) — Frontend component inventory

---

## Notes for Teams

- **Version control**: Commit `.github/` to track customizations across team members
- **Sync URLs**: If you have references to GitHub branches, ensure `applyToUrl` patterns match
- **Conflict resolution**: If two instructions match one file, more specific `applyTo` wins (alphabetical order)
- **Passwords/secrets**: Never store API keys in `.github/`; use `.env` files (git-ignored)
