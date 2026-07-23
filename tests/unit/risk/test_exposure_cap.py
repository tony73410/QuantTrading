from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.risk import (
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapRuleOutcome,
    LinkedExposureCapPreviewInput,
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    SingleAssetExposureCapDefinitionVersion,
    SingleAssetExposureCapEngine,
    TargetAdjustmentExposureCapPreviewResult,
)


NOW = datetime(2026, 7, 21, 22, tzinfo=UTC)


def _phase6a_source(**changes):
    values = dict(
        decision_result_id=uuid4(), decision_operation_id=uuid4(), decision_run_id=uuid4(),
        decision_stage_id=uuid4(), intent_id=uuid4(),
        decision_policy_id="decision.target_adjustment_preview", decision_policy_version="1.0.0",
        decision_schema_version=1, intent_schema_version=1,
        target_position_link_id=uuid4(), linked_target_operation_id=uuid4(),
        linked_parent_run_id=uuid4(), target_child_run_id=uuid4(), standardized_state_run_id=uuid4(),
        target_calculation_id=uuid4(), target_definition_id=uuid4(), target_definition_version=1,
        standardized_state_calculation_id=uuid4(), standardized_state_definition_id=uuid4(),
        standardized_state_definition_version=1, target_position_link_created_at_utc=NOW,
        target_position_link_schema_version=1, target_result_created_at_utc=NOW,
        target_result_schema_version=1, standardized_state_created_at_utc=NOW,
        standardized_state_schema_version=1, symbol="AAPL", as_of_utc=NOW,
        action="increase", current_exposure_usd=Decimal("60"),
        target_exposure_usd=Decimal("70"), desired_change_usd=Decimal("10"),
        requested_notional_usd=Decimal("10"), decision_created_at_utc=NOW,
        intent_created_at_utc=NOW,
    )
    values.update(changes)
    return LinkedTargetRiskReviewInput(**values)


def _safety(**changes):
    values = dict(
        snapshot_id=uuid4(), execution_environment=ExecutionEnvironment.ALPACA_PAPER,
        live_trading_enabled=False, automatic_submission_enabled=False,
        manual_confirmation_required=True, execution_capability_implemented=False,
        configuration_version="application-role-settings@1", software_version="test",
        source_revision="abc123", worktree_state="dirty", captured_at_utc=NOW,
    )
    values.update(changes)
    return RiskSafetyStateSnapshot(**values)


def _linked(*, cap="100", source=None, status=ExposureCapDefinitionStatus.SAVED):
    definition = SingleAssetExposureCapDefinitionVersion(
        uuid4(), 1, None, "AAPL", Decimal(cap), status,
        "explicit cap", "tester", NOW, "test",
    )
    return LinkedExposureCapPreviewInput(
        uuid4(), uuid4(), uuid4(), uuid4(),
        "risk.target_adjustment_manual_review_gate", "1.0.0", NOW,
        source or _phase6a_source(), _safety(),
        (
            ("SOURCE_CHAIN_INTEGRITY", "1", "passed"),
            ("NON_EXECUTION_SAFETY_STATE", "1", "passed"),
            ("NUMERICAL_RISK_POLICY_AVAILABILITY", "1", "manual_review"),
        ),
        definition, _safety(),
    )


def _evaluate(linked):
    return SingleAssetExposureCapEngine().evaluate(
        linked, preview_result_id=uuid4(), operation_id=uuid4(), run_id=uuid4(),
        stage_id=uuid4(), created_at_utc=NOW, created_by="tester",
        reason="numeric preview", software_version="test", id_factory=uuid4,
    )


@pytest.mark.parametrize(
    ("source", "cap", "candidate", "outcome", "disposition"),
    (
        (_phase6a_source(), "100", "10", ExposureCapRuleOutcome.PASSED_WITHIN_CAP, ExposureCapDisposition.MANUAL_REVIEW_REQUIRED),
        (_phase6a_source(), "70", "10", ExposureCapRuleOutcome.PASSED_WITHIN_CAP, ExposureCapDisposition.MANUAL_REVIEW_REQUIRED),
        (_phase6a_source(), "65", "5", ExposureCapRuleOutcome.REDUCED_TO_CAP, ExposureCapDisposition.MANUAL_REVIEW_REQUIRED),
        (_phase6a_source(), "60", "0", ExposureCapRuleOutcome.BLOCKED_NO_INCREASE_CAPACITY, ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP),
        (_phase6a_source(), "50", "0", ExposureCapRuleOutcome.BLOCKED_NO_INCREASE_CAPACITY, ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP),
        (_phase6a_source(action="decrease", current_exposure_usd=Decimal("70"), target_exposure_usd=Decimal("60"), desired_change_usd=Decimal("-10")), "50", "10", ExposureCapRuleOutcome.PRESERVED_RISK_REDUCING_DIRECTION, ExposureCapDisposition.MANUAL_REVIEW_REQUIRED),
    ),
)
def test_locked_exact_formula(source, cap, candidate, outcome, disposition):
    result = _evaluate(_linked(cap=cap, source=source))

    assert result.rule.cap_constrained_candidate_notional_usd == Decimal(candidate)
    assert result.rule.reduction_usd == source.requested_notional_usd - Decimal(candidate)
    assert result.rule.outcome is outcome
    assert result.disposition is disposition
    assert Decimal("0") <= result.cap_constrained_candidate_notional_usd <= source.requested_notional_usd


def test_result_type_has_no_approval_or_execution_fields():
    names = {field.name for field in fields(TargetAdjustmentExposureCapPreviewResult)}
    assert "approved_notional_usd" not in names
    assert "risk_approved_intent_id" not in names
    assert "execution_allowed" not in names


def test_archived_or_cross_symbol_definition_is_rejected():
    with pytest.raises(Exception, match="archived"):
        _linked(status=ExposureCapDefinitionStatus.ARCHIVED)
    definition = _linked().definition
    with pytest.raises(Exception, match="symbol"):
        replace(definition, symbol="MSFT")
        LinkedExposureCapPreviewInput(
            uuid4(), uuid4(), uuid4(), uuid4(),
            "risk.target_adjustment_manual_review_gate", "1.0.0", NOW,
            _phase6a_source(), _safety(),
            (
                ("SOURCE_CHAIN_INTEGRITY", "1", "passed"),
                ("NON_EXECUTION_SAFETY_STATE", "1", "passed"),
                ("NUMERICAL_RISK_POLICY_AVAILABILITY", "1", "manual_review"),
            ),
            replace(definition, symbol="MSFT"), _safety(),
        )


def test_rule_model_rejects_tampered_candidate():
    result = _evaluate(_linked(cap="65"))
    with pytest.raises(Exception, match="locked formula"):
        replace(result.rule, cap_constrained_candidate_notional_usd=Decimal("6"), reduction_usd=Decimal("4"))
