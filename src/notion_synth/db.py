import json
import os
import sqlite3
from collections.abc import Mapping, Sequence
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
    connection.execute("PRAGMA foreign_keys=ON")
    connection.row_factory = sqlite3.Row
    db = Database(path=path, connection=connection)
    _init_schema(db)
    _seed_if_empty(db)
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


def _seed_if_empty(db: Database) -> None:
    row = db.query_one("SELECT COUNT(*) as count FROM workspaces")
    if row and row["count"] > 0:
        return

    now = _utc_now()
    workspace_id = "ws_demo"
    db.execute(
        "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
        [workspace_id, "Synth Demo Workspace", now],
    )

    users = [
        ("user_alex", workspace_id, "Alex Rivers", "alex@example.com", now),
        ("user_bianca", workspace_id, "Bianca Holt", "bianca@example.com", now),
        ("user_cheng", workspace_id, "Cheng Zhao", "cheng@example.com", now),
    ]
    db.connection.executemany(
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
    db.connection.executemany(
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
    db.execute(
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
    db.connection.executemany(
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
    db.connection.executemany(
        "INSERT INTO comments (id, page_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)",
        comments,
    )
    db.connection.commit()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"
