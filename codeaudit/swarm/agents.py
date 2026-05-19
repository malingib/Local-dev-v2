"""
Swarm Agents - specialized agents for the Dev-Sys technical lifecycle.
"""
from typing import Any, List
from .base_agent import BaseSwarmAgent, AgentConfig

# ─── Stage 1: Architecture & Design ──────────────────────────────────────────

class ArchitectAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="architect",
            name="System Architect",
            role="Defines technical specifications, API contracts, and schema designs.",
            lifecycle_stage="architecture",
            integrated_skills=["Dialectic User Modeling", "Architecture Analysis", "Schema Design", "API Spec Generation"]
        ), coordinator)

class UIDesignerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="ui_designer",
            name="UI Designer",
            role="Creates visual interfaces, accessibility patterns, and UX specifications.",
            lifecycle_stage="architecture",
            integrated_skills=["Design System Intelligence", "HTML Prototype Generator", "WCAG Compliance Audit"]
        ), coordinator)

# ─── Stage 2: Implementation ──────────────────────────────────────────────────

class CoderAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="coder",
            name="Software Engineer",
            role="Implements features and logic based on the architectural blueprint.",
            lifecycle_stage="implementation",
            integrated_skills=["DAG-Based Implementation", "Unit Test Generation", "Code Refactoring"]
        ), coordinator)

class BackendAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="backend",
            name="Backend Architect",
            role="Implements service logic, security layers, and API integrations.",
            lifecycle_stage="implementation",
            integrated_skills=["API Implementation", "Security Pattern Integration", "Service Orchestration"]
        ), coordinator)

class DatabaseAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="database",
            name="Database Expert",
            role="Implements database schemas, migrations, and query logic.",
            lifecycle_stage="implementation",
            integrated_skills=["Schema Implementation", "SQL Migration Generation", "Data Modeling"]
        ), coordinator)

# ─── Stage 3: Verification & Security ─────────────────────────────────────────

class QAReviewerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="qa_reviewer",
            name="QA Engineer",
            role="Validates implementation against specifications and runs test suites.",
            lifecycle_stage="verification",
            integrated_skills=["Integration Test Planning", "Regression Analysis", "AST-Level Verification"]
        ), coordinator)

class SecurityAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="security",
            name="Security Auditor",
            role="Scans for vulnerabilities, secret leaks, and security anti-patterns.",
            lifecycle_stage="verification",
            integrated_skills=["Vulnerability Scanning", "Secret Detection", "Data Flow Analysis (L5)"]
        ), coordinator)

class DebuggerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="debugger",
            name="Support Engineer",
            role="Traces code execution to find root causes of defects identified in verification.",
            lifecycle_stage="verification",
            integrated_skills=["Root Cause Analysis", "Trace Extraction", "Bug Fix Generation"]
        ), coordinator)

# ─── Stage 4: Evolution & Optimization ────────────────────────────────────────

class OptimizerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="optimizer",
            name="Performance Engineer",
            role="Identifies and removes performance bottlenecks.",
            lifecycle_stage="evolution",
            integrated_skills=["Performance Profiling", "Memory Leak Analysis", "Latency Optimization"]
        ), coordinator)

class SelfModifierAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="self_modifier",
            name="System Evolver",
            role="Refines agent logic and system prompts based on recent performance data.",
            lifecycle_stage="evolution",
            integrated_skills=["Autonomous Experiment Loops", "HALO Recursive Improvement", "Metric Evaluation"]
        ), coordinator)

    async def reflect_and_optimize(self):
        """Analyze recent activity and suggest system-wide improvements."""
        activity = await self.coordinator.get_recent_activity(limit=100)
        summary = "\n".join([f"[{m['agent']}] {m['message']}" for m in activity])

        prompt = (
            f"Analyze the following swarm activity and suggest improvements to agent toolkits or lifecycle hand-offs:\n\n"
            f"{summary}\n\n"
            f"Focus on reducing unstructured chatter and improving artifact quality."
        )
        suggestions = await self.think(prompt)

        await self.broadcast(f"System Evolution Proposal: {suggestions}", "SYSTEM_PROPOSAL")
        return suggestions
