from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.target_adjustment_risk_panel import TargetAdjustmentRiskPanel
from quant_trading.risk import StructuralRuleStatus, TargetAdjustmentRiskStatus

NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


def test_panel_requires_exact_intent_delegates_and_opens_related_runs():
    app = QApplication.instance() or QApplication([])
    intent_id, decision_result_id = uuid4(), uuid4()
    risk_run, decision_run, phase5c_run, target_run, source_run = (uuid4() for _ in range(5))
    intent = SimpleNamespace(intent_id=intent_id, decision_result_id=decision_result_id, run_id=decision_run,
        symbol="AAPL", as_of_utc=NOW, action=SimpleNamespace(value="increase"),
        current_exposure_usd=Decimal("60"), target_exposure_usd=Decimal("70"),
        desired_change_usd=Decimal("10"), requested_notional_usd=Decimal("10"),
        policy_id="decision.target_adjustment_preview", policy_version="1.0.0")
    decision = SimpleNamespace(intents=(intent,))
    source = SimpleNamespace(as_of_utc=NOW, symbol="AAPL", action="increase",
        requested_notional_usd=Decimal("10"), decision_run_id=decision_run,
        linked_parent_run_id=phase5c_run, target_child_run_id=target_run,
        standardized_state_run_id=source_run)
    rule = SimpleNamespace(evaluation_order=3, rule_id="NUMERICAL_RISK_POLICY_AVAILABILITY",
        rule_version="1", status=StructuralRuleStatus.MANUAL_REVIEW,
        reason_codes=("MANUAL_REVIEW_REQUIRED",), stop_processing=True)
    result = SimpleNamespace(source=source, status=TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED,
        approved_notional_usd=None, rules=(rule,), run_id=risk_run)
    operation = SimpleNamespace(completed_at_utc=NOW, status=TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED,
        requested_intent_id=intent_id, run_id=risk_run, error_summary=None)

    class DecisionQueries:
        def list_target_adjustment_results(self, query): return (decision,)

    class RiskQueries:
        def list_target_adjustment_risk_results(self, query): return (result,)
        def list_target_adjustment_risk_operations(self, query): return (operation,)

    class Service:
        command = None
        def review(self, command):
            self.command = command
            return SimpleNamespace(summary="delegated manual review")

    service = Service()
    panel = TargetAdjustmentRiskPanel(service, RiskQueries(), DecisionQueries(), session_id="GUI")
    opened = []; panel.open_run_requested.connect(opened.append)

    assert panel.intent_choice.currentData() is None
    panel.reason.setText("explicit review"); panel.review_button.click()
    assert "required" in panel.status_text.text()
    panel.intent_choice.setCurrentIndex(1); panel.review_button.click()
    assert service.command.target_adjustment_trade_intent_id == intent_id
    assert service.command.reason == "explicit review"
    assert "delegated manual review" in panel.status_text.text()
    assert panel.rule_table.rowCount() == 1
    panel.open_risk.click(); panel.open_decision.click(); panel.open_phase5c.click(); panel.open_target.click(); panel.open_source.click()
    assert opened == [risk_run, decision_run, phase5c_run, target_run, source_run]
    panel.close(); assert app is not None
