PYTHON ?= python3
VENV ?= .venv
VENV_PIP := $(VENV)/bin/pip
VENV_PY := $(VENV)/bin/python
PIP := $(if $(wildcard $(VENV_PIP)),$(VENV_PIP),$(PYTHON) -m pip)
PY := $(if $(wildcard $(VENV_PY)),$(VENV_PY),$(PYTHON))

.PHONY: setup dev test lint typecheck build check security release
.PHONY: release-check

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e .[dev]

dev:
	$(PY) -m uvicorn notion_synth.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests

typecheck:
	$(PY) -m mypy src

build:
	$(PY) -m compileall src

check: lint typecheck test build

security:
	$(PY) -m bandit -r src
	$(PY) -m pip_audit

release-check:
	$(PY) scripts/release_check.py

release: release-check check
	@echo "Cut a release by tagging and updating docs/RELEASE.md"
