# CodeAudit Org-Sys: Organizational System for Autonomous Agents

## 1. The Vision: From Flat Swarm to Structured Organization

Current multi-agent systems often suffer from "consensus fatigue" and "unstructured chatter." CodeAudit Org-Sys moves away from the flat "Round Table" model toward a **Hierarchical Departmental Structure**. This ensures clear accountability, reduces redundant processing, and organizes agent capabilities into specialized toolkits.

---

## 2. The Organizational Hierarchy

### **Executive Leadership (L1)**
*   **CEO (Orchestrator):** Strategic alignment, final decision-making, and high-level goal setting.
*   **CTO (Self-Modifier):** System health, architectural integrity, and technological evolution (recursive improvement).

### **Management & Operations (L2)**
*   **Project Manager (PM - New Role):** Task breakdown, dependency management, and departmental coordination. Replaces simple keyword-based task assignment.
*   **QA Lead (QA Reviewer):** Standardizes quality across all departments.

### **Departmental Units (L3)**
Agents are organized into "Departments." Each department has its own **Specialized Toolkit** (formerly "Skills").

#### **A. Product & Design Department**
*   **UI/UX Designer:** Responsible for visual consistency, accessibility, and user experience.
*   **Tools:** Design System Intelligence, HTML Prototype Generator, Anti-Slop Design Audit.

#### **B. Engineering Department**
*   **Software Engineer (Coder):** General implementation and refactoring.
*   **Backend Architect:** API design, service logic, and security integration.
*   **Database Architect:** Schema design and query efficiency.
*   **Tools:** Unit Test Generator, Integration Test Planner, Database Query Optimization.

#### **C. Reliability & Performance Department**
*   **Site Reliability Engineer (SRE - Optimizer):** Performance profiling and bottleneck removal.
*   **Support Engineer (Debugger):** Root cause analysis and legacy code fixes.
*   **Tools:** Performance Profiler, Memory Analysis, Dockerfile Review.

#### **D. Independent Assurance Unit**
*   **Security Auditor:** Vulnerability scanning and supply chain audit.
*   **Critic (The Contrarian):** Independent peer review, challenges departmental assumptions.
*   **Tools:** Vulnerability Scanner, Secret Detection, Supply Chain Audit.

---

## 3. Organized Workflows (Standard Operating Procedures)

### **A. Task Lifecycle (Linear vs. Consensus)**
1.  **Incoming Request:** CEO analyzes the goal.
2.  **Strategic Briefing:** PM creates a **Task Execution Plan (TEP)** with clear dependencies.
3.  **Departmental Execution:** Assigned department works on the task. They use their *internal* tools without needing broad swarm consensus.
4.  **Departmental Review:** If Engineering finishes code, it MUST go to the **QA Reviewer** before the CEO.
5.  **Assurance Gate:** For "Critical" changes, the **Critic** is summoned to find flaws.
6.  **Final Sign-off:** CEO approves the release.

### **B. Reducing "Round Table" Noise**
*   **Local Decisions:** Departments make technical decisions within their domain.
*   **Escalation:** A "Round Table" (now renamed **Management Sync**) is ONLY called if:
    *   A conflict arises between departments (e.g., UI needs a change that Backend says is impossible).
    *   The **Critic** flags a high-severity risk.

---

## 4. Feature/Skill Integration

Instead of a generic "Skills Library" available to all, skills are "hard-wired" into the identity of the departments:

*   **Engineering Toolkit:** Inherits all Code Review, Testing, and Performance skills.
*   **Assurance Toolkit:** Inherits all Security and Audit skills.
*   **Design Toolkit:** Inherits all Frontend and Design Intelligence skills.

This reduces "Prompt Confusion" where agents try to use tools they aren't optimized for.

---

## 5. Strategic Roadmap for Implementation

1.  **Refactor `agents.py`:** Update agent roles to reflect departmental hierarchy.
2.  **Implement `PM` Agent:** Move the complex task breakdown logic from `TaskEngine` to a dedicated `ProjectManagerAgent`.
3.  **Departmental Namespacing:** Update `SkillsLibrary` to tag tools with `required_department`.
4.  **Replace RoundTable logic:** Modify `coordinator.py` to follow the "Chain of Command" workflow rather than broadcasting every message to everyone.
