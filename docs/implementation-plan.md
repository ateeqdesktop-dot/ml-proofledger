# ProofLedger — Implementation Plan

## Product decision

**ProofLedger** is a local-first, Python-first evidence ledger for AI/ML runs. It is not another observability dashboard, evaluation framework, or generic data-lineage server. Its core artifact is a portable evidence bundle that a reviewer or CI job can inspect and verify offline.

The project will evolve the existing `ml-proofledger` repository instead of creating a disconnected repository. The public promise is: **capture what happened, preserve why it should be trusted, and fail closed when the evidence no longer matches.**

## MVP to implement

The MVP will include a versioned manifest schema, deterministic canonical serialization, content hashing for files/directories, safe capture and verification, structured verdicts with stable failure codes, a human-readable report, and JSON output for CI. It will add a first-class `evidence` section for claims and references, an explicit decision policy with `accept`, `review`, and `reject`, and a bundle digest that can be verified independently of file paths.

The MVP will also include a `policy` command or equivalent validation path, a JSON Schema published in `schemas/`, an example run that demonstrates both a passing and a deliberately failing verification, and a GitHub Actions workflow that runs tests, lint, type checking, schema validation, and the sample flow.

The MVP will not claim cryptographic authorship or scientific correctness. Signing, remote registries, and third-party attestations remain adapters in the roadmap unless they can be added without weakening the local-first contract.

## Core contract

A manifest contains `schema_version`, `run_id`, `created_at`, `command`, `git`, `environment`, `parameters`, `metrics`, `dataset_split`, `inputs`, `outputs`, `evidence`, and `verification_policy`. Each evidence item has a stable identifier, kind, statement, optional source URI, optional artifact reference, and an explicit confidence/decision label. Secrets and full environment values are never collected.

The canonical digest is computed from a normalized JSON representation with sorted keys and stable separators. The digest excludes the mutable `bundle_digest` field itself. Verification first validates structure and policy, then recomputes the bundle digest, then checks declared artifacts and context claims, and finally evaluates evidence policy. Every failure has a stable code, a field/path, and an actionable message.

## Architecture

The domain layer owns immutable dataclasses, canonical serialization, evidence decisions, and verification outcomes. The infrastructure layer owns filesystem hashing, Git inspection, runtime metadata, and JSON persistence. The application layer owns capture, verification, policy evaluation, and report generation. The interface layer owns argparse commands and exit codes. No layer executes user-supplied shell strings, performs network calls, or reads undeclared paths.

```text
CLI
 ├── capture ──> CaptureService ──> HashProvider / GitInspector / EnvironmentCollector
 │                              └──> ManifestStore
 ├── verify ──> VerifyService ──> ManifestStore / HashProvider / PolicyEngine
 ├── show ────> ReportRenderer
 └── schema ──> Published JSON Schema

Optional future adapters
 ├── in-toto predicate exporter
 ├── GitHub artifact attestation verifier
 ├── OpenLineage event exporter
 └── remote evidence registry
```

## Security model

All paths are resolved against an explicit repository root and rejected when they escape it. The command field is metadata only and is never executed. Git calls use fixed argument lists and read-only operations. Verification is fail-closed. JSON parsing and dataclass validation occur before filesystem access. Evidence references are informational unless they point to a declared local artifact. The implementation must avoid collecting environment variables, tokens, prompt contents, or arbitrary package metadata beyond names and versions explicitly requested by the user.

## Performance and reliability

Hashing remains streaming and bounded-memory. Directory traversal is deterministic and path-order independent. Canonical serialization must be stable across supported Python versions. The verifier should distinguish malformed evidence, missing files, changed bytes, changed Git revision, incompatible runtime, and policy rejection. The CLI must remain useful without optional dependencies or network access.

## Test strategy

Unit tests cover canonicalization, digest stability, evidence validation, policy evaluation, path containment, failure codes, and backward compatibility with schema 1.0 manifests. Property-style tests cover directory ordering and repeated canonicalization. Integration tests run capture and verify against a temporary repository. CLI tests assert exit codes and JSON shape. A sample test intentionally mutates an output and proves that verification fails with a stable code.

## Advanced roadmap

The next releases can add detached signatures through an external signing adapter, an in-toto predicate export, SARIF output, an official GitHub Action, plugin hooks for dataset/model stores, and a content-addressed local registry. A later service may provide collaboration and review, but it must consume the same portable bundle rather than replace it.

## Definition of done

The implementation is ready for release when the package installs from a clean environment, all quality gates pass, the public schema is versioned and documented, the sample flow works without network access after installation, verification is fail-closed and explainable, the README contains a concise product story and quickstart, and GitHub metadata includes a license, topics, contributing guidance, security policy, changelog, and a tagged release.
