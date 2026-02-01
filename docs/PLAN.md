# PLAN

## Goal
Ship a synthetic Notion-like workspace API with seeded demo data for pages, databases, rows, and comments.

## Stack
- Python 3.11 + FastAPI for lightweight API and OpenAPI docs.
- SQLite for local-first storage with no auth.

## Architecture
- `main.py` creates the FastAPI app and injects a SQLite-backed `Database`.
- `db.py` owns schema creation and deterministic seeding.
- `routes.py` provides CRUD-style endpoints for pages, databases, rows, and comments.

## MVP checklist
- [x] Workspaces + users list endpoints
- [x] Pages list/get/create/update
- [x] Databases list/get/create
- [x] Database rows list/create
- [x] Comments list/create
- [x] Seeded demo org
- [x] Tests for health + seeded data + create

## Risks
- SQLite concurrency: single-process use is safe; document the limitation.
- Schema flexibility: database schemas are JSON blobs; keep validation minimal.

## Milestones
1. Scaffold repo and implement seed + API endpoints.
2. Add tests, linting, type checking, and CI.
3. Document usage + roadmap.
