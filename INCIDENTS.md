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

## 2026-02-09: CI failed in gitleaks due to shallow checkout
- Impact: CI runs failed at secret scan, blocking mainline confidence despite passing lint/tests/security locally.
- Detection: GitHub Actions run `21812114129` failed on 2026-02-09.
- Root cause: `actions/checkout` default `fetch-depth: 1` produced a shallow clone; gitleaks tried to scan a commit range (`<base>^..<head>`) and `git log` failed because the base commit was not present.
- Fix: Set `actions/checkout@v4` `fetch-depth: 0` so gitleaks can scan the push commit range reliably.
- Prevention rules:
  - Any history-range scanner (gitleaks, semantic-release, changelog tools) must run with `fetch-depth: 0` in CI.
  - Treat “tool fails due to checkout depth” as a CI configuration bug; fix workflow rather than weakening the scan.
- Evidence: `.github/workflows/ci.yml`.
- Trust: `local` (workflow change), `external` (CI failure + recovery)

## 2026-02-09: CI checkout flaked with GitHub 5xx during full-history fetch
- Impact: CI run failed before installing deps/tests, reducing confidence in mainline health.
- Detection: GitHub Actions run `21833223544` failed on 2026-02-09 at `actions/checkout`.
- Root cause: GitHub returned HTTP 500 during `git fetch` inside `actions/checkout` while fetching all branches/tags with `fetch-depth: 0`. (inferred: full-history fetch increased exposure to transient 5xx)
- Fix: Reduced `actions/checkout` `fetch-depth` to `50` and reran CI; subsequent run passed (`21833968192`).
- Prevention rules:
  - Prefer bounded `fetch-depth` values that satisfy scanners, instead of full-history fetches by default.
  - When `actions/checkout` fails with clear infrastructure HTTP 5xx, rerun before making product code changes.
- Evidence: `.github/workflows/ci.yml`, `gh run view 21833223544 --log-failed`, `gh run watch 21833968192 --exit-status`.
- Trust: `local` (workflow change), `external` (CI failure + recovery)
