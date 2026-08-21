# ML ProofLedger — Product and Architecture Design

## Product vision

**ML ProofLedger** is a local-first developer tool that turns one machine-learning execution into a portable, inspectable, and verifiable evidence record. The tool is intentionally smaller than a tracking platform: it does not require a server, remote artifact store, or vendor account. Its promise is narrower and testable: a reviewer or CI job can determine whether the files, source revision, configuration, environment, and recorded outputs still match the evidence captured for a run.

The project addresses a recurring engineering problem. A repository may contain training code and a model artifact, yet a future maintainer cannot reliably answer which dataset snapshot, split definition, parameters, dependency set, or source revision produced that artifact. MLflow provides broad run tracking [1], DVC provides data/model versioning and experiment workflows [2], OpenLineage provides lineage events for jobs and datasets [3], and SLSA/GitHub Attestations focus on build provenance and signed artifact claims [4] [5]. ProofLedger occupies a deliberately smaller intersection: a domain-specific ML evidence manifest that can be committed, diffed, verified offline, and used as a CI gate.

## Target users and use cases

The primary users are research engineers, ML platform engineers, graduate students, and maintainers of small-to-medium ML repositories who need reproducibility evidence without introducing a tracking server. A user should be able to capture a run after training, inspect the manifest in a code review, verify it on another checkout, and make CI fail when a declared input or output has changed.

| User | Need | ProofLedger response |
|---|---|---|
| Research engineer | Explain how a model artifact was produced | Captures command, Git revision, inputs, parameters, metrics, environment, and outputs |
| Repository maintainer | Detect stale or tampered evidence | Verifies schema, hashes, paths, and consistency rules |
| Reviewer or recruiter | Inspect a concrete engineering artifact quickly | Provides human-readable JSON and CLI summaries |
| CI maintainer | Gate releases on evidence integrity | Exits non-zero on verification failures and supports a machine-readable report |
| Educator or student | Teach reproducibility without cloud dependencies | Includes a deterministic sample ML run and documented fixtures |

## Scope

The MVP implements a Python 3.10+ package and CLI with two core operations. `capture` computes streaming SHA-256 hashes for declared input files, output files, and directories; records Git state, Python/runtime information, command, parameters, metrics, and an explicit dataset split; and writes a versioned JSON manifest. `verify` re-hashes the declared paths, validates the manifest schema and policy, compares the current Git revision and environment claims, and returns a structured verdict with actionable failures. `show` prints a compact human-readable summary without modifying evidence.

The MVP deliberately does not implement a tracking server, remote storage, cryptographic signing, arbitrary code execution, container introspection, or universal bit-for-bit reproducibility. SARIF output is implemented as a CI/reporting adapter; signing and remote integrations remain later adapters. The absence of a feature is documented rather than hidden behind a placeholder.

## Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Capture a run manifest | `proofledger capture` writes a schema-valid JSON file |
| FR-02 | Hash files and directories | Hashes are deterministic, streaming, and path-order independent for directories |
| FR-03 | Record execution context | Manifest includes command, timestamp, Git revision/state, Python version, platform, and package snapshot when available |
| FR-04 | Record ML metadata | Parameters, metrics, dataset split, and named input/output artifacts are represented explicitly |
| FR-05 | Verify evidence | `proofledger verify` reports pass/fail and exits non-zero on mismatch |
| FR-06 | Explain failures | Every failure has a stable code, path or field when relevant, and a remediation message |
| FR-07 | Stay safe by default | No shell command execution, no network request, no secret collection, no path traversal outside declared roots |
| FR-08 | Support CI | `--json` and SARIF 2.1.0 output are available and GitHub Actions verifies and uploads the sample report |
| FR-09 | Provide sample data | The repository includes a tiny deterministic fixture and a runnable sample capture/verify flow |

## Non-functional requirements

The CLI must be deterministic for identical file content and metadata inputs, must use bounded memory for hashing large files, and must not require a service. Public Python APIs use type hints and dataclasses. Errors are represented through a small exception hierarchy and structured verification results. The default output must be understandable to a new contributor, while JSON output must be parseable by CI. The package must work on Linux and macOS paths and avoid platform-specific shell assumptions.

