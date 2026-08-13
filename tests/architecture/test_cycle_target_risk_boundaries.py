from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    for file in path.rglob("*.py") if path.is_dir() else (path,):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"), filename=str(file))):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_p33_risk_domain_is_source_neutral_and_has_no_sql_gui_or_execution_dependencies():
    files = tuple((ROOT / "risk").glob("cycle_target_risk_*.py")) + (ROOT / "risk" / "_structural_manual_review_kernel.py",)
    imports = set().union(*(_imports(path) for path in files))
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.decision", "quant_trading.persistence",
        "quant_trading.algorithm_control", "quant_trading.target_position",
        "quant_trading.capital_allocation", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_p33_orchestration_resolves_public_p31_queries_without_sql_or_risk_formula():
    path = ROOT / "orchestration" / "cycle_target_risk_review.py"
    source, imports = path.read_text(encoding="utf-8"), _imports(path)
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.persistence", "quant_trading.target_position",
        "quant_trading.capital_allocation", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "CycleTargetRiskReviewInput" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source and "abs(" not in source


def test_p33_gui_delegates_without_sql_safety_override_approval_or_formula():
    source = (ROOT / "algorithm_control" / "ui" / "cycle_target_risk_panel.py").read_text(encoding="utf-8")
    assert "CycleTargetRiskReviewCoordinator" in source
    assert "CycleTargetRiskReviewCommand" in source
    assert "sqlite3" not in source and "quant_trading.persistence" not in source
    assert "RiskSafetyStateSnapshot(" not in source
    assert "Decimal(" not in source and "abs(" not in source
    assert 'QPushButton("Approve' not in source


def test_p33_result_has_no_phase6b_accounting_backtest_or_execution_consumer():
    protected = "CycleTargetRiskReviewResult"
    for module in ("backtesting", "portfolio_accounting", "execution"):
        for path in (ROOT / module).rglob("*.py"):
            assert protected not in path.read_text(encoding="utf-8")


def test_phase6a_and_p33_share_one_private_structural_kernel():
    old_engine = (ROOT / "risk" / "target_adjustment_engine.py").read_text(encoding="utf-8")
    new_engine = (ROOT / "risk" / "cycle_target_risk_engine.py").read_text(encoding="utf-8")
    assert "evaluate_structural_manual_review_gate" in old_engine
    assert "evaluate_structural_manual_review_gate" in new_engine
