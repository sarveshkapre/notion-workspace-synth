from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from notion_synth.audit import AuditLog
from notion_synth.blueprint_models import Blueprint, PageSpec, RowPropertySpec
from notion_synth.providers.notion.client import NotionClient
from notion_synth.state import (
    StateStore,
    get_identity,
    get_object,
    list_objects_by_kind,
    mark_event_run,
    upsert_identity,
    upsert_object,
    was_event_run,
)
from notion_synth.util import stable_hash

PLACEHOLDER_PATTERN = re.compile(r"\[\[synth:(?P<kind>page|user):(?P<id>[a-zA-Z0-9_\-:]+)\]\]")


@dataclass
class ApplyResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


@dataclass
class VerifyResult:
    matched: int
    total: int
    missing: list[str]


def verify_users(client: NotionClient, store: StateStore, roster: list[dict[str, str]]) -> VerifyResult:
    users = client.list_users()
    email_map = {}
    for user in users:
        person = user.get("person") or {}
        email = person.get("email")
        if email:
            email_map[email.lower()] = user.get("id")

    matched = 0
    missing: list[str] = []
    for row in roster:
        email = row.get("email", "").lower()
        if email and email in email_map:
            upsert_identity(store, row["synth_user_id"], notion_user_id=email_map[email], email=email)
            matched += 1
        else:
            if email:
                missing.append(email)
    total = len(roster)
    return VerifyResult(matched=matched, total=total, missing=missing)


def apply_blueprint(
    blueprint: Blueprint,
    *,
    root_page_id: str,
    store: StateStore,
    client: NotionClient,
    audit: AuditLog,
    mode: str = "apply",
) -> ApplyResult:
    if mode not in {"apply", "plan"}:
        raise ValueError("mode must be 'apply' or 'plan'")
    result = ApplyResult()

    def record(action: str, kind: str, synth_id: str, remote_id: str | None) -> None:
        audit.write({"action": action, "kind": kind, "synth_id": synth_id, "remote_id": remote_id})

    # Roots
    for root in blueprint.notion_plan.roots:
        payload = _page_payload(root_page_id, root.title, [])
        spec_hash = _page_spec_hash(root.title, [])
        existing = get_object(store, root.synth_id)
        if existing and existing["spec_hash"] == spec_hash:
            result.skipped += 1
            continue
        if mode == "plan":
            record("plan_create", "page", root.synth_id, None)
            result.created += 1
            continue
        created = client.create_page(payload)
        upsert_object(
            store,
            root.synth_id,
            kind="page",
            provider="notion",
            remote_id=created["id"],
            parent_synth_id=None,
            spec_hash=spec_hash,
        )
        record("created", "page", root.synth_id, created["id"])
        result.created += 1

    # Databases
    for db in blueprint.notion_plan.databases:
        parent_id = _resolve_parent_id(db.parent_type, db.parent_synth_id, root_page_id, store)
        payload = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "title": _rich_text(db.title),
            "properties": db.properties,
        }
        spec_hash = stable_hash(payload)
        existing = get_object(store, db.synth_id)
        if existing and existing["spec_hash"] == spec_hash:
            result.skipped += 1
            continue
        if mode == "plan":
            record("plan_create", "database", db.synth_id, None)
            result.created += 1
            continue
        if existing:
            updated = client.update_database(existing["remote_id"], {"title": _rich_text(db.title), "properties": db.properties})
            upsert_object(
                store,
                db.synth_id,
                kind="database",
                provider="notion",
                remote_id=updated["id"],
                parent_synth_id=db.parent_synth_id,
                spec_hash=spec_hash,
            )
            record("updated", "database", db.synth_id, updated["id"])
            result.updated += 1
        else:
            created = client.create_database(payload)
            upsert_object(
                store,
                db.synth_id,
                kind="database",
                provider="notion",
                remote_id=created["id"],
                parent_synth_id=db.parent_synth_id,
                spec_hash=spec_hash,
            )
            record("created", "database", db.synth_id, created["id"])
            result.created += 1

    # Pages
    pages_pending_links: list[PageSpec] = []
    for page in blueprint.notion_plan.pages:
        parent_id = _resolve_parent_id(page.parent_type, page.parent_synth_id, root_page_id, store)
        resolved_blocks, has_unresolved = _blocks_from_spec(page.blocks, store)
        payload = _page_payload(parent_id, page.title, resolved_blocks)
        spec_hash = _page_spec_hash(page.title, resolved_blocks)
        existing = get_object(store, page.synth_id)
        if existing and existing["spec_hash"] == spec_hash:
            result.skipped += 1
            if has_unresolved:
                pages_pending_links.append(page)
            continue
        if mode == "plan":
            record("plan_create", "page", page.synth_id, None)
            result.created += 1
            continue
        if existing:
            updated = client.update_page(existing["remote_id"], {"properties": {"title": {"title": _rich_text(page.title)}}})
            if resolved_blocks:
                client.request("PATCH", f"/blocks/{existing['remote_id']}/children", json={"children": resolved_blocks})
            upsert_object(
                store,
                page.synth_id,
                kind="page",
                provider="notion",
                remote_id=updated["id"],
                parent_synth_id=page.parent_synth_id,
                spec_hash=spec_hash,
            )
            record("updated", "page", page.synth_id, updated["id"])
            result.updated += 1
        else:
            created = client.create_page(payload)
            upsert_object(
                store,
                page.synth_id,
                kind="page",
                provider="notion",
                remote_id=created["id"],
                parent_synth_id=page.parent_synth_id,
                spec_hash=spec_hash,
            )
            record("created", "page", page.synth_id, created["id"])
            result.created += 1
        if has_unresolved:
            pages_pending_links.append(page)

    # Rows (database entries)
    for row in blueprint.notion_plan.rows:
        db_obj = get_object(store, row.database_synth_id)
        if not db_obj:
            continue
        properties = _row_properties(row.properties, store)
        payload = {"parent": {"database_id": db_obj["remote_id"]}, "properties": properties}
        spec_hash = stable_hash(payload)
        existing = get_object(store, row.synth_id)
        if existing and existing["spec_hash"] == spec_hash:
            result.skipped += 1
            continue
        if mode == "plan":
            record("plan_create", "row", row.synth_id, None)
            result.created += 1
            continue
        if existing:
            updated = client.update_page(existing["remote_id"], {"properties": properties})
            upsert_object(
                store,
                row.synth_id,
                kind="row",
                provider="notion",
                remote_id=updated["id"],
                parent_synth_id=row.database_synth_id,
                spec_hash=spec_hash,
            )
            record("updated", "row", row.synth_id, updated["id"])
            result.updated += 1
        else:
            created = client.create_page(payload)
            upsert_object(
                store,
                row.synth_id,
                kind="row",
                provider="notion",
                remote_id=created["id"],
                parent_synth_id=row.database_synth_id,
                spec_hash=spec_hash,
            )
            record("created", "row", row.synth_id, created["id"])
            result.created += 1

    # Comments
    for comment in blueprint.notion_plan.comments:
        page_obj = get_object(store, comment.page_synth_id)
        if not page_obj:
            continue
        rich_text, _ = _rich_text_with_placeholders(comment.body, store)
        payload = {"parent": {"page_id": page_obj["remote_id"]}, "rich_text": rich_text}
        spec_hash = stable_hash(payload)
        existing = get_object(store, comment.synth_id)
        if existing and existing["spec_hash"] == spec_hash:
            result.skipped += 1
            continue
        if mode == "plan":
            record("plan_create", "comment", comment.synth_id, None)
            result.created += 1
            continue
        created = client.create_comment(payload)
        upsert_object(
            store,
            comment.synth_id,
            kind="comment",
            provider="notion",
            remote_id=created["id"],
            parent_synth_id=comment.page_synth_id,
            spec_hash=spec_hash,
        )
        record("created", "comment", comment.synth_id, created["id"])
        result.created += 1

    # Link resolution pass (pages with unresolved placeholders)
    if pages_pending_links and mode == "apply":
        for page in pages_pending_links:
            page_obj = get_object(store, page.synth_id)
            if not page_obj:
                continue
            resolved_blocks, _ = _blocks_from_spec(page.blocks, store, force_resolve=True)
            payload_hash = _page_spec_hash(page.title, resolved_blocks)
            if page_obj["spec_hash"] == payload_hash:
                continue
            client.request("PATCH", f"/blocks/{page_obj['remote_id']}/children", json={"children": resolved_blocks})
            upsert_object(
                store,
                page.synth_id,
                kind="page",
                provider="notion",
                remote_id=page_obj["remote_id"],
                parent_synth_id=page.parent_synth_id,
                spec_hash=payload_hash,
            )

    return result


