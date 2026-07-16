"""Local-data-only Factor preview adapter for the algorithm control center."""

from __future__ import annotations

from datetime import timedelta

from quant_trading.algorithm_control.factor_definition_service import FactorDefinitionService
from quant_trading.algorithm_control.models import (
    PreviewKind,
    PreviewRequest,
    PreviewResult,
    PreviewStatus,
)
from quant_trading.factors import (
    FactorContext,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
    SafeExpressionFactorCalculator,
    SingleAssetFactorEngine,
)
from quant_trading.factors.interfaces import FactorSnapshotStore
from quant_trading.market_history.interfaces import HistoricalDataStore
from quant_trading.market_history.models import HistoricalDataRequest


class LocalMarketWindowLoader:
    """Build point-in-time Factor input from existing local Bars only."""

    def __init__(self, market_store: HistoricalDataStore) -> None:
        self._market_store = market_store

    def load(self, request: PreviewRequest) -> MarketDataWindow:
        start = request.start_utc or request.as_of_utc - timedelta(days=365)
        market_request = HistoricalDataRequest(
            symbol=request.symbol,
            start_time=start,
            end_time=request.as_of_utc,
            timeframe=request.timeframe,
            adjustment=request.adjustment,
            feed=request.feed,
        )
        bars = self._market_store.query_bars(market_request)
        observations = tuple(
            MarketDataObservation(
                bar=bar,
                available_at_utc=bar.timestamp_utc + request.timeframe.approximate_duration,
            )
            for bar in bars
            if bar.timestamp_utc + request.timeframe.approximate_duration <= request.as_of_utc
        )
        return MarketDataWindow(
            symbol=request.symbol,
            as_of_utc=request.as_of_utc,
            timeframe=request.timeframe,
            adjustment=request.adjustment,
            feed=request.feed,
            observations=observations,
        )


class LocalFactorPreviewExecutor:
    """Calculate one Factor from cached Bars; it never downloads or executes."""

    def __init__(
        self,
        definitions: FactorDefinitionService,
        market_store: HistoricalDataStore,
        factor_store: FactorSnapshotStore | None = None,
    ) -> None:
        self._definitions = definitions
        self._window_loader = LocalMarketWindowLoader(market_store)
        self._factor_store = factor_store

    def preview(self, request: PreviewRequest) -> PreviewResult:
        if request.kind is not PreviewKind.FACTOR or len(request.component_ids) != 1:
            raise ValueError("Factor preview requires exactly one Factor component")
        definition = self._definitions.get_by_component_id(request.component_ids[0])
        window = self._window_loader.load(request)
        engine = SingleAssetFactorEngine((SafeExpressionFactorCalculator(definition),))
        run_id = None
        if request.persist_factor_snapshot and self._factor_store is not None:
            run_id = self._factor_store.begin_calculation(
                window,
                correlation_id=str(request.preview_id),
            )
        try:
            snapshot = engine.calculate(
                window,
                FactorContext(request.as_of_utc, request.factor_parameters),
            )
            if run_id is not None and self._factor_store is not None:
                snapshot = self._factor_store.complete_calculation_success(run_id, snapshot, window)
        except Exception as exc:
            if run_id is not None and self._factor_store is not None:
                self._factor_store.complete_calculation_failure(
                    run_id,
                    error_code="QT-FACTOR-001",
                    error_summary=f"{type(exc).__name__}: {exc}",
                )
            raise
        result = snapshot.results[0]
        status = PreviewStatus.COMPLETED if result.status is FactorStatus.VALID else PreviewStatus.WARNING
        persistence = "并已保存到中央 SQLite 因子历史" if request.persist_factor_snapshot else "未保存，仅预览"
        return PreviewResult(
            preview_id=request.preview_id,
            kind=request.kind,
            status=status,
            message=(
                f"Factor={result.factor_name} v{result.factor_version}; "
                f"status={result.status.value}; value={result.value}; "
                f"rows={len(window.observations)}; {persistence}。"
            ),
            no_execution=True,
            factor_snapshot=snapshot,
        )
