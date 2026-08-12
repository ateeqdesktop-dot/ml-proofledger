from __future__ import annotations


class ProofLedgerError(Exception):
    """Base class for expected ProofLedger failures."""


class InputError(ProofLedgerError):
    """Raised when CLI input or a requested path is invalid."""


class ManifestError(ProofLedgerError):
    """Raised when a manifest cannot be parsed or violates its schema."""


class VerificationMismatch(ProofLedgerError):
    """Raised only by integrations that require verification to pass."""
