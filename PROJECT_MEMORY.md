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

### 2026-02-09: Add best-effort page search via `/search/pages`
- Decision: add `GET /search/pages?q=...` and back it with SQLite FTS5 when available; fall back to `LIKE` scans if FTS5 is not compiled in.
- Why: “search everywhere” is a baseline Notion workflow, and it makes the synthetic API substantially more usable for demos and integration tests.
- Evidence: `src/notion_synth/db.py` (FTS setup), `src/notion_synth/routes.py` (`GET /search/pages`), `tests/test_api.py::test_search_pages`, smoke curl.
- Commit: `2ab2d2f`
- Trust: `local`
- Confidence: `medium` (FTS availability varies by SQLite build; fallback path covered by tests).

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

### 2026-02-09: Add env-guarded admin reset endpoint for deterministic demos
- Decision: add `POST /admin/reset` (requires `NOTION_SYNTH_ADMIN=1`) supporting `dry_run=true` preview and `confirm=true` destructive reset that restores the seeded demo org.
- Why: demos and integration tests frequently need a deterministic way to return to a known-good dataset without manually deleting the SQLite file.
- Evidence: `src/notion_synth/routes.py` (`POST /admin/reset`), `src/notion_synth/db.py::seed_demo(force=True)`, `tests/test_api.py::test_admin_reset_confirm_wipes_and_reseeds`.
- Commit: `dc1e7aa`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add opt-in fault injection middleware for demo/test realism
- Decision: add fault injection middleware behind `NOTION_SYNTH_FAULT_INJECTION=1` supporting `delay_ms`, `fail_rate`, and `fail_status`.
- Why: explicit latency/failure simulation is a baseline expectation for mocking tools and makes client retry / timeout behavior testable against the synthetic API.
- Evidence: `src/notion_synth/fault_injection.py`, `src/notion_synth/main.py`, `tests/test_fault_injection.py`.
- Commit: `496df9f`
- Trust: `local`
- Confidence: `medium`

### 2026-02-09: Add Docker Compose demo stack with persisted SQLite volume
- Decision: ship `docker-compose.yml` for local demos with a named volume for SQLite persistence and a localhost-only port binding by default.
- Why: “docker compose up” is a common baseline workflow for mock/demo servers; persistence + safe binding reduces demo friction and accidental exposure risk.
- Evidence: `docker-compose.yml`, `README.md`, `docs/SECURITY.md`.
- Commit: `af7f5b8`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add optional CORS for browser demo clients
- Decision: add opt-in CORS middleware via `NOTION_SYNTH_CORS_ORIGINS` and expose paging metadata headers to browser clients.
- Why: local UIs running on a separate origin need CORS, and paging/count headers are otherwise unreadable to frontend code.
- Evidence: `src/notion_synth/main.py`, `tests/test_cors.py`, `README.md`, `docs/PROJECT.md`.
- Commit: `d96dd6d`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Document list filters + paging patterns in README
- Decision: add concrete curl examples for `include_total`, `include_pagination`, and row filter operators (`property_value_contains`, `property_value_equals`, repeatable `property_equals`).
- Why: improves time-to-first-demo and reduces reliance on reading OpenAPI schemas for common list/query flows.
- Evidence: `README.md`.
- Commit: `e2f616e`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add fixture packs you can apply without restarting the server
- Decision: add `GET /packs` plus admin-gated `POST /admin/apply-pack` (supports `dry_run=true` and `confirm=true`) to generate + replace the local DB with a realistic preset dataset.
- Why: “reset to a known realistic dataset” is a baseline expectation for mock/demo servers; packs reduce “many flags” friction and make demos reproducible.
- Evidence: `src/notion_synth/packs.py`, `src/notion_synth/routes.py`, `tests/test_packs.py`, `README.md`.
- Commit: `e84c93b`
- Trust: `local`
- Confidence: `high`

### 2026-02-09: Add X-Request-Id header and opt-in structured errors
- Decision: add `X-Request-Id` response header for all requests; add opt-in structured error payloads via `Accept: application/vnd.notion-synth.error+json` (or `?error_format=structured`) while keeping default FastAPI error shapes unchanged.
- Why: request tracing is a common expectation for production-grade APIs; opt-in structured errors improve DX without breaking existing clients/tests that assume `{"detail": ...}`.
- Evidence: `src/notion_synth/errors.py`, `src/notion_synth/main.py`, `tests/test_errors.py`, `README.md`.
- Commit: `de00d49`
- Trust: `local`
- Confidence: `high`

