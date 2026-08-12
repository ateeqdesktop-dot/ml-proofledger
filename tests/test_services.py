from __future__ import annotations

import json
import subprocess
from pathlib import Path

from proofledger.context import EnvironmentCollector
from proofledger.models import DatasetSplit, VerificationPolicy
from proofledger.services import ArtifactSpec, CaptureService, VerifyService
from proofledger.store import ManifestStore


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "ProofLedger Test"], cwd=path, check=True)
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "test: create fixture"], cwd=path, check=True)


def test_capture_store_and_verify_success(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "dataset.csv").write_text("x,y\n1,1\n", encoding="utf-8")
    (tmp_path / "model.bin").write_bytes(b"trained-model")
    manifest_path = tmp_path / "evidence.json"
    service = CaptureService(tmp_path, EnvironmentCollector())

    manifest = service.capture(
        command=["python", "train.py"],
        inputs=[ArtifactSpec("dataset", "dataset.csv")],
        outputs=[ArtifactSpec("model", "model.bin")],
        parameters={"seed": 7, "learning_rate": 0.1},
        metrics={"accuracy": 1.0},
        dataset_split=DatasetSplit("fixture", "fixed", 7, {"train": 1, "test": 1}),
        policy=VerificationPolicy(require_clean_git=False),
    )
    ManifestStore(manifest_path).save(manifest)

    result = VerifyService(tmp_path, EnvironmentCollector()).verify(
        ManifestStore(manifest_path).load(), manifest_path
    )

    assert result.ok
    assert result.checked_artifacts == 2
    assert result.issues == ()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["schema_version"] == "1.0"


def test_verify_reports_tampered_artifact(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "data.txt").write_text("before", encoding="utf-8")
    manifest_path = tmp_path / "evidence.json"
    manifest = CaptureService(tmp_path, EnvironmentCollector()).capture(
        command=["python", "run.py"],
        inputs=[ArtifactSpec("data", "data.txt")],
        outputs=[],
        policy=VerificationPolicy(require_clean_git=False),
    )
    ManifestStore(manifest_path).save(manifest)
    (tmp_path / "data.txt").write_text("after", encoding="utf-8")

    result = VerifyService(tmp_path, EnvironmentCollector()).verify(manifest, manifest_path)

    assert not result.ok
    assert {issue.code for issue in result.issues} == {
        "ARTIFACT_HASH_MISMATCH",
        "ARTIFACT_SIZE_MISMATCH",
    }


def test_verify_reports_missing_artifact(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "data.txt").write_text("before", encoding="utf-8")
    manifest_path = tmp_path / "evidence.json"
    manifest = CaptureService(tmp_path, EnvironmentCollector()).capture(
        command=["python", "run.py"],
        inputs=[ArtifactSpec("data", "data.txt")],
        outputs=[],
        policy=VerificationPolicy(require_clean_git=False),
    )
    ManifestStore(manifest_path).save(manifest)
    (tmp_path / "data.txt").unlink()

    result = VerifyService(tmp_path, EnvironmentCollector()).verify(manifest, manifest_path)

    assert not result.ok
    assert result.issues[0].code == "MISSING_OR_UNREADABLE_PATH"
