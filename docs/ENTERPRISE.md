# Enterprise usage

This project ships a local-first API plus a CLI that can generate a full synthetic engineering
workspace. The CLI is deterministic by seed, so enterprises can reproduce the same datasets across
endpoints without shipping real data or secrets.

## Recommended flow
1. Generate fixture JSON in CI or on the endpoint.
2. Import the fixture into the local SQLite DB.
3. Run the API server for integrations and demos.

```bash
notion-synth generate --company "Acme Robotics" --industry "Cloud Infrastructure" \
  --profile engineering --users 120 --teams 8 --projects 18 --incidents 12 --candidates 20 \
  --seed 2026 --output fixture.json

notion-synth import fixture.json --mode replace
make dev
```

## Safety and operational notes
- Data is local-only unless you explicitly export or share fixtures.
- The API is intentionally unauthenticated for local demo use; place it behind a VPN or reverse proxy
  if you need controls.
- Use the `--seed` flag to reproduce a known dataset for automated testing.

## LLM enrichment (optional)
The generator currently uses deterministic templates so it can run anywhere without external
dependencies. If you want richer narrative content:
- Export the fixture JSON.
- Use your preferred LLM (e.g., GPT-5.2 or a smaller variant) to post-process page content.
- Re-import the enriched fixture with `mode=replace` or `mode=merge`.

This keeps tokens and prompts out of the API runtime while letting enterprises scale content
generation safely in dedicated pipelines.
