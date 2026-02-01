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
    workspace_id: str
    title: str
    content: dict[str, Any]
    parent_type: str
    parent_id: str


class PageUpdate(BaseModel):
    title: str | None = None
    content: dict[str, Any] | None = None


class DatabaseCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workspace_id: str
    name: str
    schema_: dict[str, Any] = Field(alias="schema")


class DatabaseRowCreate(BaseModel):
    properties: dict[str, Any]


class CommentCreate(BaseModel):
    page_id: str
    author_id: str
    body: str


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
