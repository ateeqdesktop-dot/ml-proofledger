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
