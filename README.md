# Notion Workspace Synth

Synthetic Notion-like workspace API with seeded demo org. Use it to generate realistic pages, databases, and comments for demos, tests, or integrations.

## Features
- Workspaces, users, pages, databases, database rows, comments
- Deterministic demo org seeding on first run
- Enterprise-grade synthetic workspace generator for engineering orgs
- Simple REST API with JSON payloads
- Local-first SQLite storage (no auth required)
- Optional `X-Total-Count` totals on list endpoints (`include_total=true`)
- Optional paging metadata on list endpoints via headers (`include_pagination=true`, including `Link: ...; rel="next"`)
- Built-in landing page (`/`) and dataset stats (`/stats`)

## Quickstart
```bash
make setup
make dev
```

API docs:
- OpenAPI UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Search:
```bash
curl "http://localhost:8000/search/pages?q=Welcome"
```

## Example
```bash
curl http://localhost:8000/pages
```

Create a workspace and a user:
```bash
curl -X POST http://localhost:8000/workspaces -H "content-type: application/json" -d '{"name":"Acme"}'
curl -X POST http://localhost:8000/users -H "content-type: application/json" -d '{"workspace_id":"ws_...","name":"Taylor","email":"taylor@example.com"}'
```

Common API flow (create + query + delete):
```bash
# 1) Create a page
curl -sS -X POST http://localhost:8000/pages \
  -H "content-type: application/json" \
  -d '{"workspace_id":"ws_demo","title":"Sprint Notes","content":{"blocks":["Kickoff"]},"parent_type":"workspace","parent_id":"ws_demo"}'
# -> {"id":"page_...","title":"Sprint Notes",...}

# 2) Create a database and row
DB_ID=$(curl -sS -X POST http://localhost:8000/databases \
  -H "content-type: application/json" \
  -d '{"workspace_id":"ws_demo","name":"Tickets","schema":{"properties":{"Title":{"type":"title"},"Status":{"type":"select"}}}}' \
  | jq -r '.id')
curl -sS -X POST "http://localhost:8000/databases/$DB_ID/rows" \
  -H "content-type: application/json" \
  -d '{"properties":{"Title":"Investigate latency","Status":"In Progress"}}'
# -> {"id":"row_...","database_id":"db_...",...}

# 3) Filter rows by property value
curl -sS "http://localhost:8000/databases/$DB_ID/rows?property_name=Status&property_value_contains=Progress"

# 4) Delete comment or user (user delete cascades authored comments)
curl -X DELETE http://localhost:8000/comments/comment_1
curl -X DELETE http://localhost:8000/users/user_alex
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

## CLI (Real Notion + Entra)
Generate a roster template:
```bash
notion-synth roster generate --seed 2026 --users 50 --output roster.csv
```

Provision Entra users + groups:
```bash
notion-synth entra apply --roster roster.csv --mode create \
  --tenant-id "$ENTRA_TENANT_ID" --client-id "$ENTRA_CLIENT_ID" --client-secret "$ENTRA_CLIENT_SECRET" \
  --company "Acme Robotics" --state state.db
```

Verify provisioning (Entra -> Notion):
```bash
notion-synth entra verify-provisioning --roster roster.csv \
  --tenant-id "$ENTRA_TENANT_ID" --client-id "$ENTRA_CLIENT_ID" --client-secret "$ENTRA_CLIENT_SECRET" \
  --token "$NOTION_TOKEN" --company "Acme Robotics" --state state.db --wait-minutes 30
```

Generate a blueprint:
```bash
notion-synth blueprint generate --company "Acme Robotics" --seed 2026 \
  --roster roster.csv --output blueprint.json --profile engineering --scale small
```

Optional LLM enrichment:
```bash
notion-synth llm enrich blueprint.json --output blueprint.enriched.json --cache-dir .cache/llm
```

Apply to Notion:
```bash
notion-synth notion apply blueprint.enriched.json --root-page-id "$ROOT_PAGE_ID" --token "$NOTION_TOKEN"
```

Validate root access:
```bash
notion-synth notion validate-root --root-page-id "$ROOT_PAGE_ID" --token "$NOTION_TOKEN"
```

Run live activity:
```bash
notion-synth notion activity blueprint.enriched.json --token "$NOTION_TOKEN" --tick-minutes 15 --jitter 0.3
```

More details: `docs/NOTION.md`, `docs/ENTRA.md`, `docs/LLM.md`

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
curl -X DELETE http://localhost:8000/comments/comment_1
curl -X DELETE http://localhost:8000/users/user_alex
```

## Configuration
- `NOTION_SYNTH_DB` (optional): path to SQLite DB file. Default: `./notion_synth.db`
- `NOTION_SYNTH_SQLITE_WAL` (optional): set to `1` to enable SQLite WAL mode (better concurrent readers; still single-writer).
- `NOTION_SYNTH_SQLITE_BUSY_TIMEOUT_MS` (optional): SQLite `busy_timeout` in ms (default: `5000`).

## Docker
```bash
docker build -t notion-workspace-synth .
docker run --rm -p 8000:8000 notion-workspace-synth
```

## Repo docs
All repository docs (except this README) live in `docs/`. See `docs/ENTERPRISE.md` for enterprise
usage guidance.
