# Project Memory: Notion Workspace Synth

This file is intentionally lightweight and append-only. It captures decisions and operational learnings with evidence.

## Conventions
- Trust labels:
  - `local`: verified directly in this repo/workspace (tests, code, commands)
  - `external`: verified via external system (GitHub Actions, production logs)
  - `inferred`: reasonable inference, not yet verified
- Confidence: `low` | `medium` | `high`

## Decisions

### 2026-02-09: Guarded workspace deletion semantics
- Decision: `DELETE /workspaces/{workspace_id}` requires `cascade=true` when dependent objects exist; seeded demo workspace `ws_demo` additionally requires `force=true`.
- Why: avoid accidental data loss while still enabling deterministic cleanup for demos/tests.
- Evidence: `src/notion_synth/routes.py`, `tests/test_api.py`.
- Commit: `8bb0e15`
- Trust: `local`
- Confidence: `high`
- Follow-ups: consider adding a `dry_run=true` mode that only returns counts (no mutation).

### 2026-02-09: Row filtering adds exact-match + repeatable AND filters
- Decision: `GET /databases/{database_id}/rows` supports `property_value_equals` (paired with `property_name`) and repeatable `property_equals=Name:Value` for multi-property AND filtering.
- Why: demos and integration tests commonly need deterministic, exact row lookup beyond substring matching.
- Evidence: `src/notion_synth/routes.py`, `tests/test_api.py`.
- Commit: `763c849`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Release checklist gating via `make release-check`
- Decision: add `make release-check` to validate version/documentation/changelog coherence before tagging.
- Why: prevent drift between `pyproject.toml`, package `__version__`, and release/changelog docs.
- Evidence: `scripts/release_check.py`, `Makefile`, `docs/RELEASE.md`, `CHANGELOG.md`.
- Commit: `e5c9ad2`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add lightweight indexes for common list paths
- Decision: create small, stable SQLite indexes on foreign keys and `(workspace_id, created_at)`-style list paths at startup; document expression index pattern for JSON property filtering.
- Why: keep local demos snappy without adding heavy dependencies or migrations.
- Evidence: `src/notion_synth/db.py`, `docs/PROJECT.md`.
- Commit: `fb660f6`
- Trust: `local`
- Confidence: `medium`

