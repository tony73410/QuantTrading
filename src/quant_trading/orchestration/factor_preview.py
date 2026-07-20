"""Local-data-only Factor previews with durable, non-executing run history."""

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
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)


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
        *,
        run_service: AlgorithmRunService | None = None,
        software_identity: SoftwareIdentity | None = None,
        session_id: str = "algorithm-control",
    ) -> None:
        self._definitions = definitions
        self._window_loader = LocalMarketWindowLoader(market_store)
        self._factor_store = factor_store
        self._run_service = run_service
        self._software_identity = software_identity
        self._session_id = session_id

    def preview(self, request: PreviewRequest) -> PreviewResult:
        if request.kind is not PreviewKind.FACTOR or len(request.component_ids) != 1:
            raise ValueError("Factor preview requires exactly one Factor component")
        algorithm_run = None
        active_stage = None
        calculation_id = None
        try:
            if self._run_service is not None and self._software_identity is not None:
                algorithm_run = self._run_service.start_run(
                    StartRunRequest(
                        AlgorithmRunType.FACTOR_PREVIEW,
                        self._session_id,
                        f"REQ-PREVIEW-{request.preview_id.hex.upper()}",
                        request.as_of_utc,
                        (request.symbol,),
                        "algorithm_control.factor_preview",
                        "local_user",
                        self._software_identity,
                    )
                )
            definition = self._definitions.get_by_component_id(request.component_ids[0])
            if algorithm_run is not None and self._run_service is not None:
                self._run_service.bind(
                    algorithm_run.run_id,
                    RunBindingType.FACTOR_DEFINITION,
                    definition.factor_id,
                    str(definition.version),
                    source_reference=str(definition.definition_id),
                )
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.MARKET_DATA, 1
                )
            window = self._window_loader.load(request)
            if active_stage is not None and self._run_service is not None:
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="market_data_window",
                    result_id=(
                        f"{request.symbol}:{request.timeframe.value}:"
                        f"{request.adjustment.value}:{request.feed.value}:"
                        f"{request.as_of_utc.isoformat()}"
                    ),
                )
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.FACTOR, 2
                )
            engine = SingleAssetFactorEngine((SafeExpressionFactorCalculator(definition),))
            should_persist = self._factor_store is not None and (
                request.persist_factor_snapshot or algorithm_run is not None
            )
            if should_persist and self._factor_store is not None:
                calculation_id = self._factor_store.begin_calculation(
                    window,
                    correlation_id=f"REQ-PREVIEW-{request.preview_id.hex.upper()}",
                    algorithm_run_id=algorithm_run.run_id if algorithm_run else None,
                    stage_id=active_stage.stage_id if active_stage else None,
                )
            snapshot = engine.calculate(
                window,
                FactorContext(request.as_of_utc, request.factor_parameters),
            )
            if calculation_id is not None and self._factor_store is not None:
                snapshot = self._factor_store.complete_calculation_success(
                    calculation_id, snapshot, window
                )
            result = snapshot.results[0]
            warning = result.status is not FactorStatus.VALID
            if active_stage is not None and self._run_service is not None:
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="factor_snapshot",
                    result_id=str(snapshot.snapshot_id),
                    with_warnings=warning,
                )
                self._run_service.complete_run(
                    algorithm_run.run_id, with_warnings=warning
                )
        except Exception as exc:
            summary = f"{type(exc).__name__}: {exc}"
            if calculation_id is not None and self._factor_store is not None:
                try:
                    self._factor_store.complete_calculation_failure(
                        calculation_id,
                        error_code="QT-FACTOR-001",
                        error_summary=summary,
                    )
                except Exception:
                    pass
            if algorithm_run is not None and self._run_service is not None:
                try:
                    if active_stage is not None and not active_stage.status.terminal:
                        self._run_service.fail_stage(
                            active_stage,
                            error_code="QT-FACTOR-001",
                            error_summary=summary,
                        )
                    self._run_service.fail_run(
                        algorithm_run.run_id,
                        error_code="QT-PREVIEW-FAILED",
                        error_summary=summary,
                    )
                except Exception:
                    pass
            raise
        status = (
            PreviewStatus.COMPLETED
            if result.status is FactorStatus.VALID
            else PreviewStatus.WARNING
        )
        persistence = (
            "并已保存到中央 SQLite 因子历史"
            if calculation_id is not None
            else "未保存，仅预览"
        )
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
            run_id=algorithm_run.run_id if algorithm_run else None,
        )
