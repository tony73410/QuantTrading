"""Public persistence and read-only query ports for target-position research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import (
    TargetPositionCurveDefinition,
    TargetPositionDefinitionQuery,
    TargetPositionOperationAttempt,
    TargetPositionOperationQuery,
    TargetPositionResult,
    TargetPositionResultQuery,
)


class TargetPositionStore(Protocol):
    def initialize(self) -> None: ...

    def get_definition(self, definition_id: UUID) -> TargetPositionCurveDefinition | None: ...

    def get_first_operation(self, operation_id: UUID) -> TargetPositionOperationAttempt | None: ...

    def create_definition(
        self,
        definition: TargetPositionCurveDefinition,
        operation: TargetPositionOperationAttempt,
    ) -> None: ...

    def save_preview(
        self,
        result: TargetPositionResult,
        operation: TargetPositionOperationAttempt,
    ) -> None: ...

    def save_operation(self, operation: TargetPositionOperationAttempt) -> None: ...


class TargetPositionQueryService(Protocol):
    def list_definitions(
        self, query: TargetPositionDefinitionQuery = TargetPositionDefinitionQuery()
    ) -> tuple[TargetPositionCurveDefinition, ...]: ...

    def list_results(
        self, query: TargetPositionResultQuery = TargetPositionResultQuery()
    ) -> tuple[TargetPositionResult, ...]: ...

    def get_result(self, calculation_id: UUID) -> TargetPositionResult | None: ...

    def list_operations(
        self, query: TargetPositionOperationQuery = TargetPositionOperationQuery()
    ) -> tuple[TargetPositionOperationAttempt, ...]: ...


class EmptyTargetPositionQueryService:
    def list_definitions(
        self, query: TargetPositionDefinitionQuery = TargetPositionDefinitionQuery()
    ) -> tuple[TargetPositionCurveDefinition, ...]:
        return ()

    def list_results(
        self, query: TargetPositionResultQuery = TargetPositionResultQuery()
    ) -> tuple[TargetPositionResult, ...]:
        return ()

    def get_result(self, calculation_id: UUID) -> TargetPositionResult | None:
        return None

    def list_operations(
        self, query: TargetPositionOperationQuery = TargetPositionOperationQuery()
    ) -> tuple[TargetPositionOperationAttempt, ...]:
        return ()


__all__ = [
    "EmptyTargetPositionQueryService",
    "TargetPositionQueryService",
    "TargetPositionStore",
]
