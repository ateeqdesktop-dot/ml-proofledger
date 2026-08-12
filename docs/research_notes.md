# Research Notes

## Account and portfolio context

The GitHub account audit showed a public Arabic NLP project, a vision/application project, and newer private application experiments. The portfolio already demonstrates model building and application development. The selected project intentionally adds **ML developer tooling, provenance, CI, and supply-chain awareness** rather than repeating fact-checking, phishing classification, or CRUD.

## Existing tool boundaries

[MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/) documents a full run-tracking surface for parameters, code versions, metrics, output files, experiments, APIs, and artifacts. It is the right choice when a team needs a tracking service and UI. ProofLedger does not compete with that scope: its core is a small JSON evidence manifest and offline verification.

[DVC](https://doc.dvc.org/start) documents data and model versioning, pipelines, experiment management, and remote storage backends. ProofLedger does not provide data versioning or remote artifact storage. It records the exact declared paths and hashes used by one run, which can complement DVC rather than replace it.

[OpenLineage](https://openlineage.io/docs/spec/object-model/) defines a lineage object model around jobs, datasets, and runtime/design-time events. It is appropriate for distributed data and pipeline lineage. ProofLedger targets a smaller repository-local evidence contract and leaves OpenLineage export as an optional future adapter.

[GitHub Artifact Attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) and the [SLSA provenance specification](https://slsa.dev/spec/v1.0/provenance) focus on verifiable build provenance and software supply-chain claims. They are important for signed claims about how an artifact was built, but they do not by themselves provide a domain model for ML dataset splits, evaluation metrics, or model-specific evidence. ProofLedger is not signed and does not claim SLSA compliance in the MVP.

The [TensorFlow Model Card Toolkit](https://www.tensorflow.org/responsible_ai/model_card_toolkit/guide) automates structured model-card documentation. A model card is a stable transparency report about a model; ProofLedger records evidence for a particular execution and verifies the hashes and environment claims for that execution. The two can be complementary.

[ReproZip](https://github.com/VIDA-NYU/reprozip) captures general execution environments for replay-oriented workflows. ProofLedger is intentionally smaller and ML-specific: it records metrics, dataset split metadata, and named model inputs/outputs, while avoiding arbitrary command replay.

## Decision implication

The evidence supports a narrow, testable product claim: **ProofLedger makes selected ML-run evidence portable and verifiable; it does not prove scientific validity, author identity, signed provenance, or universal reproducibility.** Every README and CLI behavior should preserve that distinction.

## Sources accessed

| Source | Role in decision |
|---|---|
| MLflow Tracking | Benchmark for full experiment tracking |
| DVC documentation | Benchmark for data/model versioning |
| OpenLineage object model | Benchmark for distributed lineage |
| GitHub Artifact Attestations | Benchmark for signed GitHub build claims |
| SLSA v1.0 provenance | Standard boundary for build provenance terminology |
| Model Card Toolkit | Benchmark for model-level documentation |
| ReproZip repository | Benchmark for general environment capture |
