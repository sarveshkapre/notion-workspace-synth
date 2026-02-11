# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P1: Add ingest API v2 for partial fixtures with strict unknown-field rejection mode and explicit merge conflict reporting.
  Score: Impact 4 | Effort 4 | Strategic Fit 5 | Differentiation 3 | Risk 3 | Confidence 3
- [ ] P1: Enforce payload size guardrails for large JSON blobs (`content`, row properties, comments) with clear 400 validation messages.
  Score: Impact 4 | Effort 2 | Strategic Fit 5 | Differentiation 2 | Risk 2 | Confidence 4
- [ ] P1: Add regression tests for FTS/unavailable-FTS fallback paths covering search correctness and stable ordering.
  Score: Impact 3 | Effort 2 | Strategic Fit 4 | Differentiation 2 | Risk 1 | Confidence 4
- [ ] P2: Expand synthetic data beyond engineering with `sales_cs` and `marketing` generator profiles and profile-specific databases/pages.
  Score: Impact 4 | Effort 4 | Strategic Fit 4 | Differentiation 4 | Risk 3 | Confidence 3
- [ ] P2: Fixture packs v2 with explicit scale presets (`small`/`medium`/`large`) and deterministic `--company`/`--seed` overrides in API + CLI docs.
  Score: Impact 4 | Effort 3 | Strategic Fit 4 | Differentiation 3 | Risk 2 | Confidence 4
- [ ] P2: Add optional audit log records for admin operations (`/admin/reset`, `/admin/apply-pack`) to improve demo traceability.
  Score: Impact 3 | Effort 2 | Strategic Fit 4 | Differentiation 3 | Risk 2 | Confidence 4
- [ ] P2: Add CI smoke job that runs `make smoke` to keep runnable demo path green in GitHub Actions.
  Score: Impact 3 | Effort 2 | Strategic Fit 4 | Differentiation 2 | Risk 2 | Confidence 4
- [ ] P2: Add command-level CLI tests for failure modes (missing `--confirm`, unknown pack/profile, bad import mode).
  Score: Impact 3 | Effort 2 | Strategic Fit 4 | Differentiation 2 | Risk 1 | Confidence 5
- [ ] P2: Add JSON expression indexes for frequent row-property exact-match filters and measure query improvements.
  Score: Impact 3 | Effort 2 | Strategic Fit 4 | Differentiation 2 | Risk 2 | Confidence 3
- [ ] P2: Add API docs page in `docs/` for search semantics and expected fallback behavior (FTS vs LIKE).
  Score: Impact 3 | Effort 1 | Strategic Fit 3 | Differentiation 2 | Risk 1 | Confidence 5
- [ ] P2: Add minimal rate-limit simulation mode for local clients (per-process token bucket) behind env guard for resilience testing.
  Score: Impact 3 | Effort 3 | Strategic Fit 3 | Differentiation 4 | Risk 3 | Confidence 3
- [ ] P3: Normalize repeated query-building logic into small reusable helpers to reduce drift between list endpoints.
  Score: Impact 2 | Effort 2 | Strategic Fit 3 | Differentiation 1 | Risk 1 | Confidence 4
- [ ] P3: Add focused benchmarks for list/search endpoints against small/medium/large packs and track results in docs.
  Score: Impact 2 | Effort 3 | Strategic Fit 3 | Differentiation 2 | Risk 2 | Confidence 3
- [ ] P3: Add SQLite pragmas doc matrix for demo-safe defaults (`busy_timeout`, WAL) and expected concurrency behavior.
  Score: Impact 2 | Effort 1 | Strategic Fit 3 | Differentiation 1 | Risk 1 | Confidence 5
- [ ] P3: Add OpenAPI examples for admin pack apply and fixture merge conflict responses.
  Score: Impact 2 | Effort 1 | Strategic Fit 2 | Differentiation 1 | Risk 1 | Confidence 5
- [ ] P3: Add release checklist automation for tagging + changelog consistency hints (dry-run only).
  Score: Impact 2 | Effort 2 | Strategic Fit 3 | Differentiation 1 | Risk 2 | Confidence 4