## Architecture

The code is organized into four layers. The domain layer defines schema models, evidence records, and verification outcomes. The infrastructure layer supplies filesystem hashing, Git/environment collection, and JSON persistence. The application layer orchestrates capture and verification policies without knowing how a specific Git provider or storage backend works. The interface layer exposes the CLI. This is a modest Clean Architecture boundary: it is intentionally not a framework-heavy design, but it makes hashing and metadata collection replaceable and testable.

```text
CLI (argparse)
   |
   +--> CaptureService ----> HashProvider ----> Filesystem
   |          |              GitProvider -----> Git CLI (read-only)
   |          |              Environment -----> Python/platform metadata
   |          +-------------> ManifestStore ---> JSON file
   |
   +--> VerifyService ----> ManifestStore
              |             HashProvider
              |             PolicyEngine -----> VerificationResult
              +-------------> JSON/text renderer
```

The core interfaces are `Hasher`, `GitInspector`, `EnvironmentCollector`, and `ManifestStore`. A default adapter is provided for each. The interfaces are intentionally narrow so that future S3, OpenLineage, GitHub Attestations, or database adapters can be added without changing the manifest domain model.

## Manifest contract

The manifest is versioned with `schema_version`. It contains an immutable identity section, a `run` section, `inputs`, `outputs`, `parameters`, `metrics`, `dataset_split`, and a `verification_policy`. An artifact record contains a user-declared logical name, a normalized repository-relative path, kind (`file` or `directory`), byte size where applicable, and SHA-256 digest. Directory hashing sorts relative paths and includes each relative path and file digest in the digest stream, preventing order-dependent results.

The manifest is evidence, not a signature. A valid hash proves that the current bytes match the recorded bytes; it does not prove that the original author was trustworthy or that the model is scientifically correct. The CLI will say `VERIFIED` only when all selected policy checks pass. It will say `FAILED` with stable failure codes for changed artifacts, missing paths, schema errors, dirty Git state when required, or incompatible Python major/minor version when required.

## Error flow and safety model

Input paths are resolved against a user-specified repository root and rejected if they escape that root. The tool never evaluates a command string. The captured command is plain metadata supplied by the user or read from a safe argument list. Git inspection is read-only and uses a fixed executable invocation. JSON parsing rejects unknown unsafe structures through validation before any path is touched. Verification is fail-closed: a missing artifact or malformed manifest is a failure, not a warning disguised as success.

The CLI emits exit code 0 for a successful capture or verification, 2 for invalid user input or schema, and 1 for an evidence mismatch. Logs are concise by default and can be enabled with `--verbose`; secrets are not collected from environment variables, and package metadata is limited to names and versions when available.

## Performance strategy

Hashing is streaming with a configurable chunk size and does not read an entire file into memory. Directory hashing performs one deterministic traversal and hashes each file once. Verification reuses the same hash implementation as capture, so the main expected cost is proportional to the bytes declared in the manifest. A benchmark fixture will report throughput for small and medium files; the project will not claim performance beyond measured local results.

## MVP, advanced features, and roadmap

The MVP includes local JSON evidence, robust verification, a sample ML run, typed APIs, tests, documentation, CI, a Docker-compatible CLI image, and SARIF output for GitHub Code Scanning. Advanced features include signed manifests using an external key, an official reusable GitHub Action wrapper, dataset adapter plugins, and optional OpenLineage event export. Future work may add content-addressed artifact storage, remote evidence registries, SLSA-compatible binding, and a web review interface. These are roadmap items and are not represented as fake implementations in the MVP.

## References

[1]: https://mlflow.org/docs/latest/ml/tracking/ "MLflow Tracking documentation"
[2]: https://doc.dvc.org/start "DVC documentation"
[3]: https://openlineage.io/docs/spec/object-model/ "OpenLineage object model"
[4]: https://docs.github.com/en/actions/concepts/security/artifact-attestations "GitHub Artifact Attestations"
[5]: https://slsa.dev/spec/v1.0/provenance "SLSA provenance specification"
