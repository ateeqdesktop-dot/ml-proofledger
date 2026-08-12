# Idea Selection: ML ProofLedger

## Decision

The selected project is **ML ProofLedger**, an open-source, local-first tool that creates a verifiable evidence record for each ML execution. It records data and artifact hashes, source revision, runtime context, command metadata, parameters, dataset split, metrics, and outputs, then verifies the record later and returns CI-friendly failures.

The choice was made against the existing GitHub portfolio rather than in isolation. The account already contains **Mizan**, an Arabic NLP/fact-checking system, and **Mate-Vision**, a vision/application project. Private repositories include a phishing-risk tool and an Android/real-estate MVP. The portfolio therefore benefits more from a developer-infrastructure and ML-platform project than from another classifier, CRUD application, or chatbot.

## Problem and gap

Machine-learning repositories often show training code and a model artifact without a portable answer to: *which exact input files, source revision, split, parameters, environment, and outputs produced this artifact?* Full platforms solve part of this problem but introduce a tracking service or broader operational surface. ProofLedger targets the smaller, high-value gap: a versioned evidence manifest for one execution that can be reviewed in Git and verified offline in CI.

This is not a claim that existing tools are insufficient in general. MLflow provides broad experiment tracking [1], DVC provides data/model versioning and remote workflow support [2], OpenLineage models distributed job/dataset lineage [3], and GitHub Attestations/SLSA address signed build provenance [4] [5]. ProofLedger is intentionally a lightweight ML-domain evidence layer that can later integrate with those systems.

## Competitor comparison

| Existing tool | Strength | Boundary | ProofLedger position |
|---|---|---|---|
| [MLflow Tracking][1] | Runs, parameters, metrics, artifacts, APIs, and UI/server | Broader tracking platform rather than a small commit-friendly evidence contract | Offline manifest and verification for one run |
| [DVC][2] | Data/model versioning, pipelines, remotes, and experiments | Stronger storage/versioning system; not necessarily a minimal evidence gate | No remote storage required for the core |
| [OpenLineage][3] | Runtime/design-time lineage for jobs and datasets | Distributed lineage model is broader than a single repository evidence file | Future optional adapter; local core first |
| [GitHub Artifact Attestations][4] and [SLSA][5] | Signed supply-chain/build provenance | Does not by itself model ML split, metrics, or dataset schema | Domain-specific evidence that can bind to attestations later |
| [Model Card Toolkit][6] | Structured model transparency documentation | Describes a model/report, not each execution and artifact hash | Per-run evidence; model-card export is future work |
| [ReproZip][7] | General environment capture and replay packaging | General replay packaging, not an ML evidence contract | Smaller ML-focused contract with metrics and split metadata |

## Weighted comparison

Each criterion is scored from 0 to 10. The total is a decision aid, not a market measurement. The maximum is 180 across 18 criteria.

| Idea | Total | Average | Reason for ranking |
|---|---:|---:|---|
| **ML ProofLedger** | **168** | **9.33** | Strong portfolio differentiation, real developer value, testable core, and natural CI/open-source surface |
| API Contract Guardian | 163 | 9.06 | Excellent engineering value but less distinct from existing API tooling |
| Dataset Drift Sentinel | 157 | 8.72 | Strong ML value but overlaps common monitoring patterns |
| Secure Model Input Firewall | 155 | 8.61 | Valuable security angle but requires broader threat-model and integration work |
| Local Experiment Tracker | 150 | 8.33 | Useful but close to existing tracking products |
| Arabic Document Intelligence | 146 | 8.11 | Strong language value but overlaps the current Mizan NLP direction |
| Synthetic Data Audit Lab | 143 | 7.94 | Interesting audit use case, but evaluation and ground truth are harder |
| Policy Evidence Map | 141 | 7.83 | High documentation value, but weaker immediate developer adoption path |

The complete reproducible scoring source is kept outside the repository during ideation and is summarized here so reviewers can inspect the criteria and outcome.

## MVP boundary

The first release implements a typed Python package, `capture`/`verify`/`show` CLI commands, a versioned manifest schema, streaming file and deterministic directory hashing, Git/runtime collection, parameters, metrics, dataset split metadata, fail-closed verification, a local deterministic ML example, tests, documentation, and GitHub Actions.

The first release does **not** claim to be a full tracking server, DVC replacement, signed SLSA attestation, universal replay engine, scientific model validator, or bit-for-bit reproducibility guarantee across arbitrary hardware and dependencies. These boundaries are part of the product design, not missing documentation.

## References

[1]: https://mlflow.org/docs/latest/ml/tracking/ "MLflow Tracking"
[2]: https://doc.dvc.org/start "DVC documentation"
[3]: https://openlineage.io/docs/spec/object-model/ "OpenLineage object model"
[4]: https://docs.github.com/en/actions/concepts/security/artifact-attestations "GitHub Artifact Attestations"
[5]: https://slsa.dev/spec/v1.0/provenance "SLSA provenance"
[6]: https://www.tensorflow.org/responsible_ai/model_card_toolkit/guide "Model Card Toolkit"
[7]: https://github.com/VIDA-NYU/reprozip "ReproZip"
