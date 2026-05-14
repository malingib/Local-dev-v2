"""
Session Store - event-sourced persistence for sessions.
Stores sessions as JSON files with activity log.
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from backend.models import Session, ActivityLog, SessionState

# In-memory cache and WebSocket registry
_session_cache: Dict[str, Session] = {}
_ws_registry: Dict[str, List[Callable]] = {}
_lock = asyncio.Lock()


def _get_sessions_dir() -> Path:
    """Get the sessions directory."""
    root = Path(__file__).parent.parent
    sessions_dir = root / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    return sessions_dir


def _session_to_dict(session: Session) -> dict:
    """Convert session to JSON-serializable dict."""
    return json.loads(session.json())


def _datetime_parser(dikt: dict) -> dict:
    """Recursively parse ISO datetime strings to datetime objects."""
    datetime_fields = {"created_at", "updated_at", "completed_at", "timestamp"}
    for key, value in list(dikt.items()):
        if key in datetime_fields and isinstance(value, str):
            try:
                dikt[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        elif isinstance(value, dict):
            _datetime_parser(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _datetime_parser(item)
    return dikt


def _dict_to_session(data: dict) -> Session:
    """Convert dict to Session object using Pydantic v2 model_validate."""
    data = _datetime_parser(data.copy())
    return Session.model_validate(data)


class SessionStore:
    """Event-sourced session store."""
    
    def __init__(self):
        self.sessions_dir = _get_sessions_dir()
    
    def _get_file_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.sessions_dir / f"{session_id}.json"
    
    async def create(self, session: Session) -> Session:
        """Create a new session."""
        async with _lock:
            _session_cache[session.id] = session
            await self._persist(session)
            await self._emit_event(session.id, "session_created", {"session_id": session.id})
        return session
    
    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        async with _lock:
            # Check cache first
            if session_id in _session_cache:
                return _session_cache[session_id]
            
            # Load from disk
            file_path = self._get_file_path(session_id)
            if not file_path.exists():
                return None
            
            try:
                with open(file_path) as f:
                    data = json.load(f)
                session = _dict_to_session(data)
                _session_cache[session_id] = session
                return session
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
                return None
    
    async def update(self, session: Session) -> Session:
        """Update a session."""
        async with _lock:
            session.updated_at = datetime.utcnow()
            _session_cache[session.id] = session
            await self._persist(session)
            await self._emit_event(session.id, "session_updated", _session_to_dict(session))
        return session
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        async with _lock:
            if session_id in _session_cache:
                del _session_cache[session_id]
            
            file_path = self._get_file_path(session_id)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
    
    async def list_all(self) -> List[Session]:
        """List all sessions."""
        sessions = []
        for file_path in self.sessions_dir.glob("*.json"):
            session_id = file_path.stem
            session = await self.get(session_id)
            if session:
                sessions.append(session)
        
        # Sort by updated_at descending
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
    
    async def log_activity(
        self,
        session_id: str,
        agent: str,
        message: str,
        level: str = "info",
        metadata: Optional[Dict] = None
    ) -> None:
        """Log an activity to a session."""
        session = await self.get(session_id)
        if not session:
            return
        
        log = ActivityLog(
            agent=agent,
            message=message,
            level=level,
            metadata=metadata or {}
        )
        session.activity_log.append(log)
        
        # Keep only last 1000 logs
        if len(session.activity_log) > 1000:
            session.activity_log = session.activity_log[-1000:]
        
        await self.update(session)
        
        # Emit WebSocket event
        await self._emit_event(session_id, "activity", {
            "agent": agent,
            "message": message,
            "level": level,
            "timestamp": log.timestamp.isoformat()
        })
    
    async def log_event(self, session_id: str, event_type: str, data: dict) -> None:
        """Log a structured event."""
        await self._emit_event(session_id, event_type, data)
    
    async def register_ws(
        self,
        session_id: str,
        send_func: Callable[[str, dict], None]
    ) -> None:
        """Register a WebSocket sender for a session."""
        if session_id not in _ws_registry:
            _ws_registry[session_id] = []
        _ws_registry[session_id].append(send_func)
    
    async def unregister_ws(
        self,
        session_id: str,
        send_func: Callable[[str, dict], None]
    ) -> None:
        """Unregister a WebSocket sender."""
        if session_id in _ws_registry:
            if send_func in _ws_registry[session_id]:
                _ws_registry[session_id].remove(send_func)
            if not _ws_registry[session_id]:
                del _ws_registry[session_id]
    
    async def _persist(self, session: Session) -> None:
        """Persist session to disk."""
        file_path = self._get_file_path(session.id)
        with open(file_path, 'w') as f:
            json.dump(_session_to_dict(session), f, indent=2, default=str)
    
    async def _emit_event(self, session_id: str, event_type: str, data: dict) -> None:
        """Emit event to all registered WebSocket clients concurrently."""
        if session_id not in _ws_registry:
            return
        
        await asyncio.gather(
            *[send_func(event_type, data) for send_func in _ws_registry[session_id]],
            return_exceptions=True
        )


# Singleton instance
_store: Optional[SessionStore] = None


def get_store() -> SessionStore:
    """Get the global session store instance."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store


def reset_store() -> None:
    """Reset the store (useful for testing)."""
    global _store, _session_cache, _ws_registry
    _store = None
    _session_cache = {}
    _ws_registry = {}
