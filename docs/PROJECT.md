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
1. Add export/import fixtures for demo datasets.
2. Add request/response examples for common flows.
3. Add richer synthetic fixture packs (optional).
