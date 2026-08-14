from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.asset_state_workspace_panel import AssetStateWorkspacePanel
from quant_trading.algorithm_control.ui.reversal_observation_panel import ReversalObservationPanel
from quant_trading.asset_state import (
    EmptyAssetStateQueryService,
    ReversalObservationService,
)
from quant_trading.factors.daily_volatility_profile_interfaces import (
    EmptyDailyVolatilityProfileQueryService,
)
from quant_trading.persistence import SQLiteReversalObservationStore, SQLiteRunHistoryRepository
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState


def _environment(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store = SQLiteReversalObservationStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = ReversalObservationService(
        store, AlgorithmRunService(runs),
        SoftwareIdentity("test", "revision", WorktreeState.CLEAN),
    )
    return store, service


def test_panel_creates_explicit_immutable_versions_without_a_default_multiplier(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    store, service = _environment(tmp_path)
    panel = ReversalObservationPanel(
        service, store, EmptyDailyVolatilityProfileQueryService(), None,
        session_id="GUI-SESSION", created_by="gui-tester",
    )

    assert panel.multiplier.text() == ""
    assert panel.definition.currentData() is None
    assert panel.profile.currentData() is None
    assert panel.direction.currentData() is None
    assert not panel.run_button.isEnabled()

    panel.multiplier.setText("1.25")
    panel.definition_reason.setText("first symmetric multiplier version")
    panel.save_definition_button.click()
    first = store.list_definitions()[0]
    assert first.definition_version == 1
    assert first.shared_multiplier_input_text == "1.25"

    panel.predecessor.setCurrentIndex(panel.predecessor.findData(str(first.definition_id)))
    assert panel.predecessor.currentData() == str(first.definition_id)
    panel.multiplier.setText("1.50")
    panel.definition_reason.setText("explicit second version")
    panel.save_definition_button.click()
    assert "不可变版本已保存" in panel.preflight_text.text(), panel.preflight_text.text()
    definitions = store.list_definitions()
    second = next(item for item in definitions if item.definition_version == 2)
    assert second.predecessor_definition_id == first.definition_id
    assert second.shared_multiplier_input_text == "1.50"
    assert panel.history.rowCount() == 2
    assert "NO EXECUTION" in panel.safety_notice.text()
    panel.close()
    assert app is not None


def test_asset_state_workspace_keeps_manual_ledger_and_p28_as_separate_subtabs(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    store, service = _environment(tmp_path)
    workspace = AssetStateWorkspacePanel(
        None, EmptyAssetStateQueryService(), service, store,
        EmptyDailyVolatilityProfileQueryService(), None, session_id="GUI-SESSION",
    )
    assert workspace.tabs.count() == 4
    assert "P23-2B Mathematical Cycles" == workspace.tabs.tabText(3)
    assert workspace.mathematical_cycles.stream_table.rowCount() == 0
    assert workspace.tabs.tabText(0) == "人工状态账本"
    assert workspace.tabs.tabText(1) == "P23-2 反转观察"
    assert workspace.tabs.tabText(2) == "P23-4C1 Trading Control"
    workspace.close()
    assert app is not None
