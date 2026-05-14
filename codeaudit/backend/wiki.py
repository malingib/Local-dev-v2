"""
Wiki - markdown knowledge base with SQLite FTS5 full-text search.
Inspired by Hermes Desktop's wiki system.
"""
import json
import os
import sqlite3
import threading
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


def _get_wiki_dir() -> Path:
    env_dir = os.environ.get("CODEAUDIT_WIKI_DIR")
    if env_dir:
        d = Path(env_dir)
    else:
        d = Path.home() / ".codeaudit" / "wiki"
    d.mkdir(parents=True, exist_ok=True)
    return d


class WikiPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    content: str = ""
    tags: List[str] = Field(default_factory=list)
    category: str = "general"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


_DB_NAME = "wiki.db"
_PAGES_DIR = "pages"
_FTS_TABLE = "wiki_fts"


class WikiManager:
    """Wiki knowledge base with FTS5 search."""

    def __init__(self, wiki_dir: Optional[Path] = None):
        self.wiki_dir = wiki_dir or _get_wiki_dir()
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self._pages_dir = self.wiki_dir / _PAGES_DIR
        self._pages_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self.wiki_dir / _DB_NAME
        self._lock = threading.Lock()
        self._has_fts = False
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS wiki_pages (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        tags TEXT DEFAULT '[]',
                        category TEXT DEFAULT 'general',
                        file_path TEXT NOT NULL,
                        fts_rowid INTEGER DEFAULT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                try:
                    conn.execute(f"""
                        CREATE VIRTUAL TABLE IF NOT EXISTS {_FTS_TABLE}
                        USING fts5(title, tags, content, tokenize='porter unicode61')
                    """)
                    self._has_fts = True
                except sqlite3.OperationalError:
                    self._has_fts = False
                conn.commit()
            finally:
                conn.close()

    def _page_file_path(self, page_id: str) -> Path:
        return self._pages_dir / f"{page_id}.md"

    def _write_file_crash_safe(self, path: Path, content: str) -> None:
        fd, tmp_path = tempfile.mkstemp(dir=str(self._pages_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    # ── CRUD ──────────────────────────────────────────────────────────────

    def create_page(self, page: WikiPage) -> Dict[str, Any]:
        page.id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()
        page.created_at = now
        page.updated_at = now

        file_path = self._page_file_path(page.id)
        self._write_file_crash_safe(file_path, page.content)

        with self._lock:
            conn = self._get_conn()
            try:
                tags_str = json.dumps(page.tags)
                tags_fts = " ".join(page.tags)

                conn.execute(
                    """INSERT INTO wiki_pages (id, title, tags, category, file_path, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (page.id, page.title, tags_str, page.category,
                     str(file_path), page.created_at.isoformat(), page.updated_at.isoformat()),
                )

                if self._has_fts:
                    conn.execute(
                        f"INSERT INTO {_FTS_TABLE} (title, tags, content) VALUES (?, ?, ?)",
                        (page.title, tags_fts, page.content),
                    )
                    fts_rowid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    conn.execute(
                        "UPDATE wiki_pages SET fts_rowid = ? WHERE id = ?",
                        (fts_rowid, page.id),
                    )
                conn.commit()
            finally:
                conn.close()

        return page.model_dump(mode="json")

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
                ).fetchone()
                if not row:
                    return None
                page = self._row_to_page(row)
                return page.model_dump(mode="json")
            finally:
                conn.close()

    def update_page(self, page_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
                ).fetchone()
                if not row:
                    return None

                current = self._row_to_page(row)

                if "title" in updates:
                    current.title = updates["title"]
                if "content" in updates:
                    current.content = updates["content"]
                    self._write_file_crash_safe(self._page_file_path(page_id), current.content)
                if "tags" in updates:
                    current.tags = updates["tags"]
                if "category" in updates:
                    current.category = updates["category"]

                current.updated_at = datetime.utcnow()
                tags_json = json.dumps(current.tags)
                tags_fts = " ".join(current.tags)

                conn.execute(
                    """UPDATE wiki_pages SET title=?, tags=?, category=?, updated_at=?
                       WHERE id=?""",
                    (current.title, tags_json, current.category,
                     current.updated_at.isoformat(), page_id),
                )

                if self._has_fts and row["fts_rowid"]:
                    conn.execute(
                        f"UPDATE {_FTS_TABLE} SET title=?, tags=?, content=? WHERE rowid=?",
                        (current.title, tags_fts, current.content, row["fts_rowid"]),
                    )
                conn.commit()

                return current.model_dump(mode="json")
            finally:
                conn.close()

    def delete_page(self, page_id: str) -> bool:
        file_path = self._page_file_path(page_id)
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT fts_rowid FROM wiki_pages WHERE id = ?", (page_id,)
                ).fetchone()
                if not row:
                    return False

                if self._has_fts and row["fts_rowid"]:
                    conn.execute(
                        f"DELETE FROM {_FTS_TABLE} WHERE rowid = ?",
                        (row["fts_rowid"],),
                    )
                conn.execute("DELETE FROM wiki_pages WHERE id = ?", (page_id,))
                conn.commit()
            finally:
                conn.close()

        if file_path.exists():
            file_path.unlink()
        return True

    def list_pages(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                query = "SELECT * FROM wiki_pages"
                params: list = []
                conditions = []
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                if tag:
                    conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                query += " ORDER BY updated_at DESC"

                rows = conn.execute(query, params).fetchall()
                result = []
                for row in rows:
                    page = self._row_to_page(row)
                    d = page.model_dump(mode="json")
                    d.pop("content", None)
                    result.append(d)
                return result
            finally:
                conn.close()

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                if self._has_fts:
                    return self._search_fts(conn, query)
                else:
                    return self._search_like(conn, query)
            finally:
                conn.close()

    def _search_fts(self, conn: sqlite3.Connection, query: str) -> List[Dict[str, Any]]:
        words = [w for w in query.split() if w.strip()]
        if not words:
            return []

        # Build an FTS5 MATCH query: terms joined by AND for precision
        safe_query = " AND ".join(w for w in words)
        try:
            rows = conn.execute(
                f"""SELECT p.*, f.rank as score
                    FROM {_FTS_TABLE} f
                    JOIN wiki_pages p ON p.fts_rowid = f.rowid
                    WHERE {_FTS_TABLE} MATCH ?
                    ORDER BY rank""",
                (safe_query,),
            ).fetchall()
        except sqlite3.OperationalError:
            # Fallback: LIKE search if FTS query fails
            return self._search_like(conn, query)

        return [self._row_to_search_result(r) for r in rows]

    def _search_like(self, conn: sqlite3.Connection, query: str) -> List[Dict[str, Any]]:
        words = [w.strip() for w in query.split() if w.strip()]
        if not words:
            return []

        conditions = []
        params: list = []
        for word in words:
            like = f"%{word}%"
            conditions.append("(title LIKE ? OR tags LIKE ?)")
            params.extend([like, like])

        rows = conn.execute(
            "SELECT * FROM wiki_pages WHERE " + " AND ".join(conditions) + " ORDER BY updated_at DESC",
            params,
        ).fetchall()

        return [self._row_to_search_result(r) for r in rows]

    def _row_to_search_result(self, row: sqlite3.Row) -> Dict[str, Any]:
        tags_raw = row["tags"]
        if isinstance(tags_raw, str):
            try:
                tags = json.loads(tags_raw)
            except (json.JSONDecodeError, TypeError):
                tags = []
        else:
            tags = tags_raw or []

        return {
            "id": row["id"],
            "title": row["title"],
            "tags": tags,
            "category": row["category"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "score": float(row["score"]) if "score" in row.keys() else 0.0,
        }

    def get_page_count(self) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT COUNT(*) as cnt FROM wiki_pages").fetchone()
                return row["cnt"] if row else 0
            finally:
                conn.close()

    def list_categories(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT category, COUNT(*) as cnt FROM wiki_pages GROUP BY category ORDER BY cnt DESC"
                ).fetchall()
                return [{"name": r["category"], "count": r["cnt"]} for r in rows]
            finally:
                conn.close()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _row_to_page(self, row: sqlite3.Row) -> WikiPage:
        path = self._page_file_path(row["id"])
        content = path.read_text(encoding="utf-8") if path.exists() else ""

        tags_raw = row["tags"]
        if isinstance(tags_raw, str):
            try:
                tags = json.loads(tags_raw)
            except (json.JSONDecodeError, TypeError):
                tags = []
        else:
            tags = tags_raw or []

        return WikiPage(
            id=row["id"],
            title=row["title"],
            content=content,
            tags=tags,
            category=row["category"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


_wiki_manager: Optional[WikiManager] = None


def get_wiki_manager() -> WikiManager:
    global _wiki_manager
    if _wiki_manager is None:
        _wiki_manager = WikiManager()
    return _wiki_manager
