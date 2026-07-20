from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(root: Path) -> set[str]:
    imported: set[str] = set()
    for path in root.rglob("*.py") if root.is_dir() else (root,):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_capital_allocation_domain_is_research_neutral_and_has_no_gui_or_sql() -> None:
    imports = _imports(ROOT / "capital_allocation")
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.algorithm_control",
        "quant_trading.portfolio_accounting",
        "quant_trading.market_history",
        "quant_trading.factors",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_capital_planning_and_factual_portfolio_accounting_do_not_depend_on_each_other() -> None:
    capital_imports = _imports(ROOT / "capital_allocation")
    accounting_imports = _imports(ROOT / "portfolio_accounting")
    assert not [
        name
        for name in capital_imports
        if name.startswith("quant_trading.portfolio_accounting")
    ]
    assert not [
        name
        for name in accounting_imports
        if name.startswith("quant_trading.capital_allocation")
    ]


def test_capital_allocation_gui_uses_typed_contracts_without_sql_or_accounting_mutation() -> None:
    path = ROOT / "algorithm_control" / "ui" / "capital_allocation_panel.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3",
        "quant_trading.persistence",
        "quant_trading.portfolio_accounting",
        "quant_trading.execution",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "CapitalAllocationService" in source
    assert "CapitalAllocationQueryService" in source
    assert "NO EXECUTION" in source


def test_execution_does_not_consume_capital_plans_or_snapshots() -> None:
    imports = _imports(ROOT / "execution")
    assert not [
        name for name in imports if name.startswith("quant_trading.capital_allocation")
    ]
