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
from .linked_models import (
    LinkedTargetPositionOperationAttempt,
    LinkedTargetPositionQuery,
    StandardizedStateTargetPositionLink,
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

    def get_first_linked_operation(
        self, operation_id: UUID
    ) -> LinkedTargetPositionOperationAttempt | None: ...

    def get_standardized_state_link(
        self, operation_id: UUID
    ) -> StandardizedStateTargetPositionLink | None: ...

    def get_standardized_state_link_by_id(
        self, link_id: UUID
    ) -> StandardizedStateTargetPositionLink | None: ...

    def save_linked_operation(
        self, operation: LinkedTargetPositionOperationAttempt
    ) -> None: ...

    def save_linked_failure(
        self,
        target_operation: TargetPositionOperationAttempt,
        linked_operation: LinkedTargetPositionOperationAttempt,
    ) -> None: ...

    def save_linked_preview(
        self,
        result: TargetPositionResult,
        target_operation: TargetPositionOperationAttempt,
        linked_operation: LinkedTargetPositionOperationAttempt,
        link: StandardizedStateTargetPositionLink,
    ) -> None: ...


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

    def list_linked_operations(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[LinkedTargetPositionOperationAttempt, ...]: ...

    def list_standardized_state_links(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[StandardizedStateTargetPositionLink, ...]: ...

    def get_standardized_state_link(
        self, operation_id: UUID
    ) -> StandardizedStateTargetPositionLink | None: ...

    def get_standardized_state_link_by_id(
        self, link_id: UUID
    ) -> StandardizedStateTargetPositionLink | None: ...


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

    def list_linked_operations(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[LinkedTargetPositionOperationAttempt, ...]:
        return ()

    def list_standardized_state_links(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[StandardizedStateTargetPositionLink, ...]:
        return ()

    def get_standardized_state_link(
        self, operation_id: UUID
    ) -> StandardizedStateTargetPositionLink | None:
        return None

    def get_standardized_state_link_by_id(
        self, link_id: UUID
    ) -> StandardizedStateTargetPositionLink | None:
        return None


__all__ = [
    "EmptyTargetPositionQueryService",
    "TargetPositionQueryService",
    "TargetPositionStore",
]
