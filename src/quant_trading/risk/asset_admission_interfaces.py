"""Persistence and read-only query ports for P23-4C1 admission reviews."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .asset_admission_models import *


class CycleTargetAssetAdmissionStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> CycleTargetAssetAdmissionOperationAttempt | None: ...
    def save_operation(self, operation: CycleTargetAssetAdmissionOperationAttempt) -> None: ...
    def save_completed(self, result: CycleTargetAssetAdmissionReviewResult, operation: CycleTargetAssetAdmissionOperationAttempt, source_link: CycleTargetAssetAdmissionSourceLink) -> None: ...


class CycleTargetAssetAdmissionQueryService(Protocol):
    def list_cycle_target_asset_admission_operations(self, query: CycleTargetAssetAdmissionQuery = CycleTargetAssetAdmissionQuery()) -> tuple[CycleTargetAssetAdmissionOperationAttempt, ...]: ...
    def list_cycle_target_asset_admission_results(self, query: CycleTargetAssetAdmissionQuery = CycleTargetAssetAdmissionQuery()) -> tuple[CycleTargetAssetAdmissionReviewResult, ...]: ...
    def get_cycle_target_asset_admission_result(self, result_id: UUID) -> CycleTargetAssetAdmissionReviewResult | None: ...
    def get_cycle_target_asset_admission_source_link(self, result_id: UUID) -> CycleTargetAssetAdmissionSourceLink | None: ...


class EmptyCycleTargetAssetAdmissionQueryService:
    def list_cycle_target_asset_admission_operations(self, query=CycleTargetAssetAdmissionQuery()): return ()
    def list_cycle_target_asset_admission_results(self, query=CycleTargetAssetAdmissionQuery()): return ()
    def get_cycle_target_asset_admission_result(self, result_id): return None
    def get_cycle_target_asset_admission_source_link(self, result_id): return None


__all__ = ["CycleTargetAssetAdmissionStore", "CycleTargetAssetAdmissionQueryService", "EmptyCycleTargetAssetAdmissionQueryService"]
