from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .context import EnvironmentCollector
from .errors import InputError, ManifestError, ProofLedgerError
from .models import DatasetSplit, VerificationPolicy
from .services import ArtifactSpec, CaptureService, VerifyService
from .store import ManifestStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proofledger",
        description="Capture and verify portable evidence manifests for ML runs.",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    capture = subparsers.add_parser("capture", help="capture a run into a JSON manifest")
    capture.add_argument("--root", type=Path, default=Path("."), help="repository root")
    capture.add_argument("--manifest", type=Path, required=True, help="output manifest path")
    capture.add_argument("--command", nargs="+", required=True, help="recorded command metadata")
    capture.add_argument("--input", action="append", default=[], metavar="NAME=PATH")
    capture.add_argument("--output", action="append", default=[], metavar="NAME=PATH")
    capture.add_argument("--parameter", action="append", default=[], metavar="NAME=VALUE")
    capture.add_argument("--metric", action="append", default=[], metavar="NAME=NUMBER")
    capture.add_argument("--split", help="dataset split as a JSON object")
    capture.add_argument("--package", action="append", default=[], dest="packages")
    capture.add_argument(
        "--allow-dirty",
        action="store_true",
        help="do not require a clean worktree at verify time",
    )
    capture.add_argument(
        "--no-git-revision",
        action="store_true",
        help="allow verification without a matching Git revision",
    )

    verify = subparsers.add_parser("verify", help="verify a manifest against the current checkout")
    verify.add_argument("--root", type=Path, default=Path("."), help="repository root")
    verify.add_argument("--manifest", type=Path, required=True, help="manifest path")
    verify.add_argument("--json", action="store_true", dest="json_output")

    show = subparsers.add_parser("show", help="show a manifest summary")
    show.add_argument("--manifest", type=Path, required=True, help="manifest path")
    show.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.action == "capture":
            return _capture(args)
        if args.action == "verify":
            return _verify(args)
        if args.action == "show":
            return _show(args)
        parser.error("unknown command")
    except (InputError, ManifestError, ProofLedgerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: filesystem operation failed: {exc}", file=sys.stderr)
        return 2
    return 2


def _capture(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        raise InputError(f"root is not a directory: {root}")
    split = _parse_split(args.split) if args.split else None
    policy = VerificationPolicy(
        require_git_revision=not args.no_git_revision,
        require_clean_git=not args.allow_dirty,
        require_python_compatibility=True,
    )
    service = CaptureService(root, EnvironmentCollector.from_iterable(args.packages))
    manifest = service.capture(
        command=args.command,
        inputs=_parse_artifacts(args.input),
        outputs=_parse_artifacts(args.output),
        parameters=_parse_key_values(args.parameter),
        metrics=_parse_metrics(args.metric),
        dataset_split=split,
        policy=policy,
    )
    ManifestStore(args.manifest).save(manifest)
    print(
        json.dumps(
            {"ok": True, "manifest": str(args.manifest), "run_id": manifest.run_id},
            indent=2,
        )
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    manifest = ManifestStore(args.manifest).load()
    service = VerifyService(args.root.resolve(), EnvironmentCollector())
    result = service.verify(manifest, args.manifest)
    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        status = "VERIFIED" if result.ok else "FAILED"
        print(f"{status}: {result.checked_artifacts} artifacts checked")
        for issue in result.issues:
            location = f" [{issue.path}]" if issue.path else ""
            print(f"- {issue.code}{location}: {issue.message}")
    return 0 if result.ok else 1


def _show(args: argparse.Namespace) -> int:
    manifest = ManifestStore(args.manifest).load()
    if args.json_output:
        print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"run_id: {manifest.run_id}")
        print(f"schema: {manifest.schema_version}")
        print(f"created_at: {manifest.created_at}")
        print(f"command: {' '.join(manifest.command)}")
        print(f"inputs: {len(manifest.inputs)}; outputs: {len(manifest.outputs)}")
        print(f"git: {manifest.git.revision or 'unavailable'}")
        if manifest.metrics:
            print(f"metrics: {json.dumps(manifest.metrics, sort_keys=True)}")
    return 0


def _parse_artifacts(values: list[str]) -> tuple[ArtifactSpec, ...]:
    artifacts: list[ArtifactSpec] = []
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name.strip() or not path.strip():
            raise InputError(f"expected NAME=PATH, got: {value}")
        artifacts.append(ArtifactSpec(name.strip(), path.strip()))
    return tuple(artifacts)


def _parse_key_values(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        name, separator, raw = value.partition("=")
        if not separator or not name.strip() or not raw.strip():
            raise InputError(f"expected NAME=VALUE, got: {value}")
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        result[name.strip()] = parsed
    return result


def _parse_metrics(values: list[str]) -> dict[str, float]:
    raw_values = _parse_key_values(values)
    metrics: dict[str, float] = {}
    for name, value in raw_values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InputError(f"metric must be numeric: {name}")
        metrics[name] = float(value)
    return metrics


def _parse_split(raw: str) -> DatasetSplit:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"split must be valid JSON: {exc}") from exc
    split = DatasetSplit.from_dict(data)
    if split is None:
        raise InputError("split must be a JSON object")
    return split


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
