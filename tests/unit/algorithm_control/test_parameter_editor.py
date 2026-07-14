import os
from datetime import date
from decimal import Decimal

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.models import ParameterSchema, ParameterType
from quant_trading.algorithm_control.ui.parameter_editor import ParameterEditor
from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.ui.main_panel import AlgorithmControlPanel


def test_parameter_editor_is_generated_from_schema():
    app = QApplication.instance() or QApplication([])
    editor = ParameterEditor()
    schemas = (
        ParameterSchema("count", "Count", "Count", ParameterType.INTEGER, 2, 1, 5),
        ParameterSchema("rate", "Rate", "Rate", ParameterType.PERCENTAGE, Decimal("10")),
        ParameterSchema("enabled", "Enabled", "Enabled", ParameterType.BOOLEAN, True),
        ParameterSchema("mode", "Mode", "Mode", ParameterType.ENUM, "a", allowed_values=("a", "b")),
        ParameterSchema("day", "Day", "Day", ParameterType.DATE, date(2026, 7, 14)),
        ParameterSchema("items", "Items", "Items", ParameterType.LIST, ("AAPL", "MSFT")),
    )
    editor.set_schema(schemas, {})
    values = editor.values()
    assert values == {
        "count": 2,
        "rate": Decimal("10.0"),
        "enabled": True,
        "mode": "a",
        "day": date(2026, 7, 14),
        "items": ("AAPL", "MSFT"),
    }
    editor.close()
    assert app is not None


def test_control_panel_shows_empty_algorithm_layers_and_locked_risk_invariants(tmp_path):
    app = QApplication.instance() or QApplication([])
    panel = AlgorithmControlPanel(build_controller(tmp_path))
    assert panel.tabs.count() == 7
    assert panel.factor_page.list.count() == 0
    assert panel.decision_page.list.count() == 0
    assert panel.risk_page.list.count() == 4
    assert panel.conflict_table.rowCount() == 3
    assert {
        panel.conflict_table.item(row, 0).text()
        for row in range(panel.conflict_table.rowCount())
    } == {
        "CONFLICT-PIPELINE-MISSING-FACTOR",
        "CONFLICT-PIPELINE-MISSING-DECISION",
        "CONFLICT-PIPELINE-MISSING-RISK",
    }
    assert "关闭" in panel.overview_text.text()
    assert not panel.dry_run_button.isEnabled()
    panel.close()
    assert app is not None
