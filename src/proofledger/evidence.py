from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EvidenceDecision = Literal["accept", "review", "reject"]


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """A reviewable claim attached to an AI/ML run."""

    id: str
    kind: str
    statement: str
    decision: EvidenceDecision = "review"
    confidence: float | None = None
    source: str | None = None
    artifact: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.kind.strip() or not self.statement.strip():
            raise ValueError("evidence id, kind, and statement must be non-empty")
        if self.decision not in ("accept", "review", "reject"):
            raise ValueError("evidence decision must be accept, review, or reject")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "statement": self.statement,
            "decision": self.decision,
        }
        if self.confidence is not None:
            data["confidence"] = self.confidence
        if self.source is not None:
            data["source"] = self.source
        if self.artifact is not None:
            data["artifact"] = self.artifact
        return data

    @classmethod
    def from_dict(cls, data: Any) -> EvidenceRecord:
        if not isinstance(data, dict):
            raise ValueError("evidence must be an object")
        return cls(
            id=str(data.get("id", "")),
            kind=str(data.get("kind", "")),
            statement=str(data.get("statement", "")),
            decision=data.get("decision", "review"),
            confidence=data.get("confidence"),
            source=data.get("source"),
            artifact=data.get("artifact"),
        )
