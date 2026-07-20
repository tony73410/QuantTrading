from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from quant_trading.algorithm_control.ui.capital_allocation_panel import (
    CapitalAllocationPanel,
)
from quant_trading.capital_allocation import CapitalAllocationService, CapitalPlanQuery
from quant_trading.persistence import SQLiteCapitalAllocationStore, SQLiteRunHistoryRepository
from quant_trading.run_history import (
    AlgorithmRunService,
    SoftwareIdentity,
    WorktreeState,
)


def _panel(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    capital = SQLiteCapitalAllocationStore(database_path)
    capital.initialize()
    runs = SQLiteRunHistoryRepository(database_path)
    runs.initialize()
    service = CapitalAllocationService(
        capital,
        AlgorithmRunService(runs),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
    )
    panel = CapitalAllocationPanel(
        service,
        capital,
        session_id="GUI-SESSION",
        created_by="gui-tester",
    )
    return panel, capital, runs


def _fill_valid_plan(panel: CapitalAllocationPanel) -> None:
    panel.plan_name.setText("GUI research plan")
    panel.account_cash_basis.setText("1000")
    panel.locked_reserve.setText("100")
    panel.tactical_reserve.setText("100")
    panel.plan_reason.setText("GUI integration test")
    panel._add_asset_row()
    panel._add_asset_row()
    panel.asset_input_table.setItem(0, 0, QTableWidgetItem("AAPL"))
    panel.asset_input_table.setItem(0, 1, QTableWidgetItem("400"))
    panel.asset_input_table.setItem(1, 0, QTableWidgetItem("MSFT"))
    panel.asset_input_table.setItem(1, 1, QTableWidgetItem("400"))


def test_panel_creates_conserved_plan_transfers_and_opens_run(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    panel, capital, runs = _panel(tmp_path)
    opened = []
    panel.open_run_requested.connect(opened.append)

    _fill_valid_plan(panel)
    panel.create_plan_button.click()

    summaries = capital.list_plans(CapitalPlanQuery())
    assert len(summaries) == 1
    plan_id = summaries[0].plan_id
    assert panel.plan_table.rowCount() == 1
    assert panel.bucket_table.rowCount() == 4
    assert panel.transfer_button.isEnabled()
    assert "completed" in panel.status_text.text()
    assert "NO EXECUTION" in panel.safety_notice.text()

    panel.destination_bucket.setCurrentIndex(1)
    panel.transfer_amount.setText("25.50")
    panel.transfer_reason.setText("GUI zero-sum transfer")
    panel.transfer_button.click()

    detail = capital.get_plan_detail(plan_id)
    balances = {
        item.symbol: item.balance
        for item in detail.latest_snapshot.balances
        if item.symbol is not None
    }
    assert str(balances["AAPL"]) == "374.50"
    assert str(balances["MSFT"]) == "425.50"
    assert detail.latest_snapshot.conservation.difference == 0
    assert panel.transfer_table.rowCount() == 1
    assert panel.transfer_table.item(0, 1).text() == "AAPL"
    assert panel.transfer_table.item(0, 2).text() == "400"
    assert panel.transfer_table.item(0, 3).text() == "374.50"
    assert panel.transfer_table.item(0, 4).text() == "MSFT"
    assert panel.transfer_table.item(0, 5).text() == "400"
    assert panel.transfer_table.item(0, 6).text() == "425.50"
    assert panel.operation_table.rowCount() == 2

    panel.operation_table.selectRow(0)
    panel.open_operation_run_button.click()
    assert opened
    assert runs.get_run_detail(opened[-1]) is not None
    panel.close()
    assert app is not None


def test_panel_without_write_service_remains_read_only(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    capital = SQLiteCapitalAllocationStore(tmp_path / "central.sqlite3")
    capital.initialize()
    panel = CapitalAllocationPanel(None, capital)

    assert not panel.create_plan_button.isEnabled()
    assert not panel.transfer_button.isEnabled()
    assert panel.plan_table.rowCount() == 0
    panel.close()
    assert app is not None
