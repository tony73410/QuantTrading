"""Public persistence/query ports for specialized spectral evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from .spectral_models import (
    SpectralOperationStatus,
    SpectralVolatilityDefinition,
    SpectralVolatilityOperation,
)


@dataclass(frozen=True, slots=True)
class SpectralOperationQuery:
    symbol: str | None = None
    definition_id: UUID | None = None
    status: SpectralOperationStatus | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    evidence_mode: str | None = None
    warning_only: bool = False
    limit: int = 200

    def __post_init__(self) -> None:
        if self.symbol is not None:
            object.__setattr__(self, "symbol", self.symbol.strip().upper())
        if not 1 <= self.limit <= 5000:
            raise ValueError("spectral query limit must be within 1..5000")
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError(f"{name} must include a timezone")
                object.__setattr__(self, name, value.astimezone(UTC))


class SpectralVolatilityStore(Protocol):
    def initialize(self) -> None: ...
    def save_definition(self, definition: SpectralVolatilityDefinition) -> None: ...
    def get_definition(self, definition_id: UUID) -> SpectralVolatilityDefinition | None: ...
    def get_first_operation(self, operation_id: UUID) -> SpectralVolatilityOperation | None: ...
    def save_operation(self, operation: SpectralVolatilityOperation) -> None: ...


class SpectralVolatilityQueryService(Protocol):
    def list_operations(self, query: SpectralOperationQuery = SpectralOperationQuery()) -> tuple[SpectralVolatilityOperation, ...]: ...
    def get_operation(self, attempt_id: UUID) -> SpectralVolatilityOperation | None: ...
    def get_operation_for_run(self, run_id: UUID) -> SpectralVolatilityOperation | None: ...


class EmptySpectralVolatilityQueryService:
    def list_operations(self, query: SpectralOperationQuery = SpectralOperationQuery()) -> tuple[SpectralVolatilityOperation, ...]:
        return ()
    def get_operation(self, attempt_id: UUID) -> SpectralVolatilityOperation | None:
        return None
    def get_operation_for_run(self, run_id: UUID) -> SpectralVolatilityOperation | None:
        return None


__all__ = [
    "EmptySpectralVolatilityQueryService", "SpectralOperationQuery",
    "SpectralVolatilityQueryService", "SpectralVolatilityStore",
]
