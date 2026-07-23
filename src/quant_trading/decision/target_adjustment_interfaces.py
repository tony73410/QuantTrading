"""Public persistence/query ports for target-adjustment Decision research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .target_adjustment_models import (
    TargetAdjustmentDecisionOperationAttempt,
    TargetAdjustmentDecisionQuery,
    TargetAdjustmentDecisionResult,
    TargetAdjustmentDecisionSourceLink,
    TargetAdjustmentTradeIntent,
)


class TargetAdjustmentDecisionStore(Protocol):
    def initialize(self) -> None: ...

    def get_first_operation(
        self, operation_id: UUID
    ) -> TargetAdjustmentDecisionOperationAttempt | None: ...

    def save_operation(self, operation: TargetAdjustmentDecisionOperationAttempt) -> None: ...

    def save_completed(
        self,
        result: TargetAdjustmentDecisionResult,
        operation: TargetAdjustmentDecisionOperationAttempt,
        source_link: TargetAdjustmentDecisionSourceLink,
    ) -> None: ...


class TargetAdjustmentDecisionQueryService(Protocol):
    def list_target_adjustment_operations(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionOperationAttempt, ...]: ...

    def list_target_adjustment_results(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionResult, ...]: ...

    def get_target_adjustment_result(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionResult | None: ...

    def get_target_adjustment_source_link(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionSourceLink | None: ...

    def get_target_adjustment_intent(
        self, intent_id: UUID
    ) -> TargetAdjustmentTradeIntent | None: ...


class EmptyTargetAdjustmentDecisionQueryService:
    def list_target_adjustment_operations(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionOperationAttempt, ...]:
        return ()

    def list_target_adjustment_results(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionResult, ...]:
        return ()

    def get_target_adjustment_result(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionResult | None:
        return None

    def get_target_adjustment_source_link(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionSourceLink | None:
        return None

    def get_target_adjustment_intent(self, intent_id: UUID) -> TargetAdjustmentTradeIntent | None:
        return None


__all__ = [
    "EmptyTargetAdjustmentDecisionQueryService",
    "TargetAdjustmentDecisionQueryService",
    "TargetAdjustmentDecisionStore",
]
