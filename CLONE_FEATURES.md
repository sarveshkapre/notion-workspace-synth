# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P1: Add `DELETE /workspaces/{workspace_id}` with explicit cascade semantics and audit-safe guardrails.
- [ ] P1: Extend row querying with exact-match operators (`property_equals`) and multi-property filters.
- [ ] P1: Add focused mocked integration tests for Notion/Graph provider clients in CLI flows.
- [ ] P2: Add performance guidance and optional indexes for frequently filtered JSON row properties.
- [ ] P2: Prepare release checklist automation (`make release-check`) to gate changelog/version/tag consistency.

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