def destroy_blueprint(store: StateStore, client: NotionClient, audit: AuditLog) -> int:
    archived = 0
    kinds = ("page", "database", "row")
    seen: set[str] = set()
    for kind in kinds:
        for obj in list_objects_by_kind(store, kind):
            remote_id = obj["remote_id"]
            if remote_id in seen:
                continue
            client.archive_page(remote_id)
            audit.write(
                {"action": "archived", "kind": kind, "synth_id": obj["synth_id"], "remote_id": remote_id}
            )
            archived += 1
            seen.add(remote_id)
    return archived


def run_activity(
    blueprint: Blueprint,
    *,
    store: StateStore,
    client: NotionClient,
    audit: AuditLog,
    tick_minutes: int,
    jitter: float,
    iterations: int = 1,
) -> int:
    executed = 0
    for _ in range(max(1, iterations)):
        now = datetime.now(UTC)
        due_events = [
            event
            for event in blueprint.activity_stream
            if _parse_iso(event.scheduled_at) <= now and not was_event_run(store, event.event_id)
        ]
        for event in due_events:
            if _execute_event(event, store, client, audit):
                mark_event_run(store, event.event_id)
                executed += 1
        sleep_seconds = max(1.0, tick_minutes * 60 * (1 + random.uniform(-jitter, jitter)))
        if iterations > 1:
            time.sleep(sleep_seconds)
    return executed


