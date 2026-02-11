# ROADMAP

## Near-term
- Add more realistic synthetic fixtures (more packs + profiles).

## Later
- Add ingest API for external fixtures.

## Done
- 2026-02-11: Add synthetic attachment metadata across pages/comments (API + fixtures + generator).
- 2026-02-11: Add richer search endpoints: `GET /search/comments` and `GET /search/rows`.
- 2026-02-09: Add fixture packs: `GET /packs` plus admin-gated `POST /admin/apply-pack` for deterministic realistic datasets.
- 2026-02-09: Add request/response examples in docs for list filters + paging patterns.
- 2026-02-09: Add optional CORS support for local demo UIs (env-configured allowed origins).
- 2026-02-09: Add Docker Compose for local demos (API + persisted SQLite volume) and “safe demo” guidance.
- 2026-02-09: Add opt-in fault injection for demos/tests (latency + failure simulation; env-guarded).
- 2026-02-09: Add guarded reset endpoint to restore seeded demo data for deterministic demos.
