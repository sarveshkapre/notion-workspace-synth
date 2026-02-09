# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P1: Add `DELETE /workspaces/{workspace_id}` with explicit cascade semantics + audit-safe guardrails (block `ws_demo` unless forced) and API tests.
- [ ] P1: Extend row querying with exact-match operators (`property_equals`) + multi-property AND filters, keeping backward compatibility with `property_name`/`property_value_contains`.
- [ ] P1: Add focused mocked provider tests for Notion + Graph clients (retry behavior, headers, 204 handling) and one CLI-level smoke test harness.
- [ ] P2: Add DB indexes for common list/filter paths (workspace_id, created_at, foreign keys) and document optional expression indexes for JSON row properties.
- [ ] P2: Add release checklist automation (`make release-check`) to gate changelog/version/release-doc consistency.
- [ ] P2: Create `PROJECT_MEMORY.md` and `INCIDENTS.md` templates and start recording production signals, decisions, and mitigations per autonomous loop.
- [ ] P3: Add OpenAPI examples to key endpoints (create page/database/row) for better demo ergonomics.
- [ ] P3: Add a lightweight concurrency note (SQLite WAL + single-writer expectations) and a `make dev-wal` helper for local demos.

## Implemented
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

## Notes
- This file is maintained by the autonomous clone loop.

### Auto-discovered Open Checklist Items (2026-02-08)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] `make check` (validated locally on 2026-02-08)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [x] `make security` (validated locally on 2026-02-08)
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Update `docs/CHANGELOG.md`
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Tag release: `git tag v0.1.0`
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Push tags: `git push --tags`
- /Users/sarvesh/code/notion-workspace-synth/docs/RELEASE.md:- [ ] Publish GitHub release notes
