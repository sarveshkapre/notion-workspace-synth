# Notion Workspace Synth

Synthetic Notion-like workspace API with seeded demo org. Use it to generate realistic pages, databases, and comments for demos, tests, or integrations.

## Features
- Workspaces, users, pages, databases, database rows, comments
- Deterministic demo org seeding on first run
- Enterprise-grade synthetic workspace generator for engineering orgs
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

Create a workspace and a user:
```bash
curl -X POST http://localhost:8000/workspaces -H "content-type: application/json" -d '{"name":"Acme"}'
curl -X POST http://localhost:8000/users -H "content-type: application/json" -d '{"workspace_id":"ws_...","name":"Taylor","email":"taylor@example.com"}'
```

## CLI (Enterprise Synth)
Generate a full engineering workspace with multiple users, pages, and databases:
```bash
notion-synth generate --company "Acme Robotics" --industry "Cloud Infrastructure" --profile engineering \
  --users 120 --teams 8 --projects 18 --incidents 12 --candidates 20 \
  --seed 2026 --output fixture.json
```

Seed the local database directly (replace or merge):
```bash
notion-synth seed --company "Acme Robotics" --mode replace --users 120 --teams 8
```

Import or export fixtures:
```bash
notion-synth export --output fixture.json
notion-synth import fixture.json --mode merge
```

Profiles are deterministic by seed, so enterprise users can reproduce datasets at scale without
shipping any real data.

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

Update/delete:
```bash
curl -X PATCH http://localhost:8000/databases/db_tasks -H "content-type: application/json" -d '{"name":"Task Board v2"}'
curl -X DELETE http://localhost:8000/pages/page_home
```

## Configuration
- `NOTION_SYNTH_DB` (optional): path to SQLite DB file. Default: `./notion_synth.db`

## Docker
```bash
docker build -t notion-workspace-synth .
docker run --rm -p 8000:8000 notion-workspace-synth
```

## Repo docs
All repository docs (except this README) live in `docs/`. See `docs/ENTERPRISE.md` for enterprise
usage guidance.
