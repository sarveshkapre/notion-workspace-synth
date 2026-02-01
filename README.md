# Notion Workspace Synth

Synthetic Notion-like workspace API with seeded demo org. Use it to generate realistic pages, databases, and comments for demos, tests, or integrations.

## Features
- Workspaces, users, pages, databases, database rows, comments
- Deterministic demo org seeding on first run
- Simple REST API with JSON payloads
- Local-first SQLite storage (no auth required)
- Optional `X-Total-Count` totals on list endpoints (`include_total=true`)
- Built-in landing page (`/`) and dataset stats (`/stats`)

## Quickstart
```bash
make setup
make dev
```

API docs:
- OpenAPI UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Example
```bash
curl http://localhost:8000/pages
```

Totals via response header:
```bash
curl -i "http://localhost:8000/pages?include_total=true"
```

Fixtures (export/import):
```bash
curl http://localhost:8000/fixtures/export > fixture.json
curl -X POST "http://localhost:8000/fixtures/import?mode=replace" -H "content-type: application/json" --data-binary @fixture.json
curl -X POST "http://localhost:8000/fixtures/import?mode=merge" -H "content-type: application/json" --data-binary @fixture.json
```

## Configuration
- `NOTION_SYNTH_DB` (optional): path to SQLite DB file. Default: `./notion_synth.db`

## Docker
```bash
docker build -t notion-workspace-synth .
docker run --rm -p 8000:8000 notion-workspace-synth
```

## Repo docs
All repository docs (except this README) live in `docs/`.
