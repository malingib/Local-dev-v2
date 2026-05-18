"""
Swarm Coordinator - central management for the agent swarm.
"""
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel

from .message_bus import MessageBus
from .shared_context import SharedContext
from .round_table import RoundTable
from .task_engine import TaskEngine, SwarmTask
from .agents import (
    OrchestratorAgent, CoderAgent, DebuggerAgent, UIDesignerAgent,
    DatabaseAgent, BackendAgent, OptimizerAgent, QAReviewerAgent,
    CriticAgent, SelfModifierAgent
)

class SwarmConfig(BaseModel):
    persist_dir: str = "./swarm_data"
    enable_self_modification: bool = True
    default_model: str = "gemini-flash"

class SwarmCoordinator:
    def __init__(self, config: SwarmConfig):
        self.config = config
        self.message_bus = MessageBus()
        self._context = SharedContext()
        self._round_table = RoundTable(self)
        self._task_engine = TaskEngine(self)
        self._agents: Dict[str, Any] = {}
        self._tasks: List[Dict[str, Any]] = []
        self._running = False
        self._status_listeners: List[Callable] = []

        self._init_agents()

    def _init_agents(self):
        agent_classes = [
            OrchestratorAgent, CoderAgent, DebuggerAgent, UIDesignerAgent,
            DatabaseAgent, BackendAgent, OptimizerAgent, QAReviewerAgent,
            CriticAgent, SelfModifierAgent
        ]
        for cls in agent_classes:
            agent = cls(self)
            self._agents[agent.config.id] = agent

    async def start(self):
        self._running = True
        for agent in self._agents.values():
            await agent.start()

        # Start task engine loop
        self._task_engine_task = asyncio.create_task(self._task_engine.process_queue())

        await self.message_bus.broadcast("SYSTEM", "Swarm Coordinator started", "SYSTEM_EVENT")

    async def stop(self):
        if hasattr(self, "_task_engine_task"):
            self._task_engine_task.cancel()
        self._running = False
        for agent in self._agents.values():
            await agent.stop()
        await self.message_bus.broadcast("SYSTEM", "Swarm Coordinator stopped", "SYSTEM_EVENT")

    async def submit_task(self, description: str, task_type: str = "general", requirements: List[str] = None, priority: str = "normal", dependencies: List[str] = None) -> str:
        task = SwarmTask(description, task_type, dependencies)
        await self._task_engine.submit(task)

        # Keep internal list for legacy API
        self._tasks.append({
            "id": task.id,
            "description": description,
            "type": task_type,
            "status": "pending"
        })

        return task.id

    async def call_round_table(self, topic: str, question: str, agents: Optional[List[str]] = None) -> Dict[str, Any]:
        if agents is None:
            agents = list(self._agents.keys())
        return await self._round_table.conduct_discussion(topic, question, agents)

    def switch_agent_model(self, agent_id: str, model: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent:
            agent.config.model = model
            return True
        return False

    def switch_all_models(self, model: str):
        for agent in self._agents.values():
            agent.config.model = model

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "agents": [a.get_status() for a in self._agents.values()],
            "pending_tasks": len([t for t in self._tasks if t["status"] == "pending"]),
            "total_tasks": len(self._tasks)
        }

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        agent = self._agents.get(agent_id)
        return agent.get_status() if agent else None

    def get_available_models(self) -> List[str]:
        return ["gemini-flash", "gemini-pro", "groq/llama-3.3-70b", "groq/llama-3.1-8b", "groq/mixtral-8x7b"]

    async def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.message_bus.get_history(limit)

    def on_status_change(self, callback: Callable):
        self._status_listeners.append(callback)

    async def list_sessions(self):
        # Implementation for session listing
        return []

    async def create_session(self, project_path: str, github_url: Optional[str] = None):
        from backend.api import CreateSessionRequest, create_session
        req = CreateSessionRequest(project_path=project_path, github_url=github_url)
        res = await create_session(req)
        return res["session_id"]

    async def get_session(self, session_id: str):
        from backend.api import get_session
        return await get_session(session_id)

    async def list_sessions(self):
        from backend.api import list_sessions
        return await list_sessions()
