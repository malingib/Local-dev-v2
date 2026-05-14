"""
FastAPI server - REST + WebSocket endpoints.
All session operations, approval flow, real-time activity feed.
"""
import asyncio
import json
import uuid
import os
import tempfile
import platform
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger("codeaudit.api")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.models import (
    Session, SessionMode, SessionState, FindingStatus,
    ApprovalResponse, ApprovalStage, ProjectInfo
)
from backend.session_store import get_store
from backend.config import get_config
from agents.orchestrator import Orchestrator

app = FastAPI(title="CodeAudit API", version="1.0.0")

config_for_cors = get_config()
cors_origins = getattr(config_for_cors, 'cors_origins', None) or [
    "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request models ────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    project_path: str
    github_url: Optional[str] = ""
    mode: SessionMode = SessionMode.AUDIT
    goal: Optional[str] = ""

class StartAuditRequest(BaseModel):
    session_id: str

class FixFindingRequest(BaseModel):
    session_id: str
    finding_id: str

class ApprovalRequest(BaseModel):
    decision: str  # approve | reject | tweak
    reason: Optional[str] = ""
    tweak_instruction: Optional[str] = ""

class UpdateConfigRequest(BaseModel):
    github_url: Optional[str] = None
    project_path: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    github_token: Optional[str] = None
    figma_token: Optional[str] = None

class WriteSoulFileRequest(BaseModel):
    content: str = ""

class CreateExperimentSessionRequest(BaseModel):
    project_path: str = ""
    target_file: str = ""
    tag: str = ""
    time_budget: int = 300

class RunExperimentRequest(BaseModel):
    description: str = ""
    code_change: str = ""

class SelfModifyRequest(BaseModel):
    session_id: str = ""
    agent_file: str = ""

class OptimizeContextRequest(BaseModel):
    content: str = ""
    tool: str = "unknown"
    type: str = "text"
    max_chars: int = 500
    max_items: Optional[int] = None
    max_lines: Optional[int] = None

class TrackSessionEventRequest(BaseModel):
    session_id: str = ""
    event_type: str = ""
    summary: str = ""
    detail: str = ""

class ScanProjectRequest(BaseModel):
    project_path: str = ""

class IndexDocumentRequest(BaseModel):
    file_path: str = ""
    content: str = ""

class RecordTraceRequest(BaseModel):
    session_id: str = ""
    run_id: str = ""
    agent_name: str = ""
    action: str = ""
    tool: str = ""
    duration_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    success: bool = True
    error: str = ""

class RunImprovementLoopRequest(BaseModel):
    session_id: str = ""
    target_file: str = ""
    iterations: int = 3

class VoiceSpeakRequest(BaseModel):
    text: str = ""
    voice: str = "default"
    backend: str = "auto"

class VoiceCommandRequest(BaseModel):
    text: str = ""

class DesignSuggestRequest(BaseModel):
    project_type: str = "web"

class DesignGeneratePrototypeRequest(BaseModel):
    title: str = "Prototype"
    screens: list = []
    style: str = "glassmorphism"
    palette: str = "ocean"
    font: str = "modern"
    mobile_frame: bool = True

class CreateSpecRequest(BaseModel):
    project_name: str = ""
    goal: str = ""
    context: str = ""
    requirements: Optional[list] = None

class ApplyImplementationRequest(BaseModel):
    project_path: str = ""
    files: list = []

# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    config = get_config()
    return {
        "status": "ok",
        "has_google_key": bool(config.google_api_key),
        "has_groq_key": bool(config.groq_api_key),
        "has_openrouter_key": bool(config.openrouter_api_key),
        "has_github_token": bool(config.github_token),
        "default_model": config.default_model if hasattr(config, 'default_model') else "gemini-pro",
        "use_swarm": config.use_swarm if hasattr(config, 'use_swarm') else False,
        "has_experiments": True,
        "self_modify_enabled": config.self_modify_enabled if hasattr(config, 'self_modify_enabled') else False,
        "version": "1.0.0"
    }

# ─── Config ────────────────────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config_endpoint():
    config = get_config()
    return {
        "project_name": config.project_name,
        "github_url": config.github_url,
        "local_path": config.local_path,
        "enabled_agents": config.enabled_agents,
        "has_google_key": bool(config.google_api_key),
        "has_groq_key": bool(config.groq_api_key),
        "has_github_token": bool(config.github_token),
        "has_figma_token": bool(config.figma_token),
    }

@app.post("/api/config/validate-keys")
async def validate_keys():
    """Test that configured API keys actually work."""
    results = {}
    config = get_config()

    if config.google_api_key:
        try:
            from backend.llm_router import llm_call
            await llm_call("Say 'ok' in one word.", model="gemini-flash", fallback=False)
            results["google"] = "ok"
        except Exception as e:
            results["google"] = f"error: {str(e)[:100]}"
    else:
        results["google"] = "not configured"

    if config.openrouter_api_key:
        try:
            from backend.llm_router import llm_call
            await llm_call("Say 'ok' in one word.", model="openrouter/qwen-3.5", fallback=False)
            results["openrouter"] = "ok"
        except Exception as e:
            results["openrouter"] = f"error: {str(e)[:100]}"
    else:
        results["openrouter"] = "not configured"

    if config.groq_api_key:
        try:
            from backend.llm_router import llm_call
            # Use a very short prompt for Groq (small context model)
            await llm_call("Reply: ok", model="groq/llama-3.3-70b", fallback=False)
            results["groq"] = "ok"
        except Exception as e:
            results["groq"] = f"error: {str(e)[:100]}"
    else:
        results["groq"] = "not configured"

    return results

@app.put("/api/config")
async def update_config(req: UpdateConfigRequest):
    """Update configuration values temporarily (in-memory)."""
    from backend.config import update_config as cfg_update
    updates = {k: v for k, v in req.model_dump(exclude_none=True).items()}
    if updates:
        cfg_update(updates)
    config = get_config(force_reload=True)
    return {
        "status": "updated",
        "has_google_key": bool(config.google_api_key),
        "has_groq_key": bool(config.groq_api_key),
        "has_openrouter_key": bool(config.openrouter_api_key),
        "has_github_token": bool(config.github_token),
    }

# ─── Cache management ──────────────────────────────────────────────────────────

@app.get("/api/cache/stats")
async def cache_stats():
    from backend.llm_router import get_cache_stats
    return await get_cache_stats()

@app.post("/api/cache/clear")
async def clear_cache_endpoint():
    from backend.llm_router import clear_cache
    return await clear_cache()

# ─── Sessions ──────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions():
    store = get_store()
    sessions = await store.list_all()
    return [_session_summary(s) for s in sessions]

@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest):
    store = get_store()

    # Resolve project path
    project_path = req.project_path
    if not project_path and req.github_url:
        project_path = str(Path(tempfile.gettempdir()) / "codeaudit_repos" / req.github_url.split('/')[-1])

    if not project_path:
        raise HTTPException(400, "Either project_path or github_url required")

    # Build project info
    project = ProjectInfo(
        name=Path(project_path).name,
        path=project_path,
        github_url=req.github_url or None,
    )

    session = Session(
        mode=req.mode,
        goal=req.goal or "",
        state=SessionState.INGEST,
        project=project,
    )
    await store.create(session)

    return {"session_id": session.id, "state": session.state}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.dict()

