import os
from datetime import date
from decimal import Decimal

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.admission_models import (
    Capability,
    OwnerLayer,
    Responsibility,
)
from quant_trading.algorithm_control.models import (
    ComponentMetadata,
    ComponentStatus,
    ComponentType,
    ParameterSchema,
    ParameterType,
)
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


def test_factor_catalog_and_decision_factor_choices_are_visible(tmp_path):
    app = QApplication.instance() or QApplication([])
    controller = build_controller(tmp_path)
    factor = controller.save_factor_definition(
        factor_id="user.gui_input",
        display_name="GUI input Factor",
        description="Restricted Factor used for an offscreen GUI regression test.",
        expression='latest("close")',
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(),
        change_reason="Test GUI catalog",
    )
    controller.registry.register(
        ComponentMetadata(
            component_id="test.gui.decision",
            display_name="GUI Decision test",
            component_type=ComponentType.DECISION,
            version="1",
            description="Metadata only; no decision behavior.",
            status=ComponentStatus.NOT_IMPLEMENTED,
            parameter_schema=(),
            input_contract="FactorSnapshot",
            output_contract="TradeIntent",
            minimum_data_requirements="Selected FactorSnapshot",
            enabled_by_default=False,
            implementation_path="Not implemented",
            documentation_path="tests only",
            owner_layer=OwnerLayer.DECISION,
            owner_module="tests.decision",
            responsibilities=(Responsibility.CREATE_TRADE_INTENTS,),
            non_responsibilities=("No factor calculation or execution.",),
            required_capabilities=(
                Capability.READ_FACTOR_SNAPSHOT,
                Capability.CREATE_TRADE_INTENT,
            ),
        )
    )

    panel = AlgorithmControlPanel(controller)

    assert panel.factor_page.authoring.list.count() == 1
    assert panel.factor_page.components.list.count() == 1
    assert panel.decision_page.list.count() == 1
    assert panel.decision_page.factor_choices.count() == 1
    assert (
        panel.decision_page.factor_choices.item(0).data(Qt.ItemDataRole.UserRole)
        == factor.component_id
    )
    panel.close()
    assert app is not None
