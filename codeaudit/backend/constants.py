"""
Shared constants for CodeAudit agents.
Centralizes file extension lists so adding a language requires one change.
"""

CODE_EXTENSIONS: list[str] = [
    "py", "js", "jsx", "ts", "tsx", "vue", "svelte",
    "go", "rs", "rb", "php", "java", "cs", "cpp", "c", "h", "kt",
]

FRONTEND_EXTENSIONS: list[str] = [
    "tsx", "jsx", "vue", "svelte", "html",
]

UI_EXTENSIONS: set[str] = {"html", "htm", "jsx", "tsx", "vue", "svelte", "css", "scss"}

PERFORMANCE_EXTENSIONS: set[str] = {"py", "js", "jsx", "ts", "tsx", "vue", "svelte", "sql"}

ALL_AUDIT_EXTENSIONS: list[str] = [
    "py", "js", "jsx", "ts", "tsx", "vue", "svelte", "html", "css",
    "go", "rs", "rb", "kt",
]

IGNORE_DIRS: set[str] = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", ".eggs", "*.egg-info",
}
