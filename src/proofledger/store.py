from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ManifestError
from .models import Manifest


@dataclass(frozen=True, slots=True)
class ManifestStore:
    path: Path

    def save(self, manifest: Manifest) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", dir=self.path.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        except OSError:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise

    def load(self) -> Manifest:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data: Any = json.load(handle)
        except FileNotFoundError as exc:
            raise ManifestError(f"manifest not found: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise ManifestError(f"manifest is not valid JSON: {exc}") from exc
        return Manifest.from_dict(data)
