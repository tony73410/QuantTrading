from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.cycle_target_position_panel import (
    CycleTargetPositionPanel,
)
from quant_trading.orchestration import CycleTargetPositionResearchCoordinator
from quant_trading.persistence import CentralSQLiteDatabase, SQLiteCycleTargetPositionStore
from quant_trading.run_history import AlgorithmRunService
from quant_trading.target_position import CycleTargetPositionService

sys.path.insert(0, str(Path(__file__).parents[1] / "asset_state"))
from test_sqlite_cycle_target_position import NOW, _p28


def test_cycle_target_panel_requires_exact_source_and_persists_inspectable_result(
    tmp_path: Path,
):
    application = QApplication.instance() or QApplication([])
    path = tmp_path / "gui.sqlite3"
    reversal, runs, p28, software = _p28(path)
    store = SQLiteCycleTargetPositionStore(CentralSQLiteDatabase(path))
    service = CycleTargetPositionService(
        store, AlgorithmRunService(runs), software, clock=lambda: NOW
    )
    runner = CycleTargetPositionResearchCoordinator(reversal, service)
    panel = CycleTargetPositionPanel(
        service, store, reversal, runner, session_id="GUI", created_by="gui-tester"
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.source_result.currentData() is None
    assert panel.source_step.currentData() is None
    assert not panel.preview_button.isEnabled()

    panel.formula_name.setText("P29 GUI formula")
    panel.formula_reason.setText("Explicit approved formula family")
    panel.save_formula_button.click()
    assert panel.configuration_formula.count() == 2

    panel.configuration_formula.setCurrentIndex(1)
    panel.configuration_symbol.setText("AAPL")
    for widget, value in (
        (panel.minimum, "0.1"), (panel.neutral, "0.5"),
        (panel.maximum, "0.9"), (panel.slope, "0.05"),
        (panel.start, "2"), (panel.saturation, "4"),
    ):
        widget.setText(value)
    panel.configuration_reason.setText("Explicit AAPL research parameters")
    panel.save_configuration_button.click()
    assert panel.preview_configuration.count() == 2
    assert panel.source_result.count() == 2

    panel.preview_configuration.setCurrentIndex(1)
    panel.source_result.setCurrentIndex(1)
    assert panel.source_step.count() == len(p28.result.daily_steps) + 1
    panel.source_step.setCurrentIndex(panel.source_step.count() - 1)
    panel.capital_basis.setText("100000")
    panel.current_position.setText("50000")
    panel.preview_reason.setText("Explicit exact P28 step GUI preview")
    assert panel.preflight_button.isEnabled()
    panel.preflight_button.click()
    assert panel.preview_button.isEnabled(), panel.status_text.text()
    panel.preview_button.click()

    results = store.list_results()
    assert len(results) == 1
    result = results[0]
    assert result.source.source_result_id == p28.result.result_id
    assert result.source.source_step_id == p28.result.daily_steps[-1].step_id
    assert panel.history.rowCount() == 3
    result_row = next(
        row for row in range(panel.history.rowCount())
        if panel.history.item(row, 8).text() != "—"
    )
    panel.history.selectRow(result_row)
    assert "execution_allowed=False" in panel.detail.text()
    panel.replay_button.click()
    assert "Replay MATCH" in panel.status_text.text()
    panel.open_run_button.click()
    panel.open_p28_run_button.click()
    panel.open_p27_run_button.click()
    panel.open_p26_run_button.click()
    assert opened == [
        result.run_id, result.source.source_run_id,
        result.source.source_profile_run_id, result.source.source_parent_run_id,
    ]
    panel.close()
    assert application is not None
