from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IdentityUser(BaseModel):
    synth_user_id: str
    display_name: str
    given_name: str
    surname: str
    upn: str
    email: str
    department: str
    job_title: str
    office_location: str
    manager_synth_user_id: str | None = None
    team: str


class IdentityGroup(BaseModel):
    synth_group_id: str
    name: str
    description: str | None = None


class GroupMembership(BaseModel):
    group_synth_id: str
    user_synth_id: str


class IdentitySpec(BaseModel):
    users: list[IdentityUser]
    groups: list[IdentityGroup]
    memberships: list[GroupMembership]


class RootSpec(BaseModel):
    synth_id: str
    title: str
    parent_type: Literal["root"] = "root"


class DatabaseSpec(BaseModel):
    synth_id: str
    parent_synth_id: str
    parent_type: Literal["page", "root"] = "root"
    title: str
    properties: dict[str, Any]


class BlockSpec(BaseModel):
    type: Literal[
        "paragraph",
        "heading_2",
        "heading_3",
        "bulleted_list_item",
        "numbered_list_item",
        "to_do",
        "quote",
        "callout",
        "divider",
    ]
    text: str | None = None
    checked: bool | None = None


class PageSpec(BaseModel):
    synth_id: str
    parent_synth_id: str
    parent_type: Literal["page", "root"] = "root"
    title: str
    blocks: list[BlockSpec]


class RowPropertySpec(BaseModel):
    name: str
    type: Literal[
        "title",
        "rich_text",
        "select",
        "multi_select",
        "people",
        "date",
        "checkbox",
        "number",
        "url",
    ]
    value: Any


class RowSpec(BaseModel):
    synth_id: str
    database_synth_id: str
    properties: list[RowPropertySpec]


class CommentSpec(BaseModel):
    synth_id: str
    page_synth_id: str
    body: str


class NotionPlan(BaseModel):
    roots: list[RootSpec] = Field(default_factory=list)
    databases: list[DatabaseSpec] = Field(default_factory=list)
    pages: list[PageSpec] = Field(default_factory=list)
    rows: list[RowSpec] = Field(default_factory=list)
    comments: list[CommentSpec] = Field(default_factory=list)


class ActivityEvent(BaseModel):
    event_id: str
    kind: Literal["page_edit", "comment_add", "row_update", "page_create"]
    target_synth_id: str
    scheduled_at: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Blueprint(BaseModel):
    format_version: int = 1
    generated_at: str
    seed: int
    company: str
    org_profile: str
    identity: IdentitySpec
    notion_plan: NotionPlan
    activity_stream: list[ActivityEvent] = Field(default_factory=list)
