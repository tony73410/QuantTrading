from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from quant_trading.decision import (
    DecisionAction,
    DecisionContext,
    DecisionInput,
    DecisionPolicyRegistry,
    DecisionResult,
    DecisionStatus,
    PortfolioSnapshot,
    TradeIntent,
    TradingDecisionEngine,
)
from quant_trading.decision.errors import DecisionContractError, DecisionRegistryError
from quant_trading.factors import (
    FactorResult,
    FactorSnapshot,
    FactorSnapshotCollection,
    FactorStatus,
)
from quant_trading.market_history.models import Timeframe


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 7, 13, 21, 1, tzinfo=UTC)
FACTOR_ID = UUID("00000000-0000-0000-0000-000000000201")
COLLECTION_ID = UUID("00000000-0000-0000-0000-000000000202")
PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000203")
DECISION_ID = UUID("00000000-0000-0000-0000-000000000204")
INTENT_ID = UUID("00000000-0000-0000-0000-000000000205")


def _factor_result(status: FactorStatus = FactorStatus.VALID) -> FactorResult:
    return FactorResult(
        symbol="AAPL",
        as_of_utc=AS_OF,
        timeframe=Timeframe.DAY,
        factor_name="fake_factor",
        factor_version="test-v1",
        value=Decimal("1") if status in {FactorStatus.VALID, FactorStatus.STALE} else None,
        unit="test-unit",
        parameters=(),
        lookback=1,
        status=status,
        quality_flags=("TEST_ONLY",),
        calculated_at_utc=CREATED_AT,
        source_data_start_utc=AS_OF,
        source_data_end_utc=AS_OF,
    )


def _collection(status: FactorStatus = FactorStatus.VALID) -> FactorSnapshotCollection:
    snapshot = FactorSnapshot(
        FACTOR_ID,
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        (_factor_result(status),),
        CREATED_AT,
    )
    return FactorSnapshotCollection(COLLECTION_ID, AS_OF, (snapshot,))


def _input(status: FactorStatus = FactorStatus.VALID) -> DecisionInput:
    return DecisionInput(
        factors=_collection(status),
        portfolio=PortfolioSnapshot(PORTFOLIO_ID, AS_OF),
        context=DecisionContext(AS_OF),
    )


class FakeDecisionPolicy:
    policy_name = "test_policy"
    policy_version = "test-v1"

    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self, decision_input: DecisionInput) -> DecisionResult:
        self.calls += 1
        snapshot = decision_input.factors.snapshots[0]
        intent = TradeIntent(
            intent_id=INTENT_ID,
            decision_id=DECISION_ID,
            symbol=snapshot.symbol,
            as_of_utc=decision_input.context.as_of_utc,
            action=DecisionAction.NO_DECISION,
            current_exposure=None,
            target_exposure=None,
            desired_change=None,
            exposure_unit=None,
            confidence=None,
            reason_codes=("TEST_ONLY",),
            factor_snapshot_id=snapshot.snapshot_id,
            policy_name=self.policy_name,
            policy_version=self.policy_version,
            created_at_utc=CREATED_AT,
        )
        return DecisionResult(
            decision_id=DECISION_ID,
            as_of_utc=decision_input.context.as_of_utc,
            policy_name=self.policy_name,
            policy_version=self.policy_version,
            policy_parameters=decision_input.context.parameters,
            factor_snapshot_ids=(snapshot.snapshot_id,),
            status=DecisionStatus.VALID,
            intents=(intent,),
            reason_codes=("TEST_ONLY",),
            created_at_utc=CREATED_AT,
        )


def _engine(policy: FakeDecisionPolicy) -> TradingDecisionEngine:
    return TradingDecisionEngine(
        (policy,),
        clock=lambda: CREATED_AT,
        id_factory=lambda: DECISION_ID,
    )


def test_decision_policy_runs_from_fake_factor_snapshot_without_market_services() -> None:
    policy = FakeDecisionPolicy()
    result = _engine(policy).evaluate("test_policy", _input())

    assert policy.calls == 1
    assert result.status is DecisionStatus.VALID
    assert result.factor_snapshot_ids == (FACTOR_ID,)
    assert result.policy_version == "test-v1"
    assert result.intents[0].action is DecisionAction.NO_DECISION
    assert not hasattr(result.intents[0], "order_id")


@pytest.mark.parametrize(
    ("factor_status", "decision_status"),
    [
        (FactorStatus.INSUFFICIENT_DATA, DecisionStatus.INVALID_FACTORS),
        (FactorStatus.STALE, DecisionStatus.STALE_FACTORS),
    ],
)
def test_invalid_or_stale_factors_block_policy_and_produce_no_intent(
    factor_status: FactorStatus, decision_status: DecisionStatus
) -> None:
    policy = FakeDecisionPolicy()
    result = _engine(policy).evaluate("test_policy", _input(factor_status))

    assert policy.calls == 0
    assert result.status is decision_status
    assert result.intents == ()


def test_policy_can_be_replaced_without_changing_factor_contract() -> None:
    replacement = FakeDecisionPolicy()
    replacement.policy_name = "replacement_policy"
    result = _engine(replacement).evaluate("replacement_policy", _input())
    assert result.policy_name == "replacement_policy"
    assert result.factor_snapshot_ids == (FACTOR_ID,)


def test_policy_registry_rejects_duplicate_names() -> None:
    registry = DecisionPolicyRegistry((FakeDecisionPolicy(),))
    with pytest.raises(DecisionRegistryError):
        registry.register(FakeDecisionPolicy())


def test_trade_intent_schema_has_no_execution_or_order_fields() -> None:
    names = {field.name for field in fields(TradeIntent)}
    assert "order_id" not in names
    assert "execution_status" not in names
    assert "broker" not in names
    assert {"factor_snapshot_id", "policy_name", "policy_version"} <= names


def test_trade_intent_rejects_nonfinite_exposure_and_confidence() -> None:
    base = TradeIntent(
        intent_id=INTENT_ID,
        decision_id=DECISION_ID,
        symbol="AAPL",
        as_of_utc=AS_OF,
        action=DecisionAction.NO_DECISION,
        current_exposure=None,
        target_exposure=None,
        desired_change=None,
        exposure_unit=None,
        confidence=None,
        reason_codes=("TEST_ONLY",),
        factor_snapshot_id=FACTOR_ID,
        policy_name="test_policy",
        policy_version="test-v1",
        created_at_utc=CREATED_AT,
    )
    with pytest.raises(DecisionContractError):
        replace(base, target_exposure=Decimal("Infinity"), exposure_unit="shares")
    with pytest.raises(DecisionContractError):
        replace(base, confidence=Decimal("NaN"))
    with pytest.raises(DecisionContractError):
        replace(base, target_exposure=1.0, exposure_unit="shares")  # type: ignore[arg-type]
    with pytest.raises(DecisionContractError):
        replace(base, confidence=0.5)  # type: ignore[arg-type]
    with pytest.raises(DecisionContractError):
        replace(base, action="BUY")  # type: ignore[arg-type]


def test_valid_decision_cannot_silently_omit_all_intents() -> None:
    with pytest.raises(DecisionContractError):
        DecisionResult(
            decision_id=DECISION_ID,
            as_of_utc=AS_OF,
            policy_name="test_policy",
            policy_version="test-v1",
            policy_parameters=(),
            factor_snapshot_ids=(FACTOR_ID,),
            status=DecisionStatus.VALID,
            intents=(),
            reason_codes=("TEST_ONLY",),
            created_at_utc=CREATED_AT,
        )
