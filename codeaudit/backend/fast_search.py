"""
Fast file search toolkit for AI agents.
Inspired by dmtrKovalenko/fff.nvim — typo-resistant, frecency-ranked,
multi-mode file search with MCP-style interface.
"""
import os
import re
import json
import time
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

from backend.constants import IGNORE_DIRS


_SEARCH_HISTORY: Dict[str, Dict[str, Any]] = {}
_HISTORY_FILE = None


def _get_history_path() -> Path:
    d = Path.home() / ".codeaudit"
    d.mkdir(parents=True, exist_ok=True)
    return d / "search_history.json"


def _load_history():
    global _SEARCH_HISTORY
    path = _get_history_path()
    if path.exists():
        try:
            _SEARCH_HISTORY = json.loads(path.read_text())
        except Exception:
            _SEARCH_HISTORY = {}


def _save_history():
    path = _get_history_path()
    try:
        path.write_text(json.dumps(_SEARCH_HISTORY, indent=2, default=str))
    except Exception:
        pass


def _record_access(filepath: str):
    now = time.time()
    entry = _SEARCH_HISTORY.get(filepath, {"count": 0, "first_seen": now, "last_access": now})
    entry["count"] += 1
    entry["last_access"] = now
    _SEARCH_HISTORY[filepath] = entry
    _save_history()


def _frecency_score(filepath: str) -> float:
    entry = _SEARCH_HISTORY.get(filepath)
    if not entry:
        return 0.0
    now = time.time()
    hours_since = (now - entry["last_access"]) / 3600
    freshness = math.exp(-hours_since / 24)
    frequency = math.log1p(entry["count"])
    return freshness * frequency


def _typo_similarity(query: str, target: str) -> float:
    q, t = query.lower(), target.lower()
    if q in t:
        return 1.0
    return SequenceMatcher(None, q, t).ratio()


