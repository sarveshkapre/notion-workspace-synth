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
1. Add workspace deletion endpoint with explicit cascade semantics.
2. Add richer database row query operators and indexing guidance.
3. Add mocked provider integration tests for Notion/Entra CLI commands.
