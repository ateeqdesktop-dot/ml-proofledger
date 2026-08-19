# ProofLedger

**Evidence you can verify.**

ProofLedger is a local-first Python CLI and portable evidence format for AI/ML runs. It captures the context around a run—declared artifacts, source revision, runtime, parameters, metrics, dataset split, and reviewable evidence—then verifies that the current checkout still matches the recorded claim. It is deliberately smaller than an observability platform: no tracking server, vendor account, network, or secret collection is required.

> A model file is not a reproducibility record. ProofLedger makes the surrounding evidence explicit, inspectable, and testable.

## Why ProofLedger

MLflow provides broad experiment tracking [1]. DVC focuses on data/model versioning and experiment workflows [2]. OpenLineage models lineage events for jobs and datasets [3]. in-toto provides a framework for verifiable claims about how software is produced [4]. ProofLedger occupies a narrower, practical intersection: a commit-friendly AI/ML evidence bundle that a reviewer or CI job can inspect and verify offline.

ProofLedger does not claim that a verified hash proves scientific correctness or author trust. It proves a more precise statement: **the declared bytes and recorded context match the evidence under the selected policy.**

## What is implemented

| Capability | ProofLedger 1.1 behavior |
|---|---|
| Capture | `proofledger capture` writes a versioned JSON evidence manifest |
| Artifact integrity | Streaming SHA-256 for files and deterministic path-plus-digest hashing for directories |
| Context | Command metadata, UTC timestamp, Git revision/branch/dirty state, Python/platform, and optional package versions |
| ML metadata | Parameters, numeric metrics, explicit dataset split counts, named inputs and outputs |
| Evidence | Reviewable claims with `accept`, `review`, or `reject` decisions, confidence, source, and artifact references |
| Bundle integrity | Deterministic canonical JSON digest that detects manifest tampering offline |
| Verification | Fail-closed checks for schema, digest, paths, kind, bytes, size, file count, Git policy, runtime compatibility, and rejected evidence |
| Automation | Stable exit codes and machine-readable `--json` output |
| Safety | No shell execution, network calls, arbitrary environment collection, or path traversal |

The published contract is [`schemas/proofledger-1.1.schema.json`](schemas/proofledger-1.1.schema.json). The implementation also reads schema 1.0 manifests for backward compatibility.

## Quickstart

```bash
git clone https://github.com/ateeqdesktop-dot/ml-proofledger.git
cd ml-proofledger
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
make test
```

Run the deterministic sample:

```bash
make sample
make capture
make verify
```

Inspect the resulting evidence:

```bash
proofledger show --manifest examples/proofledger.json
proofledger show --manifest examples/proofledger.json --json
```

A custom run can attach reviewable evidence without sending data anywhere:

```bash
proofledger capture \
  --root . \
  --manifest run-evidence.json \
  --command python train.py --epochs 10 \
  --input dataset=data/train.csv \
  --output model=models/model.bin \
  --parameter seed=7 \
  --metric accuracy=0.91 \
  --evidence '{"id":"eval-accuracy","kind":"evaluation","statement":"held-out accuracy passed threshold","decision":"accept","confidence":0.97}' \
  --split '{"name":"v1","strategy":"temporal","seed":7,"counts":{"train":800,"test":200}}'

proofledger verify --root . --manifest run-evidence.json --json
```

The `--evidence` argument is metadata. ProofLedger does not execute evaluators or infer truth from a statement; it preserves the claim and applies the explicit decision policy supplied by the producer.

## Verification semantics

A successful result means that every declared evidence check passed under the policy stored in the manifest. It does not mean that the model is scientifically correct, that the original author was trustworthy, or that a run is bit-for-bit reproducible across all hardware and libraries.

| Exit code | Meaning |
|---:|---|
| `0` | Capture succeeded or verification passed |
| `1` | Verification completed but evidence mismatched or policy rejected the bundle |
| `2` | Invalid input, malformed manifest, or filesystem/CLI error |

Failures use stable codes such as `BUNDLE_DIGEST_MISMATCH`, `EVIDENCE_REJECTED`, `ARTIFACT_HASH_MISMATCH`, `MISSING_OR_UNREADABLE_PATH`, `GIT_REVISION_MISMATCH`, `GIT_WORKTREE_DIRTY`, and `PYTHON_VERSION_MISMATCH`. JSON output is intended for CI and downstream tooling.

## Architecture

The domain layer defines immutable manifest and evidence models. Infrastructure adapters collect hashes, Git metadata, runtime metadata, and JSON storage. Application services orchestrate capture, verification, and policy evaluation. The CLI remains a thin interface over those services.

![Architecture](docs/architecture.png)

The source diagram is [`docs/architecture.mmd`](docs/architecture.mmd). The detailed product design is [`docs/design.md`](docs/design.md), and the implementation plan is [`docs/implementation-plan.md`](docs/implementation-plan.md).

## Security model

Declared paths are resolved against an explicit repository root and rejected if they escape it. Symlinks are rejected to avoid surprising target substitution. Git is invoked with fixed read-only argument lists. The recorded command is plain metadata and is never executed. Environment collection is intentionally narrow and does not copy arbitrary environment variables, tokens, prompts, or secret files.

The bundle digest detects edits to the manifest, while artifact hashes detect byte changes, missing paths, type changes, and directory membership/content changes. A malicious actor who controls both a manifest and its artifacts can still rewrite both; detached signatures and GitHub/in-toto binding are roadmap adapters, not hidden promises of the MVP.

## Performance

The hot path is bounded-memory SHA-256 hashing. Directory traversal is deterministic and path-order independent. Run the local benchmark with:

```bash
make benchmark
```

Benchmark numbers are local baselines, not cross-machine capacity guarantees.

## Development

```bash
make test
make lint
make typecheck
make format-check
make benchmark
```

The test suite covers canonical digest stability, tamper detection, evidence policy rejection, deterministic file and directory hashes, path traversal and symlink rejection, capture/store/verify flows, CLI JSON output, and invalid input. GitHub Actions runs the quality gates across supported Python versions.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request and [`SECURITY.md`](SECURITY.md) for vulnerability reporting. The project is MIT licensed.

## Roadmap

The next releases can add detached signatures through an external adapter, an in-toto predicate export, SARIF output, a reusable GitHub Action, dataset/model-store plugins, and a content-addressed local registry. A future collaboration service must consume the same portable bundle rather than replace the local-first contract.

## References

[1]: https://mlflow.org/docs/latest/ml/tracking/ "MLflow Tracking"
[2]: https://doc.dvc.org/start "DVC documentation"
[3]: https://openlineage.io/docs/spec/object-model/ "OpenLineage object model"
[4]: https://github.com/in-toto/attestation "in-toto Attestation Framework"
