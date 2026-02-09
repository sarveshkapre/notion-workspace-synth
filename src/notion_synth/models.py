from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Stats(BaseModel):
    db_path: str
    workspaces: int
    users: int
    pages: int
    databases: int
    database_rows: int
    comments: int


class Workspace(BaseModel):
    id: str
    name: str
    created_at: str


class User(BaseModel):
    id: str
    workspace_id: str
    name: str
    email: str
    created_at: str


class Page(BaseModel):
    id: str
    workspace_id: str
    title: str
    content: dict[str, Any]
    parent_type: str
    parent_id: str
    created_at: str
    updated_at: str


class Database(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    workspace_id: str
    name: str
    schema_: dict[str, Any] = Field(alias="schema")
    created_at: str
    updated_at: str


class DatabaseRow(BaseModel):
    id: str
    database_id: str
    properties: dict[str, Any]
    created_at: str
    updated_at: str


class Comment(BaseModel):
    id: str
    page_id: str
    author_id: str
    body: str
    created_at: str


class PageCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "workspace_id": "ws_demo",
                    "title": "Sprint Notes",
                    "content": {"type": "doc", "blocks": ["Kickoff", "Decisions", "Next steps"]},
                    "parent_type": "workspace",
                    "parent_id": "ws_demo",
                }
            ]
        }
    )

    workspace_id: str
    title: str
    content: dict[str, Any]
    parent_type: str
    parent_id: str


class PageUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Sprint Notes v2",
                    "content": {"type": "doc", "blocks": ["Updated kickoff notes"]},
                }
            ]
        }
    )

    title: str | None = None
    content: dict[str, Any] | None = None


class DatabaseCreate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "workspace_id": "ws_demo",
                    "name": "Tickets",
                    "schema": {
                        "properties": {
                            "Title": {"type": "title"},
                            "Status": {"type": "select"},
                            "Owner": {"type": "person"},
                        }
                    },
                }
            ]
        },
    )

    workspace_id: str
    name: str
    schema_: dict[str, Any] = Field(alias="schema")


class DatabaseUpdate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Tickets v2",
                    "schema": {"properties": {"Title": {"type": "title"}, "Status": {"type": "select"}}},
                }
            ]
        },
    )

    name: str | None = None
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")


class DatabaseRowCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"properties": {"Title": "Investigate latency", "Status": "In Progress", "Owner": "Alex Rivers"}}
            ]
        }
    )

    properties: dict[str, Any]


class DatabaseRowUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"properties": {"Status": "Done"}}]}
    )

    properties: dict[str, Any] | None = None


class CommentCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"page_id": "page_home", "author_id": "user_alex", "body": "Kickoff complete."}]
        }
    )

    page_id: str
    author_id: str
    body: str


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Acme"}]})

    name: str


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"workspace_id": "ws_demo", "name": "Taylor", "email": "taylor@example.com"}]
        }
    )

    workspace_id: str
    name: str
    email: str


class WorkspaceDeletePreview(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "workspace_id": "ws_demo",
                    "requires_force": True,
                    "requires_cascade": True,
                    "can_delete": False,
                    "counts": {
                        "users": 3,
                        "pages": 2,
                        "databases": 1,
                        "database_rows": 2,
                        "comments": 2,
                    },
                }
            ]
        }
    )

    workspace_id: str
    requires_force: bool
    requires_cascade: bool
    can_delete: bool
    counts: dict[str, int]


class Fixture(BaseModel):
    format_version: int = 1
    exported_at: str
    workspaces: list[Workspace]
    users: list[User]
    pages: list[Page]
    databases: list[Database]
    database_rows: list[DatabaseRow]
    comments: list[Comment]


class FixtureImportResult(BaseModel):
    status: str
    inserted: dict[str, int]


class AdminResetResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "before": {
                        "db_path": "./notion_synth.db",
                        "workspaces": 2,
                        "users": 5,
                        "pages": 4,
                        "databases": 1,
                        "database_rows": 2,
                        "comments": 3,
                    },
                    "after": {
                        "db_path": "./notion_synth.db",
                        "workspaces": 1,
                        "users": 3,
                        "pages": 2,
                        "databases": 1,
                        "database_rows": 2,
                        "comments": 2,
                    },
                }
            ]
        }
    )

    status: str
    before: Stats
    after: Stats


class PackInfo(BaseModel):
    name: str
    description: str
    profile: str
    industry: str
    default_company: str
    default_seed: int
    counts: dict[str, int]


class PackApplyPreview(BaseModel):
    status: str
    pack: PackInfo
    before: Stats
    after: Stats
    expected_inserted: dict[str, int]


class PackApplyResult(BaseModel):
    status: str
    pack: PackInfo
    before: Stats
    after: Stats
    inserted: dict[str, int]
