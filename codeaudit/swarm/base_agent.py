"""
Base Swarm Agent - foundation for all swarm agents.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from backend.llm_router import llm_call

class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    model: str = "gemini-flash"

class BaseSwarmAgent:
    def __init__(self, config: AgentConfig, coordinator: Any):
        self.config = config
        self.coordinator = coordinator
        self._running = False

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    async def broadcast(self, message: Any, msg_type: str = "AGENT_MESSAGE"):
        await self.coordinator.message_bus.broadcast(self.config.id, message, msg_type)

    async def ask_agent(self, target_id: str, question: str, context: Optional[str] = None) -> str:
        target = self.coordinator._agents.get(target_id)
        if not target:
            return f"Error: Agent {target_id} not found."

        await self.broadcast(f"Asking {target_id}: {question}", "AGENT_QUESTION")
        response = await target.think(f"Question from {self.config.id}: {question}\nContext: {context}")
        await self.coordinator.message_bus.broadcast(target_id, response, "AGENT_ANSWER")
        return response

    async def think(self, prompt: str) -> str:
        """Call LLM to process information."""
        # Wrap prompt with agent's identity
        full_prompt = f"You are {self.config.name}, {self.config.role}.\n\nContext: {self.coordinator._context.get_summary()}\n\nTask: {prompt}"
        return await llm_call(full_prompt, model=self.config.model)

    def get_status(self) -> Dict[str, Any]:
        return {
            "id": self.config.id,
            "name": self.config.name,
            "role": self.config.role,
            "model": self.config.model,
            "running": self._running
        }
