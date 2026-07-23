"""Persistence and query ports for single-asset exposure-cap evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .exposure_cap_models import (
    ExposureCapDefinitionQuery,
    ExposureCapOperationAttempt,
    ExposureCapOperationQuery,
    ExposureCapResultQuery,
    ExposureCapSourceLink,
    SingleAssetExposureCapDefinitionVersion,
    TargetAdjustmentExposureCapPreviewResult,
)


class ExposureCapStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> ExposureCapOperationAttempt | None: ...
    def get_definition(self, definition_id: UUID, definition_version: int) -> SingleAssetExposureCapDefinitionVersion | None: ...
    def get_latest_definition(self, definition_id: UUID) -> SingleAssetExposureCapDefinitionVersion | None: ...
    def save_definition(self, definition: SingleAssetExposureCapDefinitionVersion, operation: ExposureCapOperationAttempt) -> None: ...
    def save_operation(self, operation: ExposureCapOperationAttempt) -> None: ...
    def save_completed(self, result: TargetAdjustmentExposureCapPreviewResult, operation: ExposureCapOperationAttempt, source_link: ExposureCapSourceLink) -> None: ...


class ExposureCapQueryService(Protocol):
    def list_exposure_cap_definitions(self, query: ExposureCapDefinitionQuery = ExposureCapDefinitionQuery()) -> tuple[SingleAssetExposureCapDefinitionVersion, ...]: ...
    def list_exposure_cap_operations(self, query: ExposureCapOperationQuery = ExposureCapOperationQuery()) -> tuple[ExposureCapOperationAttempt, ...]: ...
    def list_exposure_cap_results(self, query: ExposureCapResultQuery = ExposureCapResultQuery()) -> tuple[TargetAdjustmentExposureCapPreviewResult, ...]: ...
    def get_exposure_cap_result(self, preview_result_id: UUID) -> TargetAdjustmentExposureCapPreviewResult | None: ...
    def get_exposure_cap_source_link(self, preview_result_id: UUID) -> ExposureCapSourceLink | None: ...


class EmptyExposureCapQueryService:
    def list_exposure_cap_definitions(self, query=ExposureCapDefinitionQuery()): return ()
    def list_exposure_cap_operations(self, query=ExposureCapOperationQuery()): return ()
    def list_exposure_cap_results(self, query=ExposureCapResultQuery()): return ()
    def get_exposure_cap_result(self, preview_result_id): return None
    def get_exposure_cap_source_link(self, preview_result_id): return None


__all__ = ["EmptyExposureCapQueryService", "ExposureCapQueryService", "ExposureCapStore"]
