from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    paths = path.rglob("*.py") if path.is_dir() else (path,)
    for source_path in paths:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_target_adjustment_decision_domain_has_no_target_sql_gui_risk_or_execution() -> None:
    imports = set()
    for name in (
        "target_adjustment_models.py",
        "target_adjustment_interfaces.py",
        "target_adjustment_engine.py",
        "target_adjustment_service.py",
    ):
        imports.update(_imports(ROOT / "decision" / name))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.target_position",
        "quant_trading.factors",
        "quant_trading.algorithm_control",
        "quant_trading.market_history",
        "quant_trading.asset_state",
        "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_target_adjustment_coordinator_uses_public_contracts_without_sql_gui_or_math() -> None:
    path = ROOT / "orchestration" / "target_adjustment_decision_preview.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.target_position.engine",
        "quant_trading.factors.standardized_state_engine",
        "quant_trading.algorithm_control",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "target_position_link_id" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source
    assert "abs(" not in source


def test_target_adjustment_gui_delegates_without_formula_sql_risk_or_execution() -> None:
    path = ROOT / "algorithm_control" / "ui" / "target_adjustment_decision_panel.py"
    source = path.read_text(encoding="utf-8")
    assert "TargetAdjustmentDecisionPreviewCoordinator" in source
    assert "TargetAdjustmentDecisionPreviewCommand" in source
    assert "sqlite3" not in source
    assert "quant_trading.persistence" not in source
    assert "Decimal(" not in source
    assert "abs(" not in source
    assert "quant_trading.risk" not in source
    assert "quant_trading.execution" not in source


def test_risk_backtesting_accounting_and_execution_do_not_consume_specialized_intent() -> None:
    for module in ("risk", "backtesting", "portfolio_accounting", "execution"):
        imports = _imports(ROOT / module)
        assert not [
            name
            for name in imports
            if name.startswith("quant_trading.decision.target_adjustment")
            or name.startswith("quant_trading.orchestration.target_adjustment")
        ], module


def test_existing_factor_policy_trade_intent_still_requires_factor_snapshot() -> None:
    source = (ROOT / "decision" / "models.py").read_text(encoding="utf-8")
    assert "factor_snapshot_id: UUID" in source
    assert "decision must reference factor snapshots" in source
