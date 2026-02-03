from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable


@dataclass
class StateStore:
    path: str
    connection: sqlite3.Connection

    def execute(self, query: str, params: Iterable[Any] | None = None) -> None:
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(params or ()))
        self.connection.commit()

    def query_one(self, query: str, params: Iterable[Any] | None = None) -> sqlite3.Row | None:
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchone()

    def query_all(self, query: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchall()


def connect_state(path: str | None = None) -> StateStore:
    resolved = path or os.getenv("NOTION_SYNTH_STATE_DB") or "./state.db"
    connection = sqlite3.connect(resolved, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    store = StateStore(path=resolved, connection=connection)
    _init_schema(store)
    return store


def _init_schema(store: StateStore) -> None:
    store.execute(
        """
        CREATE TABLE IF NOT EXISTS objects (
            synth_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            provider TEXT NOT NULL,
            remote_id TEXT NOT NULL,
            parent_synth_id TEXT,
            spec_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    store.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            blueprint_hash TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL
        )
        """
    )
    store.execute(
        """
        CREATE TABLE IF NOT EXISTS identity_map (
            synth_user_id TEXT PRIMARY KEY,
            entra_object_id TEXT,
            notion_user_id TEXT,
            email TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    store.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_events (
            event_id TEXT PRIMARY KEY,
            last_run_at TEXT NOT NULL
        )
        """
    )


def upsert_object(
    store: StateStore,
    synth_id: str,
    *,
    kind: str,
    provider: str,
    remote_id: str,
    parent_synth_id: str | None,
    spec_hash: str,
) -> None:
    now = _utc_now()
    store.execute(
        """
        INSERT INTO objects (synth_id, kind, provider, remote_id, parent_synth_id, spec_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(synth_id) DO UPDATE SET
            kind = excluded.kind,
            provider = excluded.provider,
            remote_id = excluded.remote_id,
            parent_synth_id = excluded.parent_synth_id,
            spec_hash = excluded.spec_hash,
            updated_at = excluded.updated_at
        """,
        [synth_id, kind, provider, remote_id, parent_synth_id, spec_hash, now, now],
    )


def get_object(store: StateStore, synth_id: str) -> sqlite3.Row | None:
    return store.query_one("SELECT * FROM objects WHERE synth_id = ?", [synth_id])


def list_objects_by_kind(store: StateStore, kind: str) -> list[sqlite3.Row]:
    return store.query_all("SELECT * FROM objects WHERE kind = ?", [kind])


def upsert_identity(
    store: StateStore,
    synth_user_id: str,
    *,
    entra_object_id: str | None = None,
    notion_user_id: str | None = None,
    email: str | None = None,
) -> None:
    now = _utc_now()
    store.execute(
        """
        INSERT INTO identity_map (synth_user_id, entra_object_id, notion_user_id, email, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(synth_user_id) DO UPDATE SET
            entra_object_id = COALESCE(excluded.entra_object_id, identity_map.entra_object_id),
            notion_user_id = COALESCE(excluded.notion_user_id, identity_map.notion_user_id),
            email = COALESCE(excluded.email, identity_map.email),
            updated_at = excluded.updated_at
        """,
        [synth_user_id, entra_object_id, notion_user_id, email, now],
    )


def get_identity(store: StateStore, synth_user_id: str) -> sqlite3.Row | None:
    return store.query_one("SELECT * FROM identity_map WHERE synth_user_id = ?", [synth_user_id])


def record_run_start(store: StateStore, run_id: str, command: str, blueprint_hash: str) -> None:
    store.execute(
        """
        INSERT INTO runs (run_id, command, blueprint_hash, started_at, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        [run_id, command, blueprint_hash, _utc_now(), "running"],
    )


def record_run_finish(store: StateStore, run_id: str, status: str) -> None:
    store.execute(
        """
        UPDATE runs SET finished_at = ?, status = ? WHERE run_id = ?
        """,
        [_utc_now(), status, run_id],
    )


def was_event_run(store: StateStore, event_id: str) -> bool:
    row = store.query_one("SELECT event_id FROM activity_events WHERE event_id = ?", [event_id])
    return row is not None


def mark_event_run(store: StateStore, event_id: str) -> None:
    store.execute(
        """
        INSERT INTO activity_events (event_id, last_run_at) VALUES (?, ?)
        ON CONFLICT(event_id) DO UPDATE SET last_run_at = excluded.last_run_at
        """,
        [event_id, _utc_now()],
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
