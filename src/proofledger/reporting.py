from __future__ import annotations

from typing import Any

from .services import VerificationResult


def verification_to_sarif(result: VerificationResult) -> dict[str, Any]:
    """Render a verification result as SARIF 2.1.0 for CI consumers."""
    rules: dict[str, dict[str, Any]] = {}
    sarif_results: list[dict[str, Any]] = []
    for issue in result.issues:
        rules.setdefault(
            issue.code,
            {
                "id": issue.code,
                "shortDescription": {"text": issue.code.replace("_", " ").title()},
                "helpUri": "https://github.com/ateeqdesktop-dot/ml-proofledger#verification-semantics",
            },
        )
        item: dict[str, Any] = {
            "ruleId": issue.code,
            "level": "error",
            "message": {"text": issue.message},
        }
        if issue.path:
            item["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": issue.path},
                    }
                }
            ]
        sarif_results.append(item)

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ProofLedger",
                        "informationUri": "https://github.com/ateeqdesktop-dot/ml-proofledger",
                        "rules": list(rules.values()),
                    }
                },
                "automationDetails": {"id": f"proofledger/{result.manifest_path}"},
                "results": sarif_results,
                "properties": {
                    "verified": result.ok,
                    "checkedArtifacts": result.checked_artifacts,
                    "manifestPath": result.manifest_path,
                },
            }
        ],
    }
