"""Public interfaces for replaceable single-asset factor calculators."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from quant_trading.market_history.models import Adjustment, DataFeed, Timeframe

from .definitions import FactorDefinition
from .models import FactorContext, FactorResult, FactorSnapshot, MarketDataWindow
from .storage_models import FactorCalculationRun
from .history import (
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
    FactorVersionComparison,
    FactorVersionComparisonQuery,
)


class FactorCalculator(Protocol):
    @property
    def factor_name(self) -> str: ...

    @property
    def factor_version(self) -> str: ...

    @property
    def minimum_observations(self) -> int: ...

    @property
    def output_unit(self) -> str | None: ...

    @property
    def missing_input_policy(self) -> str: ...

    def calculate(
        self,
        market_data: MarketDataWindow,
        context: FactorContext,
    ) -> FactorResult: ...


class FactorSnapshotStore(Protocol):
    """Persist factors independently from calculation and decision logic."""

    def initialize(self) -> None: ...

    def begin_calculation(
        self,
        market_data: MarketDataWindow,
        *,
        correlation_id: str | None = None,
        algorithm_run_id: UUID | None = None,
        stage_id: UUID | None = None,
    ) -> UUID: ...

    def complete_calculation_success(
        self,
        run_id: UUID,
        snapshot: FactorSnapshot,
        market_data: MarketDataWindow,
    ) -> FactorSnapshot: ...

    def complete_calculation_failure(
        self,
        run_id: UUID,
        *,
        error_code: str,
        error_summary: str,
    ) -> None: ...

    def query_snapshots(
        self,
        *,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: Timeframe | None = None,
        adjustment: Adjustment | None = None,
        feed: DataFeed | None = None,
    ) -> list[FactorSnapshot]: ...

    def get_calculation_run(self, run_id: UUID) -> FactorCalculationRun | None: ...


class FactorDefinitionStore(Protocol):
    """Persist immutable user-authored definitions without executing them."""

    def list_definitions(self) -> tuple[FactorDefinition, ...]: ...

    def save_definition(self, definition: FactorDefinition) -> None: ...


class FactorHistoryQueryService(Protocol):
    """Read persisted Factor attempts/results without calculating them."""

    def query_factor_history(
        self, query: FactorHistoryQuery = FactorHistoryQuery()
    ) -> tuple[FactorHistoryRecord, ...]: ...

    def compare_factor_versions(
        self, query: FactorVersionComparisonQuery
    ) -> tuple[FactorVersionComparison, ...]: ...


class EmptyFactorHistoryQueryService:
    def query_factor_history(
        self, query: FactorHistoryQuery = FactorHistoryQuery()
    ) -> tuple[FactorHistoryRecord, ...]:
        return ()

    def compare_factor_versions(
        self, query: FactorVersionComparisonQuery
    ) -> tuple[FactorVersionComparison, ...]:
        return ()


class FactorVisualizationQueryService(Protocol):
    """Read exact persisted Factor/source-Bar visualization evidence."""

    def query_factor_visualization(
        self, query: FactorVisualizationQuery
    ) -> FactorVisualizationSeries: ...


class EmptyFactorVisualizationQueryService:
    def query_factor_visualization(
        self, query: FactorVisualizationQuery
    ) -> FactorVisualizationSeries:
        return FactorVisualizationSeries(query, ())
