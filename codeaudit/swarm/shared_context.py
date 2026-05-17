"""
Shared Context - collective memory for the agent swarm.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Memory(BaseModel):
    content: Any
    agent: str
    memory_type: str = "general"
    tags: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SharedContext:
    def __init__(self):
        self._memories: List[Memory] = []
        self._artifacts: Dict[str, Any] = {}

    async def add_memory(self, memory: Memory):
        """Add a memory to the collective context."""
        self._memories.append(memory)

    async def query_memories(self, tags: Optional[List[str]] = None, query: Optional[str] = None) -> List[Memory]:
        """Query memories by tags or content."""
        results = self._memories
        if tags:
            results = [m for m in results if any(tag in m.tags for tag in tags)]
        if query:
            q = query.lower()
            results = [m for m in results if q in str(m.content).lower()]
        return results

    def set_artifact(self, name: str, value: Any):
        """Set a shared artifact (e.g. current code, scan results)."""
        self._artifacts[name] = value

    def get_artifact(self, name: str) -> Optional[Any]:
        """Get a shared artifact."""
        return self._artifacts.get(name)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the context."""
        return {
            "memory_count": len(self._memories),
            "artifact_count": len(self._artifacts),
            "artifacts": list(self._artifacts.keys())
        }
