# Security Policy

## Scope

ML ProofLedger is a local CLI that reads declared repository paths, computes hashes, reads selected Git metadata, and writes or reads JSON manifests. It does not execute the recorded command and does not send data over the network.

## Supported versions

| Version | Supported |
|---|---|
| `0.1.x` | Yes |

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for the repository, or contact the maintainer privately through the contact method listed on the GitHub profile. Include a minimal reproduction, affected version, impact, and a safe remediation suggestion. Do not include credentials, private datasets, or proprietary artifacts.

## Design protections

The MVP rejects path traversal and symbolic links, uses fixed read-only Git subprocess arguments, avoids arbitrary environment-variable collection, and treats malformed manifests as errors. Hashes provide integrity evidence, not authenticity. A user who can modify both the artifact and manifest can make them agree; signed manifests and external attestations are future work.
