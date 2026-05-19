"""
Base Swarm Agent - foundation for all swarm agents.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from backend.llm_router import llm_call

class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    lifecycle_stage: str = "general"
    integrated_skills: List[str] = Field(default_factory=list)
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
        """Call LLM to process information with integrated lifecycle context."""
        # Enhanced prompt with lifecycle stage and integrated skills
        skills_str = ", ".join(self.config.integrated_skills) if self.config.integrated_skills else "General reasoning"

        full_prompt = (
            f"You are {self.config.name}, {self.config.role}.\n"
            f"Current Lifecycle Stage: {self.config.lifecycle_stage.upper()}\n"
            f"Your Integrated Toolkit: {skills_str}\n\n"
            f"Context: {self.coordinator._context.get_summary()}\n\n"
            f"Task: {prompt}\n\n"
            f"Guidelines: Focus purely on your technical stage. "
            f"Output technical artifacts or structured feedback for the next stage."
        )
        return await llm_call(full_prompt, model=self.config.model)

    def get_status(self) -> Dict[str, Any]:
        return {
            "id": self.config.id,
            "name": self.config.name,
            "role": self.config.role,
            "lifecycle_stage": self.config.lifecycle_stage,
            "integrated_skills": self.config.integrated_skills,
            "model": self.config.model,
            "running": self._running
        }
