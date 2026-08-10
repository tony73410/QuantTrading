"""Public ports for disabled P23-1F daily-volatility profiles."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .daily_volatility_profile_models import (
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileOperation,
    DailyVolatilityProfileQuery,
    DailyVolatilityProfileResult,
)


class DailyVolatilityProfileStore(Protocol):
    def initialize(self) -> None: ...
    def save_definition(self, definition: DailyVolatilityProfileDefinition) -> None: ...
    def get_definition(self, definition_id: UUID) -> DailyVolatilityProfileDefinition | None: ...
    def get_first_operation(self, operation_id: UUID) -> DailyVolatilityProfileOperation | None: ...
    def get_result_by_fingerprint(self, fingerprint: str) -> DailyVolatilityProfileResult | None: ...
    def save_operation(self, operation: DailyVolatilityProfileOperation) -> None: ...


class DailyVolatilityProfileQueryService(Protocol):
    def list_operations(
        self, query: DailyVolatilityProfileQuery = DailyVolatilityProfileQuery()
    ) -> tuple[DailyVolatilityProfileOperation, ...]: ...
    def get_operation(self, attempt_id: UUID) -> DailyVolatilityProfileOperation | None: ...
    def get_operation_for_run(self, run_id: UUID) -> DailyVolatilityProfileOperation | None: ...
    def get_result(self, result_id: UUID) -> DailyVolatilityProfileResult | None: ...


class DailyVolatilityProfileRunner(Protocol):
    def preview(self, command) -> DailyVolatilityProfileOperation: ...


class EmptyDailyVolatilityProfileQueryService:
    def list_operations(
        self, query: DailyVolatilityProfileQuery = DailyVolatilityProfileQuery()
    ) -> tuple[DailyVolatilityProfileOperation, ...]:
        return ()

    def get_operation(self, attempt_id: UUID) -> DailyVolatilityProfileOperation | None:
        return None

    def get_operation_for_run(self, run_id: UUID) -> DailyVolatilityProfileOperation | None:
        return None

    def get_result(self, result_id: UUID) -> DailyVolatilityProfileResult | None:
        return None


__all__ = [
    "DailyVolatilityProfileQueryService",
    "DailyVolatilityProfileStore",
    "DailyVolatilityProfileRunner",
    "EmptyDailyVolatilityProfileQueryService",
]
