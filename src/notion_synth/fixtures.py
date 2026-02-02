import json
from typing import Any, cast

from notion_synth.db import Database
from notion_synth.models import (
    Comment,
    Database as DatabaseModel,
    DatabaseRow,
    Fixture,
    FixtureImportResult,
    Page,
    User,
    Workspace,
)


def _parse_json(value: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(value))


def export_fixture(db: Database) -> Fixture:
    rows_workspaces = db.query_all("SELECT * FROM workspaces ORDER BY created_at")
    rows_users = db.query_all("SELECT * FROM users ORDER BY created_at")
    rows_pages = db.query_all("SELECT * FROM pages ORDER BY created_at")
    rows_databases = db.query_all("SELECT * FROM databases ORDER BY created_at")
    rows_database_rows = db.query_all("SELECT * FROM database_rows ORDER BY created_at")
    rows_comments = db.query_all("SELECT * FROM comments ORDER BY created_at")

    return Fixture(
        exported_at=_utc_now(),
        workspaces=[Workspace(**dict(row)) for row in rows_workspaces],
        users=[User(**dict(row)) for row in rows_users],
        pages=[
            Page(**{**dict(row), "content": _parse_json(row["content"])}) for row in rows_pages
        ],
        databases=[
            DatabaseModel(**{**dict(row), "schema": _parse_json(row["schema_json"])})
            for row in rows_databases
        ],
        database_rows=[
            DatabaseRow(**{**dict(row), "properties": _parse_json(row["properties_json"])})
            for row in rows_database_rows
        ],
        comments=[Comment(**dict(row)) for row in rows_comments],
    )


def import_fixture(db: Database, payload: Fixture, mode: str = "replace") -> FixtureImportResult:
    if payload.format_version != 1:
        raise ValueError("Unsupported fixture format_version")
    if mode not in {"replace", "merge"}:
        raise ValueError("Unsupported import mode")

    conn = db.connection
    cursor = conn.cursor()

    inserted: dict[str, int] = {}
    try:
        conn.execute("BEGIN")

        if mode == "replace":
            cursor.execute("DELETE FROM comments")
            cursor.execute("DELETE FROM database_rows")
            cursor.execute("DELETE FROM pages")
            cursor.execute("DELETE FROM databases")
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM workspaces")

        workspaces_query = (
            "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)"
            if mode == "replace"
            else """
            INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                created_at = excluded.created_at
            """
        )
        cursor.executemany(
            workspaces_query,
            [(w.id, w.name, w.created_at) for w in payload.workspaces],
        )
        inserted["workspaces"] = len(payload.workspaces)

        users_query = (
            "INSERT INTO users (id, workspace_id, name, email, created_at) VALUES (?, ?, ?, ?, ?)"
            if mode == "replace"
            else """
            INSERT INTO users (id, workspace_id, name, email, created_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                name = excluded.name,
                email = excluded.email,
                created_at = excluded.created_at
            """
        )
        cursor.executemany(
            users_query,
            [(u.id, u.workspace_id, u.name, u.email, u.created_at) for u in payload.users],
        )
        inserted["users"] = len(payload.users)

        pages_query = (
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
            """
            if mode == "replace"
            else """
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
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                title = excluded.title,
                content = excluded.content,
                parent_type = excluded.parent_type,
                parent_id = excluded.parent_id,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at
            """
        )
        cursor.executemany(
            pages_query,
            [
                (
                    p.id,
                    p.workspace_id,
                    p.title,
                    json.dumps(p.content),
                    p.parent_type,
                    p.parent_id,
                    p.created_at,
                    p.updated_at,
                )
                for p in payload.pages
            ],
        )
        inserted["pages"] = len(payload.pages)

        databases_query = (
            """
            INSERT INTO databases (id, workspace_id, name, schema_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            if mode == "replace"
            else """
            INSERT INTO databases (id, workspace_id, name, schema_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                name = excluded.name,
                schema_json = excluded.schema_json,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at
            """
        )
        cursor.executemany(
            databases_query,
            [
                (
                    d.id,
                    d.workspace_id,
                    d.name,
                    json.dumps(d.schema_),
                    d.created_at,
                    d.updated_at,
                )
                for d in payload.databases
            ],
        )
        inserted["databases"] = len(payload.databases)

        database_rows_query = (
            """
            INSERT INTO database_rows (id, database_id, properties_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """
            if mode == "replace"
            else """
            INSERT INTO database_rows (id, database_id, properties_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                database_id = excluded.database_id,
                properties_json = excluded.properties_json,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at
            """
        )
        cursor.executemany(
            database_rows_query,
            [
                (
                    r.id,
                    r.database_id,
                    json.dumps(r.properties),
                    r.created_at,
                    r.updated_at,
                )
                for r in payload.database_rows
            ],
        )
        inserted["database_rows"] = len(payload.database_rows)

        comments_query = (
            "INSERT INTO comments (id, page_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)"
            if mode == "replace"
            else """
            INSERT INTO comments (id, page_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                page_id = excluded.page_id,
                author_id = excluded.author_id,
                body = excluded.body,
                created_at = excluded.created_at
            """
        )
        cursor.executemany(
            comments_query,
            [(c.id, c.page_id, c.author_id, c.body, c.created_at) for c in payload.comments],
        )
        inserted["comments"] = len(payload.comments)

        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise ValueError("Fixture import failed") from exc

    return FixtureImportResult(status="ok", inserted=inserted)


def _utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()
