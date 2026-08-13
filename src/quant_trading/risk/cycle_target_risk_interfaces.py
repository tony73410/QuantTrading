"""P33 persistence and query ports."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .cycle_target_risk_models import (
    CycleTargetRiskOperationAttempt,
    CycleTargetRiskQuery,
    CycleTargetRiskReviewResult,
    CycleTargetRiskSourceLink,
)


class CycleTargetRiskStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> CycleTargetRiskOperationAttempt | None: ...
    def save_operation(self, operation: CycleTargetRiskOperationAttempt) -> None: ...
    def save_completed(self, result: CycleTargetRiskReviewResult, operation: CycleTargetRiskOperationAttempt, source_link: CycleTargetRiskSourceLink) -> None: ...


class CycleTargetRiskQueryService(Protocol):
    def list_cycle_target_risk_operations(self, query: CycleTargetRiskQuery = CycleTargetRiskQuery()) -> tuple[CycleTargetRiskOperationAttempt, ...]: ...
    def list_cycle_target_risk_results(self, query: CycleTargetRiskQuery = CycleTargetRiskQuery()) -> tuple[CycleTargetRiskReviewResult, ...]: ...
    def get_cycle_target_risk_result(self, review_result_id: UUID) -> CycleTargetRiskReviewResult | None: ...
    def get_cycle_target_risk_source_link(self, review_result_id: UUID) -> CycleTargetRiskSourceLink | None: ...


class EmptyCycleTargetRiskQueryService:
    def list_cycle_target_risk_operations(self, query=CycleTargetRiskQuery()): return ()
    def list_cycle_target_risk_results(self, query=CycleTargetRiskQuery()): return ()
    def get_cycle_target_risk_result(self, review_result_id): return None
    def get_cycle_target_risk_source_link(self, review_result_id): return None


__all__ = ["CycleTargetRiskStore", "CycleTargetRiskQueryService", "EmptyCycleTargetRiskQueryService"]
