# Update (2026-02-01)

## Shipped
- Added a small landing page at `/` (dark-mode aware) for quick navigation + curl snippets.
- Added `GET /stats` for dataset counts and DB path.
- Added filtering on list endpoints plus optional `X-Total-Count` via `include_total=true`.
- Added tests covering the new endpoints and `X-Total-Count` behavior.
- Added fixture export/import endpoints (`/fixtures/export`, `/fixtures/import`).
- Added `mode=merge` for fixture import (upsert without deleting existing data).
- Added `POST /workspaces`, `POST /users`, and `GET /users/{user_id}` to create and fetch users.

## How to run
```bash
make setup
make dev
```

Then open:
- `http://localhost:8000/` (landing page)
- `http://localhost:8000/docs` (OpenAPI UI)

## How to verify
```bash
make check
```

## Delivery
- Work is pushed directly to `main` (no PR).
