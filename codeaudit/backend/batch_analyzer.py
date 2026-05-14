"""
Batch analyzer — groups files and analyzes multiple per LLM prompt.
Reduces API calls by batching related files together.

Strategy:
  - Group files by directory/type (e.g., all components together, all routes together)
  - Send batch of 3-5 files per prompt (depends on total size)
  - LLM returns findings for all files in the batch
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models import Finding, FindingType, Severity, AgentType, Location
from backend.llm_router import llm_json, llm_call, llm_batch, LLMError


# Max files per batch (higher = fewer API calls, but larger prompts)
MAX_FILES_PER_BATCH = 4
# Max total prompt size per batch (chars)
MAX_BATCH_SIZE = 80000


def _extension_group(ext: str) -> str:
    """Map a file extension to a logical group name."""
    ext = ext.lower().lstrip(".")
    FRONTEND = {"tsx", "jsx", "ts", "js", "vue", "svelte", "html", "css", "scss", "less"}
    BACKEND = {"py", "go", "rs", "rb", "php", "java", "kt", "cs"}
    CONFIG = {"json", "yaml", "yml", "toml", "ini", "cfg", "conf", "env"}
    STYLES = {"css", "scss", "less", "sass"}
    DATA = {"sql", "graphql", "proto", "xml", "csv"}
    return (
        "frontend" if ext in FRONTEND else
        "backend" if ext in BACKEND else
        "config" if ext in CONFIG else
        "styles" if ext in STYLES else
        "data" if ext in DATA else
        "other"
    )


def group_files_by_type(files: List[str]) -> Dict[str, List[str]]:
    """Group file paths by their type/directory pattern.

    Prefers pattern-based grouping (e.g., files containing 'component')
    but falls back to extension-based grouping for files that don't
    match any pattern. This prevents unrelated file types from being
    batched together in 'other'.
    """
    groups: Dict[str, List[str]] = {
        "components": [],
        "pages": [],
        "routes": [],
        "utils": [],
        "config": [],
        "models": [],
        "tests": [],
    }

    ext_groups: Dict[str, List[str]] = {}

    for f in files:
        lower = f.lower()
        if "component" in lower or "widget" in lower or "view" in lower:
            groups["components"].append(f)
        elif "page" in lower or "screen" in lower:
            groups["pages"].append(f)
        elif "route" in lower or "api/" in lower or "endpoint" in lower:
            groups["routes"].append(f)
        elif "util" in lower or "helper" in lower or "lib/" in lower:
            groups["utils"].append(f)
        elif "config" in lower or ".env" in lower or "setting" in lower:
            groups["config"].append(f)
        elif "model" in lower or "schema" in lower or "entity" in lower:
            groups["models"].append(f)
        elif "test" in lower or "spec" in lower:
            groups["tests"].append(f)
        else:
            ext = f.split(".")[-1] if "." in f else ""
            eg = _extension_group(ext)
            if eg not in ext_groups:
                ext_groups[eg] = []
            ext_groups[eg].append(f)

    # Merge extension-based groups into the main groups dict
    result = {**groups}
    for eg_name, eg_files in ext_groups.items():
        if eg_files:
            result[eg_name] = eg_files

    return result


def create_batches(
    files: List[str],
    read_file_fn,  # Callable: (path) -> str
    max_per_batch: int = MAX_FILES_PER_BATCH,
    max_size: int = MAX_BATCH_SIZE
) -> List[List[str]]:
    """
    Split files into batches that fit within size limits.

    Args:
        files: List of relative file paths
        read_file_fn: Function to read file content
        max_per_batch: Max files per batch
        max_size: Max total content size per batch (chars)

    Returns:
        List of batches, each a list of file paths
    """
    batches: List[List[str]] = []
    current_batch: List[str] = []
    current_size = 0

    for f in files:
        try:
            content = read_file_fn(f)
            file_size = len(content)
        except Exception:
            file_size = 0

        # If a single file is too large, put it alone
        if file_size > max_size:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            batches.append([f])
            continue

        # If adding this file exceeds the batch size, start new batch
        if current_size + file_size > max_size or len(current_batch) >= max_per_batch:
            if current_batch:
                batches.append(current_batch)
            current_batch = [f]
            current_size = file_size
        else:
            current_batch.append(f)
            current_size += file_size

    if current_batch:
        batches.append(current_batch)

    return batches


def build_batch_prompt(
    files: List[str],
    read_file_fn,
    analysis_prompt: str,
    agent_name: str = "Code Auditor"
) -> str:
    """
    Build a prompt that asks the LLM to analyze multiple files.

    Returns JSON-structured prompt.
    """
    file_contents = []
    for f in files:
        try:
            content = read_file_fn(f)
            # Truncate very large files
            if len(content) > 20000:
                content = content[:10000] + "\n\n... [truncated] ...\n\n" + content[-5000:]
            file_contents.append(f"### File: {f}\n```{f.split('.')[-1] if '.' in f else 'text'}\n{content}\n```")
        except Exception as e:
            file_contents.append(f"### File: {f}\n[Error reading: {e}]")

    files_section = "\n\n".join(file_contents)

    prompt = f"""You are a {agent_name}. Analyze the following files and identify all issues.

{analysis_prompt}

Return your findings as a JSON array. Each finding must include:
- "file": the file path
- "line_start": starting line number (or null if unknown)
- "title": short description of the issue
- "severity": one of "critical", "high", "medium", "low", "info"
- "type": one of "bug", "security", "performance", "code_quality", "best_practice"
- "description": detailed explanation
- "suggested_fix": how to fix it
- "code_snippet": relevant code (max 10 lines)

Return ONLY valid JSON. No explanation, no markdown.

Files to analyze:
{files_section}"""

    return prompt


def parse_batch_findings(response: Dict[str, Any], files: List[str]) -> List[Dict[str, Any]]:
    """
    Parse LLM response for batch findings.
    Handles both array and dict-with-findings responses.
    """
    if isinstance(response, list):
        findings = response
    elif isinstance(response, dict):
        findings = response.get("findings", [])
    else:
        findings = []

    # Ensure each finding has a file reference
    for finding in findings:
        if not finding.get("file"):
            # Default to first file if not specified
            finding["file"] = files[0] if files else ""

    return findings


async def analyze_batch(
    files: List[str],
    read_file_fn,
    analysis_prompt: str,
    agent_name: str = "Code Auditor",
    model: str = "gemini-flash"
) -> List[Dict[str, Any]]:
    """
    Analyze a batch of files with a single LLM call.

    Returns list of finding dicts (parsed from JSON response).
    """
    prompt = build_batch_prompt(files, read_file_fn, analysis_prompt, agent_name)

    try:
        response = await llm_json(prompt, model=model, temperature=0.1)
        return parse_batch_findings(response, files)
    except LLMError as e:
        return [{"error": str(e), "file": files[0] if files else ""}]
