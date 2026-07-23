from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported = set()
    paths = path.rglob("*.py") if path.is_dir() else (path,)
    for item in paths:
        for node in ast.walk(ast.parse(item.read_text(encoding="utf-8"), filename=str(item))):
            if isinstance(node, ast.Import): imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imported.add(node.module)
    return imported


def test_specialized_risk_domain_has_no_decision_target_sql_gui_accounting_or_execution():
    imports = set()
    for name in ("target_adjustment_models.py", "target_adjustment_interfaces.py", "target_adjustment_engine.py", "target_adjustment_service.py"):
        imports.update(_imports(ROOT / "risk" / name))
    forbidden = ("sqlite3", "PySide6", "quant_trading.decision", "quant_trading.target_position",
                 "quant_trading.factors", "quant_trading.persistence", "quant_trading.algorithm_control",
                 "quant_trading.portfolio_accounting", "quant_trading.backtesting", "quant_trading.execution", "alpaca")
    assert not [name for name in imports if name.startswith(forbidden)]


def test_coordinator_resolves_public_evidence_without_sql_or_risk_formulas():
    path = ROOT / "orchestration" / "target_adjustment_risk_review.py"
    source, imports = path.read_text(encoding="utf-8"), _imports(path)
    forbidden = ("sqlite3", "PySide6", "quant_trading.persistence", "quant_trading.target_position.engine",
                 "quant_trading.factors", "quant_trading.algorithm_control", "quant_trading.backtesting",
                 "quant_trading.portfolio_accounting", "quant_trading.execution", "alpaca")
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "TargetAdjustmentRiskReviewCommand" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source and "abs(" not in source


def test_gui_delegates_without_sql_arithmetic_safety_override_or_approval():
    source = (ROOT / "algorithm_control" / "ui" / "target_adjustment_risk_panel.py").read_text(encoding="utf-8")
    assert "TargetAdjustmentRiskReviewCoordinator" in source
    assert "TargetAdjustmentRiskReviewCommand" in source
    assert "sqlite3" not in source and "quant_trading.persistence" not in source
    assert "Decimal(" not in source and "abs(" not in source
    assert "RiskSafetyStateSnapshot(" not in source
    assert 'QPushButton("Approve' not in source


def test_specialized_result_is_not_consumed_by_backtesting_accounting_or_execution():
    for module in ("backtesting", "portfolio_accounting", "execution"):
        imports = _imports(ROOT / module)
        assert not [name for name in imports if name.startswith("quant_trading.risk.target_adjustment")], module
