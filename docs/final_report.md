# ML ProofLedger — Final Delivery Report

## Project

**ML ProofLedger** is a portable, dependency-light developer tool for capturing and verifying evidence about machine-learning runs. It creates a deterministic JSON manifest containing declared inputs, outputs, parameters, metrics, package metadata, Git context, runtime metadata, and SHA-256 evidence hashes.

Repository: <https://github.com/ateeqdesktop-dot/ml-proofledger>  
Release: <https://github.com/ateeqdesktop-dot/ml-proofledger/releases/tag/v0.1.0>  
Default branch: `main`  
Release checkpoint: `v0.1.0`; the final documentation commit is the source of truth for the current report.

The project addresses a practical gap between experiment tracking, data/model versioning, source lineage, and build attestations. It does not attempt to replace MLflow, DVC, OpenLineage, or SLSA. Instead, it provides a small local evidence boundary that can be checked in CI without a server, database, or external API.

## Engineering

The implementation uses Python 3.10+, a typed domain model, a deterministic hashing adapter, a narrow Git/runtime context collector, an atomic JSON store, application services, and a thin CLI. The main commands are `capture`, `verify`, and `show`; all commands support actionable errors and stable process behavior, with JSON output available for automation.

The security model rejects absolute paths, traversal, Windows-style separators, symlinks, and unsupported filesystem entries. Recorded commands are metadata only and are never executed by ProofLedger. Environment collection is intentionally narrow and excludes arbitrary environment variables and secrets. Verification reports independent hash, size, missing-path, and type mismatches.

The repository includes a Mermaid architecture source and rendered PNG, product/design documentation, an idea-selection record, research notes, a sample dataset and deterministic nearest-centroid run, a reproducible hashing benchmark, Docker packaging, and Open Source maintainer files.

## Quality and validation

| Check | Evidence |
|---|---|
| Unit and integration tests | `10 passed` locally via `pytest` |
| Coverage | `83.70%` total measured with `pytest-cov`; this is reported as a quality signal, not a substitute for test relevance |
| Lint | Ruff passed on `src`, `tests`, `examples`, and `scripts` |
| Type check | Mypy strict mode passed for all 9 source modules |
| Formatting and compilation | Ruff format check and Python compileall passed |
| Package build | Wheel and sdist built successfully with `python -m build` |
| Clean installation | Built wheel installed into a fresh temporary virtual environment and `proofledger --help` succeeded |
| Security checks | Tracked-file secret-pattern scan and local-artifact rejection passed in CI |
| Performance baseline | 8 MiB SHA-256 streaming hash, five iterations: median `347.024 MiB/s` on the sandbox; rerun on target hardware before capacity decisions |
| Docker | Dockerfile and `.dockerignore` are included; Docker daemon was not available in the execution environment, so image build is documented but not claimed as locally executed |

The sample flow was executed locally through `sample`, `capture`, `show`, and `verify`, including tamper and invalid-input paths covered by the test suite. Generated model, prediction, and manifest fixtures are ignored so the repository remains source-only and reproducible.

## GitHub and Open Source

The repository was created and pushed to GitHub as a public project. Its history contains five logical Conventional Commit-style commits:

1. `feat: implement verifiable ML evidence ledger`
2. `docs: define product architecture and open-source practices`
3. `ci: add quality gates and container packaging`
4. `chore: ignore local development artifacts`
5. `perf: add reproducible hashing benchmark`

GitHub Actions run `31629033945` completed successfully. The workflow covers Python 3.10, 3.11, and 3.12, tests, Ruff, strict mypy, formatting/compile checks, repository hygiene, metadata validation, wheel/sdist build, and CLI smoke validation. Release `v0.1.0` was created after the successful CI run.

The repository contains `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, pull-request guidance, CI, Docker packaging, and documentation separated from the README.

## Reproduction

```bash
git clone https://github.com/ateeqdesktop-dot/ml-proofledger.git
cd ml-proofledger
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
make test
make lint
make typecheck
make format-check
make sample
make capture
make verify
make benchmark
```

For a packaged installation:

```bash
python -m build
python -m pip install dist/*.whl
proofledger --help
```

## Limitations and roadmap

A hash proves that the observed bytes match a manifest; it does not prove that the manifest itself was authored by a trusted party. Signed manifests, a reusable GitHub Action, SARIF output, dataset adapter plugins, optional OpenLineage export, and a remote evidence registry remain roadmap items. The MVP intentionally has no server, authentication, database, or external API so that its evidence boundary stays portable and easy to audit.

## Research references

The design was compared against official documentation for [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/), [DVC](https://doc.dvc.org/start), the [OpenLineage object model](https://openlineage.io/docs/spec/object-model/), [GitHub Artifact Attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations), and [SLSA provenance](https://slsa.dev/spec/v1.0/provenance). The project decision and comparison are recorded in [`docs/idea_selection.md`](idea_selection.md) and [`docs/research_notes.md`](research_notes.md).
