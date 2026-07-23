"""Persistence and query ports for target-adjustment Risk evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .target_adjustment_models import (
    TargetAdjustmentRiskOperationAttempt,
    TargetAdjustmentRiskQuery,
    TargetAdjustmentRiskReviewResult,
    TargetAdjustmentRiskSourceLink,
)


class TargetAdjustmentRiskStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> TargetAdjustmentRiskOperationAttempt | None: ...
    def save_operation(self, operation: TargetAdjustmentRiskOperationAttempt) -> None: ...
    def save_completed(self, result: TargetAdjustmentRiskReviewResult, operation: TargetAdjustmentRiskOperationAttempt, source_link: TargetAdjustmentRiskSourceLink) -> None: ...


class TargetAdjustmentRiskQueryService(Protocol):
    def list_target_adjustment_risk_operations(self, query: TargetAdjustmentRiskQuery = TargetAdjustmentRiskQuery()) -> tuple[TargetAdjustmentRiskOperationAttempt, ...]: ...
    def list_target_adjustment_risk_results(self, query: TargetAdjustmentRiskQuery = TargetAdjustmentRiskQuery()) -> tuple[TargetAdjustmentRiskReviewResult, ...]: ...
    def get_target_adjustment_risk_result(self, review_result_id: UUID) -> TargetAdjustmentRiskReviewResult | None: ...
    def get_target_adjustment_risk_source_link(self, review_result_id: UUID) -> TargetAdjustmentRiskSourceLink | None: ...


class EmptyTargetAdjustmentRiskQueryService:
    def list_target_adjustment_risk_operations(self, query=TargetAdjustmentRiskQuery()): return ()
    def list_target_adjustment_risk_results(self, query=TargetAdjustmentRiskQuery()): return ()
    def get_target_adjustment_risk_result(self, review_result_id): return None
    def get_target_adjustment_risk_source_link(self, review_result_id): return None


__all__ = ["EmptyTargetAdjustmentRiskQueryService", "TargetAdjustmentRiskQueryService", "TargetAdjustmentRiskStore"]
