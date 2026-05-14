"""
Notification system - queue, history, and WebSocket push.
Forwards notifications to the frontend in real-time.
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field


NOTIFICATION_TYPES = ["info", "success", "warning", "error"]
MAX_HISTORY = 50


# ─── Model ────────────────────────────────────────────────────────────────────

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = "info"
    title: str = ""
    message: str = ""
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── WebSocket registry ──────────────────────────────────────────────────────

_ws_clients: List[Callable[[str, dict], Any]] = []
_history: List[Notification] = []
_history_lock = asyncio.Lock()


# ─── Notifier ─────────────────────────────────────────────────────────────────

class Notifier:
    """Queue and broadcast notifications."""

    # ── WebSocket registration ──────────────────────────────────────────

    async def register_ws(self, send_func: Callable[[str, dict], Any]) -> None:
        _ws_clients.append(send_func)
        # Send history on connect
        async with _history_lock:
            for notif in _history[-10:]:
                try:
                    await send_func("notification", _notif_dict(notif))
                except Exception:
                    pass

    async def unregister_ws(self, send_func: Callable[[str, dict], Any]) -> None:
        if send_func in _ws_clients:
            _ws_clients.remove(send_func)

    # ── Send notification ──────────────────────────────────────────────

    async def notify(
        self,
        title: str,
        message: str = "",
        notif_type: str = "info",
    ) -> Dict[str, Any]:
        if notif_type not in NOTIFICATION_TYPES:
            notif_type = "info"

        notif = Notification(
            type=notif_type,
            title=title,
            message=message,
        )

        # Store in history
        async with _history_lock:
            _history.append(notif)
            if len(_history) > MAX_HISTORY:
                _history[:] = _history[-MAX_HISTORY:]

        # Broadcast via WebSocket
        data = _notif_dict(notif)
        if _ws_clients:
            await asyncio.gather(
                *[client("notification", data) for client in _ws_clients],
                return_exceptions=True,
            )

        return data

    async def notify_info(self, title: str, message: str = "") -> Dict[str, Any]:
        return await self.notify(title, message, "info")

    async def notify_success(self, title: str, message: str = "") -> Dict[str, Any]:
        return await self.notify(title, message, "success")

    async def notify_warning(self, title: str, message: str = "") -> Dict[str, Any]:
        return await self.notify(title, message, "warning")

    async def notify_error(self, title: str, message: str = "") -> Dict[str, Any]:
        return await self.notify(title, message, "error")

    # ── History management ─────────────────────────────────────────────

    async def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with _history_lock:
            return [_notif_dict(n) for n in _history[-limit:]]

    async def mark_read(self, notif_id: str) -> bool:
        async with _history_lock:
            for notif in _history:
                if notif.id == notif_id:
                    notif.read = True
                    return True
            return False

    async def mark_all_read(self) -> int:
        async with _history_lock:
            count = sum(1 for n in _history if not n.read)
            for notif in _history:
                notif.read = True
            return count

    async def clear_history(self) -> None:
        async with _history_lock:
            _history.clear()

    async def get_unread_count(self) -> int:
        async with _history_lock:
            return sum(1 for n in _history if not n.read)


def _notif_dict(notif: Notification) -> Dict[str, Any]:
    return {
        "id": notif.id,
        "type": notif.type,
        "title": notif.title,
        "message": notif.message,
        "read": notif.read,
        "timestamp": notif.timestamp.isoformat(),
    }


# ─── Singleton ────────────────────────────────────────────────────────────────

_notifier: Optional[Notifier] = None


def get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
