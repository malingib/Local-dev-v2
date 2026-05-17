"""
Swarm Agents - specialized agents for the swarm.
"""
from typing import Any
from .base_agent import BaseSwarmAgent, AgentConfig

class OrchestratorAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="orchestrator",
            name="Swarm Orchestrator",
            role="Central coordinator. Breaks down tasks and monitors progress."
        ), coordinator)

class CoderAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="coder",
            name="Coder",
            role="Software engineer. Writes clean, maintainable code."
        ), coordinator)

class DebuggerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="debugger",
            name="Debugger",
            role="Bug hunter. Analyzes error reports and proposes fixes."
        ), coordinator)

class UIDesignerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="ui_designer",
            name="UI Designer",
            role="Frontend & UX expert. Ensures accessibility and consistency."
        ), coordinator)

class DatabaseAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="database",
            name="Database Expert",
            role="Data architect. Schema design and query optimization."
        ), coordinator)

class BackendAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="backend",
            name="Backend Architect",
            role="API & service architect. Security and scalability expert."
        ), coordinator)

class OptimizerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="optimizer",
            name="Performance Optimizer",
            role="Finds bottlenecks and optimizes performance."
        ), coordinator)

class QAReviewerAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="qa_reviewer",
            name="QA Reviewer",
            role="Code review and best practice enforcement."
        ), coordinator)

class CriticAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="critic",
            name="Critic",
            role="Devil's advocate. Challenges assumptions and prevents groupthink."
        ), coordinator)

class SelfModifierAgent(BaseSwarmAgent):
    def __init__(self, coordinator: Any):
        super().__init__(AgentConfig(
            id="self_modifier",
            name="Self-Modifier",
            role="Meta-improver. Analyzes and improves the swarm itself."
        ), coordinator)

    async def reflect_and_optimize(self):
        """Analyze recent activity and suggest prompt improvements."""
        activity = await self.coordinator.get_recent_activity(limit=100)
        summary = "\n".join([f"[{m['agent']}] {m['message']}" for m in activity])

        prompt = f"Analyze the following swarm activity and suggest improvements to agent roles or communication patterns:\n\n{summary}"
        suggestions = await self.think(prompt)

        await self.broadcast(f"Self-Improvement Analysis: {suggestions}", "SYSTEM_PROPOSAL")
        return suggestions
