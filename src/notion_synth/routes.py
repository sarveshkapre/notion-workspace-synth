import json
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse

from notion_synth.db import Database, new_id
from notion_synth.models import (
    Comment,
    CommentCreate,
    DatabaseCreate,
    DatabaseRow,
    DatabaseRowCreate,
    Fixture,
    FixtureImportResult,
    Page,
    PageCreate,
    PageUpdate,
    Stats,
    User,
    UserCreate,
    Workspace,
    WorkspaceCreate,
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


def _set_total_header(response: Response, total: int) -> None:
    response.headers["X-Total-Count"] = str(total)


def _parse_json(value: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(value))


def _homepage_html() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Notion Workspace Synth</title>
    <style>
      :root{
        color-scheme: light dark;
        --bg: #ffffff;
        --fg: #111111;
        --muted: #6b7280;
        --card: #f5f5f7;
        --border: #e5e7eb;
        --link: #2563eb;
        --code: #111827;
      }
      @media (prefers-color-scheme: dark){
        :root{
          --bg: #0b0b0f;
          --fg: #f5f5f7;
          --muted: #9ca3af;
          --card: #14141b;
          --border: #262631;
          --link: #60a5fa;
          --code: #e5e7eb;
        }
      }
      body{
        margin: 0;
        background: var(--bg);
        color: var(--fg);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial,
          sans-serif;
        line-height: 1.5;
      }
      a{color: var(--link); text-decoration: none}
      a:hover{text-decoration: underline}
      a:focus-visible{
        outline: 2px solid var(--link);
        outline-offset: 2px;
        border-radius: 6px;
      }
      main{max-width: 960px; margin: 0 auto; padding: 28px 16px}
      header{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 18px;
      }
      h1{font-size: 24px; margin: 0}
      .muted{color: var(--muted); font-size: 14px; margin: 6px 0 0}
      .grid{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
        margin-top: 16px;
      }
      .card{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px;
      }
      .card h2{
        font-size: 14px;
        margin: 0 0 10px;
        color: var(--muted);
        letter-spacing: .02em;
        text-transform: uppercase;
      }
      code,pre{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: var(--code);
      }
      pre{
        margin: 0;
        background: rgba(127, 127, 127, .08);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
        overflow: auto;
      }
      ul{margin: 0; padding-left: 18px}
      li{margin: 6px 0}
      .pill{
        display: inline-block;
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 13px;
        color: var(--muted);
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Notion Workspace Synth</h1>
          <p class="muted">
            Local-first synthetic Notion-like workspace API for demos, tests, and integrations.
          </p>
        </div>
        <span class="pill">Unauthenticated · SQLite</span>
      </header>

      <section class="grid" aria-label="Quick links">
        <div class="card">
          <h2>Explore</h2>
          <ul>
            <li><a href="/docs">OpenAPI UI</a></li>
            <li><a href="/openapi.json">OpenAPI JSON</a></li>
            <li><a href="/health">Health</a></li>
            <li><a href="/stats">Stats</a></li>
            <li><a href="/workspaces">Workspaces</a></li>
            <li><a href="/users">Users</a></li>
          </ul>
        </div>
        <div class="card">
          <h2>Try it</h2>
          <pre><code>curl http://localhost:8000/pages
curl http://localhost:8000/pages?include_total=true
curl "http://localhost:8000/pages?title_contains=Welcome"
curl http://localhost:8000/databases?include_total=true</code></pre>
        </div>
      </section>

      <section class="grid" aria-label="Notes">
        <div class="card">
          <h2>Defaults</h2>
          <ul>
            <li>Demo org seeds on first run</li>
            <li>Pagination via <code>limit</code> + <code>offset</code></li>
            <li>Totals via <code>X-Total-Count</code> header</li>
          </ul>
        </div>
        <div class="card">
          <h2>DB Path</h2>
          <p class="muted">
            Configured by <code>NOTION_SYNTH_DB</code> (defaults to <code>./notion_synth.db</code>).
          </p>
        </div>
      </section>
    </main>
  </body>
</html>
"""


@router.get("/", response_class=HTMLResponse, tags=["meta"])
def homepage() -> HTMLResponse:
    return HTMLResponse(content=_homepage_html(), status_code=200)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/stats", response_model=Stats, tags=["meta"])
def stats(request: Request) -> Stats:
    db = _get_db(request)
    workspaces = db.query_one("SELECT COUNT(*) AS count FROM workspaces")
    users = db.query_one("SELECT COUNT(*) AS count FROM users")
    pages = db.query_one("SELECT COUNT(*) AS count FROM pages")
    databases = db.query_one("SELECT COUNT(*) AS count FROM databases")
    database_rows = db.query_one("SELECT COUNT(*) AS count FROM database_rows")
    comments = db.query_one("SELECT COUNT(*) AS count FROM comments")

    return Stats(
        db_path=db.path,
        workspaces=int(workspaces["count"]) if workspaces else 0,
        users=int(users["count"]) if users else 0,
        pages=int(pages["count"]) if pages else 0,
        databases=int(databases["count"]) if databases else 0,
        database_rows=int(database_rows["count"]) if database_rows else 0,
        comments=int(comments["count"]) if comments else 0,
    )


@router.get("/fixtures/export", response_model=Fixture, tags=["fixtures"])
def export_fixture(request: Request) -> Fixture:
    db = _get_db(request)
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


@router.post("/fixtures/import", response_model=FixtureImportResult, tags=["fixtures"])
def import_fixture(
    payload: Fixture,
    request: Request,
    mode: str = Query(
        "replace",
        description="Import mode: 'replace' (wipe then load) or 'merge' (upsert).",
    ),
) -> FixtureImportResult:
    if payload.format_version != 1:
        raise HTTPException(status_code=400, detail="Unsupported fixture format_version")
    if mode not in {"replace", "merge"}:
        raise HTTPException(status_code=400, detail="Unsupported import mode")

    db = _get_db(request)
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
        raise HTTPException(status_code=400, detail="Fixture import failed") from exc

    return FixtureImportResult(status="ok", inserted=inserted)


@router.get("/workspaces", response_model=list[Workspace])
def list_workspaces(request: Request) -> list[Workspace]:
    db = _get_db(request)
    rows = db.query_all("SELECT * FROM workspaces ORDER BY created_at")
    return [Workspace(**dict(row)) for row in rows]


@router.post("/workspaces", response_model=Workspace, status_code=201)
def create_workspace(payload: WorkspaceCreate, request: Request) -> Workspace:
    db = _get_db(request)
    now = _utc_now()
    workspace_id = new_id("ws")
    db.execute(
        "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
        [workspace_id, payload.name, now],
    )
    return Workspace(id=workspace_id, name=payload.name, created_at=now)


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
    response: Response,
    workspace_id: str | None = None,
    name_contains: str | None = None,
    email_contains: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
    include_total: bool = Query(False),
) -> list[User]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)

    conditions: list[str] = []
    params: list[Any] = []
    if workspace_id:
        conditions.append("workspace_id = ?")
        params.append(workspace_id)
    if name_contains:
        conditions.append("name LIKE ?")
        params.append(f"%{name_contains}%")
    if email_contains:
        conditions.append("email LIKE ?")
        params.append(f"%{email_contains}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    if include_total:
        count_row = db.query_one(f"SELECT COUNT(*) AS count FROM users {where}", params)  # nosec B608
        _set_total_header(response, int(count_row["count"]) if count_row else 0)

    rows = db.query_all(
        f"SELECT * FROM users {where} ORDER BY created_at LIMIT ? OFFSET ?",  # nosec B608
        [*params, limit, offset],
    )
    return [User(**dict(row)) for row in rows]


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: str, request: Request) -> User:
    db = _get_db(request)
    row = db.query_one("SELECT * FROM users WHERE id = ?", [user_id])
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**dict(row))


@router.post("/users", response_model=User, status_code=201)
def create_user(payload: UserCreate, request: Request) -> User:
    db = _get_db(request)
    workspace = db.query_one("SELECT id FROM workspaces WHERE id = ?", [payload.workspace_id])
    if workspace is None:
        raise HTTPException(status_code=400, detail="Invalid workspace_id")

    now = _utc_now()
    user_id = new_id("user")
    db.execute(
        "INSERT INTO users (id, workspace_id, name, email, created_at) VALUES (?, ?, ?, ?, ?)",
        [user_id, payload.workspace_id, payload.name, payload.email, now],
    )
    return User(
        id=user_id,
        workspace_id=payload.workspace_id,
        name=payload.name,
        email=payload.email,
        created_at=now,
    )


@router.get("/pages", response_model=list[Page])
def list_pages(
    request: Request,
    response: Response,
    workspace_id: str | None = None,
    parent_type: str | None = None,
    parent_id: str | None = None,
    title_contains: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
    include_total: bool = Query(False),
) -> list[Page]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)

    conditions: list[str] = []
    params: list[Any] = []
    if workspace_id:
        conditions.append("workspace_id = ?")
        params.append(workspace_id)
    if parent_type:
        conditions.append("parent_type = ?")
        params.append(parent_type)
    if parent_id:
        conditions.append("parent_id = ?")
        params.append(parent_id)
    if title_contains:
        conditions.append("title LIKE ?")
        params.append(f"%{title_contains}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    if include_total:
        count_row = db.query_one(f"SELECT COUNT(*) AS count FROM pages {where}", params)  # nosec B608
        _set_total_header(response, int(count_row["count"]) if count_row else 0)

    rows = db.query_all(
        f"SELECT * FROM pages {where} ORDER BY created_at LIMIT ? OFFSET ?",  # nosec B608
        [*params, limit, offset],
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
    response: Response,
    workspace_id: str | None = None,
    name_contains: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
    include_total: bool = Query(False),
) -> list[DatabaseModel]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)

    conditions: list[str] = []
    params: list[Any] = []
    if workspace_id:
        conditions.append("workspace_id = ?")
        params.append(workspace_id)
    if name_contains:
        conditions.append("name LIKE ?")
        params.append(f"%{name_contains}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    if include_total:
        count_row = db.query_one(  # nosec B608
            f"SELECT COUNT(*) AS count FROM databases {where}",  # nosec B608
            params,
        )
        _set_total_header(response, int(count_row["count"]) if count_row else 0)

    rows = db.query_all(
        f"SELECT * FROM databases {where} ORDER BY created_at LIMIT ? OFFSET ?",  # nosec B608
        [*params, limit, offset],
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
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
    include_total: bool = Query(False),
) -> list[DatabaseRow]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)
    if include_total:
        count_row = db.query_one(
            "SELECT COUNT(*) AS count FROM database_rows WHERE database_id = ?",
            [database_id],
        )
        _set_total_header(response, int(count_row["count"]) if count_row else 0)
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
    response: Response,
    page_id: str | None = None,
    author_id: str | None = None,
    limit: int = Query(50),
    offset: int = Query(0),
    include_total: bool = Query(False),
) -> list[Comment]:
    db = _get_db(request)
    limit, offset = _limit_offset(limit, offset)

    conditions: list[str] = []
    params: list[Any] = []
    if page_id:
        conditions.append("page_id = ?")
        params.append(page_id)
    if author_id:
        conditions.append("author_id = ?")
        params.append(author_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    if include_total:
        count_row = db.query_one(f"SELECT COUNT(*) AS count FROM comments {where}", params)  # nosec B608
        _set_total_header(response, int(count_row["count"]) if count_row else 0)

    rows = db.query_all(
        f"SELECT * FROM comments {where} ORDER BY created_at LIMIT ? OFFSET ?",  # nosec B608
        [*params, limit, offset],
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
