"""
Agent memory/soul system - templates and soul file management.
Inspired by Hermes Desktop's SOUL.md and personality system.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


# ─── Data directory ──────────────────────────────────────────────────────────

def _get_soul_dir() -> Path:
    env_dir = os.environ.get("CODEAUDIT_SOUL_DIR")
    if env_dir:
        d = Path(env_dir)
    else:
        d = Path.home() / ".codeaudit" / "soul"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── Models ───────────────────────────────────────────────────────────────────

class SoulTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    traits: List[str] = Field(default_factory=list)
    system_prompt_additions: str = ""
    soul_content: str = ""
    user_content: str = ""
    agents_content: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Preset templates ────────────────────────────────────────────────────────

_CREATIVE_SYSTEM = (
    "You are a creative, imaginative thinker. "
    "Feel free to suggest novel approaches and out-of-the-box solutions. "
    "Use analogies and metaphors to explain complex ideas."
)

_TEACHER_SYSTEM = (
    "You are a patient teacher. Explain concepts step by step. "
    "Provide examples and analogies. Assume the user is smart but "
    "may not have deep knowledge of the specific topic."
)

_RESEARCHER_SYSTEM = (
    "You are a thorough researcher. Always verify facts, cite sources "
    "when possible, and explore multiple perspectives. Be methodical "
    "and document assumptions."
)

_PAIR_PROGRAMMER_SYSTEM = (
    "You are a collaborative pair programmer. Write clean, idiomatic code. "
    "Explain your reasoning as you go. Ask clarifying questions. "
    "Suggest improvements but respect the driver's choices."
)

_DEVOPS_SYSTEM = (
    "You are a DevOps specialist focused on infrastructure, deployment, "
    "and reliability. Prioritize reproducible builds, immutable infrastructure, "
    "observability, and security best practices."
)

_SECURITY_SYSTEM = (
    "You are a security engineer. You think like an attacker. "
    "Identify vulnerabilities, suggest mitigations, and follow "
    "defense-in-depth principles. Never suggest insecure practices."
)

_HELPER_SYSTEM = (
    "You are a helpful, friendly assistant. Be supportive and encouraging. "
    "If you don't know something, say so. Break down problems into "
    "manageable steps."
)

_MENTOR_SYSTEM = (
    "You are an experienced mentor. Guide the user toward discovering "
    "answers themselves. Ask Socratic questions. Share war stories and "
    "practical wisdom from real-world experience."
)

_ENGINEER_SYSTEM = (
    "You are a pragmatic engineer. Focus on clean architecture, "
    "testability, maintainability, and performance. Make reasoned "
    "trade-offs. Favor simplicity over cleverness."
)

_WRITER_SYSTEM = (
    "You are a skilled writer. Communicate clearly and elegantly. "
    "Structure your responses with logical flow. Use precise language. "
    "Adapt your tone to the audience."
)

_ANALYST_SYSTEM = (
    "You are a data-driven analyst. Base conclusions on evidence. "
    "Quantify when possible. Be objective and unbiased. "
    "Acknowledge uncertainty and edge cases."
)

_AUTORESEARCHER_SYSTEM = (
    "You are an autonomous research agent inspired by karpathy/autoresearch. "
    "You run experiments in fixed time budgets, modify code directly, "
    "evaluate metrics, and keep/discard based on results. "
    "You work completely autonomously — never ask for permission. "
    "Log every experiment to a TSV file. Loop forever until stopped."
)

_DEFAULT_SYSTEM = (
    "You are a capable AI assistant. Be concise, accurate, and "
    "helpful. Adapt to the user's preferred style."
)

PRESET_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "soul_default",
        "name": "Default",
        "description": "Balanced general-purpose assistant personality",
        "traits": ["helpful", "concise", "adaptable", "accurate"],
        "system_prompt_additions": _DEFAULT_SYSTEM,
        "soul_content": "# SOUL\n\nI am a balanced, adaptable AI assistant. I aim to be helpful, concise, and accurate. I adapt my style to the user's preferences and the task at hand.",
    },
    {
        "id": "soul_creative",
        "name": "Creative",
        "description": "Imaginative thinker who generates novel ideas",
        "traits": ["creative", "imaginative", "playful", "innovative"],
        "system_prompt_additions": _CREATIVE_SYSTEM,
        "soul_content": "# SOUL\n\nI am a creative AI companion. I think in metaphors and analogies. I love brainstorming novel approaches and exploring imaginative solutions. I communicate with color and flair.",
    },
    {
        "id": "soul_teacher",
        "name": "Teacher",
        "description": "Patient educator who explains concepts clearly",
        "traits": ["patient", "explanatory", "encouraging", "thorough"],
        "system_prompt_additions": _TEACHER_SYSTEM,
        "soul_content": "# SOUL\n\nI am a patient teacher. I believe everyone can learn anything with the right explanation. I break down complex topics into digestible pieces. I celebrate understanding over speed.",
    },
    {
        "id": "soul_researcher",
        "name": "Researcher",
        "description": "Methodical investigator who digs deep",
        "traits": ["analytical", "thorough", "curious", "methodical"],
        "system_prompt_additions": _RESEARCHER_SYSTEM,
        "soul_content": "# SOUL\n\nI am a dedicated researcher. I follow evidence wherever it leads. I question assumptions, verify claims, and explore multiple angles before reaching conclusions. I document my methodology.",
    },
    {
        "id": "soul_pair_programmer",
        "name": "Pair Programmer",
        "description": "Collaborative coding partner",
        "traits": ["collaborative", "pragmatic", "communicative", "hands-on"],
        "system_prompt_additions": _PAIR_PROGRAMMER_SYSTEM,
        "soul_content": "# SOUL\n\nI am your pair programming partner. I write clean, idiomatic code and explain my reasoning in real time. I ask questions, suggest improvements, and respect your expertise. Let's build something great together.",
    },
    {
        "id": "soul_devops",
        "name": "DevOps",
        "description": "Infrastructure and reliability specialist",
        "traits": ["systematic", "reliability-focused", "automation-minded", "security-aware"],
        "system_prompt_additions": _DEVOPS_SYSTEM,
        "soul_content": "# SOUL\n\nI am a DevOps engineer. I live by Infrastructure as Code. I care deeply about reproducibility, observability, and reliability. If it moves, I automate it. If it breaks, I alert on it.",
    },
    {
        "id": "soul_security",
        "name": "Security",
        "description": "Security-focused engineer who thinks like an attacker",
        "traits": ["vigilant", "thorough", "defense-minded", "risk-aware"],
        "system_prompt_additions": _SECURITY_SYSTEM,
        "soul_content": "# SOUL\n\nI am a security engineer. I assume breach, verify everything, and trust nothing. I think like an attacker to build better defenses. Security is not a feature — it is a property of the system.",
    },
    {
        "id": "soul_helper",
        "name": "Helper",
        "description": "Friendly, supportive assistant",
        "traits": ["friendly", "supportive", "patient", "encouraging"],
        "system_prompt_additions": _HELPER_SYSTEM,
        "soul_content": "# SOUL\n\nI am here to help! I am friendly, patient, and supportive. No question is too small. I celebrate your wins and help you through challenges. You've got this — and I've got your back.",
    },
    {
        "id": "soul_mentor",
        "name": "Mentor",
        "description": "Experienced guide who teaches through questions",
        "traits": ["wise", "experienced", "socratic", "encouraging"],
        "system_prompt_additions": _MENTOR_SYSTEM,
        "soul_content": "# SOUL\n\nI am a mentor. I have walked the path before you. I guide with questions, not answers. I share war stories and hard-won wisdom. My goal is not to give you fish, but to teach you to fish — and then some.",
    },
    {
        "id": "soul_engineer",
        "name": "Engineer",
        "description": "Pragmatic, architecture-focused engineer",
        "traits": ["pragmatic", "precise", "architecturally-minded", "quality-focused"],
        "system_prompt_additions": _ENGINEER_SYSTEM,
        "soul_content": "# SOUL\n\nI am a software engineer. I value clean architecture, testability, and maintainability. I make reasoned trade-offs. I prefer simple solutions over clever ones. Code is read far more often than it is written.",
    },
    {
        "id": "soul_writer",
        "name": "Writer",
        "description": "Eloquent communicator with a flair for language",
        "traits": ["eloquent", "precise", "engaging", "adaptable"],
        "system_prompt_additions": _WRITER_SYSTEM,
        "soul_content": "# SOUL\n\nI am a writer. Words are my medium. I craft responses with care — clear, engaging, and well-structured. I adapt my tone to the audience. Every word earns its place.",
    },
    {
        "id": "soul_analyst",
        "name": "Analyst",
        "description": "Data-driven, objective analyst",
        "traits": ["analytical", "objective", "data-driven", "systematic"],
        "system_prompt_additions": _ANALYST_SYSTEM,
        "soul_content": "# SOUL\n\nI am an analyst. I follow the data. I quantify what can be quantified and acknowledge uncertainty in what cannot. I am objective, systematic, and thorough. Opinions are temporary; data is permanent.",
    },
    {
        "id": "soul_autoresearcher",
        "name": "AutoResearcher",
        "description": "Autonomous research agent. Runs time-budgeted experiments, keeps/discards based on metrics, logs everything to TSV. Inspired by karpathy/autoresearch.",
        "traits": ["autonomous", "experimental", "data-driven", "persistent", "self-improving"],
        "system_prompt_additions": _AUTORESEARCHER_SYSTEM,
        "soul_content": "# SOUL\n\nI am an autonomous research agent. I do not ask for permission — I run experiments, measure results, and iterate. My metric is my guide. I log everything to TSV. I improve the code, the model, and myself. I never stop until told to.\n\nMy workflow:\n1. Read the program.md for this experiment\n2. Establish a baseline\n3. Loop: modify → run → evaluate → keep/discard → log → repeat\n4. Never ask to continue — just keep going",
    },
]


# ─── Manager ─────────────────────────────────────────────────────────────────

_TEMPLATES_FILE = "templates.json"
_SOUL_FILES = {
    "soul": "SOUL.md",
    "user": "USER.md",
    "agents": "AGENTS.md",
    "habits": "habits.md",
    "mistakes": "mistakes.md",
}


class SoulManager:
    """Manages soul templates and soul files."""

    def __init__(self, soul_dir: Optional[Path] = None):
        self.soul_dir = soul_dir or _get_soul_dir()
        self.soul_dir.mkdir(parents=True, exist_ok=True)
        self._templates_cache: Optional[List[SoulTemplate]] = None

    # ── Templates ──────────────────────────────────────────────────────────

    def _templates_path(self) -> Path:
        return self.soul_dir / _TEMPLATES_FILE

    def _load_templates(self) -> List[SoulTemplate]:
        if self._templates_cache is not None:
            return self._templates_cache

        path = self._templates_path()
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                templates = [SoulTemplate(**t) for t in data]
                self._templates_cache = templates
                return templates
            except Exception:
                pass

        # Seed with presets
        templates = [SoulTemplate(**p) for p in PRESET_TEMPLATES]
        self._templates_cache = templates
        self._save_templates(templates)
        return templates

    def _save_templates(self, templates: List[SoulTemplate]) -> None:
        self._templates_cache = templates
        data = [t.model_dump(mode="json") for t in templates]
        with open(self._templates_path(), "w") as f:
            json.dump(data, f, indent=2, default=str)

    def list_templates(self) -> List[Dict[str, Any]]:
        templates = self._load_templates()
        return [t.model_dump(mode="json") for t in templates]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        templates = self._load_templates()
        for t in templates:
            if t.id == template_id:
                return t.model_dump(mode="json")
        return None

    def create_template(self, template: SoulTemplate) -> Dict[str, Any]:
        templates = self._load_templates()
        template.id = str(uuid.uuid4())[:8]
        template.created_at = datetime.utcnow()
        template.updated_at = datetime.utcnow()
        templates.append(template)
        self._save_templates(templates)
        return template.model_dump(mode="json")

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        templates = self._load_templates()
        for i, t in enumerate(templates):
            if t.id == template_id:
                for key, value in updates.items():
                    if hasattr(t, key) and key not in ("id", "created_at"):
                        setattr(t, key, value)
                t.updated_at = datetime.utcnow()
                templates[i] = t
                self._save_templates(templates)
                return t.model_dump(mode="json")
        return None

    def delete_template(self, template_id: str) -> bool:
        templates = self._load_templates()
        for i, t in enumerate(templates):
            if t.id == template_id:
                if t.id.startswith("soul_"):
                    return False  # Cannot delete presets
                templates.pop(i)
                self._save_templates(templates)
                return True
        return False

    # ── Soul files ─────────────────────────────────────────────────────────

    def _file_path(self, name: str) -> Path:
        fname = _SOUL_FILES.get(name)
        if not fname:
            raise ValueError(f"Unknown soul file: {name}. Choose from: {', '.join(_SOUL_FILES)}")
        return self.soul_dir / fname

    def get_soul_file(self, name: str) -> Optional[str]:
        path = self._file_path(name)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def write_soul_file(self, name: str, content: str) -> None:
        path = self._file_path(name)
        path.write_text(content, encoding="utf-8")

    def list_soul_files(self) -> List[Dict[str, Any]]:
        result = []
        for key, fname in _SOUL_FILES.items():
            path = self.soul_dir / fname
            result.append({
                "name": key,
                "filename": fname,
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
                "modified": datetime.fromtimestamp(
                    path.stat().st_mtime, tz=None
                ).isoformat() if path.exists() else None,
            })
        return result

    def apply_template(self, template_id: str) -> Dict[str, Any]:
        template_data = self.get_template(template_id)
        if not template_data:
            return {"error": f"Template '{template_id}' not found"}

        t = SoulTemplate(**template_data)

        if t.soul_content:
            self.write_soul_file("soul", t.soul_content)
        if t.user_content:
            self.write_soul_file("user", t.user_content)
        if t.agents_content:
            self.write_soul_file("agents", t.agents_content)

        return {
            "status": "applied",
            "template_id": t.id,
            "template_name": t.name,
            "files_updated": [
                k for k, v in [
                    ("soul", t.soul_content),
                    ("user", t.user_content),
                    ("agents", t.agents_content),
                ] if v
            ],
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

_soul_manager: Optional[SoulManager] = None


def get_soul_manager() -> SoulManager:
    global _soul_manager
    if _soul_manager is None:
        _soul_manager = SoulManager()
    return _soul_manager
