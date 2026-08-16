from pathlib import Path


ROOT = Path(__file__).parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_p39_owner_contracts_remain_disabled_and_do_not_depend_on_downstream_layers():
    models = _source("src/quant_trading/target_position/mathematical_cycle_link_models.py")
    interfaces = _source("src/quant_trading/target_position/mathematical_cycle_link_interfaces.py")
    combined = models + interfaces
    assert "target_position.mathematical_cycle_link.p23_3b.v1" in models
    assert "execution_allowed: bool = False" in models
    assert "live_allowed: bool = False" in models
    for forbidden in (
        "quant_trading.decision", "quant_trading.risk", "quant_trading.execution",
        "quant_trading.persistence", "quant_trading.algorithm_control", "alpaca",
    ):
        assert forbidden not in combined


def test_p39_orchestration_uses_public_ports_and_delegates_existing_p29_command():
    source = _source("src/quant_trading/orchestration/mathematical_cycle_target_position_link.py")
    assert "MathematicalCycleStateQueryService" in source
    assert "CycleTargetPositionResearchRunner" in source
    assert "CycleTargetPreviewCommand" in source
    assert "preview_prepared" in source
    assert "AlgorithmRunType.MATHEMATICAL_CYCLE_TARGET_POSITION_LINK" in source
    for forbidden in (
        "sqlite3", "SQLite", "CycleTargetPositionEngine", "MathematicalCycleStateService",
        "quant_trading.decision", "quant_trading.risk", "quant_trading.execution",
    ):
        assert forbidden not in source


def test_p39_gui_contains_no_math_sql_or_execution_logic():
    source = _source("src/quant_trading/algorithm_control/ui/mathematical_cycle_target_link_panel.py")
    assert "Select exact P37 operation (required)" in source
    assert "NO EXECUTION" in source
    for forbidden in ("sqlite3", "SQLite", "Engine", "from quant_trading.decision", "alpaca", "submit_order"):
        assert forbidden not in source
