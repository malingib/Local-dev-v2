"""
Spec-Driven Development workflow — inspired by github/spec-kit (97k★).
Implements Plan → Tasks → Implement pipeline with structured artifacts.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.llm_router import llm_call


def get_specs_dir() -> Path:
    d = Path.home() / ".codeaudit" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Phase 1: Plan ───────────────────────────────────────────────────────

async def create_spec(
    project_name: str,
    goal: str,
    context: str = "",
    requirements: List[str] = None,
) -> Dict[str, Any]:
    spec = {
        "id": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "project": project_name,
        "goal": goal,
        "context": context,
        "requirements": requirements or [],
        "phases": [],
        "created_at": datetime.utcnow().isoformat(),
        "status": "draft",
    }

    try:
        prompt = (
            f"Create a development spec for: {goal}\n\n"
            f"Project: {project_name}\n"
            f"Context: {context}\n"
            f"Requirements: {json.dumps(requirements or [])}\n\n"
            f"Return JSON with:\n"
            f"  - 'summary': 2-3 sentence overview\n"
            f"  - 'phases': list of {{'name', 'description', 'tasks': [{{'title', 'description', 'effort': 'small/medium/large'}}]}}\n"
            f"  - 'risks': list of potential issues\n"
            f"  - 'acceptance_criteria': list of criteria\n"
        )
        plan = await llm_call(prompt, model="gemini-flash")

        spec["plan"] = plan
        spec["status"] = "planned"
    except Exception as e:
        spec["plan"] = {"error": str(e)}

    _save_spec(spec)
    return spec


# ── Phase 2: Tasks ──────────────────────────────────────────────────────

async def generate_tasks(spec_id: str) -> Dict[str, Any]:
    spec = _load_spec(spec_id)
    if not spec:
        return {"error": "Spec not found"}

    try:
        prompt = (
            f"Break this spec into actionable engineering tasks:\n\n"
            f"Goal: {spec.get('goal', '')}\n"
            f"Plan: {json.dumps(spec.get('plan', {}))}\n\n"
            f"Return JSON with:\n"
            f"  - 'tasks': list of {{'id', 'title', 'description', 'files_to_modify': [], 'dependencies': [], 'effort': 'small/medium/large', 'priority': 1-5}}\n"
            f"  - 'estimated_total_effort': 'hours'\n"
            f"  - 'recommended_order': list of task IDs\n"
        )
        tasks = await llm_call(prompt, model="gemini-flash")

        spec["tasks"] = tasks
        spec["status"] = "tasks_ready"
        _save_spec(spec)
        return {"spec_id": spec_id, "tasks": tasks}
    except Exception as e:
        return {"error": str(e)}


# ── Phase 3: Implement ──────────────────────────────────────────────────

async def generate_implementation(
    spec_id: str,
    task_id: str,
    project_path: str,
) -> Dict[str, Any]:
    spec = _load_spec(spec_id)
    if not spec:
        return {"error": "Spec not found"}

    tasks_data = spec.get("tasks", {})
    all_tasks = tasks_data.get("tasks", []) if isinstance(tasks_data, dict) else []
    task = next((t for t in all_tasks if t.get("id") == task_id), None)

    if not task:
        return {"error": f"Task {task_id} not found"}

    files_to_read = task.get("files_to_modify", [])
    file_contents = {}
    for f in files_to_read:
        fp = Path(project_path) / f
        if fp.exists():
            file_contents[f] = fp.read_text(errors="ignore")[:2000]

    try:
        prompt = (
            f"Implement task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Files to modify: {json.dumps(files_to_read)}\n"
            f"Current contents: {json.dumps(file_contents)}\n\n"
            f"Return JSON with:\n"
            f"  - 'files': list of {{'path', 'content'}} with complete new file contents\n"
            f"  - 'summary': what was implemented\n"
            f"  - 'test_instructions': how to verify\n"
        )
        implementation = await llm_call(prompt, model="gemini-flash")

        return {
            "task_id": task_id,
            "implementation": implementation,
            "spec_id": spec_id,
        }
    except Exception as e:
        return {"error": str(e)}


def apply_implementation(
    project_path: str,
    files: List[Dict[str, str]],
) -> Dict[str, Any]:
    applied = []
    errors = []

    for f in files:
        filepath = Path(project_path) / f.get("path", "")
        content = f.get("content", "")
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")
            applied.append(f.get("path", ""))
        except Exception as e:
            errors.append({"file": f.get("path", ""), "error": str(e)})

    return {"applied": applied, "errors": errors}


# ── Quality Checklist ───────────────────────────────────────────────────

QUALITY_CHECKLIST = [
    "Is there error handling for edge cases?",
    "Are there unit tests for new code?",
    "Is the code documented?",
    "Are there no hardcoded secrets/credentials?",
    "Does the code follow existing patterns?",
    "Is there input validation?",
    "Are there no performance bottlenecks?",
    "Is the code accessible (a11y for UI changes)?",
    "Are dependency changes reflected in package files?",
    "Is there a migration path for breaking changes?",
]


async def run_quality_check(project_path: str, files_changed: List[str]) -> Dict[str, Any]:
    file_contents = {}
    for f in files_changed:
        fp = Path(project_path) / f
        if fp.exists():
            file_contents[f] = fp.read_text(errors="ignore")[:2000]

    try:
        prompt = (
            f"Run quality checklist on these changed files:\n\n"
            f"Files: {json.dumps(files_changed)}\n"
            f"Checklist: {json.dumps(QUALITY_CHECKLIST)}\n"
            f"Contents: {json.dumps(file_contents)}\n\n"
            f"Return JSON with:\n"
            f"  - 'passed': list of checklist items that pass\n"
            f"  - 'failed': list of {{'item', 'file', 'recommendation'}}\n"
            f"  - 'score': percentage 0-100\n"
        )
        result = await llm_call(prompt, model="gemini-flash")
        return result
    except Exception as e:
        return {"error": str(e)}


# ── Persistence ─────────────────────────────────────────────────────────

def _save_spec(spec: Dict[str, Any]):
    path = get_specs_dir() / f"{spec['id']}.json"
    path.write_text(json.dumps(spec, indent=2, default=str))


def _load_spec(spec_id: str) -> Optional[Dict[str, Any]]:
    path = get_specs_dir() / f"{spec_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    path2 = get_specs_dir() / f"{spec_id}.json"
    if not path2.exists():
        for p in get_specs_dir().glob("*.json"):
            if p.stem.startswith(spec_id):
                return json.loads(p.read_text())
    return None


def list_specs() -> List[Dict[str, Any]]:
    specs = []
    for p in sorted(get_specs_dir().glob("*.json"), reverse=True):
        try:
            data = json.loads(p.read_text())
            specs.append({
                "id": data.get("id", p.stem),
                "project": data.get("project", ""),
                "goal": data.get("goal", "")[:100],
                "status": data.get("status", "unknown"),
                "created_at": data.get("created_at", ""),
            })
        except Exception:
            continue
    return specs