def _resolve_parent_id(parent_type: str, parent_synth_id: str, root_page_id: str, store: StateStore) -> str:
    if parent_type == "root":
        return root_page_id
    existing = get_object(store, parent_synth_id)
    if not existing:
        raise ValueError(f"Parent synth id not found: {parent_synth_id}")
    return existing["remote_id"]


def _page_payload(parent_id: str, title: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {"title": {"title": _rich_text(title)}},
        "children": blocks,
    }


def _page_spec_hash(title: str, blocks: list[dict[str, Any]]) -> str:
    return stable_hash({"title": title, "children": blocks})


def _blocks_from_spec(blocks: list[Any], store: StateStore, force_resolve: bool = False) -> tuple[list[dict[str, Any]], bool]:
    resolved: list[dict[str, Any]] = []
    has_unresolved = False
    for block in blocks:
        rich_text, unresolved = _rich_text_with_placeholders(block.text or "", store, force_resolve=force_resolve)
        has_unresolved = has_unresolved or unresolved
        payload: dict[str, Any] = {"object": "block", "type": block.type}
        if block.type == "divider":
            payload["divider"] = {}
        elif block.type == "to_do":
            payload["to_do"] = {"rich_text": rich_text, "checked": bool(block.checked)}
        else:
            payload[block.type] = {"rich_text": rich_text}
        resolved.append(payload)
    return resolved, has_unresolved


def _row_properties(properties: list[RowPropertySpec], store: StateStore) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for prop in properties:
        if prop.type == "title":
            resolved[prop.name] = {"title": _rich_text(str(prop.value))}
        elif prop.type == "rich_text":
            resolved[prop.name] = {"rich_text": _rich_text(str(prop.value))}
        elif prop.type == "select":
            resolved[prop.name] = {"select": {"name": str(prop.value)}}
        elif prop.type == "multi_select":
            resolved[prop.name] = {"multi_select": [{"name": str(item)} for item in prop.value or []]}
        elif prop.type == "people":
            people = []
            for synth_user_id in prop.value or []:
                identity = get_identity(store, synth_user_id)
                if identity and identity["notion_user_id"]:
                    people.append({"id": identity["notion_user_id"]})
            resolved[prop.name] = {"people": people}
        elif prop.type == "date":
            resolved[prop.name] = {"date": {"start": str(prop.value)}}
        elif prop.type == "checkbox":
            resolved[prop.name] = {"checkbox": bool(prop.value)}
        elif prop.type == "number":
            resolved[prop.name] = {"number": prop.value}
        elif prop.type == "url":
            resolved[prop.name] = {"url": str(prop.value)}
    return resolved


def _rich_text(text: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": text}}]


def _rich_text_with_placeholders(
    text: str, store: StateStore, force_resolve: bool = False
) -> tuple[list[dict[str, Any]], bool]:
    if not text:
        return [], False
    parts: list[dict[str, Any]] = []
    idx = 0
    unresolved = False
    for match in PLACEHOLDER_PATTERN.finditer(text):
        if match.start() > idx:
            parts.append({"type": "text", "text": {"content": text[idx : match.start()]}})
        kind = match.group("kind")
        ident = match.group("id")
        if kind == "page":
            obj = get_object(store, ident)
            if obj:
                parts.append({"type": "mention", "mention": {"type": "page", "page": {"id": obj["remote_id"]}}})
            else:
                parts.append({"type": "text", "text": {"content": match.group(0)}})
                unresolved = True
        elif kind == "user":
            identity = get_identity(store, ident)
            if identity and identity["notion_user_id"]:
                parts.append(
                    {"type": "mention", "mention": {"type": "user", "user": {"id": identity["notion_user_id"]}}}
                )
            else:
                parts.append({"type": "text", "text": {"content": match.group(0)}})
                unresolved = True
        idx = match.end()
    if idx < len(text):
        parts.append({"type": "text", "text": {"content": text[idx:]}})
    if force_resolve:
        unresolved = False
    return parts, unresolved


def _execute_event(event: Any, store: StateStore, client: NotionClient, audit: AuditLog) -> bool:
    target = get_object(store, event.target_synth_id)
    if not target:
        return False
    if event.kind == "page_edit":
        append = event.payload.get("append", "Follow-up note.")
        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(str(append))},
        }
        client.request("PATCH", f"/blocks/{target['remote_id']}/children", json={"children": [block]})
        audit.write(
            {"action": "activity_page_edit", "synth_id": event.target_synth_id, "remote_id": target["remote_id"]}
        )
        return True
    if event.kind == "comment_add":
        body = event.payload.get("body", "Quick update.")
        payload = {"parent": {"page_id": target["remote_id"]}, "rich_text": _rich_text(str(body))}
        client.create_comment(payload)
        audit.write(
            {"action": "activity_comment_add", "synth_id": event.target_synth_id, "remote_id": target["remote_id"]}
        )
        return True
    if event.kind == "row_update":
        properties = {key: {"select": {"name": value}} for key, value in event.payload.items()}
        client.update_page(target["remote_id"], {"properties": properties})
        audit.write(
            {"action": "activity_row_update", "synth_id": event.target_synth_id, "remote_id": target["remote_id"]}
        )
        return True
    return False


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
