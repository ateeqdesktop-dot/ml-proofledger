from __future__ import annotations

import platform
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .canonical import bundle_digest
from .context import EnvironmentCollector, GitInspector
from .errors import InputError
from .evidence import EvidenceRecord
from .hashing import hash_declared_path
from .models import (
    ArtifactRecord,
    DatasetSplit,
    Manifest,
    VerificationPolicy,
)


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    name: str
    path: str


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {"code": self.code, "message": self.message}
        if self.path is not None:
            data["path"] = self.path
        return data


@dataclass(frozen=True, slots=True)
class VerificationResult:
    ok: bool
    manifest_path: str
    checked_artifacts: int
    issues: tuple[VerificationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "manifest_path": self.manifest_path,
            "checked_artifacts": self.checked_artifacts,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class CaptureService:
    root: Path
    environment: EnvironmentCollector

    def capture(
        self,
        *,
        command: Iterable[str],
        inputs: Iterable[ArtifactSpec],
        outputs: Iterable[ArtifactSpec],
        parameters: Mapping[str, Any] | None = None,
        metrics: Mapping[str, float] | None = None,
        dataset_split: DatasetSplit | None = None,
        evidence: Iterable[EvidenceRecord] = (),
        policy: VerificationPolicy | None = None,
        run_id: str | None = None,
    ) -> Manifest:
        root = self.root.resolve()
        command_tuple = tuple(command)
        if not command_tuple or any(not value for value in command_tuple):
            raise InputError("command must contain at least one non-empty argument")
        input_specs = tuple(inputs)
        output_specs = tuple(outputs)
        artifact_specs = input_specs + output_specs
        artifact_records = tuple(self._record_artifact(spec, root) for spec in artifact_specs)
        input_records = artifact_records[: len(input_specs)]
        output_records = artifact_records[len(input_specs) :]
        if len({record.name for record in artifact_records}) != len(artifact_records):
            raise InputError("artifact names must be unique across inputs and outputs")
        manifest = Manifest(
            schema_version="1.1",
            run_id=run_id or uuid4().hex[:12],
            created_at=datetime.now(timezone.utc).isoformat(),
            root=str(root),
            command=command_tuple,
            git=GitInspector(root).inspect(),
            environment=self.environment.collect(),
            parameters=dict(parameters or {}),
            metrics={key: float(value) for key, value in (metrics or {}).items()},
            dataset_split=dataset_split,
            inputs=input_records,
            outputs=output_records,
            evidence=tuple(evidence),
            verification_policy=policy or VerificationPolicy(),
        )
        return replace(manifest, bundle_digest=bundle_digest(manifest.to_dict()))

    @staticmethod
    def _record_artifact(spec: ArtifactSpec, root: Path) -> ArtifactRecord:
        if not spec.name.strip():
            raise InputError("artifact name must not be empty")
        result = hash_declared_path(root, spec.path)
        return ArtifactRecord(
            name=spec.name,
            path=spec.path,
            kind=result.kind,  # type: ignore[arg-type]
            sha256=result.sha256,
            size_bytes=result.size_bytes,
            file_count=result.file_count if result.kind == "directory" else None,
        )


@dataclass(frozen=True, slots=True)
class VerifyService:
    root: Path
    environment: EnvironmentCollector

    def verify(self, manifest: Manifest, manifest_path: Path) -> VerificationResult:
        root = self.root.resolve()
        issues: list[VerificationIssue] = []
        if manifest.bundle_digest is not None:
            actual_digest = bundle_digest(manifest.to_dict())
            if actual_digest != manifest.bundle_digest:
                issues.append(
                    VerificationIssue(
                        "BUNDLE_DIGEST_MISMATCH",
                        "manifest contents differ from the recorded bundle digest",
                        "bundle_digest",
                    )
                )
        for item in manifest.evidence:
            if item.decision == "reject":
                issues.append(
                    VerificationIssue(
                        "EVIDENCE_REJECTED",
                        f"evidence item is explicitly rejected: {item.id}",
                        f"evidence.{item.id}",
                    )
                )
        artifacts = (*manifest.inputs, *manifest.outputs)
        for artifact in artifacts:
            try:
                current = hash_declared_path(root, artifact.path)
            except InputError as exc:
                issues.append(
                    VerificationIssue("MISSING_OR_UNREADABLE_PATH", str(exc), artifact.path)
                )
                continue
            if current.kind != artifact.kind:
                issues.append(
                    VerificationIssue(
                        "ARTIFACT_KIND_MISMATCH",
                        f"expected {artifact.kind}, found {current.kind}",
                        artifact.path,
                    )
                )
            if current.sha256 != artifact.sha256:
                issues.append(
                    VerificationIssue(
                        "ARTIFACT_HASH_MISMATCH",
                        "SHA-256 digest differs from manifest",
                        artifact.path,
                    )
                )
            if artifact.size_bytes is not None and current.size_bytes != artifact.size_bytes:
                issues.append(
                    VerificationIssue(
                        "ARTIFACT_SIZE_MISMATCH",
                        "size differs from manifest",
                        artifact.path,
                    )
                )
            if artifact.file_count is not None and current.file_count != artifact.file_count:
                issues.append(
                    VerificationIssue(
                        "ARTIFACT_FILE_COUNT_MISMATCH",
                        "file count differs from manifest",
                        artifact.path,
                    )
                )

        current_git = GitInspector(root).inspect()
        policy = manifest.verification_policy
        if policy.require_git_revision:
            if manifest.git.revision is None or current_git.revision is None:
                issues.append(
                    VerificationIssue(
                        "GIT_REVISION_UNAVAILABLE",
                        "Git revision is required but unavailable",
                    )
                )
            elif manifest.git.revision != current_git.revision:
                issues.append(
                    VerificationIssue(
                        "GIT_REVISION_MISMATCH",
                        "current Git revision differs from manifest",
                    )
                )
        if policy.require_clean_git and current_git.dirty:
            issues.append(
                VerificationIssue(
                    "GIT_WORKTREE_DIRTY",
                    "Git worktree contains tracked changes",
                )
            )
        if policy.require_python_compatibility:
            expected = _major_minor(manifest.environment.python_version)
            actual = _major_minor(platform.python_version())
            if expected is None or actual is None or expected != actual:
                issues.append(
                    VerificationIssue(
                        "PYTHON_VERSION_MISMATCH",
                        "Python major/minor version differs from manifest",
                    )
                )
        return VerificationResult(
            ok=not issues,
            manifest_path=str(manifest_path),
            checked_artifacts=len(artifacts),
            issues=tuple(issues),
        )


def _major_minor(version: str) -> tuple[int, int] | None:
    match = re.match(r"^(\d+)\.(\d+)", version)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))
