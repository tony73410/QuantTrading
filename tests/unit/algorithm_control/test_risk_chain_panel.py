from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QWidget

from quant_trading.algorithm_control.ui.risk_chain_panel import RiskChainExplorerPanel
from quant_trading.algorithm_control.ui.target_adjustment_risk_panel import (
    RiskManagementPanel,
)

from tests.unit.algorithm_control.test_risk_chain_inspection import _chain_system


def test_panel_shows_separate_structural_and_numerical_evidence_and_opens_runs(
    tmp_path: Path,
):
    app = QApplication.instance() or QApplication([])
    service, outcome = _chain_system(tmp_path / "central.sqlite3")
    chain = service.get_chain(outcome.preview_result_id)
    panel = RiskChainExplorerPanel(service)
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.result_table.rowCount() == 1
    assert panel.structural_table.rowCount() == 3
    assert panel.numerical_table.rowCount() == 3
    assert panel.summary_table.item(19, 1).text() == "False"

    for key in (
        "phase6d", "phase6c", "phase6b", "phase6a", "decision",
        "linked_target", "target", "standardized", "capital",
    ):
        panel._run_buttons[key].click()
    link = chain.phase6d_source_link
    assert opened == [
        link.asset_cash_run_id,
        link.phase6c_run_id,
        link.phase6b_run_id,
        link.phase6a_run_id,
        link.decision_run_id,
        link.linked_parent_run_id,
        link.target_child_run_id,
        link.standardized_state_run_id,
        link.capital_snapshot_run_id,
    ]

    panel.compare_left.setCurrentIndex(1)
    panel.compare_right.setCurrentIndex(1)
    panel.compare_button.click()
    assert panel.comparison_table.rowCount() > 0
    assert all(
        panel.comparison_table.item(row, 3).text() == "True"
        for row in range(panel.comparison_table.rowCount())
    )
    assert "no numerical deltas" in panel.status_text.text()
    panel.close()
    assert app is not None


def test_panel_surfaces_invalid_date_range_without_a_completed_view(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    service, _outcome = _chain_system(tmp_path / "central.sqlite3")
    panel = RiskChainExplorerPanel(service)

    panel.as_of_from.setText("2026-07-22T00:00:00+00:00")
    panel.as_of_to.setText("2026-07-21T00:00:00+00:00")
    panel.reload()

    assert panel.result_table.rowCount() == 0
    assert "no completed chain view" in panel.status_text.text()
    panel.close()
    assert app is not None


def test_risk_management_panel_preserves_positional_parent_compatibility():
    app = QApplication.instance() or QApplication([])

    class DummyPanel(QWidget):
        preview_requested = Signal(object)
        state_changed = Signal()
        open_run_requested = Signal(object)

        def __init__(self):
            super().__init__()
            self.list = object()

        def reload(self):
            pass

    parent = QWidget()
    component = DummyPanel()
    specialized = DummyPanel()
    panel = RiskManagementPanel(
        component,
        specialized,
        DummyPanel(),
        DummyPanel(),
        DummyPanel(),
        parent,
    )

    assert panel.parent() is parent
    assert panel.risk_chain is None
    panel.close()
    parent.close()
    assert app is not None
