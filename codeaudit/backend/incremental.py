"""
Incremental analysis — tracks file hashes across sessions to skip unchanged files.
Saves API calls by only re-analyzing files that actually changed.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime

# Store file hashes in sessions directory
_hash_dir: Optional[Path] = None


def _get_hash_dir(project_path: str) -> Path:
    """Get the hash cache directory for a project."""
    global _hash_dir
    if _hash_dir is None:
        root = Path(__file__).parent.parent
        _hash_dir = root / ".file_hashes"
        _hash_dir.mkdir(exist_ok=True)
    project_name = Path(project_path).name
    return _hash_dir / project_name


def _file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()
    except (IOError, OSError):
        return ""


def load_previous_hashes(project_path: str) -> Dict[str, str]:
    """Load file hashes from the previous session."""
    hash_file = _get_hash_dir(project_path) / "previous.json"
    if hash_file.exists():
        try:
            with open(hash_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_current_hashes(project_path: str, hashes: Dict[str, str]):
    """Save current file hashes for the next session."""
    hash_file = _get_hash_dir(project_path) / "previous.json"
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    with open(hash_file, "w") as f:
        json.dump(hashes, f, indent=2)


def compute_all_file_hashes(project_path: str, extensions: list[str], ignore_dirs: set[str] | None = None) -> Dict[str, str]:
    """Compute hashes of all relevant files in a project."""
    path = Path(project_path)
    if ignore_dirs is None:
        ignore_dirs = {
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage', '.pytest_cache',
            '.mypy_cache', '.tox', '.eggs', '.cache',
        }

    hashes = {}
    for ext in extensions:
        for file_path in path.rglob(f"*.{ext}"):
            if any(part in ignore_dirs for part in file_path.parts):
                continue
            rel_path = str(file_path.relative_to(path))
            hashes[rel_path] = _file_hash(file_path)
    return hashes


def detect_changed_files(
    project_path: str,
    extensions: list[str],
    previous_hashes: Dict[str, str] | None = None
) -> Dict[str, list[str]]:
    """
    Compare current files against previous hashes.
    Returns dict with 'changed', 'new', 'deleted' file lists.
    """
    if previous_hashes is None:
        previous_hashes = load_previous_hashes(project_path)

    current_hashes = compute_all_file_hashes(project_path, extensions)

    changed = []
    new_files = []
    deleted = []

    # Check current files
    for rel_path, current_hash in current_hashes.items():
        if rel_path not in previous_hashes:
            new_files.append(rel_path)
        elif previous_hashes[rel_path] != current_hash:
            changed.append(rel_path)

    # Check for deleted files
    for rel_path in previous_hashes:
        if rel_path not in current_hashes:
            deleted.append(rel_path)

    return {
        "changed": changed,
        "new": new_files,
        "deleted": deleted,
        "unchanged": [f for f in previous_hashes if f in current_hashes and previous_hashes[f] == current_hashes[f]],
    }


def should_skip_file(rel_path: str, previous_hashes: Dict[str, str], current_hashes: Dict[str, str]) -> bool:
    """Check if a file can be skipped because it hasn't changed."""
    if rel_path in previous_hashes and rel_path in current_hashes:
        return previous_hashes[rel_path] == current_hashes[rel_path]
    return False


def get_incremental_stats(project_path: str, extensions: list[str]) -> Dict:
    """Get stats about what changed since last scan."""
    changes = detect_changed_files(project_path, extensions)
    total = len(changes["changed"]) + len(changes["new"]) + len(changes["unchanged"])
    return {
        "total_files": total,
        "changed_files": len(changes["changed"]),
        "new_files": len(changes["new"]),
        "deleted_files": len(changes["deleted"]),
        "unchanged_files": len(changes["unchanged"]),
        "scan_savings_percent": round(len(changes["unchanged"]) / max(total, 1) * 100, 1),
    }
