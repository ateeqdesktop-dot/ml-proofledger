from __future__ import annotations

import importlib.metadata
import platform
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .models import EnvironmentRecord, GitRecord


@dataclass(frozen=True, slots=True)
class GitInspector:
    root: Path

    def _run(self, *args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None

    def inspect(self) -> GitRecord:
        revision = self._run("rev-parse", "--verify", "HEAD")
        branch = self._run("branch", "--show-current")
        dirty_output = self._run("status", "--porcelain", "--untracked-files=no")
        dirty = None if revision is None else bool(dirty_output)
        return GitRecord(revision=revision, branch=branch, dirty=dirty)


@dataclass(frozen=True, slots=True)
class EnvironmentCollector:
    package_names: tuple[str, ...] = ()

    def collect(self) -> EnvironmentRecord:
        packages: dict[str, str] = {}
        for name in sorted(set(self.package_names)):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                packages[name] = "not-installed"
        return EnvironmentRecord(
            python_version=platform.python_version(),
            implementation=platform.python_implementation(),
            platform=platform.platform(),
            packages=packages,
        )

    @classmethod
    def from_iterable(cls, package_names: Iterable[str]) -> EnvironmentCollector:
        return cls(tuple(package_names))
