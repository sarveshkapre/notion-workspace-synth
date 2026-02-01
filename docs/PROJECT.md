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
1. Add filtering on pages/databases by parent.
2. Add export/import fixtures for demo datasets.
3. Add pagination metadata in list responses.
