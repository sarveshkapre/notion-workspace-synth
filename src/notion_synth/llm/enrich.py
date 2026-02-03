from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from notion_synth.blueprint_models import BlockSpec, Blueprint
from notion_synth.util import stable_hash, utc_now


class LlmError(RuntimeError):
    pass


def enrich_blueprint(
    blueprint: Blueprint,
    *,
    model: str,
    cache_dir: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> Blueprint:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise LlmError("OPENAI_API_KEY is required for LLM enrichment.")
    base = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    enriched_pages = []
    for page in blueprint.notion_plan.pages:
        if not _should_enrich(page.title):
            enriched_pages.append(page)
            continue
        prompt = _build_prompt(blueprint.company, page.title)
        cache_key = stable_hash({"model": model, "prompt": prompt})
        cached = cache_path / f"{cache_key}.json"
        if cached.exists():
            payload = json.loads(cached.read_text())
        else:
            payload = _call_openai(base, key, model, prompt)
            cached.write_text(json.dumps(payload, indent=2))
        extra_blocks = _extract_blocks(payload)
        enriched_pages.append(
            page.model_copy(
                update={
                    "blocks": page.blocks
                    + [BlockSpec(type="paragraph", text=block) for block in extra_blocks]
                }
            )
        )

    return blueprint.model_copy(
        update={
            "generated_at": utc_now(),
            "notion_plan": blueprint.notion_plan.model_copy(update={"pages": enriched_pages}),
        }
    )


def _call_openai(base_url: str, api_key: str, model: str, prompt: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "notion_enrichment",
                    "schema": {
                        "type": "object",
                        "properties": {"append_blocks": {"type": "array", "items": {"type": "string"}}},
                        "required": ["append_blocks"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            }
        },
    }
    response = httpx.post(
        f"{base_url}/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if response.status_code == 400:
        try:
            detail = response.json()
        except Exception:
            detail = {}
        if "json_schema" in str(detail) or "response_format" in str(detail) or "format" in str(detail):
            payload["text"]["format"] = {"type": "json_object"}
            response = httpx.post(
                f"{base_url}/responses",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
    response.raise_for_status()
    return response.json()


def _extract_blocks(payload: dict[str, Any]) -> list[str]:
    if "output_text" in payload:
        text = payload.get("output_text")
        if isinstance(text, str):
            try:
                parsed = json.loads(text)
                blocks = parsed.get("append_blocks", [])
                if isinstance(blocks, list):
                    return [str(item) for item in blocks][:4]
            except Exception:
                return []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "")
                try:
                    parsed = json.loads(text)
                    blocks = parsed.get("append_blocks", [])
                    if isinstance(blocks, list):
                        return [str(item) for item in blocks][:4]
                except Exception:
                    continue
            if content.get("type") == "output_json":
                parsed = content.get("json", {})
                blocks = parsed.get("append_blocks", [])
                if isinstance(blocks, list):
                    return [str(item) for item in blocks][:4]
    return []


def _should_enrich(title: str) -> bool:
    needles = ["KB", "Incident", "Design", "Sync", "Runbook", "Postmortem"]
    return any(token.lower() in title.lower() for token in needles)


def _build_prompt(company: str, title: str) -> str:
    return (
        f"You are generating synthetic Notion page content for {company}. "
        f"Produce 3 concise paragraph lines for the page titled '{title}'. "
        "Return JSON with key append_blocks (array of strings)."
    )
