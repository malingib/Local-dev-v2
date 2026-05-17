# CodeAudit System Review

## Current State

### 1. Frontend (`app/`)
- **Tech Stack:** React 19, Vite, Tailwind CSS, shadcn/ui, Zustand.
- **Pages:** Extensive set of pages covering Dashboard, Sessions, Agent (Soul), Skills, Wiki, Buddy, Experiments, and more.
- **Architecture:** Good separation of concerns in `src/lib` (api, store).
- **Observation:** The UI is quite advanced and feature-rich, but it lacks a dedicated view for the "Agent Swarm" activity as described in the documentation.

### 2. Backend (`codeaudit/backend/`)
- **Tech Stack:** Python, FastAPI, Pydantic, Google Gemini/Groq.
- **Features:**
    - Original Audit system (Orchestrator + specialized agents).
    - "Hermes" style features: Soul (agent identity), Skills (tool library), Wiki (knowledge base), Buddy (companion).
    - Autoresearch/Experiments: Staged code improvement with confidence scores.
- **Architecture:** Modular, with clear entry points in `api.py`.

### 3. Agent Swarm (`codeaudit/swarm/` - MISSING)
- **Status:** Documented in `SWARM_ARCHITECTURE.md` and `SYSTEM_SUMMARY.md`, but the implementation directory and files are missing.
- **Target Architecture:** Multi-agent system with Message Bus, Shared Context, Round Table discussions, and Consensus mechanisms.
- **Inspiration:** Kimi, Andrej Karpathy's LLM OS, Windmill (task-based), T3Code (modern UI).

## Identified Gaps

1. **Missing Swarm Core:** The entire `swarm` module needs implementation to match the documentation.
2. **Integration:** `swarm_api.py` exists but is currently a wrapper around a missing module. It needs to be fully functional.
3. **Visualization:** The frontend needs a way to visualize the swarm's message bus activity, similar to a "round table" or "war room" view.
4. **Task Orchestration:** While `Orchestrator` exists, it follows a more traditional sequential/parallel pattern. A more "Windmill-like" task-based execution model (DAGs, state machine) would be more robust for complex swarm interactions.

## Proposed Improvements (Mirroring OpenCode + Windmill + T3Code)

### Architecture (Windmill Inspiration)
- **Task-Based Execution:** Instead of hardcoded agent loops, implement a flexible task queue where agents pick up tasks, post results, and trigger downstream tasks.
- **State Persistence:** Better checkpointing of swarm state to allow for long-running audits and recovery.

### Swarm Interaction (OpenCode Inspiration)
- **Extensible Skills:** Deepen the "Skills" integration so agents can dynamically load and use new tools during the audit.
- **Self-Modification:** Strengthen the "Self-Modifier" agent to actually update system prompts and coordination logic based on performance.

### User Interface (T3Code Inspiration)
- **Collaborative Canvas:** A view showing agents discussing and voting on fixes.
- **Real-time Trace:** Detailed visualization of the thinking process (L1-L5 layers: AST, Call Graph, CFG, etc.) as implemented in `code_extractor.py`.

## Action Plan
1. Implement the `codeaudit/swarm/` core (Message Bus, Context, Consensus, Coordinator, Agents).
2. Wire the `swarm` module into `swarm_api.py`.
3. Enhance the frontend with a Swarm visualization page.
4. Refactor the `Orchestrator` to optionally use the Swarm for deep audits.
