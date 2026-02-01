# AGENTS

## Working agreements
- Keep the API local-first and unauthenticated.
- All new endpoints must include tests and OpenAPI docs (FastAPI handles docs).
- Avoid heavy dependencies; prefer standard library + FastAPI stack.

## Commands
- Setup: `make setup`
- Dev server: `make dev`
- Tests: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Full gate: `make check`

## Project structure
- `src/notion_synth`: application code
- `tests`: API tests
- `docs`: project documentation
