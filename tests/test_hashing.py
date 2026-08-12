from __future__ import annotations

from pathlib import Path

import pytest

from proofledger.errors import InputError
from proofledger.hashing import hash_declared_path


def test_file_hash_is_stable_and_reports_size(tmp_path: Path) -> None:
    (tmp_path / "input.txt").write_bytes(b"proofledger")

    first = hash_declared_path(tmp_path, "input.txt")
    second = hash_declared_path(tmp_path, "input.txt")

    assert first == second
    assert first.kind == "file"
    assert first.size_bytes == len(b"proofledger")
    assert first.file_count == 1


def test_directory_hash_is_order_independent(tmp_path: Path) -> None:
    directory = tmp_path / "dataset"
    directory.mkdir()
    (directory / "b.txt").write_text("b", encoding="utf-8")
    (directory / "a.txt").write_text("a", encoding="utf-8")

    result = hash_declared_path(tmp_path, "dataset")
    (directory / "a.txt").unlink()
    (directory / "a.txt").write_text("a", encoding="utf-8")

    assert hash_declared_path(tmp_path, "dataset") == result
    assert result.file_count == 2


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="escapes repository root"):
        hash_declared_path(tmp_path, "../outside.txt")


def test_symlink_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    target.write_text("safe", encoding="utf-8")
    link.symlink_to(target)

    with pytest.raises(InputError, match="symbolic links"):
        hash_declared_path(tmp_path, "link.txt")
