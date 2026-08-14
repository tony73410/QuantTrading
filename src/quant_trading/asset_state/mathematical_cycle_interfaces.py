"""Ports for disabled mathematical-cycle state."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .mathematical_cycle_models import (
    MathematicalCycleMaterialization,
    MathematicalCycleQuery,
    MathematicalCycleStateDefinition,
    MathematicalCycleStateOperation,
    MathematicalCycleStream,
    MathematicalCycleStreamDetail,
)


class MathematicalCycleStateStore(Protocol):
    def initialize(self) -> None: ...
    def get_definition(self, definition_id: UUID) -> MathematicalCycleStateDefinition | None: ...
    def get_first_operation(self, operation_id: UUID) -> MathematicalCycleStateOperation | None: ...
    def get_stream(self, stream_id: UUID) -> MathematicalCycleStream | None: ...
    def get_stream_detail(self, stream_id: UUID) -> MathematicalCycleStreamDetail | None: ...
    def save_definition(self, definition: MathematicalCycleStateDefinition, operation: MathematicalCycleStateOperation) -> None: ...
    def save_materialization(self, operation: MathematicalCycleStateOperation, materialization: MathematicalCycleMaterialization, *, prior_detail: MathematicalCycleStreamDetail | None) -> None: ...
    def save_operation(self, operation: MathematicalCycleStateOperation) -> None: ...


class MathematicalCycleStateQueryService(Protocol):
    def get_definition(self, definition_id: UUID) -> MathematicalCycleStateDefinition | None: ...
    def list_definitions(self, *, include_archived: bool = False, limit: int = 500) -> tuple[MathematicalCycleStateDefinition, ...]: ...
    def get_stream(self, stream_id: UUID) -> MathematicalCycleStream | None: ...
    def get_stream_detail(self, stream_id: UUID) -> MathematicalCycleStreamDetail | None: ...
    def list_streams(self, query: MathematicalCycleQuery = MathematicalCycleQuery()) -> tuple[MathematicalCycleStream, ...]: ...
    def list_operations(self, query: MathematicalCycleQuery = MathematicalCycleQuery()) -> tuple[MathematicalCycleStateOperation, ...]: ...


class EmptyMathematicalCycleStateQueryService:
    def get_definition(self, definition_id): return None
    def list_definitions(self, *, include_archived=False, limit=500): return ()
    def get_stream(self, stream_id): return None
    def get_stream_detail(self, stream_id): return None
    def list_streams(self, query=MathematicalCycleQuery()): return ()
    def list_operations(self, query=MathematicalCycleQuery()): return ()


__all__ = ["EmptyMathematicalCycleStateQueryService", "MathematicalCycleStateQueryService", "MathematicalCycleStateStore"]
