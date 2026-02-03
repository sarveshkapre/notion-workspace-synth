from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notion_synth.util import utc_now


@dataclass
class AuditLog:
    path: Path
    redact_emails: bool = False

    @classmethod
    def open(cls, directory: str, run_id: str, *, redact_emails: bool = False) -> "AuditLog":
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return cls(path / f"{run_id}.jsonl", redact_emails=redact_emails)

    def write(self, event: dict[str, Any]) -> None:
        payload = {"timestamp": utc_now(), **event}
        if self.redact_emails:
            payload = redact_payload(payload)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


def redact_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return _redact_emails(payload)
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    if isinstance(payload, dict):
        return {key: redact_payload(value) for key, value in payload.items()}
    return payload


def _redact_emails(text: str) -> str:
    return _EMAIL_RE.sub("[redacted-email]", text)


_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
