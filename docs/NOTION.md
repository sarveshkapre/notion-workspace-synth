# Notion provider (real workspace)

## Prereqs
- Create a Notion internal integration (“Synth Bot”) and save the token.
- Create a container root page in your test workspace (e.g. `🧪 Synthetic Company Root`).
- Share the root page with the integration and set any baseline access.

## Verify users (after Entra SCIM provisioning)
```bash
notion-synth notion verify-users --roster roster.csv --token "$NOTION_TOKEN" \
  --report notion_verify_report.json
```
Use `--require-all` to return a non-zero exit code if any users are missing.

## Apply a blueprint
```bash
notion-synth notion apply blueprint.enriched.json \
  --root-page-id "$ROOT_PAGE_ID" \
  --token "$NOTION_TOKEN" \
  --state state.db \
  --audit-dir audit \
  --redact-emails
```

## Cleanup
```bash
notion-synth notion destroy --token "$NOTION_TOKEN" --state state.db --audit-dir audit
```

## Live activity
```bash
notion-synth notion activity blueprint.enriched.json \
  --token "$NOTION_TOKEN" \
  --state state.db \
  --audit-dir audit \
  --tick-minutes 15 \
  --jitter 0.3 \
  --redact-emails
```

## Notes
- The integration is the author of all changes (Notion API limitation).
- Fine-grained sharing is handled by a one-time manual share on the root page.
