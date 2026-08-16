from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.mathematical_cycle_target_link_panel import (
    MathematicalCycleTargetLinkPanel,
)

sys.path.insert(0, str(Path(__file__).parents[1] / "asset_state"))
from test_sqlite_mathematical_cycle_target_link import _environment


def test_panel_starts_blank_requires_preflight_and_opens_all_run_links(tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    coordinator, _, store, targets, state, _, _ = _environment(tmp_path / "gui.sqlite3")
    panel = MathematicalCycleTargetLinkPanel(
        coordinator, store, state, targets, session_id="GUI", created_by="gui-tester"
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.state_operation.currentData() is None
    assert panel.configuration.currentData() is None
    assert not panel.preview_button.isEnabled()
    panel.state_operation.setCurrentIndex(1)
    panel.configuration.setCurrentIndex(1)
    panel.capital_basis.setText("100000")
    panel.current_position.setText("50000")
    panel.reason.setText("explicit GUI P39 preview")
    panel.preflight_button.click()
    assert panel.preview_button.isEnabled(), panel.status_text.text()
    panel.preview_button.click()

    assert panel.history.rowCount() == 1
    panel.history.selectRow(0)
    assert "P37 operation/Run/stream/snapshot" in panel.detail.text()
    assert "NO EXECUTION" in panel.detail.text()
    panel.open_bridge_run.click()
    panel.open_state_run.click()
    panel.open_target_run.click()
    panel.open_source_run.click()
    operation = store.list_operations()[0]
    assert opened == [
        operation.bridge_run_id, operation.requested_state_run_id,
        operation.resolved_target_run_id, operation.resolved_source_run_id,
    ]
    panel.close()
    assert application is not None
