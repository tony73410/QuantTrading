from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    for file in path.rglob("*.py") if path.is_dir() else (path,):
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_p31_decision_contract_and_kernel_do_not_import_target_or_consumers() -> None:
    files = (
        ROOT / "decision" / "exact_target_difference.py",
        ROOT / "decision" / "cycle_target_adjustment_models.py",
        ROOT / "decision" / "cycle_target_adjustment_engine.py",
        ROOT / "decision" / "cycle_target_adjustment_interfaces.py",
        ROOT / "decision" / "cycle_target_adjustment_service.py",
    )
    imports = set().union(*(_imports(path) for path in files))
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.persistence",
        "quant_trading.target_position", "quant_trading.risk",
        "quant_trading.capital_allocation", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution",
        "quant_trading.market_history", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_p31_orchestration_resolves_public_contracts_without_sql_or_formula_math() -> None:
    path = ROOT / "orchestration" / "cycle_target_adjustment_decision_preview.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.persistence", "quant_trading.risk",
        "quant_trading.capital_allocation", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "Decimal(" not in source
    assert "map_exact_target_difference" not in source


def test_p31_gui_is_an_inspector_without_sql_risk_or_order_logic() -> None:
    path = ROOT / "algorithm_control" / "ui" / "cycle_target_adjustment_decision_panel.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3", "quant_trading.persistence", "quant_trading.risk",
        "quant_trading.capital_allocation", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "TradeIntent(" not in source
    assert "NO EXECUTION" in source
    assert "Risk" in source


def test_risk_and_execution_do_not_consume_the_p31_intent_type() -> None:
    protected_name = "CycleTargetAdjustmentTradeIntent"
    for module in ("risk", "execution", "backtesting", "portfolio_accounting"):
        for path in (ROOT / module).rglob("*.py"):
            assert protected_name not in path.read_text(encoding="utf-8")


def test_phase5d_public_contract_remains_available_and_uses_shared_exact_kernel() -> None:
    engine = (ROOT / "decision" / "target_adjustment_engine.py").read_text(encoding="utf-8")
    models = (ROOT / "decision" / "target_adjustment_models.py").read_text(encoding="utf-8")
    assert "map_exact_target_difference" in engine
    assert "class LinkedTargetDecisionInput" in models
    assert "class TargetAdjustmentTradeIntent" in models
