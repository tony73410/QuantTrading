"""Application orchestration for factor calculation followed by a decision."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from quant_trading.decision.engine import TradingDecisionEngine
from quant_trading.decision.models import (
    DecisionContext,
    DecisionInput,
    DecisionResult,
    PortfolioSnapshot,
)
from quant_trading.error_codes import ErrorCode
from quant_trading.factors.engine import SingleAssetFactorEngine
from quant_trading.factors.interfaces import FactorSnapshotStore
from quant_trading.factors.models import (
    FactorContext,
    FactorSnapshot,
    FactorSnapshotCollection,
    MarketDataWindow,
)


@dataclass(frozen=True, slots=True)
class AnalysisDecisionRequest:
    market_data: MarketDataWindow
    factor_context: FactorContext
    portfolio: PortfolioSnapshot
    decision_context: DecisionContext
    policy_name: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if self.factor_context.as_of_utc != self.market_data.as_of_utc:
            raise ValueError("factor context and market data must share as_of")
        if self.decision_context.as_of_utc != self.market_data.as_of_utc:
            raise ValueError("pipeline currently requires one shared as_of time")


@dataclass(frozen=True, slots=True)
class AnalysisDecisionResult:
    factor_snapshot: FactorSnapshot
    decision_result: DecisionResult


class AnalysisDecisionPipeline:
    """Connect the two layers without owning factor or decision logic."""

    def __init__(
        self,
        factor_engine: SingleAssetFactorEngine,
        decision_engine: TradingDecisionEngine,
        *,
        factor_store: FactorSnapshotStore | None = None,
        collection_id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._factor_engine = factor_engine
        self._decision_engine = decision_engine
        self._factor_store = factor_store
        self._collection_id_factory = collection_id_factory

    def run(self, request: AnalysisDecisionRequest) -> AnalysisDecisionResult:
        calculation_run_id = None
        if self._factor_store is not None:
            calculation_run_id = self._factor_store.begin_calculation(
                request.market_data,
                correlation_id=request.correlation_id,
            )
        try:
            factor_snapshot = self._factor_engine.calculate(
                request.market_data,
                request.factor_context,
            )
        except Exception as exc:
            if self._factor_store is not None and calculation_run_id is not None:
                self._factor_store.complete_calculation_failure(
                    calculation_run_id,
                    error_code=ErrorCode.FACTOR_CALCULATION.value,
                    error_summary=f"{type(exc).__name__}: {exc}",
                )
            raise
        if self._factor_store is not None and calculation_run_id is not None:
            factor_snapshot = self._factor_store.complete_calculation_success(
                calculation_run_id,
                factor_snapshot,
                request.market_data,
            )
        factor_collection = FactorSnapshotCollection(
            collection_id=self._collection_id_factory(),
            as_of_utc=factor_snapshot.as_of_utc,
            snapshots=(factor_snapshot,),
        )
        decision_result = self._decision_engine.evaluate(
            request.policy_name,
            DecisionInput(
                factors=factor_collection,
                portfolio=request.portfolio,
                context=request.decision_context,
            ),
        )
        return AnalysisDecisionResult(factor_snapshot, decision_result)
