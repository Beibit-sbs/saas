from __future__ import annotations


class DependencyUnavailableError(RuntimeError):
    """Raised when a required external dependency is unavailable."""


class RevocationStoreUnavailable(RuntimeError):
    """Raised when token revocation storage is unavailable."""
