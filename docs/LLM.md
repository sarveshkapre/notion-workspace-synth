# LLM enrichment

LLM enrichment is optional. It generates richer synthetic text and writes it back into the blueprint,
so subsequent applies are deterministic. The CLI uses the Responses API with `text.format` for structured JSON.

## Usage
```bash
notion-synth llm enrich blueprint.json \
  --output blueprint.enriched.json \
  --cache-dir .cache/llm \
  --model gpt-5.2
```

Environment:
- `OPENAI_API_KEY` (required unless `--api-key` is provided)
- `OPENAI_BASE_URL` (optional)

## Notes
- Only synthetic inputs are sent to the LLM.
- Cached responses are stored in `.cache/llm/`.
