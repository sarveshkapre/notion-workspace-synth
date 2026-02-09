# PROJECT

## Quick commands
- Setup: `make setup`
- Dev server: `make dev`
- Docker Compose demo: `docker compose up --build`
- Test: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Full gate: `make check`
- Security: `make security`

## Environment
- Python 3.11+
- Optional: `NOTION_SYNTH_DB=./notion_synth.db`
- Optional: `NOTION_SYNTH_SQLITE_WAL=1` (enables WAL; better concurrent readers, still single-writer)
- Optional: `NOTION_SYNTH_SQLITE_BUSY_TIMEOUT_MS=5000` (default; reduces transient lock errors)
- Optional: `NOTION_SYNTH_CORS_ORIGINS=http://localhost:5173,http://localhost:3000` (enables CORS for local browser demo UIs)
- Optional: `NOTION_SYNTH_CORS_ALLOW_CREDENTIALS=1` (CORS only; default off)
- Optional: `NOTION_SYNTH_ADMIN=1` (enables admin endpoints like `POST /admin/reset?confirm=true`)
- Optional: `NOTION_SYNTH_FAULT_INJECTION=1` (enables opt-in demo fault injection via query params)

## Concurrency notes
- This is intended for local/dev usage; SQLite is effectively single-writer.
- Use WAL (`make dev-wal`) when you have multiple concurrent readers (demo UIs + background scripts).

## Performance notes
- The DB initializes a few small indexes for common `workspace_id` and FK list paths on startup.
- If you frequently filter `database_rows` by a known JSON property, SQLite can use an expression index.

Example (index rows in `db_tasks` by `Status`):
```sql
CREATE INDEX IF NOT EXISTS idx_db_tasks_status
ON database_rows (json_extract(properties_json, '$."Status"'))
WHERE database_id = 'db_tasks';
```

## API entrypoints
- Health: `GET /health`
- OpenAPI: `GET /openapi.json`
- Docs: `GET /docs`

## Next 3 improvements
1. Add fixture “packs” (engineering/org presets) to improve realism without external dependencies.
2. Add synthetic file attachments metadata (minimal shape, no blob hosting).
3. Add ingest API for external fixtures (validate + merge policies).
