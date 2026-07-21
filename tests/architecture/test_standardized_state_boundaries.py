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


def test_standardized_state_factor_contract_has_no_gui_sql_or_trading_consumer_dependency() -> None:
    imports = set()
    for path in (ROOT / "factors").glob("standardized_state_*.py"):
        imports.update(_imports(path))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.target_position",
        "quant_trading.asset_state",
        "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "quant_trading.market_history",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_standardized_state_gui_uses_typed_factor_services_without_sql_or_math() -> None:
    path = ROOT / "algorithm_control" / "ui" / "standardized_state_panel.py"
    source = path.read_text(encoding="utf-8")
    assert "StandardizedPriceStateService" in source
    assert "StandardizedPriceStateQueryService" in source
    assert "NO EXECUTION" in source
    assert "sqlite3" not in source
    assert "quant_trading.persistence" not in source
    assert "Decimal(" not in source
    assert "quant_trading.target_position" not in source
    assert "quant_trading.decision" not in source
    assert "quant_trading.risk" not in source


def test_trading_and_state_consumers_do_not_import_standardized_state() -> None:
    for module in (
        "target_position",
        "asset_state",
        "capital_allocation",
        "portfolio_accounting",
        "decision",
        "risk",
        "backtesting",
        "execution",
    ):
        assert not [
            name
            for name in _imports(ROOT / module)
            if name.startswith("quant_trading.factors.standardized_state")
        ], module


def test_generic_factor_publication_does_not_consume_standardized_state() -> None:
    for path in (
        ROOT / "factors" / "engine.py",
        ROOT / "factors" / "history.py",
        ROOT / "factors" / "models.py",
        ROOT / "decision",
    ):
        assert not [
            name
            for name in _imports(path)
            if name.startswith("quant_trading.factors.standardized_state")
        ], str(path)