### 2026-02-10: Add CLI packs/profiles commands + local smoke script
- Decision: add CLI subcommands for discoverability and local dataset resets: `notion-synth profiles list`, `notion-synth packs list`, and `notion-synth packs apply` (with `--dry-run` preview and `--confirm` guard), plus a runnable end-to-end smoke script (`make smoke`).
- Why: reduces “many flags” friction, improves safe local resets without needing the admin HTTP endpoint, and provides a stable smoke verification path for maintainers.
- Evidence: `src/notion_synth/cli.py`, `tests/test_cli_packs_profiles.py`, `scripts/demo_smoke.py`, `Makefile`, `README.md`.
- Commit: `98025e0` (CLI), `64b4827` (smoke)
- Trust: `local`
- Confidence: `high`

### 2026-02-11: Add attachment metadata across pages/comments
- Decision: add attachment metadata support to pages/comments with a minimal schema (`id`, `name`, `mime_type`, `size_bytes`, optional `external_url`) across API CRUD, fixture import/export, seeded demo data, and deterministic generator outputs.
- Why: attachment metadata is a baseline parity expectation for Notion-like content models and improves downstream integration realism without adding blob storage complexity.
- Evidence: `src/notion_synth/models.py`, `src/notion_synth/db.py`, `src/notion_synth/routes.py`, `src/notion_synth/fixtures.py`, `src/notion_synth/generator.py`, `tests/test_api.py`, `tests/test_generator.py`.
- Commit: `34b1084`
- Trust: `trusted (local)`
- Confidence: `high`

### 2026-02-11: Add richer search endpoints for comments and rows
- Decision: add `GET /search/comments` and `GET /search/rows` with optional filters and consistent metadata behavior (`include_total`, `include_pagination`) aligned with existing list/search endpoints.
- Why: users expect search beyond pages for practical demo/testing workflows; this closes a key parity gap with API mocking tools.
- Evidence: `src/notion_synth/routes.py`, `tests/test_api.py::test_search_comments_and_rows`, `README.md`.
- Commit: `34b1084`
- Trust: `trusted (local)`
- Confidence: `high`

### 2026-02-11: Make smoke flow resilient to pack-specific seeded IDs
- Decision: update `scripts/demo_smoke.py` to use IDs discovered at runtime (workspace/user/page) and search assertions that do not depend on fixed row IDs.
- Why: pack application replaces the DB with generated IDs, so hard-coded seeded IDs caused false-negative smoke failures.
- Evidence: `scripts/demo_smoke.py`, `make smoke`.
- Commit: `34b1084`
- Trust: `trusted (local)`
- Confidence: `high`

## Verification Evidence
- `make check` (pass) on 2026-02-09.
- `make check` (pass) on 2026-02-09 (pagination headers).
- `make check` (pass) on 2026-02-09 (page search).
- `make security` (pass) on 2026-02-09.
- `make security` (pass) on 2026-02-09 (page search bandit annotation).
- `make check` (pass) on 2026-02-09 (admin reset + fault injection).
- `make security` (pass) on 2026-02-09 (fault injection).
- Smoke (pass) on 2026-02-09:
  - `TMP_BASE=$(mktemp /tmp/notion_synth.XXXXXX) && TMP_DB="$TMP_BASE.db" && mv "$TMP_BASE" "$TMP_DB" && NOTION_SYNTH_DB=$TMP_DB .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port 8001`
  - `curl -sS http://127.0.0.1:8001/health`
  - `curl -sS http://127.0.0.1:8001/stats`
  - `curl -sS -X DELETE "http://127.0.0.1:8001/workspaces/ws_demo?dry_run=true"`
- Smoke (pass) on 2026-02-09:
  - `NOTION_SYNTH_DB=$(mktemp /tmp/notion_synth.XXXXXX).db .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port 8012`
  - `curl -sS "http://127.0.0.1:8012/search/pages?q=Welcome"`
  - `curl -sS -D - "http://127.0.0.1:8012/pages?limit=1&include_pagination=true" -o /dev/null`
