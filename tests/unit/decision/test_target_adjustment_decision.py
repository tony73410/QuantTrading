from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.decision import (
    DecisionAction,
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionEngine,
    TargetAdjustmentDecisionStatus,
)
from quant_trading.decision.errors import DecisionContractError
from quant_trading.run_history import SoftwareIdentity, WorktreeState


NOW = datetime(2026, 7, 21, 1, 0, tzinfo=UTC)
SOFTWARE = SoftwareIdentity("test", "abc123", WorktreeState.CLEAN)


def _source(*, current: str, target: str) -> LinkedTargetDecisionInput:
    target_value = Decimal(target)
    current_value = Decimal(current)
    difference = target_value - current_value
    direction = "none" if difference == 0 else "increase" if difference > 0 else "decrease"
    return LinkedTargetDecisionInput(
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(),
        uuid4(), uuid4(), uuid4(), uuid4(), 1, NOW,
        uuid4(), uuid4(), 1, NOW,
        "AAPL", NOW, Decimal("-1.23456789"), Decimal("100"),
        current_value, target_value / Decimal("100"), target_value,
        difference, direction, NOW,
    )


def _evaluate(source: LinkedTargetDecisionInput):
    return TargetAdjustmentDecisionEngine().evaluate(
        source,
        decision_result_id=uuid4(),
        intent_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        stage_id=uuid4(),
        created_at_utc=NOW,
        created_by="tester",
        reason="Exact approved mapping",
        software=SOFTWARE,
    )


@pytest.mark.parametrize(
    ("current", "target", "action", "signed", "notional"),
    (
        ("60", "70", DecisionAction.INCREASE, Decimal("10"), Decimal("10")),
        ("80", "70", DecisionAction.DECREASE, Decimal("-10"), Decimal("10")),
        ("0.00000001", "0", DecisionAction.DECREASE, Decimal("-0.00000001"), Decimal("0.00000001")),
    ),
)
def test_exact_nonzero_difference_creates_one_type_distinct_intent(
    current, target, action, signed, notional
):
    result = _evaluate(_source(current=current, target=target))

    assert result.status is TargetAdjustmentDecisionStatus.INTENT_CREATED
    assert result.action is action
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent.desired_change_usd == signed
    assert intent.requested_notional_usd == notional
    assert intent.reason_codes == ("TARGET_POSITION_DIFFERENCE",)
    assert not hasattr(intent, "factor_snapshot_id")
    assert not hasattr(intent, "order_id")


def test_exact_zero_difference_is_hold_without_intent():
    result = _evaluate(_source(current="70.000", target="70.000"))

    assert result.status is TargetAdjustmentDecisionStatus.HOLD
    assert result.action is DecisionAction.HOLD
    assert result.intents == ()
    assert result.reason_codes == ("TARGET_POSITION_EQUAL_CURRENT",)


def test_linked_input_rejects_tampered_target_arithmetic():
    source = _source(current="60", target="70")

    with pytest.raises(DecisionContractError, match="notional evidence"):
        replace(source, adjustment_value_usd=Decimal("9.99"))
