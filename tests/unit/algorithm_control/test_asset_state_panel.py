from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from quant_trading.algorithm_control.ui.asset_state_panel import AssetStatePanel
from quant_trading.asset_state import (
    AssetStateOperationStatus,
    AssetStateService,
    TradingCycleQuery,
    TradingCycleStatus,
)
from quant_trading.persistence import SQLiteAssetStateStore, SQLiteRunHistoryRepository
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState


def _panel(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    state = SQLiteAssetStateStore(database_path)
    state.initialize()
    runs = SQLiteRunHistoryRepository(database_path)
    runs.initialize()
    service = AssetStateService(
        state,
        AlgorithmRunService(runs),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
    )
    panel = AssetStatePanel(
        service, state, session_id="GUI-SESSION", created_by="gui-tester"
    )
    return panel, state, runs


def _fill_definition(panel: AssetStatePanel) -> None:
    panel.definition_name.setText("GUI symbolic graph")
    panel.definition_reason.setText("Manual research labels only")
    panel.initial_state_key.setText("OBSERVING")
    for key, label in (("OBSERVING", "Observing"), ("STATE_B", "State B")):
        panel._add_blank_row(panel.state_input_table)
        row = panel.state_input_table.rowCount() - 1
        panel.state_input_table.setItem(row, 0, QTableWidgetItem(key))
        panel.state_input_table.setItem(row, 1, QTableWidgetItem(label))
        panel.state_input_table.setItem(row, 2, QTableWidgetItem("No financial meaning"))
    panel._add_blank_row(panel.edge_input_table)
    panel.edge_input_table.setItem(0, 0, QTableWidgetItem("OBSERVING"))
    panel.edge_input_table.setItem(0, 1, QTableWidgetItem("STATE_B"))


def test_panel_manages_definition_cycle_transition_replay_and_open_run(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    panel, state, runs = _panel(tmp_path)
    opened = []
    panel.open_run_requested.connect(opened.append)

    _fill_definition(panel)
    panel.save_definition_button.click()
    assert panel.definition_table.rowCount() == 1
    assert panel.start_definition.count() == 1
    assert "completed" in panel.status_text.text()

    panel.start_symbol.setText("AAPL")
    panel.start_reason.setText("Start GUI research cycle")
    panel.start_cycle_button.click()
    cycles = state.list_cycles(TradingCycleQuery(symbol="AAPL"))
    assert len(cycles) == 1
    cycle_id = cycles[0].cycle.cycle_id
    assert panel.cycle_table.rowCount() == 1
    assert panel.destination_state.currentText() == "STATE_B"
    assert panel.transition_button.isEnabled()
    assert "MANUAL TRANSITION" in panel.safety_notice.text()

    panel.transition_reason.setText("Explicit GUI transition")
    panel.transition_button.click()
    detail = state.get_cycle_detail(cycle_id)
    assert detail.latest_snapshot.current_state_key == "STATE_B"
    assert detail.replay.status.value == "match"
    assert panel.timeline_table.rowCount() == 2
    assert not panel.transition_button.isEnabled()

    panel.close_reason.setText("Close GUI research cycle")
    panel.close_cycle_button.click()
    detail = state.get_cycle_detail(cycle_id)
    assert detail.cycle.status is TradingCycleStatus.CLOSED
    assert panel.timeline_table.rowCount() == 3
    assert not panel.close_cycle_button.isEnabled()

    panel.operation_table.selectRow(0)
    panel.open_operation_run_button.click()
    assert opened
    assert runs.get_run_detail(opened[-1]) is not None
    panel.close()
    assert app is not None


def test_panel_invalid_definition_is_visible_and_read_only_mode_disables_writes(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    panel, state, _runs = _panel(tmp_path)
    panel.definition_name.setText("Invalid")
    panel.definition_reason.setText("Missing states")
    panel.initial_state_key.setText("UNKNOWN")
    panel.save_definition_button.click()

    assert state.list_definitions() == ()
    assert any(
        panel.operation_table.item(row, 3).text()
        == AssetStateOperationStatus.INVALID_INPUT.value
        for row in range(panel.operation_table.rowCount())
    )
    panel.close()

    read_only_store = SQLiteAssetStateStore(tmp_path / "readonly.sqlite3")
    read_only_store.initialize()
    read_only = AssetStatePanel(None, read_only_store)
    assert not read_only.save_definition_button.isEnabled()
    assert not read_only.start_cycle_button.isEnabled()
    assert not read_only.transition_button.isEnabled()
    assert not read_only.close_cycle_button.isEnabled()
    read_only.close()
    assert app is not None