- Smoke (pass) on 2026-02-09 (admin reset + fault injection):
  - `NOTION_SYNTH_ADMIN=1 NOTION_SYNTH_FAULT_INJECTION=1 NOTION_SYNTH_DB=$(mktemp /tmp/notion_synth.XXXXXX).db .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port 8015`
  - `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8015/health` -> `200`
  - `curl -sS -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8015/admin/reset?dry_run=true"` -> `200`
  - `curl -sS -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8015/admin/reset?confirm=true"` -> `200`
  - `curl -sS -D - -o /dev/null "http://127.0.0.1:8015/health?delay_ms=7" | rg -i "^x-notion-synth-delay-ms:"` -> `x-notion-synth-delay-ms: 7`
  - `curl -sS -o /dev/null -w "%{http_code}" "http://127.0.0.1:8015/health?fail_rate=1&fail_status=503"` -> `503`
- CI (pass) on 2026-02-09:
  - `gh run watch 21812172624 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21817594404 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21817620448 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21825051363 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21825081080 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21825198642 --exit-status`
- CI (fail) on 2026-02-09:
  - `gh run view 21833223544 --log-failed` -> `actions/checkout` fetch returned HTTP `500` (GitHub internal error)
- CI (pass) on 2026-02-09:
  - `gh run watch 21833968192 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21834008996 --exit-status`
- CI (pass) on 2026-02-09:
  - `gh run watch 21834175788 --exit-status` (completed with a checkout-retry warning annotation about GitHub HTTP 500, but job succeeded)
- `make check` (pass) on 2026-02-09 (Docker Compose docs + CORS + README examples).
- Smoke (pass) on 2026-02-09 (CORS + paging headers):
  - `TMP_DB=$(mktemp /tmp/notion_synth.XXXXXX).db NOTION_SYNTH_DB=$TMP_DB NOTION_SYNTH_CORS_ORIGINS=http://localhost:5173 .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port 8021`
  - `curl -sS -D - -o /dev/null -H 'Origin: http://localhost:5173' 'http://127.0.0.1:8021/pages?limit=1&include_pagination=true' | rg -i '^(access-control-allow-origin|access-control-expose-headers|x-has-more|x-next-offset|link):'`
  - `curl -sS http://127.0.0.1:8021/health` -> `{"status":"ok"}`
- `make check` (pass) on 2026-02-09 (packs + request id + structured errors).
- `make security` (pass) on 2026-02-09 (packs + request id + structured errors).
- Smoke (pass) on 2026-02-09 (packs + structured errors):
  - `PORT=8034 TMP_DB=$(mktemp /tmp/notion_synth.XXXXXX).db NOTION_SYNTH_DB=$TMP_DB NOTION_SYNTH_ADMIN=1 .venv/bin/python -m uvicorn notion_synth.main:app --host 127.0.0.1 --port $PORT`
  - `curl -fsS http://127.0.0.1:$PORT/packs`
  - `curl -fsS -X POST "http://127.0.0.1:$PORT/admin/apply-pack?name=engineering_small&dry_run=true"`
  - `curl -fsS -X POST "http://127.0.0.1:$PORT/admin/apply-pack?name=engineering_small&confirm=true"`
  - `curl -sS -H "Accept: application/vnd.notion-synth.error+json" "http://127.0.0.1:$PORT/workspaces/ws_nope"`
  - `curl -fsS -D - -o /dev/null "http://127.0.0.1:$PORT/health" | rg -i "^x-request-id:"`
- CI (pass) on 2026-02-09:
  - `gh run watch 21842360214 --exit-status` (commit `e84c93b`)
- CI (pass) on 2026-02-09:
  - `gh run watch 21842373742 --exit-status` (commit `de00d49`)
- CI (pass) on 2026-02-09:
  - `gh run watch 21842438832 --exit-status` (commit `31a1105`)
- CI (pass) on 2026-02-09:
  - `gh run watch 21842492706 --exit-status` (commit `e37f1c2`)
- Docker Compose verification (fail) on 2026-02-09:
  - `docker compose config -q` -> `command not found: docker` (Docker not available in this environment)