@app.get("/api/sessions/{session_id}/findings")
async def get_findings(session_id: str):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return [f.dict() for f in session.findings]

@app.get("/api/sessions/{session_id}/approval-queue")
async def get_approval_queue(session_id: str):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    queue = []
    for fid in session.approval_queue:
        finding = next((f for f in session.findings if f.id == fid), None)
        if finding and finding.status == FindingStatus.AWAITING_APPROVAL:
            queue.append(finding.dict())
    return queue

@app.get("/api/sessions/{session_id}/activity")
async def get_activity(session_id: str, limit: int = 100):
    """Get activity log for a session."""
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    logs = session.activity_log[-limit:] if len(session.activity_log) > limit else session.activity_log
    return [log.dict() for log in logs]

# ─── Audit operations ──────────────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/ingest")
async def ingest(session_id: str, background: BackgroundTasks):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    project_path = session.project.path if session.project else ""
    if not project_path:
        raise HTTPException(400, "No project path set")
    
    background.add_task(_run_ingest, session_id, project_path)
    return {"status": "started", "session_id": session_id}

@app.post("/api/sessions/{session_id}/audit")
async def start_audit(session_id: str, background: BackgroundTasks):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    project_path = session.project.path if session.project else ""
    if not project_path:
        raise HTTPException(400, "No project path set")
    
    background.add_task(_run_audit, session_id, project_path)
    return {"status": "started", "session_id": session_id}

@app.post("/api/sessions/{session_id}/fix/{finding_id}")
async def fix_finding(session_id: str, finding_id: str, background: BackgroundTasks):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    project_path = session.project.path if session.project else ""
    background.add_task(_run_fix, session_id, finding_id, project_path)
    return {"status": "started", "finding_id": finding_id}

@app.post("/api/sessions/{session_id}/fix-all")
async def fix_all(session_id: str, background: BackgroundTasks):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    project_path = session.project.path if session.project else ""
    open_findings = [f.id for f in session.findings if f.status == FindingStatus.OPEN]
    
    background.add_task(_run_fix_all, session_id, open_findings, project_path)
    return {"status": "started", "finding_count": len(open_findings)}

