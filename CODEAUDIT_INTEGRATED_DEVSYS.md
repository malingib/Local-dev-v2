# CodeAudit Integrated Dev-Sys: The Engineering Factory

## 1. Overview
The **Integrated Dev-Sys** is a high-fidelity development system that combines a stage-gated technical lifecycle with the advanced features of world-class AI agents (Hermes, OpenCode, Windmill, Karpathy/HALO). It is a non-managerial, technical-first pipeline where specialized agents use sophisticated toolkits to build, verify, and evolve software.

---

## 2. Integrated Lifecycle & Features

### **Stage 1: Architecture & Intelligence (The Blueprint)**
*   **Agents:** Architect (Backend/DB), Designer.
*   **Hermes Integration:** **Dialectic User Modeling**. The Architect learns the user's architectural style and project-specific "DNA" to ensure the blueprint aligns with long-term goals.
*   **OpenCode Integration:** **AST-Level Intelligence**. The Architect uses L1-L2 extraction to understand existing project structures before proposing changes.
*   **Goal:** A Technical Specification that is context-aware and architecturally sound.

### **Stage 2: Precision Implementation (The Build)**
*   **Agents:** Software Engineer (Coder).
*   **Windmill Integration:** **DAG-Based Task Execution**. Large implementation tasks are broken into a Directed Acyclic Graph of sub-tasks. The Coder executes these in parallel or sequence based on dependency logic, ensuring no deadlocks or redundant work.
*   **Integrated Toolkits:** Unit Test Generation, Documentation, and Component Implementation are native methods, not external "addons."

### **Stage 3: High-Fidelity Verification (The Gatekeeper)**
*   **Agents:** QA Engineer, Security Auditor.
*   **OpenCode/L5 Integration:** **Deep Analysis Layers**. Verification uses L3 (Call Graph), L4 (Control Flow), and L5 (Data Flow) extraction to trace code paths and identify hidden vulnerabilities that standard scanners miss.
*   **Trace Integration:** **Real-time Thinking Trace**. Every verification step is recorded in the `agent_loop.db`, allowing for "Self-Improvement" analysis if bugs slip through.

### **Stage 4: Autonomous Evolution (The Refiner)**
*   **Agents:** Performance Engineer, Self-Modifier.
*   **Karpathy/HALO Integration:** **Autonomous Experiment Loops**. The system establishes a baseline, runs time-budgeted experiments (modifying code directly), evaluates metrics (val_bpb, latency, memory), and keeps/discards based on hard data.
*   **Self-Modification:** The Self-Modifier uses results from the Experiment Engine to update the system prompts of *other agents* in the lifecycle, creating a recursive improvement loop.

---

## 3. The "Dev-Flow" Protocol

1.  **Ingestion:** Architect ingests codebase via **Fast File Search** (fff.nvim-inspired) and **Knowledge Graph** (graphify-inspired).
2.  **Creation:** Coder executes the **Windmill-style DAG**.
3.  **Audit:** Security/QA perform **L1-L5 Deep Extraction** audits.
4.  **Refinement:** Performance/Self-Modifier run **HALO-style Experiment Loops**.

---

## 4. Key Innovations: The "Super-Agent" Edge

*   **No Unstructured Chatter:** All communication is artifact-driven (e.g., a "Data Flow Graph" passed from Auditor to Coder).
*   **Embedded Knowledge:** The **FTS5 Wiki** and **Dialectic Profile** act as a persistent RAG layer that agents access automatically during their lifecycle stage.
*   **Performance Accountability:** Every lifecycle stage is benchmarked. If the Evolution stage finds a performance regression, it identifies exactly which Stage 2 task caused it.
