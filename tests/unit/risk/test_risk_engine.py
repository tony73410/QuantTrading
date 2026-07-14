from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import logging

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.decision import (
    DecisionAction,
    PortfolioSnapshot,
    TradeIntent,
)
from quant_trading.factors import (
    FactorResult,
    FactorSnapshot,
    FactorSnapshotCollection,
    FactorStatus,
)
from quant_trading.market_history.models import Timeframe
from quant_trading.risk import (
    AccountSnapshot,
    MarketRiskContext,
    OpenOrdersSnapshot,
    RiskApprovedTradeIntent,
    RiskContext,
    RiskDecisionType,
    RiskEngine,
    RiskEvaluationContext,
    RiskEvaluationStatus,
    RiskReasonCode,
    RiskRuleDecision,
    RiskRuleResult,
    SystemRiskState,
)
from quant_trading.risk.errors import RiskContractError


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)
CREATED = datetime(2026, 7, 13, 21, 1, tzinfo=UTC)
FACTOR_ID = UUID("00000000-0000-0000-0000-000000000401")
COLLECTION_ID = UUID("00000000-0000-0000-0000-000000000402")
PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000403")
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000404")
ORDERS_ID = UUID("00000000-0000-0000-0000-000000000405")
DECISION_ID = UUID("00000000-0000-0000-0000-000000000406")
INTENT_ID = UUID("00000000-0000-0000-0000-000000000407")
RISK_ID = UUID("00000000-0000-0000-0000-000000000408")


class FakeRiskPolicy:
    policy_version = "test-v1"

    def __init__(
        self,
        policy_name: str,
        decision: RiskRuleDecision,
        reason: RiskReasonCode,
        *,
        approved_target: Decimal | None = None,
        approved_quantity: Decimal | None = None,
        earliest_execution_utc: datetime | None = None,
    ) -> None:
        self.policy_name = policy_name
        self._result = RiskRuleResult(
            policy_name,
            self.policy_version,
            decision,
            (reason,),
            approved_target,
            approved_quantity,
            earliest_execution_utc=earliest_execution_utc,
        )

    def evaluate(
        self, trade_intent: TradeIntent, context: RiskEvaluationContext
    ) -> RiskRuleResult:
        return self._result


def _factor_collection(status: FactorStatus = FactorStatus.VALID) -> FactorSnapshotCollection:
    result = FactorResult(
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        "test_factor",
        "test-v1",
        Decimal("1") if status in {FactorStatus.VALID, FactorStatus.STALE} else None,
        "unitless",
        (),
        1,
        status,
        ("TEST_ONLY",),
        CREATED,
        AS_OF - timedelta(days=1),
        AS_OF - timedelta(days=1),
    )
    snapshot = FactorSnapshot(
        FACTOR_ID,
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        (result,),
        CREATED,
    )
    return FactorSnapshotCollection(COLLECTION_ID, AS_OF, (snapshot,))


def _intent() -> TradeIntent:
    return TradeIntent(
        INTENT_ID,
        DECISION_ID,
        "AAPL",
        AS_OF,
        DecisionAction.INCREASE,
        Decimal("0"),
        Decimal("100"),
        Decimal("100"),
        "shares",
        None,
        ("TEST_ONLY",),
        FACTOR_ID,
        "test_policy",
        "test-v1",
        CREATED,
    )


def _context(
    *,
    factors: FactorSnapshotCollection | None = None,
    system: SystemRiskState | None = None,
    market_complete: bool = True,
    environment: ExecutionEnvironment = ExecutionEnvironment.ALPACA_PAPER,
    automatic_submission: bool = False,
) -> RiskEvaluationContext:
    return RiskEvaluationContext(
        factors or _factor_collection(),
        PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
        AccountSnapshot(ACCOUNT_ID, AS_OF),
        OpenOrdersSnapshot(ORDERS_ID, AS_OF),
        MarketRiskContext(AS_OF, AS_OF, market_complete),
        system or SystemRiskState(AS_OF),
        RiskContext(
            AS_OF,
            "test-config-v1",
            environment,
            automatic_submission_enabled=automatic_submission,
        ),
    )


def _engine(*policies: FakeRiskPolicy) -> RiskEngine:
    return RiskEngine(
        policies,
        clock=lambda: CREATED,
        id_factory=lambda: RISK_ID,
    )


