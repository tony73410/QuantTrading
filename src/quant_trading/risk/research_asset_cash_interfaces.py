"""Persistence and query ports for order-3 research asset-cash evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .research_asset_cash_models import (
    ResearchAssetCashOperationAttempt,
    ResearchAssetCashOperationQuery,
    ResearchAssetCashResultQuery,
    ResearchAssetCashSourceLink,
    TargetAdjustmentResearchAssetCashPreviewResult,
)


class ResearchAssetCashStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> ResearchAssetCashOperationAttempt | None: ...
    def save_operation(self, operation: ResearchAssetCashOperationAttempt) -> None: ...
    def save_completed(
        self,
        result: TargetAdjustmentResearchAssetCashPreviewResult,
        operation: ResearchAssetCashOperationAttempt,
        source_link: ResearchAssetCashSourceLink,
    ) -> None: ...


class ResearchAssetCashQueryService(Protocol):
    def list_research_asset_cash_operations(
        self, query: ResearchAssetCashOperationQuery = ResearchAssetCashOperationQuery()
    ) -> tuple[ResearchAssetCashOperationAttempt, ...]: ...
    def list_research_asset_cash_results(
        self, query: ResearchAssetCashResultQuery = ResearchAssetCashResultQuery()
    ) -> tuple[TargetAdjustmentResearchAssetCashPreviewResult, ...]: ...
    def get_research_asset_cash_result(
        self, preview_result_id: UUID
    ) -> TargetAdjustmentResearchAssetCashPreviewResult | None: ...
    def get_research_asset_cash_source_link(
        self, preview_result_id: UUID
    ) -> ResearchAssetCashSourceLink | None: ...


class EmptyResearchAssetCashQueryService:
    def list_research_asset_cash_operations(self, query=ResearchAssetCashOperationQuery()):
        return ()

    def list_research_asset_cash_results(self, query=ResearchAssetCashResultQuery()):
        return ()

    def get_research_asset_cash_result(self, preview_result_id):
        return None

    def get_research_asset_cash_source_link(self, preview_result_id):
        return None


__all__ = [
    "EmptyResearchAssetCashQueryService",
    "ResearchAssetCashQueryService",
    "ResearchAssetCashStore",
]
