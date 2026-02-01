PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: setup dev test lint typecheck build check security release

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

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

release: check
	@echo "Cut a release by tagging and updating docs/RELEASE.md"
