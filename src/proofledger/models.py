from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, cast

from .errors import ManifestError
from .evidence import EvidenceRecord

ArtifactKind = Literal["file", "directory"]


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    name: str
    path: str
    kind: ArtifactKind
    sha256: str
    size_bytes: int | None = None
    file_count: int | None = None

    def __post_init__(self) -> None:
        _require_string(self.name, "artifact.name")
        _require_string(self.path, "artifact.path")
        if self.kind not in ("file", "directory"):
            raise ManifestError("artifact.kind must be file or directory")
        if len(self.sha256) != 64 or any(char not in "0123456789abcdef" for char in self.sha256):
            raise ManifestError("artifact.sha256 must be a lowercase SHA-256 digest")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ManifestError("artifact.size_bytes must not be negative")
        if self.file_count is not None and self.file_count < 0:
            raise ManifestError("artifact.file_count must not be negative")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
            "kind": self.kind,
            "sha256": self.sha256,
        }
        if self.size_bytes is not None:
            data["size_bytes"] = self.size_bytes
        if self.file_count is not None:
            data["file_count"] = self.file_count
        return data

    @classmethod
    def from_dict(cls, data: Any) -> ArtifactRecord:
        if not isinstance(data, dict):
            raise ManifestError("artifact must be an object")
        try:
            return cls(
                name=_require_string(data.get("name"), "artifact.name"),
                path=_require_string(data.get("path"), "artifact.path"),
                kind=cast(ArtifactKind, data.get("kind")),
                sha256=_require_string(data.get("sha256"), "artifact.sha256"),
                size_bytes=data.get("size_bytes"),
                file_count=data.get("file_count"),
            )
        except TypeError as exc:
            raise ManifestError(f"invalid artifact fields: {exc}") from exc


@dataclass(frozen=True, slots=True)
class GitRecord:
    revision: str | None
    branch: str | None
    dirty: bool | None
    remote: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "branch": self.branch,
            "dirty": self.dirty,
            "remote": self.remote,
        }

    @classmethod
    def from_dict(cls, data: Any) -> GitRecord:
        if not isinstance(data, dict):
            raise ManifestError("git must be an object")
        dirty = data.get("dirty")
        if dirty is not None and not isinstance(dirty, bool):
            raise ManifestError("git.dirty must be boolean or null")
        return cls(
            revision=data.get("revision"),
            branch=data.get("branch"),
            dirty=dirty,
            remote=data.get("remote"),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentRecord:
    python_version: str
    implementation: str
    platform: str
    packages: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string(self.python_version, "environment.python_version")
        _require_string(self.implementation, "environment.implementation")
        _require_string(self.platform, "environment.platform")

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "implementation": self.implementation,
            "platform": self.platform,
            "packages": dict(sorted(self.packages.items())),
        }

    @classmethod
    def from_dict(cls, data: Any) -> EnvironmentRecord:
        if not isinstance(data, dict):
            raise ManifestError("environment must be an object")
        packages = data.get("packages", {})
        if not isinstance(packages, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in packages.items()
        ):
            raise ManifestError("environment.packages must be a string-to-string object")
        return cls(
            python_version=_require_string(
                data.get("python_version"), "environment.python_version"
            ),
            implementation=_require_string(
                data.get("implementation"), "environment.implementation"
            ),
            platform=_require_string(data.get("platform"), "environment.platform"),
            packages=dict(packages),
        )


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    name: str
    strategy: str
    seed: int | None
    counts: dict[str, int]

    def __post_init__(self) -> None:
        _require_string(self.name, "dataset_split.name")
        _require_string(self.strategy, "dataset_split.strategy")
        if any(
            not isinstance(key, str) or not isinstance(value, int) or value < 0
            for key, value in self.counts.items()
        ):
            raise ManifestError("dataset_split.counts must contain non-negative integer values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "strategy": self.strategy,
            "seed": self.seed,
            "counts": dict(sorted(self.counts.items())),
        }

    @classmethod
    def from_dict(cls, data: Any) -> DatasetSplit | None:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise ManifestError("dataset_split must be an object or null")
        counts = data.get("counts", {})
        if not isinstance(counts, dict):
            raise ManifestError("dataset_split.counts must be an object")
        return cls(
            name=_require_string(data.get("name"), "dataset_split.name"),
            strategy=_require_string(data.get("strategy"), "dataset_split.strategy"),
            seed=data.get("seed"),
            counts=dict(counts),
        )


