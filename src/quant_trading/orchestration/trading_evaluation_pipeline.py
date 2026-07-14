"""Three-layer evaluation ending at risk review, never order execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from quant_trading.factors.models import FactorSnapshotCollection
from quant_trading.risk.engine import RiskEngine
from quant_trading.risk.models import (
    AccountSnapshot,
    MarketRiskContext,
    OpenOrdersSnapshot,
    RiskContext,
    RiskDecision,
    RiskEvaluationContext,
    SystemRiskState,
)

from .analysis_decision_pipeline import (
    AnalysisDecisionPipeline,
    AnalysisDecisionRequest,
    AnalysisDecisionResult,
)


@dataclass(frozen=True, slots=True)
class TradingEvaluationRequest:
    analysis: AnalysisDecisionRequest
    account: AccountSnapshot
    open_orders: OpenOrdersSnapshot
    market: MarketRiskContext
    system_risk: SystemRiskState
    risk_context: RiskContext

    def __post_init__(self) -> None:
        if self.risk_context.as_of_utc != self.analysis.decision_context.as_of_utc:
            raise ValueError("analysis and risk evaluation must share as_of")


@dataclass(frozen=True, slots=True)
class TradingEvaluationResult:
    analysis: AnalysisDecisionResult
    risk_decisions: tuple[RiskDecision, ...]


class TradingEvaluationPipeline:
    """Run Factor -> Decision -> Risk and stop before order construction."""

    def __init__(
        self,
        analysis_pipeline: AnalysisDecisionPipeline,
        risk_engine: RiskEngine,
        *,
        collection_id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._analysis_pipeline = analysis_pipeline
        self._risk_engine = risk_engine
        self._collection_id_factory = collection_id_factory

    def run(self, request: TradingEvaluationRequest) -> TradingEvaluationResult:
        analysis = self._analysis_pipeline.run(request.analysis)
        factors = FactorSnapshotCollection(
            self._collection_id_factory(),
            analysis.factor_snapshot.as_of_utc,
            (analysis.factor_snapshot,),
        )
        evaluation_context = RiskEvaluationContext(
            factors,
            request.analysis.portfolio,
            request.account,
            request.open_orders,
            request.market,
            request.system_risk,
            request.risk_context,
        )
        risk_decisions = tuple(
            self._risk_engine.evaluate(intent, evaluation_context)
            for intent in analysis.decision_result.intents
        )
        return TradingEvaluationResult(analysis, risk_decisions)
