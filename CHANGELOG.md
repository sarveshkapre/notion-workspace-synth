# CHANGELOG

## [Unreleased]
- Add pagination metadata headers on list endpoints via `include_pagination=true` (includes `Link: <...>; rel="next"`).
- Add `GET /search/pages?q=...` page search endpoint with best-effort SQLite FTS5 backing (fallback to `LIKE` scans).
- Add env-guarded admin reset endpoint (`POST /admin/reset?confirm=true`) to wipe and restore seeded demo data for deterministic demos.
- Add opt-in fault injection middleware for demos/tests (`NOTION_SYNTH_FAULT_INJECTION=1` + `delay_ms` / `fail_rate` / `fail_status` query params).
- Add fixture packs: `GET /packs` plus admin-gated `POST /admin/apply-pack` to generate + replace the local DB with a realistic preset dataset.
- Add `X-Request-Id` response header for easier debugging, plus opt-in structured error responses (via `Accept: application/vnd.notion-synth.error+json`).
- Add attachment metadata support for pages/comments (`name`, `mime_type`, `size_bytes`, optional `external_url`) across API CRUD, deterministic generator output, and fixture import/export.
- Add richer search endpoints: `GET /search/comments` and `GET /search/rows` with optional total-count and pagination headers.

## [0.2.0] - 2026-02-09
- Fix CI/tooling reliability by allowing `make` targets to fall back to environment Python when `.venv` is absent.
- Add regression coverage for Makefile Python fallback (`tests/test_makefile.py`).
- Stabilize lint/type/security gates across CLI/provider modules so `make check` and `make security` pass in CI.
- Align FastAPI app version metadata with package version (`0.2.0`).
- Add landing page at `/` for quick navigation and curl snippets, plus `GET /stats` for dataset counts and DB path.
- Add list filtering and optional `X-Total-Count` header via `include_total=true`.
- Add fixtures export/import endpoints (`/fixtures/export`, `/fixtures/import`) including `mode=merge`.
- Add `POST /workspaces`, `POST /users`, and `GET /users/{user_id}` to create and retrieve user data.
- Add update/delete endpoints for pages/databases/rows with FK validation on create.
- Add comment lifecycle endpoints: `DELETE /users/{user_id}` cascades authored comments; `GET /comments/{comment_id}` + `DELETE /comments/{comment_id}`.
- Add row filters on `GET /databases/{database_id}/rows`: contains-match plus exact-match (`property_value_equals`, repeatable `property_equals`).
- Add `DELETE /workspaces/{workspace_id}` with cascade guardrails (demo workspace requires `force=true`).
- Add SQLite indexes for common list/filter paths and document optional JSON expression indexing.
- Add mocked provider tests for Notion + Graph clients and a CLI `generate` smoke test.

## [0.1.0] - 2026-02-01
- Initial API with seeded demo workspace.
