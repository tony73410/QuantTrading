"""Target-position research errors."""

from __future__ import annotations


class TargetPositionError(Exception):
    """Base error for the isolated target-position research domain."""


class TargetPositionValidationError(TargetPositionError, ValueError):
    """An explicit definition or manual preview input is invalid."""


class TargetPositionStorageError(TargetPositionError):
    """Durable target-position evidence could not be stored."""


__all__ = [
    "TargetPositionError",
    "TargetPositionStorageError",
    "TargetPositionValidationError",
]