def _find_files(root: str, extensions: Optional[List[str]] = None) -> List[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    results = []
    ignore_set = IGNORE_DIRS | {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".next", "target", ".git", ".svn"}

    for p in root_path.rglob("*"):
        if p.is_dir():
            continue
        if any(part in ignore_set for part in p.parts):
            continue
        if extensions and p.suffix.lstrip(".") not in extensions:
            continue
        results.append(p)

    return results


def _find_files_fast(root: str, extensions: Optional[List[str]] = None, max_results: int = 5000) -> List[str]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    ignore_set = IGNORE_DIRS | {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".next", "target"}
    results = []
    extensions_set = set(extensions) if extensions else None

    try:
        for p in root_path.rglob("*"):
            if p.is_dir():
                continue
            if any(part in ignore_set for part in p.parts):
                continue
            if extensions_set and p.suffix.lstrip(".") not in extensions_set:
                continue
            results.append(str(p.relative_to(root_path)))
            if len(results) >= max_results:
                break
    except PermissionError:
        pass

    return results


def search_files(
    root: str,
    query: str,
    mode: str = "fuzzy",
    extensions: Optional[List[str]] = None,
    max_results: int = 30,
) -> List[Dict[str, Any]]:
    if mode == "path":
        return _search_by_path(root, query, extensions, max_results)
    elif mode == "content":
        return _search_by_content(root, query, extensions, max_results)
    else:
        return _search_fuzzy(root, query, extensions, max_results)


def _search_fuzzy(root: str, query: str, extensions: Optional[List[str]], max_results: int) -> List[Dict[str, Any]]:
    q = query.lower()
    q_parts = q.split()
    all_files = _find_files_fast(root, extensions, max_results * 20)
    scored = []

    for rel_path in all_files:
        fname = Path(rel_path).name.lower()
        full = rel_path.lower()

        if q in full:
            score = 1.0 + _frecency_score(str(Path(root) / rel_path))
            scored.append((score, rel_path))
            continue

        if all(part in full for part in q_parts):
            score = 0.9 + _frecency_score(str(Path(root) / rel_path))
            scored.append((score, rel_path))
            continue

        sim = _typo_similarity(query, fname)
        if sim > 0.6:
            score = sim * 0.8 + _frecency_score(str(Path(root) / rel_path)) * 0.2
            scored.append((score, rel_path))

    scored.sort(key=lambda x: -x[0])
    results = []
    for score, rel_path in scored[:max_results]:
        _record_access(str(Path(root) / rel_path))
        results.append({"path": rel_path, "score": round(score, 4), "mode": "fuzzy"})

    return results


def _search_by_path(root: str, query: str, extensions: Optional[List[str]], max_results: int) -> List[Dict[str, Any]]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    results = []
    q = query.lower()
    ignore_set = IGNORE_DIRS | {"node_modules", ".git", "__pycache__"}

    for p in root_path.rglob(f"*{query}*"):
        if p.is_dir():
            continue
        if any(part in ignore_set for part in p.parts):
            continue
        if extensions and p.suffix.lstrip(".") not in extensions:
            continue
        rel = str(p.relative_to(root_path))
        _record_access(str(p))
        results.append({"path": rel, "score": 1.0, "mode": "path"})
        if len(results) >= max_results:
            break

    if not results:
        for p in root_path.rglob("*"):
            if p.is_dir():
                continue
            if any(part in ignore_set for part in p.parts):
                continue
            if extensions and p.suffix.lstrip(".") not in extensions:
                continue
            rel = str(p.relative_to(root_path))
            if q in rel.lower():
                _record_access(str(p))
                results.append({"path": rel, "score": 0.9, "mode": "path"})
                if len(results) >= max_results:
                    break

    return results


def _search_by_content(root: str, query: str, extensions: Optional[List[str]], max_results: int) -> List[Dict[str, Any]]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    results = []
    ignore_set = IGNORE_DIRS | {"node_modules", ".git", "__pycache__", ".venv"}
    max_size = 500 * 1024
    q = query.lower()

    files = _find_files_fast(root, extensions, max_results * 10)
    for rel_path in files:
        full_path = root_path / rel_path
        try:
            if full_path.stat().st_size > max_size:
                continue
            content = full_path.read_text(errors="ignore")
            if q in content.lower():
                lines = content.lower().splitlines()
                context_lines = []
                for i, line in enumerate(lines):
                    if q in line:
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        snippet = "\n".join(lines[start:end])
                        context_lines.append({"line": i + 1, "snippet": snippet[:200]})
                _record_access(str(full_path))
                results.append({
                    "path": rel_path, "score": 1.0, "mode": "content",
                    "matches": len(context_lines),
                    "context": context_lines[:3],
                })
                if len(results) >= max_results:
                    break
        except Exception:
            continue

    return results


def get_recent_files(root: str, limit: int = 20) -> List[Dict[str, Any]]:
    _load_history()
    scored = []
    now = time.time()

    for filepath, entry in _SEARCH_HISTORY.items():
        if not Path(filepath).exists():
            continue
        if root and not str(filepath).startswith(str(Path(root).resolve())):
            continue
        hours_since = (now - entry["last_access"]) / 3600
        score = math.exp(-hours_since / 24) * math.log1p(entry["count"])
        scored.append((score, filepath, entry["last_access"], entry["count"]))

    scored.sort(key=lambda x: -x[0])
    results = []
    for score, filepath, last_access, count in scored[:limit]:
        try:
            rel = str(Path(filepath).relative_to(Path(root)))
        except ValueError:
            rel = filepath
        results.append({
            "path": rel, "score": round(score, 4),
            "access_count": count,
            "last_access": datetime.fromtimestamp(last_access).isoformat() if last_access else None,
        })
    return results


def search_symbols(root: str, query: str, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    q = query.lower()
    results = []
    ignore_set = IGNORE_DIRS | {"node_modules", ".git", "__pycache__"}

    symbol_patterns = {
        "py": [r"(?:^|\n)\s*(?:async\s+)?def\s+(\w+)", r"(?:^|\n)\s*(?:async\s+)?class\s+(\w+)"],
        "js": [r"(?:^|\n)\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"(?:^|\n)\s*class\s+(\w+)", r"(?:^|\n)\s*const\s+(\w+)\s*="],
        "ts": [r"(?:^|\n)\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"(?:^|\n)\s*(?:export\s+)?class\s+(\w+)", r"(?:^|\n)\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[:=]"],
        "tsx": [r"(?:^|\n)\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"(?:^|\n)\s*(?:export\s+)?class\s+(\w+)", r"(?:^|\n)\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[:=]"],
        "rs": [r"(?:^|\n)\s*(?:pub\s+)?fn\s+(\w+)", r"(?:^|\n)\s*(?:pub\s+)?(?:struct|enum|trait|impl|mod|type)\s+(\w+)"],
        "go": [r"(?:^|\n)\s*func\s+(\w+)", r"(?:^|\n)\s*type\s+(\w+)\s+(?:struct|interface)"],
        "java": [r"(?:^|\n)\s*(?:public|private|protected)?\s*(?:static\s+)?(?:class|interface|enum)\s+(\w+)", r"(?:^|\n)\s*(?:public|private|protected)?\s*\w+\s+(\w+)\s*\("],
    }

    for p in root_path.rglob("*"):
        if p.is_dir():
            continue
        if any(part in ignore_set for part in p.parts):
            continue
        ext = p.suffix.lstrip(".")
        patterns = symbol_patterns.get(ext)
        if not patterns:
            continue

        try:
            content = p.read_text(errors="ignore")
            for pat in patterns:
                for m in re.finditer(pat, content):
                    name = m.group(1)
                    if q in name.lower():
                        rel = str(p.relative_to(root_path))
                        results.append({
                            "path": rel,
                            "symbol": name,
                            "line": content[:m.start()].count("\n") + 1,
                        })
        except Exception:
            continue

    return results[:50]


_load_history()
