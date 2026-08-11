"""Public persistence/query ports for P23-3A cycle-aware target research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .cycle_models import (
    AssetCycleTargetConfiguration,
    CycleTargetFormulaDefinition,
    CycleTargetOperation,
    CycleTargetQuery,
    CycleTargetPositionResult,
)


class CycleTargetPositionStore(Protocol):
    def initialize(self) -> None: ...
    def get_formula_definition(self, definition_id: UUID) -> CycleTargetFormulaDefinition | None: ...
    def get_configuration(self, configuration_id: UUID) -> AssetCycleTargetConfiguration | None: ...
    def get_first_operation(self, operation_id: UUID) -> CycleTargetOperation | None: ...
    def save_formula_definition(
        self, definition: CycleTargetFormulaDefinition, operation: CycleTargetOperation
    ) -> None: ...
    def save_configuration(
        self, configuration: AssetCycleTargetConfiguration, operation: CycleTargetOperation
    ) -> None: ...
    def save_preview(
        self, result: CycleTargetPositionResult, operation: CycleTargetOperation
    ) -> None: ...
    def save_operation(self, operation: CycleTargetOperation) -> None: ...


class CycleTargetPositionQueryService(Protocol):
    def get_formula_definition(self, definition_id: UUID) -> CycleTargetFormulaDefinition | None: ...
    def list_formula_definitions(
        self, *, include_archived: bool = False, limit: int = 500
    ) -> tuple[CycleTargetFormulaDefinition, ...]: ...
    def get_configuration(self, configuration_id: UUID) -> AssetCycleTargetConfiguration | None: ...
    def list_configurations(
        self, query: CycleTargetQuery = CycleTargetQuery()
    ) -> tuple[AssetCycleTargetConfiguration, ...]: ...
    def get_operation(self, attempt_id: UUID) -> CycleTargetOperation | None: ...
    def list_operations(
        self, query: CycleTargetQuery = CycleTargetQuery()
    ) -> tuple[CycleTargetOperation, ...]: ...
    def get_result(self, result_id: UUID) -> CycleTargetPositionResult | None: ...
    def list_results(
        self, query: CycleTargetQuery = CycleTargetQuery()
    ) -> tuple[CycleTargetPositionResult, ...]: ...


class EmptyCycleTargetPositionQueryService:
    def get_formula_definition(self, definition_id):
        return None

    def list_formula_definitions(self, *, include_archived=False, limit=500):
        return ()

    def get_configuration(self, configuration_id):
        return None

    def list_configurations(self, query=CycleTargetQuery()):
        return ()

    def get_operation(self, attempt_id):
        return None

    def list_operations(self, query=CycleTargetQuery()):
        return ()

    def get_result(self, result_id):
        return None

    def list_results(self, query=CycleTargetQuery()):
        return ()


__all__ = [
    "CycleTargetPositionStore",
    "CycleTargetPositionQueryService",
    "EmptyCycleTargetPositionQueryService",
]
