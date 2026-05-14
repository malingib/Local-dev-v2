"""
Context optimizer — inspired by mksglu/context-mode.
Sandboxes tool outputs, compresses context window, tracks session continuity.
Provides MCP-style sandbox tools for reducing LLM context consumption.
"""
import json
import re
import time
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple


_CONTEXT_STATS = {
    "total_raw_chars": 0,
    "total_compressed_chars": 0,
    "sandbox_calls": 0,
    "savings_by_tool": {},
}


def _get_db_path() -> Path:
    d = Path.home() / ".codeaudit"
    d.mkdir(parents=True, exist_ok=True)
    return d / "context_cache.db"


def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(_get_db_path()))
    db.execute("""
        CREATE TABLE IF NOT EXISTS context_cache (
            key TEXT PRIMARY KEY,
            content TEXT,
            summary TEXT,
            char_count INTEGER,
            compressed_count INTEGER,
            created_at TEXT,
            accessed_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS session_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT,
            summary TEXT,
            detail TEXT,
            created_at TEXT
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_events 
        ON session_events(session_id, created_at)
    """)
    db.commit()
    return db


def sandbox_output(content: str, tool_name: str = "unknown", max_chars: int = 500) -> str:
    """Sandbox tool output: strip whitespace, truncate, summarize structure."""
    raw_len = len(content)
    content = content.strip()

    if not content:
        return ""

    if raw_len <= max_chars:
        _track_savings(tool_name, raw_len, raw_len)
        return content

    lines = content.splitlines()
    line_count = len(lines)
    word_count = len(content.split())

    if line_count > 20:
        head = lines[:10]
        tail = lines[-5:]
        body_summary = f"... ({line_count - 15} lines omitted) ..."
        compressed = "\n".join(head) + "\n" + body_summary + "\n" + "\n".join(tail)
    else:
        compressed = content[:max_chars] + "\n... (truncated) ..."

    compressed_len = len(compressed)
    _track_savings(tool_name, raw_len, compressed_len)

    header = f"[sandbox:{tool_name}] {line_count} lines, {word_count} words, compressed from {raw_len} to {compressed_len} chars ({_savings_pct(raw_len, compressed_len)}% reduction)\n"
    return header + compressed


def sandbox_json(data: Any, tool_name: str = "json", max_items: int = 20) -> str:
    """Sandbox JSON output: truncate long arrays, summarize structure."""
    raw = json.dumps(data, indent=2, default=str)
    raw_len = len(raw)

    if isinstance(data, list) and len(data) > max_items:
        head = data[:max_items]
        remaining = len(data) - max_items
        compressed = json.dumps(head, indent=2, default=str)
        compressed += f"\n  ... ({remaining} more items omitted) ..."
    elif isinstance(data, dict):
        keys = list(data.keys())
        if len(keys) > 15:
            head = {k: data[k] for k in keys[:15]}
            remaining = len(keys) - 15
            compressed = json.dumps(head, indent=2, default=str)
            compressed += f"\n  ... ({remaining} more keys omitted) ..."
        else:
            compressed = raw
    else:
        compressed = raw[:2000]

    compressed_len = len(compressed)
    _track_savings(tool_name, raw_len, compressed_len)

    header = f"[sandbox:json] compressed from {raw_len} to {compressed_len} chars ({_savings_pct(raw_len, compressed_len)}% reduction)\n"
    return header + compressed


def sandbox_file(content: str, filepath: str, max_lines: int = 50) -> str:
    """Sandbox file content: show structure, truncate long files."""
    raw_len = len(content)
    lines = content.splitlines()
    line_count = len(lines)

    if line_count <= max_lines:
        _track_savings("file_read", raw_len, raw_len)
        return content

    head = lines[:int(max_lines * 0.7)]
    tail = lines[-int(max_lines * 0.3):]
    body = f"\n... ({line_count - len(head) - len(tail)} lines omitted) ...\n"
    compressed = "\n".join(head) + body + "\n".join(tail)

    compressed_len = len(compressed)
    _track_savings("file_read", raw_len, compressed_len)

    header = f"[sandbox:file] {filepath}: {line_count} lines, compressed from {raw_len} to {compressed_len} chars ({_savings_pct(raw_len, compressed_len)}% reduction)\n"
    return header + compressed


