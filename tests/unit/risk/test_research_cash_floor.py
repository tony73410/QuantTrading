from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.risk import (
    ExposureCapDefinitionStatus,
    ExposureCapSourceLink,
    LinkedExposureCapPreviewInput,
    LinkedResearchCashFloorPreviewInput,
    LinkedTargetRiskReviewInput,
    ResearchAssetCashFloorDefinitionVersion,
    ResearchAssetCashFloorEngine,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorDisposition,
    ResearchCashFloorRuleOutcome,
    RiskSafetyStateSnapshot,
    SingleAssetExposureCapDefinitionVersion,
    SingleAssetExposureCapEngine,
    TargetAdjustmentResearchCashFloorPreviewResult,
)


NOW = datetime(2026, 7, 22, 18, tzinfo=UTC)


def _phase6a_source(**changes):
    values = dict(
        decision_result_id=uuid4(),
        decision_operation_id=uuid4(),
        decision_run_id=uuid4(),
        decision_stage_id=uuid4(),
        intent_id=uuid4(),
        decision_policy_id="decision.target_adjustment_preview",
        decision_policy_version="1.0.0",
        decision_schema_version=1,
        intent_schema_version=1,
        target_position_link_id=uuid4(),
        linked_target_operation_id=uuid4(),
        linked_parent_run_id=uuid4(),
        target_child_run_id=uuid4(),
        standardized_state_run_id=uuid4(),
        target_calculation_id=uuid4(),
        target_definition_id=uuid4(),
        target_definition_version=1,
        standardized_state_calculation_id=uuid4(),
        standardized_state_definition_id=uuid4(),
        standardized_state_definition_version=1,
        target_position_link_created_at_utc=NOW,
        target_position_link_schema_version=1,
        target_result_created_at_utc=NOW,
        target_result_schema_version=1,
        standardized_state_created_at_utc=NOW,
        standardized_state_schema_version=1,
        symbol="AAPL",
        as_of_utc=NOW,
        action="increase",
        current_exposure_usd=Decimal("60"),
        target_exposure_usd=Decimal("70"),
        desired_change_usd=Decimal("10"),
        requested_notional_usd=Decimal("10"),
        decision_created_at_utc=NOW,
        intent_created_at_utc=NOW,
    )
    values.update(changes)
    return LinkedTargetRiskReviewInput(**values)


def _safety():
    return RiskSafetyStateSnapshot(
        uuid4(),
        ExecutionEnvironment.ALPACA_PAPER,
        False,
        False,
        True,
        False,
        "application-role-settings@1",
        "test",
        "abc123",
        "dirty",
        NOW,
    )


def _phase6b(*, source=None, cap="100"):
    phase6a = source or _phase6a_source()
    linked = LinkedExposureCapPreviewInput(
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        "risk.target_adjustment_manual_review_gate",
        "1.0.0",
        NOW,
        phase6a,
        _safety(),
        (
            ("SOURCE_CHAIN_INTEGRITY", "1", "passed"),
            ("NON_EXECUTION_SAFETY_STATE", "1", "passed"),
            ("NUMERICAL_RISK_POLICY_AVAILABILITY", "1", "manual_review"),
        ),
        SingleAssetExposureCapDefinitionVersion(
            uuid4(),
            1,
            None,
            "AAPL",
            Decimal(cap),
            ExposureCapDefinitionStatus.SAVED,
            "cap",
            "tester",
            NOW,
            "test",
        ),
        _safety(),
    )
    result = SingleAssetExposureCapEngine().evaluate(
        linked,
        preview_result_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        stage_id=uuid4(),
        created_at_utc=NOW,
        created_by="tester",
        reason="cap",
        software_version="test",
        id_factory=uuid4,
    )
    phase6a_source = result.source.phase6a_source
    link = ExposureCapSourceLink(
        uuid4(),
        result.operation_id,
        result.preview_result_id,
        result.run_id,
        result.stage_id,
        result.source.phase6a_review_result_id,
        result.source.phase6a_run_id,
        result.source.phase6a_stage_id,
        phase6a_source.decision_run_id,
        phase6a_source.linked_parent_run_id,
        phase6a_source.target_child_run_id,
        phase6a_source.standardized_state_run_id,
        phase6a_source.decision_result_id,
        phase6a_source.intent_id,
        phase6a_source.target_position_link_id,
        phase6a_source.target_calculation_id,
        phase6a_source.standardized_state_calculation_id,
        NOW,
    )
    return result, link