- `make check` (pass) on 2026-02-10.
- `make security` (pass) on 2026-02-10.
- `make smoke` (pass) on 2026-02-10.
- CI (pass) on 2026-02-10:
  - `gh run watch 21859503330 --exit-status` (commit `98025e0`)
- CI (pass) on 2026-02-10:
  - `gh run watch 21859534573 --exit-status` (commit `64b4827`)
- CI (pass) on 2026-02-10:
  - `gh run watch 21859562994 --exit-status` (commit `e0388eb`)
- CI (pass) on 2026-02-10:
  - `gh run watch 21859599119 --exit-status` (commit `02f0f62`)
- CI (pass) on 2026-02-10:
  - `gh run watch 21859632515 --exit-status` (commit `dba5e5d`)
- `.venv/bin/pytest -q tests/test_api.py tests/test_generator.py tests/test_packs.py tests/test_cli_packs_profiles.py` (pass) on 2026-02-11.
- `.venv/bin/pytest -q tests/test_providers.py tests/test_provisioning.py tests/test_blueprint.py` (pass) on 2026-02-11.
- `make check` (pass) on 2026-02-11.
- `make security` (pass) on 2026-02-11.
- `make smoke` (fail) on 2026-02-11:
  - `POST /comments` returned `400 Invalid page_id` after pack apply because the smoke script assumed seeded IDs.
- `make smoke` (fail) on 2026-02-11:
  - `GET /search/rows?q=Prototype` returned an empty set because pack rows are generated and do not guarantee that term.
- `make smoke` (pass) on 2026-02-11:
  - `make smoke` (updated script uses runtime IDs + robust row-search assertion).
- CI (pass) on 2026-02-11:
  - `gh run watch 21897223688 --exit-status` (commit `34b1084`)
- CI (pass) on 2026-02-11:
  - `gh run watch 21897263912 --exit-status` (commit `cd0dec1`)

## Mistakes And Fixes
- 2026-02-11: `make smoke` regressed after pack-apply due hard-coded seeded IDs and brittle row-search assumptions.
  - Root cause: smoke script posted comments to `page_home`/`user_alex` after replacing the DB with pack data and expected a fixed row identifier/content pattern.
  - Prevention rule: smoke tests must resolve IDs from runtime API responses after any reset/pack operation and assert on invariants, not hard-coded synthetic IDs.
  - Evidence: `scripts/demo_smoke.py`, `make smoke`.
  - Trust: `trusted (local)`
- 2026-02-09: Gitleaks secret scan failed in CI due to shallow checkout; fixed by setting `actions/checkout` `fetch-depth: 0`.
  - Root cause: gitleaks scans a git commit range on push; with depth=1 the base commit is missing and `git log` fails.
  - Prevention rule: run history-range scanners (gitleaks, release tooling) only with full history in CI.
  - Evidence: GitHub Actions failure `21812114129`, fix commit `120f3a2`.
  - Trust: `external` (failure), `local` (workflow change)
- 2026-02-09: CI flaked on `actions/checkout` fetch with GitHub HTTP 500/502/503 during full-history fetch; mitigated by reducing `fetch-depth` and rerunning CI.
  - Root cause: transient GitHub fetch errors (5xx) during `git fetch` in Actions; full-history fetches increase the surface area/time of fetch operations. (inferred)
  - Prevention rule: prefer bounded `fetch-depth` values that are sufficient for scanners, and rerun when failures are clearly infrastructure (HTTP 5xx).
  - Evidence: `gh run view 21833223544 --log-failed` (5xx on checkout), `.github/workflows/ci.yml` (`fetch-depth: 50`), `gh run watch 21833968192 --exit-status` (pass).
  - Trust: `external` (failure), `local` (workflow change)
- 2026-02-10: `make security` failed due to Bandit B608 on dynamic SQL construction in CLI DB stats; fixed by using static count queries.
  - Root cause: f-string SQL for table names triggered Bandit (even though the tables were internal and fixed).
  - Prevention rule: avoid dynamic SQL for identifiers in runtime code; keep queries static or fully validated.
  - Evidence: `src/notion_synth/cli.py`, `make security`.
  - Trust: `local`