@dataclass(frozen=True, slots=True)
class VerificationPolicy:
    require_git_revision: bool = True
    require_clean_git: bool = False
    require_python_compatibility: bool = True

    def to_dict(self) -> dict[str, bool]:
        return {
            "require_git_revision": self.require_git_revision,
            "require_clean_git": self.require_clean_git,
            "require_python_compatibility": self.require_python_compatibility,
        }

    @classmethod
    def from_dict(cls, data: Any) -> VerificationPolicy:
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ManifestError("verification_policy must be an object")
        values = {
            "require_git_revision": data.get("require_git_revision", True),
            "require_clean_git": data.get("require_clean_git", False),
            "require_python_compatibility": data.get("require_python_compatibility", True),
        }
        if not all(isinstance(value, bool) for value in values.values()):
            raise ManifestError("verification_policy values must be booleans")
        return cls(**values)


@dataclass(frozen=True, slots=True)
class Manifest:
    schema_version: str
    run_id: str
    created_at: str
    root: str
    command: tuple[str, ...]
    git: GitRecord
    environment: EnvironmentRecord
    parameters: dict[str, Any]
    metrics: dict[str, float]
    dataset_split: DatasetSplit | None
    inputs: tuple[ArtifactRecord, ...]
    outputs: tuple[ArtifactRecord, ...]
    evidence: tuple[EvidenceRecord, ...] = field(default_factory=tuple)
    bundle_digest: str | None = None
    verification_policy: VerificationPolicy = field(default_factory=VerificationPolicy)

    def __post_init__(self) -> None:
        if self.schema_version not in ("1.0", "1.1"):
            raise ManifestError("unsupported schema_version; expected 1.0 or 1.1")
        _require_string(self.run_id, "run_id")
        _require_string(self.created_at, "created_at")
        _require_string(self.root, "root")
        if not self.command:
            raise ManifestError("command must contain at least one argument")
        if any(
            not isinstance(value, (int, float)) or isinstance(value, bool)
            for value in self.metrics.values()
        ):
            raise ManifestError("metrics values must be numeric")
        names = [artifact.name for artifact in (*self.inputs, *self.outputs)]
        if len(names) != len(set(names)):
            raise ManifestError("artifact names must be unique across inputs and outputs")
        evidence_ids = [item.id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ManifestError("evidence ids must be unique")
        if self.bundle_digest is not None and (
            len(self.bundle_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.bundle_digest)
        ):
            raise ManifestError("bundle_digest must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "root": self.root,
            "command": list(self.command),
            "git": self.git.to_dict(),
            "environment": self.environment.to_dict(),
            "parameters": self.parameters,
            "metrics": dict(sorted(self.metrics.items())),
            "dataset_split": self.dataset_split.to_dict() if self.dataset_split else None,
            "inputs": [artifact.to_dict() for artifact in self.inputs],
            "outputs": [artifact.to_dict() for artifact in self.outputs],
            "evidence": [item.to_dict() for item in self.evidence],
            "bundle_digest": self.bundle_digest,
            "verification_policy": self.verification_policy.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Any) -> Manifest:
        if not isinstance(data, dict):
            raise ManifestError("manifest must be a JSON object")
        required = (
            "schema_version",
            "run_id",
            "created_at",
            "root",
            "command",
            "git",
            "environment",
            "inputs",
            "outputs",
        )
        missing = [field for field in required if field not in data]
        if missing:
            raise ManifestError(f"manifest is missing required fields: {', '.join(missing)}")
        command = data.get("command")
        if not isinstance(command, list) or not all(
            isinstance(value, str) and value for value in command
        ):
            raise ManifestError("command must be a non-empty list of strings")
        raw_inputs = data.get("inputs")
        raw_outputs = data.get("outputs")
        if not isinstance(raw_inputs, list) or not isinstance(raw_outputs, list):
            raise ManifestError("inputs and outputs must be arrays")
        return cls(
            schema_version=_require_string(data.get("schema_version"), "schema_version"),
            run_id=_require_string(data.get("run_id"), "run_id"),
            created_at=_require_string(data.get("created_at"), "created_at"),
            root=_require_string(data.get("root"), "root"),
            command=tuple(command),
            git=GitRecord.from_dict(data.get("git")),
            environment=EnvironmentRecord.from_dict(data.get("environment")),
            parameters=data.get("parameters", {}),
            metrics=data.get("metrics", {}),
            dataset_split=DatasetSplit.from_dict(data.get("dataset_split")),
            inputs=tuple(ArtifactRecord.from_dict(value) for value in raw_inputs),
            outputs=tuple(ArtifactRecord.from_dict(value) for value in raw_outputs),
            evidence=tuple(EvidenceRecord.from_dict(value) for value in data.get("evidence", [])),
            bundle_digest=data.get("bundle_digest"),
            verification_policy=VerificationPolicy.from_dict(data.get("verification_policy")),
        )
