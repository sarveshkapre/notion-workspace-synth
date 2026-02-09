# Project Memory: Notion Workspace Synth

This file is intentionally lightweight and append-only. It captures decisions and operational learnings with evidence.

## Conventions
- Trust labels:
  - `local`: verified directly in this repo/workspace (tests, code, commands)
  - `external`: verified via external system (GitHub Actions, production logs)
  - `inferred`: reasonable inference, not yet verified
- Confidence: `low` | `medium` | `high`

## Decisions

### 2026-02-09: Add pagination metadata via response headers
- Decision: list endpoints that support `limit`/`offset` accept `include_pagination=true` and emit paging metadata via headers (`X-Has-More`, `X-Next-Offset`, `X-Limit`, `X-Offset`, plus `Link: <...>; rel="next"` when applicable).
- Why: keep response bodies backward-compatible (still lists) while making client iteration and demo scripting easier.
- Evidence: `src/notion_synth/routes.py`, `tests/test_api.py::test_list_pages_pagination_headers`, `README.md`.
- Commit: `54e879a`
- Trust: `local`
- Confidence: `high`

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

### 2026-02-09: Add deletion dry-run preview for safer demos
- Decision: `DELETE /workspaces/{workspace_id}` supports `dry_run=true` to return dependency counts plus `requires_force`/`requires_cascade`/`can_delete` without mutating data.
- Why: improves demo UX and reduces accidental destructive actions while keeping the API simple (single endpoint).
- Evidence: `src/notion_synth/routes.py`, `src/notion_synth/models.py::WorkspaceDeletePreview`, `tests/test_api.py`.
- Commit: `69b70f7`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add OpenAPI request examples via Pydantic `json_schema_extra`
- Decision: add concrete examples for common write payload models (workspaces/users/pages/databases/rows/comments) using Pydantic v2 JSON schema extras.
- Why: makes `/docs` usable as a “copy/paste” playground for demos and integration tests.
- Evidence: `src/notion_synth/models.py` (examples), manual verification via `/docs`.
- Commit: `69b70f7`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Default SQLite busy timeout + opt-in WAL mode
- Decision: set a default SQLite `busy_timeout` and support opt-in WAL via `NOTION_SYNTH_SQLITE_WAL=1`, plus a `make dev-wal` helper.
- Why: reduces transient `database is locked` errors in local multi-client demos without adding a DB server dependency.
- Evidence: `src/notion_synth/db.py`, `Makefile`, `docs/PROJECT.md`, `README.md`.
- Commit: `b38a56b`
- Trust: `local`
- Confidence: `medium`

## Verification Evidence
- `make check` (pass) on 2026-02-09.
- `make check` (pass) on 2026-02-09 (pagination headers).
- `make security` (pass) on 2026-02-09.
- Smoke (pass) on 2026-02-09:
  - `TMP_BASE=$(mktemp /tmp/notion_synth.XXXXXX) && TMP_DB="$TMP_BASE.db" && mv "$TMP_BASE" "$TMP_DB" && NOTION_SYNTH_DB=$TMP_DB .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port 8001`
  - `curl -sS http://127.0.0.1:8001/health`
  - `curl -sS http://127.0.0.1:8001/stats`
  - `curl -sS -X DELETE "http://127.0.0.1:8001/workspaces/ws_demo?dry_run=true"`
- CI (pass) on 2026-02-09:
  - `gh run watch 21812172624 --exit-status`

## Mistakes And Fixes
- 2026-02-09: Gitleaks secret scan failed in CI due to shallow checkout; fixed by setting `actions/checkout` `fetch-depth: 0`.
  - Root cause: gitleaks scans a git commit range on push; with depth=1 the base commit is missing and `git log` fails.
  - Prevention rule: run history-range scanners (gitleaks, release tooling) only with full history in CI.
  - Evidence: GitHub Actions failure `21812114129`, fix commit `120f3a2`.
  - Trust: `external` (failure), `local` (workflow change)
