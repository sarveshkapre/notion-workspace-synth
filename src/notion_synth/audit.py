from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notion_synth.util import utc_now


@dataclass
class AuditLog:
    path: Path

    @classmethod
    def open(cls, directory: str, run_id: str) -> "AuditLog":
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return cls(path / f"{run_id}.jsonl")

    def write(self, event: dict[str, Any]) -> None:
        payload = {"timestamp": utc_now(), **event}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
