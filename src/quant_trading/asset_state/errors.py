"""Safe failures for research-only asset-state history."""

from __future__ import annotations


class AssetStateError(Exception):
    """Base asset-state failure."""


class AssetStateValidationError(AssetStateError):
    """An explicit research-state command is invalid."""


class AssetStateStorageError(AssetStateError):
    """Durable asset-state evidence could not be stored or reconstructed."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class AssetStateConcurrencyError(AssetStateStorageError):
    """The requested predecessor is no longer current."""


__all__ = [
    "AssetStateConcurrencyError",
    "AssetStateError",
    "AssetStateStorageError",
    "AssetStateValidationError",
]
