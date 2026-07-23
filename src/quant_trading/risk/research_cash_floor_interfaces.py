"""Persistence and query ports for research asset cash-floor evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .research_cash_floor_models import (
    ResearchAssetCashFloorDefinitionVersion,
    ResearchCashFloorDefinitionQuery,
    ResearchCashFloorOperationAttempt,
    ResearchCashFloorOperationQuery,
    ResearchCashFloorResultQuery,
    ResearchCashFloorSourceLink,
    TargetAdjustmentResearchCashFloorPreviewResult,
)


class ResearchCashFloorStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(
        self, operation_id: UUID
    ) -> ResearchCashFloorOperationAttempt | None: ...
    def get_definition(
        self, definition_id: UUID, definition_version: int
    ) -> ResearchAssetCashFloorDefinitionVersion | None: ...
    def get_latest_definition(
        self, definition_id: UUID
    ) -> ResearchAssetCashFloorDefinitionVersion | None: ...
    def save_definition(
        self,
        definition: ResearchAssetCashFloorDefinitionVersion,
        operation: ResearchCashFloorOperationAttempt,
    ) -> None: ...
    def save_operation(self, operation: ResearchCashFloorOperationAttempt) -> None: ...
    def save_completed(
        self,
        result: TargetAdjustmentResearchCashFloorPreviewResult,
        operation: ResearchCashFloorOperationAttempt,
        source_link: ResearchCashFloorSourceLink,
    ) -> None: ...


class ResearchCashFloorQueryService(Protocol):
    def list_research_cash_floor_definitions(
        self, query: ResearchCashFloorDefinitionQuery = ResearchCashFloorDefinitionQuery()
    ) -> tuple[ResearchAssetCashFloorDefinitionVersion, ...]: ...
    def list_research_cash_floor_operations(
        self, query: ResearchCashFloorOperationQuery = ResearchCashFloorOperationQuery()
    ) -> tuple[ResearchCashFloorOperationAttempt, ...]: ...
    def list_research_cash_floor_results(
        self, query: ResearchCashFloorResultQuery = ResearchCashFloorResultQuery()
    ) -> tuple[TargetAdjustmentResearchCashFloorPreviewResult, ...]: ...
    def get_research_cash_floor_result(
        self, preview_result_id: UUID
    ) -> TargetAdjustmentResearchCashFloorPreviewResult | None: ...
    def get_research_cash_floor_source_link(
        self, preview_result_id: UUID
    ) -> ResearchCashFloorSourceLink | None: ...


class EmptyResearchCashFloorQueryService:
    def list_research_cash_floor_definitions(
        self, query=ResearchCashFloorDefinitionQuery()
    ):
        return ()

    def list_research_cash_floor_operations(
        self, query=ResearchCashFloorOperationQuery()
    ):
        return ()

    def list_research_cash_floor_results(self, query=ResearchCashFloorResultQuery()):
        return ()

    def get_research_cash_floor_result(self, preview_result_id):
        return None

    def get_research_cash_floor_source_link(self, preview_result_id):
        return None


__all__ = [
    "EmptyResearchCashFloorQueryService",
    "ResearchCashFloorQueryService",
    "ResearchCashFloorStore",
]