def _linked(*, basis="100", floor="20", phase6b=None):
    result, link = phase6b or _phase6b()
    definition = ResearchAssetCashFloorDefinitionVersion(
        uuid4(),
        1,
        None,
        result.source.symbol,
        Decimal(floor),
        ResearchCashFloorDefinitionStatus.SAVED,
        "floor",
        "tester",
        NOW,
        "test",
    )
    return LinkedResearchCashFloorPreviewInput(
        result,
        link,
        Decimal(basis),
        NOW,
        1,
        definition,
        _safety(),
    )


def _evaluate(source):
    return ResearchAssetCashFloorEngine().evaluate(
        source,
        preview_result_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        stage_id=uuid4(),
        created_at_utc=NOW,
        created_by="tester",
        reason="cash floor",
        software_version="test",
        id_factory=uuid4,
    )


@pytest.mark.parametrize(
    ("floor", "candidate", "outcome", "disposition", "post_cash"),
    (
        (
            "0",
            "10",
            ResearchCashFloorRuleOutcome.PASSED_AT_OR_ABOVE_CASH_FLOOR,
            ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
            "30",
        ),
        (
            "30",
            "10",
            ResearchCashFloorRuleOutcome.PASSED_AT_OR_ABOVE_CASH_FLOOR,
            ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
            "30",
        ),
        (
            "35",
            "5",
            ResearchCashFloorRuleOutcome.REDUCED_TO_CASH_FLOOR,
            ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
            "35",
        ),
        (
            "40",
            "0",
            ResearchCashFloorRuleOutcome.BLOCKED_NO_RESEARCH_CASH_CAPACITY,
            ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR,
            "40",
        ),
        (
            "50",
            "0",
            ResearchCashFloorRuleOutcome.BLOCKED_NO_RESEARCH_CASH_CAPACITY,
            ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR,
            "40",
        ),
    ),
)
def test_locked_increase_formula(floor, candidate, outcome, disposition, post_cash):
    result = _evaluate(_linked(floor=floor))

    assert result.cash_floor_constrained_candidate_notional_usd == Decimal(candidate)
    assert result.rule.post_action_research_cash_usd == Decimal(post_cash)
    assert result.rule.outcome is outcome
    assert result.disposition is disposition
    assert Decimal("0") <= result.cash_floor_constrained_candidate_notional_usd <= Decimal("10")


def test_decrease_is_preserved_even_when_floor_remains_unmet():
    source = _phase6a_source(
        action="decrease",
        current_exposure_usd=Decimal("70"),
        target_exposure_usd=Decimal("60"),
        desired_change_usd=Decimal("-10"),
    )
    result = _evaluate(_linked(floor="50", phase6b=_phase6b(source=source)))

    assert result.cash_floor_constrained_candidate_notional_usd == Decimal("10")
    assert result.rule.pre_action_research_cash_usd == Decimal("30")
    assert result.rule.post_action_research_cash_usd == Decimal("40")
    assert result.rule.remaining_shortfall_usd == Decimal("10")
    assert result.rule.outcome is (
        ResearchCashFloorRuleOutcome.PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION
    )


def test_definition_rejects_negative_but_accepts_explicit_zero():
    definition = _linked(floor="0").definition
    assert definition.minimum_research_asset_cash_usd == Decimal("0")
    with pytest.raises(Exception, match="non-negative"):
        replace(definition, minimum_research_asset_cash_usd=Decimal("-1"))


def test_result_type_has_no_approval_or_execution_fields():
    names = {field.name for field in fields(TargetAdjustmentResearchCashFloorPreviewResult)}
    assert "approved_notional_usd" not in names
    assert "risk_approved_intent_id" not in names
    assert "execution_allowed" not in names


def test_rule_model_rejects_tampered_candidate():
    result = _evaluate(_linked(floor="35"))
    with pytest.raises(Exception, match="locked formula"):
        replace(
            result.rule,
            cash_floor_constrained_candidate_notional_usd=Decimal("6"),
            post_action_research_cash_usd=Decimal("34"),
            reduction_usd=Decimal("4"),
        )
