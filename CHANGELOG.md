# CHANGELOG

## [Unreleased]
- Fix CI/tooling reliability by allowing `make` targets to fall back to environment Python when `.venv` is absent.
- Add regression coverage for Makefile Python fallback (`tests/test_makefile.py`).
- Add `DELETE /users/{user_id}` with authored-comment cascade semantics.
- Add `GET /comments/{comment_id}` and `DELETE /comments/{comment_id}`.
- Add row query filters on `GET /databases/{database_id}/rows` via `property_name` and `property_value_contains`.
- Align FastAPI app version metadata with package version (`0.2.0`).
- Stabilize lint/type/security gates across CLI/provider modules so `make check` and `make security` pass in CI.
- Add landing page at `/` for quick navigation and curl snippets.
- Add `GET /stats` for dataset counts and DB path.
- Add list filtering and optional `X-Total-Count` header via `include_total=true`.
- Add fixtures export/import endpoints (`/fixtures/export`, `/fixtures/import`).
- Add `mode=merge` for fixture import (upsert without deleting existing data).
- Add `POST /workspaces`, `POST /users`, and `GET /users/{user_id}` to create and retrieve user data.
- Add page/database/row delete/update endpoints (and validate foreign keys on create to avoid 500s).
- Add enterprise CLI for generating, seeding, exporting, and importing synthetic workspaces.
- Add deterministic synthetic generator profile for engineering orgs.

## [0.1.0] - 2026-02-01
- Initial API with seeded demo workspace.
