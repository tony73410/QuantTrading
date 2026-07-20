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


def test_asset_state_domain_has_no_sql_gui_or_trading_consumer_dependencies() -> None:
    imports = _imports(ROOT / "asset_state")
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.algorithm_control",
        "quant_trading.market_history",
        "quant_trading.factors",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_asset_state_gui_uses_typed_services_without_sql_or_financial_modules() -> None:
    path = ROOT / "algorithm_control" / "ui" / "asset_state_panel.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3",
        "quant_trading.persistence",
        "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "AssetStateService" in source
    assert "AssetStateQueryService" in source
    assert "NO EXECUTION" in source


def test_financial_and_execution_modules_do_not_consume_asset_state() -> None:
    for module in (
        "capital_allocation",
        "portfolio_accounting",
        "decision",
        "risk",
        "backtesting",
        "execution",
    ):
        imports = _imports(ROOT / module)
        assert not [name for name in imports if name.startswith("quant_trading.asset_state")]
