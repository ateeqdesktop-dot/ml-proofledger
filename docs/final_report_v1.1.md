# ProofLedger — Final Delivery Report

## Executive summary

The selected project is **ProofLedger**, an evolution of the existing `ml-proofledger` repository into a portable evidence ledger for AI/ML runs. The project intentionally does not compete with general observability or evaluation platforms. Its differentiator is a local-first, reviewable, offline-verifiable bundle that records not only artifacts and hashes, but also explicit evidence claims and their decision state.

Repository: <https://github.com/ateeqdesktop-dot/ml-proofledger>

Delivered commit: `2c31df5` — `feat: add verifiable AI run evidence bundles`

## Delivered product

The release adds schema `1.1`, a deterministic canonical JSON representation, a `bundle_digest` that detects manifest tampering, and typed `EvidenceRecord` objects with `accept`, `review`, and `reject` decisions. The CLI accepts evidence JSON through repeated `--evidence` flags. Verification fails closed for a mismatched bundle digest or explicitly rejected evidence and preserves the existing artifact, Git, runtime, and path-safety checks.

The repository now publishes [`schemas/proofledger-1.1.schema.json`](../schemas/proofledger-1.1.schema.json), documents the implementation in [`implementation-plan.md`](implementation-plan.md), and presents a production-oriented README with quickstart, architecture, security model, verification semantics, and roadmap.

## Engineering quality

| Area | Result |
|---|---|
| Unit and integration tests | 14 tests passing locally and in CI |
| Lint | Ruff passed |
| Type safety | Strict mypy passed |
| Formatting and compilation | Passed |
| JSON contract | Published schema validates captured manifests |
| Package build | Wheel and sdist built successfully |
| Installed CLI smoke test | Passed in an isolated virtual environment |
| Sample flow | `make sample`, `make capture`, and `make verify` passed |
| GitHub Actions | Run `32308150465` completed successfully |
| CI matrix | Python 3.10, 3.11, and 3.12 passed; hygiene and distribution jobs passed |

## Deliberate boundaries

ProofLedger does not execute recorded commands, make network requests, collect secrets, claim scientific correctness, or pretend that an unsigned hash is author authentication. Detached signatures, in-toto predicate export, SARIF, GitHub Action packaging, and remote registries remain explicit roadmap adapters.

## Strategic rationale

OpenLineage addresses lineage events, Langfuse and Phoenix address LLM observability, and DeepEval addresses application evaluation. in-toto provides a useful attestation foundation. ProofLedger is positioned as a small, composable artifact layer that can export to or integrate with those systems later without requiring any of them for its core guarantee.

## Next release priorities

The highest-value next increment is detached signing through an external, replaceable adapter, followed by an in-toto predicate exporter and SARIF output for CI review. These should preserve the current portable JSON contract and must not turn the core package into a hosted service dependency.

## References

[1]: https://github.com/OpenLineage/OpenLineage "OpenLineage"
[2]: https://github.com/langfuse/langfuse "Langfuse"
[3]: https://github.com/Arize-ai/phoenix "Arize Phoenix"
[4]: https://github.com/confident-ai/deepeval "DeepEval"
[5]: https://github.com/in-toto/attestation "in-toto Attestation Framework"