def sandbox_diff(diff_text: str, max_lines: int = 40) -> str:
    """Sandbox diff output: only show changed hunks with context."""
    raw_len = len(diff_text)
    if not diff_text.strip():
        return ""

    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        _track_savings("diff", raw_len, raw_len)
        return diff_text

    hunks = []
    current_hunk = []
    for line in lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif current_hunk:
            current_hunk.append(line)
    if current_hunk:
        hunks.append(current_hunk)

    compressed_lines = []
    for i, hunk in enumerate(hunks):
        if i >= 5:
            compressed_lines.append(f"... ({len(hunks) - 5} more hunks omitted) ...")
            break
        hunk_lines = hunk[:int(max_lines / len(hunks))]
        if len(hunk) > len(hunk_lines):
            hunk_lines.append(f"... ({len(hunk) - len(hunk_lines)} lines in this hunk omitted) ...")
        compressed_lines.extend(hunk_lines)

    compressed = "\n".join(compressed_lines)
    compressed_len = len(compressed)
    _track_savings("diff", raw_len, compressed_len)

    header = f"[sandbox:diff] {len(lines)} lines → {len(compressed_lines)} lines ({_savings_pct(raw_len, compressed_len)}% reduction)\n"
    return header + compressed


def track_session_event(session_id: str, event_type: str, summary: str, detail: str = ""):
    """Track a session event for continuity."""
    db = _get_db()
    db.execute(
        "INSERT INTO session_events (session_id, event_type, summary, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, event_type, summary[:200], detail[:1000], datetime.utcnow().isoformat()),
    )
    db.commit()


def get_session_context(session_id: str, max_events: int = 20) -> List[Dict[str, Any]]:
    """Get recent session events for context restoration."""
    db = _get_db()
    cursor = db.execute(
        "SELECT event_type, summary, detail, created_at FROM session_events WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
        (session_id, max_events),
    )
    events = []
    for row in cursor.fetchall():
        events.append({
            "type": row[0],
            "summary": row[1],
            "detail": row[2],
            "timestamp": row[3],
        })
    return events


def get_session_summary(session_id: str) -> str:
    """Generate a compressed session summary for context restoration."""
    events = get_session_context(session_id, 30)
    if not events:
        return ""

    lines = [f"=== Session {session_id[:8]} Context ==="]
    for e in reversed(events):
        ts = e["timestamp"][11:19] if e["timestamp"] else ""
        lines.append(f"  [{ts}] {e['type']}: {e['summary']}")

    summary = "\n".join(lines)
    return sandbox_output(summary, "session_summary")


def cache_context(key: str, content: str) -> str:
    """Cache context with automatic compression and dedup."""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    summary = content[:100].replace("\n", " ").strip()
    compressed = sandbox_output(content, "cache")

    db = _get_db()
    db.execute(
        """INSERT OR REPLACE INTO context_cache (key, content, summary, char_count, compressed_count, created_at, accessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (content_hash[:16], content, summary, len(content), len(compressed),
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
    )
    db.commit()

    return compressed


def get_cached(key: str) -> Optional[str]:
    """Retrieve cached context."""
    key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
    db = _get_db()
    cursor = db.execute(
        "SELECT content FROM context_cache WHERE key = ?", (key_hash,)
    )
    row = cursor.fetchone()
    if row:
        db.execute("UPDATE context_cache SET accessed_at = ? WHERE key = ?",
                    (datetime.utcnow().isoformat(), key_hash))
        db.commit()
        return row[0]
    return None


def get_context_stats() -> Dict[str, Any]:
    """Get context optimization statistics."""
    total_raw = _CONTEXT_STATS.get("total_raw_chars", 0) or 1
    total_compressed = _CONTEXT_STATS.get("total_compressed_chars", 0) or 1

    return {
        "total_raw_chars": _CONTEXT_STATS["total_raw_chars"],
        "total_compressed_chars": _CONTEXT_STATS["total_compressed_chars"],
        "sandbox_calls": _CONTEXT_STATS["sandbox_calls"],
        "savings_percent": round((1 - total_compressed / total_raw) * 100, 1) if total_raw > 0 else 0,
        "savings_by_tool": _CONTEXT_STATS["savings_by_tool"],
    }


def reset_stats():
    _CONTEXT_STATS["total_raw_chars"] = 0
    _CONTEXT_STATS["total_compressed_chars"] = 0
    _CONTEXT_STATS["sandbox_calls"] = 0
    _CONTEXT_STATS["savings_by_tool"] = {}


def _track_savings(tool: str, raw: int, compressed: int):
    _CONTEXT_STATS["total_raw_chars"] += raw
    _CONTEXT_STATS["total_compressed_chars"] += compressed
    _CONTEXT_STATS["sandbox_calls"] += 1
    if tool not in _CONTEXT_STATS["savings_by_tool"]:
        _CONTEXT_STATS["savings_by_tool"][tool] = {"calls": 0, "raw_chars": 0, "compressed_chars": 0}
    _CONTEXT_STATS["savings_by_tool"][tool]["calls"] += 1
    _CONTEXT_STATS["savings_by_tool"][tool]["raw_chars"] += raw
    _CONTEXT_STATS["savings_by_tool"][tool]["compressed_chars"] += compressed


def _savings_pct(raw: int, compressed: int) -> float:
    if raw == 0:
        return 0.0
    return round((1 - compressed / raw) * 100, 1)