# ─── Approval flow ─────────────────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/findings/{finding_id}/approve")
async def approve_finding(session_id: str, finding_id: str, req: ApprovalRequest):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    finding = next((f for f in session.findings if f.id == finding_id), None)
    if not finding:
        raise HTTPException(404, "Finding not found")
    
    finding_type = finding.type if isinstance(finding.type, str) else finding.type.value
    
    if req.decision == "approve":
        finding.status = FindingStatus.APPROVED
        await store.log_activity(session_id, "approval", 
                                  f"Approved: {finding.title}", "success")
        # Apply the patch
        project_path = session.project.path if session.project else ""
        orch = Orchestrator(session_id)
        await orch.apply_patch(finding_id, project_path)
        
    elif req.decision == "reject":
        finding.status = FindingStatus.REJECTED
        finding.rejection_reason = req.reason
        # Log to rejection memory
        from backend.models import RejectionMemory
        session.rejection_memory.append(RejectionMemory(
            finding_title=finding.title,
            finding_type=finding_type,
            location=finding.location,
            reason=req.reason,
        ))
        await store.log_activity(session_id, "approval", 
                                  f"Rejected: {finding.title}", "warning")
    
    elif req.decision == "tweak":
        # Store tweak instruction, re-run patch generation
        finding.status = FindingStatus.IN_PROGRESS
        await store.log_activity(session_id, "approval",
                                  f"Tweak requested: {finding.title}")
    
    # Remove from approval queue
    session.approval_queue = [fid for fid in session.approval_queue 
                               if fid != finding_id]
    
    # Update finding
    for i, f in enumerate(session.findings):
        if f.id == finding_id:
            session.findings[i] = finding
            break
    
    await store.update(session)
    return {"status": req.decision, "finding_id": finding_id}

# ─── GitHub integration ────────────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/clone")
async def clone_repo(session_id: str, background: BackgroundTasks):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    config = get_config()
    github_url = (session.project.github_url if session.project else "") or config.github_url
    
    if not github_url:
        raise HTTPException(400, "No GitHub URL configured")
    
    background.add_task(_clone_repo, session_id, github_url)
    return {"status": "cloning", "url": github_url}

# ─── Report ────────────────────────────────────────────────────────────────────

@app.get("/api/sessions/{session_id}/report")
async def get_report(session_id: str):
    store = get_store()
    session = await store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    findings = session.findings
    return {
        "session_id": session_id,
        "project": session.project.dict() if session.project else {},
        "summary": {
            "total": len(findings),
            "critical": len([f for f in findings if f.severity == "critical"]),
            "high": len([f for f in findings if f.severity == "high"]),
            "medium": len([f for f in findings if f.severity == "medium"]),
            "low": len([f for f in findings if f.severity == "low"]),
            "applied": len([f for f in findings if f.status == "applied"]),
            "rejected": len([f for f in findings if f.status == "rejected"]),
            "open": len([f for f in findings if f.status == "open"]),
        },
        "by_type": _group_by_type(findings),
        "findings": [f.dict() for f in findings],
        "generated_at": datetime.utcnow().isoformat()
    }

# ─── Meta agent ─────────────────────────────────────────────────────────────────

@app.get("/api/meta/analysis")
async def get_meta_analysis():
    """Get meta-analysis of past sessions."""
    from agents.meta_agent import MetaAgent
    meta = MetaAgent()
    result = await meta.analyze_sessions(min_sessions=3)
    return result

# ─── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    store = get_store()
    
    async def send_event(event_type: str, data: dict):
        try:
            await websocket.send_text(json.dumps({
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }, default=str))
        except Exception:
            pass
    
    await store.register_ws(session_id, send_event)
    
    try:
        # Send current session state on connect
        session = await store.get(session_id)
        if session:
            await send_event("session_state", _session_summary(session))
        
        # Keep alive and handle client messages
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        await store.unregister_ws(session_id, send_event)
    except Exception:
        await store.unregister_ws(session_id, send_event)

# ─── Background tasks ──────────────────────────────────────────────────────────

async def _run_ingest(session_id: str, project_path: str):
    try:
        orch = Orchestrator(session_id)
        store = get_store()
        session = await store.get(session_id)
        if session and not session.project:
            from backend.models import ProjectInfo
            session.project = ProjectInfo(name=Path(project_path).name, path=project_path)
            await store.update(session)
        await orch.run_ingest(project_path)
    except Exception as e:
        logger.exception("Ingest failed for session %s", session_id)
        store = get_store()
        await store.log_activity(session_id, "orchestrator", f"Ingest failed: {e}", "error")

async def _run_audit(session_id: str, project_path: str):
    try:
        orch = Orchestrator(session_id)
        await orch.run_audit(project_path)
    except Exception as e:
        logger.exception("Audit failed for session %s", session_id)
        store = get_store()
        await store.log_activity(session_id, "orchestrator", f"Audit failed: {e}", "error")

async def _run_fix(session_id: str, finding_id: str, project_path: str):
    try:
        orch = Orchestrator(session_id)
        await orch.run_fix_finding(finding_id, project_path)
    except Exception as e:
        logger.exception("Fix failed for session %s finding %s", session_id, finding_id)
        store = get_store()
        await store.log_activity(session_id, "orchestrator", f"Fix failed: {e}", "error")

async def _run_fix_all(session_id: str, finding_ids: List[str], project_path: str):
    orch = Orchestrator(session_id)
    for fid in finding_ids:
        try:
            await orch.run_fix_finding(fid, project_path)
        except Exception as e:
            logger.exception("Fix-all failed for session %s finding %s", session_id, fid)
            store = get_store()
            await store.log_activity(session_id, "orchestrator", 
                                      f"Fix failed for {fid}: {e}", "error")

