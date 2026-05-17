"""
Swarm message bus - central communication system for agents.
"""
import asyncio
from typing import Dict, List, Any, Callable, Awaitable
from datetime import datetime

class MessageBus:
    def __init__(self):
        self._subscribers: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._history: List[Dict[str, Any]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Subscribe to all messages on the bus."""
        self._subscribers.append(callback)

    async def broadcast(self, sender: str, message: Any, msg_type: str = "AGENT_MESSAGE"):
        """Broadcast a message to all subscribers."""
        msg_payload = {
            "agent": sender,
            "sender": sender,
            "message": message,
            "type": msg_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._history.append(msg_payload)

        # Notify all subscribers in parallel
        tasks = [sub(msg_payload) for sub in self._subscribers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history."""
        return self._history[-limit:]
