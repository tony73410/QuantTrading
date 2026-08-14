from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.mathematical_cycle_panel import MathematicalCyclePanel
from quant_trading.asset_state import EmptyMathematicalCycleStateQueryService


def test_empty_mathematical_cycle_inspector_is_read_only_and_has_no_default_stream():
    app = QApplication.instance() or QApplication([])
    panel = MathematicalCyclePanel(EmptyMathematicalCycleStateQueryService())

    assert panel.stream_table.rowCount() == 0
    assert panel.operation_table.rowCount() == 0
    assert "No mathematical-cycle stream" in panel.detail_label.text()
    assert "No active/default stream exists" in panel.status_text.text()
    assert not panel.open_run_button.isEnabled()
    assert not [button for button in panel.findChildren(type(panel.reload_button)) if "Create" in button.text() or "Promote" in button.text()]
    panel.close()
    assert app is not None
