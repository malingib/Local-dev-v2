"""
Pydantic models for CodeAudit.
Defines all data structures: Session, Finding, Hypothesis, ProjectInfo, etc.
"""
import os
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SessionState(str, Enum):
    INGEST = "ingest"
    AUDIT = "audit"
    HYPOTHESIS_LOOP = "hypothesis_loop"
    APPROVAL_FLOW = "approval_flow"
    APPLY = "apply"
    COMPLETE = "complete"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


class SessionMode(str, Enum):
    AUDIT = "audit"
    AUDIT_FIX = "audit_fix"
    GOAL = "goal"


class FindingStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ESCALATED = "escalated"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AgentType(str, Enum):
    AUDITOR = "auditor"
    UI = "ui"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MOBILE = "mobile"
    META = "meta"


class FindingType(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UI = "ui"
    ACCESSIBILITY = "accessibility"
    CODE_QUALITY = "code_quality"
    BEST_PRACTICE = "best_practice"
    DEPRECATED = "deprecated"


class ApprovalStage(str, Enum):
    SKETCH = "sketch"
    PREVIEW = "preview"
    FULL = "full"


class ApprovalResponse(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    TWEAK = "tweak"


class Location(BaseModel):
    file: str = ""
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function: Optional[str] = None
    class_name: Optional[str] = None


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    claim: str
    confidence: float = 0.5
    status: str = "active"  # active, confirmed, ruled_out
    evidence_for: List[str] = Field(default_factory=list)
    evidence_against: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    hypothesis_id: str = ""
    action: str = ""
    tool: str = "read_file"  # read_file, grep, run_test, run_command, screenshot
    params: Dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    information_gain: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatchChange(BaseModel):
    file: str
    find: str
    replace: str


class Finding(BaseModel):
    model_config = {"use_enum_values": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    type: FindingType = FindingType.CODE_QUALITY
    severity: Severity = Severity.MEDIUM
    status: FindingStatus = FindingStatus.OPEN
    agent: AgentType = AgentType.AUDITOR
    location: Dict[str, Any] = Field(default_factory=dict)
    code_snippet: str = ""
    suggested_fix: str = ""
    proposed_patch: str = ""
    patch_explanation: str = ""
    hypothesis_tree: List[Hypothesis] = Field(default_factory=list)
    experiments: List[Experiment] = Field(default_factory=list)
    rejection_reason: str = ""
    auto_approvable: bool = False
    approval_stage: Optional[ApprovalStage] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectInfo(BaseModel):
    name: str = ""
    path: str = ""
    github_url: Optional[str] = None
    detected_stack: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)


class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent: str = "system"
    message: str
    level: str = "info"  # info, success, warning, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RejectionMemory(BaseModel):
    finding_title: str
    finding_type: str
    location: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    model_config = {"use_enum_values": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    mode: SessionMode = SessionMode.AUDIT
    state: SessionState = SessionState.INGEST
    goal: str = ""
    project: Optional[ProjectInfo] = None
    findings: List[Finding] = Field(default_factory=list)
    approval_queue: List[str] = Field(default_factory=list)
    current_finding_id: Optional[str] = None
    activity_log: List[ActivityLog] = Field(default_factory=list)
    rejection_memory: List[RejectionMemory] = Field(default_factory=list)
    stack_detected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    KEPT = "kept"
    DISCARDED = "discarded"
    CRASHED = "crashed"


class ExperimentResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    commit_hash: str = ""
    val_bpb: float = 0.0
    memory_gb: float = 0.0
    status: ExperimentStatus = ExperimentStatus.PENDING
    description: str = ""
    target_file: str = ""
    diff_preview: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0


class ExperimentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tag: str = ""
    branch: str = ""
    project_path: str = ""
    target_file: str = ""
    baseline: Optional[ExperimentResult] = None
    experiments: List[ExperimentResult] = Field(default_factory=list)
    best_bpb: float = float('inf')
    best_experiment_id: Optional[str] = None
    is_running: bool = False
    time_budget: int = 300
    total_runs: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Config(BaseModel):
    project_name: str = "CodeAudit Project"
    github_url: Optional[str] = None
    local_path: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    github_token: Optional[str] = None
    figma_token: Optional[str] = None
    enabled_agents: List[str] = Field(default_factory=lambda: [
        "auditor", "ui", "security", "performance_static", "mobile_responsiveness"
    ])
    experiment_time_budget: int = 300
    self_modify_enabled: bool = False
    auto_approve: Dict[str, bool] = Field(default_factory=lambda: {
        "missing_alt_text": True,
        "missing_meta_viewport": True,
        "missing_lazy_loading": True,
        "input_type_fix": True,
    })
    max_steps: int = 20
    confidence_threshold: float = 0.85
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    # LLM settings
    default_model: str = "gemini-pro"
    fast_model: str = "gemini-flash"
    use_swarm: bool = False  # Disable swarm by default — most users want fast audits
    cors_origins: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173",
    ])


import requests
import base64


NVIDIA_INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def read_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def nvidia_chat_completion(
    prompt: str,
    model: str = "moonshotai/kimi-k2.6",
    api_key: Optional[str] = None,
    max_tokens: int = 16384,
    temperature: float = 1.0,
    top_p: float = 1.0,
    stream: bool = True,
) -> str:
    if not api_key:
        api_key = os.environ.get("NVIDIA_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": stream,
        "chat_template_kwargs": {"thinking": True},
    }

    response = requests.post(NVIDIA_INVOKE_URL, headers=headers, json=payload, stream=stream)
    if stream:
        result = []
        for line in response.iter_lines():
            if line:
                result.append(line.decode("utf-8"))
        return "\n".join(result)
    else:
        return response.json()


NVIDIA_OPENAI_BASE_URL = "https://integrate.api.nvidia.com/v1"

def deepseek_chat_completion(
    prompt: str,
    model: str = "deepseek-ai/deepseek-v4-pro",
    api_key: Optional[str] = None,
    max_tokens: int = 16384,
    temperature: float = 1.0,
    top_p: float = 0.95,
    thinking: bool = False,
    stream: bool = True,
) -> str:
    if not api_key:
        api_key = os.environ.get("NVIDIA_API_KEY", "")
    from openai import OpenAI
    client = OpenAI(base_url=NVIDIA_OPENAI_BASE_URL, api_key=api_key)

    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        extra_body={"chat_template_kwargs": {"thinking": thinking}},
        stream=stream,
    )

    if stream:
        result = []
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            if chunk.choices and chunk.choices[0].delta.content is not None:
                result.append(chunk.choices[0].delta.content)
        return "".join(result)
    else:
        return completion
