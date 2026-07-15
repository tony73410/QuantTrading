from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import get_type_hints
from uuid import UUID

from quant_trading.decision import (
    DecisionAction,
    DecisionContext,
    DecisionInput,
    DecisionResult,
    DecisionStatus,
    PortfolioSnapshot,
    TradeIntent,
    TradingDecisionEngine,
)
from quant_trading.factors import (
    FactorContext,
    FactorResult,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
    SingleAssetFactorEngine,
)
from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe
from quant_trading.orchestration import AnalysisDecisionPipeline, AnalysisDecisionRequest
from quant_trading.orchestration import TradingEvaluationPipeline, TradingEvaluationRequest
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore
from quant_trading.risk import (
    AccountSnapshot,
    MarketRiskContext,
    OpenOrdersSnapshot,
    RiskContext,
    RiskDecisionType,
    RiskEngine,
    RiskEvaluationContext,
    RiskReasonCode,
    RiskRuleDecision,
    RiskRuleResult,
    SystemRiskState,
)
from quant_trading.application_settings import ExecutionEnvironment


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 7, 13, 21, 1, tzinfo=UTC)
FACTOR_ID = UUID("00000000-0000-0000-0000-000000000301")
COLLECTION_ID = UUID("00000000-0000-0000-0000-000000000302")
PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000303")
DECISION_ID = UUID("00000000-0000-0000-0000-000000000304")
INTENT_ID = UUID("00000000-0000-0000-0000-000000000305")
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000306")
ORDERS_ID = UUID("00000000-0000-0000-0000-000000000307")
RISK_ID = UUID("00000000-0000-0000-0000-000000000308")


class FakeFactor:
    factor_name = "pipeline_test_factor"
    factor_version = "test-v1"
    minimum_observations = 1
    output_unit = "test-unit"
    missing_input_policy = "return explicit non-valid status"

    def calculate(
        self, market_data: MarketDataWindow, context: FactorContext
    ) -> FactorResult:
        bar = market_data.bars[-1]
        return FactorResult(
            market_data.symbol,
            context.as_of_utc,
            market_data.timeframe,
            self.factor_name,
            self.factor_version,
            bar.close,
            self.output_unit,
            context.parameters,
            self.minimum_observations,
            FactorStatus.VALID,
            ("TEST_ONLY",),
            CREATED_AT,
            bar.timestamp_utc,
            bar.timestamp_utc,
        )


class FakePolicy:
    policy_name = "pipeline_test_policy"
    policy_version = "test-v1"

    def evaluate(self, decision_input: DecisionInput) -> DecisionResult:
        factor_snapshot = decision_input.factors.snapshots[0]
        intent = TradeIntent(
            INTENT_ID,
            DECISION_ID,
            factor_snapshot.symbol,
            decision_input.context.as_of_utc,
            DecisionAction.NO_DECISION,
            None,
            None,
            None,
            None,
            None,
            ("TEST_ONLY",),
            factor_snapshot.snapshot_id,
            self.policy_name,
            self.policy_version,
            CREATED_AT,
        )
        return DecisionResult(
            DECISION_ID,
            decision_input.context.as_of_utc,
            self.policy_name,
            self.policy_version,
            decision_input.context.parameters,
            (factor_snapshot.snapshot_id,),
            DecisionStatus.VALID,
            (intent,),
            ("TEST_ONLY",),
            CREATED_AT,
        )


class AlternativeFakeFactor(FakeFactor):
    factor_version = "test-v2"

    def calculate(
        self, market_data: MarketDataWindow, context: FactorContext
    ) -> FactorResult:
        return replace(
            super().calculate(market_data, context),
            factor_version=self.factor_version,
            value=Decimal("200"),
        )


class FakeRiskPolicy:
    policy_name = "pipeline_test_risk"
    policy_version = "test-v1"

    def evaluate(
        self, trade_intent: TradeIntent, context: RiskEvaluationContext
    ) -> RiskRuleResult:
        return RiskRuleResult(
            self.policy_name,
            self.policy_version,
            RiskRuleDecision.APPROVE,
            (RiskReasonCode.MANUAL_REVIEW,),
        )


def _window() -> MarketDataWindow:
    bar = MarketBar(
        "AAPL",
        datetime(2026, 7, 10, 13, 30, tzinfo=UTC),
        Decimal("100"),
        Decimal("101"),
        Decimal("99"),
        Decimal("100.50"),
        100,
        Decimal("100.25"),
        10,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        "test",
        AS_OF,
    )
    return MarketDataWindow(
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        (MarketDataObservation(bar, AS_OF),),
    )


