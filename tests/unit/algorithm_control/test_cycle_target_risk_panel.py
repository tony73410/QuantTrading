from __future__ import annotations

import os
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.cycle_target_risk_panel import CycleTargetRiskPanel
from quant_trading.decision import DecisionAction
from quant_trading.risk import CycleTargetRiskStatus, StructuralRuleStatus


NOW = datetime(2026, 8, 11, 12, tzinfo=UTC)


def test_cycle_target_risk_panel_requires_preflight_delegates_and_opens_runs():
    app = QApplication.instance() or QApplication([])
    intent_id, decision_result_id, p29_result, p28_result, p28_step = (uuid4() for _ in range(5))
    risk_run, p31_run, p29_run, p28_run = (uuid4() for _ in range(4))
    intent = SimpleNamespace(
        intent_id=intent_id, decision_result_id=decision_result_id, run_id=p31_run,
        source_result_id=p29_result, source_run_id=p29_run, symbol="AAPL",
        source_session=date(2026, 8, 10), source_available_at_utc=NOW,
        action=DecisionAction.INCREASE, current_exposure_usd=Decimal("50"),
        target_exposure_usd=Decimal("60"), desired_change_usd=Decimal("10"),
        requested_notional_usd=Decimal("10"),
        policy_id="decision.cycle_target_adjustment.p23_4a.v1", policy_version="1.0.0",
        execution_allowed=False, live_allowed=False,
    )
    decision = SimpleNamespace(intents=(intent,))
    source = SimpleNamespace(
        intent_id=intent_id, decision_result_id=decision_result_id, decision_run_id=p31_run,
        source_result_id=p29_result, source_run_id=p29_run,
        source_reversal_result_id=p28_result, source_reversal_run_id=p28_run,
        source_reversal_step_id=p28_step, symbol="AAPL", source_session=date(2026, 8, 10),
        action="increase", current_exposure_usd=Decimal("50"),
        target_exposure_usd=Decimal("60"), desired_change_usd=Decimal("10"),
        requested_notional_usd=Decimal("10"),
    )
    safety = SimpleNamespace(
        execution_environment=SimpleNamespace(value="alpaca_paper"),
        live_trading_enabled=False, automatic_submission_enabled=False,
        manual_confirmation_required=True, execution_capability_implemented=False,
    )
    rule = SimpleNamespace(
        evaluation_order=3, rule_id="NUMERICAL_RISK_POLICY_AVAILABILITY",
        rule_version="1", status=StructuralRuleStatus.MANUAL_REVIEW,
        reason_codes=("MANUAL_REVIEW_REQUIRED",), stop_processing=True,
    )
    result = SimpleNamespace(
        review_result_id=uuid4(), run_id=risk_run, created_at_utc=NOW, source=source,
        safety_snapshot=safety, status=CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED,
        approved_notional_usd=None, risk_approved_intent_id=None, rules=(rule,),
        reason_codes=("MANUAL_REVIEW_REQUIRED",), execution_allowed=False, live_allowed=False,
    )
    operation = SimpleNamespace(
        completed_at_utc=NOW, status=CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED,
        requested_intent_id=intent_id, run_id=risk_run, error_summary=None,
    )

    class Decisions:
        def list_cycle_target_adjustment_results(self, query): return (decision,)

    class Risks:
        def list_cycle_target_risk_results(self, query): return (result,)
        def list_cycle_target_risk_operations(self, query): return (operation,)

    class Service:
        command = None
        def preflight(self, command):
            self.command = command
            return SimpleNamespace(accepted=True, summary="preflight wrote no data")
        def review(self, command):
            self.command = command
            return SimpleNamespace(summary="delegated manual review")

    service = Service()
    panel = CycleTargetRiskPanel(service, Risks(), Decisions(), session_id="GUI")
    opened = []; panel.open_run_requested.connect(opened.append)
    assert panel.intent_choice.currentData() is None
    panel.reason.setText("explicit P33 review")
    panel.intent_choice.setCurrentIndex(1)
    assert panel.review_button.isEnabled() is False
    panel.preflight_button.click()
    assert panel.review_button.isEnabled() is True
    assert service.command.intent_id == intent_id
    assert service.command.decision_result_id == decision_result_id
    assert service.command.decision_run_id == p31_run
    panel.review_button.click()
    assert "delegated manual review" in panel.status_text.text()
    panel.history.selectRow(0)
    panel.open_risk.click(); panel.open_p31.click(); panel.open_p29.click(); panel.open_p28.click()
    assert opened == [risk_run, p31_run, p29_run, p28_run]
    panel.close(); assert app is not None
