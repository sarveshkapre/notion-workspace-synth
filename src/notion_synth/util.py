from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

_NAMESPACE = uuid.UUID("3b6d8b5a-1b3b-4ed1-9c4b-1b0e6c2f4b2a")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, name))


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
