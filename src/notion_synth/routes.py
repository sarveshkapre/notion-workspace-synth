import json
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, Request

from notion_synth.db import Database, new_id
from notion_synth.models import (
    Comment,
    CommentCreate,
    DatabaseCreate,
    DatabaseRow,
    DatabaseRowCreate,
    Page,
    PageCreate,
    PageUpdate,
    User,
    Workspace,
)
from notion_synth.models import (
    Database as DatabaseModel,
)

router = APIRouter()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _get_db(request: Request) -> Database:
    return cast(Database, request.app.state.db)


def _limit_offset(limit: int, offset: int) -> tuple[int, int]:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return limit, offset


def _parse_json(value: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(value))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/workspaces", response_model=list[Workspace])
def list_workspaces(request: Request) -> list[Workspace]:
    db = _get_db(request)
    rows = db.query_all("SELECT * FROM workspaces ORDER BY created_at")
    return [Workspace(**dict(row)) for row in rows]


@router.get("/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(workspace_id: str, request: Request) -> Workspace:
    db = _get_db(request)
    row = db.query_one("SELECT * FROM workspaces WHERE id = ?", [workspace_id])
    if row is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return Workspace(**dict(row))


@router.get("/users", response_model=list[User])
def list_users(
    request: Request,
    workspace_id: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
) -> list[User]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    if workspace_id:
        rows = db.query_all(
            "SELECT * FROM users WHERE workspace_id = ? ORDER BY created_at LIMIT ? OFFSET ?",
            [workspace_id, limit, offset],
        )
    else:
        rows = db.query_all(
            "SELECT * FROM users ORDER BY created_at LIMIT ? OFFSET ?", [limit, offset]
        )
    return [User(**dict(row)) for row in rows]


@router.get("/pages", response_model=list[Page])
def list_pages(
    request: Request,
    workspace_id: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
) -> list[Page]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    if workspace_id:
        rows = db.query_all(
            "SELECT * FROM pages WHERE workspace_id = ? ORDER BY created_at LIMIT ? OFFSET ?",
            [workspace_id, limit, offset],
        )
    else:
        rows = db.query_all(
            "SELECT * FROM pages ORDER BY created_at LIMIT ? OFFSET ?", [limit, offset]
        )
    return [
        Page(**{**dict(row), "content": _parse_json(row["content"])})
        for row in rows
    ]


@router.get("/pages/{page_id}", response_model=Page)
def get_page(page_id: str, request: Request) -> Page:
    db = _get_db(request)
    row = db.query_one("SELECT * FROM pages WHERE id = ?", [page_id])
    if row is None:
        raise HTTPException(status_code=404, detail="Page not found")
    data = dict(row)
    data["content"] = _parse_json(row["content"])
    return Page(**data)


@router.post("/pages", response_model=Page, status_code=201)
def create_page(payload: PageCreate, request: Request) -> Page:
    db = _get_db(request)
    now = _utc_now()
    page_id = new_id("page")
    db.execute(
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
        [
            page_id,
            payload.workspace_id,
            payload.title,
            json.dumps(payload.content),
            payload.parent_type,
            payload.parent_id,
            now,
            now,
        ],
    )
    return Page(
        id=page_id,
        workspace_id=payload.workspace_id,
        title=payload.title,
        content=payload.content,
        parent_type=payload.parent_type,
        parent_id=payload.parent_id,
        created_at=now,
        updated_at=now,
    )


@router.patch("/pages/{page_id}", response_model=Page)
def update_page(page_id: str, payload: PageUpdate, request: Request) -> Page:
    db = _get_db(request)
    row = db.query_one("SELECT * FROM pages WHERE id = ?", [page_id])
    if row is None:
        raise HTTPException(status_code=404, detail="Page not found")
    updated = dict(row)
    if payload.title is not None:
        updated["title"] = payload.title
    if payload.content is not None:
        updated["content"] = json.dumps(payload.content)
    updated["updated_at"] = _utc_now()
    db.execute(
        """
        UPDATE pages SET title = ?, content = ?, updated_at = ? WHERE id = ?
        """,
        [updated["title"], updated["content"], updated["updated_at"], page_id],
    )
    updated["content"] = _parse_json(updated["content"])
    return Page(**updated)


@router.get("/databases", response_model=list[DatabaseModel])
def list_databases(
    request: Request,
    workspace_id: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
) -> list[DatabaseModel]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    if workspace_id:
        rows = db.query_all(
            "SELECT * FROM databases WHERE workspace_id = ? ORDER BY created_at LIMIT ? OFFSET ?",
            [workspace_id, limit, offset],
        )
    else:
        rows = db.query_all(
            "SELECT * FROM databases ORDER BY created_at LIMIT ? OFFSET ?",
            [limit, offset],
        )
    return [
        DatabaseModel(**{**dict(row), "schema": _parse_json(row["schema_json"])})
        for row in rows
    ]


@router.get("/databases/{database_id}", response_model=DatabaseModel)
def get_database(database_id: str, request: Request) -> DatabaseModel:
    db = _get_db(request)
    row = db.query_one("SELECT * FROM databases WHERE id = ?", [database_id])
    if row is None:
        raise HTTPException(status_code=404, detail="Database not found")
    data = dict(row)
    data["schema"] = _parse_json(data.pop("schema_json"))
    return DatabaseModel(**data)


@router.post("/databases", response_model=DatabaseModel, status_code=201)
def create_database(payload: DatabaseCreate, request: Request) -> DatabaseModel:
    db = _get_db(request)
    now = _utc_now()
    database_id = new_id("db")
    db.execute(
        """
        INSERT INTO databases (id, workspace_id, name, schema_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [database_id, payload.workspace_id, payload.name, json.dumps(payload.schema_), now, now],
    )
    return DatabaseModel(
        id=database_id,
        workspace_id=payload.workspace_id,
        name=payload.name,
        schema=payload.schema_,
        created_at=now,
        updated_at=now,
    )


@router.get("/databases/{database_id}/rows", response_model=list[DatabaseRow])
def list_database_rows(
    database_id: str,
    request: Request,
    limit: int = Query(50),
    offset: int = Query(0),
) -> list[DatabaseRow]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    rows = db.query_all(
        """
        SELECT * FROM database_rows WHERE database_id = ? ORDER BY created_at LIMIT ? OFFSET ?
        """,
        [database_id, limit, offset],
    )
    return [
        DatabaseRow(**{**dict(row), "properties": _parse_json(row["properties_json"])})
        for row in rows
    ]


@router.post("/databases/{database_id}/rows", response_model=DatabaseRow, status_code=201)
def create_database_row(
    database_id: str, payload: DatabaseRowCreate, request: Request
) -> DatabaseRow:
    db = _get_db(request)
    now = _utc_now()
    row_id = new_id("row")
    db.execute(
        """
        INSERT INTO database_rows (id, database_id, properties_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [row_id, database_id, json.dumps(payload.properties), now, now],
    )
    return DatabaseRow(
        id=row_id,
        database_id=database_id,
        properties=payload.properties,
        created_at=now,
        updated_at=now,
    )


@router.get("/comments", response_model=list[Comment])
def list_comments(
    request: Request,
    page_id: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
) -> list[Comment]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    if page_id:
        rows = db.query_all(
            "SELECT * FROM comments WHERE page_id = ? ORDER BY created_at LIMIT ? OFFSET ?",
            [page_id, limit, offset],
        )
    else:
        rows = db.query_all(
            "SELECT * FROM comments ORDER BY created_at LIMIT ? OFFSET ?",
            [limit, offset],
        )
    return [Comment(**dict(row)) for row in rows]


@router.post("/comments", response_model=Comment, status_code=201)
def create_comment(payload: CommentCreate, request: Request) -> Comment:
    db = _get_db(request)
    now = _utc_now()
    comment_id = new_id("comment")
    db.execute(
        """
        INSERT INTO comments (id, page_id, author_id, body, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [comment_id, payload.page_id, payload.author_id, payload.body, now],
    )
    return Comment(
        id=comment_id,
        page_id=payload.page_id,
        author_id=payload.author_id,
        body=payload.body,
        created_at=now,
    )
