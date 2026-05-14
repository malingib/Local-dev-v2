"""
Buddy companion system - a lite version of Hermes Buddy.
Manage companion character profiles.
"""
import json
import os
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


# ─── Data directory ──────────────────────────────────────────────────────────

def _get_buddy_dir() -> Path:
    env_dir = os.environ.get("CODEAUDIT_BUDDY_DIR")
    if env_dir:
        d = Path(env_dir)
    else:
        d = Path.home() / ".codeaudit" / "buddy"
    d.mkdir(parents=True, exist_ok=True)
    return d


_BUDDY_FILE = "buddy.json"

# ─── Available options ────────────────────────────────────────────────────────

AVAILABLE_SPECIES = [
    "fox", "owl", "cat", "dog", "dragon", "robot", "spirit",
    "phoenix", "wolf", "rabbit", "bear", "squirrel",
]

AVAILABLE_PALETTES = [
    "ember", "ocean", "forest", "midnight", "dawn", "aurora",
    "coral", "shadow", "gold", "frost", "lava", "nebula",
]

AVAILABLE_EYE_SHAPES = [
    "round", "sharp", "gentle", "wide", "sleepy", "glowing",
    "asian", "large", "narrow", "compound",
]

AVAILABLE_ACCESSORIES = [
    "glasses", "scarf", "hat", "bowtie", "headphones", "crown",
    "monocle", "ribbon", "backpack", "none",
]

# ─── Models ───────────────────────────────────────────────────────────────────

class BuddyStats(BaseModel):
    friendliness: float = Field(default=50.0, ge=0, le=100)
    wisdom: float = Field(default=30.0, ge=0, le=100)
    energy: float = Field(default=70.0, ge=0, le=100)
    curiosity: float = Field(default=60.0, ge=0, le=100)


class BuddyPersonality(BaseModel):
    traits: List[str] = Field(default_factory=lambda: ["friendly", "helpful"])
    catchphrase: str = "Let's explore together!"


class Buddy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Buddy"
    species: str = "fox"
    palette: str = "ember"
    eye_shape: str = "round"
    accessories: str = "none"
    rarity: str = "common"  # common, uncommon, rare, legendary
    stats: BuddyStats = Field(default_factory=BuddyStats)
    personality: BuddyPersonality = Field(default_factory=BuddyPersonality)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Rarity table ────────────────────────────────────────────────────────────

_RARITY_TABLE = {
    "fox": "common", "owl": "common", "cat": "common", "dog": "common",
    "rabbit": "common", "squirrel": "common",
    "wolf": "uncommon", "bear": "uncommon",
    "dragon": "rare", "phoenix": "rare",
    "robot": "uncommon", "spirit": "legendary",
}


def _species_rarity(species: str) -> str:
    return _RARITY_TABLE.get(species, "common")


# ─── Manager ─────────────────────────────────────────────────────────────────

class BuddyManager:
    """Manage the buddy companion profile."""

    def __init__(self, buddy_dir: Optional[Path] = None):
        self.buddy_dir = buddy_dir or _get_buddy_dir()
        self.buddy_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[Buddy] = None

    def _file_path(self) -> Path:
        return self.buddy_dir / _BUDDY_FILE

    def _load(self) -> Buddy:
        if self._cache is not None:
            return self._cache

        path = self._file_path()
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                buddy = Buddy(**data)
                self._cache = buddy
                return buddy
            except Exception:
                pass

        buddy = Buddy()
        self._cache = buddy
        self._save(buddy)
        return buddy

    def _save(self, buddy: Buddy) -> None:
        self._cache = buddy
        data = buddy.model_dump(mode="json")
        with open(self._file_path(), "w") as f:
            json.dump(data, f, indent=2, default=str)

    def get_buddy(self) -> Dict[str, Any]:
        buddy = self._load()
        return buddy.model_dump(mode="json")

    def create_buddy(self, buddy: Buddy) -> Dict[str, Any]:
        buddy.id = str(uuid.uuid4())[:8]
        buddy.rarity = _species_rarity(buddy.species)
        now = datetime.utcnow()
        buddy.created_at = now
        buddy.updated_at = now
        self._save(buddy)
        return buddy.model_dump(mode="json")

    def update_buddy(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        buddy = self._load()
        for key, value in updates.items():
            if key == "stats" and isinstance(value, dict):
                for sk, sv in value.items():
                    if hasattr(buddy.stats, sk):
                        setattr(buddy.stats, sk, max(0, min(100, float(sv))))
            elif key == "personality" and isinstance(value, dict):
                for pk, pv in value.items():
                    if hasattr(buddy.personality, pk):
                        setattr(buddy.personality, pk, pv)
            elif hasattr(buddy, key) and key not in ("id", "created_at", "rarity"):
                setattr(buddy, key, value)
        buddy.updated_at = datetime.utcnow()
        buddy.rarity = _species_rarity(buddy.species)
        self._save(buddy)
        return buddy.model_dump(mode="json")

    def list_species(self) -> List[Dict[str, Any]]:
        return [
            {"name": s, "rarity": _species_rarity(s)}
            for s in AVAILABLE_SPECIES
        ]

    def list_palettes(self) -> List[str]:
        return list(AVAILABLE_PALETTES)

    def list_eye_shapes(self) -> List[str]:
        return list(AVAILABLE_EYE_SHAPES)

    def list_accessories(self) -> List[str]:
        return list(AVAILABLE_ACCESSORIES)


# ─── Singleton ────────────────────────────────────────────────────────────────

_buddy_manager: Optional[BuddyManager] = None


def get_buddy_manager() -> BuddyManager:
    global _buddy_manager
    if _buddy_manager is None:
        _buddy_manager = BuddyManager()
    return _buddy_manager