def test_valid_intent_can_be_approved_by_injected_fake_policy() -> None:
    decision = _engine(
        FakeRiskPolicy("approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW)
    ).evaluate(_intent(), _context())

    assert decision.decision is RiskDecisionType.APPROVED
    assert decision.approved_quantity == Decimal("100")
    assert decision.approved_target == Decimal("100")
    assert decision.requires_manual_review
    assert RiskApprovedTradeIntent(_intent(), decision).risk_decision == decision


def test_reject_overrides_approve() -> None:
    decision = _engine(
        FakeRiskPolicy("approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW),
        FakeRiskPolicy("reject", RiskRuleDecision.REJECT, RiskReasonCode.ORDER_SIZE_LIMIT),
    ).evaluate(_intent(), _context())

    assert decision.decision is RiskDecisionType.REJECTED
    assert decision.approved_quantity is None
    with pytest.raises(RiskContractError):
        RiskApprovedTradeIntent(_intent(), decision)


def test_multiple_reductions_use_the_strictest_target_and_quantity() -> None:
    decision = _engine(
        FakeRiskPolicy(
            "reduce_60",
            RiskRuleDecision.REDUCE,
            RiskReasonCode.POSITION_LIMIT,
            approved_target=Decimal("60"),
            approved_quantity=Decimal("60"),
        ),
        FakeRiskPolicy(
            "reduce_40",
            RiskRuleDecision.REDUCE,
            RiskReasonCode.ORDER_SIZE_LIMIT,
            approved_target=Decimal("40"),
            approved_quantity=Decimal("40"),
        ),
    ).evaluate(_intent(), _context())

    assert decision.decision is RiskDecisionType.APPROVED_WITH_REDUCTION
    assert decision.original_quantity == Decimal("100")
    assert decision.approved_quantity == Decimal("40")
    assert decision.original_target == Decimal("100")
    assert decision.approved_target == Decimal("40")


def test_rule_that_attempts_to_increase_risk_fails_closed() -> None:
    original = _intent()
    decision = _engine(
        FakeRiskPolicy(
            "unsafe",
            RiskRuleDecision.REDUCE,
            RiskReasonCode.ORDER_SIZE_LIMIT,
            approved_target=Decimal("150"),
            approved_quantity=Decimal("150"),
        )
    ).evaluate(original, _context())

    assert decision.decision is RiskDecisionType.REJECTED
    assert decision.risk_status is RiskEvaluationStatus.POLICY_ERROR
    assert RiskReasonCode.INVALID_RULE_OUTPUT in decision.reason_codes
    assert original.target_exposure == Decimal("100")


def test_defer_preserves_latest_earliest_execution_time() -> None:
    first = AS_OF + timedelta(minutes=5)
    later = AS_OF + timedelta(minutes=10)
    decision = _engine(
        FakeRiskPolicy(
            "defer_1",
            RiskRuleDecision.DEFER,
            RiskReasonCode.MARKET_CLOSED,
            earliest_execution_utc=first,
        ),
        FakeRiskPolicy(
            "defer_2",
            RiskRuleDecision.DEFER,
            RiskReasonCode.STALE_DATA,
            earliest_execution_utc=later,
        ),
    ).evaluate(_intent(), _context())

    assert decision.decision is RiskDecisionType.DEFERRED
    assert decision.earliest_execution_utc == later


def test_system_pause_preempts_rules_and_symbol_pause_is_scoped() -> None:
    policy = FakeRiskPolicy(
        "approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW
    )
    system = _engine(policy).evaluate(
        _intent(), _context(system=SystemRiskState(AS_OF, system_paused=True))
    )
    symbol = _engine(policy).evaluate(
        _intent(), _context(system=SystemRiskState(AS_OF, paused_symbols=("aapl",)))
    )

    assert system.decision is RiskDecisionType.SYSTEM_PAUSED
    assert system.system_paused
    assert not system.rule_results
    assert symbol.decision is RiskDecisionType.SYMBOL_PAUSED
    assert symbol.symbol_paused


def test_stale_or_incomplete_data_is_deferred_and_invalid_factor_is_rejected() -> None:
    policy = FakeRiskPolicy(
        "approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW
    )
    stale = _engine(policy).evaluate(
        _intent(), _context(factors=_factor_collection(FactorStatus.STALE))
    )
    incomplete = _engine(policy).evaluate(
        _intent(), _context(market_complete=False)
    )
    invalid = _engine(policy).evaluate(
        _intent(), _context(factors=_factor_collection(FactorStatus.INVALID_INPUT))
    )

    assert stale.decision is RiskDecisionType.DEFERRED
    assert incomplete.decision is RiskDecisionType.DEFERRED
    assert invalid.decision is RiskDecisionType.REJECTED
    assert RiskReasonCode.INVALID_FACTOR in invalid.reason_codes


def test_no_rule_never_silently_approves() -> None:
    decision = _engine().evaluate(_intent(), _context())
    assert decision.decision is RiskDecisionType.MANUAL_REVIEW_REQUIRED
    assert decision.requires_manual_review


def test_manual_review_and_policy_pause_outputs_are_supported() -> None:
    manual = _engine(
        FakeRiskPolicy(
            "manual",
            RiskRuleDecision.REQUIRE_MANUAL_REVIEW,
            RiskReasonCode.MANUAL_REVIEW,
        )
    ).evaluate(_intent(), _context())
    symbol = _engine(
        FakeRiskPolicy(
            "symbol_pause",
            RiskRuleDecision.PAUSE_SYMBOL,
            RiskReasonCode.SYMBOL_PAUSED,
        )
    ).evaluate(_intent(), _context())
    system = _engine(
        FakeRiskPolicy(
            "system_pause",
            RiskRuleDecision.PAUSE_SYSTEM,
            RiskReasonCode.SYSTEM_PAUSED,
        )
    ).evaluate(_intent(), _context())

    assert manual.decision is RiskDecisionType.MANUAL_REVIEW_REQUIRED
    assert symbol.decision is RiskDecisionType.SYMBOL_PAUSED
    assert system.decision is RiskDecisionType.SYSTEM_PAUSED


def test_missing_account_context_can_be_sent_to_manual_review_by_a_rule() -> None:
    class MissingAccountPolicy:
        policy_name = "account_required"
        policy_version = "test-v1"

        def evaluate(
            self, trade_intent: TradeIntent, context: RiskEvaluationContext
        ) -> RiskRuleResult:
            assert context.account.source_reference is None
            return RiskRuleResult(
                self.policy_name,
                self.policy_version,
                RiskRuleDecision.REQUIRE_MANUAL_REVIEW,
                (RiskReasonCode.MANUAL_REVIEW,),
                warnings=("Account context is unavailable.",),
            )

    decision = RiskEngine(
        (MissingAccountPolicy(),), clock=lambda: CREATED, id_factory=lambda: RISK_ID
    ).evaluate(_intent(), _context())
    assert decision.decision is RiskDecisionType.MANUAL_REVIEW_REQUIRED


def test_live_and_automatic_submission_are_blocked_before_policies() -> None:
    policy = FakeRiskPolicy(
        "approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW
    )
    live = _engine(policy).evaluate(
        _intent(), _context(environment=ExecutionEnvironment.ALPACA_LIVE)
    )
    automatic = _engine(policy).evaluate(
        _intent(), _context(automatic_submission=True)
    )

    assert live.decision is RiskDecisionType.REJECTED
    assert live.reason_codes == (RiskReasonCode.LIVE_DISABLED,)
    assert automatic.reason_codes == (RiskReasonCode.AUTOMATIC_SUBMISSION_DISABLED,)


def test_trade_intent_is_immutable_and_risk_output_preserves_source() -> None:
    intent = _intent()
    with pytest.raises(FrozenInstanceError):
        intent.target_exposure = Decimal("1")  # type: ignore[misc]

    decision = _engine(
        FakeRiskPolicy(
            "reduce",
            RiskRuleDecision.REDUCE,
            RiskReasonCode.POSITION_LIMIT,
            approved_target=Decimal("40"),
            approved_quantity=Decimal("40"),
        )
    ).evaluate(intent, _context())
    with pytest.raises(RiskContractError):
        RiskApprovedTradeIntent(replace(intent, intent_id=UUID(int=999)), decision)


def test_risk_rejects_intent_with_mismatched_as_of() -> None:
    intent = replace(_intent(), as_of_utc=AS_OF - timedelta(minutes=1))
    decision = _engine(
        FakeRiskPolicy("approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW)
    ).evaluate(intent, _context())
    assert decision.decision is RiskDecisionType.REJECTED
    assert decision.reason_codes == (RiskReasonCode.INVALID_INTENT,)


def test_risk_approved_gate_rejects_hold_or_no_exposure() -> None:
    approve = FakeRiskPolicy(
        "approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW
    )
    hold = replace(
        _intent(),
        action=DecisionAction.HOLD,
        current_exposure=None,
        target_exposure=None,
        desired_change=None,
        exposure_unit=None,
    )
    decision = _engine(approve).evaluate(hold, _context())
    with pytest.raises(RiskContractError):
        RiskApprovedTradeIntent(hold, decision)


def test_every_risk_review_writes_traceable_audit_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="quant_trading.risk.engine"):
        _engine(
            FakeRiskPolicy(
                "approve", RiskRuleDecision.APPROVE, RiskReasonCode.MANUAL_REVIEW
            )
        ).evaluate(_intent(), _context())

    message = caplog.messages[-1]
    assert f"risk_decision_id={RISK_ID}" in message
    assert f"trade_intent_id={INTENT_ID}" in message
    assert "environment=alpaca_paper" in message
    assert "configuration_version=test-config-v1" in message