def test_factor_then_decision_pipeline_uses_only_public_contracts() -> None:
    factor_engine = SingleAssetFactorEngine(
        (FakeFactor(),),
        clock=lambda: CREATED_AT,
        id_factory=lambda: FACTOR_ID,
    )
    decision_engine = TradingDecisionEngine(
        (FakePolicy(),),
        clock=lambda: CREATED_AT,
        id_factory=lambda: DECISION_ID,
    )
    pipeline = AnalysisDecisionPipeline(
        factor_engine,
        decision_engine,
        collection_id_factory=lambda: COLLECTION_ID,
    )

    result = pipeline.run(
        AnalysisDecisionRequest(
            market_data=_window(),
            factor_context=FactorContext(AS_OF),
            portfolio=PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
            decision_context=DecisionContext(AS_OF),
            policy_name="pipeline_test_policy",
        )
    )

    assert result.factor_snapshot.results[0].value == Decimal("100.50")
    assert result.decision_result.factor_snapshot_ids == (FACTOR_ID,)
    assert result.decision_result.intents[0].action is DecisionAction.NO_DECISION


def test_pipeline_persists_factor_snapshot_before_decision(tmp_path) -> None:
    store = SQLiteFactorSnapshotStore(tmp_path / "market_history.sqlite3")
    store.initialize()
    factor_engine = SingleAssetFactorEngine(
        (FakeFactor(),),
        clock=lambda: CREATED_AT,
        id_factory=lambda: FACTOR_ID,
    )
    pipeline = AnalysisDecisionPipeline(
        factor_engine,
        TradingDecisionEngine(
            (FakePolicy(),),
            clock=lambda: CREATED_AT,
            id_factory=lambda: DECISION_ID,
        ),
        factor_store=store,
        collection_id_factory=lambda: COLLECTION_ID,
    )
    result = pipeline.run(
        AnalysisDecisionRequest(
            market_data=_window(),
            factor_context=FactorContext(AS_OF),
            portfolio=PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
            decision_context=DecisionContext(AS_OF),
            policy_name="pipeline_test_policy",
            correlation_id="REQ-PIPELINE",
        )
    )

    stored = store.query_snapshots(
        symbol="AAPL",
        start_time=AS_OF.replace(day=12),
        end_time=AS_OF.replace(day=14),
    )
    assert stored == [result.factor_snapshot]
    assert result.decision_result.factor_snapshot_ids == (
        result.factor_snapshot.snapshot_id,
    )


def test_pipeline_public_annotations_are_resolvable() -> None:
    hints = get_type_hints(AnalysisDecisionPipeline.__init__)
    assert "collection_id_factory" in hints


def test_replacing_factor_implementation_does_not_change_decision_policy() -> None:
    for calculator, expected in (
        (FakeFactor(), Decimal("100.50")),
        (AlternativeFakeFactor(), Decimal("200")),
    ):
        pipeline = AnalysisDecisionPipeline(
            SingleAssetFactorEngine(
                (calculator,),
                clock=lambda: CREATED_AT,
                id_factory=lambda: FACTOR_ID,
            ),
            TradingDecisionEngine(
                (FakePolicy(),),
                clock=lambda: CREATED_AT,
                id_factory=lambda: DECISION_ID,
            ),
            collection_id_factory=lambda: COLLECTION_ID,
        )
        result = pipeline.run(
            AnalysisDecisionRequest(
                _window(),
                FactorContext(AS_OF),
                PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
                DecisionContext(AS_OF),
                "pipeline_test_policy",
            )
        )
        assert result.factor_snapshot.results[0].value == expected
        assert result.decision_result.policy_name == "pipeline_test_policy"


def test_factor_decision_risk_pipeline_stops_before_execution() -> None:
    analysis = AnalysisDecisionPipeline(
        SingleAssetFactorEngine(
            (FakeFactor(),),
            clock=lambda: CREATED_AT,
            id_factory=lambda: FACTOR_ID,
        ),
        TradingDecisionEngine(
            (FakePolicy(),),
            clock=lambda: CREATED_AT,
            id_factory=lambda: DECISION_ID,
        ),
        collection_id_factory=lambda: COLLECTION_ID,
    )
    pipeline = TradingEvaluationPipeline(
        analysis,
        RiskEngine(
            (FakeRiskPolicy(),),
            clock=lambda: CREATED_AT,
            id_factory=lambda: RISK_ID,
        ),
        collection_id_factory=lambda: COLLECTION_ID,
    )

    result = pipeline.run(
        TradingEvaluationRequest(
            AnalysisDecisionRequest(
                _window(),
                FactorContext(AS_OF),
                PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
                DecisionContext(AS_OF),
                "pipeline_test_policy",
            ),
            AccountSnapshot(ACCOUNT_ID, AS_OF),
            OpenOrdersSnapshot(ORDERS_ID, AS_OF),
            MarketRiskContext(AS_OF, AS_OF, True),
            SystemRiskState(AS_OF),
            RiskContext(
                AS_OF,
                "test-config-v1",
                ExecutionEnvironment.ALPACA_PAPER,
            ),
        )
    )

    assert result.analysis.factor_snapshot.results[0].status is FactorStatus.VALID
    assert result.analysis.decision_result.intents[0].intent_id == INTENT_ID
    assert result.risk_decisions[0].decision is RiskDecisionType.APPROVED
    assert not hasattr(result, "order_request")
    assert not hasattr(result, "execution_result")