## Implemented
- [x] 2026-02-11: Add synthetic attachment metadata across pages/comments (API create/read/update, fixture import/export, deterministic generator output, and seed defaults).
  Evidence: `src/notion_synth/models.py`, `src/notion_synth/db.py`, `src/notion_synth/routes.py`, `src/notion_synth/fixtures.py`, `src/notion_synth/generator.py`, `tests/test_api.py`, `tests/test_generator.py`.
- [x] 2026-02-11: Add richer search endpoints beyond pages (`GET /search/comments`, `GET /search/rows`) with `include_total` and `include_pagination` support.
  Evidence: `src/notion_synth/routes.py`, `tests/test_api.py`, `README.md`, `scripts/demo_smoke.py`.
- [x] 2026-02-10: Add CLI `packs` commands (`notion-synth packs list`, `notion-synth packs apply`) that operate on the local DB without running the API server (with `--dry-run` preview + `--confirm` guard).
  Evidence: `src/notion_synth/cli.py`, `tests/test_cli_packs_profiles.py`, `README.md`.
- [x] 2026-02-10: Add CLI discoverability for generator profiles (`notion-synth profiles list`) and document recommended pack/profile usage in README.
  Evidence: `src/notion_synth/cli.py`, `tests/test_cli_packs_profiles.py`, `README.md`.
- [x] 2026-02-10: Add a runnable demo smoke script (`make smoke`) that starts the server, applies a pack, and hits core endpoints end-to-end.
  Evidence: `scripts/demo_smoke.py`, `Makefile`, `make smoke`.
- [x] 2026-02-10: Document Docker Compose healthcheck and first-run seeding expectations.
  Evidence: `docker-compose.yml`, `README.md`.
- [x] 2026-02-09: Add fixture packs: `GET /packs` plus admin-gated `POST /admin/apply-pack` (supports `dry_run=true` and `confirm=true`) to generate + replace the local DB with a realistic preset dataset.
  Evidence: `src/notion_synth/packs.py`, `src/notion_synth/routes.py`, `tests/test_packs.py`, smoke curl.
- [x] 2026-02-09: Add `X-Request-Id` header on all responses, plus opt-in structured error responses (via `Accept: application/vnd.notion-synth.error+json` or `?error_format=structured`) without breaking default FastAPI error shapes.
  Evidence: `src/notion_synth/errors.py`, `src/notion_synth/main.py`, `tests/test_errors.py`, smoke curl.
- [x] 2026-02-09: Add Docker Compose for local demos (API + persisted SQLite volume) and document “safe demo” guidance (localhost binding by default).
  Evidence: `docker-compose.yml`, `README.md`, `docs/SECURITY.md`, `make check`.
- [x] 2026-02-09: Add optional CORS support for local browser demo UIs (env-configured origins; default off) and expose paging metadata headers for frontend clients.
  Evidence: `src/notion_synth/main.py`, `tests/test_cors.py`, `README.md`, `docs/PROJECT.md`, `make check`.
- [x] 2026-02-09: Add request/response examples in docs for list filters + paging patterns (`include_total`, `include_pagination`, row filter operators).
  Evidence: `README.md`, `docs/ROADMAP.md`.
- [x] 2026-02-09: Added env-guarded admin reset endpoint (`POST /admin/reset?confirm=true`) to wipe the DB and restore seeded demo data for deterministic demos.
  Evidence: `src/notion_synth/routes.py` (`POST /admin/reset`), `src/notion_synth/db.py::seed_demo(force=True)`, `tests/test_api.py::test_admin_reset_confirm_wipes_and_reseeds`, `README.md`.
- [x] 2026-02-09: Added opt-in fault injection middleware for demos/tests (`NOTION_SYNTH_FAULT_INJECTION=1` + `delay_ms` / `fail_rate` / `fail_status` query params).
  Evidence: `src/notion_synth/fault_injection.py`, `src/notion_synth/main.py`, `tests/test_fault_injection.py`, `README.md`.
- [x] 2026-02-09: Added `GET /search/pages?q=...` page search endpoint with best-effort SQLite FTS5 backing (fallback to `LIKE` scans).
  Evidence: `src/notion_synth/db.py` (FTS setup), `src/notion_synth/routes.py` (`GET /search/pages`), `tests/test_api.py::test_search_pages`, `README.md`.