async def _clone_repo(session_id: str, github_url: str):
    store = get_store()
    helper_path = None
    try:
        repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = Path(tempfile.gettempdir()) / "codeaudit_repos" / repo_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        await store.log_activity(session_id, "orchestrator", f"Cloning {github_url}...")

        config = get_config()
        clone_url = github_url

        proc_env = os.environ.copy()
        proc_env["GIT_TERMINAL_PROMPT"] = "0"

        if config.github_token and "github.com" in github_url:
            is_windows = platform.system() == "Windows"
            if is_windows:
                helper_lines = ["@echo off", f"echo {config.github_token}"]
                suffix = ".bat"
            else:
                helper_lines = ["#!/bin/sh", f'echo "{config.github_token}"']
                suffix = ".sh"

            fd, helper_path = tempfile.mkstemp(suffix=suffix, text=True)
            with os.fdopen(fd, 'w') as f:
                f.write("\n".join(helper_lines))
            if not is_windows:
                os.chmod(helper_path, 0o700)

            proc_env["GIT_ASKPASS"] = helper_path

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth=1", clone_url, str(dest),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=proc_env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            await store.log_activity(session_id, "orchestrator", "Clone timed out after 120s", "error")
            return
        finally:
            if helper_path:
                try:
                    os.unlink(helper_path)
                except OSError:
                    pass

        if proc.returncode == 0:
            session = await store.get(session_id)
            if session:
                from backend.models import ProjectInfo
                session.project = ProjectInfo(
                    name=repo_name, path=str(dest), github_url=github_url
                )
                await store.update(session)
            await store.log_activity(session_id, "orchestrator",
                                      f"Cloned to {dest}", "success")
        else:
            stderr_text = stderr.decode(errors="replace") if stderr else ""
            await store.log_activity(session_id, "orchestrator",
                                      f"Clone failed: {stderr_text[:200]}", "error")
    except Exception as e:
        logger.exception("Clone failed for session %s", session_id)
        await store.log_activity(session_id, "orchestrator", f"Clone error: {e}", "error")
    finally:
        if helper_path:
            try:
                os.unlink(helper_path)
            except OSError:
                pass

# ─── Helpers ───────────────────────────────────────────────────────────────────

def _session_summary(session: Session) -> dict:
    findings = session.findings
    state = session.state if isinstance(session.state, str) else session.state.value
    mode = session.mode if isinstance(session.mode, str) else session.mode.value
    return {
        "id": session.id,
        "state": state,
        "mode": mode,
        "project_name": session.project.name if session.project else "Unknown",
        "project_path": session.project.path if session.project else "",
        "findings_total": len(findings),
        "findings_critical": len([f for f in findings if f.severity == "critical"]),
        "findings_high": len([f for f in findings if f.severity == "high"]),
        "findings_open": len([f for f in findings if f.status == "open"]),
        "findings_applied": len([f for f in findings if f.status == "applied"]),
        "approval_queue_size": len(session.approval_queue),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }

def _group_by_type(findings) -> dict:
    groups = {}
    for f in findings:
        t = f.type if isinstance(f.type, str) else f.type.value
        severity = f.severity if isinstance(f.severity, str) else f.severity.value
        if t not in groups:
            groups[t] = []
        groups[t].append({"id": f.id, "title": f.title, "severity": severity})
    return groups

# ─── Hermes-Style: Soul / Agent Identity ─────────────────────────────────────

@app.get("/api/soul/active")
async def get_active_soul():
    from backend.soul import get_soul_manager
    sm = get_soul_manager()
    files = sm.list_soul_files()
    result = {}
    for f in files:
        content = sm.get_soul_file(f["name"])
        result[f["name"]] = content or ""
    return result

@app.get("/api/soul/templates")
async def list_soul_templates():
    from backend.soul import get_soul_manager
    return get_soul_manager().list_templates()

