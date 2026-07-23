from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.risk import (
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    StructuralRuleStatus,
    TargetAdjustmentRiskEngine,
    TargetAdjustmentRiskStatus,
)

NOW = datetime(2026, 7, 21, 10, tzinfo=UTC)


def _source(**changes):
    values = dict(
        decision_result_id=uuid4(), decision_operation_id=uuid4(), decision_run_id=uuid4(),
        decision_stage_id=uuid4(), intent_id=uuid4(),
        decision_policy_id="decision.target_adjustment_preview", decision_policy_version="1.0.0",
        decision_schema_version=1, intent_schema_version=1,
        target_position_link_id=uuid4(), linked_target_operation_id=uuid4(),
        linked_parent_run_id=uuid4(), target_child_run_id=uuid4(),
        standardized_state_run_id=uuid4(), target_calculation_id=uuid4(), target_definition_id=uuid4(),
        target_definition_version=1, standardized_state_calculation_id=uuid4(),
        standardized_state_definition_id=uuid4(), standardized_state_definition_version=1,
        target_position_link_created_at_utc=NOW, target_position_link_schema_version=1,
        target_result_created_at_utc=NOW, target_result_schema_version=1,
        standardized_state_created_at_utc=NOW, standardized_state_schema_version=1,
        symbol="AAPL", as_of_utc=NOW, action="increase", current_exposure_usd=Decimal("60"),
        target_exposure_usd=Decimal("70"), desired_change_usd=Decimal("10"),
        requested_notional_usd=Decimal("10"), decision_created_at_utc=NOW, intent_created_at_utc=NOW,
    )
    values.update(changes)
    return LinkedTargetRiskReviewInput(**values)


def _safety(**changes):
    values = dict(snapshot_id=uuid4(), execution_environment=ExecutionEnvironment.ALPACA_PAPER,
                  live_trading_enabled=False, automatic_submission_enabled=False,
                  manual_confirmation_required=True, execution_capability_implemented=False,
                  configuration_version="application-role-settings@1", software_version="test",
                  source_revision="abc123", worktree_state="clean",
                  captured_at_utc=NOW)
    values.update(changes)
    return RiskSafetyStateSnapshot(**values)


def _evaluate(source=None, safety=None):
    return TargetAdjustmentRiskEngine().evaluate(source or _source(), safety or _safety(),
        review_result_id=uuid4(), operation_id=uuid4(), run_id=uuid4(), stage_id=uuid4(),
        created_at_utc=NOW, created_by="tester", reason="structural review", software_version="test",
        id_factory=uuid4)


def test_safe_source_always_stops_at_manual_review_without_approval():
    result = _evaluate()

    assert result.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED
    assert [rule.rule_id for rule in result.rules] == [
        "SOURCE_CHAIN_INTEGRITY", "NON_EXECUTION_SAFETY_STATE",
        "NUMERICAL_RISK_POLICY_AVAILABILITY",
    ]
    assert result.rules[-1].status is StructuralRuleStatus.MANUAL_REVIEW
    assert result.approved_notional_usd is None
    assert result.risk_approved_intent_id is None


@pytest.mark.parametrize(
    "safety",
    (
        _safety(execution_environment=ExecutionEnvironment.ALPACA_LIVE,
                live_trading_enabled=True, automatic_submission_enabled=True),
        _safety(automatic_submission_enabled=True),
        _safety(manual_confirmation_required=False),
        _safety(execution_capability_implemented=True),
    ),
)
def test_unsafe_runtime_is_blocked_before_policy_availability(safety):
    result = _evaluate(safety=safety)

    assert result.status is TargetAdjustmentRiskStatus.BLOCKED
    assert [rule.rule_id for rule in result.rules] == [
        "SOURCE_CHAIN_INTEGRITY", "NON_EXECUTION_SAFETY_STATE",
    ]
    assert result.rules[-1].status is StructuralRuleStatus.BLOCKED
    assert result.approved_notional_usd is None


def test_source_arithmetic_and_approved_output_are_type_enforced():
    with pytest.raises(ValueError, match="desired change"):
        _source(desired_change_usd=Decimal("9"), requested_notional_usd=Decimal("9"))

    result = _evaluate()
    with pytest.raises(ValueError, match="cannot emit approved"):
        replace(result, approved_notional_usd=Decimal("10"))
