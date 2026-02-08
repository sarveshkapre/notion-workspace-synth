# Notion Workspace Synth — Plan

Synthetic Notion-like workspace API (FastAPI + SQLite) with deterministic demo seeding, designed for local demos, tests, and integrations.

## Features (current)
- Workspaces, users, pages, databases, rows, comments
- Deterministic demo org seeding on first run
- List filtering (e.g. `title_contains`, parent filters) + `limit`/`offset`
- Optional `X-Total-Count` header on list endpoints via `include_total=true`
- `/stats` endpoint for quick dataset sizing
- Lightweight human landing page at `/` with links + curl snippets

## Top risks / unknowns
- SQLite concurrency: intended for local/dev usage; multi-writer patterns may need pooling or WAL guidance.
- Schema validation: database schemas and page content are JSON blobs; keep validation minimal by design.
- Data realism: “synthetic” defaults may need more domain-specific fixtures over time.

## Commands
- Setup: `make setup`
- Dev server: `make dev`
- Full quality gate: `make check`
- Security checks: `make security`

More details: `docs/PROJECT.md`

## Shipped this run
- Added homepage at `/` and dataset counts at `/stats`.
- Added filtering + optional `X-Total-Count` header to list endpoints.
- Expanded API tests for the new behavior.
- Added fixture export/import endpoints for deterministic demo bundles.
- Added `mode=merge` fixture import for upsert-style iterative demos.
- Added `POST /workspaces` and `POST /users` to create data beyond the seed.
- Added update/delete endpoints for pages/databases/rows, plus basic FK validations on create endpoints.

## Ship next (tight scope)
- Add workspace deletion endpoint with explicit cascade policy (users/pages/databases/comments).
- Add richer row querying (exact match and multi-property filters) with indexed lookup strategy.
- Add focused provider integration tests (mocked Notion/Graph HTTP interactions) for CLI reliability.
