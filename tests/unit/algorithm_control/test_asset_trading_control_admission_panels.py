from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.asset_trading_control_panel import AssetTradingControlPanel
from quant_trading.algorithm_control.ui.cycle_target_asset_admission_panel import CycleTargetAssetAdmissionPanel
from quant_trading.asset_state import AssetTradingControlStatus
from quant_trading.risk import CycleTargetAssetAdmissionStatus, StructuralRuleStatus


NOW = datetime(2026, 8, 12, 20, tzinfo=UTC)


def test_asset_trading_control_panel_delegates_and_opens_exact_run():
    app = QApplication.instance() or QApplication([])
    event_id, run_id = uuid4(), uuid4()
    calendar = SimpleNamespace(effective_session=date(2026, 8, 12))
    event = SimpleNamespace(
        event_id=event_id, run_id=run_id, effective_at_utc=NOW, symbol="AAPL",
        previous_status=None, new_status=AssetTradingControlStatus.FROZEN,
        calendar=calendar, created_by="user", reason="freeze", requested_at_utc=NOW,
    )
    operation = SimpleNamespace(
        completed_at_utc=NOW, status=SimpleNamespace(value="completed"),
        requested_status=AssetTradingControlStatus.FROZEN, run_id=run_id, error_summary=None,
    )

    class Queries:
        def get_latest_asset_trading_control_event(self, symbol): return event
        def get_effective_asset_trading_control_event(self, symbol, as_of): return event
        def list_asset_trading_control_events(self, query): return (event,)
        def list_asset_trading_control_operations(self, query): return (operation,)

    class Coordinator:
        preflight_command = None
        change_command = None
        def preflight(self, command): self.preflight_command = command; return SimpleNamespace(accepted=True, summary="no write")
        def change(self, command): self.change_command = command; return SimpleNamespace(summary="saved")

    coordinator = Coordinator()
    panel = AssetTradingControlPanel(coordinator, Queries(), session_id="GUI")
    panel.symbol.setText("AAPL"); panel.reason.setText("manual change")
    panel.requested_status.setCurrentIndex(0)
    panel.preflight_button.click()
    assert coordinator.preflight_command.predecessor_event_id == event_id
    assert coordinator.preflight_command.requested_status is AssetTradingControlStatus.ELIGIBLE
    panel.save_button.click()
    assert coordinator.change_command is coordinator.preflight_command
    opened = []; panel.open_run_requested.connect(opened.append); panel.events.selectRow(0); panel.open_run.click()
    assert opened == [run_id]
    panel.close(); assert app is not None


def test_asset_admission_panel_selects_exact_p33_and_renders_missing_control():
    app = QApplication.instance() or QApplication([])
    p33_result_id, p33_run, admission_run = uuid4(), uuid4(), uuid4()
    p31_result, intent, p29, p28, p31_run, p29_run, p28_run = (uuid4() for _ in range(7))
    p33_source = SimpleNamespace(
        symbol="AAPL", action="increase", requested_notional_usd=Decimal("100"),
        decision_result_id=p31_result, intent_id=intent, source_result_id=p29,
        source_reversal_result_id=p28,
    )
    p33 = SimpleNamespace(review_result_id=p33_result_id, run_id=p33_run, source=p33_source)
    source = SimpleNamespace(
        symbol="AAPL", action="increase", requested_notional_usd=Decimal("100"),
        source_session=date(2026, 8, 11), p33_run_id=p33_run,
        p31_run_id=p31_run, p29_run_id=p29_run, p28_run_id=p28_run,
    )
    rule = SimpleNamespace(
        evaluation_order=2, rule_id="ASSET_TRADING_CONTROL_AVAILABILITY", rule_version="1",
        status=StructuralRuleStatus.BLOCKED, reason_codes=("P35_MISSING_TRADING_CONTROL",), stop_processing=True,
    )
    result = SimpleNamespace(
        result_id=uuid4(), run_id=admission_run, created_at_utc=NOW, source=source,
        control=None, status=CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL,
        rules=(rule,),
    )
    operation = SimpleNamespace(
        completed_at_utc=NOW, status=CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL,
        requested_p33_result_id=p33_result_id, run_id=admission_run, error_summary=None,
    )

    class P33:
        def list_cycle_target_risk_results(self): return (p33,)
    class Queries:
        def list_cycle_target_asset_admission_results(self, query): return (result,)
        def list_cycle_target_asset_admission_operations(self, query): return (operation,)
    class Coordinator:
        preflight_command = None
        review_command = None
        def preflight(self, command): self.preflight_command = command; return SimpleNamespace(accepted=True, summary="control missing; no write")
        def review(self, command): self.review_command = command; return SimpleNamespace(summary="blocked missing")

    coordinator = Coordinator()
    panel = CycleTargetAssetAdmissionPanel(coordinator, Queries(), P33(), session_id="GUI")
    panel.p33_choice.setCurrentIndex(1); panel.reason.setText("explicit P35")
    panel.preflight_button.click()
    assert coordinator.preflight_command.p33_result_id == p33_result_id and coordinator.preflight_command.p33_run_id == p33_run
    panel.review_button.click()
    assert coordinator.review_command is coordinator.preflight_command
    opened = []; panel.open_run_requested.connect(opened.append); panel.results.selectRow(0)
    panel.open_admission.click(); panel.open_p33.click(); panel.open_p31.click(); panel.open_p29.click(); panel.open_p28.click(); panel.open_control.click()
    assert opened == [admission_run, p33_run, p31_run, p29_run, p28_run]
    assert panel.results.item(0, 4).text() == "MISSING"
    panel.close(); assert app is not None
