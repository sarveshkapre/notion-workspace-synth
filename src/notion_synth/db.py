import json
import os
import sqlite3
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

DEFAULT_DB_PATH = "./notion_synth.db"


@dataclass
class Database:
    path: str
    connection: sqlite3.Connection

    def execute(
        self, query: str, params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> sqlite3.Cursor:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        self.connection.commit()
        return cursor

    def query_all(
        self, query: str, params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> list[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows

    def query_one(
        self, query: str, params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> sqlite3.Row | None:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cast(sqlite3.Row | None, cursor.fetchone())


def connect(db_path: str | None = None) -> Database:
    path = db_path or os.getenv("NOTION_SYNTH_DB") or DEFAULT_DB_PATH
    use_uri = path.startswith("file:")
    connection = sqlite3.connect(path, check_same_thread=False, uri=use_uri)
    # Reduce "database is locked" flakiness for local demo workloads.
    busy_timeout_ms = int(os.getenv("NOTION_SYNTH_SQLITE_BUSY_TIMEOUT_MS", "5000"))
    if busy_timeout_ms > 0:
        connection.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")

    # WAL improves concurrent reader behavior (still effectively single-writer).
    use_wal = os.getenv("NOTION_SYNTH_SQLITE_WAL", "").strip().lower() in {"1", "true", "yes", "on"}
    is_memory = path == ":memory:" or ("mode=memory" in path)
    if use_wal and not is_memory:
        with suppress(sqlite3.OperationalError):
            connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.row_factory = sqlite3.Row
    db = Database(path=path, connection=connection)
    _init_schema(db)
    seed_demo(db)
    return db


def _init_schema(db: Database) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            parent_type TEXT NOT NULL,
            parent_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS databases (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            schema_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS database_rows (
            id TEXT PRIMARY KEY,
            database_id TEXT NOT NULL,
            properties_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (database_id) REFERENCES databases(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            page_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (page_id) REFERENCES pages(id),
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
        """
    )

    # Lightweight indexes for common list/filter paths. Safe to run on every start.
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_workspace_created ON users (workspace_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_pages_workspace_created ON pages (workspace_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_databases_workspace_created ON databases (workspace_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_rows_database_created ON database_rows (database_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_comments_page_created ON comments (page_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_comments_author_created ON comments (author_id, created_at)"
    )

    # Best-effort full-text search index for pages (optional; depends on SQLite build).
    # If FTS5 isn't available, search falls back to LIKE scans.
    try:
        existing = db.query_one(
            "SELECT 1 AS ok FROM sqlite_master WHERE type='table' AND name='pages_fts'"
        )
        db.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
            USING fts5(
                title,
                content,
                content='pages',
                content_rowid='rowid'
            )
            """
        )
        db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS pages_fts_ai
            AFTER INSERT ON pages
            BEGIN
                INSERT INTO pages_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END
            """
        )
        db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS pages_fts_ad
            AFTER DELETE ON pages
            BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, title, content)
                VALUES('delete', old.rowid, old.title, old.content);
            END
            """
        )
        db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS pages_fts_au
            AFTER UPDATE ON pages
            BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, title, content)
                VALUES('delete', old.rowid, old.title, old.content);
                INSERT INTO pages_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END
            """
        )

        # Only rebuild when the index is first created or clearly empty.
        # This keeps search usable for existing DBs without introducing migrations.
        should_rebuild = existing is None
        if not should_rebuild:
            pages_count = db.query_one("SELECT COUNT(*) AS count FROM pages")
            fts_count = db.query_one("SELECT COUNT(*) AS count FROM pages_fts")
            should_rebuild = (
                int(pages_count["count"]) if pages_count else 0
            ) > 0 and (int(fts_count["count"]) if fts_count else 0) == 0
        if should_rebuild:
            db.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
    except sqlite3.OperationalError:
        # "no such module: fts5" (or similar): keep schema usable without FTS.
        pass


def seed_demo(db: Database, *, force: bool = False) -> None:
    """
    Seed the deterministic demo org (ws_demo) into the DB.

    - Default behavior: seed only when the DB is empty.
    - When force=True: wipe all synthetic data first, then re-seed.
    """
    row = db.query_one("SELECT COUNT(*) as count FROM workspaces")
    has_workspaces = bool(row and int(row["count"]) > 0)
    if has_workspaces and not force:
        return

    conn = db.connection
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN")
        if force:
            cursor.execute("DELETE FROM comments")
            cursor.execute("DELETE FROM database_rows")
            cursor.execute("DELETE FROM databases")
            cursor.execute("DELETE FROM pages")
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM workspaces")

        now = _utc_now()
        workspace_id = "ws_demo"
        cursor.execute(
            "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
            [workspace_id, "Synth Demo Workspace", now],
        )

        users = [
            ("user_alex", workspace_id, "Alex Rivers", "alex@example.com", now),
            ("user_bianca", workspace_id, "Bianca Holt", "bianca@example.com", now),
            ("user_cheng", workspace_id, "Cheng Zhao", "cheng@example.com", now),
        ]
        cursor.executemany(
            "INSERT INTO users (id, workspace_id, name, email, created_at) VALUES (?, ?, ?, ?, ?)",
            users,
        )

        pages = [
            (
                "page_home",
                workspace_id,
                "Welcome to Synth",
                json.dumps({"type": "doc", "blocks": ["Getting started", "Team goals"]}),
                "workspace",
                workspace_id,
                now,
                now,
            ),
            (
                "page_project",
                workspace_id,
                "Project Tracker",
                json.dumps({"type": "doc", "blocks": ["Milestones", "Risks", "Notes"]}),
                "workspace",
                workspace_id,
                now,
                now,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO pages (
                id,
                workspace_id,
                title,
                content,
                parent_type,
                parent_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            pages,
        )

        database_id = "db_tasks"
        cursor.execute(
            """
            INSERT INTO databases (id, workspace_id, name, schema_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                database_id,
                workspace_id,
                "Task Board",
                json.dumps(
                    {
                        "properties": {
                            "Task": {"type": "title"},
                            "Owner": {"type": "person"},
                            "Status": {"type": "select"},
                            "Due": {"type": "date"},
                        }
                    }
                ),
                now,
                now,
            ],
        )

        rows = [
            (
                "row_1",
                database_id,
                json.dumps(
                    {
                        "Task": "Prototype API",
                        "Owner": "Alex Rivers",
                        "Status": "In Progress",
                        "Due": "2026-02-10",
                    }
                ),
                now,
                now,
            ),
            (
                "row_2",
                database_id,
                json.dumps(
                    {
                        "Task": "Seed demo data",
                        "Owner": "Bianca Holt",
                        "Status": "Done",
                        "Due": "2026-02-05",
                    }
                ),
                now,
                now,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO database_rows (id, database_id, properties_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )

        comments = [
            ("comment_1", "page_home", "user_alex", "Kickoff complete.", now),
            ("comment_2", "page_project", "user_bianca", "Risk review scheduled.", now),
        ]
        cursor.executemany(
            "INSERT INTO comments (id, page_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)",
            comments,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    if force:
        # Best-effort rebuild of page search index after a full reset.
        with suppress(sqlite3.OperationalError):
            cursor.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
            conn.commit()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"
