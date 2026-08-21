# ProofLedger — v1.2 Delivery Report

## Release focus

This iteration closes the most important public gap identified in the v1.1 roadmap: verification results can now be consumed by GitHub Code Scanning through SARIF 2.1.0. The core remains local-first and dependency-light; SARIF is a reporting adapter, not a hosted service.

## Delivered changes

| Area | Change |
|---|---|
| Reporting | Added typed `verification_to_sarif` rendering with stable rule IDs, messages, artifact locations, and verification properties |
| CLI | Added mutually exclusive `proofledger verify --sarif` output mode alongside text and `--json` |
| CI/CD | Added a GitHub Actions job that runs the deterministic sample, generates SARIF, and uploads it with least-privilege `security-events: write` |
| Testing | Added success and tampered-artifact SARIF integration tests; all tests pass |
| Documentation | Updated README, architecture design, and changelog to describe the shipped capability |

## Verification

Local checks passed: 16 tests, Ruff, strict mypy, formatting, compilation, sample capture, sample verification, and SARIF structural validation. The existing GitHub Actions matrix remains the primary remote quality gate and the new SARIF job is part of the published workflow.

## Product boundary

SARIF reports findings from ProofLedger’s own verification model. It does not claim to replace CodeQL, model evaluation, signing, or scientific review. A failed artifact or policy check becomes a machine-readable result with a stable `ruleId`, while a valid bundle produces an empty findings list and a `verified: true` property.

## Next priorities

The next highest-value capability is detached signing through a replaceable adapter, followed by in-toto predicate export. Both should preserve the portable manifest contract and continue to keep the default workflow offline-capable.
