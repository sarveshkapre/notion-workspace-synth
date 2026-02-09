# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P1 (Selected - this run): Add `dry_run=true` for `DELETE /workspaces/{workspace_id}` to return dependency counts without mutation (safer demo UX).
- [ ] P1 (Selected - this run): Add OpenAPI examples to key endpoints (create page/database/row/user/workspace) for better demo ergonomics.
- [ ] P2 (Selected - this run): Add SQLite concurrency ergonomics: default `busy_timeout`, opt-in WAL via env var, and a `make dev-wal` helper; document expected single-writer behavior.
- [ ] P2: Ensure repo-root `AGENTS.md` (autonomous engineering contract) is tracked and kept current; avoid divergence from `docs/AGENTS.md`.
- [ ] P2: Improve list endpoint pagination UX: add `Link` header or `next_offset` metadata for faster client iteration.
- [ ] P3: Add optional fault injection for demos/tests (`?delay_ms=` and/or `?fail_rate=`) with strict opt-in.
- [ ] P3: Add SQLite FTS-backed search for pages (`/search/pages?q=`) to match common Notion “search everywhere” workflows.
- [ ] P3: Add fixture “packs” (engineering/org presets) to improve realism without external dependencies.
- [ ] P3: Add a guarded reset endpoint to restore seeded demo data (`POST /admin/reset`) for deterministic demos.
- [ ] P3: Add Docker Compose for local demos (db volume + API) and document “safe demo” deployment guidance.

## Implemented
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
