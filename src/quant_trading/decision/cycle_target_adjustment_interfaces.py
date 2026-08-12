"""Public persistence/query ports for P23-4A cycle-target Decision evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .cycle_target_adjustment_models import (
    CycleTargetAdjustmentDecisionResult,
    CycleTargetAdjustmentOperationAttempt,
    CycleTargetAdjustmentQuery,
    CycleTargetAdjustmentSourceLink,
    CycleTargetAdjustmentTradeIntent,
)


class CycleTargetAdjustmentDecisionStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(
        self, operation_id: UUID
    ) -> CycleTargetAdjustmentOperationAttempt | None: ...
    def save_operation(self, operation: CycleTargetAdjustmentOperationAttempt) -> None: ...
    def save_completed(
        self,
        result: CycleTargetAdjustmentDecisionResult,
        operation: CycleTargetAdjustmentOperationAttempt,
        source_link: CycleTargetAdjustmentSourceLink,
    ) -> None: ...


class CycleTargetAdjustmentDecisionQueryService(Protocol):
    def list_cycle_target_adjustment_operations(
        self, query: CycleTargetAdjustmentQuery = CycleTargetAdjustmentQuery()
    ) -> tuple[CycleTargetAdjustmentOperationAttempt, ...]: ...
    def list_cycle_target_adjustment_results(
        self, query: CycleTargetAdjustmentQuery = CycleTargetAdjustmentQuery()
    ) -> tuple[CycleTargetAdjustmentDecisionResult, ...]: ...
    def get_cycle_target_adjustment_result(
        self, decision_result_id: UUID
    ) -> CycleTargetAdjustmentDecisionResult | None: ...
    def get_cycle_target_adjustment_source_link(
        self, decision_result_id: UUID
    ) -> CycleTargetAdjustmentSourceLink | None: ...
    def get_cycle_target_adjustment_intent(
        self, intent_id: UUID
    ) -> CycleTargetAdjustmentTradeIntent | None: ...


class EmptyCycleTargetAdjustmentDecisionQueryService:
    def list_cycle_target_adjustment_operations(self, query=CycleTargetAdjustmentQuery()):
        return ()

    def list_cycle_target_adjustment_results(self, query=CycleTargetAdjustmentQuery()):
        return ()

    def get_cycle_target_adjustment_result(self, decision_result_id):
        return None

    def get_cycle_target_adjustment_source_link(self, decision_result_id):
        return None

    def get_cycle_target_adjustment_intent(self, intent_id):
        return None


__all__ = [
    "CycleTargetAdjustmentDecisionQueryService",
    "CycleTargetAdjustmentDecisionStore",
    "EmptyCycleTargetAdjustmentDecisionQueryService",
]
