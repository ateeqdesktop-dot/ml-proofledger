from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from proofledger.cli import main


def test_cli_capture_verify_and_show(tmp_path: Path, capsys) -> None:
    (tmp_path / "data.csv").write_text("x,y\n1,1\n", encoding="utf-8")
    (tmp_path / "model.bin").write_bytes(b"model")
    manifest = tmp_path / "proofledger.json"

    assert (
        main(
            [
                "capture",
                "--root",
                str(tmp_path),
                "--manifest",
                str(manifest),
                "--command",
                "python",
                "train.py",
                "--input",
                "data=data.csv",
                "--output",
                "model=model.bin",
                "--metric",
                "accuracy=1.0",
                "--allow-dirty",
                "--no-git-revision",
            ]
        )
        == 0
    )
    capture_output = capsys.readouterr().out
    assert json.loads(capture_output)["ok"] is True

    assert main(["verify", "--root", str(tmp_path), "--manifest", str(manifest), "--json"]) == 0
    verify_output = capsys.readouterr().out
    assert json.loads(verify_output)["ok"] is True

    assert main(["show", "--manifest", str(manifest)]) == 0
    assert "run_id:" in capsys.readouterr().out


def test_cli_rejects_invalid_artifact_syntax(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "capture",
            "--root",
            str(tmp_path),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--command",
            "python",
            "train.py",
            "--input",
            "not-a-pair",
        ]
    )

    assert result == 2
    assert "expected NAME=PATH" in capsys.readouterr().err


def test_installed_entrypoint_help_is_available(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "proofledger.cli", "--help"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "capture" in result.stdout


def test_cli_captures_evidence_and_bundle_digest(tmp_path: Path, capsys) -> None:
    (tmp_path / "data.txt").write_text("fixture", encoding="utf-8")
    manifest = tmp_path / "proofledger.json"
    evidence = json.dumps(
        {
            "id": "eval-1",
            "kind": "evaluation",
            "statement": "fixture passed",
            "decision": "accept",
            "confidence": 0.99,
        }
    )
    assert (
        main(
            [
                "capture",
                "--root",
                str(tmp_path),
                "--manifest",
                str(manifest),
                "--command",
                "python",
                "run.py",
                "--input",
                "data=data.txt",
                "--evidence",
                evidence,
                "--allow-dirty",
                "--no-git-revision",
            ]
        )
        == 0
    )
    capsys.readouterr()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.1"
    assert data["evidence"][0]["decision"] == "accept"
    assert len(data["bundle_digest"]) == 64
    assert main(["verify", "--root", str(tmp_path), "--manifest", str(manifest)]) == 0
    assert "VERIFIED" in capsys.readouterr().out


def test_published_schema_accepts_captured_manifest(tmp_path: Path) -> None:
    from jsonschema import validate

    (tmp_path / "data.txt").write_text("schema-fixture", encoding="utf-8")
    manifest = tmp_path / "proofledger.json"
    assert (
        main(
            [
                "capture",
                "--root",
                str(tmp_path),
                "--manifest",
                str(manifest),
                "--command",
                "python",
                "run.py",
                "--input",
                "data=data.txt",
                "--allow-dirty",
                "--no-git-revision",
            ]
        )
        == 0
    )
    schema_path = Path(__file__).parents[1] / "schemas" / "proofledger-1.1.schema.json"
    validate(
        json.loads(manifest.read_text(encoding="utf-8")),
        json.loads(schema_path.read_text(encoding="utf-8")),
    )
