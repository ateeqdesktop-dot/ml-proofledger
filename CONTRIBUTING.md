# Contributing

Thank you for considering a contribution to ML ProofLedger. The project favors small, reviewable changes that preserve the manifest contract and keep the local-first core dependency-light.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
make test
make lint
make format-check
```

## Change expectations

A change should explain the user problem it solves, keep public behavior documented, and include tests for success and failure paths. Changes to the manifest schema must update the schema version or provide a compatibility path; silently changing the meaning of an existing field is not acceptable. New integrations should remain adapters around the domain model rather than introducing network or vendor requirements into the core.

Before opening a pull request, run `make test`, `make lint`, and `make format-check`. Pull requests should describe security implications, compatibility impact, and any new dependency. Do not commit datasets, model binaries, credentials, tokens, or local environment files.

## Commit style

Use concise imperative commits such as `feat: add sarif verification output`, `fix: reject symlinked evidence`, or `docs: clarify attestation boundary`. Keep unrelated refactors separate from behavior changes.

## Reporting bugs

For ordinary bugs, open an issue with the operating system, Python version, command, minimal manifest or fixture, expected behavior, and actual output. Do not disclose secrets or private artifact contents in an issue.
