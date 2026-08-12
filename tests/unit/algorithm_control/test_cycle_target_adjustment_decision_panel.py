from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.cycle_target_adjustment_decision_panel import (
    CycleTargetAdjustmentDecisionPanel,
)

sys.path.insert(0, str(Path(__file__).parents[1] / "asset_state"))
from test_sqlite_cycle_target_adjustment_decision import _system


def test_p31_panel_requires_explicit_source_and_exposes_exact_run_chain(tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    store, _, _, p29, _, coordinator = _system(tmp_path / "gui.sqlite3")
    panel = CycleTargetAdjustmentDecisionPanel(
        coordinator, store, coordinator._cycle_targets,
        session_id="GUI", created_by="gui-tester",
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.source.count() == 2
    assert panel.source.currentData() is None
    assert not panel.preview_button.isEnabled()
    panel.source.setCurrentIndex(1)
    panel.reason.setText("Explicit P29 Result/Run GUI preview")
    assert panel.preflight_button.isEnabled()
    assert not panel.preview_button.isEnabled()
    panel.preflight_button.click()
    assert "No Run or P31 result was written" in panel.status_text.text()
    assert panel.preview_button.isEnabled()
    panel.preview_button.click()

    assert panel.history.rowCount() == 1
    panel.history.selectRow(0)
    assert "exact signed difference" in panel.detail.text()
    assert "execution_allowed=False" in panel.detail.text()
    panel.open_decision_run.click()
    panel.open_p29_run.click()
    panel.open_p28_run.click()
    result = store.list_cycle_target_adjustment_results()[0]
    assert opened == [
        result.run_id,
        p29.run_id,
        result.source.source_reversal_run_id,
    ]
    panel.close()
    assert application is not None
