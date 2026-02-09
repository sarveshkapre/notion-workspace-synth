# Incidents: Notion Workspace Synth

This file records real failures/regressions and the prevention rules adopted after fixing them.

## 2026-02-08: CI failed due to hard `.venv` dependency in Make targets
- Impact: GitHub Actions runs failed before lint/tests, masking additional quality issues.
- Detection: CI failures on `main` between 2026-02-01 and 2026-02-03 (GitHub Actions).
- Root cause: `make check` invoked `.venv/bin/python` even when CI installed dependencies into the runner Python (no `.venv` present).
- Fix: Makefile now falls back to environment `python3` when `.venv` is absent; regression coverage added.
- Prevention rules:
  - Keep a test that exercises Makefile fallback behavior (`tests/test_makefile.py`).
  - Prefer `$(PY)` indirection for Makefile commands instead of hard-coded venv paths.
  - Treat “fails before tests run” as a high-priority failure class.
- Evidence: `Makefile`, `tests/test_makefile.py`.
- Trust: `local` (fix + tests), `external` (initial failures in GitHub Actions history)

