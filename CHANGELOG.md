# CHANGELOG

## [Unreleased]
- Add landing page at `/` for quick navigation and curl snippets.
- Add `GET /stats` for dataset counts and DB path.
- Add list filtering and optional `X-Total-Count` header via `include_total=true`.
- Add fixtures export/import endpoints (`/fixtures/export`, `/fixtures/import`).
- Add `mode=merge` for fixture import (upsert without deleting existing data).
- Add `POST /workspaces`, `POST /users`, and `GET /users/{user_id}` to create and retrieve user data.
- Add page/database/row delete/update endpoints (and validate foreign keys on create to avoid 500s).

## [0.1.0] - 2026-02-01
- Initial API with seeded demo workspace.
