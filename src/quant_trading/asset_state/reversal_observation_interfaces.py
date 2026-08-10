"""Persistence and read-only query ports for P23-2 research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .reversal_observation_models import (
    ReversalObservationDefinition,
    ReversalObservationOperation,
    ReversalObservationQuery,
    ReversalObservationResult,
)


class ReversalObservationStore(Protocol):
    def initialize(self) -> None: ...
    def get_definition(self, definition_id: UUID) -> ReversalObservationDefinition | None: ...
    def get_first_operation(self, operation_id: UUID) -> ReversalObservationOperation | None: ...
    def get_result_by_fingerprint(self, fingerprint: str) -> ReversalObservationResult | None: ...
    def save_definition(
        self,
        definition: ReversalObservationDefinition,
        operation: ReversalObservationOperation,
    ) -> None: ...
    def save_operation(self, operation: ReversalObservationOperation) -> None: ...


class ReversalObservationQueryService(Protocol):
    def get_definition(self, definition_id: UUID) -> ReversalObservationDefinition | None: ...
    def list_definitions(self, *, include_archived: bool = False, limit: int = 500) -> tuple[ReversalObservationDefinition, ...]: ...
    def list_operations(
        self, query: ReversalObservationQuery = ReversalObservationQuery()
    ) -> tuple[ReversalObservationOperation, ...]: ...
    def get_operation(self, attempt_id: UUID) -> ReversalObservationOperation | None: ...
    def get_result(self, result_id: UUID) -> ReversalObservationResult | None: ...


class EmptyReversalObservationQueryService:
    def get_definition(self, definition_id: UUID):
        return None

    def list_definitions(self, *, include_archived: bool = False, limit: int = 500):
        return ()

    def list_operations(self, query: ReversalObservationQuery = ReversalObservationQuery()):
        return ()

    def get_operation(self, attempt_id: UUID):
        return None

    def get_result(self, result_id: UUID):
        return None


__all__ = [
    "EmptyReversalObservationQueryService",
    "ReversalObservationQueryService",
    "ReversalObservationStore",
]