- [x] 2026-02-09: Added paging metadata headers for list endpoints (`include_pagination=true`), including `Link: <...>; rel="next"`.
  Evidence: `src/notion_synth/routes.py` (pagination headers), `tests/test_api.py::test_list_pages_pagination_headers`, `README.md`.
- [x] 2026-02-09: Tracked repo-root `AGENTS.md` autonomous engineering contract and refreshed the task backlog for cycle 1.
  Evidence: `AGENTS.md`, `CLONE_FEATURES.md`.
- [x] 2026-02-09: Fixed CI secret scan reliability by fetching full git history for gitleaks (`actions/checkout` `fetch-depth: 0`).
  Evidence: `.github/workflows/ci.yml`.
- [x] 2026-02-09: Added `dry_run=true` preview for `DELETE /workspaces/{workspace_id}` returning dependency counts and required flags without mutation.
  Evidence: `src/notion_synth/routes.py` (`DELETE /workspaces/{workspace_id}`), `src/notion_synth/models.py::WorkspaceDeletePreview`, `tests/test_api.py::test_delete_demo_workspace_requires_force`.
- [x] 2026-02-09: Added OpenAPI request examples for common write payloads (workspaces/users/pages/databases/rows/comments).
  Evidence: `src/notion_synth/models.py` (Pydantic `json_schema_extra` examples), `/docs` rendering.
- [x] 2026-02-09: Added SQLite concurrency ergonomics: default `busy_timeout`, opt-in WAL via `NOTION_SYNTH_SQLITE_WAL=1`, plus `make dev-wal` helper; documented expected single-writer behavior.
  Evidence: `src/notion_synth/db.py`, `Makefile` (`dev-wal`), `README.md`, `docs/PROJECT.md`.
- [x] 2026-02-09: Added guarded workspace deletion endpoint with explicit cascade semantics and demo-workspace protection.
  Evidence: `src/notion_synth/routes.py` (`DELETE /workspaces/{workspace_id}`), `tests/test_api.py::test_delete_workspace_requires_cascade_and_cascades`.
- [x] 2026-02-09: Extended row querying with exact-match operators (`property_value_equals`, repeatable `property_equals`) and multi-property AND filtering.
  Evidence: `src/notion_synth/routes.py` (`GET /databases/{database_id}/rows`), `tests/test_api.py::test_database_rows_filtering_and_total_header`.
- [x] 2026-02-09: Added mocked provider tests for Notion + Graph clients plus CLI `generate` smoke coverage.
  Evidence: `tests/test_providers.py`, `make check`.
- [x] 2026-02-09: Added SQLite indexes for common list/filter paths and documented JSON expression indexing.
  Evidence: `src/notion_synth/db.py`, `docs/PROJECT.md`.
- [x] 2026-02-09: Added release gating via `make release-check` and aligned `docs/RELEASE.md` + `CHANGELOG.md` with `0.2.0`.
  Evidence: `scripts/release_check.py`, `Makefile`, `docs/RELEASE.md`, `CHANGELOG.md`.
- [x] 2026-02-09: Added `PROJECT_MEMORY.md` + `INCIDENTS.md` templates to preserve decisions and operational learnings.
  Evidence: `PROJECT_MEMORY.md`, `INCIDENTS.md`.
- [x] 2026-02-08: Fixed CI bootstrap failure by making `Makefile` targets fall back to environment Python when `.venv` is absent.
  Evidence: `Makefile`, `tests/test_makefile.py`, GH run root-cause from `https://github.com/sarveshkapre/notion-workspace-synth/actions/runs/21636365616`.
- [x] 2026-02-08: Restored quality gate health (`ruff`, `mypy`, `bandit`, `pip-audit`) by resolving baseline lint/type issues and tightening safety annotations.
  Evidence: `pyproject.toml`, `src/notion_synth/cli.py`, `src/notion_synth/providers/notion/client.py`, `src/notion_synth/providers/entra/graph.py`, `src/notion_synth/llm/enrich.py`.
- [x] 2026-02-08: Added user/comment lifecycle coverage with safe delete semantics.
  Evidence: `src/notion_synth/routes.py` (`DELETE /users/{user_id}`, `GET /comments/{comment_id}`, `DELETE /comments/{comment_id}`), `tests/test_api.py`.
