"""Public Store and read-only query ports for standardized-state research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .standardized_state_models import (
    StandardizedPriceStateDefinition,
    StandardizedPriceStateDefinitionQuery,
    StandardizedPriceStateOperationAttempt,
    StandardizedPriceStateOperationQuery,
    StandardizedPriceStateResult,
    StandardizedPriceStateResultQuery,
)


class StandardizedPriceStateStore(Protocol):
    def initialize(self) -> None: ...

    def get_definition(
        self, definition_id: UUID
    ) -> StandardizedPriceStateDefinition | None: ...

    def get_first_operation(
        self, operation_id: UUID
    ) -> StandardizedPriceStateOperationAttempt | None: ...

    def create_definition(
        self,
        definition: StandardizedPriceStateDefinition,
        operation: StandardizedPriceStateOperationAttempt,
    ) -> None: ...

    def save_preview(
        self,
        result: StandardizedPriceStateResult,
        operation: StandardizedPriceStateOperationAttempt,
    ) -> None: ...

    def save_operation(self, operation: StandardizedPriceStateOperationAttempt) -> None: ...


class StandardizedPriceStateQueryService(Protocol):
    def list_definitions(
        self,
        query: StandardizedPriceStateDefinitionQuery = StandardizedPriceStateDefinitionQuery(),
    ) -> tuple[StandardizedPriceStateDefinition, ...]: ...

    def list_results(
        self,
        query: StandardizedPriceStateResultQuery = StandardizedPriceStateResultQuery(),
    ) -> tuple[StandardizedPriceStateResult, ...]: ...

    def get_result(
        self, calculation_id: UUID
    ) -> StandardizedPriceStateResult | None: ...

    def list_operations(
        self,
        query: StandardizedPriceStateOperationQuery = StandardizedPriceStateOperationQuery(),
    ) -> tuple[StandardizedPriceStateOperationAttempt, ...]: ...


class EmptyStandardizedPriceStateQueryService:
    def list_definitions(
        self,
        query: StandardizedPriceStateDefinitionQuery = StandardizedPriceStateDefinitionQuery(),
    ) -> tuple[StandardizedPriceStateDefinition, ...]:
        return ()

    def list_results(
        self,
        query: StandardizedPriceStateResultQuery = StandardizedPriceStateResultQuery(),
    ) -> tuple[StandardizedPriceStateResult, ...]:
        return ()

    def get_result(self, calculation_id: UUID) -> StandardizedPriceStateResult | None:
        return None

    def list_operations(
        self,
        query: StandardizedPriceStateOperationQuery = StandardizedPriceStateOperationQuery(),
    ) -> tuple[StandardizedPriceStateOperationAttempt, ...]:
        return ()


__all__ = [
    "EmptyStandardizedPriceStateQueryService",
    "StandardizedPriceStateQueryService",
    "StandardizedPriceStateStore",
]
