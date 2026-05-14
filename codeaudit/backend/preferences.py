"""
Preferences System - stores and learns from user rejections.
Prevents re-suggesting rejected patterns.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.models import RejectionMemory


def _get_prefs_dir() -> Path:
    """Get the preferences directory."""
    root = Path(__file__).parent.parent
    prefs_dir = root / "preferences"
    prefs_dir.mkdir(exist_ok=True)
    return prefs_dir


def _get_prefs_file() -> Path:
    """Get the preferences file path."""
    return _get_prefs_dir() / "user_preferences.json"


def _get_rejection_file(project_name: str) -> Path:
    """Get project-specific rejection file."""
    safe_name = "".join(c for c in project_name if c.isalnum() or c in ('-', '_')).rstrip()
    return _get_prefs_dir() / f"rejections_{safe_name}.json"


class PreferencesStore:
    """Store and retrieve user preferences and rejection memory."""
    
    def __init__(self):
        self.prefs_file = _get_prefs_file()
        self._cache: Optional[Dict] = None
    
    def _load(self) -> Dict:
        """Load preferences from disk."""
        if self._cache is not None:
            return self._cache
        
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file) as f:
                    self._cache = json.load(f)
                    return self._cache
            except Exception:
                pass
        
        self._cache = {
            "rejection_patterns": [],
            "approved_patterns": [],
            "tweak_history": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        return self._cache
    
    def _save(self, data: Dict) -> None:
        """Save preferences to disk."""
        data["updated_at"] = datetime.utcnow().isoformat()
        self._cache = data
        with open(self.prefs_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_rejection_pattern(self, finding_title: str, finding_type: str, 
                              reason: str, location: Dict[str, Any]) -> None:
        """Add a rejection pattern to global memory."""
        data = self._load()
        
        pattern = {
            "finding_title": finding_title,
            "finding_type": finding_type,
            "reason": reason,
            "location": location,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        data["rejection_patterns"].append(pattern)
        
        # Keep only last 100 patterns
        if len(data["rejection_patterns"]) > 100:
            data["rejection_patterns"] = data["rejection_patterns"][-100:]
        
        self._save(data)
    
    def is_rejected_pattern(self, finding_title: str, finding_type: str) -> bool:
        """Check if a similar pattern was previously rejected."""
        data = self._load()
        
        for pattern in data["rejection_patterns"]:
            # Simple similarity check
            if (pattern["finding_type"] == finding_type and 
                self._title_similarity(pattern["finding_title"], finding_title) > 0.7):
                return True
        
        return False
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate simple similarity between two titles."""
        # Normalize
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        if t1 == t2:
            return 1.0
        
        # Check for substring match
        if t1 in t2 or t2 in t1:
            return 0.8
        
        # Word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def get_common_rejection_reasons(self, finding_type: Optional[str] = None) -> List[Dict]:
        """Get common rejection reasons, optionally filtered by type."""
        data = self._load()
        patterns = data["rejection_patterns"]
        
        if finding_type:
            patterns = [p for p in patterns if p["finding_type"] == finding_type]
        
        # Group by reason
        from collections import Counter
        reasons = Counter(p["reason"] for p in patterns if p["reason"])
        
        return [
            {"reason": reason, "count": count}
            for reason, count in reasons.most_common(5)
        ]
    
    def add_tweak_history(self, finding_title: str, original: str, 
                          tweak_instruction: str, result: str) -> None:
        """Record a tweak request and its result for learning."""
        data = self._load()
        
        tweak = {
            "finding_title": finding_title,
            "original": original,
            "tweak_instruction": tweak_instruction,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        data["tweak_history"].append(tweak)
        
        # Keep only last 50 tweaks
        if len(data["tweak_history"]) > 50:
            data["tweak_history"] = data["tweak_history"][-50:]
        
        self._save(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get preference statistics."""
        data = self._load()
        
        return {
            "total_rejections": len(data["rejection_patterns"]),
            "total_tweaks": len(data["tweak_history"]),
            "common_rejection_reasons": self.get_common_rejection_reasons(),
        }


class ProjectRejectionStore:
    """Project-specific rejection memory."""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.rejection_file = _get_rejection_file(project_name)
        self._cache: Optional[List] = None
    
    def _load(self) -> List[Dict]:
        """Load project rejections."""
        if self._cache is not None:
            return self._cache
        
        if self.rejection_file.exists():
            try:
                with open(self.rejection_file) as f:
                    self._cache = json.load(f)
                    return self._cache
            except Exception:
                pass
        
        self._cache = []
        return self._cache
    
    def _save(self, data: List[Dict]) -> None:
        """Save project rejections."""
        self._cache = data
        with open(self.rejection_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_rejection(self, finding: Dict[str, Any], reason: str) -> None:
        """Add a rejection for this project."""
        data = self._load()
        
        rejection = {
            "finding_id": finding.get("id"),
            "finding_title": finding.get("title"),
            "finding_type": finding.get("type"),
            "location": finding.get("location", {}),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        data.append(rejection)
        self._save(data)
    
    def was_rejected(self, finding_title: str, location: Dict[str, Any]) -> bool:
        """Check if this finding was previously rejected in this project."""
        data = self._load()
        
        for rejection in data:
            # Check title similarity
            if rejection["finding_title"] == finding_title:
                # Check if same file
                if rejection.get("location", {}).get("file") == location.get("file"):
                    return True
        
        return False
    
    def get_rejections(self) -> List[Dict]:
        """Get all rejections for this project."""
        return self._load()


# Singleton
_prefs_store: Optional[PreferencesStore] = None


def get_prefs_store() -> PreferencesStore:
    """Get global preferences store."""
    global _prefs_store
    if _prefs_store is None:
        _prefs_store = PreferencesStore()
    return _prefs_store


def get_project_rejection_store(project_name: str) -> ProjectRejectionStore:
    """Get project-specific rejection store."""
    return ProjectRejectionStore(project_name)
