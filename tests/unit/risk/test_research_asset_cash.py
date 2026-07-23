from __future__ import annotations

from dataclasses import fields, replace
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.risk import (
    ExposureCapRuleOutcome,
    LinkedResearchAssetCashPreviewInput,
    ResearchAssetCashAvailabilityEngine,
    ResearchAssetCashDisposition,
    ResearchAssetCashRuleOutcome,
    ResearchCashFloorRuleOutcome,
    ResearchCashFloorSourceLink,
)
from quant_trading.risk.errors import RiskContractError

from tests.unit.risk.test_research_cash_floor import NOW, _evaluate, _linked, _safety


def _source(*, balance="10", phase6c=None):
    result = phase6c or _evaluate(_linked(floor="35"))
    upstream = result.source.phase6b_source_link
    phase6c_link = ResearchCashFloorSourceLink(
        uuid4(),
        result.operation_id,
        result.preview_result_id,
        result.run_id,
        result.stage_id,
        result.source.phase6b_result.preview_result_id,
        result.source.phase6b_result.run_id,
        result.source.phase6b_result.stage_id,
        upstream.phase6a_review_result_id,
        upstream.phase6a_run_id,
        upstream.phase6a_stage_id,
        upstream.decision_run_id,
        upstream.linked_parent_run_id,
        upstream.target_child_run_id,
        upstream.standardized_state_run_id,
        upstream.decision_result_id,
        upstream.intent_id,
        upstream.target_position_link_id,
        upstream.target_calculation_id,
        upstream.standardized_state_calculation_id,
        NOW,
    )
    return LinkedResearchAssetCashPreviewInput(
        result,
        phase6c_link,
        uuid4(),
        1,
        NOW,
        uuid4(),
        uuid4(),
        NOW,
        Decimal("1000"),
        Decimal("1000"),
        Decimal("1000"),
        Decimal("0"),
        uuid4(),
        Decimal("100"),
        uuid4(),
        Decimal("100"),
        uuid4(),
        Decimal(balance),
        _safety(),
    )


def _evaluate_asset(source):
    return ResearchAssetCashAvailabilityEngine().evaluate(
        source,
        preview_result_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        stage_id=uuid4(),
        created_at_utc=NOW,
        created_by="tester",
        reason="asset cash",
        software_version="test",
        id_factory=uuid4,
    )


@pytest.mark.parametrize(
    ("balance", "candidate", "outcome", "disposition"),
    (
        (
            "10",
            "5",
            ResearchAssetCashRuleOutcome.PASSED_WITHIN_RESEARCH_ASSET_CASH,
            ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED,
        ),
        (
            "5",
            "5",
            ResearchAssetCashRuleOutcome.PASSED_WITHIN_RESEARCH_ASSET_CASH,
            ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED,
        ),
        (
            "3",
            "3",
            ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH,
            ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED,
        ),
        (
            "0",
            "0",
            ResearchAssetCashRuleOutcome.BLOCKED_NO_RESEARCH_ASSET_CASH,
            ResearchAssetCashDisposition.BLOCKED_BY_RESEARCH_ASSET_CASH,
        ),
    ),
)
def test_increase_exact_asset_cash_branches(balance, candidate, outcome, disposition):
    result = _evaluate_asset(_source(balance=balance))

    assert result.asset_cash_constrained_candidate_notional_usd == Decimal(candidate)
    assert result.rule.outcome is outcome
    assert result.disposition is disposition
    assert result.research_cash_reserved is False
    assert result.rule.research_cash_reserved is False
    assert "No cash is reserved" in result.warnings[1]


def test_decrease_preserves_candidate_and_reports_hypothetical_return():
    phase6c = _evaluate(_linked(phase6b=None, floor="35"))
    decreasing = replace(
        phase6c,
        source=replace(
            phase6c.source,
            phase6b_result=replace(
                phase6c.source.phase6b_result,
                source=replace(
                    phase6c.source.phase6b_result.source,
                    phase6a_source=replace(
                        phase6c.source.phase6b_result.source.phase6a_source,
                        action="decrease",
                        current_exposure_usd=Decimal("70"),
                        target_exposure_usd=Decimal("60"),
                        desired_change_usd=Decimal("-10"),
                    ),
                ),
                rule=replace(
                    phase6c.source.phase6b_result.rule,
                    action="decrease",
                    current_exposure_usd=Decimal("70"),
                    target_exposure_usd=Decimal("60"),
                    outcome=ExposureCapRuleOutcome.PRESERVED_RISK_REDUCING_DIRECTION,
                ),
            ),
            definition=replace(phase6c.source.definition, symbol="AAPL"),
        ),
        rule=replace(
            phase6c.rule,
            action="decrease",
            current_exposure_usd=Decimal("70"),
            pre_action_research_cash_usd=Decimal("30"),
            cash_capacity_usd=Decimal("0"),
            cash_floor_constrained_candidate_notional_usd=Decimal("10"),
            post_action_research_cash_usd=Decimal("40"),
            remaining_shortfall_usd=Decimal("0"),
            reduction_usd=Decimal("0"),
            outcome=ResearchCashFloorRuleOutcome.PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION,
        ),
    )
    result = _evaluate_asset(_source(balance="2", phase6c=decreasing))

    assert result.asset_cash_constrained_candidate_notional_usd == Decimal("10")
    assert result.rule.hypothetical_post_candidate_asset_cash_usd == Decimal("12")
    assert result.rule.outcome is ResearchAssetCashRuleOutcome.PRESERVED_RESEARCH_ASSET_CASH_INCREASING_DIRECTION


def test_invalid_conservation_and_nonfinite_balance_fail_closed():
    source = _source()
    with pytest.raises(RiskContractError):
        replace(source, conservation_difference_usd=Decimal("1"))
    with pytest.raises(RiskContractError):
        replace(source, asset_cash_balance_usd=Decimal("NaN"))


def test_result_type_has_no_approval_or_execution_field():
    names = {item.name for item in fields(type(_evaluate_asset(_source())))}
    assert not names & {
        "approved_notional_usd",
        "approved_intent_id",
        "execution_allowed",
        "order_id",
        "cash_reserved",
    }
