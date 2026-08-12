from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import InputError


@dataclass(frozen=True, slots=True)
class HashResult:
    sha256: str
    size_bytes: int
    file_count: int
    kind: str


def resolve_declared_path(root: Path, relative_path: str) -> Path:
    """Resolve a repository-relative path and reject traversal or absolute paths."""
    if not relative_path or "\\" in relative_path:
        raise InputError("paths must be non-empty POSIX-style relative paths")
    candidate = Path(relative_path)
    if candidate.is_absolute() or PurePosixPath(relative_path).is_absolute():
        raise InputError(f"absolute paths are not allowed: {relative_path}")
    root_resolved = root.resolve()
    raw_path = root_resolved / candidate
    current = root_resolved
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise InputError(f"symbolic links are not supported as evidence paths: {relative_path}")
    resolved = raw_path.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise InputError(f"path escapes repository root: {relative_path}") from exc
    return resolved


def _hash_file(path: Path, chunk_size: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def hash_declared_path(
    root: Path,
    relative_path: str,
    *,
    chunk_size: int = 1024 * 1024,
) -> HashResult:
    """Hash a file or directory using deterministic, bounded-memory semantics."""
    if chunk_size < 1024:
        raise InputError("chunk_size must be at least 1024 bytes")
    path = resolve_declared_path(root, relative_path)
    if not path.exists():
        raise InputError(f"declared path does not exist: {relative_path}")
    if path.is_symlink():
        raise InputError(f"symbolic links are not supported as evidence paths: {relative_path}")
    if path.is_file():
        digest, size = _hash_file(path, chunk_size)
        return HashResult(digest, size, 1, "file")
    if not path.is_dir():
        raise InputError(f"declared path is not a regular file or directory: {relative_path}")

    directory_digest = hashlib.sha256()
    size = 0
    file_count = 0
    entries: list[Path] = []
    for current_root, directories, files in os.walk(path, followlinks=False):
        directories[:] = sorted(
            directory
            for directory in directories
            if not (Path(current_root) / directory).is_symlink()
        )
        entries.extend(Path(current_root) / filename for filename in sorted(files))
    for file_path in sorted(entries, key=lambda item: item.relative_to(path).as_posix()):
        if file_path.is_symlink() or not file_path.is_file():
            raise InputError(f"directory contains an unsupported link or non-file: {file_path}")
        relative = file_path.relative_to(path).as_posix().encode("utf-8")
        file_digest, file_size = _hash_file(file_path, chunk_size)
        directory_digest.update(relative)
        directory_digest.update(b"\0")
        directory_digest.update(file_digest.encode("ascii"))
        directory_digest.update(b"\n")
        size += file_size
        file_count += 1
    return HashResult(directory_digest.hexdigest(), size, file_count, "directory")