- [x] 2026-02-08: Added filtered row querying for `GET /databases/{database_id}/rows` with `property_name` and `property_value_contains`.
  Evidence: `src/notion_synth/routes.py`, `tests/test_api.py::test_database_rows_filtering_and_total_header`.
- [x] 2026-02-08: Updated product/docs memory for shipped behavior and next priorities.
  Evidence: `README.md`, `PLAN.md`, `docs/PROJECT.md`, `CHANGELOG.md`.

## Insights
- CI was failing before lint/tests because workflow installed into system Python while `make check` hard-required `.venv/bin/python`; this masked additional quality gate issues.
- The repo had latent lint/type/security drift that was not visible until CI bootstrap was fixed; keeping the fallback path tested avoids similar blind spots.
- Provider-heavy CLI dispatch benefits from strict branch-local variable naming; shared names across command branches caused most mypy false conflicts.
- CI on `main` is green as of 2026-02-08/2026-02-09; the earlier failures in early February are now addressed by shipped fixes and regression tests.
- CI secret scans can fail with shallow clones because gitleaks scans commit ranges on push; use `fetch-depth: 0` for reliable history-range scanning.
- Market scan (bounded): mock API tools in this segment emphasize OpenAPI-first ergonomics, rule-based matching, dynamic templating, proxying, and opt-in failure simulation (examples: https://mockoon.com/docs/latest/ and https://mockoon.com/mock-samples/notion-api/).
- Market scan (bounded): Mockoon treats dynamic response templating and scoped variables/data buckets as a baseline capability for realistic synthetic payloads, which aligns with continuing investment in deterministic-yet-realistic fixture generation (https://mockoon.com/docs/latest/templating/mockoon-variables/).
- Market scan (bounded): Mockoon route-response rules highlight configurable latency and conditional response behavior as expected ergonomics for API simulation workflows (https://mockoon.com/docs/latest/routes/response/).
- Market scan (bounded): WireMock highlights explicit fault/latency injection as a first-class mocking feature (e.g. fixed delays, jitter distributions, chunked responses), reinforcing the value of an env-guarded `delay_ms`/`fail_rate` feature for demos/tests (https://wiremock.org/docs/simulating-faults/).
- Market scan (bounded): Prism positions OpenAPI-driven dynamic mock responses plus request/response validation as baseline expectations for API-mocking workflows (https://stoplight.io/open-source/prism).
- Market scan (bounded): Self-hosted mock tools commonly ship Docker images and document container networking gotchas (e.g., Prism notes `-h 0.0.0.0` is required for reachability from outside the container), reinforcing the value of “safe by default” localhost bindings in demo Compose stacks (https://hub.docker.com/r/stoplight/prism/).
- Market scan (bounded): Mockoon’s CLI supports headless Docker runs as a baseline workflow, reinforcing “docker compose up” as a familiar on-ramp for API mocking/demo products (https://mockoon.com/cli/).
- Market scan (bounded): Postman mock servers support simulated delay via `x-mock-response-delay` for response simulation/testing workflows (https://learning.postman.com/docs/designing-and-developing-your-api/mocking-data/mocking-with-examples/).
- Market scan (bounded): Notion’s public API documents a request limit of 3 requests per second per integration (https://developers.notion.com/reference/request-limits).
- Gap map:
  Missing: ingest API v2 (partial fixture + strict unknown-field rejection), non-engineering generator profiles, and explicit CI smoke workflow job.
  Weak: search relevance ranking for comments/rows (currently LIKE-based); fixture ingest validation depth for partially trusted external payloads.
  Parity (now improved): attachment metadata on pages/comments, cross-entity search endpoints, fixtures import/export, seeded demo data, list filtering/pagination metadata, admin reset, fault injection, Docker on-ramp.
  Differentiator: deterministic enterprise dataset generator + Entra/Notion apply workflows.

## Notes
- This file is maintained by the autonomous clone loop.

### Auto-discovered Open Checklist Items (2026-02-09)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] `make check` (validated locally on 2026-02-09)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] `make security` (validated locally on 2026-02-09)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] `make release-check` (validated locally on 2026-02-09)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] Update `CHANGELOG.md` (updated on 2026-02-09)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Tag release: `git tag v0.2.0`
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Push tags: `git push --tags`
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Publish GitHub release notes
