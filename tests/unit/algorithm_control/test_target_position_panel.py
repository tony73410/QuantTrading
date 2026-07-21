from __future__ import annotations

import os
from pathlib import Path
from decimal import Decimal
from datetime import UTC, datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from quant_trading.algorithm_control.ui.target_position_panel import TargetPositionPanel
from quant_trading.persistence import SQLiteRunHistoryRepository, SQLiteTargetPositionStore
from quant_trading.persistence import SQLiteStandardizedPriceStateStore
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState
from quant_trading.target_position import (
    LinkedTargetPositionService,
    TargetPositionOperationStatus,
    TargetPositionService,
)
from quant_trading.factors import (
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateService,
)
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
)
from quant_trading.visualization import PlotlyFigureView


def _panel(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(PlotlyFigureView, "show_figure", lambda self, figure: None)
    database = tmp_path / "central.sqlite3"
    store = SQLiteTargetPositionStore(database)
    store.initialize()
    runs = SQLiteRunHistoryRepository(database)
    runs.initialize()
    service = TargetPositionService(
        store,
        AlgorithmRunService(runs),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
    )
    panel = TargetPositionPanel(
        service, store, session_id="GUI-SESSION", created_by="gui-tester"
    )
    return panel, store, runs


def _fill_definition(panel: TargetPositionPanel) -> None:
    panel.definition_name.setText("GUI curve")
    panel.definition_reason.setText("Explicit GUI research definition")
    panel.minimum_fraction.setText("0.1")
    panel.neutral_fraction.setText("0.5")
    panel.maximum_fraction.setText("0.9")
    for state, target in (("-2", "0.9"), ("0", "0.5"), ("2", "0.1")):
        panel._add_knot()
        row = panel.knot_table.rowCount() - 1
        panel.knot_table.setItem(row, 0, QTableWidgetItem(state))
        panel.knot_table.setItem(row, 1, QTableWidgetItem(target))


def test_panel_saves_definition_previews_and_opens_exact_run(tmp_path: Path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    panel, store, runs = _panel(tmp_path, monkeypatch)
    opened = []
    panel.open_run_requested.connect(opened.append)

    _fill_definition(panel)
    panel.save_definition_button.click()
    assert panel.definition_table.rowCount() == 1, panel.status_text.text()
    assert panel.preview_definition.count() == 1
    assert "disabled research" in panel.status_text.text()

    panel.research_state_value.setText("-1")
    panel.research_capital_basis.setText("100")
    panel.current_position_value.setText("60")
    panel.preview_reason.setText("Explicit GUI preview")
    panel.preview_button.click()
    assert panel.result_table.rowCount() == 1
    assert panel.operation_table.rowCount() == 2
    result = store.list_results()[0]
    assert result.target_fraction == Decimal("0.7")
    assert "no TradeIntent or order" in panel.status_text.text()
    assert "interpolated" in panel.trace_text.text()
    assert "current fraction 0.6" in panel.trace_text.text()

    panel.open_last_run_button.click()
    assert opened == [result.run_id]
    assert runs.get_run_detail(opened[0]) is not None
    panel.close()
    assert app is not None


def test_panel_invalid_preview_visible_and_read_only_disables_writes(tmp_path: Path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    panel, store, _runs = _panel(tmp_path, monkeypatch)
    _fill_definition(panel)
    panel.save_definition_button.click()
    panel.research_state_value.setText("0")
    panel.research_capital_basis.setText("-1")
    panel.current_position_value.setText("0")
    panel.preview_reason.setText("Invalid negative basis")
    panel.preview_button.click()
    assert store.list_results() == ()
    assert any(
        panel.operation_table.item(row, 2).text()
        == TargetPositionOperationStatus.INVALID_INPUT.value
        for row in range(panel.operation_table.rowCount())
    )
    panel.close()

    readonly_store = SQLiteTargetPositionStore(tmp_path / "readonly.sqlite3")
    readonly_store.initialize()
    readonly = TargetPositionPanel(None, readonly_store)
    assert not readonly.add_knot_button.isEnabled()
    assert not readonly.remove_knot_button.isEnabled()
    assert not readonly.save_definition_button.isEnabled()
    assert not readonly.preview_button.isEnabled()
    readonly.close()
    assert app is not None


def test_panel_links_exact_standardized_result_and_opens_three_runs(tmp_path: Path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(PlotlyFigureView, "show_figure", lambda self, figure: None)
    database = tmp_path / "linked.sqlite3"
    runs = SQLiteRunHistoryRepository(database)
    runs.initialize()
    software = SoftwareIdentity("test", "abc123", WorktreeState.CLEAN)
    source_store = SQLiteStandardizedPriceStateStore(database)
    source_store.initialize()
    source_service = StandardizedPriceStateService(
        source_store, AlgorithmRunService(runs), software
    )
    source_definition = source_service.create_definition(
        CreateStandardizedPriceStateDefinitionCommand(
            "GUI source", "Exact GUI source", "GUI", "SOURCE-DEFINE", "gui-tester"
        )
    )
    source = source_service.preview(
        PreviewStandardizedPriceStateCommand(
            source_definition.definition_id,
            "AAPL",
            "90",
            "100",
            "10",
            datetime(2026, 7, 21, 1, 0, tzinfo=UTC),
            "Exact GUI source result",
            "GUI",
            "SOURCE-PREVIEW",
            "gui-tester",
        )
    )
    target_store = SQLiteTargetPositionStore(database)
    target_store.initialize()
    target_service = TargetPositionService(
        target_store, AlgorithmRunService(runs), software
    )
    linked_service = LinkedTargetPositionService(
        target_store, AlgorithmRunService(runs), software
    )
    coordinator = StandardizedStateTargetPositionPreviewCoordinator(
        source_store,
        target_store,
        linked_service,
        AlgorithmRunService(runs),
        software,
    )
    panel = TargetPositionPanel(
        target_service,
        target_store,
        session_id="GUI",
        created_by="gui-tester",
        linked_preview_service=coordinator,
        standardized_state_queries=source_store,
    )
    opened = []
    panel.open_run_requested.connect(opened.append)
    _fill_definition(panel)
    panel.save_definition_button.click()

    assert panel.linked_source_result.count() == 2
    assert panel.linked_definition.count() == 2
    assert not panel.linked_preview_button.isEnabled()
    panel.linked_source_result.setCurrentIndex(1)
    panel.linked_definition.setCurrentIndex(1)
    assert str(source.calculation_id) in panel.linked_source_detail.text()
    assert "state -1" in panel.linked_source_detail.text()
    assert panel.linked_preview_button.isEnabled()
    panel.linked_capital_basis.setText("100")
    panel.linked_current_position.setText("60")
    panel.linked_reason.setText("Exact GUI link")
    panel.linked_preview_button.click()

    assert panel.linked_operation_table.rowCount() == 1
    assert panel.result_table.rowCount() == 1
    link = target_store.list_standardized_state_links()[0]
    result = target_store.get_result(link.target_calculation_id)
    assert result.research_state_value == Decimal("-1")
    assert result.target_fraction == Decimal("0.7")
    assert panel.linked_operation_table.item(0, 2).text() == "AAPL"
    assert panel.linked_operation_table.item(0, 3).text() == "-1"

    panel.open_source_run_button.click()
    panel.open_parent_run_button.click()
    panel.open_child_run_button.click()
    assert opened == [link.source_run_id, link.parent_run_id, link.child_run_id]
    panel.close()
    assert app is not None
