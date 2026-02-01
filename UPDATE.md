# Update (2026-02-01)

## Shipped
- Added a small landing page at `/` (dark-mode aware) for quick navigation + curl snippets.
- Added `GET /stats` for dataset counts and DB path.
- Added filtering on list endpoints plus optional `X-Total-Count` via `include_total=true`.
- Added tests covering the new endpoints and `X-Total-Count` behavior.

## How to run
```bash
make setup
make dev
```

Then open:
- `http://localhost:8000/` (landing page)
- `http://localhost:8000/docs` (OpenAPI UI)

## How to verify
```bash
make check
```

## PR
If `gh` is authenticated:
```bash
git push -u origin HEAD
gh pr create --fill
```

Otherwise:
```bash
git push -u origin HEAD
```
Then open a PR from the pushed branch in GitHub UI.
