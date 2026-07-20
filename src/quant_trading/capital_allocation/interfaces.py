"""Public persistence and read-only query ports for capital allocation."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import (
    CapitalAllocationTransferEvent,
    CapitalOperationAttempt,
    CapitalPlan,
    CapitalPlanDetail,
    CapitalPlanQuery,
    CapitalPlanSummary,
    CapitalSnapshot,
)


class CapitalAllocationStore(Protocol):
    def initialize(self) -> None: ...

    def get_plan(self, plan_id: UUID) -> CapitalPlan | None: ...

    def get_latest_snapshot(self, plan_id: UUID) -> CapitalSnapshot | None: ...

    def get_transfer(self, transfer_id: UUID) -> CapitalAllocationTransferEvent | None: ...

    def save_operation(self, operation: CapitalOperationAttempt) -> None: ...

    def create_plan(
        self,
        plan: CapitalPlan,
        snapshot: CapitalSnapshot,
        operation: CapitalOperationAttempt,
    ) -> None: ...

    def append_transfer(
        self,
        transfer: CapitalAllocationTransferEvent,
        snapshot: CapitalSnapshot,
        operation: CapitalOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None: ...


class CapitalAllocationQueryService(Protocol):
    def list_plans(
        self, query: CapitalPlanQuery = CapitalPlanQuery()
    ) -> tuple[CapitalPlanSummary, ...]: ...

    def get_plan_detail(self, plan_id: UUID) -> CapitalPlanDetail | None: ...


class EmptyCapitalAllocationQueryService:
    def list_plans(
        self, query: CapitalPlanQuery = CapitalPlanQuery()
    ) -> tuple[CapitalPlanSummary, ...]:
        return ()

    def get_plan_detail(self, plan_id: UUID) -> CapitalPlanDetail | None:
        return None


__all__ = [
    "CapitalAllocationQueryService",
    "CapitalAllocationStore",
    "EmptyCapitalAllocationQueryService",
]
