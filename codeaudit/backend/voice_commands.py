"""
Voice command parser — converts natural language speech into structured actions.
Uses LLM to parse: "start audit on /path/to/proj" → {"action": "audit", "path": "..."}
"""
import json
import re
from typing import Dict, Any, Optional
from backend.llm_router import llm_json

ACTIONS = [
    "audit", "ingest", "fix", "fix_all", "scan", "search",
    "create_session", "list_sessions", "show_session",
    "run_experiment", "establish_baseline", "propose_experiment",
    "open_settings", "open_skills", "open_graph", "open_design",
    "help", "status",
]


async def parse_command(text: str) -> Dict[str, Any]:
    text = text.strip().lower()

    # Direct keyword matching for common commands (fast path, no LLM)
    direct = _try_direct_match(text)
    if direct:
        return direct

    # LLM-based parsing for complex commands
    try:
        prompt = (
            f"Parse this voice command into a structured action:\n"
            f"Command: \"{text}\"\n\n"
            f"Available actions: {json.dumps(ACTIONS)}\n\n"
            f"Return JSON with:\n"
            f"  - 'action': one of the available actions\n"
            f"  - 'params': dict of parameters {{path, target, query, etc}}\n"
            f"  - 'confidence': 0.0 to 1.0\n"
            f"  - 'fallback_text': if confidence < 0.7, what to say back\n\n"
            f"Examples:\n"
            f"  'audit the project at /home/user/code' → {{\"action\":\"audit\",\"params\":{{\"path\":\"/home/user/code\"}},\"confidence\":0.9}}\n"
            f"  'show me my sessions' → {{\"action\":\"list_sessions\",\"params\":{{}},\"confidence\":0.95}}\n"
            f"  'search for config files' → {{\"action\":\"search\",\"params\":{{\"query\":\"config\"}},\"confidence\":0.85}}"
        )
        result = await llm_json(prompt, model="gemini-flash")
        return result
    except Exception as e:
        return {
            "action": "unknown",
            "params": {"raw": text},
            "confidence": 0.0,
            "error": str(e),
            "fallback_text": f"I didn't understand. You said: {text}",
        }


def _try_direct_match(text: str) -> Optional[Dict[str, Any]]:
    # Session commands
    m = re.match(r"(?:start|begin|run|do)\s+(?:an?\s+)?audit\s+(?:on\s+)?(?:\"([^\"]+)\"|'([^']+)'|(\S+))", text)
    if m:
        path = m.group(1) or m.group(2) or m.group(3) or ""
        return {"action": "audit", "params": {"path": path}, "confidence": 0.9}

    m = re.match(r"(?:list|show)\s+(?:my\s+)?sessions?", text)
    if m:
        return {"action": "list_sessions", "params": {}, "confidence": 0.95}

    m = re.match(r"(?:open|go\s+to|show)\s+(?:the\s+)?(?:settings|config)", text)
    if m:
        return {"action": "open_settings", "params": {}, "confidence": 0.9}

    m = re.match(r"(?:open|go\s+to|show)\s+(?:the\s+)?(?:skills|skill)", text)
    if m:
        return {"action": "open_skills", "params": {}, "confidence": 0.9}

    m = re.match(r"(?:open|go\s+to|show)\s+(?:the\s+)?graph", text)
    if m:
        return {"action": "open_graph", "params": {}, "confidence": 0.9}

    m = re.match(r"(?:open|go\s+to|show)\s+(?:the\s+)?(?:design|design\s+studio)", text)
    if m:
        return {"action": "open_design", "params": {}, "confidence": 0.9}

    m = re.match(r"(?:search|find)\s+(?:for\s+)?(.+)", text)
    if m:
        return {"action": "search", "params": {"query": m.group(1).strip()}, "confidence": 0.85}

    m = re.match(r"(?:help|what\s+can\s+you\s+do|commands)", text)
    if m:
        return {"action": "help", "params": {}, "confidence": 0.95}

    m = re.match(r"(?:(?:what|wha)\s+(?:is|are|was)\s+(?:the\s+)?|show\s+)(?:status|health|state)", text)
    if m:
        return {"action": "status", "params": {}, "confidence": 0.9}

    return None


def get_help_text() -> str:
    return (
        "I can understand these voice commands:\n"
        "- \"Start audit on /path/to/project\" — begin a code audit\n"
        "- \"List my sessions\" — show all sessions\n"
        "- \"Search for config files\" — file search\n"
        "- \"Open settings\" — go to settings\n"
        "- \"Open skills\" — go to skills library\n"
        "- \"What's the status?\" — system status\n"
        "- \"Help\" — show this help"
    )


async def execute_command(parsed: Dict[str, Any]) -> Dict[str, Any]:
    action = parsed.get("action", "unknown")
    params = parsed.get("params", {})

    responses = {
        "audit": f"Starting audit on {params.get('path', 'the project')}",
        "list_sessions": "Fetching your sessions",
        "search": f"Searching for {params.get('query', 'files')}",
        "open_settings": "Opening settings",
        "open_skills": "Opening skills library",
        "open_graph": "Opening knowledge graph",
        "open_design": "Opening design studio",
        "status": "Checking system status",
        "help": get_help_text(),
    }

    text = responses.get(action, f"Executing: {action}")
    return {
        "action": action,
        "params": params,
        "spoken_response": text,
        "confidence": parsed.get("confidence", 0.5),
    }
