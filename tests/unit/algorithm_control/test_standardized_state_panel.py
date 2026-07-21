from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.standardized_state_panel import (
    StandardizedPriceStatePanel,
)
from quant_trading.factors import (
    StandardizedPriceStateOperationStatus,
    StandardizedPriceStateService,
)
from quant_trading.persistence import (
    SQLiteRunHistoryRepository,
    SQLiteStandardizedPriceStateStore,
)
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState


def _panel(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    store = SQLiteStandardizedPriceStateStore(database)
    store.initialize()
    runs = SQLiteRunHistoryRepository(database)
    runs.initialize()
    service = StandardizedPriceStateService(
        store,
        AlgorithmRunService(runs),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
    )
    panel = StandardizedPriceStatePanel(
        service, store, session_id="GUI-SESSION", created_by="gui-tester"
    )
    return panel, store, runs


def _save_definition(panel: StandardizedPriceStatePanel) -> None:
    panel.definition_name.setText("GUI manual state")
    panel.definition_reason.setText("Explicit GUI research definition")
    panel.save_definition_button.click()


def test_panel_saves_previews_shows_trace_and_opens_exact_run(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    panel, store, runs = _panel(tmp_path)
    opened = []
    panel.open_run_requested.connect(opened.append)

    _save_definition(panel)
    assert panel.definition_table.rowCount() == 1, panel.status_text.text()
    panel.symbol.setText("AAPL")
    panel.manual_price.setText("90")
    panel.manual_reference.setText("100")
    panel.manual_risk_scale.setText("5")
    panel.preview_reason.setText("Explicit GUI preview")
    panel.preview_button.click()

    assert panel.result_table.rowCount() == 1, panel.status_text.text()
    assert panel.operation_table.rowCount() == 2
    result = store.list_results()[0]
    assert result.standardized_state == Decimal("-2")
    assert "dimensionless standardized state -2" in panel.trace_text.text()
    assert "NO TARGET / NO TRADE / NO EXECUTION" in panel.safety_notice.text()

    panel.open_run_button.click()
    assert opened == [result.run_id]
    assert runs.get_run_detail(opened[0]) is not None
    panel.close()
    assert app is not None


def test_panel_persists_invalid_attempt_and_read_only_disables_writes(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    panel, store, _runs = _panel(tmp_path)
    _save_definition(panel)
    panel.symbol.setText("AAPL")
    panel.manual_price.setText("90")
    panel.manual_reference.setText("100")
    panel.manual_risk_scale.setText("0")
    panel.preview_reason.setText("Invalid zero scale")
    panel.preview_button.click()
    assert store.list_results() == ()
    assert any(
        panel.operation_table.item(row, 3).text()
        == StandardizedPriceStateOperationStatus.INVALID_INPUT.value
        for row in range(panel.operation_table.rowCount())
    )
    panel.close()

    readonly_store = SQLiteStandardizedPriceStateStore(tmp_path / "readonly.sqlite3")
    readonly_store.initialize()
    readonly = StandardizedPriceStatePanel(None, readonly_store)
    assert not readonly.save_definition_button.isEnabled()
    assert not readonly.preview_button.isEnabled()
    readonly.close()
    assert app is not None
