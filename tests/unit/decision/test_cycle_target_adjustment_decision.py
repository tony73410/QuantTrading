from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.decision import (
    CycleTargetAdjustmentDecisionEngine,
    CycleTargetAdjustmentDecisionReplayService,
    CycleTargetAdjustmentResultStatus,
    CycleTargetDecisionInput,
    DecisionAction,
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionEngine,
)
from quant_trading.decision.errors import DecisionContractError
from quant_trading.run_history import SoftwareIdentity, WorktreeState


NOW = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
SOFTWARE = SoftwareIdentity("test", "abc123", WorktreeState.CLEAN)


def _source(*, current: str, target: str) -> CycleTargetDecisionInput:
    current_value = Decimal(current)
    target_value = Decimal(target)
    difference = target_value - current_value
    return CycleTargetDecisionInput(
        source_result_id=uuid4(),
        source_operation_id=uuid4(),
        source_run_id=uuid4(),
        source_state_stage_id=uuid4(),
        source_target_stage_id=uuid4(),
        source_formula_definition_id=uuid4(),
        source_formula_definition_version=1,
        source_configuration_id=uuid4(),
        source_configuration_version=1,
        source_configuration_fingerprint="config-fingerprint",
        source_reversal_result_id=uuid4(),
        source_reversal_run_id=uuid4(),
        source_reversal_step_id=uuid4(),
        source_calculation_fingerprint="result-fingerprint",
        symbol="AAPL",
        source_session=date(2026, 8, 10),
        source_available_at_utc=NOW,
        source_region="linear",
        source_status="valid_linear",
        target_fraction=target_value / Decimal("100"),
        research_capital_basis_usd=Decimal("100"),
        current_position_value_usd=current_value,
        target_position_value_usd=target_value,
        adjustment_value_usd=difference,
        source_direction=(
            "none" if difference == 0 else "increase" if difference > 0 else "decrease"
        ),
        source_created_at_utc=NOW,
    )


def _evaluate(source: CycleTargetDecisionInput):
    return CycleTargetAdjustmentDecisionEngine().evaluate(
        source,
        decision_result_id=uuid4(),
        intent_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        target_stage_id=uuid4(),
        decision_stage_id=uuid4(),
        created_at_utc=NOW,
        created_by="tester",
        reason="Approved P31 exact mapping",
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
def test_nonzero_cycle_target_difference_creates_one_type_distinct_intent(
    current, target, action, signed, notional
):
    result = _evaluate(_source(current=current, target=target))

    assert result.status is CycleTargetAdjustmentResultStatus.INTENT_CREATED
    assert result.action is action
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent.desired_change_usd == signed
    assert intent.requested_notional_usd == notional
    assert intent.execution_allowed is False
    assert intent.live_allowed is False
    assert not hasattr(intent, "target_position_link_id")
    assert not hasattr(intent, "order_id")


def test_exact_zero_is_hold_without_intent():
    result = _evaluate(_source(current="70.000", target="70.000"))

    assert result.status is CycleTargetAdjustmentResultStatus.HOLD
    assert result.action is DecisionAction.HOLD
    assert result.intents == ()
    assert result.reason_codes == ("TARGET_POSITION_EQUAL_CURRENT",)


def test_recalculation_replay_is_exact_and_read_only():
    result = _evaluate(_source(current="60", target="70"))

    class Queries:
        def get_cycle_target_adjustment_result(self, decision_result_id):
            return result if decision_result_id == result.decision_result_id else None

    replay = CycleTargetAdjustmentDecisionReplayService(Queries())

    assert replay.recalculate(result.decision_result_id) == result
    assert replay.verify(result.decision_result_id).matched is True
    with pytest.raises(KeyError, match="does not exist"):
        replay.recalculate(uuid4())


def test_cycle_source_rejects_tampered_arithmetic_or_safety():
    source = _source(current="60", target="70")

    with pytest.raises(DecisionContractError, match="arithmetic"):
        replace(source, adjustment_value_usd=Decimal("9.99"))
    with pytest.raises(DecisionContractError, match="non-executable"):
        replace(source, source_execution_allowed=True)


@pytest.mark.parametrize(("current", "target"), (("60", "70"), ("80", "70"), ("70", "70")))
def test_p31_and_old_phase5d_use_exactly_equivalent_mapping(current, target):
    p31_source = _source(current=current, target=target)
    p31 = _evaluate(p31_source)
    old_source = LinkedTargetDecisionInput(
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(),
        uuid4(), uuid4(), uuid4(), uuid4(), 1, NOW,
        uuid4(), uuid4(), 1, NOW,
        "AAPL", NOW, Decimal("-1"), Decimal("100"), Decimal(current),
        Decimal(target) / Decimal("100"), Decimal(target),
        Decimal(target) - Decimal(current), p31_source.source_direction, NOW,
    )
    old = TargetAdjustmentDecisionEngine().evaluate(
        old_source,
        decision_result_id=uuid4(), intent_id=uuid4(), operation_id=uuid4(),
        run_id=uuid4(), stage_id=uuid4(), created_at_utc=NOW,
        created_by="tester", reason="equivalence", software=SOFTWARE,
    )

    assert p31.action is old.action
    assert bool(p31.intents) is bool(old.intents)
    if p31.intents:
        assert p31.intents[0].requested_notional_usd == old.intents[0].requested_notional_usd
