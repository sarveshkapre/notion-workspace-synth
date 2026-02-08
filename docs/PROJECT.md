# PROJECT

## Quick commands
- Setup: `make setup`
- Dev server: `make dev`
- Test: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Full gate: `make check`
- Security: `make security`

## Environment
- Python 3.11+
- Optional: `NOTION_SYNTH_DB=./notion_synth.db`

## API entrypoints
- Health: `GET /health`
- OpenAPI: `GET /openapi.json`
- Docs: `GET /docs`

## Next 3 improvements
1. Add workspace deletion endpoint with explicit cascade semantics.
2. Add richer database row query operators and indexing guidance.
3. Add mocked provider integration tests for Notion/Entra CLI commands.
