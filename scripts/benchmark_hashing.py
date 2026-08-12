"""Measure streaming file hashing throughput on the local machine."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from proofledger.hashing import hash_declared_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size-mb", type=float, default=8.0)
    parser.add_argument("--iterations", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.size_mb <= 0 or args.iterations <= 0:
        raise SystemExit("--size-mb and --iterations must be positive")

    size_bytes = int(args.size_mb * 1024 * 1024)
    block = b"proofledger-benchmark\n" * 4096
    with tempfile.TemporaryDirectory(prefix="proofledger-benchmark-") as temporary:
        path = Path(temporary) / "payload.bin"
        with path.open("wb") as handle:
            remaining = size_bytes
            while remaining:
                chunk = block[: min(len(block), remaining)]
                handle.write(chunk)
                remaining -= len(chunk)

        durations: list[float] = []
        digests: set[str] = set()
        for _ in range(args.iterations):
            started = time.perf_counter()
            result = hash_declared_path(Path(temporary), "payload.bin")
            durations.append(time.perf_counter() - started)
            digests.add(result.sha256)
            if result.size_bytes != size_bytes:
                raise RuntimeError("benchmark file size changed unexpectedly")

    durations.sort()
    median_seconds = durations[len(durations) // 2]
    result = {
        "operation": "sha256_streaming_file_hash",
        "size_bytes": size_bytes,
        "iterations": args.iterations,
        "median_seconds": round(median_seconds, 6),
        "median_mib_per_second": round(size_bytes / median_seconds / (1024 * 1024), 3),
        "stable_digest": len(digests) == 1,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
