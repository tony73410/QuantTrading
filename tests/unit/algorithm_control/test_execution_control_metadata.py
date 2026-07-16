from pathlib import Path

from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.models import ComponentStatus, ComponentType


def test_execution_control_exposes_two_disabled_declaration_only_boundaries(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    components = controller.components(ComponentType.EXECUTION)

    assert {item.component_id for item in components} == {
        "execution.alpaca_paper_boundary",
        "execution.alpaca_live_boundary",
    }
    assert all(item.status is ComponentStatus.NOT_IMPLEMENTED for item in components)
    assert all(not item.enabled_by_default for item in components)
    assert all(not item.execution_allowed and not item.live_allowed for item in components)
    assert all(item.input_contract == "ApprovedTradeIntent" for item in components)
