"""
Swarm API - FastAPI endpoints for the agent swarm.
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from swarm import SwarmCoordinator, SwarmConfig
_swarm_available = True

# Global coordinator instance
_coordinator: Optional["SwarmCoordinator"] = None


def get_coordinator():
    """Get or create the swarm coordinator."""
    if not _swarm_available:
        raise RuntimeError(
            "swarm module not installed. Install with: pip install codeaudit[swarm]"
        )
    global _coordinator
    if _coordinator is None:
        config = SwarmConfig(
            persist_dir="./swarm_data",
            enable_self_modification=True,
        )
        _coordinator = SwarmCoordinator(config)
    return _coordinator


# Pydantic models
class CreateSessionRequest(BaseModel):
    project_path: str
    github_url: Optional[str] = None
    mode: str = "audit"
    goal: Optional[str] = None


class SubmitTaskRequest(BaseModel):
    description: str
    task_type: str = "general"
    requirements: List[str] = []
    priority: str = "normal"
    dependencies: Optional[List[str]] = None


class ModelSwitchRequest(BaseModel):
    agent_id: Optional[str] = None  # None = all agents
    model: str


class RoundTableRequest(BaseModel):
    topic: str
    question: str
    agents: Optional[List[str]] = None


# Create FastAPI app
app = FastAPI(title="CodeAudit Swarm API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/api/health")
async def health():
    coord = get_coordinator()
    return {
        "status": "ok",
        "swarm_running": coord._running,
        "agents": len(coord._agents),
        "version": "2.0.0-swarm"
    }


# Swarm status
@app.get("/api/swarm/status")
async def swarm_status():
    """Get current swarm status."""
    coord = get_coordinator()
    return coord.get_status()


@app.get("/api/swarm/agents")
async def list_agents():
    """List all agents with their status."""
    coord = get_coordinator()
    return {
        "agents": [
            {
                "id": agent_id,
                **agent.get_status()
            }
            for agent_id, agent in coord._agents.items()
        ]
    }


@app.get("/api/swarm/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent status."""
    coord = get_coordinator()
    status = coord.get_agent_status(agent_id)
    if not status:
        raise HTTPException(404, "Agent not found")
    return status


@app.get("/api/swarm/models")
async def list_models():
    """List available models."""
    coord = get_coordinator()
    return {"models": coord.get_available_models()}


@app.post("/api/swarm/models/switch")
async def switch_model(req: ModelSwitchRequest):
    """Switch model for agent(s)."""
    coord = get_coordinator()
    
    if req.agent_id:
        success = coord.switch_agent_model(req.agent_id, req.model)
        if not success:
            raise HTTPException(404, "Agent not found")
    else:
        coord.switch_all_models(req.model)
    
    return {"status": "ok", "model": req.model}


# Activity
@app.get("/api/swarm/activity")
async def get_activity(limit: int = 50):
    """Get recent swarm activity."""
    coord = get_coordinator()
    return {"activity": await coord.get_recent_activity(limit)}


# Tasks
@app.post("/api/swarm/tasks")
async def submit_task(req: SubmitTaskRequest):
    """Submit a task to the swarm."""
    coord = get_coordinator()
    task_id = await coord.submit_task(
        description=req.description,
        task_type=req.task_type,
        requirements=req.requirements,
        priority=req.priority,
        dependencies=req.dependencies
    )
    return {"task_id": task_id, "status": "submitted"}


@app.get("/api/swarm/tasks")
async def list_tasks():
    """List all tasks."""
    coord = get_coordinator()
    return {"tasks": coord._tasks}


# Round table
@app.post("/api/swarm/round-table")
async def call_round_table(req: RoundTableRequest):
    """Call a round-table discussion."""
    coord = get_coordinator()
    decision = await coord.call_round_table(
        topic=req.topic,
        question=req.question,
        agents=req.agents
    )
    return decision


# Sessions (compatibility with original API)
@app.get("/api/sessions")
async def list_sessions():
    """List all audit sessions."""
    coord = get_coordinator()
    sessions = await coord.list_sessions()
    return sessions


@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest):
    """Create a new audit session."""
    coord = get_coordinator()
    session_id = await coord.create_session(
        project_path=req.project_path,
        github_url=req.github_url
    )
    return {"session_id": session_id, "status": "created"}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    coord = get_coordinator()
    session = await coord.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


# WebSocket for real-time updates
@app.websocket("/ws/swarm")
async def swarm_websocket(websocket: WebSocket):
    """WebSocket for real-time swarm updates."""
    await websocket.accept()
    coord = get_coordinator()
    
    # Subscribe to status updates
    async def send_update(status: Dict):
        try:
            await websocket.send_json({
                "type": "status_update",
                "data": status,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            pass
    
    coord.on_status_change(send_update)
    
    try:
        while True:
            # Send periodic updates
            status = coord.get_status()
            await websocket.send_json({
                "type": "status",
                "data": status
            })
            
            # Check for client messages
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=5.0
                )
                
                # Handle client commands
                if msg.get("action") == "submit_task":
                    task_id = await coord.submit_task(
                        msg.get("description", ""),
                        msg.get("task_type", "general")
                    )
                    await websocket.send_json({
                        "type": "task_submitted",
                        "task_id": task_id
                    })
                    
            except asyncio.TimeoutError:
                pass
                
    except WebSocketDisconnect:
        pass


# Startup/shutdown
@app.on_event("startup")
async def startup():
    """Start the swarm on API startup."""
    coord = get_coordinator()
    await coord.start()


@app.on_event("shutdown")
async def shutdown():
    """Stop the swarm on API shutdown."""
    global _coordinator
    if _coordinator:
        await _coordinator.stop()
