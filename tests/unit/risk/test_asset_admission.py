from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.risk import (
    AssetTradingControlEvidence,
    CycleTargetAssetAdmissionEngine,
    CycleTargetAssetAdmissionSource,
    CycleTargetAssetAdmissionStatus,
)


NOW = datetime(2026, 8, 12, 20, 0, tzinfo=UTC)


def _source(action: str = "increase") -> CycleTargetAssetAdmissionSource:
    return CycleTargetAssetAdmissionSource(
        uuid4(), uuid4(), uuid4(), uuid4(), "manual_review_required",
        "risk.cycle_target_manual_review_gate.p23_4b.v1", "1.0.0", NOW,
        ("P33_MANUAL_REVIEW_REQUIRED",), uuid4(), uuid4(), uuid4(),
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), "AAPL",
        date(2026, 8, 12), action, Decimal("1000"),
    )


def _control(status: str = "frozen", symbol: str = "AAPL") -> AssetTradingControlEvidence:
    return AssetTradingControlEvidence(
        uuid4(), uuid4(), uuid4(), uuid4(), None, symbol, status,
        NOW, NOW, date(2026, 8, 12),
        "asset_state.trading_control.p23_4c1.v1", "1.0.0",
        uuid4(), 1, "US_EQUITIES_REGULAR_V1", uuid4(), "calendar-fingerprint",
    )


def _evaluate(source: CycleTargetAssetAdmissionSource, control: AssetTradingControlEvidence | None):
    return CycleTargetAssetAdmissionEngine().evaluate(
        source, control, result_id=uuid4(), operation_id=uuid4(), run_id=uuid4(),
        stage_id=uuid4(), created_at_utc=NOW, created_by="pytest",
        reason="locked P35 rule test", software_version="test",
    )


@pytest.mark.parametrize("action", ["increase", "decrease"])
def test_frozen_status_blocks_both_directions_without_approved_output(action: str) -> None:
    result = _evaluate(_source(action), _control("frozen"))
    assert result.status is CycleTargetAssetAdmissionStatus.BLOCKED_FROZEN_ASSET
    assert [rule.rule_id for rule in result.rules] == [
        "P33_STRUCTURAL_REVIEW_INTEGRITY",
        "ASSET_TRADING_CONTROL_AVAILABILITY",
        "FROZEN_ASSET_BLOCK",
    ]
    assert result.rules[-1].stop_processing
    assert result.approved_notional_usd is None
    assert result.risk_approved_intent_id is None
    assert not result.execution_allowed and not result.live_allowed


def test_eligible_status_stops_at_manual_review_and_never_approves() -> None:
    result = _evaluate(_source(), _control("eligible"))
    assert result.status is CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED
    assert result.rules[-1].status.value == "manual_review"
    assert result.approved_notional_usd is None
    assert result.risk_approved_intent_id is None


def test_missing_and_mismatched_control_fail_closed_at_the_expected_rule() -> None:
    missing = _evaluate(_source(), None)
    assert missing.status is CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL
    assert [rule.rule_id for rule in missing.rules] == [
        "P33_STRUCTURAL_REVIEW_INTEGRITY", "ASSET_TRADING_CONTROL_AVAILABILITY"
    ]

    mismatched = _evaluate(_source(), _control(symbol="MSFT"))
    assert mismatched.status is CycleTargetAssetAdmissionStatus.BLOCKED_INVALID_SOURCE
    assert len(mismatched.rules) == 2


def test_non_manual_p33_source_is_blocked_before_control_evaluation() -> None:
    result = _evaluate(replace(_source(), p33_status="blocked"), _control("eligible"))
    assert result.status is CycleTargetAssetAdmissionStatus.BLOCKED_INVALID_SOURCE
    assert [rule.rule_id for rule in result.rules] == ["P33_STRUCTURAL_REVIEW_INTEGRITY"]
