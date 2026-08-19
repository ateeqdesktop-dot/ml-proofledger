from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Serialize JSON data deterministically for hashing and comparison."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def bundle_digest(manifest_data: dict[str, Any]) -> str:
    """Hash a manifest while excluding its self-referential digest field."""
    payload = dict(manifest_data)
    payload.pop("bundle_digest", None)
    return hashlib.sha256(canonical_json(payload)).hexdigest()
