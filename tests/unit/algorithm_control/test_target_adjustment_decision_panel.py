from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.target_adjustment_decision_panel import (
    TargetAdjustmentDecisionPanel,
)
from quant_trading.decision import (
    DecisionAction,
    TargetAdjustmentDecisionStatus,
)


NOW = datetime(2026, 7, 21, 2, 0, tzinfo=UTC)


def test_panel_requires_explicit_link_delegates_and_opens_all_related_runs():
    app = QApplication.instance() or QApplication([])
    link_id = uuid4()
    parent_run = uuid4()
    target_run = uuid4()
    source_run = uuid4()
    decision_run = uuid4()
    target_calculation = uuid4()
    link = SimpleNamespace(
        link_id=link_id,
        symbol="AAPL",
        source_as_of_utc=NOW,
        standardized_state=Decimal("-1"),
        source_calculation_id=uuid4(),
        source_definition_id=uuid4(),
        source_definition_version=1,
        parent_run_id=parent_run,
        child_run_id=target_run,
        target_calculation_id=target_calculation,
        target_definition_id=uuid4(),
        target_definition_version=1,
    )
    target = SimpleNamespace(
        research_capital_basis_usd=Decimal("100"),
        current_position_value_usd=Decimal("60"),
        target_fraction=Decimal("0.7"),
        target_position_value_usd=Decimal("70"),
        adjustment_value_usd=Decimal("10"),
        adjustment_direction=SimpleNamespace(value="increase"),
    )
    source = SimpleNamespace(
        as_of_utc=NOW,
        symbol="AAPL",
        current_position_value_usd=Decimal("60"),
        target_position_value_usd=Decimal("70"),
        adjustment_value_usd=Decimal("10"),
        linked_parent_run_id=parent_run,
        target_child_run_id=target_run,
        standardized_state_run_id=source_run,
    )
    intent = SimpleNamespace(requested_notional_usd=Decimal("10"))
    result = SimpleNamespace(
        source=source,
        action=DecisionAction.INCREASE,
        status=TargetAdjustmentDecisionStatus.INTENT_CREATED,
        intents=(intent,),
        run_id=decision_run,
    )
    operation = SimpleNamespace(
        completed_at_utc=NOW,
        status=TargetAdjustmentDecisionStatus.INTENT_CREATED,
        requested_target_position_link_id=link_id,
        run_id=decision_run,
        decision_result_id=uuid4(),
        error_summary=None,
    )

    class TargetQueries:
        def list_standardized_state_links(self, query):
            return (link,)

        def get_result(self, calculation_id):
            assert calculation_id == target_calculation
            return target

    class DecisionQueries:
        def list_target_adjustment_results(self, query):
            return (result,)

        def list_target_adjustment_operations(self, query):
            return (operation,)

    class PreviewService:
        command = None

        def preview(self, command):
            self.command = command
            return SimpleNamespace(summary="delegated exact preview")

    preview = PreviewService()
    panel = TargetAdjustmentDecisionPanel(
        preview,
        DecisionQueries(),
        TargetQueries(),
        session_id="GUI-SESSION",
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.source_choice.count() == 2
    assert panel.source_choice.currentData() is None
    panel.reason.setText("Explicit GUI research preview")
    panel.preview_button.click()
    assert "必须明确选择" in panel.status_text.text()

    panel.source_choice.setCurrentIndex(1)
    assert panel.source_fields.rowCount() == 18
    panel.preview_button.click()
    assert preview.command.target_position_link_id == link_id
    assert preview.command.reason == "Explicit GUI research preview"
    assert "delegated exact preview" in panel.status_text.text()

    panel.result_table.setCurrentCell(0, 0)
    panel.open_decision_run.click()
    panel.open_parent_run.click()
    panel.open_target_run.click()
    panel.open_source_run.click()
    assert opened == [decision_run, parent_run, target_run, source_run]
    panel.close()
    assert app is not None