@app.get("/api/soul/template/{template_id}")
async def get_soul_template(template_id: str):
    from backend.soul import get_soul_manager
    t = get_soul_manager().get_template(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    return t

@app.post("/api/soul/apply-template/{template_id}")
async def apply_soul_template(template_id: str):
    from backend.soul import get_soul_manager
    result = get_soul_manager().apply_template(template_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result

@app.get("/api/soul/file/{file_type}")
async def get_soul_file(file_type: str):
    from backend.soul import get_soul_manager
    content = get_soul_manager().get_soul_file(file_type)
    if content is None:
        return {"content": "", "exists": False}
    return {"content": content, "exists": True}

@app.put("/api/soul/file/{file_type}")
async def write_soul_file(file_type: str, req: WriteSoulFileRequest):
    from backend.soul import get_soul_manager
    get_soul_manager().write_soul_file(file_type, req.content)
    return {"status": "saved", "file_type": file_type}

@app.get("/api/soul/files")
async def list_soul_files():
    from backend.soul import get_soul_manager
    return get_soul_manager().list_soul_files()

# ─── Hermes-Style: Skills Library ────────────────────────────────────────────

@app.get("/api/skills")
async def list_skills(category: Optional[str] = None, tag: Optional[str] = None, search: Optional[str] = None):
    from backend.skills_lib import get_skills_library
    lib = get_skills_library()
    all_skills = lib.list_skills(category=category, tag=tag)
    if search:
        q = search.lower()
        all_skills = [s for s in all_skills if q in s["name"].lower() or q in s["description"].lower()]
    return all_skills

@app.get("/api/skills/categories")
async def list_skill_categories():
    from backend.skills_lib import get_skills_library
    return get_skills_library().list_categories()

@app.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    from backend.skills_lib import get_skills_library
    skill = get_skills_library().get_skill(skill_id)
    if not skill:
        raise HTTPException(404, "Skill not found")
    return skill

@app.post("/api/skills")
async def create_skill(req: dict):
    from backend.skills_lib import get_skills_library, Skill
    skill = Skill(**req)
    return get_skills_library().create_skill(skill)

@app.put("/api/skills/{skill_id}")
async def update_skill(skill_id: str, req: dict):
    from backend.skills_lib import get_skills_library
    result = get_skills_library().update_skill(skill_id, req)
    if not result:
        raise HTTPException(404, "Skill not found or is a catalog skill")
    return result

@app.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str):
    from backend.skills_lib import get_skills_library
    if not get_skills_library().delete_skill(skill_id):
        raise HTTPException(404, "Skill not found or is a catalog skill")
    return {"status": "deleted"}

# ─── Hermes-Style: Wiki Knowledge Base ───────────────────────────────────────

@app.get("/api/wiki/pages")
async def list_wiki_pages(category: Optional[str] = None, tag: Optional[str] = None):
    from backend.wiki import get_wiki_manager
    return get_wiki_manager().list_pages(category=category, tag=tag)

@app.get("/api/wiki/page/{page_id}")
async def get_wiki_page(page_id: str):
    from backend.wiki import get_wiki_manager
    page = get_wiki_manager().get_page(page_id)
    if not page:
        raise HTTPException(404, "Page not found")
    return page

@app.post("/api/wiki/page")
async def create_wiki_page(req: dict):
    from backend.wiki import get_wiki_manager, WikiPage
    page = WikiPage(**req)
    return get_wiki_manager().create_page(page)

@app.put("/api/wiki/page/{page_id}")
async def update_wiki_page(page_id: str, req: dict):
    from backend.wiki import get_wiki_manager
    result = get_wiki_manager().update_page(page_id, req)
    if not result:
        raise HTTPException(404, "Page not found")
    return result

@app.delete("/api/wiki/page/{page_id}")
async def delete_wiki_page(page_id: str):
    from backend.wiki import get_wiki_manager
    if not get_wiki_manager().delete_page(page_id):
        raise HTTPException(404, "Page not found")
    return {"status": "deleted"}

@app.get("/api/wiki/search")
async def search_wiki(q: str = ""):
    from backend.wiki import get_wiki_manager
    if not q.strip():
        return []
    return get_wiki_manager().search_pages(q)

@app.get("/api/wiki/categories")
async def list_wiki_categories():
    from backend.wiki import get_wiki_manager
    return get_wiki_manager().list_categories()

# ─── Hermes-Style: Buddy Companion ───────────────────────────────────────────

@app.get("/api/buddy")
async def get_buddy():
    from backend.buddy import get_buddy_manager
    return get_buddy_manager().get_buddy()

@app.post("/api/buddy/create")
async def create_buddy(req: dict):
    from backend.buddy import get_buddy_manager, Buddy
    buddy = Buddy(**req)
    return get_buddy_manager().create_buddy(buddy)

@app.put("/api/buddy/update")
async def update_buddy(req: dict):
    from backend.buddy import get_buddy_manager
    return get_buddy_manager().update_buddy(req)

@app.get("/api/buddy/options")
async def get_buddy_options():
    from backend.buddy import get_buddy_manager
    bm = get_buddy_manager()
    return {
        "species": bm.list_species(),
        "palettes": bm.list_palettes(),
        "eye_shapes": bm.list_eye_shapes(),
        "accessories": bm.list_accessories(),
    }

# ─── Hermes-Style: Notifications ─────────────────────────────────────────────

@app.get("/api/notifications")
async def get_notifications():
    from backend.notifier import get_notifier
    return await get_notifier().get_history()

@app.post("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    from backend.notifier import get_notifier
    await get_notifier().mark_read(notif_id)
    return {"status": "ok"}

@app.post("/api/notifications/clear")
async def clear_notifications():
    from backend.notifier import get_notifier
    await get_notifier().clear_history()
    return {"status": "cleared"}

@app.websocket("/ws/notifications")
async def notification_websocket(websocket: WebSocket):
    await websocket.accept()
    from backend.notifier import get_notifier

    async def send_notif(event_type: str, data: dict):
        try:
            await websocket.send_text(json.dumps({
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }, default=str))
        except Exception:
            pass

    notifier = get_notifier()
    await notifier.register_ws(send_notif)

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if message == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# ─── Autoresearch: Experiment Engine ───────────────────────────────────────

@app.get("/api/experiments/sessions")
async def list_experiment_sessions():
    from backend.experiment_engine import get_experiment_engine
    return get_experiment_engine().list_sessions()

@app.post("/api/experiments/sessions")
async def create_experiment_session(req: CreateExperimentSessionRequest):
    from backend.experiment_engine import get_experiment_engine
    engine = get_experiment_engine()
    session = engine.create_session(
        project_path=req.project_path,
        target_file=req.target_file,
        tag=req.tag,
        time_budget=req.time_budget,
    )
    return {
        "id": session.id, "tag": session.tag, "branch": session.branch,
        "target_file": session.target_file, "time_budget": session.time_budget,
    }

@app.get("/api/experiments/sessions/{session_id}")
async def get_experiment_session(session_id: str):
    from backend.experiment_engine import get_experiment_engine
    session = get_experiment_engine().get_session(session_id)
    if not session:
        raise HTTPException(404, "Experiment session not found")
    return session.model_dump(mode="json")

@app.delete("/api/experiments/sessions/{session_id}")
async def delete_experiment_session(session_id: str):
    from backend.experiment_engine import get_experiment_engine
    if not get_experiment_engine().delete_session(session_id):
        raise HTTPException(404, "Experiment session not found")
    return {"status": "deleted"}

@app.post("/api/experiments/sessions/{session_id}/baseline")
async def establish_baseline(session_id: str):
    from backend.experiment_engine import get_experiment_engine
    result = await get_experiment_engine().establish_baseline(session_id)
    return result

@app.post("/api/experiments/sessions/{session_id}/run")
async def run_experiment(session_id: str, req: RunExperimentRequest):
    from backend.experiment_engine import get_experiment_engine
    result = await get_experiment_engine().run_experiment(
        session_id,
        description=req.description,
        code_change=req.code_change,
    )
    return result

@app.post("/api/experiments/sessions/{session_id}/propose")
async def propose_experiment(session_id: str):
    from backend.experiment_engine import get_experiment_engine
    return await get_experiment_engine().propose_experiment(session_id)

@app.get("/api/experiments/sessions/{session_id}/results")
async def get_experiment_results(session_id: str):
    from backend.experiment_engine import get_experiment_engine
    tsv = get_experiment_engine().get_results_tsv(session_id)
    return {"tsv": tsv}

@app.post("/api/experiments/self-modify")
async def self_modify_agent(req: SelfModifyRequest):
    from backend.experiment_engine import get_experiment_engine
    result = await get_experiment_engine().self_modify_agent(
        session_id=req.session_id,
        agent_file=req.agent_file,
    )
    return result

# ─── Fast File Search (fff.nvim-inspired) ──────────────────────────────────

@app.get("/api/search/files")
async def search_files(root: str = "", query: str = "", mode: str = "fuzzy",
                       extensions: str = "", max_results: int = 30):
    from backend.fast_search import search_files as sf
    ext_list = extensions.split(",") if extensions else None
    return sf(root, query, mode=mode, extensions=ext_list, max_results=max_results)

@app.get("/api/search/symbols")
async def search_symbols(root: str = "", query: str = "", extensions: str = ""):
    from backend.fast_search import search_symbols as ss
    ext_list = extensions.split(",") if extensions else None
    return ss(root, query, extensions=ext_list)

@app.get("/api/search/recent")
async def get_recent_files(root: str = "", limit: int = 20):
    from backend.fast_search import get_recent_files as grf
    return grf(root, limit=limit)

# ─── Context Optimizer (context-mode-inspired) ──────────────────────────────

@app.post("/api/context/optimize")
async def optimize_context(req: OptimizeContextRequest):
    from backend.context_optimizer import sandbox_output, sandbox_json, sandbox_file, sandbox_diff
    content = req.content
    tool = req.tool
    context_type = req.type
    max_chars = req.max_chars
    if context_type == "json":
        try:
            import json as jmod
            return {"compressed": sandbox_json(jmod.loads(content), tool, req.max_items or 20)}
        except Exception:
            return {"compressed": sandbox_output(content, tool, max_chars)}
    elif context_type == "diff":
        return {"compressed": sandbox_diff(content, req.max_lines or 40)}
    else:
        return {"compressed": sandbox_output(content, tool, max_chars)}

@app.post("/api/context/session-event")
async def track_session_event(req: TrackSessionEventRequest):
    from backend.context_optimizer import track_session_event as tse
    tse(req.session_id, req.event_type, req.summary, req.detail)
    return {"status": "tracked"}

@app.get("/api/context/session/{session_id}")
async def get_session_context(session_id: str):
    from backend.context_optimizer import get_session_context, get_session_summary
    return {
        "events": get_session_context(session_id),
        "summary": get_session_summary(session_id),
    }

@app.get("/api/context/stats")
async def get_context_stats():
    from backend.context_optimizer import get_context_stats
    return get_context_stats()

@app.post("/api/context/reset-stats")
async def reset_context_stats():
    from backend.context_optimizer import reset_stats
    reset_stats()
    return {"status": "reset"}

# ─── Knowledge Graph (Understand-Anything + graphify-inspired) ─────────────

@app.post("/api/graph/scan")
async def scan_project_graph(req: ScanProjectRequest):
    from backend.knowledge_graph import scan_project
    return scan_project(req.project_path)

@app.get("/api/graph/load")
async def load_project_graph(project_path: str = ""):
    from backend.knowledge_graph import load_graph, analyze_architecture
    graph = load_graph(project_path)
    if not graph:
        return {"error": "No graph found", "nodes": [], "edges": []}
    arch = analyze_architecture(graph)
    return {"graph": graph, "architecture": arch}

@app.get("/api/graph/list")
async def list_knowledge_graphs():
    from backend.knowledge_graph import list_graphs
    return list_graphs()

@app.get("/api/graph/query")
async def query_knowledge_graph(project_path: str = "", node_type: str = "", search: str = ""):
    from backend.knowledge_graph import query_graph
    return query_graph(project_path, node_type or None, search or None)

@app.get("/api/graph/dependencies")
async def get_file_dependencies(project_path: str = "", file_path: str = ""):
    from backend.knowledge_graph import get_file_dependencies
    return get_file_dependencies(project_path, file_path)

@app.post("/api/graph/index-doc")
async def index_document(req: IndexDocumentRequest):
    from backend.knowledge_graph import index_document
    return index_document(req.file_path, req.content)

# ─── Code Extractor (distil-inspired: L1-L5 extraction) ──────────────────

@app.post("/api/extract/ast")
async def extract_ast_api(req: dict):
    from backend.code_extractor import extract_ast
    return extract_ast(req.get("file_path", ""))

@app.post("/api/extract/call-graph")
async def extract_call_graph(req: dict):
    from backend.code_extractor import build_call_graph
    return build_call_graph(req.get("project_path", ""), req.get("file_paths"))

@app.post("/api/extract/cfg")
async def extract_control_flow(req: dict):
    from backend.code_extractor import extract_cfg
    return extract_cfg(req.get("file_path", ""), req.get("function_name"))

@app.post("/api/extract/dataflow")
async def extract_dataflow(req: dict):
    from backend.code_extractor import extract_df
    return extract_df(req.get("project_path", ""), req.get("file_path", ""))

@app.post("/api/extract/slice")
async def extract_slice(req: dict):
    from backend.code_extractor import slice_file
    return slice_file(req.get("file_path", ""), req.get("target_line", 1), req.get("direction", "backward"))

@app.post("/api/extract/all")
async def extract_all_layers(req: dict):
    from backend.code_extractor import extract_all
    return extract_all(req.get("file_path", ""))

# ─── Agent Loop (HALO-style self-improvement) ──────────────────────────────

@app.post("/api/loop/trace")
async def record_agent_trace(req: RecordTraceRequest):
    from backend.agent_loop import record_trace
    tid = record_trace(
        session_id=req.session_id,
        run_id=req.run_id,
        agent_name=req.agent_name,
        action=req.action,
        tool=req.tool,
        duration_ms=req.duration_ms,
        tokens_in=req.tokens_in,
        tokens_out=req.tokens_out,
        success=req.success,
        error=req.error,
    )
    return {"trace_id": tid}

@app.get("/api/loop/traces")
async def get_agent_traces(session_id: str = "", limit: int = 100):
    from backend.agent_loop import get_traces
    return get_traces(session_id, limit=limit)

@app.get("/api/loop/analyze")
async def analyze_agent_traces(session_id: str = ""):
    from backend.agent_loop import analyze_traces
    return analyze_traces(session_id)

@app.post("/api/loop/improvements/generate")
async def generate_agent_improvements(req: dict = {}):
    from backend.agent_loop import generate_improvements
    return await generate_improvements(req.get("session_id", ""))

@app.get("/api/loop/improvements")
async def get_agent_improvements(session_id: str = ""):
    from backend.agent_loop import get_improvements
    return get_improvements(session_id)

@app.post("/api/loop/improvements/{imp_id}/apply")
async def apply_agent_improvement(imp_id: int, req: dict = {}):
    from backend.agent_loop import apply_improvement
    return await apply_improvement(imp_id, req.get("target_file", ""))

@app.post("/api/loop/run")
async def run_improvement_loop(req: RunImprovementLoopRequest = RunImprovementLoopRequest()):
    from backend.agent_loop import run_improvement_loop
    return await run_improvement_loop(
        req.session_id,
        req.target_file,
        req.iterations,
    )

@app.get("/api/loop/benchmarks")
async def get_loop_benchmarks(improvement_id: int = 0):
    from backend.agent_loop import get_benchmarks
    return get_benchmarks(improvement_id or None)

# ─── Design System (ui-ux-pro-max + huashu + taste-skill inspired) ─────────

@app.get("/api/design/styles")
async def list_design_styles(tag: str = ""):
    from backend.design_system import list_styles
    return list_styles(tag or None)

@app.get("/api/design/palettes")
async def list_design_palettes(industry: str = ""):
    from backend.design_system import list_palettes
    return list_palettes(industry or None)

@app.get("/api/design/fonts")
async def list_font_pairings(mood: str = ""):
    from backend.design_system import list_font_pairings
    return list_font_pairings(mood or None)

@app.post("/api/design/suggest")
async def suggest_design(req: DesignSuggestRequest):
    from backend.design_system import suggest_design as sd
    return sd(req.project_type)

@app.post("/api/design/prototype")
async def generate_prototype(req: DesignGeneratePrototypeRequest):
    from backend.design_generator import generate_prototype
    return generate_prototype(
        title=req.title,
        screens=req.screens,
        style_name=req.style,
        palette_name=req.palette,
        font_pair_name=req.font,
        mobile_frame=req.mobile_frame,
    )

@app.post("/api/design/slides")
async def generate_slides(req: dict):
    from backend.design_generator import generate_slide_deck
    return generate_slide_deck(
        title=req.get("title", "Presentation"),
        slides=req.get("slides", []),
        palette_name=req.get("palette", "midnight"),
    )

@app.post("/api/design/review")
async def generate_design_review_api(req: dict):
    from backend.design_generator import generate_design_review, save_html
    html = generate_design_review(
        req.get("project_name", "Project"),
        req.get("issues", []),
        req.get("palette", "neutral"),
    )
    path = req.get("save_path", "")
    if path:
        save_html(html, path)
    return {"html": html, "size": len(html)}

# ─── Spec-Driven Development (spec-kit-inspired) ──────────────────────────

@app.post("/api/spec/create")
async def create_spec(req: CreateSpecRequest):
    from backend.spec_driven_dev import create_spec
    return await create_spec(
        project_name=req.project_name,
        goal=req.goal,
        context=req.context,
        requirements=req.requirements,
    )

@app.post("/api/spec/{spec_id}/tasks")
async def generate_spec_tasks(spec_id: str):
    from backend.spec_driven_dev import generate_tasks
    return await generate_tasks(spec_id)

@app.post("/api/spec/{spec_id}/implement/{task_id}")
async def implement_task(spec_id: str, task_id: str, req: dict = {}):
    from backend.spec_driven_dev import generate_implementation
    return await generate_implementation(spec_id, task_id, req.get("project_path", ""))

@app.post("/api/spec/apply")
async def apply_implementation(req: ApplyImplementationRequest):
    from backend.spec_driven_dev import apply_implementation
    return apply_implementation(req.project_path, req.files)

@app.get("/api/spec/list")
async def list_specs():
    from backend.spec_driven_dev import list_specs
    return list_specs()

@app.get("/api/spec/{spec_id}")
async def get_spec(spec_id: str):
    from backend.spec_driven_dev import _load_spec
    spec = _load_spec(spec_id)
    if not spec:
        raise HTTPException(404, "Spec not found")
    return spec

# ─── Voice Interface (VibeVoice-inspired) ──────────────────────────────────

@app.get("/api/voice/status")
async def voice_status():
    from backend.voice_interface import get_voice_status
    return get_voice_status()

@app.post("/api/voice/speak")
async def voice_speak(req: VoiceSpeakRequest):
    from backend.voice_interface import speak
    return speak(req.text, req.voice, req.backend)

@app.post("/api/voice/command")
async def voice_command(req: VoiceCommandRequest):
    from backend.voice_commands import parse_command, execute_command
    parsed = await parse_command(req.text)
    result = await execute_command(parsed)
    return result

@app.get("/api/voice/help")
async def voice_help():
    from backend.voice_commands import get_help_text
    return {"help": get_help_text()}

# ─── LLM Optimizer (TurboQuant-inspired) ────────────────────────────────────

@app.get("/api/optimizer/config")
async def get_optimizer_config(model: str = "", vram: int = 0):
    from backend.llm_optimizer import get_optimization_config
    return get_optimization_config(model, vram)

@app.get("/api/optimizer/strategies")
async def list_optimization_strategies():
    from backend.llm_optimizer import OPTIMIZATION_STRATEGIES
    return OPTIMIZATION_STRATEGIES

@app.get("/api/optimizer/serving-command")
async def get_serving_command(model: str = "", port: int = 8000):
    from backend.llm_optimizer import get_serving_command
    return {"command": get_serving_command(model, port)}

# ─── openvscode-server integration ─────────────────────────────────────────

@app.get("/api/vscode/status")
async def vscode_status():
    result = {
        "available": False,
        "port": 8080,
        "command": "",
    }
    import shutil
    if shutil.which("openvscode-server"):
        result["available"] = True
        result["command"] = "openvscode-server --port 8080 --without-connection-token"
    elif Path(os.path.expanduser("~/.openvscode-server/bin/openvscode-server")).exists():
        result["available"] = True
        result["command"] = "~/.openvscode-server/bin/openvscode-server --port 8080 --without-connection-token"
    else:
        result["install_url"] = "https://github.com/gitpod-io/openvscode-server"
        result["install_command"] = "mkdir -p ~/.openvscode-server && curl -fL https://github.com/gitpod-io/openvscode-server/releases/latest/download/openvscode-server-v${VERSION}-linux-x64.tar.gz | tar xzf - -C ~/.openvscode-server --strip 1"
    return result

# ─── Serve Frontend (Production) ────────────────────────────────────────────

# Path to the built frontend (relative to backend package)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "dist"

if FRONTEND_DIR.exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React frontend for any non-API route."""
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("ws"):
            raise HTTPException(404)

        static_file = FRONTEND_DIR / full_path
        if static_file.is_file():
            return FileResponse(str(static_file))

        # SPA fallback - serve index.html for all other routes
        return FileResponse(str(FRONTEND_DIR / "index.html"))
